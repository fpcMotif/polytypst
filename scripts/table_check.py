"""Measure table squeezes in rebuilt PDFs, and render a spread sample of table pages for a visual check.

Usage:
  uv run python scripts/table_check.py measure PDF [PDF ...]
  uv run python scripts/table_check.py sample OUT_DIR --per-book 17 PDF [PDF ...]

measure prints, for each PDF, the pages where two numbers on one line sit closer than 1pt (cells run
together), and the pages where four or more lines in a row hold one CJK character (a column squeezed to one
character per line). Figure axis labels also trigger the second check, so read those pages before you count
them. A page range such as 125-169 does not count, because the ASCII hyphen is not a minus sign.

sample finds the table pages of each PDF (eight or more lines with three or more numbers each), picks
--per-book of them spread evenly through the book, and renders each to OUT_DIR/b{n}p{page}.png at 110 dpi,
where n is the PDF's position on the command line, counting from 1.
"""

import argparse
import itertools
import re
from pathlib import Path

import pymupdf

NUMBER = re.compile(r"−?\d[\d,]*(?:\.\d+)?%?")
TABLE_NUMBER = re.compile(r"^[−\-]?\d[\d,]*(?:\.\d+)?\**%?$")


def touching_pairs(page: pymupdf.Page) -> int:
    rows: dict[int, list] = {}
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                for c in span["chars"]:
                    rows.setdefault(round(c["bbox"][3]), []).append(c)
    count = 0
    for chars in rows.values():
        chars.sort(key=lambda c: c["bbox"][0])
        text = "".join(c["c"] for c in chars)
        spans = [(m.start(), m.end()) for m in NUMBER.finditer(text) if m.end() - m.start() >= 2]
        for (_, end), (start, _) in itertools.pairwise(spans):
            if not text[end:start].strip("   ") and chars[start]["bbox"][0] - chars[end - 1]["bbox"][2] < 1:
                count += 1
    return count


def stacked_characters(page: pymupdf.Page) -> bool:
    run = 0
    for line in page.get_text().splitlines():
        line = line.strip()
        run = run + 1 if len(line) == 1 and "一" <= line <= "鿿" else 0
        if run >= 4:
            return True
    return False


def table_pages(doc: pymupdf.Document) -> list[int]:
    pages = []
    for page in doc:
        rows: dict[int, int] = {}
        for word in page.get_text("words"):
            if TABLE_NUMBER.match(word[4]):
                rows[round(word[3])] = rows.get(round(word[3]), 0) + 1
        if sum(n >= 3 for n in rows.values()) >= 8:
            pages.append(page.number)
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("measure").add_argument("pdfs", nargs="+", type=Path)
    sample = commands.add_parser("sample")
    sample.add_argument("out", type=Path)
    sample.add_argument("--per-book", type=int, default=17)
    sample.add_argument("pdfs", nargs="+", type=Path)
    args = parser.parse_args()

    for n, path in enumerate(args.pdfs, 1):
        doc = pymupdf.open(path)
        if args.command == "measure":
            touching = [(p.number + 1, k) for p in doc if (k := touching_pairs(p))]
            stacked = [p.number + 1 for p in doc if stacked_characters(p)]
            print(f"{path}: touching pages {len(touching)} {touching} | stacked pages {len(stacked)} {stacked}")
            continue
        args.out.mkdir(parents=True, exist_ok=True)
        pages = table_pages(doc)
        step = max(1, len(pages) / args.per_book)
        chosen = sorted({pages[int(i * step)] for i in range(min(args.per_book, len(pages)))})
        for p in chosen:
            doc[p].get_pixmap(dpi=110).save(args.out / f"b{n}p{p + 1}.png")
        print(f"b{n} {path}: {len(pages)} table pages; rendered {[p + 1 for p in chosen]}")


if __name__ == "__main__":
    main()
