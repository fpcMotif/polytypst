from ..edition import OUTPUT, Book, monograph_edition
from .spec import FERMAT_SPEC
from .spec_vol2 import FERMAT2_SPEC

BOOK = Book(
    FERMAT_SPEC,
    OUTPUT / "fermat",
    {
        "vol1": monograph_edition(FERMAT_SPEC, OUTPUT / "fermat", "volume 1"),
        "vol2": monograph_edition(FERMAT2_SPEC, OUTPUT / "fermat2", "volume 2"),
    },
)
