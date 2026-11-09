"""Chapter assembly: turn each chapter's transcripts into Typst and Markdown chapter text, then number and link them."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .diagrams import use_scan_diagrams
from .page_cleaner import Figure
from .source_numbers import (
    _ROMAN_VALUES,
    LATEX,
    FigureCounter,
    link_citations,
    link_references,
    number_chapter,
)
from .source_numbers import labels as source_labels
from .typst_math import clean_margin_and_inline_math

if TYPE_CHECKING:
    from .monograph import MonographCompiler, MonographSpec, PageParts

FigureWriter = Callable[[list[Figure], Path], str]


@dataclass(frozen=True)
class AssembledChapters:
    """The sections after chapter assembly. `latex_sections` is None when no chapter was numbered."""

    typst_sections: list[str]
    markdown_sections: list[str]
    latex_sections: list[str] | None
    resyncs: list[str]


def markdown_figures(compiler: MonographCompiler) -> FigureWriter:
    """The figure adapter for Markdown: one image line per figure whose asset exists."""

    def write(figs: list[Figure], fig_dir: Path) -> str:
        return "".join(
            f"\n\n![{cap}]({compiler.spec.figure_dir}/{asset.name})\n\n"
            for fid, cap in figs
            if (asset := compiler._resolve_figure_asset(fig_dir, fid)) is not None
        )

    return write


def assemble_chapters(
    compiler: MonographCompiler,
    md_dir: Path,
    fig_dir: Path,
    out_dir: Path,
    typst_sections: list[str],
    markdown_sections: list[str],
) -> AssembledChapters:
    """Append every chapter of `compiler.spec` after the given front-matter sections, then number and link them."""
    spec = compiler.spec
    words = compiler.composition.language.numbering
    has_explicit_labels = any(c.label for c in spec.chapters)
    typst_sections = list(typst_sections)
    md_sections = list(markdown_sections)
    numbered_chapters: list[tuple[int, int]] = []
    latex_chapters: dict[int, tuple[str, int]] = {}
    resyncs: list[str] = []
    seen_typst: set[str] = set()
    seen_latex: set[str] = set()
    for chap in spec.chapters:
        if chap.typst_file:
            prebuilt = compiler._prebuilt_chapter(out_dir, chap)
            if prebuilt is not None:
                typst_sections += [prebuilt, "\n#pagebreak(weak: true)\n"]
            continue
        compiler._figures = FigureCounter(chap.number)
        pages_data: list[PageParts] = []
        clean_title = _bare_title(chap.title) if spec.theorem_layout else chap.title
        md_heading = (
            f"\n# {clean_title}\n"
            if spec.cross_references or is_unnumbered_chapter(chap.title, spec.unnumbered_titles)
            else f"\n# Chapter {chap.number}: {chap.title}\n"
        )
        for pno in range(chap.start_page, chap.end_page + 1):
            raw_text = compiler._read_page(md_dir, pno)
            if (
                raw_text is None
                or len(re.sub(r"<!--.*?-->", "", raw_text, flags=re.DOTALL).strip()) < spec.min_page_chars
                or any(marker in raw_text for marker in spec.skip_page_markers)
            ):
                continue
            p_body, top_f, bot_f = compiler.cleaner.clean(raw_text, pno)
            if is_contents_page(raw_text):
                p_body = mark_contents_lines(p_body, keep_title=not is_contents_title(chap.title))
            if spec.theorem_layout and pno == chap.start_page:
                m_dup = re.match(r"^\s*#+\s*([^\n]+)\n*", p_body)
                if m_dup and _bare_title(m_dup.group(1)).strip().lower() == clean_title.strip().lower():
                    p_body = p_body[m_dup.end() :]
            if spec.commutative_diagrams:
                p_body = use_scan_diagrams(p_body, pno, fig_dir)
            pages_data.append((pno, p_body, top_f, bot_f))

        opens = spec.chapter_openings and chap.number > 0
        md_body = compiler.stitch_chapter(pages_data, fig_dir, markdown_figures(compiler))
        md_sections.append(unmark_markdown(f"{md_heading}\n\n" + (mark_chapter_opening(md_body) if opens else md_body).strip()))
        title = clean_margin_and_inline_math(chap.title)
        label = chap.label if chap.label is not None else spec.chapter_label.format(number=chap.number)
        if (
            spec.cross_references
            and chap.number > 0
            and not is_unnumbered_chapter(title, spec.unnumbered_titles)
            and (label == str(chap.number) or (not label and spec.chapter_openings))
        ):
            heading = (
                f"#counter(heading).update(({chap.number - 1},))\n"
                f'#heading(level: 1, numbering: "1")[{title}] <sec-{chap.number}>'
            )
        elif label:
            heading = typst_chapter_heading(title, label, None)
        elif spec.chapter_label or is_unnumbered_chapter(title, spec.unnumbered_titles):
            heading = f"= {title}"
        else:
            heading = "= " + spec.chapter_heading.format(number=chap.number, title=title)
        stitched = compiler.stitch_chapter(pages_data, fig_dir)
        formatted = compiler.format_typst(mark_chapter_opening(stitched) if opens else stitched)
        if spec.theorem_layout:
            formatted = f"\n{heading}\n\n" + formatted
        should_number = spec.cross_references and (
            bool(chap.label)
            if has_explicit_labels
            else ("索引" not in title and "Index" not in title and "校订后记" not in title)
        )
        if should_number:
            formatted, chapter_resyncs = number_chapter(
                formatted,
                chap.number,
                seen=seen_typst,
                circled=spec.circled_items,
                words=words,
                theorem_layout=spec.theorem_layout,
            )
            resyncs += [r.line() for r in chapter_resyncs]
            numbered_chapters.append((len(typst_sections), chap.number))
            latex_chapters[len(md_sections) - 1] = (
                number_chapter(
                    md_sections[-1],
                    chap.number,
                    LATEX,
                    seen=seen_latex,
                    circled=spec.circled_items,
                    words=words,
                    theorem_layout=spec.theorem_layout,
                )[0],
                chap.number,
            )
        if "索引" in title or "Index" in title:
            formatted = re.sub(r"#src-page\((\d+)\)", r"#src-top(\1);", formatted)
            formatted = (
                "#columns(2, gutter: 1.8em)[\n"
                "  #set text(size: 8.8pt)\n"
                "  #set par(first-line-indent: 0pt, hanging-indent: 1.2em, leading: 0.46em, spacing: 0.40em, justify: false)\n"
                f"  {formatted}\n"
                "]"
            )
        typst_sections.append(formatted if spec.theorem_layout else f"\n{heading}\n\n" + formatted)
        typst_sections.append("\n#pagebreak(weak: true)\n")

    known = set().union(*(source_labels(typst_sections[i]) for i, _ in numbered_chapters))
    figure_labels = set().union(*(source_labels(section) for section in typst_sections))
    typst_sections = [
        re.sub(
            r"@(fig-[\w-]+)",
            lambda m: m.group(0) if m.group(1) in figure_labels else "Fig. " + m.group(1)[4:].replace("-", "."),
            section,
        )
        for section in typst_sections
    ]
    roman = reference_chapters(spec)
    for i, number in numbered_chapters:
        typst_sections[i] = link_references(
            typst_sections[i], number, roman, known, words=words, theorem_layout=spec.theorem_layout
        )
    latex_known = set().union(*(source_labels(text) for text, _ in latex_chapters.values()))
    latex_sections = [
        link_references(
            latex_chapters[i][0], latex_chapters[i][1], roman, latex_known, LATEX, words, spec.theorem_layout
        )
        if i in latex_chapters
        else section
        for i, section in enumerate(md_sections)
    ]
    if spec.cross_references:
        typst_sections = link_citations(typst_sections, spec.citation_abbreviations)
        latex_sections = link_citations(latex_sections, spec.citation_abbreviations, LATEX)
    return AssembledChapters(typst_sections, md_sections, latex_sections if latex_chapters else None, resyncs)


def reference_chapters(spec: MonographSpec) -> dict[str, int]:
    return {c.label.split()[-1]: c.number for c in spec.chapters if c.label}


def _bare_title(title: str) -> str:
    return re.sub(r"^\d+\.?\s*", "", clean_margin_and_inline_math(title))


OPENING_NOTE = r"(?:\^\[.*\]|@@FNSTART@@.*@@FNEND@@)"
CHAPTER_BYLINE_RE = re.compile(
    rf"^(?:#+\s*)?[：:]?\s*(?P<names>[一-鿿]{{2,6}}(?:\s+[一-鿿]{{2,6}}){{0,3}})(?P<note>{OPENING_NOTE})?$",
    re.DOTALL,
)
ABSTRACT_LABEL_RE = re.compile(rf"^#+\s*导\s*语\s*(?P<note>{OPENING_NOTE})?$", re.DOTALL)
OPENING_SECTION_RE = re.compile(r"^#{2,4}\s+(?!导\s*语|——)(?P<title>\S.*)$", re.MULTILINE)
FIRST_SECTION_RE = re.compile(r"1[\s⁠]|(?:前言|引言|序言|提出问题|问题的提出)$")


def mark_chapter_opening(s: str) -> str:
    """Mark the subtitle, byline and abstract that come before a chapter's first section."""
    headings = list(OPENING_SECTION_RE.finditer(s))[:2]
    first_section = headings[1] if len(headings) > 1 and CHAPTER_BYLINE_RE.match(headings[0][0]) else next(iter(headings), None)
    if first_section is None:
        return s
    abstract_ends = bool(FIRST_SECTION_RE.match(first_section["title"]))
    blocks = [b.strip() for b in s[: first_section.start()].split("\n\n") if b.strip()]
    lead: list[str] = []
    byline = None
    label_note = ""
    abstract: list[str] = []
    for block in blocks:
        if byline is None:
            if (subtitle := re.sub(r"^#+\s*", "", block)).startswith("——"):
                lead.append(f"@@SUBTITLE@@ {subtitle}")
            elif len(lead) < 2 and (m := CHAPTER_BYLINE_RE.match(block)):
                byline = f"@@BYLINE@@ {m['names']}{m['note'] or ''}"
            else:
                lead.append(block)
        elif not abstract_ends:
            abstract.append(block)
        elif m := ABSTRACT_LABEL_RE.match(block):
            label_note = m["note"] or ""
        elif not abstract and not label_note and re.fullmatch(OPENING_NOTE, block, re.DOTALL):
            label_note = block
        else:
            abstract.append(block)
    if byline is None:
        return s
    parts = [*lead, byline]
    if abstract_ends and abstract:
        parts += [f"@@ABSTRACT@@{label_note}", *abstract, "@@ENDABSTRACT@@"]
    else:
        parts += abstract
    return "\n\n".join(parts) + "\n\n" + s[first_section.start() :]


