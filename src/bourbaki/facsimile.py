"""Word-placed facsimile of the 1970 Bourbaki scan.

Every scan page becomes one output page of the same size. Apple Vision OCR gives
the text lines; ink gaps on the scan give the word boxes; each OCR word is set in
Baskervville and scaled so its glyph ink fills the scan word's ink box. Fletcher
diagrams replace the OCR text inside the scan box where each diagram is found.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf
from fontTools.ttLib import TTFont
from PIL import ImageFont

from ..compiler.monograph import REPO_FONTS_DIR as FONTS
from ..parity.diagrams import diagram_ink, find_diagram
from ..parity.source import (
    SCAN_DPI,
    OcrLine,
    ensure_source_ocr,
    read_source_page,
    source_ocr_dir,
)
from ..parity.words import PT_PER_PX, align_words, line_baseline, page_ink, segments
from . import DIAGRAM_DIR, DIAGRAM_TEXT, install_bourbaki_diagrams

SLUG = "bourbaki_1970_facsimile"
SIZE = 10.0
WEIGHT = 600
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


def page_placements(ink: np.ndarray, lines: tuple[OcrLine, ...], skip: list[tuple[float, float, float, float]], measure: Measure) -> list[Placement]:
    """Word placements for one page, leaving out OCR lines inside the `skip` boxes (pt)."""
    h, w = ink.shape
    out: list[Placement] = []
    for line in lines:
        x0 = max(0, int(line.x * w) - 4)
        x1 = min(w, int((line.x + line.w) * w) + 4)
        y0 = max(0, int((1 - line.y - line.h) * h))
        y1 = min(h, int((1 - line.y) * h))
        cx, cy = (x0 + x1) / 2 * PT_PER_PX, (y0 + y1) / 2 * PT_PER_PX
        if any(l <= cx <= r and t <= cy <= b for l, t, r, b in skip):
            continue
        base = line_baseline(ink, x0, x1, y0, y1)
        segs = segments(ink, x0, x1, y0, y1)
        if base is None or not segs:
            continue
        words = line.text.split()
        boxes = align_words([measure.width(wd) for wd in words], measure.space, segs) or [(segs[0][0], segs[-1][1])]
        scales = [measure.ink_scale(wd, (b - a) * PT_PER_PX) for wd, (a, b) in zip(words, boxes)]
        if len(boxes) != len(words) or any(s is not None and not MIN_SCALE <= s <= MAX_SCALE for s in scales):
            words, boxes = [line.text], [(segs[0][0], segs[-1][1])]
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
    ink_size: tuple[float, float]


def locate_diagrams(doc: pymupdf.Document, work: Path) -> dict[int, list[Diagram]]:
    """Scan position of every fletcher diagram, keyed by 1-based page."""
    found: dict[int, list[Diagram]] = {}
    for src in sorted(DIAGRAM_DIR.glob("fig_*.typ")):
        fig = src.stem.removeprefix("fig_")
        page = int(fig.split("_")[0])
        tmpl, inset = diagram_ink(src, work, SCAN_DPI, DIAGRAM_TEXT)
        y, x, th, tw, _ = find_diagram(page_ink(doc[page - 1]), tmpl, scales=(0.9, 0.95, 1.0, 1.05, 1.1, 1.15))
        ink_size = (tmpl.shape[1] * PT_PER_PX, tmpl.shape[0] * PT_PER_PX)
        found.setdefault(page, []).append(Diagram(fig, x * PT_PER_PX, y * PT_PER_PX, tw * PT_PER_PX, th * PT_PER_PX, inset, ink_size))
    return found


def diagram_typst(d: Diagram) -> str:
    """The snippet scaled so its ink box covers the diagram's ink box on the scan."""
    l, t, _, _ = d.ink_inset
    ink_w, ink_h = d.ink_size
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


def build_facsimile(source: Path, out_dir: Path) -> Path:
    """Write and compile the facsimile edition of the `source` scan; returns the PDF path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "facsimile"
    work.mkdir(exist_ok=True)
    install_bourbaki_diagrams(out_dir)
    doc = pymupdf.open(source)
    cache = source_ocr_dir(out_dir)
    ensure_source_ocr(source, cache)
    diagrams = locate_diagrams(doc, work)
    measure = Measure()
    pages = []
    for p in range(1, doc.page_count + 1):
        rect = doc[p - 1].rect
        page_diagrams = diagrams.get(p, [])
        skip = [(d.left - 2, d.top - 2, d.left + d.width + 2, d.top + d.height + 2) for d in page_diagrams]
        body = [placement_typst(pl, measure) for pl in page_placements(page_ink(doc[p - 1]), read_source_page(cache, p).lines, skip, measure)]
        body += [diagram_typst(d) for d in page_diagrams]
        pages.append(f"#page(width: {rect.width:.2f}pt, height: {rect.height:.2f}pt, margin: 0pt)[\n" + "\n".join(body) + "\n]")
        if p % 50 == 0:
            print(f"placed page {p}/{doc.page_count}", flush=True)
    typ = out_dir / f"{SLUG}.typ"
    typ.write_text(PREAMBLE + "\n".join(pages) + "\n", encoding="utf-8")
    pdf = out_dir / f"{SLUG}.pdf"
    subprocess.run(["typst", "compile", "--font-path", str(FONTS), str(typ), str(pdf)], check=True)
    return pdf
