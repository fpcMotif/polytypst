"""Universal Academic Monograph Compiler for TeX-compatible Markdown, XeLaTeX, Typst, and PDF.

A book supplies a declarative `MonographSpec`. `PageCleaner` cleans each page.
`MonographCompiler` joins the clean pages into chapters and places the figures.
It converts LaTeX math to Typst and writes the Typst preamble. It also runs
Pandoc and Typst.
"""

import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from PIL import Image

from ..ocr.lines import DEFAULT_OCR_LANGUAGES
from ..ocr.transcripts import TranscriptStore
from .page_cleaner import Figure, PageCleaner
from .presets import CompositionConfig, resolve_composition
from .typst_math import (
    clean_margin_and_inline_math,
    convert_math_batch,
    finish_typst_math,
    normalize_typst_differentials,
)

REPO_FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"
MONOGRAPH_FORMATS = frozenset({"tex", "pdf"})

PageParts = tuple[int, str, list[Figure], list[Figure]]
Rewrite = tuple[str, str]
OPERATOR_NAMES = (
    "Ad", "ad", "Aut", "ch", "Cl", "Coker", "Der", "End", "Ext", "Frob", "Gal", "GL",
    "Hom", "Id", "id", "Im", "Ker", "Mor", "Ob", "ord", "Proj", "S.S.", "SL", "Spec",
    "Spm", "Tr",
)
GENERIC_PRE_MATH_REWRITES: tuple[Rewrite, ...] = (
    (r"plus\.circle", r"\\u{2295}"),
    (r"times\.circle", r"\\u{2297}"),
    (rf"\\text\{{({'|'.join(map(re.escape, OPERATOR_NAMES))})\}}", r"\\operatorname{\1}"),
)


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
    figure_pages: frozenset[int] = frozenset()
    min_page_chars: int = 1
    skip_page_markers: tuple[str, ...] = ("1.1.1.1.1", "musical compositions")
    folio_pattern: str = r"^(?:\d{1,3}|[ivxlcdm]+)$"
    running_header_regexes: tuple[str, ...] = ()
    header_zone_lines: int | None = 2
    drop_line_regexes: tuple[str, ...] = ()
    normalize_headings: bool = True
    theorem_heads_upper: bool = False
    footnote_style: Literal["", "superscript", "paren", "symbol"] = ""
    footnote_marks: tuple[str, ...] = ()
    footnote_numbering: str = "1"
    footnote_reset: Literal["page", "chapter", "book"] = "page"
    equation_numbering: Literal["section", "page", "none"] = "section"
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
    latex_preamble: str = ""
    book_aliases: bool = True
    pdf_name_markers: tuple[str, ...] = ()
    pdf_page_count: int | None = None
    source_pdf: str = ""
    ocr_prompt: str | None = None
    ocr_languages: tuple[str, ...] = DEFAULT_OCR_LANGUAGES


@dataclass(frozen=True)
class MonographOutputs:
    """The files one build wrote. A format that was not requested has no path."""

    markdown_path: Path
    typst_path: Path
    latex_path: Path | None = None
    pdf_path: Path | None = None
    epub_path: Path | None = None
    total_pages: int = 0


def alias_as_book(path: Path) -> None:
    """Copy `path` to `book<suffix>` beside it, the stable name the web exporter reads."""
    shutil.copy2(path, path.with_name(f"book{path.suffix}"))


def run_formats(writers: Mapping[str, tuple[Path, Callable[[], object]]], formats: frozenset[str]) -> dict[str, Path]:
    """Run the writer of each requested format in parallel; each writer makes one file. Returns those files by format."""
    chosen = {name: writers[name] for name in formats}
    with ThreadPoolExecutor() as pool:
        for future in [pool.submit(write) for _, write in chosen.values()]:
            future.result()
    return {name: path for name, (path, _) in chosen.items()}


def build_outputs(markdown: Path, typst: Path, made: Mapping[str, Path]) -> MonographOutputs:
    """The outputs record of a build that wrote `markdown`, `typst` and the `made` formats."""
    pages = 0
    if "pdf" in made:
        import pymupdf

        with pymupdf.open(made["pdf"]) as doc:
            pages = len(doc)
    return MonographOutputs(
        markdown, typst, made.get("tex"), made.get("pdf"), made.get("epub"), pages
    )


