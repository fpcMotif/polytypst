import math
from collections.abc import Sequence

from polytypst.vision.diagram_engine import INK, point_dot, smooth_curve

BLUE = "#1e3a8a"
RED = "#dc2626"
GREEN = "#047857"
AMBER = "#b45309"
SLATE = "#475569"

Point = tuple[float, float]


def open_pt(x: float, y: float, color: str = INK, r: float = 3.8) -> str:
    return point_dot(x, y, color=color, r=r, open_dot=True)


def filled_pt(x: float, y: float, color: str = INK, r: float = 3.8) -> str:
    return point_dot(x, y, color=color, r=r, open_dot=False)


def seg(
    p1: Point,
    p2: Point,
    cls: str = "c-main",
    marker_end: str = "",
    stroke_width: float | None = None,
) -> str:
    m_attr = f' marker-end="url(#{marker_end})"' if marker_end else ""
    w_attr = f' stroke-width="{stroke_width:.2f}"' if stroke_width is not None else ""
    return (
        f'    <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" '
        f'x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" class="{cls}"{w_attr}{m_attr} />'
    )


def line_through(
    p1: Point,
    p2: Point,
    t0: float = -0.25,
    t1: float = 1.25,
    cls: str = "c-main",
    stroke_width: float | None = None,
) -> str:
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    q0 = (p1[0] + t0 * dx, p1[1] + t0 * dy)
    q1 = (p1[0] + t1 * dx, p1[1] + t1 * dy)
    return seg(q0, q1, cls=cls, stroke_width=stroke_width)


def line_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> Point:
    x1, y1 = a1
    x2, y2 = a2
    x3, y3 = b1
    x4, y4 = b2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return ((x1 + x3) * 0.5, (y1 + y3) * 0.5)
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return (px, py)


def txt(
    x: float,
    y: float,
    body: str,
    *,
    italic: bool = False,
    color: str = INK,
    anchor: str = "start",
    size: float = 15.0,
    weight: str = "",
    rotate: float | None = None,
) -> str:
    cls = "it" if italic else "lbl"
    fill_attr = f' fill="{color}"' if color != INK else ""
    anc_attr = f' text-anchor="{anchor}"' if anchor != "start" else ""
    sz_attr = f' font-size="{size:.1f}px"' if abs(size - 15.0) > 0.1 else ""
    wt_attr = f' font-weight="{weight}"' if weight else ""
    rot_attr = (
        f' transform="rotate({rotate:.1f} {x:.1f} {y:.1f})"'
        if rotate is not None
        else ""
    )
    return (
        f'    <text x="{x:.1f}" y="{y:.1f}" class="{cls}"'
        f"{fill_attr}{anc_attr}{sz_attr}{wt_attr}{rot_attr}>{body}</text>"
    )


def mvar(
    x: float,
    y: float,
    base: str,
    sub: str = "",
    sup: str = "",
    *,
    prime: str = "",
    color: str = INK,
    anchor: str = "start",
    size: float = 15.5,
    bold_base: bool = False,
    overbar: bool = False,
    tilde: bool = False,
) -> str:
    b_style = ' font-style="normal" font-weight="bold"' if bold_base else ""
    parts = [f"<tspan{b_style}>{base}{prime}</tspan>"]
    if sub and sup:
        parts.append(
            f'<tspan font-size="11px" dy="3.5" font-style="normal">{sub}</tspan>'
            f'<tspan font-size="11px" dy="-9.0" font-style="normal">{sup}</tspan>'
            '<tspan dy="5.5"></tspan>'
        )
    elif sub:
        parts.append(
            f'<tspan font-size="11px" dy="3.5" font-style="normal">{sub}</tspan>'
            '<tspan dy="-3.5"></tspan>'
        )
    elif sup:
        parts.append(
            f'<tspan font-size="11px" dy="-5.5" font-style="normal">{sup}</tspan>'
            '<tspan dy="5.5"></tspan>'
        )
    out = [
        txt(x, y, "".join(parts), italic=True, color=color, anchor=anchor, size=size)
    ]
    hx = x if anchor == "middle" else (x + 5.2 if anchor == "start" else x - 5.2)
    acc_cls = (
        "c-blue"
        if color == BLUE
        else "c-red"
        if color == RED
        else "c-green"
        if color == GREEN
        else "c-amber"
        if color == AMBER
        else "c-main"
    )
    if overbar:
        out.append(
            f'    <line x1="{hx - 5.2:.1f}" y1="{y - 12.6:.1f}" '
            f'x2="{hx + 5.6:.1f}" y2="{y - 12.6:.1f}" '
            f'class="{acc_cls}" stroke-width="1.35" />'
        )
    if tilde:
        td = (
            f"M {hx - 5.2:.1f} {y - 12.2:.1f} "
            f"C {hx - 2.6:.1f} {y - 15.2:.1f}, {hx + 2.2:.1f} {y - 9.6:.1f}, "
            f"{hx + 5.2:.1f} {y - 12.8:.1f}"
        )
        out.append(f'    <path d="{td}" class="{acc_cls}" stroke-width="1.3" />')
    return "\n".join(out)


