"""Overlay rebuilt Bourbaki pages on the original scan and diff them with odiff.

Usage: uv run python scripts/bourbaki_redshift.py OUT_DIR ORIG_PAGE:OURS_PAGE [...]
Pages are 1-based. Red ink is only in the original, cyan only in ours, black in both.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

from polytypst.bourbaki.pagefit import ORIGINAL, REBUILT

DPI = 150


def render(doc: pymupdf.Document, page: int, size: tuple[int, int]) -> Image.Image:
    pix = doc[page - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    im = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    return im.resize(size, Image.Resampling.LANCZOS)


def ink_page(doc: pymupdf.Document, needle: str) -> int | None:
    for i, page in enumerate(doc):
        if needle in page.get_text():
            return i + 1
    return None


def main(out_dir: Path, pairs: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    orig, ours = pymupdf.open(ORIGINAL), pymupdf.open(REBUILT)
    for pair in pairs:
        o_page, r_ref = pair.split(":")
        r_page = int(r_ref) if r_ref.isdigit() else ink_page(ours, r_ref)
        if r_page is None:
            print(f"{pair}: text not found in rebuilt PDF")
            continue
        o_rect = orig[int(o_page) - 1].rect
        size = (round(o_rect.width * DPI / 72), round(o_rect.height * DPI / 72))
        a = render(orig, int(o_page), size)
        b = render(ours, r_page, size)
        a_ink, b_ink = np.asarray(a) < 160, np.asarray(b) < 160
        rgb = np.full((*a_ink.shape, 3), 255, np.uint8)
        rgb[a_ink & ~b_ink] = (220, 0, 0)
        rgb[b_ink & ~a_ink] = (0, 170, 220)
        rgb[a_ink & b_ink] = (0, 0, 0)
        stem = f"p{int(o_page):03d}_vs_{r_page:03d}"
        Image.fromarray(rgb).save(out_dir / f"{stem}_redshift.png")
        a.save(out_dir / f"{stem}_orig.png")
        b.save(out_dir / f"{stem}_ours.png")
        res = subprocess.run(
            ["bunx", "--bun", "odiff-bin", str(out_dir / f"{stem}_orig.png"), str(out_dir / f"{stem}_ours.png"),
             str(out_dir / f"{stem}_odiff.png"), "--threshold=0.3", "--antialiasing"],
            capture_output=True, text=True, check=False,
        )
        overlap = (a_ink & b_ink).sum() / max(1, (a_ink | b_ink).sum())
        summary = (res.stdout.strip().splitlines() or [res.stderr.strip()])[-1]
        print(f"orig {o_page} vs ours {r_page}: ink IoU {overlap:.3f} | odiff: {summary}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2:])
