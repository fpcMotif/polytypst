"""`polytypst books`, `build`, `parity` and `new-book`: one entry point for every book in `src/<key>/book.py`."""

import argparse
import json
from collections import Counter
from pathlib import Path

from .books import book_by_key, books
from .checker import AuditSpec, DocumentQualityChecker
from .edition import Book, Edition
from .new_book import scaffold_book
from .parity import compare, verdict, write_report
from .parity.source import SOURCES_ENV, ensure_source_ocr, source_pdf
from .review import (
    default_running_heads,
    lowest_pages,
    read_findings,
    render_checklist,
    review_folder,
)

EPILOG = f"""\
examples:
  polytypst books
  polytypst build bourbaki --edition vintage
  polytypst parity bourbaki --edition facsimile --pages 31-34
  polytypst audit hecke

The source scan is ${SOURCES_ENV}/<spec.source_pdf>, or --source PATH.
docs/scanned-books.md explains the procedure and the report.
"""


BASELINE = Path("quality/baseline.json")


def parse_pages(text: str) -> set[int]:
    """'31-34,40' -> {31, 32, 33, 34, 40}."""
    pages: set[int] = set()
    for part in text.split(","):
        first, _, last = part.partition("-")
        pages.update(range(int(first), int(last or first) + 1))
    return pages


def _pick(parser: argparse.ArgumentParser, key: str, edition: str | None) -> tuple[Book, str, Edition]:
    try:
        book = book_by_key(key)
    except KeyError as error:
        parser.error(error.args[0])
    name = edition or next(iter(book.editions))
    if name not in book.editions:
        parser.error(f"{key} has no edition {name!r}; editions: {', '.join(book.editions)}")
    return book, name, book.editions[name]


def _list() -> int:
    for key, book in books().items():
        print(key)
        for name, edition in book.editions.items():
            check = "  [parity]" if edition.parity else ""
            print(f"  {name:<12} {edition.summary}{check}")
    return 0


