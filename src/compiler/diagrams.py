"""Commutative diagrams that OCR wrote as a LaTeX `array`, drawn with the fletcher package.

OCR puts objects and horizontal arrows on one row and the vertical or slanted arrows on the row between.
A cell in that row with text and no arrow, such as `\\pi`, is the label of a vertical arrow whose bar OCR lost."""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image

FLETCHER_IMPORT = '#import "@preview/fletcher:0.5.8" as fletcher\n'
SCAN_DIAGRAM_LATEX = r"\usepackage{graphicx}\usepackage[export]{adjustbox}\newcommand{\scandiagram}[1]{\includegraphics[max width=\linewidth,max height=0.45\textheight,keepaspectratio]{figures/fig_#1.png}}"
SCAN_DIAGRAM_RE = re.compile(r"\\scandiagram\{(\d+_\d+)\}")
DISPLAY_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)

_ARRAY_RE = re.compile(r"^\\begin\{array\}\{[clr|\s]*\}(.*)\\end\{array\}$", re.DOTALL)
_HORIZONTAL = {
    "xrightarrow": "->", "xleftarrow": "<-", "longrightarrow": "->", "rightarrow": "->", "to": "->",
    "longleftarrow": "<-", "leftarrow": "<-", "hookrightarrow": "hook->", "twoheadrightarrow": "->>",
    "mapsto": "|->", "longmapsto": "|->",
}
_SLANTED = {
    "downarrow": (0, False), "uparrow": (0, True), "searrow": (1, False), "swarrow": (-1, False),
    "nwarrow": (-1, True), "nearrow": (1, True),
}
_HORIZONTAL_RE = re.compile(rf"^\\({'|'.join(_HORIZONTAL)})(?![A-Za-z])\s*(?:\[[^\]]*\])?\s*")
_SLANTED_RE = re.compile(rf"(?:\\[Bb]ig{{1,2}}\s*)?\\({'|'.join(_SLANTED)})(?![A-Za-z])")

Point = tuple[int, int]


@dataclass(frozen=True)
class Arrow:
    source: Point
    target: Point
    tip: str
    label: str
    side: Literal["left", "right"]


@dataclass(frozen=True)
class Diagram:
    nodes: tuple[tuple[Point, str], ...]
    arrows: tuple[Arrow, ...]

    def math(self) -> list[str]:
        return [body for _, body in self.nodes] + [a.label for a in self.arrows if a.label]


def _split_top(s: str, sep: str) -> list[str]:
    parts, depth, start, i = [], 0, 0, 0
    while i < len(s):
        if s[i] == "\\" and not s.startswith(sep, i):
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
        elif depth == 0 and s.startswith(sep, i):
            parts.append(s[start:i])
            start = i = i + len(sep)
            continue
        i += 1
    return [*parts, s[start:]]


def _braced(s: str) -> str:
    s = s.strip().lstrip("^_").strip()
    return s[1:-1].strip() if s.startswith("{") and s.endswith("}") else s


def _side(source: Point, target: Point, toward: Point) -> Literal["left", "right"]:
    """Fletcher puts a label left or right of the direction of travel; `toward` is where it should go on the page."""
    dx, dy = target[0] - source[0], target[1] - source[1]
    return "left" if toward[0] * dy - toward[1] * dx > 0 else "right"


