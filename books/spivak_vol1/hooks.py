import shutil
from pathlib import Path

DIAGRAM_DIR = Path(__file__).parent / "diagrams"


def install_diagrams(out_dir: Path) -> list[Path]:
    """Copy the hand-drawn fletcher diagrams into the build's figure folder."""
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    return [Path(shutil.copy2(src, fig_dir / src.name)) for src in sorted(DIAGRAM_DIR.glob("fig_*.typ"))]
