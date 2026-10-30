from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path

from scripts.book2_figures.engine import (
    ThemeMode,
    chart_svg,
    save_figure_outputs,
    scan_canvas,
)

CHAPTER_COUNTS: list[tuple[int, int]] = [
    (1, 2),
    (2, 6),
    (3, 15),
    (4, 7),
    (5, 6),
    (6, 12),
    (7, 6),
    (8, 22),
    (9, 7),
    (10, 6),
    (11, 28),
    (12, 13),
]

CHAPTER_TITLES: dict[int, str] = {
    1: "第1章 日本的通货紧缩与货币政策",
    2: "第2章 全球化与通货膨胀",
    3: "第3章 零利率与量化宽松政策",
    4: "第4章 通货紧缩与货币政策",
    5: "第5章 货币数量论与通货紧缩",
    6: "第6章 资产价格波动、资产负债表调整与通货紧缩",
    7: "第7章 量化宽松政策与银行行为",
    8: "第8章 量化宽松政策的效果：实证分析",
    9: "第9章 通货膨胀预期与实际利率",
    10: "第10章 价格粘性与通货紧缩动态",
    11: "第11章 美联储预防通货紧缩的政策经验",
    12: "第12章 日本通货紧缩的教训与展望",
}


PAGE_PARTS = ("8-20-a", "8-20-b")


def expected_figure_ids() -> list[str]:
    return [f"{ch}-{i}" for ch, cnt in CHAPTER_COUNTS for i in range(1, cnt + 1)]


def load_all_generators() -> dict[str, Callable[[ThemeMode], str]]:
    from scripts.book2_figures import ch1_3, ch4_6, ch7_8, ch9_10, ch11, ch12

    merged: dict[str, Callable[[ThemeMode], str]] = {}
    for mod in (ch1_3, ch4_6, ch7_8, ch9_10, ch11, ch12):
        merged.update(mod.get_generators())
    return merged


def extract_svg_title(svg_text: str, fig_id: str) -> str:
    m = re.search(r"<(?:title|text[^>]*)>(图\s*" + re.escape(fig_id) + r"[^<]*)</(?:title|text)>", svg_text)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"<text[^>]*>([^<]+)</text>", svg_text)
    return m2.group(1).strip() if m2 else f"图 {fig_id}"


