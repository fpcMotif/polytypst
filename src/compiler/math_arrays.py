"""Arrays and matrices that OCR wrote for something other than a grid of math.

`array_misuses` names each one in a transcript or build source:
- MATH_ARRAY_SPEC_SHORT: a row has more cells than the column spec, so LaTeX stops on "Extra alignment tab".
- MATH_ARRAY_SEQUENCE: a one-row array of objects and arrows, an exact sequence set as a table.
- MATH_ARRAY_UNREAD_DIAGRAM: rows of objects and arrows that `parse_array_diagram` cannot read, so no diagram is drawn.
- MATH_MATRIX_EQUATIONS: a bracketed matrix whose every row is an equation.

`repair_arrays` rewrites the first two, which have one right form.
"""

import re
from dataclasses import dataclass

from .diagrams import array_rows, is_arrow_cell, is_unread_diagram

SPEC_SHORT = "MATH_ARRAY_SPEC_SHORT"
SEQUENCE = "MATH_ARRAY_SEQUENCE"
UNREAD_DIAGRAM = "MATH_ARRAY_UNREAD_DIAGRAM"
MATRIX_EQUATIONS = "MATH_MATRIX_EQUATIONS"
RULES = (SPEC_SHORT, SEQUENCE, UNREAD_DIAGRAM, MATRIX_EQUATIONS)

ARRAY_RE = re.compile(
    r"\\begin\{array\}\{(?P<spec>(?:[^{}]|\{[^{}]*\})*)\}(?P<body>.*?)\\end\{array\}"
    r"|\\begin\{(?P<env>[pbBvV]?matrix)\}(?P<mbody>.*?)\\end\{(?P=env)\}",
    re.DOTALL,
)
_EQUATION_RE = re.compile(r"(?<![<>!\\])=")


@dataclass(frozen=True)
class Misuse:
    rule: str
    line: int
    text: str


def spec_columns(spec: str) -> int | None:
    """How many columns an array spec declares, or None for a spec with `*{n}{...}` repetition."""
    if "*" in spec:
        return None
    return len(re.findall(r"[lcrpmbX]", re.sub(r"\{[^{}]*\}", "", spec)))


def _misuse(m: re.Match[str]) -> str | None:
    body = m["body"] if m["env"] is None else m["mbody"]
    rows = array_rows(body)
    if not rows:
        return None
    width = max(map(len, rows))
    if m["env"] is None and (n := spec_columns(m["spec"])) is not None and width > n:
        return SPEC_SHORT
    if any(is_arrow_cell(c) for r in rows for c in r):
        if len(rows) == 1:
            return SEQUENCE
        return UNREAD_DIAGRAM if is_unread_diagram(m[0]) else None
    if m["env"] not in (None, "matrix") and len(rows) >= 2 and all(_EQUATION_RE.search(" ".join(r)) for r in rows):
        return MATRIX_EQUATIONS
    return None


def array_misuses(text: str) -> list[Misuse]:
    """Each array or matrix in `text` that holds something other than a grid of math, with its 1-based line."""
    return [
        Misuse(rule, text.count("\n", 0, m.start()) + 1, " ".join(m[0].split())[:160])
        for m in ARRAY_RE.finditer(text)
        if (rule := _misuse(m))
    ]


def _repair(m: re.Match[str]) -> str:
    if m["env"] is not None:
        return m[0]
    rows = array_rows(m["body"])
    if len(rows) == 1 and any(is_arrow_cell(c) for c in rows[0]):
        return " ".join(c for c in rows[0] if c)
    width = max(map(len, rows), default=0)
    n = spec_columns(m["spec"])
    if n is not None and width > n:
        spec = m["spec"] + (re.findall(r"[lcr]", m["spec"]) or ["c"])[-1] * (width - n)
        return f"\\begin{{array}}{{{spec}}}{m['body']}\\end{{array}}"
    return m[0]


def repair_arrays(math: str) -> str:
    """Join a one-row array of objects and arrows into one formula, and widen a column spec to its widest row."""
    return ARRAY_RE.sub(_repair, math) if "\\begin{array}" in math else math