def _build(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    book, _, edition = _pick(parser, args.book, args.edition)
    if book.figures is not None:
        _ = book.figures(book.out_dir)
    formats = edition.formats
    if args.formats is not None:
        formats = frozenset(f for f in args.formats.split(",") if f)
        if unknown := formats - edition.formats:
            parser.error(f"{args.book} cannot make {', '.join(sorted(unknown))}; formats: {', '.join(sorted(edition.formats))}")
    if args.footnotes == "running" and (edition.spec is None or not edition.spec.footnote_style):
        parser.error(f"{args.book} has no footnotes to renumber; leave out --footnotes")
    edition.build(args.source, formats, args.footnotes)
    return 0


def _parity(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    book, name, edition = _pick(parser, args.book, args.edition)
    if edition.parity is None:
        checked = [n for n, e in book.editions.items() if e.parity]
        parser.error(f"{args.book} {name} has no parity check; checked editions: {', '.join(checked) or 'none'}")
    if not edition.rebuilt.exists():
        parser.error(f"{edition.rebuilt} is missing; run: polytypst build {args.book} --edition {name}")
    source = source_pdf(book.spec, args.source)
    ensure_source_ocr(source, book.ocr, book.spec.ocr_languages)
    page_map = edition.parity.page_map()
    if args.pages:
        wanted = parse_pages(args.pages)
        page_map = {p: v for p, v in page_map.items() if p in wanted}
    out = args.out or book.out_dir / f"parity_{name}"
    results = compare(
        source, edition.rebuilt, page_map, ocr=book.ocr,
        diagrams=edition.parity.diagrams, diagram_text=edition.parity.diagram_text, work=out / "work",
    )
    ok = write_report(results, out, edition.parity.tolerance)
    failed = sum(1 for r in results if verdict(r, edition.parity.tolerance))
    print(f"{len(results) - failed}/{len(results)} pages pass; report: {out / 'index.html'}")
    return 0 if ok else 1


def _audit(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else {}
    if args.book:
        targets = [(key, *_pick(parser, key, args.edition)[1:]) for key in args.book]
    else:
        targets = [(key, name, book_by_key(key).editions[name]) for key, editions in baseline.items() for name in editions]
    ok = True
    for key, name, edition in targets:
        if not edition.rebuilt.exists():
            print(f"{key} {name}: {edition.rebuilt} is missing; run: polytypst build {key} --edition {name}")
            ok = False
            continue
        spec = AuditSpec.from_monograph(edition.spec) if edition.spec else AuditSpec()
        counts = Counter(i.rule_name for i in DocumentQualityChecker(edition.rebuilt, spec).run_all_checks().issues)
        if args.update:
            baseline.setdefault(key, {})[name] = dict(sorted(counts.items()))
            print(f"{key} {name}: recorded {counts.total()} issues")
            continue
        recorded = baseline.get(key, {}).get(name, {})
        rose = [f"{rule} {n} > {recorded.get(rule, 0)}" for rule, n in sorted(counts.items()) if n > recorded.get(rule, 0)]
        fell = [f"{rule} {counts[rule]} < {n}" for rule, n in sorted(recorded.items()) if counts[rule] < n]
        print(f"{key} {name}: {'FAIL' if rose else 'ok'}, {counts.total()} issues")
        for line in rose:
            print(f"  rose: {line}")
        for line in fell:
            print(f"  fell: {line}; run with --update to lower the baseline")
        ok = ok and not rose
    if args.update:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(baseline, indent=2, ensure_ascii=False, sort_keys=True)
        args.baseline.write_text(f"{text}\n", encoding="utf-8")
    return 0 if ok else 1


def _review(parser: argparse.ArgumentParser, argv: list[str]) -> int:
    parser.add_argument("folder", type=Path, help="output folder holding the rebuilt PDFs, sources, logs and source_ocr/")
    parser.add_argument("--scan", type=Path, help="the source scan; needed for --visual and when source_ocr/ is empty")
    parser.add_argument(
        "--running-head", action="append", default=[],
        help="a running-head title to find in body text (repeatable; default: the folder name without its number)",
    )
    parser.add_argument("--ocr-languages", default="zh-Hans,en-US", help="Vision OCR languages when source_ocr/ is empty")
    parser.add_argument("--visual", action="store_true", help="also write red/cyan optical parity overlays per rebuilt PDF")
    parser.add_argument("--out", type=Path, help="report folder (default: FOLDER/review)")
    args = parser.parse_args(argv)
    if not args.folder.is_dir():
        parser.error(f"{args.folder} is not a folder")
    ocr = args.folder / "source_ocr"
    if not any(ocr.glob("p[0-9][0-9][0-9].json")):
        if args.scan is None:
            parser.error(f"{ocr} has no OCR pages; pass --scan SCAN.pdf to read them")
        ensure_source_ocr(args.scan, ocr, args.ocr_languages.split(","))
    if args.visual and args.scan is None:
        parser.error("--visual needs --scan")
    out = args.out or args.folder / "review"
    heads = args.running_head or default_running_heads(args.folder)
    measures = review_folder(args.folder, out, heads, args.scan, args.visual)
    for name, m in measures.items():
        if "coverage_median" in m:
            print(f"{name}: {m['pages']} pages, coverage median {m['coverage_median']}, "
                  f"{m['pages_coverage_below_half']} scan pages below half, {m['pages_text_past_edge']} pages with text past the edge")
            print(f"  lowest coverage: {lowest_pages(out / 'pages.csv', name)}")
    print(f"report: {out / 'measures.json'}, {out / 'pages.csv'}, {out / 'history.jsonl'}")
    return 0


def main(command: str, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog=f"polytypst {command}", epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter,
        description={
            "books": "List every book and its editions; [parity] marks editions you can check against the scan.",
            "build": "Build one edition of a book. The default edition is the first one `polytypst books` lists.",
            "parity": "Check a rebuilt edition against its source scan. Writes a report and exits 1 when a page fails.",
            "audit": "Count the checker's issues per rule in rebuilt editions. Exits 1 when a count rises above the baseline.",
            "new-book": "Write src/KEY/{__init__,spec,book}.py for a new book and add polytypst.KEY to pyproject.toml.",
            "review": "Measure an output folder against its scan, with or without a book key: text coverage per scan page, "
            "text past the page edge, LaTeX log warnings, literal numbers, links, footnotes and leaked running heads. "
            "Writes FOLDER/review/ and prints what changed since the last review.",
            "checklist": "Render a findings JSONL file as a Markdown checklist beside it, and count findings by status.",
        }[command],
    )
    if command == "review":
        return _review(parser, argv)
    if command == "checklist":
        parser.add_argument("findings", type=Path, help="JSONL file, one finding per line (fields of polytypst.review.Finding)")
        args = parser.parse_args(argv)
        try:
            findings = read_findings(args.findings)
        except ValueError as error:
            print(f"{args.findings} has bad lines; fix them and run the command again:\n{error}")
            return 1
        out = args.findings.with_suffix(".md")
        out.write_text(render_checklist(findings), encoding="utf-8")
        status = Counter(f.status for f in findings)
        print(f"{len(findings)} findings: " + ", ".join(f"{n} {s}" for s, n in sorted(status.items())) + f"; checklist: {out}")
        return 0
    if command == "new-book":
        parser.add_argument("key", help="package and output folder name, a Python identifier")
        parser.add_argument("--title", required=True)
        parser.add_argument("--author", required=True)
        parser.add_argument("--source", required=True, help=f"scan file name inside ${SOURCES_ENV}")
        parser.add_argument("--pages", type=int, required=True, help="page count of the scan")
        args = parser.parse_args(argv)
        try:
            written = scaffold_book(Path.cwd(), args.key, args.title, args.author, args.source, args.pages)
        except ValueError as error:
            parser.error(str(error))
        for path in written:
            print(path)
        print(f"next: fill in the chapters in src/{args.key}/spec.py, then run `polytypst books`")
        print("then: add the spec to test_specs_come_from_the_editions in tests/test_books.py")
        return 0
    if command == "audit":
        parser.add_argument("book", nargs="*", help="book keys from `polytypst books` (default: every edition in the baseline)")
        parser.add_argument("--edition", help="edition name (default: the book's first)")
        parser.add_argument("--baseline", type=Path, default=BASELINE, help=f"rule counts per book and edition (default: {BASELINE})")
        parser.add_argument("--update", action="store_true", help="record the current counts in the baseline instead of comparing")
        return _audit(parser, parser.parse_args(argv))
    if command != "books":
        parser.add_argument("book", help="book key from `polytypst books`")
        parser.add_argument("--edition", help="edition name (default: the book's first)")
        parser.add_argument("--source", type=Path, help=f"source scan PDF (default: ${SOURCES_ENV}/<spec.source_pdf>)")
    if command == "build":
        parser.add_argument(
            "--formats",
            help="comma-separated slow formats to make, e.g. pdf or pdf,tex; empty writes only Markdown and Typst "
            "(default: every format the edition makes)",
        )
        parser.add_argument(
            "--footnotes", choices=("original", "running"), default="original",
            help="original: the scan's marks (1), *, †) and restarts; running: 1, 2, 3 through the book",
        )
    if command == "parity":
        parser.add_argument("--pages", help="source pages to check, e.g. 31-34,40 (default: all)")
        parser.add_argument("--out", type=Path, help="report folder (default: output/<book>/parity_<edition>)")
    args = parser.parse_args(argv)
    if command == "books":
        return _list()
    return _build(parser, args) if command == "build" else _parity(parser, args)
