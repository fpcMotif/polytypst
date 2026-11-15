import math
from collections.abc import Callable

from polytypst.vision.diagram_engine import INK, axes_xy, smooth_curve, svg_document

from .figures_common import (
    AMBER,
    BLUE,
    GREEN,
    RED,
    Point,
    filled_pt,
    line_intersect,
    line_through,
    mvar,
    open_pt,
    panel_label,
    seg,
    txt,
)

CHAPTER_FIG_TITLES: dict[str, str] = {
    "1": "Intersections of conics",
    "2": "The polar line of a point with respect to a conic",
    "3": "Projection of a cubic",
    "4": "Projection of a conic",
    "5": "A cusp",
    "6": "Pascal's theorem",
}


def _ellipse_el(cx: float, cy: float, rx: float, ry: float, cls: str) -> str:
    return f'    <ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" class="{cls}" />'


def fig_1() -> str:
    regions = "\n".join(
        [
            _ellipse_el(64.0, 102.0, 50.0, 31.0, "f-blue"),
            _ellipse_el(156.0, 102.0, 29.0, 66.0, "f-rose"),
            _ellipse_el(268.0, 102.0, 29.0, 66.0, "f-rose"),
            _ellipse_el(320.0, 102.0, 54.0, 31.0, "f-blue"),
            _ellipse_el(488.0, 102.0, 56.0, 31.0, "f-blue"),
            _ellipse_el(488.0, 102.0, 29.0, 66.0, "f-rose"),
        ]
    )
    curves = "\n".join(
        [
            _ellipse_el(64.0, 102.0, 50.0, 31.0, "c-blue"),
            _ellipse_el(156.0, 102.0, 29.0, 66.0, "c-red"),
            _ellipse_el(268.0, 102.0, 29.0, 66.0, "c-red"),
            _ellipse_el(320.0, 102.0, 54.0, 31.0, "c-blue"),
            _ellipse_el(488.0, 102.0, 56.0, 31.0, "c-blue"),
            _ellipse_el(488.0, 102.0, 29.0, 66.0, "c-red"),
        ]
    )

    def _f_b(x: float) -> float:
        u = 1.0 - ((x - 268.0) / 29.0) ** 2
        v = 1.0 - ((x - 320.0) / 54.0) ** 2
        return 66.0 * 66.0 * u - 31.0 * 31.0 * v

    lo, hi = 268.0, 297.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if _f_b(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    xb = 0.5 * (lo + hi)
    yb = 31.0 * math.sqrt(max(0.0, 1.0 - ((xb - 320.0) / 54.0) ** 2))

    xc_off = math.sqrt(
        (56.0**2 * 29.0**2 * (66.0**2 - 31.0**2))
        / (66.0**2 * 56.0**2 - 31.0**2 * 29.0**2)
    )
    yc_off = 31.0 * math.sqrt(max(0.0, 1.0 - (xc_off / 56.0) ** 2))

    labels = "\n".join(
        [
            filled_pt(xb, 102.0 - yb, color=AMBER, r=3.6),
            filled_pt(xb, 102.0 + yb, color=AMBER, r=3.6),
            filled_pt(488.0 - xc_off, 102.0 - yc_off, color=AMBER, r=3.6),
            filled_pt(488.0 + xc_off, 102.0 - yc_off, color=AMBER, r=3.6),
            filled_pt(488.0 - xc_off, 102.0 + yc_off, color=AMBER, r=3.6),
            filled_pt(488.0 + xc_off, 102.0 + yc_off, color=AMBER, r=3.6),
            panel_label(112.0, 202.0, "a"),
            panel_label(308.0, 202.0, "b"),
            panel_label(488.0, 202.0, "c"),
        ]
    )
    return svg_document(
        "0 0 572 218",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1",
        title=CHAPTER_FIG_TITLES["1"],
        show_grid=False,
    )


def _circle_tangents_from_exterior(c: Point, r: float, p: Point) -> tuple[Point, Point]:
    dx, dy = p[0] - c[0], p[1] - c[1]
    d = math.hypot(dx, dy)
    th0 = math.atan2(dy, dx)
    alpha = math.acos(r / d)
    t1 = (c[0] + r * math.cos(th0 + alpha), c[1] + r * math.sin(th0 + alpha))
    t2 = (c[0] + r * math.cos(th0 - alpha), c[1] + r * math.sin(th0 - alpha))
    return t1, t2


def _circle_tangent_meet(
    c: Point, r: float, th1: float, th2: float
) -> tuple[Point, Point, Point]:
    a = (c[0] + r * math.cos(th1), c[1] + r * math.sin(th1))
    b = (c[0] + r * math.cos(th2), c[1] + r * math.sin(th2))
    ta = (a[0] - math.sin(th1), a[1] + math.cos(th1))
    tb = (b[0] - math.sin(th2), b[1] + math.cos(th2))
    return a, b, line_intersect(a, ta, b, tb)


def fig_2() -> str:
    ca, ra = (94.0, 148.0), 64.0
    pa = (206.0, 44.0)
    ta1, ta2 = _circle_tangents_from_exterior(ca, ra, pa)

    cb, rb = (362.0, 134.0), 56.0
    pb = (398.0, 132.0)

    def _chord_angles(phi: float) -> tuple[float, float]:
        ux, uy = math.cos(phi), math.sin(phi)
        ox, oy = pb[0] - cb[0], pb[1] - cb[1]
        b_coef = ox * ux + oy * uy
        c_coef = ox * ox + oy * oy - rb * rb
        disc = math.sqrt(max(0.0, b_coef * b_coef - c_coef))
        s_pos, s_neg = -b_coef + disc, -b_coef - disc
        p_pos = (pb[0] + s_pos * ux, pb[1] + s_pos * uy)
        p_neg = (pb[0] + s_neg * ux, pb[1] + s_neg * uy)
        return (
            math.atan2(p_pos[1] - cb[1], p_pos[0] - cb[0]),
            math.atan2(p_neg[1] - cb[1], p_neg[0] - cb[0]),
        )

    th1a, th1b = _chord_angles(math.radians(56.0))
    b1, b2, q_top = _circle_tangent_meet(cb, rb, th1a, th1b)
    th2a, th2b = _chord_angles(math.radians(-54.0))
    d1, d2, q_bot = _circle_tangent_meet(cb, rb, th2a, th2b)

    regions = "\n".join(
        [
            f'    <circle cx="{ca[0]:.1f}" cy="{ca[1]:.1f}" r="{ra:.1f}" class="f-blue" />',
            f'    <circle cx="{cb[0]:.1f}" cy="{cb[1]:.1f}" r="{rb:.1f}" class="f-blue" />',
            line_through(pa, ta1, -0.16, 1.32, cls="c-amber"),
            line_through(pa, ta2, -0.16, 1.35, cls="c-amber"),
            line_through(b1, b2, -0.22, 1.22, cls="c-main"),
            line_through(q_top, b1, -0.14, 1.22, cls="c-amber"),
            line_through(q_top, b2, -0.14, 1.28, cls="c-amber"),
            line_through(d1, d2, -0.22, 1.22, cls="c-dash"),
            line_through(q_bot, d1, -0.12, 1.22, cls="c-dash"),
            line_through(q_bot, d2, -0.12, 1.22, cls="c-dash"),
        ]
    )
    curves = "\n".join(
        [
            f'    <circle cx="{ca[0]:.1f}" cy="{ca[1]:.1f}" r="{ra:.1f}" class="c-blue" />',
            line_through(ta1, ta2, -0.22, 1.24, cls="c-red", stroke_width=2.1),
            f'    <circle cx="{cb[0]:.1f}" cy="{cb[1]:.1f}" r="{rb:.1f}" class="c-blue" />',
            line_through(q_top, q_bot, -0.14, 1.16, cls="c-red", stroke_width=2.1),
        ]
    )
    q_mid_x = 0.5 * (q_top[0] + q_bot[0])
    labels = "\n".join(
        [
            filled_pt(pa[0], pa[1], color=INK, r=3.5),
            filled_pt(ta1[0], ta1[1], color=RED, r=3.2),
            filled_pt(ta2[0], ta2[1], color=RED, r=3.2),
            filled_pt(pb[0], pb[1], color=INK, r=3.5),
            filled_pt(q_top[0], q_top[1], color=RED, r=3.2),
            filled_pt(q_bot[0], q_bot[1], color=RED, r=3.2),
            mvar(pa[0] + 6.0, pa[1] + 18.0, "P"),
            mvar(76.0, 152.0, "L", color=RED),
            mvar(pb[0] - 20.0, pb[1] + 5.0, "P"),
            mvar(q_mid_x + 10.0, 136.0, "L", color=RED),
            panel_label(126.0, 266.0, "a"),
            panel_label(412.0, 266.0, "b"),
        ]
    )
    return svg_document(
        "0 0 548 280",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="2",
        title=CHAPTER_FIG_TITLES["2"],
        show_grid=False,
    )


def fig_3() -> str:
    ox, oy = 152.0, 198.0
    sx, sy = 104.0, 104.0
    axes, ax_lbl = axes_xy(
        ox,
        oy,
        16.0,
        356.0,
        18.0,
        406.0,
        x_label="x",
        y_label="y",
        origin_label="0",
        origin_dx=-15.0,
        origin_dy=19.0,
    )
    x_one = ox + sx

    loop_pts: list[Point] = []
    for k in range(49):
        t = -1.0 + 2.0 * k / 48.0
        xv = t * t - 1.0
        yv = t * (t * t - 1.0)
        loop_pts.append((ox + sx * xv, oy - sy * yv))

    cubic_pts: list[Point] = []
    for k in range(97):
        t = -1.66 + (1.52 + 1.66) * k / 96.0
        xv = t * t - 1.0
        yv = t * (t * t - 1.0)
        cubic_pts.append((ox + sx * xv, oy - sy * yv))

    t_main = -1.52
    px_val, py_val = t_main * t_main - 1.0, t_main * (t_main * t_main - 1.0)
    p_pt = (ox + sx * px_val, oy - sy * py_val)
    q_pt = (x_one, oy - sy * t_main)

    fan_slopes = (-0.26, 0.14, 0.42)
    fan_lines = [
        seg(
            (ox - 128.0, oy + 128.0 * m),
            (ox + 168.0, oy - 168.0 * m),
            cls="c-sub",
        )
        for m in fan_slopes
    ]
    fan_lines.append(seg((ox - 62.0, oy - 96.0), (ox, oy), cls="c-sub"))
    fan_lines.append(
        line_through((ox, oy), p_pt, -0.02, 1.12, cls="c-amber", stroke_width=1.55)
    )

    loop_d = "M " + " L ".join(f"{p[0]:.2f} {p[1]:.2f}" for p in loop_pts) + " Z"
    regions = "\n".join(
        [
            f'    <path d="{loop_d}" class="f-blue" opacity="0.45" />',
            seg((x_one, 20.0), (x_one, 408.0), cls="c-red-dash"),
            *fan_lines,
        ]
    )
    curves = smooth_curve(cubic_pts, cls="c-blue")
    labels = "\n".join(
        [
            ax_lbl,
            txt(x_one + 6.0, oy + 18.0, "1", italic=False, color=RED),
            open_pt(ox, oy, color=BLUE, r=4.0),
            open_pt(q_pt[0], q_pt[1], color=RED, r=4.0),
            open_pt(p_pt[0], p_pt[1], color=BLUE, r=4.0),
            mvar(q_pt[0] - 22.0, q_pt[1] + 5.0, "Q", color=RED),
            mvar(p_pt[0] + 10.0, p_pt[1] + 5.0, "P", color=BLUE),
        ]
    )
    return svg_document(
        "0 0 382 424",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3",
        title=CHAPTER_FIG_TITLES["3"],
    )


def fig_4() -> str:
    cx, cy, r = 204.0, 108.0, 58.0
    pole = (cx, cy - r)
    y_line = 228.0
    x_targets = (58.0, 134.0, 204.0, 278.0, 352.0)

    rays: list[str] = []
    hit_dots: list[str] = []
    for xt in x_targets:
        dx, dy = xt - pole[0], y_line - pole[1]
        rays.append(
            seg(
                (pole[0] - 0.14 * dx, pole[1] - 0.14 * dy),
                (pole[0] + 1.12 * dx, pole[1] + 1.12 * dy),
                cls="c-amber",
                stroke_width=1.35,
            )
        )
        hit_dots.append(filled_pt(xt, y_line, color=RED, r=2.8))
        if abs(xt - cx) > 1.0:
            s = 2.0 * r * dy / (dx * dx + dy * dy)
            cx_hit = pole[0] + s * dx
            cy_hit = pole[1] + s * dy
            hit_dots.append(filled_pt(cx_hit, cy_hit, color=BLUE, r=2.8))
        else:
            hit_dots.append(filled_pt(cx, cy + r, color=BLUE, r=2.8))

    regions = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-blue" />',
            *rays,
        ]
    )
    curves = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="c-blue" />',
            seg((20.0, y_line), (392.0, y_line), cls="c-red", stroke_width=2.0),
        ]
    )
    pole_lbl = (
        f'    <text x="{pole[0] + 18.0:.1f}" y="{pole[1] - 2.0:.1f}" class="lbl">'
        '(<tspan class="it">x</tspan><tspan font-size="11px" dy="3.5">0</tspan>'
        '<tspan dy="-3.5">, </tspan>'
        '<tspan class="it">y</tspan><tspan font-size="11px" dy="3.5">0</tspan>'
        '<tspan dy="-3.5">)</tspan></text>'
    )
    labels = "\n".join(
        [
            *hit_dots,
            open_pt(pole[0], pole[1], color=BLUE, r=4.2),
            pole_lbl,
            mvar(cx + r + 10.0, cy + 8.0, "X", color=BLUE),
        ]
    )
    return svg_document(
        "0 0 412 266",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="4",
        title=CHAPTER_FIG_TITLES["4"],
    )


