from pathlib import Path
from .figures import generate_all_algebra1_figures


def draw_figures(out_dir: Path) -> None:
    """Pre-build hook: generate all 45 vector figures as SVG and 300-DPI PNGs."""
    generate_all_algebra1_figures(out_dir)
