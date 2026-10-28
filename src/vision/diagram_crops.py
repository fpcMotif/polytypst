"""Commutative diagrams cropped from scan page renders, for books whose diagrams have no caption.

A diagram's vertical arrows join its rows of objects into one tall band of ink, while text lines are short bands.
The NNN-th such band on page PPP is the page's NNN-th array diagram in the transcript, saved as `fig_PPP_NNN.png`."""

import shutil
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image

from ..book_state import book_state
from ..compiler.diagrams import page_diagrams, scan_diagram_id
from ..ocr.transcripts import TranscriptStore

Box = tuple[int, int, int, int]
INK = 140
PAD = 8


def _runs(mask: np.ndarray, gap: int) -> list[tuple[int, int]]:
    """Start and end of each run of True in `mask`, joining runs split by at most `gap` False entries."""
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    breaks = np.flatnonzero(np.diff(idx) > gap + 1)
    starts = np.concatenate(([idx[0]], idx[breaks + 1]))
    ends = np.concatenate((idx[breaks], [idx[-1]]))
    return list(zip(starts.tolist(), (ends + 1).tolist(), strict=True))


def diagram_boxes(render: Image.Image) -> list[Box]:
    """(left, top, right, bottom) of each diagram on a page render, top to bottom."""
    ink = np.asarray(render.convert("L")) < INK
    cols = _runs(ink.sum(axis=0) > 2, 0)
    if not cols:
        return []
    text_left, text_right = cols[0][0], cols[-1][1]
    width = text_right - text_left
    bands = _runs(ink.sum(axis=1) > 2, 3)
    line = float(np.median([b - a for a, b in bands]))
    rows = []
    for top, bottom in bands:
        used = ink[top:bottom].any(axis=0)
        clusters = _runs(used, round(width * 0.06))
        arrows = (
            bottom - top > 1.5 * line
            and clusters[0][0] > text_left + width * 0.08
            and used.sum() < width * 0.1
        )
        if len(clusters) > 1 and clusters[0][1] < text_left + width * 0.25:
            clusters = clusters[1:]
        left, right = clusters[0][0], clusters[-1][1]
        centered = left >= text_left + width * 0.08 and right <= text_right - width * 0.08
        rows.append((top, bottom, left, right, centered, arrows))
    near = [i > 0 and top - rows[i - 1][1] < 0.9 * line for i, (top, *_) in enumerate(rows)]
    blocks: list[list[int]] = []
    for i, (top, bottom, left, right, centered, _) in enumerate(rows):
        beside_arrows = (near[i] and rows[i - 1][5]) or (i + 1 < len(rows) and near[i + 1] and rows[i + 1][5])
        if not (centered or beside_arrows):
            blocks.append([])
        elif near[i] and blocks and blocks[-1]:
            b = blocks[-1]
            blocks[-1] = [min(b[0], left), b[1], max(b[2], right), bottom]
        else:
            blocks.append([left, top, right, bottom])
    return [
        (left - PAD, top - PAD, right + PAD, bottom + PAD)
        for left, top, right, bottom in (b for b in blocks if b)
        if bottom - top >= 2.5 * line
    ]


def match_boxes(boxes: list[Box], places: list[float], height: int) -> list[Box] | None:
    """The boxes, in order, whose middles lie nearest the transcript diagrams' places, as shares of the page height."""
    if len(boxes) < len(places):
        return None
    middles = [(b[1] + b[3]) / 2 / height for b in boxes]
    best = min(
        combinations(range(len(boxes)), len(places)),
        key=lambda pick: sum(
            abs(middles[i] - p) for i, p in zip(pick, places, strict=True)
        ),
    )
    return [boxes[i] for i in best]


def install_scan_diagrams(snippets: Path, out_dir: Path) -> list[Path]:
    """Copy the snippets into `out_dir/figures` and crop each transcript array diagram from its page render."""
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    written = [
        Path(shutil.copy2(src, fig_dir / src.name))
        for src in sorted(snippets.glob("fig_*.typ"))
    ]
    for fig, (render, box) in scan_diagram_boxes(out_dir).items():
        path = fig_dir / f"fig_{fig}.png"
        with Image.open(render) as im:
            im.crop(box).save(path, dpi=(300, 300))
        written.append(path)
    return written


def scan_diagram_boxes(out_dir: Path) -> dict[str, tuple[Path, Box]]:
    """Each transcript array diagram's id `PPP_NNN`, with its page render and its box on that render."""
    store = TranscriptStore(book_state(out_dir) / "markdown_pages")
    found: dict[str, tuple[Path, Box]] = {}
    for render in sorted((out_dir / "page_renders").glob("p_*.png")):
        page = int(render.stem.removeprefix("p_"))
        text = store.text(page) or ""
        places = [m.start() / len(text) for m in page_diagrams(text)]
        if not places:
            continue
        with Image.open(render) as im:
            boxes = match_boxes(diagram_boxes(im), places, im.size[1])
        if boxes is None:
            print(f"page {page}: the scan shows fewer diagrams than the transcript's {len(places)}; no crops")
            continue
        for k, box in enumerate(boxes, 1):
            found[scan_diagram_id(page, k)] = (render, box)
    return found
