"""Frigyes Riesz and Béla Sz.-Nagy: Functional Analysis."""

from ..compiler.monograph import ChapterSpec, MonographSpec

FUNCTIONAL_ANALYSIS_SPEC = MonographSpec(
    domain="math",
    slug="functional_analysis",
    title="Functional Analysis",
    author="Frigyes Riesz and Béla Sz.-Nagy",
    publisher="Frederick Ungar Publishing Co.",
    series="",
    year=1955,
    source_pdf="Functional analysis (Riesz, Frigyes, Sz.-Nagy).pdf",
    pdf_page_count=478,
    preface_page=4,
    references_page=457,
    index_pages=(468, 477),
    index_title="Index",
    cross_references=True,
    chapters=[
        ChapterSpec(1, "Differentiation", 15, 40),
        ChapterSpec(2, "The Lebesgue Integral", 41, 116),
        ChapterSpec(3, "The Stieltjes Integral and Its Generalizations", 117, 153),
        ChapterSpec(4, "Integral Equations", 154, 205),
        ChapterSpec(5, "Hilbert and Banach Spaces", 206, 237),
        ChapterSpec(6, "Completely Continuous Symmetric Transformations of Hilbert Space", 238, 271),
        ChapterSpec(7, "Bounded Symmetric, Unitary, and Normal Transformations of Hilbert Space", 272, 306),
        ChapterSpec(8, "Unbounded Linear Transformations of Hilbert Space", 307, 351),
        ChapterSpec(9, "Self-Adjoint Transformations. Functional Calculus, Spectrum, Perturbations", 352, 390),
        ChapterSpec(10, "Groups and Semigroups of Transformations", 391, 425),
        ChapterSpec(11, "Spectral Theories for Linear Transformations of General Type", 426, 456),
    ],
    running_header_regexes=(
        r"^([0-9IVXLCDM]+\.?\s*)?(?:differentiation|the lebesgue integral|the stieltjes integral|integral equations|hilbert and banach spaces|completely continuous|bounded symmetric|unbounded linear|self-adjoint transformations|groups and semigroups|spectral theories|functional analysis|contents|bibliography|index)\b",
    ),
    latex_preamble=r"""
\DeclareUnicodeCharacter{2070}{\textsuperscript{0}}
\DeclareUnicodeCharacter{2074}{\textsuperscript{4}}
\DeclareUnicodeCharacter{2075}{\textsuperscript{5}}
\DeclareUnicodeCharacter{2076}{\textsuperscript{6}}
\DeclareUnicodeCharacter{2077}{\textsuperscript{7}}
\DeclareUnicodeCharacter{2078}{\textsuperscript{8}}
\DeclareUnicodeCharacter{2079}{\textsuperscript{9}}
\DeclareUnicodeCharacter{00B9}{\textsuperscript{1}}
\DeclareUnicodeCharacter{00B2}{\textsuperscript{2}}
\DeclareUnicodeCharacter{00B3}{\textsuperscript{3}}
\DeclareUnicodeCharacter{0150}{\H{O}}
\DeclareMathOperator{\arccot}{arccot}
""",
)
