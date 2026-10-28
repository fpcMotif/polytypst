import re
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from ..tex_markdown import normalize_html_tables, repair_page_math
from ..vision.figure_extractor import (
    FIGURES_MANIFEST_NAME,
    ExtractedFigure,
    manifest_figures,
)
from .presets import resolve_composition

if TYPE_CHECKING:
    from .monograph import MonographSpec

Figure = tuple[str, str]

_OPEN_EQNUM_SPACE_RE = re.compile(r"\((\d{1,3})\.[ \t]+(\d{1,3})\)")
_DOUBLE_BACKSLASH_MACRO_RE = re.compile(r"\\\\(?=[A-Za-z])")
_MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")

_DOUBLE_SUBSCRIPT_RE = re.compile(r"(\^\\[A-Za-z]+)_")
_STAR_DOUBLE_SUPERSCRIPT_RE = re.compile(r"\^\*_\{([^{}]*)\}\^(\{[^{}]*\}|\\[A-Za-z]+|[A-Za-z0-9])")


def _fix_inline_math_delimiters(text: str) -> str:
    """Drop spaces just inside a single-dollar math span; Pandoc and Typst reject them."""
    out: list[str] = []
    in_math = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\" and text[i + 1 : i + 2] == "$":
            out.append("\\$")
            i += 2
            continue
        if ch != "$":
            out.append(ch)
            i += 1
            continue
        if text[i + 1 : i + 2] == "$":
            end = text.find("$$", i + 2)
            if end == -1:
                out.append(text[i:])
                break
            out.append(text[i : end + 2])
            i = end + 2
            continue
        if in_math:
            while out and out[-1].isspace():
                out.pop()
            out.append("$")
            in_math = False
        else:
            out.append("$")
            in_math = True
            i += 1
            while i < n and text[i] in " \t":
                i += 1
            continue
        i += 1
    return "".join(out)


def _section_equation_id(ch: str, num: str | None) -> str:
    return f"{ch}-{num.replace('.', '-')}" if num else ch


def _label_section_equations(s: str, pno: int, deep: bool = False) -> str:
    """Label `(1.2)`-style equation numbers as `<eq-PAGE-1-2>`.

    With `deep`, numbers of any depth such as `(1.2.1.1)` are labelled too, as `<eq-1-2-1-1>`."""
    number = r"(\d+)(?:\.(\d+(?:\.\d+)*))?\.?" if deep else r"(\d+)(?:\.(\d+[a-z']?))?"
    s = re.sub(r"\\tag\{\(?(\d+)\.(\d+[a-z']?)\)?\}", rf"\\tag{{{pno}-\1-\2}}", s)
    s = re.sub(
        rf"^[ \t]*(\({number}\))[ \t]*\$([^$\n]{{8,}})\$[ \t]*([.,;]?)[ \t]*$",
        r"\1\n$$\n\4\5\n$$",
        s,
        flags=re.MULTILINE,
    )
    s = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\n\1\n$$", s, flags=re.DOTALL)

    def replace_block(m: re.Match[str]) -> str:
        pre_ch, pre_num = m.group(1), m.group(2)
        body = m.group(3).strip()
        post_ch, post_num = m.group(4), m.group(5)
        eq_id = ""
        if pre_ch:
            eq_id = _section_equation_id(pre_ch, pre_num)
        elif post_ch:
            eq_id = _section_equation_id(post_ch, post_num)
        m_start = re.match(rf"^\({number}\)\s*(?:\\q?quad\s*|\\hfill\s*)*", body)
        if m_start and not eq_id:
            eq_id = _section_equation_id(m_start.group(1), m_start.group(2))
            body = body[m_start.end() :].strip()
        m_end = re.search(rf"(?:\\hfill|\\q?quad|\s)+\({number}\)\s*$", body)
        if m_end and not eq_id:
            eq_id = _section_equation_id(m_end.group(1), m_end.group(2))
            body = body[: m_end.start()].strip()
        m_tag = re.search(r"\\tag\{([0-9a-zA-Z'-]+)\}", body)
        if m_tag:
            eq_id = eq_id or m_tag.group(1)
            body = (body[: m_tag.start()] + body[m_tag.end() :]).strip()
        label = f" <eq-{eq_id}>" if eq_id else ""
        return f"\n\n$$\n{body}\n$${label}\n\n"

    s = re.sub(
        rf"(?:^[ \t]*\({number}\)[ \t]*\n*\s*)?\$\$(.*?)\$\$"
        rf"(?:[ \t]*\n?[ \t]*\n?[ \t]*\({number}\)[ \t]*(?=\n|$)(?!\s*\$\$))?",
        replace_block,
        s,
        flags=re.MULTILINE | re.DOTALL,
    )
    s = re.sub(r"\\tag\{[^{}]*\}", "", s)
    s = re.sub(r"(<eq-[^>]+>)(?:\s*<eq-[^>]+>)+", r"\1", s)
    if len(re.findall(r"\$\$", s)) % 2 != 0:
        s = s.rstrip()
        para_end = s.find("\n\n", s.rfind("$$") + 2)
        s = s + "$$" if para_end == -1 else s[:para_end].rstrip() + "$$" + s[para_end:]
    return s


