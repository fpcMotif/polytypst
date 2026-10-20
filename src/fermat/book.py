from ..edition import OUTPUT, Book, monograph_edition
from .spec import FERMAT_SPEC
from .spec_vol2 import FERMAT2_SPEC
from .spec_vol3 import FERMAT3_SPEC

_OUT_DIR = OUTPUT / "fermat3"
_OUT_VOL1 = OUTPUT / "fermat"
_OUT_VOL2 = OUTPUT / "fermat2"

BOOK = Book(
    FERMAT3_SPEC,
    _OUT_DIR,
    {
        "monograph": monograph_edition(FERMAT3_SPEC, _OUT_DIR, "monograph"),
        "vol3": monograph_edition(FERMAT3_SPEC, _OUT_DIR, "volume 3"),
        "vol2": monograph_edition(FERMAT2_SPEC, _OUT_VOL2, "volume 2"),
        "vol1": monograph_edition(FERMAT_SPEC, _OUT_VOL1, "volume 1"),
    },
)
