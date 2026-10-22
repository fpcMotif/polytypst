import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg"})
_TRAILING_NUMBER = re.compile(r"(\d+)$")


class OCRBackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class PageImage:
    number: int
    path: Path


@dataclass(frozen=True)
class Transcript:
    number: int
    text: str


class Transcriber(Protocol):
    @property
    def provenance(self) -> str: ...

    def transcribe(self, pages: Sequence[PageImage]) -> Iterator[Transcript]: ...


@dataclass(frozen=True)
class OcrLine:
    """One OCR line; x, y, w, h are fractions of the page with the origin at the bottom left."""

    text: str
    x: float
    y: float
    w: float
    h: float
    confidence: float = 1.0


@dataclass(frozen=True)
class LinePage:
    number: int
    lines: tuple[OcrLine, ...]


class LineReader(Protocol):
    @property
    def provenance(self) -> str: ...

    def read(self, pages: Sequence[PageImage]) -> Iterator[LinePage]: ...


def image_lines(reader: LineReader, image: Path) -> tuple[OcrLine, ...]:
    """The lines of one image that belongs to no book page, such as a figure crop."""
    for page in reader.read([PageImage(1, image)]):
        return page.lines
    return ()


def page_images(renders_dir: Path) -> list[PageImage]:
    pages: list[PageImage] = []
    for path in renders_dir.iterdir():
        if path.suffix.lower() not in IMAGE_SUFFIXES or path.name.startswith("._"):
            continue
        number = _TRAILING_NUMBER.search(path.stem)
        if number is None:
            raise ValueError(f"Page render {path.name} has no trailing page number")
        pages.append(PageImage(int(number.group(1)), path))
    return sorted(pages, key=lambda page: page.number)
