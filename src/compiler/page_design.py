"""The page design of a rebuilt book: trim, margins, body type, running heads and display skips.

One `PageDesign` holds each value once. `typst()` writes the page, text and paragraph rules from it,
and `audit()` measures a compiled PDF against the same values.
"""

import re
import statistics
from dataclasses import dataclass
from itertools import pairwise

import pymupdf

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
    max_hyphen_run: int = 3

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

    @property
    def pitch_range(self) -> tuple[float, float]:
        """The line pitch, as a multiple of the body size, that the publisher bar allows."""
        return (1.4, 1.8) if self.lang in ("zh", "ja") else (1.15, 1.5)

    def audit(
        self, doc: pymupdf.Document, skip_pages: frozenset[int] = frozenset()
    ) -> list[Finding]:
        """What on the pages of `doc` departs from this design; `skip_pages` are 1-based page numbers."""
        pages = [
            _Page.read(self, page) for page in doc if page.number + 1 not in skip_pages
        ]
        return [
            *_page_size(self, pages),
            *_text_block_edges(self, pages),
            *_line_pitch(self, pages),
            *_hyphen_runs(self, pages),
            *_loose_lines(self, pages),
        ]

    def chapter_folio_footer(self) -> str:
        """The page footer: the folio, centred, on each page that opens a chapter."""
        folio = f"text({self.running_heads.folio_size_pt:g}pt, font: {self.font})[#page-number]"
        return f"""context {{
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if on-chapter-page {{ align(center, {folio}) }}
  }}"""

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
  footer: {self.chapter_folio_footer()}
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


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    page: int
    message: str
    snippet: str = ""


@dataclass(frozen=True)
class _Line:
    block: int
    x0: float
    x1: float
    baseline: float
    text: str
    words: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class _Page:
    number: int
    width: float
    height: float
    lines: tuple[_Line, ...]

    @classmethod
    def read(cls, design: PageDesign, page: pymupdf.Page) -> _Page:
        """The body lines of `page`: text at the body size, inside the text block's height, with no math font."""
        top, foot = design.margin_top_pt, page.rect.height - design.margin_bottom_pt
        words = page.get_text("words")
        lines = []
        for b, block in enumerate(page.get_text("dict")["blocks"]):
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans or any(
                    "Math" in s["font"] or abs(s["size"] - design.body_size_pt) > 0.35
                    for s in spans
                ):
                    continue
                x0, y0, x1, y1 = line["bbox"]
                if not top <= spans[0]["origin"][1] <= foot:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                inked = tuple(
                    sorted(
                        (w[0], w[2])
                        for w in words
                        if y0 <= (w[1] + w[3]) / 2 <= y1 and x0 - 1 <= w[0] <= x1
                    )
                )
                if inked:
                    x0, x1 = inked[0][0], inked[-1][1]
                lines.append(_Line(b, x0, x1, spans[0]["origin"][1], text, inked))
        return cls(page.number + 1, page.rect.width, page.rect.height, tuple(lines))


def _page_size(design: PageDesign, pages: list[_Page]) -> list[Finding]:
    trims = {
        (round(design.width_pt), round(design.height_pt)),
        (round(design.height_pt), round(design.width_pt)),
    }
    return [
        Finding(
            "ERROR",
            "PAGE_SIZE",
            p.number,
            f"Page is {p.width:.0f} by {p.height:.0f} pt, the design is {design.width_pt:g} by {design.height_pt:g} pt",
        )
        for p in pages
        if (round(p.width), round(p.height)) not in trims
    ]


