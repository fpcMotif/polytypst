"""`polytypst books`, `build`, `parity` and `new-book`: one entry point for every book in `src/<key>/book.py`."""

import argparse
from pathlib import Path

from .books import books
from .edition import Book, Edition
from .new_book import scaffold_book
from .parity import compare, verdict, write_report
from .parity.source import SOURCES_ENV, ensure_source_ocr, source_pdf

EPILOG = f"""\
examples:
  polytypst books
  polytypst build bourbaki --edition vintage
  polytypst parity bourbaki --edition facsimile --pages 31-34

The source scan is ${SOURCES_ENV}/<spec.source_pdf>, or --source PATH.
docs/scanned-books.md explains the procedure and the report.
"""


def parse_pages(text: str) -> set[int]:
    """'31-34,40' -> {31, 32, 33, 34, 40}."""
    pages: set[int] = set()
    for part in text.split(","):
        first, _, last = part.partition("-")
        pages.update(range(int(first), int(last or first) + 1))
    return pages


def _pick(parser: argparse.ArgumentParser, key: str, edition: str | None) -> tuple[Book, str, Edition]:
    known = books()
    normalized = {**known, **{k.replace("_", "-"): v for k, v in known.items()}}
    if key not in normalized:
        parser.error(f"unknown book {key!r}; known: {', '.join(known)}")
    book = normalized[key]
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
    edition.build(args.source, formats)
    return 0


def _parity(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    book, name, edition = _pick(parser, args.book, args.edition)
    if edition.parity is None:
        checked = [n for n, e in book.editions.items() if e.parity]
        parser.error(f"{args.book} {name} has no parity check; checked editions: {', '.join(checked) or 'none'}")
    if not edition.rebuilt.exists():
        parser.error(f"{edition.rebuilt} is missing; run: polytypst build {args.book} --edition {name}")
    source = source_pdf(book.spec, args.source)
    ensure_source_ocr(source, book.ocr)
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


def main(command: str, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog=f"polytypst {command}", epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter,
        description={
            "books": "List every book and its editions; [parity] marks editions you can check against the scan.",
            "build": "Build one edition of a book. The default edition is the first one `polytypst books` lists.",
            "parity": "Check a rebuilt edition against its source scan. Writes a report and exits 1 when a page fails.",
            "new-book": "Write src/KEY/{__init__,spec,book}.py for a new book and add polytypst.KEY to pyproject.toml.",
        }[command],
    )
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
    if command == "parity":
        parser.add_argument("--pages", help="source pages to check, e.g. 31-34,40 (default: all)")
        parser.add_argument("--out", type=Path, help="report folder (default: output/<book>/parity_<edition>)")
    args = parser.parse_args(argv)
    if command == "books":
        return _list()
    return _build(parser, args) if command == "build" else _parity(parser, args)
