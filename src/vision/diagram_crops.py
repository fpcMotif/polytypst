"""Commutative diagrams cropped from scan page renders, for books whose diagrams have no caption.

A diagram's vertical arrows join its rows of objects into one tall band of ink, while text lines are short bands.
The NNN-th such band on page PPP is the page's NNN-th array diagram in the transcript, saved as `fig_PPP_NNN.png`."""

import shutil
from collections.abc import Mapping
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image

from ..book_state import transcripts
from ..compiler.diagrams import page_scan_diagrams, page_unread_diagrams
from ..ocr.scan import SourceScan
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
    """Each transcript array or unread diagram's id, with its page render and its box on that render.

    A page whose scan shows fewer diagrams than its transcript keeps boxes for its array diagrams alone when it can."""
    store = TranscriptStore(transcripts(out_dir))
    found: dict[str, tuple[Path, Box]] = {}
    for render in sorted(p for ext in ("png", "jpg") for p in (out_dir / "page_renders").glob(f"p_*.{ext}")):
        page = int(render.stem.removeprefix("p_"))
        text = store.text(page) or ""
        diagrams = page_scan_diagrams(text, page)
        if not diagrams:
            continue
        with Image.open(render) as im:
            boxes, height = diagram_boxes(im), im.size[1]
        picked = match_boxes(boxes, [m.start() / len(text) for m, _ in diagrams], height)
        if picked is None:
            print(f"page {page}: the scan shows {len(boxes)} diagrams, the transcript {len(diagrams)}; array diagrams only")
            diagrams = [(m, fig) for m, fig in diagrams if "_u" not in fig]
            picked = match_boxes(boxes, [m.start() / len(text) for m, _ in diagrams], height) if diagrams else None
        if picked is None:
            continue
        for (_, fig), box in zip(diagrams, picked, strict=True):
            found[fig] = (render, box)
    return found


def install_unread_diagrams(
    out_dir: Path, scan: SourceScan, dpi: int, boxes: Mapping[str, tuple[int, ...]] = {}
) -> list[Path]:
    """Render the pages that hold unread diagrams at `dpi` and crop each one into `out_dir/figures/fig_PPP_uNNN.png`.

    `boxes` overrides the box found for an id; an empty box keeps that diagram's transcript."""
    fig_dir = out_dir / "figures"
    for stale in fig_dir.glob("fig_*_u*.png"):
        stale.unlink()
    store = TranscriptStore(transcripts(out_dir))
    pages = [p for p in store.pages() if page_unread_diagrams(store.text(p) or "")]
    if not pages:
        return []
    renders = {r.number: r.path for r in scan.pages(out_dir / "page_renders", dpi=dpi, numbers=pages)}
    crops = {fig: found for fig, found in scan_diagram_boxes(out_dir).items() if "_u" in fig}
    for fig, box in boxes.items():
        crops.pop(fig, None)
        if box:
            crops[fig] = (renders[int(fig.split("_")[0])], box)
    fig_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fig, (render, box) in crops.items():
        path = fig_dir / f"fig_{fig}.png"
        with Image.open(render) as im:
            im.crop(box).save(path, dpi=(300, 300))
        written.append(path)
    return written
