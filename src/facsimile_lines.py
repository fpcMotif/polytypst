"""Strict line mode: the transcript set line by line on the scan's own lines, at the size the scan's ink shows.

A line is never squeezed. When the transcript text cut for a scan line cannot reach the line's ink width with
letter spacing between -`TRACKING_LIMIT` and `SPREAD_LIMIT` em, it is set at its natural width and reported as a mismatch.
"""

import itertools
import re
import statistics
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, replace
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pymupdf
from fontTools.ttLib import TTCollection
from PIL import ImageFont

from .facsimile_text import Chunk, Piece
from .ocr.pages import OcrLine
from .parity.words import PT_PER_PX, uncolored_ink

FIT_TOLERANCE = 0.06
TRACKING_LIMIT = 0.15
SPREAD_LIMIT = 0.4
SIZE_SNAP = 0.10
WIDE_SHARE = 0.3
WORD_SPREAD_LIMIT = 1.0
WORD_SHRINK = 0.08
LATIN_SHRINK = 0.12
MEASURED_INK = 50
BAND_GAP_PX = 3
SIZE_RANGE = (5.0, 40.0)
LINE_PAD_PX = 2
RULE_SHARE = 0.9
REFERENCE_GLYPH = "国"
TURNED_SHAPE = 1.4
MIXED_SHARE = 0.8
WIDTH_AGREES = 0.2
RULE_MIN_PT = 30.0
RULE_PIECE_PT = 15.0
TABLE_CELLS = 3
COLUMN_SHARE = 0.25
UNREAD_MIN_SHARE = 0.4
SPANNED_RATIO = 0.6
RESCUE_RATIO = 0.75
ROW_SPREAD = 1.5
ROW_PAD = 0.3
VALUE_RE = re.compile(r"[\s\d.,+\-−–()（）%％*]+$")
RULE_THICK_PX = 8
RULE_LEVEL = 200
CAPTION_RE =re.compile(r"\s*[（(]?\s*(图|表|注|资料来源|数据来源|出处|http)")


@dataclass(frozen=True)
class Atom:
    """One transcript character, or one whole math piece holding its LaTeX."""

    text: str
    kind: str = "text"
    style: str = ""


@dataclass(frozen=True)
class ScanLine:
    """One OCR line of the scan and its ink box in pt from the page's top-left corner."""

    text: str
    left: float
    right: float
    top: float
    bottom: float


@dataclass(frozen=True)
class TableCell:
    """One cell of a transcript table: its grid row and first column, the columns it spans, its plain text,
    and the rows it spans."""

    row: int
    col: int
    span: int
    text: str
    down: int = 1


@dataclass(frozen=True)
class SetLine:
    typst: str
    size: float
    tracking: float
    mismatch: str | None
    ratio: float


def face_index(font_file: Path, family: str) -> int:
    """The index of `family`'s regular face in a font collection; 0 for a single-face file."""
    if font_file.suffix.lower() != ".ttc":
        return 0
    names = [f["name"].getDebugName(4) for f in TTCollection(str(font_file)).fonts]
    return next((i for i, n in enumerate(names) if n == f"{family} Regular"), next((i for i, n in enumerate(names) if n.startswith(family)), 0))


def transcript_atoms(cs: Sequence[Chunk]) -> list[Atom]:
    out: list[Atom] = []
    for k, chunk in enumerate(cs):
        if k:
            out.append(Atom(" "))
        for p in chunk:
            out += [Atom(c, "text", p.style) for c in p.text] if p.kind == "text" else [Atom(p.text, p.kind)]
    return out


def _key(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).lower() if not c.isspace())


def main_band(profile: np.ndarray) -> tuple[int, int]:
    """The run of inked rows holding the most ink, runs closer than `BAND_GAP_PX` joined: the line itself,
    without the edges of the lines above and below that its OCR box overlaps."""
    inked = np.flatnonzero(profile)
    if not inked.size:
        return 0, len(profile)
    runs, start = [], inked[0]
    for a, b in itertools.pairwise(inked):
        if b - a > BAND_GAP_PX:
            runs.append((start, a + 1))
            start = b
    runs.append((start, inked[-1] + 1))
    return max(runs, key=lambda r: profile[r[0] : r[1]].sum())


