"""Command-line runner for reverse engineering Kerodon treatise."""

import argparse
from pathlib import Path
from .extractor import KerodonExtractor
from .diagrams import KerodonDiagramCropper
from .compiler import KerodonCompiler


def main():
    parser = argparse.ArgumentParser(description="Reverse engineer Kerodon into Typst, XeLaTeX, and EPUB")
    parser.add_argument("--cache-dir", type=Path, default=Path("output/kerodon/cache_web"), help="Path to cached web HTML")
    parser.add_argument("--pdf-path", type=Path, default=Path("kerodon.pdf"), help="Path to kerodon.pdf")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output/kerodon"), help="Output directory")
    parser.add_argument("--chapter", type=int, default=1, help="Chapter number to process (default: 1)")
    args = parser.parse_args()

    out_dir = args.output_dir
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== REVERSE ENGINEERING KERODON CHAPTER {args.chapter} ===")
    print("1. Extracting structured mathematical DOM from Kerodon...")
    extractor = KerodonExtractor(args.cache_dir)
    chapter = extractor.extract_chapter_1()
    print(f"   Chapter {chapter.number}: {chapter.title} ({len(chapter.sections)} sections)")

    print("\n2. Cropping commutative diagrams from kerodon.pdf...")
    cropper = KerodonDiagramCropper(args.pdf_path, fig_dir)
    cropped = cropper.crop_chapter_diagrams(chapter, start_page=18, end_page=145)
    print(f"   Cropped {cropped} diagrams at 300 DPI into {fig_dir}")

    print("\n3. Generating Typst and XeLaTeX masters...")
    compiler = KerodonCompiler(chapter)
    out_typ = out_dir / f"chapter{args.chapter}.typ"
    out_pdf = out_dir / f"chapter{args.chapter}.pdf"
    out_tex = out_dir / f"chapter{args.chapter}.tex"

    compiler.generate_typst(out_typ)
    print(f"   Typst Source: {out_typ}")

    compiler.generate_latex(out_tex)
    print(f"   XeLaTeX Source: {out_tex}")

    print("\n4. Compiling to Typst PDF...")
    compiler.compile_pdf(out_typ, out_pdf)
    print(f"   Compiled PDF: {out_pdf} ({out_pdf.stat().st_size / (1024*1024):.2f} MB)")
    print("\n🎉 Kerodon reverse engineering complete!")


if __name__ == "__main__":
    main()
