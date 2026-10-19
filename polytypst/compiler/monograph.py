"""Universal Academic Monograph Compiler for TeX-compatible Markdown, XeLaTeX, Typst, and PDF.

A book supplies a declarative `MonographSpec`. `MonographCompiler` owns page
cleaning, cross-page stitching, figure placement, LaTeX-to-Typst math, the
Typst preamble, and the Pandoc and Typst subprocess runs.
"""

import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

import pymupdf
from PIL import Image

from .presets import CompositionConfig, resolve_composition
from .typst_math import clean_margin_and_inline_math, convert_math_batch

REPO_FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"

Figure = tuple[str, str]
PageParts = tuple[int, str, list[Figure], list[Figure]]
Rewrite = tuple[str, str]


@dataclass(frozen=True)
class ChapterSpec:
    number: int
    title: str
    start_page: int
    end_page: int
    typst_file: str = ""
    label: str | None = None


@dataclass(frozen=True)
class FigureLayout:
    caption_pattern: str = (
        r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.?\s*(?P<chapter>\d+)[\.\-]"
        r"(?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*$"
    )
    caption_ignore_case: bool = True
    caption_format: str = "Fig. {chapter}.{number}"
    top_zone_lines: int = 2
    top_pages: frozenset[int] = frozenset()
    svg_single_pct: int | None = None
    svg_paired_pct: int = 90
    png_single_divisor: int = 1350
    png_single_range: tuple[int, int] = (26, 78)
    png_max_height_ratio: float = 0.38
    png_min_pct_tall: int = 24
    png_paired_divisor: int = 650
    png_paired_range: tuple[int, int] = (50, 88)
    supplement_none: bool = True


@dataclass(frozen=True)
class MonographSpec:
    slug: str
    title: str
    author: str
    subtitle: str = ""
    translator: str = ""
    editor: str = ""
    publisher: str = "Cambridge University Press"
    series: str = "Cambridge Studies in Advanced Mathematics"
    year: int = 2007
    publisher_key: str = "cambridge"
    lang: str = "en"
    domain: str = "math"
    preface_page: int | None = None
    chapters: list[ChapterSpec] = field(default_factory=list)
    sections: dict[str, tuple[int, str]] = field(default_factory=dict)
    problems_pages: tuple[int, int] | None = None
    references_page: int | None = None
    index_pages: tuple[int, int] | None = None
    index_title: str = "Index"
    index_subentries: bool = False
    markdown_dir: str = "markdown_pages"
    figure_dir: str = "figures"
    figures: FigureLayout = field(default_factory=FigureLayout)
    extra_figures: dict[int, tuple[Figure, ...]] = field(default_factory=dict)
    min_page_chars: int = 20
    skip_page_markers: tuple[str, ...] = ("1.1.1.1.1", "musical compositions")
    folio_pattern: str = r"^(?:\d{1,3}|[ivxlcdm]+)$"
    running_header_regexes: tuple[str, ...] = ()
    header_zone_lines: int | None = 2
    drop_line_regexes: tuple[str, ...] = ()
    normalize_headings: bool = True
    theorem_heads_upper: bool = False
    footnote_marker: str = ""
    equation_numbering: Literal["section", "page"] = "section"
    page_fixups: dict[int, tuple[Rewrite, ...]] = field(default_factory=dict)
    heading_rewrites: tuple[Rewrite, ...] = ()
    heading_hook: Callable[[str, int], str | None] | None = None
    paginate_like_source: bool = False
    source_line_breaks: Callable[[int, str, Path], str] | None = None
    justify_page_end: Callable[[str], bool] | None = None
    pre_math_rewrites: tuple[Rewrite, ...] = ()
    stray_dollar_symbol: str = ""
    nonbreaking_hyphens: bool = False
    chapter_heading: str = "{number} {title}"
    chapter_label: str = ""
    prebuilt_fixups: tuple[tuple[str, str], ...] = ()
    typst_preamble: str = ""
    typst_front_matter: str = ""
    book_aliases: bool = True
    pdf_name_markers: tuple[str, ...] = ()
    pdf_page_count: int | None = None
    source_pdf: str = ""
    ocr_prompt: str | None = None


@dataclass(frozen=True)
class MonographOutputs:
    markdown_path: Path
    latex_path: Path
    typst_path: Path
    pdf_path: Path
    total_pages: int


@dataclass(frozen=True)
class RenderedMonograph:
    markdown: str
    typst: str


def running_header_regexes(pattern: str) -> tuple[str, ...]:
    """Line regexes for running headers named by an alternation of titles."""
    prefix = r"(?:[0-9A-Z]{1,2}\.(?:\d{1,2}\.?)?\s+)?"
    return (
        rf"^(?:#+\s*)?{prefix}(?:{pattern})(?:\s+\d{{1,3}})?$",
        rf"^\d{{1,3}}\s+{prefix}(?:{pattern})$",
    )


def resolve_monograph_spec(
    pdf_path: Path,
    total_pages: int,
    publisher_key: str = "cambridge",
    lang: str = "en",
    domain: str = "math",
) -> MonographSpec:
    """Return a known book's spec, or a one-chapter spec for an unknown PDF."""
    from ..books import find_known_book

    comp = resolve_composition(publisher=publisher_key, lang=lang, domain=domain)
    known = find_known_book(pdf_path, total_pages)
    if known is not None:
        if (
            comp.publisher.key == known.publisher_key
            and comp.language.code == known.lang
            and comp.domain.key == known.domain
        ):
            return known
        return replace(
            known,
            publisher=comp.publisher.imprint_name,
            series=comp.publisher.default_series,
            publisher_key=comp.publisher.key,
            lang=comp.language.code,
            domain=comp.domain.key,
        )
    slug = re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_") or "book"
    return MonographSpec(
        slug=slug,
        title=pdf_path.stem,
        author="Author",
        publisher=comp.publisher.imprint_name,
        series=comp.publisher.default_series,
        publisher_key=comp.publisher.key,
        lang=comp.language.code,
        domain=comp.domain.key,
        chapters=[ChapterSpec(1, pdf_path.stem, 1, total_pages)],
    )


EQ_LABEL_END_RE = re.compile(r"<eq-[0-9a-zA-Z'-]+>$")
HYPHEN_JOIN_WORDS = frozenset(
    (
        "z",
        "w",
        "x",
        "y",
        "k",
        "n",
        "m",
        "p",
        "q",
        "one",
        "two",
        "non",
        "self",
        "well",
        "half",
        "single",
        "many",
    )
)
BLOCK_STARTS = (
    "#",
    "=",
    "$$",
    "\\[",
    "**",
    "*Proof",
    "Proof",
    "1.",
    "2.",
    "3.",
    "4.",
    "5.",
    "(i)",
    "(ii)",
    "(a)",
    "(b)",
)
PROSE_IN_MATH_RE = re.compile(
    r"differential|equations|functions|polynomial|converges|identically|"
    r"derivative|continuous|condition|sufficient|necessary|arbitrary|"
    r"original|equation|type|ordinary|point|removable|singularity|coefficients|"
    r"holomorphic|meromorphic|neighborhood|connected|compact",
    re.IGNORECASE,
)


def ends_complete_paragraph(text: str) -> bool:
    t = text.rstrip()
    if not t:
        return True
    last_line = t.splitlines()[-1].strip()
    if (
        last_line.startswith(("#", "=", "$$", "\\["))
        or last_line.endswith("$$")
        or EQ_LABEL_END_RE.search(last_line)
    ):
        return True
    return t.endswith(
        (".", "?", "!", ":", '."', ".'", ".)", ".*", ".*)", "]", "@@FNEND@@")
    )


def starts_new_block(text: str) -> bool:
    t = text.lstrip()
    if not t:
        return True
    return t.splitlines()[0].strip().startswith(BLOCK_STARTS)


def _mark_page_ends(page: str, pno: int) -> str:
    """Put position markers inline on a source page's first and last text lines."""
    top, end = f"@@SRCTOP{pno}@@", f"@@SRCEND{pno}@@"
    block_starts = ("#", "$", "!", "|", "\\[")
    body = page.strip()
    if body.startswith("@@NOINDENT@@"):
        body = "@@NOINDENT@@" + top + body.removeprefix("@@NOINDENT@@")
    elif body.startswith(block_starts) or body.startswith("@@"):
        body = f"{top}\n\n{body}"
    else:
        body = top + body
    if body.endswith(" @@JUSTIFYEND@@"):
        return body.removesuffix(" @@JUSTIFYEND@@") + f"{end} @@JUSTIFYEND@@"
    last_line = body.splitlines()[-1].lstrip()
    if last_line.startswith(block_starts):
        return f"{body}\n\n{end}"
    return body + end


