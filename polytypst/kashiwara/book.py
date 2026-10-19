from ..edition import OUTPUT, Book, monograph_edition
from .spec import KASHIWARA_SPEC

OUT_DIR = OUTPUT / "kashiwara"

BOOK = Book(KASHIWARA_SPEC, OUT_DIR, {"monograph": monograph_edition(KASHIWARA_SPEC, OUT_DIR, "monograph")})