def _text_block_edges(design: PageDesign, pages: list[_Page]) -> list[Finding]:
    out = []
    for p in pages:
        wide = [ln for ln in p.lines if ln.x1 - ln.x0 > 0.8 * design.text_width_pt]
        if len(wide) < 5:
            continue
        left = statistics.quantiles([ln.x0 for ln in wide], n=10, method="inclusive")[0]
        expected = design.margin_inside_pt if p.number % 2 else design.margin_outside_pt
        if abs(left - expected) > 2:
            out.append(
                Finding(
                    "WARNING",
                    "TEXT_BLOCK_OFFSET",
                    p.number,
                    f"Text starts at {left:.1f} pt, the design puts the {'inside' if p.number % 2 else 'outside'} margin at {expected:g} pt",
                )
            )
            continue
        ends = [ln.x1 for ln in wide if ln.text[-1:].isalnum()]
        if len(ends) < 2:
            continue
        right = statistics.quantiles(ends, n=10, method="inclusive")[-1]
        if abs(right - expected - design.text_width_pt) > 2:
            out.append(
                Finding(
                    "WARNING",
                    "TEXT_BLOCK_WIDTH",
                    p.number,
                    f"Justified lines end at {right:.1f} pt, the design ends them at {expected + design.text_width_pt:g} pt",
                )
            )
    return out


def _pitches(page: _Page, size: float) -> list[float]:
    return [
        round(b.baseline - a.baseline, 1)
        for a, b in pairwise(page.lines)
        if 0 < b.baseline - a.baseline < 2.5 * size and a.x0 < b.x1 and b.x0 < a.x1
    ]


def _line_pitch(design: PageDesign, pages: list[_Page]) -> list[Finding]:
    size = design.body_size_pt
    per_page = {p.number: _pitches(p, size) for p in pages}
    every = [d for ds in per_page.values() for d in ds]
    if len(every) < 20:
        return []
    book = statistics.median(every)
    low, high = design.pitch_range
    out = []
    if not low <= book / size <= high:
        first = next(n for n, ds in per_page.items() if ds)
        out.append(
            Finding(
                "ERROR",
                "LINE_PITCH",
                first,
                f"Body lines are {book:.1f} pt apart, {book / size:.2f} times the {size:g} pt body; the bar allows {low:g} to {high:g}",
            )
        )
    for number, ds in per_page.items():
        if len(ds) >= 8 and abs(statistics.median(ds) - book) > 0.25:
            out.append(
                Finding(
                    "WARNING",
                    "UNEVEN_LINE_PITCH",
                    number,
                    f"Body lines are {statistics.median(ds):.1f} pt apart here and {book:.1f} pt in the book",
                )
            )
    return out


def _hyphen_runs(design: PageDesign, pages: list[_Page]) -> list[Finding]:
    out = []
    for p in pages:
        run: list[_Line] = []
        for line in p.lines:
            hyphenated = line.text[-1:] in ("-", "‐", "­") and line.text[-2:-1].isalpha()
            same_paragraph = not run or run[-1].block == line.block
            run = ([*run, line] if same_paragraph else [line]) if hyphenated else []
            if len(run) == design.max_hyphen_run + 1:
                out.append(
                    Finding(
                        "WARNING",
                        "HYPHEN_RUN",
                        p.number,
                        f"{len(run)} lines in a row end in a hyphen; the design allows {design.max_hyphen_run}",
                        run[0].text[-40:],
                    )
                )
    return out


def _loose_lines(design: PageDesign, pages: list[_Page]) -> list[Finding]:
    """Justified lines whose median word space passes M/2. The last line of a block is ragged, so it is skipped."""
    out = []
    em = design.body_size_pt
    for p in pages:
        loose = []
        for a, b in pairwise(p.lines):
            if a.block != b.block or len(a.words) < 4:
                continue
            gaps = [(right[0] - left[1]) / em for left, right in pairwise(a.words)]
            if statistics.median(gaps) > 0.5:
                loose.append(a)
        if loose:
            out.append(
                Finding(
                    "WARNING",
                    "LOOSE_LINE",
                    p.number,
                    f"{len(loose)} justified line(s) set their word spaces wider than 0.5 em",
                    loose[0].text[:60],
                )
            )
    return out
