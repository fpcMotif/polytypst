"""Put page images side by side with titles, and box in red what changed between two of them.

Usage: uv run python scripts/review_sheet.py OUT.png --panel "Scan=page_renders/p_036.png" \
    --panel "Before=before.pdf#31" --panel "After=after.pdf#31" [--diff 1,2] [--title TEXT]

A panel is TITLE=PATH, where PATH is a PNG or JPEG, or PDF#PAGE for a 1-based PDF page.
Every panel is scaled to the height of the first one. --diff I,J compares panels I and J (0-based)
and draws the same boxes on both. --box I=L,T,R,B draws a box on panel I in shares of its size.
"""

import argparse
from dataclasses import replace
from pathlib import Path

from polytypst.compare_sheet import Panel, diff_marks, write_sheet


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("out", type=Path)
    parser.add_argument("--panel", action="append", required=True)
    parser.add_argument("--diff")
    parser.add_argument("--box", action="append", default=[])
    parser.add_argument("--title", default="")
    args = parser.parse_args()

    panels = []
    for spec in args.panel:
        title, _, source = spec.partition("=")
        path, _, page = source.partition("#")
        panels.append(Panel(title, Path(path), int(page or 1)))
    if args.diff:
        i, j = (int(n) for n in args.diff.split(","))
        marks_i, marks_j = diff_marks(panels[i], panels[j])
        for k, marks in ((i, marks_i), (j, marks_j)):
            panels[k] = replace(panels[k], label=f"{panels[k].label}  ({len(marks)} changed)", marks=tuple(marks))
    for spec in args.box:
        k, _, rect = spec.partition("=")
        box = tuple(float(v) for v in rect.split(","))
        panels[int(k)] = replace(panels[int(k)], marks=(*panels[int(k)].marks, box))
    if args.title:
        panels[0] = replace(panels[0], label=f"{args.title}: {panels[0].label}")
    print(write_sheet([panels], args.out))


if __name__ == "__main__":
    main()
