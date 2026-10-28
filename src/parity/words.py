"""Ink word boxes on a source scan page and on a rebuilt PDF page, in pt from the top-left corner.

Scan words come from the Vision OCR lines: each line's ink is split into runs at
word-sized gaps and the OCR words are matched to the runs. Rebuilt words come from
the PDF text layer; their box is the ink inside the text-layer box, so both sides
are compared ink to ink, and their baseline is the glyph origin.
"""

import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pymupdf
from polytypst_native import ink_mask

from .source import SCAN_DPI, SourcePage

PT_PER_PX = 72 / SCAN_DPI
INK_LEVEL = 140
PEN_CHROMA = 90
EDGE_LINE_SHARE = 0.9
EDGE_STRIP_SHARE = 0.02
EDGE_GAP_PT = 4.0
MEASURE_RANK = 3
SEG_GAP_PT = 0.9
WORD_GAP_PT = 1.8
LINE_GAP_PT = 2.5


@dataclass(frozen=True)
class InkWord:
    """A word's ink box and baseline (pt) and the index of its text line on the page."""

    text: str
    left: float
    right: float
    top: float
    bottom: float
    baseline: float
    line: int


def page_ink(page: pymupdf.Page) -> np.ndarray:
    """Dark pixels, less any strongly coloured ones such as a reader's pen marks over the print."""
    return uncolored_ink(page, INK_LEVEL)


def uncolored_ink(page: pymupdf.Page, level: int) -> np.ndarray:
    pix = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY)
    gray = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    color = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csRGB, alpha=False)
    rgb = np.frombuffer(color.samples, np.uint8).reshape(color.height, color.width, 3)
    return ink_mask(gray, rgb, level, PEN_CHROMA)


def line_measure(starts: Sequence[int], ends: Sequence[int]) -> tuple[int, int]:
    """The left and right edge of a text block from its lines' first and last ink columns: the
    `MEASURE_RANK`-th furthest start and end, so a speck or two cannot widen it and short lines cannot narrow it."""
    k = min(MEASURE_RANK, len(starts)) - 1
    return sorted(starts)[k], sorted(ends, reverse=True)[k]


def without_edge_lines(ink: np.ndarray) -> np.ndarray:
    """The ink without a scan's page border: columns inked down more than `EDGE_LINE_SHARE` of the page,
    and an ink run lying wholly in the outer `EDGE_STRIP_SHARE` of either side, apart from the rest by a gap."""
    out = ink.copy()
    out[:, ink.mean(axis=0) > EDGE_LINE_SHARE] = False
    cols = np.flatnonzero(out.any(axis=0))
    if not cols.size:
        return out
    runs = np.split(cols, np.flatnonzero(np.diff(cols) > EDGE_GAP_PT / PT_PER_PX) + 1)
    strip = EDGE_STRIP_SHARE * ink.shape[1]
    if len(runs) > 1 and runs[0][-1] < strip:
        out[:, : runs[0][-1] + 1] = False
    if len(runs) > 1 and runs[-1][0] >= ink.shape[1] - strip:
        out[:, runs[-1][0] :] = False
    return out


def segments(ink: np.ndarray, x0: int, x1: int, y0: int, y1: int, gap_pt: float = SEG_GAP_PT) -> list[tuple[int, int]]:
    """Column runs of ink in a line band, split at gaps of at least `gap_pt`."""
    gap = round(gap_pt / PT_PER_PX)
    cols = np.concatenate([ink[y0:y1, x0:x1].any(axis=0), np.zeros(gap + 1, bool)])
    segs, start, run, end = [], None, 0, 0
    for i, v in enumerate(cols):
        if v:
            if start is None:
                start = i
            run, end = 0, i
        elif start is not None:
            run += 1
            if run >= gap:
                segs.append((x0 + start, x0 + end + 1))
                start = None
    return segs


