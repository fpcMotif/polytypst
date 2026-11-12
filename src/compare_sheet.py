"""One PNG that sets regions of PDF pages side by side, labelled, for an agent to compare in one look.

Each row of panels is scaled to one height, so a scan line and its rebuilt line sit at the same size.
White margins are trimmed, a ruler at each panel's left edge gives page shares for a crop box, and
the whole sheet fits SHEET_LIMIT pixels, the largest image a vision model reads without shrinking it.
"""

import shutil
import subprocess
import unicodedata
from dataclasses import dataclass, replace
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
GREY = "#969696"
MARK = "#dc1e1e"
DIFF_DPI = 200
DIFF_CELL = 24
FRAMES = ("#d01818", "#108a30", "#1858d0")
TEXT_PAGE = """#set page(width: auto, height: auto, margin: 6pt)
#set text(size: 14pt)
#read("text.txt")
"""


@dataclass(frozen=True)
class Panel:
    """Region `shares` (L,T,R,B as shares of the page) of 1-based `page` of `pdf`, titled `label`.

    `pdf` is a PDF, or an SVG or image file, which counts as one page.
    Each box in `marks`, in shares of the page, is drawn in red on the panel."""

    label: str
    pdf: Path
    page: int
    shares: Box = (0.0, 0.0, 1.0, 1.0)
    marks: tuple[Box, ...] = ()

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
    source: tuple[Path, int]
    marks: tuple[Box, ...] = ()


def _letters(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text).casefold() if c.isalnum() or c.isspace())


def _line_rect(page: pymupdf.Page, text: str) -> pymupdf.Rect | None:
    hits = page.search_for(text)
    if hits:
        return hits[0]
    wanted = _letters(text).split()
    lines: dict[tuple[int, int], list] = {}
    for word in page.get_text("words"):
        lines.setdefault((word[5], word[6]), []).append(word)
    for words in lines.values():
        have = _letters(" ".join(w[4] for w in words))
        if wanted and all(token in have for token in wanted):
            return pymupdf.Rect(
                min(w[0] for w in words), min(w[1] for w in words), max(w[2] for w in words), max(w[3] for w in words)
            )
    return None


def find_text(
    pdf: Path, text: str, page: int | None = None, pad: tuple[float, float] = (0.05, 1.0)
) -> tuple[int, Box] | None:
    """The first 1-based page of `pdf` whose text layer holds `text`, and the box round that line.

    A line holds `text` as a phrase, or holds every word of it. `pad` widens the box by shares of the
    page, up and down, then left and right. `page` keeps the search to one page."""
    with pymupdf.open(pdf) as doc:
        for number in [page] if page else range(1, doc.page_count + 1):
            sheet = doc[number - 1]
            hit = _line_rect(sheet, text)
            if hit is None:
                continue
            r = sheet.rect
            return number, (
                max(0.0, (hit.x0 - r.x0) / r.width - pad[1]),
                max(0.0, (hit.y0 - r.y0) / r.height - pad[0]),
                min(1.0, (hit.x1 - r.x0) / r.width + pad[1]),
                min(1.0, (hit.y1 - r.y0) / r.height + pad[0]),
            )
    return None


def text_pdf(text: str, out: Path) -> Path:
    """`text` set by Typst on a page of its own size at `out`, to hold a candidate reading beside a scan."""
    found = shutil.which("typst")
    typst = [found] if found else ["mise", "exec", "--", "typst"]
    out.parent.mkdir(parents=True, exist_ok=True)
    (out.parent / "text.txt").write_text(text, encoding="utf-8")
    source = out.with_suffix(".typ")
    source.write_text(TEXT_PAGE, encoding="utf-8")
    subprocess.run([*typst, "compile", source.name, out.name], cwd=out.parent, check=True)
    return out


def share_rect(rect: pymupdf.Rect, shares: Box) -> pymupdf.Rect:
    """The part of `rect` that `shares` (L,T,R,B as shares of it) names."""
    left, top, right, bottom = shares
    return pymupdf.Rect(
        rect.x0 + left * rect.width,
        rect.y0 + top * rect.height,
        rect.x0 + right * rect.width,
        rect.y0 + bottom * rect.height,
    )


