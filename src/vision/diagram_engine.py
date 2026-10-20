"""Code-drawn vector diagrams: one SVG house style, geometry primitives, and a figure registry.

Every book registers `FigureSpec` entries in a `FigureBook`. `render_figures` writes
`fig_<id>.svg` for Typst `#figure` inclusion, `manifest.json`, and an interactive
gallery. Figures draw in four layers (grid, region, curve, label), which the gallery
reveals step by step.
"""

import html
import json
import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

LAYERS = ("grid", "region", "curve", "label")
INK = "#0f172a"

_ARROW_PATH = "M 0 1.2 L 8.8 5 L 0 8.8 L 2.2 5 z"
_MARKERS = (
    ("arr", INK, 6.8, 5.6, _ARROW_PATH),
    ("arr-axis", "#475569", 7.0, 5.2, "M 0 1.5 L 8.5 5 L 0 8.5 L 2.0 5 z"),
    ("arr-blue", "#1e3a8a", 6.8, 5.6, _ARROW_PATH),
    ("arr-red", "#dc2626", 6.8, 5.6, _ARROW_PATH),
    ("arr-green", "#047857", 6.8, 5.6, _ARROW_PATH),
    ("arr-amber", "#b45309", 6.8, 5.6, _ARROW_PATH),
)
_LINEAR_GRADIENTS = (
    ("bg-canvas", "#f8fafc", 0.5, "#f1f5f9", 0.3, "100%"),
    ("grad-blue", "#dbeafe", 0.78, "#bfdbfe", 0.48, "100%"),
    ("grad-amber", "#fef3c7", 0.82, "#fde68a", 0.52, "100%"),
    ("grad-green", "#d1fae5", 0.78, "#a7f3d0", 0.48, "100%"),
    ("grad-rose", "#ffe4e6", 0.78, "#fecdd3", 0.48, "100%"),
    ("grad-uhp", "#eff6ff", 0.35, "#93c5fd", 0.72, "0%"),
)


def _house_defs() -> str:
    parts: list[str] = []
    for gid, c0, o0, c1, o1, x2 in _LINEAR_GRADIENTS:
        parts.append(
            f'    <linearGradient id="{gid}" x1="0%" y1="0%" x2="{x2}" y2="100%">\n'
            f'      <stop offset="0%" stop-color="{c0}" stop-opacity="{o0}" />\n'
            f'      <stop offset="100%" stop-color="{c1}" stop-opacity="{o1}" />\n'
            "    </linearGradient>\n"
        )
    parts.append(
        '    <radialGradient id="glow-pole" cx="50%" cy="50%" r="50%">\n'
        '      <stop offset="0%" stop-color="#ef4444" stop-opacity="0.36" />\n'
        '      <stop offset="100%" stop-color="#ef4444" stop-opacity="0.0" />\n'
        "    </radialGradient>\n"
        '    <radialGradient id="grad-sphere" cx="38%" cy="32%" r="65%">\n'
        '      <stop offset="0%" stop-color="#eff6ff" stop-opacity="0.85" />\n'
        '      <stop offset="58%" stop-color="#bfdbfe" stop-opacity="0.45" />\n'
        '      <stop offset="100%" stop-color="#93c5fd" stop-opacity="0.25" />\n'
        "    </radialGradient>\n"
        '    <radialGradient id="grad-torus" cx="38%" cy="32%" r="65%">\n'
        '      <stop offset="0%" stop-color="#eff6ff" />\n'
        '      <stop offset="55%" stop-color="#bfdbfe" />\n'
        '      <stop offset="100%" stop-color="#93c5fd" />\n'
        "    </radialGradient>\n"
        '    <pattern id="grid-fine" width="24" height="24" patternUnits="userSpaceOnUse">\n'
        '      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#e2e8f0" stroke-width="0.6" />\n'
        "    </pattern>\n"
    )
    for pid, color in (("stipple", "#1e3a8a"), ("stipple-amber", "#b45309")):
        parts.append(
            f'    <pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse">\n'
            f'      <circle cx="1.5" cy="1.5" r="0.78" fill="{color}" opacity="0.38" />\n'
            f'      <circle cx="4.5" cy="4.5" r="0.78" fill="{color}" opacity="0.38" />\n'
            "    </pattern>\n"
        )
    for pid, size, angle, color, width, opacity in (
        ("hatch", 7, 45, "#1e3a8a", 1.2, 0.38),
        ("hatch-amber", 7, -45, "#b45309", 1.25, 0.38),
        ("hatch-border", 5, 45, "#475569", 1.15, 0.45),
    ):
        parts.append(
            f'    <pattern id="{pid}" width="{size}" height="{size}" patternTransform="rotate({angle} 0 0)" patternUnits="userSpaceOnUse">\n'
            f'      <line x1="0" y1="0" x2="0" y2="{size}" stroke="{color}" stroke-width="{width}" opacity="{opacity}" />\n'
            "    </pattern>\n"
        )
    for mid, color, ref_x, size, path in _MARKERS:
        parts.append(
            f'    <marker id="{mid}" viewBox="0 0 10 10" refX="{ref_x}" refY="5" markerWidth="{size}" markerHeight="{size}" orient="auto-start-reverse">\n'
            f'      <path d="{path}" fill="{color}" />\n'
            "    </marker>\n"
        )
    return "".join(parts)


