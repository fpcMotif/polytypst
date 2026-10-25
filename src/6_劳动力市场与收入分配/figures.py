"""Rebuild the figure crops whose panels run across two scan pages."""

from pathlib import Path

import pymupdf

from ..parity.source import source_pdf
from .spec import LABOR_SPEC

# Each box is (left, top, right, bottom) as fractions of the scan page.
Box = tuple[float, float, float, float]

# 图 13-4 prints panel (a) and the legend one page before panels (b) and (c), so its crop stacks both.
STACKED: dict[str, tuple[tuple[int, Box], ...]] = {
    "13-4": ((415, (0.12, 0.5, 0.88, 0.79)), (416, (0.12, 0.11, 0.87, 0.58))),
}
# 图 10-26 prints panels (1) and (2) one page before panel (3) and the caption. Stacked, it would print
# at half width, so panels (1) and (2) become an uncaptioned image on the page before.
SPLIT: dict[str, tuple[int, Box]] = {
    "10-26": (340, (0.13, 0.1, 0.79, 0.632)),
    "10-26-panels": (339, (0.12, 0.33, 0.83, 0.855)),
}
UNCAPTIONED = ("10-26-panels",)

FIGURE_DPI = 600
SCAN_TEXT_WIDTH_PT = 356
BOOK_TEXT_WIDTH_PT = 330
# Markdown images print at width_px / 300 * 72 pt, so this dpi keeps a panel's scan share of the line.
UNCAPTIONED_DPI = round(300 * BOOK_TEXT_WIDTH_PT / SCAN_TEXT_WIDTH_PT)


def figure_path(out_dir: Path, name: str) -> Path:
    return out_dir / "figures" / f"fig_{name}.png"


def _crop(scan: pymupdf.Document, page_number: int, box: Box, dpi: int) -> pymupdf.Pixmap:
    page = scan[page_number - 1]
    r = page.rect
    clip = pymupdf.Rect(r.width * box[0], r.height * box[1], r.width * box[2], r.height * box[3])
    return page.get_pixmap(dpi=dpi, clip=clip, colorspace=pymupdf.csGRAY)


def _stack(parts: list[pymupdf.Pixmap]) -> pymupdf.Pixmap:
    width = max(p.width for p in parts)
    sheet = pymupdf.open()
    page = sheet.new_page(width=width, height=sum(p.height for p in parts))
    top = 0
    for p in parts:
        left = (width - p.width) / 2
        page.insert_image(pymupdf.Rect(left, top, left + p.width, top + p.height), pixmap=p)
        top += p.height
    return page.get_pixmap(dpi=72, colorspace=pymupdf.csGRAY)


def crop_cross_page_figures(out_dir: Path, source: Path | None) -> None:
    scan = pymupdf.open(source_pdf(LABOR_SPEC, source))
    for name, parts in STACKED.items():
        _stack([_crop(scan, page, box, FIGURE_DPI) for page, box in parts]).save(figure_path(out_dir, name))
    for name, (page, box) in SPLIT.items():
        dpi = UNCAPTIONED_DPI if name in UNCAPTIONED else FIGURE_DPI
        _crop(scan, page, box, dpi).save(figure_path(out_dir, name))
