"""Universal KISS Document Intelligence Pipeline for any PDF (Math, Econ, Physics, etc.)."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .books import render_book_figures
from .compiler.monograph import (
    MonographCompiler,
    MonographOutputs,
    resolve_monograph_spec,
)
from .ocr.backend import DEFAULT_BACKEND, Backend
from .ocr.lines import DEFAULT_OCR_LANGUAGES, LineStore, line_reader
from .ocr.pages import LinePage, PageImage, page_images
from .ocr.scan import SourceScan
from .ocr.transcripts import TranscriptStore
from .tex_markdown import stitch_document
from .vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    FigureExtractor,
    load_complete_figures_manifest,
    write_figures_manifest,
)


@dataclass
class PipelineResult:
    source: Path
    total_pages: int
    output_dir: Path
    master_markdown_path: Path
    figures: list[ExtractedFigure]
    monograph: MonographOutputs | None = None


class UniversalPDFPipeline:
    """End-to-end KISS pipeline to turn any PDF into TeX-compatible Markdown and Typst."""

    def __init__(
        self,
        source: Path,
        output_dir: Path,
        backend: Backend | None = None,
        render_dpi: int = 200,
        running_headers: list[str] | None = None,
        publisher: str = "cambridge",
        lang: str = "en",
        domain: str = "math",
        ocr_prompt: str | None = None,
        pages: set[int] | None = None,
        retranscribe: bool = False,
    ):
        self.backend: Backend = backend or Backend.parse(DEFAULT_BACKEND)
        self.ocr_prompt: str | None = ocr_prompt
        self.pages: set[int] | None = pages
        self.retranscribe: bool = retranscribe
        self.source: Path = Path(source)
        self.output_dir: Path = Path(output_dir)
        self.render_dpi: int = render_dpi
        self.running_headers: list[str] = running_headers or []
        self.publisher: str = publisher
        self.lang: str = lang
        self.domain: str = domain

        self.renders_dir: Path = self.output_dir / "page_renders"
        self.figures_dir: Path = self.output_dir / "figures"
        self.markdown_dir: Path = self.output_dir / "markdown_pages"

    def render_all_pages(self, scan: SourceScan) -> list[PageImage]:
        """Render every page of the source scan that `renders_dir` lacks, with 2-up spreads split."""
        split = " (2-up spreads split down the spine)" if scan.split else ""
        print(f"Rendering {scan.page_count} pages from {self.source.name}{split} at {self.render_dpi} DPI...")
        pages = scan.pages(self.renders_dir, dpi=self.render_dpi)
        print(f"{len(pages)} page images in {self.renders_dir}.")
        return pages

    def extract_figures(
        self,
        rendered_pages: list[PageImage],
        ocr_languages: Sequence[str] = DEFAULT_OCR_LANGUAGES,
    ) -> list[ExtractedFigure]:
        """Automatically detect, crop, and catalogue all figures in the PDF."""
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.output_dir / FIGURES_MANIFEST_NAME
        cached = load_complete_figures_manifest(manifest_path)
        if cached is not None:
            return cached
        extractor = FigureExtractor(self.source, line_reader(ocr_languages))

        # First run fast local Apple Vision OCR for layout and figure caption detection
        print(
            "Running Apple Vision OCR pass for figure grounding and double-checking..."
        )
        figures = extractor.extract_whitespace_isolated_figures(
            self.renders_dir, self.figures_dir
        )
        if not figures and rendered_pages:
            store = LineStore(self.output_dir / "source_ocr")
            lines = store.read(rendered_pages, extractor.reader)
            ocr_pages = [LinePage(number, page_lines) for number, page_lines in lines.items()]
            figures = extractor.extract_all(
                self.figures_dir, ocr_pages=ocr_pages, dpi=300
            )
        write_figures_manifest(manifest_path, figures)
        print(f"Extracted {len(figures)} figures into {self.figures_dir}.")
        return figures

    def run_transcription(self) -> dict[int, str]:
        """Transcribe the rendered pages that the store lacks, limited to `pages` when set."""
        pages = page_images(self.renders_dir)
        if self.pages:
            pages = [p for p in pages if p.number in self.pages]
        transcriber = self.backend.transcriber(self.ocr_prompt)
        print(f"Transcribing with {transcriber.provenance}")
        return TranscriptStore(self.markdown_dir).transcribe(
            pages, transcriber, retranscribe=self.retranscribe
        )

    def process(self) -> PipelineResult:
        """Run full end-to-end pipeline: render -> figures -> OCR -> clean/stitch."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        scan = SourceScan(self.source)
        total_pages = scan.page_count
        spec = resolve_monograph_spec(
            self.source,
            total_pages,
            publisher_key=self.publisher,
            lang=self.lang,
            domain=self.domain,
        )
        if self.ocr_prompt is None:
            self.ocr_prompt = spec.ocr_prompt
        self.markdown_dir = self.output_dir / spec.markdown_dir

        # Step 1: Render pages
        rendered_pages = self.render_all_pages(scan)

        # Step 2: Extract & Ground all figures
        if scan.pdf is not None:
            figures = self.extract_figures(rendered_pages, spec.ocr_languages)
        else:
            figures = []
            print("Skipping figure extraction: it reads the PDF, and this scan's pages are not PDF pages.")

        # Step 3: Transcribe the pages the transcript store lacks
        pages_md = self.run_transcription()

        # Step 4: Clean, ground figures, and stitch into TeX-compatible Markdown
        print(
            "Cleaning math formulas, grounding figures, and stitching master document..."
        )
        if spec.chapters:
            if render_book_figures(spec.slug, self.output_dir):
                print(f"Generated vector SVG figures and web gallery for {spec.slug}")
            monograph_compiler = MonographCompiler(spec)
            monograph_out = monograph_compiler.build_all(self.output_dir)
            master_path = monograph_out.markdown_path
            print(
                f"SUCCESS: Compiled Monograph:\n"
                f"  Markdown: {monograph_out.markdown_path}\n"
                f"  LaTeX:    {monograph_out.latex_path}\n"
                f"  Typst:    {monograph_out.typst_path}\n"
                f"  PDF:      {monograph_out.pdf_path} ({monograph_out.total_pages} pages)"
            )
            return PipelineResult(
                source=self.source,
                total_pages=total_pages,
                output_dir=self.output_dir,
                master_markdown_path=master_path,
                figures=figures,
                monograph=monograph_out,
            )

        master_markdown = stitch_document(
            sorted(pages_md.items()),
            figures=figures,
            running_headers=self.running_headers,
        )

        master_path = self.output_dir / "book.md"
        _ = master_path.write_text(master_markdown, encoding="utf-8")
        print(
            f"SUCCESS: Generated TeX-compatible master Markdown: {master_path} ({master_path.stat().st_size / 1024:.1f} KB)"
        )

        return PipelineResult(
            source=self.source,
            total_pages=total_pages,
            output_dir=self.output_dir,
            master_markdown_path=master_path,
            figures=figures,
        )
