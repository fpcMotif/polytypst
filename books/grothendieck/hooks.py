from pathlib import Path

from polytypst.edition import OUTPUT, install_page_fit
from polytypst.vision.diagram_crops import install_scan_diagrams, scan_diagram_boxes

OUT_DIR = OUTPUT / "grothendieck"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"


def install_diagrams(out_dir: Path) -> list[Path]:
    return install_scan_diagrams(DIAGRAM_DIR, out_dir)


def diagram_boxes() -> dict[str, tuple[int, int, int, int]]:
    return {fig: box for fig, (_, box) in scan_diagram_boxes(OUT_DIR).items()}


def prepare_vintage(_source: Path | None) -> None:
    """The vintage Typst reads page_fit.json for per-page size and leading."""
    install_page_fit(OUT_DIR)
