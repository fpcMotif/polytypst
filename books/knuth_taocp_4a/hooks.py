from __future__ import annotations

from pathlib import Path

from .figures import build_all_figures


def draw_figures(out_dir: Path) -> list[Path]:
    return build_all_figures(out_dir)
