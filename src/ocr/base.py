"""Base definitions for OCR engines in polytypst."""

import re
import unicodedata
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OCRLine:
    text: str
    x: float  # Normalized 0.0 - 1.0 (left)
    y: float  # Normalized 0.0 - 1.0 (bottom or top depending on engine, normalized to bottom-left 0,0)
    w: float  # Normalized width
    h: float  # Normalized height
    confidence: float = 1.0
    is_heading: bool = False
    heading_level: int = 0


@dataclass
class OCRPage:
    page_number: int
    width: int
    height: int
    lines: list[OCRLine] = field(default_factory=list)
    raw_text: str | None = None


MIN_TRANSCRIPT_BYTES = 30
_FENCED_RE = re.compile(
    r"\A\s*```(?:markdown|md|latex|tex)?\s*\n(.*?)\n\s*```\s*\Z", re.DOTALL
)
_OPEN_FENCE_RE = re.compile(r"\A\s*```(?:markdown|md|latex|tex)?[^\n]*\n")
_CLOSE_FENCE_RE = re.compile(r"\n\s*```\s*\Z")


def page_number(image_path: Path) -> int:
    """The page number at the end of a render name such as `p_012.png` or `page_12.png`."""
    m = re.search(r"(\d+)$", image_path.stem)
    if m is None:
        raise ValueError(f"Page render {image_path.name} has no trailing page number")
    return int(m.group(1))


def transcript_path(out_dir: Path, number: int) -> Path:
    return out_dir / f"p_{number:03d}.md"


def pending_pages(pages: Sequence[Path], out_dir: Path) -> list[Path]:
    """Pages whose transcript is missing or shorter than `MIN_TRANSCRIPT_BYTES`."""
    return [
        p
        for p in pages
        if not (t := transcript_path(out_dir, page_number(p))).exists()
        or t.stat().st_size < MIN_TRANSCRIPT_BYTES
    ]


def read_transcripts(out_dir: Path, pages: Sequence[Path]) -> list[tuple[int, str]]:
    """The transcripts of `pages` that exist in `out_dir`, in page order."""
    found: list[tuple[int, str]] = []
    for n in sorted({page_number(p) for p in pages}):
        t = transcript_path(out_dir, n)
        if t.exists():
            found.append((n, t.read_text(encoding="utf-8")))
    return found


def normalize_ocr_markdown(decoded: object) -> str:
    """Coerce raw OCR output to NFC Markdown without a wrapping code fence."""
    if isinstance(decoded, (list, tuple)):
        decoded = decoded[0] if decoded else ""
    text = unicodedata.normalize("NFC", str(decoded)).replace("\r\n", "\n")
    m = _FENCED_RE.match(text)
    if m:
        text = m.group(1)
    elif _OPEN_FENCE_RE.match(text):
        # A fence the model never closed would swallow the rest of the book.
        text = _CLOSE_FENCE_RE.sub("\n", _OPEN_FENCE_RE.sub("", text, count=1))
    return text.strip() + "\n" if text.strip() else ""


class OCREngine(ABC):
    @abstractmethod
    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        """Run OCR on a single rendered page image."""

    @abstractmethod
    def recognize_document(self, image_paths: list[Path]) -> list[OCRPage]:
        """Run OCR on an entire sequence of page images."""

    def transcribe_pages(
        self, pages: Sequence[Path], out_dir: Path
    ) -> list[tuple[int, str]]:
        """Write `p_NNN.md` for every page not yet transcribed, then return all transcripts."""
        out_dir.mkdir(parents=True, exist_ok=True)
        for image_path in pending_pages(pages, out_dir):
            n = page_number(image_path)
            page = self.recognize_page(image_path, n)
            text = (
                page.raw_text
                if page.raw_text is not None
                else "\n\n".join(line.text for line in page.lines)
            )
            _ = transcript_path(out_dir, n).write_text(
                normalize_ocr_markdown(text), encoding="utf-8"
            )
        return read_transcripts(out_dir, pages)
