"""Put each redrawn chart beside its scan crop, so a reviewer can check the redraw's data against the scan.

Usage: mise exec -- uv run python scripts/figure_compare.py KEY [FIGURE_ID ...] [--out DIR]

Writes one PNG per figure, the scan crop on the left and the printed SVG on the right at the same height,
into output/KEY/review/figure_compare/ unless --out names another folder. The crop comes from the source
scan, $POLYTYPST_SOURCES/<source_pdf>, at the figure's figures_manifest.json box.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import tomllib
from pathlib import Path

import pymupdf
from PIL import Image

from polytypst.books import book_by_key, book_folders

CROP_DPI = 200
PANEL_H = 900


def scan_crop(scan: pymupdf.Document, page: int, box: list[float]) -> Image.Image:
    p = scan[page - 1]
    r = p.rect
    clip = pymupdf.Rect(r.x0 + box[0] * r.width, r.y0 + box[1] * r.height, r.x0 + box[2] * r.width, r.y0 + box[3] * r.height)
    pix = p.get_pixmap(dpi=CROP_DPI, clip=clip)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def svg_render(svg: Path) -> Image.Image:
    doc = pymupdf.open("svg", svg.read_bytes())
    try:
        pix = doc[0].get_pixmap(dpi=CROP_DPI)
    finally:
        doc.close()
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def side_by_side(left: Image.Image, right: Image.Image) -> Image.Image:
    def fit(im: Image.Image) -> Image.Image:
        return im.resize((max(1, round(im.width * PANEL_H / im.height)), PANEL_H))

    a, b = fit(left), fit(right)
    out = Image.new("RGB", (a.width + b.width + 30, PANEL_H), "white")
    out.paste(a, (0, 0))
    out.paste(b, (a.width + 30, 0))
    for y in range(PANEL_H):
        out.putpixel((a.width + 15, y), (200, 0, 0))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("key")
    parser.add_argument("ids", nargs="*", help="figure ids such as 3-2; every redrawn figure when omitted")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    book = book_by_key(args.key)
    out_dir = book.out_dir
    source_pdf = tomllib.loads((book_folders()[args.key] / "book.toml").read_text(encoding="utf-8"))["source_pdf"]
    scan = pymupdf.open(Path(os.environ["POLYTYPST_SOURCES"]) / source_pdf)
    manifest = {e["figure_id"]: e for e in json.loads((out_dir / "figures_manifest.json").read_text(encoding="utf-8"))}
    dest = args.out or out_dir / "review" / "figure_compare"
    dest.mkdir(parents=True, exist_ok=True)
    ids = args.ids or sorted(fid for fid in manifest if (out_dir / "figures" / f"fig_{fid}.svg").exists())
    done = 0
    for fid in ids:
        entry = manifest.get(fid)
        svg = out_dir / "figures" / f"fig_{fid}.svg"
        if not entry or not entry.get("box") or not svg.exists():
            print(f"{fid}: no scan box or no SVG")
            continue
        side_by_side(scan_crop(scan, int(entry["source_page"]), entry["box"]), svg_render(svg)).save(dest / f"fig_{fid}.png")
        done += 1
    print(f"{done} comparisons in {dest}")


if __name__ == "__main__":
    main()
