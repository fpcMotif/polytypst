from pathlib import Path

from polytypst.edition import OUTPUT, Book, monograph_edition

from .figures import crop_cross_page_figures
from .spec import LABOR_ILLUSTRATED_SPEC, LABOR_SPEC

OUT_DIR = OUTPUT / "6_劳动力市场与收入分配"


def prepare(source: Path | None) -> None:
    crop_cross_page_figures(OUT_DIR, source)


BOOK = Book(
    LABOR_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(
            LABOR_SPEC, OUT_DIR, "17 chapters, academic monograph", prepare
        ),
        "illustrated": monograph_edition(
            LABOR_ILLUSTRATED_SPEC,
            OUT_DIR,
            "17 chapters, illustrated monograph with scan figures",
            prepare,
        ),
    },
)