def scan_lines(ink: np.ndarray, lines: Sequence[OcrLine], skip: Sequence[tuple[float, float, float, float]]) -> list[ScanLine]:
    """The OCR lines outside the `skip` boxes (pt) with their ink boxes, less any table rule crossing the line."""
    h, w = ink.shape
    out = []
    for line in lines:
        x0, x1 = max(0, int(line.x * w) - LINE_PAD_PX), min(w, int((line.x + line.w) * w) + LINE_PAD_PX)
        y0, y1 = max(0, int((1 - line.y - line.h) * h) - LINE_PAD_PX), min(h, int((1 - line.y) * h) + LINE_PAD_PX)
        cx, cy = (x0 + x1) / 2 * PT_PER_PX, (y0 + y1) / 2 * PT_PER_PX
        inside = any(l <= cx <= r and t <= cy <= b for l, t, r, b in skip)
        if not line.text.strip() or (inside and not CAPTION_RE.match(line.text)):
            continue
        box = ink[y0:y1, x0:x1].copy()
        across = 0 if y1 - y0 > TURNED_SHAPE * (x1 - x0) else 1
        if across:
            box[box.mean(axis=1) > RULE_SHARE] = False
        else:
            box[:, box.mean(axis=0) > RULE_SHARE] = False
        band = main_band(box.sum(axis=across))
        if across:
            box[: band[0]] = box[band[1] :] = False
        else:
            box[:, : band[0]] = box[:, band[1] :] = False
        rows, cols = np.flatnonzero(box.any(axis=1)), np.flatnonzero(box.any(axis=0))
        if rows.size and cols.size:
            out.append(ScanLine(line.text, (x0 + cols[0]) * PT_PER_PX, (x0 + cols[-1] + 1) * PT_PER_PX, (y0 + rows[0]) * PT_PER_PX, (y0 + rows[-1] + 1) * PT_PER_PX))
    return out


def turned(line: ScanLine) -> bool:
    return line.bottom - line.top > TURNED_SHAPE * (line.right - line.left)


def _runs(ink: np.ndarray, min_px: int) -> list[tuple[int, int, int]]:
    """Each row's runs of ink at least `min_px` long, as (row, start, end)."""
    out = []
    for y in np.flatnonzero(ink.sum(axis=1) >= min_px):
        edges = np.flatnonzero(np.diff(np.concatenate(([0], ink[y].astype(np.int8), [0]))))
        out += [(int(y), int(a), int(b)) for a, b in zip(edges[::2], edges[1::2]) if b - a >= min_px]
    return out


def _merged(runs: list[tuple[int, int, int]]) -> list[tuple[float, float, int, int]]:
    """Runs on neighbouring rows that overlap joined into one rule, a slightly skewed rule included:
    (middle row, thickness in px as ink per unit of length, start, end)."""
    rules: list[list[int]] = []
    for y, a, b in sorted(runs):
        for rule in rules:
            if y - rule[1] <= 1 and a <= rule[3] + 1 and rule[2] <= b + 1:
                rule[1], rule[2], rule[3], rule[4] = y, min(rule[2], a), max(rule[3], b), rule[4] + b - a
                break
        else:
            rules.append([y, y, a, b, b - a])
    return [
        ((r[0] + r[1] + 1) / 2, r[4] / (r[3] - r[2]), r[2], r[3])
        for r in rules
        if r[4] / (r[3] - r[2]) <= RULE_THICK_PX
    ]


def faint_ink(page: pymupdf.Page) -> np.ndarray:
    """Pixels darker than `RULE_LEVEL`, less strongly coloured ones: the scan's ink with its light gray rules."""
    return uncolored_ink(page, RULE_LEVEL)


def rules_typst(ink: np.ndarray, skip: Sequence[tuple[float, float, float, float]]) -> list[str]:
    """Vector lines for the scan's rules, such as table rules and the footnote rule: ink runs at least `RULE_MIN_PT`
    long and at most `RULE_THICK_PX` thick, outside the `skip` boxes (pt). A skewed rule is joined from its steps on
    neighbouring rows, each at least `RULE_PIECE_PT` long, which is longer than any glyph stroke."""
    min_px, piece_px = round(RULE_MIN_PT / PT_PER_PX), round(RULE_PIECE_PT / PT_PER_PX)
    out = []

    def outside(x: float, y: float) -> bool:
        return not any(l <= x <= r and t <= y <= b for l, t, r, b in skip)

    for mid, thick_px, a, b in _merged(_runs(ink, piece_px)):
        y, thick = mid * PT_PER_PX, thick_px * PT_PER_PX
        if b - a >= min_px and outside((a + b) / 2 * PT_PER_PX, y):
            out.append(f"#place(top + left, dx: {a * PT_PER_PX:.2f}pt, dy: {y:.2f}pt, line(length: {(b - a) * PT_PER_PX:.2f}pt, stroke: {thick:.2f}pt))")
    for mid, thick_px, a, b in _merged(_runs(ink.T, piece_px)):
        x, thick = mid * PT_PER_PX, thick_px * PT_PER_PX
        if b - a >= min_px and outside(x, (a + b) / 2 * PT_PER_PX):
            out.append(
                f"#place(top + left, dx: {x:.2f}pt, dy: {a * PT_PER_PX:.2f}pt, "
                f"line(angle: 90deg, length: {(b - a) * PT_PER_PX:.2f}pt, stroke: {thick:.2f}pt))"
            )
    return out


def order_lines(lines: Sequence[ScanLine]) -> list[ScanLine]:
    """Reading order: rows top to bottom, a row being lines whose middles sit inside each other's height; left to right in a row.
    On a sideways page, where most lines run down the page and read bottom to top, rows are columns from the left."""
    if sum(turned(ln) for ln in lines) * 2 > len(lines):
        upright = {ScanLine(str(n), -ln.bottom, -ln.top, ln.left, ln.right): ln for n, ln in enumerate(lines)}
        return [upright[u] for u in order_lines(list(upright))]
    return [ln for row in _rows(lines) for ln in row]


