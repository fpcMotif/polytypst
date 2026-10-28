import shutil
from pathlib import Path

from .figures import generate_modern_geometry_figures

DIAGRAM_DIR = Path(__file__).parent / "diagrams"


def draw_figures(out_dir: Path) -> list[Path]:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    installed = [
        Path(shutil.copy2(src, fig_dir / src.name))
        for src in sorted(DIAGRAM_DIR.glob("*.typ"))
    ]
    generate_modern_geometry_figures(out_dir / "figures", out_dir / "figures_color")
    return installed
