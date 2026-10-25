"""Charts cropped from scan pages whose caption `图 X-Y title` sits under the chart, as in Chinese economics books.

A chart fills the band between the last body-text line above its caption and the caption itself,
less the small-font notes (注、资料来源) printed between chart and caption. Nothing inside the band is erased.
A caption printed sideways marks a landscape page: the whole text block is the chart, turned upright."""

import re
import statistics
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from ..ocr.pages import OcrLine, PageImage
from .figure_extractor import ExtractedFigure

CAPTION = re.compile(
    r"^\s*图\s*(\d+)\s*[-—–－‑一]\s*(\d+(?:\.\d+)?(?:[A-Z](?![A-Za-z]))?)\s*(.*)$"
)
TRANSCRIPT_CAPTION = re.compile(
    r"(?m)^(?:\*\*)?图\s*(\d+)\s*[-—–－]\s*(\d+(?:\.\d+)?(?:[A-Z](?![A-Za-z]))?)(?![\d.])"
)
NOTE = re.compile(
    r"^\s*[（(［\[]?\s*(?:[注往汪][：:]|注|资料来源|数据来源|出处|出典|来源)"
)
PROSE_AFTER_NUMBER = re.compile(
    r"(?:所示|显示|表明|报告|反映|列出|给出|描述|说明|展示|体现|归纳|总结|是|为|中|[（(、，。）)])"
)
HAN = re.compile(r"[一-鿿]")
TABLE = re.compile(r"^\s*(?:续表|表\s*\d+\s*[-—–－]\s*\d+)")
INK = 190
HEADER = 0.075
RUNNING_HEAD = 0.1
EARLIER_FIGURE_GAP = 0.1
FOOT = 0.93
TAIL_MIN = 0.15
TAIL_INK = 0.1
RULE_THICK = 0.002
FOOTNOTE_ZONE = 0.6
CHART_AT_TOP = HEADER + 0.03
SENTENCE_END = ("。", "！", "？", "；", "：", "，", ".")
PAD = 0.006


@dataclass(frozen=True)
class Row:
    """An OCR line in fractions of the page, with the origin at the top left."""

    text: str
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def sideways(self) -> bool:
        """Whether the line runs down the page, as a caption on a landscape page does."""
        return self.width < 0.04 and self.height > 1.5 * self.width


def _rows(lines: Sequence[OcrLine]) -> list[Row]:
    rows = [
        Row(l.text.strip(), l.x, 1.0 - (l.y + l.h), l.x + l.w, 1.0 - l.y)
        for l in lines
        if l.text.strip()
    ]
    return sorted(rows, key=lambda r: r.top)


@dataclass(frozen=True)
class Body:
    """The line height and left margin of a book's body text, as page fractions."""

    height: float
    left: float


def body_text(pages: Iterable[Sequence[Row]]) -> Body:
    lines = [
        r
        for rows in pages
        for r in rows
        if r.width > 0.6 and len(HAN.findall(r.text)) >= 15
    ]
    if not lines:
        return Body(0.02, 0.12)
    return Body(
        statistics.median(r.height for r in lines),
        statistics.median(r.left for r in lines),
    )


def captions(rows: Sequence[Row], body: Body) -> dict[int, re.Match[str]]:
    """The caption match of each caption row, by index, leaving out prose that mentions a figure ("图1-1所示为…").

    Prose starts at the body margin or runs on into a line there; a caption is centred and stands alone."""
    found: dict[int, re.Match[str]] = {}
    for i, row in enumerate(rows):
        m = CAPTION.match(row.text)
        if m is None:
            continue
        if row.sideways:
            found[i] = m
            continue
        follower = next((s for s in rows[i + 1 :] if s.top > row.top + 0.005), None)
        runs_on = (
            follower is not None
            and follower.top - row.bottom < 0.012
            and abs(follower.left - body.left) < 0.015
            and follower.width > 0.6
            and not NOTE.match(follower.text)
        )
        prose = (
            PROSE_AFTER_NUMBER.match(m.group(3))
            or row.text.endswith(SENTENCE_END)
            or (abs(row.left - body.left) < 0.015 and row.width > 0.3)
            or runs_on
        )
        if row.width < 0.8 and not prose:
            found[i] = m
    return found


