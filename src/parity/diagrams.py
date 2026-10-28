from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from ..compiler.typst_math import compile_typst

HARNESS = Path(__file__).parent / "diagram_harness.typ"
INK_LEVEL = 140


@dataclass(frozen=True)
class DiagramText:
    """Text settings a book's diagram snippets are set in (font family, size in pt, weight)."""

    font: str
    size: float
    weight: int


def diagram_ink(snippet: Path, work: Path, dpi: int, text: DiagramText) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Ink mask of a Typst diagram snippet at `dpi`, trimmed to its ink, and its ink insets (pt) inside the snippet box."""
    work.mkdir(parents=True, exist_ok=True)
    png = work / f"{snippet.stem}@{dpi}.png"
    if not png.exists():
        inputs = {"snippet": str(snippet.resolve()), "font": text.font, "size": str(text.size), "weight": str(text.weight)}
        flags = [arg for k, v in inputs.items() for arg in ("--input", f"{k}={v}")]
        compile_typst(HARNESS, png, "--root", "/", *flags, "--ppi", str(dpi), capture_output=True)
    img = np.asarray(Image.open(png).convert("L")) < INK_LEVEL
    ys, xs = np.where(img)
    k = 72 / dpi
    inset = (xs.min() * k, ys.min() * k, (img.shape[1] - xs.max() - 1) * k, (img.shape[0] - ys.max() - 1) * k)
    return img[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1], inset


def diagram_box(page: np.ndarray, tmpl: np.ndarray, scales: tuple[float, ...] = (0.9, 0.95, 1.0, 1.05, 1.1, 1.15)) -> tuple[int, int, int, int, float]:
    """The ink box (left, top, right, bottom px) of the best template match on a page, and its score."""
    y, x, th, tw, score = find_diagram(page, tmpl, scales)
    pad = max(2, round(0.04 * max(th, tw)))
    region = page[max(0, y - pad) : y + th + pad, max(0, x - pad) : x + tw + pad]
    ys, xs = np.where(region)
    if ys.size == 0:
        return x, y, x + tw, y + th, score
    ox, oy = max(0, x - pad), max(0, y - pad)
    return ox + int(xs.min()), oy + int(ys.min()), ox + int(xs.max()) + 1, oy + int(ys.max()) + 1, score


def _blur(img: np.ndarray, r: int) -> np.ndarray:
    out = img.astype(np.float32)
    for axis in (0, 1):
        acc = np.zeros_like(out)
        for d in range(-r, r + 1):
            acc += np.roll(out, d, axis=axis)
        out = acc / (2 * r + 1)
    return out


def _fast_len(n: int) -> int:
    while True:
        m = n
        for f in (2, 3, 5):
            while m % f == 0:
                m //= f
        if m == 1:
            return n
        n += 1


def display_blocks(page: np.ndarray, min_height: int) -> list[tuple[int, int]]:
    """Vertical spans of rows indented on both sides of the text block (diagram candidates)."""
    cols = np.where(page.sum(axis=0) > 2)[0]
    if cols.size == 0:
        return []
    left, right = np.percentile(cols, 1), np.percentile(cols, 99)
    margin = 0.06 * (right - left)
    on = np.append(page.sum(axis=1) > 1, False)
    spans, start = [], None
    for y, v in enumerate(on):
        if v and start is None:
            start = y
        elif not v and start is not None:
            xs = np.where(page[start:y].any(axis=0))[0]
            spans.append((start, y, xs.min() > left + margin and xs.max() < right - margin))
            start = None
    blocks: list[tuple[int, int]] = []
    gap = max(4, min_height // 4)
    for a, b, indented in spans:
        if not indented:
            continue
        if blocks and a - blocks[-1][1] <= gap:
            blocks[-1] = (blocks[-1][0], b)
        else:
            blocks.append((a, b))
    return [blk for blk in blocks if blk[1] - blk[0] >= min_height]


def find_diagram(page: np.ndarray, tmpl: np.ndarray, scales: tuple[float, ...] = (0.95, 1.0, 1.05, 1.1)) -> tuple[int, int, int, int, float]:
    """Best match of a diagram ink template on a page ink map: (y, x, height, width, score).

    The template is zero-mean, so dense body text scores low where the diagram has blank space.
    Only tops near a both-sides-indented block of rows are considered when the page has one.
    """
    p = _blur(page, 2)
    h, w = p.shape
    blocks = display_blocks(page, int(tmpl.shape[0] * 0.5))
    sizes = [(max(1, round(tmpl.shape[0] * s)), max(1, round(tmpl.shape[1] * s))) for s in scales]
    sizes = [(th, tw) for th, tw in sizes if th < h and tw < w]
    top, end = 0, h
    if blocks and sizes:
        th_max = max(th for th, _ in sizes)
        top = max(0, min(a for a, _ in blocks) - th_max // 3)
        end = min(h, max(b for _, b in blocks) + th_max)
    band = p[top:end]
    shape = (_fast_len(band.shape[0]), _fast_len(w))
    fp = np.fft.rfft2(band, s=shape)

    def match(size: tuple[int, int]) -> tuple[int, int, int, int, float]:
        th, tw = size
        if th > band.shape[0]:
            return (0, 0, th, tw, -np.inf)
        t = np.asarray(Image.fromarray(tmpl.astype(np.uint8) * 255).resize((tw, th), Image.Resampling.BILINEAR)) > 100
        t = _blur(t, 2)
        t = (t - t.mean()) / (t.std() * t.size + 1e-6)
        corr = np.fft.irfft2(fp * np.fft.rfft2(t[::-1, ::-1], s=shape), s=shape)[th - 1 : band.shape[0], tw - 1 : w]
        if blocks:
            allowed = np.zeros(h - th + 1, bool)
            for a, b in blocks:
                allowed[max(0, a - th // 3) : min(h - th + 1, b - th // 2 + 1)] = True
            corr = np.where(allowed[top : top + corr.shape[0], None], corr, -np.inf)
        y, x = np.unravel_index(np.argmax(corr), corr.shape)
        local = band[y : y + th, x : x + tw]
        return (top + int(y), int(x), th, tw, float(corr[y, x] / (local.std() + 1e-6)))

    best = (0, 0, tmpl.shape[0], tmpl.shape[1], -np.inf)
    with ThreadPoolExecutor(max(1, len(sizes))) as pool:
        for found in pool.map(match, sizes):
            if found[4] > best[4]:
                best = found
    return best