def _label_page_equations(s: str, ch_num: int, pno: int) -> str:
    """Label plain `(n)` equation numbers as `<eq-CHAPTER-PAGE-n>`."""
    s = re.sub(r"\\tag\{(\d+)\}", rf"\\tag{{{ch_num}-{pno}-\1}}", s)
    s = re.sub(
        r"^[ \t]*\((\d+)\)[ \t]*\$([^$\n]{10,})\$([.,;]?)[ \t]*$",
        r"(\1)\n$$\n\2\3\n$$",
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
        r"(?:[ \t]*\n?[ \t]*\n?[ \t]*\((\d+)\)[ \t]*(?=\n|$)(?!\s*\$\$))?",
        replace_block,
        s,
        flags=re.MULTILINE | re.DOTALL,
    )


SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
CIRCLED_DIGITS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
FOOTNOTE_LINE_RES = {
    "superscript": re.compile(rf"^([{SUPERSCRIPT_DIGITS}]+)\s*(\S.*)$"),
    "paren": re.compile(r"^(\d{1,2})\)\s+(\S.*)$"),
    "parenthesized": re.compile(r"^(?=\$\^|\(\d{1,2}\)\s+[A-ZÀ-Ý«\u4e00-\u9fff])(?:\$\^\{?)?\((\d{1,2})\)(?:\}?\$)?\s*(\S.*)$"),
    "circled": re.compile(
        rf"^(?:(?:\$\^(?:\{{\\text\{{|\{{)?|\\text\{{|\^\{{)?([{CIRCLED_DIGITS}])(?:\}}\}}?\$|\}})?|(?:\$\^\{{?)?\((\d{{1,2}})\)(?:\}}?\$)?|(?:([{SUPERSCRIPT_DIGITS}]+)\)|(?:\$\^\{{|\^\{{)(\d{{1,2}})\)\}}\$?))\s*(\S.*)$"
    ),
    "symbol": re.compile(r"^\\?(\*{1,3}|†{1,2}|‡|§(?=\s+[A-Z]))\s*(\S.*)$"),
}
FOOTNOTE_RULE_RE = re.compile(r"^(?:[—–-]+|_{3,})$")

NOTE_CONTINUATION_RE = re.compile(r'^[a-z"“$(]')


def _note_line(line: str, style: str, below_rule: bool = False) -> re.Match[str] | None:
    """Above a note rule a star note must open a sentence, and a star touching its word must be the line's only star,
    so italic heads ("*Example 3.* Let"), starred exercises ("*6.") and math lines stay in the body."""
    m = FOOTNOTE_LINE_RES[style].match(line)
    if not m or below_rule or not (m.group(1) or "").startswith("*"):
        return m
    touching = not line.lstrip("\\")[len(m.group(1))].isspace()
    if not re.match(r"[A-Z“\"]", m.group(2)) or (touching and "*" in re.sub(r"\$[^$]*\$", "", m.group(2))):
        return None
    return m


