"""Scan parity: how far a rebuilt PDF's words, lines and diagrams sit from the same ink on the source scan."""

import difflib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf

from .diagrams import DiagramText, diagram_box, diagram_ink
from .source import SCAN_DPI, read_source_page
from .words import PT_PER_PX, InkWord, page_ink, rebuilt_words, scan_words, token

LINE_MERGE_PT = 2.5
OVERFLOW_PT = 2.0
OVERFLOW_ROW_GAP_PX = 3
OVERFLOW_COLUMN_INK_PX = 2


@dataclass(frozen=True)
class WordOffset:
    """Rebuilt minus source, in pt: ink left edge, ink right edge, baseline."""

    text: str
    source_line: int
    dx_left: float
    dx_right: float
    dy: float


@dataclass(frozen=True)
class LineOffset:
    """One source line: its median baseline offset (pt) and whether the rebuilt text breaks at the same word."""

    source_line: int
    dy: float
    ends_agree: bool


@dataclass(frozen=True)
class DiagramOffset:
    """Rebuilt minus source ink box of one diagram: dx, dy of the top-left corner (pt) and width, height ratios.

    `source_box` is the diagram's ink box on the scan (left, top, right, bottom pt).
    """

    name: str
    dx: float
    dy: float
    sx: float
    sy: float
    source_box: tuple[float, float, float, float]


@dataclass(frozen=True)
class PageParity:
    source: Path
    rebuilt: Path
    source_page: int
    rebuilt_pages: tuple[int, ...]
    page_dx: float
    page_dy: float
    ink_iou: float
    lines_source: int
    lines_rebuilt: int
    words_source: int
    words: tuple[WordOffset, ...] = ()
    lines: tuple[LineOffset, ...] = ()
    diagrams: tuple[DiagramOffset, ...] = ()
    right_overflow_lines: int = 0


def right_overflow_lines(source: np.ndarray, rebuilt: np.ndarray, page_dx: float = 0.0) -> int:
    """Lines of rebuilt ink that reach more than `OVERFLOW_PT` past the right edge of the scan's text block,
    once the whole page is moved back by its offset `page_dx` (pt)."""
    cols = np.flatnonzero(source.sum(axis=0) > OVERFLOW_COLUMN_INK_PX)
    if cols.size == 0:
        return 0
    past = rebuilt[:, max(0, cols[-1] + round((OVERFLOW_PT + page_dx) / PT_PER_PX)) :]
    rows = np.flatnonzero(past.any(axis=1))
    bands = np.split(rows, np.flatnonzero(np.diff(rows) > OVERFLOW_ROW_GAP_PX) + 1) if rows.size else []
    return sum(int(past[band[0] : band[-1] + 1].sum(axis=0).max() > OVERFLOW_COLUMN_INK_PX) for band in bands)


def _count_lines(baselines: list[float]) -> int:
    count, last = 0, -np.inf
    for b in sorted(baselines):
        if b - last > LINE_MERGE_PT:
            count, last = count + 1, b
    return count


def _dilate(img: np.ndarray) -> np.ndarray:
    out = img.copy()
    out[1:] |= img[:-1]
    out[:-1] |= img[1:]
    out[:, 1:] |= img[:, :-1]
    out[:, :-1] |= img[:, 1:]
    return out


