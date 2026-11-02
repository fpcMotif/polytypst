import base64
import html
import io
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import BoundedSemaphore

import pymupdf
from PIL import Image, ImageDraw, ImageFont
from polytypst_native import encode_png

from . import STRIP_PAD, Band, PageCheck, strip_png
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


@dataclass(frozen=True)
class Strip:
    page: int
    band: Band
    dpi: int
    out: Path


def _clip(rect: pymupdf.Rect, band: Band) -> pymupdf.Rect:
    top, bottom = max(0.0, band[0] - STRIP_PAD), min(1.0, band[1] + STRIP_PAD)
    return pymupdf.Rect(rect.x0, rect.y0 + top * rect.height, rect.x1, rect.y0 + bottom * rect.height)


def image_png(image: Image.Image) -> bytes:
    return encode_png(image.tobytes(), image.width, image.height, len(image.getbands()))


def scan_jpeg(page: pymupdf.Page) -> bytes | None:
    images = page.get_images(full=True)
    if len(images) != 1 or page.rotation or page.get_drawings() or any(span["type"] != 3 for span in page.get_texttrace()):
        return None
    xref, smask, _, _, bpc, colorspace, _, _, codec = images[0][:9]
    if smask or bpc != 8 or colorspace not in ("DeviceRGB", "DeviceGray") or codec != "DCTDecode":
        return None
    placed = page.get_image_info()
    if len(placed) != 1 or placed[0]["has-mask"] or page.parent.xref_get_key(xref, "Decode")[0] != "null":
        return None
    a, b, c, d, e, f = placed[0]["transform"]
    r = page.rect
    if b or c or max(abs(e - r.x0), abs(f - r.y0), abs(a - r.width), abs(d - r.height)) > 0.01:
        return None
    return page.parent.xref_stream_raw(xref)


def _shrunk(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    if image.size == size:
        return image
    factor = image.width // size[0]
    if factor > 1 and (reduced := image.reduce(factor)).size == size:
        return reduced
    return image.resize(size, Image.Resampling.BOX)


def _page_strips(rect: pymupdf.Rect, jpeg: bytes, strips: list[Strip]) -> None:
    top_dpi = max(s.dpi for s in strips)
    full = (rect * pymupdf.Matrix(top_dpi / 72, top_dpi / 72)).irect
    image = Image.open(io.BytesIO(jpeg))
    w, h = image.size
    scale = next(s for s in (8, 4, 2, 1) if -(-w // s) >= full.width and -(-h // s) >= full.height)
    image.draft(image.mode, (w // scale, h // scale))
    image = _shrunk(image, (full.width, full.height))
    for dpi in sorted({s.dpi for s in strips}, reverse=True):
        scale = pymupdf.Matrix(dpi / 72, dpi / 72)
        size = (rect * scale).irect
        at_dpi = _shrunk(image, (size.width, size.height))
        for s in strips:
            if s.dpi == dpi:
                cut = (_clip(rect, s.band) * scale).irect & size
                s.out.write_bytes(image_png(at_dpi.crop((cut.x0, cut.y0, cut.x1, cut.y1))))


def write_strips(doc: pymupdf.Document, strips: list[Strip]) -> None:
    by_page: dict[int, list[Strip]] = {}
    for s in strips:
        by_page.setdefault(s.page, []).append(s)
    threads = os.cpu_count() or 1
    in_flight = BoundedSemaphore(2 * threads)
    with ThreadPoolExecutor(threads) as pool:
        done = []
        for page, wanted in by_page.items():
            jpeg = scan_jpeg(doc[page - 1])
            pymupdf.TOOLS.store_shrink(100)
            if jpeg is None:
                for s in wanted:
                    s.out.write_bytes(strip_png(doc, s.page, s.band, s.dpi))
                continue
            in_flight.acquire()
            done.append(pool.submit(_page_strips, doc[page - 1].rect, jpeg, wanted))
            done[-1].add_done_callback(lambda _: in_flight.release())
        for future in done:
            future.result()


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
