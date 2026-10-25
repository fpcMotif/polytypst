"""B. A. Dubrovin, A. T. Fomenko, S. P. Novikov: Modern Geometry—Methods and Applications. Part I."""

from ..compiler.monograph import ChapterSpec, FigureLayout, MonographSpec

MODERN_GEOMETRY_SPEC = MonographSpec(
    domain="math",
    slug="modern_geometry",
    title="Modern Geometry—Methods and Applications. Part I",
    author="B. A. Dubrovin, A. T. Fomenko, S. P. Novikov",
    source_pdf="Modern geometry--methods and applications (Dubrovin, B. A, Fomenko, A. T, Novikov).pdf",
    pdf_page_count=487,
    cross_references=True,
    figure_dir="figures",
    require_vector_figures=True,
    chapters=[ChapterSpec(1, "Modern Geometry—Methods and Applications. Part I", 1, 487)],
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.?\s*(?:(?P<chapter>\d+)[\.\-])?(?P<number>\d+[a-z]?)\.?(?:\*\*)?(?:\s+(?P<tail>.*))?\s*$",
        caption_format="Figure {number}",
    ),
)

MODERN_GEOMETRY_ILLUSTRATED_SPEC = MonographSpec(
    domain="math",
    slug="modern_geometry_illustrated",
    title="Modern Geometry—Methods and Applications. Part I",
    subtitle="Illustrated Edition with Colour Geometric Figures",
    author="B. A. Dubrovin, A. T. Fomenko, S. P. Novikov",
    source_pdf="Modern geometry--methods and applications (Dubrovin, B. A, Fomenko, A. T, Novikov).pdf",
    pdf_page_count=487,
    cross_references=True,
    figure_dir="figures_color",
    require_vector_figures=True,
    chapters=[ChapterSpec(1, "Modern Geometry—Methods and Applications. Part I", 1, 487)],
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.?\s*(?:(?P<chapter>\d+)[\.\-])?(?P<number>\d+[a-z]?)\.?(?:\*\*)?(?:\s+(?P<tail>.*))?\s*$",
        caption_format="Figure {number}",
    ),
)
