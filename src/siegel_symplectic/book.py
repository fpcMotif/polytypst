from ..edition import OUTPUT, Book, monograph_edition
from .spec import SIEGEL_SYMPLECTIC_SPEC
from .styles import STYLED_SPECS

OUT_DIR = OUTPUT / "siegel-symplectic"

BOOK = Book(
    SIEGEL_SYMPLECTIC_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(SIEGEL_SYMPLECTIC_SPEC, OUT_DIR, "monograph"),
        "journal": monograph_edition(STYLED_SPECS["journal"], OUT_DIR, "1943 offprint layout, Modern type on cream"),
        "oxblood": monograph_edition(STYLED_SPECS["oxblood"], OUT_DIR, "offprint layout, Baskerville with oxblood heads"),
        "indigo": monograph_edition(STYLED_SPECS["indigo"], OUT_DIR, "offprint layout, Libertinus with indigo heads"),
    },
)
