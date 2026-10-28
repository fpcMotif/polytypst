from pathlib import Path

from .figures import generate_colorful_ahlfors_figures


def draw_figures(out_dir: Path) -> None:
    generate_colorful_ahlfors_figures(out_dir / "figures", out_dir / "figures_color")
