from pathlib import Path

import pymupdf
import pytest

from polytypst.checker import LAYOUT_TIER, DocumentQualityChecker
from polytypst.compiler.monograph import (
    MonographCompiler,
    compile_typst,
    is_unnumbered_chapter,
)
from polytypst.compiler.page_cleaner import normalize_run_in


def test_theorem_note_before_the_closing_bold_leaves_no_stray_asterisks():
    out = normalize_run_in("**Theorem 1.1 (Cauchy's criterion).** The complex sequence converges.")
    assert out.startswith("**Theorem 1.1.** (Cauchy's criterion) ")
    assert out.count("**") == 2
from polytypst.books import book_by_key, module

HECKE_SPEC = book_by_key("hecke").spec
KODAIRA_SPEC = module("kodaira", "spec").KODAIRA_SPEC


def test_first_appearance_of_a_section_at_page_top_is_a_heading_not_a_running_head():
    compiler = MonographCompiler(KODAIRA_SPEC)
    line = "## 1.4 Properties of holomorphic functions"
    assert not compiler.cleaner._is_page_furniture(line, 58, 1)
    assert compiler.cleaner._normalized_heading(line, 58) == "## 1.4 Properties of holomorphic functions"
    assert compiler.cleaner._is_page_furniture(line, 60, 1)


@pytest.mark.parametrize(("level", "spacer"), [(2, 140), (3, 154), (4, 154)])
def test_heading_at_page_bottom_moves_with_its_text(tmp_path: Path, level: int, spacer: int) -> None:
    rules = MonographCompiler(KODAIRA_SPEC).composition.typst_heading_rules()
    filler = "\n\n".join(f"Line {i} of filler prose." for i in range(400))
    body = (
        f"#set page(height: 200pt, width: 200pt, margin: 10pt)\n#let chapter-label = state(\"chapter-label\", none)\n{rules}\n"
        f"#block(height: {spacer}pt)[]\n{'=' * level} Lonely Heading\n\n{filler}"
    )
    typ = tmp_path / "h.typ"
    typ.write_text(body, encoding="utf-8")
    pdf = tmp_path / "h.pdf"
    compile_typst(typ, pdf)
    doc = pymupdf.open(pdf)
    heading_page = next(p.number for p in doc if "Lonely Heading" in p.get_text())
    assert "Line 0 of filler" in doc[heading_page].get_text()


def _odd_heads(tmp_path: Path, body: str) -> tuple[dict[int, str], pymupdf.Document]:
    typ = tmp_path / "r.typ"
    typ.write_text(MonographCompiler(KODAIRA_SPEC).build_typst_preamble() + body, encoding="utf-8")
    pdf = tmp_path / "r.pdf"
    compile_typst(typ, pdf)
    doc = pymupdf.open(pdf)
    heads = {
        p.number + 1: " ".join(" ".join(b[4].split()) for b in p.get_text("blocks") if b[1] < 50)
        for p in doc
        if (p.number + 1) % 2 == 1
    }
    return heads, doc


def test_display_too_wide_to_fit_breaks_instead_of_shrinking(tmp_path: Path) -> None:
    terms = " + ".join(f"integral K_{k} (t, x - x') u({k}, x') dif x'" for k in range(9))
    body = f"\nSome prose before.\n\n$ u(t, x) = {terms} $\n\nMore prose.\n\n$ v(t, x) = {terms} $ <eq-3-7>\n\nEnd.\n"
    typ = tmp_path / "w.typ"
    typ.write_text(MonographCompiler(KODAIRA_SPEC).build_typst_preamble() + body, encoding="utf-8")
    pdf = tmp_path / "w.pdf"
    compile_typst(typ, pdf)
    doc = pymupdf.open(pdf)
    sizes = [
        s["size"]
        for p in doc
        for b in p.get_text("dict")["blocks"]
        for ln in b.get("lines", [])
        for s in ln["spans"]
        if "𝐾" in s["text"]
    ]
    assert len(sizes) == 18
    assert min(sizes) >= 8
    assert "(3.7)" in "".join(p.get_text() for p in doc)
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({LAYOUT_TIER}))
    assert not {"SHRUNKEN_DISPLAY_MATH", "MARGIN_OVERFLOW"} & report.rules()


