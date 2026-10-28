"""Vladimir I. Arnold: Ordinary Differential Equations."""

from ..compiler.monograph import ChapterSpec, FigureLayout, MonographSpec

ODE_ARNOLD_SPEC = MonographSpec(
    domain="math",
    slug="ode_arnold",
    title="Ordinary Differential Equations",
    author="Vladimir I. Arnold",
    translator="Richard A. Silverman",
    publisher="Springer-Verlag",
    year=1992,
    source_pdf="Ordinary Differential Equations (Vladimir I. Arnold) .pdf",
    pdf_name_markers=("Ordinary Differential Equations", "Arnold"),
    pdf_page_count=338,
    preface_page=5,
    index_pages=(335, 338),
    index_title="Subject Index",
    cross_references=True,
    chapters=[
        ChapterSpec(1, "Basic Concepts", 17, 92),
        ChapterSpec(2, "Basic Theorems", 93, 155),
        ChapterSpec(3, "Linear Systems", 156, 270),
        ChapterSpec(4, "Proofs of the Main Theorems", 271, 291),
        ChapterSpec(5, "Differential Equations on Manifolds", 292, 326),
        ChapterSpec(6, "Examination Topics and Problems", 327, 334, label=""),
    ],
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.?\s*(?P<number>\d+[a-z]?)\.?(?:\*\*)?(?:\s+(?P<tail>.*))?\s*$",
        caption_format="Figure {number}",
    ),
    running_header_regexes=(
        r"^([0-9IVXLCDM]+\.?\s*)?(?:basic concepts|basic theorems|linear systems|proofs of the main theorems|differential equations on manifolds|phase spaces|vector fields|linear equations|phase flows|diffeomorphisms|symmetries|rectification|autonomous system|first integrals|conservative system|linear problems|exponential function|diagonalizable operator|complexification|singular points|topological classification|stability of equilibrium|purely imaginary|multiple eigenvalues|quasi-polynomials|nonautonomous linear|periodic coefficients|variation of constants|contraction mappings|differentiability|differentiable manifolds|tangent bundle|indices of the singular points|examination topics|contents|preface|index)\b",
    ),
    latex_preamble=r"""
\usepackage{graphicx}
\DeclareMathOperator{\arccot}{arccot}
\ifPDFTeX
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
  \DeclareUnicodeCharacter{25A1}{\ensuremath{\square}}
\fi
\makeatletter
\AtBeginDocument{%
  \pdfstringdefDisableCommands{%
    \def\delta{delta}%
    \def\alpha{alpha}%
    \def\beta{beta}%
    \def\omega{omega}%
  }%
}
\makeatother
""",
)
