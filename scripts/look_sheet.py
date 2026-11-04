"""Make two contact sheets of six sample pages from a rebuilt book, for a visual review of its typesetting.

Usage: uv run python scripts/look_sheet.py KEY OUT_DIR

The pages are a chapter opening, the page with the most math, a table, a figure, a prose page and
the index. A page that the book lacks is left out. The sheets are OUT_DIR/KEY-look-1.png and -2.png.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from polytypst.books import books
from polytypst.checker import AuditSpec

INDEX_RE = re.compile(r"^(?:index|索引|さくいん)", re.IGNORECASE)


def math_chars(page: pymupdf.Page) -> int:
    spans = [s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"]]
    return sum(len(s["text"]) for s in spans if "Math" in s["font"])


def rule_lines(page: pymupdf.Page) -> int:
    width = page.rect.width
    return sum(
        1
        for d in page.get_drawings()
        for item in d["items"]
        if item[0] == "l" and abs(item[1].y - item[2].y) < 0.5 and abs(item[2].x - item[1].x) > 0.3 * width
    )


def figure_area(page: pymupdf.Page) -> float:
    images = [pymupdf.Rect(info["bbox"]).get_area() for info in page.get_image_info()]
    drawings = [r.get_area() for r in page.cluster_drawings() if r.width > 60 and r.height > 60]
    return max([*images, *drawings], default=0.0)


def sample_pages(doc: pymupdf.Document, front: int) -> list[tuple[str, int]]:
    body = range(front, len(doc))
    chapters = [p - 1 for level, _, p, *_ in doc.get_toc(simple=False) if level == 1 and p - 1 >= front]
    index = [p - 1 for _, title, p, *_ in doc.get_toc(simple=False) if INDEX_RE.match(title.strip())]
    maths = {p: math_chars(doc[p]) for p in body}
    picks = [
        ("Chapter opening", chapters[1] if len(chapters) > 1 else chapters[0] if chapters else None),
        ("Most math", max(maths, key=maths.get, default=None)),
        ("Table", max(body, key=lambda p: rule_lines(doc[p]), default=None)),
        ("Figure", max(body, key=lambda p: figure_area(doc[p]), default=None)),
        ("Prose", max(range(len(doc) // 3, 2 * len(doc) // 3), key=lambda p: len(doc[p].get_text()) - 20 * maths.get(p, 0), default=None)),
        ("Index", index[-1] if index else None),
    ]
    found = [(name, p) for name, p in picks if p is not None]
    has_table = rule_lines(doc[dict(found).get("Table", 0)]) >= 3
    has_figure = figure_area(doc[dict(found).get("Figure", 0)]) > 0
    return [(n, p) for n, p in found if (n != "Table" or has_table) and (n != "Figure" or has_figure)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("key")
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()
    edition = next(iter(books()[args.key].editions.values()))
    doc = pymupdf.open(edition.rebuilt)
    picks = sample_pages(doc, AuditSpec.from_monograph(edition.spec).front_matter_pages)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for n, start in enumerate(range(0, len(picks), 3), 1):
        panels = [arg for name, p in picks[start : start + 3] for arg in ("--panel", f"{name} p{p + 1}={edition.rebuilt}#{p + 1}")]
        out = args.out_dir / f"{args.key}-look-{n}.png"
        subprocess.run([sys.executable, str(REPO / "scripts" / "review_sheet.py"), str(out), *panels, "--title", args.key], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
