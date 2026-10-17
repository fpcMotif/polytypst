"""Word-placed facsimile of the 1970 Bourbaki scan.

Every scan page becomes one output page of the same size. Apple Vision OCR gives
the text lines; ink gaps on the scan give the word boxes; each OCR word is set in
Baskervville and scaled so its glyph ink fills the scan word's ink box. Fletcher
diagrams replace the OCR text inside the scan box where each diagram is found.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf
from fontTools.ttLib import TTFont
from PIL import Image, ImageFont

from . import DIAGRAM_DIR, install_bourbaki_diagrams
from .pagefit import FONTS, ORIGINAL, find_diagram

SLUG = "bourbaki_1970_facsimile"
SCAN_DPI = 300
PT_PER_PX = 72 / SCAN_DPI
INK_LEVEL = 140
SIZE = 10.0
WEIGHT = 600
SEG_GAP_PT = 0.9
FONT_FILE = FONTS / "Baskervville-wght.ttf"
FONT_STACK = '("Baskervville", "STIX Two Text", "STIX Two Math")'


@dataclass(frozen=True)
class Placement:
    """A run of text whose glyph ink is stretched to an ink box on the scan (pt, top-left origin)."""

    text: str
    left: float
    right: float
    top: float
    bottom: float
    baseline: float


def scan_ink(page: pymupdf.Page) -> np.ndarray:
    pix = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width) < INK_LEVEL


def ocr_pages(doc: pymupdf.Document, cache: Path, batch: int = 40) -> dict[int, list[dict]]:
    """Vision OCR lines per 1-based page, cached as one JSON file per page."""
    from polytypst.ocr.apple_vision import AppleVisionOCREngine

    cache.mkdir(parents=True, exist_ok=True)
    todo = [p for p in range(1, doc.page_count + 1) if not (cache / f"p{p:03d}.json").exists()]
    engine = AppleVisionOCREngine(["en-US", "fr-FR"])
    scans = cache / "scans"
    scans.mkdir(exist_ok=True)
    for start in range(0, len(todo), batch):
        pages = todo[start : start + batch]
        paths = []
        for p in pages:
            png = scans / f"p{p:03d}.png"
            doc[p - 1].get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY).save(png)
            paths.append(png)
        for p, result in zip(pages, engine.recognize_document(paths)):
            lines = [dict(text=l.text, x=l.x, y=l.y, w=l.w, h=l.h) for l in result.lines]
            (cache / f"p{p:03d}.json").write_text(json.dumps(lines, ensure_ascii=False), encoding="utf-8")
        for png in paths:
            png.unlink()
        print(f"OCR {pages[-1]}/{doc.page_count}", flush=True)
    return {p: json.loads((cache / f"p{p:03d}.json").read_text()) for p in range(1, doc.page_count + 1)}


def segments(ink: np.ndarray, x0: int, x1: int, y0: int, y1: int) -> list[tuple[int, int]]:
    """Column runs of ink in a line band, split at gaps of at least SEG_GAP_PT."""
    gap = round(SEG_GAP_PT / PT_PER_PX)
    cols = np.concatenate([ink[y0:y1, x0:x1].any(axis=0), np.zeros(gap + 1, bool)])
    segs, start, run, end = [], None, 0, 0
    for i, v in enumerate(cols):
        if v:
            if start is None:
                start = i
            run, end = 0, i
        elif start is not None:
            run += 1
            if run >= gap:
                segs.append((x0 + start, x0 + end + 1))
                start = None
    return segs


def align_words(widths: list[float], space: float, segs: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
    """Monotone match of each word to a run of ink segments, by predicted width and position."""
    n, m = len(widths), len(segs)
    if n == 0 or m < n:
        return None
    nat = np.array(widths)
    scale = (segs[-1][1] - segs[0][0]) / (nat.sum() + space * (n - 1))
    pred_start = segs[0][0] + np.concatenate([[0.0], np.cumsum(nat + space)[:-1]]) * scale
    pred_w = nat * scale
    cost = np.full((n + 1, m + 1), np.inf)
    back = np.zeros((n + 1, m + 1), int)
    cost[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(i, m - (n - i) + 1):
            for k in range(i - 1, j):
                if cost[i - 1, k] == np.inf:
                    continue
                a, b = segs[k][0], segs[j - 1][1]
                c = cost[i - 1, k] + abs((b - a) - pred_w[i - 1]) + 0.5 * abs(a - pred_start[i - 1])
                if c < cost[i, j]:
                    cost[i, j], back[i, j] = c, k
    if cost[n, m] == np.inf:
        return None
    out, j = [], m
    for i in range(n, 0, -1):
        k = back[i, j]
        out.append((segs[k][0], segs[j - 1][1]))
        j = k
    return out[::-1]


def line_baseline(ink: np.ndarray, x0: int, x1: int, y0: int, y1: int) -> int | None:
    """Bottom row (px) of the densest ink band of a line, which is its baseline."""
    rows = ink[y0:y1, x0:x1].sum(axis=1)
    if rows.size == 0 or rows.max() == 0:
        return None
    j = peak = int(np.argmax(rows))
    while j + 1 < len(rows) and rows[j + 1] > 0.3 * rows[peak]:
        j += 1
    return y0 + j + 1


class Measure:
    """Glyph ink boxes and advances in Baskervville at WEIGHT, per 100 units of font size."""

    def __init__(self) -> None:
        self.font = ImageFont.truetype(str(FONT_FILE), 100)
        self.font.set_variation_by_axes([WEIGHT])
        self.cmap = set(TTFont(str(FONT_FILE)).getBestCmap())
        self.space = self.font.getlength(" ")

    def covers(self, text: str) -> bool:
        return all(ord(c) in self.cmap for c in text)

    def width(self, text: str) -> float:
        return self.font.getlength(text) if self.covers(text) else self.space * 2 * len(text)

    def ink_scale(self, text: str, width: float) -> float | None:
        """Horizontal scale that makes the text's ink at SIZE exactly `width` pt wide."""
        if not self.covers(text):
            return None
        l, _, r, _ = self.font.getbbox(text, anchor="ls")
        return width / ((r - l) * SIZE / 100) if r > l else None


