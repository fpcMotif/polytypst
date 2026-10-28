import math
from collections.abc import Callable

from polytypst.vision.diagram_engine import (
    arc_path,
    arrow_line,
    axes_xy,
    circle_contour,
    math_label,
    point_dot,
    smooth_curve,
    svg_document,
    tangent_arrow,
)


def _curly_brace(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    offset: float = 8.0,
    cls: str = "c-sub",
) -> str:
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return ""
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    ax, ay = x1 + nx * offset * 0.35, y1 + ny * offset * 0.35
    bx, by = x2 + nx * offset * 0.35, y2 + ny * offset * 0.35
    mx, my = 0.5 * (x1 + x2) + nx * offset, 0.5 * (y1 + y2) + ny * offset
    q1x, q1y = (
        x1 + ux * length * 0.25 + nx * offset * 0.7,
        y1 + uy * length * 0.25 + ny * offset * 0.7,
    )
    q2x, q2y = (
        x1 + ux * length * 0.75 + nx * offset * 0.7,
        y1 + uy * length * 0.75 + ny * offset * 0.7,
    )
    d = (
        f"M {ax:.1f} {ay:.1f} "
        f"Q {q1x:.1f} {q1y:.1f} {mx:.1f} {my:.1f} "
        f"Q {q2x:.1f} {q2y:.1f} {bx:.1f} {by:.1f}"
    )
    return f'    <path d="{d}" class="{cls}" />'


def _sample_triangle(
    x: float, y: float, dx: float, dy: float, color: str = "#1e3a8a"
) -> str:
    norm = math.hypot(dx, dy)
    if norm < 1e-6:
        ux, uy = 1.0, 0.0
    else:
        ux, uy = dx / norm, dy / norm
    nx, ny = -uy, ux
    p1x, p1y = x + ux * 4.2, y + uy * 4.2
    p2x, p2y = x - ux * 3.2 + nx * 3.2, y - uy * 3.2 + ny * 3.2
    p3x, p3y = x - ux * 3.2 - nx * 3.2, y - uy * 3.2 - ny * 3.2
    return (
        f'    <polygon points="{p1x:.1f},{p1y:.1f} {p2x:.1f},{p2y:.1f} {p3x:.1f},{p3y:.1f}" '
        f'fill="{color}" stroke="#ffffff" stroke-width="0.9" />'
    )


def fig_1_1() -> str:
    ox, oy = 152.0, 242.0
    axes, ax_labels = axes_xy(
        ox, oy, 22.0, 428.0, 20.0, 278.0, origin_dx=-15.0, origin_dy=17.0
    )
    z1x, z1y = 398.0, 174.0
    z2x, z2y = 54.0, 140.0
    wx, wy = z1x + (z2x - ox), z1y + (z2y - oy)
    regions = (
        f'    <polygon points="{ox:.1f},{oy:.1f} {z1x:.1f},{z1y:.1f} {wx:.1f},{wy:.1f} {z2x:.1f},{z2y:.1f}" '
        'class="f-blue" opacity="0.55" />'
    )
    curves = "\n".join(
        [
            f'    <line x1="{z2x:.1f}" y1="{z2y:.1f}" x2="{wx:.1f}" y2="{wy:.1f}" class="c-main" stroke-width="1.25" />',
            f'    <line x1="{z1x:.1f}" y1="{z1y:.1f}" x2="{wx:.1f}" y2="{wy:.1f}" class="c-main" stroke-width="1.25" />',
            arrow_line(ox, oy, z1x, z1y, cls="c-blue", marker="arr-blue"),
            arrow_line(ox, oy, z2x, z2y, cls="c-green", marker="arr-green"),
            arrow_line(ox, oy, wx, wy, cls="c-red", marker="arr-red"),
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            point_dot(ox, oy),
            math_label(405.0, 179.0, "z", sub="1", color="#1e3a8a"),
            math_label(25.0, 143.0, "z", sub="2", color="#047857"),
            (
                f'    <text x="{wx - 12:.1f}" y="{wy - 10:.1f}" class="it" fill="#dc2626">'
                'w = z<tspan font-size="10.5px" dy="3.2">1</tspan>'
                '<tspan dy="-3.2"> + z</tspan>'
                '<tspan font-size="10.5px" dy="3.2">2</tspan></text>'
            ),
        ]
    )
    return svg_document(
        "0 0 460 295",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_1",
        title=CHAPTER_FIG_TITLES["1_1"],
    )


def fig_1_2() -> str:
    ox, oy = 165.0, 142.0
    axes, ax_labels = axes_xy(
        ox,
        oy,
        24.0,
        355.0,
        18.0,
        265.0,
        x_label="",
        y_label="",
        origin_dx=-15.0,
        origin_dy=18.0,
    )
    zx, zy = 256.0, 82.0
    zbx, zby = 256.0, 202.0
    curves = f'    <line x1="{zx:.1f}" y1="{zy:.1f}" x2="{zbx:.1f}" y2="{zby:.1f}" class="c-dash" />'
    labels = "\n".join(
        [
            ax_labels,
            '    <text x="20.0" y="42.0" class="lbl">imaginary axis</text>',
            '    <text x="366.0" y="172.0" class="lbl">real axis</text>',
            point_dot(zx, zy, color="#1e3a8a"),
            point_dot(zbx, zby, color="#dc2626"),
            math_label(266.0, 87.0, "z = x + iy", color="#1e3a8a"),
            math_label(266.0, 207.0, "z = x \u2212 iy", color="#dc2626"),
            '    <line x1="266.5" y1="196.2" x2="274.8" y2="196.2" stroke="#dc2626" stroke-width="1.35" />',
        ]
    )
    return svg_document(
        "0 0 460 280",
        grid=axes,
        curve=curves,
        label=labels,
        fig_id="1_2",
        title=CHAPTER_FIG_TITLES["1_2"],
    )


