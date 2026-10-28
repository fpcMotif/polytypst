"""Word-placed facsimile of a scanned book.

Every scan page becomes one output page of the same size. Apple Vision OCR gives
the text lines; ink gaps on the scan give the word boxes; each OCR word is set in
the book's face and scaled so its glyph ink fills the scan word's ink box. Fletcher
diagrams replace the OCR text inside the scan box where each diagram is found.
"""

import copy
import difflib
import itertools
import json
import os
import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import pymupdf
from fontTools.ttLib import TTFont, TTLibError
from PIL import Image, ImageFont

from .book_state import book_state
from .compiler.diagrams import page_diagrams
from .compiler.typst_math import compile_typst, convert_math_batch
from .facsimile_figures import (
    FigureArt,
    drawing_gaps,
    figure_typst,
    gray_svg,
    slices,
    svg_ink,
    without_lines,
)
from .facsimile_lines import CAPTION_RE, TableCell, face_index, faint_ink, strict_page
from .facsimile_text import Chunk, Piece, chunks, match_units
from .ocr.pages import OcrLine
from .ocr.transcripts import TranscriptStore
from .parity.diagrams import DiagramText, diagram_ink, find_diagram
from .parity.ink_cache import InkCache
from .parity.source import (
    SCAN_DPI,
    ensure_source_ocr,
    read_source_page,
    source_ocr_dir,
)
from .parity.words import (
    PT_PER_PX,
    align_words,
    line_baseline,
    line_measure,
    page_ink,
    segments,
    without_edge_lines,
)

MAX_SCALE = 1.25
UNREAD_INK_GAP_PT = 20.0
UNREAD_INK_MIN_PT = 3.0
UNREAD_INK_MIN_HEIGHT_PT = 1.0
UNREAD_LINES_RATIO = 1.6
UNREAD_VALLEY_SHARE = 0.25
UNCLAIMED_INK_MARGIN_PT = 1.0
CJK_CUT_WINDOW = 4
RUNNING_HEAD_SHARE = 0.12
FOLIO_SHARE = 0.93
RULE_MAX_PT = 4.0
RULE_MAX_SKEW_PT = 8.0
RULE_COVER_SHARE = 0.9
RULE_MIN_SHARE = 0.5
HEAD_GAP_PT = 20.0
DUST_LINE_SHARE = 0.4
PITCH_RANGE = (0.5, 1.3)
PITCH_SAMPLE_EVERY = 4
LEADING_RANGE = (0.2, 3.0)
SPECK_MAX_PX = 40
FOLIO_RE = re.compile(r"\W*(\[)?\s*(\d+)\s*\]?\W*")
TABLE_RE = re.compile(r"\s*<table\b.*</table>\s*", re.DOTALL)
ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.DOTALL)
CELL_RE = re.compile(r"<t[hd]\w*\b[^>]*>(.*?)</t[hd]\w*>", re.DOTALL)
CELL_TAG_RE = re.compile(r"<t[hd]\w*\b([^>]*)>(.*?)</t[hd]\w*>", re.DOTALL)
SPAN_RE = re.compile(r"\b(col|row)span\s*=\s*[\"']?(\d+)")
RUN_IN_RE = re.compile(r"\d+\.\s")
NOTE_RE = re.compile(r"[①-⑳]|[⁰¹²³⁴⁵⁶⁷⁸⁹]+\)")
FOOTNOTE_SIZE = 0.857
FOOTNOTE_RULE = "#v(0.6em)#line(length: 30%, stroke: 0.4pt)"
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
PIPE_ROW_RE =re.compile(r"\s*\|.*\|\s*")
PIPE_RULE_RE = re.compile(r"[\s|:-]*-{3,}[\s|:-]*")
IMAGE_RE = re.compile(r"\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*")
ENTRY_RE = re.compile(r"(?<=\s\d)\s+(?=\d+\.\s)|(?<=\s\d\d)\s+(?=\d+\.\s)|(?<=\s\d\d\d)\s+(?=\d+\.\s)")
ROMAN_FOLIO_RE = re.compile(r"[^\w]*[ivxlc]+[^\w]*")
TALL_SHARE = 0.3
LEADER_DOTS = 3
MATCH_SHARE = 0.6
TEXT_LINE_SHARE = 0.5
DISPLAY_MARK = "\x00"

CHAPTER_HEAD_RE = re.compile(r"(第\s*)([一二三四五六七八九十]+|\d+)(\s*章)\s*(\S.*)")
SECTION_HEAD_RE = re.compile(r"(§\s*)(\d+)(\.?)\s*(\S.*)")
TOC_ENTRY_RE = re.compile(r"(.*\S)\s+(\d+)")
CONTENTS_SHARE = 0.3
NEAR_BREAK = 4
CHINESE_DIGITS = "一二三四五六七八九"
ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}

Band = tuple[int, int, int, int]
GUTTER_LINES = 2.0
RUN_GAP_LINES = 1.5
LOCK_FILL = 1.3


def no_diagrams(_out_dir: Path) -> list[Path]:
    return []


@dataclass(frozen=True)
class FacsimileStyle:
    """One book's facsimile: its output name, title, face and the diagram snippets it places."""

    slug: str
    title: str
    font_file: Path
    font_stack: str
    size: float
    weight: int
    diagram_dir: Path
    diagram_text: DiagramText
    install_diagrams: Callable[[Path], object] = no_diagrams
    diagram_boxes: Callable[[], dict[str, tuple[int, int, int, int]]] | None = None
    figure_boxes: Callable[[], dict[int, list[tuple[float, float, float, float]]]] | None = None
    transcripts: str | None = None
    flow: bool = False
    scan_pages: frozenset[int] = frozenset()
    strict_lines: bool = False
    figure_art: Callable[[], dict[int, list[FigureArt]]] | None = None


@dataclass(frozen=True)
class Placement:
    """A run of text whose glyph ink is stretched to an ink box on the scan (pt, top-left origin)."""

    text: str
    left: float
    right: float
    top: float
    bottom: float
    baseline: float
    line: int = 0


class Measure:
    """Glyph ink boxes and advances in the style's face at its weight, per 100 units of font size."""

    def __init__(self, style: FacsimileStyle) -> None:
        self.size = style.size
        self.font = ImageFont.truetype(str(style.font_file), 100)
        try:
            self.font.set_variation_by_axes([style.weight])
        except (OSError, ValueError, TypeError):
            pass
        try:
            self.cmap = set(TTFont(str(style.font_file)).getBestCmap())
        except TTLibError:
            self.cmap = set(TTFont(str(style.font_file), fontNumber=0).getBestCmap())
        self.space = self.font.getlength(" ")
        self._ink_boxes: dict[str, tuple[float, float, float, float]] = {}

    def covers(self, text: str) -> bool:
        return all(ord(c) in self.cmap for c in text)

    def ink_box(self, text: str) -> tuple[float, float, float, float]:
        if (box := self._ink_boxes.get(text)) is None:
            box = self._ink_boxes[text] = self.font.getbbox(text, anchor="ls")
        return box

    def width(self, text: str) -> float:
        if not self.covers(text):
            return self.space * 2 * len(text)
        l, _, r, _ = self.ink_box(text)
        return r - l


def page_placements(
    ink: np.ndarray,
    lines: tuple[OcrLine, ...],
    skip: list[tuple[float, float, float, float]],
    measure: Measure,
) -> list[Placement]:
    """Word placements for one page, leaving out OCR lines inside the `skip` boxes (pt)."""
    h, w = ink.shape
    out: list[Placement] = []
    for index, line in enumerate(lines):
        x0 = max(0, int(line.x * w) - 4)
        x1 = min(w, int((line.x + line.w) * w) + 4)
        y0 = max(0, int((1 - line.y - line.h) * h))
        y1 = min(h, int((1 - line.y) * h))
        cx, cy = (x0 + x1) / 2 * PT_PER_PX, (y0 + y1) / 2 * PT_PER_PX
        if any(l <= cx <= r and t <= cy <= b for l, t, r, b in skip):
            continue
        base = line_baseline(ink, x0, x1, y0, y1)
        segs = segments(ink, x0, x1, y0, y1)
        if base is None or not segs:
            continue
        words = line.text.split()
        boxes = align_words([measure.width(wd) for wd in words], measure.space, segs)
        if boxes is None:
            words, boxes = [line.text], [(segs[0][0], segs[-1][1])]
        for word, (a, b) in zip(words, boxes):
            rows = np.where(ink[y0:y1, a:b].any(axis=1))[0]
            if rows.size == 0:
                continue
            out.append(
                Placement(
                    word,
                    a * PT_PER_PX,
                    b * PT_PER_PX,
                    (y0 + rows.min()) * PT_PER_PX,
                    (y0 + rows.max() + 1) * PT_PER_PX,
                    base * PT_PER_PX,
                    index,
                )
            )
    return out


def ink_bands(ink: np.ndarray, gap: int = 3) -> list[tuple[int, int]]:
    rows = np.flatnonzero(ink.sum(axis=1) > 2)
    if rows.size == 0:
        return []
    breaks = np.flatnonzero(np.diff(rows) > gap + 1)
    starts = np.concatenate(([rows[0]], rows[breaks + 1]))
    ends = np.concatenate((rows[breaks], [rows[-1]])) + 1
    return list(zip(starts.tolist(), ends.tolist(), strict=True))


def split_by_width(word: Placement, measure: Measure) -> list[Placement]:
    """A placement that holds a whole OCR line, cut into its words in proportion to their measured widths."""
    parts = re.sub(r"(?<!\w)(附表|图|表)(?=\d)", r"\1 ", word.text).split()
    if len(parts) < 2:
        return [word]
    widths = [measure.width(p) for p in parts]
    scale = (word.right - word.left) / (sum(widths) + measure.space * (len(parts) - 1))
    out, x = [], word.left
    for text, width in zip(parts, widths):
        out.append(
            Placement(
                text,
                x,
                x + width * scale,
                word.top,
                word.bottom,
                word.baseline,
                word.line,
            )
        )
        x += (width + measure.space) * scale
    return out


