import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ORIGINAL = Path.home() / "Downloads" / "Elements of Mathematics Commutative Algebra Chapters 1-7 (Nicolas Bourbaki) .pdf"
OUT_DIR = Path("output/bourbaki")
TYP = OUT_DIR / "bourbaki_1970_vintage.typ"
REBUILT = OUT_DIR / "bourbaki_1970_vintage.pdf"
FONTS = Path("fonts")


def query_marks(inputs: dict[str, str] | None = None) -> list[dict]:
    """Source-page position markers (kind, key, page, y) from the compiled vintage Typst source."""
    flags = [arg for k, v in (inputs or {}).items() for arg in ("--input", f"{k}={v}")]
    res = subprocess.run(
        ["typst", "query", "--font-path", str(FONTS), *flags, str(TYP), "<src-mark>", "--field", "value"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(res.stdout)


def _blur(img: np.ndarray, r: int) -> np.ndarray:
    out = img.astype(np.float32)
    for axis in (0, 1):
        acc = np.zeros_like(out)
        for d in range(-r, r + 1):
            acc += np.roll(out, d, axis=axis)
        out = acc / (2 * r + 1)
    return out


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
    fp = np.fft.rfft2(p, s=(h, w))
    blocks = display_blocks(page, int(tmpl.shape[0] * 0.5))
    best = (0, 0, tmpl.shape[0], tmpl.shape[1], -np.inf)
    for s in scales:
        th, tw = max(1, round(tmpl.shape[0] * s)), max(1, round(tmpl.shape[1] * s))
        if th >= h or tw >= w:
            continue
        t = np.asarray(Image.fromarray(tmpl.astype(np.uint8) * 255).resize((tw, th), Image.Resampling.BILINEAR)) > 100
        t = _blur(t, 2)
        t = (t - t.mean()) / (t.std() * t.size + 1e-6)
        corr = np.fft.irfft2(fp * np.fft.rfft2(t[::-1, ::-1], s=(h, w)), s=(h, w))[th - 1 :, tw - 1 :]
        if blocks:
            allowed = np.zeros(corr.shape[0], bool)
            for top, bottom in blocks:
                allowed[max(0, top - th // 3) : min(corr.shape[0], bottom - th // 2 + 1)] = True
            corr = np.where(allowed[:, None], corr, -np.inf)
        y, x = np.unravel_index(np.argmax(corr), corr.shape)
        local = p[y : y + th, x : x + tw]
        score = float(corr[y, x] / (local.std() + 1e-6))
        if score > best[4]:
            best = (int(y), int(x), th, tw, score)
    return best
