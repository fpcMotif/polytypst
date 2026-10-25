"""Scan parity verdicts per page against an edition's tolerance, written as CSV, JSON and an HTML page review."""

import csv
import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pymupdf
from PIL import Image

from .compare import PageParity, common_crop

REVIEW_DPI = 100
REVIEW_INK = 150
DIAGRAM_DPI = 200
DIAGRAM_PAD_PT = 10.0


@dataclass(frozen=True)
class Tolerance:
    """Limits (pt, or ratios) a rebuilt page must keep to pass scan parity.

    `word_lines` is "all" when every word must sit on the scan, or "agreeing" when only
    words on lines that break at the same word as the scan are held to `word_pt`.
    """

    word_pt: float
    word_lines: Literal["all", "agreeing"]
    baseline_pt: float
    page_offset_pt: float
    max_bad_word_share: float = 0.01
    min_matched_share: float = 0.5
    diagram_pt: float = 1.0
    diagram_scale: float = 0.02
    same_line_count: bool = False
    one_page: bool = False
    max_right_overflow_lines: int = 0


FACSIMILE = Tolerance(word_pt=0.5, word_lines="all", baseline_pt=0.5, page_offset_pt=0.3)
SOURCE_PAGINATED = Tolerance(
    word_pt=1.5, word_lines="agreeing", baseline_pt=1.5, page_offset_pt=1.0, same_line_count=True, one_page=True
)


def bad_words(page: PageParity, tol: Tolerance) -> list[str]:
    """The words of a page that sit further from the scan than the tolerance allows."""
    agreeing = {line.source_line for line in page.lines if line.ends_agree}
    out = []
    for w in page.words:
        if tol.word_lines == "all":
            off = max(abs(w.dx_left), abs(w.dx_right), abs(w.dy))
        elif w.source_line in agreeing:
            off = max(abs(w.dx_left), abs(w.dx_right))
        else:
            continue
        if off > tol.word_pt:
            out.append(w.text)
    return out


def verdict(page: PageParity, tol: Tolerance) -> list[str]:
    """Reasons the page fails scan parity; empty when it passes."""
    reasons = []
    if page.words_source and len(page.words) < tol.min_matched_share * page.words_source:
        reasons.append(f"only {len(page.words)}/{page.words_source} words matched")
    if max(abs(page.page_dx), abs(page.page_dy)) > tol.page_offset_pt:
        reasons.append(f"page offset {page.page_dx:+.2f},{page.page_dy:+.2f}pt")
    bad = bad_words(page, tol)
    if page.words and len(bad) > tol.max_bad_word_share * len(page.words):
        reasons.append(f"{len(bad)} words off by more than {tol.word_pt}pt")
    lines_off = [line for line in page.lines if abs(line.dy) > tol.baseline_pt]
    if lines_off:
        reasons.append(f"{len(lines_off)} baselines off by more than {tol.baseline_pt}pt")
    if tol.same_line_count and page.lines_source != page.lines_rebuilt:
        reasons.append(f"lines {page.lines_source} vs {page.lines_rebuilt}")
    if tol.one_page and len(page.rebuilt_pages) > 1:
        reasons.append(f"overflows onto {len(page.rebuilt_pages) - 1} more page(s)")
    for d in page.diagrams:
        if max(abs(d.dx), abs(d.dy)) > tol.diagram_pt or max(abs(d.sx - 1), abs(d.sy - 1)) > tol.diagram_scale:
            reasons.append(f"diagram {d.name} off {d.dx:+.1f},{d.dy:+.1f}pt x{d.sx:.3f},{d.sy:.3f}")
    if page.right_overflow_lines > tol.max_right_overflow_lines:
        reasons.append(f"{page.right_overflow_lines} lines cross the scan's right text edge")
    return reasons


def _gray(doc: pymupdf.Document, page: int, dpi: int = REVIEW_DPI, clip: pymupdf.Rect | None = None) -> np.ndarray:
    pix = doc[page - 1].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, clip=clip)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)


def _diagram_crops(src: pymupdf.Document, ours: pymupdf.Document, page: PageParity, img: Path) -> str:
    """A zoomed overlay of each diagram's area, the same clip on both pages; returns the HTML for them."""
    out = []
    for d in page.diagrams:
        l, t, r, b = d.source_box
        clip = pymupdf.Rect(l - DIAGRAM_PAD_PT, t - DIAGRAM_PAD_PT, r + DIAGRAM_PAD_PT, b + DIAGRAM_PAD_PT)
        name = f"p{page.source_page:03d}_{d.name}.png"
        write_overlay(_gray(src, page.source_page, DIAGRAM_DPI, clip), _gray(ours, page.rebuilt_pages[0], DIAGRAM_DPI, clip), img / name)
        caption = f"{d.name}: {d.dx:+.2f}, {d.dy:+.2f}pt, x{d.sx:.3f}, {d.sy:.3f}"
        out.append(f'<figure><img class="diagram" loading="lazy" src="img/{name}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>')
    return "".join(out)


def write_overlay(source: np.ndarray, rebuilt: np.ndarray, path: Path) -> None:
    """Red ink only on the scan, cyan only in the rebuilt page, black in both; pages in place, no shift."""
    a, b = common_crop(source < REVIEW_INK, rebuilt < REVIEW_INK)
    rgb = np.full((*a.shape, 3), 255, np.uint8)
    rgb[a & ~b] = (220, 0, 0)
    rgb[b & ~a] = (0, 170, 220)
    rgb[a & b] = (0, 0, 0)
    Image.fromarray(rgb).save(path)


