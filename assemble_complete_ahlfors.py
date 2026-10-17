"""Build the complete and the colour-illustrated Ahlfors monographs from output/ahlfors."""

from pathlib import Path

from polytypst.ahlfors.spec import AHLFORS_ILLUSTRATED_SPEC, AHLFORS_SPEC
from polytypst.books import render_book_figures
from polytypst.compiler.monograph import MonographCompiler


def main(out_dir: Path) -> None:
    _ = render_book_figures(AHLFORS_SPEC.slug, out_dir)
    for spec in (AHLFORS_SPEC, AHLFORS_ILLUSTRATED_SPEC):
        outputs = MonographCompiler(spec).build_all(out_dir)
        print(f"{outputs.pdf_path} ({outputs.total_pages} pages)")


if __name__ == "__main__":
    main(Path("output/ahlfors"))