def common_crop(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    return a[:h, :w], b[:h, :w]


def ink_iou(a: np.ndarray, b: np.ndarray) -> float:
    """Ink overlap of two page masks in place, forgiving one pixel of edge difference."""
    a, b = common_crop(a, b)
    inter = (_dilate(a) & b).sum() + (a & _dilate(b)).sum()
    return float(inter / max(1, a.sum() + b.sum()))


def match_words(src: list[InkWord], ours: list[InkWord]) -> list[tuple[InkWord, InkWord]]:
    """Pairs of the same word in both reading orders: runs of two or more equal tokens, or one word of four letters or more."""
    a, b = [token(w.text) for w in src], [token(w.text) for w in ours]
    pairs = []
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            if blk.size >= 2 or len(a[blk.a + k]) >= 4:
                pairs.append((src[blk.a + k], ours[blk.b + k]))
    return [(s, o) for s, o in pairs if token(s.text)]


def _line_offsets(pairs: list[tuple[InkWord, InkWord]], src: list[InkWord], ours: list[InkWord]) -> tuple[LineOffset, ...]:
    last_src = {w.line: w for w in src}
    last_ours = {w.line: w for w in ours}
    by_line: dict[int, list[tuple[InkWord, InkWord]]] = {}
    for s, o in pairs:
        by_line.setdefault(s.line, []).append((s, o))
    out = []
    for line, line_pairs in sorted(by_line.items()):
        dy = float(np.median([o.baseline - s.baseline for s, o in line_pairs]))
        ends = any(s is last_src[line] and o is last_ours[o.line] for s, o in line_pairs)
        out.append(LineOffset(line, round(dy, 2), ends))
    return tuple(out)


def _diagram_offsets(names: list[Path], a: np.ndarray, b: np.ndarray, work: Path, text: DiagramText) -> tuple[DiagramOffset, ...]:
    out = []
    for snippet in names:
        tmpl, _ = diagram_ink(snippet, work, SCAN_DPI, text)
        sl, st, sr, sb, _ = diagram_box(a, tmpl)
        rl, rt, rr, rb, _ = diagram_box(b, tmpl)
        out.append(DiagramOffset(
            snippet.stem,
            round((rl - sl) * PT_PER_PX, 2),
            round((rt - st) * PT_PER_PX, 2),
            round((rr - rl) / max(1, sr - sl), 4),
            round((rb - rt) / max(1, sb - st), 4),
            (sl * PT_PER_PX, st * PT_PER_PX, sr * PT_PER_PX, sb * PT_PER_PX),
        ))
    return tuple(out)


def diagram_snippets(diagrams: Path | None) -> dict[int, list[Path]]:
    """Snippets `fig_PPP_NNN.typ` keyed by their 1-based source page PPP."""
    found: dict[int, list[Path]] = {}
    for snippet in sorted(diagrams.glob("fig_*.typ")) if diagrams else ():
        found.setdefault(int(snippet.stem.split("_")[1]), []).append(snippet)
    return found


def compare(
    source: Path,
    rebuilt: Path,
    page_map: dict[int, list[int]],
    *,
    ocr: Path,
    diagrams: Path | None = None,
    diagram_text: DiagramText | None = None,
    work: Path | None = None,
) -> list[PageParity]:
    """Scan parity of every mapped page, measured on the first rebuilt page each source page maps to.

    `diagrams` is a folder of the book's `fig_PPP_NNN.typ` snippets; it needs the book's `diagram_text`.
    """
    if diagrams is not None and diagram_text is None:
        raise ValueError("compare needs the book's diagram_text to render its diagram snippets")
    src_doc, our_doc = pymupdf.open(source), pymupdf.open(rebuilt)
    snippets = diagram_snippets(diagrams)
    work = work or Path(rebuilt).parent / "parity_work"
    results = []
    for pno, ours in sorted(page_map.items()):
        a = page_ink(src_doc[pno - 1])
        page = our_doc[ours[0] - 1]
        b = page_ink(page)
        src_page = read_source_page(ocr, pno)
        src = scan_words(a, src_page)
        our = rebuilt_words(page, b)
        pairs = match_words(src, our)
        words = tuple(
            WordOffset(s.text, s.line, round(o.left - s.left, 2), round(o.right - s.right, 2), round(o.baseline - s.baseline, 2))
            for s, o in pairs
        )
        page_dx = round(float(np.median([w.dx_left for w in words])), 2) if words else 0.0
        results.append(PageParity(
            source=Path(source),
            rebuilt=Path(rebuilt),
            source_page=pno,
            rebuilt_pages=tuple(ours),
            page_dx=page_dx,
            page_dy=round(float(np.median([w.dy for w in words])), 2) if words else 0.0,
            ink_iou=round(ink_iou(a, b), 3),
            lines_source=_count_lines([src_page.top_pt(line) for line in src_page.lines]),
            lines_rebuilt=_count_lines([w.baseline for w in our]),
            words_source=len(src),
            words=words,
            lines=_line_offsets(pairs, src, our),
            diagrams=_diagram_offsets(snippets.get(pno, []), a, b, work, diagram_text) if diagram_text else (),
            right_overflow_lines=right_overflow_lines(a, b, page_dx),
        ))
        print(f"parity page {pno}: {len(words)}/{len(src)} words matched", flush=True)
    return results
