from pathlib import Path

from polytypst.edition import OUTPUT, Book, facsimile_edition, monograph_edition
from polytypst.facsimile import FacsimileStyle
from polytypst.parity.diagrams import DiagramText

from .figures import crop_macro_figures, figure_page_art, figure_page_boxes
from .spec import MACRO_ILLUSTRATED_SPEC, MACRO_SPEC

OUT_DIR = OUTPUT / "1_宏观经济与产业结构"

FACSIMILE_STYLE = FacsimileStyle(
    slug="1_facsimile",
    title="宏观经济与产业结构 (facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    font_stack='("Songti SC", "STSong", "STIX Two Math")',
    size=10.5,
    weight=400,
    diagram_dir=OUT_DIR / "figures",
    diagram_text=DiagramText(font="Songti SC", size=10.5, weight=400),
    install_diagrams=lambda out: [],
    figure_boxes=lambda: figure_page_boxes(OUT_DIR),
    figure_art=lambda: figure_page_art(OUT_DIR),
    transcripts=MACRO_SPEC.markdown_dir,
    strict_lines=True,
)


def draw_figures(out_dir: Path) -> list[Path]:
    crop_macro_figures(out_dir)
    return sorted((out_dir / "figures").glob("fig_*.png"))


BOOK = Book(
    MACRO_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(
            MACRO_SPEC, OUT_DIR, "13 chapters, monochrome academic monograph"
        ),
        "illustrated": monograph_edition(
            MACRO_ILLUSTRATED_SPEC,
            OUT_DIR,
            "13 chapters, illustrated monograph with redrawn figures",
        ),
        "facsimile": facsimile_edition(MACRO_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
    draw_figures,
)
