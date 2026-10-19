from ..edition import OUTPUT, Book, monograph_edition
from .spec import BOURBAKI_LIE_SPEC

OUT_DIR = OUTPUT / "bourbaki_lie"

BOOK = Book(BOURBAKI_LIE_SPEC, OUT_DIR, {"monograph": monograph_edition(BOURBAKI_LIE_SPEC, OUT_DIR, "monograph")})