UNNUMBERED_CHAPTER_PREFIXES = (
    "作者简介",
    "编译委员会",
    "中文版前言",
    "中文版序言",
    "序",
    "后记",
    "前言",
    "序言",
    "导读",
    "目录",
    "人名索引",
    "专业名词索引",
    "译后记",
    "校订后记",
    "绪论",
    "附录",
    "参考文献",
    "Index",
    "Preface",
    "Author's Preface",
    "Translator's Preface",
    "Appendix",
    "Bibliography",
    "References",
    "Solutions",
    "Historical Note",
    "Contents",
    "Table of Contents",
)


def typst_chapter_heading(title: str, label: str, sec_label: str | None) -> str:
    word, _, number = label.rpartition(" ")
    tag = f" <{sec_label}>" if sec_label else ""
    if number.isdigit() and int(number) > 0:
        value, style = int(number), "1"
    elif number in _ROMAN_VALUES:
        value, style = _ROMAN_VALUES[number], "I"
    elif re.fullmatch(r"[A-Z]", number):
        value, style = ord(number) - ord("A") + 1, "A"
    else:
        return f'#chapter-label.update("{label}")\n#heading(level: 1, numbering: none)[{title}]{tag}\n#chapter-label.update(none)'
    shown = f"{word} " if word else ""
    return (
        f"#counter(heading).update(({value - 1},))\n"
        f'#chapter-label.update([{shown}#context counter(heading).display("{style}")])\n'
        f'#heading(level: 1, numbering: "{style}")[{title}]{tag}\n'
        "#chapter-label.update(none)"
    )


