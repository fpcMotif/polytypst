"""Ahlfors, Complex Analysis (McGraw-Hill, 1979): the book's declarative monograph specs."""

import re
from dataclasses import replace

from polytypst.compiler.monograph import ChapterSpec, FigureLayout, MonographSpec

from .typst_blocks import TITLE_PAGE_BLOCK, TOC_BLOCK, TYPST_PREAMBLE

RUNNING_HEADERS = (
    "COMPLEX ANALYSIS|COMPLEX NUMBERS|COMPLEX FUNCTIONS|"
    "ANALYTIC FUNCTIONS AS MAPPINGS|COMPLEX INTEGRATION|"
    "SERIES AND PRODUCT DEVELOPMENTS|CONFORMAL MAPPING|"
    "ELLIPTIC FUNCTIONS|GLOBAL ANALYTIC FUNCTIONS|"
    "DIRICHLET'S PROBLEM|CONFORMAL MAPPING\\. DIRICHLET'S PROBLEM|INDEX"
)

AHLFORS_SPEC = MonographSpec(
    domain="math",
    slug="ahlfors_complete",
    title="Complex Analysis",
    author="Lars V. Ahlfors",
    subtitle="An Introduction to the Theory of Analytic Functions of One Complex Variable",
    publisher="McGraw-Hill Book Company",
    series="International Series in Pure and Applied Mathematics",
    year=1979,
    publisher_key="harvard",
    chapters=[
        ChapterSpec(1, "COMPLEX NUMBERS", 1, 36, typst_file="chapter1.md"),
        ChapterSpec(2, "COMPLEX FUNCTIONS", 37, 64),
        ChapterSpec(3, "ANALYTIC FUNCTIONS AS MAPPINGS", 65, 116),
        ChapterSpec(4, "COMPLEX INTEGRATION", 117, 190),
        ChapterSpec(5, "SERIES AND PRODUCT DEVELOPMENTS", 191, 244),
        ChapterSpec(6, "CONFORMAL MAPPING. DIRICHLET'S PROBLEM", 245, 278),
        ChapterSpec(7, "ELLIPTIC FUNCTIONS", 279, 298),
        ChapterSpec(8, "GLOBAL ANALYTIC FUNCTIONS", 299, 340),
    ],
    index_pages=(341, 347),
    index_title="INDEX",
    index_subentries=True,
    markdown_dir="markdown",
    figures=FigureLayout(
        caption_pattern=(
            r"^(?:\*\*)?FIG\.\s*(?P<chapter>\d+)-(?P<number>\d+)\.?(?:\*\*)?(?P<tail>.*)$"
        ),
        caption_ignore_case=False,
        caption_format="FIG. {chapter}-{number}.",
        top_zone_lines=1,
        top_pages=frozenset({298}),
        svg_single_pct=60,
        svg_paired_pct=82,
        png_single_divisor=1050,
        png_single_range=(28, 82),
        png_max_height_ratio=0.42,
        png_min_pct_tall=26,
        png_paired_divisor=520,
        png_paired_range=(55, 90),
        supplement_none=False,
    ),
    min_page_chars=41,
    skip_page_markers=("1.1.1.1.1",),
    folio_pattern=r"^\d{1,3}$",
    running_header_regexes=(
        rf"^(?:{RUNNING_HEADERS})$",
        rf"^\d{{1,3}}\s+(?:{RUNNING_HEADERS})\b.*$",
        rf"^(?:{RUNNING_HEADERS})\b.*?\s+\d{{1,3}}$",
    ),
    header_zone_lines=None,
    drop_line_regexes=(
        r"^#\s+(?:[1-8]\b|CHAPTER|COMPLEX|ANALYTIC|SERIES|CONFORMAL|ELLIPTIC|GLOBAL|INDEX)",
        r"^!\[FIG\.",
        r"^\(a\) \(b\)$",
    ),
    normalize_headings=False,
    footnote_style="symbol",
    footnote_marks=("†", "‡"),
    equation_numbering="page",
    page_fixups={
        38: ((re.escape("as $x$ tends to $a$,"), "as $x$ tends to $a$,*"),),
        91: ((r"sub-\s*\n+\s*regions", "subregions"),),
        177: ((re.escape(r"if $|\zeta| < 1$, then*"), r"if $|\\zeta| < 1$, then"),),
        298: ((re.escape("Fig. 7-0"), "Fig. 7-2"),),
    },
    heading_rewrites=(
        (r"^#{1,4}\s+(\*?)EXERCISES?\*?\s*$", r"==== \1EXERCISES"),
        (r"^###\s+(\d+\.\s+(?:Compute|Prove|Find)\b.*?)$", r"\1"),
        (r"^###\s+(Theorem\s+\d+\.)$", r"**\1**"),
        (r"^##\s+(4\.2\.\s+Extension of .*?\.)\s+(Recall that)$", r"=== \1\n\n\2"),
        (r"^##\s+(\d+\.\d+\.\s+.*?)$", r"=== \1"),
    ),
    pre_math_rewrites=(
        (
            r"(\\?partial\s+[a-zA-Z0-9_]+)\s*/\s*(\\?partial\s+[a-zA-Z0-9_]+)",
            r"(\1)/(\2)",
        ),
        (r"(\\?partial\s+[a-zA-Z0-9_]+)\s*/\s*([a-zA-Z0-9_]+)", r"(\1)/(\2)"),
    ),
    stray_dollar_symbol="zeta",
    nonbreaking_hyphens=True,
    chapter_heading="CHAPTER {number}: {title}",
    prebuilt_fixups=(
        ("|z_1 / z_2| = |z_1| / |z_2|", "abs(z_1 / z_2) = abs(z_1) / abs(z_2)"),
    ),
    typst_preamble=TYPST_PREAMBLE,
    typst_front_matter=TITLE_PAGE_BLOCK
    + "\n"
    + TOC_BLOCK,
    book_aliases=False,
)

AHLFORS_ILLUSTRATED_SPEC = replace(
    AHLFORS_SPEC,
    slug="ahlfors_illustrated",
    figure_dir="figures_color",
    require_vector_figures=True,
    typst_front_matter=TITLE_PAGE_BLOCK.replace(
        "THIRD EDITION", "THIRD EDITION — COLORFUL ILLUSTRATED EDITION"
    )
    + "\n"
    + TOC_BLOCK,
    extra_figures={
        55: (
            (
                "bonus_2_1",
                "FIG. 2-1. Hadamard disk of convergence $|z - z_0| < R$ and compact subdisk.",
            ),
        ),
        135: (
            (
                "bonus_4_cauchy",
                "FIG. 4-2a. Cauchy integral formula contour around excavated disk $C_\\delta$.",
            ),
        ),
        201: (
            (
                "bonus_5_laurent",
                "FIG. 5-1a. Laurent series annulus $r_1 < |z - a| < r_2$.",
            ),
        ),
        246: (
            (
                "bonus_6_riemann",
                "FIG. 6-0a. Conformal bijection of the Riemann Mapping Theorem ($z_0 \\mapsto 0, f'(z_0) > 0$).",
            ),
        ),
        281: (
            (
                "bonus_7_torus",
                "FIG. 7-1a. Quotient of the period parallelogram $(\\omega_1, \\omega_2)$ onto the complex torus $\\mathbb{C}\\text{/}\\Lambda$.",
            ),
        ),
    },
)
