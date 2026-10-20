"""Master runner for Lars Ahlfors Complex Analysis (1979 McGraw-Hill style)."""

from pathlib import Path
from polytypst.ahlfors.figures import generate_all_ahlfors_figures
from polytypst.ahlfors.transcriber import AhlforsTranscriber
from polytypst.ahlfors.compiler import AhlforsCompiler
from polytypst.checker import audit_pdf
import subprocess

def main():
    pdf_input = Path("/Users/martinfan/Downloads/[Lars_Ahlfors]_Complex_Analysis_(Third_Edition).pdf")
    out_dir = Path("output/ahlfors")
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("Step 1: Re-computing publication-grade vector figures (1979 pen-and-ink style)...")
    generate_all_ahlfors_figures(fig_dir)

    print("\nStep 2: Transcribing and cross-validating Chapter 1 text & math...")
    transcriber = AhlforsTranscriber(pdf_input)
    ch1_md = transcriber.transcribe_chapter_1(out_dir / "chapter1.md")
    print(f"Transcribed Chapter 1 ({len(ch1_md)} characters).")

    print("\nStep 3: Compiling Typst master and XeLaTeX sources (1979 McGraw-Hill Standard)...")
    compiler = AhlforsCompiler(ch1_md)
    out_typ = out_dir / "ahlfors.typ"
    out_pdf = out_dir / "ahlfors.pdf"
    out_tex = out_dir / "ahlfors.tex"
    out_epub = out_dir / "ahlfors.epub"

    compiler.generate_typst(out_typ)
    print(f"Generated Typst source: {out_typ} ({out_typ.stat().st_size / 1024:.1f} KB)")

    compiler.generate_latex(out_tex)
    print(f"Generated XeLaTeX source: {out_tex} ({out_tex.stat().st_size / 1024:.1f} KB)")

    print("\nStep 4: Compiling to Typst PDF...")
    compiler.compile_pdf(out_typ, out_pdf)
    print(f"SUCCESS: Compiled Typst PDF to {out_pdf} ({out_pdf.stat().st_size / (1024*1024):.2f} MB)")

    print("\nStep 5: Compiling to EPUB e-book...")
    cmd_epub = [
        "pandoc", str(out_dir / "chapter1.md"),
        "-o", str(out_epub),
        "--toc",
        "--mathml",
        "--metadata", "title=Complex Analysis (Third Edition)",
        "--metadata", "author=Lars V. Ahlfors",
        "--metadata", "publisher=McGraw-Hill Book Company",
        "--metadata", "date=1979"
    ]
    subprocess.run(cmd_epub, check=True)
    print(f"SUCCESS: Compiled EPUB to {out_epub} ({out_epub.stat().st_size / 1024:.1f} KB)")

    print("\nStep 6: Running automated production quality audit on ahlfors.pdf...")
    report = audit_pdf(out_pdf)


if __name__ == "__main__":
    main()
