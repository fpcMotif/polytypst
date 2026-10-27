"""Native Typst and LaTeX numbering for books that number sections, paragraphs and equations like EGA.

The scan prints `§ 1.`, `1.2.`, `(1.2.9)` and `(1.2.9.1)`. Typst numbers them with its heading and equation
counters, and LaTeX with its own counters, so the text carries no typed numbers. Where the computed number
would differ from the scan's, because OCR lost or split a heading, a counter update restores the scan's number,
and the build lists it."""

import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

TYPST_RULES = r"""
#let source-article = counter("source-article")
#let source-roman = counter("source-roman")
#let source-circled = counter("source-circled")
#let source-heading-number(..nums) = {
  let n = nums.pos().slice(1)
  if n.len() == 1 { "§ " + str(n.first()) + "." }
  else if n.len() == 2 { n.map(str).join(".") + "." }
  else if n.len() > 2 { "(" + n.map(str).join(".") + ")" }
}
#let source-article-number(..nums) = str(source-article.get().first() + 1) + "."
#let source-equation-number(n) = "(" + (counter(heading).get().slice(1) + (n,)).map(str).join(".") + ")"
#let source-digits(el) = {
  let nums = counter(heading).at(el.location()).slice(1)
  if el.func() == math.equation or (el.func() == metadata and el.value == "item") { nums += counter(math.equation).at(el.location()) }
  nums.map(str).join(".")
}
#let source-paragraph(kind) = {
  counter(heading).step(level: 4)
  counter(math.equation).update(0)
  context strong(if kind == [] { counter(heading).display(source-heading-number) } else { [#kind #counter(heading).display(source-heading-number)] })
  h(0.5em)
}
#let source-item = {
  counter(math.equation).step()
  context strong(source-equation-number(counter(math.equation).get().first()))
  h(0.5em)
}
#let source-roman-item = {
  source-roman.step()
  context strong(source-roman.display("I."))
  h(0.5em)
}
#let source-circled-item = {
  source-circled.step()
  context str.from-unicode(0x2460 + source-circled.get().first() - 1)
}
#set heading(numbering: source-heading-number)
#show heading.where(level: 1): set heading(numbering: none)
#show figure.where(kind: image): set figure(supplement: [图])
#show figure.where(kind: table): set figure(supplement: [表])
#set math.equation(numbering: none)
#show heading: it => {
  counter(math.equation).update(0)
  if it.level == 3 and it.numbering == source-article-number {
    source-article.step()
  }
  it
}
#show ref: it => {
  let el = it.element
  let target = str(it.target)
  if el == none { return it }
  if target.starts-with("art-") {
    let n = source-article.at(el.location()).first() + 1
    return link(el.location())[#n]
  }
  if target.starts-with("eq-art-") {
    let n = counter(math.equation).at(el.location()).first()
    return link(el.location())[(#n)]
  }
  if not (target.starts-with("par-c") or target.starts-with("eq-c")) { return it }
  let chapter = if it.supplement in (auto, none) { [] } else { [#it.supplement, ] }
  link(el.location())[(#chapter#source-digits(el))]
}
"""

TYPST_EQUATION_LAYOUT = r"""
#show math.equation.where(block: true): it => {
  if it.numbering == none { return it }
  layout(size => {
    let number = counter(math.equation).display(it.numbering)
    grid(
      columns: (1fr, auto),
      column-gutter: 0.8em,
      align: (center + horizon, right + horizon),
      fit-display(it.body, size.width - measure(number).width - 12pt),
      number,
    )
  })
}
"""

LATEX_RULES = (
    r"\newcounter{sourcesection}\newcounter{sourcesubsection}[sourcesection]"
    r"\newcounter{sourceparagraph}[sourcesubsection]\newcounter{sourcearticle}\newcounter{sourceroman}\newcounter{sourcecircled}"
    r"\renewcommand\thesourcesubsection{\arabic{sourcesection}.\arabic{sourcesubsection}}"
    r"\renewcommand\thesourceparagraph{\thesourcesubsection.\arabic{sourceparagraph}}"
    r"\counterwithin*{equation}{sourceparagraph}"
    r"\renewcommand\theequation{\ifnum\value{sourceparagraph}>0 \thesourceparagraph.\arabic{equation}\else\ifnum\value{sourcesubsection}>0 \thesourcesubsection.\arabic{equation}\else\arabic{equation}\fi\fi}"
    r"\newcommand\sourcesection[1]{\refstepcounter{sourcesection}\setcounter{equation}{0}"
    r"\section*{\S\,\arabic{sourcesection}. #1}\addcontentsline{toc}{section}{\S\,\arabic{sourcesection}. #1}}"
    r"\newcommand\sourcesubsection[1]{\refstepcounter{sourcesubsection}\setcounter{equation}{0}\subsection*{\thesourcesubsection. #1}}"
    r"\newcommand\sourcearticle[1]{\refstepcounter{sourcearticle}\setcounter{equation}{0}"
    r"\subsection*{\arabic{sourcearticle}. #1}\addcontentsline{toc}{subsection}{\arabic{sourcearticle}. #1}}"
    r"\newcommand\sourceparagraph[1]{\par\refstepcounter{sourceparagraph}"
    r"\textbf{#1(\thesourceparagraph)}\enspace\ignorespaces}"
    r"\newcommand\sourceitem{\refstepcounter{equation}\textbf{(\theequation)}\enspace\ignorespaces}"
    r"\newcommand\sourceroman{\refstepcounter{sourceroman}\textbf{\Roman{sourceroman}.}\enspace\ignorespaces}"
    r"\newcommand\sourcecircled{\refstepcounter{sourcecircled}\textcircled{\arabic{sourcecircled}}}"
)

