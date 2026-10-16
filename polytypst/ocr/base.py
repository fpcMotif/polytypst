"""Base definitions for OCR engines in polytypst."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


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
    lines: List[OCRLine] = field(default_factory=list)
    raw_text: Optional[str] = None


class OCREngine(ABC):
    @abstractmethod
    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        """Run OCR on a single rendered page image."""
        pass

    @abstractmethod
    def recognize_document(self, image_paths: List[Path]) -> List[OCRPage]:
        """Run OCR on an entire sequence of page images."""
        pass
