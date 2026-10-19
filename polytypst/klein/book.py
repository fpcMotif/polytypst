from ..edition import OUTPUT, Book, monograph_edition
from .spec import KLEIN_SPEC
from .zh_spec import KLEIN_ZH_SPEC

BOOK = Book(
    KLEIN_SPEC,
    OUTPUT / "klein",
    {
        "en": monograph_edition(KLEIN_SPEC, OUTPUT / "klein", "English"),
        "zh": monograph_edition(KLEIN_ZH_SPEC, OUTPUT / "klein_zh", "Chinese"),
    },
)
