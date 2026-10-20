from ..edition import OUTPUT, Book, monograph_edition
from .spec import KENJI_ALG_SPEC
from .spec_vol2 import KENJI_ALG2_SPEC
from .spec_vol3 import KENJI_ALG3_SPEC

_OUT_DIR = OUTPUT / "kenji-alg"
_OUT_VOL1 = OUTPUT / "kenji-alg_vol1"
_OUT_VOL2 = OUTPUT / "kenji-alg_vol2"

BOOK = Book(
    KENJI_ALG3_SPEC,
    _OUT_DIR,
    {
        "monograph": monograph_edition(KENJI_ALG3_SPEC, _OUT_DIR, "monograph"),
        "vol3": monograph_edition(KENJI_ALG3_SPEC, _OUT_DIR, "volume 3"),
        "vol2": monograph_edition(KENJI_ALG2_SPEC, _OUT_VOL2, "volume 2"),
        "vol1": monograph_edition(KENJI_ALG_SPEC, _OUT_VOL1, "volume 1"),
    },
)
