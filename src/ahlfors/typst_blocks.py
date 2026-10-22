"""Typst preamble, title page and contents blocks of the Ahlfors 1979 McGraw-Hill edition."""

TYPST_PREAMBLE = r"""// ==============================================================================
// Lars V. Ahlfors — Complex Analysis (Third Edition, 1979)
// McGraw-Hill International Series in Pure and Applied Mathematics
// Reconstructed & Typeset via Polytypst (Authentic 1979 Publisher Standards)
// ==============================================================================

#set document(
  title: "Complex Analysis — Lars Ahlfors",
  author: "Lars V. Ahlfors",
  date: auto
)

// 6x9 inches (Crown Octavo) classic academic monograph trim
#set page(
  width: 432pt,
  height: 648pt,
  margin: (inside: 54pt, outside: 54pt, top: 54pt, bottom: 60pt),
  header: context {
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if page-number > 3 and not on-chapter-page [
      #if calc.odd(page-number) [
        #let chapters = query(heading.where(level: 1).before(here()))
        #let title = if chapters != () { chapters.last().body } else { "Complex Analysis" }
        #grid(
          columns: (1fr, auto),
          align(left)[#text(8.5pt, font: "New Computer Modern", style: "italic")[#smallcaps(title)]],
          align(right)[#text(9.5pt, font: "New Computer Modern")[#page-number]]
        )
      ] else [
        #grid(
          columns: (auto, 1fr),
          align(left)[#text(9.5pt, font: "New Computer Modern")[#page-number]],
          align(right)[#text(8.5pt, font: "New Computer Modern", style: "italic")[#smallcaps("Complex Analysis")]]
        )
      ]
      #v(-0.35em)
      #line(length: 100%, stroke: 0.35pt + rgb("#000000"))
    ]
  },
  footer: none
)

#set text(
  font: "New Computer Modern",
  size: 10pt,
  lang: "en",
  hyphenate: true
)

#set par(
  leading: 0.65em,
  spacing: 0.85em,
  justify: true,
  first-line-indent: 1.5em,
  linebreaks: "optimized"
)

#show math.equation: set text(font: "New Computer Modern Math")
#set math.equation(numbering: "(1)")
#let thm-break = block(above: 1.65em, below: 0pt, sticky: true)[]
#let sub-break = block(above: 1.35em, below: 0pt, sticky: true)[]
#let item-break = block(above: 1.0em, below: 0pt)[]
#let qed = { h(0.6em); box(width: 1fr, align(right)[$square.stroked$]) }
#let dd = math.dif
#let dv(f, x, deg: none) = if deg == none { $(dif f)/(dif x)$ } else { $(dif^deg f)/(dif x^deg)$ }
#let pdv(f, x, deg: none) = if deg == none { $(partial f)/(partial x)$ } else { $(partial^deg f)/(partial x^deg)$ }
#show ref: it => {
  let target = str(it.target)
  if target.starts-with("eq-") {
    let num = target.split("-").last()
    link(it.target)[(#num)]
  } else {
    it
  }
}
#show math.equation.where(block: true): it => {
  if it.numbering == none {
    return it
  }
  layout(size => {
    let eq = math.equation(it.body, block: true, numbering: none)
    if not it.has("label") {
      let m = measure(eq)
      if m.width > size.width and m.width > 0pt {
        let factor = (size.width / m.width) * 100%
        align(center, scale(x: factor, y: factor, reflow: true, eq))
      } else {
        eq
      }
    } else {
      let num = str(it.label).split("-").last()
      let num-box = [(#num)]
      let avail = size.width - measure(num-box).width - 12pt
      let m = measure(eq)
      let fitted = if m.width > avail and m.width > 0pt {
        let factor = (avail / m.width) * 100%
        scale(x: factor, y: factor, reflow: true, eq)
      } else {
        eq
      }
      grid(
        columns: (1fr, auto),
        column-gutter: 0.8em,
        align: (center + horizon, right + horizon),
        fitted,
        num-box
      )
    }
  })
}

#show heading: set par(justify: false, first-line-indent: 0pt)

// Classical 1979 McGraw-Hill Headings
#show heading.where(level: 1): it => {
  v(2.2em)
  align(center)[
    #text(15pt, weight: "bold", font: "New Computer Modern")[#it.body]
  ]
  v(1.6em)
}

#show heading.where(level: 2): it => block(above: 1.4em, below: 0.55em, sticky: true)[
  #text(11.5pt, weight: "bold", font: "New Computer Modern")[#it.body]
]

#show heading.where(level: 3): it => block(above: 1.1em, below: 0.35em, sticky: true)[
  #text(10.5pt, weight: "bold", font: "New Computer Modern")[#it.body]
]

#show heading.where(level: 4): it => block(above: 1.0em, below: 0.45em, sticky: true, width: 100%)[
  #align(center)[#text(9.5pt, weight: "bold", font: "New Computer Modern")[#smallcaps(it.body)]]
]

// Classical McGraw-Hill Figure Caption styling
#show figure.caption: it => [
  #v(0.35em)
  #text(8.5pt, font: "New Computer Modern")[#it.body]
]

"""

