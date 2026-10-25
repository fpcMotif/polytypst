"""Print the 1-based pages of a PDF whose text contains each search text.

Usage: uv run python scripts/find_pages.py output/4_不良债权与金融危机/4.pdf "图 9-22" "倒闭”包括"

Line breaks inside a page are removed before the search, so a text that wraps still matches.
Use the pages with scripts/review_sheet.py PDF#PAGE panels.
"""

import argparse
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("texts", nargs="+")
    args = parser.parse_args()
    pages = [page.get_text().replace("\n", "") for page in pymupdf.open(args.pdf)]
    for text in args.texts:
        print(text, [n for n, page in enumerate(pages, 1) if text in page])


if __name__ == "__main__":
    main()
