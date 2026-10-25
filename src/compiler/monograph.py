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
from .diagrams import (
    FLETCHER_IMPORT,
    SCAN_DIAGRAM_LATEX,
    SCAN_DIAGRAM_RE,
    convert_diagrams,
    scan_diagram_typst,
    use_scan_diagrams,
)
from .page_cleaner import Figure, PageCleaner, has_circled_footnotes
from .presets import CompositionConfig, resolve_composition
from .source_numbers import LATEX, link_citations, link_references, number_chapter
from .source_numbers import LATEX_RULES as SOURCE_NUMBER_LATEX_RULES
from .source_numbers import TYPST_EQUATION_LAYOUT as SOURCE_EQUATION_LAYOUT
from .source_numbers import TYPST_RULES as SOURCE_NUMBER_RULES
from .source_numbers import labels as source_labels
from .typst_math import (
    REPO_FONTS_DIR,
    clean_margin_and_inline_math,
    compile_typst,
    convert_math_batch,
)

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
    require_vector_figures: bool = False
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
    footnote_style: Literal["", "superscript", "paren", "parenthesized", "circled", "symbol"] = ""
    footnote_marks: tuple[str, ...] = ()
    footnote_numbering: str = "1"
    footnote_reset: Literal["page", "chapter", "book"] = "page"
    equation_numbering: Literal["section", "page", "none"] = "section"
    cross_references: bool = False
    citation_abbreviations: dict[str, str] = field(default_factory=dict)
    commutative_diagrams: bool = False
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
    numbering_resyncs: tuple[str, ...] = ()
    latex_markdown: str | None = None


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