def test_display_too_wide_with_no_top_level_break_stays_inside_the_margins(tmp_path: Path) -> None:
    terms = " + ".join(f"integral K_{k} (t, x - x') u({k}, x') dif x'" for k in range(9))
    body = (
        f"\nSome prose before.\n\n$ Lambda = {{ ({terms}) }} $\n\nMore prose.\n\n"
        f"$ u &= {terms} \\\n &= 0 $\n\nEnd.\n"
    )
    typ = tmp_path / "w.typ"
    typ.write_text(MonographCompiler(KODAIRA_SPEC).build_typst_preamble() + body, encoding="utf-8")
    pdf = tmp_path / "w.pdf"
    compile_typst(typ, pdf)
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({LAYOUT_TIER}))
    assert "MARGIN_OVERFLOW" not in report.rules()


def test_rows_of_a_too_wide_aligned_display_are_fitted_one_by_one(tmp_path: Path) -> None:
    long = " + ".join(f"integral K_{k} (t, x - x') u({k}, x') dif x'" for k in range(3))
    breakable = " + ".join(f"integral K_{k} (t, x - x') u({k}, x') dif x'" for k in range(3, 12))
    body = f"\nSome prose before.\n\n$ {long} &= 0 \\\n 0 &= {long} \\\n &= {breakable} $\n\nEnd.\n"
    typ = tmp_path / "w.typ"
    typ.write_text(MonographCompiler(KODAIRA_SPEC).build_typst_preamble() + body, encoding="utf-8")
    pdf = tmp_path / "w.pdf"
    compile_typst(typ, pdf)
    doc = pymupdf.open(pdf)
    sizes = [
        s["size"]
        for p in doc
        for b in p.get_text("dict")["blocks"]
        for ln in b.get("lines", [])
        for s in ln["spans"]
        if "𝐾" in s["text"]
    ]
    assert len(sizes) == 15
    assert min(sizes) >= 8
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({LAYOUT_TIER}))
    assert not {"SHRUNKEN_DISPLAY_MATH", "MARGIN_OVERFLOW"} & report.rules()


def test_running_head_shows_the_current_chapter_section(tmp_path: Path) -> None:
    filler = "\n\n".join(f"Filler paragraph {i} of ordinary prose for the page." for i in range(60))
    body = (
        "#pagebreak()\n#pagebreak()\n#pagebreak()\n#pagebreak()\n"
        f"= First Chapter\n\n== Old Section\n\n{filler}\n\n#pagebreak()\n"
        f"= Second Chapter\n\n{filler}\n\n#pagebreak()\n"
        f"#lorem(20)\n\n== Fresh Section\n\n{filler}\n"
    )
    heads, doc = _odd_heads(tmp_path, body)
    fresh_page = next(p.number + 1 for p in doc if "Fresh Section" in p.get_text())
    assert fresh_page % 2 == 1
    second = [n for n, h in heads.items() if "Second Chapter" in h]
    assert second, heads
    assert not any("Old Section" in heads[n] for n in heads if n > min(second)), heads
    assert heads[fresh_page] == f"Fresh Section {fresh_page}"


def test_japanese_inside_math_uses_the_body_mincho(tmp_path: Path) -> None:
    fukuso = book_by_key("複素多様体論").spec
    typ = tmp_path / "j.typ"
    body = 'これは本文です。\n\n$ lambda, mu upright("は複素数") $\n'
    typ.write_text(MonographCompiler(fukuso).build_typst_preamble() + body, encoding="utf-8")
    pdf = tmp_path / "j.pdf"
    compile_typst(typ, pdf)
    spans = [s for b in pymupdf.open(pdf)[0].get_text("dict")["blocks"] for ln in b.get("lines", []) for s in ln["spans"]]
    body_font = next(s["font"] for s in spans if "本文" in s["text"])
    math_font = next(s["font"] for s in spans if "複素数" in s["text"])
    assert math_font == body_font


def test_title_page_names_only_the_book_publisher_and_keeps_the_title_whole():
    page = MonographCompiler(HECKE_SPEC).build_typst_title_page()
    assert "SPRINGER-VERLAG" in page
    assert "Melbourne" not in page
    assert "hyphenate: false" in page
    assert "Melbourne" in MonographCompiler(KODAIRA_SPEC).build_typst_title_page()


