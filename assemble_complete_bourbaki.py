import sys
from pathlib import Path

import pymupdf

from polytypst.books import render_book_figures
from polytypst.bourbaki import OUT_DIR
from polytypst.bourbaki.facsimile import build_facsimile
from polytypst.bourbaki.spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC
from polytypst.compiler.monograph import MonographCompiler
from polytypst.parity.source import ensure_source_ocr, source_ocr_dir, source_pdf

SPECS = {"modern": BOURBAKI_SPEC, "vintage": BOURBAKI_1970_SPEC}


def main(edition: str, source: Path | None) -> None:
    out_dir = OUT_DIR
    if edition == "facsimile":
        pdf = build_facsimile(source_pdf(BOURBAKI_SPEC, source), out_dir)
        print(f"{pdf}: {pymupdf.open(pdf).page_count} pages")
        return
    spec = SPECS[edition]
    _ = render_book_figures(spec.slug, out_dir)
    if spec.source_line_breaks is not None:
        ensure_source_ocr(source_pdf(spec, source), source_ocr_dir(out_dir))
    fit_file = out_dir / "page_fit.json"
    if spec.paginate_like_source and not fit_file.exists():
        _ = fit_file.write_text("{}\n", encoding="utf-8")
    outputs = MonographCompiler(spec).build_all(out_dir)
    print(f"{outputs.pdf_path}: {outputs.total_pages} pages")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0] if args else "vintage", Path(args[1]) if len(args) > 1 else None)
