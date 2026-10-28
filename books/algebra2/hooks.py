from pathlib import Path

from .figures import generate_all_algebra2_figures


def draw_figures(out_dir: Path) -> list[Path]:
    generate_all_algebra2_figures(out_dir / "figures", out_dir / "figures_color")
    return list((out_dir / "figures").glob("fig_*.svg"))
