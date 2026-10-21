from pathlib import Path

import pymupdf

from polytypst.ahlfors.typst_blocks import TOC_BLOCK, TYPST_PREAMBLE
from polytypst.compiler.monograph import compile_typst

PROSE = " ".join(["The radius of convergence is determined by the coefficients."] * 6)


def test_contents_page_settings_do_not_reach_the_body(tmp_path: Path) -> None:
    typ = tmp_path / "a.typ"
    typ.write_text(f"{TYPST_PREAMBLE}\n{TOC_BLOCK}\n{PROSE}\n\n{PROSE}\n", encoding="utf-8")
    pdf = tmp_path / "a.pdf"
    compile_typst(typ, pdf)
    page = pymupdf.open(pdf)[-1]
    lines = [b for b in page.get_text("dict")["blocks"] for b in b["lines"]]
    starts = [ln["bbox"][0] for ln in lines if ln["spans"][0]["text"].startswith("The radius")]
    others = [ln["bbox"][0] for ln in lines if not ln["spans"][0]["text"].startswith("The radius")]
    assert starts and others
    assert max(starts) > min(others) + 5
