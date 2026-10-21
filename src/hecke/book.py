from ..edition import OUTPUT, Book, monograph_edition
from .spec import HECKE_SPEC

OUT_DIR = OUTPUT / "hecke"

BOOK = Book(HECKE_SPEC, OUT_DIR, {"monograph": monograph_edition(HECKE_SPEC, OUT_DIR, "monograph")})