def parse_array_diagram(latex: str) -> Diagram | None:
    """Read an `array` whose rows alternate objects and arrows, or None when it is not such a diagram."""
    m = _ARRAY_RE.match(latex.strip())
    if not m:
        return None
    rows = [[c.strip() for c in _split_top(r, "&")] for r in _split_top(m.group(1), r"\\")]
    rows = [r for r in rows if any(r)]
    if len(rows) < 3:
        return None
    width = max(map(len, rows))
    rows = [r + [""] * (width - len(r)) for r in rows]
    slanted_rows = {y for y, r in enumerate(rows) if any(_SLANTED_RE.search(c) for c in r)}
    if not slanted_rows and not any(_HORIZONTAL_RE.match(c) for r in rows for c in r):
        return None
    arrow_rows = slanted_rows or {
        y for y in range(1, len(rows) - 1) if not any(_HORIZONTAL_RE.match(c) for c in rows[y])
    }
    if any(y - 1 in arrow_rows or y in (0, len(rows) - 1) for y in arrow_rows):
        return None
    nodes: dict[Point, str] = {}
    for y, row in enumerate(rows):
        if y not in arrow_rows:
            nodes |= {(x, y): c for x, c in enumerate(row) if c and not _HORIZONTAL_RE.match(c)}
    arrows: list[tuple[Point, Point, str, str, Point]] = []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if not cell:
                continue
            if y not in arrow_rows:
                if not (h := _HORIZONTAL_RE.match(cell)):
                    continue
                left = max((p for p in nodes if p[1] == y and p[0] < x), default=None)
                right = min((p for p in nodes if p[1] == y and p[0] > x), default=None)
                if left is None or right is None or cell[h.end() :].strip()[:1] not in ("", "{"):
                    return None
                tip = _HORIZONTAL[h.group(1)]
                source, target = (right, left) if tip == "<-" else (left, right)
                toward = (0, 1) if y == len(rows) - 1 else (0, -1)
                arrows.append((source, target, tip.replace("<-", "->"), _braced(cell[h.end() :]), toward))
                continue
            v = _SLANTED_RE.search(cell)
            dx, upward = _SLANTED[v.group(1)] if v else (0, False)
            before = cell[: v.start()].strip() if v else cell
            after = _braced(cell[v.end() :]) if v else ""
            down_dx = -dx if upward else dx
            above = [p for p in nodes if p[1] == y - 1 and (p[0] - x) * down_dx <= 0 and (down_dx or p[0] == x)]
            below = [p for p in nodes if p[1] == y + 1 and (p[0] - x) * down_dx >= 0 and (down_dx or p[0] == x)]
            if not above or not below:
                return None
            top = min(above, key=lambda p: abs(p[0] - x))
            bottom = min(below, key=lambda p: abs(p[0] - x))
            source, target = (bottom, top) if upward else (top, bottom)
            arrows.append((source, target, "->", after or before, (1, 0) if after else (-1, 0)))
    if not arrows:
        return None
    cols = {x: i for i, x in enumerate(sorted({p[0] for p in nodes}))}
    lines = {y: i for i, y in enumerate(sorted({p[1] for p in nodes}))}

    def place(p: Point) -> Point:
        return cols[p[0]], lines[p[1]]

    return Diagram(
        tuple((place(p), body) for p, body in sorted(nodes.items(), key=lambda n: (n[0][1], n[0][0]))),
        tuple(
            Arrow(place(s), place(t), tip, label, _side(place(s), place(t), toward))
            for s, t, tip, label, toward in arrows
        ),
    )


def fletcher_diagram(diagram: Diagram, typst_math: Iterator[str]) -> str:
    """Typst for `diagram`, taking each node's and label's converted math from `typst_math` in `Diagram.math` order."""
    nodes = [f"  fletcher.node({p}, ${next(typst_math)}$)," for p, _ in diagram.nodes]
    edges = []
    for a in diagram.arrows:
        label = f", ${next(typst_math)}$, label-side: {a.side}" if a.label else ""
        edges.append(f'  fletcher.edge({a.source}, {a.target}, "{a.tip}"{label}),')
    body = "\n".join([*nodes, *edges])
    return f"fletcher.diagram(\n  spacing: (2.6em, 2.4em),\n  label-size: 0.85em,\n{body}\n)"


def page_diagrams(text: str) -> list[re.Match[str]]:
    """The `$$` displays on one page that are array diagrams, in reading order."""
    return [m for m in DISPLAY_RE.finditer(text) if parse_array_diagram(m.group(1).strip())]


def scan_diagram_id(page: int, k: int) -> str:
    return f"{page:03d}_{k:03d}"


def use_scan_diagrams(text: str, page: int, fig_dir: Path) -> str:
    """Put `\\scandiagram{PPP_NNN}` in place of the page's NNN-th array diagram when its snippet or crop exists."""
    out, end = [], 0
    for k, m in enumerate(page_diagrams(text), 1):
        fig = scan_diagram_id(page, k)
        if any((fig_dir / f"fig_{fig}.{ext}").exists() for ext in ("typ", "png")):
            out += [text[end : m.start()], f"$$\n\\scandiagram{{{fig}}}\n$$"]
            end = m.end()
    return "".join(out) + text[end:]


def scan_diagram_typst(fig: str, fig_dir: Path, figure_dir: str) -> str:
    """The snippet `fig_<fig>.typ` when it exists, else the 300 dpi scan crop at its printed size."""
    if (fig_dir / f"fig_{fig}.typ").exists():
        return f'#(include "{figure_dir}/fig_{fig}.typ")'
    with Image.open(fig_dir / f"fig_{fig}.png") as im:
        width = im.size[0] / 300 * 72
    return f'#image("{figure_dir}/fig_{fig}.png", width: {width:.1f}pt)'


def convert_diagrams(
    displays: list[str], convert: Callable[[list[str]], list[str]]
) -> dict[int, str]:
    """Fletcher Typst for each display in `displays` that is a diagram, keyed by its index."""
    found = {i: d for i, body in enumerate(displays) if (d := parse_array_diagram(body))}
    math = convert([m for d in found.values() for m in d.math()])
    it = iter(math)
    return {i: fletcher_diagram(d, it) for i, d in found.items()}
