import base64
import html
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import Band, PageCheck
from .results import Verdict, issue_key

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
    band: Band | None = None
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


def cases_from_verdicts(verdicts: list[Verdict], verdict: str) -> list[Case]:
    """A scan_typo record holds the printed text in `transcript` and the meant text in `scan`. A real record holds
    the scan's text in `scan`."""
    chosen = [r for r in verdicts if r["verdict"] == verdict]
    if verdict == "scan_typo":
        return [Case(page=int(r["page"] or 0), find=r["transcript"], scan=r["transcript"], meant=r.get("scan", ""), note=r["detail"]) for r in chosen]
    return [Case(page=int(r["page"] or 0), find=r.get("scan", ""), scan=r.get("scan", ""), transcript=r["transcript"], note=r["detail"]) for r in chosen]


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


def scan_sheet(check: PageCheck, cases: list[Case], title: str, intro: str, dpi: int) -> tuple[str, list[Case]]:
    cards, missed = [], []
    for case in cases:
        band = case.band or check.band(case.page, case.find)
        if band is None:
            missed.append(case)
            continue
        cards.append(card(case, check.strip(case.page, band, dpi)))
    return page_html(title, intro, cards), missed


def contact_sheet(
    cards: list[tuple[str, Path]], out: Path, width: int = 1200, max_crop_h: int = 260
) -> Path:
    header_h, pad = 28, 6
    font = ImageFont.load_default(size=14)
    loaded: list[tuple[str, Image.Image]] = []
    for label, img_path in cards:
        with Image.open(img_path) as raw:
            img = raw.convert("RGB")
        if img.width > width - 2 * pad:
            scale = (width - 2 * pad) / img.width
            img = img.resize(
                (width - 2 * pad, max(1, round(img.height * scale))), Image.Resampling.LANCZOS
            )
        if img.height > max_crop_h:
            img = img.crop((0, 0, img.width, max_crop_h))
        loaded.append((label, img))
    total_h = sum(header_h + img.height + pad for _, img in loaded) + pad
    canvas = Image.new("RGB", (width, max(1, total_h)), (245, 245, 245))
    draw = ImageDraw.Draw(canvas)
    y = pad
    for label, img in loaded:
        draw.rectangle([pad, y, width - pad, y + header_h - 2], fill=(35, 40, 50))
        draw.text((pad + 6, y + 6), label[:140], fill=(255, 255, 255), font=font)
        y += header_h
        canvas.paste(img, (pad, y))
        y += img.height + pad
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def sheets(check: PageCheck, size: int = 30) -> list[Path]:
    results = check.results
    done = results.verdict_keys()
    seen: set[tuple] = set()
    cards: list[tuple[str, Path]] = []
    for idx, q in enumerate(results.queue()):
        key = issue_key(q)
        if key in done or key in seen:
            continue
        seen.add(key)
        img_path = Path(q.get("zoom") or q.get("page_image", ""))
        if not img_path.exists():
            continue
        t = " ".join(q.get("transcript", "").splitlines())[:42]
        s = " ".join(q.get("scan", "").splitlines())[:42]
        label = (
            f"#{idx} p{q['page']} L{q.get('line', 1)} [{q['kind']}] | T: {t} | S: {s}"
        )
        cards.append((label, img_path))
    out_dir = results.verify_folder / "sheets"
    return [
        contact_sheet(cards[start : start + size], out_dir / f"sheet_{n:02d}.png")
        for n, start in enumerate(range(0, len(cards), size), 1)
    ]
