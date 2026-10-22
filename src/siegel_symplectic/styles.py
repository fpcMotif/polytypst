"""Styled editions of Siegel's paper that keep the text but take the look of the 1943 offprint:
its 381 x 608 pt page, centred running heads, roman chapter heads, bold section numbers and
small-capital theorem heads, each in its own paper, ink and accent colour."""

from dataclasses import dataclass, replace

from ..compiler.monograph import ChapterSpec, MonographCompiler, MonographSpec
from .spec import SIEGEL_SYMPLECTIC_SPEC

ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")


@dataclass(frozen=True)
class Style:
    name: str
    paper: str
    ink: str
    accent: str
    body_font: str
    math_font: str
    head_font: str
    number_type: str
    ornament: str


STYLES = (
    Style(
        name="journal",
        paper="#f6f0e1",
        ink="#1f1b16",
        accent="#1f1b16",
        body_font='"New Computer Modern"',
        math_font="New Computer Modern Math",
        head_font='("Gill Sans", "Source Sans 3")',
        number_type='"lining"',
        ornament="line(length: 20%, stroke: 0.5pt + accent)",
    ),
    Style(
        name="oxblood",
        paper="#f3ead6",
        ink="#2a2118",
        accent="#7a1f1d",
        body_font='("Baskervville", "STIX Two Text")',
        math_font="STIX Two Math",
        head_font='("Baskervville", "STIX Two Text")',
        number_type='"old-style"',
        ornament="stack(spacing: 2pt, line(length: 26%, stroke: 0.8pt + accent), line(length: 26%, stroke: 0.3pt + accent))",
    ),
    Style(
        name="indigo",
        paper="#f7f4ec",
        ink="#1c2230",
        accent="#23395d",
        body_font='"Libertinus Serif"',
        math_font="STIX Two Math",
        head_font='"Libertinus Serif"',
        number_type='"old-style"',
        ornament='text(9pt, fill: accent)[#sym.diamond.filled.small #h(0.6em) #sym.diamond.filled.small #h(0.6em) #sym.diamond.filled.small]',
    ),
)

PREAMBLE = """
#let paper = rgb("@PAPER@")
#let ink = rgb("@INK@")
#let accent = rgb("@ACCENT@")
#let body-font = @BODY@
#let head-font = @HEAD@
#let ornament = align(center, @ORNAMENT@)
#let chapter-page(n) = query(heading.where(level: 1)).any(h => h.location().page() == n)

#set page(
  width: 381pt,
  height: 608pt,
  margin: (inside: 46pt, outside: 40pt, top: 56pt, bottom: 54pt),
  fill: paper,
  header: context {
    let n = here().page()
    if n > 2 and not chapter-page(n) {
      set text(8pt, fill: ink, tracking: 0.1em, number-type: "lining")
      grid(
        columns: (3em, 1fr, 3em),
        align(left, if calc.even(n) { text(9.5pt, tracking: 0pt)[#n] }),
        align(center, text(fill: accent, if calc.odd(n) [@ODD@] else [@EVEN@])),
        align(right, if calc.odd(n) { text(9.5pt, tracking: 0pt)[#n] }),
      )
    }
  },
  footer: context {
    let n = here().page()
    if chapter-page(n) { align(center, text(9.5pt, fill: ink, number-type: "lining")[#n]) }
  },
)

#set text(font: body-font, size: 10pt, fill: ink, number-type: @NUMBERS@)
#show math.equation: set text(font: "@MATH@")
#set par(leading: 0.62em, spacing: 0.62em, first-line-indent: 1.2em, justify: true)
#show math.equation.where(block: true): set block(above: 0.9em, below: 0.9em)

#show heading.where(level: 1): it => {
  v(1.8em)
  align(center, text(font: head-font, size: 11pt, weight: "bold", tracking: 0.05em, fill: accent, upper(it.body)))
  v(0.7em)
  ornament
  v(1.3em)
}

#show strong: it => {
  let t = if it.body.has("text") { it.body.text } else { "" }
  if t.match(regex("^\\d+\\.$")) != none {
    text(weight: "bold", fill: accent, number-type: "lining", it.body)
  } else if t.match(regex("^(Theorem|Lemma|Corollary|Proposition|Definition)\\b")) != none {
    text(tracking: 0.04em, fill: accent, smallcaps(t))
  } else {
    it
  }
}

#show enum: it => {
  for (i, item) in it.children.enumerate() {
    let number = if item.number == auto { i + 1 } else { item.number }
    par[#text(weight: "bold", fill: accent, number-type: "lining")[#number.]#h(0.45em)#item.body]
  }
}

#show outline.entry.where(level: 1): it => {
  v(0.35em)
  it
}
"""

FRONT_MATTER = """
#page(header: none, footer: none)[
  #v(22%)
  #align(center)[
    #text(font: head-font, size: 15pt, weight: "bold", tracking: 0.06em, fill: accent)[SYMPLECTIC GEOMETRY.]
    #v(1.3em)
    #text(11pt)[By #smallcaps[Carl Ludwig Siegel.]]
    #v(1.6em)
    #ornament
    #v(2.4em)
    #text(9pt, style: "italic")[Reprinted from the American Journal of Mathematics,]
    #linebreak()
    #text(9pt, style: "italic")[Vol. LXV, No. 1, January, 1943.]
  ]
]

#page(header: none, footer: none)[
  #v(3em)
  #outline(title: align(center, text(font: head-font, size: 11pt, weight: "bold", tracking: 0.08em, fill: accent)[CONTENTS]), indent: 1.2em, depth: 1)
]
"""


def styled_spec(base: MonographSpec, style: Style) -> MonographSpec:
    """`base` with the offprint's page, heads and type in `style`'s colours."""
    preamble = PREAMBLE
    for key, value in {
        "@PAPER@": style.paper,
        "@INK@": style.ink,
        "@ACCENT@": style.accent,
        "@BODY@": style.body_font,
        "@HEAD@": style.head_font,
        "@ORNAMENT@": style.ornament,
        "@MATH@": style.math_font,
        "@NUMBERS@": style.number_type,
        "@ODD@": base.title.upper() + ".",
        "@EVEN@": base.author.upper() + ".",
    }.items():
        preamble = preamble.replace(key, value)
    return replace(
        base,
        slug=f"{base.slug}_{style.name}",
        chapters=[
            ChapterSpec(c.number, f"{ROMAN[c.number - 1]}. {c.title}.", c.start_page, c.end_page) for c in base.chapters
        ],
        chapter_heading="{title}",
        drop_line_regexes=(*base.drop_line_regexes, r"^By\s+CARL\s+LUDWIG\s+SIEGEL\.?\s*$"),
        typst_preamble=MonographCompiler(base).build_typst_preamble() + preamble,
        typst_front_matter=FRONT_MATTER,
    )


STYLED_SPECS = {style.name: styled_spec(SIEGEL_SYMPLECTIC_SPEC, style) for style in STYLES}
