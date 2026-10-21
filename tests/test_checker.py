from pathlib import Path

import pymupdf

from polytypst.checker import (
    LAYOUT_TIER,
    STRUCTURE_TIER,
    TEXT_TIER,
    AuditSpec,
    DocumentQualityChecker,
    audit_pdf,
)
from polytypst.compiler.monograph import compile_typst
from polytypst.kodaira.spec import KODAIRA_SPEC
from polytypst.siegel_symplectic.spec import SIEGEL_SYMPLECTIC_SPEC

BODY = "This paragraph is ordinary body prose that fills a page with enough characters."


def _pdf(
    tmp_path: Path, pages: list[list[str]], width: float = 612, height: float = 792
) -> Path:
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page(width=width, height=height)
        for i, line in enumerate(lines):
            _ = page.insert_text((72, height * 0.15 + 40 * i), line, fontsize=11)
    path = tmp_path / "book.pdf"
    doc.save(path)
    return path


def test_text_tier_catches_leaked_markup(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path, [[BODY, "Roy,~1952 wrote \\frac{a}{b} here"]])
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({TEXT_TIER}))
    assert {"NO_LITERAL_TILDE", "UNRENDERED_LATEX_MACRO"} <= report.rules()
    assert all(issue.tier == TEXT_TIER for issue in report.issues)
    assert not report.is_clean


def test_text_tier_catches_an_invented_thesis_outline(tmp_path: Path) -> None:
    pdf = _pdf(
        tmp_path,
        [[BODY, "1.1 Background", "1.2 Problem Statement", "3.4 Model Training"]],
    )
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({TEXT_TIER}))
    invented = [i for i in report.issues if i.rule_name == "HALLUCINATED_BOILERPLATE"]
    assert [i.context_snippet for i in invented] == [
        "problem statement",
        "model training",
    ]


def test_one_thesis_word_in_history_prose_is_not_an_invented_outline(
    tmp_path: Path,
) -> None:
    pdf = _pdf(tmp_path, [[BODY, "Riemann's dissertation of 1851 founded the theory."]])
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({TEXT_TIER}))
    assert "HALLUCINATED_BOILERPLATE" not in report.rules()


def _typst_pdf(tmp_path: Path, source: str) -> Path:
    typ = tmp_path / "m.typ"
    typ.write_text(source, encoding="utf-8")
    pdf = tmp_path / "m.pdf"
    compile_typst(typ, pdf)
    return pdf


def test_layout_tier_flags_a_display_shrunk_to_fit(tmp_path: Path) -> None:
    prose = "Ordinary prose fills the page at the body size. " * 12
    pdf = _typst_pdf(
        tmp_path,
        f"{prose}\n\n#align(center, scale(35%, reflow: true)[$ f(x) = sum_(n=1)^infinity a_n x^n + integral_0^1 g(t) dif t $])\n\n{prose}",
    )
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({LAYOUT_TIER}))
    assert "SHRUNKEN_DISPLAY_MATH" in report.rules()


def test_layout_tier_accepts_scripts_and_limits_at_normal_size(tmp_path: Path) -> None:
    prose = "Ordinary prose fills the page at the body size. " * 12
    pdf = _typst_pdf(
        tmp_path,
        f"{prose}\n\n$ f(x) = sum_(n=1)^infinity a_(n_k)^(m_j) x^n + integral_0^1 g(t) dif t $\n\n{prose}",
    )
    report = DocumentQualityChecker(pdf).run_all_checks(frozenset({LAYOUT_TIER}))
    assert "SHRUNKEN_DISPLAY_MATH" not in report.rules()


def test_book_author_or_title_alone_on_a_body_line_is_a_leaked_header(
    tmp_path: Path,
) -> None:
    filler = [[BODY, BODY, BODY]] * 4
    pdf = _pdf(
        tmp_path,
        [
            *filler,
            [BODY, "CARL LUDWIG SIEGEL.", BODY],
            ["SYMPLECTIC GEOMETRY. 7", BODY],
            ["In 1943 Carl Ludwig Siegel wrote on Symplectic Geometry.", BODY],
            [BODY, "the functional equation of zeta, we have CARL LUDWIG SIEGEL."],
        ],
    )
    report = audit_pdf(pdf, SIEGEL_SYMPLECTIC_SPEC, frozenset({TEXT_TIER}))
    leaked = [i for i in report.issues if i.rule_name == "LEAKED_RUNNING_HEADER"]
    assert [i.page_num for i in leaked] == [5, 6, 8]
    plain = DocumentQualityChecker(pdf).run_all_checks(frozenset({TEXT_TIER}))
    assert "LEAKED_RUNNING_HEADER" not in plain.rules()


