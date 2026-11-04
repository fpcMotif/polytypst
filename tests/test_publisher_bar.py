import re
from itertools import pairwise
from pathlib import Path

import pymupdf
import pytest

from polytypst.books import book_by_key
from polytypst.checker import TEXT_TIER, AuditSpec, DocumentQualityChecker
from polytypst.compiler.monograph import MonographCompiler, compile_typst
from polytypst.compiler.tables import layout_tables

KODAIRA_SPEC = book_by_key("kodaira").spec


def _rows_split_across_pages(doc: pymupdf.Document) -> list[str]:
    split = []
    for page, following in pairwise(doc):
        keys = [w[4] for w in page.get_text("words") if re.fullmatch(r"R\d\d", w[4])]
        if keys and f"end{keys[-1][1:]}" not in page.get_text() and f"end{keys[-1][1:]}" in following.get_text():
            split.append(keys[-1])
    return split


def test_a_table_row_stays_on_one_page_and_the_header_repeats(tmp_path: Path) -> None:
    rows = [f"| R{i:02d} | {'word ' * (60 if i % 7 == 0 else 6)}end{i:02d} | {i} |" for i in range(60)]
    table = "| Key | Text | n |\n| --- | --- | --- |\n" + "\n".join(rows) + "\n"
    filler = "\n\n".join(f"Filler line {i}." for i in range(25))
    body = filler + "\n\n" + layout_tables("@@TABLEBLOCK0@@\n", [table])
    typ = tmp_path / "t.typ"
    typ.write_text(MonographCompiler(KODAIRA_SPEC).build_typst_preamble() + body, encoding="utf-8")
    compile_typst(typ, tmp_path / "t.pdf")
    doc = pymupdf.open(tmp_path / "t.pdf")
    table_pages = [p for p in doc if re.search(r"\bR\d\d\b", p.get_text())]
    assert len(table_pages) >= 2
    assert _rows_split_across_pages(doc) == []
    assert all("Key" in p.get_text() for p in table_pages)


def _leaked_words(tmp_path: Path, math: str) -> list[int]:
    typ = tmp_path / "m.typ"
    typ.write_text(f"Some prose before the formula.\n\n$ {math} $\n", encoding="utf-8")
    compile_typst(typ, tmp_path / "m.pdf")
    report = DocumentQualityChecker(tmp_path / "m.pdf", AuditSpec(front_matter_pages=0)).run_all_checks(frozenset({TEXT_TIER}))
    return [i.page_num for i in report.issues if i.rule_name == "UNRENDERED_MATH_ITALIC_WORD"]


@pytest.mark.parametrize(
    "math",
    [
        "S x r i g h t a r r o w Y",
        "a u n d e r b r a c e b",
        "t h e f r a c f",
        "T h e f i r s t t h e o r e m p a r t i a l l y f u l f i l l s",
    ],
)
def test_a_latex_command_or_prose_set_as_math_letters_is_flagged(tmp_path: Path, math: str) -> None:
    assert _leaked_words(tmp_path, math) == [1]


@pytest.mark.parametrize("math", ["a_i b_j c_(i j k) e_k", "x arrow.r y", "theta(t) = phi(t)"])
def test_subscripts_and_real_symbols_are_not_leaked_words(tmp_path: Path, math: str) -> None:
    assert _leaked_words(tmp_path, math) == []
