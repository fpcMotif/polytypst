import shutil
from collections.abc import Callable
from pathlib import Path

from ..vision.diagram_engine import FigureBook, FigureSpec, render_figures
from .figures_ch1 import CHAPTER_FIG_TITLES as CH1_TITLES
from .figures_ch1 import CHAPTER_SVG_GENERATORS as CH1_GENS
from .figures_ch2a import CHAPTER_FIG_TITLES as CH2A_TITLES
from .figures_ch2a import CHAPTER_SVG_GENERATORS as CH2A_GENS
from .figures_ch2b import CHAPTER_FIG_TITLES as CH2B_TITLES
from .figures_ch2b import CHAPTER_SVG_GENERATORS as CH2B_GENS
from .figures_ch3 import CHAPTER_FIG_TITLES as CH3_TITLES
from .figures_ch3 import CHAPTER_SVG_GENERATORS as CH3_GENS
from .figures_ch4 import CHAPTER_FIG_TITLES as CH4_TITLES
from .figures_ch4 import CHAPTER_SVG_GENERATORS as CH4_GENS
from .figures_ch5 import CHAPTER_FIG_TITLES as CH5_TITLES
from .figures_ch5 import CHAPTER_SVG_GENERATORS as CH5_GENS

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


def _sort_key(fid: str) -> list[int]:
    return [int(x) for x in fid.split("_") if x.isdigit()]


KODAIRA_FIGURE_BOOK = FigureBook(
    slug="kodaira_complex_analysis",
    title="Kunihiko Kodaira · Complex Analysis",
    subtitle="Parametric Code-Reproduced 2D Illustrations · Textbook Monograph & Progressive 3Blue1Brown Web Renderer",
    figures=tuple(
        FigureSpec(
            fig_id=fid,
            label=f"Fig. {fid.replace('_', '.')}",
            chapter=int(fid.split("_")[0]),
            build=KODAIRA_SVG_GENERATORS[fid],
            title=KODAIRA_FIG_TITLES.get(fid, ""),
        )
        for fid in sorted(KODAIRA_SVG_GENERATORS, key=_sort_key)
    ),
    chapter_titles={
        1: "Holomorphic Functions",
        2: "Cauchy's Theorem & Cellular Decomposition",
        3: "Conformal Mappings & Riemann Sphere",
        4: "Analytic Continuation",
        5: "Riemann's Mapping Theorem",
    },
    scan_dir="../figures_raw",
    search_hint="Search Fig. 2.27, cellular, sphere...",
)


def generate_all_kodaira_figures(out_dir: Path) -> Path:
    """Render every Kodaira figure and its gallery; keep the original PNG scans for comparison."""
    fig_dir = out_dir / "figures"
    raw_dir = out_dir / "figures_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for png_file in sorted(fig_dir.glob("fig_*.png")):
        dest_raw = raw_dir / png_file.name
        if not dest_raw.exists():
            _ = shutil.copy2(png_file, dest_raw)
    web_dir = out_dir / "web_figures"
    _ = render_figures(KODAIRA_FIGURE_BOOK, fig_dir, web_dir)
    return web_dir / "index.html"
