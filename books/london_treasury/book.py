from pathlib import Path

from polytypst.edition import OUTPUT, Book, Edition, report_build

from .build import LONDON_FORMATS, build_london_treasury
from .spec import LONDON_TREASURY_SPEC

OUT_DIR = OUTPUT / "london_treasury"


def _build(source: Path | None, formats: frozenset[str], _footnotes: str) -> None:
    report_build(build_london_treasury(source_pdf=source, out_dir=OUT_DIR, formats=formats))


BOOK = Book(
    LONDON_TREASURY_SPEC,
    OUT_DIR,
    {
        "monograph": Edition(
            rebuilt=OUT_DIR / f"{LONDON_TREASURY_SPEC.slug}.pdf",
            build=_build,
            summary="bilingual guide + 53 extracted primary texts",
            spec=LONDON_TREASURY_SPEC,
            formats=LONDON_FORMATS,
        )
    },
)
