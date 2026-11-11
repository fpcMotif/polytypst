"""One PNG that sets regions of PDF pages side by side, labelled, for an agent to compare in one look.

Each row of panels is scaled to one height, so a scan line and its rebuilt line sit at the same size.
White margins are trimmed, a ruler at each panel's left edge gives page shares for a crop box, and
the whole sheet fits SHEET_LIMIT pixels, the largest image a vision model reads without shrinking it.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont

Box = tuple[float, float, float, float]
SHEET_LIMIT = 1568
MAX_DPI = 400
INK = 200
PAD = 6
GAP = 12
LABEL = 26
RULER = 30


@dataclass(frozen=True)
class Panel:
    """Region `shares` (L,T,R,B as shares of the page) of 1-based `page` of `pdf`, titled `label`."""

    label: str
    pdf: Path
    page: int
    shares: Box = (0.0, 0.0, 1.0, 1.0)

    def __post_init__(self) -> None:
        with pymupdf.open(self.pdf) as doc:
            count = doc.page_count
        if not 1 <= self.page <= count:
            raise ValueError(
                f"{self.label}: page {self.page} does not exist; {self.pdf.name} has {count} pages (1-based)"
            )


@dataclass(frozen=True)
class _Drawn:
    image: Image.Image
    label: str
    shares: Box


def _render(panel: Panel, dpi: float) -> _Drawn:
    page = pymupdf.open(panel.pdf)[panel.page - 1]
    r = page.rect
    left, top, right, bottom = panel.shares
    clip = pymupdf.Rect(
        r.x0 + left * r.width,
        r.y0 + top * r.height,
        r.x0 + right * r.width,
        r.y0 + bottom * r.height,
    )
    pix = page.get_pixmap(dpi=round(dpi), clip=clip)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return _trim(_Drawn(image, panel.label, panel.shares))


def _trim(drawn: _Drawn) -> _Drawn:
    """Cut the white margin around the ink, and narrow `shares` to the part that is kept."""
    ink = np.asarray(drawn.image.convert("L")) < INK
    ys, xs = np.nonzero(ink)
    if not len(xs):
        return drawn
    w, h = drawn.image.size
    x0, y0 = max(xs.min() - PAD, 0), max(ys.min() - PAD, 0)
    x1, y1 = min(xs.max() + PAD + 1, w), min(ys.max() + PAD + 1, h)
    left, top, right, bottom = drawn.shares
    sw, sh = (right - left) / w, (bottom - top) / h
    return _Drawn(
        drawn.image.crop((x0, y0, x1, y1)),
        drawn.label,
        (left + x0 * sw, top + y0 * sh, left + x1 * sw, top + y1 * sh),
    )


def _fit_dpi(row: list[Panel]) -> float:
    """The dpi at which the row's panels, side by side, fill the sheet width, capped at MAX_DPI."""
    width_in = 0.0
    for panel in row:
        rect = pymupdf.open(panel.pdf)[panel.page - 1].rect
        width_in += rect.width * (panel.shares[2] - panel.shares[0]) / 72
    room = SHEET_LIMIT - len(row) * (RULER + GAP) - GAP
    return min(MAX_DPI, room / width_in)


def _scaled_row(drawn: list[_Drawn]) -> list[_Drawn]:
    height = max(d.image.height for d in drawn)
    width = sum(d.image.width * height / d.image.height for d in drawn)
    room = SHEET_LIMIT - len(drawn) * (RULER + GAP) - GAP
    height = min(height, round(height * room / width))
    return [
        _Drawn(
            d.image.resize(
                (max(1, round(d.image.width * height / d.image.height)), height),
                Image.LANCZOS,
            ),
            d.label,
            d.shares,
        )
        for d in drawn
    ]


def _ruler(draw: ImageDraw.ImageDraw, x: int, y: int, d: _Drawn, font) -> None:
    """Ticks at each tenth of the page height that the panel shows, labelled with the share."""
    _, top, _, bottom = d.shares
    for tenth in range(11):
        share = tenth / 10
        if not top <= share <= bottom:
            continue
        ty = y + round((share - top) / (bottom - top) * (d.image.height - 1))
        draw.line((x + RULER - 8, ty, x + RULER - 1, ty), fill=(200, 30, 30), width=2)
        draw.text(
            (x, ty - 7),
            f"{share:.1f}"[1:] if share < 1 else "1",
            fill=(200, 30, 30),
            font=font,
        )


def write_sheet(rows: list[list[Panel]], out: Path, dpi: float | None = None) -> Path:
    """Write `rows` to `out` as one labelled PNG at most SHEET_LIMIT pixels on a side.

    Without `dpi`, each row renders at the dpi that fills the sheet width, so a narrow box zooms in."""
    drawn = [
        _scaled_row([_render(p, dpi or _fit_dpi(row)) for p in row]) for row in rows
    ]
    width = max(sum(d.image.width + RULER + GAP for d in row) + GAP for row in drawn)
    height = sum(LABEL + row[0].image.height + GAP for row in drawn) + GAP
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    font, small = ImageFont.load_default(size=18), ImageFont.load_default(size=12)
    y = GAP
    for row in drawn:
        x = GAP
        for d in row:
            draw.text((x + RULER, y + 3), d.label, fill="black", font=font)
            sheet.paste(d.image, (x + RULER, y + LABEL))
            draw.rectangle(
                (
                    x + RULER - 1,
                    y + LABEL - 1,
                    x + RULER + d.image.width,
                    y + LABEL + d.image.height,
                ),
                outline=(150, 150, 150),
            )
            _ruler(draw, x, y + LABEL, d, small)
            x += d.image.width + RULER + GAP
        y += LABEL + row[0].image.height + GAP
    if max(sheet.size) > SHEET_LIMIT:
        scale = SHEET_LIMIT / max(sheet.size)
        sheet = sheet.resize(
            (round(sheet.width * scale), round(sheet.height * scale)), Image.LANCZOS
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    return out