_NUMBER = r"\d+(?:\.\d+)+"
_KINDS = r"(?:Proposition|Corollaire|D[ée]finition|Remarques?|Lemme|Th[ée]or[èe]me|Exemples?|Scholie)"
_ROMAN_VALUES = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
_SECTION_RE = re.compile(r"^(?:§\s*)?(\d+)\.?\s+(\D.*)$")
_SUBSECTION_RE = re.compile(r"^(\d+)\.(\d+)\.?\s+(.*)$")
_PARAGRAPH_HEADING_RE = re.compile(rf"^\(({_NUMBER})\.?\)\s*(.*)$")
_REF_RE = re.compile(rf"\((?:(?P<chapter>0|I{{1,3}}|IV|VI{{0,3}}|IX|X), ?)?(?P<number>{_NUMBER})\.?\)")
_FIG_REF_RE = re.compile(r"(?i)(?:\bFig(?:ure)?(?:\.|\b)|图)\s*(?P<fig>\d+(?:[.\-]\d+){0,2}[a-z]?)(?![\d\-]|\.\d)")
_ART_EQ_RE = re.compile(
    r"(?<![(\w§\d\-])(?<!,\s)(?P<art>\d{1,3})(?P<sep>\s*(?:,\s*|\s+目的|\s+)?(?:公式\s*)?)\((?P<eq>\d+[a-z*]?)\)"
)
_BRACKET_REF_RE = {
    "typst": re.compile(r"\\\[(?:[^\[\]\\]|\\.|#strong\[\d+\])*\\\]|(?<![\w@>\]])\[[^\[\]\n]+\]"),
    "latex": re.compile(r"(?<!!)\[[^\[\]\n]+\]"),
}
_BRACKET_ART_RE = re.compile(
    r"(?<![.\w§\d\-@\\{])(?<!定理 )(?<!例 )(?<!例题 )(?<!脚注 )(?<!图 )(?P<bold>#strong\[|\*\*)?(?P<art>\d{1,3})(?(bold)(?:\]|\*\*))(?![.\d°a-z*})])(?!\s*(?:倍|年|月|日|%|％|个|种|位|次|名|家|人))"
)
_BRACKET_EQ_RE = re.compile(r"\((?P<eq>\d+)\)")
_PROSE_ART_RE = re.compile(
    r"(?P<pre>(?:在|由|依|据|按|见|看|同|如|照|对|比较|参阅|参看|第|推广)\s*)(?P<pbold>#strong\[|\*\*)?(?P<art>\d{1,3})(?(pbold)(?:\]|\*\*))(?=(?:\s*,\s*\d+[)°]|\s*(?:内|中|末|初|目|月|的|之)))"
)
_PROSE_EQ_RE = re.compile(
    r"(?P<pre>(?:方程(?:组)?|公式|等式|不等式|关系式|展开式|条件|曲线|显式)\s*)\((?P<eq1>\d+)\)"
    r"(?:(?P<mid>\s*(?:及|与|或|、|,)\s*)\((?P<eq2>\d+)\))?"
)
_TYPST_FIG_RE = re.compile(
    r"#figure\(\n(?P<img>  image\([^\n]+\),\n)"
    r"  caption: \[(?:#strong\[)?(?i:Fig(?:ure)?(?:\.|\b)|图)\s*(?P<fig>\d+(?:[.\-]\d+){0,2}[a-z]?)\.?(?:\])?[ \t]*(?P<cap>[^\n]*)\]"
    r"(?:,\n  supplement: none)?\n\)(?!\s*<fig-)"
)
_LATEX_FIG_RE = re.compile(
    r"!\[(?:\*\*)?(?P<sup>(?i:Fig(?:ure)?(?:\.|\b)|图))\s*(?P<fig>\d+(?:[.\-]\d+){0,2}[a-z]?)\.?(?:\*\*)?[ \t]*(?P<cap>.*?)\s*\]\((?P<path>[^)]+)\)"
)
_PAGE_MARK = r"(?:#src-top\(\d+\);)?"
_BIB_ENTRY_RE = re.compile(rf"(?m)^{_PAGE_MARK}\\?\[(?P<key>\d+(?: bis)?|[A-Z]{{2,4}})\\?\] ")
_LABEL_RE = re.compile(r"(?:<|\\label\{)((?:eq|par)-c\d+(?:-\d+)+|art-\d+|eq-art-\d+-\d+|(?:fig|tbl)-[\w-]+)")


