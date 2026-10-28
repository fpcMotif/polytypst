"""`polytypst evidence`: proof for review findings.

zoom boxes a span on a scan page, placed from the local OCR line boxes; sweep runs only the page cleaner
over books and records the notes it cuts, so a shared cleaner change is measured on every book without a
rebuild; report renders chosen findings, with their evidence PNGs inlined, as one HTML page."""

import argparse
import base64
import html
import json
import re
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from unittest.mock import patch

import pymupdf
from PIL import Image, ImageDraw, ImageFont

from .book_state import book_state
from .compiler import page_cleaner
from .compiler.monograph import MonographCompiler, adhoc_spec
from .ocr.lines import LineStore, source_ocr_dir
from .ocr.pages import OcrLine
from .review import Finding, read_findings

ZOOM_DPI = 400
INSET = 3
RED = (200, 30, 30)
LABEL_FONTS = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
)
EVIDENCE_PNG = re.compile(r"[^\s;,]+\.png")


@dataclass(frozen=True)
class Box:
    """A region as fractions of the page, origin at the top left."""

    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True)
class NoteChange:
    book: str
    page: int
    direction: str
    key: str
    text: str


def _width(text: str) -> float:
    return sum(0.5 if unicodedata.east_asian_width(c) in "NaH" else 1.0 for c in text)