@dataclass(frozen=True)
class RenderedMonograph:
    markdown: str
    typst: str


_CJK_CHARS = "　-鿿가-힯＀-￯"
_UNBREAKABLE_RUN_RE = re.compile(rf"[{_CJK_CHARS}]|[^\s{_CJK_CHARS}]+")


def escape_typst_text(text: str) -> str:
    """Escape plain text, such as a title from a file name, for Typst markup."""
    s = re.sub(r"([\\#$*_\[\]<>@~^`/])", r"\\\1", text)
    return re.sub(r"^(\s*)([=+\-]|\d+\.)", r"\1\\\2", s)


def _balanced_backticks(para: str) -> bool:
    """True when every backtick run opens and closes Typst raw text: runs of 1-3 that pair up."""
    runs = [len(r) for r in re.findall(r"`+", para)]
    return all(n <= 3 and runs.count(n) % 2 == 0 for n in runs)


def escape_quoted(text: str) -> str:
    """Escape text for a double-quoted Typst or YAML string."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def running_header_regexes(pattern: str) -> tuple[str, ...]:
    """Line regexes for running headers named by an alternation of titles."""
    prefix = r"(?:[0-9A-Z]{1,2}\.(?:\d{1,2}\.?)?\s+)?"
    return (
        rf"^(?:#+\s*)?{prefix}(?:{pattern})(?:\s+\d{{1,3}})?$",
        rf"^\d{{1,3}}\s+{prefix}(?:{pattern})$",
    )


def adhoc_spec(
    pdf_path: Path,
    total_pages: int,
    publisher_key: str = "cambridge",
    lang: str = "en",
    domain: str = "math",
) -> MonographSpec:
    """A one-chapter spec for a source scan that no book in `src/<key>/` describes."""
    comp = resolve_composition(publisher=publisher_key, lang=lang, domain=domain)
    slug = re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_") or "book"
    return MonographSpec(
        slug=slug,
        title=pdf_path.stem,
        author="",
        publisher="",
        series="",
        publisher_key=comp.publisher.key,
        lang=comp.language.code,
        domain=comp.domain.key,
        chapters=[ChapterSpec(1, escape_typst_text(pdf_path.stem), 1, total_pages)],
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
_UNESCAPED_DOLLAR_RE = re.compile(r"(?<!\\)\$")
_LATEX_GROUP_SUPERSCRIPT_RE = re.compile(r"\{\}\^(\\[A-Za-z]+|[A-Za-z0-9])")
_LATEX_ACCENT_SUPERSCRIPT_RE = re.compile(
    r"\{\}\^(\\(?:bar|tilde|hat|vec|dot|ddot|overline))(\{[^{}]*\})"
)
_LATEX_SUPERSCRIPT_SUBSCRIPT_RE = re.compile(r"(\^(?:\\[A-Za-z]+|\{[^{}]*\}))_")
_LATEX_SPACED_RIGHT_RE = re.compile(r"\\(\s+)?[Rr]ight(?![a-zA-Z])")
_LATEX_CARET_CONTROL_RE = re.compile(r"\^\\\s")
_LATEX_TRAILING_CARET_RE = re.compile(r"\^(?=\s*[\$}\)\],])")
_LATEX_UNICODE_GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
    "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
    "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi", "ο": "omicron",
    "π": "pi", "ρ": "rho", "σ": "sigma", "τ": "tau", "υ": "upsilon",
    "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
    "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta", "Λ": "Lambda", "Ξ": "Xi",
    "Π": "Pi", "Σ": "Sigma", "Υ": "Upsilon", "Φ": "Phi", "Ψ": "Psi", "Ω": "Omega",
}
_LATEX_UNICODE_GREEK_RE = re.compile(r"\\([" + "".join(_LATEX_UNICODE_GREEK) + r"])")
_LATEX_SCRIPT_TWO_ARG_RE = re.compile(
    r"([_^])(\\[dt]?frac|\\binom)(\{[^{}]*\})(\{[^{}]*\})"
)
_LATEX_SCRIPT_EMPTY_GROUP_RE = re.compile(r"([_^])(\\[A-Za-z]+)\{\}([_^])")
_LATEX_SCRIPT_MACRO_RE = re.compile(
    r"([_^])(\\(?!frac|dfrac|tfrac|binom)[A-Za-z]+)(\{[^{}]*\})"
)
_LATEX_SCRIPT_MACRO_GROUP_RE = re.compile(r"([_^])(\\[A-Za-z]+)([_^])")
_LATEX_SCRIPT_SEPARATION_RE = re.compile(r"(\^\{[^{}]*\}|\^[A-Za-z0-9])([_^])")
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




def latex_safe_markdown(text: str) -> str:
    """Repair OCR math that LaTeX rejects but Typst tolerates."""
    text = _LATEX_ACCENT_SUPERSCRIPT_RE.sub(r"{}^{\1\2}", text)
    text = _LATEX_UNICODE_GREEK_RE.sub(
        lambda m: "\\" + _LATEX_UNICODE_GREEK[m.group(1)], text
    )
    text = _LATEX_SCRIPT_TWO_ARG_RE.sub(r"\1{\2\3\4}", text)
    text = _LATEX_SCRIPT_EMPTY_GROUP_RE.sub(r"\1{\2}{}\3", text)
    text = _LATEX_SCRIPT_MACRO_RE.sub(r"\1{\2\3}", text)
    text = _LATEX_SCRIPT_MACRO_GROUP_RE.sub(r"\1{\2}\3", text)
    text = _LATEX_SCRIPT_SEPARATION_RE.sub(r"\1{}\2", text)
    text = _LATEX_SPACED_RIGHT_RE.sub(r"\\right", text)
    text = _LATEX_CARET_CONTROL_RE.sub(r"^\\", text)
    text = _LATEX_TRAILING_CARET_RE.sub("", text)
    return _LATEX_GROUP_SUPERSCRIPT_RE.sub(r"{}^{\1}", text)


def _split_trailing_note_block(text: str) -> tuple[str, str]:
    """Split a trailing reference/rule block off the prose that precedes it."""
    if not text.strip():
        return text, ""
    blocks = re.split(r"\n\s*\n", text.rstrip())
    if len(blocks) < 2:
        return text, ""
    tail = blocks[-1].strip()
    if not re.match(r"^(?:—|---|\d+\)\s)", tail):
        return text, ""
    return "\n\n".join(blocks[:-1]).rstrip(), blocks[-1].strip()


def _join_pages_across_math(pages: list[str]) -> list[str]:
    """Merge a page that opens inline math with the page that closes it."""
    merged: list[str] = []
    for page in pages:
        if (
            merged
            and len(_UNESCAPED_DOLLAR_RE.findall(merged[-1].rstrip())) % 2 == 1
            and page.lstrip().startswith("$")
            and not page.lstrip().startswith("$$")
        ):
            merged[-1] = merged[-1].rstrip() + " " + page.lstrip()[1:]
            continue
        merged.append(page)
    return merged


def join_cross_page_text(prev: str, curr_first: str) -> str:
    prev_r = prev.rstrip()
    curr_l = curr_first.lstrip()
    last_line = prev_r.splitlines()[-1].strip() if prev_r else ""
    if len(_UNESCAPED_DOLLAR_RE.findall(prev_r)) % 2 == 1 and curr_l.startswith("$") and not curr_l.startswith("$$"):
        return prev_r + " " + curr_l[1:]
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






FOOTNOTE_RE = re.compile(r"@@FNSTART@@(.*?)@@FNEND@@", re.DOTALL)
















def keep_notes_with_calls(block: str) -> str:
    """Typst places a note entry before orphan and widow control moves its call's line to the next page,
    so a paragraph that holds a note gives up that control. Source-page markers become set rules and stay unscoped."""
    if "@@FNSTART@@" not in block or "@@SRC" in block:
        return block
    return f"#[#set text(costs: (orphan: 0%, widow: 0%))\n{block}\n]"


def markdown_footnotes(s: str) -> str:
    return FOOTNOTE_RE.sub(r"^[\1]", s)


def running_footnotes(spec: MonographSpec) -> MonographSpec:
    return replace(spec, footnote_marks=(), footnote_numbering="1", footnote_reset="book")


def typst_footnote_rules(spec: MonographSpec) -> str:
    if not spec.footnote_style:
        return ""
    if spec.footnote_marks:
        marks = ", ".join(f'"{m}"' for m in spec.footnote_marks)
        numbering = f"n => ({marks},).at(n - 1, default: str(n))"
    else:
        numbering = f'"{spec.footnote_numbering}"'
    reset = {
        "page": "#set page(background: counter(footnote).update(0))\n",
        "chapter": "#show heading.where(level: 1): it => { counter(footnote).update(0); it }\n",
        "book": "",
    }[spec.footnote_reset]
    return f"#set footnote(numbering: {numbering})\n{reset}"


LATEX_FOOTNOTE_MARKS = {"*": "*", "**": "**", "***": "***", "†": r"\textdagger", "‡": r"\textdaggerdbl", "§": r"\textsection"}


def latex_footnote_header(spec: MonographSpec) -> str:
    """footmisc settings for the spec's marks. The book class already restarts notes at each chapter."""
    if not spec.footnote_style:
        return ""
    header = {
        "page": r"\usepackage[perpage]{footmisc}",
        "chapter": "",
        "book": r"\counterwithout{footnote}{chapter}",
    }[spec.footnote_reset]
    if spec.footnote_marks:
        marks = "".join(f"{{{LATEX_FOOTNOTE_MARKS[m]}}}" for m in spec.footnote_marks)
        header += (
            rf"\DefineFNsymbols{{original}}{{{marks}}}\setfnsymbol{{original}}"
            r"\renewcommand\thefootnote{\fnsymbol{footnote}}"
        )
    elif spec.footnote_numbering == "1)":
        header += r"\renewcommand\thefootnote{\arabic{footnote})}"
    return header


