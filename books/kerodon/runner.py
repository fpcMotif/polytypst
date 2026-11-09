"""Command-line runner for reverse engineering Kerodon treatise across chapters."""

import argparse
import tomllib
from pathlib import Path

from polytypst.paths import OUTPUT

from .compiler import KerodonCompiler
from .diagrams import KerodonDiagramCropper
from .extractor import KerodonExtractor

CHAPTER_METADATA = {
    c["number"]: (c["tag"], c["first_page"], c["last_page"])
    for c in tomllib.loads((Path(__file__).parent / "chapters.toml").read_text(encoding="utf-8"))["chapter"]
}


def main():
    parser = argparse.ArgumentParser(description="Reverse engineer Kerodon into Typst, XeLaTeX, and EPUB")
    parser.add_argument("--cache-dir", type=Path, default=OUTPUT / "kerodon" / "cache_web", help="Path to cached web HTML")
    parser.add_argument("--pdf-path", type=Path, default=Path("kerodon.pdf"), help="Path to kerodon.pdf")
    parser.add_argument("-o", "--output-dir", type=Path, default=OUTPUT / "kerodon", help="Output directory")
    parser.add_argument("--chapter", type=int, default=1, help="Chapter number to process (1 to 10)")
    args = parser.parse_args()

    out_dir = args.output_dir
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    if args.chapter not in CHAPTER_METADATA:
        print(f"Error: Chapter {args.chapter} not in known range (1 to 10).")
        return

    ch_tag, start_p, end_p = CHAPTER_METADATA[args.chapter]

    print(f"=== REVERSE ENGINEERING KERODON CHAPTER {args.chapter} (Tag {ch_tag}) ===")
    print("1. Extracting structured mathematical DOM from Kerodon...")
    extractor = KerodonExtractor(args.cache_dir)
    chapter = extractor.extract_chapter(args.chapter, ch_tag)
    print(f"   Chapter {chapter.number}: {chapter.title} ({len(chapter.sections)} sections)")

    print(f"\n2. Cropping commutative diagrams from kerodon.pdf (pp. {start_p} - {end_p})...")
    cropper = KerodonDiagramCropper(args.pdf_path, fig_dir)
    cropped = cropper.crop_chapter_diagrams(chapter, start_page=start_p, end_page=end_p)
    print(f"   Cropped {cropped} diagrams at 300 DPI into {fig_dir}")

    print("\n3. Generating Typst and XeLaTeX masters...")
    compiler = KerodonCompiler(chapter)
    out_typ = out_dir / f"chapter{args.chapter}.typ"
    out_pdf = out_dir / f"chapter{args.chapter}.pdf"
    out_tex = out_dir / f"chapter{args.chapter}.tex"

    compiler.generate_typst(out_typ)
    print(f"   Typst Source: {out_typ} ({out_typ.stat().st_size / 1024:.1f} KB)")

    compiler.generate_latex(out_tex)
    print(f"   XeLaTeX Source: {out_tex} ({out_tex.stat().st_size / 1024:.1f} KB)")

    print("\n4. Compiling to Typst PDF...")
    compiler.compile_pdf(out_typ, out_pdf)
    print(f"   Compiled PDF: {out_pdf} ({out_pdf.stat().st_size / (1024*1024):.2f} MB)")
    print(f"\n🎉 Kerodon Chapter {args.chapter} reverse engineering complete!")


if __name__ == "__main__":
    main()
