"""Universal KISS Document Intelligence Pipeline for any PDF (Math, Econ, Physics, etc.)."""

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from .books import render_book_figures
from .compiler.monograph import (
    MonographCompiler,
    MonographOutputs,
    resolve_monograph_spec,
)
from .ocr.apple_vision import AppleVisionOCREngine
from .ocr.backend import DEFAULT_BACKEND, Backend
from .ocr.pages import page_images
from .ocr.splitter import TwoUpSplitter
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
    pdf_path: Path
    total_pages: int
    output_dir: Path
    master_markdown_path: Path
    figures: list[ExtractedFigure]
    monograph: MonographOutputs | None = None


class UniversalPDFPipeline:
    """End-to-end KISS pipeline to turn any PDF into TeX-compatible Markdown and Typst."""

    def __init__(
        self,
        pdf_path: Path,
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
        self.pdf_path: Path = Path(pdf_path)
        self.output_dir: Path = Path(output_dir)
        self.render_dpi: int = render_dpi
        self.running_headers: list[str] = running_headers or []
        self.publisher: str = publisher
        self.lang: str = lang
        self.domain: str = domain

        self.renders_dir: Path = self.output_dir / "page_renders"
        self.figures_dir: Path = self.output_dir / "figures"
        self.markdown_dir: Path = self.output_dir / "markdown_pages"

    def render_all_pages(self) -> list[Path]:
        """Render all pages from PDF to image directory, handling 2-up spreads if present."""
        self.renders_dir.mkdir(parents=True, exist_ok=True)
        existing = sorted(self.renders_dir.glob("p_*.png"))
        doc = pymupdf.open(self.pdf_path)
        total_pages = len(doc)
        if len(existing) >= max(1, total_pages - 15):
            print(
                f"Loaded {len(existing)} existing page images from {self.renders_dir}."
            )
            return existing

        print(
            f"Rendering {total_pages} pages from {self.pdf_path.name} at {self.render_dpi} DPI..."
        )

        splitter = TwoUpSplitter(self.pdf_path)
        if splitter.is_two_up():
            print(
                "Detected 2-up scanned book spread. Splitting down spine into single portrait pages..."
            )
            return splitter.split_and_render_all(self.renders_dir, dpi=self.render_dpi)

        rendered_paths: list[Path] = []
        for i in range(total_pages):
            out_p = self.renders_dir / f"p_{i + 1:03d}.png"
            if not out_p.exists():
                page = doc[i]
                imgs = page.get_images()
                saved_native = False
                if len(imgs) == 1:
                    xref = imgs[0][0]
                    base_img = doc.extract_image(xref)
                    if (
                        base_img
                        and str(base_img.get("ext", "")) == "png"
                        and int(base_img.get("width", 0)) >= 1000
                    ):
                        _ = out_p.write_bytes(bytes(base_img["image"]))
                        saved_native = True
                if not saved_native:
                    pix = page.get_pixmap(dpi=self.render_dpi)
                    pix.save(out_p)
            rendered_paths.append(out_p)

        print(f"Rendered {len(rendered_paths)} page images in {self.renders_dir}.")
        return rendered_paths

    def extract_figures(
        self,
        rendered_pages: list[Path],
        ocr_languages: list[str] | None = None,
    ) -> list[ExtractedFigure]:
        """Automatically detect, crop, and catalogue all figures in the PDF."""
        _ = ocr_languages
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.output_dir / FIGURES_MANIFEST_NAME
        cached = load_complete_figures_manifest(manifest_path)
        if cached is not None:
            return cached
        extractor = FigureExtractor(self.pdf_path)

        # First run fast local Apple Vision OCR for layout and figure caption detection
        print(
            "Running Apple Vision OCR pass for figure grounding and double-checking..."
        )
        figures = extractor.extract_whitespace_isolated_figures(
            self.renders_dir, self.figures_dir
        )
        if not figures and rendered_pages:
            apple_engine = AppleVisionOCREngine(languages=["en-US", "fr-FR", "zh-Hans"])
            ocr_pages = apple_engine.recognize_document(rendered_pages)
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
        t_start = pymupdf.open(self.pdf_path)
        total_pages = len(t_start)
        spec = resolve_monograph_spec(
            self.pdf_path,
            total_pages,
            publisher_key=self.publisher,
            lang=self.lang,
            domain=self.domain,
        )
        if self.ocr_prompt is None:
            self.ocr_prompt = spec.ocr_prompt
        self.markdown_dir = self.output_dir / spec.markdown_dir

        # Step 1: Render pages
        rendered_pages = self.render_all_pages()

        # Step 2: Extract & Ground all figures
        figures = self.extract_figures(rendered_pages)

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
                pdf_path=self.pdf_path,
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
            pdf_path=self.pdf_path,
            total_pages=total_pages,
            output_dir=self.output_dir,
            master_markdown_path=master_path,
            figures=figures,
        )
