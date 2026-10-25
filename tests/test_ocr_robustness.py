"""The spec-less build turns any OCR page text into a Typst book that compiles and keeps its prose."""

import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import pymupdf
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from polytypst.book_state import book_state
from polytypst.compiler.monograph import (
    MonographCompiler,
    adhoc_spec,
)
from polytypst.compiler.typst_math import REPO_FONTS_DIR, convert_math_batch

OCR_STATES: dict[str, str] = {
    "empty": "",
    "whitespace": "   \n\n\t\n",
    "page_number_only": "123",
    "running_header": "IMPLICIT FUNCTIONS 87\n\nThe implicit function theorem follows.",
    "unclosed_inline_math": "Let $f(z) = \\sum a_n z^n be a power series that converges.",
    "unclosed_display_math": "Consider\n\n$$\n\\int_0^1 f(x)\\,dx\n\nand the rest of the page.",
    "unclosed_bracket_display": "Consider \\[ \\int_0^1 f(x) dx and nothing closes it.",
    "stray_close_bracket_display": "An equation ends here \\] with no opening.",
    "lone_dollar": "$",
    "lone_double_dollar": "$$",
    "four_dollars": "$$$$",
    "nested_dollars": "$a $b$ c$",
    "prices": "It costs $5 and then $10 more, or \\$15 in all.",
    "unbalanced_brace": "We have $\\frac{a}{b + c$ in the text.",
    "extra_close_brace": "We have $a + b}}$ in the text.",
    "left_without_right": "Then $\\left( \\frac{1}{2} \\right.$ and $\\left[ x$ hold.",
    "unknown_macro": "The map $\\foobarbaz{x} \\qux y$ is exotic.",
    "script_without_operand": "$\\frac$ and $\\sqrt$ and $x^$ and $x_$ and $^$ and $(x_)$.",
    "begin_without_end": "$$\\begin{pmatrix} a & b \\\\ c & d$$",
    "end_without_begin": "$$a & b \\\\ c & d \\end{bmatrix}$$",
    "align_env": "$$\\begin{align} a &= b \\\\ &= c \\end{align}$$",
    "cases_env": "$$f(x) = \\begin{cases} 1 & x > 0 \\\\ 0 \\end{cases}$$",
    "array_env": "$$\\begin{array}{cc} a & b \\\\ c & d \\end{array}$$",
    "xymatrix": "$$\\xymatrix{A \\ar[r] & B}$$",
    "tag_and_label": "$$x = 1 \\tag{1.2} \\label{eq:x}$$",
    "math_with_text": '$\\text{for all } x \\text{ in "S"}$',
    "math_with_hash": "$#x + \\# y$",
    "long_math": "$" + " + ".join(f"x_{{{i}}}" for i in range(800)) + "$",
    "deep_braces": "$" + "{" * 200 + "x" + "}" * 200 + "$",
    "html_table": "<table><tr><td>$a$</td><td>b</td></tr><tr><td>c</td></tr></table>",
    "broken_html_table": "<table><tr><td>unclosed cell<td>next",
    "html_tags": "<div><b>bold</b> <span style='x'>s</span> <br> <sup>2</sup></div>",
    "html_comment": "<!-- page 4 --> visible <!-- unclosed",
    "markdown_table": "| a | b |\n|---|---|\n| $x$ | 2 |",
    "missing_image": "![Figure 3](image_17.png)\n\nText after the figure.",
    "image_with_brackets_in_alt": "![Fig. [3] a] (b)](figures/none.png) after.",
    "empty_headings": "# \n\n## \n\n###",
    "seven_hash_heading": "####### Seven hashes heading\n\nBody.",
    "unclosed_bold": "**Theorem 2.3 The statement never closes bold.",
    "unclosed_emph": "*Proof. The emphasis never closes.",
    "stray_brackets": "A list ] closes [ and opens [x] in prose.",
    "typst_specials": "Email @someone #hashtag <label> * star _under_ ~tilde ] [ \\",
    "unclosed_code_fence": "```python\nprint('hello')\n",
    "lone_backtick": "The prime ` is a backtick.",
    "inline_code_with_dollar": "Use `$HOME` and `a$b` in shell.",
    "footnote": "Text with a note.[^1]\n\n[^1]: The note body.",
    "label_like": "See <eq-1> and <eq-1> again and @eq-1.",
    "latex_commands_in_prose": "\\section{Intro} \\textbf{bold} \\emph{e} \\cite{x} \\ref{y}",
    "trailing_backslash": "Ends with a backslash \\",
    "percent": "100% sure, 50 % off, \\% escaped.",
    "quotes": "He said \"hello\" and 'bye' and “curly” and «guillemets».",
    "cjk": "定理 1.1. 正則関数 $f$ は $D$ で連続である．",
    "arabic": "هذه جملة عربية مع $x^2$ رياضيات.",
    "emoji": "Results 🎉 hold for $n \\geq 1$ 🚀.",
    "control_chars": "Before\x00null\x07bell\x1bescape after.",
    "bom_and_crlf": "﻿First line\r\nSecond line\r\n",
    "long_line": ("word " * 5000).strip(),
    "runaway_frac_nesting": "$" + "\\frac{" * 2000 + "x" + "}{y}" * 2000 + "$",
    "backtick_run": "`" * 10000,
    "star_run": "*" * 20000,
    "dollar_run": "$" * 20001,
    "unclosed_bold_over_a_page": "**" + "word " * 10000,
    "left_run": "$" + "\\left(" * 5000 + "$",
}
HOSTILE_PDF_NAMES = [
    "Lectures [draft] #2.pdf",
    'He said "hi".pdf',
    "Price $5 and $x$.pdf",
    "back\\slash.pdf",
    "star*under_score@at<lt>.pdf",
    "]].pdf",
    "#set page(width: 1pt).pdf",
    "/* comment.pdf",
    "// slashes.pdf",
    "a}b{c.pdf",
    "it's.pdf",
    "ünïcödé 数学.pdf",
]
OCR_CORPUS_DIR = Path(
    os.environ.get("OCR_CORPUS_DIR", Path(__file__).resolve().parents[1] / "output")
)
CORPUS_PAGES = sorted(OCR_CORPUS_DIR.glob("*/markdown_pages/p_*.md"))