def span_box(line: OcrLine, span: str) -> Box:
    """The box of `span` inside an OCR line, measured in character widths (CJK 1, Latin 0.5)."""
    start = line.text.index(span)
    total = _width(line.text)
    left = line.x + line.w * _width(line.text[:start]) / total
    right = line.x + line.w * _width(line.text[: start + len(span)]) / total
    top = 1 - line.y - line.h
    return Box(left, top, right, top + line.h)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in LABEL_FONTS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def zoom(scan: Path, ocr: Path, page: int, span: str, label: str, out: Path) -> Path:
    """Write the scan line holding `span` with the span boxed in red, a label, and a magnified inset."""
    lines = LineStore(ocr).lines(page) or ()
    line = next((ln for ln in lines if span in ln.text), None)
    if line is None:
        raise ValueError(
            f"no OCR line of page {page} in {ocr} holds {span!r}; copy the span as the OCR read it"
        )
    box = span_box(line, span)
    pix = pymupdf.open(scan)[page - 1].get_pixmap(dpi=ZOOM_DPI)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    w, h = image.size
    pad = (box.bottom - box.top) * h * 0.25
    strip = image.crop(
        (
            int(0.06 * w),
            int(box.top * h - pad),
            int(0.96 * w),
            int(box.bottom * h + pad),
        )
    )
    margin = 0.4 * (box.bottom - box.top) * h
    frame = (
        int(box.left * w - 0.06 * w - margin),
        0,
        int(box.right * w - 0.06 * w + margin),
        strip.height - 1,
    )
    inset = strip.crop(frame)
    inset = inset.resize(
        (inset.width * INSET, inset.height * INSET), Image.Resampling.LANCZOS
    )
    ImageDraw.Draw(strip).rectangle(frame, outline=RED, width=6)
    sheet = Image.new(
        "RGB",
        (max(strip.width, inset.width + 40), strip.height + inset.height + 120),
        "white",
    )
    sheet.paste(strip, (0, 0))
    draw = ImageDraw.Draw(sheet)
    draw.text((20, strip.height + 20), label, fill=RED, font=_font(44))
    sheet.paste(inset, (20, strip.height + 90))
    draw.rectangle(
        (20, strip.height + 90, 20 + inset.width, strip.height + 90 + inset.height),
        outline=RED,
        width=6,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def sweep(
    folders: list[Path], style: str = "circled"
) -> dict[str, dict[str, list[list[str]]]]:
    """For each book folder, the notes the page cleaner cuts from each page of its transcript store."""
    found: dict[str, dict[str, list[list[str]]]] = {}
    split = page_cleaner.split_page_footnotes
    cut: list[tuple[str, str]] = []

    def recording(
        md: str, style: str, folio_pattern: str
    ) -> tuple[str, list[tuple[str, str]]]:
        body, notes = split(md, style, folio_pattern)
        cut.extend(notes)
        return body, notes

    with patch.object(page_cleaner, "split_page_footnotes", side_effect=recording):
        for folder in folders:
            pages = sorted(book_state(folder).glob("markdown_pages/p_*.md"))
            spec = adhoc_spec(
                Path(f"{folder.name}.pdf"), len(pages), lang="zh", domain="economics"
            )
            cleaner = MonographCompiler(replace(spec, footnote_style=style)).cleaner
            book = found.setdefault(folder.name, {})
            for path in pages:
                cut.clear()
                number = int(path.stem.removeprefix("p_"))
                cleaner.clean(path.read_text(encoding="utf-8"), number)
                if cut:
                    book[str(number)] = [list(note) for note in cut]
    return found


def note_changes(before: dict, after: dict) -> list[NoteChange]:
    """Each note cut in one sweep and not the other, by book and page."""
    changes: list[NoteChange] = []
    for book in dict.fromkeys([*before, *after]):
        old, new = before.get(book, {}), after.get(book, {})
        for page in sorted({*old, *new}, key=int):
            was, now = old.get(page, []), new.get(page, [])
            changes += [
                NoteChange(book, int(page), "note->body", k, t)
                for k, t in was
                if [k, t] not in now
            ]
            changes += [
                NoteChange(book, int(page), "body->note", k, t)
                for k, t in now
                if [k, t] not in was
            ]
    return changes


def _inline_png(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def report(findings: list[Finding], title: str, root: Path) -> str:
    """One self-contained HTML page: a card per finding, with each PNG its evidence names inlined."""
    cards = []
    for f in findings:
        shots = [root / m for m in EVIDENCE_PNG.findall(f.evidence)]
        images = "".join(
            f'<img src="{_inline_png(p)}" alt="{html.escape(p.name)}">'
            for p in shots
            if p.is_file()
        )
        cards.append(
            f'<section class="card {html.escape(f.status)}"><header><span class="id">{html.escape(f.id)}</span>'
            f"<b>{html.escape(f.severity)} · {html.escape(f.format)} · {html.escape(f.status)}</b>"
            f"<span>{html.escape(f.book)}</span></header>{images}<dl>"
            f"<dt>Where</dt><dd><code>{html.escape(f.where)}</code></dd>"
            f"<dt>What</dt><dd>{html.escape(f.what)}</dd>"
            f"<dt>Evidence</dt><dd>{html.escape(f.evidence)}</dd></dl></section>"
        )
    return REPORT_PAGE.format(
        title=html.escape(title), count=len(findings), cards="\n".join(cards)
    )


REPORT_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#fbfaf7;--card:#fff;--ink:#1d1d1b;--mute:#6b6a65;--line:#e4e1d9;--bad:#c0392b;--badbg:#fdecea;--good:#1e7a46;--goodbg:#e7f5ec}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--mute:#a09e97;--line:#34332f;--bad:#ff7b6b;--badbg:#3a1d19;--good:#5fd38d;--goodbg:#17301f}}}}
:root[data-theme="dark"]{{--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--mute:#a09e97;--line:#34332f;--bad:#ff7b6b;--badbg:#3a1d19;--good:#5fd38d;--goodbg:#17301f}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,"PingFang SC",sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:28px 16px 60px}}
h1{{font-size:22px;margin:0 0 4px}} p.lead{{color:var(--mute);margin:0 0 16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin-top:16px;overflow:hidden}}
.card header{{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;padding:10px 14px;border-bottom:1px solid var(--line)}}
.card header span:last-child{{color:var(--mute);font-size:13px}}
.id{{font:600 12px ui-monospace,Menlo,monospace;background:var(--badbg);color:var(--bad);padding:1px 8px;border-radius:99px}}
.card.fixed .id{{background:var(--goodbg);color:var(--good)}}
.card img{{display:block;width:100%;background:#fff;border-bottom:1px solid var(--line)}}
dl{{display:grid;grid-template-columns:100px 1fr;margin:0}} dt,dd{{margin:0;padding:8px 14px;border-bottom:1px solid var(--line)}}
dt{{color:var(--mute);font-size:13px}} code{{font:13px ui-monospace,Menlo,monospace}}
@media (max-width:640px){{dl{{grid-template-columns:1fr}} dt{{border-bottom:0;padding-bottom:0}}}}
</style></head><body><main><h1>{title}</h1><p class="lead">{count} findings</p>
{cards}
</main></body></html>
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="polytypst evidence", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    z = commands.add_parser(
        "zoom", help="box a span on a scan page and write a PNG with a magnified inset"
    )
    z.add_argument(
        "folder",
        type=Path,
        help="output folder; its book state's source_ocr/ holds the scan's OCR lines",
    )
    z.add_argument("--scan", type=Path, required=True)
    z.add_argument("--page", type=int, required=True, help="1-based scan page")
    z.add_argument(
        "--span",
        required=True,
        help="the span exactly as the local OCR read it, such as 而是pO",
    )
    z.add_argument("--label", required=True, help="one line printed under the strip")
    z.add_argument("--out", type=Path, required=True)
    s = commands.add_parser(
        "sweep",
        help="record the notes the page cleaner cuts from every transcript page",
    )
    s.add_argument(
        "folders",
        type=Path,
        nargs="+",
        help="book output folders; each book state's markdown_pages/ is swept",
    )
    s.add_argument(
        "--style", default="circled", help="footnote style the cleaner assumes"
    )
    s.add_argument(
        "--out",
        type=Path,
        required=True,
        help="JSON file: {book: {page: [[mark, note], ...]}}",
    )
    d = commands.add_parser(
        "diff", help="list each note that moved between note and body across two sweeps"
    )
    d.add_argument("before", type=Path)
    d.add_argument("after", type=Path)
    r = commands.add_parser(
        "report",
        help="render chosen findings with their evidence PNGs as one HTML page",
    )
    r.add_argument("findings", type=Path)
    r.add_argument(
        "--ids", required=True, help="comma-separated finding ids, such as B2-39,B2-40"
    )
    r.add_argument("--title", default="Review evidence")
    r.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="folder that evidence PNG paths are relative to",
    )
    r.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "zoom":
        try:
            print(
                zoom(
                    args.scan,
                    source_ocr_dir(args.folder),
                    args.page,
                    args.span,
                    args.label,
                    args.out,
                )
            )
        except ValueError as error:
            print(error)
            return 1
    elif args.command == "sweep":
        found = sweep(args.folders, args.style)
        args.out.write_text(
            json.dumps(found, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(
            ", ".join(
                f"{book}: {len(pages)} pages with notes"
                for book, pages in found.items()
            )
            + f"; {args.out}"
        )
    elif args.command == "diff":
        before, after = (
            json.loads(p.read_text(encoding="utf-8")) for p in (args.before, args.after)
        )
        changes = note_changes(before, after)
        for book in dict.fromkeys([*before, *after]):
            mine = [c for c in changes if c.book == book]
            print(f"== {book}: {len({c.page for c in mine})} pages changed")
            for c in mine:
                print(f"  p{c.page} {c.direction} {c.key} {c.text[:70]}")
    else:
        wanted = args.ids.split(",")
        chosen = [f for f in read_findings(args.findings) if f.id in wanted]
        missing = sorted(set(wanted) - {f.id for f in chosen})
        if missing:
            print(f"no finding with id {', '.join(missing)} in {args.findings}")
            return 1
        args.out.write_text(
            report(
                sorted(chosen, key=lambda f: wanted.index(f.id)), args.title, args.root
            ),
            encoding="utf-8",
        )
        print(f"{len(chosen)} findings: {args.out}")
    return 0
