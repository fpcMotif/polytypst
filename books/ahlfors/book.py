from pathlib import Path

from polytypst.edition import OUTPUT, Book, monograph_edition

from .figures import generate_colorful_ahlfors_figures
from .spec import AHLFORS_ILLUSTRATED_SPEC, AHLFORS_SPEC

OUT_DIR = OUTPUT / "ahlfors"


def draw_figures(out_dir: Path) -> None:
    generate_colorful_ahlfors_figures(out_dir / "figures", out_dir / "figures_color")


BOOK = Book(
    AHLFORS_SPEC,
    OUT_DIR,
    {
        "complete": monograph_edition(AHLFORS_SPEC, OUT_DIR, "complete monograph"),
        "illustrated": monograph_edition(AHLFORS_ILLUSTRATED_SPEC, OUT_DIR, "with colour figures"),
    },
    draw_figures,
)
