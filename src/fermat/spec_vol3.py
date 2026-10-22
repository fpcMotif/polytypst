"""Kurokawa, Kurihara, Saito: Number Theory 3: Iwasawa Theory and Modular Forms (AMS, Vol 242)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"MODULAR FORMS|IWASAWA THEORY|ELLIPTIC CURVES|"
    r"BIBLIOGRAPHY|ANSWERS TO QUESTIONS|ANSWERS TO EXERCISES|"
    r"INDEX|CONTENTS|PREFACE|OBJECTIVES AND OUTLINE"
)

FERMAT3_SPEC = MonographSpec(
    slug="number_theory_3_iwasawa_theory_and_modular_forms",
    title="Number Theory 3: Iwasawa Theory and Modular Forms",
    author="Nobushige Kurokawa, Masato Kurihara, Takeshi Saito",
    translator="Masato Kuwata",
    publisher="American Mathematical Society",
    series="Translations of Mathematical Monographs, Volume 242",
    year=2012,
    publisher_key="ams",
    lang="en",
    domain="math",
    pdf_page_count=242,
    pdf_name_markers=("number theory 3", "iwasawa theory", "modular forms"),
    preface_page=10,
    chapters=[
        ChapterSpec(9, "Modular Forms", 16, 101, label="Chapter 9"),
        ChapterSpec(10, "Iwasawa Theory", 102, 181, label="Chapter 10"),
        ChapterSpec(11, "Modular forms (II)", 182, 203, label="Chapter 11"),
        ChapterSpec(12, "Elliptic curves (II)", 204, 225, label="Chapter 12"),
        ChapterSpec(13, "Bibliography", 226, 231),
        ChapterSpec(14, "Answers to Questions", 232, 233),
        ChapterSpec(15, "Answers to Exercises", 234, 239),
        ChapterSpec(16, "Index", 240, 242),
    ],
    sections={
        "9.1": (19, "Ramanujan's discoveries"),
        "9.2": (32, "Ramanujan's $\\Delta$ and holomorphic Eisenstein series"),
        "9.3": (40, "Automorphy and functional equations"),
        "9.4": (46, "Real analytic Eisenstein series"),
        "9.5": (62, "Kronecker's limit formula and regularized products"),
        "9.6": (79, "Modular forms for $SL_2(\\mathbb{Z})$"),
        "9.7": (89, "Classical modular forms"),
        "10.0": (103, "What is Iwasawa theory?"),
        "10.1": (112, "Analytic $p$-adic zeta functions"),
        "10.2": (141, "Ideal class groups and cyclotomic $\\mathbb{Z}_p$-extensions"),
        "10.3": (162, "Iwasawa main conjecture"),
        "11.1": (183, "Automorphic forms and representation theory"),
        "11.2": (189, "Poisson summation formula"),
        "11.3": (195, "Selberg trace formula"),
        "11.4": (200, "Langlands conjectures"),
        "12.1": (204, "Elliptic curves over the rational number field"),
        "12.2": (216, "Fermat's Last Theorem"),
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
    figure_pages=frozenset({107, 108, 156}),
)
