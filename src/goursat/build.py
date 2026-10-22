"""Convert Goursat's Course in Mathematical Analysis: figures, OCR, stitching, and vector art."""

import argparse
from pathlib import Path

from ..ocr.backend import Backend, backend_argument
from ..ocr.lines import LineStore
from ..ocr.pages import LinePage, PageImage, Transcriber, page_images
from ..ocr.transcripts import TranscriptStore
from ..tex_markdown import stitch_document
from ..vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    FigureExtractor,
    load_complete_figures_manifest,
    write_figures_manifest,
)
from .figures import (
    export_goursat_figures,
    export_goursat_web_gallery,
    normalize_goursat_markdown,
)

GOURSAT_LAST_TEXT_PAGE = 553
GOURSAT_RUNNING_HEADERS = (
    "A COURSE IN MATHEMATICAL ANALYSIS",
    "DERIVATIVES AND DIFFERENTIALS",
    "IMPLICIT FUNCTIONS",
    "FUNCTIONAL DETERMINANTS",
    "CHANGE OF VARIABLE",
    "SERIES",
    "DEFINITE INTEGRALS",
    "APPLICATIONS TO GEOMETRY",
)


def _figures(
    pdf_path: Path, out_dir: Path, renders: list[PageImage]
) -> list[ExtractedFigure]:
    manifest_path = out_dir / FIGURES_MANIFEST_NAME
    cached = load_complete_figures_manifest(manifest_path)
    if cached is not None:
        return cached
    extractor = FigureExtractor(pdf_path)
    lines = LineStore(out_dir / "source_ocr").read(renders, extractor.reader)
    ocr_pages = [LinePage(number, page_lines) for number, page_lines in lines.items()]
    figures = extractor.extract_figures_from_ocr_pages(
        ocr_pages, out_dir / "figures", dpi=300
    )
    write_figures_manifest(manifest_path, figures)
    return figures


def build_goursat(pdf_path: Path, out_dir: Path, transcriber: Transcriber) -> Path:
    """Write `book.md`, the vector figures, and the web gallery into `out_dir`."""
    pages = page_images(out_dir / "page_renders")
    figures = _figures(pdf_path, out_dir, pages)
    print(f"{len(figures)} figures grounded.")

    text_pages = [p for p in pages if p.number <= GOURSAT_LAST_TEXT_PAGE]
    store = TranscriptStore(out_dir / "markdown_pages")
    pages_md = store.transcribe(text_pages, transcriber)
    print(f"{len(pages_md)}/{len(text_pages)} pages transcribed.")

    master_md = normalize_goursat_markdown(
        stitch_document(
            sorted(pages_md.items()),
            figures=figures,
            running_headers=list(GOURSAT_RUNNING_HEADERS),
        )
    )
    master_path = out_dir / "book.md"
    _ = master_path.write_text(master_md, encoding="utf-8")
    svgs = export_goursat_figures(out_dir / "figures")
    gallery = export_goursat_web_gallery(out_dir / "web_figures")
    print(f"{len(svgs)} vector figures; gallery at {gallery}")
    return master_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("pdf", type=Path)
    _ = parser.add_argument("--out", type=Path, default=Path("output/goursat_colab"))
    _ = parser.add_argument(
        "--backend",
        type=backend_argument,
        default=Backend.parse("colab?session=goursat"),
        help="OCR backend as KIND[:MODEL][?KEY=VALUE&...], as in `polytypst --backend`",
    )
    args = parser.parse_args()
    path = build_goursat(args.pdf, args.out, args.backend.transcriber(None))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
