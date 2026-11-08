"""The page design of a rebuilt book: trim, margins, body type, running heads and display skips.

One `PageDesign` holds each value once. `typst()` writes the page, text and paragraph rules from it.
"""

import re
from dataclasses import dataclass

from .presets import CompositionConfig

_LENGTH = re.compile(r"(?P<value>\d+(?:\.\d+)?)(?P<unit>pt|em)")


@dataclass(frozen=True)
class Length:
    value: float
    unit: str

    @classmethod
    def parse(cls, text: str) -> Length:
        match = _LENGTH.fullmatch(text.strip())
        if match is None:
            raise ValueError(f"{text!r} is not a length in pt or em")
        return cls(float(match["value"]), match["unit"])

    def pt(self, body_size_pt: float) -> float:
        return self.value * body_size_pt if self.unit == "em" else self.value

    def __str__(self) -> str:
        return f"{self.value:g}{self.unit}"


@dataclass(frozen=True)
class RunningHeads:
    head_size_pt: float
    folio_size_pt: float
    head_style: str
    rule_pt: float
    first_page: int


@dataclass(frozen=True)
class PageDesign:
    width_pt: float
    height_pt: float
    margin_inside_pt: float
    margin_outside_pt: float
    margin_top_pt: float
    margin_bottom_pt: float
    body_size_pt: float
    font: str
    lang: str
    hyphenate: bool
    leading: Length
    par_spacing: Length
    first_line_indent: Length
    display_above: Length
    display_below: Length
    display_leading: Length
    running_heads: RunningHeads

    def __post_init__(self) -> None:
        if self.text_width_pt <= 0 or self.text_height_pt <= 0:
            raise ValueError(
                f"the margins leave no text block on a {self.width_pt:g} by {self.height_pt:g} pt page"
            )
        if self.body_size_pt <= 0:
            raise ValueError(f"body size {self.body_size_pt:g} pt is not positive")

    @property
    def text_width_pt(self) -> float:
        return self.width_pt - self.margin_inside_pt - self.margin_outside_pt

    @property
    def text_height_pt(self) -> float:
        return self.height_pt - self.margin_top_pt - self.margin_bottom_pt

    def typst(self, title: str) -> str:
        """The `page`, `text`, `par` and display rules; `title` heads pages before the first chapter."""
        heads = self.running_heads
        font = self.font
        rule_line = (
            f"#v(-0.35em)\n      #line(length: 100%, stroke: {heads.rule_pt}pt + luma(120))"
            if heads.rule_pt > 0
            else ""
        )
        head = f'#text({heads.head_size_pt:g}pt, font: {font}, style: "{heads.head_style}")'
        folio = f"#text({heads.folio_size_pt:g}pt, font: {font})[#page-number]"
        return f"""#set page(
  width: {self.width_pt:g}pt,
  height: {self.height_pt:g}pt,
  margin: (inside: {self.margin_inside_pt:g}pt, outside: {self.margin_outside_pt:g}pt, top: {self.margin_top_pt:g}pt, bottom: {self.margin_bottom_pt:g}pt),
  header: context {{
    let strip-fn(it) = if type(it) == content and it.has("children") {{ it.children.filter(c => c.func() not in (footnote, (context none).func())).join() }} else if type(it) == content and it.func() == footnote {{ [] }} else {{ it }}
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if page-number > {heads.first_page - 1} and not on-chapter-page [
      #if calc.odd(page-number) [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let in-chapter = if chaps == () {{ heading.where(level: 2) }} else {{ heading.where(level: 2).after(chaps.last().location()) }}
        #let secs = query(in-chapter).filter(h => h.location().page() <= here().page())
        #let on-page = secs.filter(h => h.location().page() == here().page())
        #let title = strip-fn(if on-page != () {{ on-page.first().body }} else if secs != () {{ secs.last().body }} else if chaps != () {{ chaps.last().body }} else {{ "{title}" }})
        #grid(
          columns: (1fr, auto),
          align(left)[{head}[#title]],
          align(right)[{folio}]
        )
      ] else [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = strip-fn(if chaps != () {{ chaps.last().body }} else {{ "{title}" }})
        #grid(
          columns: (auto, 1fr),
          align(left)[{folio}],
          align(right)[{head}[#title]]
        )
      ]
      {rule_line}
    ]
  }},
  footer: context {{
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if page-number > {heads.first_page - 1} and on-chapter-page {{ align(center, {folio[1:]}) }}
  }}
)

#set text(
  font: {font},
  size: {self.body_size_pt:g}pt,
  lang: "{self.lang}",
  hyphenate: {"true" if self.hyphenate else "false"}
)

#set par(
  leading: {self.leading},
  spacing: {self.par_spacing},
  justify: true,
  first-line-indent: {self.first_line_indent},
  linebreaks: "optimized"
)

#show math.equation.where(block: true): set block(above: {self.display_above}, below: {self.display_below})
#show math.equation.where(block: true): set par(leading: {self.display_leading})
"""


def page_design(composition: CompositionConfig) -> PageDesign:
    """The design that a publisher preset and a language profile give together."""
    pub = composition.publisher
    lang = composition.language
    cjk = lang.code in ("zh", "ja")
    return PageDesign(
        width_pt=pub.width_pt,
        height_pt=pub.height_pt,
        margin_inside_pt=pub.margin_inside_pt,
        margin_outside_pt=pub.margin_outside_pt,
        margin_top_pt=pub.margin_top_pt,
        margin_bottom_pt=pub.margin_bottom_pt,
        body_size_pt=pub.body_size_pt,
        font=composition.typst_font_tuple(),
        lang=lang.typst_lang,
        hyphenate=lang.hyphenate,
        leading=Length.parse(lang.leading),
        par_spacing=Length.parse(lang.par_spacing),
        first_line_indent=Length.parse(lang.first_line_indent),
        display_above=Length(1.3, "em"),
        display_below=Length(1.3, "em"),
        display_leading=Length(0.88, "em"),
        running_heads=RunningHeads(
            head_size_pt=8.5,
            folio_size_pt=9.5,
            head_style="normal" if cjk else "italic",
            rule_pt=pub.header_rule_pt,
            first_page=5,
        ),
    )
