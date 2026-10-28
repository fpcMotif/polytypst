"""Redrawn vector figures placed on a facsimile page where the scan prints its figure art.

Each figure's SVG is fitted ink box to ink box: the ink the SVG draws is scaled onto the ink the scan prints inside the
figure's box. A figure the scan prints over several page bands is cut into slices of its upright drawing, one per band,
in proportion to the bands' ink; a band printed sideways takes its slice turned.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf

from .ocr.pages import OcrLine
from .parity.words import PT_PER_PX, page_ink

GAP_MIN_PX = 4
GAP_SNAP = 0.25
GAP_TIE = 0.9


@dataclass(frozen=True)
class FigureArt:
    """One figure's redrawn SVG, or one band of it, for a box on a scan page (page fractions l, t, r, b).
    `turn` is the rotation that brings the band upright, as in the figure extractor (-90 for a sideways band)."""

    figure_id: str
    box: tuple[float, float, float, float]
    svg: Path
    turn: int = 0


@dataclass(frozen=True)
class Placed:
    art: FigureArt
    ink: tuple[float, float, float, float]
    start: float
    end: float


def ink_box(ink: np.ndarray, box: tuple[float, float, float, float]) -> tuple[float, float, float, float] | None:
    """The tight ink box (pt) inside a box given in page fractions, or None when it is blank."""
    h, w = ink.shape
    y0, y1, x0, x1 = int(box[1] * h), int(box[3] * h), int(box[0] * w), int(box[2] * w)
    ys, xs = np.nonzero(ink[y0:y1, x0:x1])
    if not ys.size:
        return None
    return ((x0 + xs.min()) * PT_PER_PX, (y0 + ys.min()) * PT_PER_PX, (x0 + xs.max() + 1) * PT_PER_PX, (y0 + ys.max() + 1) * PT_PER_PX)


def without_lines(ink: np.ndarray, lines: Sequence[OcrLine], pattern: re.Pattern[str]) -> np.ndarray:
    """The page ink less the ink inside the OCR lines whose text matches `pattern`, such as a figure's caption."""
    h, w = ink.shape
    out = ink.copy()
    for ln in lines:
        if pattern.match(ln.text):
            out[int((1 - ln.y - ln.h) * h) : int((1 - ln.y) * h) + 1, int(ln.x * w) : int((ln.x + ln.w) * w) + 1] = False
    return out


def svg_ink(svg: Path, ink: np.ndarray | None = None) -> tuple[float, float, float, float, float, float]:
    """The SVG's size and the ink box its drawing covers, in its own units: (width, height, l, t, r, b).
    `ink` is the drawing's `page_ink` when the caller already has it."""
    ink = page_ink(pymupdf.open(svg)[0]) if ink is None else ink
    width, height = svg_size(svg)
    box = ink_box(ink, (0.0, 0.0, 1.0, 1.0)) or (0.0, 0.0, width, height)
    return (width, height, *box)


def svg_size(svg: Path) -> tuple[float, float]:
    """The SVG page's width and height in points.
    MuPDF bounds the page directly, because `pymupdf.open` first converts an SVG to PDF, about 0.2 s each."""
    bound = pymupdf.mupdf.fz_bound_page(pymupdf.mupdf.fz_load_page(pymupdf.mupdf.fz_open_document(str(svg)), 0))
    return bound.x1 - bound.x0, bound.y1 - bound.y0


def drawing_gaps(svg: Path, ink: np.ndarray | None = None) -> list[tuple[float, float]]:
    """The middle and height of each blank row band inside the SVG's drawing, such as between two panels, as
    fractions of its ink height. `ink` is the drawing's `page_ink` when the caller already has it."""
    ink = page_ink(pymupdf.open(svg)[0]) if ink is None else ink
    rows = np.flatnonzero(ink.any(axis=1))
    if not rows.size:
        return []
    top, bottom = rows[0], rows[-1] + 1
    blank = ~ink[top:bottom].any(axis=1)
    gaps, start = [], None
    for y, empty in enumerate([*blank, False]):
        if empty and start is None:
            start = y
        elif not empty and start is not None:
            if y - start >= GAP_MIN_PX:
                gaps.append(((start + y) / 2 / (bottom - top), (y - start) / (bottom - top)))
            start = None
    return gaps


