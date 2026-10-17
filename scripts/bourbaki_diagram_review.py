"""Build a side-by-side review page: each original Bourbaki diagram next to its fletcher version.

Usage: uv run python scripts/bourbaki_diagram_review.py

The original crop is found by matching our render against the scan page, so a
wrong crop from the old figure extractor is never reused. Writes
output/bourbaki/diagram_review/index.html with original, fletcher, and a
red/cyan overlay (red only in the original, cyan only in ours) per diagram.
"""

import html
import subprocess
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

from polytypst.bourbaki import DIAGRAM_DIR
from polytypst.bourbaki.pagefit import FONTS, ORIGINAL, find_diagram

OUT = Path("output/bourbaki/diagram_review")
DPI = 200
PAD = 14


def ink(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L")) < 150


def trim(img: Image.Image) -> Image.Image:
    ys, xs = np.where(ink(img))
    return img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)) if ys.size else img


def render_fletcher(fig: str) -> Image.Image:
    png = OUT / f"{fig}_fletcher_raw.png"
    subprocess.run(
        ["typst", "compile", "--root", ".", "--font-path", str(FONTS), "--input", f"id={fig}",
         "output/_proto/diag.typ", str(png), "--ppi", str(DPI)],
        check=True, capture_output=True,
    )
    img = trim(Image.open(png).convert("L"))
    png.unlink()
    return img


def overlay(orig: Image.Image, ours: Image.Image) -> Image.Image:
    w, h = max(orig.width, ours.width), max(orig.height, ours.height)
    a, b = np.zeros((h, w), bool), np.zeros((h, w), bool)
    a[: orig.height, : orig.width] = ink(orig)
    b[: ours.height, : ours.width] = ink(ours)
    rgb = np.full((h, w, 3), 255, np.uint8)
    rgb[a & ~b] = (220, 0, 0)
    rgb[b & ~a] = (0, 170, 220)
    rgb[a & b] = (0, 0, 0)
    return Image.fromarray(rgb)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(ORIGINAL)
    rows = []
    k = 72 / DPI
    for src in sorted(DIAGRAM_DIR.glob("fig_*.typ")):
        fig = src.stem.removeprefix("fig_")
        pno = int(fig.split("_")[0])
        ours = render_fletcher(fig)
        pix = doc[pno - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
        page = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        y, x, th, tw, score = find_diagram(ink(page), ink(ours))
        box = (max(0, x - PAD), max(0, y - PAD), min(page.width, x + tw + PAD), min(page.height, y + th + PAD))
        orig = trim(page.crop(box))
        orig.save(OUT / f"{fig}_original.png")
        ours.save(OUT / f"{fig}_fletcher.png")
        overlay(orig, ours).save(OUT / f"{fig}_overlay.png")
        rows.append((fig, pno, score, orig.size, ours.size))
        print(f"{fig}: page {pno}, match {score:.2f}, original {orig.width * k:.0f}x{orig.height * k:.0f}pt, "
              f"fletcher {ours.width * k:.0f}x{ours.height * k:.0f}pt", flush=True)

    items = "\n".join(
        f"""<tr id="d{fig}"><td class="meta"><b>{html.escape(fig)}</b><br>PDF page {pno}<br>
match {score:.2f}{' <span class="warn">check</span>' if score < 0.5 else ''}<br>
original {o[0] * k:.0f}&times;{o[1] * k:.0f}pt<br>fletcher {f[0] * k:.0f}&times;{f[1] * k:.0f}pt</td>
<td><img src="{fig}_original.png" alt="original {fig}"></td>
<td><img src="{fig}_fletcher.png" alt="fletcher {fig}"></td>
<td><img src="{fig}_overlay.png" alt="overlay {fig}"></td></tr>"""
        for fig, pno, score, o, f in rows
    )
    (OUT / "index.html").write_text(f"""<!doctype html>
<meta charset="utf-8"><title>Bourbaki diagram review</title>
<style>
body {{ font: 14px system-ui, sans-serif; margin: 16px; background: #fff; color: #111; }}
table {{ border-collapse: collapse; }}
td, th {{ border-bottom: 1px solid #ddd; padding: 10px; vertical-align: middle; }}
th {{ text-align: left; position: sticky; top: 0; background: #fff; }}
img {{ max-width: 46vw; height: auto; display: block; }}
.meta {{ white-space: nowrap; font-size: 12px; color: #444; }}
.warn {{ color: #b00; font-weight: 600; }}
</style>
<h1>Bourbaki commutative diagrams: original vs fletcher</h1>
<p>{len(rows)} diagrams. Overlay: red only in the original, cyan only in fletcher, black in both.
A low match score means the automatic crop may have found the wrong spot on the page.</p>
<table><tr><th></th><th>Original scan</th><th>Fletcher (Typst)</th><th>Overlay</th></tr>
{items}
</table>
""", encoding="utf-8")
    print(f"wrote {OUT / 'index.html'}", flush=True)


if __name__ == "__main__":
    main()
