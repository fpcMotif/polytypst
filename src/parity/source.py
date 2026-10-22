"""The source scan of a book and the Vision OCR lines of its pages.

The spec names the scan file; the folder comes from POLYTYPST_SOURCES or an
explicit path. OCR lines are cached as one JSON file per page in the book's
`source_ocr` folder, which the facsimile, the line-break hook and scan parity share.
"""

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pymupdf

from ..compiler.monograph import MonographSpec
from ..ocr.lines import LineStore, line_reader
from ..ocr.pages import OcrLine
from ..ocr.scan import SourceScan, SourceScanError

SOURCES_ENV = "POLYTYPST_SOURCES"
SCAN_DPI = 300


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


def source_ocr_dir(out_dir: Path) -> Path:
    return Path(out_dir) / "source_ocr"


@dataclass(frozen=True)
class SourcePage:
    number: int
    width: float
    height: float
    lines: tuple[OcrLine, ...]

    def top_pt(self, line: OcrLine) -> float:
        return (1 - line.y - line.h) * self.height


def ensure_source_ocr(source: Path, cache: Path, languages: Sequence[str], batch: int = 40) -> None:
    """Run OCR on every scan page that has no cached lines, and record the page sizes."""
    cache.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(source)
    sizes = cache / "pages.json"
    if not sizes.exists():
        pages = {str(p): [doc[p - 1].rect.width, doc[p - 1].rect.height] for p in range(1, doc.page_count + 1)}
        sizes.write_text(json.dumps(pages), encoding="utf-8")
    todo = [p for p in range(1, doc.page_count + 1) if not (cache / f"p{p:03d}.json").exists()]
    if not todo:
        return
    reader = line_reader(languages)
    store = LineStore(cache)
    scan = SourceScan(source, split=False)
    for start in range(0, len(todo), batch):
        pages = scan.pages(cache / "scans", dpi=SCAN_DPI, grey=True, numbers=todo[start : start + batch])
        store.read(pages, reader)
        for page in pages:
            page.path.unlink()
        print(f"OCR {pages[-1].number}/{doc.page_count}", flush=True)


@cache
def _page_sizes(sizes: Path) -> dict[str, list[float]]:
    return json.loads(sizes.read_text())


def read_source_page(cache: Path, number: int) -> SourcePage:
    """The cached OCR lines and size of a 1-based scan page; raises when `ensure_source_ocr` has not run."""
    path = cache / f"p{number:03d}.json"
    sizes = cache / "pages.json"
    if not path.exists() or not sizes.exists():
        raise SourceScanError(f"no source OCR for page {number} in {cache}; run ensure_source_ocr first")
    width, height = _page_sizes(sizes)[str(number)]
    return SourcePage(number, width, height, LineStore(cache).lines(number) or ())
