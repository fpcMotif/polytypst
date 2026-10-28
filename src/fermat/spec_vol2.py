"""Kato, Kurokawa, Saito: Number Theory 2: Introduction to Class Field Theory (AMS, Vol 240)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"WHAT IS CLASS FIELD THEORY\?|LOCAL AND GLOBAL FIELDS|"
    r"ZETA FUNCTIONS|CLASS FIELD THEORY|ANSWERS|INDEX|CONTENTS|PREFACE"
)

FERMAT2_SPEC = MonographSpec(
    domain="math",
    slug="number_theory_2_class_field_theory",
    title="Number Theory 2: Introduction to Class Field Theory",
    author="Kazuya Kato, Nobushige Kurokawa, Takeshi Saito",
    translator="Masato Kuwata and Katsumi Nomizu",
    publisher="American Mathematical Society",
    series="Translations of Mathematical Monographs, Volume 240",
    year=2011,
    publisher_key="ams",
    pdf_page_count=250,
    pdf_name_markers=("number theory 2", "class field theory"),
    preface_page=8,
    chapters=[
        ChapterSpec(5, "What is Class Field Theory?", 10, 41),
        ChapterSpec(6, "Local and Global Fields", 42, 119),
        ChapterSpec(7, "Zeta Functions and L-Functions", 120, 159),
        ChapterSpec(8, "Class Field Theory", 160, 235),
        ChapterSpec(9, "Answers to Questions and Exercises", 236, 246),
        ChapterSpec(10, "Index", 247, 250),
    ],
    sections={
        "5.1": (10, "Examples of class field theoretic phenomena"),
        "5.2": (22, "Cyclotomic fields and quadratic fields"),
        "5.3": (34, "An outline of class field theory"),
        "6.1": (42, "A curious analogy between numbers and functions"),
        "6.2": (49, "Places and local fields"),
        "7.1": (120, "Zeta functions and L-functions"),
        "8.1": (160, "Cohomology of groups"),
    },
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Table\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_format="Table {chapter}.{number}",
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(
        r"^Translations of MATHEMATICAL MONOGRAPHS.*$",
        r"^Volume 240.*$",
        r"^American Mathematical Society.*$",
        r"^\d+\s+[A-Z\s\$\-\.\,\?]+$",
        r"^[A-Z\s\$\-\.\,\?]+\s+\d+$",
    ),
)