def _cjk_running_headers(titles: tuple[str, ...], chapters: list[ChapterSpec]) -> tuple[str, ...]:
    """A running-header regex for Chinese titles, with or without a folio, OCR spaces or a `序` prefix."""
    names = (*titles, *(c.title.removeprefix("序 ") for c in chapters if c.number))
    pattern = "|".join(r"\s*".join(re.escape(ch) for ch in name if not ch.isspace()) for name in names)
    return (rf"^(?:#+\s*)?(?:\d{{1,3}}\s+)?(?:序\s*)?(?:{pattern})(?:\s+\d{{1,3}})?$",)


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
    ocr_langs = ("zh-Hans", "en-US") if comp.language.code == "zh" else DEFAULT_OCR_LANGUAGES
    chapters = [ChapterSpec(1, escape_typst_text(pdf_path.stem), 1, total_pages)]
    preface_page = None
    cross_refs = False
    running_headers = ()
    header_zone = None
    if "国际经济环境的变化与日本经济" in pdf_path.stem:
        chapters = [
            ChapterSpec(0, "作者简介", 4, 5),
            ChapterSpec(0, "中文版前言", 6, 7),
            ChapterSpec(0, "中文版序言", 8, 15),
            ChapterSpec(0, "序 国际经济环境的变化与日本经济", 16, 24),
            ChapterSpec(1, "进口竞争对日本国内产业的影响", 30, 55),
            ChapterSpec(2, "日本对内直接投资的变化与经济影响", 56, 101),
            ChapterSpec(3, "泡沫、通缩期的日本通商政策", 102, 127),
            ChapterSpec(4, "泡沫、通缩期的日本食品和农业问题", 128, 162),
            ChapterSpec(5, "货币和汇率政策（国际金融政策）变化", 163, 189),
            ChapterSpec(6, "亚洲金融危机和日本金融机构的行动", 190, 218),
            ChapterSpec(7, "汇率和国际收支", 219, 251),
            ChapterSpec(8, "从老龄化等结构性要因来看日本的国际收支问题", 252, 279),
            ChapterSpec(9, "内外价格差和汇率传导", 280, 296),
            ChapterSpec(10, "少子老龄化时代的外国劳动者问题", 297, 323),
            ChapterSpec(11, "经济全球化对20世纪90年代劳动力市场的影响", 324, 347),
        ]
        preface_page = None
        cross_refs = True
        running_headers = (
            r"^(?:#+\s*)?(?:\d{1,3}\s+)?(?:国际经济环境的变化与日本经济|序\s*国际经济环境的变化与日本经济|目录)(?:\s+\d{1,3})?$",
            r"^(?:#+\s*)?(?:\d{1,3}\s+)?(?:进口竞争对日本国内产业的影响|日本对内直接投资的变化与经济影响|泡沫、通缩期的日本通商政策|泡沫、通缩期的日本食品和农业问题|货币和汇率政策[（\(]国际金融政策[）\)]变化|亚洲金融危机和日本金融机构的行动|汇率和国际收支|从老龄化等结构性要因来看日本的国际收支问题|内外价格差和汇率传导|少子老龄化时代的外国劳动者问题|经济全球化对\s*20\s*世纪\s*90\s*年代劳动力市场的影响)(?:\s+\d{1,3})?$",
        )
        header_zone = 4
    elif "通缩经济与货币政策" in pdf_path.stem:
        chapters = [
            ChapterSpec(0, "作者简介", 4, 5),
            ChapterSpec(0, "中文版前言", 6, 7),
            ChapterSpec(0, "中文版序言", 8, 15),
            ChapterSpec(0, "序 通缩经济与货币政策", 16, 27),
            ChapterSpec(1, "根据泡沫形成与破灭的经验考察货币政策框架", 32, 58),
            ChapterSpec(2, "全球化与通货膨胀", 59, 96),
            ChapterSpec(3, "“零利率约束”再思考", 97, 126),
            ChapterSpec(4, "通货紧缩与货币政策", 127, 155),
            ChapterSpec(5, "通货紧缩期的价格走势与货币的作用", 156, 172),
            ChapterSpec(6, "债务—通货紧缩理论与通货紧缩心理预期", 173, 194),
            ChapterSpec(7, "泡沫破灭后的金融市场动荡与货币政策", 195, 223),
            ChapterSpec(8, "量化宽松政策改善经济的传导机制", 224, 260),
            ChapterSpec(9, "四分之一世纪的价格波动", 261, 274),
            ChapterSpec(10, "日本消费者物价指数的各种特性与货币政策运行", 275, 317),
            ChapterSpec(11, "互联网泡沫破灭后的美国货币政策", 318, 344),
            ChapterSpec(12, "泡沫—通货紧缩时期的日本货币政策", 345, 376),
            ChapterSpec(0, "后记", 377, total_pages),
        ]
        cross_refs = True
        running_headers = _cjk_running_headers(("通缩经济与货币政策", "目录", "中文版序言", "中文版前言"), chapters)
        header_zone = 4
    elif "财政政策与社会保障" in pdf_path.stem:
        chapters = [
            ChapterSpec(0, "作者简介", 4, 5),
            ChapterSpec(0, "中文版前言", 6, 7),
            ChapterSpec(0, "中文版序言", 8, 15),
            ChapterSpec(0, "序 财政政策与社会保障", 16, 27),
            ChapterSpec(1, "财政可持续性和财政管理评估", 32, 60),
            ChapterSpec(2, "20世纪90年代公共投资政策评估", 61, 87),
            ChapterSpec(3, "日本发生非凯恩斯效应的可能性", 88, 125),
            ChapterSpec(4, "1996年至1998年财政政策的施行对经济和物价走势的影响", 126, 155),
            ChapterSpec(5, "利用制度信息计算财政乘数", 156, 181),
            ChapterSpec(6, "20世纪80年代后的养老金改革与社会保障资产", 182, 206),
            ChapterSpec(7, "医疗保险制度的推进及其对日本经济的影响", 207, 245),
            ChapterSpec(8, "20世纪90年代代际再分配政策的变迁", 246, 264),
            ChapterSpec(9, "税收制度", 265, 309),
            ChapterSpec(10, "资产税收制度与“泡沫”", 310, 343),
            ChapterSpec(11, "对所得征税中税收弹性系数的分析", 344, 368),
            ChapterSpec(12, "泡沫和通货紧缩时期的地方财政", 369, 388),
            ChapterSpec(13, "各级政府间财政软预算约束", 389, 417),
            ChapterSpec(14, "日本财政投融资", 418, 454),
            ChapterSpec(0, "后记", 455, total_pages),
        ]
        cross_refs = True
        running_headers = _cjk_running_headers(("财政政策与社会保障", "目录", "中文版序言", "中文版前言"), chapters)
        header_zone = 4
    fig_layout = (
        FigureLayout(
            caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?(?:Fig(?:ure)?\.?|Abb\.|图)\s*(?:(?P<chapter>\d+)[\.\-])?(?P<number>\d+[a-z]?)\.?(?:\*\*)?(?:[:\s]+(?P<title>[^\n]+))?$"
        )
        if comp.language.code == "zh"
        else FigureLayout()
    )
    return MonographSpec(
        slug=slug,
        title=pdf_path.stem,
        author="",
        publisher="",
        series="",
        publisher_key=comp.publisher.key,
        lang=comp.language.code,
        domain=comp.domain.key,
        ocr_languages=ocr_langs,
        preface_page=preface_page,
        cross_references=cross_refs,
        chapters=chapters,
        running_header_regexes=running_headers,
        header_zone_lines=header_zone,
        figures=fig_layout,
        chapter_heading="{title}" if cross_refs else "{number} {title}",
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
    "表",
    "附表",
    "图",
    "|",
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
_LATEX_CARET_HASH_RE = re.compile(r"\^#(?![a-zA-Z])")
_LATEX_PRIME_SUPER_RE = re.compile(
    r"((?:\\[a-zA-Z]+|[a-zA-Z0-9]+))'((?:_[a-zA-Z0-9]+|_\{[^{}]*\})*)\^([a-zA-Z0-9\-]+|\{[^}]+\})"
)
_LATEX_DOUBLE_SUB_RE = re.compile(
    r"([a-zA-Z\\][a-zA-Z0-9\\']*(?:\{[^{}]*\})*)(_\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})_(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})"
)
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
        (".", "?", "!", ":", '."', ".'", ".)", ".*", ".*)", "]", "@@FNEND@@", "。", "？", "！", "：", "”", "’", "）")
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
    text = _LATEX_CARET_HASH_RE.sub(r"^\#", text)
    text = _LATEX_PRIME_SUPER_RE.sub(r"{\1'\2}^\3", text)
    text = _LATEX_DOUBLE_SUB_RE.sub(r"{\1\2}_\3", text)
    text = re.sub(r"\\\\(?:\s*)\n\s*\[", r"\\\\\n\\relax [", text)
    text = _LATEX_GROUP_SUPERSCRIPT_RE.sub(r"{}^{\1}", text)
    text = re.sub(r"(\!\[.*?\]\([^)]+?)\.svg\)", r"\1.png)", text)
    text = re.sub(
        r"\\source[a-z]+\*?\{[^{}\n]*\}",
        lambda m: re.sub(r"(?<!\\)&", r"\\&", m.group(0)),
        text,
    )
    def _escape_amp(m: re.Match[str]) -> str:
        blk = m.group(0)
        if blk.startswith("$") or blk.startswith("|") or blk.startswith("\\"):
            return blk
        return re.sub(r"(?<!\\)&", r"\&", blk)
    return re.sub(r"\$\$[\s\S]*?\$\$|(?<!\\)\$(?:[^$\n\\]|\\.)+\$|^\|[^\n]+\|$|[^$|\n]+", _escape_amp, text, flags=re.MULTILINE)

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
    if last_line.endswith("|") or curr_l.startswith("|") or last_line.endswith("$$") or EQ_LABEL_END_RE.search(last_line):
        return prev_r + "\n\n" + curr_l
    if prev_r.endswith("-"):
        m1 = re.search(r"\b([a-zA-Z\u00C0-\u017F]+)-$", prev_r)
        m2 = re.match(r"^(?:[a-zA-Z\u00C0-\u017F]+\b|\$[^\$]+\$)", curr_l)
        if m1 and m2:
            word = m1.group(1).lower()
            if word in HYPHEN_JOIN_WORDS or word in ("non", "quasi", "sous", "s", "pro", "anti", "demi", "co", "sub"):
                return prev_r + curr_l
            return prev_r[:-1] + curr_l
    return prev_r + " " + curr_l






FOOTNOTE_RE = re.compile(r"@@FNSTART@@(.*?)@@FNEND@@", re.DOTALL)
_HEADING_FN_RE = re.compile(r"^(#+[^\n@]*?)@@FNSTART@@(.*?)@@FNEND@@([^\n]*)$", re.MULTILINE)
_HEADING_LATEX_FN_RE = re.compile(r"^(#+[^\n]*?)\s*\\footnote\{([^{}\n]*(?:\{[^{}\n]*\}[^{}\n]*)*)\}([^\n]*)$", re.MULTILINE)
_LATEX_TEXT_SPECIAL_RE = re.compile(r"(?<!\\)([_&%#])")
_HEADING_MD_FN_RE = re.compile(r"^(#+[^\n\^]*?)\s*\^\[([^\n]+?)\]([^\n]*)$", re.MULTILINE)
_SOURCE_FN_RE = re.compile(
    r"([^\n@]*?\\source[a-zA-Z]+\*?\{)([^{}@\n]*?)@@FNSTART@@(.*?)@@FNEND@@([^{}@\n]*)\}",
    re.MULTILINE | re.DOTALL,
)


def _hoist_heading_footnotes(s: str, fn_formatter: Callable[[str], str]) -> str:
    def _repl(m: re.Match[str]) -> str:
        heading = m.group(1).strip()
        trailing = m.group(3).strip()
        body = fn_formatter(m.group(2).replace("\n\n", " ").strip())
        tail = f" {trailing}" if trailing else ""
        return f"{heading}{tail}\n\n{body}"

    return _HEADING_FN_RE.sub(_repl, s)
















def keep_notes_with_calls(block: str) -> str:
    return block


def markdown_footnotes(s: str) -> str:
    s = _hoist_heading_footnotes(s, lambda b: f"^[{b}]")
    return FOOTNOTE_RE.sub(r"^[\1]", s)


def latex_footnotes(s: str) -> str:
    def _source_repl(m: re.Match[str]) -> str:
        cmd = m.group(1)
        title = m.group(2).strip()
        body = m.group(3).replace("\n\n", " ").strip()
        trailing = m.group(4).strip()
        return f"{cmd}{title}}}{trailing} \\footnote{{{body}}}"

    s = _SOURCE_FN_RE.sub(_source_repl, s)
    s = _hoist_heading_footnotes(s, lambda b: f"\\footnote{{{b}}}")
    return FOOTNOTE_RE.sub(
        lambda m: r" \footnote{" + _escape_latex_text(m.group(1).replace("\n\n", " ").strip()) + "}", s
    )


def _escape_latex_text(text: str) -> str:
    return re.sub(
        r"(?<!\\)\$(?:[^$\\]|\\.)+\$|[^$]+",
        lambda m: m.group(0) if m.group(0).startswith("$") else _LATEX_TEXT_SPECIAL_RE.sub(r"\\\1", m.group(0)),
        text,
    )


def running_footnotes(spec: MonographSpec) -> MonographSpec:
    return replace(spec, footnote_marks=(), footnote_numbering="1", footnote_reset="book")


def reference_chapters(spec: MonographSpec) -> dict[str, int]:
    return {c.label.split()[-1]: c.number for c in spec.chapters if c.label}


TYPST_CIRCLE = "box(baseline: -15%, circle(radius: if str(n).len() > 1 { 0.55em } else { 0.45em }, stroke: 0.4pt, inset: 0pt)[#align(center + horizon)[#text(size: if str(n).len() > 1 { 0.52em } else { 0.65em })[#n]]])"
CIRCLED_GLYPH_RE = re.compile("[①-⑳⓪Ⓐ-ⓩ]")
TYPST_CIRCLED_GLYPHS = (
    '#show regex("[①-⑳⓪Ⓐ-ⓩ]"): it => {\n'
    "  let u = str.to-unicode(it.text)\n"
    '  let n = if u == 0x24EA { "0" } else if u <= 0x2473 { str(u - 0x245F) }'
    " else if u <= 0x24CF { str.from-unicode(u - 0x24B6 + 65) } else { str.from-unicode(u - 0x24D0 + 97) }\n"
    f"  {TYPST_CIRCLE}\n"
    "}\n"
)
LATEX_CIRCLED_GLYPHS = (
    r"\makeatletter\def\polytypst@circled#1#2#3{\ifPDFTeX\DeclareUnicodeCharacter{#2}{\text{\textcircled{\scriptsize #3}}}"
    r"\else\begingroup\lccode`\~=`#1\lowercase{\endgroup\def~}{\text{\textcircled{\scriptsize #3}}}\catcode`#1=\active\fi}"
) + "".join(
    rf"\polytypst@circled{{{glyph}}}{{{ord(glyph):04X}}}{{{label}}}"
    for glyph, label in [
        *((chr(0x2460 + i), str(i + 1)) for i in range(20)),
        ("⓪", "0"),
        *((chr(0x24B6 + i), chr(65 + i)) for i in range(26)),
        *((chr(0x24D0 + i), chr(97 + i)) for i in range(26)),
    ]
) + r"\makeatother"


TYPST_CJK_NOTE_MARKS = (
    '#show super: set text(font: "New Computer Modern")\n'
    "#show footnote: it => sym.wj + it\n"
)


def typst_footnote_rules(spec: MonographSpec) -> str:
    cjk_note_marks = TYPST_CJK_NOTE_MARKS if spec.lang == "zh" else ""
    if not spec.footnote_style:
        return cjk_note_marks
    if spec.footnote_marks:
        marks = ", ".join(f'"{m}"' for m in spec.footnote_marks)
        numbering = f"n => ({marks},).at(n - 1, default: str(n))"
    elif spec.footnote_style == "circled" or spec.footnote_numbering == "circled":
        if spec.lang == "zh":
            numbering = '"①"'
        else:
            numbering = f"n => {TYPST_CIRCLE}"
    else:
        numbering = f'"{spec.footnote_numbering}"'
    reset = {
        "page": "#set page(background: counter(footnote).update(0))\n",
        "chapter": "#show heading.where(level: 1): it => { counter(footnote).update(0); it }\n",
        "book": "",
    }[spec.footnote_reset]
    notes_stay_with_calls = "#set text(costs: (widow: 0%, orphan: 0%))\n"
    return f"{cjk_note_marks}#set footnote(numbering: {numbering})\n{notes_stay_with_calls}{reset}"


LATEX_CHINESE_PARAGRAPHS = (
    r"\setlength{\parindent}{2em}"
    r'\ifdefined\XeTeXlinebreaklocale\XeTeXlinebreaklocale "zh"\XeTeXlinebreakskip=0pt plus 1pt\fi'
    r"\makeatletter\let\@afterindentfalse\@afterindenttrue\@afterindenttrue"
    r"\begingroup\lccode`\~=`、\lowercase{\endgroup\def~}{\text{、}}\catcode`、=\active\makeatother"
)
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
    elif spec.footnote_style == "circled" or spec.footnote_numbering == "circled":
        header += r"\renewcommand\thefootnote{\protect\textcircled{\scriptsize\arabic{footnote}}}"
    elif spec.footnote_numbering == "1)":
        header += r"\renewcommand\thefootnote{\arabic{footnote})}"
    elif spec.footnote_numbering == "(1)":
        header += r"\renewcommand\thefootnote{(\arabic{footnote})}"
    return header


UNNUMBERED_CHAPTER_PREFIXES = (
    "作者简介",
    "中文版前言",
    "中文版序言",
    "序",
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


def format_pipe_tables_as_typst(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith("|") and next_line.endswith("|") and all(c in " |-:—–" for c in next_line):
                table_lines = [line]
                i += 2
                while i < len(lines):
                    curr = lines[i].strip()
                    if curr.startswith("|") and curr.endswith("|"):
                        table_lines.append(curr)
                        i += 1
                    else:
                        break

                parsed_rows: list[list[str]] = []
                for tl in table_lines:
                    cells = [c.strip() for c in tl.split("|")[1:-1]]
                    parsed_rows.append(cells)

                if parsed_rows:
                    ncols = max(len(r) for r in parsed_rows)
                    for r in parsed_rows:
                        r.extend([""] * (ncols - len(r)))
                    nrows = len(parsed_rows)
                    items: list[str] = []
                    for r_idx, r in enumerate(parsed_rows):
                        first = r[0].strip()
                        if first and all(not c.strip() for c in r[1:]) and (first.startswith(("#strong", "**")) or first.startswith(("一、", "二、", "三、", "四、", "A ", "B ", "A面板", "B面板", "A 面板", "B 面板"))):
                            title_text = re.sub(r"^\*\*(.*?)\*\*$", r"\1", first)
                            title_text = re.sub(r"^#strong\[(.*?)\]$", r"\1", title_text)
                            items.append(f"table.cell(colspan: {ncols}, fill: luma(245))[#strong[{title_text}]]")
                        elif r_idx < 2 and any(not c.strip() for c in r) and any(c.strip() for c in r):
                            col_idx = 0
                            while col_idx < len(r):
                                c = r[col_idx]
                                c_clean = c.replace("<br>", "\\ ").replace("<br/>", "\\ ")
                                c_clean = re.sub(r"<(?!eq-|fig-|sec-)", r"\<", c_clean)
                                c_clean = re.sub(r"(?<![@\\])@(?=[\w])(?!@)", r"\@", c_clean)
                                c_clean = re.sub(r"(?<!\\)\[", r"\[", c_clean)
                                c_clean = re.sub(r"(?<!\\)\]", r"\]", c_clean)
                                c_clean = re.sub(r"(?<!\\)\*", r"\*", c_clean)
                                c_clean = re.sub(r"(?<!\\)_", r"\_", c_clean)
                                span = 1
                                if c.strip():
                                    while col_idx + span < len(r) and not r[col_idx + span].strip():
                                        span += 1
                                    if span > 1:
                                        items.append(f"table.cell(colspan: {span})[#strong[{c_clean}]]")
                                        col_idx += span
                                        continue
                                items.append(f"[#strong[{c_clean}]]" if c_clean.strip() else "[]")
                                col_idx += 1
                        else:
                            for c in r:
                                c_clean = c.replace("<br>", "\\ ").replace("<br/>", "\\ ")
                                c_clean = re.sub(r"<(?!eq-|fig-|sec-)", r"\<", c_clean)
                                c_clean = re.sub(r"(?<![@\\])@(?=[\w])(?!@)", r"\@", c_clean)
                                c_clean = re.sub(r"(?<!\\)\[", r"\[", c_clean)
                                c_clean = re.sub(r"(?<!\\)\]", r"\]", c_clean)
                                c_clean = re.sub(r"(?<!\\)\*", r"\*", c_clean)
                                c_clean = re.sub(r"(?<!\\)_", r"\_", c_clean)
                                if r_idx == 0 and c_clean.strip() and not c_clean.strip().startswith(("#strong", "**")):
                                    items.append(f"[#strong[{c_clean}]]")
                                else:
                                    items.append(f"[{c_clean}]")
                    body = ", ".join(items)
                    if ncols >= 10:
                        size_pt = "6.8pt"
                        col_def = f"(1.8fr, ..(1fr,)*{ncols - 1})"
                    elif ncols >= 8:
                        size_pt = "7.2pt"
                        col_def = f"(1.6fr, ..(1fr,)*{ncols - 1})"
                    elif ncols >= 6:
                        size_pt = "7.8pt"
                        col_def = f"(1.5fr, ..(1fr,)*{ncols - 1})"
                    elif ncols >= 5:
                        size_pt = "8.2pt"
                        col_def = f"(1.4fr, ..(1fr,)*{ncols - 1})"
                    else:
                        size_pt = "8.8pt"
                        col_def = f"{ncols}"

                    if nrows > 1:
                        stroke_str = f"  stroke: (x, y) => if y == 0 {{ (top: 1.0pt + luma(30), bottom: 0.6pt + luma(60)) }} else if y == {nrows - 1} {{ (bottom: 1.0pt + luma(30)) }} else {{ (bottom: 0.3pt + luma(220)) }},\n"
                    else:
                        stroke_str = "  stroke: (x, y) => (top: 1.0pt + luma(30), bottom: 1.0pt + luma(30)),\n"
                    fill_str = "  fill: (col, row) => if row > 0 and calc.even(row) { luma(252) } else { none },\n" if ncols >= 6 else ""
                    typst_table = (
                        f"\n#align(center)[\n"
                        f"#set text(size: {size_pt})\n"
                        f"#table(\n"
                        f"  columns: {col_def},\n"
                        f"  align: (col, row) => if col == 0 {{ left + horizon }} else {{ center + horizon }},\n"
                        f"{stroke_str}"
                        f"{fill_str}"
                        f"  {body}\n"
                        f")\n"
                        f"]\n"
                    )
                    out.append(typst_table)
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)

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
        self._figure_labels: set[str] = set()

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
        header_style = "normal" if self.composition.language.code in ("zh", "ja") else "italic"
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
    let strip-fn(it) = if type(it) == content and it.has("children") {{ it.children.filter(c => c.func() != footnote).join() }} else if type(it) == content and it.func() == footnote {{ [] }} else {{ it }}
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if page-number > 4 and not on-chapter-page [
      #if calc.odd(page-number) [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let in-chapter = if chaps == () {{ heading.where(level: 2) }} else {{ heading.where(level: 2).after(chaps.last().location()) }}
        #let secs = query(in-chapter).filter(h => h.location().page() <= here().page())
        #let on-page = secs.filter(h => h.location().page() == here().page())
        #let title = strip-fn(if on-page != () {{ on-page.first().body }} else if secs != () {{ secs.last().body }} else if chaps != () {{ chaps.last().body }} else {{ "{escape_quoted(self.spec.title)}" }})
        #grid(
          columns: (1fr, auto),
          align(left)[#text(8.5pt, font: {font_expr}, style: "{header_style}")[#title]],
          align(right)[#text(9.5pt, font: {font_expr})[#page-number]]
        )
      ] else [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = strip-fn(if chaps != () {{ chaps.last().body }} else {{ "{escape_quoted(self.spec.title)}" }})
        #grid(
          columns: (auto, 1fr),
          align(left)[#text(9.5pt, font: {font_expr})[#page-number]],
          align(right)[#text(8.5pt, font: {font_expr}, style: "{header_style}")[#title]]
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
    let sc = calc.max(0.62, avail / w)
    scale(x: sc * 100%, y: sc * 100%, reflow: true, eq)
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
  #text(9pt, font: {font_expr})[#if it.supplement != none [#strong[#it.supplement #context it.counter.display(it.numbering)]#if it.body != [] [: ]]#it.body]
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

#[
  #show footnote: none
  #outline(title: [{lang.contents_title}], indent: 1.4em, depth: 2)
]

#pagebreak()
"""


    def _resolve_figure_asset(self, fig_dir: Path, fig_id: str) -> Path | None:
        exts = ("svg",) if self.spec.require_vector_figures else ("svg", "png")
        for ext in exts:
            for fid in (fig_id, fig_id.replace("_", "-"), fig_id.replace("-", "_")):
                candidate = fig_dir / f"fig_{fid}.{ext}"
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
        asset = self._resolve_figure_asset(fig_dir, fig_id)
        if asset is None:
            if self.spec.cross_references:
                digits = re.sub(r"[.\_]", "-", fig_id)
                cap_body = re.sub(r"^(?:(?:Fig(?:ure)?\.?|图)\s*(?:\d+[\.\-])?\d+[a-z]?\.?\s*:?\s*)", "", clean_cap, flags=re.IGNORECASE).strip()
                raw_num = fig_id.replace("_", "-")
                label = "" if digits in self._figure_labels else f" <fig-{digits}>"
                self._figure_labels.add(digits)
                return f'#align(center)[#figure(caption: [{cap_body}], numbering: _ => "{raw_num}")[]{label}]'
            return f"#emph[{clean_cap}]"
        width_pct = self._figure_width_pct(asset, paired)
        supplement = (
            ",\n  supplement: none"
            if self.spec.figures.supplement_none and not self.spec.cross_references
            else ""
        )
        cap_body = clean_cap
        label_str = ""
        counter_update = ""
        numbering = ""
        if self.spec.cross_references:
            cap_body = re.sub(
                r"^(?:(?:Fig(?:ure)?\.?|图)\s*(?:\d+[\.\-])?\d+[a-z]?\.?\s*:?\s*)",
                "",
                clean_cap,
                flags=re.IGNORECASE,
            ).strip()
            digits = re.sub(r"[.\_]", "-", fig_id)
            label_str = "" if digits in self._figure_labels else f" <fig-{digits}>"
            self._figure_labels.add(digits)
            raw_num = fig_id.replace("_", "-")
            num_tail = digits.split("-")[-1]
            num_int = int(re.match(r"\d+", num_tail).group(0)) if re.match(r"\d+", num_tail) else 1
            counter_update = f"#counter(figure.where(kind: image)).update({max(0, num_int - 1)})\n"
            numbering = f'  numbering: _ => "{raw_num}",\n'
        else:
            clean_cap = re.sub(
                r"^(Fig(?:ure)?\.?\s*\d+[\.\-]\d+[a-z]?\.?)",
                r"#strong[\1]",
                clean_cap,
                flags=re.IGNORECASE,
            )
            cap_body = clean_cap
        return (
            f"{counter_update}#figure(\n"
            f'  image("{fig_dir.name}/{asset.name}", width: {width_pct}%),\n'
            f"{numbering}"
            f"  caption: [{cap_body}]{supplement}\n"
            f"){label_str}"
        )

    def render_figure_group(self, figs: list[Figure], fig_dir: Path) -> str:
        if not figs:
            return ""
        if len(figs) == 2 and all(
            self._resolve_figure_asset(fig_dir, fid) is not None for fid, _ in figs
        ):
            f1 = self.make_figure_typst(*figs[0], fig_dir, paired=True)
            f2 = self.make_figure_typst(*figs[1], fig_dir, paired=True)
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
            for fid, cap in figs
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
            if (
                PROSE_IN_MATH_RE.search(code)
                or (re.search(r"[\u4e00-\u9fff]", code) and r"\text" not in code)
            ) and "\\" not in code:
                return f" {code.replace(chr(34), '').strip()} "
            inline_blocks.append(code.strip())
            return f"@@INLINEMATH{len(inline_blocks) - 1}@@"

        s = re.sub(r"(?<!\\)\$((?:[^$\n\\]|\\.)+)\$", save_inline, s)
        s = "\n\n".join(
            para if _balanced_backticks(para) else para.replace("`", r"\`")
            for para in s.split("\n\n")
        )
        table_blocks: list[str] = []
        def _extract_pipe_tables(text_chunk: str) -> str:
            lines = text_chunk.split("\n")
            out_lines = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("|") and line.endswith("|") and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("|") and next_line.endswith("|") and all(c in " |-:—–" for c in next_line):
                        tbl = [line]
                        i += 2
                        while i < len(lines):
                            curr = lines[i].strip()
                            if curr.startswith("|") and curr.endswith("|"):
                                tbl.append(curr)
                                i += 1
                            else:
                                break
                        raw_tbl = "\n".join([line, next_line] + tbl[1:])
                        table_blocks.append(raw_tbl)
                        out_lines.append(f"@@TABLEBLOCK{len(table_blocks)-1}@@")
                        continue
                out_lines.append(lines[i])
                i += 1
            return "\n".join(out_lines)

        s = _extract_pipe_tables(s)

        s = re.sub(r"^\s*#(?!pagebreak\b)", r"\#", s, flags=re.MULTILINE)
        s = re.sub(r"(?<![=\\])#(?!pagebreak\b)", r"\#", s)
        s = re.sub(r"<(?!eq-|fig-|sec-)", r"\<", s)
        s = re.sub(r"^\s*/\s*", r"\/ ", s, flags=re.MULTILINE)
        s = s.replace("//", r"\/\/").replace("*/", "* /")
        s = re.sub(r"(?<![@\\])@(?=[\w])(?!@)", r"\@", s)
        if spec.lang in ("zh", "ja"):
            s = s.replace("~", "～")
        else:
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
            cap_before = m.group(1)
            alt = m.group(2)
            path = m.group(3).replace(r"\_", "_")
            cap_after = m.group(4)
            width_str = "width: 45%"
            for candidate_dir in (self._out_dir, Path("output/bourbaki"), Path("output/klein"), Path("output/fermat"), Path("output/kashiwara"), Path("output/kenji-alg"), Path(".")):
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
                    if local_f.suffix.lower() == ".svg":
                        width_str = "width: 75%"
                        break
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
            def is_real_caption(text: str | None) -> bool:
                if not text or len(text.strip()) > 70:
                    return False
                t = text.strip()
                if not re.match(r"^(?:#+\s*)?图\s*\d+[-－]\d+", t):
                    return False
                prose_markers = ("显示了", "表明了", "描绘了", "给出了", "可以看出", "由此可见", "是由", "反映了", "当一个", "如图", "假设", "对于", "在图")
                return not any(w in t for w in prose_markers)

            pre_is_cap = is_real_caption(cap_before)
            post_is_cap = is_real_caption(cap_after)
            cap = None
            if pre_is_cap:
                cap = cap_before.strip()
            elif is_real_caption(alt):
                cap = alt.strip()
            elif post_is_cap:
                cap = cap_after.strip()

            lead = ""
            if cap_before and not pre_is_cap:
                lead = f"{cap_before}\n\n"
            trail = ""
            if cap_after and not post_is_cap:
                trail = f"\n\n{cap_after}"

            if cap and re.match(r"^(?:#+\s*)?图\s*\d+[-－]\d+", cap):
                clean_c = re.sub(r"^(?:#+\s*)?(图\s*\d+[-－]\d+[a-z]?\.?)", r"#strong[\1]", cap)
                if post_is_cap and not pre_is_cap and not (alt and is_real_caption(alt)):
                    fig_block = f"#align(center)[#block(breakable: false)[\n  #image(\"{path}\", {width_str})\n  #v(0.4em)\n  #text(size: 10pt)[{clean_c}]\n]]"
                else:
                    fig_block = f"#align(center)[#block(breakable: false)[\n  #text(size: 10pt)[{clean_c}]\n  #v(0.4em)\n  #image(\"{path}\", {width_str})\n]]"
                return f"\n\n{lead}{fig_block}{trail}\n\n"
            return f"\n\n{lead}#align(center)[#image(\"{path}\", {width_str})]{trail}\n\n"
        s = re.sub(r"@@IMAGE(\d+)@@", lambda m: images[int(m.group(1))], s)
        s = re.sub(
            r"(?:^(?:#+\s*)?(图\s*\d+[-－]\d+[^\n]*)\n+)?"
            r"!\[([^\]]*)\]\(([^)]+)\)"
            r"(?:\n+(?:#+\s*)?(图\s*\d+[-－]\d+[^\n]*))?",
            repl_img,
            s,
            flags=re.MULTILINE,
        )
        s = s.replace(r"\cdots", "...").replace(r"\ldots", "...").replace(r"\neq", r"\!=")
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
        inline_typst = converted[: len(inline_blocks)]
        display_typst = converted[len(inline_blocks) :]
        s = re.sub(
            r"@@INLINEMATH(\d+)@@", lambda m: f"${inline_typst[int(m.group(1))].strip()}$", s
        )
        diagrams = (
            convert_diagrams(
                [body for body, _ in display_blocks],
                lambda cells: convert_math_batch([(c, False) for c in cells]),
            )
            if spec.commutative_diagrams
            else {}
        )
        def display(m: re.Match[str]) -> str:
            i = int(m.group(1))
            label = display_blocks[i][1]
            if scan := SCAN_DIAGRAM_RE.fullmatch(display_blocks[i][0].strip()):
                fig = scan_diagram_typst(scan.group(1), self._out_dir / spec.figure_dir, spec.figure_dir)
                return f"\n$ {fig} $ {label}\n"
            if i not in diagrams:
                return f"\n$ {display_typst[i]} $ {label}\n"
            return f"\n$ #{diagrams[i]} $ {label}\n" if label else f"\n#align(center, {diagrams[i]})\n"

        s = re.sub(r"@@DISPLAYBLOCK(\d+)@@", display, s)
        indent = self.composition.language.first_line_indent
        s = re.sub(
            r"(\n\$ [^\n]*(?:\n[^\n$]*)*?\.\s*\$ (?:<eq-[^>]+>)?\n)\n+"
            r"(?=(?!Then\b|Where\b|Here\b|Hence\b|Thus\b|Indeed\b)[A-Z“\"])",
            rf"\1\n#h({indent});",
            s,
        )
        s = re.sub(r"(#(?:strong|emph)\[[^\]]+\])(?=\()", r"\1\\", s)
        s = re.sub(r"(#(?:strong|emph)\[[^\]]+\])\.(?=[^\s\d])", r"\1\\.", s)
        if spec.cross_references:
            s = re.sub(
                r"\b(?:Figure|Fig\.)\s+(\d+[a-z]?)\b",
                r"@fig-\1",
                s,
            )
            known_figs = {m.group(1) for m in re.finditer(r"<fig-([\w-]+)>", s)}
            def _link_chinese_fig(m: re.Match[str]) -> str:
                digits = re.sub(r"[.\-]", "-", m.group(1))
                label = f"fig-{digits}"
                if label not in known_figs:
                    return m.group(0)
                next_char = m.string[m.end():m.end()+1]
                if re.match(r"[\w:\[-]", next_char):
                    return f"@{label}#[]"
                return f"@{label}"
            s = re.sub(
                r"(?<!<fig-)(?<!\[#strong\[)图\s*(\d+[-.]\d+[a-z]?)(?!>)",
                _link_chinese_fig,
                s,
            )
        def _format_table_title(m: re.Match[str]) -> str:
            full_title = m.group(1).strip()
            if len(full_title) > 60 or "，" in full_title or "。" in full_title:
                return m.group(0)
            return f"\n\n#v(0.6em)\n#align(center)[#strong[{full_title}]]\n#v(0.2em)\n\n"

        s = re.sub(
            r"^\s*(?:#+\s*)?((?:附)?表\s*\d+[-.]\d+[^\n]*)\s*$",
            _format_table_title,
            s,
            flags=re.MULTILINE,
        )
        s = re.sub(r"@@FIGBLOCK(\d+)@@", lambda m: fig_blocks[int(m.group(1))], s)
        s = "\n\n".join(map(keep_notes_with_calls, s.split("\n\n")))
        s = re.sub(r"@@FNEND@@(?=\()", r"@@FNEND@@\\", s)
        s = re.sub(
            r"@@FNEND@@\.(?=[^\s\d])",
            r"@@FNEND@@\\.",
            s.replace("@@FNEND@@;", "@@FNEND@@\\;"),
        )
        def _typst_hoist_heading_fn(m: re.Match[str]) -> str:
            heading = m.group(1).strip()
            trailing = m.group(3).strip()
            body = m.group(2).replace("\n\n", " ").strip()
            tail = f" {trailing}" if trailing else ""
            return f"{heading}{tail}\n#footnote[{body}]"

        s = re.sub(
            r"^([#=]+[^\n@]*?)@@FNSTART@@(.*?)@@FNEND@@([^\n]*)$",
            _typst_hoist_heading_fn,
            s,
            flags=re.MULTILINE,
        )
        s = FOOTNOTE_RE.sub(r"#footnote[\1]", s)
        def _expand_table(m: re.Match[str]) -> str:
            raw_tbl = table_blocks[int(m.group(1))]
            if spec.lang in ("zh", "ja"):
                raw_tbl = raw_tbl.replace("~", "～")
            tbl_math = re.sub(
                r"@@INLINEMATH(\d+)@@",
                lambda im: f"${inline_typst[int(im.group(1))].strip()}$",
                raw_tbl,
            )
            tbl_out = format_pipe_tables_as_typst(tbl_math)
            return FOOTNOTE_RE.sub(r"#footnote[\1]", tbl_out)

        s = re.sub(r"@@TABLEBLOCK(\d+)@@", _expand_table, s)
        s = format_pipe_tables_as_typst(s)
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
        s = s.replace("@@PAGEBREAK@@", "\n#pagebreak()\n")
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
        self._figure_labels = set()
        out_dir = Path(out_dir)
        md_dir = out_dir / spec.markdown_dir
        store = TranscriptStore(md_dir)
        page_texts = [store.text(int(p.stem[2:])) or "" for p in sorted(md_dir.glob("p_*.md"))]
        if not spec.footnote_style and any(has_circled_footnotes(t, spec.folio_pattern) for t in page_texts):
            spec = self.spec = replace(spec, footnote_style="circled", footnote_numbering="circled")
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
            TYPST_CIRCLED_GLYPHS
            if spec.lang != "zh" and spec.footnote_style != "circled" and any(CIRCLED_GLYPH_RE.search(t) for t in page_texts)
            else "",
            SOURCE_NUMBER_RULES if spec.cross_references else "",
            SOURCE_EQUATION_LAYOUT if spec.cross_references and (not spec.typst_preamble or "fit-display" in spec.typst_preamble) else "",
            FLETCHER_IMPORT if spec.commutative_diagrams else "",
            self.build_typst_title_page(),
        ]
        numbered_chapters: list[tuple[int, int]] = []
        latex_chapters: dict[int, tuple[str, int]] = {}
        resyncs: list[str] = []
        has_explicit_labels = any(c.label for c in spec.chapters)

        if spec.preface_page is not None:
            preface = self._single_page_section(md_dir, spec.preface_page, "Preface")
            if preface:
                md_sections.append(f"\n## Preface\n\n{preface[0]}\n")
                typst_sections.append(preface[1])

        seen_typst: set[str] = set()
        seen_latex: set[str] = set()
        for chap in spec.chapters:
            if chap.typst_file:
                prebuilt = self._prebuilt_chapter(out_dir, chap)
                if prebuilt is not None:
                    typst_sections += [prebuilt, "\n#pagebreak(weak: true)\n"]
                continue
            pages_data: list[PageParts] = []
            ch_md_pages: list[str] = [
                f"\n# {chap.title}\n"
                if spec.cross_references or is_unnumbered_chapter(chap.title)
                else f"\n# Chapter {chap.number}: {chap.title}\n"
            ]
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
                if spec.commutative_diagrams:
                    p_body = use_scan_diagrams(p_body, pno, fig_dir)
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
            should_number = spec.cross_references and (
                bool(chap.label)
                if has_explicit_labels
                else ("索引" not in title and "Index" not in title and "校订后记" not in title)
            )
            if should_number:
                formatted, chapter_resyncs = number_chapter(formatted, chap.number, seen=seen_typst)
                resyncs += [r.line() for r in chapter_resyncs]
                numbered_chapters.append((len(typst_sections), chap.number))
                latex_chapters[len(md_sections) - 1] = (
                    number_chapter(md_sections[-1], chap.number, LATEX, seen=seen_latex)[0],
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
            typst_sections.append(f"\n{heading}\n\n" + formatted)
            typst_sections.append("\n#pagebreak(weak: true)\n")

        known = set().union(*(source_labels(typst_sections[i]) for i, _ in numbered_chapters))
        roman = reference_chapters(spec)
        for i, number in numbered_chapters:
            typst_sections[i] = link_references(typst_sections[i], number, roman, known)
        latex_known = set().union(*(source_labels(text) for text, _ in latex_chapters.values()))
        latex_sections = [
            link_references(latex_chapters[i][0], latex_chapters[i][1], roman, latex_known, LATEX)
            if i in latex_chapters
            else section
            for i, section in enumerate(md_sections)
        ]
        if spec.cross_references:
            typst_sections = link_citations(typst_sections, spec.citation_abbreviations)
            latex_sections = link_citations(latex_sections, spec.citation_abbreviations, LATEX)

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
            markdown=markdown_footnotes("\n\n".join(md_sections)),
            typst="\n".join(typst_sections),
            numbering_resyncs=tuple(resyncs),
            latex_markdown=latex_footnotes("\n\n".join(latex_sections)) if latex_chapters else None,
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
        if self.spec.cross_references:
            report = out_dir / f"{self.spec.slug}-numbering-resyncs.txt"
            _ = report.write_text("".join(f"{line}\n" for line in rendered.numbering_resyncs), encoding="utf-8")
            print(f"{len(rendered.numbering_resyncs)} numbering resyncs -> {report}")
        tex_out = self._write(out_dir, "tex")
        pdf_out = self._write(out_dir, "pdf")
        made = run_formats(
            {
                "tex": (tex_out, lambda: self._write_latex(md_out, tex_out, rendered.latex_markdown)),
                "pdf": (pdf_out, lambda: compile_typst(typ_out, pdf_out)),
            },
            formats,
        )
        for path in (md_out, typ_out, *made.values()):
            self._alias(path)
        return build_outputs(md_out, typ_out, made)

    def _write_latex(self, md_out: Path, tex_out: Path, markdown: str | None = None) -> None:
        xy_inc = r"\usepackage[all,cmtip]{xy}" if self.spec.commutative_diagrams else ""
        header_includes = (
            xy_inc
            + r"\usepackage{graphicx}\usepackage{amscd}\usepackage{amsthm}\usepackage{caption}\captionsetup[figure]{labelformat=empty}"
            + LATEX_CIRCLED_GLYPHS
            + latex_footnote_header(self.spec)
            + (SOURCE_NUMBER_LATEX_RULES if self.spec.cross_references else "")
            + (SCAN_DIAGRAM_LATEX if self.spec.commutative_diagrams else "")
            + (LATEX_CHINESE_PARAGRAPHS if self.composition.language.code == "zh" else "")
        )
        if self.spec.latex_preamble:
            header_includes = f"{header_includes}\n{self.spec.latex_preamble}"
        latex_md = md_out.with_name(md_out.stem + "_latex.md")
        raw_md = markdown or md_out.read_text(encoding="utf-8")
        raw_md = FOOTNOTE_RE.sub(lambda m: r"\footnote{" + m.group(1).replace("\n\n", " ").strip() + "}", raw_md)
        raw_md = _HEADING_LATEX_FN_RE.sub(r"\1\3\n\n\\footnote{\2}", raw_md)
        raw_md = _HEADING_MD_FN_RE.sub(r"\1\3\n\n^[\2]", raw_md)
        raw_md = re.sub(
            r"([^\n]*?\\source[a-zA-Z]+\*?\{)([^{}\n]*(?:\{[^{}\n]*\}[^{}\n]*)*)\s*\\footnote\{([^{}\n]*(?:\{[^{}\n]*\}[^{}\n]*)*)\}([^{}\n]*)\}",
            r"\1\2\4} \\footnote{\3}",
            raw_md,
        )
        latex_md.write_text(latex_safe_markdown(raw_md), encoding="utf-8")
        pandoc_cmd = [
            "pandoc",
            str(latex_md),
            "-f",
            "markdown+tex_math_dollars+raw_tex",
            "-t",
            "latex",
            "-s",
            "--top-level-division=chapter",
            "--number-sections",
            "--toc",
            "-V",
            "documentclass=book",
            "-V",
            f"geometry:{self.composition.publisher.pandoc_geometry}",
            "-V",
            f"header-includes={header_includes}",
            "-o",
            str(tex_out),
        ]
        if self.composition.language.code == "zh":
            pandoc_cmd[3] += "-superscript"
            pandoc_cmd.extend(["-V", "mainfont=Songti SC", "-V", "indent=true"])
        _ = subprocess.run(pandoc_cmd, check=True)
        latex_md.unlink()