_STROKE = "fill: none; stroke-linecap: round; stroke-linejoin: round;"
_FONT = '"New Computer Modern", "Latin Modern Roman", "STIX Two Math", Georgia, serif'
_HOUSE_STYLE = (
    "    .ax { stroke: #475569; stroke-width: 1.15; fill: none; }\n"
    f"    .c-main {{ stroke: {INK}; stroke-width: 1.8; {_STROKE} }}\n"
    f"    .c-blue {{ stroke: #1e3a8a; stroke-width: 1.8; {_STROKE} }}\n"
    f"    .c-red {{ stroke: #dc2626; stroke-width: 1.65; {_STROKE} }}\n"
    f"    .c-green {{ stroke: #047857; stroke-width: 1.7; {_STROKE} }}\n"
    f"    .c-amber {{ stroke: #b45309; stroke-width: 1.65; {_STROKE} }}\n"
    "    .c-dash { stroke: #64748b; stroke-width: 1.15; stroke-dasharray: 5,4; fill: none; }\n"
    "    .c-blue-dash { stroke: #1e3a8a; stroke-width: 1.25; stroke-dasharray: 5,4; fill: none; }\n"
    "    .c-red-dash { stroke: #dc2626; stroke-width: 1.25; stroke-dasharray: 4,3; fill: none; }\n"
    "    .c-green-dash { stroke: #047857; stroke-width: 1.25; stroke-dasharray: 4,3; fill: none; }\n"
    "    .c-sub { stroke: #64748b; stroke-width: 0.9; fill: none; }\n"
    "    .c-sub-blue { stroke: #3b82f6; stroke-width: 0.9; stroke-opacity: 0.48; fill: none; }\n"
    "    .c-sub-red { stroke: #ef4444; stroke-width: 0.9; stroke-opacity: 0.45; fill: none; }\n"
    "    .f-blue { fill: url(#grad-blue); }\n"
    "    .f-amber { fill: url(#grad-amber); }\n"
    "    .f-green { fill: url(#grad-green); }\n"
    "    .f-rose { fill: url(#grad-rose); }\n"
    "    .f-uhp { fill: url(#grad-uhp); }\n"
    "    .f-stipple { fill: url(#stipple); }\n"
    "    .f-hatch { fill: url(#hatch); }\n"
    "    .pt { stroke: #ffffff; stroke-width: 1.25; }\n"
    "    .pt-open { fill: #ffffff; stroke-width: 1.5; }\n"
    f"    .lbl {{ font-family: {_FONT}; font-size: 14.5px; fill: {INK}; paint-order: stroke fill; stroke: #ffffff; stroke-width: 3.2px; stroke-linejoin: round; }}\n"
    f"    .it {{ font-family: {_FONT}; font-size: 15px; font-style: italic; fill: {INK}; paint-order: stroke fill; stroke: #ffffff; stroke-width: 3.2px; stroke-linejoin: round; }}\n"
)
_HOUSE_DEFS = _house_defs()


def svg_document(
    viewbox: str,
    *,
    grid: str = "",
    region: str = "",
    curve: str = "",
    label: str = "",
    fig_id: str = "",
    title: str = "",
    show_grid: bool = True,
) -> str:
    """Wrap the four drawing layers in the house SVG scaffold."""
    vb_parts = [float(x) for x in viewbox.split()]
    vw = vb_parts[2] if len(vb_parts) == 4 else 460.0
    vh = vb_parts[3] if len(vb_parts) == 4 else 280.0
    meta_attr = f' data-fig="{fig_id}" role="img"' if fig_id else ' role="img"'
    title_el = f"  <title>{html.escape(title, quote=False)}</title>\n" if title else ""
    grid_rects = (
        f'    <rect class="canvas-bg" x="4" y="4" width="{vw - 8:.0f}" height="{vh - 8:.0f}" rx="6" fill="url(#bg-canvas)" />\n'
        f'    <rect class="canvas-grid" x="4" y="4" width="{vw - 8:.0f}" height="{vh - 8:.0f}" rx="6" fill="url(#grid-fine)" />\n'
        if show_grid
        else ""
    )
    contents = dict(zip(LAYERS, (grid_rects + grid, region, curve, label), strict=True))
    layers = "".join(
        f'  <g class="layer-{name}" data-layer="{name}" data-step="{step}">\n{contents[name]}\n  </g>\n'
        for step, name in enumerate(LAYERS, start=1)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="100%" height="100%"{meta_attr}>\n'
        f"{title_el}"
        f"  <defs>\n{_HOUSE_DEFS}  </defs>\n"
        f"  <style>\n{_HOUSE_STYLE}  </style>\n"
        f"{layers}"
        "</svg>"
    )


def figure_svg(viewbox: str, body: str, fig_id: str = "", title: str = "") -> str:
    """A figure drawn as one body, placed in the curve layer over the house grid."""
    return svg_document(viewbox, curve=body, fig_id=fig_id, title=title)


