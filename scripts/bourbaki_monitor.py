"""Score every page of the 1970 Bourbaki rebuild against the original scan.

Usage: uv run python scripts/bourbaki_monitor.py [--overlays N]   (N = -1 writes every page)

For each source page this aligns our page to the scan on the first body text
line, then reports ink overlap (IoU), text-line counts, and for every diagram
the vertical offset between its position here and in the original. It writes
output/bourbaki/monitor/report.csv and red/cyan overlays for the N worst pages
plus every page with a diagram (red only in the original, cyan only in ours).
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

from polytypst.bourbaki import OUT_DIR
from polytypst.bourbaki.marks import query_marks
from polytypst.bourbaki.spec import BOURBAKI_1970_SPEC
from polytypst.compiler.monograph import REPO_FONTS_DIR as FONTS
from polytypst.parity.diagrams import find_diagram
from polytypst.parity.source import source_pdf

ORIGINAL = source_pdf(BOURBAKI_1970_SPEC)
REBUILT = OUT_DIR / f"{BOURBAKI_1970_SPEC.slug}.pdf"
TYP = OUT_DIR / f"{BOURBAKI_1970_SPEC.slug}.typ"

OUT = Path("output/bourbaki/monitor")
DPI = 100
K = 72 / DPI


def ink(doc: pymupdf.Document, page: int) -> np.ndarray:
    pix = doc[page - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width) < 150


def rows(img: np.ndarray) -> list[tuple[int, int]]:
    on = np.append(img.sum(axis=1) > 1, False)
    out, start = [], None
    for y, v in enumerate(on):
        if v and start is None:
            start = y
        elif not v and start is not None:
            if y - start >= 2:
                out.append((start, y))
            start = None
    return out


def body_rows(img: np.ndarray) -> list[tuple[int, int]]:
    r = rows(img)
    if r:
        xs = np.where(img[r[-1][0] : r[-1][1]].any(axis=0))[0]
        if xs.max() - xs.min() < 25 / K:
            r = r[:-1]
    return r[1:] if len(r) > 2 else r


def anchor(img: np.ndarray) -> tuple[int, int]:
    """Top of the first body text line and the left edge of the text block."""
    r = body_rows(img)
    top = r[0][0] if r else 0
    cols = np.where(img[top:].sum(axis=0) > 2)[0]
    return top, int(cols.min()) if cols.size else 0


def shift(img: np.ndarray, dy: int, dx: int, shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, bool)
    h, w = img.shape
    ys, xs = max(0, dy), max(0, dx)
    ye, xe = min(shape[0], h + dy), min(shape[1], w + dx)
    if ye > ys and xe > xs:
        out[ys:ye, xs:xe] = img[ys - dy : ye - dy, xs - dx : xe - dx]
    return out


def dilate(img: np.ndarray) -> np.ndarray:
    out = img.copy()
    out[1:] |= img[:-1]
    out[:-1] |= img[1:]
    out[:, 1:] |= img[:, :-1]
    out[:, :-1] |= img[:, 1:]
    return out


def diagram_template(fig: str, cache: Path) -> np.ndarray | None:
    png = cache / f"{fig}.png"
    if not png.exists():
        res = subprocess.run(
            ["typst", "compile", "--root", ".", "--font-path", str(FONTS), "--input", f"id={fig}",
             "output/_proto/diag.typ", str(png), "--ppi", str(DPI)],
            capture_output=True, check=False,
        )
        if res.returncode != 0:
            return None
    img = np.asarray(Image.open(png).convert("L")) < 150
    ys, xs = np.where(img)
    return img[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1] if ys.size else None


def main(n_overlays: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / "diagram_templates"
    cache.mkdir(exist_ok=True)
    marks = query_marks(TYP)
    tops = {int(m["key"]): m["page"] for m in marks if m["kind"] == "top"}
    ends = {int(m["key"]): m["page"] for m in marks if m["kind"] == "end"}
    figs: dict[int, list[str]] = {}
    for m in marks:
        if m["kind"] == "fig":
            figs.setdefault(int(str(m["key"]).split("_")[0]), []).append(str(m["key"]))
    orig, ours = pymupdf.open(ORIGINAL), pymupdf.open(REBUILT)
    results = []
    for pno, our_page in sorted(tops.items()):
        a = ink(orig, pno)
        b = ink(ours, our_page)
        (ay, ax), (by, bx) = anchor(a), anchor(b)
        b_al = shift(b, ay - by, ax - bx, a.shape)
        inter = (dilate(a) & b_al).sum() + (a & dilate(b_al)).sum()
        dys = []
        for fig in figs.get(pno, []):
            tmpl = diagram_template(fig, cache)
            if tmpl is not None:
                dys.append((find_diagram(b, tmpl)[0] - by - (find_diagram(a, tmpl)[0] - ay)) * K)
        row = {
            "source_page": pno,
            "our_page": our_page,
            "overflow_pages": ends.get(pno, our_page) - our_page,
            "ink_overlap": round(float(inter / max(1, a.sum() + b_al.sum())), 3),
            "lines_orig": len(body_rows(a)),
            "lines_ours": len(body_rows(b)),
            "diagram_dy_pt": " ".join(f"{d:+.1f}" for d in dys),
        }
        results.append((row, a, b_al))

    with (OUT / "report.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0][0]))
        writer.writeheader()
        writer.writerows(r for r, _, _ in results)

    selected = results if n_overlays < 0 else sorted(results, key=lambda r: r[0]["ink_overlap"])[:n_overlays]
    with_figs = [r for r in results if r[0]["diagram_dy_pt"]]
    for row, a, b in {r[0]["source_page"]: r for r in selected + with_figs}.values():
        rgb = np.full((*a.shape, 3), 255, np.uint8)
        rgb[a & ~b] = (220, 0, 0)
        rgb[b & ~a] = (0, 170, 220)
        rgb[a & b] = (0, 0, 0)
        Image.fromarray(rgb).save(OUT / f"p{row['source_page']:03d}.png")

    overlaps = np.array([r["ink_overlap"] for r, _, _ in results])
    line_diff = np.array([abs(r["lines_orig"] - r["lines_ours"]) for r, _, _ in results])
    dys = np.array([abs(float(d)) for r, _, _ in results for d in r["diagram_dy_pt"].split()])
    summary = {
        "pages": len(results),
        "overflowing_pages": sum(1 for r, _, _ in results if r["overflow_pages"] > 0),
        "ink_overlap_median": round(float(np.median(overlaps)), 3),
        "same_line_count_pct": round(float(np.mean(line_diff == 0) * 100), 1),
        "within_one_line_pct": round(float(np.mean(line_diff <= 1) * 100), 1),
        "diagrams": int(dys.size),
        "diagram_offset_median_pt": round(float(np.median(dys)), 1) if dys.size else None,
        "diagrams_within_6pt": int(np.sum(dys <= 6)),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    args = sys.argv[1:]
    main(int(args[args.index("--overlays") + 1]) if "--overlays" in args else 12)
