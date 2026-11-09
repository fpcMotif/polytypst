"""Numbers and citations that a built book types as text instead of producing from counters, labels and links.

A book with `cross_references` numbers its items and equations with counters, labels each one,
links each `(1.2.9)` to its label and each `[8]` or `(T, 1.7, d)` to its bibliography entry.
Whatever is still literal in the built Typst or LaTeX source is counted here by rule:

- LITERAL_ITEM_HEAD: an item or equation number typed as text, such as `Remarque (1.6.6)`.
- UNLINKED_REFERENCE: a reference typed as text although its label exists.
- REFERENCE_WITHOUT_TARGET: a reference typed as text with no label to link to.
- UNLINKED_CITATION: a citation typed as text instead of a link to its entry.
- LITERAL_NUMBER_IN_MATH: a number such as `(4.3.3.1)` typed inside math, usually an equation's own tag.
- HARDCODED_NUMBERING: a heading or figure that prints a fixed string as its number, such as `numbering: _ => "6"`.
"""

import re
from bisect import bisect_right
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from .compiler.chapter_assembly import reference_chapters
from .compiler.monograph import MonographSpec, build_source
from .compiler.presets import ENGLISH_WORDS, NumberingWords
from .compiler.source_numbers import (
    _ART_EQ_RE,
    _FIG_REF_RE,
    _NUMBER,
    _PROSE_ART_RE,
    _REF_RE,
    LATEX,
    TYPST,
    LatexWriter,
    TypstWriter,
    _sec_target,
    chapter_reference_re,
    kinds,
    labels,
    reference_re,
)
from .compiler.typst_math import italic_differentials


def _head_re(words: NumberingWords) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)(?<!\w){kinds(words.item_kinds)}\]?\s*\({_NUMBER}\.?\)|^\({_NUMBER}\.?\)(?= )|^(?:#strong\[|\*\*)?(?:I{{1,3}}|IV|VI{{0,3}}|IX|X)\.(?:\]|\*\*)?(?= )|[①-⑳ⓐ-ⓩ]"
        r"|^(?:#strong\[|\*\*|\\textbf\{)[^\W\d_][^\]}\n*]{0,23}?\s?\d+(?:\.\d+)*\.?(?:\]|\*\*|\})(?=\s)"
    )


_HEADING_NUMBER = {
    "typst": re.compile(r"(?m)^={2,4}\s+(?:§\s*\d+|\d+(?:\.\d+)*\.?\s+\D)"),
    "latex": re.compile(r"(?m)^\\(?:(?:sub)*section|source(?:section|subsection|article))\{(?:\\S\s*)?\d+(?:\.\d+)*\.?\s+\D"),
}


def _chapter_heading(kind: str, words: NumberingWords) -> re.Pattern[str]:
    number = rf"(?:{words.chapter_word}\s+)?\d+[:.]?\s+\D"
    if kind == "typst":
        return re.compile(rf"(?m)^=\s+{number}")
    return re.compile(rf"(?m)^\\chapter\{{{number}|^#\s+{number}")

