"""Felix Klein: Development of Mathematics in the 19th Century (Math Sci Press, 1979)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"DEVELOPMENT OF MATHEMATICS|GAUSS|APPLIED MATHEMATICS|PURE MATHEMATICS|"
    r"FRANCE AND THE ECOLE POLYTECHNIQUE|CRELLE'S JOURNAL|ALGEBRAIC GEOMETRY|"
    r"MECHANICS AND MATHEMATICAL PHYSICS|RIEMANN AND WEIERSTRASS|"
    r"ALGEBRAIC VARIETIES|GROUP THEORY|AUTOMORPHIC FUNCTIONS|INTRODUCTION|PREFACE|CONTENTS|"
    r"KLEINIAN MATHEMATICS|APPENDIX|APPENDICES"
)

KLEIN_SPEC = MonographSpec(
    slug="klein_development_19th_century",
    title="Development of Mathematics in the 19th Century",
    footnote_style="symbol",
    footnote_marks=("*", "**", "***"),
    author="Felix Klein",
    translator="M. Ackerman",
    editor="Robert Hermann",
    publisher="Math Sci Press",
    series="Lie Groups: History, Frontiers and Applications, Volume IX",
    year=1979,
    publisher_key="springer",
    pdf_page_count=634,
    pdf_name_markers=("development of mathematics", "felix klein", "klein"),
    preface_page=4,
    chapters=[
        ChapterSpec(0, "Introduction", 10, 14),
        ChapterSpec(1, "Gauss", 15, 66),
        ChapterSpec(2, "France and the École Polytechnique in the First Decades of the 19th Century", 67, 91),
        ChapterSpec(3, "The Founding of Crelle's Journal and the Rise of Pure Mathematics in Germany", 92, 126),
        ChapterSpec(4, "The Development of Algebraic Geometry after Möbius, Plücker and Steiner", 127, 184),
        ChapterSpec(5, "Mechanics and Mathematical Physics in Germany and England until about 1880", 185, 238),
        ChapterSpec(6, "The General Theory of Functions of Complex Variables according to Riemann and Weierstrass", 239, 284),
        ChapterSpec(7, "Deeper Insight into the Nature of Algebraic Varieties and Structures", 285, 322),
        ChapterSpec(8, "Group Theory and Function Theory; Automorphic Functions", 323, 370),
        ChapterSpec(9, "Appendices: Kleinian Mathematics from an Advanced Standpoint", 371, 634),
    ],
    sections={
        "0.1": (10, "Introduction"),
        "1.1": (15, "Biographical Data and General Characterization"),
        "1.2": (16, "Applied Mathematics"),
        "1.3": (39, "Pure Mathematics"),
    },
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Figure\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_format="Figure {chapter}.{number}",
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(
        r"^Lie Groups: History, Frontiers and Applications.*$",
        r"^Volume IX.*$",
        r"^\d+\s+[A-Z\s\$\-\.\,]+$",
        r"^[A-Z\s\$\-\.\,]+\s+\d+$",
    ),
    pre_math_rewrites=(
        (r"\bGaus\s+s\b", "Gauss"),
        (r"\bGoettingen\b", "Göttingen"),
        (r"\bPluecker\b", "Plücker"),
        (r"\bMoebius\b", "Möbius"),
        (r"\bBraunschweig\b", "Brunswick"),
        (r"plus\.circle", r"\\u{2295}"),
    ),
)
