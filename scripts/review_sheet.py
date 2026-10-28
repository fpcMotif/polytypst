"""Put page images side by side with titles, and box in red what changed between two of them.

Usage: uv run python scripts/review_sheet.py OUT.png --panel "Scan=page_renders/p_036.png" \
    --panel "Before=before.pdf#31" --panel "After=after.pdf#31" [--diff 1,2] [--title TEXT]

A panel is TITLE=PATH, where PATH is a PNG or JPEG, or PDF#PAGE for a 1-based PDF page.
Every panel is scaled to the height of the first one. --diff I,J compares panels I and J (0-based)
and draws the same boxes on both. --box I=L,T,R,B draws a box on panel I in shares of its size.
"""

import argparse
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont

RED = (220, 30, 30)
HEADER = 56
GAP = 24
CELL = 24


def load(spec: str, height: int | None) -> Image.Image:
    path, _, page = spec.partition("#")
    if page:
        doc = pymupdf.open(path)
        pix = doc[int(page) - 1].get_pixmap(dpi=200)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    else:
        with Image.open(path) as raw:
            img = raw.convert("RGB")
    if height is not None and img.height != height:
        img = img.resize(
            (round(img.width * height / img.height), height), Image.LANCZOS
        )
    return img


def diff_boxes(a: Image.Image, b: Image.Image) -> list[tuple[int, int, int, int]]:
    """Boxes around the CELL-pixel grid cells whose ink differs, joined where cells touch."""
    w, h = min(a.width, b.width), min(a.height, b.height)
    ink_a = np.asarray(a.convert("L").crop((0, 0, w, h))) < 160
    ink_b = np.asarray(b.convert("L").crop((0, 0, w, h))) < 160
    rows, cols = h // CELL, w // CELL
    changed = (ink_a ^ ink_b)[: rows * CELL, : cols * CELL].reshape(
        rows, CELL, cols, CELL
    ).sum(axis=(1, 3)) > 8
    seen = np.zeros_like(changed)
    boxes = []
    for r, c in zip(*np.nonzero(changed), strict=True):
        if seen[r, c]:
            continue
        stack, cells = [(r, c)], []
        seen[r, c] = True
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < rows
                        and 0 <= nx < cols
                        and changed[ny, nx]
                        and not seen[ny, nx]
                    ):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        ys, xs = zip(*cells, strict=True)
        boxes.append(
            (min(xs) * CELL, min(ys) * CELL, (max(xs) + 1) * CELL, (max(ys) + 1) * CELL)
        )
    return boxes


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

    titles, panels = [], []
    for spec in args.panel:
        title, _, path = spec.partition("=")
        titles.append(title)
        panels.append(load(path, panels[0].height if panels else None))
    boxes: dict[int, list[tuple[int, int, int, int]]] = {
        i: [] for i in range(len(panels))
    }
    if args.diff:
        i, j = (int(n) for n in args.diff.split(","))
        found = diff_boxes(panels[i], panels[j])
        boxes[i] += found
        boxes[j] += found
    for spec in args.box:
        i, _, rect = spec.partition("=")
        left, top, right, bottom = (float(v) for v in rect.split(","))
        p = panels[int(i)]
        boxes[int(i)].append(
            (
                round(left * p.width),
                round(top * p.height),
                round(right * p.width),
                round(bottom * p.height),
            )
        )

    top = HEADER * (2 if args.title else 1)
    sheet = Image.new(
        "RGB",
        (
            sum(p.width for p in panels) + GAP * (len(panels) + 1),
            panels[0].height + top + GAP,
        ),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=30)
    if args.title:
        draw.text((GAP, 12), args.title, fill="black", font=font)
    x = GAP
    for k, (title, panel) in enumerate(zip(titles, panels, strict=True)):
        sheet.paste(panel, (x, top))
        draw.rectangle(
            (x, top, x + panel.width - 1, top + panel.height - 1),
            outline=(160, 160, 160),
        )
        label = (
            f"{title}  ({len(boxes[k])} changed)"
            if args.diff and k in (int(n) for n in args.diff.split(","))
            else title
        )
        draw.text((x, top - HEADER + 12), label, fill="black", font=font)
        for left, t, right, bottom in boxes[k]:
            draw.rectangle(
                (x + left, top + t, x + right, top + bottom), outline=RED, width=4
            )
        x += panel.width + GAP
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
