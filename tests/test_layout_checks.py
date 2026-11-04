from pathlib import Path

import pymupdf

from polytypst.checker import (
    LAYOUT_TIER,
    AuditSpec,
    CheckReport,
    DocumentQualityChecker,
)
from polytypst.compiler.monograph import compile_typst

PROSE = "Ordinary prose fills the page at the body size. " * 20
FULL_PAGE = "#rect(width: 100%, height: 100%)\n#pagebreak()\n"


def _layout(tmp_path: Path, source: str, spec: AuditSpec | None = None) -> CheckReport:
    typ = tmp_path / "book.typ"
    typ.write_text(source, encoding="utf-8")
    pdf = tmp_path / "book.pdf"
    compile_typst(typ, pdf)
    return DocumentQualityChecker(pdf, spec or AuditSpec(front_matter_pages=0)).run_all_checks(frozenset({LAYOUT_TIER}))


def _pages(report: CheckReport, rule: str) -> list[int]:
    return [i.page_num for i in report.issues if i.rule_name == rule]


def test_a_glyph_set_in_a_font_the_source_never_declares_is_a_fallback(tmp_path: Path) -> None:
    report = _layout(tmp_path, f'#set text(font: "New Computer Modern")\n{PROSE} Proof done. ❖')
    assert _pages(report, "FONT_FALLBACK") == [1]


def test_declared_fonts_and_the_default_math_font_are_not_fallbacks(tmp_path: Path) -> None:
    report = _layout(tmp_path, f'#set text(font: ("New Computer Modern", "Zapf Dingbats"))\n{PROSE} $x^2$ done. ❖')
    assert _pages(report, "FONT_FALLBACK") == []


def test_a_declared_family_matches_its_abbreviated_postscript_name(tmp_path: Path) -> None:
    report = _layout(tmp_path, f'#set text(font: ("New Computer Modern", "Hiragino Mincho ProN"))\n{PROSE} 複素多様体論')
    assert _pages(report, "FONT_FALLBACK") == []


def test_a_one_word_family_does_not_match_by_its_first_letter(tmp_path: Path) -> None:
    report = _layout(tmp_path, f'#set text(font: ("New Computer Modern", "STSong"))\n{PROSE} `raw code`')
    assert _pages(report, "FONT_FALLBACK") == [1]


def test_text_inside_an_embedded_figure_is_not_a_typst_fallback(tmp_path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    _ = page.insert_text((72, 200), "A label that a LaTeX figure set in its own font", fontsize=11)
    doc.save(tmp_path / "book.pdf")
    (tmp_path / "book.typ").write_text('#set text(font: "New Computer Modern")\n', encoding="utf-8")
    report = DocumentQualityChecker(tmp_path / "book.pdf", AuditSpec(front_matter_pages=0)).run_all_checks(frozenset({LAYOUT_TIER}))
    assert _pages(report, "FONT_FALLBACK") == []


def test_a_rule_wider_than_the_text_block_overflows_inside_the_page(tmp_path: Path) -> None:
    report = _layout(tmp_path, f"{PROSE}\n\n#rect(width: 107%, height: 8pt, fill: black)\n\n{PROSE}")
    assert _pages(report, "MARGIN_OVERFLOW") == [1]


def test_ragged_prose_stays_inside_the_text_block(tmp_path: Path) -> None:
    report = _layout(tmp_path, f"{PROSE}\n\n{PROSE}")
    assert _pages(report, "MARGIN_OVERFLOW") == []


def test_a_page_that_stops_halfway_before_more_prose_is_underfull(tmp_path: Path) -> None:
    source = "#set page(width: 300pt, height: 300pt)\n" + FULL_PAGE * 2 + "#lorem(20)\n#pagebreak()\n" + FULL_PAGE * 2
    report = _layout(tmp_path, source)
    assert _pages(report, "UNDERFULL_PAGE") == [3]


def test_the_last_page_of_a_chapter_may_stop_short(tmp_path: Path) -> None:
    source = (
        "#set page(width: 300pt, height: 300pt)\n"
        + FULL_PAGE * 2
        + "#lorem(20)\n#pagebreak()\n#text(24pt)[Chapter 2]\n\n#lorem(20)\n#rect(width: 100%, height: 1fr)\n#pagebreak()\n"
        + FULL_PAGE
    )
    report = _layout(tmp_path, source)
    assert _pages(report, "UNDERFULL_PAGE") == []


def test_a_formula_in_the_running_head_is_flagged(tmp_path: Path) -> None:
    report = _layout(tmp_path, f"#set page(header: [$x^2 + y^2 = r^2$ #h(1fr) 3])\n{PROSE}")
    assert _pages(report, "RUNNING_HEAD_FORMULA") == [1]


def test_a_title_in_the_running_head_is_not_a_formula(tmp_path: Path) -> None:
    report = _layout(tmp_path, f"#set page(header: [Gauss' Equation #h(1fr) 3])\n{PROSE}")
    assert _pages(report, "RUNNING_HEAD_FORMULA") == []


def test_a_chapter_title_printed_twice_on_its_page_is_a_duplicate(tmp_path: Path) -> None:
    report = _layout(
        tmp_path,
        f'#set text(10pt)\n= The Gauss-Bonnet Theorem\n\n#text(10.5pt, weight: "bold")[THE GAUSS-BONNET THEOREM]\n\n{PROSE}',
    )
    assert _pages(report, "DUPLICATE_HEADING") == [1]


def test_a_chapter_label_above_its_title_is_not_a_duplicate(tmp_path: Path) -> None:
    report = _layout(tmp_path, f"= Chapter 6\n\n== The Gauss-Bonnet Theorem\n\n{PROSE}")
    assert _pages(report, "DUPLICATE_HEADING") == []


def test_a_contents_page_whose_numbers_have_no_leaders_is_flagged(tmp_path: Path) -> None:
    entries = "\n\n".join(f"Section {n} on curves and surfaces {10 * n}" for n in range(1, 8))
    report = _layout(tmp_path, f"#text(16pt)[Contents]\n\n{entries}")
    assert _pages(report, "CONTENTS_WITHOUT_LEADERS") == [1]


def test_an_outline_sets_its_entries_with_dot_leaders(tmp_path: Path) -> None:
    headings = "\n".join(f"= Section {n} on curves\n#lorem(10)\n" for n in range(1, 8))
    report = _layout(tmp_path, f"#outline(title: [Contents])\n#pagebreak()\n{headings}")
    assert _pages(report, "CONTENTS_WITHOUT_LEADERS") == []
