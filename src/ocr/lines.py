import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pymupdf

from ..book_state import book_state
from .pages import LineReader, OcrLine, PageImage
from .scan import SourceScan, SourceScanError

DEFAULT_OCR_LANGUAGES = ("en-US",)
FIGURE_OCR_DIR = Path.home() / ".cache" / "polytypst" / "figure_ocr"
PROVENANCE_NAME = "lines.json"
PAGES_NAME = "pages.json"
SCAN_DPI = 300


def source_ocr_dir(out_dir: Path) -> Path:
    return book_state(out_dir) / "source_ocr"


@dataclass(frozen=True)
class SourcePage:
    number: int
    width: float
    height: float
    lines: tuple[OcrLine, ...]

    def top_pt(self, line: OcrLine) -> float:
        return (1 - line.y - line.h) * self.height


@cache
def _page_sizes(sizes: Path) -> dict[str, list[float]]:
    return json.loads(sizes.read_text(encoding="utf-8"))



def line_reader(languages: Sequence[str]) -> LineReader:
    """Apple Vision on macOS, Tesseract everywhere else."""
    if sys.platform == "darwin":
        from .apple_vision import AppleVisionReader

        return AppleVisionReader(languages)
    from .tesseract import TesseractReader

    return TesseractReader(languages)


class ImageLineStore:
    """OCR lines of standalone images such as figure crops, cached as one file per image bytes and reader."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    def _path(self, image: Path, provenance: str) -> Path:
        key = hashlib.sha256(image.read_bytes() + provenance.encode()).hexdigest()
        return self.directory / f"{key}.json"

    def lines(self, image: Path, provenance: str) -> tuple[OcrLine, ...] | None:
        path = self._path(image, provenance)
        if not path.exists():
            return None
        return tuple(OcrLine(**line) for line in json.loads(path.read_text(encoding="utf-8")))

    def read(self, images: Sequence[Path], reader: LineReader) -> None:
        """Send the images with no cached file to `reader`, storing each page as it arrives."""
        self.directory.mkdir(parents=True, exist_ok=True)
        pending = [
            PageImage(n, image)
            for n, image in enumerate(images, 1)
            if not self._path(image, reader.provenance).exists()
        ]
        by_number = {page.number: page.path for page in pending}
        for page in reader.read(pending) if pending else ():
            rows = [line.__dict__ for line in page.lines]
            _ = self._path(by_number[page.number], reader.provenance).write_text(
                json.dumps(rows, ensure_ascii=False), encoding="utf-8"
            )


class LineStore:
    """OCR lines cached as one `pNNN.json` file per page, plus `lines.json` naming each page's reader."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    def _path(self, number: int) -> Path:
        return self.directory / f"p{number:03d}.json"

    def lines(self, number: int) -> tuple[OcrLine, ...] | None:
        path = self._path(number)
        if not path.exists():
            return None
        return tuple(
            OcrLine(**line) for line in json.loads(path.read_text(encoding="utf-8"))
        )

    def _made_by(self) -> dict[str, str]:
        path = self.directory / PROVENANCE_NAME
        return (
            json.loads(path.read_text(encoding="utf-8"))["pages"]
            if path.exists()
            else {}
        )

    def read(
        self, pages: Sequence[PageImage], reader: LineReader
    ) -> dict[int, tuple[OcrLine, ...]]:
        """The lines of `pages`, sending only the pages that have no cached file to `reader`."""
        self.directory.mkdir(parents=True, exist_ok=True)
        pending = [p for p in pages if not self._path(p.number).exists()]
        if pending:
            made_by = self._made_by()
            for page in reader.read(pending):
                rows = [line.__dict__ for line in page.lines]
                _ = self._path(page.number).write_text(
                    json.dumps(rows, ensure_ascii=False), encoding="utf-8"
                )
                made_by[str(page.number)] = reader.provenance
            draft = self.directory / f"{PROVENANCE_NAME}.tmp"
            _ = draft.write_text(
                json.dumps({"pages": made_by}, indent=1) + "\n", encoding="utf-8"
            )
            _ = draft.replace(self.directory / PROVENANCE_NAME)
        found = {
            p.number: lines
            for p in pages
            if (lines := self.lines(p.number)) is not None
        }
        if missing := len(pages) - len(found):
            print(f"{missing} page(s) got no OCR lines from {reader.provenance}")
        return found

    def ensure_pdf(
        self,
        source: Path,
        languages: Sequence[str],
        batch: int = 40,
        reader: LineReader | None = None,
    ) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        doc = pymupdf.open(source)
        sizes = self.directory / PAGES_NAME
        if not sizes.exists():
            pages = {
                str(p): [doc[p - 1].rect.width, doc[p - 1].rect.height]
                for p in range(1, doc.page_count + 1)
            }
            _ = sizes.write_text(json.dumps(pages), encoding="utf-8")
        todo = [
            p for p in range(1, doc.page_count + 1) if self.lines(p) is None
        ]
        if not todo:
            return
        line_r = reader or line_reader(languages)
        scan = SourceScan(source, split=False)
        for start in range(0, len(todo), batch):
            pages = scan.pages(
                self.directory / "scans",
                dpi=SCAN_DPI,
                grey=True,
                numbers=todo[start : start + batch],
            )
            _ = self.read(pages, line_r)
            for page in pages:
                page.path.unlink()
            print(f"OCR {pages[-1].number}/{doc.page_count}", flush=True)

    def page(self, number: int) -> SourcePage:
        lines = self.lines(number)
        sizes = self.directory / PAGES_NAME
        if lines is None or not sizes.exists():
            raise SourceScanError(
                f"no source OCR for page {number} in {self.directory}; run ensure_source_ocr first"
            )
        width, height = _page_sizes(sizes)[str(number)]
        return SourcePage(number, width, height, lines)