def _inline_note_math(text: str) -> str:
    text = re.sub(r"\$\$\s*(.*?)\s*\$\$", r"$\\displaystyle \1$", text, flags=re.DOTALL)
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", text):
        return text
    return re.sub(
        rf"[{CIRCLED_DIGITS}]",
        lambda m: f"({CIRCLED_DIGITS.index(m.group(0)) + 1})",
        text,
    )

def _note(m: re.Match[str]) -> tuple[str, str]:
    """A star mark that leaves the note's emphasis stars unpaired also opened an italic title ("*Memorial*, see")."""
    groups = m.groups()
    key = next(g for g in groups[:-1] if g is not None)
    if all(ch in SUPERSCRIPT_DIGITS for ch in key) and len(groups) > 2 and groups[2] == key:
        key = key.translate(str.maketrans(SUPERSCRIPT_DIGITS, "0123456789")) + ")"
    elif len(groups) > 3 and groups[3] == key:
        key = f"{key})"
    text = _inline_note_math(groups[-1].strip())
    if key.startswith("*") and len(re.findall(r"\*+", re.sub(r"\$[^$]*\$", "", text))) % 2:
        text = f"*{text}"
    return key, text


def _split_mid_page_notes(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Cut note lines that OCR left above body text, with the lines that continue them.

    A note ending in a colon takes every line below it, such as a list of volumes."""
    lines = body.splitlines()
    notes: list[tuple[str, str]] = []
    cut: set[int] = set()
    i = 0
    while i < len(lines):
        m = _note_line(lines[i].strip(), "symbol")
        if not m:
            i += 1
            continue
        key, text = _note(m)
        takes_all = text.endswith(":")
        cut.add(i)
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if nxt and (_note_line(nxt, "symbol") or not (takes_all or NOTE_CONTINUATION_RE.match(nxt))):
                break
            if nxt:
                text = f"{text} {nxt}"
            cut.add(i)
            i += 1
        notes.append((key, text))
    return "\n".join(ln for k, ln in enumerate(lines) if k not in cut), notes


def split_page_footnotes(md: str, style: str, folio_pattern: str) -> tuple[str, list[tuple[str, str]]]:
    """Cut the run of note lines, and the rule above it, off the bottom of a page.

    In symbol books, also cut notes that OCR placed above the page's last body text."""
    body, notes = _split_foot_notes(md, style, folio_pattern)
    if style != "symbol":
        return body, notes
    body, mid_page = _split_mid_page_notes(body)
    return body, mid_page + notes


def has_circled_footnotes(md: str, folio_pattern: str) -> bool:
    """Whether the page ends in circled note lines whose marks the body also calls, such as "估算①" and "① Romer"."""
    body, notes = split_page_footnotes(md, "circled", folio_pattern)
    return bool(notes) and all(key in CIRCLED_DIGITS and key in body for key, _ in notes)


def _uncalled_circled(m: re.Match[str], above: list[str]) -> bool:
    key = _note(m)[0]
    return key in CIRCLED_DIGITS and not any(key in line.lstrip()[1:] for line in above)


def _split_foot_notes(md: str, style: str, folio_pattern: str) -> tuple[str, list[tuple[str, str]]]:
    lines = md.splitlines()
    notes: list[tuple[str, str]] = []
    kept = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.strip() and not re.match(folio_pattern, ln.strip(), re.IGNORECASE)]
    for (i, lt), (_, after) in pairwise(kept):
        if FOOTNOTE_RULE_RE.match(lt) and _note_line(after, style, below_rule=True):
            for _, below in kept[kept.index((i, lt)) + 1 :]:
                if m := _note_line(below, style, below_rule=True):
                    notes.append(_note(m))
                else:
                    notes[-1] = (notes[-1][0], _inline_note_math(f"{notes[-1][1]} {below}"))
            return "\n".join(lines[:i]), notes
    if style == "circled":
        for idx, (i, lt) in enumerate(kept):
            in_display = "\n".join(lines[:i]).count("$$") % 2 == 1
            m_note = _note_line(lt, style, below_rule=True)
            if not in_display and m_note and not _uncalled_circled(m_note, lines[:i]) and not any(
                re.match(r"^(?:#+\s+|\d{1,3}\.\s+\S)", below) for _, below in kept[idx + 1 :]
            ):
                for _, below in kept[idx:]:
                    if m := _note_line(below, style, below_rule=True):
                        notes.append(_note(m))
                    elif re.match(r"^(\d{1,2})\)\s+(\S.*)$", below) and re.search(
                        rf"(?:\^\{{?\s*{below.split(')', 1)[0]}\)\s*\}}?|[{SUPERSCRIPT_DIGITS}]+\))",
                        "\n".join(lines[:i]),
                    ):
                        m_ed = re.match(r"^(\d{1,2})\)\s+(\S.*)$", below)
                        if m_ed:
                            notes.append((f"{m_ed.group(1)})", _inline_note_math(m_ed.group(2).strip())))
                    else:
                        notes[-1] = (notes[-1][0], _inline_note_math(f"{notes[-1][1]} {below}"))
                return "\n".join(lines[:i]), notes
    end = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        lt = lines[i].strip()
        if not lt or re.match(folio_pattern, lt, re.IGNORECASE):
            continue
        m = _note_line(lt, style)
        if not m or (style == "circled" and _uncalled_circled(m, lines[:i])):
            if notes and FOOTNOTE_RULE_RE.match(lt):
                end = i
            break
        notes.append(_note(m))
        end = i
    return "\n".join(lines[:end]), notes[::-1]


