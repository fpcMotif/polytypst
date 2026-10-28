"""Search typeface settings for the 1970 Bourbaki rebuild by line-break agreement with the scan.

Usage: uv run python books/bourbaki/tools/linebreak_search.py [NAME=k=v,k=v ...]

Each candidate is a set of Typst inputs read by the vintage preamble (font,
size-scale, weight, tracking, word-spacing, linebreaks). For every source page it
compares the last word of each body line in the scan (the source OCR cache in
$POLYTYPST_BOOKS/bourbaki/source_ocr) with the last words of our lines on the matching output pages.
Agreement is the share of scan line endings that also end a line in ours.
Writes $POLYTYPST_BOOKS/bourbaki/linebreaks.json.
"""

import json
import re
import subprocess
import sys
from collections import Counter

import numpy as np
import pymupdf

from polytypst.book_state import book_state
from polytypst.books import module
from polytypst.compiler.typst_math import REPO_FONTS_DIR as FONTS
from polytypst.ocr.lines import LineStore
from polytypst.parity.source import read_source_page, source_ocr_dir, source_pdf

OUT_DIR = module("bourbaki", None).OUT_DIR
query_typ_marks = module("bourbaki", "marks").query_marks
BOURBAKI_1970_SPEC = module("bourbaki", "spec").BOURBAKI_1970_SPEC

ORIGINAL = source_pdf(BOURBAKI_1970_SPEC)
TYP = OUT_DIR / f"{BOURBAKI_1970_SPEC.slug}.typ"
OCR = source_ocr_dir(OUT_DIR)
WORK = OUT_DIR / "linebreak_search"
RESULTS = book_state(OUT_DIR) / "linebreaks.json"
BODY_TOP, BODY_BOTTOM = 60.0, 58.0
TARGETS = OUT_DIR / "page_targets.json"
BODY_HEIGHT = 609 - 74 - 66


def ending(text: str) -> str | None:
    words = re.findall(r"[A-Za-z]+", text)
    return words[-1].lower() if words and len(words[-1]) >= 3 else None


def query_marks(inputs: dict[str, str] | None = None) -> list[dict]:
    return query_typ_marks(TYP, inputs)


def scan_endings(page: int) -> Counter:
    src = read_source_page(OCR, page)
    out: Counter = Counter()
    for line in src.lines:
        top = src.top_pt(line)
        if BODY_TOP < top < src.height - BODY_BOTTOM and (e := ending(line.text)):
            out[e] += 1
    return out


def our_endings(doc: pymupdf.Document, pages: range) -> Counter:
    out: Counter = Counter()
    for p in pages:
        page = doc[p - 1]
        rows: dict[int, list[tuple[float, str]]] = {}
        for x0, y0, _, _, word, *_ in page.get_text("words"):
            if BODY_TOP < y0 < page.rect.height - BODY_BOTTOM:
                rows.setdefault(round(y0 / 3), []).append((x0, word))
        for words in rows.values():
            if e := ending(max(words)[1]):
                out[e] += 1
    return out


def height_offset(inputs: dict[str, str]) -> float:
    """Median of (our first-to-last line height - the scan's), vertical fill off, base leading."""
    marks = query_marks({**inputs, "fill": "0"})
    targets = json.loads(TARGETS.read_text())
    tops = {str(m["key"]): m for m in marks if m["kind"] == "top"}
    ends = {str(m["key"]): m for m in marks if m["kind"] == "end"}
    diffs = [
        (ends[k]["page"] - t["page"]) * BODY_HEIGHT + ends[k]["y"] - t["y"] - (targets[k]["last"] - targets[k]["top"])
        for k, t in tops.items()
        if k in ends and k in targets
    ]
    return round(float(np.median(diffs)), 1)


def evaluate(name: str, inputs: dict[str, str], scan: dict[int, Counter]) -> dict:
    WORK.mkdir(parents=True, exist_ok=True)
    pdf = WORK / f"{name}.pdf"
    flags = [arg for k, v in inputs.items() for arg in ("--input", f"{k}={v}")]
    subprocess.run(["typst", "compile", "--font-path", str(FONTS), *flags, str(TYP), str(pdf)], check=True, capture_output=True)
    marks = query_marks(inputs)
    tops = {int(m["key"]): m["page"] for m in marks if m["kind"] == "top"}
    ends = {int(m["key"]): m["page"] for m in marks if m["kind"] == "end"}
    doc = pymupdf.open(pdf)
    hit = total = 0
    for src, first in tops.items():
        if src not in scan:
            continue
        ours = our_endings(doc, range(first, ends.get(src, first) + 1))
        hit += sum((scan[src] & ours).values())
        total += sum(scan[src].values())
    overflow = sum(1 for k, v in tops.items() if ends.get(k, v) > v)
    result = {
        "name": name,
        "inputs": inputs,
        "agreement": round(hit / max(1, total), 4),
        "overflow_pages": overflow,
        "pages": doc.page_count,
        "height_minus_scan_pt": height_offset(inputs),
    }
    print(json.dumps(result), flush=True)
    return result


def parse(arg: str) -> tuple[str, dict[str, str]]:
    name, _, spec = arg.partition("=")
    return name, dict(kv.split("=", 1) for kv in spec.split(",") if kv)


DEFAULT_GRID = [
    "base=",
    "simple=linebreaks=simple",
    "track+.1=tracking=0.1",
    "track-.1=tracking=-0.1",
    "size1.02=size-scale=1.02",
    "size0.98=size-scale=0.98",
    "w400=weight=400",
    "w600=weight=600",
    "ws90=word-spacing=90",
    "ws115=word-spacing=115",
    "libre=font=Libre Baskerville",
    "libre0.92=font=Libre Baskerville,size-scale=0.92",
]


def main(args: list[str]) -> None:
    orig = pymupdf.open(ORIGINAL)
    store = LineStore(OCR)
    scan = {p: scan_endings(p) for p in range(31, orig.page_count + 1) if store.lines(p) is not None}
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else []
    for arg in args or DEFAULT_GRID:
        name, inputs = parse(arg)
        results = [r for r in results if r["name"] != name] + [evaluate(name, inputs, scan)]
        RESULTS.write_text(json.dumps(results, indent=1))
    for r in sorted(results, key=lambda r: -r["agreement"]):
        print(f"{r['agreement']:.3f}  overflow {r['overflow_pages']:3d}  height {r.get('height_minus_scan_pt', '?'):>6}pt  {r['name']}  {r['inputs']}")


if __name__ == "__main__":
    main(sys.argv[1:])