def _rows(lines: Sequence[ScanLine]) -> list[list[ScanLine]]:
    """Upright lines grouped into rows top to bottom, each row left to right."""
    rows: list[list[ScanLine]] = []
    for ln in sorted(lines, key=lambda ln: ln.top):
        mid = (ln.top + ln.bottom) / 2
        row = rows[-1] if rows else None
        if row and any(o.top <= mid <= o.bottom or ln.top <= (o.top + o.bottom) / 2 <= ln.bottom for o in row):
            row.append(ln)
        else:
            rows.append([ln])
    return [sorted(row, key=lambda ln: ln.left) for row in rows]


def _matched_end(seg: Sequence[Atom], text: str) -> int:
    """The index in `seg` just after its last atom that matches the scan line's OCR `text`."""
    keyed = [i for i, a in enumerate(seg) if a.kind != "text" or _key(a.text)]
    keys = ["§" if seg[i].kind != "text" else _key(seg[i].text) for i in keyed]
    blocks = [b for b in SequenceMatcher(None, keys, list(_key(text)), autojunk=False).get_matching_blocks() if b.size]
    return keyed[blocks[-1].a + blocks[-1].size - 1] + 1 if blocks else 0


def row_labels(lines: Sequence[ScanLine], segments: Sequence[Sequence[Atom]], gap: float) -> list[tuple[int, int, int, float]]:
    """The table row labels the OCR missed, which the transcript cut leaves at the end of the row above:
    (that row's last line, where its unmatched label starts, the labelled row's first line, the label column's left).
    A table row holds at least `TABLE_CELLS` lines. The label column is the median left of the table rows' first cells
    that sit at least `gap` left of the labelled row's first cell, and the label is one word. The labelled row starts
    with a value, as a row whose label the OCR missed does; a row that starts with text has its label already."""
    if sum(turned(ln) for ln in lines) * 2 > len(lines):
        return []
    index = {id(ln): n for n, ln in enumerate(lines)}
    rows = [[index[id(ln)] for ln in row] for row in _rows(lines)]
    firsts = [lines[row[0]].left for row in rows if len(row) >= TABLE_CELLS]
    out = []
    for above, row in itertools.pairwise(rows):
        if len(above) + 1 < TABLE_CELLS or len(row) + 1 < TABLE_CELLS:
            continue
        last, first = above[-1], row[0]
        cut = _matched_end(segments[last], lines[last].text)
        label = "".join(a.text for a in segments[last][cut:]).strip()
        lefts = [x for x in firsts if x <= lines[first].left - gap]
        if label and len(label.split()) == 1 and lefts and VALUE_RE.match(lines[first].text):
            out.append((last, cut, first, statistics.median(lefts)))
    return out


def _keys(atoms: Sequence[Atom]) -> tuple[list[int], list[str]]:
    """The atoms that a line reader sees, by index, and their match keys, a math piece keyed `§`."""
    keyed = [i for i, a in enumerate(atoms) if a.kind != "text" or _key(a.text)]
    return keyed, ["§" if atoms[i].kind != "text" else _key(atoms[i].text) for i in keyed]


def _starts(atoms: Sequence[Atom], lines: Sequence[ScanLine]) -> list[int | None]:
    """Each line's first atom matching its OCR text, None for a line that nothing matches."""
    keyed, a_keys = _keys(atoms)
    b_keys, b_line = [], []
    for n, ln in enumerate(lines):
        for c in _key(ln.text):
            b_keys.append(c)
            b_line.append(n)
    starts: list[int | None] = [None] * len(lines)
    for block in SequenceMatcher(None, a_keys, b_keys, autojunk=False).get_matching_blocks():
        for k in range(block.size):
            n = b_line[block.b + k]
            if starts[n] is None:
                starts[n] = keyed[block.a + k]
    return starts


def _trimmed(seg: Sequence[Atom]) -> list[Atom]:
    seg = list(seg)
    while seg and seg[0].kind == "text" and seg[0].text.isspace():
        seg.pop(0)
    while seg and seg[-1].kind == "text" and seg[-1].text.isspace():
        seg.pop()
    return seg


def _spans(starts: Sequence[int | None], size: int) -> list[tuple[int, int] | None]:
    """Each line's atoms as (first, end): from its first matching atom to the next matched line's, None for a line that
    nothing matches. The first line also takes the atoms before its match."""
    spans: list[tuple[int, int] | None] = []
    last = 0
    for n, s in enumerate(starts):
        last = 0 if n == 0 else max(last, s) if s is not None else last
        spans.append((last, size) if s is not None or n == 0 else None)
    end = size
    for n in reversed(range(len(spans))):
        if (span := spans[n]) is not None:
            spans[n], end = (span[0], max(span[0], end)), span[0]
    return spans


