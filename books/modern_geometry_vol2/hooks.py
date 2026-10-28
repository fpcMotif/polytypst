from pathlib import Path

from .figures import generate_modern_geometry_vol2_figures


def draw_figures(out_dir: Path) -> list[Path]:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    generate_modern_geometry_vol2_figures(out_dir / "figures", out_dir / "figures_color")
    return list(fig_dir.glob("*.svg"))
