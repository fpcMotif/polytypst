import shutil
from pathlib import Path

from polytypst.edition import OUTPUT, Book, facsimile_edition, monograph_edition
from polytypst.facsimile import FacsimileStyle
from polytypst.parity.diagrams import DiagramText

from .figures import generate_modern_geometry_figures
from .spec import MODERN_GEOMETRY_ILLUSTRATED_SPEC, MODERN_GEOMETRY_SPEC

OUT_DIR = OUTPUT / "modern_geometry"
DIAGRAM_DIR = Path(__file__).parent / "diagrams"
DIAGRAM_TEXT = DiagramText(font="Times New Roman", size=9.5, weight=400)


def draw_figures(out_dir: Path) -> list[Path]:
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    installed = [
        Path(shutil.copy2(src, fig_dir / src.name))
        for src in sorted(DIAGRAM_DIR.glob("*.typ"))
    ]
    generate_modern_geometry_figures(out_dir / "figures", out_dir / "figures_color")
    return installed


FACSIMILE_STYLE = FacsimileStyle(
    slug="modern_geometry_facsimile",
    title="Modern Geometry—Methods and Applications. Part I (facsimile)",
    font_file=Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
    font_stack='("Times New Roman", "STIX Two Math")',
    size=9.5,
    weight=400,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=draw_figures,
    transcripts=MODERN_GEOMETRY_SPEC.markdown_dir,
)


BOOK = Book(
    MODERN_GEOMETRY_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(MODERN_GEOMETRY_SPEC, OUT_DIR, "monograph (ordinary figures)"),
        "illustrated": monograph_edition(MODERN_GEOMETRY_ILLUSTRATED_SPEC, OUT_DIR, "illustrated monograph with colour figures"),
        "facsimile": facsimile_edition(MODERN_GEOMETRY_SPEC, OUT_DIR, FACSIMILE_STYLE),
    },
    draw_figures,
)