def line_segments(atoms: Sequence[Atom], lines: Sequence[ScanLine]) -> list[list[Atom]]:
    """The transcript cut at the scan's line breaks: each line gets the atoms from the first one matching its OCR text."""
    starts = _starts(atoms, lines)
    cuts = _cuts(starts, len(atoms))
    return [_trimmed(atoms[cuts[n] : cuts[n + 1]]) if starts[n] is not None or n == 0 else [] for n in range(len(lines))]


def _cuts(starts: Sequence[int | None], size: int) -> list[int]:
    cuts, last = [], 0
    for s in starts:
        last = max(last, s) if s is not None else last
        cuts.append(last)
    if cuts:
        cuts[0] = 0
    return [*cuts, size]


def table_columns(lines: Sequence[ScanLine]) -> tuple[list[int | None], list[tuple[float, float]]]:
    """Each table line's column, counted from the left, or None for a line spanning columns, and each column's x
    extent (pt), reaching halfway across the gutters to its neighbours and as far again past the outer columns.
    A column is a run of x that at least `COLUMN_SHARE` of the busiest x's lines cover, and two or more; a spanning
    header covers the gutters between columns alone. A line reaching into two runs spans them. A line in no run, such as
    a lone label down the left, is a column of its own."""
    lo = int(min(ln.left for ln in lines))
    cover = np.zeros(int(max(ln.right for ln in lines)) + 2 - lo)
    for ln in lines:
        cover[int(ln.left) - lo : int(np.ceil(ln.right)) - lo] += 1
    busy = np.flatnonzero(cover >= max(2, COLUMN_SHARE * cover.max()))
    runs = [(lo + r[0], lo + r[-1] + 1.0) for r in np.split(busy, np.flatnonzero(np.diff(busy) > 1) + 1) if r.size]
    lone: list[list[float]] = []
    picks: list[tuple[str, int] | None] = []
    for ln in lines:
        over = [min(b, ln.right) - max(a, ln.left) for a, b in runs]
        held = [k for k, o in enumerate(over) if o > 0]
        if len(held) >= 2:
            picks.append(None)
        elif held:
            picks.append(("run", held[0]))
        else:
            k = next((k for k, (a, b) in enumerate(lone) if a < ln.right and ln.left < b), None)
            if k is None:
                lone.append([ln.left, ln.right])
                k = len(lone) - 1
            lone[k] = [min(lone[k][0], ln.left), max(lone[k][1], ln.right)]
            picks.append(("lone", k))
    found = sorted({(*(runs[k] if kind == "run" else lone[k]), kind, k) for kind, k in filter(None, picks)})
    rank = {(kind, k): n for n, (_, _, kind, k) in enumerate(found)}
    edges = [(a, b) for a, b, _, _ in found]
    gaps = [max(0.0, b[0] - a[1]) / 2 for a, b in itertools.pairwise(edges)]
    pads = [gaps[0] if gaps else 0.0, *gaps, gaps[-1] if gaps else 0.0]
    extents = [(a - pads[n], b + pads[n + 1]) for n, (a, b) in enumerate(edges)]
    return [None if p is None else rank[p] for p in picks], extents


@dataclass(frozen=True)
class Unread:
    """Transcript text of a table cell that no OCR line read, the box (pt) between the read lines around it, across
    its column, where the scan prints it, and the read line it `follows`, or else precedes."""

    atoms: tuple[Atom, ...]
    box: tuple[float, float, float, float]
    line: int
    follows: bool


def _spanned(text: str, cells: Sequence[TableCell], cell_atoms: dict[TableCell, list[Atom]], ratio: float = 0.0) -> list[TableCell]:
    """The cells side by side in one row that a scan line reads best: a header spanning them, headers the OCR read
    as one line, or a cell the OCR misread. The run reading at least `ratio`, `SPANNED_RATIO` by default, alike, or none."""
    key, best, out = _key(text), ratio or SPANNED_RATIO, []
    for _, group in itertools.groupby(sorted(cells, key=lambda c: (c.row, c.col)), key=lambda c: c.row):
        row = list(group)
        for i, j in itertools.combinations(range(len(row) + 1), 2):
            ratio = SequenceMatcher(None, key, "".join(k for c in row[i:j] for k in _keys(cell_atoms[c])[1]), autojunk=False).ratio()
            if ratio > best:
                best, out = ratio, row[i:j]
    return out


def _row_box(
    row: Sequence[ScanLine], columns: Sequence[int | None], rank: int | None, extents: Sequence[tuple[float, float]]
) -> tuple[float, float, float, float] | None:
    """The box (pt) on the scan row that reads a table row, in column `rank` between the row's read cells either side;
    None when the row's read lines spread over more than `ROW_SPREAD` line heights, as a wrapped row does."""
    if not row or rank is None:
        return None
    height = statistics.median(ln.bottom - ln.top for ln in row)
    top, bottom = min(ln.top for ln in row), max(ln.bottom for ln in row)
    if bottom - top > ROW_SPREAD * height:
        return None
    left = max((ln.right for ln, c in zip(row, columns) if c is not None and c < rank), default=extents[rank][0])
    right = min((ln.left for ln, c in zip(row, columns) if c is not None and c > rank), default=extents[rank][1])
    return left, top - ROW_PAD * height, right, bottom + ROW_PAD * height


