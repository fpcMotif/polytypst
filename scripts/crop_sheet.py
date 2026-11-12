"""Crop regions from PDF pages or images and pack them, labelled, into sheets an agent reads in one look.

Usage: uv run python scripts/crop_sheet.py OUT.png STRIP [STRIP ...] [--spec FILE] [--across PDF]... [--cols 1]
    [--frame] [--dpi N] [--max-dpi 400] [--max 1568] [--kb N] [--pad 0.05,1]

A strip is one row: LABEL=PANEL, or LABEL || LABEL=PANEL || PANEL for panels side by side at one height.
A panel is one of
    SOURCE#PAGE@REGION   REGION of 1-based PAGE of a PDF; SOURCE alone is an SVG or image file, or page 1
    SOURCE@~TEXT         the first page of SOURCE that holds TEXT
    typst:TEXT           TEXT set by Typst, to hold a candidate reading beside the scan
    ~TEXT                with --across: one panel for each --across PDF, at the line that holds TEXT
REGION is L,T,R,B in shares of the page, such as 0.05,0.4,0.95,0.6, or ~TEXT for the line that holds TEXT
in the text layer, widened by --pad (shares: up and down, then left and right). No REGION is the whole page.

To check a rebuilt figure, table or formula against its scan, name the three PDFs once and one caption per strip:
    crop_sheet.py out.png --across SCAN.pdf --across TYPST.pdf --across LATEX.pdf --pad 0.25,1 "Fig 3.2=~Figure 3.2"

Each row fills the sheet width, so a narrow box zooms in, up to --max-dpi; raise it to read one glyph.
A ruler at each panel's left edge gives page shares for a tighter box. --cols N puts N strips on a row.
--frame draws a coloured frame round each panel; the colour changes when a row comes from another page.
A new sheet starts when the next row would pass --max pixels: OUT.png, or OUT-1.png, OUT-2.png.
The script prints each sheet's path and size, then each panel whose TEXT was not found.
A scan with no text layer has no TEXT to find: give a box, or use `polytypst page-check` for its OCR lines.
"""

import argparse
import tempfile
from pathlib import Path

from PIL import Image

from polytypst.compare_sheet import (
    MAX_DPI,
    SHEET_LIMIT,
    Box,
    Panel,
    find_text,
    text_pdf,
    write_sheets,
)

FULL: Box = (0.0, 0.0, 1.0, 1.0)


def panels(label: str, spec: str, across: list[Path], pad: tuple[float, float], tmp: Path) -> list[Panel] | None:
    if spec.startswith("typst:"):
        return [Panel(label, text_pdf(spec[6:], tmp / f"text{len(list(tmp.glob('*.pdf')))}.pdf"), 1)]
    if spec.startswith("~"):
        found = [(pdf, find_text(pdf, spec[1:], pad=pad)) for pdf in across]
        if not found or any(hit is None for _, hit in found):
            return None
        return [Panel(f"{label} p{hit[0]} {pdf.stem}", pdf, hit[0], hit[1]) for pdf, hit in found]
    source, _, region = spec.partition("@")
    path, _, number = source.partition("#")
    page = int(number) if number else None
    if region.startswith("~"):
        hit = find_text(Path(path), region[1:], page, pad)
        return None if hit is None else [Panel(f"{label} p{hit[0]}", Path(path), hit[0], hit[1])]
    shares = tuple(float(v) for v in region.split(",")) if region else FULL
    return [Panel(label, Path(path), page or 1, shares)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    parser.add_argument("strips", nargs="*")
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--across", type=Path, action="append", default=[])
    parser.add_argument("--cols", type=int, default=1)
    parser.add_argument("--frame", action="store_true")
    parser.add_argument("--dpi", type=float)
    parser.add_argument("--max-dpi", type=int, default=MAX_DPI)
    parser.add_argument("--max", type=int, default=SHEET_LIMIT, dest="limit")
    parser.add_argument("--kb", type=int)
    parser.add_argument("--pad", default="0.05,1")
    args = parser.parse_args()

    pad_y, pad_x = (float(v) for v in args.pad.split(","))
    specs = [*args.strips, *(args.spec.read_text(encoding="utf-8").splitlines() if args.spec else [])]
    with tempfile.TemporaryDirectory() as tmp:
        strips, missing = [], []
        for spec in filter(None, specs):
            label, _, body = spec.partition("=")
            row: list[Panel] = []
            names = [name.strip() for name in label.split("||")]
            for n, part in enumerate(body.split("||")):
                name = names[n] if n < len(names) else Path(part.partition("@")[0].partition("#")[0].strip()).stem[:40]
                made = panels(name, part.strip(), args.across, (pad_y, pad_x), Path(tmp))
                if made is None:
                    missing.append(f"{label}: {part.strip()}")
                else:
                    row += made
            if row:
                strips.append(row)
        if not strips:
            parser.error("no strip gave a panel")
        rows = [[p for strip in strips[n : n + args.cols] for p in strip] for n in range(0, len(strips), args.cols)]
        outs = write_sheets(rows, args.out, args.dpi, limit=args.limit, max_dpi=args.max_dpi, kb=args.kb, frame=args.frame)
    for out in outs:
        with Image.open(out) as sheet:
            print(f"{out} {sheet.width}x{sheet.height} {out.stat().st_size // 1024}KB")
    for item in missing:
        print(f"NOT FOUND: {item}")


if __name__ == "__main__":
    main()
