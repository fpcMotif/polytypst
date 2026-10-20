from pathlib import Path

from ..edition import OUTPUT, Book, Edition
from .extractor import build_london_treasury
from .spec import LONDON_TREASURY_SPEC

OUT_DIR = OUTPUT / "london_treasury"


def _build(source: Path | None) -> None:
    outputs = build_london_treasury(source_pdf=source, out_dir=OUT_DIR)
    print(f"{outputs.pdf_path}: {outputs.total_pages} pages")


BOOK = Book(
    LONDON_TREASURY_SPEC,
    OUT_DIR,
    {
        "monograph": Edition(
            rebuilt=OUT_DIR / f"{LONDON_TREASURY_SPEC.slug}.pdf",
            build=_build,
            summary="bilingual guide + 53 extracted primary texts",
            spec=LONDON_TREASURY_SPEC,
        )
    },
)
