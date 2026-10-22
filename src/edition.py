"""A book is a source scan plus the editions polytypst can rebuild from it; `polytypst build` and `polytypst parity` read these."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .compiler.monograph import (
    MONOGRAPH_FORMATS,
    MonographCompiler,
    MonographOutputs,
    MonographSpec,
    running_footnotes,
)
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
    """One rebuild of a book. `build` takes an explicit source scan path, or None for the spec's,
    the subset of the optional `formats` to make beside the outputs it always writes,
    and "original" for the scan's footnote marks or "running" for 1, 2, 3 through the book."""

    rebuilt: Path
    build: Callable[[Path | None, frozenset[str], str], None]
    summary: str = ""
    parity: Parity | None = None
    spec: MonographSpec | None = None
    formats: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Book:
    """A book lives in `src/<key>/book.py` as `BOOK`. The first edition is the default."""

    spec: MonographSpec
    out_dir: Path
    editions: dict[str, Edition] = field(default_factory=dict)
    figures: Callable[[Path], object] | None = None

    @property
    def ocr(self) -> Path:
        return source_ocr_dir(self.out_dir)


def report_build(outputs: MonographOutputs) -> None:
    """Print the PDF and its page count, or the Typst file when no PDF was made."""
    if outputs.pdf_path is not None:
        print(f"{outputs.pdf_path}: {outputs.total_pages} pages")
    else:
        print(outputs.typst_path)


def monograph_edition(
    spec: MonographSpec, out_dir: Path, summary: str = "", prepare: Callable[[Path | None], None] | None = None,
    parity: Parity | None = None,
) -> Edition:
    """An edition built by compiling the book's OCR pages with `MonographCompiler`."""

    def build(source: Path | None, formats: frozenset[str], footnotes: str) -> None:
        if prepare is not None:
            prepare(source)
        built = running_footnotes(spec) if footnotes == "running" else spec
        report_build(MonographCompiler(built).build_all(out_dir, formats))

    return Edition(out_dir / f"{spec.slug}.pdf", build, summary, parity, spec, MONOGRAPH_FORMATS)
