"""`polytypst books`, `build`, `parity` and `new-book`: one entry point for every book in `books/<key>/`."""

import argparse
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

from .books import BOOKS_DIR, book_by_key, books
from .checker import AuditSpec, DocumentQualityChecker
from .compiler.presets import DOMAIN_PROFILES
from .edition import Book, Edition, VisualLimits
from .figure_leaks import FIGURE_TEXT_LEAK, figure_text_leaks
from .literal_numbers import edition_literal_counts
from .new_book import scaffold_book
from .ocr.scan import SourceScanError
from .parity import FACSIMILE, compare, verdict, write_report
from .parity.ink_cache import InkCache
from .parity.measure import measure_pages, read_measures, worse, write_measures
from .parity.source import SOURCES_ENV, ensure_source_ocr, source_ocr_dir, source_pdf
from .parity.visual import (
    LAYOUT_LIMIT,
    TOP_REGIONS,
    layout_check,
    visual_check,
    write_visual_report,
)
from .parity.words import page_ink
from .review import (
    default_running_heads,
    lowest_pages,
    read_findings,
    render_checklist,
    review_folder,
)
from .rules import all_rules
from .step_profile import as_json, profile_step, render, run_cold, time_typst

LAYOUT_SAMPLE_EVERY = 10

EPILOG = f"""\
examples:
  polytypst books
  polytypst build bourbaki --edition vintage
  polytypst parity bourbaki --edition facsimile --pages 31-34
  polytypst audit hecke
  polytypst profile bourbaki --edition facsimile --step build

The source scan is ${SOURCES_ENV}/<spec.source_pdf>, or --source PATH.
docs/scanned-books.md explains the procedure and the report.
"""


BASELINE = Path("quality/baseline.json")
DOCUMENT_FORMATS = {"pdf": "", "epub": "EPUB_"}


def format_output(edition: Edition, fmt: str) -> Path:
    """The file an edition writes for `fmt`, beside its rebuilt PDF and named like it."""
    return edition.rebuilt if fmt == "pdf" else edition.rebuilt.with_suffix(f".{fmt}")


def parse_pages(text: str) -> set[int]:
    """'31-34,40' -> {31, 32, 33, 34, 40}."""
    pages: set[int] = set()
    for part in text.split(","):
        first, _, last = part.strip().partition("-")
        try:
            start, stop = int(first), int(last or first)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"pages must look like 3,7-9, got {text!r}"
            ) from None
        pages.update(range(start, stop + 1))
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
    book, name, edition = _pick(parser, args.book, args.edition)
    formats = edition.formats
    if args.formats is not None:
        formats = frozenset(f for f in args.formats.split(",") if f)
        if unknown := formats - edition.formats:
            parser.error(f"{args.book} cannot make {', '.join(sorted(unknown))}; formats: {', '.join(sorted(edition.formats))}")
    if args.footnotes == "running" and (edition.spec is None or not edition.spec.footnote_style):
        parser.error(f"{args.book} has no footnotes to renumber; leave out --footnotes")
    if args.pages and edition.build_pages is None:
        parser.error(f"{args.book} {name} cannot rebuild only some pages; leave out --pages")
    _ = book.build(name, args.source, formats, args.footnotes, parse_pages(args.pages) if args.pages else None)
    if edition.spec is None:
        return 0
    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    recorded = baseline.get(args.book, {}).get(name, {})
    rose = _rose(Counter(edition_literal_counts(edition.rebuilt, edition.spec)), recorded)
    for line in rose:
        print(f"numbering: {line}; run: polytypst audit {args.book} --edition {name}")
    return 1 if rose else 0