def _note_rows(
    rows: Sequence[Row], caps: Mapping[int, re.Match[str]], body: Body
) -> set[int]:
    """Indices of note rows: each 注 or 资料来源 line and the small-font lines that continue it."""
    notes: set[int] = set()
    for i, r in enumerate(rows):
        if NOTE.match(r.text):
            notes.add(i)
            prev = r
            for j in range(i + 1, len(rows)):
                s = rows[j]
                small = s.height < 0.9 * body.height
                if (
                    s.top - prev.bottom > 0.012
                    or j in caps
                    or NOTE.match(s.text)
                    or not small
                ):
                    break
                notes.add(j)
                prev = s
    return notes


def _ink_box(
    gray: np.ndarray, top: int, bottom: int, left: int, right: int
) -> tuple[int, int, int, int] | None:
    """Tight (left, top, right, bottom) box of the ink in a region, ignoring rows and columns of scattered specks."""
    ink = gray[top:bottom, left:right] < INK
    rows = np.flatnonzero(ink.sum(axis=1) > 3)
    cols = np.flatnonzero(ink.sum(axis=0) > 3)
    if rows.size == 0 or cols.size == 0:
        return None
    return (
        left + int(cols[0]),
        top + int(rows[0]),
        left + int(cols[-1]) + 1,
        top + int(rows[-1]) + 1,
    )


def _is_prose(
    i: int,
    r: Row,
    body: Body,
    notes: Collection[int],
    caps: Mapping[int, re.Match[str]],
) -> bool:
    if i in notes or i in caps:
        return False
    indent = r.left - body.left
    if abs(indent) < 0.02 and r.text.endswith(SENTENCE_END):
        return True
    if r.height < 0.85 * body.height:
        return False
    sentence = len(HAN.findall(r.text)) >= 6 or r.text.endswith(SENTENCE_END)
    return sentence and (
        abs(indent) < 0.02 or (r.width > 0.5 and -0.02 < indent < 0.06)
    )


def tail_band(
    rows: Sequence[Row], body: Body
) -> tuple[float, float, float, float] | None:
    """The band below a page's last prose line that can hold the uncaptioned start of a chart continued on the next page."""
    caps = captions(rows, body)
    notes = _note_rows(rows, caps, body)
    top = HEADER
    for i, r in enumerate(rows):
        caption_line = any(
            r.top - rows[c].bottom < 0.01 and r.top >= rows[c].top for c in caps
        )
        running_head = r.top < RUNNING_HEAD and len(r.text) >= 4
        footnote = r.top > FOOTNOTE_ZONE and r.height < 0.9 * body.height
        text = not footnote and (i in notes or _is_prose(i, r, body, notes, caps))
        if r.top < FOOT and (i in caps or caption_line or running_head or text):
            top = max(top, r.bottom)
    if FOOT - top < TAIL_MIN:
        return None
    return 0.04, top, 0.96, FOOT


def _footnote_rule(ink: np.ndarray, body_left: int, max_thick: int) -> int | None:
    """The row of the short rule that opens the page's footnotes, as a thin line starting at the body margin."""
    h, w = ink.shape
    counts = ink.sum(axis=1)
    y = 0
    while y < h:
        if counts[y] == 0:
            y += 1
            continue
        end = y
        while end < h and counts[end] > 0:
            end += 1
        cols = np.flatnonzero(ink[y:end].any(axis=0))
        if (
            end - y <= max_thick
            and cols[-1] - cols[0] < 0.35 * w
            and abs(int(cols[0]) - body_left) < 0.05 * w
            and counts[y:end].max() > 0.1 * w
        ):
            return y
        y = end
    return None


