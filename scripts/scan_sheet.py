"""Build an HTML sheet of scan strips: each card cuts one line out of the scan PDF at 300 dpi and labels
what it prints.

Usage:
  uv run python scripts/scan_sheet.py BOOK --scan SCAN.pdf --cases CASES.jsonl > SHEET.html
  uv run python scripts/scan_sheet.py BOOK --scan SCAN.pdf --verdicts scan_typo > SHEET.html

Each line of CASES.jsonl is one card:
  {"page": 74, "find": "节纪", "scan": "20 节纪", "meant": "20 世纪", "note": "Wrong character"}
  {"page": 12, "find": "必不可免", "scan": "必不可免", "transcript": "必不可少"}
  {"page": 33, "band": [0.41, 0.45], "scan": "0, 1", "meant": "0.1"}

`find` names text of the line in the local OCR, which gives the strip's band. `band` gives it directly,
as the top and the bottom in shares of the page height. A card with `meant` shows a scan typo, and a
card with `transcript` shows a transcript error. `--verdicts KIND` reads the cards from
output/page_check/BOOK/verdicts.jsonl, for KIND scan_typo or real.
"""

import argparse
import base64
import html
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pymupdf

STRIP_PAD = 0.008
STYLE = """:root{--bg:#fff;--fg:#1d1d1f;--mut:#666;--card:#f6f6f4;--mark:#ffe08a;--ok:#1a7f37}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#151515;--fg:#eee;--mut:#aaa;--card:#222;--mark:#7a5c00;--ok:#5fd27a}}
:root[data-theme="dark"]{--bg:#151515;--fg:#eee;--mut:#aaa;--card:#222;--mark:#7a5c00;--ok:#5fd27a}
body{background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,"PingFang SC",sans-serif;max-width:980px;margin:0 auto;padding:16px}
p{color:var(--mut)} figure{background:var(--card);border-radius:8px;margin:0 0 14px;padding:10px 12px}
img{width:100%;height:auto;display:block;margin-top:8px;background:#fff;border-radius:4px}
mark{background:var(--mark);color:inherit;padding:0 3px} .ok{color:var(--ok);font-weight:600} small{color:var(--mut)}"""


@dataclass(frozen=True)
class Case:
    page: int
    scan: str
    find: str = ""
    band: tuple[float, float] | None = None
    meant: str = ""
    transcript: str = ""
    note: str = ""


def cases_from_jsonl(text: str) -> list[Case]:
    cases = []
    for line in filter(str.strip, text.splitlines()):
        record = json.loads(line)
        if "band" in record:
            record["band"] = tuple(record["band"])
        cases.append(Case(**record))
    return cases


def cases_from_verdicts(text: str, verdict: str) -> list[Case]:
    """A scan_typo record holds the printed text in `transcript` and the meant text in `scan`. A real record holds
    the scan's text in `scan`."""
    records = [json.loads(line) for line in filter(str.strip, text.splitlines())]
    chosen = [r for r in records if r["verdict"] == verdict]
    if verdict == "scan_typo":
        return [Case(page=r["page"], find=r["transcript"], scan=r["transcript"], meant=r["scan"], note=r["detail"]) for r in chosen]
    return [Case(page=r["page"], find=r["scan"], scan=r["scan"], transcript=r["transcript"], note=r["detail"]) for r in chosen]


def card(case: Case, png: bytes) -> str:
    e = html.escape
    if case.meant:
        label = f'scan prints <mark>{e(case.scan)}</mark> · meant <span class="ok">{e(case.meant)}</span>'
    else:
        label = f'transcript has <mark>{e(case.transcript)}</mark> · scan prints <span class="ok">{e(case.scan)}</span>'
    note = f"<br><small>{e(case.note)}</small>" if case.note else ""
    src = base64.b64encode(png).decode()
    return (
        f"<figure><figcaption><b>p{case.page}</b> · {label}{note}</figcaption>"
        f'<img src="data:image/png;base64,{src}" alt="scan p{case.page}"></figure>'
    )


def page_html(title: str, intro: str, cards: list[str]) -> str:
    return (
        '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>\n{STYLE}\n</style></head><body>\n"
        f"<h1>{html.escape(title)}</h1>\n<p>{html.escape(intro)}</p>\n{''.join(cards)}\n</body></html>\n"
    )


def find_band(book: str, case: Case) -> tuple[float, float] | None:
    import page_check

    if case.band:
        return case.band
    key = page_check.norm(case.find)
    return next(((top, bottom) for top, bottom, text in page_check.ocr_lines(book, case.page) if key in page_check.norm(text)), None)


def strip_png(doc: pymupdf.Document, page: int, band: tuple[float, float], dpi: int) -> bytes:
    rect = doc[page - 1].rect
    top, bottom = max(0.0, band[0] - STRIP_PAD), min(1.0, band[1] + STRIP_PAD)
    clip = pymupdf.Rect(rect.x0, rect.y0 + top * rect.height, rect.x1, rect.y0 + bottom * rect.height)
    return doc[page - 1].get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72), clip=clip).tobytes("png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("book", help="a book number from 1 to 6, or a folder name under books/")
    parser.add_argument("--scan", required=True, type=Path, help="the scan PDF")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--cases", type=Path, help="a JSONL file with one card per line")
    source.add_argument("--verdicts", choices=["scan_typo", "real"], help="read the cards from the page check's verdicts.jsonl")
    parser.add_argument("--title", default="", help="the page title")
    parser.add_argument("--intro", default="Each strip is cut straight from the scan PDF.", help="the line under the title")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    if args.cases:
        cases = cases_from_jsonl(args.cases.read_text(encoding="utf-8"))
    else:
        verdicts = Path("output/page_check") / args.book / "verdicts.jsonl"
        cases = cases_from_verdicts(verdicts.read_text(encoding="utf-8"), args.verdicts)
    doc = pymupdf.open(args.scan)
    cards = []
    for case in cases:
        band = find_band(args.book, case)
        if band is None:
            print(f"p{case.page}: no OCR line holds {case.find!r}; give the case a band", file=sys.stderr)
            continue
        cards.append(card(case, strip_png(doc, case.page, band, args.dpi)))
    title = args.title or f"Book {args.book}: {args.verdicts or 'scan'} strips"
    sys.stdout.write(page_html(title, args.intro, cards))
    print(f"{len(cards)} of {len(cases)} cards", file=sys.stderr)


if __name__ == "__main__":
    main()
