"""Set each theorem-like statement in the book's statement style, as its scan prints it.

The OCR marks the scan's italic only in patches, so the style comes from the statement's kind, not from
the transcript's marks. A statement runs from its run-in head to the end of that paragraph, then through
the items that follow it in order: (i), (ii), (iii) or (a), (b) or 1), 2). An item out of order, such as
a proof that starts "(i) has already been proved", ends it.
"""

import re

STATEMENT_KINDS = (
    "Theorem",
    "Lemma",
    "Corollary",
    "Proposition",
    "Conjecture",
    "Axiom",
    "Claim",
    "Fact",
    "Théorème",
    "Lemme",
    "Corollaire",
    "定理",
    "引理",
    "推论",
    "命题",
    "定义",
)
_HEAD_RE = re.compile(
    rf"^(?P<head>\*\*(?:{'|'.join(STATEMENT_KINDS)})(?![a-zà-ÿ])[^*\n]{{0,24}}\*\*(?:\s*\([^()\n]{{1,60}}\)\.?)?)"
    r"\s+(?P<rest>\S.*)$",
    re.IGNORECASE,
)
_ATTRIBUTION_RE = re.compile(r"^\([^()\n]{1,60}\)\.?$")
_RUN_IN_RE = re.compile(r"^\*{1,2}[^*\n]{1,24}\.\*{1,2}")
_ITEM_RE = re.compile(
    r"^(?P<label>\(?(?P<n>[ivx]{1,4}|[a-h]|\d{1,2})\))\s+(?P<rest>\S.*)$"
)
_MATH_RE = re.compile(r"\$\$.*?\$\$|(?<!\\)\$(?:[^$\\]|\\.)+\$")
_DISPLAY_RE = re.compile(r"\$\$|\\\[|\\begin\{")
_ITALIC_RE = re.compile(r"(?<![*(])\*(?![*)])")
_BOLD_RE = re.compile(r"\*\*")
_ROMAN = {"i": 1, "v": 5, "x": 10}
_MARKS = {"italic": "*", "bold": "**"}


def style_statements(text: str, style: str) -> str:
    """Return `text` with every statement set in `style`: "italic", "bold", or "upright" (unchanged)."""
    if style not in _MARKS:
        return text
    mark = _MARKS[style]
    lines = text.split("\n")
    expected: tuple[str, int] | None = None
    closer = ""
    body_below = False
    for i, line in enumerate(lines):
        if closer:
            if (
                not line.strip()
                or closer == "$$"
                and line.count("$$") % 2
                or closer != "$$"
                and closer in line
            ):
                closer = ""
            continue
        closer = _display_closer(line)
        if closer:
            body_below = False
            continue
        if not line.strip():
            continue
        if head := _HEAD_RE.match(line):
            body_below = bool(_ATTRIBUTION_RE.match(head["rest"]))
            if not body_below and not _DISPLAY_RE.search(head["rest"]):
                lines[i] = f"{head['head']} {_wrap(head['rest'], mark)}"
            expected = ("", 1)
            continue
        if expected is None or _DISPLAY_RE.match(line.lstrip()):
            continue
        item = _ITEM_RE.match(line)
        if body_below and not item and not _RUN_IN_RE.match(line):
            lines[i] = _wrap(line, mark)
            body_below = False
            continue
        body_below = False
        if item and (
            _DISPLAY_RE.search(item["rest"])
            or _MATH_RE.fullmatch(item["rest"].rstrip(" .,;"))
        ):
            continue
        place = _place(item["n"]) if item else None
        if (
            item
            and place
            and (expected[0] in ("", place[0]))
            and place[1] == expected[1]
        ):
            lines[i] = f"{item['label']} {_wrap(item['rest'], mark)}"
            expected = (place[0], place[1] + 1)
            continue
        expected = None
    return "\n".join(lines)


def _display_closer(line: str) -> str:
    """The text that ends the display `line` opens and leaves open, or "" when it opens none."""
    if line.count("$$") % 2:
        return "$$"
    if "$$" in line:
        return ""
    if "\\[" in line and "\\]" not in line:
        return "\\]"
    if (
        env := re.search(r"\\begin\{([^}]+)\}", line)
    ) and f"\\end{{{env[1]}}}" not in line:
        return f"\\end{{{env[1]}}}"
    return ""


def _place(n: str) -> tuple[str, int]:
    if set(n) <= set(_ROMAN) and (len(n) > 1 or n in "ivx"):
        values = [_ROMAN[c] for c in n]
        return (
            "roman",
            sum(-v if v < w else v for v, w in zip(values, [*values[1:], 0])),
        )
    if n.isdigit():
        return ("digit", int(n))
    return ("letter", ord(n) - ord("a") + 1)


def _wrap(rest: str, mark: str) -> str:
    """`rest` without its own `mark` emphasis outside math, wrapped once in `mark`; other emphasis stays."""

    def strip(text: str) -> str:
        return _ITALIC_RE.sub("", text) if mark == "*" else _BOLD_RE.sub("", text)

    parts, last = [], 0
    for m in _MATH_RE.finditer(rest):
        parts.append(strip(rest[last : m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(strip(rest[last:]))
    plain = "".join(parts).strip()
    return f"{mark}{plain}{mark}" if plain else rest
