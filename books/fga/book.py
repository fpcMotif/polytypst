from pathlib import Path

from polytypst.edition import OUTPUT, Book, facsimile_edition, monograph_edition
from polytypst.facsimile import FacsimileStyle
from polytypst.parity.diagrams import DiagramText
from polytypst.vision.diagram_crops import install_scan_diagrams, scan_diagram_boxes

from .spec import FGA_SPEC

OUT_DIR = OUTPUT / "fga"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"
DIAGRAM_TEXT = DiagramText(font="STIX Two Text", size=9.5, weight=400)


def install_diagrams(out_dir: Path) -> list[Path]:
    return install_scan_diagrams(DIAGRAM_DIR, out_dir)

def fga_diagram_boxes() -> dict[str, tuple[int, int, int, int]]:
    boxes = {fig: box for fig, (_, box) in scan_diagram_boxes(OUT_DIR).items()}
    boxes["070_001"] = (667, 2208, 1458, 2417)
    return boxes



FACSIMILE_STYLE = FacsimileStyle(
    slug="fga_facsimile",
    title="Fondements de la géométrie algébrique (facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/STIXTwoText.ttf"),
    font_stack='("STIX Two Text", "STIX Two Math")',
    size=9.5,
    weight=400,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=install_diagrams,
    diagram_boxes=fga_diagram_boxes,
    transcripts=FGA_SPEC.markdown_dir,
)


BOOK = Book(
    FGA_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(FGA_SPEC, OUT_DIR, "monograph"),
        "facsimile": facsimile_edition(FGA_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
    install_diagrams,
)