def fig_1_3() -> str:
    domain_pts = [
        (26.0, 145.0),
        (58.0, 74.0),
        (165.0, 28.0),
        (292.0, 18.0),
        (398.0, 56.0),
        (438.0, 134.0),
        (408.0, 204.0),
        (302.0, 214.0),
        (182.0, 226.0),
        (72.0, 224.0),
    ]
    zx, zy, rho = 316.0, 126.0, 62.0
    ang = math.radians(26.0)
    rx, ry = zx + rho * math.cos(ang), zy - rho * math.sin(ang)
    hx, hy = 292.0, 92.0
    regions = "\n".join(
        [
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-stipple"),
            f'    <circle cx="{zx:.1f}" cy="{zy:.1f}" r="{rho:.1f}" class="f-amber" />',
            f'    <circle cx="{zx:.1f}" cy="{zy:.1f}" r="{rho:.1f}" fill="url(#stipple-amber)" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <circle cx="{zx:.1f}" cy="{zy:.1f}" r="{rho:.1f}" class="c-amber" stroke-dasharray="3,2.5" />',
            f'    <line x1="{zx:.1f}" y1="{zy:.1f}" x2="{rx:.1f}" y2="{ry:.1f}" class="c-main" />',
            _curly_brace(zx, zy, rx, ry, offset=9.5, cls="c-main"),
        ]
    )
    labels = "\n".join(
        [
            math_label(122.0, 136.0, "D", size=18.0),
            point_dot(zx, zy),
            math_label(310.0, 144.0, "z"),
            point_dot(hx, hy, color="#1e3a8a"),
            math_label(300.0, 96.0, "z + h", color="#1e3a8a"),
            math_label(346.0, 136.0, "\u03c1"),
        ]
    )
    return svg_document(
        "0 0 460 250",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_3",
        title=CHAPTER_FIG_TITLES["1_3"],
        show_grid=False,
    )


def fig_1_4() -> str:
    ox, oy, r = 242.0, 158.0, 100.0
    axes, ax_labels = axes_xy(
        ox, oy, 82.0, 412.0, 18.0, 292.0, origin_dx=-15.0, origin_dy=18.0
    )
    regions = f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r:.1f}" class="f-blue" />'
    curves = circle_contour(ox, oy, r, cls="c-blue")
    labels = "\n".join(
        [
            ax_labels,
            math_label(ox + r + 6.0, oy + 15.0, "r"),
            math_label(ox - 24.0, oy - r - 6.0, "ir"),
            math_label(ox + 68.0, oy - 74.0, "C", sub="r", color="#1e3a8a"),
        ]
    )
    return svg_document(
        "0 0 460 308",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_4",
        title=CHAPTER_FIG_TITLES["1_4"],
    )


def fig_1_5() -> str:
    ox, oy, r = 205.0, 155.0, 88.0
    axes, ax_labels = axes_xy(
        ox, oy, 58.0, 385.0, 18.0, 285.0, origin_dx=-15.0, origin_dy=17.0
    )
    deg = 33.0
    rad = math.radians(deg)
    ux, uy = ox + r * math.cos(rad), oy - r * math.sin(rad)
    zx, zy = ox + 148.0 * math.cos(rad), oy - 148.0 * math.sin(rad)
    regions = f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r:.1f}" class="f-blue" opacity="0.45" />'
    curves = "\n".join(
        [
            circle_contour(ox, oy, r, cls="c-blue"),
            arrow_line(ox, oy, zx, zy, cls="c-main", marker="arr"),
            arc_path(ox, oy, 38.0, 0.0, deg, cls="c-red", ccw=True, arrow_mid=False),
            tangent_arrow(
                ox + 38.0 * math.cos(rad),
                oy - 38.0 * math.sin(rad),
                -math.sin(rad),
                -math.cos(rad),
                marker="arr-red",
            ),
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            point_dot(ux, uy, color="#1e3a8a", r=2.8),
            math_label(248.0, 148.0, "\u03b8", color="#dc2626"),
            math_label(284.0, 115.0, "e", sup="i\u03b8", color="#1e3a8a"),
            math_label(zx + 5.0, zy + 2.0, "z"),
        ]
    )
    return svg_document(
        "0 0 460 300",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_5",
        title=CHAPTER_FIG_TITLES["1_5"],
    )


def fig_1_6() -> str:
    ox, oy = 150.0, 212.0
    axes, ax_labels = axes_xy(
        ox, oy, 18.0, 426.0, 18.0, 286.0, origin_dx=-15.0, origin_dy=17.0
    )
    x_int = 58.0
    bx, by = 258.0, 152.0
    alpha_rad = math.atan2(oy - by, bx - x_int)
    alpha_deg = math.degrees(alpha_rad)
    ca, sa = math.cos(alpha_rad), math.sin(alpha_rad)
    u0x, u0y = x_int - 42.0 * ca, oy + 42.0 * sa
    u1x, u1y = x_int + 378.0 * ca, oy - 378.0 * sa
    v0x, v0y = bx + 132.0 * sa, by + 132.0 * ca
    v1x, v1y = bx - 138.0 * sa, by - 138.0 * ca
    r_arc = 52.0
    curves = "\n".join(
        [
            arrow_line(u0x, u0y, u1x, u1y, cls="c-blue", marker="arr-blue"),
            arrow_line(v0x, v0y, v1x, v1y, cls="c-blue", marker="arr-blue"),
            arc_path(x_int, oy, r_arc, 0.0, alpha_deg, cls="c-red", ccw=True),
            tangent_arrow(
                x_int + r_arc * ca,
                oy - r_arc * sa,
                -sa,
                -ca,
                marker="arr-red",
            ),
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            point_dot(bx, by, color="#1e3a8a", r=2.9),
            math_label(u1x + 5.0, u1y + 4.0, "u", color="#1e3a8a"),
            math_label(v1x - 24.0, v1y + 8.0, "iv", color="#1e3a8a"),
            math_label(bx - 12.0, by + 21.0, "b", color="#1e3a8a"),
            math_label(x_int + 56.0, oy - 4.0, "\u03b1", color="#dc2626"),
        ]
    )
    return svg_document(
        "0 0 460 300",
        grid=axes,
        curve=curves,
        label=labels,
        fig_id="1_6",
        title=CHAPTER_FIG_TITLES["1_6"],
    )