class _Writer(Protocol):
    """How one output format writes the numbered elements; the numbers themselves come from its counters."""

    events: re.Pattern[str]
    math: re.Pattern[str]
    chapter_start: str

    def set_levels(self, nums: tuple[int, ...]) -> str: ...
    def set_article(self, n: int) -> str: ...
    def set_roman(self, n: int) -> str: ...
    def set_equation(self, n: int) -> str: ...
    def section(self, title: str) -> str: ...
    def subsection(self, title: str) -> str: ...
    def article(self, title: str, label: str) -> str: ...
    def unnumbered(self, marks: str, title: str) -> str: ...
    def paragraph(self, kind: str, label: str) -> str: ...
    def item(self, kind: str, label: str) -> str: ...
    def roman_item(self, prefix: str) -> str: ...
    def set_circled(self, n: int) -> str: ...
    def circled_item(self) -> str: ...
    def equation(self, body: str, label: str, simple: bool = False) -> str: ...
    def label(self, name: str) -> str: ...
    def ref(self, name: str, chapter: str | None) -> str: ...
    def target(self, name: str) -> str: ...
    def link(self, name: str, text: str) -> str: ...


class TypstWriter:
    events = re.compile(
        rf"(?m)^(?P<heading>={{2,4}} .+)$"
        rf"|#strong\[(?:(?P<kind>{_KINDS})\s+)?\((?P<bold>{_NUMBER})\.?\)\.?\]"
        rf"|^(?:#h\([^)]*\);)?(?P<top>#src-top\(\d+\);)?\((?P<plain>{_NUMBER})\.?\)(?= )"
        r"|^(?P<rtop>(?:#h\([^)]*\);)?(?:#src-top\(\d+\);)?)(?P<rprefix>#strong\[附注\.?\]\s+)?(?:#strong\[)?(?P<roman>I{1,3}|IV|VI{0,3}|IX|X)\.(?:\])?(?= )"
        r"|^(?P<ctop>(?:#h\([^)]*\);)?(?:#src-top\(\d+\);)?)(?P<circled>[①-⑳])(?=\S)"
        r"|\$ (?P<body>#fletcher\.diagram\((?s:.*?)\n\)"
        r"|(?:[^$\\]|\\.)*?) \$ <eq-(?P<eq>\d+(?:-\d+)*)>"
    )
    math = re.compile(r"(?<!\\)\$(?:[^$\\]|\\[\s\S])*\$")
    chapter_start = "#counter(heading).update((..c) => (c.pos().at(0, default: 0),))\n#counter(math.equation).update(0)\n"

    def set_levels(self, nums: tuple[int, ...]) -> str:
        """Set every level below the chapter, keeping the chapter's own count."""
        return f"#counter(heading).update((..c) => (c.pos().at(0, default: 0), {', '.join(map(str, nums))}))\n"

    def set_article(self, n: int) -> str:
        return f"#source-article.update({n})\n"

    def set_roman(self, n: int) -> str:
        return f"#source-roman.update({n})\n"

    def set_equation(self, n: int) -> str:
        return f"#counter(math.equation).update({n})\n"

    def section(self, title: str) -> str:
        return f"== {title}"

    def subsection(self, title: str) -> str:
        return f"=== {title}"

    def article(self, title: str, label: str) -> str:
        return f"#heading(level: 3, numbering: source-article-number)[{title}]{label}"

    def unnumbered(self, marks: str, title: str) -> str:
        return f"#heading(level: {len(marks)}, numbering: none)[{title}]"

    def paragraph(self, kind: str, label: str) -> str:
        return f'#source-paragraph[{kind}]#metadata("paragraph"){label}'

    def item(self, kind: str, label: str) -> str:
        return (f"#strong[{kind}] " if kind else "") + f'#source-item#metadata("item"){label}'

    def roman_item(self, prefix: str) -> str:
        return f"{prefix}#source-roman-item"

    def set_circled(self, n: int) -> str:
        return f"#source-circled.update({n})\n"

    def circled_item(self) -> str:
        return "#source-circled-item;"

    def equation(self, body: str, label: str, simple: bool = False) -> str:
        numbering = '"(1)"' if simple else "source-equation-number"
        return f"#math.equation(block: true, numbering: {numbering}, $ {body} $){label}"

    def label(self, name: str) -> str:
        return f" <{name}>"

    def ref(self, name: str, chapter: str | None) -> str:
        return f"@{name}[{chapter}]" if chapter else f"@{name}"

    def target(self, name: str) -> str:
        return f'#metadata("citation") <{name}>'

    def link(self, name: str, text: str) -> str:
        return f"#link(<{name}>)[{text}]"


