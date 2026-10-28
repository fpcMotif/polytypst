"""Put every figure image of a book on contact sheets, 12 to a sheet, each labelled with its file name.

Usage: uv run python scripts/figure_sheet.py output/4_不良债权与金融危机/figures OUT_DIR
       uv run python scripts/figure_sheet.py --pdf output/6_劳动力市场与收入分配/6.pdf OUT_DIR [--pages 180,323]

A crop that holds only notes, a rotated table, a cut chart or a tiny chart shows at a glance.
A caption with no image is not on a sheet: compare `fig_*.png` with the captions in the book.

With --pdf, the sheets show the rebuilt pages that hold an image instead, 6 to a sheet, each
labelled with its page number. They show how each figure sits in the layout: a figure printed
too small, two charts squeezed side by side, or a crop edge that catches a note line.
--pages limits them to the listed 1-based pages.
"""

import argparse
import re
from pathlib import Path

import pymupdf

COLS, ROWS, CELL_W, CELL_H = 3, 4, 260, 190


def figure_order(path: Path) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", path.stem))


def page_sheets(pdf: Path, out: Path, pages: str) -> None:
    doc = pymupdf.open(pdf)
    wanted = [int(p) - 1 for p in pages.split(",")] if pages else [i for i, p in enumerate(doc) if p.get_images()]
    w, h = doc[0].rect.width, doc[0].rect.height
    for start in range(0, len(wanted), 6):
        sheet = pymupdf.open()
        page = sheet.new_page(width=w * 3, height=h * 2)
        for i, number in enumerate(wanted[start : start + 6]):
            rect = pymupdf.Rect((i % 3) * w, (i // 3) * h, (i % 3 + 1) * w, (i // 3 + 1) * h)
            page.show_pdf_page(rect, doc, number)
            page.insert_text((rect.x0 + 10, rect.y0 + 14), f"p{number + 1}", fontsize=12, color=(1, 0, 0))
        path = out / f"pages_{start // 6:02d}.png"
        page.get_pixmap(dpi=90).save(path)
        print(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("figures", type=Path, nargs="?")
    parser.add_argument("out", type=Path)
    parser.add_argument("--pdf", type=Path, help="sheet the rebuilt pages that hold an image")
    parser.add_argument("--pages", default="", help="with --pdf: comma-separated 1-based pages")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        page_sheets(args.pdf, args.out, args.pages)
        return
    figures = sorted(args.figures.glob("fig_*.png"), key=figure_order)
    per_sheet = COLS * ROWS
    for start in range(0, len(figures), per_sheet):
        doc = pymupdf.open()
        page = doc.new_page(width=COLS * CELL_W, height=ROWS * CELL_H)
        for i, fig in enumerate(figures[start : start + per_sheet]):
            x, y = (i % COLS) * CELL_W, (i // COLS) * CELL_H
            page.insert_image(
                pymupdf.Rect(x + 4, y + 14, x + CELL_W - 4, y + CELL_H - 4),
                filename=str(fig),
                keep_proportion=True,
            )
            page.insert_text((x + 4, y + 11), fig.stem, fontsize=10, color=(1, 0, 0))
            page.draw_rect(
                pymupdf.Rect(x + 2, y + 2, x + CELL_W - 2, y + CELL_H - 2),
                color=(0.6, 0.6, 0.6),
                width=0.5,
            )
        path = args.out / f"sheet_{start // per_sheet:02d}.png"
        page.get_pixmap(dpi=144).save(path)
        print(path)


if __name__ == "__main__":
    main()