@pytest.mark.parametrize(
    "title", ["Bibliography", "References", "Solutions to Problems", "Historical Note (Chapters I to III)", "参考文献", "Index"]
)
def test_back_matter_chapters_carry_no_number(title: str) -> None:
    assert is_unnumbered_chapter(title)


def test_body_chapters_keep_their_number() -> None:
    assert not is_unnumbered_chapter("Holomorphic functions")


def test_paren_inline_math_delimiters_become_dollars():
    compiler = MonographCompiler(HECKE_SPEC)
    text, _, _ = compiler.cleaner.clean("(2) implies \\( x = u + y \\), whence \\( \\varepsilon(x)\n= 0 \\).\n", 30)
    assert "\\(" not in text
    assert "$x = u + y$" in text
    assert "$\\varepsilon(x)\n= 0$" in text


def test_scanner_watermark_is_removed_from_page_text():
    compiler = MonographCompiler(HECKE_SPEC)
    text, _, _ = compiler.cleaner.clean("Gauss wrote.\n\nClibPDF - www.fastio.com; for example the lemniscate.\n\nClibPDF - www.iasj.net\n", 30)
    assert "ClibPDF" not in text
    assert "for example the lemniscate." in text


def test_display_holding_a_sentence_is_set_as_a_paragraph():
    compiler = MonographCompiler(HECKE_SPEC)
    page = "$$a = 0 \\text{ holds; in a similar manner, one obtains the same bound for } b = 0.\n\nNext paragraph.\n"
    text, _, _ = compiler.cleaner.clean(page, 30)
    assert "$$" not in text
    assert "in a similar manner, one obtains the same bound for $b = 0.$" in text


def test_first_section_on_a_chapter_start_page_is_kept():
    compiler = MonographCompiler(HECKE_SPEC)
    text, _, _ = compiler.cleaner.clean("# CHAPTER I\n\n## §1 Factorization into Primes\n\nEvery integer is a product.\n", 11)
    assert "## §1 Factorization into Primes" in text


def test_starred_problem_number_is_bold_with_its_star():
    out = MonographCompiler(KODAIRA_SPEC).format_typst("**2*.** If the radius of convergence is positive, show it.")
    assert out.startswith("#strong[2\\*.] If the radius")


def test_numbered_paragraph_is_run_in_text_but_a_short_list_stays_a_list():
    compiler = MonographCompiler(HECKE_SPEC)
    paragraph = "1. The prime q does not divide the order of the group. Then there is exactly one element of the desired sort."
    assert compiler.format_typst(paragraph).startswith("1\\. The prime q")
    assert compiler.format_typst("1. short\n2. list").startswith("1. short")


def test_unknown_short_heading_stays_a_heading_and_its_repeats_are_dropped():
    compiler = MonographCompiler(HECKE_SPEC)
    assert compiler.cleaner._normalized_heading("## 1. ALGEBRAS", 30) == "### 1. ALGEBRAS"
    assert compiler.cleaner._normalized_heading("## 1. ALGEBRAS", 31) == ""
    assert compiler.cleaner._normalized_heading("# R.H. Analytical Mechanics", 32) == ""
    long_line = "## " + "This paragraph was tagged as a heading by the OCR but is ordinary prose. " * 2
    assert compiler.cleaner._normalized_heading(long_line, 33) == long_line[3:].strip()


def test_section_sign_numbers_are_kept_per_chapter_and_in_full():
    compiler = MonographCompiler(HECKE_SPEC)
    assert compiler.cleaner._normalized_heading("## § 1. DEFINITION", 12) == "## § 1. DEFINITION"
    assert compiler.cleaner._normalized_heading("## § 1. GENERALITIES", 27) == "## § 1. GENERALITIES"
    assert compiler.cleaner._normalized_heading("## §1.1 First", 13) == "## §1.1 First"
    assert compiler.cleaner._normalized_heading("## §1.2 Second", 14) == "## §1.2 Second"


def test_section_sign_heading_becomes_a_section_once():
    compiler = MonographCompiler(HECKE_SPEC)
    assert compiler.cleaner._normalized_heading("## §20 Generating Field Elements", 76) == "## §20 Generating Field Elements"
    assert compiler.cleaner._normalized_heading("## §20 Generating Field Elements", 77) == ""
