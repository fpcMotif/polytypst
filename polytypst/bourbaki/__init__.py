import shutil
from pathlib import Path

DIAGRAM_DIR = Path(__file__).parent / "diagrams"


def install_bourbaki_diagrams(out_dir: Path) -> list[Path]:
    """Copy the fletcher diagram snippets next to the scanned figure crops they replace."""
    fig_dir = Path(out_dir) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    return [Path(shutil.copy2(src, fig_dir / src.name)) for src in sorted(DIAGRAM_DIR.glob("fig_*.typ"))]