def chart_tail(
    gray: np.ndarray, rows: Sequence[Row], body: Body
) -> tuple[int, int, int, int] | None:
    """Pixel box of the uncaptioned chart start at the foot of a page, above any footnotes, or None."""
    band = tail_band(rows, body)
    if band is None:
        return None
    h, w = gray.shape
    l, t, r, b = band
    top, bottom = int((t + PAD) * h), int(b * h)
    ink = gray[top:bottom] < INK
    rule = _footnote_rule(ink, int(body.left * w), max(3, int(RULE_THICK * h)))
    if rule is not None:
        bottom = top + rule
    box = _ink_box(gray, top, bottom, int(l * w), int(r * w))
    if box is None or box[3] - box[1] < TAIL_INK * h:
        return None
    inside = [
        row
        for row in rows
        if row.top * h >= box[1] - PAD * h and row.bottom * h <= box[3] + PAD * h
    ]
    if any(
        TABLE.match(row.text)
        or (
            row.width > 0.5
            and abs(row.left - body.left) < 0.03
            and len(HAN.findall(row.text)) >= 15
        )
        for row in inside
    ):
        return None
    return box


def _stack(upper: Image.Image, lower: Image.Image) -> Image.Image:
    sheet = Image.new(
        "L", (max(upper.width, lower.width), upper.height + lower.height), 255
    )
    sheet.paste(upper, ((sheet.width - upper.width) // 2, 0))
    sheet.paste(lower, ((sheet.width - lower.width) // 2, upper.height))
    return sheet


def chart_band(
    rows: Sequence[Row], index: int, body: Body, caps: Mapping[int, re.Match[str]]
) -> tuple[float, float, float, float]:
    """(left, top, right, bottom) page fractions of the band that holds the chart above caption `rows[index]`."""
    cap = rows[index]
    notes = _note_rows(rows, caps, body)

    def is_prose(i: int, r: Row) -> bool:
        return _is_prose(i, r, body, notes, caps)

    top = HEADER
    for i, r in enumerate(rows):
        if r.bottom > cap.top:
            break
        if (r.top < RUNNING_HEAD and len(r.text) >= 4) or is_prose(i, r):
            top = max(top, r.bottom)
        elif i in caps and i != index:
            top = max(top, r.bottom)
            for s in rows[i + 1 :]:
                if (
                    s.top > r.bottom + 0.035
                    or s.top >= cap.top
                    or not NOTE.match(s.text)
                ):
                    break
                top = max(top, s.bottom)
    bottom = cap.top
    for i in sorted(notes):
        if i - 1 in notes:
            continue
        block = [
            rows[j]
            for j in range(i, len(rows))
            if all(k in notes for k in range(i, j + 1))
        ]
        block_bottom = max(r.bottom for r in block)
        if top < rows[i].top and block_bottom < bottom - EARLIER_FIGURE_GAP:
            top = max(top, block_bottom)
    note_tops = [r.top for r in rows if top < r.top < bottom and NOTE.match(r.text)]
    if note_tops and min(note_tops) > top + 0.05:
        bottom = min(note_tops)

    left, right = 0.04, 0.96
    peers = sorted(
        (rows[i].left + rows[i].right) / 2
        for i in caps
        if abs(rows[i].top - cap.top) < 0.02
    )
    if len(peers) > 1:
        centre = (cap.left + cap.right) / 2
        pos = peers.index(centre)
        left = left if pos == 0 else (peers[pos - 1] + centre) / 2
        right = right if pos == len(peers) - 1 else (centre + peers[pos + 1]) / 2
    return left, top, right, bottom


def crop_page_charts(
    page: PageImage,
    rows: Sequence[Row],
    body: Body,
    out_dir: Path,
    seen: set[str],
    known_ids: Collection[str] = (),
    lead: Image.Image | None = None,
) -> list[ExtractedFigure]:
    """Crop each captioned chart on one page into `out_dir/fig_X-Y.png`, skipping ids already in `seen`.

    `known_ids` are the figure ids the transcripts caption, used to repair OCR misreadings of a number.
    `lead` is the start of a chart at the foot of the previous page; it goes above a chart that opens this page."""
    figures: list[ExtractedFigure] = []
    with Image.open(page.path) as im:
        page_img = im.convert("L")
    gray = np.asarray(page_img)
    h, w = gray.shape
    caps = captions(rows, body)
    for index, m in sorted(caps.items()):
        row = rows[index]
        number, title = m.group(2), m.group(3)
        if (
            known_ids
            and f"{m.group(1)}-{number}" not in known_ids
            and f"{m.group(1)}-{number[:-1]}" in known_ids
        ):
            number, title = number[:-1], number[-1] + title
        fid = f"{m.group(1)}-{number}"
        if fid in seen:
            continue
        sideways = row.sideways
        if sideways:
            right = row.left - PAD if row.left > 0.5 else 0.96
            left = row.right + PAD if row.left <= 0.5 else 0.04
            band = (left, HEADER, right, 0.97)
        else:
            band = chart_band(rows, index, body, caps)
        l, t, r, b = band
        box = _ink_box(
            gray, int((t + PAD) * h), int((b - PAD) * h), int(l * w), int(r * w)
        )
        if box is None or box[3] - box[1] < 0.04 * h:
            print(f"Warning: no chart found above 图 {fid} on page {page.number}.")
            continue
        pad = int(PAD * h)
        box = (
            max(0, box[0] - pad),
            max(0, box[1] - pad),
            min(w, box[2] + pad),
            min(h, box[3] + pad),
        )
        crop = page_img.crop(box)
        if sideways:
            crop = crop.rotate(-90 if row.left > 0.5 else 90, expand=True)
        elif lead is not None and band[1] <= CHART_AT_TOP:
            crop = _stack(lead, crop)
        lead = None
        name = f"fig_{fid}.png"
        crop.save(out_dir / name, format="PNG")
        seen.add(fid)
        title = re.sub(r"\s+", " ", title).strip()
        figures.append(
            ExtractedFigure(
                figure_id=fid,
                caption=f"图 {fid} {title}".strip(),
                image_rel_path=f"figures/{name}",
                source_page=page.number,
                box=(box[0] / w, box[1] / h, box[2] / w, box[3] / h),
                width_px=crop.width,
                height_px=crop.height,
            )
        )
    return figures


def transcript_figure_ids(texts: Iterable[str]) -> set[str]:
    """The `X-Y` ids of the figure captions that begin a line in transcripts."""
    return {
        f"{m[1]}-{m[2]}" for text in texts for m in TRANSCRIPT_CAPTION.finditer(text)
    }


def extract_cjk_charts(
    pages: Sequence[PageImage],
    lines: Mapping[int, Sequence[OcrLine]],
    out_dir: Path,
    known_ids: Collection[str] = (),
) -> list[ExtractedFigure]:
    """Crop every `图 X-Y` chart of a book into `out_dir`, keeping the first page of a figure continued on the next."""
    out_dir.mkdir(parents=True, exist_ok=True)
    page_rows = {p.number: _rows(lines.get(p.number, ())) for p in pages}
    body = body_text(page_rows.values())
    seen: set[str] = set()
    figures: list[ExtractedFigure] = []
    lead: Image.Image | None = None
    previous = None
    for page in sorted(pages, key=lambda p: p.number):
        if previous is None or page.number != previous + 1:
            lead = None
        figures.extend(
            crop_page_charts(
                page, page_rows[page.number], body, out_dir, seen, known_ids, lead
            )
        )
        with Image.open(page.path) as im:
            page_img = im.convert("L")
        box = chart_tail(np.asarray(page_img), page_rows[page.number], body)
        lead = page_img.crop(box) if box else None
        previous = page.number
    return figures