FUZZ_EXAMPLES = int(os.environ.get("OCR_FUZZ_EXAMPLES", "30"))
OPENING = "The opening page of the probe book is plain prose."
CLOSING = "The closing page of the probe book is plain prose."
SENTINEL_LETTERS = "bcdkmnprstvwxz"


def _typst_command() -> list[str]:
    if shutil.which("typst"):
        return ["typst"]
    if shutil.which("mise"):
        return ["mise", "exec", "--", "typst"]
    pytest.skip("Typst is not installed")


def _compile(typ: Path) -> str:
    """Compile `typ` and return the PDF text, failing the test with Typst's error."""
    pdf = typ.with_suffix(".pdf")
    res = subprocess.run(
        [
            *_typst_command(),
            "compile",
            "--font-path",
            str(REPO_FONTS_DIR),
            str(typ),
            str(pdf),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert res.returncode == 0, res.stderr
    return "\n".join(page.get_text() for page in pymupdf.open(pdf))


def _build_spec_less_book(out_dir: Path, pages: list[str], pdf_name: str = "Probe Book.pdf") -> str:
    """Write `pages` as OCR output for an unknown PDF, build it, and return the PDF text."""
    spec = adhoc_spec(Path(pdf_name), len(pages))
    md_dir = book_state(out_dir) / spec.markdown_dir
    md_dir.mkdir(parents=True, exist_ok=True)
    for old in md_dir.glob("p_*.md"):
        old.unlink()
    for pno, text in enumerate(pages, start=1):
        _ = (md_dir / f"p_{pno:03d}.md").write_text(text, encoding="utf-8")
    typ = out_dir / f"{spec.slug}.typ"
    _ = typ.write_text(MonographCompiler(spec).render(out_dir).typst, encoding="utf-8")
    return _compile(typ)


def _flat(text: str) -> str:
    """Join hyphenated line breaks, drop whitespace, and straighten typeset quotes, so words compare."""
    text = text.translate(str.maketrans("“”‘’", "\"\"''"))
    return re.sub(r"\s+", "", re.sub(r"[-\xad]\s*\n", "", text))


@pytest.mark.parametrize("ocr_text", OCR_STATES.values(), ids=OCR_STATES.keys())
def test_each_ocr_state_compiles_and_keeps_its_neighbour_pages(
    tmp_path: Path, ocr_text: str
) -> None:
    pdf_text = _flat(_build_spec_less_book(tmp_path, [OPENING, ocr_text, CLOSING]))
    assert _flat(OPENING) in pdf_text
    assert _flat(CLOSING) in pdf_text


@pytest.mark.parametrize("short_page", ["以上で証明を終わる。", "QED.", "\\"])
def test_a_short_page_keeps_its_text(tmp_path: Path, short_page: str) -> None:
    pdf_text = _flat(_build_spec_less_book(tmp_path, [OPENING, short_page, CLOSING]))
    assert _flat(short_page).strip("\\") in pdf_text
    assert _flat(CLOSING) in pdf_text


def test_math_nested_too_deep_for_the_fallback_converter_still_compiles(tmp_path: Path) -> None:
    deep = OCR_STATES["runaway_frac_nesting"]
    pdf_text = _flat(_build_spec_less_book(tmp_path, [OPENING + "\n\n" + deep[:1304], deep[1304:], CLOSING]))
    assert _flat(OPENING) in pdf_text
    assert _flat(CLOSING) in pdf_text


@pytest.mark.parametrize(
    "pdf_name", ["数学在十九世纪的发展第二卷复变函数与代数几何.pdf", "Lectures on the Theory of Algebraic Numbers and Their Ideals.pdf"]
)
def test_a_title_that_can_wrap_keeps_its_full_size(tmp_path: Path, pdf_name: str) -> None:
    _ = _build_spec_less_book(tmp_path, [OPENING], pdf_name)
    slug = adhoc_spec(Path(pdf_name), 1).slug
    title_page = pymupdf.open(tmp_path / f"{slug}.pdf")[0]
    sizes = [span["size"] for block in title_page.get_text("dict")["blocks"] for line in block.get("lines", []) for span in line["spans"]]
    assert max(sizes) == pytest.approx(26)


@pytest.mark.parametrize("pdf_name", HOSTILE_PDF_NAMES)
def test_any_pdf_file_name_becomes_a_title_that_compiles(tmp_path: Path, pdf_name: str) -> None:
    pdf_text = _flat(_build_spec_less_book(tmp_path, [OPENING, CLOSING], pdf_name))
    assert _flat(Path(pdf_name).stem.upper()) in pdf_text
    assert _flat(OPENING) in pdf_text


@settings(
    max_examples=FUZZ_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(
    stem=st.text(
        st.characters(codec="utf-8", exclude_categories=["Cs", "Cc"], exclude_characters="/"),
        min_size=1,
        max_size=30,
    )
)
def test_generated_pdf_file_names_compile(tmp_path: Path, stem: str) -> None:
    _ = _build_spec_less_book(tmp_path, [OPENING, CLOSING], f"{stem}.pdf")


def _mutate(text: str, op: str, at: int) -> str:
    """Apply one OCR-style damage to a real page: a lost delimiter, a cut page, or a misread line order."""
    delimiters = [i for i, ch in enumerate(text) if ch in "$}{\\]["]
    lines = text.splitlines()
    if op == "drop_delimiter" and delimiters:
        i = delimiters[at % len(delimiters)]
        return text[:i] + text[i + 1 :]
    if op == "cut_page":
        return text[: at % max(len(text), 1)]
    if op == "repeat_line" and lines:
        i = at % len(lines)
        return "\n".join(lines[: i + 1] + lines[i:])
    if op == "swap_lines" and len(lines) > 1:
        i = at % (len(lines) - 1)
        lines[i], lines[i + 1] = lines[i + 1], lines[i]
        return "\n".join(lines)
    return text


@pytest.mark.skipif(not CORPUS_PAGES, reason="no saved OCR pages under OCR_CORPUS_DIR")
@settings(
    max_examples=FUZZ_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(
    page=st.sampled_from(CORPUS_PAGES or [Path()]),
    ops=st.lists(
        st.tuples(
            st.sampled_from(["drop_delimiter", "cut_page", "repeat_line", "swap_lines"]),
            st.integers(min_value=0, max_value=10_000),
        ),
        min_size=1,
        max_size=4,
    ),
)
def test_damaged_real_ocr_pages_compile_and_keep_their_neighbour_pages(
    tmp_path: Path, page: Path, ops: list[tuple[str, int]]
) -> None:
    text = page.read_text(encoding="utf-8")
    for op, at in ops:
        text = _mutate(text, op, at)
    pdf_text = _flat(_build_spec_less_book(tmp_path, [OPENING, text, CLOSING]))
    assert _flat(OPENING) in pdf_text
    assert _flat(CLOSING) in pdf_text


class OCREngineMachine(RuleBasedStateMachine):
    """Plays an OCR engine that writes pages mixing sentinel prose, catalog states, and noise.

    Every sentinel word is ordinary prose, so it must reach the PDF whatever surrounds it.
    """

    def __init__(self) -> None:
        super().__init__()
        self.pages: list[list[str]] = []
        self.sentinels: list[str] = []

    @initialize()
    def open_book(self) -> None:
        self.pages.append([OPENING])

    def _sentinel(self, draw_letters: str) -> str:
        word = (
            "zq"
            + draw_letters
            + SENTINEL_LETTERS[len(self.sentinels) % len(SENTINEL_LETTERS)]
        )
        self.sentinels.append(word)
        return f"The word {word} is plain prose."

    @rule(letters=st.text(SENTINEL_LETTERS, min_size=4, max_size=8))
    def new_page_of_prose(self, letters: str) -> None:
        self.pages.append([self._sentinel(letters)])

    @rule(state=st.sampled_from(sorted(OCR_STATES)))
    def append_ocr_state(self, state: str) -> None:
        self.pages[-1].append(OCR_STATES[state])

    @rule(state=st.sampled_from(sorted(OCR_STATES)))
    def new_page_from_ocr_state(self, state: str) -> None:
        self.pages.append([OCR_STATES[state]])

    @rule(letters=st.text(SENTINEL_LETTERS, min_size=4, max_size=8))
    def append_prose(self, letters: str) -> None:
        self.pages[-1].append(self._sentinel(letters))

    @rule(
        noise=st.text(
            st.characters(codec="utf-8", exclude_categories=["Cs"]), max_size=40
        )
    )
    def append_noise(self, noise: str) -> None:
        self.pages[-1].append(noise)

    @rule()
    def blank_page(self) -> None:
        self.pages.append([])

    @rule(cut=st.integers(min_value=0, max_value=10_000))
    def page_break_inside_last_fragment(self, cut: int) -> None:
        fragment = self.pages[-1][-1] if self.pages[-1] else ""
        if len(fragment) < 2 or "zq" in fragment:
            return
        at = 1 + cut % (len(fragment) - 1)
        self.pages[-1][-1] = fragment[:at]
        self.pages.append([fragment[at:]])

    @invariant()
    def pages_render(self) -> None:
        spec = adhoc_spec(Path("Probe Book.pdf"), len(self.pages))
        _ = MonographCompiler(spec).format_typst(
            "\n\n".join("\n\n".join(page) for page in self.pages)
        )

    def teardown(self) -> None:
        with tempfile.TemporaryDirectory() as out_dir:
            pdf_text = _flat(
                _build_spec_less_book(
                    Path(out_dir), ["\n\n".join(page) for page in self.pages]
                )
            )
        missing = [word for word in self.sentinels if word not in pdf_text]
        assert not missing, f"sentinel prose lost: {missing}"


OCREngineMachine.TestCase.settings = settings(
    max_examples=FUZZ_EXAMPLES,
    stateful_step_count=8,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
TestOCREngineMachine = OCREngineMachine.TestCase


LATEX_ATOMS = st.sampled_from(
    [
        "x",
        "y",
        "n",
        "1",
        "2",
        "+",
        "-",
        "=",
        "<",
        ">",
        ",",
        ".",
        "|",
        "'",
        "!",
        "^",
        "_",
        "{",
        "}",
        "(",
        ")",
        "[",
        "]",
        "&",
        "\\\\",
        " ",
        "\\frac",
        "\\sqrt",
        "\\left(",
        "\\right)",
        "\\left.",
        "\\right|",
        "\\alpha",
        "\\infty",
        "\\sum",
        "\\int",
        "\\partial",
        "\\mathbb{R}",
        "\\mathcal",
        "\\bar",
        "\\hat",
        "\\text{ if }",
        "\\operatorname{Hom}",
        "\\cdots",
        "\\to",
        "\\begin{pmatrix}",
        "\\end{pmatrix}",
        "\\begin{cases}",
        "\\end{cases}",
        "\\binom",
        "\\overline",
        "\\lim_{n \\to \\infty}",
        "\\,",
        "\\;",
        "\\quad",
        "\\foo",
    ]
)


@settings(
    max_examples=FUZZ_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(
    snippets=st.lists(
        st.tuples(
            st.lists(LATEX_ATOMS, min_size=1, max_size=12).map("".join), st.booleans()
        ),
        min_size=1,
        max_size=12,
    )
)
def test_any_ocr_math_converts_to_typst_that_compiles(
    tmp_path: Path, snippets: list[tuple[str, bool]]
) -> None:
    converted = convert_math_batch(snippets)
    body = "\n\n".join(
        f"$ {typ} $" if display else f"${typ}$"
        for typ, (_, display) in zip(converted, snippets, strict=True)
    )
    typ = tmp_path / "math.typ"
    _ = typ.write_text(body, encoding="utf-8")
    _ = _compile(typ)


HOSTILE_UNICODE = [
    *("1\ufe0f\u20e3", "2\u20e3", "#\ufe0f\u20e3", "*\ufe0f\u20e3"),
    *("🎉", "🚀", "😀", "👍🏽", "👨\u200d👩\u200d👧", "🇫🇷", "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f", "⭐", "✅", "❤\ufe0f", "☺\ufe0f", "✔\ufe0f"),
    *("➕", "➖", "➗", "✖\ufe0f"),
    *("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\u200e", "\u200f"),
    *("\u202a", "\u202e", "\u2066", "\u2069", "\x00", "\x07", "\x1b", "\x7f", "\x85", "\r"),
    *("\ufe0f", "\ufe0e", "\U000e0100", "\ue000", "\uf8ff", "\U000f0001", "\U0010fffd", "\uffff", "�"),
    *("①", "⑳", "⑴", "⒈", "Ⓐ", "ⓐ", "⓪", "❶", "❿"),
    *("\\ud83d\\ude00", "\\ud83d", "\\U0001F600", "&#x1F600;", "&#128512;", "&#xE000;"),
    *("\u0301", "\u20e3"),
]
FULLWIDTH_MATH = ["ｆ", "（", "）", "＝", "＋", "１", "\u3000"]
HOSTILE = st.one_of(
    st.sampled_from(HOSTILE_UNICODE),
    st.characters(categories=["Cc", "Cf", "Co"]),
    st.characters(min_codepoint=0x1F300, max_codepoint=0x1FAFF),
)


def _untypesettable(c: str) -> bool:
    """A character no book font draws, by its Unicode class: controls, format, private-use,
    unassigned, emoji and selectors, keycap marks, and fullwidth forms."""
    n = ord(c)
    return (
        (unicodedata.category(c) in ("Cc", "Cf", "Co", "Cs", "Cn") and c not in "\t\n")
        or 0x1F000 <= n <= 0x1FAFF
        or 0xFE00 <= n <= 0xFE0F
        or 0xE0100 <= n <= 0xE01EF
        or n in (0x20E3, 0xFFFD)
        or 0xFF01 <= n <= 0xFF5E
    )


def _compile_latex(tex: Path) -> str:
    """Compile `tex` with XeLaTeX and return the log, failing on an error or a missing glyph.
    XeLaTeX, not LuaLaTeX: the book loads xypic, whose PDF driver rejects LuaTeX."""
    if not shutil.which("xelatex"):
        pytest.skip("XeLaTeX is not installed")
    res = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
        cwd=tex.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    log = tex.with_suffix(".log").read_text(encoding="utf-8", errors="replace")
    assert res.returncode == 0, next((line for line in log.splitlines() if line.startswith("!")), log[-2000:])
    missing = [line for line in log.splitlines() if line.startswith("Missing character")]
    assert not missing, missing[:5]
    return log


@pytest.mark.parametrize(
    "page",
    [
        "Steps ① and ⑳, cases Ⓐ and ⓩ, start ⓪.",
        "In math $x^{②} + \\text{③} = ④$ and $$\n⑤ = a\n$$",
    ],
)
def test_circled_numbers_compile_with_every_glyph_drawn(tmp_path: Path, page: str) -> None:
    spec = adhoc_spec(Path("Probe Book.pdf"), 1)
    md_dir = book_state(tmp_path) / spec.markdown_dir
    md_dir.mkdir(parents=True)
    _ = (md_dir / "p_001.md").write_text(page, encoding="utf-8")
    built = MonographCompiler(spec).build_all(tmp_path, frozenset({"tex"}))
    assert built.latex_path is not None
    _ = _compile(built.typst_path)
    _ = _compile_latex(built.latex_path)


class BadMarkdownMachine(RuleBasedStateMachine):
    """Plays an OCR engine that writes hostile Unicode into prose, inline math, display math and `\\text`.

    Both the Typst and the LaTeX book must compile with every glyph drawn, keep every sentinel word,
    and carry none of the untypesettable characters the pages held."""

    def __init__(self) -> None:
        super().__init__()
        self.pages: list[list[str]] = []
        self.sentinels: list[str] = []
        self.inserted: set[str] = set()

    @initialize()
    def open_book(self) -> None:
        self.pages.append([OPENING])

    def _sentinel(self, letters: str) -> str:
        word = "zq" + letters + SENTINEL_LETTERS[len(self.sentinels) % len(SENTINEL_LETTERS)]
        self.sentinels.append(word)
        return word

    def _add(self, fragment: str, *hostile: str) -> None:
        self.inserted.update(hostile)
        self.pages[-1].append(fragment)

    @rule(letters=st.text(SENTINEL_LETTERS, min_size=4, max_size=8))
    def new_page_of_prose(self, letters: str) -> None:
        self.pages.append([f"The word {self._sentinel(letters)} is plain prose."])

    @rule(letters=st.text(SENTINEL_LETTERS, min_size=4, max_size=8), h=HOSTILE, glued=st.booleans())
    def hostile_beside_a_sentinel(self, letters: str, h: str, glued: bool) -> None:
        word = self._sentinel(letters)
        gap = "" if glued else " "
        self._add(f"The {h}{gap}word {word}{gap}{h} is prose.", h)

    @rule(h=HOSTILE, at_start=st.booleans())
    def hostile_in_inline_math(self, h: str, at_start: bool) -> None:
        self._add(f"Let ${h}x + 1$ hold." if at_start else f"Let $x {h}+ 1$ hold.", h)

    @rule(h=HOSTILE)
    def hostile_in_display_math(self, h: str) -> None:
        self._add(f"$$\n{h}a = b {h}\n$$", h)

    @rule(h=HOSTILE)
    def hostile_in_math_text(self, h: str) -> None:
        self._add(f"Then $\\text{{for all {h} x}}$ holds.", h)

    @rule(
        call=st.text(SENTINEL_LETTERS, min_size=4, max_size=8),
        body=st.text(SENTINEL_LETTERS, min_size=4, max_size=8),
        n=st.integers(min_value=1, max_value=20),
        in_math=st.booleans(),
    )
    def page_with_a_circled_note(self, call: str, body: str, n: int, in_math: bool) -> None:
        mark = chr(0x245F + n)
        called = f"$^{{{mark}}}$" if in_math else mark
        self.pages.append([f"The word {self._sentinel(call)}{called} has a note.", f"{mark} The note says {self._sentinel(body)}."])

    @rule(fw=st.lists(st.sampled_from(FULLWIDTH_MATH), min_size=1, max_size=6).map("".join))
    def fullwidth_math(self, fw: str) -> None:
        self._add(f"Here $a {fw} b$ is fullwidth.", fw)

    def teardown(self) -> None:
        with tempfile.TemporaryDirectory() as out_dir:
            spec = adhoc_spec(Path("Probe Book.pdf"), len(self.pages))
            md_dir = book_state(Path(out_dir)) / spec.markdown_dir
            md_dir.mkdir(parents=True)
            for pno, page in enumerate(self.pages, start=1):
                _ = (md_dir / f"p_{pno:03d}.md").write_text("\n\n".join(page), encoding="utf-8")
            built = MonographCompiler(spec).build_all(Path(out_dir), frozenset({"tex"}))
            assert built.latex_path is not None
            pdf_text = _flat(_compile(built.typst_path))
            _ = _compile_latex(built.latex_path)
            typst = built.typst_path.read_text(encoding="utf-8")
            latex = built.latex_path.read_text(encoding="utf-8")
        bad = {c for h in self.inserted for c in h if _untypesettable(c)}
        assert not [c for c in bad if c in typst], f"untypesettable in Typst: {[c for c in bad if c in typst]}"
        assert not [c for c in bad if c in latex], f"untypesettable in LaTeX: {[c for c in bad if c in latex]}"
        missing = [word for word in self.sentinels if word not in pdf_text or word not in latex]
        assert not missing, f"sentinel prose lost: {missing}"


BadMarkdownMachine.TestCase.settings = settings(
    max_examples=FUZZ_EXAMPLES,
    stateful_step_count=8,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
TestBadMarkdownMachine = BadMarkdownMachine.TestCase