MIN_SCALE, MAX_SCALE = 0.8, 1.25


def page_placements(ink: np.ndarray, lines: list[dict], skip: list[tuple[float, float, float, float]], measure: Measure) -> list[Placement]:
    """Word placements for one page, leaving out OCR lines inside the `skip` boxes (pt)."""
    h, w = ink.shape
    out: list[Placement] = []
    for line in lines:
        x0 = max(0, int(line["x"] * w) - 4)
        x1 = min(w, int((line["x"] + line["w"]) * w) + 4)
        y0 = max(0, int((1 - line["y"] - line["h"]) * h))
        y1 = min(h, int((1 - line["y"]) * h))
        cx, cy = (x0 + x1) / 2 * PT_PER_PX, (y0 + y1) / 2 * PT_PER_PX
        if any(l <= cx <= r and t <= cy <= b for l, t, r, b in skip):
            continue
        base = line_baseline(ink, x0, x1, y0, y1)
        segs = segments(ink, x0, x1, y0, y1)
        if base is None or not segs:
            continue
        words = line["text"].split()
        boxes = align_words([measure.width(wd) for wd in words], measure.space, segs) or [(segs[0][0], segs[-1][1])]
        scales = [measure.ink_scale(wd, (b - a) * PT_PER_PX) for wd, (a, b) in zip(words, boxes)]
        if len(boxes) != len(words) or any(s is not None and not MIN_SCALE <= s <= MAX_SCALE for s in scales):
            words, boxes = [line["text"]], [(segs[0][0], segs[-1][1])]
        for word, (a, b) in zip(words, boxes):
            rows = np.where(ink[y0:y1, a:b].any(axis=1))[0]
            if rows.size == 0:
                continue
            out.append(Placement(word, a * PT_PER_PX, b * PT_PER_PX, (y0 + rows.min()) * PT_PER_PX, (y0 + rows.max() + 1) * PT_PER_PX, base * PT_PER_PX))
    return out


def typst_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def placement_typst(p: Placement, measure: Measure) -> str:
    """A placed word: ink-fitted when Baskervville has every glyph, else advance-fitted."""
    s = SIZE / 100
    if measure.covers(p.text):
        l, _, r, _ = measure.font.getbbox(p.text, anchor="ls")
        if r > l:
            sx = min(MAX_SCALE, max(MIN_SCALE, (p.right - p.left) / ((r - l) * s)))
            return (
                f"#place(top + left, dx: {p.left - l * s * sx:.2f}pt, dy: {p.baseline:.2f}pt, "
                f"scale(x: {sx * 100:.1f}%, origin: top + left, reflow: false, word({typst_string(p.text)})))"
            )
    return f"#place(top + left, dx: {p.left:.2f}pt, dy: {p.baseline:.2f}pt, fit({p.right - p.left:.2f}pt, word({typst_string(p.text)})))"


@dataclass(frozen=True)
class Diagram:
    fig: str
    left: float
    top: float
    width: float
    height: float
    ink_inset: tuple[float, float, float, float]