def _measure(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    book, name, edition = _pick(parser, args.book, args.edition)
    if edition.parity is None:
        parser.error(f"{args.book} {name} maps no scan pages to rebuilt pages; measure a facsimile edition")
    if not edition.rebuilt.exists():
        parser.error(f"{edition.rebuilt} is missing; run: polytypst build {args.book} --edition {name}")
    source = source_pdf(book.spec, args.source)
    page_map = {p: v[0] for p, v in edition.parity.page_map().items() if v}
    if args.pages:
        wanted = parse_pages(args.pages)
        page_map = {p: v for p, v in page_map.items() if p in wanted}
    measures = measure_pages(_scan_ink(book, source), edition.rebuilt, page_map)
    review = book.out_dir / "review"
    report, baseline = review / f"measure_{name}.json", review / f"measure_{name}_baseline.json"
    write_measures(report, {**read_measures(report), **{m.page: m for m in measures}}.values())
    coverage = sorted(m.coverage for m in measures)
    print(f"{len(measures)} pages, coverage median {coverage[len(coverage) // 2] if coverage else 0}; report: {report}")
    recorded = read_measures(baseline)
    if args.update:
        write_measures(baseline, {**recorded, **{m.page: m for m in measures}}.values())
        print(f"baseline: {baseline}")
        return 0
    if not recorded:
        print(f"no baseline yet; record one: polytypst measure {args.book} --edition {name} --update")
        return 1
    failed = [(m.page, why) for m in measures if m.page in recorded and (why := worse(m, recorded[m.page]))]
    for page, why in failed:
        print(f"p{page} got worse: {', '.join(why)}")
    print(f"{len(failed)} of {len(measures)} pages got worse than {baseline}")
    return 1 if failed else 0


def _rose(counts: Counter[str], recorded: dict[str, int]) -> list[str]:
    return [f"{rule} {n} > {recorded.get(rule, 0)}" for rule, n in sorted(counts.items()) if n > recorded.get(rule, 0)]


def _scan_ink(book: Book, source: Path) -> InkCache:
    return InkCache(source, book.out_dir / "facsimile" / "ink", page_ink)


def _parity(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    book, name, edition = _pick(parser, args.book, args.edition)
    if edition.parity is None:
        checked = [n for n, e in book.editions.items() if e.parity]
        parser.error(f"{args.book} {name} has no parity check; checked editions: {', '.join(checked) or 'none'}")
    if not edition.rebuilt.exists():
        parser.error(f"{edition.rebuilt} is missing; run: polytypst build {args.book} --edition {name}")
    if args.against is not None and not args.against.exists():
        parser.error(f"{args.against} is missing")
    source = source_pdf(book.spec, args.source)
    page_map = edition.parity.page_map()
    if args.pages:
        wanted = parse_pages(args.pages)
        page_map = {p: v for p, v in page_map.items() if p in wanted}
    preset = edition.parity.visual or VisualLimits()
    limits = {
        "missing": args.max_missing if args.max_missing is not None else preset.missing,
        "extra": args.max_extra if args.max_extra is not None else preset.extra,
        "layout": args.max_layout if args.max_layout is not None else preset.layout,
        "offset": args.max_offset if args.max_offset is not None else preset.offset,
    }
    if args.visual or args.against or edition.parity.visual or any(v is not None for v in limits.values()):
        return _visual(args, _scan_ink(book, source), edition.rebuilt, page_map, args.out or book.out_dir / f"visual_{name}", limits)
    ensure_source_ocr(source, book.ocr, book.spec.ocr_languages)
    out = args.out or book.out_dir / f"parity_{name}"
    results = compare(
        _scan_ink(book, source), edition.rebuilt, page_map, ocr=book.ocr,
        diagrams=edition.parity.diagrams, diagram_text=edition.parity.diagram_text, work=out / "work",
    )
    ok = write_report(results, out, edition.parity.tolerance)
    failed = sum(1 for r in results if verdict(r, edition.parity.tolerance))
    print(f"{len(results) - failed}/{len(results)} pages pass; report: {out / 'index.html'}")
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
    ocr = source_ocr_dir(args.folder)
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


def _visual(
    args: argparse.Namespace, scan: InkCache, rebuilt: Path, page_map: dict[int, list[int]], out: Path,
    limits: dict[str, float | None],
) -> int:
    results = visual_check(scan, rebuilt, page_map)
    against = (args.against, visual_check(scan, args.against, page_map)) if args.against else None
    summary = write_visual_report(results, out, scan.source, rebuilt, against, args.top)
    regions = summary["regions"]
    print(f"{summary['pages_with_regions']}/{summary['pages']} pages differ from the scan: "
          f"{regions['extra']} extra, {regions['missing']} missing regions; report: {out / 'index.html'}")
    failed = False
    for kind, limit in limits.items():
        if limit is not None and (over := [p.source_page for p in results if getattr(p, kind) > limit]):
            print(f"{kind} over {limit}: page {', '.join(map(str, over))}")
            failed = True
    if against:
        print(f"against {args.against}: improved {summary['improved']}, regressed {summary['regressed']}")
        failed = failed or bool(summary["regressed"])
    return 1 if failed else 0


def _share(text: str) -> float:
    value = float(text)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError(f"{text} is not a share from 0 to 1")
    return value


def _layout_counts(key: str, name: str, edition: Edition) -> Counter[str]:
    try:
        source = source_pdf(book_by_key(key).spec, None)
    except SourceScanError as error:
        print(f"{key} {name}: layout not checked: {error}")
        return Counter()
    page_map = edition.parity.page_map() if edition.parity else {}
    sample = {p: v for p, v in page_map.items() if p % LAYOUT_SAMPLE_EVERY == 0}
    shares = layout_check(source, edition.rebuilt, sample)
    return Counter({"facsimile_layout": sum(1 for share in shares.values() if share > LAYOUT_LIMIT)})


def _audit(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else {}
    if args.book:
        targets = [(key, *_pick(parser, key, args.edition)[1:]) for key in args.book]
    else:
        recorded_targets = [(key, name, book_by_key(key).editions[name]) for key, editions in baseline.items() for name in editions]
        built = [
            (key, name, edition)
            for key, book in books().items()
            for name, edition in book.editions.items()
            if edition.rebuilt.exists() and name not in baseline.get(key, {})
        ]
        targets = recorded_targets + built
    ok = True
    for key, name, edition in targets:
        if not edition.rebuilt.exists():
            print(f"{key} {name}: {edition.rebuilt} is missing; run: polytypst build {key} --edition {name}")
            ok = False
            continue
        if not args.book and not args.update and name not in baseline.get(key, {}):
            print(f"{key} {name}: FAIL, no baseline; run: polytypst audit {key} --edition {name} --update")
            ok = False
            continue
        missing = [f for f in sorted(edition.formats) if not format_output(edition, f).exists()]
        if missing:
            formats = ",".join(missing)
            print(f"{key} {name}: FAIL, no {formats} output; run: polytypst build {key} --edition {name} --formats {formats}")
            ok = False
            continue
        spec = AuditSpec.from_monograph(edition.spec) if edition.spec else AuditSpec()
        spec = replace(spec, scan_line_breaks=edition.scan_line_breaks)
        counts: Counter[str] = Counter()
        for fmt in sorted(edition.formats | {"pdf"}):
            if fmt in DOCUMENT_FORMATS:
                issues = DocumentQualityChecker(format_output(edition, fmt), spec).run_all_checks().issues
                counts.update(f"{DOCUMENT_FORMATS[fmt]}{i.rule_name}" for i in issues)
        if edition.spec:
            counts.update(edition_literal_counts(edition.rebuilt, edition.spec))
            if leaks := figure_text_leaks(book_by_key(key)):
                counts[FIGURE_TEXT_LEAK] = len(leaks)
        if edition.parity is not None and edition.parity.tolerance is FACSIMILE:
            counts.update(_layout_counts(key, name, edition))
        recorded = baseline.get(key, {}).get(name, {})
        rose = _rose(counts, recorded)
        if args.update:
            if rose and name in baseline.get(key, {}) and not args.allow_rise:
                print(f"{key} {name}: FAIL, not recorded; fix the rise or pass --allow-rise")
                for line in rose:
                    print(f"  rose: {line}")
                ok = False
                continue
            baseline.setdefault(key, {})[name] = dict(sorted(counts.items()))
            print(f"{key} {name}: recorded {counts.total()} issues")
            continue
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


def _rules() -> int:
    table = [("STAGE", "RULE", "SEVERITY", "ENFORCED", "WHERE")] + [
        (r.stage, r.name, r.severity, r.enforced, f"{r.path}:{r.line}") for r in all_rules()
    ]
    widths = [max(len(row[i]) for row in table) for i in range(4)]
    for row in table:
        print("  ".join(cell.ljust(w) for cell, w in zip(row, widths)) + "  " + row[4])
    print(f"\n{len(table) - 1} rules. audit: fails when a count rises above {BASELINE}. build: fails when a source count rises. parity: fails on any reason. no: prints only.")
    return 0


PROFILE_STEPS = ("build", "parity", "audit")


def _profile(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    _, name, edition = _pick(parser, args.book, args.edition)
    step_argv = [args.book, "--edition", name]
    if args.source is not None:
        if args.step == "audit":
            parser.error("audit reads no scan; leave out --source")
        step_argv += ["--source", str(args.source)]

    def step() -> int:
        return main(args.step, step_argv)

    typ = edition.rebuilt.with_suffix(".typ")
    before = typ.stat().st_mtime_ns if typ.exists() else None
    title = f"{args.book} {name} {args.step}{' --cold' if args.cold else ''}"
    profile = profile_step(title, (lambda: run_cold(step)) if args.cold else step)
    if args.step == "build" and typ.exists() and typ.stat().st_mtime_ns != before:
        profile = replace(profile, typst=time_typst(typ))
    print(json.dumps(as_json(profile), indent=2, ensure_ascii=False) if args.json else render(profile))
    return profile.exit_code


def main(command: str, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog=f"polytypst {command}", epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter,
        description={
            "books": "List every book and its editions; [parity] marks editions you can check against the scan.",
            "build": "Build one edition of a book. The default edition is the first one `polytypst books` lists. "
            "Exits 1 when the built Typst or LaTeX has more literal numbers than quality/baseline.json records.",
            "parity": "Check a rebuilt edition against its source scan. Writes a report and exits 1 when a page fails.",
            "measure": "Measure each page of a rebuilt facsimile against its scan: coverage of the scan's ink cells and "
            "the extra, missing and layout shares. Writes output/<book>/review/measure_<edition>.json and exits 1 "
            "when a page got worse than measure_<edition>_baseline.json beside it.",
            "audit": "Count the checker's issues per rule in every format a rebuilt edition declares. Exits 1 when a count rises above the baseline, a declared format has no output, or a built edition has no baseline.",
            "rules": "List every rule a book is checked against: its stage, severity, the command that enforces it, and where it is written.",
            "new-book": "Write books/KEY/book.toml for a new book.",
            "review": "Measure an output folder against its scan, with or without a book key: text coverage per scan page, "
            "text past the page edge, LaTeX log warnings, literal numbers, links, footnotes and leaked running heads. "
            "Writes FOLDER/review/ and prints what changed since the last review.",
            "checklist": "Render a findings JSONL file as a Markdown checklist beside it, and count findings by status.",
            "profile": "Run one build step of one edition under cProfile. Prints its time by owner (Python bytecode, each "
            "native library, subprocess waits) and its top functions by own time. After a build, also times the "
            "generated .typ cold, edited and repeat, beside the Typst CLI. Exits with the step's exit code.",
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
        parser.add_argument("--domain", required=True, choices=list(DOMAIN_PROFILES), help="subject profile, such as math or economics")
        args = parser.parse_args(argv)
        try:
            written = scaffold_book(BOOKS_DIR.parent, args.key, args.title, args.author, args.source, args.pages, domain=args.domain)
        except ValueError as error:
            parser.error(str(error))
        for path in written:
            print(path)
        print(f"next: fill in the chapters in books/{args.key}/book.toml, then run `polytypst books`")
        print("then: add the spec to test_specs_come_from_the_editions in tests/test_books.py")
        return 0
    if command == "rules":
        parser.parse_args(argv)
        return _rules()
    if command == "audit":
        parser.add_argument("book", nargs="*", help="book keys from `polytypst books` (default: every edition in the baseline or built)")
        parser.add_argument("--edition", help="edition name (default: the book's first)")
        parser.add_argument("--baseline", type=Path, default=BASELINE, help=f"rule counts per book and edition (default: {BASELINE})")
        parser.add_argument(
            "--update", action="store_true",
            help="record the current counts in the baseline instead of comparing; a count may only fall, "
            "and an edition with a count that rose is left as recorded and fails",
        )
        parser.add_argument("--allow-rise", action="store_true", help="with --update, record counts that rose too")
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
        parser.add_argument(
            "--pages",
            help="scan pages to set again, e.g. 229 or 200-210; every other page reuses its last built Typst "
            "(strict facsimile editions only)",
        )
    if command == "profile":
        parser.description = f"{parser.description} steps: {', '.join(PROFILE_STEPS)}; books: {', '.join(books())}."
        parser.add_argument("--step", choices=PROFILE_STEPS, required=True, help="the build step to run under the profiler")
        parser.add_argument(
            "--cold", action="store_true",
            help="draw scan ink into an empty scratch folder, as a first build does; the real ink cache stays as it is",
        )
        parser.add_argument("--json", action="store_true", help="print the profile as JSON instead of text tables")
    if command == "measure":
        parser.add_argument("--pages", help="source pages to measure, e.g. 229 or 200-210 (default: all)")
        parser.add_argument(
            "--update", action="store_true",
            help="record the measured pages in the baseline instead of comparing; other pages keep their record",
        )
    if command == "parity":
        parser.add_argument("--pages", help="source pages to check, e.g. 31-34,40 (default: all)")
        parser.add_argument("--out", type=Path, help="report folder (default: output/<book>/parity_<edition>, or visual_<edition>)")
        parser.add_argument(
            "--visual", action="store_true",
            help="compare ink only, without OCR: box the rebuilt ink the scan lacks and the scan ink not rebuilt, with crops",
        )
        parser.add_argument(
            "--against", type=Path,
            help="an older build of the edition to compare too (implies --visual); exits 1 when a page got worse",
        )
        parser.add_argument(
            "--top", type=int, default=TOP_REGIONS,
            help=f"with --visual, how many of the book's largest regions get crops (default: {TOP_REGIONS})",
        )
        parser.add_argument(
            "--max-missing", type=_share,
            help="the largest share of a page's scan ink the rebuild may lack (implies --visual); exits 1 above it",
        )
        parser.add_argument(
            "--max-extra", type=_share,
            help="the largest share of a page's rebuilt ink the scan may lack (implies --visual); exits 1 above it",
        )
        parser.add_argument(
            "--max-layout", type=_share,
            help="the largest share of a page's coarse grid cells inked on only one of scan and rebuild "
            "(implies --visual); exits 1 above it",
        )
        parser.add_argument(
            "--max-offset", type=float, metavar="PT",
            help="the largest move in pt of any edge of a page's text block, rebuilt against scan "
            "(implies --visual); exits 1 above it",
        )
    args = parser.parse_args(argv)
    if command == "books":
        return _list()
    if command == "measure":
        return _measure(parser, args)
    if command == "profile":
        return _profile(parser, args)
    return _build(parser, args) if command == "build" else _parity(parser, args)