def page_segments(
    atoms: Sequence[Atom], lines: Sequence[ScanLine], tables: Sequence[Sequence[TableCell]]
) -> tuple[list[list[Atom]], list[Unread]]:
    """`line_segments`, with each table's lines cut again column by column, and the table text no OCR line read.
    A cell can wrap over several scan lines, which the scan reads row by row across the cells and the transcript reads
    cell by cell. A table's scan lines are the ones between the first and last whose page-wide cut starts in its text.
    A line spanning columns takes the cells `_spanned` finds; the others are cut column by column on both sides, less
    the cells spanning columns. A line takes its matched text, and the rest of its cell when no other line reads that
    cell; a line matching nothing takes the cells it reads at least `RESCUE_RATIO` alike, as a misread line out of its
    column does. Text between two read lines that neither takes is `Unread`, in the column of the line it follows or
    else of the line it precedes: a whole cell on the scan row reading its table row, the rest between those two lines.
    Text of a column with no read line around it is dropped."""
    from .facsimile_text import chunks

    out = line_segments(atoms, lines)
    unread: list[Unread] = []
    if not lines or sum(turned(ln) for ln in lines) * 2 > len(lines):
        return out, unread
    keyed, a_keys = _keys(atoms)
    page_key = "".join(a_keys)
    starts = _starts(atoms, lines)
    for cells in tables:
        cell_atoms = {c: transcript_atoms(chunks(c.text)) for c in cells}
        table_key = "".join(k for c in sorted(cells, key=lambda c: (c.row, c.col)) for k in _keys(cell_atoms[c])[1])
        at = page_key.find(table_key) if table_key else -1
        if at < 0:
            continue
        ta, tb = keyed[at], keyed[at + len(table_key) - 1] + 1
        inside = [n for n, s in enumerate(starts) if s is not None and ta <= s < tb]
        if len(inside) < 2:
            continue
        n0, n1 = inside[0], inside[-1]
        body = range(n0, n1 + 1)
        ranks, extents = table_columns([lines[n] for n in body])
        column = dict(zip(body, ranks))
        held: set[TableCell] = set()
        for n in body:
            out[n] = []
            if column[n] is None:
                run = _spanned(lines[n].text, [c for c in cells if c not in held], cell_atoms)
                held |= set(run)
                out[n] = _trimmed([a for k, c in enumerate(run) for a in [Atom(" ")] * bool(k) + cell_atoms[c]])
        order = sorted((n for n in body if column[n] is not None), key=lambda n: (column[n], n))
        flat: list[Atom] = []
        owner: list[TableCell | None] = []
        first, last = {}, {}
        for c in sorted((c for c in cells if c not in held and c.span == 1), key=lambda c: (c.col, c.row)):
            if flat:
                flat.append(Atom(" "))
                owner.append(None)
            first[c] = len(flat)
            flat += cell_atoms[c]
            owner += [c] * len(cell_atoms[c])
            last[c] = len(flat)
        own = _starts(flat, [lines[n] for n in order])
        spans = _spans(own, len(flat))
        chain = [(n, s, s + max(1, _matched_end(flat[s : span[1]], lines[n].text))) for n, s, span in zip(order, own, spans) if s is not None and span]
        heads = [
            s if k and owner[s] is owner[chain[k - 1][2] - 1] else max(chain[k - 1][2] if k else 0, first[owner[s]])
            for k, (_, s, _) in enumerate(chain)
        ]
        tails = [
            m if k + 1 < len(chain) and owner[m - 1] is owner[chain[k + 1][1]]
            else max(m, min(heads[k + 1] if k + 1 < len(chain) else len(flat), last[owner[m - 1]]))
            for k, (_, _, m) in enumerate(chain)
        ]
        for (n, _, _), a, b in zip(chain, heads, tails):
            out[n] = _trimmed(flat[a:b])
        touched = {owner[i] for a, b in zip(heads, tails) for i in range(a, b)}
        pool = [c for c in cells if c not in held and c not in touched]
        cut = {n for n, _, _ in chain}
        for n in order:
            if n not in cut and (run := _spanned(lines[n].text, pool, cell_atoms, RESCUE_RATIO)):
                held |= set(run)
                pool = [c for c in pool if c not in run]
                out[n] = _trimmed([a for k, c in enumerate(run) for a in [Atom(" ")] * bool(k) + cell_atoms[c]])
        rows: dict[int, list[int]] = {}
        for n, s, m in chain:
            if owner[s].row == owner[m - 1].row and owner[s].down == 1:
                rows.setdefault(owner[s].row, []).append(n)
        top, bottom = min(lines[n].top for n in body), max(lines[n].bottom for n in body)
        for k in range(len(chain) + 1):
            gap = range(tails[k - 1] if k else 0, heads[k] if k < len(chain) else len(flat))
            sides = []
            if k:
                p = chain[k - 1][0]
                below = next((lines[q].bottom for q, _, _ in chain[k:] if column[q] == column[p]), bottom)
                sides.append((p, True, owner[chain[k - 1][2] - 1].col, (lines[p].top, below)))
            if k < len(chain):
                q = chain[k][0]
                above = next((lines[p].top for p, _, _ in reversed(chain[:k]) if column[p] == column[q]), top)
                sides.append((q, False, owner[chain[k][1]].col, (above, lines[q].bottom)))
            taken: set[int] = set()
            for n, follows, col, (y0, y1) in sides:
                picked = [i for i in gap if i not in taken and (owner[i] is None or owner[i].col == col and owner[i] not in held)]
                taken |= {i for i in picked if owner[i] is not None}
                loose: list[Atom] = []
                for cell, group in itertools.groupby(picked, key=lambda i: owner[i]):
                    held_atoms = [flat[i] for i in group]
                    box = _row_box([lines[r] for r in rows.get(cell.row, [])], [column[r] for r in rows.get(cell.row, [])], column[n], extents) if cell else None
                    if box and len(held_atoms) == last[cell] - first[cell]:
                        unread.append(Unread(tuple(held_atoms), box, n, follows))
                    else:
                        loose += held_atoms if cell else [Atom(" ")]
                if text := _trimmed(loose):
                    left, right = extents[column[n]]
                    unread.append(Unread(tuple(text), (left, y0, right, y1), n, follows))
        cuts = _cuts(starts, len(atoms))
        for n in range(n0):
            if out[n] and cuts[n + 1] > ta:
                out[n] = _trimmed(atoms[cuts[n] : max(cuts[n], ta)])
    return out, unread