def _footnote_call(s: str, key: str, style: str) -> re.Match[str] | None:
    if style == "superscript":
        digits = key.translate(str.maketrans(SUPERSCRIPT_DIGITS, "0123456789"))
        sup = f"[{SUPERSCRIPT_DIGITS}]"
        return re.search(rf"(?<!{sup}){re.escape(key)}(?!{sup})|\$\^\{{?{digits}\}}?\$", s)
    if style == "paren":
        sup = key.translate(str.maketrans("0123456789", SUPERSCRIPT_DIGITS))
        return re.search(rf"\$\^\{{?\(?{key}\)\}}?\$|\$\^\{{?{key}\}}?\)\$|{sup}[)⁾]", s)
    if style == "parenthesized":
        return re.search(rf"\s?\$\^\{{?\({key}\)\}}?\$", s)
    if style == "circled":
        if key.endswith(")"):
            num = key[:-1]
            sup = num.translate(str.maketrans("0123456789", SUPERSCRIPT_DIGITS))
            return re.search(rf"\s?\$\^\{{?\s*\(?{num}\)\s*\}}?\$|\^\{{?\s*{num}\)\s*\}}?|{sup}[)⁾]", s)
        num = str(CIRCLED_DIGITS.index(key) + 1) if key in CIRCLED_DIGITS else key
        k_char = CIRCLED_DIGITS[int(num) - 1] if num.isdigit() and 1 <= int(num) <= 20 else key
        exact = re.search(
            rf"\s?\$(?!\$)(?:\^\{{?(?:\\text\{{)?|\\text\{{)?{re.escape(k_char)}\}}?\}}?\$(?!\$)"
            rf"|\s?\^\{{?(?:\\text\{{)?{re.escape(k_char)}\}}?\}}?"
            rf"|\s?\\text\{{{re.escape(k_char)}\}}"
            rf"|{re.escape(k_char)}",
            s,
        ) or re.search(rf"\s?\$(?!\$)\^\{{?\({num}\)\}}?\$(?!\$)|\^\{{?\({num}\)\}}?", s)
        if exact:
            return exact
        return re.search(
            r"\s?\$(?!\$)\^(?:\{?\\text\{[⊙①-⑳]\}|\{\\(?:odot|ominus|oplus|circ)\}|\\(?:odot|ominus|oplus|circ))\}?\$(?!\$)"
            r"|\s?\^(?:\{?\\text\{[⊙①-⑳]\}|\{\\(?:odot|ominus|oplus|circ)\}|\\(?:odot|ominus|oplus|circ))\}?"
            r"|\s*\\(?:odot|ominus|oplus|circledast)"
            r"|\$(?!\$)\\circledast\$(?!\$)",
            s,
        )
    if key.startswith("*"):
        for m in re.finditer(rf"(?<!\*)\*+(?=[\s,.;:)]|$)|\$\^\{{?{re.escape(key)}\}}?\$", s):
            line = s[s.rfind("\n", 0, m.start()) + 1 : m.start()]
            outside_math = m.group(0).startswith("$") or len(re.findall(r"(?<!\\)\$", line)) % 2 == 0
            if m.group(0).strip("$^{}") == key and outside_math and len(re.findall(r"\*+", line)) % 2 == 0:
                return m
        return None
    if key == "§":
        return re.search(r"(?<=\S)§(?=[\s,.;:)]|$)", s)
    return re.search(rf"{re.escape(key)}|\$\^?\{{?\\dagger\}}?\$", s)


