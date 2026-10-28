"""Kodaira, Complex Analysis (Cambridge, 2007): the book's declarative monograph spec."""

from ..compiler.monograph import ChapterSpec, MonographSpec, running_header_regexes

RUNNING_HEADERS = (
    r"Holomorphic functions|Cauchy's Theorem|Conformal mappings|"
    r"Analytic continuation|Riemann's Mapping Theorem|Riemann surfaces|"
    r"The structure of\s*Riemann surfaces|Analytic functions on a closed Riemann surface|"
    r"Piecewise smooth curves|Cellular decomposition|Differentiability and homology|"
    r"The Riemann sphere|Linear fractional transformations|"
    r"Analytic continuation along curves|Analytic continuation by integrals|"
    r"Cauchy's Theorem \(continued\)|Correspondence of boundaries|The principle of reflection|"
    r"Differential forms|Differential forms on a Riemann surface|Dirichlet's Principle|"
    r"Planar Riemann surfaces|Compact Riemann surfaces|"
    r"Abelian differentials of the first kind|Abelian differentials of the second and third kind|"
    r"The Riemann[-–—]Roch Theorem|Abel's Theorem|Power series|Integrals|"
    r"Properties of holomorphic functions|Preface|Contents|Problems|References|Index"
)

KODAIRA_OCR_PROMPT = (
    "Transcribe this page from Kunihiko Kodaira's Complex Analysis textbook into clean, "
    "faithful TeX-compatible Markdown.\n"
    "Rules:\n"
    "1. Format all mathematical expressions in exact LaTeX syntax: inline $...$ and display $$...$$.\n"
    "2. Preserve all Greek letters, barred conjugates (\\bar{z}), integrals (\\int_\\gamma), "
    "sums, fractions, subscripts, superscripts, and homology/cohomology notation exactly.\n"
    "3. Format chapter, section, and subsection headings with Markdown (#, ##, ###).\n"
    "4. Bold theorem, lemma, definition, corollary, proposition, and remark headers "
    "(e.g. **Theorem 1.1.**, **Definition 1.5.**, **Lemma 2.3.**) and italicize *Proof.*\n"
    "5. Preserve exact equation numbers on display equations (e.g. $$ |zw|^2 = |z|^2 |w|^2 $$ (1.1)).\n"
    "6. When a figure caption appears (e.g. Fig. 1.1), output a standalone line `Fig. X.Y` at its exact position.\n"
    "7. Do not omit any prose, proofs, or exercises."
)

KODAIRA_SPEC = MonographSpec(
    domain="math",
    slug="kodaira_complex_analysis",
    title="Complex Analysis",
    require_vector_figures=True,
    footnote_style="symbol",
    footnote_marks=("*", "**", "***"),
    author="Kunihiko Kodaira",
    translator="A. Sevenster",
    editor="A. F. Beardon and T. K. Carne",
    publisher="Cambridge University Press",
    series="Cambridge Studies in Advanced Mathematics",
    year=2007,
    preface_page=10,
    chapters=[
        ChapterSpec(1, "Holomorphic functions", 12, 70),
        ChapterSpec(2, "Cauchy's Theorem", 71, 127),
        ChapterSpec(3, "Conformal mappings", 128, 163),
        ChapterSpec(4, "Analytic continuation", 164, 210),
        ChapterSpec(5, "Riemann's Mapping Theorem", 211, 257),
        ChapterSpec(6, "Riemann surfaces", 258, 329),
        ChapterSpec(7, "The structure of Riemann surfaces", 330, 386),
        ChapterSpec(8, "Analytic functions on a closed Riemann surface", 387, 404),
    ],
    sections={
        "1.1": (12, "Holomorphic functions"),
        "1.2": (26, "Power series"),
        "1.3": (35, "Integrals"),
        "1.4": (58, "Properties of holomorphic functions"),
        "2.1": (71, "Piecewise smooth curves"),
        "2.2": (85, "Cellular decomposition"),
        "2.3": (112, "Cauchy's Theorem"),
        "2.4": (124, "Differentiability and homology"),
        "3.1": (128, "Conformal mappings"),
        "3.2": (143, "The Riemann sphere"),
        "3.3": (150, "Linear fractional transformations"),
        "4.1": (164, "Analytic continuation"),
        "4.2": (171, "Analytic continuation along curves"),
        "4.3": (191, "Analytic continuation by integrals"),
        "4.4": (201, "Cauchy's Theorem (continued)"),
        "5.1": (211, "Riemann's Mapping Theorem"),
        "5.2": (225, "Correspondence of boundaries"),
        "5.3": (235, "The principle of reflection"),
        "6.1": (258, "Differential forms"),
        "6.2": (271, "Riemann surfaces"),
        "6.3": (279, "Differential forms on a Riemann surface"),
        "6.4": (305, "Dirichlet's Principle"),
        "7.1": (330, "Planar Riemann surfaces"),
        "7.2": (351, "Compact Riemann surfaces"),
        "8.1": (387, "Abelian differentials of the first kind"),
        "8.2": (390, "Abelian differentials of the second and third kind"),
        "8.3": (392, "The Riemann-Roch Theorem"),
        "8.4": (399, "Abel's Theorem"),
    },
    problems_pages=(405, 412),
    references_page=413,
    index_pages=(414, 417),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(rf"^#+\s*(?:{RUNNING_HEADERS})(?:\s+\d{{1,3}})?\s*$",),
    pdf_name_markers=("kodaira", "complex analysis ( etc.)"),
    pdf_page_count=417,
    ocr_prompt=KODAIRA_OCR_PROMPT,
)