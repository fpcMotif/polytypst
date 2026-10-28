from pathlib import Path

from polytypst.edition import OUTPUT
from polytypst.vision.diagram_crops import install_scan_diagrams, scan_diagram_boxes

OUT_DIR = OUTPUT / "fga"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"


def install_diagrams(out_dir: Path) -> list[Path]:
    return install_scan_diagrams(DIAGRAM_DIR, out_dir)


def fga_diagram_boxes() -> dict[str, tuple[int, int, int, int]]:
    boxes = {fig: box for fig, (_, box) in scan_diagram_boxes(OUT_DIR).items()}
    boxes["070_001"] = (667, 2208, 1458, 2417)
    return boxes