def build_web_gallery(book_dir: Path, titles: dict[str, str], pages: dict[str, int]) -> Path:
    web_dir = book_dir / "web_figures"
    web_dir.mkdir(parents=True, exist_ok=True)
    fids = expected_figure_ids()

    cards_html: list[str] = []
    for fid in fids:
        ch = int(fid.split("-")[0])
        title = titles.get(fid, f"图 {fid}")
        pnum = pages.get(fid, 0)
        page_badge = f"Scan p.{pnum}" if pnum else "Scan ref"
        cards_html.append(
            f"""
            <article class="fig-card" data-ch="{ch}" data-id="{fid}" data-title="{escape(title.lower())}">
              <header class="card-head">
                <div>
                  <span class="badge-id">图 {fid}</span>
                  <span class="badge-ch">Ch {ch} · {page_badge}</span>
                </div>
                <button class="btn-compare" onclick="toggleCompare(this)">对比原书扫描 (Compare Scan)</button>
              </header>
              <h3 class="card-title">{escape(title)}</h3>
              <div class="stage-grid">
                <div class="replica-pane">
                  <div class="pane-label">Vector Replication (<span class="mode-tag">3Blue1Brown Colorful</span>)</div>
                  <img class="img-replica" data-fid="{fid}" src="../figures_color/fig_{fid}.svg" alt="{escape(title)}" loading="lazy"/>
                  <div class="asset-links">
                    <a href="../figures_mono/fig_{fid}.svg" target="_blank">Mono SVG</a>
                    <a href="../figures_mono/fig_{fid}.png" target="_blank">Mono PNG</a>
                    <a href="../figures_color/fig_{fid}.svg" target="_blank">3B1B Color SVG</a>
                    <a href="../figures_color/fig_{fid}.png" target="_blank">3B1B Color PNG</a>
                    <a href="../figures_3b1b_dark/fig_{fid}.svg" target="_blank">3B1B Dark SVG</a>
                  </div>
                </div>
                <div class="scan-pane">
                  <div class="pane-label">Original Scan Crop ({page_badge})</div>
                  <img class="img-scan" src="../figures_raw/fig_{fid}.png" alt="Original scan {fid}" loading="lazy"/>
                </div>
              </div>
            </article>
            """
        )

    ch_buttons = ['<button class="ch-pill active" onclick="filterCh(0, this)">全部 (130)</button>']
    for ch, cnt in CHAPTER_COUNTS:
        ch_buttons.append(
            f'<button class="ch-pill" onclick="filterCh({ch}, this)">第{ch}章 ({cnt})</button>'
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>《通缩经济与货币政策》全书 130 幅图表：单色学术版 &amp; 3Blue1Brown 彩色版</title>
<style>
  :root {{
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #0f172a;
    --muted: #475569;
    --border: #cbd5e1;
    --accent: #2563eb;
    --accent-soft: #dbeafe;
  }}
  body.theme-dark {{
    --bg: #070a12;
    --card: #0f1624;
    --text: #f8fafc;
    --muted: #94a3b8;
    --border: #1e293b;
    --accent: #38bdf8;
    --accent-soft: #0c4a6e;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: "PingFang SC", "STIX Two Text", -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.5;
  }}
  .topbar {{
    position: sticky;
    top: 0;
    z-index: 50;
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
  }}
  .topbar-row {{
    max-width: 1480px;
    margin: 0 auto;
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    align-items: center;
    justify-content: space-between;
  }}
  .brand h1 {{
    margin: 0;
    font-size: 19px;
    font-weight: 700;
  }}
  .brand p {{
    margin: 2px 0 0;
    font-size: 12.5px;
    color: var(--muted);
  }}
  .controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }}
  .mode-btn, .action-btn {{
    padding: 7px 13px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }}
  .mode-btn.active {{
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }}
  .search-input {{
    padding: 7px 11px;
    border-radius: 7px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
    font-size: 13px;
    width: 200px;
  }}
  .ch-bar {{
    max-width: 1480px;
    margin: 10px auto 0;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }}
  .ch-pill {{
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--muted);
    font-size: 12px;
    cursor: pointer;
  }}
  .ch-pill.active {{
    background: var(--accent-soft);
    color: var(--accent);
    border-color: var(--accent);
    font-weight: 600;
  }}
  .gallery {{
    max-width: 1480px;
    margin: 22px auto 60px;
    padding: 0 20px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(640px, 1fr));
    gap: 20px;
  }}
  body.compare-all .gallery {{
    grid-template-columns: 1fr;
  }}
  .fig-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .card-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .badge-id {{
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 700;
    font-size: 12.5px;
    padding: 2px 8px;
    border-radius: 5px;
    margin-right: 6px;
  }}
  .badge-ch {{
    color: var(--muted);
    font-size: 12px;
  }}
  .card-title {{
    margin: 0;
    font-size: 15px;
    font-weight: 600;
  }}
  .btn-compare {{
    font-size: 11.5px;
    padding: 4px 9px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--muted);
    cursor: pointer;
  }}
  .stage-grid {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 14px;
    align-items: start;
  }}
  .fig-card.comparing .stage-grid,
  body.compare-all .stage-grid {{
    grid-template-columns: 1fr 1fr;
  }}
  .scan-pane {{
    display: none;
  }}
  .fig-card.comparing .scan-pane,
  body.compare-all .scan-pane {{
    display: block;
  }}
  .pane-label {{
    font-size: 11.5px;
    color: var(--muted);
    margin-bottom: 6px;
    font-weight: 500;
  }}
  .img-replica, .img-scan {{
    width: 100%;
    height: auto;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: #fff;
    display: block;
  }}
  .asset-links {{
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 11.5px;
  }}
  .asset-links a {{
    color: var(--accent);
    text-decoration: none;
  }}
  .asset-links a:hover {{
    text-decoration: underline;
  }}
</style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-row">
      <div class="brand">
        <h1>《通缩经济与货币政策》全书 130 幅图表矢量重绘库</h1>
        <p>Monochrome Publication Edition &amp; 3Blue1Brown Colorful / Dark Vector Editions (SVG + 300-DPI PNG)</p>
      </div>
      <div class="controls">
        <button class="mode-btn active" onclick="setMode('color', this)">3Blue1Brown 彩色版 (Light)</button>
        <button class="mode-btn" onclick="setMode('dark', this)">3Blue1Brown 暗色版 (Dark)</button>
        <button class="mode-btn" onclick="setMode('mono', this)">学术黑白版 (Monochrome)</button>
        <button class="action-btn" onclick="toggleCompareAll(this)">全图并排对比原书扫描</button>
        <input class="search-input" type="search" placeholder="搜索图号或标题 (如 8-3, 泰勒)..." oninput="filterSearch(this.value)"/>
      </div>
    </div>
    <div class="ch-bar">
      {"".join(ch_buttons)}
    </div>
  </header>
  <main class="gallery" id="gallery">
    {"".join(cards_html)}
  </main>
<script>
  let currentCh = 0;
  let currentQuery = "";
  const folderMap = {{
    color: "../figures_color",
    dark: "../figures_3b1b_dark",
    mono: "../figures_mono"
  }};
  const labelMap = {{
    color: "3Blue1Brown Colorful",
    dark: "3Blue1Brown Dark Canvas",
    mono: "Monochrome Publication"
  }};
  function setMode(mode, btn) {{
    document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    document.body.classList.toggle("theme-dark", mode === "dark");
    const folder = folderMap[mode];
    document.querySelectorAll(".img-replica").forEach(img => {{
      const fid = img.getAttribute("data-fid");
      img.src = `${{folder}}/fig_${{fid}}.svg`;
    }});
    document.querySelectorAll(".mode-tag").forEach(el => {{
      el.textContent = labelMap[mode];
    }});
  }}
  function toggleCompare(btn) {{
    btn.closest(".fig-card").classList.toggle("comparing");
  }}
  function toggleCompareAll(btn) {{
    document.body.classList.toggle("compare-all");
    btn.textContent = document.body.classList.contains("compare-all")
      ? "退出全图并排对比"
      : "全图并排对比原书扫描";
  }}
  function applyFilters() {{
    document.querySelectorAll(".fig-card").forEach(card => {{
      const ch = parseInt(card.getAttribute("data-ch"), 10);
      const id = card.getAttribute("data-id");
      const title = card.getAttribute("data-title");
      const matchCh = currentCh === 0 || ch === currentCh;
      const matchQ = !currentQuery || id.includes(currentQuery) || title.includes(currentQuery);
      card.style.display = (matchCh && matchQ) ? "" : "none";
    }});
  }}
  function filterCh(ch, btn) {{
    currentCh = ch;
    document.querySelectorAll(".ch-pill").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    applyFilters();
  }}
  function filterSearch(q) {{
    currentQuery = q.trim().toLowerCase();
    applyFilters();
  }}