def unread_lines(block: np.ndarray, line_px: float) -> list[np.ndarray]:
    """The inked rows of `block`, cut into pieces about `line_px` tall at their emptiest rows when
    the block is taller than `UNREAD_LINES_RATIO` lines, as touching sub- and superscripts merge lines.
    A row is cut only in a valley of ink, so one tall arrow or delimiter stays whole."""
    ys = np.flatnonzero(block.any(axis=1))
    if not ys.size:
        return []
    height = ys[-1] + 1 - ys[0]
    if not line_px or height <= UNREAD_LINES_RATIO * line_px:
        return [ys]
    profile = block.sum(axis=1)
    valley = UNREAD_VALLEY_SHARE * float(np.median(profile[ys]))
    n = round(height / line_px)
    reach = max(1, round(line_px / 3))
    cuts = []
    for i in range(1, n):
        target = ys[0] + round(i * height / n)
        lo, hi = max(ys[0] + 1, target - reach), min(ys[-1], target + reach)
        if hi > lo and profile[(cut := lo + int(np.argmin(profile[lo:hi])))] <= valley:
            cuts.append(cut)
    edges = [ys[0], *cuts, ys[-1] + 1]
    return [p for lo, hi in itertools.pairwise(edges) if (p := ys[(ys >= lo) & (ys < hi)]).size]


def page_words(
    ink: np.ndarray,
    lines: tuple[OcrLine, ...],
    skip: list[tuple[float, float, float, float]],
    measure: Measure,
) -> list[Placement]:
    """The OCR words plus one textless word for each ink band no OCR line covers, such as display math
    that the line reader skipped, in reading order. OCR lines that share a row get one line number."""
    h = ink.shape[0]
    spans = [
        (max(0, int((1 - ln.y - ln.h) * h)), min(h, int((1 - ln.y) * h)))
        for ln in lines
    ]
    words = [
        part
        for w in page_placements(ink, lines, skip, measure)
        for part in split_by_width(w, measure)
    ]
    width = ink.shape[1]
    ocr_spans = list(spans)
    line_px = float(np.median([y1 - y0 for y0, y1 in ocr_spans])) if ocr_spans else 0.0
    for a, b in ink_bands(ink):
        unread = ink[a:b].copy()
        overlapping = [
            (ln, y0, y1) for ln, (y0, y1) in zip(lines, ocr_spans) if min(b, y1) > max(a, y0)
        ]
        for ln, y0, y1 in overlapping:
            unread[max(a, y0 - 4) - a : min(b, y1 + 4) - a, max(0, int(ln.x * width) - 4) : int((ln.x + ln.w) * width) + 4] = False
        cols = np.flatnonzero(unread.any(axis=0))
        if overlapping:
            runs = np.split(cols, np.flatnonzero(np.diff(cols) > UNREAD_INK_GAP_PT / PT_PER_PX) + 1)
            runs = [r for r in runs if r.size and (r[-1] + 1 - r[0]) * PT_PER_PX >= UNREAD_INK_MIN_PT]
        else:
            runs = [cols]
        for run in runs:
            block = unread[:, run[0] : run[-1] + 1]
            for ys in unread_lines(block, line_px):
                if (ys[-1] + 1 - ys[0]) * PT_PER_PX < UNREAD_INK_MIN_HEIGHT_PT:
                    continue
                xs = np.flatnonzero(block[ys[0] : ys[-1] + 1].any(axis=0)) + run[0]
                left, right, top, bottom = (
                    xs[0] * PT_PER_PX,
                    (xs[-1] + 1) * PT_PER_PX,
                    (a + ys[0]) * PT_PER_PX,
                    (a + ys[-1] + 1) * PT_PER_PX,
                )
                if any(
                    l <= (left + right) / 2 <= r and t <= (top + bottom) / 2 <= btm
                    for l, t, r, btm in skip
                ):
                    continue
                spans.append((a + ys[0], a + ys[-1] + 1))
                words.append(Placement("", left, right, top, bottom, bottom, len(spans) - 1))
    height = float(np.median([y1 - y0 for y0, y1 in spans])) if spans else 0.0
    row, last, rows = -1, -np.inf, {}
    for i in sorted(range(len(spans)), key=lambda i: sum(spans[i])):
        middle = sum(spans[i]) / 2
        if middle - last > 0.4 * height:
            row += 1
        rows[i], last = row, middle
    words = [
        Placement(w.text, w.left, w.right, w.top, w.bottom, w.baseline, rows[w.line])
        for w in words
    ]
    return sorted(words, key=lambda w: (w.line, w.left))


def without_diagrams(text: str) -> str:
    """The transcript without its array diagrams, which the fletcher snippets replace."""
    for m in reversed(page_diagrams(text)):
        text = text[: m.start()] + text[m.end() :]
    return text


def math_items(chunks: list[Chunk]) -> list[tuple[str, bool]]:
    return [
        (p.text, p.kind == "display") for c in chunks for p in c if p.kind != "text"
    ]


def chunk_markup(chunk: Chunk, math: dict[tuple[str, bool], str]) -> str:
    out = []
    for p in chunk:
        if p.kind == "text":
            s = typst_string(p.text)
            out.append(
                f"#emph({s})"
                if p.style == "italic"
                else f"#strong({s})"
                if p.style == "bold"
                else f"#{s}"
            )
        elif p.kind == "math":
            out.append(f"${math[(p.text, False)]}$")
        else:
            out.append(f"$ {math[(p.text, True)]} $")
    return "".join(out)


def with_break_hyphen(piece: str) -> str:
    """The head of a word broken at a line end: a hyphen after a Latin letter, none after a full-width one."""
    if not piece or piece.endswith("-") or unicodedata.east_asian_width(piece[-1]) in ("W", "F"):
        return piece
    return piece + "-"


def split_across_lines(word: str, parts: list[Placement]) -> list[Placement]:
    """A word the scan hyphenates over several lines, cut in proportion to each line's ink width."""
    total = sum(p.right - p.left for p in parts)
    out, start, acc = [], 0, 0.0
    for k, p in enumerate(parts):
        acc += p.right - p.left
        fragment = p.text.split()[-1] if p.text.split() else ""
        scanned = fragment.removesuffix("-")
        if k == len(parts) - 1:
            end = len(word)
        elif (
            fragment.endswith("-")
            and 0 < len(scanned) < len(word) - start
            and scanned[:2].casefold() == word[start : start + 2].casefold()
        ):
            end = start + len(scanned)
            if word[end] == "-":
                end += 1
        else:
            end = max(start + 1, round(len(word) * acc / total))
            if (
                len(scanned) >= 2
                and unicodedata.east_asian_width(scanned[-1]) in ("W", "F")
                and (hits := [m.end() for m in re.finditer(re.escape(scanned[-2:]), word) if start < m.end() < len(word)])
            ):
                nearest = min(hits, key=lambda h: abs(h - end))
                if abs(nearest - end) <= CJK_CUT_WINDOW:
                    end = nearest
        piece = word[start:end]
        out.append(
            Placement(
                piece if k == len(parts) - 1 else with_break_hyphen(piece),
                p.left,
                p.right,
                p.top,
                p.bottom,
                p.baseline,
                p.line,
            )
        )
        start = end
    return out


def transcript_typst(
    words: list[Placement],
    page_chunks: list[Chunk],
    math: dict[tuple[str, bool], str],
    measure: Measure,
    ink: np.ndarray,
) -> list[str]:
    """The transcript set on the scan words: a plain word is ink-fitted at its baseline, a run of
    styled prose is width-fitted, and anything with math is fitted to the ink box it covers."""
    units = match_units(page_chunks, [w.text for w in words], [w.line for w in words])
    owner = {j: k for k, u in enumerate(units) for j in u.words}
    inline_math = {
        k
        for k, u in enumerate(units)
        if any(p.kind == "math" for i in u.chunks for p in page_chunks[i])
        and not any(p.kind == "display" for i in u.chunks for p in page_chunks[i])
    }
    used_lines = {words[j].line for u in units for j in u.words}
    first, last = min(used_lines, default=0), max(used_lines, default=-1)
    out = [
        placement_typst(w, measure)
        for w in words
        if w.text and not first <= w.line <= last
    ]
    for k, unit in enumerate(units):
        if not unit.words:
            continue
        cs = [page_chunks[i] for i in unit.chunks]
        pieces = [p for c in cs for p in c]
        by_line: dict[int, list[Placement]] = {}
        for j in unit.words:
            by_line.setdefault(words[j].line, []).append(words[j])
        if any(p.kind == "display" for p in pieces):
            box = [words[j] for j in unit.words]
            if valid := [w for w in box if w.text or w.left > 20.0]:
                box = valid
        elif len(by_line) > 1 and len(cs) == 1 and len(pieces) > 1 and all(p.kind == "text" for p in pieces):
            spans = [
                Placement(
                    " ".join(w.text for w in ws), ws[0].left, ws[-1].right,
                    min(w.top for w in ws), max(w.bottom for w in ws), ws[0].baseline, ws[0].line,
                )
                for ws in by_line.values()
            ]
            styles = [p.style for p in pieces for _ in p.text]
            joined = "".join(p.text for p in pieces)
            start = 0
            for part in split_across_lines(joined, spans):
                end = start + len(part.text) - (joined[start : start + len(part.text)] != part.text)
                runs = [
                    Piece("text", "".join(c for _, c in run), style)
                    for style, run in itertools.groupby(zip(styles[start:end], joined[start:end]), key=lambda sc: sc[0])
                ]
                if end - start < len(part.text):
                    runs[-1] = replace(runs[-1], text=runs[-1].text + part.text[-1])
                out.append(
                    f"#place(top + left, dx: {part.left:.2f}pt, dy: {part.baseline:.2f}pt, "
                    f"fit({part.right - part.left:.2f}pt, [{chunk_markup(tuple(runs), math)}]))"
                )
                start = end
            continue
        elif len(by_line) > 1 and len(pieces) == 1 and pieces[0].kind == "text":
            spans = [
                Placement(
                    " ".join(w.text for w in ws),
                    ws[0].left,
                    ws[-1].right,
                    min(w.top for w in ws),
                    max(w.bottom for w in ws),
                    ws[0].baseline,
                    ws[0].line,
                )
                for ws in by_line.values()
            ]
            parts = split_across_lines(pieces[0].text, spans)
            if pieces[0].style == "":
                out += [placement_typst(p, measure) for p in parts]
            else:
                out += [
                    f"#place(top + left, dx: {p.left:.2f}pt, dy: {p.baseline:.2f}pt, "
                    f"fit({p.right - p.left:.2f}pt, [{chunk_markup((Piece('text', p.text, pieces[0].style),), math)}]))"
                    for p in parts
                ]
            continue
        elif (
            len(by_line) > 1
            and pieces[-1].kind == "text"
            and 0 < len(tail := " ".join(w.text for w in list(by_line.values())[-1])) < len(pieces[-1].text)
            and pieces[-1].text.casefold().endswith(tail.casefold())
        ):
            *head_lines, tail_line = by_line.values()
            tail_piece = pieces[-1]
            tail_place = Placement(
                tail_piece.text[-len(tail) :],
                tail_line[0].left,
                tail_line[-1].right,
                min(w.top for w in tail_line),
                max(w.bottom for w in tail_line),
                tail_line[0].baseline,
                tail_line[0].line,
            )
            if tail_piece.style == "":
                out.append(placement_typst(tail_place, measure))
            else:
                out.append(
                    f"#place(top + left, dx: {tail_place.left:.2f}pt, dy: {tail_place.baseline:.2f}pt, "
                    f"fit({tail_place.right - tail_place.left:.2f}pt, [{chunk_markup((Piece('text', tail_place.text, tail_piece.style),), math)}]))"
                )
            head = tail_piece.text[: -len(tail)]
            cs = [*cs[:-1], (*cs[-1][:-1], Piece("text", with_break_hyphen(head), tail_piece.style))]
            pieces = [p for c in cs for p in c]
            box = max(head_lines, key=len)
        else:
            box = max(by_line.values(), key=len)
        left, right = min(w.left for w in box), max(w.right for w in box)
        top, bottom = min(w.top for w in box), max(w.bottom for w in box)
        if k in inline_math:
            line = [
                (j, w) for j, w in enumerate(words) if w.line == box[0].line
            ]
            others = [(j, w) for j, w in line if owner.get(j, k) != k]
            before = [(j, w) for j, w in others if w.right <= left]
            if not before:
                lo = min(w.left for w in words)
            else:
                j, w = max(before, key=lambda jw: jw[1].right)
                lo = left - UNCLAIMED_INK_MARGIN_PT if owner[j] in inline_math else w.right
            others = [w for _, w in others]
            hi = min(
                (w.left for w in others if w.left >= right),
                default=max(w.right for w in words),
            )
            texts = [w for _, w in line if w.text] or box
            r0 = round(min(top, *(w.top for w in texts)) / PT_PER_PX)
            r1 = round(max(bottom, *(w.bottom for w in texts)) / PT_PER_PX)
            a = round((lo + UNCLAIMED_INK_MARGIN_PT) / PT_PER_PX)
            b = round((hi - UNCLAIMED_INK_MARGIN_PT) / PT_PER_PX)
            cols = np.flatnonzero(ink[r0:r1, a:b].any(axis=0)) + a
            if cols.size:
                rows = np.flatnonzero(ink[r0:r1, cols[0] : cols[-1] + 1].any(axis=1))
                left = min(left, cols[0] * PT_PER_PX)
                right = max(right, (cols[-1] + 1) * PT_PER_PX)
                top = min(top, (r0 + rows[0]) * PT_PER_PX)
                bottom = max(bottom, (r0 + rows[-1] + 1) * PT_PER_PX)
        if len(pieces) == 1 and pieces[0].kind == "text" and pieces[0].style == "":
            out.append(
                placement_typst(
                    Placement(
                        pieces[0].text, left, right, top, bottom, box[0].baseline
                    ),
                    measure,
                )
            )
            continue
        markup = " ".join(chunk_markup(c, math) for c in cs)
        if all(p.kind == "text" for p in pieces):
            out.append(
                f"#place(top + left, dx: {left:.2f}pt, dy: {box[0].baseline:.2f}pt, fit({right - left:.2f}pt, [{markup}]))"
            )
        else:
            out.append(
                f"#place(top + left, dx: {left:.2f}pt, dy: {top:.2f}pt, inkfit({right - left:.2f}pt, {bottom - top:.2f}pt, [{markup}]))"
            )
    return out