def _raw(panel: Panel, dpi: float) -> Image.Image:
    page = pymupdf.open(panel.pdf)[panel.page - 1]
    pix = page.get_pixmap(dpi=round(dpi), clip=share_rect(page.rect, panel.shares), alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _render(panel: Panel, dpi: float) -> _Drawn:
    return _trim(_Drawn(_raw(panel, dpi), panel.label, panel.shares, (panel.pdf, panel.page), panel.marks))


def _changed_cells(a: Image.Image, b: Image.Image) -> list[tuple[int, int, int, int]]:
    """Boxes around the DIFF_CELL-pixel grid cells whose ink differs, joined where cells touch."""
    w, h = min(a.width, b.width), min(a.height, b.height)
    ink_a = np.asarray(a.convert("L").crop((0, 0, w, h))) < 160
    ink_b = np.asarray(b.convert("L").crop((0, 0, w, h))) < 160
    rows, cols = h // DIFF_CELL, w // DIFF_CELL
    changed = (ink_a ^ ink_b)[: rows * DIFF_CELL, : cols * DIFF_CELL].reshape(rows, DIFF_CELL, cols, DIFF_CELL).sum(
        axis=(1, 3)
    ) > 8
    seen = np.zeros_like(changed)
    boxes = []
    for r, c in zip(*np.nonzero(changed), strict=True):
        if seen[r, c]:
            continue
        stack, cells = [(r, c)], []
        seen[r, c] = True
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for ny in range(max(0, y - 1), min(rows, y + 2)):
                for nx in range(max(0, x - 1), min(cols, x + 2)):
                    if changed[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        ys, xs = zip(*cells, strict=True)
        boxes.append((min(xs) * DIFF_CELL, min(ys) * DIFF_CELL, (max(xs) + 1) * DIFF_CELL, (max(ys) + 1) * DIFF_CELL))
    return boxes


def diff_marks(a: Panel, b: Panel) -> tuple[list[Box], list[Box]]:
    """Boxes round the places where the ink of `a` and `b` differs once both stand at one height.

    The first list is in page shares of `a` and the second of `b`, ready for each panel's `marks`."""
    image_a, image_b = _raw(a, DIFF_DPI), _raw(b, DIFF_DPI)
    image_b = image_b.resize((max(1, round(image_b.width * image_a.height / image_b.height)), image_a.height))
    cells = _changed_cells(image_a, image_b)

    def on_page(panel: Panel, image: Image.Image) -> list[Box]:
        left, top, right, bottom = panel.shares
        sw, sh = (right - left) / image.width, (bottom - top) / image.height
        return [(left + x0 * sw, top + y0 * sh, left + x1 * sw, top + y1 * sh) for x0, y0, x1, y1 in cells]

    return on_page(a, image_a), on_page(b, image_b)


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
    return replace(
        drawn,
        image=drawn.image.crop((x0, y0, x1, y1)),
        shares=(left + x0 * sw, top + y0 * sh, left + x1 * sw, top + y1 * sh),
    )


def _room(panels: int, limit: int) -> int:
    return limit - panels * (RULER + GAP) - GAP


def _fit_dpi(row: list[Panel], limit: int, max_dpi: int) -> float:
    """The dpi at which the row's panels, side by side, fill the sheet width, capped at `max_dpi`."""
    width_in = 0.0
    for panel in row:
        rect = pymupdf.open(panel.pdf)[panel.page - 1].rect
        width_in += rect.width * (panel.shares[2] - panel.shares[0]) / 72
    return min(max_dpi, _room(len(row), limit) / width_in)


def _scaled_row(drawn: list[_Drawn], limit: int) -> list[_Drawn]:
    height = max(d.image.height for d in drawn)
    width = sum(d.image.width * height / d.image.height for d in drawn)
    height = min(height, round(height * _room(len(drawn), limit) / width), limit - LABEL - 2 * GAP)
    return [
        replace(
            d,
            image=d.image.resize(
                (max(1, round(d.image.width * height / d.image.height)), height),
                Image.Resampling.LANCZOS,
            ),
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


def _row_height(row: list[_Drawn]) -> int:
    return LABEL + row[0].image.height + GAP


def _compose(rows: list[list[_Drawn]], colours: list[str | None]) -> Image.Image:
    width = max(sum(d.image.width + RULER + GAP for d in row) + GAP for row in rows)
    sheet = Image.new("RGB", (width, sum(map(_row_height, rows)) + GAP), "white")
    draw = ImageDraw.Draw(sheet)
    font, small = ImageFont.load_default(size=18), ImageFont.load_default(size=12)
    y = GAP
    for row, colour in zip(rows, colours, strict=True):
        x = GAP
        for d in row:
            label = d.label
            while len(label) > 1 and draw.textlength(label, font=font) > d.image.width:
                label = label[:-1]
            draw.text((x + RULER, y + 3), label, fill=colour or "black", font=font)
            sheet.paste(d.image, (x + RULER, y + LABEL))
            draw.rectangle(
                (
                    x + RULER - 1,
                    y + LABEL - 1,
                    x + RULER + d.image.width,
                    y + LABEL + d.image.height,
                ),
                outline=colour or GREY,
                width=3 if colour else 1,
            )
            left, top, right, bottom = d.shares
            sx, sy = d.image.width / (right - left), d.image.height / (bottom - top)
            for x0, y0, x1, y1 in d.marks:
                draw.rectangle(
                    (
                        x + RULER + max(0, round((x0 - left) * sx)),
                        y + LABEL + max(0, round((y0 - top) * sy)),
                        x + RULER + min(d.image.width - 1, round((x1 - left) * sx)),
                        y + LABEL + min(d.image.height - 1, round((y1 - top) * sy)),
                    ),
                    outline=MARK,
                    width=3,
                )
            _ruler(draw, x, y + LABEL, d, small)
            x += d.image.width + RULER + GAP
        y += _row_height(row)
    return sheet


def _frame_colours(rows: list[list[_Drawn]]) -> list[str | None]:
    colours: list[str | None] = []
    index = 0
    for n, row in enumerate(rows):
        if n and row[0].source != rows[n - 1][0].source:
            index += 1
        colours.append(FRAMES[index % len(FRAMES)])
    return colours


def _save(sheet: Image.Image, out: Path, limit: int, kb: int | None) -> Path:
    if max(sheet.size) > limit:
        scale = limit / max(sheet.size)
        sheet = sheet.resize((round(sheet.width * scale), round(sheet.height * scale)), Image.Resampling.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    if kb and out.stat().st_size > kb * 1024:
        sheet.quantize(64).save(out, optimize=True)
    while kb and out.stat().st_size > kb * 1024 and min(sheet.size) > 200:
        sheet = sheet.resize((round(sheet.width * 0.9), round(sheet.height * 0.9)), Image.Resampling.LANCZOS)
        sheet.quantize(64).save(out, optimize=True)
    return out


def write_sheets(
    rows: list[list[Panel]],
    out: Path,
    dpi: float | None = None,
    *,
    limit: int = SHEET_LIMIT,
    max_dpi: int = MAX_DPI,
    kb: int | None = None,
    frame: bool = False,
) -> list[Path]:
    """Write `rows` as labelled PNGs, each at most `limit` pixels on a side and `kb` kilobytes.

    A new sheet starts when the next row would pass `limit`, so no row shrinks to fit its neighbours.
    The sheets are `out`, or `out` with -1, -2 before its suffix when there are several.
    Without `dpi`, each row renders at the dpi that fills the sheet width, so a narrow box zooms in,
    up to `max_dpi`. `frame` draws a coloured frame round each panel, and the colour changes each
    time a row's first panel comes from another page, so rows from one page read as one group."""
    drawn = [_scaled_row([_render(p, dpi or _fit_dpi(row, limit, max_dpi)) for p in row], limit) for row in rows]
    colours: list[str | None] = _frame_colours(drawn) if frame else [None] * len(drawn)
    sheets: list[list[int]] = [[]]
    used = GAP
    for n, row in enumerate(drawn):
        if sheets[-1] and used + _row_height(row) > limit:
            sheets.append([])
            used = GAP
        sheets[-1].append(n)
        used += _row_height(row)
    return [
        _save(
            _compose([drawn[n] for n in members], [colours[n] for n in members]),
            out if len(sheets) == 1 else out.with_name(f"{out.stem}-{k}{out.suffix}"),
            limit,
            kb,
        )
        for k, members in enumerate(sheets, 1)
    ]


def write_sheet(rows: list[list[Panel]], out: Path, dpi: float | None = None) -> Path:
    """Write `rows` to `out` as one labelled PNG at most SHEET_LIMIT pixels on a side.

    Without `dpi`, each row renders at the dpi that fills the sheet width, so a narrow box zooms in."""
    drawn = [
        _scaled_row([_render(p, dpi or _fit_dpi(row, SHEET_LIMIT, MAX_DPI)) for p in row], SHEET_LIMIT)
        for row in rows
    ]
    return _save(_compose(drawn, [None] * len(drawn)), out, SHEET_LIMIT, None)
