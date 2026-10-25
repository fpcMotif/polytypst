"""A book is a source scan plus the editions polytypst can rebuild from it; `polytypst build` and `polytypst parity` read these."""

import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from .book_state import book_state
from .compiler.monograph import (
    MONOGRAPH_FORMATS,
    MonographCompiler,
    MonographOutputs,
    MonographSpec,
    adhoc_spec,
    running_footnotes,
)
from .facsimile import FacsimileStyle, build_facsimile
from .ocr.backend import Backend
from .ocr.scan import SourceScan
from .ocr.transcripts import TranscriptStore
from .parity.diagrams import DiagramText
from .parity.report import FACSIMILE, Tolerance
from .parity.source import source_ocr_dir, source_pdf
from .vision.figure_extractor import extract_book_figures

OUTPUT = Path("output")
RENDER_DPI = 200
PAGE_FIT = "page_fit.json"


def install_page_fit(out_dir: Path) -> None:
    kept = book_state(out_dir) / PAGE_FIT
    if not kept.exists():
        kept.parent.mkdir(parents=True, exist_ok=True)
        _ = kept.write_text("{}\n", encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    _ = shutil.copy2(kept, out_dir / PAGE_FIT)


@dataclass(frozen=True)
class VisualLimits:
    """The largest optical-parity values a page may have: ink shares from 0 to 1, and the text block offset in pt.
    An edition with these limits is checked optically by default, and `polytypst parity` exits 1 above any of them."""

    missing: float | None = None
    extra: float | None = None
    layout: float | None = None
    offset: float | None = None


@dataclass(frozen=True)
class Parity:
    """How to check an edition against the source scan: its page map, tolerance, and diagram snippets."""

    page_map: Callable[[], dict[int, list[int]]]
    tolerance: Tolerance
    diagrams: Path | None = None
    diagram_text: DiagramText | None = None
    visual: VisualLimits | None = None


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
    scan_line_breaks: bool = False


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

    @property
    def transcripts(self) -> Path:
        return book_state(self.out_dir) / self.spec.markdown_dir

    @classmethod
    def adhoc(
        cls, source: Path, out_dir: Path | None = None, publisher_key: str = "cambridge", lang: str = "en",
        domain: str = "math",
    ) -> "Book":
        """A one-chapter book for a source scan that no `src/<key>/book.py` describes, in `output/<slug>` by default."""
        spec = adhoc_spec(Path(source), SourceScan(source).page_count, publisher_key, lang, domain)
        out_dir = out_dir or OUTPUT / spec.slug
        return cls(spec, out_dir, {"monograph": monograph_edition(spec, out_dir, "one chapter, generic rules")})

    def transcribe(
        self, source: Path, backend: Backend, pages: set[int] | None = None, retranscribe: bool = False
    ) -> dict[int, str]:
        """Render the scan into `page_renders/`, find its figures, and transcribe the pages the store lacks."""
        scan = SourceScan(source)
        if self.spec.pdf_page_count not in (None, scan.page_count):
            print(f"Warning: {self.spec.slug} expects {self.spec.pdf_page_count} pages; {source} has {scan.page_count}")
        split = " (2-up spreads split down the spine)" if scan.split else ""
        print(f"Rendering {scan.page_count} pages from {Path(source).name}{split} at {RENDER_DPI} DPI...")
        renders = scan.pages(self.out_dir / "page_renders", dpi=RENDER_DPI)
        if scan.pdf is not None:
            _ = extract_book_figures(scan.pdf, self.out_dir, renders, self.transcripts, self.spec.ocr_languages)
        else:
            print("Skipping figure extraction: it reads the PDF, and this scan's pages are not PDF pages.")
        if pages:
            renders = [p for p in renders if p.number in pages]
        transcriber = backend.transcriber(self.spec.ocr_prompt)
        print(f"Transcribing with {transcriber.provenance}")
        return TranscriptStore(self.transcripts).transcribe(renders, transcriber, retranscribe=retranscribe)

    def build(
        self,
        edition_name: str | None = None,
        source: Path | None = None,
        formats: frozenset[str] | None = None,
        footnotes: str = "original",
    ) -> Edition:
        name = edition_name or next(iter(self.editions))
        edition = self.editions[name]
        if self.figures is not None:
            if source is not None or self.spec.source_pdf:
                scan = SourceScan(source if source is not None else source_pdf(self.spec))
                _ = scan.pages(self.out_dir / "page_renders", dpi=RENDER_DPI)
            _ = self.figures(self.out_dir)
        edition.build(
            source, edition.formats if formats is None else formats, footnotes
        )
        return edition



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


def facsimile_edition(
    spec: MonographSpec, out_dir: Path, style: FacsimileStyle,
    summary: str = "every OCR word placed on its scan ink box",
    visual: VisualLimits | None = None,
) -> Edition:
    rebuilt = out_dir / f"{style.slug}.pdf"

    def page_map() -> dict[int, list[int]]:
        if not rebuilt.exists():
            return {}
        pages = int(pymupdf.open(rebuilt).page_count)
        return {p: [p] for p in range(1, pages + 1)}

    def build(source: Path | None, _formats: frozenset[str], _footnotes: str) -> None:
        pdf = build_facsimile(source_pdf(spec, source), out_dir, spec.ocr_languages, style)
        print(f"{pdf}: {int(pymupdf.open(pdf).page_count)} pages")

    return Edition(
        rebuilt, build, summary,
        Parity(page_map, FACSIMILE, style.diagram_dir, style.diagram_text, visual),
        scan_line_breaks=True,
    )

