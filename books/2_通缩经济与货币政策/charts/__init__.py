from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from polytypst.charts.engine import (
    ChartStyle,
    ThemeMode,
    chart_svg,
    save_figure_outputs,
)

from .gallery import (
    build_typst_showcases,
    build_web_gallery,
    expected_figure_ids,
    extract_svg_title,
    source_pages,
)


def write(fid: str, generator: Callable[[ThemeMode], str], style: ChartStyle, book_dir: Path) -> None:
    svgs: dict[ThemeMode, str] = {"mono": chart_svg(generator, style), "color": generator("color"), "dark": generator("dark")}
    save_figure_outputs(fid, svgs, book_dir=book_dir, dpi=300)


def finish(book_dir: Path, generators: dict[str, Callable[[ThemeMode], str]], style: ChartStyle) -> None:
    fids = expected_figure_ids()
    if missing := [fid for fid in fids if fid not in generators]:
        raise RuntimeError(f"Missing {len(missing)} figure generators: {missing}")
    titles = {fid: extract_svg_title(generators[fid]("color"), fid) for fid in fids}
    print(f"Web gallery: {build_web_gallery(book_dir, titles, source_pages(book_dir))}")
    print(f"Showcase PDFs: {[str(p) for p in build_typst_showcases(book_dir, titles)]}")
