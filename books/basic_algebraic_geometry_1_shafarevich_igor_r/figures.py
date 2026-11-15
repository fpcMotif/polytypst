import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

import pymupdf

from polytypst.parity.source import source_pdf
from polytypst.vision.diagram_engine import FigureBook, FigureSpec, render_figures
from polytypst.vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    write_figures_manifest,
)

from .figures_ch1 import CHAPTER_FIG_TITLES as CH1_TITLES
from .figures_ch1 import CHAPTER_SVG_GENERATORS as CH1_GENS
from .figures_ch2 import CHAPTER_FIG_TITLES as CH2_TITLES
from .figures_ch2 import CHAPTER_SVG_GENERATORS as CH2_GENS
from .figures_ch3 import CHAPTER_FIG_TITLES as CH3_TITLES
from .figures_ch3 import CHAPTER_SVG_GENERATORS as CH3_GENS
from .figures_ch4 import CHAPTER_FIG_TITLES as CH4_TITLES
from .figures_ch4 import CHAPTER_SVG_GENERATORS as CH4_GENS

FOLDER = Path(__file__).parent
REPO_FONTS = FOLDER.parent.parent / "fonts"

_FIGURES: tuple[tuple[str, int, int, int, str], ...] = (
    ("1", 22, 0, 1, "Figure 1 Intersections of conics"),
    ("2", 23, 0, 1, "Figure 2 The polar line of a point with respect to a conic"),
    ("3", 24, 0, 1, "Figure 3 Projection of a cubic"),
    ("4", 25, 0, 1, "Figure 4 Projection of a conic"),
    ("5", 31, 0, 1, "Figure 5 A cusp"),
    ("6", 39, 0, 1, "Figure 6 Pascal's theorem"),
    ("7", 115, 0, 2, "Figure 7 Transversal curves on a surface"),
    ("8", 126, 0, 2, "Figure 8 y^2 = x^3 - x over R"),
    ("9", 126, 1, 2, "Figure 9 y^2 = x^3 - x over C"),
    ("10", 131, 0, 2, "Figure 10 The blowup sigma: Pi -> P^2"),
    ("11", 149, 0, 2, "Figure 11 The Newton polygon"),
    ("12", 188, 0, 3, "Figure 12 Constructing functions on a plane cubic"),
    ("13", 190, 0, 3, "Figure 13 The group law on a plane cubic"),
    ("14", 190, 1, 3, "Figure 14 The inverse map gamma -> gamma_1"),
    ("15", 203, 0, 3, "Figure 15 The map f(x, y) = xy"),
    ("16", 270, 0, 4, "Figure 16 Curves on a quadric surface"),
    ("17", 272, 0, 4, "Figure 17 Lines on the cubic surface"),
    ("18", 285, 0, 4, "Figure 18 The standard quadratic transformation"),
    ("19", 288, 0, 4, "Figure 19 Resolutions of some curve singularities"),
    ("20", 291, 0, 4, "Figure 20 The Dynkin diagrams A_n, D_n, E_6, E_7 and E_8"),
    (
        "21",
        296,
        0,
        4,
        "Figure 21 The extended Dynkin diagrams A_n, D_n, E_6, E_7 and E_8",
    ),
)

SHAFAREVICH_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    **CH1_GENS,
    **CH2_GENS,
    **CH3_GENS,
    **CH4_GENS,
}

SHAFAREVICH_FIG_TITLES: dict[str, str] = {
    **CH1_TITLES,
    **CH2_TITLES,
    **CH3_TITLES,
    **CH4_TITLES,
}

