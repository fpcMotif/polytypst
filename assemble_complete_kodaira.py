"""Build the Kodaira monograph (Markdown, LaTeX, Typst, PDF) from output/kodaira."""

from pathlib import Path

from polytypst.books import render_book_figures
from polytypst.compiler.monograph import MonographCompiler
from polytypst.kodaira.spec import KODAIRA_SPEC


def main(out_dir: Path) -> None:
    _ = render_book_figures(KODAIRA_SPEC.slug, out_dir)
    outputs = MonographCompiler(KODAIRA_SPEC).build_all(out_dir)
    print(f"{outputs.pdf_path} ({outputs.total_pages} pages)")


if __name__ == "__main__":
    main(Path("output/kodaira"))