class LatexWriter:
    events = re.compile(
        rf"(?m)^(?P<heading>#{{2,4}} .+)$"
        rf"|\*\*(?:(?P<kind>{_KINDS})\s+)?\((?P<bold>{_NUMBER})\.?\)\.?\*\*"
        rf"|^\((?P<plain>{_NUMBER})\.?\)(?= )"
        r"|^(?P<rprefix>\*\*附注\.?\*\*\s+)?(?:\*\*)?(?P<roman>I{1,3}|IV|VI{0,3}|IX|X)\.(?:\*\*)?(?= )"
        r"|^(?P<circled>[①-⑳])(?=\S)"
        r"|(?s:\$\$\n(?P<body>(?:(?!\$\$).)*?)\n\$\$) <eq-(?P<eq>\d+(?:-\d+)*)>"
    )
    math = re.compile(r"(?s:\\begin\{equation\}.*?\\end\{equation\}|\$\$.*?\$\$)|(?<!\\)\$(?:[^$\\]|\\.)*\$")
    chapter_start = "\\setcounter{sourcesection}{0}\\setcounter{equation}{0}\n\n"
    _counters = ("sourcesection", "sourcesubsection", "sourceparagraph")

    def set_levels(self, nums: tuple[int, ...]) -> str:
        return "".join(rf"\setcounter{{{c}}}{{{n}}}" for c, n in zip(self._counters, nums, strict=False))

    def set_article(self, n: int) -> str:
        return rf"\setcounter{{sourcearticle}}{{{n}}}"

    def set_roman(self, n: int) -> str:
        return rf"\setcounter{{sourceroman}}{{{n}}}"

    def set_equation(self, n: int) -> str:
        return rf"\setcounter{{equation}}{{{n}}}"

    def section(self, title: str) -> str:
        return rf"\sourcesection{{{title}}}"

    def subsection(self, title: str) -> str:
        return rf"\sourcesubsection{{{title}}}"

    def article(self, title: str, label: str) -> str:
        return rf"\sourcearticle{{{title}}}{label}"

    def unnumbered(self, marks: str, title: str) -> str:
        return f"{marks} {title}"

    def paragraph(self, kind: str, label: str) -> str:
        return rf"\sourceparagraph{{{kind + ' ' if kind else ''}}}{label}"

    def item(self, kind: str, label: str) -> str:
        return (f"**{kind}** " if kind else "") + rf"\sourceitem{label}"

    def roman_item(self, prefix: str) -> str:
        return rf"{prefix}\sourceroman"

    def set_circled(self, n: int) -> str:
        return rf"\setcounter{{sourcecircled}}{{{n}}}"

    def circled_item(self) -> str:
        return r"\sourcecircled{}"

    def equation(self, body: str, label: str, simple: bool = False) -> str:
        return f"\\begin{{equation}}\n{body}\n{label}\\end{{equation}}"

    def label(self, name: str) -> str:
        return rf"\label{{{name}}}"

    def ref(self, name: str, chapter: str | None) -> str:
        if chapter:
            return rf"({chapter}, \ref{{{name}}})"
        if name.startswith("art-"):
            return rf"\ref{{{name}}}"
        return rf"\eqref{{{name}}}" if name.startswith("eq-") else rf"(\ref{{{name}}})"

    def target(self, name: str) -> str:
        return rf"\hypertarget{{{name}}}{{}}"

    def link(self, name: str, text: str) -> str:
        return rf"\hyperlink{{{name}}}{{{text}}}"


TYPST = TypstWriter()
LATEX = LatexWriter()


@dataclass(frozen=True)
class Resync:
    chapter: int
    kind: str
    scan: str
    computed: str

    def line(self) -> str:
        return f"chapter {self.chapter}: {self.kind} {self.scan} would have been numbered {self.computed}"