def slices(
    arts: dict[int, list[FigureArt]],
    scan_ink: dict[int, np.ndarray],
    gaps: dict[Path, list[tuple[float, float]]] | None = None,
) -> dict[int, list[Placed]]:
    """Each page's figure bands with the scan's ink box and the slice of the upright drawing it shows (fractions of
    the drawing's ink height), bands of one figure taken in page order. A cut moves to the widest of the drawing's
    `gaps` within `GAP_SNAP`, so a figure split across pages breaks between its panels."""
    by_figure: dict[str, list[tuple[int, FigureArt, tuple[float, float, float, float]]]] = {}
    for page in sorted(arts):
        for art in arts[page]:
            if (box := ink_box(scan_ink[page], art.box)) is not None:
                by_figure.setdefault(art.figure_id, []).append((page, art, box))
    out: dict[int, list[Placed]] = {}
    for bands in by_figure.values():
        tall = [(b[2] - b[0]) if art.turn else (b[3] - b[1]) for _, art, b in bands]
        start = 0.0
        for k, ((page, art, box), h) in enumerate(zip(bands, tall)):
            end = start + h / sum(tall) if k < len(bands) - 1 else 1.0
            near = [(g, size) for g, size in (gaps or {}).get(art.svg, []) if start < g < 1 and abs(g - end) <= GAP_SNAP]
            if k < len(bands) - 1 and near:
                widest = max(size for _, size in near)
                end = min((g for g, size in near if size >= GAP_TIE * widest), key=lambda g: abs(g - end))
            out.setdefault(page, []).append(Placed(art, box, start, end))
            start = end
    return out


def gray_svg(svg: Path, out: Path) -> Path:
    """A copy of the SVG with every hex colour turned to the gray of its lightness, as the scan prints in black ink.
    An unchanged copy is left as it is, so its change time keys the cached ink of its drawing."""

    def gray(m: re.Match[str]) -> str:
        h = m[1] if len(m[1]) == 6 else "".join(c * 2 for c in m[1])
        r, g, b = (int(h[k : k + 2], 16) for k in (0, 2, 4))
        return "#{0:02x}{0:02x}{0:02x}".format(round(0.299 * r + 0.587 * g + 0.114 * b))

    text = re.sub(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", gray, svg.read_text(encoding="utf-8"))
    if not out.exists() or out.read_text(encoding="utf-8") != text:
        out.write_text(text, encoding="utf-8")
    return out


def figure_typst(placed: Placed, drawing: Sequence[float], svg: Path) -> str:
    """Typst stretching the slice of a figure's drawing `svg` onto the scan's ink box, turned for a sideways band."""
    sw, sh, sl, st, sr, sb = drawing
    l, t, r, b = placed.ink
    width, height = (b - t, r - l) if placed.art.turn else (r - l, b - t)
    top = st + placed.start * (sb - st)
    tall = (placed.end - placed.start) * (sb - st)
    sx, sy = width / (sr - sl), height / tall
    dx, dy = (width - (sr - sl) * sx) / 2 - sl * sx, (height - tall * sy) / 2 - top * sy
    art = (
        f"#box(width: {width:.2f}pt, height: {height:.2f}pt, clip: true)[#place(top + left, dx: {dx:.2f}pt, "
        f'dy: {dy:.2f}pt, image("{svg.resolve()}", width: {sw * sx:.2f}pt, height: {sh * sy:.2f}pt, fit: "stretch"))]'
    )
    if placed.art.turn:
        return f"#place(top + left, dx: {l:.2f}pt, dy: {b:.2f}pt, rotate(-90deg, origin: top + left)[{art}])"
    return f"#place(top + left, dx: {l:.2f}pt, dy: {t:.2f}pt)[{art}]"
