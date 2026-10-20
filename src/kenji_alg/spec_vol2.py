"""Kenji Ueno: Algebraic Geometry 2: Sheaves and Cohomology (AMS, Vol 197)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"COHERENT SHEAVES|PROPER AND PROJECTIVE MORPHISMS|"
    r"COHOMOLOGY OF COHERENT SHEAVES|"
    r"SOLUTIONS TO PROBLEMS|SOLUTIONS TO EXERCISES|INDEX|"
    r"PREFACE|CONTENTS"
)

KENJI_ALG2_SPEC = MonographSpec(
    slug="algebraic_geometry_2_sheaves_and_cohomology_kenji_ueno",
    title="Algebraic Geometry 2: Sheaves and Cohomology",
    author="Kenji Ueno",
    translator="Goro Kato",
    publisher="American Mathematical Society",
    series="Translations of Mathematical Monographs, Volume 197",
    year=2001,
    publisher_key="ams",
    lang="en",
    domain="math",
    pdf_page_count=194,
    pdf_name_markers=("algebraic geometry 2", "sheaves and cohomology", "ueno"),
    preface_page=8,
    chapters=[
        ChapterSpec(4, "Coherent Sheaves", 8, 59, label="Chapter 4"),
        ChapterSpec(5, "Proper and Projective Morphisms", 60, 117, label="Chapter 5"),
        ChapterSpec(6, "Cohomology of Coherent Sheaves", 118, 167, label="Chapter 6"),
        ChapterSpec(7, "Solutions to Problems", 168, 179),
        ChapterSpec(8, "Solutions to Exercises", 180, 189),
        ChapterSpec(9, "Index", 190, 194),
    ],
    sections={
        "4.1": (9, "Exact Sequence of Sheaves"),
        "4.2": (23, "Quasicoherent Sheaves and Coherent Sheaves"),
        "4.3": (43, "Direct Image and Inverse Image"),
        "4.4": (51, "Schemes and Quasicoherent Sheaves"),
        "5.1": (60, "Proper Morphisms"),
        "5.2": (74, "Quasicoherent Sheaves over a Projective Scheme"),
        "5.3": (98, "Projective Morphisms"),
        "6.1": (118, "Cohomology of Sheaves"),
        "6.2": (145, "Cohomology of a Projective Scheme"),
        "6.3": (160, "Higher Direct Image"),
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
    figure_pages=frozenset({10, 12, 128}),
)
