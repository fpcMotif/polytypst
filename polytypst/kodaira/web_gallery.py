import json
import re
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from .figures_ch1 import (
    CHAPTER_FIG_TITLES as CH1_TITLES,
)
from .figures_ch1 import (
    CHAPTER_SVG_GENERATORS as CH1_GENS,
)
from .figures_ch2a import (
    CHAPTER_FIG_TITLES as CH2A_TITLES,
)
from .figures_ch2a import (
    CHAPTER_SVG_GENERATORS as CH2A_GENS,
)
from .figures_ch2b import (
    CHAPTER_FIG_TITLES as CH2B_TITLES,
)
from .figures_ch2b import (
    CHAPTER_SVG_GENERATORS as CH2B_GENS,
)
from .figures_ch3 import (
    CHAPTER_FIG_TITLES as CH3_TITLES,
)
from .figures_ch3 import (
    CHAPTER_SVG_GENERATORS as CH3_GENS,
)
from .figures_ch4 import (
    CHAPTER_FIG_TITLES as CH4_TITLES,
)
from .figures_ch4 import (
    CHAPTER_SVG_GENERATORS as CH4_GENS,
)
from .figures_ch5 import (
    CHAPTER_FIG_TITLES as CH5_TITLES,
)
from .figures_ch5 import (
    CHAPTER_SVG_GENERATORS as CH5_GENS,
)

KODAIRA_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    **CH1_GENS,
    **CH2A_GENS,
    **CH2B_GENS,
    **CH3_GENS,
    **CH4_GENS,
    **CH5_GENS,
}

KODAIRA_FIG_TITLES: dict[str, str] = {
    **CH1_TITLES,
    **CH2A_TITLES,
    **CH2B_TITLES,
    **CH3_TITLES,
    **CH4_TITLES,
    **CH5_TITLES,
}

CHAPTER_NAMES: dict[int, str] = {
    1: "Holomorphic Functions",
    2: "Cauchy's Theorem & Cellular Decomposition",
    3: "Conformal Mappings & Riemann Sphere",
    4: "Analytic Continuation",
    5: "Riemann's Mapping Theorem",
}


@dataclass(frozen=True)
class KodairaFigureEntry:
    fig_id: str
    label: str
    filename: str
    chapter: int
    chapter_title: str
    title: str
    viewbox: str
    layers: list[str]


def _sort_key(fid: str) -> list[int]:
    return [int(x) for x in fid.split("_") if x.isdigit()]


