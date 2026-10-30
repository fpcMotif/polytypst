"""Render PDF pages, or a region of each, to PNG files for a look at print size.

Usage: uv run python scripts/page_png.py PDF OUT_PREFIX --pages 58,59 [--dpi 150] [--clip L,T,R,B] [--rotate 90]

Pages count from 1. Each page goes to OUT_PREFIX + "p58.png", and the script prints each path.
--clip keeps the box L,T,R,B given in shares of the page, such as 0,0.4,1,0.8 for the middle band,
so a figure's labels or a note line can be read at 300 dpi without rendering the whole page.
Find the pages with scripts/find_pages.py. To compare with the scan, use scripts/review_sheet.py.
"""

import argparse
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("prefix", help="output path prefix, such as /tmp/book1-")
    parser.add_argument("--pages", required=True, help="comma-separated 1-based pages")
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--clip", help="L,T,R,B in shares of the page")
    parser.add_argument("--rotate", type=int, default=0, help="degrees clockwise, such as 90 for a table printed sideways")
    args = parser.parse_args()

    doc = pymupdf.open(args.pdf)
    for n in (int(p) for p in args.pages.split(",") if p):
        page = doc[n - 1]
        clip = None
        if args.clip:
            left, top, right, bottom = (float(v) for v in args.clip.split(","))
            r = page.rect
            clip = pymupdf.Rect(r.x0 + left * r.width, r.y0 + top * r.height, r.x0 + right * r.width, r.y0 + bottom * r.height)
        out = f"{args.prefix}p{n}.png"
        zoom = args.dpi / 72
        page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom).prerotate(args.rotate), clip=clip).save(out)
        print(out)


if __name__ == "__main__":
    main()