def fig_5() -> str:
    vx, vy = 66.0, 122.0
    sx, sy = 152.0, 62.0
    upper: list[Point] = []
    lower: list[Point] = []
    for k in range(45):
        t = 1.20 * k / 44.0
        upper.append((vx + sx * t * t, vy - sy * t * t * t))
        lower.append((vx + sx * t * t, vy + sy * t * t * t))

    grid_line = seg((26.0, vy), (314.0, vy), cls="c-dash")
    curves = "\n".join(
        [
            smooth_curve(upper, cls="c-blue"),
            smooth_curve(lower, cls="c-blue"),
        ]
    )
    labels = filled_pt(vx, vy, color=RED, r=3.8)
    return svg_document(
        "0 0 340 244",
        grid=grid_line,
        curve=curves,
        label=labels,
        fig_id="5",
        title=CHAPTER_FIG_TITLES["5"],
    )


def fig_6() -> str:
    cx, cy, rx, ry = 156.0, 188.0, 86.0, 126.0

    def _pt(deg: float) -> Point:
        rad = math.radians(deg)
        return (cx + rx * math.cos(rad), cy - ry * math.sin(rad))

    u1, u2, u3 = _pt(126.0), _pt(184.0), _pt(234.0)
    v1, v2, v3 = _pt(31.0), _pt(2.0), _pt(332.0)
    pts = (u1, u2, u3, v1, v2, v3)
    q_top = line_intersect(u3, v2, u2, v1)
    q_mid = line_intersect(u1, v1, u3, v3)
    q_bot = line_intersect(u2, v3, u1, v2)

    regions = _ellipse_el(cx, cy, rx, ry, "f-blue")
    curves = "\n".join(
        [
            _ellipse_el(cx, cy, rx, ry, "c-main"),
            line_through(u1, q_mid, -0.14, 1.12, cls="c-blue"),
            line_through(u2, q_bot, -0.16, 1.12, cls="c-blue"),
            line_through(u3, q_top, -0.14, 1.08, cls="c-blue"),
            line_through(u3, q_mid, -0.14, 1.12, cls="c-green"),
            line_through(u1, q_bot, -0.12, 1.12, cls="c-green"),
            line_through(u2, q_top, -0.16, 1.08, cls="c-green"),
            line_through(q_top, q_bot, -0.08, 1.15, cls="c-red", stroke_width=2.15),
        ]
    )
    labels = "\n".join(
        [
            *(filled_pt(p[0], p[1], r=3.1) for p in pts),
            filled_pt(q_top[0], q_top[1], color=RED, r=3.7),
            filled_pt(q_mid[0], q_mid[1], color=RED, r=3.7),
            filled_pt(q_bot[0], q_bot[1], color=RED, r=3.7),
            mvar(166.0, 98.0, "l", sub="1", color=BLUE),
            mvar(102.0, 218.0, "l", sub="2", color=BLUE),
            mvar(116.0, 264.0, "l", sub="3", color=BLUE),
            mvar(188.0, 280.0, "m", sub="1", color=GREEN),
            mvar(116.0, 128.0, "m", sub="2", color=GREEN),
            mvar(112.0, 168.0, "m", sub="3", color=GREEN),
            mvar(q_top[0] + 10.0, q_top[1] + 28.0, "L", color=RED),
        ]
    )
    return svg_document(
        "0 0 502 356",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="6",
        title=CHAPTER_FIG_TITLES["6"],
        show_grid=False,
    )


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "1": fig_1,
    "2": fig_2,
    "3": fig_3,
    "4": fig_4,
    "5": fig_5,
    "6": fig_6,
}