def fig_1_7() -> str:
    ox, oy = 206.0, 148.0
    axes, ax_labels = axes_xy(
        ox,
        oy,
        18.0,
        438.0,
        18.0,
        268.0,
        origin_label="",
    )
    pts = [
        (72.0, 240.0),
        (118.0, 148.0),
        (160.0, 105.0),
        (206.0, 88.0),
        (254.0, 108.0),
        (292.0, 148.0),
        (334.0, 182.0),
        (382.0, 148.0),
        (430.0, 56.0),
    ]
    tx, ty = 160.0, 105.0
    curves = "\n".join(
        [
            smooth_curve(pts, cls="c-blue"),
            arrow_line(tx, ty, tx + 22.0, ty - 14.0, cls="c-red", marker="arr-red"),
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            point_dot(pts[0][0], pts[0][1], color="#1e3a8a"),
            point_dot(tx, ty, color="#dc2626"),
            point_dot(pts[-1][0], pts[-1][1], color="#1e3a8a"),
            math_label(50.0, 263.0, "\u03b3(a)"),
            math_label(108.0, 98.0, "\u03b3(t)", color="#dc2626"),
            math_label(392.0, 46.0, "\u03b3(b)"),
        ]
    )
    return svg_document(
        "0 0 460 280",
        grid=axes,
        curve=curves,
        label=labels,
        fig_id="1_7",
        title=CHAPTER_FIG_TITLES["1_7"],
    )


def _fig_1_8_trace(ox: float) -> list[tuple[float, float]]:
    return [
        (ox - 84.0, 52.0),
        (ox - 48.0, 36.0),
        (ox - 12.0, 54.0),
        (ox, 95.0),
        (ox - 26.0, 138.0),
        (ox - 52.0, 195.0),
        (ox - 24.0, 242.0),
        (ox, 250.0),
        (ox + 24.0, 242.0),
        (ox + 52.0, 195.0),
        (ox + 26.0, 138.0),
        (ox, 95.0),
        (ox + 12.0, 54.0),
        (ox + 48.0, 36.0),
        (ox + 84.0, 52.0),
    ]


def fig_1_8() -> str:
    ox1, ox2, oy = 126.0, 386.0, 195.0
    axes1, lbl1 = axes_xy(
        ox1, oy, 26.0, 224.0, 18.0, 278.0, origin_dx=-13.0, origin_dy=16.0
    )
    axes2, lbl2 = axes_xy(
        ox2, oy, 286.0, 484.0, 18.0, 278.0, origin_dx=-13.0, origin_dy=16.0
    )
    pts1 = _fig_1_8_trace(ox1)
    pts2 = _fig_1_8_trace(ox2)
    arrows1 = [(1, True), (3, True), (6, True), (10, True), (12, True)]
    arrows2 = [(1, False), (3, False), (7, False), (10, False), (12, False)]
    regions = "\n".join(
        [
            f'    <circle cx="{ox1:.1f}" cy="192.0" r="50.0" class="f-blue" opacity="0.35" />',
            f'    <circle cx="{ox2:.1f}" cy="192.0" r="50.0" class="f-amber" opacity="0.35" />',
        ]
    )
    curves = "\n".join(
        [
            smooth_curve(pts1, cls="c-blue", arrow_indices=arrows1, marker="arr-blue"),
            smooth_curve(
                pts2, cls="c-amber", arrow_indices=arrows2, marker="arr-amber"
            ),
        ]
    )
    labels = "\n".join(
        [
            lbl1,
            lbl2,
            math_label(14.0, 72.0, "\u03b3", sub="1", tail="(a)", color="#1e3a8a"),
            math_label(188.0, 72.0, "\u03b3", sub="1", tail="(b)", color="#1e3a8a"),
            math_label(36.0, 264.0, "\u03b3", sub="1", color="#1e3a8a"),
            math_label(274.0, 72.0, "\u03b3", sub="2", tail="(a)", color="#b45309"),
            math_label(448.0, 72.0, "\u03b3", sub="2", tail="(b)", color="#b45309"),
            math_label(296.0, 264.0, "\u03b3", sub="2", color="#b45309"),
        ]
    )
    return svg_document(
        "0 0 520 292",
        grid=f"{axes1}\n{axes2}",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_8",
        title=CHAPTER_FIG_TITLES["1_8"],
    )


