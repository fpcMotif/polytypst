"""Convert Goursat's Course in Mathematical Analysis: figures, OCR, stitching, and vector art."""

import argparse
from pathlib import Path

from ..ocr.apple_vision import AppleVisionOCREngine
from ..ocr.base import OCREngine, page_number
from ..ocr.colab import COLAB_GPUS
from ..ocr.engines import OCR_MODES, ocr_engine
from ..ocr.ocr_models import DEFAULT_OCR_MODEL, OCR_MODELS
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
    pdf_path: Path, out_dir: Path, renders: list[Path]
) -> list[ExtractedFigure]:
    manifest_path = out_dir / FIGURES_MANIFEST_NAME
    cached = load_complete_figures_manifest(manifest_path)
    if cached is not None:
        return cached
    ocr_pages = AppleVisionOCREngine(languages=["en-US"]).recognize_document(renders)
    figures = FigureExtractor(pdf_path).extract_figures_from_ocr_pages(
        ocr_pages, out_dir / "figures", dpi=300
    )
    write_figures_manifest(manifest_path, figures)
    return figures


def build_goursat(pdf_path: Path, out_dir: Path, engine: OCREngine) -> Path:
    """Write `book.md`, the vector figures, and the web gallery into `out_dir`."""
    renders = sorted((out_dir / "page_renders").glob("*.png"))
    figures = _figures(pdf_path, out_dir, renders)
    print(f"{len(figures)} figures grounded.")

    text_pages = [p for p in renders if page_number(p) <= GOURSAT_LAST_TEXT_PAGE]
    pages_md = engine.transcribe_pages(text_pages, out_dir / "markdown_pages")
    print(f"{len(pages_md)}/{len(text_pages)} pages transcribed.")

    master_md = normalize_goursat_markdown(
        stitch_document(
            pages_md, figures=figures, running_headers=list(GOURSAT_RUNNING_HEADERS)
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
    _ = parser.add_argument("--mode", choices=OCR_MODES, default="colab")
    _ = parser.add_argument(
        "--model", choices=sorted(OCR_MODELS), default=DEFAULT_OCR_MODEL
    )
    _ = parser.add_argument("--gpu", choices=sorted(COLAB_GPUS), default="G4")
    _ = parser.add_argument("--cache-dir", type=Path)
    _ = parser.add_argument("--batch-size", type=int, default=70)
    args = parser.parse_args()
    engine = ocr_engine(
        args.mode,
        model=args.model,
        gpu_type=args.gpu,
        session_prefix="goursat",
        batch_size=args.batch_size,
        cache_dir=args.cache_dir,
        languages=["en-US"],
    )
    path = build_goursat(args.pdf, args.out, engine)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
