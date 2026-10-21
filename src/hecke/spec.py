"""Erich Hecke: Lectures on the Theory of Algebraic Numbers (Springer GTM 77)."""

from ..compiler.monograph import ChapterSpec, MonographSpec, running_header_regexes

RUNNING_HEADERS = (
    r"Lectures on the Theory of Algebraic Numbers|Erich Hecke|"
    r"Translators' Preface|Author's Preface|Contents|"
    r"Elements of Rational Number Theory|Abelian Groups|"
    r"Abelian Groups in Rational Number Theory|Algebra of Number Fields|"
    r"General Arithmetic of Algebraic Number Fields|"
    r"Introduction of Transcendental Methods into the Arithmetic of Number Fields|"
    r"The Quadratic Number Field|"
    r"The Law of Quadratic Reciprocity in Arbitrary Number Fields|"
    r"Chronological Table|References"
)

HECKE_SPEC = MonographSpec(
    slug="hecke",
    title="Lectures on the Theory of Algebraic Numbers",
    author="Erich Hecke",
    translator="George U. Brauer and Jay R. Goldman",
    publisher="Springer-Verlag",
    series="Graduate Texts in Mathematics",
    year=1981,
    preface_page=5,
    chapters=[
        ChapterSpec(1, "Elements of Rational Number Theory", 11, 25),
        ChapterSpec(2, "Abelian Groups", 26, 49),
        ChapterSpec(3, "Abelian Groups in Rational Number Theory", 50, 63),
        ChapterSpec(4, "Algebra of Number Fields", 64, 77),
        ChapterSpec(5, "General Arithmetic of Algebraic Number Fields", 78, 148),
        ChapterSpec(6, "Introduction of Transcendental Methods into the Arithmetic of Number Fields", 149, 164),
        ChapterSpec(7, "The Quadratic Number Field", 165, 204),
        ChapterSpec(8, "The Law of Quadratic Reciprocity in Arbitrary Number Fields", 205, 248),
    ],
    references_page=249,
    latex_preamble=(
        r"\usepackage{fancyhdr}" "\n"
        r"\pagestyle{fancy}" "\n"
        r"\fancyhf{}" "\n"
        r"\fancyhead[LE]{\small\thepage\quad\textsc{Erich Hecke}}" "\n"
        r"\fancyhead[RO]{\small\textsc{Theory of Algebraic Numbers}\quad\thepage}" "\n"
        r"\renewcommand{\headrulewidth}{0pt}"
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(rf"^#+\s*(?:{RUNNING_HEADERS})(?:\s+\d{{1,3}})?\s*$",),
    pdf_name_markers=("hecke", "algebraic numbers"),
    pdf_page_count=249,
    source_pdf="Lectures on the theory of algebraic numbers (Hecke, Erich).pdf",
)