def fig_1_9() -> str:
    c_top = (122.0, 30.0)
    c_left = (24.0, 220.0)
    c_bot = (218.0, 240.0)
    c_right = (320.0, 112.0)
    seg_left = [c_top, (154.0, 74.0), (146.0, 118.0), (104.0, 158.0), c_left]
    seg_bot = [c_left, (82.0, 202.0), (150.0, 206.0), c_bot]
    seg_right = [c_bot, (214.0, 184.0), (244.0, 146.0), (288.0, 132.0), c_right]
    seg_top = [c_right, (284.0, 76.0), (236.0, 36.0), (178.0, 24.0), c_top]
    poly_pts = " ".join(
        f"{x:.1f},{y:.1f}"
        for x, y in (seg_left[:-1] + seg_bot[:-1] + seg_right[:-1] + seg_top[:-1])
    )
    regions = f'    <polygon points="{poly_pts}" class="f-blue" opacity="0.48" />'
    curves = "\n".join(
        [
            smooth_curve(
                seg_left, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                seg_bot, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                seg_right, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                seg_top, cls="c-blue", arrow_indices=[(0, True)], marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(236.0, 36.0, color="#1e3a8a"),
            point_dot(104.0, 158.0, color="#1e3a8a"),
            point_dot(c_right[0], c_right[1], color="#dc2626"),
            math_label(244.0, 32.0, "\u03b3(s)", color="#1e3a8a"),
            math_label(50.0, 153.0, "\u03b3(t)", color="#1e3a8a"),
            math_label(328.0, 117.0, "\u03b3(b) = \u03b3(a)", color="#dc2626"),
            '    <text x="215.0" y="274.0" class="lbl" text-anchor="middle">Jordan curve</text>',
        ]
    )
    return svg_document(
        "0 0 460 288",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_9",
        title=CHAPTER_FIG_TITLES["1_9"],
        show_grid=False,
    )


def fig_1_10() -> str:
    tri = "54.0,192.0 230.0,22.0 406.0,192.0"
    regions = "\n".join(
        [
            f'    <polygon points="{tri}" class="f-blue" />',
            f'    <polygon points="{tri}" class="f-stipple" />',
        ]
    )
    curves = f'    <polygon points="{tri}" class="c-sub" stroke-dasharray="3,3" />'
    labels = "\n".join(
        [
            point_dot(206.0, 92.0, color="#1e3a8a"),
            math_label(216.0, 97.0, "\u03b3(t)", color="#1e3a8a"),
            math_label(224.0, 156.0, "C", size=18.0),
            math_label(22.0, 215.0, "\u03b3(a)"),
            math_label(384.0, 215.0, "\u03b3(b)"),
        ]
    )
    return svg_document(
        "0 0 460 236",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_10",
        title=CHAPTER_FIG_TITLES["1_10"],
        show_grid=False,
    )


def fig_1_11() -> str:
    ox, oy = 245.0, 238.0
    axes, ax_labels = axes_xy(
        ox, oy, 18.0, 438.0, 18.0, 286.0, origin_dx=-15.0, origin_dy=17.0
    )
    deg = 30.0
    rad = math.radians(deg)
    ca, sa = math.cos(rad), math.sin(rad)
    x_int = 62.0
    tx, ty = x_int + 106.0 * ca, oy - 106.0 * sa
    l0x, l0y = x_int - 44.0 * ca, oy + 44.0 * sa
    l1x, l1y = x_int + 412.0 * ca, oy - 412.0 * sa
    lax, lay = x_int + 188.0 * ca, oy - 188.0 * sa
    vx, vy = ox + 112.0 * ca, oy - 112.0 * sa
    curve_pts = [
        (46.0, 195.0),
        (95.0, 200.0),
        (tx, ty),
        (206.0, 134.0),
        (245.0, 86.0),
        (318.0, 46.0),
        (372.0, 62.0),
        (402.0, 92.0),
    ]
    r_arc = 46.0
    curves = "\n".join(
        [
            smooth_curve(curve_pts, cls="c-blue"),
            f'    <line x1="{l0x:.1f}" y1="{l0y:.1f}" x2="{l1x:.1f}" y2="{l1y:.1f}" class="c-main" stroke-width="1.35" />',
            tangent_arrow(lax, lay, ca, -sa, marker="arr"),
            arrow_line(ox, oy, vx, vy, cls="c-red", marker="arr-red"),
            arc_path(x_int, oy, r_arc, 0.0, deg, cls="c-red", ccw=True),
            tangent_arrow(
                x_int + r_arc * ca, oy - r_arc * sa, -sa, -ca, marker="arr-red"
            ),
            arc_path(ox, oy, r_arc, 0.0, deg, cls="c-red", ccw=True),
            tangent_arrow(ox + r_arc * ca, oy - r_arc * sa, -sa, -ca, marker="arr-red"),
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            point_dot(tx, ty, color="#1e3a8a"),
            math_label(20.0, 184.0, "\u03b3(a)", color="#1e3a8a"),
            math_label(
                tx + 4.0, ty + 20.0, "\u03b3(t", sub="0", tail=")", color="#1e3a8a"
            ),
            math_label(288.0, 126.0, "l(t)"),
            math_label(
                vx + 4.0, vy + 2.0, "\u03b3\u2032(t", sub="0", tail=")", color="#dc2626"
            ),
            math_label(384.0, 114.0, "\u03b3(b)", color="#1e3a8a"),
            math_label(x_int + 52.0, oy - 6.0, "\u03b8", color="#dc2626"),
            math_label(ox + 52.0, oy - 6.0, "\u03b8", color="#dc2626"),
        ]
    )
    return svg_document(
        "0 0 460 300",
        grid=axes,
        curve=curves,
        label=labels,
        fig_id="1_11",
        title=CHAPTER_FIG_TITLES["1_11"],
    )


def fig_1_12() -> str:
    ox, oy = 132.0, 145.0
    axes, ax_labels = axes_xy(
        ox, oy, 22.0, 392.0, 18.0, 275.0, origin_dx=-16.0, origin_dy=18.0
    )
    scale_x, scale_y = 182.0, 112.0
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for k in range(19):
        u = k / 16.5
        dx = scale_x * (u**2)
        dy = scale_y * (u**3)
        upper.append((ox + dx, oy - dy))
        lower.append((ox + dx, oy + dy))
    x1 = ox + scale_x
    curves = "\n".join(
        [
            smooth_curve(upper, cls="c-blue"),
            smooth_curve(lower, cls="c-blue"),
            f'    <line x1="{x1:.1f}" y1="{oy - 5.0:.1f}" x2="{x1:.1f}" y2="{oy + 5.0:.1f}" class="ax" />',
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            point_dot(ox, oy, color="#dc2626"),
            math_label(x1 - 4.0, oy - 10.0, "1", italic=False),
        ]
    )
    return svg_document(
        "0 0 420 290",
        grid=axes,
        curve=curves,
        label=labels,
        fig_id="1_12",
        title=CHAPTER_FIG_TITLES["1_12"],
    )


def fig_1_13() -> str:
    ox, oy = 136.0, 190.0
    axes, ax_labels = axes_xy(
        ox,
        oy,
        18.0,
        438.0,
        18.0,
        268.0,
        origin_label="",
    )
    pts: list[tuple[float, float]] = []
    steps = 160
    max_theta = 6.5 * math.pi
    for k in range(steps + 1):
        theta = max_theta * (1.0 - k / steps)
        r = 220.0 / ((1.0 + 0.34 * theta) ** 2.05)
        x = ox + r * math.cos(theta)
        y = oy - 0.86 * r * math.sin(theta)
        pts.append((x, y))
    x1, y1 = pts[-1]
    curves = smooth_curve(pts, cls="c-blue")
    labels = "\n".join(
        [
            ax_labels,
            point_dot(ox, oy, color="#dc2626", r=3.5),
            math_label(x1 - 4.0, y1 + 21.0, "1", italic=False),
        ]
    )
    return svg_document(
        "0 0 460 280",
        grid=axes,
        curve=curves,
        label=labels,
        fig_id="1_13",
        title=CHAPTER_FIG_TITLES["1_13"],
    )


def fig_1_14() -> str:
    ox, oy = 276.0, 294.0
    axes, ax_labels = axes_xy(
        ox, oy, 18.0, 438.0, 18.0, 326.0, origin_dx=-15.0, origin_dy=17.0
    )
    z0x, z0y = 140.0, 184.0
    a1, a2 = 44.0, 152.0
    r1, r2 = math.radians(a1), math.radians(a2)
    c1, s1 = math.cos(r1), math.sin(r1)
    c2, s2 = math.cos(r2), math.sin(r2)
    gamma_pts = [
        (20.0, 212.0),
        (88.0, 206.0),
        (z0x, z0y),
        (178.0, 136.0),
        (216.0, 82.0),
        (268.0, 56.0),
        (318.0, 48.0),
    ]
    lam_pts = [
        (338.0, 190.0),
        (292.0, 190.0),
        (225.0, 198.0),
        (z0x, z0y),
        (82.0, 136.0),
        (40.0, 110.0),
    ]
    t1_0x, t1_0y = z0x - 118.0 * c1, z0y + 118.0 * s1
    t1_1x, t1_1y = z0x + 236.0 * c1, z0y - 236.0 * s1
    t2_0x, t2_0y = z0x - 242.0 * c2, z0y + 242.0 * s2
    t2_1x, t2_1y = z0x + 118.0 * c2, z0y - 118.0 * s2
    v1x, v1y = ox + 104.0 * c1, oy - 104.0 * s1
    v2x, v2y = ox + 94.0 * c2, oy - 94.0 * s2
    curves = "\n".join(
        [
            f'    <line x1="{t1_0x:.1f}" y1="{t1_0y:.1f}" x2="{t1_1x:.1f}" y2="{t1_1y:.1f}" class="c-sub" stroke-width="1.25" />',
            f'    <line x1="{t2_0x:.1f}" y1="{t2_0y:.1f}" x2="{t2_1x:.1f}" y2="{t2_1y:.1f}" class="c-sub" stroke-width="1.25" />',
            smooth_curve(
                gamma_pts, cls="c-blue", arrow_indices=[(3, True)], marker="arr-blue"
            ),
            smooth_curve(
                lam_pts, cls="c-green", arrow_indices=[(4, True)], marker="arr-green"
            ),
            arc_path(z0x, z0y, 35.0, a1, a2, cls="c-red", ccw=True),
            tangent_arrow(z0x + 35.0 * c2, z0y - 35.0 * s2, -s2, -c2, marker="arr-red"),
            arrow_line(ox, oy, v1x, v1y, cls="c-blue", marker="arr-blue"),
            arrow_line(ox, oy, v2x, v2y, cls="c-green", marker="arr-green"),
            arc_path(ox, oy, 36.0, a1, a2, cls="c-red", ccw=True),
            tangent_arrow(ox + 36.0 * c2, oy - 36.0 * s2, -s2, -c2, marker="arr-red"),
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            point_dot(z0x, z0y),
            math_label(z0x - 6.0, z0y + 20.0, "z", sub="0"),
            math_label(208.0, 68.0, "\u03b3", color="#1e3a8a"),
            math_label(76.0, 124.0, "\u03bb", color="#047857"),
            math_label(z0x - 8.0, z0y - 43.0, "\u03b8", color="#dc2626"),
            math_label(ox - 18.0, oy - 43.0, "\u03b8", color="#dc2626"),
            math_label(
                v1x + 4.0,
                v1y + 2.0,
                "\u03b3\u2032(t",
                sub="0",
                tail=")",
                color="#1e3a8a",
            ),
            math_label(
                v2x - 22.0,
                v2y - 6.0,
                "\u03bb\u2032(s",
                sub="0",
                tail=")",
                color="#047857",
            ),
        ]
    )
    return svg_document(
        "0 0 460 338",
        grid=axes,
        curve=curves,
        label=labels,
        fig_id="1_14",
        title=CHAPTER_FIG_TITLES["1_14"],
    )


def fig_1_15() -> str:
    domain_pts = [
        (24.0, 162.0),
        (48.0, 96.0),
        (158.0, 66.0),
        (254.0, 18.0),
        (366.0, 32.0),
        (434.0, 118.0),
        (424.0, 212.0),
        (348.0, 248.0),
        (236.0, 260.0),
        (106.0, 246.0),
    ]
    gamma_pts = [
        (148.0, 214.0),
        (166.0, 182.0),
        (194.0, 172.0),
        (212.0, 190.0),
        (202.0, 206.0),
        (188.0, 192.0),
        (198.0, 152.0),
        (232.0, 124.0),
        (274.0, 134.0),
        (286.0, 162.0),
        (266.0, 174.0),
        (246.0, 148.0),
        (264.0, 96.0),
        (308.0, 76.0),
        (352.0, 96.0),
    ]
    regions = "\n".join(
        [
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-stipple"),
        ]
    )
    curves = smooth_curve(
        gamma_pts,
        cls="c-blue",
        arrow_indices=[(0, True), (2, True), (6, True), (8, True), (12, True)],
        marker="arr-blue",
    )
    labels = "\n".join(
        [
            point_dot(148.0, 214.0, color="#1e3a8a"),
            point_dot(352.0, 96.0, color="#dc2626"),
            math_label(152.0, 232.0, "\u03b1 = \u03b3(a)", color="#1e3a8a"),
            math_label(316.0, 122.0, "\u03b2 = \u03b3(b)", color="#dc2626"),
            math_label(208.0, 114.0, "\u03b3", color="#1e3a8a"),
            math_label(298.0, 210.0, "D", size=18.0),
        ]
    )
    return svg_document(
        "0 0 460 278",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_15",
        title=CHAPTER_FIG_TITLES["1_15"],
        show_grid=False,
    )


def fig_1_16() -> str:
    arc1 = [
        (48.0, 188.0),
        (58.0, 132.0),
        (96.0, 94.0),
        (144.0, 88.0),
        (166.0, 106.0),
        (170.0, 134.0),
        (166.0, 168.0),
        (190.0, 214.0),
        (234.0, 218.0),
        (272.0, 164.0),
        (264.0, 112.0),
        (230.0, 98.0),
        (182.0, 106.0),
        (166.0, 100.0),
    ]
    arc2 = [
        (166.0, 100.0),
        (176.0, 70.0),
        (220.0, 36.0),
        (276.0, 26.0),
        (332.0, 34.0),
        (406.0, 72.0),
    ]
    curves = "\n".join(
        [
            smooth_curve(
                arc1,
                cls="c-blue",
                arrow_indices=[
                    (0, True),
                    (2, True),
                    (5, True),
                    (7, True),
                    (9, True),
                    (11, True),
                ],
                marker="arr-blue",
            ),
            smooth_curve(
                arc2,
                cls="c-blue",
                arrow_indices=[(1, True), (3, True)],
                marker="arr-blue",
            ),
        ]
    )
    z_dots = [
        (48.0, 188.0),
        (58.0, 132.0),
        (96.0, 94.0),
        (144.0, 88.0),
        (166.0, 168.0),
        (190.0, 214.0),
        (272.0, 164.0),
        (230.0, 98.0),
        (176.0, 70.0),
        (260.0, 27.0),
        (332.0, 34.0),
        (406.0, 72.0),
    ]
    zeta_tris = [
        (51.0, 160.0, 8.0, -45.0),
        (76.0, 108.0, 34.0, -32.0),
        (120.0, 88.0, 42.0, -4.0),
        (174.0, 194.0, 22.0, 36.0),
        (248.0, 204.0, 28.0, -28.0),
        (262.0, 106.0, -28.0, -14.0),
        (202.0, 103.0, -36.0, 4.0),
        (220.0, 36.0, 42.0, -18.0),
        (294.0, 27.0, 42.0, 4.0),
        (368.0, 51.0, 42.0, 20.0),
    ]
    labels = "\n".join(
        [point_dot(x, y) for x, y in z_dots]
        + [
            _sample_triangle(x, y, dx, dy, color="#dc2626")
            for x, y, dx, dy in zeta_tris
        ]
        + [
            math_label(14.0, 214.0, "z", sub="0", tail=" = \u03b3(a)"),
            math_label(58.0, 168.0, "\u03b6", sub="1", color="#dc2626"),
            math_label(34.0, 132.0, "z", sub="1"),
            math_label(80.0, 128.0, "\u03b6", sub="2", color="#dc2626"),
            math_label(82.0, 82.0, "z", sub="2"),
            math_label(186.0, 200.0, "z", sub="k\u22121"),
            math_label(198.0, 242.0, "\u03b3", color="#1e3a8a"),
            math_label(248.0, 224.0, "\u03b6", sub="k", color="#dc2626"),
            math_label(244.0, 160.0, "z", sub="k"),
            math_label(324.0, 24.0, "z", sub="m\u22121"),
            math_label(354.0, 74.0, "\u03b6", sub="m", color="#dc2626"),
            math_label(384.0, 54.0, "z", sub="m", tail=" = \u03b3(b)"),
        ]
    )
    return svg_document(
        "0 0 480 256",
        curve=curves,
        label=labels,
        fig_id="1_16",
        title=CHAPTER_FIG_TITLES["1_16"],
        show_grid=False,
    )


def fig_1_17() -> str:
    domain_pts = [
        (56.0, 156.0),
        (96.0, 82.0),
        (194.0, 74.0),
        (292.0, 22.0),
        (388.0, 24.0),
        (436.0, 96.0),
        (438.0, 198.0),
        (368.0, 236.0),
        (244.0, 232.0),
        (174.0, 210.0),
        (82.0, 212.0),
    ]
    cx, cy, r = 344.0, 142.0, 68.0
    wx, wy = 372.0, 168.0
    regions = "\n".join(
        [
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-stipple"),
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-amber" />',
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#stipple-amber)" />',
        ]
    )
    curves = circle_contour(
        cx, cy, r, cls="c-blue", arrow_deg=56.0, ccw=True, marker="arr-blue"
    )
    labels = "\n".join(
        [
            math_label(162.0, 148.0, "D", size=18.0),
            point_dot(cx, cy),
            math_label(cx - 18.0, cy + 5.0, "c"),
            f'    <text x="{wx:.1f}" y="{wy + 5.0:.1f}" class="lbl" fill="#dc2626" text-anchor="middle">*</text>',
            math_label(wx - 22.0, wy + 4.0, "w", color="#dc2626"),
            math_label(cx + 36.0, cy - 72.0, "\u03b3", color="#1e3a8a"),
        ]
    )
    return svg_document(
        "0 0 460 252",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_17",
        title=CHAPTER_FIG_TITLES["1_17"],
        show_grid=False,
    )


def _closed_bezier_d(points: list[tuple[float, float]]) -> str:
    pts = list(points)
    n = len(pts)
    padded = [pts[-1]] + pts + [pts[0], pts[1]]
    segs: list[str] = [f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"]
    for i in range(n):
        p0, p1, p2, p3 = padded[i], padded[i + 1], padded[i + 2], padded[i + 3]
        c1x = p1[0] + (p2[0] - p0[0]) / 6.0
        c1y = p1[1] + (p2[1] - p0[1]) / 6.0
        c2x = p2[0] - (p3[0] - p1[0]) / 6.0
        c2y = p2[1] - (p3[1] - p1[1]) / 6.0
        segs.append(
            f"C {c1x:.2f} {c1y:.2f}, {c2x:.2f} {c2y:.2f}, {p2[0]:.2f} {p2[1]:.2f}"
        )
    segs.append("Z")
    return " ".join(segs)


def fig_1_18() -> str:
    outer_pts = [
        (24.0, 148.0),
        (56.0, 54.0),
        (178.0, 16.0),
        (338.0, 26.0),
        (434.0, 96.0),
        (436.0, 198.0),
        (348.0, 272.0),
        (194.0, 282.0),
        (64.0, 246.0),
    ]
    hole_pts = [
        (168.0, 134.0),
        (182.0, 120.0),
        (200.0, 132.0),
        (202.0, 152.0),
        (184.0, 156.0),
    ]
    g0_pts = [
        (150.0, 136.0),
        (178.0, 106.0),
        (210.0, 118.0),
        (225.0, 140.0),
        (234.0, 166.0),
        (196.0, 174.0),
        (158.0, 160.0),
    ]
    gs_pts = [
        (102.0, 142.0),
        (134.0, 74.0),
        (188.0, 68.0),
        (232.0, 98.0),
        (288.0, 95.0),
        (330.0, 117.0),
        (344.0, 156.0),
        (302.0, 206.0),
        (242.0, 216.0),
        (184.0, 196.0),
        (114.0, 184.0),
    ]
    g1_pts = [
        (70.0, 152.0),
        (108.0, 54.0),
        (184.0, 42.0),
        (238.0, 82.0),
        (320.0, 72.0),
        (372.0, 108.0),
        (392.0, 168.0),
        (344.0, 214.0),
        (274.0, 246.0),
        (192.0, 224.0),
        (88.0, 202.0),
    ]
    annulus_d = f"{_closed_bezier_d(outer_pts)} {_closed_bezier_d(hole_pts)}"
    regions = "\n".join(
        [
            f'    <path d="{annulus_d}" class="f-blue" fill-rule="evenodd" />',
            f'    <path d="{annulus_d}" class="f-stipple" fill-rule="evenodd" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{_closed_bezier_d(outer_pts)}" class="c-sub" />',
            f'    <path d="{_closed_bezier_d(hole_pts)}" class="c-sub" />',
            smooth_curve(g0_pts, cls="c-green", closed=True),
            smooth_curve(gs_pts, cls="c-amber", closed=True),
            smooth_curve(g1_pts, cls="c-blue", closed=True),
            '    <line x1="225.0" y1="140.0" x2="372.0" y2="108.0" class="c-red" />',
        ]
    )
    labels = "\n".join(
        [
            point_dot(225.0, 140.0, color="#047857"),
            point_dot(330.0, 117.0, color="#b45309"),
            point_dot(372.0, 108.0, color="#1e3a8a"),
            math_label(210.0, 122.0, "\u03b3", sub="0", tail="(t)", color="#047857"),
            math_label(302.0, 103.0, "\u03b3", sub="s", tail="(t)", color="#b45309"),
            math_label(368.0, 96.0, "\u03b3", sub="1", tail="(t)", color="#1e3a8a"),
            math_label(278.0, 148.0, "L", sub="t", color="#dc2626"),
            math_label(168.0, 256.0, "D", size=18.0),
        ]
    )
    return svg_document(
        "0 0 460 298",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_18",
        title=CHAPTER_FIG_TITLES["1_18"],
        show_grid=False,
    )


def fig_1_19() -> str:
    ox, oy = 66.0, 214.0
    axes, ax_labels = axes_xy(
        ox,
        oy,
        18.0,
        396.0,
        20.0,
        246.0,
        x_label="t",
        y_label="s",
        origin_dx=-15.0,
        origin_dy=18.0,
    )
    xa, xb, y1 = 132.0, 326.0, 84.0
    w, h = xb - xa, oy - y1
    regions = "\n".join(
        [
            f'    <rect x="{xa:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{h:.1f}" class="f-blue" />',
            f'    <rect x="{xa:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{h:.1f}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <rect x="{xa:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{h:.1f}" class="c-blue" />',
            f'    <line x1="{ox:.1f}" y1="{y1:.1f}" x2="{ox + 8.0:.1f}" y2="{y1:.1f}" class="ax" />',
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            math_label(ox - 16.0, y1 + 5.0, "1", italic=False),
            math_label(xa - 4.0, oy + 20.0, "a"),
            math_label(xb - 4.0, oy + 20.0, "b"),
            math_label(0.5 * (xa + xb) - 6.0, 0.5 * (y1 + oy) + 6.0, "K", size=17.0),
        ]
    )
    return svg_document(
        "0 0 436 256",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_19",
        title=CHAPTER_FIG_TITLES["1_19"],
    )


def fig_1_20() -> str:
    cx, cy, r_big = 206.0, 155.0, 122.0
    wx, wy, r_eps = 264.0, 192.0, 38.0
    deg = 48.0
    rad = math.radians(deg)
    gx, gy = cx + r_big * math.cos(rad), cy - r_big * math.sin(rad)
    gex, gey = wx + r_eps * math.cos(rad), wy - r_eps * math.sin(rad)
    regions = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_big:.1f}" class="f-blue" opacity="0.48" />',
            f'    <circle cx="{wx:.1f}" cy="{wy:.1f}" r="{r_eps:.1f}" class="f-amber" opacity="0.72" />',
        ]
    )
    curves = "\n".join(
        [
            circle_contour(cx, cy, r_big, cls="c-blue"),
            circle_contour(wx, wy, r_eps, cls="c-amber"),
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{gx:.1f}" y2="{gy:.1f}" class="c-main" />',
            f'    <line x1="{wx:.1f}" y1="{wy:.1f}" x2="{gex:.1f}" y2="{gey:.1f}" class="c-main" />',
            f'    <line x1="{gex:.1f}" y1="{gey:.1f}" x2="{gx:.1f}" y2="{gy:.1f}" class="c-red" />',
        ]
    )
    labels = "\n".join(
        [
            point_dot(cx, cy),
            point_dot(wx, wy),
            point_dot(gx, gy, color="#1e3a8a"),
            point_dot(gex, gey, color="#b45309"),
            math_label(cx - 16.0, cy + 5.0, "c"),
            math_label(wx - 21.0, wy + 5.0, "w"),
            math_label(gx + 6.0, gy - 6.0, "\u03b3(\u03b8)", color="#1e3a8a"),
            math_label(
                0.5 * (gx + gex) + 6.0,
                0.5 * (gy + gey) + 6.0,
                "L",
                sub="\u03b8",
                color="#dc2626",
            ),
            math_label(
                gex + 6.0,
                gey + 2.0,
                "\u03b3",
                sub="\u03b5",
                tail="(\u03b8)",
                color="#b45309",
            ),
        ]
    )
    return svg_document(
        "0 0 420 306",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_20",
        title=CHAPTER_FIG_TITLES["1_20"],
        show_grid=False,
    )


