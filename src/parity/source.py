"""The source scan of a book and the Vision OCR lines of its pages.

The spec names the scan file; the folder comes from POLYTYPST_SOURCES or an
explicit path. OCR lines are cached as one JSON file per page in the book's
`source_ocr` folder, which the facsimile, the line-break hook and scan parity share.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from ..compiler.monograph import MonographSpec

SOURCES_ENV = "POLYTYPST_SOURCES"
SCAN_DPI = 300


class SourceScanError(RuntimeError):
    pass


def source_pdf(spec: MonographSpec, override: Path | None = None) -> Path:
    """The book's source scan: `override` when given, else `spec.source_pdf` inside $POLYTYPST_SOURCES."""
    if override is not None:
        path = Path(override).expanduser()
    else:
        if not spec.source_pdf:
            raise SourceScanError(f"{spec.slug} has no source_pdf on its spec")
        root = os.environ.get(SOURCES_ENV)
        if not root:
            raise SourceScanError(
                f"set {SOURCES_ENV} (environment or mise.local.toml) to the folder holding {spec.source_pdf!r}"
            )
        path = Path(root).expanduser() / spec.source_pdf
    if not path.is_file():
        raise SourceScanError(f"source scan not found: {path}")
    return path


def source_ocr_dir(out_dir: Path) -> Path:
    return Path(out_dir) / "source_ocr"


@dataclass(frozen=True)
class OcrLine:
    """One Vision OCR line; x, y, w, h are fractions of the page with the origin at the bottom left."""

    text: str
    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True)
class SourcePage:
    number: int
    width: float
    height: float
    lines: tuple[OcrLine, ...]

    def top_pt(self, line: OcrLine) -> float:
        return (1 - line.y - line.h) * self.height


def ensure_source_ocr(source: Path, cache: Path, batch: int = 40) -> None:
    """Run Vision OCR on every scan page that has no cached lines, and record the page sizes."""
    cache.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(source)
    sizes = cache / "pages.json"
    if not sizes.exists():
        pages = {str(p): [doc[p - 1].rect.width, doc[p - 1].rect.height] for p in range(1, doc.page_count + 1)}
        sizes.write_text(json.dumps(pages), encoding="utf-8")
    todo = [p for p in range(1, doc.page_count + 1) if not (cache / f"p{p:03d}.json").exists()]
    if not todo:
        return
    from ..ocr.apple_vision import AppleVisionOCREngine

    engine = AppleVisionOCREngine(["en-US", "fr-FR"])
    scans = cache / "scans"
    scans.mkdir(exist_ok=True)
    for start in range(0, len(todo), batch):
        pages = todo[start : start + batch]
        paths = []
        for p in pages:
            png = scans / f"p{p:03d}.png"
            doc[p - 1].get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY).save(png)
            paths.append(png)
        for p, result in zip(pages, engine.recognize_document(paths)):
            lines = [{"text": l.text, "x": l.x, "y": l.y, "w": l.w, "h": l.h} for l in result.lines]
            (cache / f"p{p:03d}.json").write_text(json.dumps(lines, ensure_ascii=False), encoding="utf-8")
        for png in paths:
            png.unlink()
        print(f"OCR {pages[-1]}/{doc.page_count}", flush=True)


def read_source_page(cache: Path, number: int) -> SourcePage:
    """The cached OCR lines and size of a 1-based scan page; raises when `ensure_source_ocr` has not run."""
    path = cache / f"p{number:03d}.json"
    sizes = cache / "pages.json"
    if not path.exists() or not sizes.exists():
        raise SourceScanError(f"no source OCR for page {number} in {cache}; run ensure_source_ocr first")
    width, height = json.loads(sizes.read_text())[str(number)]
    lines = tuple(OcrLine(**line) for line in json.loads(path.read_text(encoding="utf-8")))
    return SourcePage(number, width, height, lines)
