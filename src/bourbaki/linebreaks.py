"""Line endings of the 1970 Bourbaki scan, inserted as forced breaks into the source text.

The source OCR cache (`polytypst.parity.source`) gives each scan page's body lines.
For every line that ends outside math, the word that ends it is found in the
page's Markdown, and a justified break marker goes after it (`@@BR@@`), or
inside it at the scan's hyphenation point (`@@HY@@`).
"""

import itertools
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..compiler.monograph import REPO_FONTS_DIR as FONTS
from ..parity.source import SourcePage, read_source_page, source_ocr_dir

BODY_TOP, BODY_BOTTOM = 60.0, 58.0
WINDOW = 60
WORD_RE = re.compile(r"[A-Za-z]+")
MATH_RE = re.compile(r"\$\$.*?\$\$|\$[^$\n]*\$", re.DOTALL)


def scan_body_lines(page: SourcePage) -> list[str]:
    """OCR text of the body lines of a scan page, top to bottom, without running head and folio."""
    lines = []
    for line in page.lines:
        top = page.top_pt(line)
        if BODY_TOP < top < page.height - BODY_BOTTOM:
            lines.append((top, line.text.strip()))
    return [text for _, text in sorted(lines)]


@dataclass(frozen=True)
class Ending:
    """A scan line end: the two words before it, the next line's first word, and its word offset."""

    before: str
    end: str
    nxt: str
    hyphenated: bool
    offset: int


def line_endings(lines: list[str]) -> list[Ending]:
    """The ending of every line but the last that has two words before the break."""
    out, offset = [], 0
    for text, nxt in itertools.pairwise(lines):
        words, following = WORD_RE.findall(text), WORD_RE.findall(nxt)
        offset += len(words)
        if len(words) < 2 or not following:
            continue
        hyphenated = text.endswith("-") and text[:-1].rstrip().endswith(words[-1])
        out.append(Ending(words[-2].lower(), words[-1].lower(), following[0].lower(), hyphenated, offset))
    return out


def _tokens(body: str) -> list[re.Match]:
    math = [m.span() for m in MATH_RE.finditer(body)]
    skip = [(m.start(), m.end()) for m in re.finditer(r"^(?:#|!\[).*$", body, re.MULTILINE)]
    blocked = sorted(math + skip)
    out, k = [], 0
    for tok in WORD_RE.finditer(body):
        while k < len(blocked) and blocked[k][1] <= tok.start():
            k += 1
        if k < len(blocked) and blocked[k][0] <= tok.start() < blocked[k][1]:
            continue
        out.append(tok)
    return out


def _edit_at(body: str, toks: list[re.Match], j: int, e: Ending) -> tuple[int, int, str] | None:
    """The marker edit for ending `e` at token `j`, or None when the words around `j` differ."""
    word = toks[j].group().lower()
    if j == 0 or toks[j - 1].group().lower() != e.before:
        return None
    if e.hyphenated:
        if len(word) > len(e.end) and word.startswith(e.end) and word[len(e.end) :].startswith(e.nxt):
            at = toks[j].start() + len(e.end)
            return at, at, "@@HY@@"
        return None
    if word != e.end or j + 1 >= len(toks) or toks[j + 1].group().lower() != e.nxt:
        return None
    gap = body[toks[j].end() : toks[j + 1].start()]
    space = re.search(r"\s+", gap)
    if space is None or "\n\n" in gap or "$" in gap:
        return None
    return toks[j].end() + space.start(), toks[j].end() + space.end(), "@@BR@@"


def insert_breaks(body: str, endings: list[Ending]) -> str:
    """Insert `@@BR@@` after, or `@@HY@@` inside, each line-ending word whose three-word context matches.

    Matches keep scan order; among candidates the one nearest the ending's word offset wins.
    """
    toks = _tokens(body)
    edits: list[tuple[int, int, str]] = []
    cursor = 0
    for e in endings:
        found = [(abs(j - e.offset), j, edit) for j in range(cursor, min(len(toks), e.offset + WINDOW)) if (edit := _edit_at(body, toks, j, e))]
        if found:
            _, j, edit = min(found)
            edits.append(edit)
            cursor = j + 1
    for a, b, marker in sorted(edits, reverse=True):
        body = body[:a] + marker + body[b:]
    return body


MEASURE_PT = 324.0
SIZE_PT = 9.6
INDENT_EM = 1.1
MULTI_LINE = 1.5
LINE_STRETCH_PT, LINE_SHRINK_PT = 12.0, 15.0
SPACE_SHRINK, SPACE_STRETCH, TRACK_SHRINK_EM = 1 - 0.6667, 0.5, 0.02
MARKER_RE = re.compile(r"@@(BR|HY)@@")
SCRIPT_RE = re.compile(r"[_^](\{[^{}]*\}|\\[A-Za-z]+|.)")
WIDE_OPS = ("\\to", "\\otimes", "\\oplus", "\\in", "\\subset", "\\circ", "\\times", "\\cap", "\\cup", "=", "+", "<", ">", "\\leq", "\\geq", "\\neq")