def fig_1_21() -> str:
    p_bl = (42.0, 240.0)
    p_br = (368.0, 254.0)
    p_tl = (96.0, 72.0)
    p_tr = (406.0, 76.0)
    g0 = [p_bl, (148.0, 220.0), (254.0, 238.0), p_br]
    g1 = [p_tl, (214.0, 36.0), (318.0, 68.0), p_tr]
    ga = [p_bl, (84.0, 166.0), (108.0, 114.0), p_tl]
    gb = [p_br, (388.0, 206.0), (374.0, 142.0), p_tr]
    poly = " ".join(
        f"{x:.1f},{y:.1f}"
        for x, y in (
            g0[:-1] + gb[:-1] + list(reversed(g1))[:-1] + list(reversed(ga))[:-1]
        )
    )
    regions = f'    <polygon points="{poly}" class="f-blue" opacity="0.45" />'
    curves = "\n".join(
        [
            smooth_curve(
                g0, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                g1, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                ga, cls="c-green", arrow_indices=[(1, True)], marker="arr-green"
            ),
            smooth_curve(
                gb, cls="c-green", arrow_indices=[(1, True)], marker="arr-green"
            ),
        ]
    )
    labels = "\n".join(
        [
            math_label(210.0, 260.0, "\u03b3", sub="0", color="#1e3a8a"),
            math_label(248.0, 26.0, "\u03b3", sub="1", color="#1e3a8a"),
            (
                '    <text x="52.0" y="156.0" class="it" fill="#047857">'
                '<tspan font-size="10.5px" dy="3.2">a</tspan>'
                '<tspan dy="-3.2">\u03b3</tspan></text>'
            ),
            (
                '    <text x="386.0" y="168.0" class="it" fill="#047857">'
                '<tspan font-size="10.5px" dy="3.2">b</tspan>'
                '<tspan dy="-3.2">\u03b3</tspan></text>'
            ),
        ]
    )
    return svg_document(
        "0 0 440 280",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_21",
        title=CHAPTER_FIG_TITLES["1_21"],
        show_grid=False,
    )