def diagram_ink(fig: str, work: Path) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Ink mask of a fletcher snippet at SCAN_DPI and its ink insets (pt) inside the snippet box."""
    harness = work / "diagram_harness.typ"
    harness.write_text(
        '#set page(width: auto, height: auto, margin: 0pt)\n'
        f'#set text(font: {FONT_STACK}, size: 9.6pt, weight: 500, number-type: "lining")\n'
        '#include "/polytypst/bourbaki/diagrams/fig_" + sys.inputs.at("id") + ".typ"\n',
        encoding="utf-8",
    )
    png = work / f"diagram_{fig}.png"
    subprocess.run(
        ["typst", "compile", "--root", ".", "--font-path", str(FONTS), "--input", f"id={fig}", str(harness), str(png), "--ppi", str(SCAN_DPI)],
        check=True, capture_output=True,
    )
    img = np.asarray(Image.open(png).convert("L")) < INK_LEVEL
    ys, xs = np.where(img)
    inset = (xs.min() * PT_PER_PX, ys.min() * PT_PER_PX, (img.shape[1] - xs.max() - 1) * PT_PER_PX, (img.shape[0] - ys.max() - 1) * PT_PER_PX)
    return img[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1], inset


def locate_diagrams(doc: pymupdf.Document, work: Path) -> dict[int, list[Diagram]]:
    """Scan position of every fletcher diagram, keyed by 1-based page."""
    found: dict[int, list[Diagram]] = {}
    for src in sorted(DIAGRAM_DIR.glob("fig_*.typ")):
        fig = src.stem.removeprefix("fig_")
        page = int(fig.split("_")[0])
        tmpl, inset = diagram_ink(fig, work)
        y, x, th, tw, _ = find_diagram(scan_ink(doc[page - 1]), tmpl, scales=(0.9, 0.95, 1.0, 1.05, 1.1, 1.15))
        found.setdefault(page, []).append(Diagram(fig, x * PT_PER_PX, y * PT_PER_PX, tw * PT_PER_PX, th * PT_PER_PX, inset))
    return found


def diagram_typst(d: Diagram, natural: tuple[float, float]) -> str:
    """The snippet scaled so its ink box covers the diagram's ink box on the scan."""
    l, t, r, b = d.ink_inset
    ink_w, ink_h = natural[0] - l - r, natural[1] - t - b
    sx, sy = d.width / ink_w, d.height / ink_h
    return (
        f"#place(top + left, dx: {d.left - l * sx:.2f}pt, dy: {d.top - t * sy:.2f}pt, "
        f'scale(x: {sx * 100:.1f}%, y: {sy * 100:.1f}%, origin: top + left, reflow: false, diagram-text(include "figures/fig_{d.fig}.typ")))'
    )


PREAMBLE = f"""#set document(title: "Commutative Algebra (1970 facsimile)")
#set text(font: {FONT_STACK}, size: {SIZE}pt, weight: {WEIGHT}, number-type: "lining", top-edge: "baseline", bottom-edge: "baseline")
#let word(s) = text(s)
#let fit(w, body) = context {{ let n = measure(body).width; if n > 0pt {{ scale(x: calc.clamp(w / n, {MIN_SCALE}, {MAX_SCALE}) * 100%, origin: top + left, reflow: false, body) }} else {{ body }} }}
#let diagram-text(body) = {{ set text(size: 9.6pt, weight: 500, top-edge: "cap-height", bottom-edge: "baseline"); body }}
"""


def build_facsimile(out_dir: Path) -> Path:
    """Write and compile the facsimile edition; returns the PDF path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "facsimile"
    work.mkdir(exist_ok=True)
    install_bourbaki_diagrams(out_dir)
    doc = pymupdf.open(ORIGINAL)
    ocr = ocr_pages(doc, work / "ocr")
    diagrams = locate_diagrams(doc, work)
    measure = Measure()
    natural = {}
    for page_diagrams in diagrams.values():
        for d in page_diagrams:
            png = Image.open(work / f"diagram_{d.fig}.png")
            natural[d.fig] = (png.width * PT_PER_PX, png.height * PT_PER_PX)
    pages = []
    for p in range(1, doc.page_count + 1):
        rect = doc[p - 1].rect
        page_diagrams = diagrams.get(p, [])
        skip = [(d.left - 2, d.top - 2, d.left + d.width + 2, d.top + d.height + 2) for d in page_diagrams]
        body = [placement_typst(pl, measure) for pl in page_placements(scan_ink(doc[p - 1]), ocr[p], skip, measure)]
        body += [diagram_typst(d, natural[d.fig]) for d in page_diagrams]
        pages.append(f"#page(width: {rect.width:.2f}pt, height: {rect.height:.2f}pt, margin: 0pt)[\n" + "\n".join(body) + "\n]")
        if p % 50 == 0:
            print(f"placed page {p}/{doc.page_count}", flush=True)
    typ = out_dir / f"{SLUG}.typ"
    typ.write_text(PREAMBLE + "\n".join(pages) + "\n", encoding="utf-8")
    pdf = out_dir / f"{SLUG}.pdf"
    subprocess.run(["typst", "compile", "--font-path", str(FONTS), str(typ), str(pdf)], check=True)
    return pdf
