from ..edition import OUTPUT, Book, monograph_edition
from .spec import FUNCTIONAL_ANALYSIS_SPEC

OUT_DIR = OUTPUT / "functional_analysis"

BOOK = Book(FUNCTIONAL_ANALYSIS_SPEC, OUT_DIR, {"monograph": monograph_edition(FUNCTIONAL_ANALYSIS_SPEC, OUT_DIR, "monograph")})
