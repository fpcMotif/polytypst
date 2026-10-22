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
