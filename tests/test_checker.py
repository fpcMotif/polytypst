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
from polytypst.kodaira.spec import KODAIRA_SPEC

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