def fig_1_22() -> str:
    domain_pts = [
        (24.0, 152.0),
        (54.0, 92.0),
        (168.0, 64.0),
        (262.0, 16.0),
        (348.0, 42.0),
        (388.0, 98.0),
        (436.0, 198.0),
        (398.0, 236.0),
        (264.0, 218.0),
        (114.0, 200.0),
    ]
    cx, cy, r = 322.0, 116.0, 62.0
    ang = math.radians(-22.0)
    rx, ry = cx + r * math.cos(ang), cy - r * math.sin(ang)
    regions = "\n".join(
        [
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(domain_pts, cls="c-sub", closed=True, fill_cls="f-stipple"),
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-amber" />',
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#stipple-amber)" />',
        ]
    )
    curves = "\n".join(
        [
            circle_contour(cx, cy, r, cls="c-main"),
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{rx:.1f}" y2="{ry:.1f}" class="c-main" />',
            _curly_brace(cx, cy, rx, ry, offset=-9.5, cls="c-main"),
        ]
    )
    labels = "\n".join(
        [
            math_label(132.0, 145.0, "D", size=18.0),
            point_dot(cx, cy),
            point_dot(364.2, 70.4, color="#dc2626", r=2.8),
            math_label(cx - 16.0, cy + 5.0, "c"),
            math_label(cx + 16.0, cy - 10.0, "r(c)"),
        ]
    )
    return svg_document(
        "0 0 460 250",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_22",
        title=CHAPTER_FIG_TITLES["1_22"],
        show_grid=False,
    )


