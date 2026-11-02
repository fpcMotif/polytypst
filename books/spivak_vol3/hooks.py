from pathlib import Path

from .figures import generate_all_spivak_figures


def draw_figures(out_dir: Path) -> list[Path]:
    """Hook called before building editions: generate mono and 3b1b figures."""
    fig_dir_mono = out_dir / "figures"
    fig_dir_color = out_dir / "figures_color"
    generate_all_spivak_figures(fig_dir_mono, fig_dir_color)
    return sorted(fig_dir_mono.glob("*.png"))
