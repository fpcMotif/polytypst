"""Masaki Kashiwara, Takahiro Kawai, Tatsuo Kimura: Foundations of Algebraic Analysis (PUP, Vol 37)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"HYPERFUNCTIONS|MICROFUNCTIONS|FUNDAMENTAL OPERATIONS|"
    r"MICRODIFFERENTIAL EQUATIONS|PREFACE|NOTATIONS|BIBLIOGRAPHY|INDEX"
)

KASHIWARA_SPEC = MonographSpec(
    slug="foundations_of_algebraic_analysis",
    title="Foundations of Algebraic Analysis",
    footnote_style="superscript",
    footnote_reset="book",
    author="Masaki Kashiwara, Takahiro Kawai, Tatsuo Kimura",
    translator="Goro Kato",
    publisher="Princeton University Press",
    series="Princeton Mathematical Series, Volume 37",
    year=1986,
    publisher_key="princeton",
    pdf_page_count=267,
    pdf_name_markers=("foundations of algebraic analysis", "kashiwara"),
    preface_page=7,
    chapters=[
        ChapterSpec(1, "Hyperfunctions", 15, 46),
        ChapterSpec(2, "Microfunctions", 47, 112),
        ChapterSpec(3, "Fundamental Operations", 113, 202),
        ChapterSpec(4, "Microdifferential Equations", 203, 259),
        ChapterSpec(5, "Bibliography", 260, 264),
        ChapterSpec(6, "Index", 265, 267),
    ],
    sections={
        "1.1": (15, "Sheaf Theory"),
        "1.2": (33, "Hyperfunctions as Boundary Values of Holomorphic Functions"),
        "2.1": (47, "Definition of Microfunctions"),
        "2.2": (63, "Vanishing Theorems of Relative Cohomology Groups"),
        "2.3": (72, "Fundamental Exact Sequences"),
        "2.4": (93, "Examples"),
        "3.1": (113, "Product, Restriction, and Substitution"),
        "3.2": (128, "Integration"),
        "3.3": (143, "Analyticity of Feynman Integrals"),
        "3.4": (147, "Microlocal Operators and the Fundamental Theorem of Sato"),
        "3.5": (157, "The Wave Equation"),
        "3.6": (173, "Fundamental Solutions for Regularly Hyperbolic Operators"),
        "4.1": (203, "Microdifferential Operators"),
        "4.2": (225, "Quantized Contact Transformations"),
        "4.3": (245, "Structure of Systems of Microdifferential Equations"),
    },
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Figure\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_format="Figure {chapter}.{number}",
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(
        r"^PRINCETON MATHEMATICAL SERIES.*$",
        r"^Volume 37.*$",
        r"^Princeton University Press.*$",
        r"^\d+\s+[A-Z\s\$\-\.\,\?]+$",
        r"^[A-Z\s\$\-\.\,\?]+\s+\d+$",
    ),
    pre_math_rewrites=(
        (r"plus\.circle", r"\\u{2295}"),
        (r"times\.circle", r"\\u{2297}"),
        (r"\\text\{Ker\}", r"\\operatorname{Ker}"),
        (r"\\text\{Coker\}", r"\\operatorname{Coker}"),
        (r"\\text\{Im\}", r"\\operatorname{Im}"),
        (r"\\text\{Hom\}", r"\\operatorname{Hom}"),
        (r"\\text\{Ext\}", r"\\operatorname{Ext}"),
        (r"\\text\{ch\}", r"\\operatorname{ch}"),
        (r"\\text\{S\.S\.\}", r"\\operatorname{S.S.}"),
    ),
)
