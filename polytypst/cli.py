"""Command-line interface for polytypst."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pymupdf

from .compiler.epub import PandocCompilers
from .compiler.typst import TypstCompiler
from .ocr.apple_vision import AppleVisionOCREngine
from .ocr.base import OCRLine, OCRPage
from .ocr.colab import COLAB_GPUS
from .ocr.jina import JinaCloudOCREngine
from .ocr.mistral import MistralOCREngine
from .ocr.ocr_models import DEFAULT_OCR_MODEL, OCR_MODELS
from .ocr.splitter import TwoUpSplitter
from .ocr.tesseract import TesseractOCREngine
from .parser.stitcher import DocumentStitcher, FigureBlock
from .vision.vector_figures import generate_all_vector_figures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="polytypst: Universal tool to turn complex PDFs into beautiful Typst, LaTeX, and EPUB."
    )
    parser.add_argument(
        "pdf_path", type=Path, nargs="?", help="Path to input PDF document"
    )
    parser.add_argument(
        "--book",
        type=str,
        choices=["modern-firm", "serre", "kerodon", "all"],
        help="Build canonical book deliverables",
    )
    parser.add_argument(
        "--export-web",
        action="store_true",
        help="Export web catalog and static assets to polytypst/web/public",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("output"), help="Output directory"
    )
    parser.add_argument(
        "--formats",
        type=str,
        default="typst,pdf,epub,latex",
        help="Comma-separated formats: typst,pdf,epub,latex",
    )
    parser.add_argument(
        "--ocr-engine",
        type=str,
        choices=["apple_vision", "mistral", "jina", "tesseract"],
        default="jina",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["colab", "jina-cloud", "local", "apple-vision"],
        default="colab",
        help="Execution engine mode: colab (self-hosted model on Colab GPUs), jina-cloud, local, or apple-vision",
    )
    parser.add_argument(
        "--ocr-model",
        choices=sorted(OCR_MODELS),
        default=DEFAULT_OCR_MODEL,
        help="Self-hosted OCR model for the colab and local modes",
    )
    parser.add_argument(
        "--gpu-type",
        choices=sorted(COLAB_GPUS),
        default="G4",
        help="Colab GPU accelerator; see `polytypst-colab gpus`",
    )
    parser.add_argument(
        "--colab-workers", type=int, default=2, help="Number of Colab GPU workers"
    )
    parser.add_argument(
        "--shards",
        type=int,
        default=3,
        help="Most model copies per GPU; the worker lowers it to fit the VRAM",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Disable Apple Vision cross-verification",
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="zh-Hans,en-US,fr-FR",
        help="Comma-separated OCR languages",
    )
    parser.add_argument(
        "--font-style",
        type=str,
        choices=["songti", "pingfang"],
        default="songti",
        help="Primary CJK typography: songti (academic serif) or pingfang (modern sans)",
    )
    parser.add_argument(
        "--columns",
        type=int,
        choices=[1, 2],
        default=1,
        help="Number of text columns (1 for standard book, 2 for academic math)",
    )
    parser.add_argument(
        "--vector-graphics",
        action="store_true",
        default=True,
        help="Generate clean vector SVG graphics for diagrams",
    )
    parser.add_argument(
        "--use-jev",
        action="store_true",
        default=True,
        help="Use TypeSafe Jev 1.14 Box primitive for diagram localization",
    )
    parser.add_argument(
        "--publisher",
        type=str,
        choices=["cambridge", "springer", "mit", "harvard", "ams"],
        default="cambridge",
        help="Publisher house preset",
    )
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en", "ja", "fr", "zh"],
        default="en",
        help="Primary document language profile",
    )
    parser.add_argument(
        "--domain",
        type=str,
        choices=["math", "physics", "economics", "philosophy", "history", "novel"],
        default="math",
        help="Subject domain profile",
    )
    args = parser.parse_args()

    if args.export_web:
        from .web_exporter import export_all_web_data

        root_dir = Path(__file__).resolve().parents[2]
        web_pub = Path(__file__).resolve().parents[1] / "web" / "public"
        export_all_web_data(root_dir, web_pub)
        print(f"Exported web catalog and assets to {web_pub}")
        if not args.book and not args.pdf_path:
            return

    if not args.pdf_path or not args.pdf_path.exists():
        print(f"Error: File {args.pdf_path} does not exist.")
        sys.exit(1)

    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    if not args.book:
        from .core.pipeline import UniversalPDFPipeline

        pipeline = UniversalPDFPipeline(
            pdf_path=args.pdf_path,
            output_dir=out_dir,
            gpu_type=args.gpu_type,
            num_colab_workers=args.colab_workers,
            shards_per_gpu=args.shards,
            ocr_model=args.ocr_model,
            publisher=args.publisher,
            lang=args.lang,
            domain=args.domain,
        )
        res = pipeline.process(
            mode=args.mode, double_check_with_mac=(not args.no_verify)
        )
        print(f"\n🎉 polytypst build complete! Master file: {res.master_markdown_path}")
        return

    print(f"=== polytypst processing: {args.pdf_path.name} ===")
    print(f"Target formats: {args.formats}")
    print(f"OCR engine: {args.ocr_engine}")
    print(f"CJK Font style: {args.font_style}")

    # Generate vector diagrams
    if args.vector_graphics:
        print("Generating crisp publication-grade vector SVGs for all diagrams...")
        generate_all_vector_figures(figures_dir)

    # Check for existing OCR cache or run OCR
    cache_dir = out_dir / "cache_ocr"
    cache_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(args.pdf_path)
    total_pages = len(doc)
    print(f"Total pages in document: {total_pages}")

    cached_jsons = sorted(cache_dir.glob("page_*.json"))
    ocr_pages = []

    if len(cached_jsons) == total_pages:
        print(f"Loaded {total_pages} cached OCR pages from {cache_dir}.")
        for f in cached_jsons:
            with open(f) as fp:
                data = json.load(fp)
            lines = [
                OCRLine(l["text"], l["x"], l["y"], l["w"], l["h"])
                for l in data.get("lines", [])
            ]
            ocr_pages.append(
                OCRPage(
                    data["page"], data.get("width", 0), data.get("height", 0), lines
                )
            )
    else:
        print(f"Rendering {total_pages} pages to temporary directory...")
        temp_img_dir = out_dir / "temp_page_renders"
        splitter = TwoUpSplitter(args.pdf_path)
        if splitter.is_two_up():
            print(
                "Detected 2-up scanned book spreads. Splitting down spine into single portrait pages..."
            )
            img_paths = splitter.split_and_render_all(temp_img_dir, dpi=150)
        else:
            img_paths = []
            for i in range(total_pages):
                page = doc[i]
                pix = page.get_pixmap(dpi=150)
                p_path = temp_img_dir / f"p_{i + 1:03d}.png"
                pix.save(p_path)
                img_paths.append(p_path)

        print(
            f"Running OCR on {len(img_paths)} pages with engine '{args.ocr_engine}'..."
        )
        if args.ocr_engine == "apple_vision":
            engine = AppleVisionOCREngine(languages=args.languages.split(","))
        elif args.ocr_engine == "mistral":
            engine = MistralOCREngine()
        elif args.ocr_engine == "jina":
            engine = JinaCloudOCREngine()
        else:
            engine = TesseractOCREngine(languages=args.languages)
        ocr_pages = engine.recognize_document(img_paths)
        for p in ocr_pages:
            with open(cache_dir / f"page_{p.page_number:03d}.json", "w") as fp:
                json.dump(
                    {
                        "page": p.page_number,
                        "width": p.width,
                        "height": p.height,
                        "lines": [
                            {"text": l.text, "x": l.x, "y": l.y, "w": l.w, "h": l.h}
                            for l in p.lines
                        ],
                    },
                    fp,
                )

    # Figures map
    figures_map = {}
    known_figures = [
        (1, 22, "图1 设计问题就是在特定的环境下选择战略和组织以达到最大绩效"),
        (2, 34, "图2 互补性可以产生离散的内在相互匹配模式"),
        (3, 42, "图3 选择和绩效关系的经典模型"),
        (4, 43, "图4 选择和绩效的关系发生改变"),
        (5, 45, "图5 非凹性的绩效关系"),
        (6, 46, "图6 非凹性允许存在多个不同的内在相互匹配的点"),
        (7, 48, "图7 非凹性绩效关系转变导致最佳绩效点的不连续改变"),
        (8, 74, "图8 合作和主动行为"),
        (9, 125, "图9 长期关系拓宽了可实现的行为的组合"),
    ]

    for fig_id, pno, cap_text in known_figures:
        # Prefer vector SVG if exists, else PNG
        svg_file = figures_dir / f"fig_{fig_id}.svg"
        if svg_file.exists():
            img_rel = f"figures/fig_{fig_id}.svg"
        else:
            img_rel = f"figures/fig_{fig_id}.png"

        figures_map[fig_id] = FigureBlock(
            figure_id=fig_id, caption=cap_text, image_rel_path=img_rel, source_page=pno
        )

    print(f"Grounded {len(figures_map)} figures.")

    # Stitch document
    print("Stitching document structure and hierarchy...")
    stitcher = DocumentStitcher(ocr_pages, figures_map=figures_map)
    book = stitcher.stitch_document()

    formats = [f.strip().lower() for f in args.formats.split(",")]

    # Typst Compiler
    typst_compiler = TypstCompiler(book, font_style=args.font_style)
    typ_source = typst_compiler.generate_typst_source()
    typ_path = out_dir / "book.typ"
    with open(typ_path, "w", encoding="utf-8") as f:
        f.write(typ_source)
    print(f"Generated Typst source: {typ_path} ({len(typ_source)} chars)")

    if "typst" in formats or "pdf" in formats:
        pdf_path = out_dir / "book.pdf"
        print(f"Compiling Typst to PDF: {pdf_path}...")
        try:
            typst_compiler.compile_pdf(typ_path, pdf_path)
            print(
                f"SUCCESS: Typst PDF generated at {pdf_path} ({pdf_path.stat().st_size / (1024 * 1024):.2f} MB)"
            )
        except (subprocess.SubprocessError, OSError, RuntimeError) as e:
            print(f"Typst compilation warning: {e}")

    # Pandoc Markdown, EPUB & LaTeX Compilers
    pandoc_compiler = PandocCompilers(book)
    md_source = pandoc_compiler.generate_markdown()
    md_path = out_dir / "book.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_source)
    print(f"Generated Markdown source: {md_path} ({len(md_source)} chars)")

    if "epub" in formats:
        epub_path = out_dir / "book.epub"
        print(f"Compiling EPUB via Pandoc: {epub_path}...")
        try:
            pandoc_compiler.compile_epub(md_path, epub_path)
            print(
                f"SUCCESS: EPUB generated at {epub_path} ({epub_path.stat().st_size / (1024 * 1024):.2f} MB)"
            )
        except (subprocess.SubprocessError, OSError, RuntimeError) as e:
            print(f"EPUB compilation warning: {e}")

    if "latex" in formats or "tex" in formats:
        tex_path = out_dir / "book.tex"
        print(f"Compiling LaTeX via Pandoc: {tex_path}...")
        try:
            pandoc_compiler.compile_latex(md_path, tex_path)
            print(
                f"SUCCESS: LaTeX generated at {tex_path} ({tex_path.stat().st_size / (1024 * 1024):.2f} MB)"
            )
        except (subprocess.SubprocessError, OSError, RuntimeError) as e:
            print(f"LaTeX generation warning: {e}")

    print("\n🎉 polytypst build complete!")


if __name__ == "__main__":
    main()
