"""The source scan of a book and the Vision OCR lines of its pages.

The spec names the scan file; the folder comes from POLYTYPST_SOURCES or an
explicit path. OCR lines are cached as one JSON file per page in the book's
`source_ocr` folder, which the facsimile, the line-break hook and scan parity share.
"""

import os
from collections.abc import Sequence
from pathlib import Path

from ..compiler.monograph import MonographSpec
from ..ocr.lines import SCAN_DPI, LineStore, SourcePage, source_ocr_dir
from ..ocr.scan import SourceScanError

SOURCES_ENV = "POLYTYPST_SOURCES"


def sources_dir(wanted: str) -> Path:
    """The folder of source scans named by $POLYTYPST_SOURCES; `wanted` names the file for the error."""
    root = os.environ.get(SOURCES_ENV)
    if not root:
        raise SourceScanError(f"set {SOURCES_ENV} (environment or mise.local.toml) to the folder holding {wanted!r}")
    return Path(root).expanduser()


def source_pdf(spec: MonographSpec, override: Path | None = None) -> Path:
    """The book's source scan: `override` when given, else `spec.source_pdf` inside $POLYTYPST_SOURCES."""
    if override is not None:
        path = Path(override).expanduser()
    else:
        if not spec.source_pdf:
            raise SourceScanError(f"{spec.slug} has no source_pdf on its spec")
        path = sources_dir(spec.source_pdf) / spec.source_pdf
    if not path.is_file():
        raise SourceScanError(f"source scan not found: {path}")
    return path


def ensure_source_ocr(source: Path, cache: Path, languages: Sequence[str], batch: int = 40) -> None:
    """Run OCR on every scan page that has no cached lines, and record the page sizes."""
    LineStore(cache).ensure_pdf(source, languages, batch=batch)


def read_source_page(cache: Path, number: int) -> SourcePage:
    """The cached OCR lines and size of a 1-based scan page; raises when `ensure_source_ocr` has not run."""
    return LineStore(cache).page(number)

__all__ = [
    "SCAN_DPI",
    "SOURCES_ENV",
    "SourcePage",
    "ensure_source_ocr",
    "read_source_page",
    "source_ocr_dir",
    "source_pdf",
    "sources_dir",
]
