from ..edition import OUTPUT, Book, monograph_edition
from .spec import MODERN_GEOMETRY_VOL3_SPEC

OUT_DIR = OUTPUT / "modern_geometry_vol3"

BOOK = Book(
    MODERN_GEOMETRY_VOL3_SPEC,
    OUT_DIR,
    {"monograph": monograph_edition(MODERN_GEOMETRY_VOL3_SPEC, OUT_DIR, "monograph")},
)
