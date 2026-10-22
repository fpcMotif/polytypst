"""Nicolas Bourbaki: Lie Groups and Lie Algebras (Chapters 1-3)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"LIE ALGEBRAS|FREE LIE ALGEBRAS|LIE GROUPS|"
    r"HISTORICAL NOTE|INDEX OF NOTATION|INDEX OF TERMINOLOGY|CONTENTS|TO THE READER"
)

CHAPTERS = [
    ChapterSpec(1, "Lie Algebras", 19, 128, label="Chapter I"),
    ChapterSpec(2, "Free Lie Algebras", 129, 226, label="Chapter II"),
    ChapterSpec(3, "Lie Groups", 227, 427, label="Chapter III"),
    ChapterSpec(4, "Historical Note (Chapters I to III)", 428, 452),
    ChapterSpec(5, "Index of Notation", 453, 456),
    ChapterSpec(6, "Index of Terminology", 457, 468),
]

BOURBAKI_LIE_SPEC = MonographSpec(
    slug="bourbaki_lie_groups_and_lie_algebras",
    title="Lie Groups and Lie Algebras (Chapters 1–3)",
    footnote_style="symbol",
    footnote_marks=("†", "‡", "§"),
    author="Nicolas Bourbaki",
    publisher="Springer-Verlag",
    series="Elements of Mathematics",
    year=1989,
    publisher_key="springer",
    pdf_page_count=476,
    pdf_name_markers=("lie groups and lie algebras", "bourbaki"),
    preface_page=6,
    chapters=CHAPTERS,
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Diagram\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_format="Diagram {chapter}.{number}",
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(
        r"^Springer-Verlag.*$",
        r"^Elements of Mathematics.*$",
        r"^\d+\s+[A-Z\s\$\-\.\,]+$",
        r"^[A-Z\s\$\-\.\,]+\s+\d+$",
    ),
)
