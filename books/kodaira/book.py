from polytypst.edition import OUTPUT, Book, monograph_edition

from .figures import generate_all_kodaira_figures
from .spec import KODAIRA_SPEC

OUT_DIR = OUTPUT / "kodaira"

BOOK = Book(
    KODAIRA_SPEC, OUT_DIR, {"monograph": monograph_edition(KODAIRA_SPEC, OUT_DIR, "monograph")},
    generate_all_kodaira_figures,
)
