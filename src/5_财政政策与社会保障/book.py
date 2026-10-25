from ..edition import OUTPUT, Book, monograph_edition
from .spec import FISCAL_POLICY_ILLUSTRATED_SPEC, FISCAL_POLICY_SPEC

OUT_DIR = OUTPUT / "5_财政政策与社会保障"


BOOK = Book(
    FISCAL_POLICY_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(
            FISCAL_POLICY_SPEC, OUT_DIR, "14 chapters, monochrome academic monograph"
        ),
        "illustrated": monograph_edition(
            FISCAL_POLICY_ILLUSTRATED_SPEC,
            OUT_DIR,
            "14 chapters, illustrated monograph with scan figures",
        ),
    },
)