def _dotted(nums: tuple[int, ...]) -> str:
    return ".".join(map(str, nums))


class _Numbering:
    """Mirror the counters while walking a chapter, and resync them at each scan number they would miss."""

    def __init__(self, chapter: int, writer: _Writer, seen: set[str] | None = None) -> None:
        self.chapter = chapter
        self.writer = writer
        self.levels: tuple[int, ...] = ()
        self.article: int | None = None
        self.roman = 0
        self.circled = 0
        self.equation = 0
        self.resyncs: list[Resync] = []
        self.seen: set[str] = seen if seen is not None else set()

    def heading(self, scan: tuple[int, ...], kind: str) -> str:
        depth = len(scan)
        parents = (*self.levels, *(0,) * depth)[: depth - 1]
        current = self.levels[depth - 1] if len(self.levels) >= depth else 0
        computed = (*parents, current + 1)
        self.levels, self.equation = scan, 0
        if computed == scan:
            return ""
        self.resyncs.append(Resync(self.chapter, kind, _dotted(scan), _dotted(computed)))
        return self.writer.set_levels((*scan[:-1], scan[-1] - 1))

    def article_heading(self, n: int) -> str:
        self.equation = 0
        if self.article is None:
            self.article = n
            return self.writer.set_article(n - 1)
        computed = self.article + 1
        self.article = n
        if n == computed:
            return ""
        self.resyncs.append(Resync(self.chapter, "article", str(n), str(computed)))
        return self.writer.set_article(n - 1)

    def article_label(self, n: int) -> str:
        name = f"art-{n}"
        if name in self.seen:
            return ""
        self.seen.add(name)
        return self.writer.label(name)

    def roman_number(self, n: int) -> str:
        if n == 1:
            update = self.writer.set_roman(0) if self.roman != 0 else ""
            self.roman = 1
            return update
        computed = self.roman + 1
        self.roman = n
        if n == computed:
            return ""
        self.resyncs.append(Resync(self.chapter, "roman", str(n), str(computed)))
        return self.writer.set_roman(n - 1)

    def circled_number(self, n: int) -> str:
        if n == 1:
            self.circled = 1
            return self.writer.set_circled(0)
        computed = self.circled + 1
        self.circled = n
        if n == computed:
            return ""
        self.resyncs.append(Resync(self.chapter, "circled", str(n), str(computed)))
        return self.writer.set_circled(n - 1)

    def unnumbered_heading(self) -> None:
        self.equation = 0

    def equation_number(self, scan: tuple[int, ...], kind: str = "equation") -> str:
        computed = (*self.levels, self.equation + 1)
        update = ""
        if computed != scan:
            self.resyncs.append(Resync(self.chapter, kind, _dotted(scan), _dotted(computed)))
            if self.levels != scan[:-1]:
                update += self.writer.set_levels(scan[:-1])
            update += self.writer.set_equation(scan[-1] - 1)
        self.levels, self.equation = scan[:-1], scan[-1]
        return update

    def simple_equation(self, n: int) -> tuple[str, str]:
        computed = self.equation + 1
        update = ""
        if n != computed:
            if n != 1:
                self.resyncs.append(Resync(self.chapter, "equation", str(n), str(computed)))
            update = self.writer.set_equation(n - 1)
        self.equation = n
        name = f"eq-art-{self.article}-{n}" if self.article is not None else f"eq-c{self.chapter}-{n}"
        if name in self.seen:
            return update, ""
        self.seen.add(name)
        return update, self.writer.label(name)

    def label(self, kind: str, scan: tuple[int, ...]) -> str:
        name = f"{kind}-c{self.chapter}-{'-'.join(map(str, scan))}"
        if name in self.seen:
            return ""
        self.seen.add(name)
        return self.writer.label(name)


def _parse(number: str) -> tuple[int, ...]:
    return tuple(int(n) for n in number.split("."))


