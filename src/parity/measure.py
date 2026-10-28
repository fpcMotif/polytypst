"""Per-page measures of a rebuilt facsimile against its scan, and a gate that fails on any page that got worse.

Coverage cuts a page into CELL x CELL px cells (2pt at 300 dpi). A scan cell with ink is covered when the rebuilt
page has ink in it or in a neighbouring cell. Uncovered cells are grouped into 8-connected regions and called a rule
(one cell thick, long), a figure (both sides over FIGURE_PT) or text. Extra, missing and layout are the optical
shares of `page_visual`.
"""

import json
import os
from collections import Counter, deque
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pymupdf

from .ink_cache import InkCache
from .visual import REGRESSION_SHARE, page_visual
from .words import PT_PER_PX, page_ink

CELL = 8
FIGURE_PT = 40.0
RULE_PT = 30.0
MIN_CELLS = 2
COVERAGE_DROP = 0.002


@dataclass(frozen=True)
class PageMeasure:
    """One page's covered share of scan ink cells, its optical shares, and its uncovered cells by kind."""

    page: int
    coverage: float
    extra: float
    missing: float
    layout: float
    misses: dict[str, int] = field(default_factory=dict)


def cells(ink: np.ndarray) -> np.ndarray:
    h, w = ink.shape[0] // CELL * CELL, ink.shape[1] // CELL * CELL
    return ink[:h, :w].reshape(h // CELL, CELL, w // CELL, CELL).any(axis=(1, 3))


def grow(grid: np.ndarray) -> np.ndarray:
    g = np.pad(grid, 1)
    return np.logical_or.reduce(
        [g[1 + dy : g.shape[0] - 1 + dy, 1 + dx : g.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    )


def regions(grid: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """The (top, left, bottom, right, cells) of each 8-connected region of set cells."""
    seen = np.zeros_like(grid)
    found = []
    for y, x in zip(*np.nonzero(grid), strict=True):
        if seen[y, x]:
            continue
        queue, box, n = deque([(y, x)]), [y, x, y, x], 0
        seen[y, x] = True
        while queue:
            cy, cx = queue.popleft()
            n += 1
            box = [min(box[0], cy), min(box[1], cx), max(box[2], cy), max(box[3], cx)]
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < grid.shape[0] and 0 <= nx < grid.shape[1] and grid[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
        found.append((*box, n))
    return found


def miss_kind(top: int, left: int, bottom: int, right: int) -> str:
    h, w = (bottom - top + 1) * CELL * PT_PER_PX, (right - left + 1) * CELL * PT_PER_PX
    thin = 2 * CELL * PT_PER_PX
    if (h <= thin and w >= RULE_PT) or (w <= thin and h >= RULE_PT):
        return "rule"
    return "figure" if h >= FIGURE_PT and w >= FIGURE_PT else "text"


def page_measure(scan: np.ndarray, built: np.ndarray, page: int) -> PageMeasure:
    s, b = cells(scan), cells(built)
    b = b[: s.shape[0], : s.shape[1]]
    s = s[: b.shape[0], : b.shape[1]]
    miss = s & ~grow(b)
    misses: Counter[str] = Counter()
    for top, left, bottom, right, n in regions(miss):
        if n >= MIN_CELLS:
            misses[miss_kind(top, left, bottom, right)] += n
    optical = page_visual(scan, built, page, page)
    return PageMeasure(
        page, round(float(1 - miss.sum() / max(int(s.sum()), 1)), 4),
        optical.extra, optical.missing, optical.layout, dict(misses),
    )


_WORKER: dict = {}


def _start_worker(scan: InkCache, rebuilt: Path) -> None:
    _WORKER.update(scan=scan, rebuilt=pymupdf.open(rebuilt))


def _measure_job(pair: tuple[int, int]) -> PageMeasure:
    source_page, rebuilt_page = pair
    return page_measure(_WORKER["scan"](source_page), page_ink(_WORKER["rebuilt"][rebuilt_page - 1]), source_page)


def measure_pages(scan: InkCache, rebuilt: Path, page_map: dict[int, int]) -> list[PageMeasure]:
    """Measure each scan page against the `rebuilt` page it maps to, in parallel, in scan page order."""
    pairs = sorted(page_map.items())
    with ProcessPoolExecutor(
        min(os.cpu_count() or 1, max(len(pairs), 1)), initializer=_start_worker, initargs=(scan, rebuilt)
    ) as pool:
        return list(pool.map(_measure_job, pairs, chunksize=4))


def worse(new: PageMeasure, old: PageMeasure) -> list[str]:
    """Each measure on which `new` is worse than `old` by more than its tolerance, as 'name old -> new'."""
    out = []
    if new.coverage < old.coverage - COVERAGE_DROP:
        out.append(f"coverage {old.coverage} -> {new.coverage}")
    for name in ("extra", "missing", "layout"):
        if getattr(new, name) > getattr(old, name) + REGRESSION_SHARE:
            out.append(f"{name} {getattr(old, name)} -> {getattr(new, name)}")
    return out


def read_measures(path: Path) -> dict[int, PageMeasure]:
    if not path.exists():
        return {}
    return {m["page"]: PageMeasure(**m) for m in json.loads(path.read_text(encoding="utf-8"))}


def write_measures(path: Path, measures: Iterable[PageMeasure]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(m) for m in sorted(measures, key=lambda m: m.page)]
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
