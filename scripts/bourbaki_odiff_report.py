"""Score every page of the 1970 Bourbaki facsimile against the scan with odiff.

Usage: uv run python scripts/bourbaki_odiff_report.py
(build first with: uv run python assemble_complete_bourbaki.py facsimile)

Renders each scan page and the matching facsimile page at 150 dpi, runs odiff
(threshold 0.3, antialiasing ignored), and writes output/bourbaki/odiff_report/:
report.csv, summary.json, and index.html with original | facsimile | redshift |
odiff per page (redshift: red only in the original, cyan only in ours).
"""

import csv
import html
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

from polytypst.bourbaki.facsimile import SLUG
from polytypst.bourbaki.spec import BOURBAKI_SPEC
from polytypst.parity.source import source_pdf

ORIGINAL = source_pdf(BOURBAKI_SPEC)

FACSIMILE = Path("output/bourbaki") / f"{SLUG}.pdf"
OUT = Path("output/bourbaki/odiff_report")
DPI = 150
GOAL = 5.0


def render(doc: pymupdf.Document, page: int, size: tuple[int, int] | None = None) -> Image.Image:
    pix = doc[page - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    return img.resize(size, Image.Resampling.LANCZOS) if size else img


def prepare(orig: pymupdf.Document, ours: pymupdf.Document, page: int) -> None:
    a = render(orig, page)
    b = render(ours, page, a.size)
    a.save(OUT / "img" / f"o{page:03d}.png")
    b.save(OUT / "img" / f"f{page:03d}.png")
    ai, bi = np.asarray(a) < 160, np.asarray(b) < 160
    rgb = np.full((*ai.shape, 3), 255, np.uint8)
    rgb[ai & ~bi] = (220, 0, 0)
    rgb[bi & ~ai] = (0, 170, 220)
    rgb[ai & bi] = (0, 0, 0)
    Image.fromarray(rgb).save(OUT / "img" / f"r{page:03d}.png")


def odiff(page: int) -> float:
    img = OUT / "img"
    res = subprocess.run(
        ["bunx", "--bun", "odiff-bin", str(img / f"o{page:03d}.png"), str(img / f"f{page:03d}.png"),
         str(img / f"d{page:03d}.png"), "--threshold=0.3", "--antialiasing"],
        capture_output=True, text=True, check=False,
    )
    found = re.search(r"\(([\d.]+)%\)", res.stdout + res.stderr)
    if found:
        return float(found.group(1))
    if res.returncode == 0:
        return 0.0
    raise RuntimeError(f"odiff failed on page {page}: {res.stdout}{res.stderr}")


def main() -> None:
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    orig, ours = pymupdf.open(ORIGINAL), pymupdf.open(FACSIMILE)
    if orig.page_count != ours.page_count:
        raise SystemExit(f"page counts differ: scan {orig.page_count}, facsimile {ours.page_count}")
    pages = list(range(1, orig.page_count + 1))
    for p in pages:
        prepare(orig, ours, p)
    with ThreadPoolExecutor(8) as pool:
        diffs = dict(zip(pages, pool.map(odiff, pages)))
    for p in pages:
        print(f"page {p}: {diffs[p]:.2f}%", flush=True)

    with (OUT / "report.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["pdf_page", "odiff_pct", "under_goal"])
        writer.writerows([p, diffs[p], diffs[p] < GOAL] for p in pages)
    values = np.array([diffs[p] for p in pages])
    summary = {
        "pages": len(pages),
        "goal_pct": GOAL,
        "under_goal": int(np.sum(values < GOAL)),
        "median_pct": round(float(np.median(values)), 2),
        "mean_pct": round(float(values.mean()), 2),
        "p90_pct": round(float(np.percentile(values, 90)), 2),
        "max_pct": round(float(values.max()), 2),
        "worst_pages": [int(p) for p in sorted(pages, key=lambda p: -diffs[p])[:10]],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))

    rows = "".join(
        f"""<tr class="{'pass' if diffs[p] < GOAL else 'fail'}" data-diff="{diffs[p]}" data-page="{p}">
<td class="meta"><b>PDF page {p}</b><br><span class="tag">{diffs[p]:.2f}%</span></td>
<td><img loading="lazy" src="img/o{p:03d}.png" alt="original {p}"></td>
<td><img loading="lazy" src="img/f{p:03d}.png" alt="facsimile {p}"></td>
<td><img loading="lazy" src="img/r{p:03d}.png" alt="redshift {p}"></td>
<td><img loading="lazy" src="img/d{p:03d}.png" alt="odiff {p}"></td></tr>"""
        for p in pages
    )
    stats = "".join(f"<li>{html.escape(k)}: {html.escape(str(v))}</li>" for k, v in summary.items())
    (OUT / "index.html").write_text(f"""<!doctype html>
<meta charset="utf-8"><title>Bourbaki facsimile odiff</title>
<style>
body {{ font: 14px system-ui, sans-serif; margin: 16px; background: #fff; color: #111; }}
table {{ border-collapse: collapse; }}
td, th {{ border-bottom: 1px solid #ddd; padding: 6px; vertical-align: top; }}
th {{ text-align: left; position: sticky; top: 0; background: #fff; z-index: 1; }}
img {{ width: 22vw; max-width: 420px; height: auto; display: block; border: 1px solid #eee; }}
.meta {{ white-space: nowrap; font-size: 12px; }}
.tag {{ font-weight: 600; padding: 0 4px; border-radius: 3px; }}
.pass .tag {{ background: #dfd; }} .fail .tag {{ background: #fdd; }}
</style>
<h1>Bourbaki 1970 facsimile vs scan: odiff per page</h1>
<p>odiff at {DPI} dpi, threshold 0.3, antialiasing ignored. Goal: under {GOAL}% per page.
Redshift: red only in the original, cyan only in the facsimile, black in both.</p>
<ul>{stats}</ul>
<p>Show: <button data-f="all">all</button><button data-f="pass">under {GOAL}%</button><button data-f="fail">{GOAL}% or more</button>
<button id="sort">worst first</button></p>
<table><thead><tr><th></th><th>Original scan</th><th>Facsimile</th><th>Redshift</th><th>odiff</th></tr></thead>
<tbody id="b">{rows}</tbody></table>
<script>
const body = document.getElementById('b');
document.querySelectorAll('[data-f]').forEach(b => b.onclick = () => {{
  for (const tr of body.rows) tr.hidden = b.dataset.f !== 'all' && !tr.classList.contains(b.dataset.f);
}});
let worst = false;
document.getElementById('sort').onclick = e => {{
  worst = !worst;
  e.target.textContent = worst ? 'page order' : 'worst first';
  const key = worst ? r => -r.dataset.diff : r => +r.dataset.page;
  [...body.rows].sort((a, b) => key(a) - key(b)).forEach(r => body.appendChild(r));
}};
</script>
""", encoding="utf-8")
    print(f"wrote {OUT / 'index.html'}", flush=True)


if __name__ == "__main__":
    main()