def number_chapter(
    text: str, chapter: int, writer: _Writer = TYPST, seen: set[str] | None = None, circled: bool = False
) -> tuple[str, list[Resync]]:
    """Replace the scan's typed numbers in one chapter with counter-numbered headings, paragraphs and equations."""
    state = _Numbering(chapter, writer, seen)

    def paragraph(scan: tuple[int, ...], kind: str) -> str:
        if len(scan) > 3:
            update = state.equation_number(scan, "item")
            return update + writer.item(kind, state.label("par", scan))
        update = state.heading(scan, "paragraph")
        return update + writer.paragraph(kind, state.label("par", scan))

    def heading(marks: str, title: str) -> str:
        if m := _PARAGRAPH_HEADING_RE.match(title):
            return paragraph(_parse(m.group(1)), m.group(2))
        if m := _SUBSECTION_RE.match(title):
            return state.heading((int(m.group(1)), int(m.group(2))), "section") + writer.subsection(m.group(3))
        if m := _SECTION_RE.match(title):
            n, rest = int(m.group(1)), m.group(2)
            if len(marks) == 3 and not title.lstrip().startswith("§"):
                return state.article_heading(n) + writer.article(rest, state.article_label(n))
            return state.heading((n,), "§") + writer.section(rest)
        state.unnumbered_heading()
        return writer.unnumbered(marks, title)

    def event(m: re.Match[str]) -> str:
        if line := m.group("heading"):
            marks, title = line.split(" ", 1)
            return heading(marks, title)
        if m.group("eq"):
            scan = tuple(int(n) for n in m.group("eq").split("-"))
            if len(scan) == 1:
                update, lbl = state.simple_equation(scan[0])
                return update + writer.equation(m.group("body"), lbl, simple=True)
            update = state.equation_number(scan)
            return update + writer.equation(m.group("body"), state.label("eq", scan))
        if roman := m.groupdict().get("roman"):
            rtop = m.groupdict().get("rtop") or ""
            rprefix = m.groupdict().get("rprefix") or ""
            update = state.roman_number(_ROMAN_VALUES[roman])
            return rtop + update + writer.roman_item(rprefix)
        if mark := m.groupdict().get("circled"):
            if not circled:
                return m.group(0)
            ctop = m.groupdict().get("ctop") or ""
            return ctop + state.circled_number(ord(mark) - ord("①") + 1) + writer.circled_item()
        top = m.groupdict().get("top") or ""
        return top + paragraph(_parse(m.group("bold") or m.group("plain")), m.group("kind") or "")

    def number_figure(m: re.Match[str]) -> str:
        raw_num = m.group("fig")
        digits = re.sub(r"[.\-]", "-", raw_num)
        label = f"fig-{digits}"
        if label in state.seen:
            return m.group(0)
        state.seen.add(label)
        cap = m.group("cap").strip()
        num_tail = raw_num.split(".")[-1].split("-")[-1]
        num_int = int(re.match(r"\d+", num_tail).group(0)) if re.match(r"\d+", num_tail) else 1
        return (
            f"#counter(figure.where(kind: image)).update({max(0, num_int - 1)})\n"
            f"#figure(\n{m.group('img')}"
            f'  numbering: _ => "{raw_num}",\n'
            f"  caption: [{cap}]\n"
            f") <{label}>"
        )

    def number_figure_latex(m: re.Match[str]) -> str:
        raw_num = m.group("fig")
        digits = re.sub(r"[.\-]", "-", raw_num)
        label = f"fig-{digits}"
        if label in state.seen:
            return m.group(0)
        state.seen.add(label)
        cap = re.sub(r"(?<!\\)([%&#])", r"\\\1", m.group("cap").strip())
        num_tail = raw_num.split(".")[-1].split("-")[-1]
        num_int = int(re.match(r"\d+", num_tail).group(0)) if re.match(r"\d+", num_tail) else 1
        return (
            f"\\setcounter{{figure}}{{{max(0, num_int - 1)}}}"
            f"\\begin{{figure}}[htbp]\\centering"
            f"\\includegraphics[width=\\linewidth,height=0.75\\textheight,keepaspectratio]{{{re.sub(r'\.svg$', '.png', m.group('path'))}}}"
            f"\\renewcommand{{\\thefigure}}{{{raw_num}}}"
            f"\\captionsetup{{labelformat=simple,labelsep=space,name={{{m.group('sup')}}}}}"
            f"\\caption{{{cap}}}\\label{{{label}}}\\end{{figure}}"
        )

    numbered = writer.events.sub(event, text)
    if writer is TYPST:
        numbered = _TYPST_FIG_RE.sub(number_figure, numbered)
    else:
        numbered = _LATEX_FIG_RE.sub(number_figure_latex, numbered)
    return writer.chapter_start + numbered, state.resyncs


def labels(text: str) -> set[str]:
    return set(_LABEL_RE.findall(text))


