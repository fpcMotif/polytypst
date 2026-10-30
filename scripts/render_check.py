"""Pair each table and figure of a rebuilt PDF with its scan page, and render both pages as PNG files, so that
an agent can compare the rendered table or figure with the scan.

Usage:
  uv run python scripts/render_check.py BOOK --pdf REBUILT.pdf --scan SCAN.pdf
  uv run python scripts/render_check.py BOOK --pdf REBUILT.pdf --scan SCAN.pdf --labels 表1-1,图2-3 --out DIR

  uv run python scripts/render_check.py BOOK --pdf REBUILT.pdf --scan SCAN.pdf --run [--size 6] [--jobs 8]

The first form prints one line per caption: the label, the rebuilt page and the scan page. The second also
writes DIR/LABEL_rebuilt.png and DIR/LABEL_scan.png at 110 dpi, each the caption page and the page after it. The third renders every pair and starts one
omp agent for each batch of labels; each batch writes DIR/rK.jsonl, and a batch whose file exists is skipped.
docs/render-check.md is the runbook.
"""

import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf

CAPTION = re.compile(r"^(附表|表|图)[\s ]*(\d+-\d+|[A-Z])(?:\s|$)")
CAPTION_MAX_CHARS = 80
SENTENCE = re.compile(r"。|^(附表|表|图)[\s ]*(?:\d+-\d+|[A-Z])\s*(显示|所示|表明|中|是|给出|列出|反映|的)")
DPI = 110


def caption_label(text: str) -> str | None:
    """The label of a caption line, such as 表1-1. A sentence that names a table is not a caption."""
    text = text.strip()
    if len(text) > CAPTION_MAX_CHARS or SENTENCE.search(text) or not (m := CAPTION.match(text)):
        return None
    return f"{m[1]}{m[2]}"


def rebuilt_pages(pdf: pymupdf.Document) -> dict[str, int]:
    pages: dict[str, int] = {}
    for number, page in enumerate(pdf, 1):
        for block in page.get_text("blocks"):
            if (label := caption_label(block[4])) and label not in pages:
                pages[label] = number
    return pages


def scan_pages(book: str) -> dict[str, int]:
    import page_check

    pages: dict[str, int] = {}
    for number in page_check.transcript_pages(book):
        for _, _, text in page_check.ocr_lines(book, number):
            if (label := caption_label(text)) and label not in pages:
                pages[label] = number
    return pages


def render(doc: pymupdf.Document, page: int, path: Path) -> None:
    """The caption page and the page after it, side by side, so that a table or a note that runs on is in view."""
    pages = [doc[n] for n in (page - 1, page) if n < len(doc)]
    width, height = sum(p.rect.width for p in pages), max(p.rect.height for p in pages)
    spread = pymupdf.open()
    sheet = spread.new_page(width=width, height=height)
    x = 0.0
    for p in pages:
        sheet.show_pdf_page(pymupdf.Rect(x, 0, x + p.rect.width, p.rect.height), doc, p.number)
        x += p.rect.width
    sheet.get_pixmap(matrix=pymupdf.Matrix(DPI / 72, DPI / 72)).save(path)


def check_batch(book: str, labels: list[str], out: Path, model: str) -> str:
    log = out.with_suffix(".log")
    prompt = f"Follow this runbook with BOOK={book} DIR={out.parent} ITEMS={','.join(labels)} OUT={out}."
    with log.open("w", encoding="utf-8") as stream:
        code = subprocess.run(
            ["omp", "-p", "--no-session", "--model", model, "@docs/render-check.md", prompt],
            stdout=stream, stderr=subprocess.STDOUT, timeout=3600, check=False,
        ).returncode
    lines = sum(1 for line in out.read_text(encoding="utf-8").splitlines() if line.strip()) if out.exists() else 0
    return f"{out.name}: exit {code}, {lines} of {len(labels)} items"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("book", help="a book number from 1 to 6, or a folder name under books/")
    parser.add_argument("--pdf", required=True, type=Path, help="the rebuilt PDF")
    parser.add_argument("--scan", required=True, type=Path, help="the scan PDF")
    parser.add_argument("--labels", default="", help="comma-separated labels to render, such as 表1-1,图2-3")
    parser.add_argument("--out", type=Path, help="the folder for the PNG files, by default output/render_check/BOOK")
    parser.add_argument("--run", action="store_true", help="render every pair and start the omp agents")
    parser.add_argument("--size", type=int, default=6, help="labels per agent")
    parser.add_argument("--jobs", type=int, default=8, help="omp agents at once")
    parser.add_argument("--model", default="gemini-3.8-flash")
    args = parser.parse_args()
    args.out = args.out or Path("output/render_check") / args.book

    rebuilt_doc, scan_doc = pymupdf.open(args.pdf), pymupdf.open(args.scan)
    rebuilt, scan = rebuilt_pages(rebuilt_doc), scan_pages(args.book)
    if args.run:
        paired = [label for label in rebuilt if label in scan]
        args.out.mkdir(parents=True, exist_ok=True)
        for label in paired:
            render(rebuilt_doc, rebuilt[label], args.out / f"{label}_rebuilt.png")
            render(scan_doc, scan[label], args.out / f"{label}_scan.png")
        batches = [(paired[i : i + args.size], args.out / f"r{i // args.size + 1}.jsonl") for i in range(0, len(paired), args.size)]
        todo = [(labels, out) for labels, out in batches if not out.exists()]
        print(f"{len(paired)} pairs, {len(todo)} of {len(batches)} batches to run, {args.jobs} at a time", flush=True)
        with ThreadPoolExecutor(args.jobs) as pool:
            for line in pool.map(lambda batch: check_batch(args.book, *batch, args.model), todo):
                print(line, flush=True)
        return
    wanted = [label for label in args.labels.split(",") if label]
    if not wanted:
        for label, page in rebuilt.items():
            print(f"{label}\trebuilt {page}\tscan {scan.get(label, '-')}")
        print(f"{len(rebuilt)} captions, {sum(label in scan for label in rebuilt)} found in the scan", file=sys.stderr)
        return
    args.out.mkdir(parents=True, exist_ok=True)
    for label in wanted:
        if label not in rebuilt or label not in scan:
            print(f"{label}: not in the {'rebuilt PDF' if label not in rebuilt else 'scan OCR'}", file=sys.stderr)
            continue
        render(rebuilt_doc, rebuilt[label], args.out / f"{label}_rebuilt.png")
        render(scan_doc, scan[label], args.out / f"{label}_scan.png")
        print(f"{label}\t{args.out / f'{label}_rebuilt.png'}\t{args.out / f'{label}_scan.png'}")


if __name__ == "__main__":
    main()
