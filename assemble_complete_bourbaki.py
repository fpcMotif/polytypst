import sys
from pathlib import Path

import pymupdf

from polytypst.books import render_book_figures
from polytypst.bourbaki.facsimile import build_facsimile
from polytypst.bourbaki.spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC
from polytypst.compiler.monograph import MonographCompiler

SPECS = {"modern": BOURBAKI_SPEC, "vintage": BOURBAKI_1970_SPEC}


def main(edition: str) -> None:
    out_dir = Path("output/bourbaki")
    if edition == "facsimile":
        pdf = build_facsimile(out_dir)
        print(f"{pdf}: {pymupdf.open(pdf).page_count} pages")
        return
    spec = SPECS[edition]
    _ = render_book_figures(spec.slug, out_dir)
    fit_file = out_dir / "page_fit.json"
    if spec.paginate_like_source and not fit_file.exists():
        _ = fit_file.write_text("{}\n", encoding="utf-8")
    outputs = MonographCompiler(spec).build_all(out_dir)
    print(f"{outputs.pdf_path}: {outputs.total_pages} pages")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "vintage")