SHAFAREVICH_FIGURE_BOOK = FigureBook(
    slug="basic_algebraic_geometry_1_shafarevich_igor_r",
    title="Igor R. Shafarevich · Basic Algebraic Geometry 1",
    subtitle="Parametric 3Blue1Brown Vector Illustrations · Varieties in Projective Space",
    figures=tuple(
        FigureSpec(
            fig_id=fid,
            label=f"Figure {fid}",
            chapter=chap,
            build=SHAFAREVICH_SVG_GENERATORS[fid],
            title=SHAFAREVICH_FIG_TITLES[fid],
        )
        for fid, _, _, chap, _ in _FIGURES
    ),
    chapter_titles={
        1: "Basic Notions",
        2: "Local Properties",
        3: "Divisors and Differential Forms",
        4: "Intersection Numbers",
    },
    scan_dir="../figures_raw",
    search_hint="Search Figure 13, cubic, blowup, Dynkin...",
)

_DARK_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        '<stop offset="0%" stop-color="#f8fafc" stop-opacity="0.5" />',
        '<stop offset="0%" stop-color="#090d16" stop-opacity="1.0" />',
    ),
    (
        '<stop offset="100%" stop-color="#f1f5f9" stop-opacity="0.3" />',
        '<stop offset="100%" stop-color="#0b1120" stop-opacity="1.0" />',
    ),
    (
        '<stop offset="0%" stop-color="#dbeafe" stop-opacity="0.78" />',
        '<stop offset="0%" stop-color="#38bdf8" stop-opacity="0.24" />',
    ),
    (
        '<stop offset="100%" stop-color="#bfdbfe" stop-opacity="0.48" />',
        '<stop offset="100%" stop-color="#0284c7" stop-opacity="0.12" />',
    ),
    (
        '<stop offset="0%" stop-color="#fef3c7" stop-opacity="0.82" />',
        '<stop offset="0%" stop-color="#facc15" stop-opacity="0.22" />',
    ),
    (
        '<stop offset="100%" stop-color="#fde68a" stop-opacity="0.52" />',
        '<stop offset="100%" stop-color="#ca8a04" stop-opacity="0.10" />',
    ),
    (
        '<stop offset="0%" stop-color="#d1fae5" stop-opacity="0.78" />',
        '<stop offset="0%" stop-color="#34d399" stop-opacity="0.22" />',
    ),
    (
        '<stop offset="100%" stop-color="#a7f3d0" stop-opacity="0.48" />',
        '<stop offset="100%" stop-color="#059669" stop-opacity="0.10" />',
    ),
    (
        '<stop offset="0%" stop-color="#ffe4e6" stop-opacity="0.78" />',
        '<stop offset="0%" stop-color="#fb7185" stop-opacity="0.22" />',
    ),
    (
        '<stop offset="100%" stop-color="#fecdd3" stop-opacity="0.48" />',
        '<stop offset="100%" stop-color="#e11d48" stop-opacity="0.10" />',
    ),
    (
        '<stop offset="0%" stop-color="#eff6ff" />\n      <stop offset="55%" stop-color="#bfdbfe" />\n      <stop offset="100%" stop-color="#93c5fd" />',
        '<stop offset="0%" stop-color="#1e3a5f" />\n      <stop offset="55%" stop-color="#0f2942" />\n      <stop offset="100%" stop-color="#081a2e" />',
    ),
    ('stroke="#e2e8f0" stroke-width="0.6"', 'stroke="#1e293b" stroke-width="0.65"'),
    (".pt { stroke: #ffffff;", ".pt { stroke: #090d16;"),
    (".pt-open { fill: #ffffff;", ".pt-open { fill: #090d16;"),
    (
        "fill: #0f172a; paint-order: stroke fill; stroke: #ffffff;",
        "fill: #f8fafc; paint-order: stroke fill; stroke: #090d16;",
    ),
    ('fill="#ffffff"', 'fill="#090d16"'),
    ("#0f172a", "#e2e8f0"),
    ("#1e3a8a", "#38bdf8"),
    ("#dc2626", "#fb7185"),
    ("#047857", "#34d399"),
    ("#b45309", "#facc15"),
    ("#475569", "#94a3b8"),
    ("#64748b", "#94a3b8"),
)