def fig_1_23() -> str:
    ox, oy, r = 176.0, 130.0, 102.0
    zx, zy = 205.0, 66.0
    deg = 42.0
    rad = math.radians(deg)
    zetax, zetay = ox + r * math.cos(rad), oy - r * math.sin(rad)
    regions = f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r:.1f}" class="f-blue" opacity="0.48" />'
    curves = circle_contour(ox, oy, r, cls="c-blue")
    labels = "\n".join(
        [
            point_dot(ox, oy),
            point_dot(zx, zy, color="#dc2626"),
            point_dot(zetax, zetay, color="#1e3a8a"),
            math_label(ox - 4.0, oy + 20.0, "0", italic=False),
            math_label(zx - 17.0, zy + 4.0, "z", color="#dc2626"),
            math_label(
                zetax + 8.0, zetay - 4.0, "\u03b6 = re", sup="i\u03b8", color="#1e3a8a"
            ),
        ]
    )
    return svg_document(
        "0 0 420 260",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="1_23",
        title=CHAPTER_FIG_TITLES["1_23"],
        show_grid=False,
    )


CHAPTER_FIG_TITLES: dict[str, str] = {
    "1_1": "Fig. 1.1: Parallelogram law of complex addition w = z1 + z2",
    "1_2": "Fig. 1.2: Complex conjugate across the real axis",
    "1_3": "Fig. 1.3: rho-neighborhood U_rho(z) inside domain D",
    "1_4": "Fig. 1.4: Circle of convergence C_r with radius r",
    "1_5": "Fig. 1.5: Polar angle theta and unit circle rotation e^(i theta)",
    "1_6": "Fig. 1.6: Affine coordinate transformation w = z/a - b/a",
    "1_7": "Fig. 1.7: Parameterized curve gamma(t) on [a, b]",
    "1_8": "Fig. 1.8: Curves gamma_1 and gamma_2 with opposite orientations",
    "1_9": "Fig. 1.9: Piecewise smooth closed Jordan curve",
    "1_10": "Fig. 1.10: Space-filling curve filling a triangle C",
    "1_11": "Fig. 1.11: Tangent line l(t) and derivative vector gamma'(t_0)",
    "1_12": "Fig. 1.12: Cusp at the origin on y^2 = x^3",
    "1_13": "Fig. 1.13: Infinitely spiraling C^1 Jordan arc gamma(t) = t^3 e^(2 pi i / t)",
    "1_14": "Fig. 1.14: Angle theta between intersecting smooth curves gamma and lambda",
    "1_15": "Fig. 1.15: Contour integral along curve gamma in domain D",
    "1_16": "Fig. 1.16: Partition points z_k and sample points zeta_k on gamma",
    "1_17": "Fig. 1.17: Cauchy integral formula on disk U_r(c) in D",
    "1_18": "Fig. 1.18: Linear homotopy gamma_s(t) between closed curves in D",
    "1_19": "Fig. 1.19: Parameter rectangle K = [a, b] x [0, 1] in the (t, s)-plane",
    "1_20": "Fig. 1.20: Radial segment L_theta between circles gamma and gamma_epsilon",
    "1_21": "Fig. 1.21: Boundary curves gamma_0, gamma_1, _a gamma, _b gamma of homotopy image",
    "1_22": "Fig. 1.22: Maximal open disk U_r(c)(c) contained in domain D",
    "1_23": "Fig. 1.23: Cauchy kernel power series expansion on circle |zeta| = r",
}


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "1_1": fig_1_1,
    "1_2": fig_1_2,
    "1_3": fig_1_3,
    "1_4": fig_1_4,
    "1_5": fig_1_5,
    "1_6": fig_1_6,
    "1_7": fig_1_7,
    "1_8": fig_1_8,
    "1_9": fig_1_9,
    "1_10": fig_1_10,
    "1_11": fig_1_11,
    "1_12": fig_1_12,
    "1_13": fig_1_13,
    "1_14": fig_1_14,
    "1_15": fig_1_15,
    "1_16": fig_1_16,
    "1_17": fig_1_17,
    "1_18": fig_1_18,
    "1_19": fig_1_19,
    "1_20": fig_1_20,
    "1_21": fig_1_21,
    "1_22": fig_1_22,
    "1_23": fig_1_23,
}