def typst_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def placement_typst(p: Placement, measure: Measure) -> str:
    """A placed word: ink-fitted when the face has every glyph, else advance-fitted."""
    s = measure.size / 100
    if measure.covers(p.text):
        l, _, r, _ = measure.ink_box(p.text)
        if r > l:
            sx = min(MAX_SCALE, (p.right - p.left) / ((r - l) * s))
            return (
                f"#place(top + left, dx: {p.left - l * s * sx:.2f}pt, dy: {p.baseline:.2f}pt, "
                f"scale(x: {sx * 100:.1f}%, origin: top + left, reflow: false, word({typst_string(p.text)})))"
            )
    return f"#place(top + left, dx: {p.left:.2f}pt, dy: {p.baseline:.2f}pt, fit({p.right - p.left:.2f}pt, word({typst_string(p.text)})))"


@dataclass(frozen=True)
class Frame:
    left: float
    top: float
    right: float
    bottom: float
    line: float
    rule: tuple[float, float, float, float] | None
    margins: tuple[tuple[int, int], ...]


def is_rule(band: np.ndarray, page_width: int) -> bool:
    """A band holding one long stroke: thin in every column it inks, even when the scan is skewed."""
    cols = np.flatnonzero(band.any(axis=0))
    if not cols.size or cols[-1] + 1 - cols[0] < RULE_MIN_SHARE * page_width:
        return False
    if band.shape[0] * PT_PER_PX > RULE_MAX_SKEW_PT:
        return False
    span = band[:, cols[0] : cols[-1] + 1]
    return bool(span.any(axis=0).mean() >= RULE_COVER_SHARE and span.sum(axis=0).mean() * PT_PER_PX <= RULE_MAX_PT)


def page_frame(ink: np.ndarray) -> Frame | None:
    h, w = ink.shape
    bands = [(a, b) for a, b in ink_bands(ink) if ink[a:b].sum() > SPECK_MAX_PX]
    rule, start = None, 0
    for k, (a, b) in enumerate(bands):
        if b > RUNNING_HEAD_SHARE * h:
            break
        cols = np.flatnonzero(ink[a:b].any(axis=0))
        if is_rule(ink[a:b], w):
            rule = (cols[0] * PT_PER_PX, a * PT_PER_PX, (cols[-1] + 1) * PT_PER_PX, b * PT_PER_PX)
            start = k + 1
    margins = [band for band in bands[:start] if rule is None or band[1] * PT_PER_PX < rule[1]]
    body = bands[start:]
    while body and body[-1][0] > FOLIO_SHARE * h:
        cols = np.flatnonzero(ink[slice(*body[-1])].any(axis=0))
        if cols[-1] + 1 - cols[0] > (1 - RULE_MIN_SHARE) * w:
            break
        margins.append(body.pop())
    if len(body) < 2:
        return None
    line_px = float(np.median([b - a for a, b in body]))
    while len(body) > 2 and body[0][1] - body[0][0] < DUST_LINE_SHARE * line_px:
        body.pop(0)
    while len(body) > 2 and body[-1][1] - body[-1][0] < DUST_LINE_SHARE * line_px:
        body.pop()
    top, bottom = body[0][0], body[-1][1]
    extents = [cols[[0, -1]] for a, b in body if (cols := np.flatnonzero(ink[a:b].any(axis=0))).size]
    if not extents:
        return None
    starts, ends = zip(*extents, strict=True)
    left, right = line_measure([int(s) for s in starts], [int(e) + 1 for e in ends])
    return Frame(
        left * PT_PER_PX,
        top * PT_PER_PX,
        right * PT_PER_PX,
        bottom * PT_PER_PX,
        float(np.median([b - a for a, b in body])) * PT_PER_PX,
        rule,
        tuple(margins),
    )


def folio_placements(ink: np.ndarray, lines: tuple[OcrLine, ...], frame: Frame) -> list[Placement]:
    h, w = ink.shape
    out = []
    for ln in lines:
        middle = (1 - ln.y - ln.h / 2) * h
        band = next(((a, b) for a, b in frame.margins if a - 4 <= middle <= b + 4), None)
        m = FOLIO_RE.fullmatch(ln.text.strip())
        roman = ROMAN_FOLIO_RE.fullmatch(ln.text.strip())
        if band is None or (m is None and roman is None):
            continue
        x0, x1 = max(0, int(ln.x * w) - 4), min(w, int((ln.x + ln.w) * w) + 4)
        cols = np.flatnonzero(ink[band[0] : band[1], x0:x1].any(axis=0)) + x0
        if not cols.size:
            continue
        text = f"· {re.sub(r'[^ivxlc]', '', ln.text)} ·" if m is None else f"[{m[2]}]" if m[1] else f"· {m[2]} ·"
        rows = np.flatnonzero(ink[band[0] : band[1], cols[0] : cols[-1] + 1].any(axis=1)) + band[0]
        top, bottom = rows[0] * PT_PER_PX, (rows[-1] + 1) * PT_PER_PX
        left, right = cols[0] * PT_PER_PX, (cols[-1] + 1) * PT_PER_PX
        if any(o.left < right and left < o.right and o.top < bottom and top < o.bottom for o in out):
            continue
        out.append(Placement(text, left, right, top, bottom, bottom))
    return out


def with_foot_lines(ink: np.ndarray, frame: Frame, lines: tuple[OcrLine, ...]) -> Frame:
    """The frame grown over the foot bands whose OCR text is not a folio, such as a short last formula line."""
    h = ink.shape[0]
    foot = sorted(
        (a, b) for a, b in frame.margins
        if a * PT_PER_PX >= frame.bottom
        and not any(
            a - 4 <= (1 - ln.y - ln.h / 2) * h <= b + 4
            and (FOLIO_RE.fullmatch(ln.text.strip()) or ROMAN_FOLIO_RE.fullmatch(ln.text.strip()))
            for ln in lines
        )
    )
    if not foot:
        return frame
    gap = frame.line * GUTTER_LINES / PT_PER_PX
    bottom = frame.bottom / PT_PER_PX
    kept = []
    for a, b in foot:
        if a - bottom > gap:
            break
        kept.append((a, b))
        bottom = b
    if not kept:
        return frame
    return replace(frame, bottom=bottom * PT_PER_PX, margins=tuple(m for m in frame.margins if m not in kept))


def head_band(ink: np.ndarray, frame: Frame) -> tuple[int, int] | None:
    """The margin band above the header rule with the most ink, so dust specks above the head do not count."""
    if frame.rule is None:
        return None
    bands = [(a, b) for a, b in frame.margins if b * PT_PER_PX <= frame.rule[1]]
    return max(bands, key=lambda ab: int(ink[ab[0] : ab[1]].sum()), default=None)


