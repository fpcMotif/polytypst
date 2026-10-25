"""List transcript lines whose text the scan prints inside a figure crop, so the book prints it twice.

Usage: mise exec -- uv run python scripts/figure_leaks.py KEY [--ratio 0.8]

A transcriber often copies a chart's legend, axis title or panel title ("（1）日本") into the
page text. The crop already shows that text, so the rebuilt page prints it under the figure as
well. Each printed line is `pPAGE fig ID LLINE (RATIO): TEXT`, where RATIO is how closely the
line matches an OCR line inside the figure box. Remove each true hit with a page fixup in the
book's spec, such as `71: ((r"(?m)^（[1-6]）(?:日本|美国)\\n*", ""),)`. A caption, table row or
display formula is never printed.
"""

import argparse
import difflib
import json
import re
from collections.abc import Iterable
from importlib import import_module
from typing import TYPE_CHECKING

from .ocr.lines import LineStore, OcrLine
from .vision.figure_extractor import load_figures_manifest

if TYPE_CHECKING:
    from .edition import Book

FIGURE_TEXT_LEAK = "FIGURE_TEXT_LEAK"
SKIP = re.compile(r"^(?:<|\||!\[|\$\$|(?:\*\*)?[图表]\s*\d)")


def norm(s: str) -> str:
    return re.sub(r"[\s$\\{}*#（）()，,。：:、]", "", s)


def apply_page_fixups(text: str, fixups: Iterable[tuple[str, str]]) -> str:
    for pattern, repl in fixups:
        text = re.sub(pattern, repl if re.search(r"\\[1-9]|\\g<", repl) else lambda _, r=repl: r, text, flags=re.DOTALL)
    return text


def page_leaks(
    text: str, crop_lines: Iterable[str], fixups: Iterable[tuple[str, str]] = (), ratio: float = 0.8
) -> list[tuple[int, float, str]]:
    """Each transcript line, after the page fixups, that matches a line inside the figure crop, as (line index, match ratio, text)."""
    inside = [n for line in crop_lines if len(n := norm(line)) >= 2]
    leaks = []
    for i, raw in enumerate(apply_page_fixups(text, fixups).splitlines()):
        line = raw.strip()
        n = norm(line)
        if not line or SKIP.match(line) or not 2 <= len(n) <= 60:
            continue
        best = max((difflib.SequenceMatcher(None, n, s).ratio() for s in inside), default=0)
        if best >= ratio:
            leaks.append((i, best, line))
    return leaks


def in_top_down_box(line: OcrLine, box: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = box
    bottom_up_center = line.y + line.h / 2
    return x0 <= line.x + line.w / 2 <= x1 and y0 <= 1 - bottom_up_center <= y1


def figure_text_leaks(book: "Book", ratio: float = 0.8) -> list[tuple[int, str, int, float, str]]:
    """Every leaked line of a book, once per page line, as (scan page, figure id, line index, ratio, text)."""
    manifest = book.out_dir / "figures_manifest.json"
    if not manifest.exists() or not isinstance(json.loads(manifest.read_text(encoding="utf-8")), list):
        return []
    ocr = LineStore(book.ocr)
    seen: set[tuple[int, int]] = set()
    leaks = []
    for fig in load_figures_manifest(manifest):
        md = book.transcripts / f"p_{fig.source_page:03d}.md"
        lines = ocr.lines(fig.source_page)
        if fig.box is None or lines is None or not md.exists():
            continue
        inside = [line.text for line in lines if in_top_down_box(line, fig.box)]
        fixups = book.spec.page_fixups.get(fig.source_page, ())
        for i, best, text in page_leaks(md.read_text(encoding="utf-8"), inside, fixups, ratio):
            if (fig.source_page, i) not in seen:
                seen.add((fig.source_page, i))
                leaks.append((fig.source_page, fig.figure_id, i, best, text))
    return leaks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("key", help="the folder name under src/, such as 6_劳动力市场与收入分配")
    parser.add_argument("--ratio", type=float, default=0.8, help="lowest match ratio printed (default 0.8)")
    args = parser.parse_args()
    book = import_module(f"polytypst.{args.key}.book").BOOK
    for page, figure_id, i, best, text in figure_text_leaks(book, args.ratio):
        print(f"p{page} fig {figure_id} L{i} ({best:.2f}): {text[:60]}")