def align_words(widths: list[float], space: float, segs: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
    """Monotone match of each word to a run of ink segments, by predicted width and position."""
    n, m = len(widths), len(segs)
    if n == 0 or m < n:
        return None
    nat = np.array(widths)
    scale = (segs[-1][1] - segs[0][0]) / (nat.sum() + space * (n - 1))
    pred_start = segs[0][0] + np.concatenate([[0.0], np.cumsum(nat + space)[:-1]]) * scale
    pred_w = nat * scale
    cost = np.full((n + 1, m + 1), np.inf)
    back = np.zeros((n + 1, m + 1), int)
    cost[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(i, m - (n - i) + 1):
            for k in range(i - 1, j):
                if cost[i - 1, k] == np.inf:
                    continue
                a, b = segs[k][0], segs[j - 1][1]
                c = cost[i - 1, k] + abs((b - a) - pred_w[i - 1]) + 0.5 * abs(a - pred_start[i - 1])
                if c < cost[i, j]:
                    cost[i, j], back[i, j] = c, k
    if cost[n, m] == np.inf:
        return None
    out, j = [], m
    for i in range(n, 0, -1):
        k = back[i, j]
        out.append((segs[k][0], segs[j - 1][1]))
        j = k
    return out[::-1]


def line_baseline(ink: np.ndarray, x0: int, x1: int, y0: int, y1: int) -> int | None:
    """Bottom row (px) of the densest ink band of a line, which is its baseline."""
    rows = ink[y0:y1, x0:x1].sum(axis=1)
    if rows.size == 0 or rows.max() == 0:
        return None
    j = peak = int(np.argmax(rows))
    while j + 1 < len(rows) and rows[j + 1] > 0.3 * rows[peak]:
        j += 1
    return y0 + j + 1


def _ink_box(ink: np.ndarray, x0: int, x1: int, y0: int, y1: int) -> tuple[int, int, int, int] | None:
    """Tight (left, right, top, bottom) px of the ink inside a px box, or None when it is blank."""
    region = ink[max(0, y0) : y1, max(0, x0) : x1]
    ys, xs = np.where(region)
    if ys.size == 0:
        return None
    return max(0, x0) + int(xs.min()), max(0, x0) + int(xs.max()) + 1, max(0, y0) + int(ys.min()), max(0, y0) + int(ys.max()) + 1


def scan_words(ink: np.ndarray, page: SourcePage) -> list[InkWord]:
    """Ink boxes of the OCR words on a scan page; a line whose ink cannot be split word by word is left out."""
    h, w = ink.shape
    out: list[InkWord] = []
    for index, line in enumerate(page.lines):
        x0 = max(0, int(line.x * w) - 4)
        x1 = min(w, int((line.x + line.w) * w) + 4)
        y0 = max(0, int((1 - line.y - line.h) * h))
        y1 = min(h, int((1 - line.y) * h))
        base = line_baseline(ink, x0, x1, y0, y1)
        words = line.text.split()
        if base is None:
            continue
        boxes = segments(ink, x0, x1, y0, y1, WORD_GAP_PT)
        if len(boxes) != len(words):
            segs = segments(ink, x0, x1, y0, y1)
            boxes = align_words([float(len(wd)) for wd in words], 0.6, segs) if segs else None
        if boxes is None:
            continue
        for word, (a, b) in zip(words, boxes):
            box = _ink_box(ink, a, b, y0, y1)
            if box is not None:
                l, r, t, btm = box
                out.append(InkWord(word, l * PT_PER_PX, r * PT_PER_PX, t * PT_PER_PX, btm * PT_PER_PX, base * PT_PER_PX, index))
    return out


def rebuilt_words(page: pymupdf.Page, ink: np.ndarray) -> list[InkWord]:
    """Ink boxes of the text-layer words on a rebuilt page, in reading order, baseline from the glyph origin."""
    raw: list[tuple[str, list[float], float]] = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", ()):
            text, box, base = "", [np.inf, np.inf, -np.inf, -np.inf], 0.0
            for span in line["spans"]:
                for ch in span["chars"]:
                    if ch["c"].isspace():
                        if text:
                            raw.append((text, box, base))
                        text, box = "", [np.inf, np.inf, -np.inf, -np.inf]
                        continue
                    if not text:
                        base = ch["origin"][1]
                    text += ch["c"]
                    x0, y0, x1, y1 = ch["bbox"]
                    box = [min(box[0], x0), min(box[1], y0), max(box[2], x1), max(box[3], y1)]
            if text:
                raw.append((text, box, base))
    placed: list[tuple[str, tuple[int, int, int, int], float]] = []
    for text, (x0, y0, x1, y1), base in raw:
        px = _ink_box(ink, int(x0 / PT_PER_PX), int(np.ceil(x1 / PT_PER_PX)), int(y0 / PT_PER_PX), int(np.ceil(y1 / PT_PER_PX)))
        if px is not None:
            placed.append((text, px, base))
    out: list[InkWord] = []
    row, row_base = -1, -np.inf
    for text, (l, r, t, btm), base in sorted(placed, key=lambda p: p[2]):
        if base - row_base > LINE_GAP_PT:
            row, row_base = row + 1, base
        out.append(InkWord(text, l * PT_PER_PX, r * PT_PER_PX, t * PT_PER_PX, btm * PT_PER_PX, base, row))
    return sorted(out, key=lambda wd: (wd.line, wd.left))


def token(text: str) -> str:
    """Comparison form of a word: compatibility-folded, lower case, letters and digits only."""
    return "".join(c for c in unicodedata.normalize("NFKC", text).lower() if c.isalnum())
