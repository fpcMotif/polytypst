"""Universal KISS Document Intelligence Pipeline for any PDF (Math, Econ, Physics, etc.)."""

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from ..cleaner.tex_markdown import TeXMarkdownCleaner
from ..compiler.monograph import (
    MonographCompiler,
    MonographOutputs,
    resolve_monograph_spec,
)
from ..ocr.apple_vision import AppleVisionOCREngine
from ..ocr.dual_colab import DualColabG4Cluster
from ..ocr.splitter import TwoUpSplitter
from ..ocr.verifier import OCRVerifier, VerificationReport
from ..vision.figure_extractor import ExtractedFigure, FigureExtractor


@dataclass
class PipelineResult:
    pdf_path: Path
    total_pages: int
    output_dir: Path
    master_markdown_path: Path
    figures: list[ExtractedFigure]
    verification: VerificationReport | None = None
    monograph: MonographOutputs | None = None


class UniversalPDFPipeline:
    """End-to-end KISS pipeline to turn any PDF into TeX-compatible Markdown and Typst."""

    def __init__(
        self,
        pdf_path: Path,
        output_dir: Path,
        gpu_type: str = "G4",
        num_colab_workers: int = 2,
        shards_per_gpu: int = 3,
        render_dpi: int = 200,
        running_headers: list[str] | None = None,
    ):
        self.pdf_path: Path = Path(pdf_path)
        self.output_dir: Path = Path(output_dir)
        self.gpu_type: str = gpu_type
        self.num_colab_workers: int = num_colab_workers
        self.shards_per_gpu: int = shards_per_gpu
        self.render_dpi: int = render_dpi
        self.running_headers: list[str] = running_headers or []

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
        print(f"Extracted {len(figures)} figures into {self.figures_dir}.")
        return figures

    def run_transcription(
        self,
        mode: str = "dual-g4",
        page_subset: list[int] | None = None,
    ) -> list[tuple[int, str]]:
        """Execute OCR transcription using Dual-G4 Colab or local engine."""
        self.markdown_dir.mkdir(parents=True, exist_ok=True)

        if mode == "dual-g4":
            cluster = DualColabG4Cluster(
                gpu_type=self.gpu_type,
                num_workers=self.num_colab_workers,
                shards_per_gpu=self.shards_per_gpu,
            )
            if cluster.is_colab_available():
                print(
                    f"Launching Dual-{self.gpu_type} Colab cluster for Jina OCR v1..."
                )
                _ = cluster.run_cluster(self.renders_dir, self.markdown_dir)
            else:
                print(
                    "Warning: Colab CLI not available or no active credentials. Falling back to local/cached engine."
                )
                self._run_local_worker(page_subset)
        elif mode == "apple-vision":
            print("Running local Apple Vision OCR engine...")
            engine = AppleVisionOCREngine()
            img_files = sorted(self.renders_dir.glob("*.png"))
            pages = engine.recognize_document(img_files)
            for p in pages:
                out_f = self.markdown_dir / f"p_{p.page_number:03d}.md"
                md_content = "\n\n".join(l.text for l in p.lines)
                _ = out_f.write_text(md_content, encoding="utf-8")
        else:
            self._run_local_worker(page_subset)

        # Collect all markdown files
        pages_md: list[tuple[int, str]] = []
        md_files = sorted(self.markdown_dir.glob("p_*.md"))
        for f in md_files:
            try:
                p_num = int(f.stem.split("_")[-1])
            except ValueError:
                p_num = len(pages_md) + 1
            pages_md.append((p_num, f.read_text(encoding="utf-8")))

        return pages_md

    def _run_local_worker(self, page_subset: list[int] | None = None) -> None:
        """Run Jina worker locally using available GPU/MPS/CPU."""
        from ..ocr.jina_worker import run_worker

        run_worker(self.renders_dir, self.markdown_dir, page_subset)

    def process(
        self,
        mode: str = "dual-g4",
        double_check_with_mac: bool = True,
    ) -> PipelineResult:
        """Run full end-to-end pipeline: render -> figures -> OCR -> verify -> clean/stitch."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        t_start = pymupdf.open(self.pdf_path)
        total_pages = len(t_start)

        # Step 1: Render pages
        rendered_pages = self.render_all_pages()

        # Step 2: Extract & Ground all figures
        figures = self.extract_figures(rendered_pages)

        # Step 3: Run OCR transcription (Jina OCR v1)
        pages_md = self.run_transcription(mode=mode)

        # Step 4: Double check with macOS Apple Vision OCR if requested
        verification: VerificationReport | None = None
        if double_check_with_mac and pages_md:
            print(
                "Double-checking Jina OCR transcription with macOS Apple Vision OCR..."
            )
            verifier = OCRVerifier()
            verification = verifier.verify_document(rendered_pages, pages_md)
            print(
                f"Verified {verification.total_pages_verified} pages. Discrepancies found on {len(verification.discrepant_pages)} pages."
            )

        # Step 5: Clean, ground figures, and stitch into TeX-compatible Markdown
        print(
            "Cleaning math formulas, grounding figures, and stitching master document..."
        )
        spec = resolve_monograph_spec(self.pdf_path, total_pages)
        if spec.chapters:
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
                verification=verification,
                monograph=monograph_out,
            )

        cleaner = TeXMarkdownCleaner(running_headers=self.running_headers)
        master_markdown = cleaner.stitch_document(pages_md, figures=figures)

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
            verification=verification,
        )