def _row(page: PageParity, reasons: list[str], tol: Tolerance) -> dict[str, object]:
    worst = max((max(abs(w.dx_left), abs(w.dx_right), abs(w.dy)) for w in page.words), default=0.0)
    return {
        "source_page": page.source_page,
        "rebuilt_pages": " ".join(map(str, page.rebuilt_pages)),
        "status": "fail" if reasons else "ok",
        "reasons": "; ".join(reasons),
        "page_dx_pt": page.page_dx,
        "page_dy_pt": page.page_dy,
        "ink_iou": page.ink_iou,
        "lines_source": page.lines_source,
        "lines_rebuilt": page.lines_rebuilt,
        "words_matched": len(page.words),
        "words_source": page.words_source,
        "bad_words": len(bad_words(page, tol)),
        "worst_word_pt": round(worst, 2),
        "worst_baseline_pt": max((abs(line.dy) for line in page.lines), default=0.0),
        "right_overflow_lines": page.right_overflow_lines,
        "diagrams": " ".join(f"{d.name}:{d.dx:+.1f},{d.dy:+.1f},x{d.sx:.3f}" for d in page.diagrams),
    }


def write_report(results: list[PageParity], out_dir: Path, tolerance: Tolerance) -> bool:
    """Write report.csv, summary.json and index.html with source, rebuilt and overlay images; True when every page passes."""
    img = out_dir / "img"
    img.mkdir(parents=True, exist_ok=True)
    rows, items = [], []
    docs: dict[Path, pymupdf.Document] = {}
    for page in results:
        reasons = verdict(page, tolerance)
        row = _row(page, reasons, tolerance)
        rows.append(row)
        src = docs.setdefault(page.source, pymupdf.open(page.source))
        ours = docs.setdefault(page.rebuilt, pymupdf.open(page.rebuilt))
        a, b = _gray(src, page.source_page), _gray(ours, page.rebuilt_pages[0])
        stem = f"p{page.source_page:03d}"
        Image.fromarray(a).save(img / f"{stem}_source.png")
        Image.fromarray(b).save(img / f"{stem}_rebuilt.png")
        write_overlay(a, b, img / f"{stem}_overlay.png")
        meta = "<br>".join(html.escape(f"{k}: {v}") for k, v in row.items() if k not in ("source_page", "status", "reasons"))
        worst = sorted(page.words, key=lambda w: -max(abs(w.dx_left), abs(w.dx_right), abs(w.dy)))[:8]
        worst_html = "".join(
            f"<li>{html.escape(w.text)} {w.dx_left:+.2f} {w.dx_right:+.2f} {w.dy:+.2f}</li>" for w in worst
        )
        items.append(
            f'<tr class="{row["status"]}" data-page="{page.source_page}" data-worst="{row["worst_word_pt"]}">'
            f'<td class="meta"><b>source page {page.source_page}</b><br><span class="tag {row["status"]}">{row["status"]}</span>'
            f'<br>{html.escape(str(row["reasons"]))}<br>{meta}<br>worst words (dx left, dx right, dy pt):<ul>{worst_html}</ul>'
            f"{_diagram_crops(src, ours, page, img)}</td>"
            f'<td><img loading="lazy" src="img/{stem}_source.png" alt="source {page.source_page}"></td>'
            f'<td><img loading="lazy" src="img/{stem}_rebuilt.png" alt="rebuilt {page.source_page}"></td>'
            f'<td><img loading="lazy" src="img/{stem}_overlay.png" alt="overlay {page.source_page}"></td></tr>'
        )
    if rows:
        with (out_dir / "report.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    failed = [r for r in rows if r["status"] == "fail"]
    summary = {"pages": len(rows), "passed": len(rows) - len(failed), "failed": len(failed), "right_overflow_lines": sum(r.right_overflow_lines for r in results), "tolerance": asdict(tolerance)}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (out_dir / "index.html").write_text(_page_html(summary, "".join(items)), encoding="utf-8")
    return not failed


def _page_html(summary: dict, rows: str) -> str:
    return f"""<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scan parity</title>
<style>
body {{ font: 14px system-ui, sans-serif; margin: 16px; background: #fff; color: #111; }}
table {{ border-collapse: collapse; }}
td {{ border-bottom: 1px solid #ddd; padding: 8px; vertical-align: top; }}
img {{ width: 28vw; max-width: 520px; height: auto; display: block; border: 1px solid #eee; }}
.meta {{ font-size: 12px; color: #444; max-width: 260px; }}
img.diagram {{ width: 100%; max-width: 260px; }}
figure {{ margin: 8px 0; }}
.tag {{ font-weight: 600; padding: 0 4px; border-radius: 3px; }}
.tag.ok {{ background: #dfd; }} .tag.fail {{ background: #fcc; }}
</style>
<h1>Scan parity</h1>
<p>{summary["passed"]} of {summary["pages"]} pages pass. Overlay: red ink only on the source scan, cyan only in the rebuilt PDF,
black in both. Pages are compared in place, with no shift.</p>
<p>Show: <button data-f="all">all</button> <button data-f="fail">fail</button> <button data-f="ok">ok</button>
<button id="sort">worst word first</button></p>
<table><tbody id="t">{rows}</tbody></table>
<script>
const body = document.getElementById('t');
document.querySelectorAll('[data-f]').forEach(b => b.onclick = () => {{
  for (const tr of body.rows) tr.hidden = b.dataset.f !== 'all' && !tr.classList.contains(b.dataset.f);
}});
let worst = false;
document.getElementById('sort').onclick = e => {{
  worst = !worst;
  e.target.textContent = worst ? 'page order' : 'worst word first';
  const key = worst ? r => -r.dataset.worst : r => +r.dataset.page;
  [...body.rows].sort((a, b) => key(a) - key(b)).forEach(r => body.appendChild(r));
}};
</script>
"""
