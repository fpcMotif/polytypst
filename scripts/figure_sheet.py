"""Put every figure image of a book on contact sheets, 3 to a row, each labelled with its file name.

Usage: uv run python scripts/figure_sheet.py output/4_不良债权与金融危机/figures OUT_DIR
       uv run python scripts/figure_sheet.py --pdf output/6_劳动力市场与收入分配/6.pdf OUT_DIR [--pages 180,323]

A crop that holds only notes, a rotated table, a cut chart or a tiny chart shows at a glance.
A caption with no image is not on a sheet: compare `fig_*.png` with the captions in the book.

With --pdf, the sheets show the rebuilt pages that hold an image instead, 3 to a row, each
labelled with its page number. They show how each figure sits in the layout: a figure printed
too small, two charts squeezed side by side, or a crop edge that catches a note line.
--pages limits them to the listed 1-based pages.
"""

import argparse
import re
from pathlib import Path

import pymupdf

from polytypst.compare_sheet import Panel, write_sheets

COLS = 3


def figure_order(path: Path) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", path.stem))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("figures", type=Path, nargs="?")
    parser.add_argument("out", type=Path)
    parser.add_argument("--pdf", type=Path, help="sheet the rebuilt pages that hold an image")
    parser.add_argument("--pages", default="", help="with --pdf: comma-separated 1-based pages")
    args = parser.parse_args()
    if args.pdf:
        with pymupdf.open(args.pdf) as doc:
            wanted = [int(p) for p in args.pages.split(",")] if args.pages else [n + 1 for n, p in enumerate(doc) if p.get_images()]
        panels, name = [Panel(f"p{n}", args.pdf, n) for n in wanted], "pages.png"
    else:
        figures = sorted(args.figures.glob("fig_*.png"), key=figure_order)
        panels, name = [Panel(fig.stem, fig, 1) for fig in figures], "sheet.png"
    rows = [panels[n : n + COLS] for n in range(0, len(panels), COLS)]
    for path in write_sheets(rows, args.out / name):
        print(path)


if __name__ == "__main__":
    main()
