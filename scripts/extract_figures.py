"""High-precision 300-DPI diagram cropper for a book whose figures stand above `Fig. X.Y` captions.

Locates every standalone `Fig. X.Y` caption across the given pages and crops the diagram
above each caption using horizontal whitespace band isolation and tight ink bounding boxes.

Usage: uv run python scripts/extract_figures.py KEY SCAN FIRST LAST
(Kodaira: kodaira "Complex Analysis ( etc.).pdf" 12 412)
"""

import sys
from pathlib import Path

from polytypst.books import book_by_key
from polytypst.parity.source import sources_dir
from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    FigureExtractor,
    write_figures_manifest,
)


def extract_all_figures(
    pdf_path: Path,
    renders_dir: Path,
    figs_dir: Path,
    transcripts: Path,
    pages: range,
) -> list[ExtractedFigure]:
    extracted = FigureExtractor(pdf_path).extract_whitespace_isolated_figures(
        renders_dir, figs_dir, transcripts, pages=pages
    )
    write_figures_manifest(figs_dir.parent / FIGURES_MANIFEST_NAME, extracted)
    print(f"Extracted {len(extracted)} figures to {figs_dir}")
    return extracted


if __name__ == "__main__":
    key, scan, first, last = sys.argv[1:5]
    book = book_by_key(key)
    extract_all_figures(
        pdf_path=sources_dir(scan) / scan,
        renders_dir=book.out_dir / "page_renders",
        figs_dir=book.out_dir / "figures",
        transcripts=book.transcripts,
        pages=range(int(first), int(last) + 1),
    )