def unread_bands(ink: np.ndarray, box: tuple[float, float, float, float], lines: Sequence[ScanLine], min_pt: float) -> list[ScanLine]:
    """The ink lines in `box` (pt) that no OCR line covers, top to bottom, less rules: runs longer than `RULE_PIECE_PT`,
    found in a window that far around the box, as a rule can cross a box shorter than that.
    A band at least `min_pt` tall is a line; a lower one is a speck."""
    h, w = ink.shape
    long = round(RULE_PIECE_PT / PT_PER_PX)
    x0, y0 = max(0, int(box[0] / PT_PER_PX)), max(0, int(box[1] / PT_PER_PX))
    x1, y1 = min(w, int(box[2] / PT_PER_PX) + 1), min(h, int(box[3] / PT_PER_PX) + 1)
    if x1 <= x0 or y1 <= y0:
        return []
    wx, wy = max(0, x0 - long), max(0, y0 - long)
    window = ink[wy : min(h, y1 + long), wx : min(w, x1 + long)].copy()
    for ln in lines:
        l, t = int(ln.left / PT_PER_PX) - LINE_PAD_PX - wx, int(ln.top / PT_PER_PX) - LINE_PAD_PX - wy
        r, b = int(ln.right / PT_PER_PX) + LINE_PAD_PX + 1 - wx, int(ln.bottom / PT_PER_PX) + LINE_PAD_PX + 1 - wy
        window[max(0, t) : max(0, b), max(0, l) : max(0, r)] = False
    rules = np.zeros_like(window)
    for y, a, b in _runs(window, long):
        rules[max(0, y - 1) : y + 2, a:b] = True
    for x, a, b in _runs(window.T, long):
        rules[a:b, max(0, x - 1) : x + 2] = True
    sub = (window & ~rules)[y0 - wy : y1 - wy, x0 - wx : x1 - wx]
    rows = np.flatnonzero(sub.any(axis=1))
    out = []
    for band in np.split(rows, np.flatnonzero(np.diff(rows) > BAND_GAP_PX) + 1) if rows.size else []:
        cols = np.flatnonzero(sub[band[0] : band[-1] + 1].any(axis=0))
        if (band[-1] + 1 - band[0]) * PT_PER_PX >= min_pt:
            out.append(ScanLine("", (x0 + cols[0]) * PT_PER_PX, (x0 + cols[-1] + 1) * PT_PER_PX, (y0 + band[0]) * PT_PER_PX, (y0 + band[-1] + 1) * PT_PER_PX))
    return out


def place_unread(
    ink: np.ndarray, unread: Sequence[Unread], lines: Sequence[ScanLine], segments: list[list[Atom]], min_pt: float
) -> tuple[list[tuple[list[Atom], ScanLine]], list[Unread]]:
    """The unread table text split over the ink bands that print it, and the pieces set nowhere. A piece with no ink
    of its own is in a read line's box, misread: it joins the cut of the line it follows or precedes, unless that line
    has none."""
    placed, dropped = [], []
    for piece in unread:
        if split := split_unread(piece.atoms, unread_bands(ink, piece.box, lines, min_pt)):
            placed += split
        elif seg := segments[piece.line]:
            segments[piece.line] = seg + list(piece.atoms) if piece.follows else list(piece.atoms) + seg
        else:
            dropped.append(piece)
    return placed, dropped


