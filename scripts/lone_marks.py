"""List PDF lines whose only text is footnote marks, with the line above each.

Usage: uv run python scripts/lone_marks.py output/3_国际经济环境的变化与日本经济/3.pdf

A lone ① usually follows a heading or a chapter title: the scan put the note call on the
title line, and the compiler set the title itself and left the call behind. A finished
edition prints nothing. Fix each line as `docs/scanned-books.md` "Notes" says.
"""

import argparse
import re
from pathlib import Path

import pymupdf

MARKS_ONLY = re.compile(r"^[\s①-⑳\d*※]+$")
MARK = re.compile(r"[①-⑳]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    for n, page in enumerate(pymupdf.open(args.pdf), 1):
        lines = [
            "".join(span["text"] for span in line["spans"]).strip()
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
        ]
        lines = [text for text in lines if text]
        for i, text in enumerate(lines):
            if MARKS_ONLY.match(text) and MARK.search(text):
                above = lines[i - 1][:40] if i else ""
                print(f"p{n} {text!r} after {above!r}")


if __name__ == "__main__":
    main()
