"""High-precision 300-DPI diagram cropper for Kunihiko Kodaira's Complex Analysis.

Locates every standalone `Fig. X.Y` caption across all pages and crops the diagram
above each caption using horizontal whitespace band isolation and tight ink bounding boxes.
"""

from pathlib import Path

from polytypst.kodaira.spec import KODAIRA_SPEC
from polytypst.parity.source import sources_dir
from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    FigureExtractor,
    write_figures_manifest,
)

KODAIRA_PDF = "Complex Analysis ( etc.).pdf"

KODAIRA_BODY_PAGES = range(12, 413)


def extract_all_kodaira_figures(
    pdf_path: Path,
    renders_dir: Path,
    figs_dir: Path,
) -> list[ExtractedFigure]:
    extracted = FigureExtractor(pdf_path).extract_whitespace_isolated_figures(
        renders_dir, figs_dir, renders_dir.parent / KODAIRA_SPEC.markdown_dir, pages=KODAIRA_BODY_PAGES
    )
    write_figures_manifest(figs_dir.parent / FIGURES_MANIFEST_NAME, extracted)
    print(f"Extracted {len(extracted)} figures to {figs_dir}")
    return extracted


if __name__ == "__main__":
    extract_all_kodaira_figures(
        pdf_path=sources_dir(KODAIRA_PDF) / KODAIRA_PDF,
        renders_dir=Path("output/kodaira/page_renders"),
        figs_dir=Path("output/kodaira/figures"),
    )