_FIGURE_CAPTION = {
    "typst": re.compile(
        r"#figure\([\s\S]*?caption:\s*\[(?:#strong\[)?(?i:Fig(?:ure)?(?:\.|\b)|图)\s*\d+[\s\S]*?\)(?!\s*<fig-)"
    ),
    "latex": re.compile(
        r"\\caption\{(?i:Fig(?:ure)?(?:\.|\b)|图)\s*\d+[^}]*\}(?!\s*\\label\{fig-)"
    ),
}
_FIGURE_BLOCK = {
    "typst": re.compile(
        r"#figure\([\s\S]*?\n\)(?:\s*<fig-[\w-]+>)?|#table\([\s\S]*?\n\)|#align\(center\)\[[\s\S]*?let cells = arguments\([\s\S]*?\n\]"
    ),
    "latex": re.compile(
        r"\\caption\{[^}]*\}(?:\s*\\label\{[^}]*\})?"
        r"|\\begin\{(longtable|tabularx?)\}[\s\S]*?\\end\{\1\}"
    ),
}
_ORPHANED_FIGURE_CAPTION = {
    "typst": re.compile(
        r"(?m)#align\(center\)\[\s*#emph\[(?i:Fig(?:ure)?(?:\.|\b)|Abb\.|图)\s*\d+[^\]]*\]\s*\]"
        r"|^[ \t]*(?:#strong\[|#emph\[)?(?i:Fig(?:ure)?(?:\.|\b)|Abb\.|图)\s*\d+(?:[.\-]\d+)?[a-z]?\.?(?:\])?[ \t]*$"
    ),
    "latex": re.compile(
        r"(?m)\\begin\{center\}\s*\\emph\{(?i:Fig(?:ure)?(?:\.|\b)|Abb\.|图)\s*\d+[^}]*\}\s*\\end\{center\}"
        r"|^[ \t]*(?:\\textbf\{|\\emph\{)?(?i:Fig(?:ure)?(?:\.|\b)|Abb\.|图)\s*\d+(?:[.\-]\d+)?[a-z]?\.?(?:\})?[ \t]*$"
    ),
}
_RASTER_FIGURE_FALLBACK = {
    "typst": re.compile(r'image\("[^"\n]*?\.png"'),
    "latex": re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{[^}\n]*?\.png\}|\\scandiagram\{[^}\n]+\}"),
}
_FALLBACK_SPLIT = {
    "typst": re.compile(r"(?m)^(?==\s+|#chapter-label\.update\()"),
    "latex": re.compile(r"(?m)^(?=\\chapter\b)"),
}
_LINKS = {
    "typst": re.compile(r"#link\(<[^>]+>\)\[(?:\\.|[^\]\\])*\]|@[\w-]+(?:\[[^\]]*\])?"),
    "latex": re.compile(r"\\hyperlink\{[^}]*\}\{[^}]*\}|\\(?:eq)?ref\{[^}]*\}"),
}
_OPEN, _CLOSE = r"(?<!#strong)(?<!#emph)(?:\{\[\}|\\?\[)", r"(?:\{\]\}|\\?\])"
_ENTRIES = {
    "typst": re.compile(
        rf'#metadata\("citation"\) <bib-[^>]+>{_OPEN}[^\]\n{{}}]*?{_CLOSE}'
    ),
    "latex": re.compile(
        rf"\\hypertarget\{{bib-[^}}]*\}}\{{\}}\s*{_OPEN}[^\]\n{{}}]*?{_CLOSE}"
    ),
}
_MATH = {
    "typst": TYPST.math,
    "latex": re.compile(
        r"(?s)\\\[.*?\\\]|\\\(.*?\\\)|\\begin\{(equation|aligned|array|cases)\*?\}.*?\\end\{\1\*?\}"
        r"|\$\$.*?\$\$|(?<!\\)\$(?:[^$\\]|\\.)*\$"
    ),
}
_HARDCODED_NUMBERING = {
    "typst": re.compile(r'numbering:\s*_\s*=>\s*"'),
    "latex": re.compile(r"\\renewcommand\{?\\the(?:chapter|section|figure|table|equation)\}?\{[^{}]*\d[^{}]*\}"),
}
_MATH_NUMBER_RE = re.compile(r"\(\s*\d+(?:\s*\.\s*\d+){2,}\s*\)")
_CHAPTER_RE = re.compile(r"-c(\d+)-")


@dataclass(frozen=True)
class LiteralHit:
    rule: str
    line: int
    text: str


def _blank(rx: re.Pattern[str], text: str) -> str:
    return rx.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def _chapters(source: str, writer: TypstWriter | LatexWriter, kind: str) -> list[tuple[int, str]]:
    marker = writer.chapter_start
    if marker in source:
        starts = [m.end() for m in re.finditer(re.escape(marker), source)]
        ends = [m.start() for m in re.finditer(re.escape(marker), source)][1:] + [len(source)]
        return [(s, source[s:e]) for s, e in zip(starts, ends)]
    starts = [m.start() for m in _FALLBACK_SPLIT[kind].finditer(source)]
    if starts:
        return [(s, source[s:e]) for s, e in zip(starts, starts[1:] + [len(source)])]
    preamble = re.match(r"#set math\.equation\(numbering: [^\n]+\)\n", source)
    skip = preamble.end() if preamble else 0
    return [(skip, source[skip:])]


