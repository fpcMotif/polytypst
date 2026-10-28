"""Numbers and citations that a built book types as text instead of producing from counters, labels and links.

A book with `cross_references` numbers its items and equations with counters, labels each one,
links each `(1.2.9)` to its label and each `[8]` or `(T, 1.7, d)` to its bibliography entry.
Whatever is still literal in the built Typst or LaTeX source is counted here by rule:

- LITERAL_ITEM_HEAD: an item or equation number typed as text, such as `Remarque (1.6.6)`.
- UNLINKED_REFERENCE: a reference typed as text although its label exists.
- REFERENCE_WITHOUT_TARGET: a reference typed as text with no label to link to.
- UNLINKED_CITATION: a citation typed as text instead of a link to its entry.
- LITERAL_NUMBER_IN_MATH: a number such as `(4.3.3.1)` typed inside math, usually an equation's own tag.
"""

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from types import MappingProxyType

from .compiler.monograph import MonographSpec, reference_chapters
from .compiler.source_numbers import (
    _ART_EQ_RE,
    _FIG_REF_RE,
    _KINDS,
    _NUMBER,
    _PROSE_ART_RE,
    _REF_RE,
    LATEX,
    TYPST,
    labels,
)
from .compiler.typst_math import italic_differentials

_HEAD_RE = re.compile(
    rf"(?m)(?<!\w){_KINDS}\]?\s*\({_NUMBER}\.?\)|^\({_NUMBER}\.?\)(?= )|^(?:#strong\[|\*\*)?(?:I{{1,3}}|IV|VI{{0,3}}|IX|X)\.(?:\]|\*\*)?(?= )|[①-⑳ⓐ-ⓩ]"
    r"|^(?:#strong\[|\*\*|\\textbf\{)[^\W\d_][^\]}\n*]{0,23}?\s?\d+(?:\.\d+)*\.?(?:\]|\*\*|\})(?=\s)"
)
_HEADING_NUMBER = {
    "typst": re.compile(r"(?m)^={2,4}\s+(?:§\s*\d+|\d+(?:\.\d+)*\.?\s+\D)"),
    "latex": re.compile(r"(?m)^\\(?:(?:sub)*section|source(?:section|subsection|article))\{(?:\\S\s*)?\d+(?:\.\d+)*\.?\s+\D"),
}
_FIGURE_CAPTION = {
    "typst": re.compile(
        r"#figure\([\s\S]*?caption:\s*\[(?:#strong\[)?(?i:Fig(?:ure)?(?:\.|\b)|图)\s*\d+[\s\S]*?\)(?!\s*<fig-)"
    ),
    "latex": re.compile(
        r"\\caption\{(?i:Fig(?:ure)?(?:\.|\b)|图)\s*\d+[^}]*\}(?!\s*\\label\{fig-)"
    ),
}
_FIGURE_BLOCK = {
    "typst": re.compile(r"#figure\([\s\S]*?\n\)(?:\s*<fig-[\w-]+>)?|#table\([\s\S]*?\n\)"),
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
_MATH_NUMBER_RE = re.compile(r"\(\s*\d+(?:\s*\.\s*\d+){2,}\s*\)")
_CHAPTER_RE = re.compile(r"-c(\d+)-")


def literal_numbering_counts(
    source: str,
    writer: object,
    abbreviations: Iterable[str] = (),
    chapters: Mapping[str, int] = MappingProxyType({}),
    *,
    require_vector_figures: bool = False,
) -> dict[str, int]:
    """Count the literal numbers and citations in a built book's Typst (`TYPST`) or LaTeX (`LATEX`) source.
    `chapters` maps the book's chapter names in references, such as `0` in `(0, 4.1.9)`, to label numbers."""
    kind = "typst" if writer is TYPST else "latex"
    known = labels(source)
    abbrs = "|".join(map(re.escape, abbreviations)) or "(?!)"
    citation = re.compile(
        rf"{_OPEN}(?:\d+(?: bis)?|[A-Z]{{2,4}}(?: \d+)?){_CLOSE}|(?<![\w\[])SGA(?=, \d)|(?<!\w)\((?:{abbrs}), "
    )
    counts: Counter[str] = Counter()
    parts = source.split(writer.chapter_start)[1:]
    if not parts:
        fallback = _FALLBACK_SPLIT[kind].split(source)[1:]
        parts = fallback or [re.sub(r'^#set math\.equation\(numbering: [^\n]+\)\n', "", source)]
    for chapter in parts:
        ids = Counter(_CHAPTER_RE.findall(" ".join(labels(chapter))))
        own = ids.most_common(1)[0][0] if ids else None
        math = _MATH[kind]
        counts["LITERAL_NUMBER_IN_MATH"] += sum(
            len(_MATH_NUMBER_RE.findall(m.group(0))) for m in math.finditer(chapter)
        )
        counts["LITERAL_HEADING_NUMBER"] += len(_HEADING_NUMBER[kind].findall(chapter))
        counts["LITERAL_FIGURE_CAPTION"] += len(_FIGURE_CAPTION[kind].findall(chapter))
        if require_vector_figures:
            counts["RASTER_FIGURE_FALLBACK"] += len(_RASTER_FIGURE_FALLBACK[kind].findall(chapter))
        text = _FIGURE_BLOCK[kind].sub(
            " ", _ENTRIES[kind].sub(" ", _LINKS[kind].sub(" ", math.sub(" ", chapter)))
        )
        counts["ORPHANED_FIGURE_CAPTION"] += len(_ORPHANED_FIGURE_CAPTION[kind].findall(text))
        text = _ORPHANED_FIGURE_CAPTION[kind].sub(" ", text)
        counts["LITERAL_ITEM_HEAD"] += len(_HEAD_RE.findall(text))
        text = _HEAD_RE.sub(" ", text)
        counts["UNLINKED_CITATION"] += len(citation.findall(text))
        fig_labels = {k for k in known if k.startswith("fig-")}
        fig_sep = re.compile(r"[.\-]")
        counts["UNLINKED_FIGURE_REFERENCE"] += sum(
            1
            for m in _FIG_REF_RE.finditer(text)
            if not fig_labels or f"fig-{fig_sep.sub('-', m.group('fig'))}" in fig_labels
        )
        for m in _REF_RE.finditer(text):
            digits = m.group("number").replace(".", "-")
            target = chapters.get(m.group("chapter")) if m.group("chapter") else own
            linked = any(f"{k}-c{target}-{digits}" in known for k in ("eq", "par"))
            counts["UNLINKED_REFERENCE" if linked else "REFERENCE_WITHOUT_TARGET"] += 1
        for rx in (_ART_EQ_RE, _PROSE_ART_RE):
            counts["UNLINKED_REFERENCE"] += sum(
                1 for m in rx.finditer(text) if f"art-{m.group('art')}" in known
            )
    return {rule: n for rule, n in counts.items() if n}


def edition_literal_counts(rebuilt: Path, spec: MonographSpec) -> dict[str, int]:
    """The counts for the Typst and LaTeX sources beside a rebuilt PDF, as `TYPST_RULE` and `LATEX_RULE`;
    every book promises native numbering."""
    out: dict[str, int] = {}
    for suffix, writer, prefix in ((".typ", TYPST, "TYPST"), (".tex", LATEX, "LATEX")):
        path = rebuilt.with_suffix(suffix)
        if path.exists():
            source = path.read_text(encoding="utf-8")
            counts = literal_numbering_counts(
                source,
                writer,
                spec.citation_abbreviations,
                reference_chapters(spec),
                require_vector_figures=spec.require_vector_figures,
            )
            out |= {f"{prefix}_{rule}": n for rule, n in counts.items()}
            if writer is TYPST and (italic := italic_differential_count(source)):
                out["TYPST_ITALIC_DIFFERENTIAL"] = italic
    return out


def italic_differential_count(source: str) -> int:
    return sum(len(italic_differentials(m.group(0)[1:-1])) for m in TYPST.math.finditer(source))