def link_references(
    text: str, chapter: int, chapters: Mapping[str, int], known: set[str], writer: _Writer = TYPST
) -> str:
    """Turn the scan's `(1.2.9)` and `(0, 4.3.2)` into references to their labels, such as `@par-c2-1-2-9`."""
    kind = "typst" if writer is TYPST else "latex"

    def _fmt_ref(name: str, roman: str | None, next_char: str) -> str:
        ref = writer.ref(name, roman)
        follows_name = writer is TYPST and bool(re.match(r"[\w:\[-]", next_char))
        return ref + "#[]" if follows_name else ref

    def link(m: re.Match[str]) -> str:
        roman = m.group("chapter")
        if roman and roman not in chapters:
            return m.group(0)
        target = chapters[roman] if roman else chapter
        digits = m.group("number").replace(".", "-")
        name = next((n for kind in ("eq", "par") if (n := f"{kind}-c{target}-{digits}") in known), None)
        if name is None:
            return m.group(0)
        return _fmt_ref(name, roman, m.string[m.end() : m.end() + 1])

    def link_fig(m: re.Match[str]) -> str:
        if writer is TYPST and "caption:" in m.string[max(0, m.start() - 32) : m.start()]:
            return m.group(0)
        digits = re.sub(r"[.\-]", "-", m.group("fig"))
        name = f"fig-{digits}"
        if name not in known:
            return m.group(0)
        if writer is LATEX:
            prefix = m.group(0)[: m.start("fig") - m.start()]
            return rf"{prefix}\ref{{{name}}}"
        return _fmt_ref(name, None, m.string[m.end() : m.end() + 1])

    out = _sub_outside_math(_REF_RE, link, text, writer)
    out = _sub_outside_math(_FIG_REF_RE, link_fig, out, writer)
    _tbl_ref_re = re.compile(r"(?i)(?:表|附表)\s*(?P<tbl>\d+(?:[.\-]\d+)?[a-z]?)(?![\d\-])")
    def link_tbl(m: re.Match[str]) -> str:
        if writer is TYPST and "caption:" in m.string[max(0, m.start() - 32) : m.start()]:
            return m.group(0)
        digits = re.sub(r"[.\-]", "-", m.group("tbl"))
        name = f"tbl-{digits}"
        if name not in known:
            return m.group(0)
        if writer is LATEX:
            prefix = m.group(0)[: m.start("tbl") - m.start()]
            return rf"{prefix}\ref{{{name}}}"
        return _fmt_ref(name, None, m.string[m.end() : m.end() + 1])
    out = _sub_outside_math(_tbl_ref_re, link_tbl, out, writer)
    if not any(k.startswith("art-") for k in known):
        return out

    art_split = re.compile(r"(<art-(\d+)>|\\label\{art-(\d+)\})")
    parts = art_split.split(out)
    linked_parts: list[str] = []
    current_art: str | None = None
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if i + 3 < len(parts) and parts[i + 1] and (parts[i + 2] or parts[i + 3]):
            linked_parts.append(_link_article_chunk(chunk, current_art, known, writer, kind, _fmt_ref))
            linked_parts.append(parts[i + 1])
            current_art = parts[i + 2] or parts[i + 3]
            i += 4
        else:
            linked_parts.append(_link_article_chunk(chunk, current_art, known, writer, kind, _fmt_ref))
            i += 1
    return "".join(linked_parts)


def _link_article_chunk(
    text: str,
    current_art: str | None,
    known: set[str],
    writer: _Writer,
    kind: str,
    fmt_ref: Callable[[str, str | None, str], str],
) -> str:
    def link_art_eq(m: re.Match[str]) -> str:
        art, sep, eq = m.group("art"), m.group("sep"), m.group("eq")
        if f"art-{art}" not in known:
            return m.group(0)
        after = m.string[m.end() : m.end() + 1]
        eq_name = f"eq-art-{art}-{eq}"
        eq_part = fmt_ref(eq_name, None, after) if eq_name in known else f"({eq})"
        art_part = fmt_ref(f"art-{art}", None, (sep or eq_part)[:1])
        return f"{art_part}{sep}{eq_part}"

    def link_bracket(m: re.Match[str]) -> str:
        if writer is TYPST and (
            "caption:" in m.string[max(0, m.start() - 32) : m.start()]
            or "heading(" in m.string[max(0, m.start() - 64) : m.start()]
        ):
            return m.group(0)
        s = m.group(0)

        def sub_art(am: re.Match[str]) -> str:
            art = am.group("art")
            if f"art-{art}" not in known:
                return am.group(0)
            return fmt_ref(f"art-{art}", None, am.string[am.end() : am.end() + 1])

        s = _BRACKET_ART_RE.sub(sub_art, s)
        if current_art is not None:

            def sub_eq(em: re.Match[str]) -> str:
                eq = em.group("eq")
                eq_name = f"eq-art-{current_art}-{eq}"
                if eq_name not in known:
                    return em.group(0)
                return fmt_ref(eq_name, None, em.string[em.end() : em.end() + 1])

            s = _BRACKET_EQ_RE.sub(sub_eq, s)
        return s

    def link_prose_art(m: re.Match[str]) -> str:
        art = m.group("art")
        is_month = re.match(r"\s*月", m.string[m.end() :]) and not m.group("pre").startswith("第")
        if f"art-{art}" not in known or is_month:
            return m.group(0)
        return m.group("pre") + fmt_ref(f"art-{art}", None, m.string[m.end() : m.end() + 1])

    def link_prose_eq(m: re.Match[str]) -> str:
        if current_art is None:
            return m.group(0)
        eq1 = m.group("eq1")
        name1 = f"eq-art-{current_art}-{eq1}"
        mid = m.group("mid") or ""
        eq2 = m.group("eq2")
        after1 = mid[:1] if mid else m.string[m.end() : m.end() + 1]
        part1 = fmt_ref(name1, None, after1) if name1 in known else f"({eq1})"
        if not eq2:
            return m.group("pre") + part1
        name2 = f"eq-art-{current_art}-{eq2}"
        part2 = fmt_ref(name2, None, m.string[m.end() : m.end() + 1]) if name2 in known else f"({eq2})"
        return f"{m.group('pre')}{part1}{mid}{part2}"

    out = _sub_outside_math(_ART_EQ_RE, link_art_eq, text, writer)
    out = _sub_outside_math(_BRACKET_REF_RE[kind], link_bracket, out, writer)
    out = _sub_outside_math(_PROSE_ART_RE, link_prose_art, out, writer)
    return _sub_outside_math(_PROSE_EQ_RE, link_prose_eq, out, writer)


