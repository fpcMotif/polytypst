"""Word-placed facsimile of the 1970 Bourbaki scan, set in Baskervville."""

from polytypst.compiler.typst_math import REPO_FONTS_DIR as FONTS
from polytypst.facsimile import FacsimileStyle

from . import DIAGRAM_DIR, DIAGRAM_TEXT, install_bourbaki_diagrams

STYLE = FacsimileStyle(
    slug="bourbaki_1970_facsimile",
    title="Commutative Algebra (1970 facsimile)",
    font_file=FONTS / "Baskervville-wght.ttf",
    font_stack='("Baskervville", "STIX Two Text", "STIX Two Math")',
    size=10.0,
    weight=600,
    diagram_dir=DIAGRAM_DIR,
    diagram_text=DIAGRAM_TEXT,
    install_diagrams=install_bourbaki_diagrams,
)
