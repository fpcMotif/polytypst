"""A book is a source scan plus the editions polytypst can rebuild from it; `polytypst build` and `polytypst parity` read these."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .compiler.monograph import MonographCompiler, MonographSpec
from .parity.diagrams import DiagramText
from .parity.report import Tolerance
from .parity.source import source_ocr_dir

OUTPUT = Path("output")


@dataclass(frozen=True)
class Parity:
    """How to check an edition against the source scan: its page map, tolerance, and diagram snippets."""

    page_map: Callable[[], dict[int, list[int]]]
    tolerance: Tolerance
    diagrams: Path | None = None
    diagram_text: DiagramText | None = None


@dataclass(frozen=True)
class Edition:
    """One rebuild of a book. `build` takes an explicit source scan path, or None for the spec's."""

    rebuilt: Path
    build: Callable[[Path | None], None]
    summary: str = ""
    parity: Parity | None = None
    spec: MonographSpec | None = None


@dataclass(frozen=True)
class Book:
    """A book lives in `polytypst/<key>/book.py` as `BOOK`. The first edition is the default."""

    spec: MonographSpec
    out_dir: Path
    editions: dict[str, Edition] = field(default_factory=dict)
    figures: Callable[[Path], object] | None = None

    @property
    def ocr(self) -> Path:
        return source_ocr_dir(self.out_dir)


def monograph_edition(
    spec: MonographSpec, out_dir: Path, summary: str = "", prepare: Callable[[Path | None], None] | None = None,
    parity: Parity | None = None,
) -> Edition:
    """An edition built by compiling the book's OCR pages with `MonographCompiler`."""

    def build(source: Path | None) -> None:
        if prepare is not None:
            prepare(source)
        outputs = MonographCompiler(spec).build_all(out_dir)
        print(f"{outputs.pdf_path}: {outputs.total_pages} pages")

    return Edition(out_dir / f"{spec.slug}.pdf", build, summary, parity, spec)