def is_unnumbered_chapter(title: str, book_titles: tuple[str, ...] = ()) -> bool:
    """True for front and back matter: the shared titles, and the book's own `unnumbered_titles`."""
    return title.startswith((*UNNUMBERED_CHAPTER_PREFIXES, *book_titles))


CONTENTS_TITLE_RE = re.compile(r"^\s*#+\s*(?:table\s+of\s+)?contents\s*$", re.IGNORECASE | re.MULTILINE)
CONTENTS_ENTRY_RE = re.compile(r"^(?P<title>[^#$|>\s].*?)(?:\s*(?:\.\s*){2,}|\s+)(?P<page>\d{1,3})\s*$")


def is_contents_title(title: str) -> bool:
    return bool(CONTENTS_TITLE_RE.fullmatch(f"# {title}"))


def is_contents_page(raw: str) -> bool:
    return bool(CONTENTS_TITLE_RE.search(raw[:200]))


def mark_contents_lines(body: str, keep_title: bool) -> str:
    out: list[str] = []
    pending: list[str] = []
    for line in body.split("\n"):
        if CONTENTS_TITLE_RE.fullmatch(line):
            out += pending
            pending = []
            if keep_title:
                out.append(line)
        elif (m := re.match(r"^#+\s*(.+)$", line)) and (
            not CONTENTS_ENTRY_RE.match(m[1]) or re.fullmatch(r"(?i)(?:chapter|part)\s+\d+", m[1].strip())
        ):
            out += [*pending, f"@@CONTENTSHEAD@@{m[1]}"]
            pending = []
        elif m := CONTENTS_ENTRY_RE.match(re.sub(r"^#+\s*", "", line)):
            out.append(f"@@CONTENTS@@{' '.join([*pending, m['title']])}@@PAGE@@{m['page']}")
            pending = []
        elif line.strip() and not line.lstrip().startswith(("$", "|", "<", "!")):
            pending.append(line.strip())
        else:
            out += [*pending, line]
            pending = []
    return "\n\n".join(line for line in [*out, *pending] if line.strip())


def unmark_markdown(body: str) -> str:
    """Turn the Typst-only markers into plain Markdown: drop landscape and page-break markers, keep the opening's text."""
    body = re.sub(r"[ \t]*\n*@@PAGEBREAK@@\n*[ \t]*", "\n\n", body)
    body = re.sub(r"@@CONTENTS@@(.*?)@@PAGE@@(\d+)", r"\1 \2", body)
    body = re.sub(r"@@CONTENTSHEAD@@", "", body)
    body = re.sub(r"\n*@@FLIPPED\d+@@\n*", "\n\n", body)
    body = re.sub(r"(?m)^@@SUBTITLE@@ (.+)$", r"*\1*", body)
    body = re.sub(r"(?m)^@@BYLINE@@ ", "", body)
    body = re.sub(r"(?m)^@@ABSTRACT@@", "", body)
    return re.sub(r"\n*@@ENDABSTRACT@@\n*", "\n\n", body)
