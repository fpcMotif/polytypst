from pathlib import Path

from ..edition import (
    OUTPUT,
    Book,
    facsimile_edition,
    install_page_fit,
    monograph_edition,
)
from ..facsimile import FacsimileStyle
from ..parity.diagrams import DiagramText
from ..vision.diagram_crops import install_scan_diagrams, scan_diagram_boxes
from .spec import GROTHENDIECK_1971_SPEC, GROTHENDIECK_SPEC

OUT_DIR = OUTPUT / "grothendieck"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"
DIAGRAM_TEXT = DiagramText(font="STIX Two Text", size=9.5, weight=400)


def install_diagrams(out_dir: Path) -> list[Path]:
    return install_scan_diagrams(DIAGRAM_DIR, out_dir)


FACSIMILE_STYLE = FacsimileStyle(
    slug="grothendieck_1971_facsimile",
    title="Éléments de géométrie algébrique I (1971 facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/STIXTwoText.ttf"),
    font_stack='("STIX Two Text", "STIX Two Math")',
    size=9.5,
    weight=400,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=install_diagrams,
    diagram_boxes=lambda: {fig: box for fig, (_, box) in scan_diagram_boxes(OUT_DIR).items()},
    transcripts=GROTHENDIECK_SPEC.markdown_dir,
)


def prepare_vintage(_source: Path | None) -> None:
    """The vintage Typst reads page_fit.json for per-page size and leading."""
    install_page_fit(OUT_DIR)


BOOK = Book(
    GROTHENDIECK_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(
            GROTHENDIECK_SPEC, OUT_DIR, "reflowed Springer-style monograph"
        ),
        "vintage": monograph_edition(
            GROTHENDIECK_1971_SPEC,
            OUT_DIR,
            "1971 look, one output page per scan page",
            prepare_vintage,
        ),
        "facsimile": facsimile_edition(GROTHENDIECK_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
    install_diagrams,
)
