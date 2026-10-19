import shutil
from pathlib import Path

from ..parity.diagrams import DiagramText

DIAGRAM_DIR = Path(__file__).parent / "diagrams"
DIAGRAM_TEXT = DiagramText(font="Baskervville", size=9.6, weight=500)
OUT_DIR = Path("output/bourbaki")


def install_bourbaki_diagrams(out_dir: Path) -> list[Path]:
    """Copy the fletcher diagram snippets next to the scanned figure crops they replace."""
    fig_dir = Path(out_dir) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    return [Path(shutil.copy2(src, fig_dir / src.name)) for src in sorted(DIAGRAM_DIR.glob("fig_*.typ"))]
