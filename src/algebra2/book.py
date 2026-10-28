from pathlib import Path

from ..edition import OUTPUT, Book, facsimile_edition, monograph_edition
from ..facsimile import FacsimileStyle
from ..parity.diagrams import DiagramText
from .figures import generate_all_algebra2_figures
from .spec import ALGEBRA2_ILLUSTRATED_SPEC, ALGEBRA2_SPEC

OUT_DIR = OUTPUT / "algebra2"
DIAGRAM_DIR = OUT_DIR / "figures"
DIAGRAM_TEXT = DiagramText(font="Songti SC", size=60.0, weight=400)


FACSIMILE_STYLE = FacsimileStyle(
    slug="algebra2_facsimile",
    title="代数学引论 (第2卷) 线性代数 (facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    font_stack='("Songti SC", "STSong", "STIX Two Math")',
    size=60.0,
    weight=400,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=lambda out: [],
    transcripts=ALGEBRA2_SPEC.markdown_dir,
    flow=False,
    scan_pages=frozenset({1, 2}),
)

def draw_figures(out_dir: Path) -> list[Path]:
    generate_all_algebra2_figures(out_dir / "figures", out_dir / "figures_color")
    return list((out_dir / "figures").glob("fig_*.svg"))


BOOK = Book(
    ALGEBRA2_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(ALGEBRA2_SPEC, OUT_DIR, "ordinary figures monograph"),
        "illustrated": monograph_edition(
            ALGEBRA2_ILLUSTRATED_SPEC, OUT_DIR, "illustrated monograph with 3b1b colour figures"
        ),
        "facsimile": facsimile_edition(ALGEBRA2_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
    draw_figures,
)