def running_head(ink: np.ndarray, frame: Frame) -> Placement | None:
    """The title box in the head band above the rule, when the band also holds other ink such as the folio.
    The title is the ink run nearest the page middle."""
    band = head_band(ink, frame)
    if band is None:
        return None
    cols = np.flatnonzero(ink[band[0] : band[1]].any(axis=0))
    runs = np.split(cols, np.flatnonzero(np.diff(cols) > HEAD_GAP_PT / PT_PER_PX) + 1)
    middle = ink.shape[1] / 2
    title = min(runs, key=lambda r: abs((r[0] + r[-1]) / 2 - middle))
    others = [r for r in runs if r is not title]
    if not others:
        return None
    rows = np.flatnonzero(ink[band[0] : band[1], title[0] : title[-1] + 1].any(axis=1)) + band[0]
    top, bottom = rows[0] * PT_PER_PX, (rows[-1] + 1) * PT_PER_PX
    return Placement("", title[0] * PT_PER_PX, (title[-1] + 1) * PT_PER_PX, top, bottom, bottom)


def ocr_head(ink: np.ndarray, frame: Frame, lines: tuple[OcrLine, ...]) -> str | None:
    """The OCR text of the title in the head band above the rule: the line nearest the page middle that is not a folio."""
    h = ink.shape[0]
    band = head_band(ink, frame)
    if band is None:
        return None
    titles = [
        ln for ln in lines
        if band[0] - 4 <= (1 - ln.y - ln.h / 2) * h <= band[1] + 4
        and not FOLIO_RE.fullmatch(ln.text.strip()) and not ROMAN_FOLIO_RE.fullmatch(ln.text.strip())
    ]
    return min(titles, key=lambda ln: abs(ln.x + ln.w / 2 - 0.5)).text.strip() if titles else None


def head_typst(p: Placement, size: float = 10.0, fallback: str = "") -> str:
    """The running head in the scan's head box: the last chapter heading before it, or on an odd page the last
    section heading in that chapter; `fallback` before any chapter."""
    return (
        f"#place(top + left, dx: {p.left:.2f}pt, dy: {p.top:.2f}pt, "
        f'inkfit({p.right - p.left:.2f}pt, {p.bottom - p.top:.2f}pt, text(size: {size:.2f}pt, weight: "bold", '
        f"running-head({typst_string(fallback)}))))"
    )


def folio_value(p: Placement) -> int:
    digits = re.sub(r"\D", "", p.text)
    return int(digits) if digits else roman_number(re.sub(r"[^ivxlc]", "", p.text))


def page_starts(folios: dict[int, list[int]]) -> dict[int, int]:
    """The pages where the page counter restarts, with the value it restarts at. `folios` holds the numbers read
    in each page's margins. The counter restarts where no number on the page or on the next page with numbers
    fits the running count, and a number on the page fits a new count together with one on that next page.
    A single misread folio restarts nothing."""
    starts: dict[int, int] = {}
    offset = 0
    pages = [p for p in sorted(folios) if folios[p]]
    for n, p in enumerate(pages):
        if any(v - p == offset for v in folios[p]):
            continue
        following = {v - pages[n + 1] for v in folios[pages[n + 1]]} if n + 1 < len(pages) else None
        if following is not None and offset in following:
            continue
        value = next((v for v in folios[p] if following is None or v - p in following), None)
        if value is not None:
            starts[p] = value
            offset = value - p
    return starts


def folio_typst(p: Placement, size: float) -> str:
    """A folio printed by the page counter, in the scan's folio box and with the scan's decoration."""
    style = "i" if re.search(r"[ivxlc]", p.text) else "1"
    markup = re.sub(r"[ivxlc]+|\d+", f"#context counter(page).display({typst_string(style)})", p.text.replace("[", "\\[").replace("]", "\\]"), count=1)
    return (
        f"#place(top + left, dx: {p.left:.2f}pt, dy: {p.top:.2f}pt, "
        f"inkfit({p.right - p.left:.2f}pt, {p.bottom - p.top:.2f}pt, text(size: {size:.2f}pt, [{markup}])))"
    )


def ends_sentence(latex: str) -> bool:
    return re.sub(r"(\\end\{\w+\*?\}|\\\\|\s|\})+$", "", latex).endswith(".")


def table_typst(html: str, math: dict[tuple[str, bool], str]) -> str:
    rows = [
        [" ".join(chunk_markup(c, math) for c in chunks(cell)) for cell in CELL_RE.findall(row)]
        for row in ROW_RE.findall(html)
    ]
    columns = max((len(r) for r in rows), default=0)
    if not columns:
        return ""
    cells = ", ".join(f"[{cell}]" for row in rows for cell in row + [""] * (columns - len(row)))
    return f"#align(center, table(columns: {columns}, stroke: 0.4pt, inset: 3pt, {cells}))"


def cell_text(cell: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cell)).strip()


def table_cells(markdown: str) -> list[list[TableCell]]:
    """Each HTML or pipe table's non-empty cells on its grid, in the order `table_text` reads them. A cell takes the
    first column its row leaves free of the cells spanning down from the rows above."""
    tables = []
    for table in re.finditer(r"<table\b.*?</table>", markdown, flags=re.DOTALL):
        taken: set[tuple[int, int]] = set()
        cells = []
        for r, row in enumerate(ROW_RE.findall(table[0])):
            col = 0
            for attrs, inner in CELL_TAG_RE.findall(row):
                while (r, col) in taken:
                    col += 1
                spans = dict(SPAN_RE.findall(attrs))
                across, down = int(spans.get("col", 1)), int(spans.get("row", 1))
                taken |= {(r + i, col + j) for i in range(down) for j in range(across)}
                if text := cell_text(inner):
                    cells.append(TableCell(r, col, across, text, down))
                col += across
        tables.append(cells)
    rows: list[list[str]] = []
    for line in [*markdown.split("\n"), ""]:
        if PIPE_ROW_RE.fullmatch(line):
            if not PIPE_RULE_RE.fullmatch(line):
                rows.append(line.strip().strip("|").split("|"))
        elif rows:
            tables.append([TableCell(r, c, 1, t) for r, row in enumerate(rows) for c, cell in enumerate(row) if (t := cell_text(cell))])
            rows = []
    return [cells for cells in tables if cells]


def table_text(markdown: str) -> str:
    """The transcript with each HTML or pipe table turned into plain text, one line of non-empty cells per row."""

    def row_text(cells: list[str]) -> str:
        return " ".join(c for cell in cells if (c := cell_text(cell)))

    def rows(table: re.Match[str]) -> str:
        return "\n".join(line for row in ROW_RE.findall(table[0]) if (line := row_text(CELL_RE.findall(row))))

    out = []
    for line in re.sub(r"<table\b.*?</table>", rows, markdown, flags=re.DOTALL).split("\n"):
        if PIPE_ROW_RE.fullmatch(line):
            if PIPE_RULE_RE.fullmatch(line):
                continue
            line = row_text(line.strip().strip("|").split("|"))
            if not line:
                continue
        out.append(line)
    return "\n".join(out)


def chinese_number(digits: str) -> int:
    if digits.isdigit():
        return int(digits)
    if "十" not in digits:
        return CHINESE_DIGITS.index(digits) + 1
    tens, ones = digits.split("十")
    return (CHINESE_DIGITS.index(tens) + 1 if tens else 1) * 10 + (CHINESE_DIGITS.index(ones) + 1 if ones else 0)


def roman_number(text: str) -> int:
    values = [ROMAN_VALUES[c] for c in text]
    return sum(-v if i + 1 < len(values) and v < values[i + 1] else v for i, v in enumerate(values))


@dataclass(frozen=True)
class Heading:
    """A chapter (level 1) or section (level 2) heading as printed: its number, the Typst numbering pattern
    that prints the number the same way, and its title."""

    level: int
    number: int
    pattern: str
    title: str


def book_heading(text: str) -> Heading | None:
    if m := CHAPTER_HEAD_RE.fullmatch(text):
        return Heading(1, chinese_number(m[2]), m[1] + ("1" if m[2].isdigit() else "一") + m[3], m[4])
    if m := SECTION_HEAD_RE.fullmatch(text):
        return Heading(2, int(m[2]), m[1] + "1" + m[3], m[4])
    return None


def title_key(text: str) -> str:
    return re.sub(r"\W", "", text)


def contents_pages(texts: dict[int, str]) -> range:
    """The contents pages: from the first page that lists a chapter or section with its page number, through the
    pages after it where at least `CONTENTS_SHARE` of the lines end in a page number. An index at the back is not
    in the run."""
    def share(p: int) -> float:
        entries = line_entries(texts.get(p) or "") or []
        return sum(bool(TOC_ENTRY_RE.fullmatch(t)) for t, _ in entries) / max(1, len(entries))

    start = next(
        (
            p for p in sorted(texts)
            if any((m := TOC_ENTRY_RE.fullmatch(t)) and book_heading(m[1]) for t, _ in line_entries(texts[p] or "") or [])
        ),
        None,
    )
    if start is None:
        return range(0)
    end = start
    while share(end + 1) >= CONTENTS_SHARE:
        end += 1
    return range(start, end + 1)


def contents_parts(texts: dict[int, str], contents: range) -> dict[str, int]:
    """The unnumbered titles, such as an introduction or an index, that one line of the `contents` pages lists with
    a page number and that the body sets as a heading, keyed by their letters. Numbered articles and titles listed
    again and again, such as each section's exercises, are not parts."""
    entries = {p: line_entries(markdown or "") or [] for p, markdown in texts.items()}
    headings = {title_key(text) for p, es in entries.items() if p not in contents for text, bold in es if bold}
    listed = [
        m[1] for p in contents for text, _ in entries.get(p, [])
        if (m := TOC_ENTRY_RE.fullmatch(text)) and book_heading(m[1]) is None and not RUN_IN_RE.match(m[1])
    ]
    counts = Counter(title_key(title) for title in listed)
    parts: dict[str, int] = {}
    for title in listed:
        if counts[title_key(title)] == 1 and title_key(title) in headings:
            parts.setdefault(title_key(title), len(parts))
    return parts