def axes_xy(
    ox: float,
    oy: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    x_label: str = "x",
    y_label: str = "iy",
    origin_label: str = "0",
    origin_dx: float = -13.0,
    origin_dy: float = 15.0,
) -> tuple[str, str]:
    """Return (axes, labels) for a 2D complex-plane frame."""
    ax_parts = [
        f'    <line x1="{x0:.1f}" y1="{oy:.1f}" x2="{x1:.1f}" y2="{oy:.1f}" class="ax" marker-end="url(#arr-axis)" />',
        f'    <line x1="{ox:.1f}" y1="{y1:.1f}" x2="{ox:.1f}" y2="{y0:.1f}" class="ax" marker-end="url(#arr-axis)" />',
    ]
    lbl_parts: list[str] = []
    if x_label:
        lbl_parts.append(
            f'    <text x="{x1 + 5:.1f}" y="{oy + 5:.1f}" class="it">{x_label}</text>'
        )
    if y_label:
        lbl_parts.append(
            f'    <text x="{ox - 18:.1f}" y="{y0 + 4:.1f}" class="it">{y_label}</text>'
        )
    if origin_label:
        lbl_parts.append(
            f'    <text x="{ox + origin_dx:.1f}" y="{oy + origin_dy:.1f}" class="lbl">{origin_label}</text>'
        )
    return "\n".join(ax_parts), "\n".join(lbl_parts)


def axes_2d(
    ox: float,
    oy: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    xlabel: str = "x",
    ylabel: str = "y",
    origin_label: str = "O",
) -> str:
    """Real-plane axes with arrowheads, axis names, and a labelled origin."""
    lines = [
        f'    <line x1="{x0:.1f}" y1="{oy:.1f}" x2="{x1:.1f}" y2="{oy:.1f}" class="ax" marker-end="url(#arr)" />',
        f'    <line x1="{ox:.1f}" y1="{y0:.1f}" x2="{ox:.1f}" y2="{y1:.1f}" class="ax" marker-end="url(#arr)" />',
    ]
    if xlabel:
        lines.append(text_label(x1 + 6, oy + 5, xlabel))
    if ylabel:
        lines.append(text_label(ox - 16, y1 + 8, ylabel))
    if origin_label:
        lines.append(labeled_point(ox, oy, origin_label, dx=-15, dy=16, r=2.8))
    return "\n".join(lines)


def axes_3d(
    ox: float,
    oy: float,
    x_vec: tuple[float, float] = (-78.0, 92.0),
    y_vec: tuple[float, float] = (185.0, 0.0),
    z_vec: tuple[float, float] = (0.0, -155.0),
    labels: tuple[str, str, str] = ("x", "y", "z"),
) -> str:
    """Oblique-projection 3D axes from origin (ox, oy)."""
    xx, xy = ox + x_vec[0], oy + x_vec[1]
    yx, yy = ox + y_vec[0], oy + y_vec[1]
    zx, zy = ox + z_vec[0], oy + z_vec[1]
    return "\n".join(
        [
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{xx:.1f}" y2="{xy:.1f}" class="ax" marker-end="url(#arr)" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{yx:.1f}" y2="{yy:.1f}" class="ax" marker-end="url(#arr)" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{zx:.1f}" y2="{zy:.1f}" class="ax" marker-end="url(#arr)" />',
            text_label(xx - 14, xy + 14, labels[0]),
            text_label(yx + 6, yy + 5, labels[1]),
            text_label(zx - 15, zy + 6, labels[2]),
            labeled_point(ox, oy, "O", dx=-16, dy=4, r=2.8),
        ]
    )


def arrow_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    cls: str = "c-main",
    marker: str = "arr",
) -> str:
    m_end = f' marker-end="url(#{marker})"' if marker else ""
    return f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}"{m_end} />'


def tangent_arrow(
    x: float, y: float, dx: float, dy: float, marker: str = "arr-blue"
) -> str:
    """An invisible stub at (x, y) whose marker shows the direction (dx, dy)."""
    norm = math.hypot(dx, dy)
    if norm < 1e-6:
        return ""
    ux, uy = dx / norm, dy / norm
    x0, y0 = x - ux * 2.5, y - uy * 2.5
    x1, y1 = x + ux * 1.5, y + uy * 1.5
    return f'    <line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" stroke="none" fill="none" marker-end="url(#{marker})" />'


def arrow_head(x: float, y: float, angle_deg: float, color: str = "#1e3a8a") -> str:
    """A filled arrowhead at (x, y) rotated by angle_deg."""
    return (
        f'    <g transform="translate({x:.1f},{y:.1f}) rotate({angle_deg:.1f})">'
        f'<path d="M -5 -3.5 L 5 0 L -5 3.5 L -2.5 0 z" fill="{color}" />'
        f"</g>"
    )


def mid_arrow_path(
    d: str,
    mx: float,
    my: float,
    dx: float,
    dy: float,
    cls: str = "c-blue",
    marker: str = "arr-blue",
) -> str:
    p = f'    <path d="{d}" class="{cls}" />'
    t = tangent_arrow(mx, my, dx, dy, marker=marker)
    return f"{p}\n{t}" if t else p


