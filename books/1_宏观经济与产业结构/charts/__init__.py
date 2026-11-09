from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from polytypst.charts.engine import ChartStyle, ThemeMode, chart_svg, scan_canvas


def prepare(book_dir: Path) -> None:
    (book_dir / "figures_scan").mkdir(exist_ok=True)


def write(fid: str, generator: Callable[[ThemeMode], str], style: ChartStyle, book_dir: Path) -> None:
    with scan_canvas(book_dir, fid):
        (book_dir / "figures_scan" / f"fig_{fid}.svg").write_text(generator("scan"), encoding="utf-8")
    (book_dir / "figures" / f"fig_{fid}.svg").write_text(chart_svg(generator, style), encoding="utf-8")
