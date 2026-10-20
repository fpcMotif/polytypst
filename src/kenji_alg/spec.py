"""Kenji Ueno: Algebraic Geometry 1: From Algebraic Varieties to Schemes (AMS, Vol 185)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"ALGEBRAIC VARIETIES|SCHEMES|CATEGORIES AND SCHEMES|"
    r"SOLUTIONS TO PROBLEMS|SOLUTIONS TO EXERCISES|INDEX|"
    r"PREFACE|CONTENTS|SUMMARY AND GOALS"
)

KENJI_ALG_SPEC = MonographSpec(
    slug="algebraic_geometry_1_from_algebraic_varieties_to_schemes_kenji_ueno",
    title="Algebraic Geometry 1: From Algebraic Varieties to Schemes",
    author="Kenji Ueno",
    translator="Goro Kato",
    publisher="American Mathematical Society",
    series="Translations of Mathematical Monographs, Volume 185",
    year=1999,
    publisher_key="ams",
    lang="en",
    domain="math",
    pdf_page_count=178,
    pdf_name_markers=("algebraic geometry 1", "kenji ueno", "ueno"),
    preface_page=10,
    chapters=[
        ChapterSpec(1, "Algebraic Varieties", 22, 63, label="Chapter 1"),
        ChapterSpec(2, "Schemes", 64, 121, label="Chapter 2"),
        ChapterSpec(3, "Categories and Schemes", 122, 159, label="Chapter 3"),
        ChapterSpec(4, "Solutions to Problems", 160, 167),
        ChapterSpec(5, "Solutions to Exercises", 168, 173),
        ChapterSpec(6, "Index", 174, 178),
    ],
    sections={
        "1.1": (22, "Algebraic Sets"),
        "1.2": (27, "Hilbert's Nullstellensatz"),
        "1.3": (33, "Affine Algebraic Varieties"),
        "1.4": (47, "Multiplicity and Local Intersection Multiplicity"),
        "1.5": (50, "Projective Varieties"),
        "1.6": (59, "What is Missing?"),
        "2.1": (64, "Prime Spectrum"),
        "2.2": (72, "Affine Schemes"),
        "2.3": (96, "Ringed Space and Scheme"),
        "2.4": (109, "Schemes and Morphisms"),
        "3.1": (122, "Categories and Functors"),
        "3.2": (136, "Representable Functors and Fibre Products"),
        "3.3": (152, "Separated Morphisms"),
    },
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Figure\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_ignore_case=True,
        caption_format="Figure {chapter}.{number}",
    ),
    header_zone_lines=2,
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(
        r"^Translations of MATHEMATICAL MONOGRAPHS.*$",
        r"^Volume 185.*$",
        r"^American Mathematical Society.*$",
        r"^\d+\s+[A-Z\s\$\-\.\,\?]+$",
        r"^[A-Z\s\$\-\.\,\?]+\s+\d+$",
    ),
    pre_math_rewrites=(
        (r"plus\.circle", r"\\u{2295}"),
        (r"times\.circle", r"\\u{2297}"),
        (r"\\text\{Spec\}", r"\\operatorname{Spec}"),
        (r"\\text\{Spm\}", r"\\operatorname{Spm}"),
        (r"\\text\{Proj\}", r"\\operatorname{Proj}"),
        (r"\\text\{Hom\}", r"\\operatorname{Hom}"),
        (r"\\text\{Mor\}", r"\\operatorname{Mor}"),
        (r"\\text\{Ob\}", r"\\operatorname{Ob}"),
        (r"\\text\{id\}", r"\\operatorname{id}"),
        (r"\\text\{Id\}", r"\\operatorname{Id}"),
    ),
    figure_pages=frozenset({106, 121}),
)
