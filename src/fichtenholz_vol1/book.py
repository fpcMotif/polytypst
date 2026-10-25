from pathlib import Path

from ..edition import OUTPUT, Book, facsimile_edition, monograph_edition
from ..facsimile import FacsimileStyle
from ..parity.diagrams import DiagramText
from ..vision.diagram_crops import install_scan_diagrams
from .figures import generate_all_fichtenholz_figures
from .spec import FICHTENHOLZ_VOL1_ILLUSTRATED_SPEC, FICHTENHOLZ_VOL1_SPEC

OUT_DIR = OUTPUT / "fichtenholz_vol1"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"
DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
DIAGRAM_TEXT = DiagramText(font="Songti SC", size=10.0, weight=400)


def draw_figures(out_dir: Path) -> None:
    generate_all_fichtenholz_figures(out_dir / "figures", out_dir / "figures_color")
    _ = install_scan_diagrams(DIAGRAM_DIR, out_dir)

def fichtenholz_diagram_boxes() -> dict[str, tuple[int, int, int, int]]:
    return {
        "453_001": (1600, 350, 2700, 1600),
        "465_001": (800, 1350, 3200, 2600),
    }


FACSIMILE_STYLE = FacsimileStyle(
    slug="fichtenholz_vol1_facsimile",
    title="微积分学教程（第一卷） (facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    font_stack='("Songti SC", "New Computer Modern Math")',
    size=10.0,
    weight=400,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=draw_figures,
    diagram_boxes=fichtenholz_diagram_boxes,
    transcripts=FICHTENHOLZ_VOL1_SPEC.markdown_dir,
    flow=True,
)


BOOK = Book(
    FICHTENHOLZ_VOL1_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(FICHTENHOLZ_VOL1_SPEC, OUT_DIR, "ordinary figures monograph"),
        "illustrated": monograph_edition(FICHTENHOLZ_VOL1_ILLUSTRATED_SPEC, OUT_DIR, "with colorful figures"),
        "facsimile": facsimile_edition(FICHTENHOLZ_VOL1_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
    draw_figures,
)