def split_unread(atoms: Sequence[Atom], bands: Sequence[ScanLine]) -> list[tuple[list[Atom], ScanLine]]:
    """The unread text over the ink bands that print it, in reading order, each band taking a share of the characters
    as wide as its share of the bands' ink width; with more bands than characters, the widest bands."""
    marks = [a for a in atoms if a.kind != "text" or not a.text.isspace()]
    if not marks or not bands:
        return []
    bands = sorted(sorted(bands, key=lambda b: b.left - b.right)[: len(marks)], key=lambda b: (b.top, b.left))
    widths = list(itertools.accumulate(b.right - b.left for b in bands))
    cuts = [0]
    for k, w in enumerate(widths[:-1]):
        cuts.append(min(len(marks) - (len(bands) - k - 1), max(cuts[-1] + 1, round(len(marks) * w / widths[-1]))))
    cuts.append(len(marks))
    return [(marks[a:b], band) for a, b, band in zip(cuts, cuts[1:], bands)]


def _markup(seg: Sequence[Atom], math: dict[tuple[str, bool], str]) -> str:
    from .facsimile import chunk_markup

    pieces: list[Piece] = []
    for a in seg:
        if a.kind == "text" and pieces and pieces[-1].kind == "text" and pieces[-1].style == a.style:
            pieces[-1] = Piece("text", pieces[-1].text + a.text, a.style)
        else:
            pieces.append(Piece(a.kind, a.text, a.style))
    return chunk_markup(tuple(pieces), math)


def set_line(
    seg: Sequence[Atom],
    line: ScanLine,
    font: ImageFont.FreeTypeFont,
    size_hint: float,
    math: dict[tuple[str, bool], str],
    height_scale: float = 1.0,
) -> SetLine:
    """Typst for one scan line: its text at the size its ink height shows times `height_scale`, letter-spaced to its
    ink width. The size and spacing come from the page's `size_hint` when the line holds math, which the font cannot measure.
    A line of several characters in a box much taller than wide runs down a sideways page: it is set upright and turned."""
    if len(seg) > 1 and turned(line):
        upright = ScanLine(line.text, 0.0, line.bottom - line.top, 0.0, line.right - line.left)
        out = set_line(seg, upright, font, size_hint, math, height_scale)
        typst = (
            f"#place(top + left, dx: {line.left:.2f}pt, dy: {line.bottom:.2f}pt, rotate(-90deg, origin: top + left)"
            f"[#box(width: {upright.right * 3:.2f}pt, height: {upright.bottom:.2f}pt)[{out.typst}]])"
        )
        return replace(out, typst=typst)
    width = line.right - line.left
    markup = _markup(seg, math)
    text = "".join(a.text for a in seg)
    if any(a.kind != "text" for a in seg) or not text.strip():
        top = font.getbbox(REFERENCE_GLYPH, anchor="ls")[1]
        base = line.top - top * size_hint / 100
        return SetLine(_place(line.left, base, size_hint, 0.0, markup), size_hint, 0.0, "math" if text.strip() or seg else "empty", 0.0)
    l, t, r, b = font.getbbox(text, anchor="ls")
    wide = sum(unicodedata.east_asian_width(c) in ("W", "F") for c in text)
    scale = 1 + (height_scale - 1) * wide / len(text)
    from_height = (line.bottom - line.top) / (b - t) * 100 * scale if b > t else size_hint
    from_width = width / (r - l) * 100 if r > l else 0.0
    if wide < MIXED_SHARE * len(text) and abs(from_width / from_height - 1) <= WIDTH_AGREES:
        from_height = from_width
    measured = b - t >= MEASURED_INK and SIZE_RANGE[0] <= from_height <= SIZE_RANGE[1]
    size = from_height if measured and abs(from_height / size_hint - 1) > SIZE_SNAP else size_hint
    spaces = text.count(" ")
    words = spaces >= 2 and wide < WIDE_SHARE * len(text)
    if words and r > l and width < (r - l) * size / 100:
        size = max(width / (r - l) * 100, size * (1 - LATIN_SHRINK))
    gaps = len(text) - 1
    ratio = width / ((r - l) * size / 100) if r > l else 0.0
    spare = width - (r - l) * size / 100
    spacing = min(max(spare / spaces, -WORD_SHRINK * size), WORD_SPREAD_LIMIT * size) if words else 0.0
    tracking = (spare - spacing * spaces) / gaps if gaps else 0.0
    fits = -TRACKING_LIMIT * size <= tracking <= SPREAD_LIMIT * size if gaps else abs(ratio - 1) <= FIT_TOLERANCE
    tracking, spacing = (tracking, spacing) if fits else (0.0, 0.0)
    dx, base = line.left - l * size / 100, line.top - t * size / 100
    return SetLine(_place(dx, base, size, tracking, markup, spacing), size, tracking, None if fits else "width", ratio)


