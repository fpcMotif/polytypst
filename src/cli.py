"""Command-line interface for polytypst."""

import argparse
import sys
from pathlib import Path

from .ocr.backend import DEFAULT_BACKEND, KINDS, backend_argument

BOOK_COMMANDS = """\
book commands (see `polytypst COMMAND --help`):
  polytypst books                         list every book and its editions
  polytypst build BOOK [--edition E]      build one edition of a book
  polytypst parity BOOK --edition E       check a rebuilt edition against its scan
  polytypst new-book KEY --title T ...    write src/KEY/ for a new book and list its package
"""


def page_set(text: str) -> set[int]:
    """Page numbers from `3,7-9` style text."""
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


def main() -> None:
    if sys.argv[1:2] in (["books"], ["build"], ["parity"], ["new-book"]):
        from .books_cli import main as books_main

        sys.exit(books_main(sys.argv[1], sys.argv[2:]))
    parser = argparse.ArgumentParser(
        description="polytypst: Universal tool to turn complex PDFs into beautiful Typst, LaTeX, and EPUB.",
        epilog=BOOK_COMMANDS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "source", type=Path, nargs="?", help="The source scan: a PDF, a folder of page images, or one image"
    )
    parser.add_argument(
        "--export-web",
        action="store_true",
        help="Export web catalog and static assets to polytypst/web/public",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("output"), help="Output directory"
    )
    parser.add_argument(
        "--backend",
        type=backend_argument,
        default=DEFAULT_BACKEND,
        help=(
            "OCR backend as KIND[:MODEL][?KEY=VALUE&...], as in gemini, "
            "local:deepseek-ocr, colab?gpu=A100&workers=3, or "
            f"openai:MODEL?base_url=http://host:8000/v1&key_env=. Kinds: {', '.join(KINDS)}"
        ),
    )
    parser.add_argument(
        "--pages",
        type=page_set,
        help="Transcribe only these pages, as in 3,7-9",
    )
    parser.add_argument(
        "--retranscribe",
        action="store_true",
        help="Redo stored transcripts that another backend or prompt made",
    )
    parser.add_argument(
        "--publisher",
        type=str,
        choices=["cambridge", "springer", "mit", "harvard", "ams"],
        default="cambridge",
        help="Publisher house preset",
    )
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en", "ja", "fr", "zh"],
        default="en",
        help="Primary document language profile",
    )
    parser.add_argument(
        "--domain",
        type=str,
        choices=["math", "physics", "economics", "philosophy", "history", "novel"],
        default="math",
        help="Subject domain profile",
    )
    args = parser.parse_args()

    if args.export_web:
        from .web_exporter import export_all_web_data

        root_dir = Path(__file__).resolve().parents[1]
        web_pub = Path(__file__).resolve().parents[1] / "web" / "public"
        export_all_web_data(root_dir, web_pub)
        print(f"Exported web catalog and assets to {web_pub}")
        if not args.source:
            return

    if not args.source or not args.source.exists():
        print(f"Error: File {args.source} does not exist.")
        sys.exit(1)

    from .ocr.pages import OCRBackendError
    from .ocr.scan import SourceScanError
    from .pipeline import UniversalPDFPipeline

    pipeline = UniversalPDFPipeline(
        source=args.source,
        output_dir=args.output,
        backend=args.backend,
        publisher=args.publisher,
        lang=args.lang,
        domain=args.domain,
        pages=args.pages,
        retranscribe=args.retranscribe,
    )
    try:
        res = pipeline.process()
    except OCRBackendError as exc:
        sys.exit(f"OCR backend {args.backend} failed: {exc}")
    except SourceScanError as exc:
        sys.exit(f"Cannot read the source scan: {exc}")
    print(f"\n🎉 polytypst build complete! Master file: {res.master_markdown_path}")


if __name__ == "__main__":
    main()
