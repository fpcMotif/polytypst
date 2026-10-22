"""Kenji Ueno: Algebraic Geometry 3: Further Study of Schemes (AMS, Vol 218)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"FUNDAMENTAL PROPERTIES OF SCHEME THEORY|"
    r"ALGEBRAIC CURVES AND JACOBIAN VARIETIES|"
    r"ALGEBRAIC GEOMETRY AND ANALYTIC GEOMETRY|"
    r"OVERVIEW AND REFERENCES|SOLUTIONS TO PROBLEMS|"
    r"SOLUTIONS TO EXERCISES|INDEX|PREFACE|CONTENTS"
)

KENJI_ALG3_SPEC = MonographSpec(
    slug="algebraic_geometry_3_further_study_of_schemes_kenji_ueno",
    title="Algebraic Geometry 3: Further Study of Schemes",
    author="Kenji Ueno",
    translator="Goro Kato",
    publisher="American Mathematical Society",
    series="Translations of Mathematical Monographs, Volume 218",
    year=2003,
    publisher_key="ams",
    lang="en",
    domain="math",
    pdf_page_count=234,
    pdf_name_markers=("algebraic geometry 3", "further study of schemes", "ueno"),
    preface_page=10,
    chapters=[
        ChapterSpec(7, "Fundamental Properties of Scheme Theory", 10, 133, label="Chapter 7"),
        ChapterSpec(8, "Algebraic Curves and Jacobian Varieties", 134, 191, label="Chapter 8"),
        ChapterSpec(9, "Algebraic Geometry and Analytic Geometry", 192, 201, label="Chapter 9"),
        ChapterSpec(10, "Overview and References", 202, 211),
        ChapterSpec(11, "Solutions to Problems", 212, 219),
        ChapterSpec(12, "Solutions to Exercises", 220, 227),
        ChapterSpec(13, "Index", 228, 234),
    ],
    sections={
        "7.1": (11, "Algebraic Schemes and Algebraic Varieties"),
        "7.2": (23, "Dimension"),
        "7.3": (61, "Flat Morphisms and Proper Morphisms"),
        "7.4": (89, "Regular Schemes and Smooth Morphisms"),
        "7.5": (122, "Completion and Zariski's Main Theorem"),
        "8.1": (134, "Algebraic Curves"),
        "8.2": (162, "Jacobian Varieties"),
        "9.1": (192, "Analytic Geometry"),
        "9.2": (197, "Kodaira's Vanishing Theorem"),
    },
    figures=FigureLayout(),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    folio_pattern=r"^(?:\d{1,3}|[ivxlcdm]+)$",
    drop_line_regexes=(
        r"^[ivxlcdm]+\s+[A-Z\s\$\-\.\,\?]+$",
        r"^[A-Z\s\$\-\.\,\?]+\s+[ivxlcdm]+$",
        r"^\d+\s+[A-Z\s\$\-\.\,\?]+$",
        r"^[A-Z\s\$\-\.\,\?]+\s+\d+$",
    ),
    figure_pages=frozenset({20, 48, 128, 150}),
)