def attach_footnotes(s: str, notes: list[tuple[str, str]], style: str) -> str:
    if style == "symbol":
        s = re.sub(
            r"(\S)(\s*\n\s*\$\$(?:(?!\$\$).)*?)\s*\\dagger\s*(\$\$)",
            r"\1†\2\n\3",
            s,
            flags=re.DOTALL,
        )
        s = re.sub(r"\s*\\dagger\s*\$", "$†", s)
    for key, text in notes:
        note = f"@@FNSTART@@{text}@@FNEND@@"
        call = _footnote_call(s, key, style)
        if call:
            clean_s = s[: call.start()] + s[call.end() :]
            pos = call.start()
            for m in re.finditer(r"\$\$[\s\S]*?\$\$|(?<!\\)\$(?:[^$\n\\]|\\.)+\$", clean_s):
                if m.start() <= pos < m.end():
                    pos = m.end()
                    break
            s = clean_s[:pos] + note + clean_s[pos:]
        else:
            s = s + note
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
    r"\s*(?P<note>\([^()]{1,60}\))?\s*(?:\*\*)?(?P<dot2>\.)?(?:\*\*)?\s*(?P<rest>.*)$",
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

SCANNER_WATERMARK_RE = re.compile(r"ClibPDF\s*-\s*www\.[\w.]+\.(?:com|net)[;,]?[ \t]*")
DISPLAY_TO_BLANK_LINE_RE = re.compile(r"\$\$(.*?)(?:\$\$|(?=\n[ \t]*\n)|\Z)", re.DOTALL)
DISPLAY_TAG_RE = re.compile(r"(?:\\tag\{[^{}]*\}|\(\d+(?:\.\d+)*[a-z]?\))\s*$")
TEXT_MACRO_RE = re.compile(r"\\(?:text|textrm|mbox)\{")
MATH_EDGE_SPACING_RE = re.compile(r"^(?:\s|\\[,;:! ]|\\q?quad\b)+|(?:\s|\\[,;:! ]|\\q?quad\b)+$")


def _math_and_text_pieces(body: str) -> list[tuple[bool, str]]:
    pieces: list[tuple[bool, str]] = []
    pos = 0
    while m := TEXT_MACRO_RE.search(body, pos):
        depth, end = 1, m.end()
        while end < len(body) and depth:
            depth += {"{": 1, "}": -1}.get(body[end], 0)
            end += 1
        pieces += [(True, body[pos : m.start()]), (False, body[m.end() : end - 1])]
        pos = end
    return [*pieces, (True, body[pos:])]


