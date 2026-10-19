from pathlib import Path

import pymupdf

from ..edition import Book, Edition, Parity, monograph_edition
from ..parity.report import FACSIMILE, SOURCE_PAGINATED
from ..parity.source import ensure_source_ocr, source_ocr_dir, source_pdf
from . import DIAGRAM_DIR, DIAGRAM_TEXT, OUT_DIR, install_bourbaki_diagrams
from .facsimile import SLUG as FACSIMILE_SLUG
from .facsimile import build_facsimile as write_facsimile
from .marks import query_marks
from .spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC

VINTAGE_TYP = OUT_DIR / f"{BOURBAKI_1970_SPEC.slug}.typ"
FACSIMILE_PDF = OUT_DIR / f"{FACSIMILE_SLUG}.pdf"


def facsimile_page_map() -> dict[int, list[int]]:
    """The facsimile sets every scan page on the output page with the same number."""
    pages = pymupdf.open(FACSIMILE_PDF).page_count
    return {p: [p] for p in range(1, pages + 1)}


def vintage_page_map() -> dict[int, list[int]]:
    """Each source page's output pages, from its first-line and last-line markers in the vintage Typst."""
    marks = query_marks(VINTAGE_TYP)
    tops = {int(m["key"]): m["page"] for m in marks if m["kind"] == "top"}
    ends = {int(m["key"]): m["page"] for m in marks if m["kind"] == "end"}
    return {p: list(range(top, ends.get(p, top) + 1)) for p, top in sorted(tops.items())}


def prepare_vintage(source: Path | None) -> None:
    """Vintage forces the scan's line breaks, so it needs the source OCR, and Typst reads page_fit.json."""
    ensure_source_ocr(source_pdf(BOURBAKI_1970_SPEC, source), source_ocr_dir(OUT_DIR))
    fit = OUT_DIR / "page_fit.json"
    if not fit.exists():
        fit.write_text("{}\n", encoding="utf-8")


def build_facsimile(source: Path | None) -> None:
    pdf = write_facsimile(source_pdf(BOURBAKI_SPEC, source), OUT_DIR)
    print(f"{pdf}: {pymupdf.open(pdf).page_count} pages")


BOOK = Book(
    BOURBAKI_SPEC,
    OUT_DIR,
    {
        "vintage": monograph_edition(
            BOURBAKI_1970_SPEC, OUT_DIR, "1970 look, paginated and line-broken like the scan", prepare_vintage,
            Parity(vintage_page_map, SOURCE_PAGINATED, DIAGRAM_DIR, DIAGRAM_TEXT),
        ),
        "facsimile": Edition(
            FACSIMILE_PDF, build_facsimile, "every OCR word placed on its scan ink box",
            Parity(facsimile_page_map, FACSIMILE, DIAGRAM_DIR, DIAGRAM_TEXT),
        ),
        "modern": monograph_edition(BOURBAKI_SPEC, OUT_DIR, "reflowed Springer-style monograph"),
    },
    install_bourbaki_diagrams,
)