def _place(dx: float, base: float, size: float, tracking: float, markup: str, spacing: float = 0.0) -> str:
    return (
        f"#place(top + left, dx: {dx:.2f}pt, dy: {base:.2f}pt, "
        f"text(size: {size:.2f}pt, tracking: {tracking:.3f}pt, spacing: 100% + {spacing:.3f}pt)[{markup}])"
    )


def page_size(
    segments: Sequence[Sequence[Atom]], lines: Sequence[ScanLine], font: ImageFont.FreeTypeFont, fallback: float
) -> tuple[float, float]:
    """The body size of a page, the median size at which its long text lines fill their ink width, and the factor
    from a size read off ink height to that size: the scan's face is taller for its width than the set face."""
    sizes, scales = [], []
    for seg, line in zip(segments, lines):
        text = "".join(a.text for a in seg)
        if len(text) >= 12 and all(a.kind == "text" for a in seg):
            l, t, r, b = font.getbbox(text, anchor="ls")
            along, across = (line.bottom - line.top, line.right - line.left) if turned(line) else (line.right - line.left, line.bottom - line.top)
            if b > t and r > l and SIZE_RANGE[0] <= (size := along / (r - l) * 100) <= SIZE_RANGE[1]:
                sizes.append(size)
                scales.append(size / (across / (b - t) * 100))
    return (statistics.median(sizes), statistics.median(scales)) if sizes else (fallback, 1.0)


def strict_page(
    page: int,
    ink: np.ndarray,
    ocr_lines: Sequence[OcrLine],
    skip: Sequence[tuple[float, float, float, float]],
    page_chunks: Sequence[Chunk],
    math: dict[tuple[str, bool], str],
    font: ImageFont.FreeTypeFont,
    fallback: float,
    rule_ink: np.ndarray | None = None,
    tables: Sequence[Sequence[TableCell]] = (),
) -> tuple[list[str], list[dict]]:
    """Typst for a page set line by line on its scan lines, and one record per line that could not match its scan line.
    Its rules are found in `rule_ink` when given, which can hold rules printed lighter than the text's ink.
    A scan line that no transcript text matches is set from its OCR text and recorded as `ocr-only`. So is a line whose
    transcript cut misses its ink width while its OCR text fits, recorded as `ocr-for-width` with the cut it replaced."""
    lines = order_lines(scan_lines(ink, ocr_lines, skip))
    segments, unread = page_segments(transcript_atoms(page_chunks), lines, tables)
    hint, height_scale = page_size(segments, lines, font, fallback)
    placed, dropped = place_unread(ink, unread, lines, segments, UNREAD_MIN_SHARE * hint)
    labels = {}
    for above, cut, row, left in row_labels(lines, segments, 2 * hint):
        labels[row] = ([a for a in segments[above][cut:] if a.kind != "text" or not a.text.isspace()], left)
        segments[above] = segments[above][:cut]
    sizes = []
    body, records = rules_typst(ink if rule_ink is None else rule_ink, skip), []
    for line, seg in zip(lines, segments):
        kind, cut = None, "".join(a.text for a in seg)
        ocr = [Atom(c) for c in line.text.strip()]
        if not seg:
            seg, kind = ocr, "ocr-only"
        out = set_line(seg, line, font, hint, math, height_scale)
        if out.mismatch == "width" and not kind and (alt := set_line(ocr, line, font, hint, math, height_scale)).mismatch is None:
            out, kind = alt, "ocr-for-width"
        body.append(out.typst)
        sizes.append(out.size)
        if kind or out.mismatch:
            records.append({
                "page": page,
                "kind": kind or out.mismatch,
                "scan": line.text,
                "transcript": cut,
                "ratio": round(out.ratio, 3),
                "box": [round(v, 1) for v in (line.left, line.top, line.right, line.bottom)],
            })
    for row, (label, left) in labels.items():
        cell, size, text = lines[row], sizes[row], "".join(a.text for a in label)
        cell_text = "".join(a.text for a in segments[row] if a.kind == "text") or cell.text
        base = cell.top - font.getbbox(cell_text, anchor="ls")[1] * size / 100
        body.append(_place(left - font.getbbox(text, anchor="ls")[0] * size / 100, base, size, 0.0, _markup(label, math)))
        records.append({"page": page, "kind": "row-label", "scan": "", "transcript": text, "ratio": 1.0,
                        "box": [round(left, 1), round(cell.top, 1), round(left, 1), round(cell.bottom, 1)]})
    for seg, band in placed:
        out = set_line(seg, band, font, hint, math, height_scale)
        body.append(out.typst)
        records.append({"page": page, "kind": "unread-cell", "scan": "", "transcript": "".join(a.text for a in seg),
                        "ratio": round(out.ratio, 3), "box": [round(v, 1) for v in (band.left, band.top, band.right, band.bottom)]})
    for piece in dropped:
        records.append({"page": page, "kind": "unread-dropped", "scan": "", "transcript": "".join(a.text for a in piece.atoms),
                        "ratio": 0.0, "box": [round(v, 1) for v in piece.box]})
    return body, records