def _to_3b1b_dark_svg(svg: str) -> str:
    m_vb = re.search(r'viewBox="([^"]+)"', svg)
    vw, vh = 460.0, 280.0
    if m_vb:
        parts = [float(x) for x in m_vb.group(1).split()]
        if len(parts) == 4:
            vw, vh = parts[2], parts[3]
    dark = svg
    for old, new in _DARK_REPLACEMENTS:
        dark = dark.replace(old, new)
    backdrop = (
        f'  <rect x="0" y="0" width="{vw:.0f}" height="{vh:.0f}" '
        'rx="8" fill="#090d16" stroke="#1e293b" stroke-width="1.2" />\n'
    )
    return dark.replace(
        '  <g class="layer-grid"', backdrop + '  <g class="layer-grid"', 1
    )


def _activate_3b1b_gallery(html_path: Path) -> None:
    text = html_path.read_text(encoding="utf-8")
    torus_css = (
        '    [data-theme="3b1b"] svg #grad-torus stop:nth-child(1) { stop-color: #1e3a5f !important; }\n'
        '    [data-theme="3b1b"] svg #grad-torus stop:nth-child(2) { stop-color: #0f2942 !important; }\n'
        '    [data-theme="3b1b"] svg #grad-torus stop:nth-child(3) { stop-color: #081a2e !important; }\n'
        '    [data-theme="3b1b"] svg circle[fill="#ffffff"], [data-theme="3b1b"] svg ellipse[fill="#ffffff"] { fill: #090d16 !important; }\n'
    )
    text = text.replace("  </style>", torus_css + "  </style>", 1)
    text = text.replace(
        '<body data-theme="textbook" data-grid="on" data-compare="off">',
        '<body data-theme="3b1b" data-grid="on" data-compare="on">',
        1,
    )
    text = text.replace(
        '<button type="button" class="theme active" onclick="setTheme(\'textbook\', this)">Textbook Classic</button>'
        '<button type="button" class="theme" onclick="setTheme(\'3b1b\', this)">3Blue1Brown 2D</button>',
        '<button type="button" class="theme" onclick="setTheme(\'textbook\', this)">Textbook Classic</button>'
        '<button type="button" class="theme active" onclick="setTheme(\'3b1b\', this)">3Blue1Brown 2D</button>',
        1,
    )
    text = text.replace(
        '<button type="button" onclick="toggleCompare(this)">Compare Scan</button>',
        '<button type="button" class="active" onclick="toggleCompare(this)">Compare Scan</button>',
        1,
    )
    _ = html_path.write_text(text, encoding="utf-8")


def _typst_binary() -> str:
    found = shutil.which("typst")
    if found:
        return found
    shim = Path.home() / ".local" / "share" / "mise" / "shims" / "typst"
    if shim.exists():
        return str(shim)
    raise RuntimeError("typst executable not found")