@cache
def _font():
    from PIL import ImageFont

    font = ImageFont.truetype(str(FONTS / "Baskervville-wght.ttf"), 100)
    font.set_variation_by_axes([500])
    return font


def math_width_em(tex: str) -> float:
    """A width estimate for inline TeX math, in em, fitted to the scan's single-line segments."""
    scripts = sum(len(re.sub(r"\\[A-Za-z]+", "x", s)) for s in SCRIPT_RE.findall(tex))
    main = SCRIPT_RE.sub("", tex)
    ops = sum(main.count(op) for op in WIDE_OPS)
    main = re.sub(r"\\(?:operatorname|mathfrak|mathrm|mathbf|mathcal|mathbb)", "", main)
    visible = len(re.sub(r"[\s{}]", "", re.sub(r"\\[A-Za-z]+", "x", main)))
    return 0.08 + 0.54 * visible + 0.24 * scripts + 1.05 * ops


def line_width_pt(segment: str) -> tuple[float, int, int]:
    """Natural width (pt), space count and character count of one line of Markdown text."""
    font = _font()
    width_em = 0.0
    for tex in re.findall(r"\$([^$]*)\$", segment):
        width_em += math_width_em(tex)
    text = re.sub(r"\$[^$]*\$", "x", segment)
    text = re.sub(r"[*_]", "", text)
    width_em += font.getlength(text) / 100
    return width_em * SIZE_PT, text.count(" "), len(text)


def fits(segment: str, indent: bool) -> bool:
    """Whether a forced line, or a run of lines whose inner scan breaks did not match, sets within the justification limits."""
    width, spaces, chars = line_width_pt(segment)
    width += INDENT_EM * SIZE_PT if indent else 0.0
    if width > MULTI_LINE * MEASURE_PT:
        return run_fills_lines(width)
    space = _font().getlength(" ") / 100 * SIZE_PT
    stretch = spaces * SPACE_STRETCH * space
    shrink = 0.8 * (spaces * SPACE_SHRINK * space + chars * TRACK_SHRINK_EM * SIZE_PT)
    return MEASURE_PT - stretch <= width <= MEASURE_PT + shrink


def keep_fitting_breaks(body: str) -> str:
    """Drop, per paragraph, the first forced break whose line would not fit and every one after it.

    A forced line that is too wide gets re-broken into two loose lines, and one that is too
    narrow is stretched; letting the rest of the paragraph flow avoids both.
    """
    paragraphs = body.split("\n\n")
    continues = bool(body) and body[0].islower()
    out = []
    for i, para in enumerate(paragraphs):
        start, kept, indent = 0, [], not (i == 0 and continues)
        for m in MARKER_RE.finditer(para):
            segment = para[start : m.start()] + ("-" if m.group(1) == "HY" else "")
            if not fits(segment.strip(), indent):
                break
            kept.append(m.span())
            start, indent = m.end(), False
        dropped = [s for s in (m.span() for m in MARKER_RE.finditer(para)) if s not in kept]
        for a, b in reversed(dropped):
            replacement = "" if para[a:b] == "@@HY@@" else " "
            para = para[:a] + replacement + para[b:]
        out.append(para)
    return "\n\n".join(out)


def last_line_fills(page: str) -> bool:
    """Whether the page's last paragraph can end in a full justified line within the limits."""
    para = page.rstrip().split("\n\n")[-1]
    tail = MARKER_RE.split(para)[-1].strip()
    width, _, _ = line_width_pt(tail)
    if not MARKER_RE.search(para) and not para.startswith("@@NOINDENT@@"):
        width += INDENT_EM * SIZE_PT
    return run_fills_lines(width)


def run_fills_lines(width: float) -> bool:
    """Whether a run of `width` pt sets as whole justified lines: n measures plus a rest that
    the line breaker can stretch to a full line or spread as shrink over the other n lines."""
    lines, rest = divmod(width, MEASURE_PT)
    return MEASURE_PT - rest <= (lines + 1) * LINE_STRETCH_PT or rest <= lines * LINE_SHRINK_PT


def scan_line_breaks(pno: int, body: str, out_dir: Path) -> str:
    """The page body with the scan's line endings forced where they match and the lines fit."""
    page = read_source_page(source_ocr_dir(out_dir), pno)
    return keep_fitting_breaks(insert_breaks(body, line_endings(scan_body_lines(page))))