def prose_displays_to_paragraphs(md: str) -> str:
    """Turn a display whose \\text{} parts hold a sentence back into a paragraph with inline math."""

    def rewrite(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        if "\\begin{" in body or "\\\\" in body or DISPLAY_TAG_RE.search(body):
            return m.group(0)
        pieces = _math_and_text_pieces(body)
        if any(
            p.replace(r"\{", "").replace(r"\}", "").count("{") != p.replace(r"\{", "").replace(r"\}", "").count("}")
            for is_math, p in pieces
            if is_math
        ):
            return m.group(0)
        if sum(len(text.split()) for is_math, text in pieces if not is_math) < 8:
            return m.group(0)
        words = []
        for is_math, part in pieces:
            part = MATH_EDGE_SPACING_RE.sub("", part) if is_math else part.strip()
            if part:
                words.append(f"${part}$" if is_math else part)
        return "\n\n" + " ".join(" ".join(words).split()) + "\n\n"

    out = DISPLAY_TO_BLANK_LINE_RE.sub(rewrite, md)
    return re.sub(r"\n{3,}", "\n\n", out).strip("\n") if out != md else md
END_MATTER_HEADING_RE = re.compile(
    r"^\**(?:summary|exercises|problems|notes)\**$", re.IGNORECASE
)


FIGURE_LABEL_RE = re.compile(
    r"^(?![#*>]|\$\$|\\\[|\(\d+\.\d+\))[^\n]{1,60}(?<![.:;?!,。：；？！，])\s*$"
)
FIGURE_SOURCE_OR_NOTE_RE = re.compile(r"^\s*[（(]?\s*(?:资料来源|注)\s*[：:]")


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


class CleanPage(NamedTuple):
    body: str
    top_figures: list[Figure]
    bottom_figures: list[Figure]


class PageCleaner:
    def __init__(self, spec: "MonographSpec", theorem_heads: tuple[str, ...], asset_root: Path) -> None:
        self.spec: MonographSpec = spec
        self.theorem_heads: tuple[str, ...] = theorem_heads
        self.asset_root: Path = asset_root
        self._seen_sections: set[str] = set()
        self._caption_re: re.Pattern[str] = re.compile(
            spec.figures.caption_pattern,
            re.IGNORECASE if spec.figures.caption_ignore_case else 0,
        )
        self._chapter_starts: frozenset[int] = frozenset(
            c.start_page for c in spec.chapters
        )
        self._chapter_figures: dict[str, ExtractedFigure] = {
            fid: f for fid, f in manifest_figures(asset_root / FIGURES_MANIFEST_NAME).items() if "-" in fid
        }

    @classmethod
    def for_spec(cls, spec: "MonographSpec", asset_root: Path = Path()) -> "PageCleaner":
        domain = resolve_composition(publisher=spec.publisher_key, lang=spec.lang, domain=spec.domain).domain
        return cls(spec, domain.theorem_heads, asset_root)

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
        m_sec_hdr = re.match(r"^(?:#+\s*)?([0-9A-Z]+\.\d+)\.?\s+(.+?)(?:\s+\d{1,3})?$", lt)
        sec_id = m_sec_hdr.group(1) if m_sec_hdr else ""
        known_section = sec_id in spec.sections and self._section_in_chapter(sec_id, pno)
        if known_section and lines_so_far <= 2:
            return sec_id in self._seen_sections
        if lines_so_far <= (2 if zone is None else zone):
            if any(re.match(rx, lt, re.IGNORECASE) for rx in spec.running_header_regexes):
                return True
            if any(re.match(rx, lt, re.IGNORECASE) for rx in spec.drop_line_regexes):
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
        m_para = re.match(r"^§\s*(\d+(?:\.\d+)*)", inner_h)
        if m_para:
            key = f"{self._chapter_of(pno)}:§{m_para.group(1)}"
            if key in self._seen_sections:
                return ""
            self._seen_sections.add(key)
            return f"## {inner_h}"
        if re.match(r"^Proof\b", inner_h, re.IGNORECASE):
            return f"*{inner_h}*"
        thm_heads = "|".join(
            (*self.theorem_heads, r"Weyl['’]s Lemma")
        )
        if thm_heads and re.match(rf"^(?:{thm_heads})\b", inner_h):
            return (
                f"**{inner_h}**" if inner_h.endswith((".", ":")) else f"**{inner_h}.**"
            )
        if inner_h.startswith("R.H. "):
            return ""
        if len(inner_h) > 90:
            return inner_h
        key = f"heading:{inner_h}"
        if key in self._seen_sections:
            return ""
        self._seen_sections.add(key)
        return f"### {inner_h}"

    def _drop_missing_images(self, text: str) -> str:
        """Drop OCR-emitted image refs whose file is not on disk; real figures are re-added from captions."""

        def keep(match: re.Match[str]) -> str:
            target = match.group(1)
            if Path(target).exists() or (self.asset_root / target).exists():
                return match.group(0)
            return ""

        return _MD_IMAGE_RE.sub(keep, text)

    def clean(self, md_text: str, pno: int) -> CleanPage:
        spec = self.spec
        layout = spec.figures
        if spec.repair_math:
            md_text = repair_page_math(md_text)
        md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)
        md_text = SCANNER_WATERMARK_RE.sub("", md_text)
        md_text = re.sub(r"(?<!\\)\${3,}", "", md_text)
        if len(re.findall(r"(?<!\\)\$\$", md_text)) % 2:
            tail = re.match(r"\s*\$?((?:(?!\n\s*\n)[^$])+)\$\$", md_text)
            if tail and re.search(r"[\\&{}^_]", tail.group(1)):
                md_text = "$$" + md_text[tail.start(1) :]
            elif foot := re.search(r"(?:^|\n\s*\n)\s*\$\$\s*$", md_text):
                md_text = md_text[: foot.start()]
        md_text = re.sub(r"\\\(\s*((?:(?!\n\n).)+?)\s*\\\)", r"$\1$", md_text, flags=re.DOTALL)
        md_text = prose_displays_to_paragraphs(md_text)
        md_text = normalize_html_tables(md_text)
        footnotes: list[tuple[str, str]] = []
        if spec.footnote_style:
            md_text, footnotes = split_page_footnotes(md_text, spec.footnote_style, spec.folio_pattern)
        body_lines: list[str] = []
        top_figs: list[Figure] = []
        bot_figs: list[Figure] = []
        seen_figs_on_page: set[str] = set()
        caption_rest = ""

        for line in md_text.splitlines():
            lt = line.strip()
            if not lt:
                body_lines.append("")
                continue
            squeezed = re.sub(r"\s+", "", lt.replace("**", ""))
            if caption_rest and caption_rest.startswith(squeezed):
                caption_rest = caption_rest[len(squeezed):]
                while body_lines and not body_lines[-1].strip():
                    _ = body_lines.pop()
                continue
            caption_rest = ""
            if re.match(spec.folio_pattern, lt, re.IGNORECASE):
                continue
            lines_so_far = len([b for b in body_lines if b.strip()])
            if self._is_page_furniture(lt, pno, lines_so_far):
                continue

            m_fig = self._caption_re.match(lt)
            listed = None
            if m_fig:
                title = m_fig.groupdict().get("title") or ""
                chapter = m_fig.groupdict().get("chapter")
                listed = self._chapter_figures.get(f"{chapter}-{m_fig.group('number')}") if chapter else None
                manifest_page = listed.source_page if listed else None
                if manifest_page is not None and manifest_page != pno or title and (
                    (manifest_page is None and len(title) > 50)
                    or any(w in title for w in ["所示为", "体现了", "表明", "可知", "指出", "解释为"])
                    or title.endswith("。")
                ):
                    m_fig = None
            if m_fig:
                while body_lines and (
                    not body_lines[-1].strip() or FIGURE_LABEL_RE.match(body_lines[-1])
                ):
                    if body_lines[-1].strip() and (
                        not _is_isolated(body_lines) or FIGURE_SOURCE_OR_NOTE_RE.match(body_lines[-1])
                    ):
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
                chapter = m_fig.groupdict().get("chapter")
                number = m_fig.group("number")
                fid = f"{chapter}_{number}" if chapter else number
                if fid not in seen_figs_on_page:
                    seen_figs_on_page.add(fid)
                    tail = (m_fig.groupdict().get("tail") or m_fig.groupdict().get("title") or "").strip()
                    if "{chapter}" in layout.caption_format and not chapter:
                        cap = f"图 {number}" if "图" in lt else f"Figure {number}"
                    elif "图" in lt and not layout.caption_format.startswith("图"):
                        cap = f"图 {chapter}-{number}"
                    else:
                        cap = layout.caption_format.format(chapter=chapter or "", number=number)
                    if tail:
                        sep = " " if cap.endswith((".", ":")) or cap.startswith("图") else ". "
                        cap = f"{cap}{sep}{tail}"
                    whole = re.sub(r"\s+", "", listed.caption) if listed else ""
                    if listed and len(whole) > len(squeezed) and whole.startswith(squeezed):
                        cap = listed.caption
                        caption_rest = whole[len(squeezed):]
                    if spec.lang in ("zh", "ja"):
                        cap = cap.replace("~", "～")
                    if lines_so_far <= layout.top_zone_lines or pno in layout.top_pages:
                        top_figs.append((fid, cap))
                    else:
                        bot_figs.append((fid, cap))
                continue

            if spec.normalize_headings:
                heading = self._normalized_heading(lt, pno) if spec.heading_hook is not None else None
                if (
                    heading is None
                    and pno in self._chapter_starts
                    and not any(b.strip() and not b.startswith("#") for b in body_lines)
                    and re.match(r"^#\s+(?:Chapter\s+\d+|\d+\s+.*)", lt, re.IGNORECASE)
                    and not re.match(r"^#*\s*(?:[0-9A-Z]+\.\d+|§)", lt)
                ):
                    continue
                if heading is None and spec.heading_hook is None:
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
        s = _DOUBLE_BACKSLASH_MACRO_RE.sub(r"\\", s)
        s = _OPEN_EQNUM_SPACE_RE.sub(r"(\1.\2)", s)
        s = self._drop_missing_images(s)
        s = _fix_inline_math_delimiters(s)
        s = _DOUBLE_SUBSCRIPT_RE.sub(r"\1{}_", s)
        s = _STAR_DOUBLE_SUPERSCRIPT_RE.sub(
            lambda m: "^{" + "*" + m.group(2).strip("{}") + "}_{" + m.group(1) + "}", s
        )
        if spec.lang in ("zh", "ja"):
            def _replace_cjk_prose(m: re.Match[str]) -> str:
                if m.group(0).startswith("$"):
                    return m.group(0)
                txt = m.group(0).replace("~", "～")
                return re.sub(r"(?<=[，。；：\s（\[])\((\d{1,2})\)(?=[\s\u4e00-\u9fff，。；：])", r"（\1）", txt)
            s = re.sub(r"\$\$[\s\S]*?\$\$|(?<!\\)\$(?:[^$\n\\]|\\.)+\$|[^$]+", _replace_cjk_prose, s)
        for pattern, repl in spec.page_fixups.get(pno, ()):
            rep_arg = (
                repl if re.search(r"\\[1-9]|\\g<", repl) else (lambda _, r=repl: r)
            )
            s = re.sub(pattern, rep_arg, s, flags=re.DOTALL)
        if footnotes:
            s = attach_footnotes(s, footnotes, spec.footnote_style)
        if spec.equation_numbering == "page":
            s = _label_page_equations(s, self._chapter_of(pno), pno)
        elif spec.equation_numbering == "section":
            s = _label_section_equations(s, pno, deep=spec.cross_references)
        bot_figs.extend(spec.extra_figures.get(pno, ()))
        bot_figs.extend(
            (fid.replace("-", "_", 1), f.caption)
            for fid, f in self._chapter_figures.items()
            if f.source_page == pno and fid.replace("-", "_", 1) not in seen_figs_on_page
        )
        return CleanPage(s.strip(), top_figs, bot_figs)
