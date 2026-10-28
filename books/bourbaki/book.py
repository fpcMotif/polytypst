from pathlib import Path

from polytypst.edition import (
    Book,
    Parity,
    facsimile_edition,
    install_page_fit,
    monograph_edition,
)
from polytypst.parity.report import SOURCE_PAGINATED
from polytypst.parity.source import ensure_source_ocr, source_ocr_dir, source_pdf

from . import DIAGRAM_DIR, DIAGRAM_TEXT, OUT_DIR, install_bourbaki_diagrams
from .facsimile import STYLE as FACSIMILE_STYLE
from .marks import query_marks
from .spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC

VINTAGE_TYP = OUT_DIR / f"{BOURBAKI_1970_SPEC.slug}.typ"


def vintage_page_map() -> dict[int, list[int]]:
    """Each source page's output pages, from its first-line and last-line markers in the vintage Typst."""
    marks = query_marks(VINTAGE_TYP)
    tops = {int(m["key"]): m["page"] for m in marks if m["kind"] == "top"}
    ends = {int(m["key"]): m["page"] for m in marks if m["kind"] == "end"}
    return {p: list(range(top, ends.get(p, top) + 1)) for p, top in sorted(tops.items())}


def prepare_vintage(source: Path | None) -> None:
    """Vintage forces the scan's line breaks, so it needs the source OCR, and Typst reads page_fit.json."""
    ensure_source_ocr(source_pdf(BOURBAKI_1970_SPEC, source), source_ocr_dir(OUT_DIR), BOURBAKI_1970_SPEC.ocr_languages)
    install_page_fit(OUT_DIR)


BOOK = Book(
    BOURBAKI_SPEC,
    OUT_DIR,
    {
        "vintage": monograph_edition(
            BOURBAKI_1970_SPEC, OUT_DIR, "1970 look, paginated and line-broken like the scan", prepare_vintage,
            Parity(vintage_page_map, SOURCE_PAGINATED, DIAGRAM_DIR, DIAGRAM_TEXT),
        ),
        "facsimile": facsimile_edition(BOURBAKI_SPEC, OUT_DIR, FACSIMILE_STYLE),
        "modern": monograph_edition(BOURBAKI_SPEC, OUT_DIR, "reflowed Springer-style monograph"),
    },
    install_bourbaki_diagrams,
)