UNNUMBERED_CHAPTER_PREFIXES = (
    "人名索引",
    "专业名词索引",
    "译后记",
    "附录",
    "参考文献",
    "Index",
    "Appendix",
    "Bibliography",
    "References",
    "Solutions",
    "Historical Note",
)


def is_unnumbered_chapter(title: str) -> bool:
    return title.startswith(UNNUMBERED_CHAPTER_PREFIXES)
















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
    r"^(?:[+\-<>]|\\(?:times|cdot|le|ge|equiv|cong|approx|to|mapsto|longmapsto|Longleftrightarrow|Leftrightarrow)\b)"
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


class MonographCompiler:
    """Compiles transcribed Markdown pages and figures into Markdown, LaTeX, Typst, and PDF."""

    def __init__(self, spec: MonographSpec) -> None:
        self.spec: MonographSpec = spec
        self.composition: CompositionConfig = resolve_composition(
            publisher=spec.publisher_key,
            lang=spec.lang,
            domain=spec.domain,
        )
        self._out_dir: Path = Path()
        self.cleaner: PageCleaner = PageCleaner.for_spec(spec)

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
  title: "{escape_quoted(" — ".join(filter(None, (self.spec.title, self.spec.author))))}",
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
        #let chaps = query(heading.where(level: 1).before(here()))
        #let in-chapter = if chaps == () {{ heading.where(level: 2) }} else {{ heading.where(level: 2).after(chaps.last().location()) }}
        #let secs = query(in-chapter).filter(h => h.location().page() <= here().page())
        #let on-page = secs.filter(h => h.location().page() == here().page())
        #let title = if on-page != () {{ on-page.first().body }} else if secs != () {{ secs.last().body }} else if chaps != () {{ chaps.last().body }} else {{ "{escape_quoted(self.spec.title)}" }}
        #grid(
          columns: (1fr, auto),
          align(left)[#text(8.5pt, font: {font_expr}, style: "italic")[#title]],
          align(right)[#text(9.5pt, font: {font_expr})[#page-number]]
        )
      ] else [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = if chaps != () {{ chaps.last().body }} else {{ "{escape_quoted(self.spec.title)}" }}
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

#show math.equation: set text(font: ({", ".join(f'"{f}"' for f in (lang.math_font, *lang.font_stack[1:]))},))
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
#let display-break-after = ("=", "<", ">", "+", "−", "≤", "≥", "≠", "≈", "≡", "→", "∈", "⊂", "⊆")
#let display-pieces(body) = {{
  let kids = if body.has("children") {{ body.children }} else {{ (body,) }}
  if kids.any(k => k.func() == linebreak) {{
    return ()
  }}
  let pieces = ((),)
  for k in kids {{
    pieces.at(-1).push(k)
    if k.has("text") and k.text in display-break-after {{
      pieces.push(())
    }}
  }}
  pieces.filter(p => p.len() > 0).map(p => p.join())
}}
#let display-rows(body) = {{
  let kids = if body.has("children") {{ body.children }} else {{ (body,) }}
  let rows = ((),)
  for k in kids {{
    if k.func() == linebreak {{
      rows.push(())
    }} else if repr(k.func()) != "align-point" {{
      rows.at(-1).push(k)
    }}
  }}
  rows.filter(r => r.any(k => k.func() != [ ].func())).map(r => r.join())
}}
#let fit-display(body, avail) = {{
  let eq = math.equation(body, block: true, numbering: none)
  let w = measure(eq).width
  let rows = display-rows(body)
  if w > avail and avail / w < 0.8 and rows.len() > 1 {{
    return stack(spacing: 0.9em, ..rows.map(r => align(center, fit-display(r, avail))))
  }}
  let pieces = display-pieces(body)
  let breakable = pieces.len() > 1 and pieces.all(p => measure(math.equation(math.display(p), block: false)).width <= avail)
  if w <= avail or w == 0pt {{
    eq
  }} else if avail / w >= 0.8 or not breakable {{
    scale(x: avail / w * 100%, y: avail / w * 100%, reflow: true, eq)
  }} else {{
    block(width: avail, {{
      set align(center)
      set par(justify: false, first-line-indent: 0pt)
      math.equation(math.display(body), block: false)
    }})
  }}
}}
#show math.equation.where(block: true): it => {{
  if it.numbering == none {{
    return it
  }}
  layout(size => {{
    if not it.has("label") {{
      align(center, fit-display(it.body, size.width))
    }} else {{
      let lbl = str(it.label).trim("eq-", at: start)
      let parts = lbl.split("-")
      let disp = if parts.len() >= 2 {{ parts.at(-2) + "." + parts.last() }} else {{ parts.last() }}
      let num-box = [(#disp)]
      let fitted = fit-display(it.body, size.width - measure(num-box).width - 12pt)
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
        series = (
            f'#text(10pt, tracking: 0.14em, font: {font_expr})[#smallcaps("{self.spec.series}")]\n  #v(3em)'
            if self.spec.series
            else ""
        )
        author = (
            f'#v(2.2em)\n  #text(14pt, weight: "bold", font: {font_expr})[#smallcaps("{self.spec.author}")]'
            if self.spec.author
            else ""
        )
        cities = (
            f'\n  #v(0.4em)\n  #text(8.5pt, fill: luma(90), font: {font_expr})[{pub.cities_line}]'
            if self.spec.publisher == pub.imprint_name
            else ""
        )
        imprint = (
            f"""#v(5em)
  #line(length: 35%, stroke: 0.4pt + luma(140))
  #v(1.2em)
  #text(11pt, weight: "bold", tracking: 0.12em, font: {font_expr})[{self.spec.publisher.upper()}]{cities}"""
            if self.spec.publisher
            else ""
        )
        title = self.spec.title.upper()
        return f"""
#align(center + horizon)[
  {series}
  #layout(size => {{
    let longest = measure(text(26pt, weight: "bold", font: {font_expr})[{escape_typst_text(max(_UNBREAKABLE_RUN_RE.findall(title) or [""], key=len))}]).width
    let fit = calc.min(1, size.width / calc.max(longest, 1pt))
    par(justify: false)[#text(26pt * fit, weight: "bold", hyphenate: false, font: {font_expr})[{escape_typst_text(title)}]]
  }})
  {author}
  {credits}
  {imprint}
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
            prose, note_block = _split_trailing_note_block(acc)
            continues_prev = (
                not ends_complete_paragraph(prose) and not starts_new_block(text)
            ) or starts_lower

            if not acc:
                acc = self.render_figure_group(all_top_figs, fig_dir) + text
            elif continues_prev:
                first_p, rest_p = split_first_paragraph(text)
                acc = join_cross_page_text(prose, first_p)
                if all_top_figs:
                    acc += self.render_figure_group(all_top_figs, fig_dir)
                if note_block:
                    acc += "\n\n" + note_block
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
        for pattern, repl in (*GENERIC_PRE_MATH_REWRITES, *spec.pre_math_rewrites):
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
            if len(_UNESCAPED_DOLLAR_RE.findall(line)) % 2 != 0:
                if spec.stray_dollar_symbol:
                    line = re.sub(
                        r"(?<![\\$])\$(?!\$)(?=[0-9A-Za-z_])",
                        lambda _: symbol + "_",
                        line,
                    )
                    line = re.sub(r"(?<![\\$])\$(?!\$)", lambda _: symbol + " ", line)
                else:
                    line = re.sub(r"(?<![\\$])\$(?!\$)", "", line, count=1)
            cleaned_lines.append(line)
        s = "\n".join(cleaned_lines)

        inline_blocks: list[str] = []

        def save_inline(m: re.Match[str]) -> str:
            code = m.group(1)
            if PROSE_IN_MATH_RE.search(code) and "\\" not in code:
                return f" {code.replace(chr(34), '').strip()} "
            inline_blocks.append(code)
            return f"@@INLINEMATH{len(inline_blocks) - 1}@@"

        s = re.sub(r"(?<!\\)\$((?:[^$\n\\]|\\.)+)\$", save_inline, s)
        s = "\n\n".join(
            para if _balanced_backticks(para) else para.replace("`", r"\`")
            for para in s.split("\n\n")
        )

        s = re.sub(r"^\s*#", r"\#", s, flags=re.MULTILINE)
        s = re.sub(r"(?<![=\\])#", r"\#", s)
        s = re.sub(r"<(?!eq-|fig-|sec-)", r"\<", s)
        s = re.sub(r"^\s*/\s*", r"\/ ", s, flags=re.MULTILINE)
        s = s.replace("//", r"\/\/").replace("*/", "* /")
        s = re.sub(r"(?<![@\\])@(?=[\w])(?!@)", r"\@", s)
        s = re.sub(r"(?<!\\)~", r"\~", s)
        images: list[str] = []

        def save_image(m: re.Match[str]) -> str:
            images.append(m.group(0))
            return f"@@IMAGE{len(images) - 1}@@"

        s = re.sub(r"!\[[^\]]*\]\([^)]+\)", save_image, s)
        if spec.nonbreaking_hyphens:
            s = re.sub(
                r"(?<![@<])\b(?!(?:eq|fig|sec)\b)([a-zA-Z]+)-([a-zA-Z]+)",
                "\\1\u2011\\2",
                s,
            )

        s = re.sub(r"^(\d+)\.(?= \S.{99,})", r"\1\\.", s, flags=re.MULTILINE)
        s = re.sub(r"(?<!\\)([\[\]])", r"\\\1", s)
        s = re.sub(r"^\*\*(\d+)\*\.\*\*", r"#strong[\1\\*.]", s, flags=re.MULTILINE)
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
        s = re.sub(r"(#emph\[[^\]]+\])(?=\\?\[)", r"\1 ", s)
        s = re.sub(r"(?<!\\)_", r"\\_", s)
        s = re.sub(r"(?<!\\)\^", r"\\^", s)
        def repl_img(m: re.Match[str]) -> str:
            path = m.group(2).replace(r"\_", "_")
            width_str = "width: 45%"
            for candidate_dir in (Path("output/bourbaki"), Path("output/klein"), Path("output/fermat"), Path("output/kashiwara"), Path("output/kenji-alg"), Path(".")):
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
                    except OSError:
                        continue
            else:
                print(f"warning: image {path!r} not found, omitted", file=sys.stderr)
                return "\n\n"
            return f"\n\n#align(center)[#image(\"{path}\", {width_str})]\n\n"
        s = re.sub(r"@@IMAGE(\d+)@@", lambda m: images[int(m.group(1))], s)
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
            normalize_typst_differentials(t) for t in converted[: len(inline_blocks)]
        ]
        display_typst = [
            normalize_typst_differentials(t) for t in converted[len(inline_blocks) :]
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
        s = "\n\n".join(map(keep_notes_with_calls, s.split("\n\n")))
        s = FOOTNOTE_RE.sub(r"#footnote[\1]", s)
        s = finish_typst_math(s)
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
        store = TranscriptStore(md_dir)
        for pno in range(start_p, end_p + 1):
            text = store.text(pno)
            if text is None:
                continue
            for raw_line in text.splitlines():
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
        text = TranscriptStore(md_dir).text(pno)
        return None if text is None else text.strip()

    def _single_page_section(
        self, md_dir: Path, pno: int, title: str
    ) -> tuple[str, str] | None:
        raw = self._read_page(md_dir, pno)
        if raw is None:
            return None
        body, _, _ = self.cleaner.clean(raw, pno)
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
        self.cleaner = PageCleaner.for_spec(spec, out_dir)

        md_sections: list[str] = [
            (
                "---\n"
                f'title: "{escape_quoted(spec.title)}"\n'
                f'author: "{spec.author}"\n'
                f'translator: "{spec.translator}"\n'
                f'editor: "{spec.editor}"\n'
                f'publisher: "{spec.publisher}"\n'
                f"year: {spec.year}\n"
                "---\n\n"
                f"# {spec.title}\n\n"
                + "  \n".join(f"**{s}**" for s in (spec.author, spec.publisher) if s)
                + "\n"
            )
        ]
        typst_sections: list[str] = [
            self.build_typst_preamble(),
            typst_footnote_rules(spec),
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
                    or len(re.sub(r"<!--.*?-->", "", raw_text, flags=re.DOTALL).strip())
                    < spec.min_page_chars
                    or any(marker in raw_text for marker in spec.skip_page_markers)
                ):
                    continue
                p_body, top_f, bot_f = self.cleaner.clean(raw_text, pno)
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

            md_sections.append("\n\n".join(_join_pages_across_math(ch_md_pages)))
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
            elif spec.chapter_label or is_unnumbered_chapter(title):
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
                p_body, top_f, bot_f = self.cleaner.clean(raw_text, pno)
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
            markdown=markdown_footnotes("\n\n".join(md_sections)), typst="\n".join(typst_sections)
        )

    def _write(self, out_dir: Path, ext: str, content: str | None = None) -> Path:
        path = out_dir / f"{self.spec.slug}.{ext}"
        if content is not None:
            _ = path.write_text(content, encoding="utf-8")
        return path

    def _alias(self, path: Path) -> None:
        if self.spec.book_aliases and path.stem != "book":
            alias_as_book(path)

    def build_all(self, out_dir: Path, formats: frozenset[str] = MONOGRAPH_FORMATS) -> MonographOutputs:
        """Write Markdown and Typst, then run Pandoc for LaTeX and Typst for PDF when `formats` names them."""
        out_dir = Path(out_dir)
        rendered = self.render(out_dir)
        md_out = self._write(out_dir, "md", rendered.markdown)
        typ_out = self._write(out_dir, "typ", rendered.typst)
        tex_out = self._write(out_dir, "tex")
        pdf_out = self._write(out_dir, "pdf")
        made = run_formats(
            {
                "tex": (tex_out, lambda: self._write_latex(md_out, tex_out)),
                "pdf": (pdf_out, lambda: compile_typst(typ_out, pdf_out)),
            },
            formats,
        )
        for path in (md_out, typ_out, *made.values()):
            self._alias(path)
        return build_outputs(md_out, typ_out, made)

    def _write_latex(self, md_out: Path, tex_out: Path) -> None:
        header_includes = (
            r"\usepackage[all,cmtip]{xy}\usepackage{amscd}\usepackage{amsthm}"
            + latex_footnote_header(self.spec)
        )
        if self.spec.latex_preamble:
            header_includes = f"{header_includes}\n{self.spec.latex_preamble}"
        latex_md = md_out.with_name(md_out.stem + "_latex.md")
        latex_md.write_text(
            latex_safe_markdown(md_out.read_text(encoding="utf-8")), encoding="utf-8"
        )
        _ = subprocess.run(
            [
                "pandoc",
                str(latex_md),
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
                "-V",
                f"header-includes={header_includes}",
                "-o",
                str(tex_out),
            ],
            check=True,
        )
        latex_md.unlink()


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
