"""Build a side-by-side review of every page of the 1970 Bourbaki rebuild against the scan.

Usage: uv run python scripts/bourbaki_page_review.py

Run scripts/bourbaki_monitor.py --overlays -1 first. Each row shows the original
scan page, our page, and the monitor's red/cyan overlay (red only in the original,
cyan only in ours), with the monitor's scores. Writes output/bourbaki/page_review/index.html.
"""

import csv
import html
import json
from pathlib import Path

import pymupdf

from polytypst.bourbaki.pagefit import ORIGINAL, REBUILT

MONITOR = Path("output/bourbaki/monitor")
OUT = Path("output/bourbaki/page_review")
DPI = 100


def save_page(doc: pymupdf.Document, page: int, path: Path) -> None:
    if not path.exists():
        doc[page - 1].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY).save(path)


def flag(row: dict[str, str]) -> str:
    dys = [abs(float(d)) for d in row["diagram_dy_pt"].split()]
    if int(row["overflow_pages"]) > 0:
        return "overflow"
    if abs(int(row["lines_orig"]) - int(row["lines_ours"])) > 1:
        return "lines"
    if any(d > 6 for d in dys):
        return "diagram"
    return "ok"


def main() -> None:
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((MONITOR / "report.csv").open()))
    summary = json.loads((MONITOR / "summary.json").read_text())
    orig, ours = pymupdf.open(ORIGINAL), pymupdf.open(REBUILT)
    items = []
    for row in rows:
        pno, our = int(row["source_page"]), int(row["our_page"])
        save_page(orig, pno, OUT / "img" / f"o{pno:03d}.png")
        save_page(ours, our, OUT / "img" / f"r{pno:03d}.png")
        overlay = MONITOR / f"p{pno:03d}.png"
        status = flag(row)
        items.append(
            f"""<tr class="{status}" data-overlap="{row['ink_overlap']}" data-page="{pno}">
<td class="meta"><b>PDF page {pno}</b><br>our page {our}<br>
<span class="tag {status}">{status}</span><br>
ink overlap {row['ink_overlap']}<br>lines {row['lines_orig']} / {row['lines_ours']}<br>
overflow {row['overflow_pages']}<br>{('diagram dy ' + html.escape(row['diagram_dy_pt']) + 'pt') if row['diagram_dy_pt'] else ''}</td>
<td><img loading="lazy" src="img/o{pno:03d}.png" alt="original {pno}"></td>
<td><img loading="lazy" src="img/r{pno:03d}.png" alt="ours {pno}"></td>
<td>{f'<img loading="lazy" src="../monitor/{overlay.name}" alt="overlay {pno}">' if overlay.exists() else ''}</td></tr>"""
        )
        print(f"page {pno}: {status}", flush=True)

    counts = {s: sum(1 for r in rows if flag(r) == s) for s in ("ok", "lines", "diagram", "overflow")}
    stats = "".join(f"<li>{html.escape(k)}: {html.escape(str(v))}</li>" for k, v in summary.items())
    (OUT / "index.html").write_text(f"""<!doctype html>
<meta charset="utf-8"><title>Bourbaki page review</title>
<style>
body {{ font: 14px system-ui, sans-serif; margin: 16px; background: #fff; color: #111; }}
table {{ border-collapse: collapse; }}
td, th {{ border-bottom: 1px solid #ddd; padding: 8px; vertical-align: top; }}
th {{ text-align: left; position: sticky; top: 0; background: #fff; z-index: 1; }}
img {{ width: 30vw; max-width: 540px; height: auto; display: block; border: 1px solid #eee; }}
.meta {{ white-space: nowrap; font-size: 12px; color: #444; }}
.tag {{ font-weight: 600; padding: 0 4px; border-radius: 3px; }}
.tag.ok {{ background: #dfd; }} .tag.lines {{ background: #ffd; }}
.tag.diagram {{ background: #fdd; }} .tag.overflow {{ background: #fcc; }}
.bar button {{ margin-right: 6px; }}
</style>
<h1>Bourbaki 1970 vintage: original vs rebuild, page by page</h1>
<p>Overlay: red only in the original, cyan only in ours, black in both. Our page is aligned on the first body line.
Diagram details: <a href="../diagram_review/index.html">diagram review</a>.</p>
<ul>{stats}</ul>
<p>Flags: ok {counts['ok']}, line count off by 2+ {counts['lines']}, diagram moved over 6pt {counts['diagram']},
page overflows {counts['overflow']}.</p>
<p class="bar">Show: <button data-f="all">all</button><button data-f="ok">ok</button><button data-f="lines">lines</button>
<button data-f="diagram">diagram</button><button data-f="overflow">overflow</button>
<button id="sort">worst overlap first</button></p>
<table id="t"><thead><tr><th></th><th>Original scan</th><th>Rebuild</th><th>Overlay</th></tr></thead>
<tbody>{''.join(items)}</tbody></table>
<script>
const body = document.querySelector('#t tbody');
document.querySelectorAll('[data-f]').forEach(b => b.onclick = () => {{
  for (const tr of body.rows) tr.hidden = b.dataset.f !== 'all' && !tr.classList.contains(b.dataset.f);
}});
let worst = false;
document.getElementById('sort').onclick = e => {{
  worst = !worst;
  e.target.textContent = worst ? 'page order' : 'worst overlap first';
  const key = worst ? r => +r.dataset.overlap : r => +r.dataset.page;
  [...body.rows].sort((a, b) => key(a) - key(b)).forEach(r => body.appendChild(r));
}};
</script>
""", encoding="utf-8")
    print(f"wrote {OUT / 'index.html'}", flush=True)


if __name__ == "__main__":
    main()