TOC_BLOCK = r"""// ==============================================================================
// Authentic 1979 McGraw-Hill Table of Contents
// ==============================================================================

#align(center)[
  #v(1.5em)
  #text(14pt, weight: "bold", font: "New Computer Modern")[#smallcaps("Contents")]
  #v(2em)
]

#[
#set par(first-line-indent: 0pt, leading: 0.85em, spacing: 0.9em)

#let toc-line(title, page-str, bold: false, indent: 0pt) = {
  block(width: 100%, spacing: 0.5em)[
    #h(indent)
    #if bold [
      #text(weight: "bold")[#title]
      #h(0.4em)
      #box(width: 1fr)[#repeat[#text(8.5pt)[. ]]]
      #h(0.4em)
      #text(weight: "bold")[#page-str]
    ] else [
      #text()[#title]
      #h(0.4em)
      #box(width: 1fr)[#repeat[#text(8.5pt)[. ]]]
      #h(0.4em)
      #text()[#page-str]
    ]
  ]
}

#toc-line("Preface", "xiii", bold: true)
#v(0.8em)

#toc-line("CHAPTER 1   COMPLEX NUMBERS", "1", bold: true)
#v(0.3em)
#toc-line("1   The Algebra of Complex Numbers", "1", bold: true, indent: 1.2em)
#toc-line("1.1  Arithmetic Operations", "1", indent: 2.4em)
#toc-line("1.2  Square Roots", "3", indent: 2.4em)
#toc-line("1.3  Justification", "4", indent: 2.4em)
#toc-line("1.4  Conjugation, Absolute Value", "6", indent: 2.4em)
#toc-line("1.5  Inequalities", "9", indent: 2.4em)
#v(0.3em)
#toc-line("2   The Geometric Representation of Complex Numbers", "12", bold: true, indent: 1.2em)
#toc-line("2.1  Geometric Addition and Multiplication", "12", indent: 2.4em)
#toc-line("2.2  The Binomial Equation", "15", indent: 2.4em)
#toc-line("2.3  Analytic Geometry", "17", indent: 2.4em)
#toc-line("2.4  The Spherical Representation", "18", indent: 2.4em)
#v(0.8em)

#toc-line("CHAPTER 2   COMPLEX FUNCTIONS", "21", bold: true)
#v(0.3em)
#toc-line("1   Introduction to the Concept of Analytic Function", "21", bold: true, indent: 1.2em)
#toc-line("1.1  Limits and Continuity", "22", indent: 2.4em)
#toc-line("1.2  Analytic Functions", "24", indent: 2.4em)
#toc-line("1.3  Polynomials", "28", indent: 2.4em)
#toc-line("1.4  Rational Functions", "30", indent: 2.4em)
#v(0.3em)
#toc-line("2   Elementary Theory of Power Series", "33", bold: true, indent: 1.2em)
#toc-line("2.1  Sequences", "33", indent: 2.4em)
#toc-line("2.2  Series", "35", indent: 2.4em)
#toc-line("2.3  Uniform Convergence", "35", indent: 2.4em)
#toc-line("2.4  Power Series", "38", indent: 2.4em)
#toc-line("2.5  Abel's Limit Theorem", "41", indent: 2.4em)
#v(0.3em)
#toc-line("3   The Exponential and Trigonometric Functions", "42", bold: true, indent: 1.2em)
#toc-line("3.1  The Exponential", "42", indent: 2.4em)
#toc-line("3.2  The Trigonometric Functions", "43", indent: 2.4em)
#toc-line("3.3  The Periodicity", "44", indent: 2.4em)
#toc-line("3.4  The Logarithm", "46", indent: 2.4em)
#v(0.8em)

#toc-line("CHAPTER 3   ANALYTIC FUNCTIONS AS MAPPINGS", "49", bold: true)
#v(0.3em)
#toc-line("1   Elementary Point Set Topology", "50", bold: true, indent: 1.2em)
#toc-line("2   Conformality", "67", bold: true, indent: 1.2em)
#toc-line("3   Linear Transformations", "76", bold: true, indent: 1.2em)
#toc-line("4   Elementary Conformal Mappings", "89", bold: true, indent: 1.2em)
#v(0.8em)

#toc-line("CHAPTER 4   COMPLEX INTEGRATION", "101", bold: true)
#v(0.3em)
#toc-line("1   Fundamental Theorems", "101", bold: true, indent: 1.2em)
#toc-line("2   Cauchy's Integral Formula", "114", bold: true, indent: 1.2em)
#toc-line("3   Local Properties of Analytical Functions", "124", bold: true, indent: 1.2em)
#toc-line("4   The General Form of Cauchy's Theorem", "137", bold: true, indent: 1.2em)
#toc-line("5   The Calculus of Residues", "148", bold: true, indent: 1.2em)
#toc-line("6   Harmonic Functions", "162", bold: true, indent: 1.2em)
#v(0.8em)

#toc-line("CHAPTER 5   SERIES AND PRODUCT DEVELOPMENTS", "175", bold: true)
#v(0.8em)

#toc-line("CHAPTER 6   CONFORMAL MAPPING. DIRICHLET'S PROBLEM", "229", bold: true)
#v(0.8em)

#toc-line("CHAPTER 7   ELLIPTIC FUNCTIONS", "263", bold: true)
#v(0.8em)

#toc-line("CHAPTER 8   GLOBAL ANALYTIC FUNCTIONS", "283", bold: true)
#v(0.8em)

#toc-line("INDEX", "313", bold: true)
]

#pagebreak()
"""

TITLE_PAGE_BLOCK: str = r"""
#align(center + horizon)[
  #text(10pt, font: "New Computer Modern")[#smallcaps("International Series in Pure and Applied Mathematics")]
  #v(2.5em)
  #text(24pt, weight: "bold", font: "New Computer Modern")[COMPLEX ANALYSIS]
  #v(0.8em)
  #text(11pt, style: "italic", font: "New Computer Modern")[An Introduction to the Theory of Analytic Functions\ of One Complex Variable]
  #v(1.5em)
  #text(10.5pt, weight: "bold", font: "New Computer Modern")[THIRD EDITION]
  #v(3em)
  #text(13pt, font: "New Computer Modern")[#smallcaps("Lars V. Ahlfors")]
  #v(0.4em)
  #text(9.5pt, style: "italic", font: "New Computer Modern")[Professor of Mathematics, Emeritus\ Harvard University]
  #v(4em)
  #text(10.5pt, weight: "bold", font: "New Computer Modern")[McGRAW-HILL BOOK COMPANY]
]

#pagebreak()
"""
