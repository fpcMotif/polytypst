"""End-to-end Kerodon Chapter 1 Reverse Engineering and Compilation Script."""

import sys
from pathlib import Path
from polytypst.kerodon.extractor import KerodonExtractor
from polytypst.kerodon.diagrams import KerodonDiagramCropper
from polytypst.kerodon.compiler import KerodonCompiler
from polytypst.checker import audit_pdf

def main():
    cache_dir = Path("output/kerodon/cache_web")
    pdf_path = Path("kerodon.pdf")
    out_dir = Path("output/kerodon")
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("Step 1: Extracting structured mathematical DOM from Kerodon...")
    extractor = KerodonExtractor(cache_dir)
    chapter = extractor.extract_chapter_1()
    print(f"  Extracted Chapter {chapter.number}: {chapter.title}")
    print(f"  Total Sections: {len(chapter.sections)}")

    print("\nStep 2: Cropping commutative diagrams from kerodon.pdf...")
    cropper = KerodonDiagramCropper(pdf_path, fig_dir)
    cropped_count = cropper.crop_chapter_diagrams(chapter, start_page=18, end_page=145)
    print(f"  Cropped {cropped_count} high-resolution diagram figures at 300 DPI")

    print("\nStep 3: Compiling Typst master and XeLaTeX sources...")
    compiler = KerodonCompiler(chapter)
    out_typ = out_dir / "chapter1.typ"
    out_pdf = out_dir / "chapter1.pdf"
    out_tex = out_dir / "chapter1.tex"

    compiler.generate_typst(out_typ)
    print(f"  Generated Typst source: {out_typ} ({out_typ.stat().st_size / 1024:.1f} KB)")

    compiler.generate_latex(out_tex)
    print(f"  Generated XeLaTeX source: {out_tex} ({out_tex.stat().st_size / 1024:.1f} KB)")

    print("\nStep 4: Compiling to Typst PDF...")
    compiler.compile_pdf(out_typ, out_pdf)
    print(f"  SUCCESS! Compiled PDF to {out_pdf} ({out_pdf.stat().st_size / (1024*1024):.2f} MB)")

    print("\nStep 5: Running strict production quality audit on chapter1.pdf...")
    report = audit_pdf(out_pdf)

if __name__ == "__main__":
    main()
