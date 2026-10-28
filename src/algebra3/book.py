from pathlib import Path

from ..edition import OUTPUT, Book, facsimile_edition, monograph_edition
from ..facsimile import FacsimileStyle
from ..parity.diagrams import DiagramText
from .spec import ALGEBRA3_SPEC

OUT_DIR = OUTPUT / "algebra3"
DIAGRAM_DIR = OUT_DIR / "figures"
DIAGRAM_TEXT = DiagramText(font="Songti SC", size=10.0, weight=400)


FACSIMILE_STYLE = FacsimileStyle(
    slug="algebra3_facsimile",
    title="代数学引论 (第3卷) 基本结构 (facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    font_stack='("Songti SC", "STSong", "STIX Two Math")',
    size=10.0,
    weight=400,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=lambda out: [],
    transcripts=ALGEBRA3_SPEC.markdown_dir,
    flow=True,
    scan_pages=frozenset({1, 2}),
)

BOOK = Book(
    ALGEBRA3_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(ALGEBRA3_SPEC, OUT_DIR, "monograph"),
        "facsimile": facsimile_edition(ALGEBRA3_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
)