@dataclass
class Outline:
    """The book's chapter and section headings in reading order. Each heading gets a Typst heading whose counter
    prints its number, a label the contents entries refer to, and a counter update where the count misses the
    printed number (`resyncs`)."""

    parts: dict[str, int]
    scope: str = "chap-0"
    chapter: int = 0
    section: int = 0
    contents_scope: str = "chap-0"
    seen: set[str] = field(default_factory=set)
    labels: set[str] = field(default_factory=set)
    refs: set[str] = field(default_factory=set)
    resyncs: int = 0
    in_contents: bool = False

    def heading(self, text: str, markup: Callable[[str], str]) -> tuple[str, str, str] | None:
        """For a body heading line: the Typst heading, the markup that prints its number, and its title.
        None on a contents page, and for a line that is not a chapter, a section or a listed part, that ends in a
        page number, or that repeats one already seen."""
        key = title_key(text)
        h = book_heading(text)
        if self.in_contents or TOC_ENTRY_RE.fullmatch(text) or key in self.seen or (h is None and key not in self.parts):
            return None
        self.seen.add(key)
        update = ""
        if h is None:
            label = f"part-{self.parts[key]}"
            if self.chapter:
                self.scope = label
            title, level, pattern = text, 1, "none"
        elif h.level == 1:
            if h.number != self.chapter + 1:
                update, self.resyncs = f"#counter(heading).update(({h.number - 1},))", self.resyncs + 1
            self.chapter, self.section = h.number, 0
            self.scope = label = f"chap-{h.number}"
            title, level, pattern = h.title, 1, typst_string(h.pattern)
        else:
            if h.number != self.section + 1:
                update, self.resyncs = f"#counter(heading).update(({self.chapter}, {h.number - 1}))", self.resyncs + 1
            self.section = h.number
            label = f"{self.scope}-sec-{h.number}"
            title, level, pattern = h.title, 2, typst_string(h.pattern)
        self.labels.add(label)
        lead = "" if h is None else f"#context numbering({pattern}, counter(heading).get().last())"
        return f"{update}#heading(level: {level}, numbering: {pattern}, outlined: true)[{markup(title)}] <{label}>", lead, title

    def entry(self, text: str) -> tuple[str, str, str] | None:
        """For a contents line: the markup that prints the number of the heading it names, the line without that
        number, and the markup that prints the heading's page. None off the contents pages and for a line that
        names no heading."""
        m = TOC_ENTRY_RE.fullmatch(text)
        if m is None or not self.in_contents:
            return None
        title, page = m[1], m[2]
        h = book_heading(title)
        if h is None:
            if title_key(title) not in self.parts:
                return None
            label = f"part-{self.parts[title_key(title)]}"
            if self.contents_scope != "chap-0":
                self.contents_scope = label
            lead = ""
        else:
            if h.level == 1:
                self.contents_scope = label = f"chap-{h.number}"
            else:
                label = f"{self.contents_scope}-sec-{h.number}"
            printed = title[: len(title) - len(h.title)].strip()
            title = h.title
            lead = f"#facsimile-ref(<{label}>, h => numbering(h.numbering, counter(heading).at(h.location()).last()), {typst_string(printed)})"
        self.refs.add(label)
        page_markup = f"#facsimile-ref(<{label}>, h => str(counter(page).at(h.location()).first()), {typst_string(page)})"
        return lead, f"{title} {page}", page_markup


def image_typst(alt: str, path: Path, max_width: float) -> str:
    with Image.open(path) as image:
        width = min(max_width, image.width * PT_PER_PX)
    return f'#align(center, stack(spacing: 0.5em, image("{path}", width: {width:.2f}pt), text(size: 0.9em, {typst_string(alt)})))'


def flow_markup(
    markdown: str,
    math: dict[tuple[str, bool], str],
    seen_headings: set[str],
    root: Path | None = None,
    max_width: float = 0.0,
    outline: Outline | None = None,
) -> str:
    out: list[str] = []
    indent = False
    run_in = ""
    notes_start: int | None = None
    for paragraph in re.split(r"\n\s*\n", without_diagrams(markdown).strip()):
        if not out and FOLIO_RE.fullmatch(paragraph):
            continue
        if notes_start is None and NOTE_RE.match(paragraph):
            notes_start = len(out) + bool(run_in)
        heading = re.fullmatch(r"(#+)\s+(.+?)\s*", paragraph, re.DOTALL)
        if run_in and (heading or not chunks(paragraph) or chunks(paragraph)[0][0].kind == "display"):
            out.append(run_in)
            run_in = ""
        if TABLE_RE.fullmatch(paragraph):
            out.append(table_typst(paragraph, math))
            indent = False
            continue
        if (image := IMAGE_RE.fullmatch(paragraph)) and root and (root / image[2]).exists():
            out.append(image_typst(image[1], (root / image[2]).resolve(), max_width))
            continue
        key = re.sub(r"\W", "", heading[2]) if heading else ""
        if heading and not out and key in seen_headings:
            continue
        if heading:
            seen_headings.add(key)
            title = " ".join(chunk_markup(c, math) for c in chunks(heading[2]))
            if RUN_IN_RE.match(heading[2]):
                run_in = f'#h(2em)#text(weight: "bold")[{title}]'
            elif outline is not None and (numbered := outline.heading(heading[2], lambda t: " ".join(chunk_markup(c, math) for c in chunks(t)))):
                out.append(numbered[0])
            else:
                out.append(f"#heading(level: {len(heading[1])}, outlined: false, [{title}])")
            indent = True
            continue
        run: list[str] = []
        for c in [*chunks(paragraph), None]:
            if c is not None and c[0].kind != "display":
                run.append(chunk_markup(c, math))
                continue
            if run:
                lead = f"{run_in} " if run_in else "#h(2em)" if indent else ""
                out.append(lead + " ".join(run))
                run, indent, run_in = [], True, ""
            if c is not None:
                out.append(chunk_markup(c, math))
                indent = ends_sentence(c[0].text)
    if run_in:
        out.append(run_in)
    if notes_start is not None and notes_start < len(out):
        notes = "\n\n".join(out[notes_start:])
        out[notes_start:] = [FOOTNOTE_RULE, f"#text(size: {FOOTNOTE_SIZE}em)[\n{notes}\n]"]
    return "\n\n".join(out)


def book_pitch(pages: Sequence[tuple[np.ndarray, Frame]]) -> float:
    """The glyph advance (pt) of a book's body text: the strongest repeat in the ink profiles of its text lines,
    between `PITCH_RANGE` times the median line height."""
    line = float(np.median([f.line for _, f in pages])) / PT_PER_PX
    lo, hi = round(PITCH_RANGE[0] * line), round(PITCH_RANGE[1] * line)
    total = np.zeros(hi - lo)
    for ink, frame in pages:
        w = ink.shape[1]
        for a, b in ink_bands(ink):
            if ink[a:b].sum() <= SPECK_MAX_PX or a * PT_PER_PX < frame.top or b * PT_PER_PX > frame.bottom:
                continue
            profile = ink[a:b].sum(axis=0).astype(float)
            profile -= profile.mean()
            f = np.fft.rfft(profile, 2 * w)
            ac = np.fft.irfft(f * np.conj(f))
            if ac[0] > 0:
                total += ac[lo:hi] / ac[0]
    if not total.any():
        return line * PT_PER_PX
    return (lo + int(np.argmax(total))) * PT_PER_PX


def flow_typst(frame: Frame, size: float, markup: str) -> list[str]:
    width = size * max(1, round((frame.right - frame.left) / size))
    out = [
        (
            f"#place(top + left, dx: {(frame.left + frame.right - width) / 2:.2f}pt, dy: {frame.top:.2f}pt, "
            f"flowfit({width:.2f}pt, {frame.bottom - frame.top:.2f}pt, {size:.2f}pt, [\n{markup}\n]))"
        )
    ]
    if frame.rule:
        l, t, r, b = frame.rule
        out.append(
            f"#place(top + left, dx: {l:.2f}pt, dy: {(t + b) / 2:.2f}pt, line(length: {r - l:.2f}pt, stroke: {min(1.0, max(0.4, (b - t) / 2)):.2f}pt))"
        )
    return out


def line_entries(markdown: str) -> list[tuple[str, bool]] | None:
    """The transcript as (text, is_heading) lines, with run-together contents entries split at each page number
    and each display formula kept whole with its `$$`; None when it holds a table or an image, which only flow mode sets."""
    text = without_diagrams(markdown)
    if TABLE_RE.search(text) or IMAGE_RE.search(text):
        return None
    out: list[tuple[str, bool]] = []
    for segment in re.split(r"(\$\$.*?\$\$)", text, flags=re.DOTALL):
        if segment.startswith("$$"):
            out.append((segment, False))
            continue
        for raw in segment.splitlines():
            line = raw.strip()
            if not line or FOLIO_RE.fullmatch(line) or ROMAN_FOLIO_RE.fullmatch(line):
                continue
            heading = re.fullmatch(r"#+\s+(.+)", line)
            out += [(e, bool(heading)) for e in ENTRY_RE.split(heading[1] if heading else line)]
    return out