def panel_label(x: float, y: float, letter: str) -> str:
    return txt(
        x, y, f"({letter})", italic=False, anchor="middle", size=15.0, weight="bold"
    )


def cubic_y(x: float, roots: tuple[float, float, float]) -> float:
    e1, e2, e3 = roots
    val = (x - e1) * (x - e2) * (x - e3)
    return math.sqrt(max(0.0, val))


def cubic_secant_third(
    p1: Point, p2: Point, roots: tuple[float, float, float]
) -> Point:
    s1 = roots[0] + roots[1] + roots[2]
    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
    x3 = m * m + s1 - p1[0] - p2[0]
    y3 = -(p1[1] + m * (x3 - p1[0]))
    return (x3, -y3)


def cubic_tangent_third(
    p: Point, roots: tuple[float, float, float]
) -> tuple[Point, float]:
    e1, e2, e3 = roots
    s1 = e1 + e2 + e3
    s2 = e1 * e2 + e2 * e3 + e3 * e1
    x0, y0 = p
    m = (3.0 * x0 * x0 - 2.0 * s1 * x0 + s2) / (2.0 * y0)
    x3 = m * m + s1 - 2.0 * x0
    y3 = y0 + m * (x3 - x0)
    return ((x3, y3), m)


def render_elliptic_components(
    roots: tuple[float, float, float],
    x_max: float,
    to_svg: Sequence[float],
    *,
    oval_cls: str = "c-blue",
    branch_cls: str = "c-blue",
    oval_fill: str = "f-blue",
) -> tuple[str, str]:
    cx, cy, sx, sy = to_svg[0], to_svg[1], to_svg[2], to_svg[3]
    e1, e2, e3 = roots
    oval_pts: list[Point] = []
    n_oval = 64
    for k in range(n_oval):
        th = 2.0 * math.pi * k / n_oval
        xv = 0.5 * (e1 + e2) + 0.5 * (e2 - e1) * math.cos(th)
        yv = 0.5 * (e2 - e1) * math.sin(th) * math.sqrt(e3 - xv)
        oval_pts.append((cx + sx * xv, cy - sy * yv))
    branch_pts: list[Point] = []
    n_br = 65
    for k in range(n_br):
        u = -1.0 + 2.0 * k / (n_br - 1)
        xv = e3 + (x_max - e3) * u * u
        yv = u * math.sqrt(x_max - e3) * math.sqrt((xv - e1) * (xv - e2))
        branch_pts.append((cx + sx * xv, cy - sy * yv))
    reg = (
        smooth_curve(oval_pts, cls=oval_cls, closed=True, fill_cls=oval_fill)
        if oval_fill
        else ""
    )
    reg_only = (
        f'    <path d="{_closed_poly_d(oval_pts)}" class="{oval_fill}" opacity="0.48" />'
        if oval_fill
        else ""
    )
    _ = reg
    crv = "\n".join(
        [
            smooth_curve(oval_pts, cls=oval_cls, closed=True),
            smooth_curve(branch_pts, cls=branch_cls, closed=False),
        ]
    )
    return reg_only, crv


def _closed_poly_d(pts: Sequence[Point]) -> str:
    if not pts:
        return ""
    return (
        f"M {pts[0][0]:.2f} {pts[0][1]:.2f} "
        + " ".join(f"L {p[0]:.2f} {p[1]:.2f}" for p in pts[1:])
        + " Z"
    )
