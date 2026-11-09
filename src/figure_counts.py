"""Counts of how a rebuilt book's Typst source sets its figures and diagrams."""

import re
from collections import Counter

_MATH_RE = re.compile(r'(?<!\\)\$(?:\\.|"(?:\\.|[^"\\])*"|[^$\\"])*\$', re.DOTALL)
_ROW_BREAK_RE = re.compile(r"\\\s*\n|;")
_VERTICAL_RE = re.compile(r"arrow\.[bt](?:[lr])?(?![a-z])|[↓↑↘↙↗↖]")
_HORIZONTAL_RE = re.compile(r"arrow\.[rl](?![a-z])|arrow\.[rl]\.|-->|->|<-|[⟶⟵→←↦↪↩]|x r i g h t|x l e f t")
_RASTER_RE = re.compile(r'image\("[^"\n]*?\.(?:png|jpe?g)"')
_VECTOR_RE = re.compile(r'image\("[^"\n]*?\.(?:svg|pdf)"|include "[^"\n]*?\.typ"|fletcher\.diagram\(')


def figure_counts(typst: str) -> Counter[str]:
    """DIAGRAM_AS_ARRAY: math with rows, a vertical arrow and a horizontal arrow, which fletcher should draw.
    RASTER_FIGURE and VECTOR_FIGURE: placed images and drawings by kind."""
    counts: Counter[str] = Counter(DIAGRAM_AS_ARRAY=0)
    for m in _MATH_RE.finditer(typst):
        math = m.group()
        if "fletcher." in math:
            continue
        if _ROW_BREAK_RE.search(math) and _VERTICAL_RE.search(math) and _HORIZONTAL_RE.search(math):
            counts["DIAGRAM_AS_ARRAY"] += 1
    counts["RASTER_FIGURE"] = len(_RASTER_RE.findall(typst))
    counts["VECTOR_FIGURE"] = len(_VECTOR_RE.findall(typst))
    return counts