def link_citations(
    sections: list[str], abbreviations: Mapping[str, str], writer: _Writer = TYPST
) -> list[str]:
    """Make each bibliography entry `[8] Kähler…` a link target, and link the citations `[8]`, `[SGA 4]`,
    `SGA, 3` and `(T, 1.7, d)` to their entries; `abbreviations` maps the book's `T` to the entry `6`."""
    section_keys = [{m.group("key") for m in _BIB_ENTRY_RE.finditer(s)} for s in sections]
    key_counts = Counter(k for ks in section_keys for k in ks)
    keys = set(key_counts)
    if not keys:
        return sections
    first_section = {k: next(i for i, ks in enumerate(section_keys) if k in ks) for k in keys}
    keys_re = "|".join(map(re.escape, sorted(keys, key=len, reverse=True)))
    abbrs_re = "|".join(re.escape(a) for a, key in abbreviations.items() if key in keys) or "(?!)"
    citation = re.compile(
        rf"(?m)^(?P<mark>{_PAGE_MARK})(?P<entry>\\?\[(?P<key>{keys_re})\\?\] )"
        rf"|\\?\[(?P<bracket>{keys_re})(?: \d+)?\\?\]"
        r"|(?<![\w\[])(?P<sga>SGA)(?=, \d)"
        rf"|(?<!\w)\((?P<abbr>{abbrs_re})(?P<rest>, (?:I{{1,3}}|IV|V|\d)[^()$\[\]#<>\\]*)?\)"
    )

    def name_for(key: str, idx: int) -> str:
        slug = key.replace(" ", "-")
        if key_counts[key] == 1:
            return f"bib-{slug}"
        owner = idx if key in section_keys[idx] else first_section[key]
        return f"bib-s{owner}-{slug}"

    out: list[str] = []
    for idx, s in enumerate(sections):
        emitted: set[str] = set()

        def link(m: re.Match[str], section_idx: int = idx, seen_targets: set[str] = emitted) -> str:
            if m.group("entry"):
                target_name = name_for(m.group("key"), section_idx)
                if target_name in seen_targets:
                    return m.group(0)
                seen_targets.add(target_name)
                return m.group("mark") + writer.target(target_name) + m.group("entry")
            if m.group("abbr"):
                text = m.group("abbr") + (m.group("rest") or "")
                target_name = name_for(abbreviations[m.group("abbr")], section_idx)
                return "(" + writer.link(target_name, text) + ")"
            key = m.group("bracket") or m.group("sga")
            if key not in keys:
                return m.group(0)
            return writer.link(name_for(key, section_idx), m.group(0))

        out.append(_sub_outside_math(citation, link, s, writer))
    return out


def _sub_outside_math(
    pattern: re.Pattern[str], repl: Callable[[re.Match[str]], str], text: str, writer: _Writer
) -> str:
    def sub_paragraph(para: str) -> str:
        if "#table(" in para:
            return para
        out: list[str] = []
        pos = 0
        for m in writer.math.finditer(para):
            out += [pattern.sub(repl, para[pos : m.start()]), m.group(0)]
            pos = m.end()
        out.append(pattern.sub(repl, para[pos:]))
        return "".join(out)

    return "\n\n".join(map(sub_paragraph, text.split("\n\n")))
