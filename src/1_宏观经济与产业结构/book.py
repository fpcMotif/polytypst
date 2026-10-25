from pathlib import Path

from ..edition import OUTPUT, Book, monograph_edition
from .figures import crop_macro_figures
from .spec import MACRO_ILLUSTRATED_SPEC, MACRO_SPEC

OUT_DIR = OUTPUT / "1_宏观经济与产业结构"


def draw_figures(out_dir: Path) -> list[Path]:
    crop_macro_figures(out_dir)
    return sorted((out_dir / "figures").glob("fig_*.png"))


BOOK = Book(
    MACRO_SPEC,
    OUT_DIR,
    {
        "monograph": monograph_edition(
            MACRO_SPEC, OUT_DIR, "13 chapters, monochrome academic monograph"
        ),
        "illustrated": monograph_edition(
            MACRO_ILLUSTRATED_SPEC,
            OUT_DIR,
            "13 chapters, illustrated monograph with redrawn figures",
        ),
    },
    draw_figures,
)
