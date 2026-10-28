"""B. A. Dubrovin, A. T. Fomenko, S. P. Novikov: Modern Geometry—Methods and Applications. Part II. The Geometry and Topology of Manifolds."""

from polytypst.compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographCompiler,
    MonographSpec,
)

_BASE = MonographSpec(
    domain="math",
    slug="modern_geometry_vol2",
    title="Modern Geometry—Methods and Applications. Part II. The Geometry and Topology of Manifolds",
    author="B. A. Dubrovin, A. T. Fomenko, S. P. Novikov",
    publisher="Springer-Verlag",
    publisher_key="springer",
    translator="Robert G. Burns",
    series="Graduate Texts in Mathematics",
)

_PREAMBLE = MonographCompiler(_BASE).build_typst_preamble() + "\n#show heading.where(level: 1): set par(leading: 0.38em)\n"
_FRONT_MATTER = MonographCompiler(_BASE).build_typst_title_page() + "\n#set heading(numbering: none)\n"

_LATEX_PREAMBLE = r"""
\usepackage{newunicodechar}
\newunicodechar{□}{\ensuremath{\qedsymbol}}
\AtBeginDocument{
  \renewcommand{\setminus}{\mathbin{\backslash}}
}
"""

MODERN_GEOMETRY_VOL2_SPEC = MonographSpec(
    domain="math",
    slug="modern_geometry_vol2",
    title="Modern Geometry—Methods and Applications. Part II. The Geometry and Topology of Manifolds",
    author="B. A. Dubrovin, A. T. Fomenko, S. P. Novikov",
    translator="Robert G. Burns",
    publisher="Springer-Verlag",
    publisher_key="springer",
    series="Graduate Texts in Mathematics",
    year=1985,
    source_pdf="GTM104-Modern Geometry — Methods and Applications Part II.The Geometry and Topology of Manifolds1985.pdf",
    pdf_page_count=447,
    chapters=[
        ChapterSpec(1, "Examples of Manifolds", 17, 80),
        ChapterSpec(2, "Foundational Questions. Essential Facts Concerning Functions on a Manifold. Typical Smooth Mappings", 81, 114),
        ChapterSpec(3, "The Degree of a Mapping. The Intersection Index of Submanifolds. Applications", 115, 150),
        ChapterSpec(4, "Orientability of Manifolds. The Fundamental Group. Covering Spaces (Fibre Bundles with Discrete Fibre)", 151, 200),
        ChapterSpec(5, "Homotopy Groups", 201, 235),
        ChapterSpec(6, "Smooth Fibre Bundles", 236, 312),
        ChapterSpec(7, "Some Examples of Dynamical Systems and Foliations on Manifolds", 313, 373),
        ChapterSpec(8, "The Global Structure of Solutions of Higher-Dimensional Variational Problems", 374, 434),
    ],
    references_page=435,
    index_pages=(438, 445),
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.?\s*(?:(?P<chapter>\d+)[\.\-])?(?P<number>\d+[a-z]?)\.?(?:\*\*)?(?:\s+(?P<tail>.*))?\s*$",
        caption_format="Figure {number}",
        supplement_none=False,
    ),
    typst_preamble=_PREAMBLE,
    typst_front_matter=_FRONT_MATTER,
    latex_preamble=_LATEX_PREAMBLE,
    cross_references=True,
    require_vector_figures=True,
)

MODERN_GEOMETRY_VOL2_ILLUSTRATED_SPEC = MonographSpec(
    domain="math",
    slug="modern_geometry_vol2_illustrated",
    title="Modern Geometry—Methods and Applications. Part II. The Geometry and Topology of Manifolds",
    subtitle="Illustrated Edition with Colour Geometric Figures",
    author="B. A. Dubrovin, A. T. Fomenko, S. P. Novikov",
    translator="Robert G. Burns",
    publisher="Springer-Verlag",
    publisher_key="springer",
    series="Graduate Texts in Mathematics",
    year=1985,
    source_pdf="GTM104-Modern Geometry — Methods and Applications Part II.The Geometry and Topology of Manifolds1985.pdf",
    pdf_page_count=447,
    figure_dir="figures_color",
    require_vector_figures=True,
    chapters=[
        ChapterSpec(1, "Examples of Manifolds", 17, 80),
        ChapterSpec(2, "Foundational Questions. Essential Facts Concerning Functions on a Manifold. Typical Smooth Mappings", 81, 114),
        ChapterSpec(3, "The Degree of a Mapping. The Intersection Index of Submanifolds. Applications", 115, 150),
        ChapterSpec(4, "Orientability of Manifolds. The Fundamental Group. Covering Spaces (Fibre Bundles with Discrete Fibre)", 151, 200),
        ChapterSpec(5, "Homotopy Groups", 201, 235),
        ChapterSpec(6, "Smooth Fibre Bundles", 236, 312),
        ChapterSpec(7, "Some Examples of Dynamical Systems and Foliations on Manifolds", 313, 373),
        ChapterSpec(8, "The Global Structure of Solutions of Higher-Dimensional Variational Problems", 374, 434),
    ],
    references_page=435,
    index_pages=(438, 445),
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.?\s*(?:(?P<chapter>\d+)[\.\-])?(?P<number>\d+[a-z]?)\.?(?:\*\*)?(?:\s+(?P<tail>.*))?\s*$",
        caption_format="Figure {number}",
        supplement_none=False,
    ),
    typst_preamble=_PREAMBLE,
    typst_front_matter=_FRONT_MATTER,
    latex_preamble=_LATEX_PREAMBLE,
    cross_references=True,
)