</script>
</body>
</html>
"""
    index_path = web_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


def build_typst_showcases(book_dir: Path, titles: dict[str, str]) -> list[Path]:
    fids = expected_figure_ids()
    editions = [
        ("figures_monochrome", "figures_mono", "《通缩经济与货币政策》图表全集（学术单色版 · Monochrome Edition）", "#0f172a"),
        ("figures_color_3b1b", "figures_color", "《通缩经济与货币政策》图表全集（3Blue1Brown 彩色版 · Colorful Edition）", "#1d4ed8"),
    ]
    built_pdfs: list[Path] = []
    for stem, folder, doc_title, accent in editions:
        lines: list[str] = [
            '#set page(paper: "a4", margin: (x: 18mm, y: 18mm), numbering: "1")',
            '#set text(font: ("Songti SC", "STIX Two Text", "PingFang SC"), size: 10.5pt, lang: "zh")',
            "#align(center)[",
            f'  #text(size: 18pt, weight: "bold", fill: rgb("{accent}"))[{doc_title}]',
            "  #v(4pt)",
            '  #text(size: 10.5pt, fill: rgb("#475569"))[全书 1–12 章共 130 幅矢量重绘图表（图 1-1 至 图 12-13）]',
            "]",
            "#v(10pt)",
        ]
        cur_ch = 0
        for fid in fids:
            ch = int(fid.split("-")[0])
            if ch != cur_ch:
                cur_ch = ch
                ch_name = CHAPTER_TITLES.get(ch, f"第{ch}章")
                lines.append(f"== {ch_name}")
            t = titles.get(fid, f"图 {fid}").replace("[", "(").replace("]", ")").replace("#", "")
            lines.append(
                f'#figure(\n  image("{folder}/fig_{fid}.svg", width: 92%),\n  caption: [{t}],\n  supplement: none,\n)'
            )
            lines.append("#v(6pt)")

        typ_path = book_dir / f"{stem}.typ"
        pdf_path = book_dir / f"{stem}.pdf"
        typ_path.write_text("\n".join(lines), encoding="utf-8")
        subprocess.run(
            ["mise", "exec", "--", "typst", "compile", str(typ_path), str(pdf_path)],
            check=True,
        )
        built_pdfs.append(pdf_path)
    return built_pdfs


def main() -> None:
    parser = argparse.ArgumentParser(description="Redraw book 2's chart figures in monochrome, color and dark SVGs.")
    parser.add_argument("--style", choices=("a", "b"), default="a", help="a: the redraw style; b: the scan's chart style in the body fonts")
    args = parser.parse_args()
    book_dir = Path("output/2 通缩经济与货币政策")
    fids = expected_figure_ids()
    generators = load_all_generators()

    missing = [fid for fid in fids if fid not in generators]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} figure generators: {missing}")

    manifest_path = book_dir / "figures_manifest.json"
    pages: dict[str, int] = {"6-12": 190, "8-7": 237}
    if manifest_path.exists():
        for item in json.loads(manifest_path.read_text(encoding="utf-8")):
            pages[item["figure_id"]] = int(item.get("source_page", 0))

    titles: dict[str, str] = {}

    def _render_one(fid: str) -> tuple[str, str]:
        fn = generators[fid]
        with scan_canvas(book_dir, fid):
            svgs: dict[ThemeMode, str] = {
                "mono": chart_svg(fn, args.style),
                "color": fn("color"),
                "dark": fn("dark"),
            }
        save_figure_outputs(fid, svgs, book_dir=book_dir, dpi=300)
        return fid, extract_svg_title(svgs["color"], fid)

    with ThreadPoolExecutor(max_workers=8) as pool:
        for fid, title in pool.map(_render_one, fids):
            titles[fid] = title
        list(pool.map(_render_one, PAGE_PARTS))

    gallery_path = build_web_gallery(book_dir, titles, pages)
    pdfs = build_typst_showcases(book_dir, titles)
    print(f"Rendered {len(fids)} figures across 4 directories.")
    print(f"Web gallery: {gallery_path}")
    print(f"Showcase PDFs: {[str(p) for p in pdfs]}")


if __name__ == "__main__":
    main()
