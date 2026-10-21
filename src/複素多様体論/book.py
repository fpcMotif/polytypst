from ..edition import OUTPUT, Book, monograph_edition
from .spec import FUKUSO_SPEC

OUT_DIR = OUTPUT / "複素多様体論"

BOOK = Book(
    FUKUSO_SPEC,
    OUT_DIR,
    {"monograph": monograph_edition(FUKUSO_SPEC, OUT_DIR, "monograph")},
)