def _rasterize_svgs_via_typst(jobs: list[tuple[Path, Path, str]]) -> None:
    if not jobs:
        return
    typst_bin = _typst_binary()
    with tempfile.TemporaryDirectory(prefix="shafarevich_svg_") as tmp:
        tmp_dir = Path(tmp)
        blocks: list[str] = []
        for idx, (svg_path, _, bg_hex) in enumerate(jobs):
            local_svg = tmp_dir / f"src_{idx}.svg"
            _ = shutil.copy2(svg_path, local_svg)
            m_vb = re.search(
                r'viewBox="([^"]+)"', local_svg.read_text(encoding="utf-8")
            )
            vw, vh = 460.0, 280.0
            if m_vb:
                parts = [float(x) for x in m_vb.group(1).split()]
                if len(parts) == 4:
                    vw, vh = parts[2], parts[3]
            blocks.append(
                f"#page(width: {vw * 1.15:.1f}pt, height: {vh * 1.15:.1f}pt, "
                f'margin: 0pt, fill: rgb("{bg_hex}"))[\n'
                f'  #image("src_{idx}.svg", width: 100%, height: 100%)\n'
                "]"
            )
        typ_file = tmp_dir / "batch.typ"
        _ = typ_file.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
        out_pattern = tmp_dir / "out-{0p}.png"
        cmd = [
            typst_bin,
            "compile",
            "--font-path",
            str(REPO_FONTS),
            "--ppi",
            "300",
            str(typ_file),
            str(out_pattern),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        pad = len(str(len(jobs)))
        for idx, (_, dst_png, _) in enumerate(jobs, start=1):
            rendered = tmp_dir / f"out-{idx:0{pad}d}.png"
            if not rendered.exists():
                rendered = tmp_dir / f"out-{idx}.png"
            dst_png.parent.mkdir(parents=True, exist_ok=True)
            _ = shutil.move(str(rendered), str(dst_png))


def draw_figures(out_dir: Path) -> list[Path]:
    from polytypst.books import book_by_key

    spec = book_by_key(FOLDER.name).spec
    fig_dir = out_dir / "figures"
    raw_dir = out_dir / "figures_raw"
    dark_dir = out_dir / "figures_3b1b"
    web_dir = out_dir / "web_figures"
    for d in (fig_dir, raw_dir, dark_dir, web_dir):
        d.mkdir(parents=True, exist_ok=True)

    scan = pymupdf.open(source_pdf(spec))
    raw_meta: dict[str, tuple[tuple[float, float, float, float], int, int]] = {}
    for fid, pno, idx, _, _ in _FIGURES:
        page = scan[pno - 1]
        rects = sorted(
            (
                r
                for img in page.get_images(full=True)
                for r in page.get_image_rects(img[0])
            ),
            key=lambda r: (round(r.y0, 1), round(r.x0, 1)),
        )
        rect = rects[idx]
        w, h = page.rect.width, page.rect.height
        pix = page.get_pixmap(dpi=600, clip=rect)
        raw_path = raw_dir / f"fig_{fid}.png"
        pix.save(raw_path)
        raw_meta[fid] = (
            (rect.x0 / w, rect.y0 / h, rect.x1 / w, rect.y1 / h),
            pix.width,
            pix.height,
        )

    _ = render_figures(SHAFAREVICH_FIGURE_BOOK, fig_dir, web_dir)
    _activate_3b1b_gallery(web_dir / "index.html")

    jobs: list[tuple[Path, Path, str]] = []
    svg_paths: list[Path] = []
    for fid, *_ in _FIGURES:
        light_svg = fig_dir / f"fig_{fid}.svg"
        dark_svg = dark_dir / f"fig_{fid}.svg"
        _ = dark_svg.write_text(
            _to_3b1b_dark_svg(light_svg.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        svg_paths.append(light_svg)
        jobs.append((light_svg, fig_dir / f"fig_{fid}.png", "#ffffff"))
        jobs.append((dark_svg, dark_dir / f"fig_{fid}.png", "#090d16"))

    _rasterize_svgs_via_typst(jobs)

    entries: list[ExtractedFigure] = []
    for fid, pno, _, chap, caption in _FIGURES:
        box, w_px, h_px = raw_meta[fid]
        entries.append(
            ExtractedFigure(
                figure_id=fid,
                caption=caption,
                image_rel_path=f"figures/fig_{fid}.png",
                source_page=pno,
                box=box,
                width_px=w_px,
                height_px=h_px,
                chapter=chap,
                title=SHAFAREVICH_FIG_TITLES[fid],
                scan_crop_path=f"figures_raw/fig_{fid}.png",
                svg_path=f"figures/fig_{fid}.svg",
                reproduced_by="vector",
            )
        )
    write_figures_manifest(out_dir / FIGURES_MANIFEST_NAME, entries)

    missing = SHAFAREVICH_FIGURE_BOOK.verify_completeness(
        out_dir,
        caption_pattern=spec.figures.caption_pattern,
    )
    if missing:
        raise RuntimeError(f"Missing vector figures in FigureBook: {missing}")

    return svg_paths