def generate_all_kodaira_figures(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    fig_dir = out_dir / "figures"
    raw_dir = out_dir / "figures_raw"
    web_dir = out_dir / "web_figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)

    for png_file in sorted(fig_dir.glob("fig_*.png")):
        dest_raw = raw_dir / png_file.name
        if not dest_raw.exists():
            _ = shutil.copy2(png_file, dest_raw)

    entries: list[KodairaFigureEntry] = []
    cards_html: list[str] = []

    for fid in sorted(KODAIRA_SVG_GENERATORS.keys(), key=_sort_key):
        fn = KODAIRA_SVG_GENERATORS[fid]
        svg_code = fn()
        fname = f"fig_{fid}.svg"
        _ = (fig_dir / fname).write_text(svg_code, encoding="utf-8")
        _ = (web_dir / fname).write_text(svg_code, encoding="utf-8")

        ch = int(fid.split("_")[0])
        ch_title = CHAPTER_NAMES.get(ch, f"Chapter {ch}")
        label = f"Fig. {fid.replace('_', '.')}"
        title = KODAIRA_FIG_TITLES.get(fid, label)
        m_vb = re.search(r'viewBox="([^"]+)"', svg_code)
        vb = m_vb.group(1) if m_vb else "0 0 460 280"

        entry = KodairaFigureEntry(
            fig_id=fid,
            label=label,
            filename=fname,
            chapter=ch,
            chapter_title=ch_title,
            title=title,
            viewbox=vb,
            layers=["grid", "region", "curve", "label"],
        )
        entries.append(entry)

        search_key = f"{label} {title} {ch_title}".lower().replace('"', "")
        cards_html.append(
            f'<article class="fig-card" id="fig-{fid.replace("_", "-")}" data-chapter="{ch}" data-step="4" data-search="{search_key}">'
            f'<div class="card-head">'
            f'<div class="card-meta"><span class="fig-code">{label}</span><span class="badge">Ch {ch} · {ch_title}</span></div>'
            f'<div class="step-pills" role="group" aria-label="Progressive 2D layer steps">'
            f'<button type="button" class="pill" onclick="setCardStep(this, 1)" title="Step 1: Axes & Frame">1</button>'
            f'<button type="button" class="pill" onclick="setCardStep(this, 2)" title="Step 2: + Domains & Regions">2</button>'
            f'<button type="button" class="pill" onclick="setCardStep(this, 3)" title="Step 3: + Curves & Contours">3</button>'
            f'<button type="button" class="pill active" onclick="setCardStep(this, 4)" title="Step 4: + Points & Labels">4</button>'
            f"</div>"
            f"</div>"
            f'<div class="stage-wrap">'
            f'<div class="svg-stage">{svg_code}</div>'
            f'<div class="raw-stage"><img src="../figures_raw/fig_{fid}.png" alt="Original scan {label}" loading="lazy" /><span>Original 2007 Raster Scan</span></div>'
            f"</div>"
            f'<p class="fig-title">{title}</p>'
            f"</article>"
        )

    _ = (web_dir / "manifest.json").write_text(
        json.dumps([asdict(e) for e in entries], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    html = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        "  <title>Kodaira Complex Analysis — 2D Vector Atlas & Progressive Educational Renderer</title>\n"
        "  <style>\n"
        "    :root {\n"
        "      --bg: #f8fafc;\n"
        "      --card: #ffffff;\n"
        "      --ink: #0f172a;\n"
        "      --muted: #475569;\n"
        "      --border: #e2e8f0;\n"
        "      --stage: #ffffff;\n"
        "      --accent: #1e3a8a;\n"
        "      --badge-bg: #dbeafe;\n"
        "      --badge-fg: #1e3a8a;\n"
        "    }\n"
        '    [data-theme="parchment"] {\n'
        "      --bg: #f5f0e6;\n"
        "      --card: #fdfaf3;\n"
        "      --ink: #1c1917;\n"
        "      --muted: #57534e;\n"
        "      --border: #e5dec9;\n"
        "      --stage: #fbf7ee;\n"
        "      --accent: #7c2d12;\n"
        "      --badge-bg: #fef3c7;\n"
        "      --badge-fg: #92400e;\n"
        "    }\n"
        '    [data-theme="3b1b"] {\n'
        "      --bg: #070b14;\n"
        "      --card: #0f172a;\n"
        "      --ink: #f8fafc;\n"
        "      --muted: #94a3b8;\n"
        "      --border: #1e293b;\n"
        "      --stage: #090d16;\n"
        "      --accent: #38bdf8;\n"
        "      --badge-bg: rgba(56, 189, 248, 0.16);\n"
        "      --badge-fg: #7dd3fc;\n"
        "    }\n"
        '    [data-theme="3b1b"] svg .canvas-bg { fill: #090d16 !important; }\n'
        '    [data-theme="3b1b"] svg #grid-fine path { stroke: #1e293b !important; }\n'
        '    [data-theme="3b1b"] svg .ax { stroke: #64748b !important; }\n'
        '    [data-theme="3b1b"] svg .c-main { stroke: #e2e8f0 !important; }\n'
        '    [data-theme="3b1b"] svg .c-blue, [data-theme="3b1b"] svg .c-blue-dash { stroke: #38bdf8 !important; }\n'
        '    [data-theme="3b1b"] svg .c-red, [data-theme="3b1b"] svg .c-red-dash { stroke: #fb7185 !important; }\n'
        '    [data-theme="3b1b"] svg .c-green, [data-theme="3b1b"] svg .c-green-dash { stroke: #34d399 !important; }\n'
        '    [data-theme="3b1b"] svg .c-amber { stroke: #facc15 !important; }\n'
        '    [data-theme="3b1b"] svg .c-dash, [data-theme="3b1b"] svg .c-sub { stroke: #64748b !important; }\n'
        '    [data-theme="3b1b"] svg .f-blue { fill: rgba(56, 189, 248, 0.16) !important; }\n'
        '    [data-theme="3b1b"] svg .f-amber { fill: rgba(250, 204, 21, 0.15) !important; }\n'
        '    [data-theme="3b1b"] svg .f-green { fill: rgba(52, 211, 153, 0.15) !important; }\n'
        '    [data-theme="3b1b"] svg .f-rose { fill: rgba(251, 113, 133, 0.15) !important; }\n'
        '    [data-theme="3b1b"] svg #stipple circle { fill: #38bdf8 !important; opacity: 0.45 !important; }\n'
        '    [data-theme="3b1b"] svg #hatch line { stroke: #38bdf8 !important; opacity: 0.4 !important; }\n'
        '    [data-theme="3b1b"] svg #arr path { fill: #e2e8f0 !important; }\n'
        '    [data-theme="3b1b"] svg #arr-axis path { fill: #94a3b8 !important; }\n'
        '    [data-theme="3b1b"] svg #arr-blue path { fill: #38bdf8 !important; }\n'
        '    [data-theme="3b1b"] svg #arr-red path { fill: #fb7185 !important; }\n'
        '    [data-theme="3b1b"] svg #arr-green path { fill: #34d399 !important; }\n'
        '    [data-theme="3b1b"] svg #arr-amber path { fill: #facc15 !important; }\n'
        '    [data-theme="3b1b"] svg .pt { stroke: #090d16 !important; }\n'
        '    [data-theme="3b1b"] svg .pt-open { fill: #090d16 !important; }\n'
        '    [data-theme="3b1b"] svg .lbl, [data-theme="3b1b"] svg .it {\n'
        "      fill: #f8fafc !important;\n"
        "      stroke: #090d16 !important;\n"
        "    }\n"
        '    [data-theme="3b1b"] svg .lbl[fill="#1e3a8a"], [data-theme="3b1b"] svg .it[fill="#1e3a8a"] { fill: #38bdf8 !important; }\n'
        '    [data-theme="3b1b"] svg .lbl[fill="#dc2626"], [data-theme="3b1b"] svg .it[fill="#dc2626"] { fill: #fb7185 !important; }\n'
        '    [data-theme="3b1b"] svg .lbl[fill="#047857"], [data-theme="3b1b"] svg .it[fill="#047857"] { fill: #34d399 !important; }\n'
        '    [data-theme="3b1b"] svg .lbl[fill="#b45309"], [data-theme="3b1b"] svg .it[fill="#b45309"] { fill: #facc15 !important; }\n'
        '    [data-grid="off"] svg .canvas-grid { display: none; }\n'
        "    svg .layer-grid, svg .layer-region, svg .layer-curve, svg .layer-label { transition: opacity 0.22s ease; }\n"
        '    .fig-card[data-step="1"] svg .layer-region,\n'
        '    .fig-card[data-step="1"] svg .layer-curve,\n'
        '    .fig-card[data-step="1"] svg .layer-label { opacity: 0.06; }\n'
        '    .fig-card[data-step="2"] svg .layer-curve,\n'
        '    .fig-card[data-step="2"] svg .layer-label { opacity: 0.06; }\n'
        '    .fig-card[data-step="3"] svg .layer-label { opacity: 0.06; }\n'
        '    body { margin: 0; font-family: "New Computer Modern", "Charter", Georgia, serif; background: var(--bg); color: var(--ink); }\n'
        "    header { position: sticky; top: 0; z-index: 20; backdrop-filter: blur(12px); background: color-mix(in srgb, var(--bg) 88%, transparent); border-bottom: 1px solid var(--border); padding: 18px 24px; }\n"
        "    .header-inner { max-width: 1440px; margin: 0 auto; display: flex; flex-direction: column; gap: 12px; }\n"
        "    .top-row { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; }\n"
        "    h1 { margin: 0; font-size: 1.45rem; font-weight: 700; }\n"
        "    .sub { margin: 2px 0 0; color: var(--muted); font-size: 0.9rem; font-family: system-ui, sans-serif; }\n"
        "    .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between; font-family: system-ui, sans-serif; }\n"
        "    .btn-group { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }\n"
        "    button, input[type='search'] { background: var(--card); color: var(--ink); border: 1px solid var(--border); padding: 6px 11px; border-radius: 6px; font-size: 0.8rem; font-family: system-ui, sans-serif; }\n"
        "    button { cursor: pointer; font-weight: 500; }\n"
        "    button.active { background: var(--accent); color: #ffffff; border-color: var(--accent); }\n"
        '    [data-theme="3b1b"] button.active { color: #070b14; font-weight: 700; }\n'
        "    input[type='search'] { min-width: 210px; }\n"
        "    .grid { max-width: 1440px; margin: 0 auto; padding: 24px; display: grid; grid-template-columns: repeat(auto-fill, minmax(390px, 1fr)); gap: 20px; }\n"
        "    .fig-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 1px 3px rgba(15,23,42,0.05); }\n"
        "    .card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-family: system-ui, sans-serif; font-size: 0.76rem; }\n"
        "    .card-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }\n"
        "    .fig-code { font-weight: 700; letter-spacing: 0.03em; color: var(--ink); font-size: 0.84rem; }\n"
        "    .badge { padding: 2px 8px; border-radius: 999px; font-weight: 600; background: var(--badge-bg); color: var(--badge-fg); }\n"
        "    .step-pills { display: flex; gap: 3px; }\n"
        "    .pill { padding: 2px 7px; font-size: 0.72rem; border-radius: 4px; }\n"
        "    .stage-wrap { display: grid; grid-template-columns: 1fr; gap: 10px; }\n"
        '    body[data-compare="on"] .stage-wrap { grid-template-columns: 1fr 1fr; }\n'
        "    .svg-stage { background: var(--stage); border: 1px solid var(--border); border-radius: 8px; padding: 8px; min-height: 225px; display: flex; align-items: center; justify-content: center; }\n"
        "    .raw-stage { display: none; background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 8px; flex-direction: column; align-items: center; justify-content: center; gap: 6px; }\n"
        '    body[data-compare="on"] .raw-stage { display: flex; }\n'
        "    .raw-stage img { max-width: 100%; max-height: 210px; object-fit: contain; }\n"
        "    .raw-stage span { font-family: system-ui, sans-serif; font-size: 0.7rem; color: #64748b; }\n"
        "    .fig-title { margin: 0; font-size: 0.95rem; color: var(--ink); text-align: center; }\n"
        "  </style>\n"
        "</head>\n"
        '<body data-theme="textbook" data-grid="on" data-compare="off">\n'
        "  <header>\n"
        '    <div class="header-inner">\n'
        '      <div class="top-row">\n'
        "        <div>\n"
        f"          <h1>Kunihiko Kodaira · Complex Analysis — 2D Vector Figure Atlas ({len(entries)} SVGs)</h1>\n"
        '          <p class="sub">Parametric Code-Reproduced 2D Illustrations · Textbook Monograph &amp; Progressive 3Blue1Brown Web Renderer</p>\n'
        "        </div>\n"
        '        <div class="btn-group" id="theme-group">\n'
        '          <button type="button" class="active" onclick="setTheme(\'textbook\', this)">Textbook Classic</button>\n'
        '          <button type="button" onclick="setTheme(\'3b1b\', this)">3Blue1Brown 2D</button>\n'
        '          <button type="button" onclick="setTheme(\'parchment\', this)">Warm Parchment</button>\n'
        '          <button type="button" onclick="toggleGrid(this)">Grid: ON</button>\n'
        '          <button type="button" onclick="toggleCompare(this)">Compare Scan</button>\n'
        "        </div>\n"
        "      </div>\n"
        '      <div class="toolbar">\n'
        '        <div class="btn-group" id="ch-group">\n'
        f'          <button type="button" class="active" onclick="filterCh(0, this)">All ({len(entries)})</button>\n'
        '          <button type="button" onclick="filterCh(1, this)">Ch 1 · Holomorphic (23)</button>\n'
        '          <button type="button" onclick="filterCh(2, this)">Ch 2 · Cauchy (38)</button>\n'
        '          <button type="button" onclick="filterCh(3, this)">Ch 3 · Conformal (15)</button>\n'
        '          <button type="button" onclick="filterCh(4, this)">Ch 4 · Continuation (21)</button>\n'
        '          <button type="button" onclick="filterCh(5, this)">Ch 5 · Riemann Mapping (19)</button>\n'
        "        </div>\n"
        '        <div class="btn-group" id="global-step-group">\n'
        '          <span style="font-size:0.78rem;color:var(--muted);">Progressive 2D Build:</span>\n'
        '          <button type="button" onclick="setAllSteps(1, this)">1 · Frame</button>\n'
        '          <button type="button" onclick="setAllSteps(2, this)">2 · Domains</button>\n'
        '          <button type="button" onclick="setAllSteps(3, this)">3 · Contours</button>\n'
        '          <button type="button" class="active" onclick="setAllSteps(4, this)">4 · Complete</button>\n'
        '          <input type="search" id="fig-search" placeholder="Search Fig. 2.27, cellular, sphere..." oninput="applyFilters()" />\n'
        "        </div>\n"
        "      </div>\n"
        "    </div>\n"
        "  </header>\n"
        f'  <main class="grid" id="fig-grid">\n    {"".join(cards_html)}\n  </main>\n'
        "  <script>\n"
        "    let currentCh = 0;\n"
        "    function setTheme(t, btn) {\n"
        "      document.body.dataset.theme = t;\n"
        "      for (const b of btn.parentElement.querySelectorAll('button')) {\n"
        "        if (b.textContent.includes('Textbook') || b.textContent.includes('3Blue1Brown') || b.textContent.includes('Parchment')) b.classList.remove('active');\n"
        "      }\n"
        "      btn.classList.add('active');\n"
        "    }\n"
        "    function toggleGrid(btn) {\n"
        "      const next = document.body.dataset.grid === 'on' ? 'off' : 'on';\n"
        "      document.body.dataset.grid = next;\n"
        "      btn.textContent = 'Grid: ' + next.toUpperCase();\n"
        "    }\n"
        "    function toggleCompare(btn) {\n"
        "      const next = document.body.dataset.compare === 'on' ? 'off' : 'on';\n"
        "      document.body.dataset.compare = next;\n"
        "      btn.classList.toggle('active', next === 'on');\n"
        "    }\n"
        "    function setCardStep(btn, step) {\n"
        "      const card = btn.closest('.fig-card');\n"
        "      card.dataset.step = String(step);\n"
        "      for (const p of card.querySelectorAll('.pill')) p.classList.remove('active');\n"
        "      btn.classList.add('active');\n"
        "    }\n"
        "    function setAllSteps(step, btn) {\n"
        "      for (const b of document.querySelectorAll('#global-step-group button')) b.classList.remove('active');\n"
        "      btn.classList.add('active');\n"
        "      for (const card of document.querySelectorAll('.fig-card')) {\n"
        "        card.dataset.step = String(step);\n"
        "        const pills = card.querySelectorAll('.pill');\n"
        "        pills.forEach((p, idx) => p.classList.toggle('active', idx + 1 === step));\n"
        "      }\n"
        "    }\n"
        "    function filterCh(ch, btn) {\n"
        "      currentCh = ch;\n"
        "      for (const b of document.querySelectorAll('#ch-group button')) b.classList.remove('active');\n"
        "      btn.classList.add('active');\n"
        "      applyFilters();\n"
        "    }\n"
        "    function applyFilters() {\n"
        "      const q = document.getElementById('fig-search').value.trim().toLowerCase();\n"
        "      for (const card of document.querySelectorAll('.fig-card')) {\n"
        "        const chOk = currentCh === 0 || Number(card.dataset.chapter) === currentCh;\n"
        "        const qOk = !q || card.dataset.search.includes(q);\n"
        "        card.style.display = (chOk && qOk) ? '' : 'none';\n"
        "      }\n"
        "    }\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )
    index_path = web_dir / "index.html"
    _ = index_path.write_text(html, encoding="utf-8")
    return index_path