def poly_path(
    pts: Sequence[tuple[float, float]],
    cls: str = "c-blue",
    closed: bool = False,
    marker_end: str = "",
) -> str:
    if not pts:
        return ""
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(
        f"L {p[0]:.1f} {p[1]:.1f}" for p in pts[1:]
    )
    if closed:
        d += " Z"
    m_attr = f' marker-end="url(#{marker_end})"' if marker_end else ""
    return f'    <path d="{d}" class="{cls}"{m_attr} />'


def circle_contour(
    cx: float,
    cy: float,
    r: float,
    cls: str = "c-blue",
    arrow_deg: float | None = None,
    ccw: bool = True,
    marker: str = "arr-blue",
) -> str:
    parts = [f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="{cls}" />']
    if arrow_deg is not None:
        rad = math.radians(arrow_deg)
        px = cx + r * math.cos(rad)
        py = cy - r * math.sin(rad)
        sgn = 1.0 if ccw else -1.0
        parts.append(
            tangent_arrow(
                px, py, -sgn * math.sin(rad), -sgn * math.cos(rad), marker=marker
            )
        )
    return "\n".join(parts)


def arc_path(
    cx: float,
    cy: float,
    r: float,
    deg1: float,
    deg2: float,
    cls: str = "c-blue",
    ccw: bool = True,
    arrow_mid: bool = False,
    marker: str = "arr-blue",
) -> str:
    r1 = math.radians(deg1)
    r2 = math.radians(deg2)
    x1, y1 = cx + r * math.cos(r1), cy - r * math.sin(r1)
    x2, y2 = cx + r * math.cos(r2), cy - r * math.sin(r2)
    span = (deg2 - deg1) % 360.0 if ccw else (deg1 - deg2) % 360.0
    large_arc = 1 if span > 180.0 else 0
    sweep = 0 if ccw else 1
    d = f"M {x1:.2f} {y1:.2f} A {r:.2f} {r:.2f} 0 {large_arc} {sweep} {x2:.2f} {y2:.2f}"
    if not arrow_mid:
        return f'    <path d="{d}" class="{cls}" />'
    mid_deg = deg1 + (span * 0.5 if ccw else -span * 0.5)
    rm = math.radians(mid_deg)
    mx, my = cx + r * math.cos(rm), cy - r * math.sin(rm)
    sgn = 1.0 if ccw else -1.0
    return mid_arrow_path(
        d, mx, my, -sgn * math.sin(rm), -sgn * math.cos(rm), cls=cls, marker=marker
    )


def smooth_curve(
    points: list[tuple[float, float]],
    cls: str = "c-blue",
    closed: bool = False,
    fill_cls: str = "",
    arrow_indices: list[tuple[int, bool]] | None = None,
    marker: str = "arr-blue",
) -> str:
    """Catmull-Rom spline through points as cubic Béziers, with optional mid-segment arrows."""
    if len(points) < 2:
        return ""
    pts = list(points)
    n = len(pts)
    if closed:
        padded = [pts[-1]] + pts + [pts[0], pts[1]]
        count = n
    else:
        padded = [pts[0]] + pts + [pts[-1]]
        count = n - 1

    segs: list[str] = [f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"]
    mid_arrows: list[str] = []
    arrow_map = dict(arrow_indices or [])
    for i in range(count):
        p0, p1, p2, p3 = padded[i], padded[i + 1], padded[i + 2], padded[i + 3]
        c1x = p1[0] + (p2[0] - p0[0]) / 6.0
        c1y = p1[1] + (p2[1] - p0[1]) / 6.0
        c2x = p2[0] - (p3[0] - p1[0]) / 6.0
        c2y = p2[1] - (p3[1] - p1[1]) / 6.0
        segs.append(
            f"C {c1x:.2f} {c1y:.2f}, {c2x:.2f} {c2y:.2f}, {p2[0]:.2f} {p2[1]:.2f}"
        )
        if i in arrow_map:
            mx = 0.125 * p1[0] + 0.375 * c1x + 0.375 * c2x + 0.125 * p2[0]
            my = 0.125 * p1[1] + 0.375 * c1y + 0.375 * c2y + 0.125 * p2[1]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            if not arrow_map[i]:
                dx, dy = -dx, -dy
            mid_arrows.append(tangent_arrow(mx, my, dx, dy, marker=marker))
    if closed:
        segs.append("Z")
    d = " ".join(segs)
    out: list[str] = []
    if fill_cls:
        out.append(f'    <path d="{d}" class="{fill_cls}" />')
    out.append(f'    <path d="{d}" class="{cls}" />')
    out.extend(mid_arrows)
    return "\n".join(out)


def point_dot(
    x: float, y: float, color: str = INK, r: float = 3.3, open_dot: bool = False
) -> str:
    if open_dot:
        return f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" stroke="{color}" class="pt-open" />'
    return f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" class="pt" />'


def format_math_label(text: str) -> str:
    """Render primes, upright differentials, and `_x` / `_{xy}` subscripts as SVG tspans."""
    s = text.replace("''", "″").replace("'", "′")
    s = re.sub(
        r"(?<![a-zA-Z])d(?=[xyztuvwsrρθφωασ])",
        r'<tspan font-style="normal">d</tspan>',
        s,
    )
    sub = r'<tspan font-size="11px" dy="3.5" font-style="normal">\1</tspan><tspan dy="-3.5"></tspan>'
    s = re.sub(r"_\{([^}]+)\}", sub, s)
    return re.sub(r"_([0-9a-zA-Z])", sub, s)


def text_label(
    x: float,
    y: float,
    text: str,
    italic: bool = True,
    color: str = "",
) -> str:
    """A text label whose `_` subscripts and primes are typeset by `format_math_label`."""
    cls = "it" if italic else "lbl"
    fill_attr = f' fill="{color}"' if color else ""
    return f'    <text x="{x:.1f}" y="{y:.1f}" class="{cls}"{fill_attr}>{format_math_label(text)}</text>'


def labeled_point(
    x: float,
    y: float,
    label: str = "",
    dx: float = 6.0,
    dy: float = -6.0,
    color: str = INK,
    r: float = 3.2,
) -> str:
    dot = f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" class="pt" />'
    if not label:
        return dot
    return (
        dot + "\n" + text_label(x + dx, y + dy, label, color=color if color != INK else "")
    )


def math_label(
    x: float,
    y: float,
    base: str,
    sub: str = "",
    sup: str = "",
    tail: str = "",
    color: str = INK,
    italic: bool = True,
    anchor: str = "start",
    size: float = 15.0,
) -> str:
    """A label with explicit subscript, superscript, and trailing text."""
    cls = "it" if italic else "lbl"
    fill_attr = f' fill="{color}"' if color != INK else ""
    anchor_attr = f' text-anchor="{anchor}"' if anchor != "start" else ""
    size_attr = f' font-size="{size:.1f}px"' if abs(size - 15.0) > 0.2 else ""
    inner = base
    if sub:
        inner += f'<tspan font-size="10.5px" dy="3.2">{sub}</tspan>'
        if sup:
            inner += f'<tspan font-size="10.5px" dy="-8.2">{sup}</tspan>'
            if tail:
                inner += f'<tspan dy="5.0">{tail}</tspan>'
        elif tail:
            inner += f'<tspan dy="-3.2">{tail}</tspan>'
    elif sup:
        inner += f'<tspan font-size="10.5px" dy="-5.0">{sup}</tspan>'
        if tail:
            inner += f'<tspan dy="5.0">{tail}</tspan>'
    elif tail:
        inner += tail
    return f'    <text x="{x:.1f}" y="{y:.1f}" class="{cls}"{fill_attr}{anchor_attr}{size_attr}>{inner}</text>'


@dataclass(frozen=True)
class FigureSpec:
    fig_id: str
    label: str
    chapter: int
    build: Callable[[], str]
    title: str = ""


@dataclass(frozen=True)
class FigureBook:
    slug: str
    title: str
    subtitle: str
    figures: tuple[FigureSpec, ...]
    chapter_titles: dict[int, str] = field(default_factory=dict)
    scan_dir: str = ""
    search_hint: str = "Search figures..."


@dataclass(frozen=True)
class FigureAsset:
    fig_id: str
    label: str
    filename: str
    chapter: int
    chapter_title: str
    title: str
    viewbox: str
    layers: list[str]


_SVG_NS = "{http://www.w3.org/2000/svg}"


def _describe(svg: str, spec: FigureSpec) -> tuple[str, str, list[str]]:
    """Read title, viewBox, and drawing layers from the parsed SVG tree."""
    root = ET.fromstring(svg)
    title_el = root.find(f"{_SVG_NS}title")
    title = (
        spec.title
        or (title_el.text or "" if title_el is not None else "")
        or spec.label
    )
    layers = [
        g.attrib["data-layer"]
        for g in root.findall(f"{_SVG_NS}g")
        if "data-layer" in g.attrib and len(g)
    ]
    return title, root.attrib.get("viewBox", "0 0 460 280"), layers


def render_figures(
    book: FigureBook, fig_dir: Path, web_dir: Path | None = None
) -> dict[str, FigureAsset]:
    """Write each figure as `fig_<id>.svg`, plus the manifest and gallery when `web_dir` is set."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    assets: dict[str, FigureAsset] = {}
    svgs: dict[str, str] = {}
    for spec in book.figures:
        svg = spec.build()
        filename = f"fig_{spec.fig_id}.svg"
        _ = (fig_dir / filename).write_text(svg, encoding="utf-8")
        title, viewbox, layers = _describe(svg, spec)
        assets[spec.fig_id] = FigureAsset(
            fig_id=spec.fig_id,
            label=spec.label,
            filename=filename,
            chapter=spec.chapter,
            chapter_title=book.chapter_titles.get(spec.chapter, ""),
            title=title,
            viewbox=viewbox,
            layers=layers,
        )
        svgs[spec.fig_id] = svg
    if web_dir is not None:
        web_dir.mkdir(parents=True, exist_ok=True)
        for fid, svg in svgs.items():
            _ = (web_dir / assets[fid].filename).write_text(svg, encoding="utf-8")
        _ = (web_dir / "manifest.json").write_text(
            json.dumps(
                [asdict(a) for a in assets.values()], indent=2, ensure_ascii=False
            ),
            encoding="utf-8",
        )
        _ = (web_dir / "index.html").write_text(
            _gallery_html(book, assets, svgs), encoding="utf-8"
        )
    return assets


_GALLERY_CSS = """
    :root { --bg: #f8fafc; --card: #ffffff; --ink: #0f172a; --muted: #475569; --border: #e2e8f0; --stage: #ffffff; --accent: #1e3a8a; --badge-bg: #dbeafe; --badge-fg: #1e3a8a; }
    [data-theme="parchment"] { --bg: #f5f0e6; --card: #fdfaf3; --ink: #1c1917; --muted: #57534e; --border: #e5dec9; --stage: #fbf7ee; --accent: #7c2d12; --badge-bg: #fef3c7; --badge-fg: #92400e; }
    [data-theme="3b1b"] { --bg: #070b14; --card: #0f172a; --ink: #f8fafc; --muted: #94a3b8; --border: #1e293b; --stage: #090d16; --accent: #38bdf8; --badge-bg: rgba(56, 189, 248, 0.16); --badge-fg: #7dd3fc; }
    [data-theme="3b1b"] svg .canvas-bg { fill: #090d16 !important; }
    [data-theme="3b1b"] svg #grid-fine path { stroke: #1e293b !important; }
    [data-theme="3b1b"] svg .ax { stroke: #64748b !important; }
    [data-theme="3b1b"] svg .c-main { stroke: #e2e8f0 !important; }
    [data-theme="3b1b"] svg .c-blue, [data-theme="3b1b"] svg .c-blue-dash, [data-theme="3b1b"] svg .c-sub-blue { stroke: #38bdf8 !important; }
    [data-theme="3b1b"] svg .c-red, [data-theme="3b1b"] svg .c-red-dash, [data-theme="3b1b"] svg .c-sub-red { stroke: #fb7185 !important; }
    [data-theme="3b1b"] svg .c-green, [data-theme="3b1b"] svg .c-green-dash { stroke: #34d399 !important; }
    [data-theme="3b1b"] svg .c-amber { stroke: #facc15 !important; }
    [data-theme="3b1b"] svg .c-dash, [data-theme="3b1b"] svg .c-sub { stroke: #64748b !important; }
    [data-theme="3b1b"] svg .f-blue, [data-theme="3b1b"] svg .f-uhp { fill: rgba(56, 189, 248, 0.16) !important; }
    [data-theme="3b1b"] svg .f-amber { fill: rgba(250, 204, 21, 0.15) !important; }
    [data-theme="3b1b"] svg .f-green { fill: rgba(52, 211, 153, 0.15) !important; }
    [data-theme="3b1b"] svg .f-rose { fill: rgba(251, 113, 133, 0.15) !important; }
    [data-theme="3b1b"] svg #stipple circle { fill: #38bdf8 !important; opacity: 0.45 !important; }
    [data-theme="3b1b"] svg #hatch line { stroke: #38bdf8 !important; opacity: 0.4 !important; }
    [data-theme="3b1b"] svg #arr path { fill: #e2e8f0 !important; }
    [data-theme="3b1b"] svg #arr-axis path { fill: #94a3b8 !important; }
    [data-theme="3b1b"] svg #arr-blue path { fill: #38bdf8 !important; }
    [data-theme="3b1b"] svg #arr-red path { fill: #fb7185 !important; }
    [data-theme="3b1b"] svg #arr-green path { fill: #34d399 !important; }
    [data-theme="3b1b"] svg #arr-amber path { fill: #facc15 !important; }
    [data-theme="3b1b"] svg .pt { stroke: #090d16 !important; }
    [data-theme="3b1b"] svg .pt-open { fill: #090d16 !important; }
    [data-theme="3b1b"] svg .lbl, [data-theme="3b1b"] svg .it { fill: #f8fafc !important; stroke: #090d16 !important; }
    [data-theme="3b1b"] svg .lbl[fill="#1e3a8a"], [data-theme="3b1b"] svg .it[fill="#1e3a8a"] { fill: #38bdf8 !important; }
    [data-theme="3b1b"] svg .lbl[fill="#dc2626"], [data-theme="3b1b"] svg .it[fill="#dc2626"] { fill: #fb7185 !important; }
    [data-theme="3b1b"] svg .lbl[fill="#047857"], [data-theme="3b1b"] svg .it[fill="#047857"] { fill: #34d399 !important; }
    [data-theme="3b1b"] svg .lbl[fill="#b45309"], [data-theme="3b1b"] svg .it[fill="#b45309"] { fill: #facc15 !important; }
    [data-grid="off"] svg .canvas-grid { display: none; }
    svg .layer-grid, svg .layer-region, svg .layer-curve, svg .layer-label { transition: opacity 0.22s ease; }
    .fig-card[data-step="1"] svg .layer-region, .fig-card[data-step="1"] svg .layer-curve, .fig-card[data-step="1"] svg .layer-label { opacity: 0.06; }
    .fig-card[data-step="2"] svg .layer-curve, .fig-card[data-step="2"] svg .layer-label { opacity: 0.06; }
    .fig-card[data-step="3"] svg .layer-label { opacity: 0.06; }
    body { margin: 0; font-family: "New Computer Modern", "Charter", Georgia, serif; background: var(--bg); color: var(--ink); }
    header { position: sticky; top: 0; z-index: 20; backdrop-filter: blur(12px); background: color-mix(in srgb, var(--bg) 88%, transparent); border-bottom: 1px solid var(--border); padding: 18px 24px; }
    .header-inner { max-width: 1440px; margin: 0 auto; display: flex; flex-direction: column; gap: 12px; }
    .top-row { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; }
    h1 { margin: 0; font-size: 1.45rem; font-weight: 700; }
    .sub { margin: 2px 0 0; color: var(--muted); font-size: 0.9rem; font-family: system-ui, sans-serif; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between; font-family: system-ui, sans-serif; }
    .btn-group { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    button, input[type='search'] { background: var(--card); color: var(--ink); border: 1px solid var(--border); padding: 6px 11px; border-radius: 6px; font-size: 0.8rem; font-family: system-ui, sans-serif; }
    button { cursor: pointer; font-weight: 500; }
    button.active { background: var(--accent); color: #ffffff; border-color: var(--accent); }
    [data-theme="3b1b"] button.active { color: #070b14; font-weight: 700; }
    input[type='search'] { min-width: 210px; }
    .grid { max-width: 1440px; margin: 0 auto; padding: 24px; display: grid; grid-template-columns: repeat(auto-fill, minmax(min(390px, 100%), 1fr)); gap: 20px; }
    .fig-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 1px 3px rgba(15,23,42,0.05); }
    .card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-family: system-ui, sans-serif; font-size: 0.76rem; }
    .card-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .fig-code { font-weight: 700; letter-spacing: 0.03em; color: var(--ink); font-size: 0.84rem; }
    .badge { padding: 2px 8px; border-radius: 999px; font-weight: 600; background: var(--badge-bg); color: var(--badge-fg); }
    .step-pills { display: flex; gap: 3px; }
    .pill { padding: 2px 7px; font-size: 0.72rem; border-radius: 4px; }
    .stage-wrap { display: grid; grid-template-columns: 1fr; gap: 10px; }
    body[data-compare="on"] .stage-wrap { grid-template-columns: 1fr 1fr; }
    .svg-stage { background: var(--stage); border: 1px solid var(--border); border-radius: 8px; padding: 8px; min-height: 225px; display: flex; align-items: center; justify-content: center; }
    .raw-stage { display: none; background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 8px; flex-direction: column; align-items: center; justify-content: center; gap: 6px; }
    body[data-compare="on"] .raw-stage { display: flex; }
    .raw-stage img { max-width: 100%; max-height: 210px; object-fit: contain; }
    .raw-stage span { font-family: system-ui, sans-serif; font-size: 0.7rem; color: #64748b; }
    .fig-title { margin: 0; font-size: 0.95rem; color: var(--ink); text-align: center; }
"""

_GALLERY_JS = """
    let currentCh = 0;
    function setTheme(t, btn) {
      document.body.dataset.theme = t;
      for (const b of document.querySelectorAll('#theme-group .theme')) b.classList.remove('active');
      btn.classList.add('active');
    }
    function toggleGrid(btn) {
      const next = document.body.dataset.grid === 'on' ? 'off' : 'on';
      document.body.dataset.grid = next;
      btn.textContent = 'Grid: ' + next.toUpperCase();
    }
    function toggleCompare(btn) {
      const next = document.body.dataset.compare === 'on' ? 'off' : 'on';
      document.body.dataset.compare = next;
      btn.classList.toggle('active', next === 'on');
    }
    function setCardStep(btn, step) {
      const card = btn.closest('.fig-card');
      card.dataset.step = String(step);
      for (const p of card.querySelectorAll('.pill')) p.classList.remove('active');
      btn.classList.add('active');
    }
    function setAllSteps(step, btn) {
      for (const b of document.querySelectorAll('#global-step-group button')) b.classList.remove('active');
      btn.classList.add('active');
      for (const card of document.querySelectorAll('.fig-card')) {
        card.dataset.step = String(step);
        card.querySelectorAll('.pill').forEach((p, idx) => p.classList.toggle('active', idx + 1 === step));
      }
    }
    function filterCh(ch, btn) {
      currentCh = ch;
      for (const b of document.querySelectorAll('#ch-group button')) b.classList.remove('active');
      btn.classList.add('active');
      applyFilters();
    }
    function applyFilters() {
      const q = document.getElementById('fig-search').value.trim().toLowerCase();
      for (const card of document.querySelectorAll('.fig-card')) {
        const chOk = currentCh === 0 || Number(card.dataset.chapter) === currentCh;
        const qOk = !q || card.dataset.search.includes(q);
        card.style.display = (chOk && qOk) ? '' : 'none';
      }
    }
"""

_STEP_NAMES = (
    "Axes & Frame",
    "Domains & Regions",
    "Curves & Contours",
    "Points & Labels",
)


def _gallery_card(book: FigureBook, asset: FigureAsset, svg: str) -> str:
    esc = html.escape
    badge = (
        f"Ch {asset.chapter} · {asset.chapter_title}"
        if asset.chapter_title
        else "Vector SVG"
    )
    search = esc(f"{asset.label} {asset.title} {asset.chapter_title}".lower())
    pills = ""
    if len(asset.layers) >= 3:
        pills = (
            '<div class="step-pills" role="group" aria-label="Progressive layer steps">'
            + "".join(
                f'<button type="button" class="pill{" active" if step == 4 else ""}" '
                f'onclick="setCardStep(this, {step})" title="Step {step}: {name}">{step}</button>'
                for step, name in enumerate(_STEP_NAMES, start=1)
            )
            + "</div>"
        )
    scan = ""
    if book.scan_dir:
        scan = (
            f'<div class="raw-stage"><img src="{book.scan_dir}/fig_{asset.fig_id}.png" '
            f'alt="Original scan {esc(asset.label)}" loading="lazy" /><span>Original raster scan</span></div>'
        )
    return (
        f'<article class="fig-card" id="fig-{asset.fig_id.replace("_", "-")}" '
        f'data-chapter="{asset.chapter}" data-step="4" data-search="{search}">'
        f'<div class="card-head"><div class="card-meta"><span class="fig-code">{esc(asset.label)}</span>'
        f'<span class="badge">{esc(badge)}</span></div>{pills}</div>'
        f'<div class="stage-wrap"><div class="svg-stage">{svg}</div>{scan}</div>'
        f'<p class="fig-title">{esc(asset.title)}</p>'
        "</article>"
    )


def _gallery_html(
    book: FigureBook, assets: dict[str, FigureAsset], svgs: dict[str, str]
) -> str:
    esc = html.escape
    counts: dict[int, int] = {}
    for asset in assets.values():
        counts[asset.chapter] = counts.get(asset.chapter, 0) + 1
    chapter_buttons = "".join(
        f'<button type="button" onclick="filterCh({ch}, this)">Ch {ch} · {esc(book.chapter_titles.get(ch, ""))} ({n})</button>'
        for ch, n in sorted(counts.items())
        if ch in book.chapter_titles
    )
    compare = (
        '<button type="button" onclick="toggleCompare(this)">Compare Scan</button>'
        if book.scan_dir
        else ""
    )
    cards = "\n    ".join(
        _gallery_card(book, a, svgs[fid]) for fid, a in assets.items()
    )
    total = len(assets)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '  <meta charset="utf-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        f"  <title>{esc(book.title)} — Vector Figure Atlas</title>\n"
        f"  <style>{_GALLERY_CSS}  </style>\n"
        "</head>\n"
        '<body data-theme="textbook" data-grid="on" data-compare="off">\n'
        '  <header>\n    <div class="header-inner">\n      <div class="top-row">\n'
        f"        <div><h1>{esc(book.title)} — Vector Figure Atlas ({total} SVGs)</h1>"
        f'<p class="sub">{esc(book.subtitle)}</p></div>\n'
        '        <div class="btn-group" id="theme-group">'
        '<button type="button" class="theme active" onclick="setTheme(\'textbook\', this)">Textbook Classic</button>'
        '<button type="button" class="theme" onclick="setTheme(\'3b1b\', this)">3Blue1Brown 2D</button>'
        '<button type="button" class="theme" onclick="setTheme(\'parchment\', this)">Warm Parchment</button>'
        '<button type="button" onclick="toggleGrid(this)">Grid: ON</button>'
        f"{compare}</div>\n"
        "      </div>\n"
        '      <div class="toolbar">\n'
        '        <div class="btn-group" id="ch-group">'
        f'<button type="button" class="active" onclick="filterCh(0, this)">All ({total})</button>'
        f"{chapter_buttons}</div>\n"
        '        <div class="btn-group" id="global-step-group">'
        '<span style="font-size:0.78rem;color:var(--muted);">Progressive build:</span>'
        '<button type="button" onclick="setAllSteps(1, this)">1 · Frame</button>'
        '<button type="button" onclick="setAllSteps(2, this)">2 · Domains</button>'
        '<button type="button" onclick="setAllSteps(3, this)">3 · Contours</button>'
        '<button type="button" class="active" onclick="setAllSteps(4, this)">4 · Complete</button>'
        f'<input type="search" id="fig-search" placeholder="{esc(book.search_hint)}" oninput="applyFilters()" />'
        "</div>\n"
        "      </div>\n    </div>\n  </header>\n"
        f'  <main class="grid" id="fig-grid">\n    {cards}\n  </main>\n'
        f"  <script>{_GALLERY_JS}  </script>\n"
        "</body>\n</html>\n"
    )