def test_heading_rule_flags_headings_but_not_cardinality(tmp_path: Path) -> None:
    def headings(line: str) -> list[str]:
        pdf = _pdf(tmp_path, [[BODY, line]])
        report = DocumentQualityChecker(pdf).run_all_checks(frozenset({TEXT_TIER}))
        return [
            i.rule_name for i in report.issues if i.rule_name == "RAW_MARKDOWN_HEADING"
        ]

    assert headings("## 1.2 Schemes") == ["RAW_MARKDOWN_HEADING"]
    assert headings("# Introduction") == ["RAW_MARKDOWN_HEADING"]
    assert headings("# A K n = 3") == []
    assert headings("\\# A_{K_n} is finite") == []


def test_monograph_heading_drives_chapter_regression(tmp_path: Path) -> None:
    filler = [[BODY, BODY, BODY]] * 4
    pdf = _pdf(
        tmp_path,
        [
            *filler,
            ["2 Cauchy's Theorem", BODY, BODY],
            ["1 Holomorphic functions", BODY, BODY],
        ],
    )
    spec = AuditSpec.from_monograph(KODAIRA_SPEC)
    report = DocumentQualityChecker(pdf, spec).run_all_checks(
        frozenset({STRUCTURE_TIER})
    )
    regressions = [i for i in report.issues if i.rule_name == "CHAPTER_REGRESSION"]
    assert [i.page_num for i in regressions] == [6]

    default_report = DocumentQualityChecker(pdf).run_all_checks(
        frozenset({STRUCTURE_TIER})
    )
    assert "CHAPTER_REGRESSION" not in default_report.rules()


def test_numbered_prose_is_not_a_chapter_heading(tmp_path: Path) -> None:
    filler = [[BODY, BODY, BODY]] * 4
    pdf = _pdf(
        tmp_path,
        [*filler, ["3 Conformal mappings", BODY], ["2 is the only even prime", BODY]],
    )
    report = audit_pdf(pdf, KODAIRA_SPEC, frozenset({STRUCTURE_TIER}))
    assert "CHAPTER_REGRESSION" not in report.rules()


def test_stale_running_header_uses_spec_titles(tmp_path: Path) -> None:
    filler = [[BODY, BODY, BODY]] * 4
    pdf = _pdf(
        tmp_path,
        [
            *filler,
            ["2 Cauchy's Theorem", BODY, BODY],
            [BODY, BODY],
            ["Holomorphic functions", BODY, BODY],
        ],
    )
    report = audit_pdf(pdf, KODAIRA_SPEC, frozenset({STRUCTURE_TIER}))
    stale = [i for i in report.issues if i.rule_name == "STALE_RUNNING_HEADER"]
    assert [i.page_num for i in stale] == [7]


def test_margin_overflow_scales_with_page_width(tmp_path: Path) -> None:
    doc = pymupdf.open()
    for width in (612.0, 1224.0):
        page = doc.new_page(width=width, height=792)
        _ = page.insert_text((width * 0.955, 300), "edge", fontsize=11)
    path = tmp_path / "wide.pdf"
    doc.save(path)
    report = DocumentQualityChecker(path).run_all_checks(frozenset({LAYOUT_TIER}))
    overflow_pages = sorted(
        {i.page_num for i in report.issues if i.rule_name == "MARGIN_OVERFLOW"}
    )
    assert overflow_pages == [1, 2]


def test_figure_pages_are_exempt_from_isolated_letters(tmp_path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    _ = page.insert_text((300, 400), "z", fontsize=24)
    path = tmp_path / "fig.pdf"
    doc.save(path)
    flagged = DocumentQualityChecker(path).run_all_checks(frozenset({LAYOUT_TIER}))
    assert "ISOLATED_MATH_BLOCK" in flagged.rules()
    exempt = DocumentQualityChecker(
        path, AuditSpec(figure_pages=frozenset({1}))
    ).run_all_checks(frozenset({LAYOUT_TIER}))
    assert "ISOLATED_MATH_BLOCK" not in exempt.rules()
