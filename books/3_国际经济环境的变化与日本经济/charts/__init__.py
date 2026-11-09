from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from polytypst.charts.engine import (
    ChartStyle,
    ThemeMode,
    chart_svg,
    save_figure_outputs,
)

PREFACE_CHART = "preface_exchange_rate"


def chart_file(book_dir: Path, fid: str) -> Path:
    """The preface page links its chart by name, and the scan crop keeps the PNG name."""
    return book_dir / "figures" / (f"{fid}.svg" if fid == PREFACE_CHART else f"fig_{fid}.svg")


def prepare(book_dir: Path) -> None:
    """Copy each scan crop to figures_raw before the mono PNG takes its name in figures."""
    raw_dir = book_dir / "figures_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for crop in (book_dir / "figures").glob("*.png"):
        if not (raw_dir / crop.name).exists():
            shutil.copy2(crop, raw_dir / crop.name)


def write(fid: str, generator: Callable[[ThemeMode], str], style: ChartStyle, book_dir: Path) -> None:
    svg = chart_svg(generator, style)
    if fid == PREFACE_CHART:
        chart_file(book_dir, fid).write_text(svg, encoding="utf-8")
    else:
        save_figure_outputs(fid, {"mono": svg}, book_dir=book_dir, dpi=300)