def text_columns(ink: np.ndarray, frame: Frame) -> list[tuple[int, int]]:
    """One column, or two when a blank gutter at least `GUTTER_LINES` lines wide runs down the middle of the text block."""
    top, bottom = round(frame.top / PT_PER_PX), round(frame.bottom / PT_PER_PX)
    w = ink.shape[1]
    lo, hi = int(0.3 * w), int(0.7 * w)
    blank = np.flatnonzero(~ink[top:bottom, lo:hi].any(axis=0))
    if not blank.size:
        return [(0, w)]
    runs = np.split(blank, np.flatnonzero(np.diff(blank) > 1) + 1)
    gutter = max(runs, key=len)
    if len(gutter) * PT_PER_PX < GUTTER_LINES * frame.line:
        return [(0, w)]
    cut = lo + int(gutter[len(gutter) // 2])
    return [(0, cut), (cut, w)]


def column_lines(ink: np.ndarray, frame: Frame, x0: int, x1: int) -> list[tuple[int, int]]:
    top, bottom = round(frame.top / PT_PER_PX), round(frame.bottom / PT_PER_PX)
    sub = ink[top:bottom, x0:x1]
    bands = [(top + a, top + b) for a, b in ink_bands(sub) if sub[a:b].sum() > SPECK_MAX_PX]
    return [(a, b) for a, b in bands if (b - a) * PT_PER_PX >= DUST_LINE_SHARE * frame.line]


def glyph_count(text: str) -> float:
    """Glyph advances of a line in ems: a CJK glyph is one, anything else about half; inline math counts its
    letters and digits, not its LaTeX commands."""
    text = re.sub(r"\$([^$]*)\$", lambda m: "".join(c for c in re.sub(r"\\[A-Za-z]+", "", m[1]) if c.isalnum()), text)
    return sum(1.0 if ord(c) >= 0x2E80 else 0.55 for c in text if not c.isspace() and c != "*")


def text_lines(ink: np.ndarray, frame: Frame) -> list[tuple[int, int, int, int]]:
    """The scan's text lines as (x0, x1, top, bottom) px, column by column."""
    return [(x0, x1, a, b) for x0, x1 in text_columns(ink, frame) for a, b in column_lines(ink, frame, x0, x1)]


def comparable(text: str) -> list[tuple[str, int]]:
    """The letters and digits of `text` with their indices, for matching against OCR; inside inline math,
    LaTeX command names are left out."""
    out, math = [], False
    commands = {i for m in re.finditer(r"\\[A-Za-z]+", text) for i in range(m.start(), m.end())}
    for i, c in enumerate(text):
        if c == "$":
            math = not math
        elif c.isalnum() and not (math and i in commands):
            out.append((unicodedata.normalize("NFKC", c).lower(), i))
    return out


def split_by_gaps(bands: list[Band], parts: int) -> list[list[Band]]:
    """`bands` in `parts` groups, cut at the widest vertical gaps between neighbours."""
    gaps = sorted(range(1, len(bands)), key=lambda k: bands[k][2] - bands[k - 1][3], reverse=True)[: parts - 1]
    cuts = [0, *sorted(gaps), len(bands)]
    return [bands[a:b] for a, b in itertools.pairwise(cuts)]


def ocr_line_entries(
    entries: list[tuple[str, bool]], ink: np.ndarray, frame: Frame, lines: tuple[OcrLine, ...]
) -> list[tuple[str, bool, list[Band]]] | None:
    """The transcript cut at the scan's own line breaks. Each scan line's OCR text is matched into the transcript;
    a line whose OCR mostly matches, and not only inside inline formulas, is a text line. Its cut falls at the
    first line break, else the last space, between its last matched letter or digit and the next line's first,
    and after the inline formula holding it. Each display formula takes the other scan lines between the text
    lines around it.
    Text before the first text line, a heading that repeats the running head, is dropped.
    None when the match is weak or a display formula has no scan line of its own."""
    bands = text_lines(ink, frame)
    h, w = ink.shape
    ocr = [""] * len(bands)
    for ln in lines:
        cx, cy = (ln.x + ln.w / 2) * w, (1 - ln.y - ln.h / 2) * h
        k = next((k for k, (x0, x1, a, b) in enumerate(bands) if x0 <= cx < x1 and a - 2 <= cy <= b + 2), None)
        if k is not None:
            ocr[k] += ln.text
    displays = [e for e, _ in entries if e.startswith("$$")]
    text = "\n".join(DISPLAY_MARK if e.startswith("$$") else e for e, _ in entries)
    heads = [False] * len(text)
    pos = 0
    for e, bold in entries:
        size = 1 if e.startswith("$$") else len(e)
        heads[pos : pos + size] = [bold] * size
        pos += size + 1
    t = comparable(text)
    o, owner = [], []
    for k, band_text in enumerate(ocr):
        chars = [c for c, _ in comparable(band_text)]
        o += chars
        owner += [k] * len(chars)
    if not t or not o:
        return None
    blocks = difflib.SequenceMatcher(None, [c for c, _ in t], o, autojunk=False).get_matching_blocks()
    if 2 * sum(b.size for b in blocks) < MATCH_SHARE * (len(t) + len(o)):
        return None
    hits: dict[int, list[int]] = {}
    for b in blocks:
        for j in range(b.size):
            hits.setdefault(owner[b.b + j], []).append(t[b.a + j][1])
    counts = [len(comparable(s)) for s in ocr]
    in_math = list(itertools.accumulate((c == "$" for c in text), lambda odd, dollar: odd != dollar))
    text_bands = [
        k for k in range(len(bands))
        if len(hits.get(k, ())) >= max(1, TEXT_LINE_SHARE * counts[k]) and not all(in_math[i] for i in hits[k])
    ]
    if not text_bands:
        return None
    cuts, last = [], -1
    for n, k in enumerate(text_bands):
        last = max(last, max(hits[k]))
        cut = last + 1
        if n + 1 < len(text_bands):
            gap_end = min(hits[text_bands[n + 1]])
            if (space := text.find("\n", cut, gap_end)) < 0:
                space = text.rfind(" ", cut, gap_end)
            if space >= 0:
                cut = space + 1
        breaks = [i + 1 for i in range(max(cut - NEAR_BREAK, cuts[-1] if cuts else 0), min(cut + NEAR_BREAK, len(text))) if text[i] == "\n"]
        if breaks:
            cut = min(breaks, key=lambda b: abs(b - cut))
        if text[:cut].count("$") % 2:
            if (close := text.find("$", cut)) < 0:
                return None
            cut = close + 1
        cuts.append(cut)
    start = min(hits[text_bands[0]])
    if (entry_start := text.rfind("\n", 0, start) + 1) >= start - NEAR_BREAK:
        start = entry_start
    if text[:start].count("$") % 2:
        start = text.rindex("$", 0, start)
    marks = [i for i, c in enumerate(text) if c == DISPLAY_MARK]
    out: list[tuple[str, bool, list[Band]]] = []
    for n, k in enumerate(text_bands):
        a, b = (cuts[n - 1] if n else start), (cuts[n] if n + 1 < len(text_bands) else len(text))
        piece = " ".join(text[a:b].replace(DISPLAY_MARK, " ").split())
        if piece:
            out.append((piece, all(heads[i] for i in range(a, b) if not text[i].isspace() and text[i] != DISPLAY_MARK), [bands[k]]))
    firsts = [min(hits[k]) for k in text_bands]
    gap_of = [sum(f < i for f in firsts) for i in marks]
    bounds = [-1, *text_bands, len(bands)]
    for g in range(len(bounds) - 1):
        here = [displays[m] for m, gap in enumerate(gap_of) if gap == g]
        loose = bands[bounds[g] + 1 : bounds[g + 1]]
        if not here:
            out += [("", False, [band]) for band in loose]
            continue
        if len(loose) < len(here):
            return None
        out += [(latex, False, group) for latex, group in zip(here, split_by_gaps(loose, len(here)), strict=True)]
    return out


def line_typst(
    ink: np.ndarray, band: Band, text: str, bold: bool, frame: Frame, size: float, math: dict[tuple[str, bool], str],
    lead: str = "", page: str = "",
) -> list[str] | None:
    """One transcript line set in one scan line: the text fills the line's ink, and a trailing page number past a
    leader goes on the right with the leader dots between. None when the text is too long for the line."""
    x0, x1, a, b = band
    out = []
    sub = ink[a:b, x0:x1]
    inked = sub.any(axis=0)
    first, last = sub.argmax(axis=0), sub.shape[0] - 1 - sub[::-1].argmax(axis=0)
    cols = np.flatnonzero(inked & (last - first + 1 >= TALL_SHARE * (b - a)))
    if not cols.size:
        cols = np.flatnonzero(sub.any(axis=0))
    if glyph_count(text) * size > LOCK_FILL * (cols[-1] + 1 - cols[0]) * PT_PER_PX + 2 * size:
        return None
    runs = np.split(cols, np.flatnonzero(np.diff(cols) > RUN_GAP_LINES * frame.line / PT_PER_PX) + 1)
    runs = [r for r in runs if sub[:, r[0] : r[-1] + 1].sum() > SPECK_MAX_PX] or runs
    number = re.fullmatch(r"(.*\S)\s+(\d+)", text)
    parts = [(text, runs[0][0], runs[-1][-1] + 1)]
    if number and len(runs) > 1:
        parts = [(number[1], runs[0][0], runs[-2][-1] + 1), (number[2], runs[-1][0], runs[-1][-1] + 1)]
        gap_l, gap_r = (x0 + runs[-2][-1] + 1) * PT_PER_PX, (x0 + runs[-1][0]) * PT_PER_PX
        dots = np.flatnonzero(sub[:, runs[-2][-1] + 1 : runs[-1][0]].any(axis=0))
        if dots.size and np.count_nonzero(np.diff(dots) > 1) + 1 >= LEADER_DOTS:
            out.append(
                f"#place(top + left, dx: {gap_l + size / 4:.2f}pt, dy: {b * PT_PER_PX:.2f}pt, "
                f'box(width: {gap_r - gap_l - size / 2:.2f}pt, repeat(text(size: {size:.2f}pt, ". "))))'
            )
    for n, (part, l, r) in enumerate(parts):
        rows = np.flatnonzero(sub[:, l:r].any(axis=1))
        markup = " ".join(chunk_markup(c, math) for c in chunks(part))
        if n and page:
            markup = page
        elif page and number:
            markup = " ".join(chunk_markup(c, math) for c in chunks(number[1])) + " " + page
        if not n and lead:
            markup = f"{lead} {markup}"
        weight = ', weight: "bold"' if bold else ""
        body = f"text(size: {size:.2f}pt{weight}, [{markup}])"
        out.append(
            f"#place(top + left, dx: {(x0 + l) * PT_PER_PX:.2f}pt, dy: {(a + rows[0]) * PT_PER_PX:.2f}pt, "
            f"inkfit({(r - l) * PT_PER_PX:.2f}pt, {(rows[-1] + 1 - rows[0]) * PT_PER_PX:.2f}pt, {body}))"
        )
    return out


def display_typst(ink: np.ndarray, bands: list[Band], latex: str, size: float, math: dict[tuple[str, bool], str]) -> str:
    """A display formula stretched over the ink of the scan lines it takes."""
    x0, x1 = min(band[0] for band in bands), max(band[1] for band in bands)
    top, bottom = min(band[2] for band in bands), max(band[3] for band in bands)
    sub = ink[top:bottom, x0:x1]
    cols = np.flatnonzero(sub.any(axis=0))
    runs = [r for r in np.split(cols, np.flatnonzero(np.diff(cols) > 1) + 1)
            if sub[:, r[0] : r[-1] + 1].sum() > SPECK_MAX_PX] or [cols]
    l, r = runs[0][0], runs[-1][-1] + 1
    return (
        f"#place(top + left, dx: {(x0 + l) * PT_PER_PX:.2f}pt, dy: {top * PT_PER_PX:.2f}pt, "
        f"inkfit({(r - l) * PT_PER_PX:.2f}pt, {(bottom - top) * PT_PER_PX:.2f}pt, text(size: {size:.2f}pt, box($ {math[(chunks(latex)[0][0].text, True)]} $))))"
    )


def crop_typst(ink: np.ndarray, band: Band, path: Path) -> str:
    """The scan's own ink in a line the transcript does not hold, such as a figure or its caption, as a 1-bit image."""
    x0, x1, a, b = band
    cols = np.flatnonzero(ink[a:b, x0:x1].any(axis=0))
    l, r = x0 + int(cols[0]), x0 + int(cols[-1]) + 1
    Image.fromarray(~ink[a:b, l:r]).save(path)
    return (
        f'#place(top + left, dx: {l * PT_PER_PX:.2f}pt, dy: {a * PT_PER_PX:.2f}pt, '
        f'image("{path.resolve()}", width: {(r - l) * PT_PER_PX:.2f}pt, height: {(b - a) * PT_PER_PX:.2f}pt))'
    )


def without_figure_words(text: str, art_lines: Sequence[str]) -> str:
    """The transcript without its figure image links and without lines, such as legends, whose every word the
    scan prints inside a figure's art."""
    art = "".join(re.sub(r"\W", "", s) for s in art_lines)

    def in_art(line: str) -> bool:
        if line.lstrip().startswith("#"):
            return False
        words = [re.sub(r"\W", "", w) for w in line.split()]
        return bool(words) and all(w and w in art for w in words)

    lines = text.split("\n")
    return "\n".join(line for line in lines if not re.fullmatch(r"\s*!\[[^\]]*\]\([^)]*\)\s*", line) and not in_art(line))


def figure_crop_typst(page: pymupdf.Page, box: tuple[float, float, float, float], path: Path) -> str:
    """The scan's own figure art inside `box` (page fractions l, t, r, b) as a gray image, placed where it sits."""
    w, h = page.rect.width, page.rect.height
    clip = pymupdf.Rect(box[0] * w, box[1] * h, box[2] * w, box[3] * h)
    page.get_pixmap(dpi=SCAN_DPI, clip=clip, colorspace=pymupdf.csGRAY).save(path)
    return (
        f"#place(top + left, dx: {clip.x0:.2f}pt, dy: {clip.y0:.2f}pt, "
        f'image("{path.resolve()}", width: {clip.width:.2f}pt, height: {clip.height:.2f}pt))'
    )


def placed_typst(
    ink: np.ndarray,
    frame: Frame,
    placed: list[tuple[str, bool, list[Band]]],
    size: float,
    math: dict[tuple[str, bool], str],
    crops: Path | None = None,
    outline: Outline | None = None,
) -> list[str] | None:
    """Every transcript line and display formula set in the scan lines it was given, plus the header rule.
    A scan line with no transcript text becomes a crop saved as `crops`_N.png; without `crops` it stays blank.
    With `outline`, a chapter or section heading line becomes a Typst heading, and a contents line takes its
    number and page from the heading it names."""
    out = []
    for n, (text, bold, bands) in enumerate(placed):
        if not text:
            if crops is not None:
                out.append(crop_typst(ink, bands[0], crops.with_name(f"{crops.name}_{n}.png")))
            continue
        if text.startswith("$$"):
            out.append(display_typst(ink, bands, text, size, math))
            continue
        lead = page = ""
        if outline is not None and (entry := outline.entry(text)):
            lead, text, page = entry
        elif outline is not None and bold and (heading := outline.heading(text, lambda t: " ".join(chunk_markup(c, math) for c in chunks(t)))):
            hidden, lead, text = heading
            x0, _, a, _ = bands[0]
            out.append(f"#place(top + left, dx: {x0 * PT_PER_PX:.2f}pt, dy: {a * PT_PER_PX:.2f}pt, hide[{hidden}])")
        if (line := line_typst(ink, bands[0], text, bold, frame, size, math, lead, page)) is None:
            return None
        out += line
    if frame.rule:
        out += flow_typst(frame, size, "")[1:]
    return out


def dropped_headings(
    entries: list[tuple[str, bool]],
    placed: list[tuple[str, bool, list[Band]]],
    frame: Frame,
    outline: Outline,
    math: dict[tuple[str, bool], str],
) -> list[str]:
    """The chapter and section headings that line locking dropped as copies of the running head, as hidden
    Typst headings at the top of the text block, so a section that opens a page still counts."""
    shown = {title_key(text) for text, _, _ in placed}
    return [
        f"#place(top + left, dx: {frame.left:.2f}pt, dy: {frame.top:.2f}pt, hide[{heading[0]}])"
        for text, bold in entries
        if bold and title_key(text) not in shown
        and (heading := outline.heading(text, lambda t: " ".join(chunk_markup(c, math) for c in chunks(t))))
    ]


def counted_lines(entries: list[tuple[str, bool]], ink: np.ndarray, frame: Frame) -> list[tuple[str, bool, list[Band]]] | None:
    """Transcript lines paired with scan lines in order, column by column, when they are as many (after leading
    headings, which repeat the running head) and none is a display formula; else None."""
    bands = text_lines(ink, frame)
    while entries and len(entries) > len(bands) and entries[0][1]:
        entries = entries[1:]
    if not bands or len(entries) != len(bands) or any(e.startswith("$$") for e, _ in entries):
        return None
    return [(e, bold, [band]) for (e, bold), band in zip(entries, bands, strict=True)]


@dataclass(frozen=True)
class Diagram:
    fig: str
    left: float
    top: float
    width: float
    height: float
    ink_inset: tuple[float, float, float, float]
    ink_size: tuple[float, float]


def locate_diagrams(
    doc: pymupdf.Document, work: Path, style: FacsimileStyle
) -> dict[int, list[Diagram]]:
    """Scan position of every fletcher diagram, keyed by 1-based page: the ink inside the style's known
    box for the diagram, else the best match of the snippet's ink on the page."""
    known = style.diagram_boxes() if style.diagram_boxes else {}
    found: dict[int, list[Diagram]] = {}
    for src in sorted(style.diagram_dir.glob("fig_*.typ")):
        fig = src.stem.removeprefix("fig_")
        page = int(fig.split("_")[0])
        tmpl, inset = diagram_ink(src, work, SCAN_DPI, style.diagram_text)
        ink = page_ink(doc[page - 1])
        if fig in known:
            l, t, r, b = known[fig]
            ys, xs = np.where(ink[t:b, l:r])
            x, y, tw, th = (
                l + int(xs.min()),
                t + int(ys.min()),
                int(np.ptp(xs)) + 1,
                int(np.ptp(ys)) + 1,
            )
        else:
            y, x, th, tw, _ = find_diagram(
                ink, tmpl, scales=(0.9, 0.95, 1.0, 1.05, 1.1, 1.15)
            )
        ink_size = (tmpl.shape[1] * PT_PER_PX, tmpl.shape[0] * PT_PER_PX)
        found.setdefault(page, []).append(
            Diagram(
                fig,
                x * PT_PER_PX,
                y * PT_PER_PX,
                tw * PT_PER_PX,
                th * PT_PER_PX,
                inset,
                ink_size,
            )
        )
    return found


def diagram_typst(d: Diagram) -> str:
    """The snippet scaled so its ink box covers the diagram's ink box on the scan."""
    l, t, _, _ = d.ink_inset
    ink_w, ink_h = d.ink_size
    sx, sy = d.width / ink_w, d.height / ink_h
    return (
        f"#place(top + left, dx: {d.left - l * sx:.2f}pt, dy: {d.top - t * sy:.2f}pt, "
        f'scale(x: {sx * 100:.1f}%, y: {sy * 100:.1f}%, origin: top + left, reflow: false, diagram-text(include "figures/fig_{d.fig}.typ")))'
    )


def preamble(style: FacsimileStyle) -> str:
    dt = style.diagram_text
    return f"""#set document(title: "{style.title}")
#set text(font: {style.font_stack}, size: {style.size}pt, weight: {style.weight}, number-type: "lining", top-edge: "baseline", bottom-edge: "baseline")
#let word(s) = text(s)
#let facsimile-number(it) = if it.numbering == none [] else [#numbering(it.numbering, counter(heading).at(it.location()).last()) ]
#let facsimile-ref(target, shown, fallback) = context {{ let q = query(target); if q.len() > 0 {{ link(q.first().location(), shown(q.first())) }} else {{ fallback }} }}
#let running-head(fallback) = context {{
  let chapters = query(heading.where(outlined: true, level: 1).before(here()))
  if chapters.len() == 0 {{ return fallback }}
  let sections = query(heading.where(outlined: true, level: 2).after(chapters.last().location()).before(here()))
  let h = if calc.odd(counter(page).get().first()) and sections.len() > 0 {{ sections.last() }} else {{ chapters.last() }}
  [#facsimile-number(h)#h.body]
}}
#let fit(w, body) = context {{ let n = measure(body).width; if n > 0pt {{ scale(x: calc.min(w / n, {MAX_SCALE}) * 100%, origin: top + left, reflow: false, body) }} else {{ body }} }}
#let inkfit(w, h, body) = context {{ let b = {{ set text(top-edge: "bounds", bottom-edge: "bounds"); body }}; let m = measure(b); if m.width > 0pt and m.height > 0pt {{ scale(x: calc.min(w / m.width, 2) * 100%, y: calc.min(h / m.height, 2) * 100%, origin: top + left, reflow: false, b) }} else {{ b }} }}
#let flowfit(w, h, line, body) = context {{
  let set-body(size, leading) = block(width: w, {{
    set text(size: size, top-edge: "cap-height", bottom-edge: "baseline")
    set par(justify: true, leading: leading * 1em, spacing: leading * 1em)
    show heading: it => block(above: leading * 1em, below: leading * 1em, text(size: if it.level == 1 {{ 1.8em }} else {{ 1.1em }}, weight: "bold", [#facsimile-number(it)#it.body]))
    body
  }})
  let lo = line
  if measure(set-body(line, {LEADING_RANGE[0]})).height > h {{
    let hi = line
    lo = line / 2
    for _ in range(10) {{
      let mid = (lo + hi) / 2
      if measure(set-body(mid, {LEADING_RANGE[0]})).height <= h {{ lo = mid }} else {{ hi = mid }}
    }}
  }}
  let (a, b) = {LEADING_RANGE}
  if measure(set-body(lo, b)).height <= h {{ a = b }} else {{
    for _ in range(8) {{
      let mid = (a + b) / 2
      if measure(set-body(lo, mid)).height <= h {{ a = mid }} else {{ b = mid }}
    }}
  }}
  set-body(lo, a)
}}
#let diagram-text(body) = {{ set text(font: "{dt.font}", size: {dt.size}pt, weight: {dt.weight}, top-edge: "cap-height", bottom-edge: "baseline"); body }}
"""


_STRICT_WORKER: dict = {}


def _start_strict_worker(scan_ink: InkCache, scan_faint: InkCache, cache: Path, font_file: Path, family: str, size: float) -> None:
    font = ImageFont.truetype(str(font_file), 100, index=face_index(font_file, family))
    _STRICT_WORKER.update(ink=scan_ink, faint=scan_faint, cache=cache, font=font, size=size)


def _strict_job(
    job: tuple[int, list, list[Chunk], dict[tuple[str, bool], str], list[list[TableCell]]],
) -> tuple[int, list[str], list[dict]]:
    p, skip, page_chunks, math, cells = job
    w = _STRICT_WORKER
    lines = read_source_page(w["cache"], p).lines
    body, found = strict_page(p, w["ink"](p), lines, skip, page_chunks, math, w["font"], w["size"], w["faint"](p), cells)
    return p, body, found


def build_facsimile(
    source: Path, out_dir: Path, languages: Sequence[str], style: FacsimileStyle, pages: set[int] | None = None
) -> Path:
    """Write and compile the facsimile edition of the `source` scan; returns the PDF path.

    Strict pages are set in parallel, and each one's Typst and mismatches are kept in `facsimile/pages/`.
    With `pages`, only those strict pages are set again and every other one reuses its kept result."""
    if pages is not None and not (style.strict_lines and not style.flow):
        raise ValueError(f"{style.slug} sets pages in one flow, so it cannot rebuild only some pages")
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "facsimile"
    work.mkdir(exist_ok=True)
    style.install_diagrams(out_dir)
    doc = pymupdf.open(source)
    cache = source_ocr_dir(out_dir)
    ensure_source_ocr(source, cache, languages)
    scan_ink = InkCache(source, work / "ink", page_ink)
    scan_faint = InkCache(source, work / "ink", faint_ink)
    diagrams = locate_diagrams(doc, work, style)
    measure = Measure(style)
    store = TranscriptStore(book_state(out_dir) / style.transcripts) if style.transcripts else None
    texts = {p: store.text(p) for p in range(1, doc.page_count + 1)} if store else {}
    figure_boxes = style.figure_boxes() if style.figure_boxes else {}
    for p, boxes in figure_boxes.items():
        if texts.get(p):
            art = [
                ln.text
                for ln in read_source_page(cache, p).lines
                if any(l <= ln.x + ln.w / 2 <= r and t <= 1 - ln.y - ln.h / 2 <= b for l, t, r, b in boxes)
                and not (style.strict_lines and CAPTION_RE.match(ln.text))
            ]
            texts[p] = without_figure_words(texts[p], art)
    cleaned = {p: without_diagrams(COMMENT_RE.sub("", t)) for p, t in texts.items() if t}
    page_chunks = {p: chunks(table_text(t)) for p, t in cleaned.items()}
    skips = {
        p: [
            (d.left - 2, d.top - 2, d.left + d.width + 2, d.top + d.height + 2)
            for d in diagrams.get(p, [])
        ] + [
            (l * doc[p - 1].rect.width, t * doc[p - 1].rect.height, r * doc[p - 1].rect.width, b * doc[p - 1].rect.height)
            for l, t, r, b in figure_boxes.get(p, [])
        ]
        for p in range(1, doc.page_count + 1)
    }
    strict_pages = [p for p in page_chunks if p not in style.scan_pages] if style.strict_lines and not style.flow else []
    kept = work / "pages"
    kept.mkdir(exist_ok=True)
    todo = [
        p for p in strict_pages
        if pages is None or p in pages or not (kept / f"p_{p:04d}.json").exists()
    ]
    math_pages = todo if strict_pages else list(page_chunks)
    items = list(
        dict.fromkeys(i for p in math_pages for i in math_items(page_chunks[p]))
    )
    math = dict(zip(items, convert_math_batch(items), strict=True))
    family = style.font_stack.split('"')[1]
    if todo:
        jobs = [
            (p, skips[p], page_chunks[p], {i: math[i] for i in math_items(page_chunks[p])}, table_cells(cleaned[p]))
            for p in todo
        ]
        with ProcessPoolExecutor(
            min(os.cpu_count() or 1, len(todo)), initializer=_start_strict_worker,
            initargs=(scan_ink, scan_faint, cache, style.font_file, family, style.size),
        ) as pool:
            for n, (p, body, found) in enumerate(pool.map(_strict_job, jobs, chunksize=4), 1):
                (kept / f"p_{p:04d}.json").write_text(json.dumps({"body": body, "found": found}, ensure_ascii=False), encoding="utf-8")
                if n % 50 == 0:
                    print(f"set strict page {n}/{len(todo)}", flush=True)
    strict = {p: json.loads((kept / f"p_{p:04d}.json").read_text(encoding="utf-8")) for p in strict_pages}
    frames = {
        p: frame
        for p in (page_chunks if style.flow else ())
        if (frame := page_frame(without_edge_lines(scan_ink(p)))) is not None
    }
    seen_headings: set[str] = set()
    sample = sorted(frames)[::PITCH_SAMPLE_EVERY]
    size = book_pitch([(without_edge_lines(scan_ink(p)), frames[p]) for p in sample]) if frames else 0.0
    width = float(np.median([f.right - f.left for f in frames.values()])) if frames else 0.0
    pages = []
    crops = 0
    starts = page_starts({
        p: [
            folio_value(pl)
            for pl in folio_placements(without_edge_lines(scan_ink(p)), read_source_page(cache, p).lines, frame)
            if not pl.text.startswith("[")
        ]
        for p, frame in frames.items()
    })
    page_offset = 0
    mismatches: list[dict] = []
    art = style.figure_art() if style.figure_art else {}
    grays = {a.svg: gray_svg(a.svg, work / f"gray_{a.svg.name}") for arts in art.values() for a in arts}
    gray_inks = {svg: InkCache(path, work / "ink", page_ink)(1) for svg, path in grays.items()}
    drawings = {svg: svg_ink(path, gray_inks[svg]) for svg, path in grays.items()}
    art_bands = slices(
        art,
        {p: without_lines(scan_ink(p), read_source_page(cache, p).lines, CAPTION_RE) for p in art},
        {svg: drawing_gaps(path, gray_inks[svg]) for svg, path in grays.items()},
    )
    contents = contents_pages(texts)
    outline = Outline(contents_parts(texts, contents))
    for p in range(1, doc.page_count + 1):
        outline.in_contents = p in contents
        if p in starts:
            page_offset = starts[p] - p
        rect = doc[p - 1].rect
        page_diagrams = diagrams.get(p, [])
        skip = skips[p]
        ink, lines = scan_ink(p), read_source_page(cache, p).lines
        if p in style.scan_pages:
            png = work / f"scan_{p}.png"
            doc[p - 1].get_pixmap(dpi=SCAN_DPI).save(png)
            body = [f'#place(top + left, image("{png.resolve()}", width: {rect.width:.2f}pt, height: {rect.height:.2f}pt))']
        elif (frame := frames.get(p)) is not None:
            ink = without_edge_lines(ink)
            frame = with_foot_lines(ink, frame, lines)
            entries = line_entries(texts[p])
            placed = entries and (counted_lines(entries, ink, frame) or ocr_line_entries(entries, ink, frame, lines))
            if placed:
                placed = [
                    (text, bold, bands) for text, bold, bands in placed
                    if text or not any(
                        l <= bands[0][1] * PT_PER_PX and bands[0][0] * PT_PER_PX <= r
                        and t <= bands[0][3] * PT_PER_PX and bands[0][2] * PT_PER_PX <= b
                        for l, t, r, b in skip
                    )
                ]
            before = copy.deepcopy(outline)
            locked = placed_typst(ink, frame, placed, size, math, work / f"crop_{p}", outline) if placed else None
            if locked is not None:
                crops += sum(not text for text, _, _ in placed)
                locked = dropped_headings(entries, placed, frame, outline, math) + locked
            if locked is None:
                placed, outline = None, before
                frame = replace(frame, right=max(frame.right, frame.left + width))
                locked = flow_typst(frame, size, flow_markup(texts[p], math, seen_headings, out_dir, frame.right - frame.left, outline))
            body = [f"#counter(page).update({starts[p]})"] if p in starts else []
            folios = folio_placements(ink, lines, frame)
            numbers = [pl for pl in folios if not pl.text.startswith("[")]
            folio = min(numbers, key=lambda pl: abs(folio_value(pl) - p - page_offset), default=None)
            body += locked + [folio_typst(pl, size) if pl is folio else placement_typst(pl, measure) for pl in folios]
            fallback = entries[0][0] if placed and entries and entries[0][1] else ocr_head(ink, frame, lines) or ""
            if head := running_head(ink, frame):
                body.append(head_typst(head, size, fallback))
        elif p in strict:
            body = list(strict[p]["body"])
            mismatches += strict[p]["found"]
        elif p in page_chunks:
            body = transcript_typst(
                page_words(ink, lines, skip, measure),
                page_chunks[p],
                math,
                measure,
                ink,
            )
        else:
            body = [
                placement_typst(pl, measure)
                for pl in page_placements(ink, lines, skip, measure)
            ]
        body += [diagram_typst(d) for d in page_diagrams]
        if style.figure_art:
            body += [figure_typst(band, drawings[band.art.svg], grays[band.art.svg]) for band in art_bands.get(p, [])]
        elif p not in style.scan_pages:
            body += [
                figure_crop_typst(doc[p - 1], box, work / f"figure_{p}_{n}.png")
                for n, box in enumerate(figure_boxes.get(p, []))
            ]
        pages.append(
            f"#page(width: {rect.width:.2f}pt, height: {rect.height:.2f}pt, margin: 0pt)[\n"
            + "\n".join(body)
            + "\n]"
        )
        if p % 50 == 0:
            print(f"placed page {p}/{doc.page_count}", flush=True)
    print(f"{crops} scan crops for lines missing from the transcript", flush=True)
    if style.strict_lines:
        report = out_dir / "review" / "facsimile_mismatches.jsonl"
        report.parent.mkdir(exist_ok=True)
        report.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in mismatches), encoding="utf-8")
        kinds = Counter(r["kind"] for r in mismatches)
        added = kinds["row-label"] + kinds["unread-cell"] + kinds["unread-dropped"]
        print(
            f"{len(mismatches) - added} scan lines set without matching their scan line, "
            f"{kinds['row-label']} table row labels and {kinds['unread-cell']} table cell lines set from the transcript "
            f"where the OCR missed them, {kinds['unread-dropped']} unread cell texts with no ink to set them on: {report}",
            flush=True,
        )
    if outline.labels or outline.refs:
        print(
            f"{len(outline.labels)} numbered headings, {outline.resyncs} counter resyncs; "
            f"{len(outline.refs - outline.labels)} of {len(outline.refs)} contents entries name no heading; "
            f"{len(starts)} page counter starts",
            flush=True,
        )
    typ = out_dir / f"{style.slug}.typ"
    typ.write_text(preamble(style) + "\n".join(pages) + "\n", encoding="utf-8")
    pdf = out_dir / f"{style.slug}.pdf"
    compile_facsimile(typ, pdf)
    return pdf


def compile_facsimile(typ: Path, pdf: Path) -> None:
    compile_typst(typ, pdf, "--root", "/", "--no-pdf-tags")
