import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .pages import LineReader, OcrLine, PageImage

DEFAULT_OCR_LANGUAGES = ("en-US",)
PROVENANCE_NAME = "lines.json"


def line_reader(languages: Sequence[str]) -> LineReader:
    """Apple Vision on macOS, Tesseract everywhere else."""
    if sys.platform == "darwin":
        from .apple_vision import AppleVisionReader

        return AppleVisionReader(languages)
    from .tesseract import TesseractReader

    return TesseractReader(languages)


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