def split_first_paragraph(text: str) -> tuple[str, str]:
    parts = re.split(r"\n\s*\n", text.lstrip(), maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def join_cross_page_text(prev: str, curr_first: str) -> str:
    prev_r = prev.rstrip()
    curr_l = curr_first.lstrip()
    last_line = prev_r.splitlines()[-1].strip() if prev_r else ""
    if last_line.endswith("$$") or EQ_LABEL_END_RE.search(last_line):
        return prev_r + "\n" + curr_l
    if prev_r.endswith("-"):
        m1 = re.search(r"\b([a-zA-Z]+)-$", prev_r)
        m2 = re.match(r"^([a-zA-Z]+)\b", curr_l)
        if m1 and m2:
            if m1.group(1).lower() in HYPHEN_JOIN_WORDS:
                return prev_r[:-1] + "\u2011" + curr_l
            return prev_r[:-1] + curr_l
    return prev_r + " " + curr_l


def _label_section_equations(s: str, pno: int) -> str:
    """Label `(1.2)`-style equation numbers as `<eq-PAGE-1-2>`."""
    s = re.sub(r"\\tag\{\(?(\d+)\.(\d+[a-z']?)\)?\}", rf"\\tag{{{pno}-\1-\2}}", s)
    s = re.sub(
        r"^\s*\((\d+)\.(\d+[a-z']?)\)\s*\$([^$\n]{8,})\$\s*$",
        r"(\1.\2)\n$$\n\3\n$$",
        s,
        flags=re.MULTILINE,
    )
    s = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\n\1\n$$", s, flags=re.DOTALL)

    def replace_block(m: re.Match[str]) -> str:
        pre_ch, pre_num = m.group(1), m.group(2)
        body = m.group(3).strip()
        post_ch, post_num = m.group(4), m.group(5)
        eq_id = ""
        if pre_ch and pre_num:
            eq_id = f"{pre_ch}-{pre_num}"
        elif pre_ch:
            eq_id = f"{pre_ch}"
        elif post_ch and post_num:
            eq_id = f"{post_ch}-{post_num}"
        elif post_ch:
            eq_id = f"{post_ch}"
        m_start = re.match(
            r"^\((\d+)(?:\.(\d+[a-z']?))?\)\s*(?:\\q?quad\s*|\\hfill\s*)*", body
        )
        if m_start and not eq_id:
            ch, num = m_start.group(1), m_start.group(2)
            eq_id = f"{ch}-{num}" if num else f"{ch}"
            body = body[m_start.end() :].strip()
        m_end = re.search(r"(?:\\hfill|\\q?quad|\s)+\((\d+)(?:\.(\d+[a-z']?))?\)\s*$", body)
        if m_end and not eq_id:
            ch, num = m_end.group(1), m_end.group(2)
            eq_id = f"{ch}-{num}" if num else f"{ch}"
            body = body[: m_end.start()].strip()
        m_tag = re.search(r"\\tag\{([0-9a-zA-Z'-]+)\}", body)
        if m_tag:
            eq_id = eq_id or m_tag.group(1)
            body = (body[: m_tag.start()] + body[m_tag.end() :]).strip()
        label = f" <eq-{eq_id}>" if eq_id else ""
        return f"\n\n$$\n{body}\n$${label}\n\n"

    s = re.sub(
        r"(?:^[ \t]*\((\d+)(?:\.(\d+[a-z']?))?\)[ \t]*\n*\s*)?\$\$(.*?)\$\$"
        r"(?:[ \t]*\n?[ \t]*\((\d+)(?:\.(\d+[a-z']?))?\)[ \t]*(?=\n|$))?",
        replace_block,
        s,
        flags=re.MULTILINE | re.DOTALL,
    )
    s = re.sub(r"\\tag\{[^{}]*\}", "", s)
    s = re.sub(r"(<eq-[^>]+>)(?:\s*<eq-[^>]+>)+", r"\1", s)
    if len(re.findall(r"\$\$", s)) % 2 != 0:
        s = s.rstrip() + "$$"
    return s


def _label_page_equations(s: str, ch_num: int, pno: int) -> str:
    """Label plain `(n)` equation numbers as `<eq-CHAPTER-PAGE-n>`."""
    s = re.sub(r"\\tag\{(\d+)\}", rf"\\tag{{{ch_num}-{pno}-\1}}", s)
    s = re.sub(
        r"^\s*\((\d+)\)\s*\$([^$\n]{10,})\$\s*$",
        r"(\1)\n$$\n\2\n$$",
        s,
        flags=re.MULTILINE,
    )
    s = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\n\1\n$$", s, flags=re.DOTALL)

    def replace_block(m: re.Match[str]) -> str:
        number = m.group(1) or m.group(3)
        body = m.group(2).strip()
        eq_id = f"{ch_num}-{pno}-{number}" if number else ""
        m_start = re.match(r"^\((\d+)\)\s*(?:\\quad\s*)*", body)
        if m_start and not eq_id:
            eq_id = f"{ch_num}-{pno}-{m_start.group(1)}"
            body = body[m_start.end() :].strip()
        m_end = re.search(r"(?:\\quad|\s)+\((\d+)\)$", body)
        if m_end and not eq_id:
            eq_id = f"{ch_num}-{pno}-{m_end.group(1)}"
            body = body[: m_end.start()].strip()
        m_tag = re.search(r"\\tag\{([0-9-]+)\}", body)
        if m_tag:
            eq_id = eq_id or m_tag.group(1)
            body = (body[: m_tag.start()] + body[m_tag.end() :]).strip()
        label = f" <eq-{eq_id}>" if eq_id else ""
        return f"\n\n$$\n{body}\n$${label}\n\n"

    return re.sub(
        r"(?:^[ \t]*\((\d+)\)[ \t]*\n*\s*)?\$\$(.*?)\$\$"
        r"(?:[ \t]*\n?[ \t]*\n?[ \t]*\((\d+)\)[ \t]*(?=\n|$))?",
        replace_block,
        s,
        flags=re.MULTILINE | re.DOTALL,
    )


def _attach_footnotes(s: str, footnotes: list[str], marker: str) -> str:
    s = re.sub(
        r"takes the form(\s*\n+\s*\$\$.*?)\s*\\dagger\s*(\$\$)",
        rf"takes the form{marker}\1\2",
        s,
        flags=re.DOTALL,
    )
    s = re.sub(r"\s*\\dagger\s*\$", f"${marker}", s)
    for text in footnotes:
        note = f"@@FNSTART@@{text}@@FNEND@@"
        s = s.replace(marker, note, 1) if marker in s else s + note
    return s


THEOREM_KINDS = (
    "Theorem",
    "Lemma",
    "Corollary",
    "Proposition",
    "Definition",
    "Example",
    "Remark",
    "Question",
    "Exercise",
    "Problem",
    "Claim",
    "Conjecture",
    "Axiom",
    "Fact",
)
ITALIC_THEOREM_KINDS = frozenset(
    {
        "theorem",
        "lemma",
        "corollary",
        "proposition",
        "conjecture",
        "axiom",
        "claim",
        "fact",
    }
)
THEOREM_HEAD_RE = re.compile(
    rf"^(?P<open>\*\*)?(?P<kind>{'|'.join(THEOREM_KINDS)})\s+"
    r"(?P<num>[0-9A-Z]+(?:\.\d+)*[a-z]?)(?P<dot>\.)?(?P<close>\*\*)?"
    r"\s*(?P<note>\([^()]{1,60}\))?\s*(?:\*\*)?(?P<dot2>\.)?\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
PROOF_HEAD_RE = re.compile(
    r"^(?:\*\*|\*)?(?P<head>proof(?:\s+of\s+[^*]{1,60}?)?)\.(?!\d|\()(?:\*\*|\*)?"
    r"\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
RUN_IN_PAREN_RE = re.compile(r"^\(([a-h])\)")
RUN_IN_SPLIT_RE = re.compile(r"^(?P<title>.{2,120}?[.:])\s+(?P<rest>[A-Z“\"(].*)$")
RUN_IN_VERBS = frozenset(
    [
        "let",
        "show",
        "prove",
        "suppose",
        "if",
        "find",
        "assume",
        "then",
        "for",
        "determine",
        "compute",
        "we",
        "the",
    ]
)
CHAPTER_OPENING_RE = re.compile(
    r"^(?:#+\s*.+|(?:CHAPTER|APPENDIX)\s+[0-9A-Z]+|[—–-]+\s*.+?\s*[—–-]+)$",
    re.IGNORECASE,
)
END_MATTER_HEADING_RE = re.compile(
    r"^\**(?:summary|exercises|problems|notes)\**$", re.IGNORECASE
)


FIGURE_LABEL_RE = re.compile(
    r"^(?![#*>]|\$\$|\\\[|\(\d+\.\d+\))[^\n]{1,60}(?<![.:;?!,])\s*$"
)


def _is_isolated(body_lines: list[str]) -> bool:
    """A line that is a paragraph on its own, as OCR'd figure labels are."""
    before = body_lines[-2] if len(body_lines) >= 2 else ""
    return not before.strip()


def _proof_head(head: str) -> str:
    words = head.lower().split()
    return " ".join(
        w.capitalize() if i == 0 or w.rstrip("s").capitalize() in THEOREM_KINDS else w
        for i, w in enumerate(words)
    )


def normalize_run_in(lt: str, from_heading: bool = False, upper: bool = False) -> str:
    """Rewrite a paragraph's run-in head (theorem, proof, `(a)` subhead) in one style."""
    m = THEOREM_HEAD_RE.match(lt)
    if (
        m
        and (m["dot"] or m["dot2"] or m["close"])
        and (m["open"] or m["kind"][0].isupper())
    ):
        kind = m["kind"].upper() if upper else m["kind"].capitalize()
        note = f" {m['note']}" if m["note"] else ""
        r = (m["rest"] or "").strip()
        if r and m["kind"].lower() in ITALIC_THEOREM_KINDS and "*" not in r:
            m_item = re.match(r"^(\([0-9ivx]+\))\s+(.+)$", r)
            r = f"{m_item.group(1)} *{m_item.group(2)}*" if m_item else f"*{r}*"
        rest = f" {r}" if r else ""
        return f"**{kind} {m['num']}.**{note}{rest}"
    m = PROOF_HEAD_RE.match(lt)
    if m:
        rest = f" {m['rest']}" if m["rest"] else ""
        return f"*{_proof_head(m['head'])}.*{rest}"
    m = re.match(r"^\*\*\(([a-h])\)\s*(.+?)\*\*\s*(.*)$", lt)
    if m:
        return f"**({m[1]}) {m[2].strip()}** {m[3]}".rstrip()
    m = re.match(r"^\(([a-h])\)\s*\*\*(.+?)\*\*\s*(.*)$", lt)
    if m:
        return f"**({m[1]}) {m[2].strip()}** {m[3]}".rstrip()
    m = re.match(r"^(?:\*\*)?\(([a-h])\)(\*\*)?\s+(.+)$", lt)
    if not m or not (from_heading or m[2]):
        if not m:
            return lt
        split = RUN_IN_SPLIT_RE.match(m[3])
        first = m[3].split(maxsplit=1)[0].lower()
        if (
            split is None
            or "$" in split["title"]
            or len(split["title"].split()) > 6
            or first in RUN_IN_VERBS
        ):
            return lt
        return f"**({m[1]}) {split['title']}** {split['rest']}"
    split = RUN_IN_SPLIT_RE.match(m[3])
    if split is None:
        return f"**({m[1]}) {m[3].strip()}**"
    return f"**({m[1]}) {split['title']}** {split['rest']}"


def _first_top_level_char(body: str, target: str) -> int:
    depth = 0
    for i, ch in enumerate(body):
        if ch in "{([" and (i == 0 or body[i - 1] != "\\"):
            depth += 1
        elif ch in "})]" and (i == 0 or body[i - 1] != "\\"):
            depth -= 1
        elif ch == target and depth == 0:
            return i
    return -1


CONTINUATION_OP_RE = re.compile(
    r"^(?:\+|-|\\times|\\cdot|\\le|\\ge|<|>|\\equiv|\\cong|\\approx|\\to|\\mapsto|\\longmapsto|\\Longleftrightarrow|\\Leftrightarrow)\b"
)


def _merge_display_run(run: str, display_blocks: list[tuple[str, str]]) -> str:
    """Join displays that the OCR split row by row into one aligned display."""
    ids = [int(n) for n in re.findall(r"@@DISPLAYBLOCK(\d+)@@", run)]
    bodies = [display_blocks[i][0] for i in ids]
    labels = [display_blocks[i][1] for i in ids]
    if (
        sum(bool(lbl) for lbl in labels) > 1
        or any("\\begin" in b or "\\\\" in b or "&" in b for b in bodies)
        or sum(len(b) for b in bodies) > 900
    ):
        return run
    eq_at = [_first_top_level_char(b, "=") for b in bodies]
    semi_at = [_first_top_level_char(b, ";") for b in bodies]
    if all(pos >= 0 for pos in eq_at):
        rows = [b[:pos] + "&" + b[pos:] for b, pos in zip(bodies, eq_at, strict=True)]
        env = "aligned"
    elif eq_at[0] >= 0 and all(
        pos >= 0 or CONTINUATION_OP_RE.match(b.lstrip())
        for b, pos in zip(bodies, eq_at, strict=True)
    ):
        rows = [
            b[:pos] + "&" + b[pos:] if pos >= 0 else r"&\quad " + b
            for b, pos in zip(bodies, eq_at, strict=True)
        ]
        env = "aligned"
    elif eq_at[0] < 0 and all(pos == 0 for pos in eq_at[1:]):
        rows = ["&" + bodies[0], *[r"&\qquad " + b for b in bodies[1:]]]
        env = "aligned"
    elif all(pos >= 0 for pos in semi_at):
        rows = [
            b[: pos + 1] + "&" + b[pos + 1 :]
            for b, pos in zip(bodies, semi_at, strict=True)
        ]
        env = "aligned"
    else:
        rows = bodies
        env = "gathered"
    merged = rf"\begin{{{env}}}" + " \\\\\n".join(rows) + rf"\end{{{env}}}"
    label = next((lbl for lbl in labels if lbl), "")
    display_blocks[ids[0]] = (merged, label)
    return f"@@DISPLAYBLOCK{ids[0]}@@"


def _find_balanced_parens(s: str, start: int) -> int:
    count = 0
    for i in range(start, len(s)):
        if s[i] == "(":
            count += 1
        elif s[i] == ")":
            count -= 1
            if count == 0:
                return i
    return -1


def _fix_typst_single_arg_frac(text: str) -> str:
    pos = 0
    res: list[str] = []
    while True:
        idx = text.find("frac(", pos)
        if idx == -1:
            res.append(text[pos:])
            break
        res.append(text[pos:idx])
        end1 = _find_balanced_parens(text, idx + 4)
        if end1 != -1:
            inner1 = text[idx + 5 : end1]
            if "," not in inner1:
                nxt = text[end1 + 1 :].lstrip()
                if nxt.startswith("("):
                    start2 = text.find("(", end1 + 1)
                    end2 = _find_balanced_parens(text, start2)
                    if end2 != -1:
                        inner2 = text[start2 + 1 : end2]
                        res.append(f"({inner1})/({inner2})")
                        pos = end2 + 1
                        continue
        res.append("frac(")
        pos = idx + 5
    return "".join(res)
def _normalize_typst_differentials(t: str) -> str:
    t = t.replace("upright(d)", "dif")
    return re.sub(
        r"(?<![a-zA-Z0-9_\^])d\s*([xyztrsuvwqp]|xi|alpha|beta|gamma|theta|phi|tau|lambda|mu)(?=[0-9\s\^_,.;!?\)]|$)",
        r"dif \1",
        t,
    )


class MonographCompiler:
    """Compiles transcribed Markdown pages and figures into Markdown, LaTeX, Typst, and PDF."""

    def __init__(self, spec: MonographSpec) -> None:
        self.spec: MonographSpec = spec
        self.composition: CompositionConfig = resolve_composition(
            publisher=spec.publisher_key,
            lang=spec.lang,
            domain=spec.domain,
        )
        self._seen_sections: set[str] = set()
        self._out_dir: Path = Path()
        self._caption_re: re.Pattern[str] = re.compile(
            spec.figures.caption_pattern,
            re.IGNORECASE if spec.figures.caption_ignore_case else 0,
        )
        self._chapter_starts: frozenset[int] = frozenset(
            c.start_page for c in spec.chapters
        )

    def build_typst_preamble(self) -> str:
        if self.spec.typst_preamble:
            return self.spec.typst_preamble
        pub = self.composition.publisher
        lang = self.composition.language
        dom = self.composition.domain
        font_expr = self.composition.typst_font_tuple()
        hyph_str = "true" if lang.hyphenate else "false"
        eq_num_str = (
            "none"
            if dom.equation_numbering == "none"
            else f'"{dom.equation_numbering}"'
        )
        rule_line = (
            f"#v(-0.35em)\n      #line(length: 100%, stroke: {pub.header_rule_pt}pt + luma(120))"
            if pub.header_rule_pt > 0
            else ""
        )
        heading_rules = self.composition.typst_heading_rules()
        return f"""#set document(
  title: "{self.spec.title} — {self.spec.author}",
  author: "{self.spec.author}",
  date: auto
)

#set page(
  width: {pub.width_pt}pt,
  height: {pub.height_pt}pt,
  margin: (inside: {pub.margin_inside_pt}pt, outside: {pub.margin_outside_pt}pt, top: {pub.margin_top_pt}pt, bottom: {pub.margin_bottom_pt}pt),
  header: context {{
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if page-number > 4 and not on-chapter-page [
      #if calc.odd(page-number) [
        #let secs = query(heading.where(level: 2).before(here()))
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = if secs != () {{ secs.last().body }} else if chaps != () {{ chaps.last().body }} else {{ "{self.spec.title}" }}
        #grid(
          columns: (1fr, auto),
          align(left)[#text(8.5pt, font: {font_expr}, style: "italic")[#title]],
          align(right)[#text(9.5pt, font: {font_expr})[#page-number]]
        )
      ] else [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = if chaps != () {{ chaps.last().body }} else {{ "{self.spec.title}" }}
        #grid(
          columns: (auto, 1fr),
          align(left)[#text(9.5pt, font: {font_expr})[#page-number]],
          align(right)[#text(8.5pt, font: {font_expr}, style: "italic")[#title]]
        )
      ]
      {rule_line}
    ]
  }},
  footer: none
)

#set text(
  font: {font_expr},
  size: {pub.body_size_pt:g}pt,
  lang: "{lang.typst_lang}",
  hyphenate: {hyph_str}
)

#set par(
  leading: {lang.leading},
  spacing: {lang.par_spacing},
  justify: true,
  first-line-indent: {lang.first_line_indent},
  linebreaks: "optimized"
)

#show math.equation: set text(font: "{lang.math_font}")
#set math.equation(numbering: {eq_num_str})
#set math.mat(row-gap: 0.55em, column-gap: 0.8em)
#set math.cases(gap: 0.55em)
#show math.equation.where(block: false): it => {{
  show math.frac: set text(size: 0.85em)
  it
}}
#show math.equation.where(block: true): set block(above: 1.3em, below: 1.3em)
#show math.equation.where(block: true): set par(leading: 0.88em)
#let thm-break = block(above: 1.65em, below: 0pt, sticky: true)[]
#let sub-break = block(above: 1.35em, below: 0pt, sticky: true)[]
#let item-break = block(above: 1.0em, below: 0pt)[]
#let qed = {{ h(0.6em); box(width: 1fr, align(right)[$square.stroked$]) }}
#let dd = math.dif
#let dv(f, x, deg: none) = if deg == none {{ $(dif f)/(dif x)$ }} else {{ $(dif^deg f)/(dif x^deg)$ }}
#let pdv(f, x, deg: none) = if deg == none {{ $(partial f)/(partial x)$ }} else {{ $(partial^deg f)/(partial x^deg)$ }}
#let const = math.op("const")
#let ord = math.op("ord")
#let grad = math.op("grad")
#let rot = math.op("rot")
#let div = math.op("div")
#let rank = math.op("rank")
#show ref: it => {{
  let target = str(it.target)
  if target.starts-with("eq-") {{
    let raw = target.trim("eq-", at: start)
    let parts = raw.split("-")
    let disp = if parts.len() >= 2 {{ parts.at(-2) + "." + parts.last() }} else {{ parts.last() }}
    link(it.target)[(#disp)]
  }} else {{
    it
  }}
}}
#show math.equation.where(block: true): it => {{
  if it.numbering == none {{
    return it
  }}
  layout(size => {{
    let eq = math.equation(it.body, block: true, numbering: none)
    if not it.has("label") {{
      let m = measure(eq)
      if m.width > size.width and m.width > 0pt {{
        let factor = (size.width / m.width) * 100%
        align(center, scale(x: factor, y: factor, reflow: true, eq))
      }} else {{
        eq
      }}
    }} else {{
      let lbl = str(it.label).trim("eq-", at: start)
      let parts = lbl.split("-")
      let disp = if parts.len() >= 2 {{ parts.at(-2) + "." + parts.last() }} else {{ parts.last() }}
      let num-box = [(#disp)]
      let avail = size.width - measure(num-box).width - 12pt
      let m = measure(eq)
      let fitted = if m.width > avail and m.width > 0pt {{
        let factor = (avail / m.width) * 100%
        scale(x: factor, y: factor, reflow: true, eq)
      }} else {{
        eq
      }}
      grid(
        columns: (1fr, auto),
        column-gutter: 0.8em,
        align: (center + horizon, right + horizon),
        fitted,
        num-box
      )
    }}
  }})
}}

#show heading: set par(justify: false, first-line-indent: 0pt)
#let chapter-label = state("chapter-label", none)

{heading_rules}

#show figure: set block(above: 1.6em, below: 1.6em)
#show figure.caption: it => [
  #v(0.45em)
  #text(9pt, font: {font_expr})[#it.body]
]
"""

    def build_typst_title_page(self) -> str:
        if self.spec.typst_front_matter:
            return self.spec.typst_front_matter
        font_expr = self.composition.typst_font_tuple()
        pub = self.composition.publisher
        lang = self.composition.language
        credits = ""
        if self.spec.translator or self.spec.editor:
            parts: list[str] = []
            if self.spec.translator:
                parts.append(f"Translated by {self.spec.translator}")
            if self.spec.editor:
                parts.append(f"Edited by {self.spec.editor}")
            joined_credits = "\\ ".join(parts)
            credits = f'#v(1.6em)\n  #text(10pt, style: "italic", font: {font_expr})[{joined_credits}]'
        return f"""
#align(center + horizon)[
  #text(10pt, tracking: 0.14em, font: {font_expr})[#smallcaps("{self.spec.series}")]
  #v(3em)
  #text(26pt, weight: "bold", font: {font_expr})[{self.spec.title.upper()}]
  #v(2.2em)
  #text(14pt, weight: "bold", font: {font_expr})[#smallcaps("{self.spec.author}")]
  {credits}
  #v(5em)
  #line(length: 35%, stroke: 0.4pt + luma(140))
  #v(1.2em)
  #text(11pt, weight: "bold", tracking: 0.12em, font: {font_expr})[{self.spec.publisher.upper()}]
  #v(0.4em)
  #text(8.5pt, fill: luma(90), font: {font_expr})[{pub.cities_line}]
]

#pagebreak()

#outline(title: [{lang.contents_title}], indent: 1.4em, depth: 2)

#pagebreak()
"""

    def _resolve_figure_asset(self, fig_dir: Path, fig_id: str) -> Path | None:
        for ext in ("svg", "png"):
            candidate = fig_dir / f"fig_{fig_id}.{ext}"
            if candidate.exists():
                return candidate
        return None

    def _figure_width_pct(self, asset: Path, paired: bool) -> int:
        layout = self.spec.figures
        if asset.suffix == ".svg":
            if paired:
                return layout.svg_paired_pct
            if layout.svg_single_pct is not None:
                return layout.svg_single_pct
            m_vb = re.search(r'viewBox="([^"]+)"', asset.read_text(encoding="utf-8"))
            vw, vh = 460.0, 280.0
            if m_vb:
                parts = [float(x) for x in m_vb.group(1).split()]
                if len(parts) == 4:
                    vw, vh = parts[2], parts[3]
            width_pct = min(68, max(40, round(vw / 720 * 100)))
            if vh * (width_pct / 100.0) / max(vw, 1.0) > 0.36:
                width_pct = max(32, round(0.36 * vw / max(vh, 1.0) * 100))
            return width_pct
        with Image.open(asset) as im:
            w_px, h_px = im.size
        if paired:
            lo, hi = layout.png_paired_range
            return min(hi, max(lo, round(w_px / layout.png_paired_divisor * 100)))
        lo, hi = layout.png_single_range
        width_pct = min(hi, max(lo, round(w_px / layout.png_single_divisor * 100)))
        ratio = layout.png_max_height_ratio
        if h_px * (width_pct / 100.0) / max(w_px, 1) > ratio:
            width_pct = max(
                layout.png_min_pct_tall, round(ratio * w_px / max(h_px, 1) * 100)
            )
        return width_pct

    def make_figure_typst(
        self, fig_id: str, raw_caption: str, fig_dir: Path, paired: bool = False
    ) -> str:
        clean_cap = clean_margin_and_inline_math(raw_caption.strip().replace("**", ""))
        clean_cap = re.sub(
            r"^(Fig(?:ure)?\.?\s*\d+[\.\-]\d+[a-z]?\.?)",
            r"#strong[\1]",
            clean_cap,
            flags=re.IGNORECASE,
        )
        asset = self._resolve_figure_asset(fig_dir, fig_id)
        if asset is None:
            return f"\n\n#align(center)[#emph[{clean_cap}]]\n\n"
        width_pct = self._figure_width_pct(asset, paired)
        supplement = (
            ",\n  supplement: none" if self.spec.figures.supplement_none else ""
        )
        return (
            f"#figure(\n"
            f'  image("{fig_dir.name}/{asset.name}", width: {width_pct}%),\n'
            f"  caption: [{clean_cap}]{supplement}\n"
            f")"
        )

    def render_figure_group(self, figs: list[Figure], fig_dir: Path) -> str:
        valid_figs = [
            (fid, cap)
            for fid, cap in figs
            if self._resolve_figure_asset(fig_dir, fid) is not None
        ]
        if not valid_figs:
            return ""
        if len(valid_figs) == 2:
            f1 = self.make_figure_typst(*valid_figs[0], fig_dir, paired=True)
            f2 = self.make_figure_typst(*valid_figs[1], fig_dir, paired=True)
            return (
                f"\n\n#align(center)[\n"
                f"  #grid(\n"
                f"    columns: (1fr, 1fr),\n"
                f"    column-gutter: 1.5em,\n"
                f"    align: center + bottom,\n"
                f"    [{f1}],\n"
                f"    [{f2}]\n"
                f"  )\n"
                f"]\n\n"
            )
        return "".join(
            f"\n\n#align(center)[\n  {self.make_figure_typst(fid, cap, fig_dir)}\n]\n\n"
            for fid, cap in valid_figs
        )

    def _chapter_of(self, pno: int) -> int:
        for chap in self.spec.chapters:
            if chap.start_page <= pno <= chap.end_page:
                return chap.number
        return 0

    def _section_in_chapter(self, sec_id: str, pno: int) -> bool:
        chapter = self._chapter_of(pno)
        if self._chapter_of(self.spec.sections[sec_id][0]) == chapter:
            return True
        prefix = sec_id.split(".")[0]
        if prefix.isdigit():
            return int(prefix) == chapter
        return any(
            c.number == chapter and f"appendix {prefix.lower()}" in c.title.lower()
            for c in self.spec.chapters
        )

    def _is_page_furniture(self, lt: str, pno: int, lines_so_far: int) -> bool:
        spec = self.spec
        zone = spec.header_zone_lines
        if lines_so_far <= (2 if zone is None else zone):
            if any(re.match(rx, lt, re.IGNORECASE) for rx in spec.running_header_regexes):
                return True
            if any(re.match(rx, lt, re.IGNORECASE) for rx in spec.drop_line_regexes):
                return True
        if spec.sections and lines_so_far <= 2:
            m_sec_hdr = re.match(
                r"^(?:#+\s*)?([0-9A-Z]+\.\d+)\.?\s+(.+?)(?:\s+\d{1,3})?$", lt
            )
            sec_id = m_sec_hdr.group(1) if m_sec_hdr else ""
            if (
                sec_id in spec.sections
                and sec_id in self._seen_sections
                and self._section_in_chapter(sec_id, pno)
            ):
                return True
        return (
            pno in self._chapter_starts
            and lines_so_far <= 2
            and bool(re.match(r"^(?:#+\s*)?[1-9]\d?$", lt))
        )

    def _normalized_heading(self, lt: str, pno: int) -> str | None:
        """Return the canonical heading line, "" to drop the line, or None to keep it."""
        if self.spec.heading_hook is not None:
            hooked = self.spec.heading_hook(lt, self._chapter_of(pno))
            if hooked is not None and hooked.startswith("## "):
                key = f"{self._chapter_of(pno)}:{hooked}"
                if key in self._seen_sections:
                    return ""
                self._seen_sections.add(key)
            if hooked is not None:
                return hooked
        m_sec = re.match(
            r"^(?:#+\s*|\*\*)?([0-9A-Z]+\.\d+)\.?\s+([^\n]+?)(?:\*\*)?$", lt
        )
        if (
            m_sec
            and m_sec.group(1) in self.spec.sections
            and len(m_sec.group(2)) <= 90
            and self._section_in_chapter(m_sec.group(1), pno)
        ):
            sec_id = m_sec.group(1)
            canon_title = self.spec.sections[sec_id][1]
            if sec_id not in self._seen_sections:
                self._seen_sections.add(sec_id)
                return f"## {sec_id} {canon_title}"
            return ""
        m_sub = re.match(
            r"^(?:#+\s*|\*\*)?([a-e])\.?\s+([A-Z\$][A-Za-z0-9\s\-,'’\(\)–—\$\\]{2,65}?)(?:\*\*)?\.?$",
            lt,
        )
        if m_sub and len(lt) < 76:
            return f"### {m_sub.group(1)}. {m_sub.group(2).strip()}"
        m_hash = re.match(r"^#+\s*(.+?)\s*$", lt)
        if not m_hash:
            return None
        inner_h = m_hash.group(1).strip()
        if END_MATTER_HEADING_RE.match(inner_h):
            title = inner_h.strip("*").title()
            key = f"{self._chapter_of(pno)}:{title}"
            if key in self._seen_sections:
                return ""
            self._seen_sections.add(key)
            return f"## {title}"
        if RUN_IN_PAREN_RE.match(inner_h.lstrip("*")):
            return normalize_run_in(inner_h, from_heading=True)
        if re.match(r"^Chapter\s+\d+$", inner_h, re.IGNORECASE):
            return f"## {inner_h}"
        if re.match(r"^Proof\b", inner_h, re.IGNORECASE):
            return f"*{inner_h}*"
        thm_heads = "|".join(
            (*self.composition.domain.theorem_heads, r"Weyl['’]s Lemma")
        )
        if thm_heads and re.match(rf"^(?:{thm_heads})\b", inner_h):
            return (
                f"**{inner_h}**" if inner_h.endswith((".", ":")) else f"**{inner_h}.**"
            )
        return inner_h

    def extract_page_parts(
        self, md_text: str, pno: int
    ) -> tuple[str, list[Figure], list[Figure]]:
        spec = self.spec
        layout = spec.figures
        md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)
        from ..cleaner.tex_markdown import TeXMarkdownCleaner
        md_text = TeXMarkdownCleaner.normalize_html_tables(md_text)
        body_lines: list[str] = []
        footnotes: list[str] = []
        top_figs: list[Figure] = []
        bot_figs: list[Figure] = []
        seen_figs_on_page: set[str] = set()

        for line in md_text.splitlines():
            lt = line.strip()
            if not lt:
                body_lines.append("")
                continue
            if re.match(spec.folio_pattern, lt, re.IGNORECASE):
                continue
            lines_so_far = len([b for b in body_lines if b.strip()])
            if self._is_page_furniture(lt, pno, lines_so_far):
                continue
            if spec.footnote_marker and lt.startswith(spec.footnote_marker):
                footnotes.append(lt.lstrip(spec.footnote_marker).strip())
                continue

            m_fig = self._caption_re.match(lt)
            if m_fig:
                while body_lines and (
                    not body_lines[-1].strip() or FIGURE_LABEL_RE.match(body_lines[-1])
                ):
                    if body_lines[-1].strip() and not _is_isolated(body_lines):
                        break
                    _ = body_lines.pop()
                while body_lines and (
                    not body_lines[-1].strip()
                    or re.match(r"^\([1-9a-z]\)$", body_lines[-1].strip())
                ):
                    if re.match(r"^\([1-9a-z]\)$", body_lines[-1].strip()) or (
                        len(body_lines) >= 2
                        and re.match(r"^\([1-9a-z]\)$", body_lines[-2].strip())
                    ):
                        _ = body_lines.pop()
                    else:
                        break
                chapter, number = m_fig.group("chapter"), m_fig.group("number")
                fid = f"{chapter}_{number}"
                if fid not in seen_figs_on_page:
                    seen_figs_on_page.add(fid)
                    tail = (m_fig.groupdict().get("tail") or "").strip()
                    cap = layout.caption_format.format(chapter=chapter, number=number)
                    if tail:
                        sep = " " if cap.endswith((".", ":")) else ". "
                        cap = f"{cap}{sep}{tail}"
                    if lines_so_far <= layout.top_zone_lines or pno in layout.top_pages:
                        top_figs.append((fid, cap))
                    else:
                        bot_figs.append((fid, cap))
                continue

            if spec.normalize_headings:
                if (
                    pno in self._chapter_starts
                    and not any(b.strip() and not b.startswith("#") for b in body_lines)
                    and CHAPTER_OPENING_RE.match(lt)
                    and not re.match(r"^#*\s*[0-9A-Z]+\.\d+", lt)
                ):
                    continue
                heading = self._normalized_heading(lt, pno)
                if heading == "":
                    continue
                if heading is not None:
                    body_lines.append(heading)
                    continue
                line = normalize_run_in(lt, upper=spec.theorem_heads_upper)

            body_lines.append(line)

        s = "\n".join(body_lines).strip()
        s = re.sub(r"\\\s+(begin|end)\b", r"\\\1", s)
        for pattern, repl in spec.page_fixups.get(pno, ()):
            rep_arg = (
                repl if re.search(r"\\[1-9]|\\g<", repl) else (lambda _, r=repl: r)
            )
            s = re.sub(pattern, rep_arg, s, flags=re.DOTALL)
        if footnotes:
            s = _attach_footnotes(s, footnotes, spec.footnote_marker)
        if spec.equation_numbering == "page":
            s = _label_page_equations(s, self._chapter_of(pno), pno)
        else:
            s = _label_section_equations(s, pno)
        bot_figs.extend(spec.extra_figures.get(pno, ()))
        return s.strip(), top_figs, bot_figs

    def stitch_chapter(self, pages_data: list[PageParts], fig_dir: Path) -> str:
        if self.spec.paginate_like_source:
            return self._stitch_by_source_page(pages_data, fig_dir)
        acc = ""
        pending_figs: list[Figure] = []

        for idx, (_pno, text, top_figs, bot_figs) in enumerate(pages_data):
            if not text and not top_figs and not bot_figs:
                continue

            all_top_figs = pending_figs + top_figs
            pending_figs = []
            starts_lower = bool(text.strip()) and text.lstrip()[0].islower()
            continues_prev = (
                not ends_complete_paragraph(acc) and not starts_new_block(text)
            ) or starts_lower

            if not acc:
                acc = self.render_figure_group(all_top_figs, fig_dir) + text
            elif continues_prev:
                first_p, rest_p = split_first_paragraph(text)
                acc = join_cross_page_text(acc, first_p)
                if all_top_figs:
                    acc += self.render_figure_group(all_top_figs, fig_dir)
                if rest_p:
                    acc += "\n\n" + rest_p
            else:
                if all_top_figs:
                    acc += self.render_figure_group(all_top_figs, fig_dir)
                acc += "\n\n" + text

            if bot_figs:
                next_starts_lower = (
                    idx + 1 < len(pages_data)
                    and bool(pages_data[idx + 1][1].strip())
                    and pages_data[idx + 1][1].lstrip()[0].islower()
                )
                if ends_complete_paragraph(acc) and not next_starts_lower:
                    acc += self.render_figure_group(bot_figs, fig_dir)
                else:
                    pending_figs.extend(bot_figs)

        if pending_figs:
            acc += self.render_figure_group(pending_figs, fig_dir)
        return acc


    def format_typst(self, s: str) -> str:
        spec = self.spec
        fig_blocks: list[str] = []

        def save_fig(m: re.Match[str]) -> str:
            fig_blocks.append(m.group(0))
            return f"\n\n@@FIGBLOCK{len(fig_blocks) - 1}@@\n\n"

        s = re.sub(r"#align\(center\)\[\n.*?\n\]", save_fig, s, flags=re.DOTALL)
        s = re.sub(r"^(\s*)=", r"\1\\=", s, flags=re.MULTILINE)
        s = re.sub(r"^>\s?", "", s, flags=re.MULTILINE)

        for pattern, repl in spec.heading_rewrites:
            s = re.sub(pattern, repl, s, flags=re.MULTILINE)
        s = re.sub(r"^#{4,6}\s+(.*?)$", r"==== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^###\s+(.*?)$", r"=== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^##\s+(.*?)$", r"== \1", s, flags=re.MULTILINE)
        s = re.sub(r"^#\s+(.*?)$", r"= \1", s, flags=re.MULTILINE)

        s = s.replace(r"\leqq", "<=").replace(r"\geqq", ">=")
        for pattern, repl in spec.pre_math_rewrites:
            s = re.sub(pattern, repl, s)

        display_blocks: list[tuple[str, str]] = []

        def save_display(m: re.Match[str]) -> str:
            display_blocks.append((m.group(1).strip(), m.group(2) or ""))
            return f"\n\n@@DISPLAYBLOCK{len(display_blocks) - 1}@@\n\n"

        def save_align(m: re.Match[str]) -> str:
            label = f"<eq-align-{m.group(1)}>" if m.group(1) else ""
            display_blocks.append((m.group(2).strip(), label))
            return f"\n\n@@DISPLAYBLOCK{len(display_blocks) - 1}@@\n\n"

        s = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\n\1\n$$", s, flags=re.DOTALL)
        s = re.sub(
            r"\$\$\s*(.*?)\s*\$\$\s*(<eq-[^>]+>)?", save_display, s, flags=re.DOTALL
        )
        s = re.sub(
            r"(?:\((\d+)\)\s*)?\\begin\{align\*?\}(.*?)\\end\{align\*?\}",
            save_align,
            s,
            flags=re.DOTALL,
        )
        s = re.sub(
            r"@@DISPLAYBLOCK(\d+)@@(?:\s*@@DISPLAYBLOCK\d+@@)+",
            lambda m: _merge_display_run(m.group(0), display_blocks),
            s,
        )

        cleaned_lines: list[str] = []
        symbol = "\\" + spec.stray_dollar_symbol
        for line in s.splitlines():
            if line.count("$") % 2 != 0:
                if spec.stray_dollar_symbol:
                    line = re.sub(
                        r"(?<!\$)\$(?!\$)(?=[0-9A-Za-z_])",
                        lambda _: symbol + "_",
                        line,
                    )
                    line = re.sub(r"(?<!\$)\$(?!\$)", lambda _: symbol + " ", line)
                else:
                    line = re.sub(r"(?<!\$)\$(?!\$)", "", line, count=1)
            cleaned_lines.append(line)
        s = "\n".join(cleaned_lines)

        inline_blocks: list[str] = []

        def save_inline(m: re.Match[str]) -> str:
            code = m.group(1)
            if PROSE_IN_MATH_RE.search(code) and "\\" not in code:
                return f" {code.replace(chr(34), '').strip()} "
            inline_blocks.append(code)
            return f"@@INLINEMATH{len(inline_blocks) - 1}@@"

        s = re.sub(r"\$([^$\n]+)\$", save_inline, s)

        s = re.sub(r"(?<![=\s])#", r"\#", s)
        s = re.sub(r"^\s*#", r"\#", s, flags=re.MULTILINE)
        s = re.sub(r"<(?!eq-|fig-|sec-)", r"\<", s)
        s = re.sub(r"^\s*/\s*", r"\/ ", s, flags=re.MULTILINE)
        s = s.replace("//", r"\/\/").replace("*/", "* /")
        s = re.sub(r"(?<![@\\])@(?=[\w])(?!@)", r"\@", s)
        s = re.sub(r"(?<!\\)~", r"\~", s)
        if spec.nonbreaking_hyphens:
            s = re.sub(
                r"(?<![@<])\b(?!(?:eq|fig|sec)\b)([a-zA-Z]+)-([a-zA-Z]+)",
                "\\1\u2011\\2",
                s,
            )

        s = re.sub(r"^(\s*)\*(?=\d+\.|EXERCISES)", r"\1\\*", s, flags=re.MULTILINE)
        s = re.sub(
            r"\*\*((?:(?!\n\n|@@DISPLAYBLOCK|@@FN)[^\*])+?)\*\*", r"#strong[\1]", s
        )
        s = re.sub(
            r"(?<![\\\*])\*((?:(?!\n\n|@@DISPLAYBLOCK|@@FN)[^\*])+?)\*(?!\*)",
            r"#emph[\1]",
            s,
        )
        s = re.sub(r"(?<!\\)\*", r"\\*", s)
        s = re.sub(r"(#emph\[[^\]]+\])(?=\[)", r"\1 ", s)
        s = re.sub(r"(?<!\\)_", r"\\_", s)
        s = re.sub(r"(?<!\\)\^", r"\\^", s)
        def repl_img(m: re.Match[str]) -> str:
            path = m.group(2).replace(r"\_", "_")
            width_str = "width: 45%"
            for candidate_dir in (Path("output/bourbaki"), Path("output/klein"), Path("output/fermat"), Path("output/kashiwara"), Path(".")):
                local_f = candidate_dir / path
                if local_f.with_suffix(".typ").exists():
                    typ_path = Path(path).with_suffix(".typ").as_posix()
                    include = f"#align(center)[#include \"{typ_path}\"]"
                    if spec.paginate_like_source:
                        fig = Path(path).stem.removeprefix("fig_")
                        include = (
                            f"#src-fig(\"{fig}\")\n{include}\n"
                            f"#set par(leading: fit-fig-leading(\"{fig}\"), spacing: fit-fig-leading(\"{fig}\"))"
                        )
                    return f"\n\n{include}\n\n"
                if local_f.exists():
                    try:
                        with Image.open(local_f) as im_obj:
                            pw, _ = im_obj.size
                            pt_w = min(360, max(110, round(pw / 300 * 72)))
                            width_str = f"width: {pt_w}pt"
                            break
                    except Exception:
                        pass
            return f"\n\n#align(center)[#image(\"{path}\", {width_str})]\n\n"
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl_img, s)
        s = s.replace(r"\cdots", "...").replace(r"\ldots", "...")
        s = re.sub(
            r"^\s*□\s*$",
            r"#v(-0.35em, weak: true)\n#align(right)[$square.stroked$]",
            s,
            flags=re.MULTILINE,
        )
        s = re.sub(r"[ \t]*□", r"#qed", s)
        s = re.sub(r"(\n\n)(?=#strong\[)", r"\1#thm-break\n", s)
        s = re.sub(r"(\n\n)(?=#emph\[Proof)", r"\1#sub-break\n", s)
        s = re.sub(
            r"(\n\n)(?=\((?:[1-9]\d?|[ivx]{1,4}|[1-9]-[1-9])\)\s+)",
            r"\1#item-break\n",
            s,
        )

        s = re.sub(r"(@@INLINEMATH\d+@@)\s+([.,;:?!\)])", r"\1\2", s)
        s = re.sub(r"(\()\s+(@@INLINEMATH\d+@@)", r"\1\2", s)
        converted = convert_math_batch(
            [(code, False) for code in inline_blocks]
            + [(body, True) for body, _ in display_blocks]
        )
        inline_typst = [
            _normalize_typst_differentials(t) for t in converted[: len(inline_blocks)]
        ]
        display_typst = [
            _normalize_typst_differentials(t) for t in converted[len(inline_blocks) :]
        ]
        s = re.sub(
            r"@@INLINEMATH(\d+)@@", lambda m: f"${inline_typst[int(m.group(1))]}$", s
        )
        s = re.sub(
            r"@@DISPLAYBLOCK(\d+)@@",
            lambda m: (
                f"\n$ {display_typst[int(m.group(1))]} $ "
                f"{display_blocks[int(m.group(1))][1]}\n"
            ),
            s,
        )
        indent = self.composition.language.first_line_indent
        s = re.sub(
            r"(\n\$ [^\n]*(?:\n[^\n$]*)*?\.\s*\$ (?:<eq-[^>]+>)?\n)\n+"
            r"(?=(?!Then\b|Where\b|Here\b|Hence\b|Thus\b|Indeed\b)[A-Z“\"])",
            rf"\1\n#h({indent});",
            s,
        )
        s = re.sub(r"(#(?:strong|emph)\[[^\]]+\])(?=\()", r"\1\\", s)
        s = re.sub(r"@@FIGBLOCK(\d+)@@", lambda m: fig_blocks[int(m.group(1))], s)
        s = re.sub(r"@@FNSTART@@(.*?)@@FNEND@@", r"#footnote[\1]", s)
        s = re.sub(r'delim:\s*"\|\|"', 'delim: "|"', s)
        s = s.replace("planck.reduce", "planck")
        s = s.replace("times.circle", r"\u{2297}")
        s = s.replace("plus.circle", r"\u{2295}")
        s = s.replace("angle.l", "chevron.l")
        s = s.replace("angle.r", "chevron.r")
        s = re.sub(r"\bneq\b", "!=", s)
        s = re.sub(r"\bprod(?=[^a-zA-Z]|$)", "product", s)
        s = re.sub(r"\bs\s*u\s*b\s*s\s*t\s*a\s*c\s*k\b", "", s)
        s = re.sub(r"o\s+p\s+e\s+r\s+a\s+t\s+o\s+r\s+n\s+a\s+m\s+e\s*\(\s*([a-zA-Z]+)\s*\)", r'op("\1")', s)
        s = re.sub(r"t\s+e\s+x\s+t\s*\(\s*(\"[^\"]*\")\s*\)", r"upright(\1)", s)
        s = re.sub(r"(?<=[(\s])\^([a-zA-Z0-9]+)", r'""^\1', s)
        s = re.sub(r"(?<=[(\s])_([a-zA-Z0-9]+)", r'""_\1', s)
        s = _fix_typst_single_arg_frac(s)
        if spec.paginate_like_source:
            s = re.sub(
                r"(?:#h\([^)]*\);)?@@SRCPAGE(\d+)@@",
                r"#src-page(\1)\n#set text(size: fit-size(\1))\n"
                r"#set par(leading: fit-leading(\1, 0), spacing: fit-leading(\1, 0))",
                s,
            )
            s = re.sub(r"@@SRCTOP(\d+)@@", r"#src-top(\1);", s)
            s = re.sub(r"@@SRCEND(\d+)@@", r"#src-end(\1);", s)
            s = s.replace("@@JUSTIFYEND@@", "#linebreak(justify: true)")
            s = s.replace("@@BR@@", "#linebreak(justify: true);")
            s = s.replace("@@HY@@", "-#linebreak(justify: true);")
            s = re.sub(r"(?:#h\([^)]*\);)?@@NOINDENT@@\s*", "#src-cont;", s)
        return s

    def _stitch_by_source_page(self, pages_data: list[PageParts], fig_dir: Path) -> str:
        """Keep each source page's text on its own output page, marking split paragraphs."""
        pages: list[tuple[int, str]] = []
        for pno, text, top_figs, bot_figs in pages_data:
            body = text.strip()
            if not body and not top_figs and not bot_figs:
                continue
            if self.spec.source_line_breaks is not None:
                body = self.spec.source_line_breaks(pno, body, self._out_dir)
            continues = bool(pages) and bool(body) and (
                body[0].islower()
                or (not ends_complete_paragraph(pages[-1][1]) and not starts_new_block(body))
            )
            prev_last_line = pages[-1][1].rstrip().splitlines()[-1] if pages else ""
            justify = self.spec.justify_page_end is None or self.spec.justify_page_end(pages[-1][1] if pages else "")
            if continues and justify and not prev_last_line.lstrip().startswith(("![", "$", "#")):
                prev_pno, prev_page = pages[-1]
                pages[-1] = (prev_pno, prev_page.rstrip() + " @@JUSTIFYEND@@")
            page = self.render_figure_group(top_figs, fig_dir)
            page += f"@@NOINDENT@@{body}" if continues else body
            page += self.render_figure_group(bot_figs, fig_dir)
            pages.append((pno, page))
        return "\n\n".join(
            f"@@SRCPAGE{pno}@@\n\n{_mark_page_ends(page, pno)}" for pno, page in pages
        )

    def format_index(self, md_dir: Path, start_p: int, end_p: int) -> str:
        title = self.spec.index_title
        entries: list[str] = []
        for pno in range(start_p, end_p + 1):
            p_file = md_dir / f"p_{pno:03d}.md"
            if not p_file.exists():
                continue
            for raw_line in p_file.read_text(encoding="utf-8").splitlines():
                lt = raw_line.strip()
                if not lt or re.match(rf"^(?:#+\s*)?{title}$", lt, re.IGNORECASE):
                    continue
                if re.match(
                    rf"^\d{{1,3}}\s+{title}$|^{title}\s+\d{{1,3}}$|^\d{{1,3}}$",
                    lt,
                    re.IGNORECASE,
                ):
                    continue
                line_clean = lt.replace('"', "''").replace("#", r"\#")
                line_clean = re.sub(r"\*([^\*]+)\*", r"#emph[\1]", line_clean)
                line_clean = clean_margin_and_inline_math(line_clean)
                is_sub = self.spec.index_subentries and (
                    raw_line.startswith("  ")
                    or (lt[0].islower() and not lt.startswith(("i.e.", "e.g.")))
                )
                entries.append(f"#h(1.2em){line_clean}" if is_sub else line_clean)

        joined = "\n\n".join(entries)
        return (
            f"\n= {title}\n\n"
            "#columns(2, gutter: 1.8em)[\n"
            "  #set text(size: 9pt)\n"
            "  #set par(first-line-indent: 0pt, hanging-indent: 1.2em, leading: 0.52em, spacing: 0.48em, justify: false)\n"
            f"  {joined}\n"
            "]\n"
        )

    def _read_page(self, md_dir: Path, pno: int) -> str | None:
        p_file = md_dir / f"p_{pno:03d}.md"
        if not p_file.exists():
            return None
        return p_file.read_text(encoding="utf-8").strip()

    def _single_page_section(
        self, md_dir: Path, pno: int, title: str
    ) -> tuple[str, str] | None:
        raw = self._read_page(md_dir, pno)
        if raw is None:
            return None
        body, _, _ = self.extract_page_parts(raw, pno)
        body = re.sub(
            rf"^(?:#+\s*)?{title}\s*\n+", "", body, flags=re.IGNORECASE
        ).strip()
        return (
            body,
            f"\n= {title}\n\n{self.format_typst(body)}\n#pagebreak(weak: true)\n",
        )

    def _prebuilt_chapter(self, out_dir: Path, chap: ChapterSpec) -> str | None:
        path = out_dir / chap.typst_file
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        for old, new in self.spec.prebuilt_fixups:
            text = text.replace(old, new)
        if self.spec.figure_dir != "figures":
            text = text.replace('image("figures/', f'image("{self.spec.figure_dir}/')
        text = re.sub(r"<eq-(\d+)>", rf"<eq-{chap.number}-\1>", text)
        return re.sub(r"@eq-(\d+)", rf"@eq-{chap.number}-\1", text)

    def render(self, out_dir: Path) -> RenderedMonograph:
        """Build the Markdown and Typst sources from the page files in `out_dir`."""
        spec = self.spec
        out_dir = Path(out_dir)
        md_dir = out_dir / spec.markdown_dir
        fig_dir = out_dir / spec.figure_dir
        self._out_dir = out_dir
        self._seen_sections = set()

        md_sections: list[str] = [
            (
                "---\n"
                f'title: "{spec.title}"\n'
                f'author: "{spec.author}"\n'
                f'translator: "{spec.translator}"\n'
                f'editor: "{spec.editor}"\n'
                f'publisher: "{spec.publisher}"\n'
                f"year: {spec.year}\n"
                "---\n\n"
                f"# {spec.title}\n\n"
                f"**{spec.author}**  \n"
                f"**{spec.publisher}**\n"
            )
        ]
        typst_sections: list[str] = [
            self.build_typst_preamble(),
            self.build_typst_title_page(),
        ]

        if spec.preface_page is not None:
            preface = self._single_page_section(md_dir, spec.preface_page, "Preface")
            if preface:
                md_sections.append(f"\n## Preface\n\n{preface[0]}\n")
                typst_sections.append(preface[1])

        for chap in spec.chapters:
            if chap.typst_file:
                prebuilt = self._prebuilt_chapter(out_dir, chap)
                if prebuilt is not None:
                    typst_sections += [prebuilt, "\n#pagebreak(weak: true)\n"]
                continue
            pages_data: list[PageParts] = []
            ch_md_pages: list[str] = [f"\n# Chapter {chap.number}: {chap.title}\n"]
            for pno in range(chap.start_page, chap.end_page + 1):
                raw_text = self._read_page(md_dir, pno)
                if (
                    raw_text is None
                    or len(raw_text) < spec.min_page_chars
                    or any(marker in raw_text for marker in spec.skip_page_markers)
                ):
                    continue
                p_body, top_f, bot_f = self.extract_page_parts(raw_text, pno)
                pages_data.append((pno, p_body, top_f, bot_f))
                md_page = p_body
                for fid, cap in top_f:
                    asset = self._resolve_figure_asset(fig_dir, fid)
                    if asset is not None:
                        md_page = (
                            f"![{cap}]({spec.figure_dir}/{asset.name})\n\n" + md_page
                        )
                for fid, cap in bot_f:
                    asset = self._resolve_figure_asset(fig_dir, fid)
                    if asset is not None:
                        md_page += f"\n\n![{cap}]({spec.figure_dir}/{asset.name})"
                ch_md_pages.append(md_page)

            md_sections.append("\n\n".join(ch_md_pages))
            title = clean_margin_and_inline_math(chap.title)
            label = (
                chap.label
                if chap.label is not None
                else spec.chapter_label.format(number=chap.number)
            )
            if label:
                number = label.split()[-1]
                heading = (
                    f'#chapter-label.update("{label}")\n'
                    f'#heading(level: 1, numbering: _ => "{number}")[{title}]\n'
                    "#chapter-label.update(none)"
                )
            elif spec.chapter_label or any(title.startswith(k) for k in ("人名索引", "专业名词索引", "译后记", "附录", "Index", "Appendix")):
                heading = f"= {title}"
            else:
                heading = "= " + spec.chapter_heading.format(
                    number=chap.number, title=title
                )
            stitched = self.stitch_chapter(pages_data, fig_dir)
            formatted = self.format_typst(stitched)
            if "索引" in title or "Index" in title:
                formatted = re.sub(r"#src-page\((\d+)\)", r"#src-top(\1);", formatted)
                formatted = (
                    "#columns(2, gutter: 1.8em)[\n"
                    "  #set text(size: 9pt)\n"
                    "  #set par(first-line-indent: 0pt, hanging-indent: 1.2em, leading: 0.52em, spacing: 0.48em, justify: false)\n"
                    f"  {formatted}\n"
                    "]"
                )
            typst_sections.append(f"\n{heading}\n\n" + formatted)
            typst_sections.append("\n#pagebreak(weak: true)\n")

        if spec.problems_pages is not None:
            prob_pages: list[PageParts] = []
            prob_md: list[str] = ["\n# Problems\n"]
            for pno in range(spec.problems_pages[0], spec.problems_pages[1] + 1):
                raw_text = self._read_page(md_dir, pno)
                if raw_text is None:
                    continue
                p_body, top_f, bot_f = self.extract_page_parts(raw_text, pno)
                p_body = re.sub(
                    r"^(?:#+\s*)?Problems\s*\n+", "", p_body, flags=re.IGNORECASE
                ).strip()
                prob_pages.append((pno, p_body, top_f, bot_f))
                prob_md.append(p_body)
            if prob_pages:
                md_sections.append("\n\n".join(prob_md))
                typst_sections.append(
                    "\n= Problems\n\n"
                    + self.format_typst(self.stitch_chapter(prob_pages, fig_dir))
                    + "\n#pagebreak(weak: true)\n"
                )

        if spec.references_page is not None:
            refs = self._single_page_section(md_dir, spec.references_page, "References")
            if refs:
                md_sections.append(f"\n# References\n\n{refs[0]}\n")
                typst_sections.append(refs[1])

        if spec.index_pages is not None:
            typst_sections.append(self.format_index(md_dir, *spec.index_pages))

        return RenderedMonograph(
            markdown="\n\n".join(md_sections), typst="\n".join(typst_sections)
        )

    def _write(self, out_dir: Path, ext: str, content: str | None = None) -> Path:
        path = out_dir / f"{self.spec.slug}.{ext}"
        if content is not None:
            _ = path.write_text(content, encoding="utf-8")
        return path

    def _alias(self, path: Path) -> None:
        book = path.with_name(f"book{path.suffix}")
        if self.spec.book_aliases and path != book:
            _ = shutil.copy2(path, book)

    def build_all(self, out_dir: Path) -> MonographOutputs:
        """Write Markdown and Typst, then run Pandoc for LaTeX and Typst for PDF."""
        out_dir = Path(out_dir)
        rendered = self.render(out_dir)
        md_out = self._write(out_dir, "md", rendered.markdown)
        typ_out = self._write(out_dir, "typ", rendered.typst)
        tex_out = self._write(out_dir, "tex")
        pdf_out = self._write(out_dir, "pdf")
        _ = subprocess.run(
            [
                "pandoc",
                str(md_out),
                "-f",
                "markdown+tex_math_dollars+raw_tex",
                "-t",
                "latex",
                "-s",
                "--top-level-division=chapter",
                "-V",
                "documentclass=book",
                "-V",
                f"geometry:{self.composition.publisher.pandoc_geometry}",
                "-o",
                str(tex_out),
            ],
            check=True,
        )
        compile_typst(typ_out, pdf_out)
        for path in (md_out, typ_out, tex_out, pdf_out):
            self._alias(path)
        with pymupdf.open(str(pdf_out)) as doc:
            total_pages = len(doc)
        return MonographOutputs(
            markdown_path=md_out,
            latex_path=tex_out,
            typst_path=typ_out,
            pdf_path=pdf_out,
            total_pages=total_pages,
        )


def compile_typst(typ_path: Path, pdf_path: Path) -> None:
    """Compile a Typst source to PDF with local Typst, mise, or Nix."""
    font_args = ["--font-path", str(REPO_FONTS_DIR)]
    if shutil.which("typst"):
        res = subprocess.run(
            ["typst", "compile", *font_args, str(typ_path), str(pdf_path)], check=False
        )
        if res.returncode == 0:
            return
    if shutil.which("mise"):
        res = subprocess.run(
            ["mise", "exec", "--", "typst", "compile", *font_args, str(typ_path), str(pdf_path)],
            check=False,
        )
        if res.returncode == 0:
            return
    _ = subprocess.run(
        [
            "nix",
            "shell",
            "nixpkgs#typst",
            "--command",
            "typst",
            "compile",
            *font_args,
            str(typ_path),
            str(pdf_path),
        ],
        check=True,
    )