def literal_numbering_hits(
    source: str,
    writer: TypstWriter | LatexWriter,
    abbreviations: Iterable[str] = (),
    chapters: Mapping[str, int] = MappingProxyType({}),
    *,
    require_vector_figures: bool = False,
    words: NumberingWords = ENGLISH_WORDS,
    theorem_layout: bool = False,
) -> list[LiteralHit]:
    kind = "typst" if writer is TYPST else "latex"
    known = labels(source)
    abbrs = "|".join(map(re.escape, abbreviations)) or "(?!)"
    citation = re.compile(
        rf"{_OPEN}(?:\d+(?: bis)?|[A-Z]{{2,4}}(?: \d+)?){_CLOSE}|(?<![\w\[])SGA(?=, \d)|(?<!\w)\((?:{abbrs}), "
    )
    newlines = [m.start() for m in re.finditer("\n", source)]
    hits: list[LiteralHit] = []

    def add(rule: str, at: int, matches: Iterable[re.Match[str]]) -> None:
        for m in matches:
            line = bisect_right(newlines, at + m.start()) + 1
            hits.append(LiteralHit(rule, line, " ".join(m.group(0).split())[:80]))

    add("HARDCODED_NUMBERING", 0, _HARDCODED_NUMBERING[kind].finditer(source))
    for at, chapter in _chapters(source, writer, kind):
        ids = Counter(_CHAPTER_RE.findall(" ".join(labels(chapter))))
        own = ids.most_common(1)[0][0] if ids else None
        math = _MATH[kind]
        for m in math.finditer(chapter):
            add("LITERAL_NUMBER_IN_MATH", at + m.start(), _MATH_NUMBER_RE.finditer(m.group(0)))
        if theorem_layout and writer.chapter_start in source:
            add("LITERAL_HEADING_NUMBER", at, _chapter_heading(kind, words).finditer(chapter[:1000]))
        add("LITERAL_HEADING_NUMBER", at, _HEADING_NUMBER[kind].finditer(chapter))
        add("LITERAL_FIGURE_CAPTION", at, _FIGURE_CAPTION[kind].finditer(chapter))
        if require_vector_figures:
            add("RASTER_FIGURE_FALLBACK", at, _RASTER_FIGURE_FALLBACK[kind].finditer(chapter))
        text = chapter
        for rx in (math, _LINKS[kind], _ENTRIES[kind], _FIGURE_BLOCK[kind]):
            text = _blank(rx, text)
        add("ORPHANED_FIGURE_CAPTION", at, _ORPHANED_FIGURE_CAPTION[kind].finditer(text))
        text = _blank(_ORPHANED_FIGURE_CAPTION[kind], text)
        head = _head_re(words)
        add("LITERAL_ITEM_HEAD", at, head.finditer(text))
        text = _blank(head, text)
        add("UNLINKED_CITATION", at, citation.finditer(text))
        fig_labels = {k for k in known if k.startswith("fig-")}
        fig_sep = re.compile(r"[.\-]")
        add("UNLINKED_FIGURE_REFERENCE", at, (
            m for m in _FIG_REF_RE.finditer(text)
            if not fig_labels or f"fig-{fig_sep.sub('-', m.group('fig'))}" in fig_labels
        ))
        for m in _REF_RE.finditer(text):
            digits = m.group("number").replace(".", "-")
            target = chapters.get(m.group("chapter")) if m.group("chapter") else own
            linked = any(f"{k}-c{target}-{digits}" in known for k in ("eq", "par"))
            add("UNLINKED_REFERENCE" if linked else "REFERENCE_WITHOUT_TARGET", at, [m])
        for rx in (_ART_EQ_RE, _PROSE_ART_RE):
            add("UNLINKED_REFERENCE", at, (m for m in rx.finditer(text) if f"art-{m.group('art')}" in known))
        for rx in (reference_re(words), chapter_reference_re(words)):
            add("UNLINKED_REFERENCE", at, (m for m in rx.finditer(text) if _sec_target(m.group("number")) in known))
    return sorted(hits, key=lambda h: h.line)


def literal_numbering_counts(
    source: str,
    writer: TypstWriter | LatexWriter,
    abbreviations: Iterable[str] = (),
    chapters: Mapping[str, int] = MappingProxyType({}),
    *,
    require_vector_figures: bool = False,
    words: NumberingWords = ENGLISH_WORDS,
    theorem_layout: bool = False,
) -> dict[str, int]:
    """Count the literal numbers and citations in a built book's Typst (`TYPST`) or LaTeX (`LATEX`) source.
    `chapters` maps the book's chapter names in references, such as `0` in `(0, 4.1.9)`, to label numbers."""
    hits = literal_numbering_hits(
        source, writer, abbreviations, chapters,
        require_vector_figures=require_vector_figures, words=words, theorem_layout=theorem_layout,
    )
    return dict(Counter(h.rule for h in hits))


def edition_literal_hits(rebuilt: Path, spec: MonographSpec) -> dict[str, list[tuple[Path, LiteralHit]]]:
    out: dict[str, list[tuple[Path, LiteralHit]]] = {}
    for ext, writer, prefix in (("typ", TYPST, "TYPST"), ("tex", LATEX, "LATEX")):
        path = build_source(rebuilt, ext)
        if path.exists():
            source = path.read_text(encoding="utf-8")
            hits = literal_numbering_hits(
                source,
                writer,
                spec.citation_abbreviations,
                reference_chapters(spec),
                require_vector_figures=spec.require_vector_figures,
                words=spec.composition().language.numbering,
                theorem_layout=spec.theorem_layout,
            )
            for hit in hits:
                out.setdefault(f"{prefix}_{hit.rule}", []).append((path, hit))
            if writer is TYPST:
                for m in TYPST.math.finditer(source):
                    for word in italic_differentials(m.group(0)[1:-1]):
                        line = source.count("\n", 0, m.start() + 1 + word.start()) + 1
                        hit = LiteralHit("ITALIC_DIFFERENTIAL", line, word.group(0))
                        out.setdefault("TYPST_ITALIC_DIFFERENTIAL", []).append((path, hit))
    return out


def edition_literal_counts(rebuilt: Path, spec: MonographSpec) -> dict[str, int]:
    """The counts for the Typst and LaTeX sources beside a rebuilt PDF, as `TYPST_RULE` and `LATEX_RULE`;
    every book promises native numbering."""
    return {rule: len(hits) for rule, hits in edition_literal_hits(rebuilt, spec).items()}


def italic_differential_count(source: str) -> int:
    return sum(len(italic_differentials(m.group(0)[1:-1])) for m in TYPST.math.finditer(source))
