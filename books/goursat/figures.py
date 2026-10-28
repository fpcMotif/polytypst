import math
import shutil
from collections.abc import Callable
from pathlib import Path

from polytypst.vision.diagram_engine import (
    FigureBook,
    FigureSpec,
    arrow_head,
    axes_2d,
    axes_3d,
    figure_svg,
    labeled_point,
    poly_path,
    render_figures,
    text_label,
)


def generate_fig_1() -> str:
    ox, oy = 85.0, 238.0

    def f(x: float) -> float:
        return oy - (28.0 + 0.0029 * (x - 55.0) ** 2)

    curve_pts = [(x, f(x)) for x in range(115, 365, 4)]
    mx, my = 195.0, f(195.0)
    mpx, mpy = 310.0, f(310.0)
    slope = 2.0 * 0.0029 * (mx - 55.0)
    tx, ty = mpx, my - slope * (mpx - mx)
    sec_slope = (mpy - my) / (mpx - mx)
    body = "\n".join(
        [
            axes_2d(ox, oy, 50, 410, 265, 24),
            f'    <polygon points="{mx:.1f},{my:.1f} {mpx:.1f},{my:.1f} {mpx:.1f},{mpy:.1f}" class="f-blue" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{mpx:.1f}" y1="{mpy:.1f}" x2="{mpx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{mpx:.1f}" y2="{my:.1f}" class="c-dash" />',
            f'    <line x1="{mx - 55:.1f}" y1="{my + slope * 55:.1f}" x2="{mpx + 42:.1f}" y2="{ty - slope * 42:.1f}" class="c-red" />',
            f'    <line x1="{mx - 45:.1f}" y1="{my - sec_slope * 45:.1f}" x2="{mpx + 32:.1f}" y2="{mpy + sec_slope * 32:.1f}" class="c-amber" />',
            poly_path(curve_pts, cls="c-blue"),
            labeled_point(mx, oy, "P", dx=-5, dy=18),
            labeled_point(mpx, oy, "Q", dx=-5, dy=18),
            labeled_point(mpx, my, "N", dx=8, dy=5),
            labeled_point(tx, ty, "T", dx=8, dy=4, color="#dc2626"),
            labeled_point(mx, my, "M", dx=-18, dy=-8, color="#1e3a8a"),
            labeled_point(mpx, mpy, "M'", dx=-22, dy=-8, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 460 285",
        body,
        "fig_1",
        "FIG. 1 — Geometric interpretation of the derivative: secant MM' and tangent MT",
    )


def generate_fig_2() -> str:
    ox, oy = 82.0, 236.0

    def f(x: float) -> float:
        return oy - 16.0 * math.sqrt(max(0.0, x - 95.0)) + 28.0

    curve_pts = [(x, f(x)) for x in range(135, 375, 4)]
    mx, my = 225.0, f(225.0)
    dy_dx = 8.0 / math.sqrt(mx - 95.0)
    tx = mx - (oy - my) / dy_dx
    nx = mx + (oy - my) * dy_dx
    body = "\n".join(
        [
            axes_2d(ox, oy, 45, 415, 265, 25),
            f'    <polygon points="{tx:.1f},{oy:.1f} {mx:.1f},{my:.1f} {nx:.1f},{oy:.1f}" class="f-blue" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{tx - 24:.1f}" y1="{oy + 24 * dy_dx:.1f}" x2="{mx + 95:.1f}" y2="{my - 95 * dy_dx:.1f}" class="c-red" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{nx:.1f}" y2="{oy:.1f}" class="c-green" />',
            poly_path(curve_pts, cls="c-blue"),
            text_label(365, f(365) - 8, "C"),
            labeled_point(tx, oy, "T", dx=-6, dy=18, color="#dc2626"),
            labeled_point(mx, oy, "P", dx=-5, dy=18),
            labeled_point(nx, oy, "N", dx=-5, dy=18, color="#047857"),
            labeled_point(mx, my, "M", dx=-16, dy=-8, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 460 285",
        body,
        "fig_2",
        "FIG. 2 — Tangent MT, normal MN, subtangent TP, and subnormal PN",
    )


def generate_fig_3() -> str:
    ox, oy = 245.0, 178.0
    mx, my = 315.0, 98.0
    dx, dy = mx - ox, my - oy
    ux, uy = -dy, dx
    tx, ty = ox - 0.85 * ux, oy - 0.85 * uy
    nx, ny = ox + 1.35 * ux, oy + 1.35 * uy
    arc_pts = [
        (302.0 + 18.0 * math.sin(t), 98.0 - 52.0 * math.cos(t) + 12.0)
        for t in [i * 0.08 for i in range(-12, 16)]
    ]
    body = "\n".join(
        [
            f'    <polygon points="{ox:.1f},{oy:.1f} {mx:.1f},{my:.1f} {nx:.1f},{ny:.1f}" class="f-green" />',
            f'    <polygon points="{ox:.1f},{oy:.1f} {mx:.1f},{my:.1f} {tx:.1f},{ty:.1f}" class="f-blue" />',
            f'    <line x1="{nx - 28:.1f}" y1="{ny - 18:.1f}" x2="{tx + 22:.1f}" y2="{ty + 14:.1f}" class="ax" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{mx:.1f}" y2="{my:.1f}" class="c-main" />',
            f'    <line x1="{mx:.1f}" y1="{my - 48:.1f}" x2="{tx:.1f}" y2="{ty + 16:.1f}" class="c-red" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{nx - 24:.1f}" y2="{ny:.1f}" class="c-green" />',
            poly_path(arc_pts, cls="c-blue"),
            text_label(arc_pts[-1][0] - 14, arc_pts[-1][1] - 6, "C"),
            labeled_point(ox, oy, "O", dx=-16, dy=15),
            labeled_point(mx, my, "M", dx=8, dy=4, color="#1e3a8a"),
            labeled_point(tx, ty, "T", dx=8, dy=6, color="#dc2626"),
            labeled_point(nx, ny, "N", dx=-6, dy=-8, color="#047857"),
        ]
    )
    return figure_svg(
        "0 0 460 280",
        body,
        "fig_3",
        "FIG. 3 — Polar tangent MT, polar normal MN, polar subtangent OT, and subnormal ON",
    )


def generate_fig_4() -> str:
    ox, oy = 72.0, 244.0
    m0 = (165.0, 185.0)
    m1 = (192.0, 152.0)
    m2 = (224.0, 118.0)
    xy = (335.0, 74.0)
    curve_pts = [
        (
            152.0 + 185.0 * (t / 50.0),
            202.0 - 165.0 * math.sin(1.15 * (t / 50.0)),
        )
        for t in range(51)
    ]
    body = "\n".join(
        [
            axes_2d(ox, oy, 42, 412, 268, 24, xlabel="x", ylabel="y"),
            f'    <rect x="{m0[0] - 38:.1f}" y="{m0[1] - 38:.1f}" width="76" height="76" class="f-blue" stroke="#1e3a8a" stroke-width="1.4" />',
            f'    <rect x="{m1[0] - 36:.1f}" y="{m1[1] - 36:.1f}" width="72" height="72" class="f-amber" stroke="#b45309" stroke-width="1.35" stroke-dasharray="5,3" />',
            f'    <rect x="{m2[0] - 36:.1f}" y="{m2[1] - 36:.1f}" width="72" height="72" class="f-green" stroke="#047857" stroke-width="1.4" />',
            poly_path(curve_pts, cls="c-blue", marker_end="arr-blue"),
            text_label(m0[0] - 54, m0[1] + 44, "A"),
            text_label(m0[0] + 38, m0[1] + 44, "B"),
            text_label(m0[0] + 40, m0[1] - 26, "C"),
            text_label(m0[0] - 54, m0[1] - 26, "D"),
            labeled_point(m0[0], m0[1], "M_0", dx=6, dy=15),
            labeled_point(m1[0], m1[1], "M_1", dx=7, dy=13, color="#b45309"),
            labeled_point(m2[0], m2[1], "M_2", dx=7, dy=4, color="#047857"),
            labeled_point(xy[0], xy[1], "(X, Y)", dx=8, dy=4, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 460 285",
        body,
        "fig_4",
        "FIG. 4 — Analytic continuation of an implicit function across overlapping squares",
    )


def generate_fig_5() -> str:
    c_pts = [(145.0 + 3.2 * t, 178.0 - 0.015 * (t - 28.0) ** 2) for t in range(55)]
    c2_pts = [(235.0 + 1.6 * t - 0.018 * t * t, 52.0 + 3.1 * t) for t in range(52)]
    mx, my = 218.0, 169.0
    m_small = (292.0, 108.0)
    px, py = 175.0, 196.0
    ax, ay = 198.0, 232.0
    body = "\n".join(
        [
            poly_path(c_pts, cls="c-blue"),
            poly_path(c2_pts, cls="c-green"),
            '    <line x1="145" y1="164" x2="315" y2="178" class="c-main" />',
            '    <line x1="128" y1="226" x2="296" y2="105" class="c-red" />',
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{px:.1f}" y2="{py:.1f}" class="c-main" />',
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{mx:.1f}" y2="{my:.1f}" class="c-dash" />',
            '    <line x1="138" y1="238" x2="332" y2="198" class="c-dash" />',
            '    <line x1="274" y1="36" x2="328" y2="212" class="c-amber" />',
            text_label(152, 148, "C"),
            text_label(224, 54, "c"),
            text_label(334, 202, "t"),
            labeled_point(mx, my, "M", dx=-4, dy=18, color="#1e3a8a"),
            labeled_point(302, 177, "T", dx=-4, dy=16),
            labeled_point(m_small[0], m_small[1], "m", dx=8, dy=2, color="#047857"),
            labeled_point(px, py, "P", dx=-16, dy=-4, color="#dc2626"),
            labeled_point(ax, ay, "A", dx=-4, dy=18),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_5",
        "FIG. 5 — Pedal curve construction and normal property",
    )


def generate_fig_6() -> str:
    ox, oy = 250.0, 212.0
    r_circ = 44.0
    mx, my = 176.0, 122.0
    msx, msy = 274.0, 68.0
    ax, ay = 263.0, 134.0
    m1x, m1y = 228.0, 174.0
    c_pts = [(164.0 + 0.015 * (t - 26) ** 2, 74.0 + 2.1 * t) for t in range(52)]
    c2_pts = [(222.0 + 2.4 * t, 88.0 - 24.0 * math.sin(t / 15.0)) for t in range(52)]
    body = "\n".join(
        [
            f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r_circ:.1f}" class="f-amber" stroke="#b45309" stroke-width="1.6" />',
            poly_path(c_pts, cls="c-blue"),
            poly_path(c2_pts, cls="c-green"),
            '    <line x1="112" y1="164" x2="328" y2="34" class="c-red" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{msx:.1f}" y2="{msy:.1f}" class="c-main" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{mx:.1f}" y2="{my:.1f}" class="c-main" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{ax:.1f}" y2="{ay:.1f}" class="c-dash" />',
            text_label(202, 82, "C"),
            text_label(348, 74, "c"),
            text_label(112, 156, "t"),
            text_label(154, 185, "T"),
            text_label(298, 212, "γ"),
            text_label(242, 186, "i_1"),
            labeled_point(ox, oy, "O", dx=-6, dy=18),
            labeled_point(m1x, m1y, "m_1", dx=-26, dy=6, color="#b45309"),
            labeled_point(ax, ay, "A", dx=8, dy=5),
            labeled_point(mx, my, "M", dx=-18, dy=-4, color="#1e3a8a"),
            labeled_point(msx, msy, "m", dx=-12, dy=-8, color="#047857"),
        ]
    )
    return figure_svg(
        "0 0 460 280",
        body,
        "fig_6",
        "FIG. 6 — Refraction tangent construction with auxiliary circle γ",
    )


def generate_fig_7() -> str:
    ox, oy = 215.0, 148.0
    c1_pts = [
        (ox - 75.0 + 3.2 * t, oy - 36.0 + 0.019 * (t - 24.0) ** 2) for t in range(52)
    ]
    c2_pts = [
        (ox - 28.0 + 0.018 * (t - 25.0) ** 2, oy - 85.0 + 3.4 * t) for t in range(52)
    ]
    body = "\n".join(
        [
            axes_2d(ox, oy, 85, 365, 255, 35, xlabel="x", ylabel="y", origin_label="O"),
            f'    <line x1="{ox - 82:.1f}" y1="{oy - 68:.1f}" x2="{ox + 88:.1f}" y2="{oy + 72:.1f}" class="c-dash" />',
            f'    <line x1="{ox - 82:.1f}" y1="{oy + 68:.1f}" x2="{ox + 88:.1f}" y2="{oy - 72:.1f}" class="c-dash" />',
            poly_path(c1_pts, cls="c-blue"),
            poly_path(c2_pts, cls="c-red"),
            text_label(302, 128, "C_1", color="#1e3a8a"),
            text_label(178, 68, "C_2", color="#dc2626"),
            text_label(256, 140, "+", italic=False),
            text_label(165, 162, "+", italic=False),
            text_label(226, 108, "−", italic=False),
            text_label(224, 196, "−", italic=False),
        ]
    )
    return figure_svg(
        "0 0 450 280",
        body,
        "fig_7",
        "FIG. 7 — Two intersecting branches C₁, C₂ and sign sectors at the origin",
    )


def generate_fig_8() -> str:
    ax, ay = 212.0, 246.0
    epx, epy = 178.0, 206.0
    cx, cy = 168.0, 148.0
    ex, ey = 218.0, 96.0
    bx, by = 298.0, 58.0
    arc_pts = [
        (
            298.0 - 130.0 * math.sin(1.42 * t / 40.0),
            58.0 + 188.0 * (t / 40.0) ** 1.15,
        )
        for t in range(41)
    ]
    body = "\n".join(
        [
            f'    <polygon points="{ax:.1f},{ay:.1f} {cx:.1f},{cy:.1f} {bx:.1f},{by:.1f}" class="f-blue" />',
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" class="c-main" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{bx:.1f}" y2="{by:.1f}" class="c-dash" />',
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{cx:.1f}" y2="{cy:.1f}" class="c-dash" />',
            '    <line x1="128" y1="168" x2="328" y2="42" class="c-red" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="195" y2="165" class="c-dash" />',
            f'    <line x1="{ex:.1f}" y1="{ey:.1f}" x2="236" y2="148" class="c-dash" />',
            poly_path(arc_pts, cls="c-blue"),
            text_label(122, 175, "T", color="#dc2626"),
            text_label(192, 178, "K"),
            text_label(228, 162, "H"),
            text_label(242, 114, "F"),
            labeled_point(ax, ay, "A", dx=-6, dy=16),
            labeled_point(epx, epy, "E'", dx=-24, dy=4),
            labeled_point(cx, cy, "C", dx=-18, dy=-2, color="#1e3a8a"),
            labeled_point(ex, ey, "E", dx=-14, dy=-6, color="#1e3a8a"),
            labeled_point(bx, by, "B", dx=8, dy=6, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 450 280",
        body,
        "fig_8",
        "FIG. 8 — Inscribed polygon and tangent bounds on a convex arc ACB",
    )


def generate_fig_9() -> str:
    oy = 225.0

    def f(x: float) -> float:
        return oy - (78.0 + 26.0 * math.sin((x - 70.0) / 38.0) + 0.16 * (x - 70.0))

    curve_pts = [(x, f(x)) for x in range(70, 394, 4)]
    rects = []
    for xL, xR, lbl_r in [
        (70, 96, "R_1"),
        (96, 122, "R_2"),
        (245, 276, "R_i"),
        (342, 368, ""),
        (368, 390, ""),
    ]:
        y_top = min(f(xL), f(xR))
        y_bot = max(f(xL), f(xR))
        rects.append(
            f'    <rect x="{xL}" y="{y_top:.1f}" width="{xR - xL}" height="{oy - y_top:.1f}" class="f-blue" stroke="#1e3a8a" stroke-width="1.1" />'
        )
        rects.append(
            f'    <line x1="{xL}" y1="{y_bot:.1f}" x2="{xR}" y2="{y_bot:.1f}" class="c-red-dash" />'
        )
        if lbl_r:
            rects.append(text_label((xL + xR) / 2 - 8, oy - 32, lbl_r))

    body = "\n".join(
        [
            f'    <line x1="42" y1="{oy:.1f}" x2="425" y2="{oy:.1f}" class="ax" marker-end="url(#arr)" />',
            text_label(430, oy + 5, "x"),
            *rects,
            poly_path(curve_pts, cls="c-blue"),
            labeled_point(70, f(70), "A", dx=-16, dy=4),
            labeled_point(96, f(96), "Q_1", dx=-10, dy=-8),
            labeled_point(122, f(122), "Q_2", dx=-6, dy=-8),
            labeled_point(185, f(185), "M", dx=-6, dy=18),
            labeled_point(245, f(245), "Q_{i-1}", dx=-26, dy=-8),
            labeled_point(276, f(276), "Q_i", dx=4, dy=-8),
            labeled_point(368, f(368), "Q_{n-1}", dx=-28, dy=-8),
            labeled_point(390, f(390), "B", dx=6, dy=-4),
            text_label(234, oy + 16, "P_{i-1}"),
            text_label(272, oy + 16, "P_i"),
            text_label(352, oy + 16, "P_{n-1}"),
            text_label(385, oy + 16, "B_0"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_9",
        "FIG. 9 — Darboux upper and lower rectangle sums for the definite integral",
    )


def generate_fig_10() -> str:
    ox, oy = 132.0, 172.0

    def f(x: float) -> float:
        return oy - 72.0 * math.sin((x - 95.0) / 68.0)

    pts = [(x, f(x)) for x in range(48, 396, 4)]
    fill_pos = [(95.0, oy)] + [(x, f(x)) for x in range(95, 309, 4)] + [(309.0, oy)]
    body = "\n".join(
        [
            poly_path(fill_pos, cls="f-blue", closed=True),
            axes_2d(ox, oy, 30, 422, 250, 26, xlabel="x", ylabel="y", origin_label="O"),
            poly_path(pts, cls="c-blue"),
            f'    <line x1="58" y1="{oy:.1f}" x2="58" y2="{f(58):.1f}" class="c-dash" />',
            f'    <line x1="168" y1="{oy:.1f}" x2="168" y2="{f(168):.1f}" class="c-dash" />',
            f'    <line x1="238" y1="{oy:.1f}" x2="238" y2="{f(238):.1f}" class="c-dash" />',
            f'    <line x1="256" y1="{oy:.1f}" x2="256" y2="{f(256):.1f}" class="c-dash" />',
            f'    <line x1="362" y1="{oy:.1f}" x2="362" y2="{f(362):.1f}" class="c-dash" />',
            labeled_point(58, f(58), "M''", dx=-10, dy=18),
            text_label(50, oy - 6, "P''"),
            text_label(84, oy + 16, "D"),
            labeled_point(168, f(168), "M_0", dx=-10, dy=-8, color="#1e3a8a"),
            text_label(162, oy + 16, "P_0"),
            labeled_point(238, f(238), "M", dx=-6, dy=-8, color="#1e3a8a"),
            labeled_point(256, f(256), "N", dx=6, dy=-4, color="#1e3a8a"),
            text_label(232, oy + 16, "P"),
            text_label(252, oy + 16, "Q"),
            text_label(306, oy - 6, "C"),
            text_label(356, oy - 6, "P'"),
            labeled_point(362, f(362), "M'", dx=-10, dy=18),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_10",
        "FIG. 10 — Signed area and abscissa increments along an oscillating curve",
    )


def generate_fig_11() -> str:
    ox, oy = 84.0, 226.0
    p1 = [(118 + t, 174 - 0.35 * t) for t in range(0, 78, 4)]
    p2 = [(196 + t, 172 + 0.22 * t + 0.002 * t * t) for t in range(0, 74, 4)]
    p3 = [(270 + t, 118 - 0.32 * t + 0.0012 * t * t) for t in range(0, 88, 4)]
    body = "\n".join(
        [
            axes_2d(ox, oy, 42, 415, 255, 25, xlabel="x", ylabel="y", origin_label=""),
            f'    <polygon points="118,{oy:.1f} 118,174 196,147 196,{oy:.1f}" class="f-blue" />',
            f'    <polygon points="196,{oy:.1f} 196,172 270,199 270,{oy:.1f}" class="f-amber" />',
            f'    <polygon points="270,{oy:.1f} 270,118 354,99 354,{oy:.1f}" class="f-green" />',
            f'    <line x1="118" y1="174" x2="118" y2="{oy:.1f}" class="c-main" />',
            f'    <line x1="196" y1="147" x2="196" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="270" y1="118" x2="270" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="354" y1="99" x2="354" y2="{oy:.1f}" class="c-main" />',
            poly_path(p1, cls="c-blue"),
            poly_path(p2, cls="c-amber"),
            poly_path(p3, cls="c-green"),
            labeled_point(118, 174, "A", dx=-16, dy=-2),
            labeled_point(196, 147, "C", dx=6, dy=-4, color="#1e3a8a"),
            labeled_point(196, 172, "C'", dx=-22, dy=6, color="#b45309"),
            labeled_point(270, 199, "D", dx=6, dy=4, color="#b45309"),
            labeled_point(270, 118, "D'", dx=-22, dy=-4, color="#047857"),
            labeled_point(354, 99, "B", dx=6, dy=-4, color="#047857"),
            text_label(110, oy + 18, "A_0"),
            text_label(346, oy + 18, "B_0"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_11",
        "FIG. 11 — Integration of a function with finite jump discontinuities",
    )


def generate_fig_12() -> str:
    c1 = [(115.0 + 38.0 * math.sin(t / 18.0), 82.0 + 3.2 * t) for t in range(52)]
    c2 = [
        (270.0 + 2.4 * t, 46.0 + 95.0 * (1.0 - math.exp(-t / 24.0))) for t in range(52)
    ]
    m1 = (151.0, 158.0)
    m2 = (312.0, 96.0)
    body = "\n".join(
        [
            poly_path(c1, cls="c-blue"),
            poly_path(c2, cls="c-blue"),
            f'    <line x1="{m1[0]:.1f}" y1="{m1[1]:.1f}" x2="{m2[0]:.1f}" y2="{m2[1]:.1f}" class="c-main" />',
            f'    <line x1="{m1[0] - 10:.1f}" y1="{m1[1] - 45:.1f}" x2="{m1[0] + 18:.1f}" y2="{m1[1] + 82:.1f}" class="c-red" />',
            f'    <line x1="{m2[0] - 32:.1f}" y1="{m2[1] - 34:.1f}" x2="{m2[0] + 68:.1f}" y2="{m2[1] + 72:.1f}" class="c-red" />',
            text_label(102, 108, "A_1"),
            text_label(106, 245, "C_1"),
            text_label(175, 242, "T_1", color="#dc2626"),
            text_label(165, 178, "θ_1"),
            text_label(226, 118, "l"),
            text_label(295, 52, "A"),
            text_label(392, 134, "C"),
            text_label(364, 184, "T", color="#dc2626"),
            text_label(312, 125, "θ"),
            labeled_point(m1[0], m1[1], "M_1", dx=6, dy=-8, color="#1e3a8a"),
            labeled_point(m2[0], m2[1], "M", dx=-20, dy=-4, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_12",
        "FIG. 12 — Differential of chord length l between two curves C₁ and C",
    )


def generate_fig_13() -> str:
    cx, cy = 225.0, 152.0
    mx, my = 258.0, 76.0
    bx, by = 148.0, 142.0
    ax, ay = 304.0, 146.0
    body = "\n".join(
        [
            f'    <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="148" ry="76" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />',
            f'    <ellipse cx="{cx - 6:.1f}" cy="{cy + 4:.1f}" rx="86" ry="42" class="f-amber" stroke="#b45309" stroke-width="1.75" />',
            f'    <line x1="{bx:.1f}" y1="{by:.1f}" x2="{mx:.1f}" y2="{my:.1f}" class="c-red" />',
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{mx:.1f}" y2="{my:.1f}" class="c-red" />',
            f'    <line x1="{mx - 72:.1f}" y1="{my - 4:.1f}" x2="{mx + 75:.1f}" y2="{my + 8:.1f}" class="c-green" />',
            text_label(192, 70, "T", color="#047857"),
            text_label(192, 104, "l'"),
            text_label(285, 108, "l"),
            text_label(224, 110, "N"),
            text_label(215, 188, "E"),
            text_label(294, 212, "E'"),
            text_label(276, 194, "O"),
            text_label(348, 128, "O'"),
            labeled_point(mx, my, "M", dx=-4, dy=-10, color="#1e3a8a"),
            labeled_point(bx, by, "B", dx=-16, dy=-4, color="#b45309"),
            labeled_point(ax, ay, "A", dx=8, dy=-2, color="#b45309"),
        ]
    )
    return figure_svg(
        "0 0 460 265",
        body,
        "fig_13",
        "FIG. 13 — Graves–Chasles string theorem for closed convex curve E and outer locus E'",
    )


def generate_fig_14() -> str:
    ox, oy = 96.0, 228.0
    s_pts = []
    for i in range(65):
        t = i / 64.0
        y = 192.0 - 148.0 * t
        x = 136.0 + 135.0 * t + 44.0 * math.sin(2.0 * math.pi * t)
        s_pts.append((x, y))
    ax, ay = s_pts[0]
    cx, cy = max(s_pts[:35], key=lambda p: p[0])
    dx, dy = min(s_pts[25:], key=lambda p: p[0])
    bx, by = s_pts[-1]
    body = "\n".join(
        [
            axes_2d(ox, oy, 55, 405, 256, 26, xlabel="x", ylabel="y", origin_label="O"),
            f'    <line x1="{dx:.1f}" y1="{dy:.1f}" x2="{dx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            poly_path(s_pts, cls="c-blue"),
            labeled_point(ax, ay, "A", dx=-16, dy=5, color="#1e3a8a"),
            labeled_point(cx, cy, "C", dx=8, dy=5, color="#dc2626"),
            labeled_point(dx, dy, "D", dx=-18, dy=4, color="#dc2626"),
            labeled_point(bx, by, "B", dx=8, dy=4, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_14",
        "FIG. 14 — Decomposition of curvilinear integral along arc ACDB at turning points C and D",
    )


def generate_fig_15() -> str:
    ox, oy = 82.0, 234.0
    cx, cy = 248.0, 136.0
    oval = []
    for i in range(73):
        ang = 2.0 * math.pi * i / 72.0
        x = cx + 92.0 * math.cos(ang) + 18.0 * math.sin(ang)
        y = cy - 68.0 * math.sin(ang) + 14.0 * math.cos(ang)
        oval.append((x, y))
    a_pt = min(oval, key=lambda p: p[0])
    b_pt = max(oval, key=lambda p: p[0])
    poly_pts = [oval[0], oval[12], oval[26], oval[38], oval[52], oval[64], oval[0]]
    body = "\n".join(
        [
            poly_path(oval, cls="f-blue", closed=True),
            axes_2d(ox, oy, 44, 415, 260, 24, xlabel="x", ylabel="y", origin_label="O"),
            f'    <line x1="{a_pt[0]:.1f}" y1="{a_pt[1]:.1f}" x2="{a_pt[0]:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{b_pt[0]:.1f}" y1="{b_pt[1]:.1f}" x2="{b_pt[0]:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{cx:.1f}" y1="{cy - 68:.1f}" x2="{cx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            poly_path(poly_pts, cls="c-amber"),
            poly_path(oval, cls="c-blue", closed=True),
            arrow_head(cx - 45, cy - 58, -28),
            arrow_head(cx + 52, cy + 52, 152),
            labeled_point(a_pt[0], a_pt[1], "A", dx=-16, dy=5),
            labeled_point(b_pt[0], b_pt[1], "B", dx=8, dy=5),
            labeled_point(cx, cy - 67, "m_2", dx=-22, dy=-8, color="#1e3a8a"),
            labeled_point(cx, cy + 67, "m_1", dx=6, dy=15, color="#1e3a8a"),
            text_label(178, 188, "M"),
            text_label(a_pt[0] - 4, oy + 16, "a"),
            text_label(b_pt[0] - 4, oy + 16, "b"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_15",
        "FIG. 15 — Green's theorem and line integral around a closed contour Am₁Bm₂",
    )


def generate_fig_16() -> str:
    pts = []
    for i in range(81):
        t = 2.0 * math.pi * i / 80.0
        r = 84.0 + 26.0 * math.cos(2.0 * t) + 14.0 * math.sin(3.0 * t)
        x = 235.0 + r * math.cos(t) * 0.95
        y = 142.0 - r * math.sin(t) * 0.88
        pts.append((x, y))
    body = "\n".join(
        [
            poly_path(pts, cls="f-blue", closed=True),
            poly_path(pts, cls="c-blue", closed=True),
            '    <line x1="176" y1="126" x2="246" y2="152" class="c-red" />',
            '    <line x1="168" y1="192" x2="275" y2="208" class="c-red" />',
            arrow_head(212, 134, 20, "#dc2626"),
            arrow_head(208, 144, -160, "#dc2626"),
            arrow_head(222, 195, 8, "#dc2626"),
            arrow_head(218, 205, -172, "#dc2626"),
            text_label(318, 76, "p"),
            text_label(312, 108, "C"),
            text_label(158, 124, "c"),
            text_label(254, 154, "d"),
            text_label(112, 152, "q"),
            text_label(148, 194, "a"),
            text_label(284, 214, "b"),
            text_label(282, 182, "n"),
            text_label(205, 245, "m"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_16",
        "FIG. 16 — Decomposition of a non-convex region by interior crosscuts cd and ab",
    )


def generate_fig_17() -> str:
    ox1, oy1 = 104.0, 208.0
    loop1 = [
        (
            ox1 + (135.0 * math.sin(t) + 35.0) * math.cos(0.9 * t - 0.3),
            oy1 - (135.0 * math.sin(t) + 35.0) * math.sin(0.9 * t - 0.3),
        )
        for t in [i * 0.05 for i in range(6, 56)]
    ]
    ox2, oy2 = 302.0, 224.0
    oval2 = [
        (356.0 + 36.0 * math.cos(t), 132.0 + 48.0 * math.sin(t))
        for t in [i * 0.1 for i in range(64)]
    ]
    body = "\n".join(
        [
            f'    <polygon points="{ox1:.1f},{oy1:.1f} 232,126 218,98" fill="url(#hatch)" stroke="#1e3a8a" stroke-width="1.2" />',
            poly_path(loop1, cls="c-blue-dash"),
            f'    <line x1="{ox1:.1f}" y1="{oy1:.1f}" x2="188" y2="82" class="c-main" />',
            f'    <line x1="{ox1:.1f}" y1="{oy1:.1f}" x2="218" y2="98" class="c-blue" />',
            f'    <line x1="{ox1:.1f}" y1="{oy1:.1f}" x2="232" y2="126" class="c-blue" />',
            f'    <line x1="{ox1:.1f}" y1="{oy1:.1f}" x2="225" y2="175" class="c-main" />',
            text_label(182, 74, "B"),
            text_label(222, 92, "M'"),
            text_label(238, 128, "M"),
            text_label(232, 182, "A"),
            poly_path(oval2, cls="f-amber", closed=True),
            poly_path(oval2, cls="c-amber", closed=True),
            f'    <line x1="{ox2:.1f}" y1="{oy2:.1f}" x2="342" y2="72" class="c-main" />',
            f'    <line x1="{ox2:.1f}" y1="{oy2:.1f}" x2="404" y2="112" class="c-main" />',
            text_label(308, 140, "B"),
            text_label(362, 80, "M"),
            text_label(396, 156, "A"),
            text_label(338, 192, "N"),
            labeled_point(ox1, oy1, "O", dx=-16, dy=14),
            labeled_point(ox2, oy2, "O", dx=-14, dy=15),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_17",
        "FIG. 17 — Polar area element ½ r² dθ and closed loop enclosed between extreme radii",
    )


def generate_fig_18() -> str:
    ox, oy = 112.0, 224.0
    ang = math.radians(64.0)
    ux, uy = math.cos(ang), -math.sin(ang)
    curve = [
        (175.0 + 2.2 * t, 172.0 - 1.1 * t - 12.0 * math.sin(t / 18.0))
        for t in range(72)
    ]
    strips = []
    for t_idx, lbl_b in [(0, "A_0"), (22, ""), (45, ""), (71, "B_0")]:
        px, py = curve[t_idx]
        s = (oy - py) / (-uy)
        bx = px - s * ux
        strips.append(
            f'    <line x1="{bx:.1f}" y1="{oy:.1f}" x2="{px:.1f}" y2="{py:.1f}" class="c-dash" />'
        )
        if lbl_b:
            strips.append(text_label(bx - 8, oy + 18, lbl_b))

    body = "\n".join(
        [
            f'    <polygon points="151,{oy:.1f} {curve[0][0]:.1f},{curve[0][1]:.1f} {curve[-1][0]:.1f},{curve[-1][1]:.1f} 252,{oy:.1f}" class="f-blue" />',
            f'    <line x1="65" y1="{oy:.1f}" x2="412" y2="{oy:.1f}" class="ax" marker-end="url(#arr)" />',
            f'    <line x1="{ox - 20 * ux:.1f}" y1="{oy - 20 * uy:.1f}" x2="{ox + 215 * ux:.1f}" y2="{oy + 215 * uy:.1f}" class="ax" marker-end="url(#arr)" />',
            *strips,
            poly_path(curve, cls="c-blue"),
            text_label(416, oy + 5, "x"),
            text_label(ox + 215 * ux - 18, oy + 215 * uy + 8, "y"),
            text_label(ox + 24, oy - 8, "θ"),
            labeled_point(ox, oy, "O", dx=-18, dy=16),
            labeled_point(
                curve[0][0], curve[0][1], "A", dx=-16, dy=-2, color="#1e3a8a"
            ),
            labeled_point(
                curve[22][0], curve[22][1], "M", dx=-12, dy=-8, color="#1e3a8a"
            ),
            labeled_point(
                curve[45][0], curve[45][1], "M'", dx=-14, dy=-8, color="#1e3a8a"
            ),
            labeled_point(curve[-1][0], curve[-1][1], "B", dx=8, dy=2, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_18",
        "FIG. 18 — Area under a curve referred to oblique axes Ox, Oy of angle θ",
    )


def generate_fig_19() -> str:
    lem = []
    for i in range(81):
        t = 2.0 * math.pi * i / 80.0
        d = 1.0 + math.sin(t) ** 2
        x = 108.0 + 68.0 * math.cos(t) / d
        y = 148.0 - 56.0 * math.sin(t) * math.cos(t) / d - 0.35 * (x - 108.0)
        lem.append((x, y))
    loop2 = []
    for i in range(101):
        t = 2.0 * math.pi * i / 100.0
        x = 315.0 + 78.0 * math.cos(t) + 32.0 * math.cos(2.0 * t)
        y = 142.0 - 64.0 * math.sin(t) + 28.0 * math.sin(2.0 * t)
        loop2.append((x, y))
    body = "\n".join(
        [
            poly_path(lem, cls="f-blue", closed=True),
            poly_path(lem, cls="c-blue", closed=True),
            labeled_point(108, 148, "O", dx=-4, dy=18),
            text_label(30, 178, "B"),
            text_label(168, 96, "A"),
            poly_path(loop2, cls="f-amber", closed=True),
            poly_path(loop2, cls="c-amber", closed=True),
            '    <ellipse cx="295" cy="142" rx="48" ry="68" class="c-blue" />',
            text_label(242, 95, "t"),
            text_label(316, 72, "B"),
            text_label(398, 108, "p"),
            text_label(285, 132, "q"),
            text_label(332, 132, "s"),
            text_label(235, 168, "C"),
            text_label(284, 174, "u"),
            text_label(325, 178, "A"),
            text_label(266, 224, "r"),
        ]
    )
    return figure_svg(
        "0 0 460 265",
        body,
        "fig_19",
        "FIG. 19 — Signed area of self-intersecting loops and figure-eight contours",
    )


def generate_fig_20() -> str:
    c1 = [
        (118 + 26 * math.cos(t), 192 - 38 * math.sin(t))
        for t in [i * 0.1 for i in range(64)]
    ]
    c2 = [
        (236 + 18 * math.cos(t), 132 - 32 * math.sin(t))
        for t in [i * 0.1 for i in range(64)]
    ]
    c3 = [
        (348 + 32 * math.cos(t), 74 - 42 * math.sin(t))
        for t in [i * 0.1 for i in range(64)]
    ]
    body = "\n".join(
        [
            poly_path(c1, cls="f-blue", closed=True),
            poly_path(c1, cls="c-blue", closed=True),
            poly_path(c2, cls="f-amber", closed=True),
            poly_path(c2, cls="c-amber", closed=True),
            poly_path(c3, cls="f-green", closed=True),
            poly_path(c3, cls="c-green", closed=True),
            '    <line x1="78" y1="224" x2="395" y2="54" class="c-main" />',
            '    <line x1="74" y1="212" x2="392" y2="38" class="c-red-dash" />',
            '    <line x1="178" y1="84" x2="232" y2="136" class="c-main" />',
            labeled_point(178, 84, "O", dx=-14, dy=-6),
            text_label(92, 152, "C_1"),
            text_label(128, 224, "A_1"),
            text_label(124, 182, "A_1'"),
            text_label(236, 166, "A_2"),
            text_label(244, 128, "A_2'"),
            text_label(316, 42, "C_3"),
            text_label(382, 82, "A_3"),
            text_label(386, 46, "A_3'"),
        ]
    )
    return figure_svg(
        "0 0 460 265",
        body,
        "fig_20",
        "FIG. 20 — Areas swept by a moving line intersecting three closed curves C₁, C₂, C₃",
    )


def generate_fig_21() -> str:
    ox, oy = 210.0, 142.0
    hyp = []
    for i in range(-32, 33):
        t = i * 0.042
        x = ox + 58.0 * math.cosh(t)
        y = oy - 58.0 * math.sinh(t)
        hyp.append((x, y))
    mx, my = ox + 58.0 * math.cosh(0.78), oy - 58.0 * math.sinh(0.78)
    sector = (
        [(ox, oy)]
        + [p for p in hyp if p[1] <= oy and p[0] <= mx]
        + [(mx, my), (ox, oy)]
    )
    body = "\n".join(
        [
            poly_path(sector, cls="f-blue", closed=True),
            axes_2d(ox, oy, 48, 418, 258, 24, xlabel="x", ylabel="y", origin_label="O"),
            f'    <line x1="{ox - 115:.1f}" y1="{oy + 115:.1f}" x2="{ox + 122:.1f}" y2="{oy - 122:.1f}" class="c-dash" />',
            f'    <line x1="{ox - 115:.1f}" y1="{oy - 115:.1f}" x2="{ox + 122:.1f}" y2="{oy + 122:.1f}" class="c-dash" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{mx:.1f}" y2="{my:.1f}" class="c-red" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            poly_path(hyp, cls="c-blue"),
            labeled_point(ox + 58, oy, "A", dx=-15, dy=16, color="#1e3a8a"),
            labeled_point(mx, oy, "P", dx=-4, dy=16),
            labeled_point(mx, my, "M", dx=8, dy=4, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 460 280",
        body,
        "fig_21",
        "FIG. 21 — Equilateral hyperbola x² − y² = a² and hyperbolic sector OAM",
    )


def generate_fig_22() -> str:
    ox, oy = 135.0, 226.0
    p1 = [(ox + t, oy - 0.016 * t * t) for t in range(-88, 118, 4)]
    cat = [(ox + t, oy - 36.0 * math.cosh(t / 72.0)) for t in range(0, 185, 4)]
    p2 = [(232.0 + t, oy - 12.0 - 0.015 * (t - 22.0) ** 2) for t in range(-52, 112, 4)]
    body = "\n".join(
        [
            axes_2d(ox, oy, 45, 418, 255, 25, xlabel="x", ylabel="y", origin_label="O"),
            poly_path(p1, cls="c-blue"),
            poly_path(p2, cls="c-amber"),
            poly_path(cat, cls="c-red"),
            '    <line x1="176" y1="226" x2="345" y2="112" class="c-dash" />',
            '    <line x1="225" y1="185" x2="225" y2="226" class="c-dash" />',
            labeled_point(ox, oy - 36, "F", dx=6, dy=-4, color="#dc2626"),
            labeled_point(225, 185, "F'", dx=8, dy=4, color="#dc2626"),
            labeled_point(225, 168, "M", dx=6, dy=-6, color="#1e3a8a"),
            text_label(172, oy + 16, "T"),
            text_label(220, oy + 16, "T'"),
            text_label(312, oy + 16, "M'"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_22",
        "FIG. 22 — Locus of the focus F' of a parabola rolling without slipping on Ox (catenary)",
    )


def generate_fig_23() -> str:
    ox, oy = 112.0, 228.0
    grid_lines = []
    for gx in range(148, 336, 16):
        grid_lines.append(
            f'    <line x1="{gx}" y1="48" x2="{gx}" y2="208" stroke="#94a3b8" stroke-width="0.9" />'
        )
    for gy in range(48, 212, 16):
        grid_lines.append(
            f'    <line x1="148" y1="{gy}" x2="324" y2="{gy}" stroke="#94a3b8" stroke-width="0.9" />'
        )
    oval = []
    for i in range(65):
        t = 2.0 * math.pi * i / 64.0
        u = 68.0 * math.cos(t)
        v = 42.0 * math.sin(t)
        ang = math.radians(-38.0)
        x = 236.0 + u * math.cos(ang) - v * math.sin(ang)
        y = 128.0 + u * math.sin(ang) + v * math.cos(ang)
        oval.append((x, y))
    body = "\n".join(
        [
            poly_path(oval, cls="f-blue", closed=True),
            *grid_lines,
            poly_path(oval, cls="c-blue", closed=True),
            axes_2d(ox, oy, 55, 395, 256, 24, xlabel="x", ylabel="y", origin_label="O"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_23",
        "FIG. 23 — Double integral over a plane region partitioned by a regular grid of squares",
    )


def generate_fig_24() -> str:
    ox, oy = 84.0, 224.0
    xs = [142, 162, 182, 268, 294, 344, 368]
    ys = [192, 174, 156, 114, 92, 68]
    vlines = [
        f'    <line x1="{x}" y1="68" x2="{x}" y2="{oy:.1f}" stroke="#64748b" stroke-width="1.0" />'
        for x in xs
    ]
    hlines = [
        f'    <line x1="{ox:.1f}" y1="{y}" x2="368" y2="{y}" stroke="#64748b" stroke-width="1.0" />'
        for y in ys
    ]
    body = "\n".join(
        [
            '    <rect x="142" y="68" width="226" height="124" class="f-blue" />',
            '    <rect x="268" y="92" width="26" height="22" fill="url(#hatch)" stroke="#1e3a8a" stroke-width="1.5" />',
            *vlines,
            *hlines,
            '    <rect x="142" y="68" width="226" height="124" class="c-blue" />',
            axes_2d(ox, oy, 45, 420, 255, 24, xlabel="x", ylabel="y", origin_label="O"),
            text_label(126, 198, "A"),
            text_label(374, 196, "B"),
            text_label(374, 72, "C"),
            text_label(144, 62, "D"),
            text_label(64, 195, "y_0"),
            text_label(64, 177, "y_1"),
            text_label(64, 159, "y_2"),
            text_label(52, 118, "y_{k-1}"),
            text_label(64, 96, "y_k"),
            text_label(66, 72, "Y"),
            text_label(135, oy + 16, "x_0"),
            text_label(156, oy + 16, "x_1"),
            text_label(176, oy + 16, "x_2"),
            text_label(254, oy + 16, "x_{i-1}"),
            text_label(288, oy + 16, "x_i"),
            text_label(328, oy + 16, "x_{n-1}"),
            text_label(364, oy + 16, "X"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_24",
        "FIG. 24 — Double integral over rectangle ABCD partitioned into subrectangles",
    )


def generate_fig_25() -> str:
    ox, oy = 68.0, 228.0

    def y_top(x: float) -> float:
        return 72.0 + 0.0012 * (x - 295.0) ** 2

    def y_bot(x: float) -> float:
        return 192.0 - 0.0011 * (x - 225.0) ** 2

    x0, x1 = 112.0, 356.0
    top_pts = [(x, y_top(x)) for x in range(int(x0), int(x1) + 1, 4)]
    bot_pts = [(x, y_bot(x)) for x in range(int(x1), int(x0) - 1, -4)]
    region_pts = top_pts + bot_pts
    xi0, xi1 = 264.0, 286.0
    body = "\n".join(
        [
            poly_path(region_pts, cls="f-blue", closed=True),
            f'    <rect x="{xi0:.1f}" y="{y_top(xi0):.1f}" width="{xi1 - xi0:.1f}" height="{y_bot(xi0) - y_top(xi0):.1f}" class="f-amber" stroke="#b45309" stroke-width="1.1" />',
            f'    <rect x="{xi0:.1f}" y="122" width="{xi1 - xi0:.1f}" height="18" fill="url(#hatch)" stroke="#1e3a8a" stroke-width="1.4" />',
            f'    <line x1="{x0:.1f}" y1="{y_top(x0):.1f}" x2="{x0:.1f}" y2="{oy:.1f}" class="c-main" />',
            f'    <line x1="{x1:.1f}" y1="{y_top(x1):.1f}" x2="{x1:.1f}" y2="{oy:.1f}" class="c-main" />',
            f'    <line x1="{xi0:.1f}" y1="{y_top(xi0):.1f}" x2="{xi0:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{xi1:.1f}" y1="{y_top(xi1):.1f}" x2="{xi1:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{ox:.1f}" y1="122" x2="{x1:.1f}" y2="122" class="c-dash" />',
            f'    <line x1="{ox:.1f}" y1="140" x2="{x1:.1f}" y2="140" class="c-dash" />',
            poly_path(top_pts, cls="c-blue"),
            poly_path(list(reversed(bot_pts)), cls="c-blue"),
            axes_2d(ox, oy, 38, 422, 255, 24, xlabel="x", ylabel="y", origin_label="O"),
            text_label(92, y_top(x0) + 6, "A'"),
            text_label(94, y_bot(x0) + 4, "A"),
            text_label(208, y_top(208) - 8, "Q"),
            text_label(214, y_bot(214) + 16, "P"),
            text_label(362, y_top(x1) + 4, "B'"),
            text_label(362, y_bot(x1) + 4, "B"),
            text_label(x0 - 6, oy + 16, "x_0"),
            text_label(xi0 - 16, oy + 16, "x_{i-1}"),
            text_label(xi1 - 2, oy + 16, "x_i"),
            text_label(x1 - 4, oy + 16, "X"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_25",
        "FIG. 25 — Reduction of a double integral over region AA'B'B to iterated single integrals",
    )


def generate_fig_26() -> str:
    oval1 = [
        (138 + 56 * math.cos(t), 138 - 76 * math.sin(t))
        for t in [i * 0.1 for i in range(64)]
    ]
    split1 = [
        (82 + t, 152 - 0.12 * t - 12 * math.sin(t / 35.0)) for t in range(0, 113, 4)
    ]
    cres = []
    for i in range(65):
        t = 2.0 * math.pi * i / 64.0
        x = 336 + 54 * math.cos(t) + 14 * math.cos(2 * t)
        y = 142 - 58 * math.sin(t)
        cres.append((x, y))
    body = "\n".join(
        [
            poly_path(oval1, cls="f-blue", closed=True),
            poly_path(oval1, cls="c-blue", closed=True),
            poly_path(split1, cls="c-red"),
            text_label(72, 92, "p_1"),
            text_label(56, 156, "m_1"),
            text_label(198, 136, "n"),
            text_label(168, 212, "q_1"),
            text_label(132, 108, "a_1"),
            text_label(135, 178, "a_1'"),
            poly_path(cres, cls="f-amber", closed=True),
            poly_path(cres, cls="c-amber", closed=True),
            '    <path d="M 304 185 Q 325 112 372 95" class="c-blue" />',
            '    <path d="M 304 185 Q 258 122 288 94 Q 326 82 372 95" class="c-red-dash" />',
            text_label(266, 98, "q"),
            text_label(298, 134, "a'"),
            text_label(332, 118, "r"),
            text_label(362, 126, "a"),
            text_label(358, 78, "p"),
            text_label(398, 146, "n"),
            text_label(298, 202, "m"),
        ]
    )
    return figure_svg(
        "0 0 460 265",
        body,
        "fig_26",
        "FIG. 26 — Orientation of boundary curves across adjacent regions a₁, a₁' and folded domains",
    )


def generate_fig_27() -> str:
    oval = []
    for i in range(65):
        t = 2.0 * math.pi * i / 64.0
        u = 98.0 * math.cos(t)
        v = 58.0 * math.sin(t)
        ang = math.radians(-32.0)
        x = 225.0 + u * math.cos(ang) - v * math.sin(ang)
        y = 136.0 + u * math.sin(ang) + v * math.cos(ang)
        oval.append((x, y))
    u_lines = []
    for k in range(-4, 5):
        pts = [
            (118 + s + k * 14, 198 - 0.72 * s + k * 8 + 8 * math.sin(s / 45.0))
            for s in range(0, 175, 8)
        ]
        u_lines.append(
            poly_path(pts, cls="c-sub-blue" if k not in (0, 1) else "c-blue")
        )
    v_lines = []
    for k in range(-4, 5):
        pts = [
            (152 + s + k * 16, 68 + 0.68 * s - k * 10 + 6 * math.cos(s / 42.0))
            for s in range(0, 145, 8)
        ]
        v_lines.append(poly_path(pts, cls="c-sub-red" if k not in (0, 1) else "c-red"))
    body = "\n".join(
        [
            poly_path(oval, cls="f-blue", closed=True),
            *u_lines,
            *v_lines,
            '    <polygon points="218,142 232,132 242,141 228,151" fill="#0f172a" opacity="0.78" />',
            poly_path(oval, cls="c-main", closed=True),
            text_label(302, 194, "(u+du)", color="#1e3a8a"),
            text_label(292, 208, "(u)", color="#1e3a8a"),
            text_label(242, 238, "(v=b)", color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_27",
        "FIG. 27 — Curvilinear coordinate net (u, v) and infinitesimal area element ∂(x,y)/∂(u,v) du dv",
    )


def generate_fig_28() -> str:
    body = "\n".join(
        [
            '    <rect x="44" y="54" width="142" height="152" fill="url(#hatch)" stroke="#1e3a8a" stroke-width="1.2" />',
            '    <line x1="26" y1="206" x2="205" y2="206" class="ax" marker-end="url(#arr)" />',
            '    <line x1="44" y1="224" x2="44" y2="42" class="ax" marker-end="url(#arr)" />',
            text_label(208, 210, "x"),
            text_label(30, 48, "y"),
            text_label(30, 220, "O"),
            text_label(82, 220, "F"),
            '    <rect x="296" y="138" width="128" height="68" fill="url(#hatch-amber)" stroke="#b45309" stroke-width="1.3" />',
            '    <line x1="228" y1="206" x2="436" y2="206" class="ax" marker-end="url(#arr)" />',
            '    <line x1="252" y1="224" x2="252" y2="42" class="ax" marker-end="url(#arr)" />',
            '    <line x1="234" y1="138" x2="428" y2="138" class="c-main" />',
            '    <line x1="296" y1="54" x2="296" y2="206" class="c-main" />',
            text_label(438, 210, "λ"),
            text_label(236, 48, "μ"),
            text_label(238, 220, "O"),
            text_label(272, 220, "c²", italic=False),
            text_label(292, 222, "A"),
            text_label(300, 132, "B"),
        ]
    )
    return figure_svg(
        "0 0 460 260",
        body,
        "fig_28",
        "FIG. 28 — Mapping between the (x, y) plane and the (λ, μ) strip",
    )


def generate_fig_29() -> str:
    ox, oy = 74.0, 226.0
    body = "\n".join(
        [
            axes_2d(ox, oy, 42, 425, 252, 26, xlabel="x", ylabel="y", origin_label="O"),
            '    <line x1="74" y1="138" x2="405" y2="138" class="c-main" />',
            '    <line x1="74" y1="186" x2="405" y2="186" class="c-main" />',
            '    <line x1="74" y1="162" x2="365" y2="162" class="c-dash" />',
            '    <ellipse cx="148" cy="162" rx="34" ry="24" class="f-blue" stroke="#1e3a8a" stroke-width="1.7" />',
            '    <ellipse cx="328" cy="162" rx="34" ry="24" class="f-amber" stroke="#b45309" stroke-width="1.7" />',
            '    <circle cx="328" cy="96" r="36" class="f-green" stroke="#047857" stroke-width="1.7" />',
            '    <line x1="292" y1="78" x2="292" y2="226" class="c-dash" />',
            '    <line x1="364" y1="78" x2="364" y2="226" class="c-dash" />',
            labeled_point(148, 152, "m", dx=-6, dy=-6),
            text_label(118, 174, "m_0"),
            text_label(164, 174, "m_1"),
            text_label(142, 184, "C"),
            labeled_point(328, 152, "m'", dx=6, dy=-2),
            text_label(298, 174, "m_0'"),
            text_label(366, 174, "m_1'"),
            text_label(338, 184, "C'"),
            labeled_point(328, 88, "M_1", dx=6, dy=4, color="#047857"),
            text_label(348, 60, "C_1"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_29",
        "FIG. 29 — Contours C, C' inside a strip and lifted loop C₁",
    )


def generate_fig_30() -> str:
    ox, oy = 178.0, 174.0
    body = "\n".join(
        [
            axes_3d(ox, oy),
            '    <path d="M 212 86 A 64 28 0 1 1 340 86 L 340 202 A 64 32 0 1 1 212 202 Z" class="f-blue" />',
            '    <ellipse cx="276" cy="86" rx="64" ry="28" class="f-amber" stroke="#1e3a8a" stroke-width="1.85" />',
            '    <ellipse cx="276" cy="202" rx="64" ry="32" fill="none" stroke="#0f172a" stroke-width="1.65" />',
            '    <line x1="212" y1="86" x2="212" y2="202" class="c-main" />',
            '    <line x1="340" y1="86" x2="340" y2="202" class="c-main" />',
            '    <line x1="306" y1="111" x2="306" y2="230" class="c-red" />',
            text_label(268, 88, "S"),
            text_label(346, 102, "Γ"),
            text_label(224, 244, "C"),
            labeled_point(306, 111, "M", dx=-14, dy=-8, color="#dc2626"),
            labeled_point(306, 230, "m", dx=6, dy=12, color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 460 280",
        body,
        "fig_30",
        "FIG. 30 — Cylindrical surface over planar contour C capped by space curve Γ and surface S",
    )


def generate_fig_31() -> str:
    body = "\n".join(
        [
            '    <line x1="188" y1="184" x2="112" y2="254" class="ax" marker-end="url(#arr)" />',
            '    <line x1="188" y1="184" x2="342" y2="184" class="ax" marker-end="url(#arr)" />',
            '    <line x1="188" y1="184" x2="188" y2="32" class="ax" marker-end="url(#arr)" />',
            text_label(98, 260, "y"),
            text_label(172, 40, "z"),
            '    <path d="M 188 72 A 112 112 0 0 1 300 184 Q 222 246 138 228 Q 132 132 188 72 Z" fill="url(#grad-sphere)" stroke="#1e3a8a" stroke-width="1.85" />',
            '    <path d="M 188 72 Q 236 124 238 214" class="c-red-dash" />',
            '    <path d="M 188 184 Q 252 178 300 184 Q 252 228 188 184" class="f-amber" stroke="#b45309" stroke-width="1.6" />',
            '    <line x1="188" y1="184" x2="246" y2="210" class="c-main" />',
            text_label(224, 148, "Γ", color="#dc2626"),
            text_label(208, 198, "ω"),
            text_label(188, 224, "C"),
            labeled_point(188, 184, "O", dx=-16, dy=-2),
            labeled_point(300, 184, "A", dx=6, dy=-4),
            labeled_point(246, 210, "M", dx=6, dy=6, color="#b45309"),
        ]
    )
    return figure_svg(
        "0 0 450 280",
        body,
        "fig_31",
        "FIG. 31 — Spherical octant and Viviani surface bounded by space curve Γ over contour C",
    )


def generate_fig_32() -> str:
    ox, oy = 178.0, 174.0
    body = "\n".join(
        [
            axes_3d(
                ox,
                oy,
                x_vec=(-56, 86),
                y_vec=(195, 0),
                z_vec=(0, -142),
                labels=("y", "x", "z"),
            ),
            '    <ellipse cx="268" cy="102" rx="64" ry="26" transform="rotate(-22 268 102)" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />',
            '    <path d="M 208 124 Q 262 64 328 80" class="c-red" />',
            '    <path d="M 208 124 Q 274 142 328 80" class="c-blue" />',
            '    <ellipse cx="258" cy="214" rx="48" ry="22" transform="rotate(-22 258 214)" class="f-amber" stroke="#b45309" stroke-width="1.6" />',
            '    <line x1="234" y1="174" x2="196" y2="248" class="c-dash" />',
            '    <line x1="322" y1="174" x2="284" y2="248" class="c-dash" />',
            '    <line x1="274" y1="68" x2="274" y2="232" class="c-dash" />',
            text_label(246, 68, "Σ_2", color="#dc2626"),
            text_label(298, 128, "Σ_1", color="#1e3a8a"),
            text_label(282, 98, "Γ"),
            text_label(254, 218, "A"),
            text_label(276, 248, "C"),
            text_label(226, 170, "x_1"),
            text_label(316, 170, "x_2"),
            text_label(266, 192, "y_1"),
            text_label(244, 256, "y_2"),
        ]
    )
    return figure_svg(
        "0 0 450 280",
        body,
        "fig_32",
        "FIG. 32 — Triple integral over spatial domain bounded by lower surface Σ₁ and upper surface Σ₂",
    )


def generate_fig_33() -> str:
    ox, oy = 168.0, 186.0
    body = "\n".join(
        [
            axes_3d(
                ox,
                oy,
                x_vec=(-68, 72),
                y_vec=(185, 0),
                z_vec=(0, -152),
                labels=("y", "x", "z"),
            ),
            '    <ellipse cx="248" cy="64" rx="34" ry="22" transform="rotate(-18 248 64)" class="f-amber" stroke="#b45309" stroke-width="1.7" />',
            '    <ellipse cx="248" cy="136" rx="32" ry="20" transform="rotate(-24 248 136)" class="f-blue" stroke="#1e3a8a" stroke-width="1.7" />',
            '    <ellipse cx="248" cy="226" rx="34" ry="18" class="f-green" stroke="#047857" stroke-width="1.7" />',
            '    <line x1="248" y1="36" x2="248" y2="226" class="c-main" />',
            labeled_point(248, 44, "m_2'", dx=6, dy=12, color="#b45309"),
            labeled_point(248, 84, "m_1'", dx=6, dy=-4, color="#b45309"),
            labeled_point(248, 118, "m_2", dx=6, dy=12, color="#1e3a8a"),
            labeled_point(248, 154, "m_1", dx=-24, dy=-4, color="#1e3a8a"),
            labeled_point(248, 226, "m", dx=6, dy=4, color="#047857"),
            text_label(234, 238, "A"),
            text_label(284, 244, "C"),
        ]
    )
    return figure_svg(
        "0 0 450 280",
        body,
        "fig_33",
        "FIG. 33 — Change of variables in triple integrals: vertical fibers piercing (E) and (E')",
    )


def generate_fig_34() -> str:
    ox, oy = 148.0, 192.0
    body = "\n".join(
        [
            axes_3d(
                ox,
                oy,
                x_vec=(-64, 76),
                y_vec=(215, 0),
                z_vec=(0, -150),
                labels=("x", "y", "z"),
            ),
            '    <polygon points="242,84 278,66 306,82 308,112 268,136 242,112" class="f-blue" stroke="#1e3a8a" stroke-width="1.75" />',
            '    <line x1="242" y1="84" x2="268" y2="102" class="c-blue" />',
            '    <line x1="268" y1="102" x2="306" y2="82" class="c-blue" />',
            '    <line x1="268" y1="102" x2="268" y2="136" class="c-blue" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="242" y2="112" class="c-dash" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="268" y2="136" class="c-dash" />',
            '    <line x1="148" y1="116" x2="242" y2="112" class="c-dash" />',
            text_label(254, 86, "dρ"),
            text_label(176, 114, "dφ"),
            text_label(188, 168, "dθ"),
        ]
    )
    return figure_svg(
        "0 0 450 280",
        body,
        "fig_34",
        "FIG. 34 — Volume element ρ² sin φ dρ dφ dθ in spherical coordinates",
    )


def generate_fig_35() -> str:
    body = "\n".join(
        [
            '    <ellipse cx="235" cy="142" rx="126" ry="72" transform="rotate(-14 235 142)" class="f-blue" stroke="#1e3a8a" stroke-width="1.9" />',
            '    <circle cx="174" cy="134" r="22" fill="#ffffff" stroke="#dc2626" stroke-width="1.75" />',
            '    <circle cx="246" cy="162" r="20" fill="#ffffff" stroke="#047857" stroke-width="1.75" />',
            '    <line x1="116" y1="126" x2="152" y2="132" class="c-red" />',
            '    <line x1="266" y1="164" x2="328" y2="168" class="c-green" />',
            text_label(352, 92, "m"),
            text_label(358, 146, "C"),
            text_label(202, 226, "p"),
            text_label(182, 108, "C''", color="#dc2626"),
            text_label(168, 138, "d"),
            text_label(124, 120, "c"),
            text_label(202, 138, "n"),
            text_label(248, 136, "C'", color="#047857"),
            text_label(216, 164, "r"),
            text_label(218, 184, "q"),
            text_label(266, 182, "a"),
            text_label(316, 184, "b"),
        ]
    )
    return figure_svg(
        "0 0 460 265",
        body,
        "fig_35",
        "FIG. 35 — Multiply connected domain with interior holes C', C'' rendered simply connected by crosscuts",
    )


def generate_fig_36() -> str:
    cx, cy = 236.0, 140.0
    loop_b = [
        (168 + 42 * math.cos(t), 108 - 32 * math.sin(t))
        for t in [i * 0.1 for i in range(64)]
    ]
    loop_c = [
        (182 + 44 * math.cos(t), 178 - 30 * math.sin(t))
        for t in [i * 0.1 for i in range(64)]
    ]
    body = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="112" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />',
            poly_path(loop_b, cls="f-amber", closed=True),
            poly_path(loop_b, cls="c-amber", closed=True),
            poly_path(loop_c, cls="f-green", closed=True),
            poly_path(loop_c, cls="c-green", closed=True),
            '    <path d="M 210 144 Q 248 98 278 96 Q 282 140 210 144" fill="none" stroke="#dc2626" stroke-width="1.75" />',
            '    <line x1="210" y1="144" x2="348" y2="144" class="c-main" />',
            '    <line x1="210" y1="150" x2="348" y2="150" class="c-dash" />',
            labeled_point(174, 108, "b", dx=6, dy=4, color="#b45309"),
            labeled_point(184, 178, "c", dx=6, dy=4, color="#047857"),
            labeled_point(210, 144, "M_0", dx=-14, dy=18),
            labeled_point(282, 144, "a", dx=6, dy=-6),
            text_label(324, 56, "C"),
            text_label(268, 88, "M"),
            text_label(112, 92, "β"),
            text_label(124, 212, "γ"),
            text_label(168, 136, "d"),
            text_label(218, 120, "e"),
            text_label(236, 198, "f"),
            text_label(324, 138, "m'"),
            text_label(324, 164, "m"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_36",
        "FIG. 36 — Double-loop contour around branch points a, b, c inside circle C",
    )


def generate_fig_37_a() -> str:
    env = [
        (258 - 115 * math.sin(1.4 * t / 45.0), 34 + 205 * (t / 45.0)) for t in range(46)
    ]
    c1 = [(118 + 3.4 * t, 195 - 2.6 * t + 0.015 * t * t) for t in range(52)]
    c2 = [(146 + 3.6 * t, 145 - 1.2 * t + 0.014 * (t - 22) ** 2) for t in range(52)]
    body = "\n".join(
        [
            poly_path(c1, cls="c-amber"),
            poly_path(c2, cls="c-green"),
            poly_path(env, cls="c-blue"),
            text_label(224, 42, "E", color="#1e3a8a"),
            text_label(198, 238, "C", color="#1e3a8a"),
            text_label(318, 66, "C'", color="#047857"),
            labeled_point(146, 128, "M", dx=-18, dy=4, color="#1e3a8a"),
            labeled_point(184, 78, "M'", dx=-22, dy=-2, color="#1e3a8a"),
            labeled_point(188, 108, "N", dx=6, dy=-4, color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 450 270",
        body,
        "fig_37_a",
        "FIG. 37, a — Envelope E touched by neighboring curves of a one-parameter family and their intersection N",
    )


def generate_fig_37_b() -> str:
    loc = [(115 + 4.2 * t, 124 + 0.35 * t + 0.008 * t * t) for t in range(55)]
    loop1 = []
    loop2 = []
    for i in range(61):
        u = (i - 30) / 14.0
        x1 = 212 + 24 * (u * u - 1.0)
        y1 = 144 + 28 * (u * u * u - u)
        loop1.append((x1, y1))
        x2 = 248 + 24 * (u * u - 1.0) + 12 * u
        y2 = 152 + 28 * (u * u * u - u) - 8 * u
        loop2.append((x2, y2))
    body = "\n".join(
        [
            poly_path(loc, cls="c-main"),
            poly_path(loop1, cls="c-blue"),
            poly_path(loop2, cls="c-red-dash"),
            text_label(178, 86, "C", color="#1e3a8a"),
            text_label(298, 118, "C'", color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 450 260",
        body,
        "fig_37_b",
        "FIG. 37, b — Locus of nodal double points for a family of self-intersecting curves C, C'",
    )


def generate_fig_38() -> str:
    ox, oy = 230.0, 140.0
    r = 108.0
    ast = []
    for i in range(121):
        t = 2.0 * math.pi * i / 120.0
        x = ox + r * (math.cos(t) ** 3)
        y = oy - r * (math.sin(t) ** 3)
        ast.append((x, y))
    t0 = math.radians(38.0)
    mx = ox + r * (math.cos(t0) ** 3)
    my = oy - r * (math.sin(t0) ** 3)
    ax = ox + r * math.cos(t0)
    by = oy - r * math.sin(t0)
    body = "\n".join(
        [
            poly_path(ast, cls="f-blue", closed=True),
            axes_2d(ox, oy, 75, 385, 262, 18, xlabel="x", ylabel="y", origin_label="O"),
            f'    <rect x="{ox:.1f}" y="{by:.1f}" width="{ax - ox:.1f}" height="{oy - by:.1f}" fill="none" stroke="#64748b" stroke-width="1.15" />',
            f'    <line x1="{ox:.1f}" y1="{by:.1f}" x2="{ax:.1f}" y2="{oy:.1f}" class="c-red" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{ax:.1f}" y2="{by:.1f}" class="c-dash" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{ox:.1f}" y2="{my:.1f}" class="c-dash" />',
            poly_path(ast, cls="c-blue", closed=True),
            text_label(ox + r + 4, oy + 16, "C"),
            text_label(ox - r - 18, oy + 16, "C'"),
            text_label(ox + 6, oy - r - 2, "D"),
            text_label(ox + 6, oy + r + 12, "D'"),
            text_label(ox - 16, by + 4, "B"),
            text_label(ax - 6, oy + 16, "A"),
            text_label(ax + 6, by + 4, "I"),
            text_label(ox - 16, my + 4, "Q"),
            text_label(mx - 4, oy + 16, "P"),
            labeled_point(mx, my, "M", dx=8, dy=-4, color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 460 280",
        body,
        "fig_38",
        "FIG. 38 — Four-cusped astroid as envelope of a segment AB of constant length sliding on Ox, Oy",
    )


def generate_fig_39() -> str:
    mx, my = 232.0, 144.0
    r = 68.0
    body = "\n".join(
        [
            f'    <circle cx="{mx:.1f}" cy="{my:.1f}" r="{r:.1f}" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />',
            '    <path d="M 118 176 Q 178 136 226 38" class="c-amber" />',
            '    <path d="M 164 242 Q 248 202 318 118" class="c-green-dash" stroke="#047857" stroke-width="1.4" stroke-dasharray="5,4" fill="none" />',
            '    <line x1="184" y1="96" x2="280" y2="192" class="c-dash" />',
            '    <line x1="142" y1="226" x2="294" y2="66" class="c-red" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="165" y2="154" class="c-main" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="188" y2="196" class="c-main" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="218" y2="210" class="c-main" />',
            labeled_point(mx, my, "M", dx=8, dy=4, color="#1e3a8a"),
            text_label(202, 48, "C_1"),
            text_label(294, 64, "C", color="#dc2626"),
            text_label(172, 92, "P"),
            text_label(284, 204, "P'"),
            text_label(135, 148, "E"),
            text_label(144, 168, "N"),
            text_label(172, 208, "Q"),
            text_label(208, 226, "N'"),
            text_label(260, 232, "E'"),
            text_label(128, 232, "T", color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_39",
        "FIG. 39 — Caustic by reflection and auxiliary circle with center M",
    )


def generate_fig_40() -> str:
    mx, my = 230.0, 142.0
    r = 82.0
    caustic = [
        (
            mx + 42 * math.cos(t) - 18 * math.cos(2 * t),
            my - 36 * math.sin(t),
        )
        for t in [i * 0.08 for i in range(-18, 19)]
    ]
    body = "\n".join(
        [
            f'    <circle cx="{mx:.1f}" cy="{my:.1f}" r="{r:.1f}" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />',
            '    <line x1="108" y1="142" x2="356" y2="142" class="ax" />',
            f'    <line x1="{mx:.1f}" y1="46" x2="{mx:.1f}" y2="238" class="c-dash" />',
            '    <line x1="148" y1="36" x2="282" y2="246" class="c-red" />',
            '    <line x1="184" y1="74" x2="184" y2="142" class="c-dash" />',
            '    <line x1="165" y1="90" x2="165" y2="142" class="c-dash" />',
            '    <path d="M 152 216 Q 194 202 204 42" class="c-amber" />',
            poly_path(caustic, cls="c-green"),
            labeled_point(mx, my, "M", dx=6, dy=-4, color="#1e3a8a"),
            text_label(156, 44, "O"),
            text_label(196, 52, "E"),
            text_label(226, 54, "I"),
            text_label(224, 240, "I'"),
            text_label(172, 68, "N"),
            text_label(148, 86, "Q"),
            text_label(186, 104, "P"),
            text_label(160, 156, "q"),
            text_label(182, 156, "p"),
            text_label(278, 128, "C", color="#047857"),
            text_label(344, 158, "T"),
            text_label(168, 222, "N'"),
            text_label(184, 238, "E'"),
            text_label(272, 224, "R"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_40",
        "FIG. 40 — Epicycloid caustic formed by rays emanating from point E on a circle",
    )


def generate_fig_41() -> str:
    ox, oy = 96.0, 228.0
    arc = [(158 + 2.6 * t, 174 - 0.35 * t - 0.028 * t * t) for t in range(52)]
    ax, ay = arc[14]
    bx, by = arc[36]
    body = "\n".join(
        [
            axes_2d(ox, oy, 55, 405, 255, 28, xlabel="x", ylabel="y", origin_label="O"),
            '    <line x1="168" y1="184" x2="346" y2="96" class="c-dash" />',
            '    <line x1="224" y1="162" x2="298" y2="34" class="c-red" />',
            poly_path(arc, cls="c-blue"),
            arrow_head(214, 146, -42),
            labeled_point(ax, ay, "A", dx=6, dy=15, color="#1e3a8a"),
            labeled_point(bx, by, "B", dx=-18, dy=-4, color="#1e3a8a"),
            text_label(266, 134, "ω"),
            text_label(348, 112, "T"),
            text_label(302, 48, "T'", color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 450 270",
        body,
        "fig_41",
        "FIG. 41 — Angle of contingency ω between tangents AT and BT' and curvature dα/ds",
    )


def generate_fig_42() -> str:
    evol = [(138 + 112 * (t / 40.0) ** 1.4, 168 - 128 * (t / 40.0)) for t in range(41)]
    inv1 = [(126 + 3.2 * t, 198 + 0.9 * t - 0.008 * t * t) for t in range(46)]
    inv2 = [(118 + 3.4 * t, 208 + 0.95 * t - 0.008 * t * t) for t in range(46)]
    inv3 = [(110 + 3.6 * t, 218 + 1.0 * t - 0.008 * t * t) for t in range(48)]
    body = "\n".join(
        [
            poly_path(evol, cls="c-red"),
            poly_path(inv1, cls="c-dash"),
            poly_path(inv2, cls="c-dash"),
            poly_path(inv3, cls="c-blue"),
            '    <line x1="208" y1="108" x2="122" y2="218" class="c-main" />',
            '    <line x1="228" y1="82" x2="168" y2="236" class="c-main" />',
            '    <line x1="244" y1="54" x2="226" y2="245" class="c-main" />',
            text_label(168, 108, "(D)", color="#dc2626"),
            text_label(226, 44, "A"),
            labeled_point(244, 54, "I_2", dx=-22, dy=4, color="#dc2626"),
            labeled_point(228, 82, "I", dx=-16, dy=2, color="#dc2626"),
            labeled_point(208, 108, "I_1", dx=-20, dy=-2, color="#dc2626"),
            labeled_point(122, 218, "M_1", dx=-26, dy=4, color="#1e3a8a"),
            labeled_point(168, 236, "M", dx=-12, dy=16, color="#1e3a8a"),
            labeled_point(226, 245, "M_2", dx=-6, dy=16, color="#1e3a8a"),
            text_label(282, 246, "C", color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_42",
        "FIG. 42 — Evolute (D) as envelope of normals I₁M₁, IM, I₂M₂ and parallel involutes",
    )


def generate_fig_43() -> str:
    cusp_l = [(225 - 86 * (t / 30.0) ** 1.5, 48 + 94 * (t / 30.0)) for t in range(31)]
    cusp_r = [(225 + 86 * (t / 30.0) ** 1.5, 48 + 94 * (t / 30.0)) for t in range(31)]
    base_arc = [
        (134 + 3.8 * t, 216 + 24 * math.sin(math.pi * t / 50.0)) for t in range(51)
    ]
    body = "\n".join(
        [
            poly_path(cusp_l, cls="c-red"),
            poly_path(cusp_r, cls="c-red"),
            poly_path(base_arc, cls="c-blue"),
            '    <line x1="205" y1="88" x2="148" y2="222" class="c-main" />',
            '    <line x1="225" y1="48" x2="236" y2="240" class="c-main" />',
            '    <line x1="248" y1="88" x2="318" y2="220" class="c-main" />',
            labeled_point(225, 48, "I", dx=-4, dy=-8, color="#dc2626"),
            labeled_point(205, 88, "I_1", dx=-22, dy=4, color="#dc2626"),
            labeled_point(248, 88, "I_2", dx=8, dy=4, color="#dc2626"),
            labeled_point(148, 222, "M_1", dx=-22, dy=14, color="#1e3a8a"),
            labeled_point(236, 240, "M", dx=-6, dy=18, color="#1e3a8a"),
            labeled_point(318, 220, "M'", dx=8, dy=12, color="#1e3a8a"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_43",
        "FIG. 43 — Evolute with a cusp at I corresponding to an extremum of curvature at M",
    )


def generate_fig_44() -> str:
    ox, oy = 84.0, 140.0
    r = 38.0
    cyc = []
    evol = []
    for i in range(65):
        t = 2.0 * math.pi * i / 64.0
        x = ox + r * (t - math.sin(t))
        y = oy - r * (1.0 - math.cos(t))
        cyc.append((x, y))
    for i in range(33):
        t = math.pi * i / 32.0
        x = ox + r * (t + math.sin(t))
        y = oy + r * (1.0 - math.cos(t))
        evol.append((x, y))
    cx = ox + r * 1.95
    body = "\n".join(
        [
            axes_2d(ox, oy, 48, 412, 245, 32, xlabel="x", ylabel="y", origin_label="O"),
            f'    <line x1="{ox:.1f}" y1="{oy - 2 * r:.1f}" x2="{ox + 2 * math.pi * r:.1f}" y2="{oy - 2 * r:.1f}" class="c-dash" />',
            f'    <line x1="{ox:.1f}" y1="{oy + 2 * r:.1f}" x2="{ox + math.pi * r:.1f}" y2="{oy + 2 * r:.1f}" class="c-dash" />',
            f'    <line x1="{ox + math.pi * r:.1f}" y1="{oy - 2 * r:.1f}" x2="{ox + math.pi * r:.1f}" y2="{oy + 2 * r:.1f}" class="c-dash" />',
            f'    <circle cx="{cx:.1f}" cy="{oy - r:.1f}" r="{r:.1f}" class="f-blue" stroke="#1e3a8a" stroke-width="1.4" />',
            f'    <circle cx="{cx:.1f}" cy="{oy + r:.1f}" r="{r:.1f}" class="f-amber" stroke="#b45309" stroke-width="1.4" />',
            f'    <line x1="{cx:.1f}" y1="{oy - 2 * r:.1f}" x2="{cx:.1f}" y2="{oy + 2 * r:.1f}" class="c-dash" />',
            '    <line x1="126" y1="88" x2="196" y2="198" class="c-red" />',
            poly_path(cyc, cls="c-blue"),
            poly_path(evol, cls="c-red"),
            text_label(cx - 6, oy - 2 * r - 6, "T"),
            text_label(cx - 6, oy + 2 * r + 15, "T'"),
            text_label(ox + math.pi * r - 6, oy - 2 * r - 6, "B"),
            text_label(ox + math.pi * r - 6, oy + 2 * r + 15, "B'"),
            text_label(ox + math.pi * r + 5, oy - 4, "H"),
            text_label(ox + 2 * math.pi * r - 6, oy + 16, "O_1"),
            labeled_point(cx, oy - r, "C", dx=5, dy=4),
            labeled_point(cx, oy, "I", dx=5, dy=-4),
            labeled_point(cx, oy + r, "C'", dx=5, dy=4),
            labeled_point(126, 88, "M", dx=-18, dy=-2, color="#1e3a8a"),
            labeled_point(196, 198, "M'", dx=6, dy=4, color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_44",
        "FIG. 44 — Cycloid arch OMBO₁, generating circles C, C', and congruent cycloid evolute OM'B'",
    )


def generate_fig_45() -> str:
    ox, oy = 188.0, 224.0
    a = 52.0
    cat = [(ox + t, oy - a * math.cosh(t / a)) for t in range(-105, 110, 4)]
    trac_r = []
    trac_l = []
    for i in range(1, 48):
        s = i * 0.062
        sech = 1.0 / math.cosh(s)
        y = oy - a * sech
        dx = a * (s - math.tanh(s))
        trac_r.append((ox + dx, y))
        trac_l.append((ox - dx, y))
    x0 = 48.0
    mx, my = ox + x0, oy - a * math.cosh(x0 / a)
    tx_pt = ox + x0 - a * math.cosh(x0 / a) / math.sinh(x0 / a) * 0.55
    nx_pt = ox + x0 + a * math.cosh(x0 / a) * math.sinh(x0 / a) * 1.15
    body = "\n".join(
        [
            axes_2d(ox, oy, 42, 418, 252, 24, xlabel="x", ylabel="y", origin_label="O"),
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{tx_pt:.1f}" y2="{oy:.1f}" class="c-red" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{nx_pt:.1f}" y2="{oy:.1f}" class="c-green" />',
            poly_path(cat, cls="c-blue"),
            poly_path(trac_r, cls="c-amber"),
            poly_path(trac_l, cls="c-amber"),
            labeled_point(ox, oy - a, "A", dx=-16, dy=-4, color="#1e3a8a"),
            labeled_point(mx, my, "M", dx=-18, dy=-4, color="#1e3a8a"),
            labeled_point(
                ox - 58, oy - a * math.cosh(58 / a), "M'", dx=-22, dy=4, color="#1e3a8a"
            ),
            labeled_point(tx_pt, oy, "T", dx=-4, dy=16, color="#dc2626"),
            labeled_point(mx, oy, "P", dx=-4, dy=16),
            labeled_point(nx_pt, oy, "N", dx=-4, dy=16, color="#047857"),
            text_label(ox + 20, oy - 24, "m", color="#b45309"),
            text_label(ox - 48, oy - 14, "m'", color="#b45309"),
            text_label(ox + 108, oy - 8, "n", color="#b45309"),
            text_label(ox - 118, oy - 8, "n'", color="#b45309"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_45",
        "FIG. 45 — Catenary M'AM and its involute the tractrix n'm'Amn",
    )


def generate_fig_46() -> str:
    ox, oy = 112.0, 232.0
    body = "\n".join(
        [
            f'    <line x1="68" y1="{oy:.1f}" x2="405" y2="{oy:.1f}" class="ax" marker-end="url(#arr)" />',
            '    <line x1="106" y1="248" x2="176" y2="34" class="ax" marker-end="url(#arr)" />',
            '    <line x1="184" y1="232" x2="210" y2="152" class="c-main" />',
            '    <line x1="274" y1="232" x2="322" y2="84" class="c-main" />',
            '    <path d="M 278 164 Q 328 112 368 42" class="c-blue" />',
            '    <path d="M 278 164 Q 344 128 394 64" class="c-amber" />',
            '    <line x1="210" y1="152" x2="314" y2="108" class="c-red" />',
            '    <line x1="210" y1="152" x2="342" y2="112" class="c-red-dash" />',
            '    <line x1="210" y1="152" x2="352" y2="136" class="c-main" />',
            text_label(408, oy + 5, "x"),
            text_label(158, 44, "y"),
            text_label(124, 218, "θ"),
            labeled_point(ox, oy, "O", dx=-16, dy=15),
            text_label(178, oy + 16, "a"),
            text_label(268, oy + 16, "p"),
            labeled_point(210, 152, "A", dx=-18, dy=4),
            labeled_point(314, 108, "m", dx=-14, dy=-8, color="#1e3a8a"),
            labeled_point(342, 112, "m'", dx=8, dy=4, color="#b45309"),
            labeled_point(298, 156, "n", dx=6, dy=12),
            text_label(348, 52, "C", color="#1e3a8a"),
            text_label(394, 78, "C'", color="#b45309"),
        ]
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig_46",
        "FIG. 46 — Tangents and secants drawn from point A to curves C and C' in oblique coordinates",
    )


def generate_fig_47() -> str:
    ox, oy = 230.0, 218.0
    r = 68.0
    parab = [(ox + t, oy - 0.0082 * t * t) for t in range(-136, 140, 4)]
    mx = ox + 64.0
    my = oy - 0.0082 * 64.0 * 64.0
    body = "\n".join(
        [
            axes_2d(ox, oy, 64, 396, 252, 24, xlabel="x", ylabel="y", origin_label="O"),
            f'    <circle cx="{ox:.1f}" cy="{oy - r:.1f}" r="{r:.1f}" class="f-blue" stroke="#dc2626" stroke-width="1.8" />',
            poly_path(parab, cls="c-blue"),
            f'    <line x1="{ox:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{my:.1f}" class="c-main" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{oy:.1f}" class="c-dash" />',
            text_label(276, 94, "C_1", color="#dc2626"),
            labeled_point(ox, my, "m", dx=-18, dy=4),
            labeled_point(mx, my, "M", dx=8, dy=4, color="#1e3a8a"),
            labeled_point(mx, oy, "P", dx=-5, dy=16),
        ]
    )
    return figure_svg(
        "0 0 450 270",
        body,
        "fig_47",
        "FIG. 47 — Osculating circle C₁ at the vertex O of a symmetric curve",
    )


def generate_fig_48() -> str:
    cx, cy = 118.0, 148.0
    r = 76.0
    body = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#grad-sphere)" stroke="#1e3a8a" stroke-width="1.8" />',
            '    <path d="M 168 182 Q 178 136 154 96" class="c-red" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="154" y2="96" class="c-main" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="168" y2="128" class="c-main" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="72" y2="104" class="c-dash" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="62" y2="128" class="c-dash" />',
            labeled_point(cx, cy, "O", dx=-6, dy=16),
            text_label(176, 154, "Σ", color="#dc2626"),
            text_label(172, 186, "a"),
            text_label(174, 128, "m"),
            text_label(140, 96, "m'"),
            text_label(158, 86, "t"),
            text_label(68, 96, "t'"),
            text_label(74, 114, "n'"),
            text_label(52, 134, "n"),
            '    <path d="M 244 212 Q 326 208 386 92" class="c-blue" />',
            '    <path d="M 294 202 Q 336 168 332 82" class="c-amber" />',
            '    <line x1="252" y1="214" x2="412" y2="158" class="c-red" />',
            '    <line x1="336" y1="184" x2="398" y2="98" class="c-red-dash" />',
            '    <line x1="282" y1="128" x2="328" y2="195" class="c-main" />',
            labeled_point(328, 195, "M", dx=4, dy=15, color="#1e3a8a"),
            labeled_point(358, 152, "M'", dx=8, dy=4, color="#1e3a8a"),
            text_label(258, 228, "A"),
            text_label(415, 162, "T", color="#dc2626"),
            text_label(402, 102, "T'", color="#dc2626"),
            text_label(364, 178, "Γ", color="#1e3a8a"),
            text_label(338, 108, "Γ'", color="#b45309"),
            text_label(266, 132, "N"),
            text_label(316, 94, "P"),
        ]
    )
    return figure_svg(
        "0 0 460 270",
        body,
        "fig_48",
        "FIG. 48 — Spherical indicatrix Σ of tangents alongside space curve Γ and evolutes Γ'",
    )


def generate_fig_49_a() -> str:
    mx, my = 225.0, 174.0
    c_pos = [(mx + 2.4 * t, my - 0.036 * t * t) for t in range(0, 48, 3)]
    c_neg = [(mx - 1.8 * t, my + 0.032 * t * t) for t in range(0, 46, 3)]
    body = "\n".join(
        [
            '    <line x1="112" y1="174" x2="348" y2="174" class="ax" marker-end="url(#arr)" />',
            '    <line x1="225" y1="174" x2="225" y2="44" class="c-main" marker-end="url(#arr)" />',
            poly_path(c_pos, cls="c-blue"),
            poly_path(c_neg, cls="c-red-dash"),
            labeled_point(mx, my, "M", dx=-8, dy=18, color="#1e3a8a"),
            labeled_point(mx, 134, "P", dx=8, dy=4),
            text_label(232, 56, "N"),
            text_label(338, 118, "M'", color="#1e3a8a"),
            text_label(152, 242, "M''", color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 450 265",
        body,
        "fig_49_a",
        "FIG. 49, a — Projection of a space curve at a point where the first odd derivative is non-zero",
    )


def generate_fig_49_b() -> str:
    mx, my = 225.0, 174.0
    c_left = [(mx - 2.3 * t, my - 0.036 * t * t) for t in range(0, 48, 3)]
    c_right = [(mx + 1.8 * t, my + 0.032 * t * t) for t in range(0, 46, 3)]
    body = "\n".join(
        [
            '    <line x1="112" y1="174" x2="348" y2="174" class="ax" marker-end="url(#arr)" />',
            '    <line x1="225" y1="174" x2="225" y2="44" class="c-main" marker-end="url(#arr)" />',
            poly_path(c_left, cls="c-blue"),
            poly_path(c_right, cls="c-red-dash"),
            labeled_point(mx, my, "M", dx=-8, dy=18, color="#1e3a8a"),
            labeled_point(mx, 134, "P", dx=8, dy=4),
            text_label(232, 56, "N"),
            text_label(122, 114, "M''", color="#1e3a8a"),
            text_label(316, 242, "M'", color="#dc2626"),
        ]
    )
    return figure_svg(
        "0 0 450 265",
        body,
        "fig_49_b",
        "FIG. 49, b — Projection of a space curve crossing its tangent line from left to right",
    )


def generate_fig_50() -> str:
    mx, my = 168.0, 212.0
    gamma = [(96 + 3.8 * t, 96 + 3.4 * t - 0.025 * t * t) for t in range(58)]
    d_curve = [(226 + 1.8 * t, 142 - 1.4 * t + 0.015 * t * t) for t in range(42)]
    body = "\n".join(
        [
            poly_path(gamma, cls="c-blue"),
            poly_path(d_curve, cls="c-amber"),
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="124" y2="62" class="c-main" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="348" y2="168" class="c-green" />',
            f'    <line x1="{mx:.1f}" y1="{my:.1f}" x2="298" y2="56" class="c-red" />',
            '    <line x1="234" y1="44" x2="286" y2="184" class="c-main" />',
            text_label(104, 178, "Γ", color="#1e3a8a"),
            text_label(308, 98, "D", color="#b45309"),
            text_label(132, 74, "N_b"),
            text_label(354, 172, "N", color="#047857"),
            text_label(196, 198, "φ"),
            labeled_point(mx, my, "M", dx=-18, dy=14, color="#1e3a8a"),
            labeled_point(256, 104, "M_1", dx=-26, dy=4, color="#b45309"),
            labeled_point(286, 184, "P", dx=-4, dy=18, color="#047857"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_50",
        "FIG. 50 — Bertrand curves Γ and D with common normals and constant angle φ",
    )


def generate_fig_51() -> str:
    body = "\n".join(
        [
            '    <ellipse cx="268" cy="76" rx="38" ry="22" transform="rotate(34 268 76)" class="f-blue" stroke="#1e3a8a" stroke-width="1.65" />',
            '    <ellipse cx="242" cy="144" rx="42" ry="24" transform="rotate(34 242 144)" class="f-amber" stroke="#b45309" stroke-width="1.65" />',
            '    <ellipse cx="214" cy="216" rx="44" ry="26" transform="rotate(34 214 216)" class="f-green" stroke="#047857" stroke-width="1.65" />',
            '    <line x1="282" y1="36" x2="202" y2="254" class="c-main" />',
            '    <line x1="184" y1="212" x2="244" y2="220" class="c-red" />',
            '    <line x1="196" y1="196" x2="232" y2="236" class="c-blue" />',
            text_label(286, 44, "N"),
            text_label(188, 258, "S"),
            text_label(306, 94, "Σ"),
            text_label(286, 162, "Σ'"),
            text_label(266, 92, "Γ"),
            text_label(224, 134, "Γ'"),
            text_label(254, 162, "γ'"),
            labeled_point(268, 76, "A", dx=-18, dy=2),
            labeled_point(242, 144, "A'", dx=6, dy=-2),
            labeled_point(214, 216, "M", dx=6, dy=-4),
            text_label(186, 228, "T'"),
            text_label(242, 234, "T"),
            text_label(204, 236, "C'"),
            text_label(224, 238, "C"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_51",
        "FIG. 51 — Central point M and variation of the tangent plane along a generator SN of a ruled surface",
    )


def generate_fig_52() -> str:
    mx, my = 216.0, 144.0
    sigma = [
        (126 + 2.4 * t, 224 - 80 * math.sin(math.pi * t / 82.0)) for t in range(68)
    ]
    gamma = [(216 + 24 * math.sin(t / 28.0), 144 + 2.2 * t) for t in range(46)]
    c_arc = [(216 + 2.2 * t, 144 - 64 * math.sin(t / 34.0)) for t in range(54)]
    cp_arc = [(216 + 1.6 * t, 144 - 72 * math.sin(t / 28.0)) for t in range(42)]
    body = "\n".join(
        [
            '    <line x1="216" y1="248" x2="216" y2="38" class="c-main" marker-end="url(#arr)" />',
            '    <line x1="216" y1="144" x2="365" y2="144" class="c-main" marker-end="url(#arr)" />',
            '    <line x1="216" y1="144" x2="308" y2="212" class="c-red" />',
            '    <line x1="216" y1="144" x2="178" y2="222" class="c-main" />',
            '    <line x1="216" y1="144" x2="314" y2="92" class="c-blue" />',
            '    <line x1="216" y1="144" x2="268" y2="82" class="c-amber" />',
            poly_path(sigma, cls="c-main"),
            poly_path(gamma, cls="c-green"),
            poly_path(c_arc, cls="c-blue"),
            poly_path(cp_arc, cls="c-amber"),
            text_label(198, 48, "N"),
            text_label(368, 142, "T"),
            text_label(312, 216, "T_1", color="#dc2626"),
            text_label(248, 162, "ω"),
            text_label(134, 214, "Σ"),
            text_label(244, 224, "Γ", color="#047857"),
            text_label(162, 222, "R"),
            text_label(202, 174, "r"),
            text_label(276, 122, "l", color="#1e3a8a"),
            text_label(248, 102, "l'", color="#b45309"),
            text_label(232, 128, "i"),
            text_label(338, 112, "C", color="#1e3a8a"),
            text_label(224, 68, "C'", color="#b45309"),
            labeled_point(mx, my, "M", dx=-20, dy=-4),
            labeled_point(314, 92, "m", dx=8, dy=-2, color="#1e3a8a"),
            labeled_point(268, 82, "m'", dx=-6, dy=-8, color="#b45309"),
        ]
    )
    return figure_svg(
        "0 0 450 275",
        body,
        "fig_52",
        "FIG. 52 — Meusnier's theorem and normal vs. oblique sections Γ, C, C' of a surface Σ at M",
    )


GOURSAT_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "1": generate_fig_1,
    "2": generate_fig_2,
    "3": generate_fig_3,
    "4": generate_fig_4,
    "5": generate_fig_5,
    "6": generate_fig_6,
    "7": generate_fig_7,
    "8": generate_fig_8,
    "9": generate_fig_9,
    "10": generate_fig_10,
    "11": generate_fig_11,
    "12": generate_fig_12,
    "13": generate_fig_13,
    "14": generate_fig_14,
    "15": generate_fig_15,
    "16": generate_fig_16,
    "17": generate_fig_17,
    "18": generate_fig_18,
    "19": generate_fig_19,
    "20": generate_fig_20,
    "21": generate_fig_21,
    "22": generate_fig_22,
    "23": generate_fig_23,
    "24": generate_fig_24,
    "25": generate_fig_25,
    "26": generate_fig_26,
    "27": generate_fig_27,
    "28": generate_fig_28,
    "29": generate_fig_29,
    "30": generate_fig_30,
    "31": generate_fig_31,
    "32": generate_fig_32,
    "33": generate_fig_33,
    "34": generate_fig_34,
    "35": generate_fig_35,
    "36": generate_fig_36,
    "37_a": generate_fig_37_a,
    "37_b": generate_fig_37_b,
    "38": generate_fig_38,
    "39": generate_fig_39,
    "40": generate_fig_40,
    "41": generate_fig_41,
    "42": generate_fig_42,
    "43": generate_fig_43,
    "44": generate_fig_44,
    "45": generate_fig_45,
    "46": generate_fig_46,
    "47": generate_fig_47,
    "48": generate_fig_48,
    "49_a": generate_fig_49_a,
    "49_b": generate_fig_49_b,
    "50": generate_fig_50,
    "51": generate_fig_51,
    "52": generate_fig_52,
}


def generate_goursat_cover_svg() -> str:
    stripe_ys: list[float] = []
    for y in range(6, 13, 3):
        stripe_ys.append(float(y))
    for y in range(44, 114, 4):
        stripe_ys.append(float(y))
    for y in range(156, 184, 4):
        stripe_ys.append(float(y))
    for y in range(226, 254, 4):
        stripe_ys.append(float(y))
    for y in range(296, 324, 4):
        stripe_ys.append(float(y))
    for y in range(398, 582, 4):
        stripe_ys.append(float(y))

    stripes = "\n".join(
        f'    <line x1="0" y1="{y:.1f}" x2="432" y2="{y:.1f}" stroke="#f6f1e3" stroke-width="1.45" />'
        for y in stripe_ys
    )

    emblem_pts = [
        (86 + t * 2.6, 520 - 82 * math.sin(t / 32.0) - 0.18 * t)
        for t in range(0, 102, 3)
    ]
    emblem_evol = [
        (132 + t * 1.9, 442 + 48 * math.cos(t / 28.0) - 0.12 * t)
        for t in range(0, 96, 3)
    ]

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 432 648" width="432" height="648" data-fig="book_cover" role="img">\n'
        "  <title>Édouard Goursat — A Course in Mathematical Analysis, Volume I (Book Cover)</title>\n"
        "  <defs>\n"
        '    <linearGradient id="dover-tan" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '      <stop offset="0%" stop-color="#c3ae86" />\n'
        '      <stop offset="55%" stop-color="#baa37a" />\n'
        '      <stop offset="100%" stop-color="#ae966c" />\n'
        "    </linearGradient>\n"
        '    <linearGradient id="plinth-ink" x1="0%" y1="0%" x2="0%" y2="100%">\n'
        '      <stop offset="0%" stop-color="#141619" />\n'
        '      <stop offset="100%" stop-color="#090a0c" />\n'
        "    </linearGradient>\n"
        "  </defs>\n"
        "  <style>\n"
        '    .cov-top { font-family: "Futura", "Helvetica Neue", "Arial Narrow", sans-serif; font-size: 16.5px; font-weight: 700; letter-spacing: 0.03em; fill: #0d0f12; }\n'
        '    .cov-band { font-family: "Futura", "Helvetica Neue", "Arial Narrow", sans-serif; font-size: 22.0px; font-weight: 800; letter-spacing: 0.02em; fill: #090a0c; }\n'
        '    .cov-by { font-family: "Helvetica Neue", "Futura", sans-serif; font-size: 15px; font-weight: 700; letter-spacing: 0.015em; fill: #0d0f12; }\n'
        '    .cov-vol { font-family: "New Computer Modern", "Palatino", "Georgia", serif; font-size: 38px; font-weight: 700; font-style: italic; letter-spacing: 0.08em; fill: #d6c39b; }\n'
        '    .cov-sub { font-family: "New Computer Modern", "Georgia", serif; font-size: 10.5px; font-style: italic; fill: #4a3d28; }\n'
        "  </style>\n"
        '  <rect x="0" y="0" width="432" height="584" fill="url(#dover-tan)" />\n'
        f"{stripes}\n"
        '  <g opacity="0.28">\n'
        '    <circle cx="216" cy="488" r="68" fill="none" stroke="#4a3d28" stroke-width="1.3" stroke-dasharray="4,3" />\n'
        '    <circle cx="216" cy="488" r="44" fill="none" stroke="#4a3d28" stroke-width="1.0" />\n'
        f'    <path d="M {" L ".join(f"{x:.1f} {y:.1f}" for x, y in emblem_pts)}" fill="none" stroke="#3b2f1e" stroke-width="1.75" />\n'
        f'    <path d="M {" L ".join(f"{x:.1f} {y:.1f}" for x, y in emblem_evol)}" fill="none" stroke="#5c4930" stroke-width="1.3" stroke-dasharray="3,3" />\n'
        '    <line x1="156" y1="532" x2="276" y2="444" stroke="#3b2f1e" stroke-width="1.2" />\n'
        '    <line x1="216" y1="488" x2="262" y2="532" stroke="#3b2f1e" stroke-width="1.2" />\n'
        "  </g>\n"
        '  <rect x="0" y="13" width="432" height="29" fill="url(#dover-tan)" />\n'
        '  <text x="216" y="33.5" text-anchor="middle" class="cov-top">A COURSE IN MATHEMATICAL ANALYSIS</text>\n'
        '  <rect x="0" y="115" width="432" height="39" fill="url(#dover-tan)" />\n'
        '  <text x="216" y="143" text-anchor="middle" class="cov-band">APPLICATIONS TO GEOMETRY</text>\n'
        '  <rect x="0" y="185" width="432" height="39" fill="url(#dover-tan)" />\n'
        '  <text x="216" y="213" text-anchor="middle" class="cov-band">EXPANSION IN SERIES</text>\n'
        '  <rect x="0" y="255" width="432" height="39" fill="url(#dover-tan)" />\n'
        '  <text x="216" y="283" text-anchor="middle" class="cov-band">DEFINITE INTEGRALS</text>\n'
        '  <rect x="0" y="325" width="432" height="71" fill="url(#dover-tan)" />\n'
        '  <text x="216" y="353" text-anchor="middle" class="cov-band">DERIVATIVES AND</text>\n'
        '  <text x="216" y="385" text-anchor="middle" class="cov-band">DIFFERENTIALS</text>\n'
        '  <rect x="122" y="471" width="188" height="21" rx="2" fill="url(#dover-tan)" />\n'
        '  <text x="216" y="487" text-anchor="middle" class="cov-by">by Édouard Goursat</text>\n'
        '  <rect x="98" y="519" width="236" height="21" rx="2" fill="url(#dover-tan)" />\n'
        '  <text x="216" y="535" text-anchor="middle" class="cov-by">translated by E. R. Hedrick</text>\n'
        '  <rect x="0" y="582" width="432" height="66" fill="url(#plinth-ink)" />\n'
        '  <line x1="0" y1="582" x2="432" y2="582" stroke="#f6f1e3" stroke-width="1.6" />\n'
        '  <text x="216" y="628" text-anchor="middle" class="cov-vol">VOLUME I</text>\n'
        "</svg>"
    )


GOURSAT_FIGURE_BOOK = FigureBook(
    slug="goursat_analysis",
    title="Édouard Goursat · A Course in Mathematical Analysis, Vol. I",
    subtitle="Dover Edition Cover & All 54 Canonical Textbook Diagrams Reproduced via Code as Vector SVGs",
    figures=(
        FigureSpec(
            fig_id="cover",
            label="BOOK COVER",
            chapter=0,
            build=generate_goursat_cover_svg,
            title="Dover Edition Cover — A Course in Mathematical Analysis, Volume I",
        ),
        *(
            FigureSpec(
                fig_id=fid,
                label=f"FIG. {fid.replace('_', ', ')}",
                chapter=0,
                build=build,
            )
            for fid, build in GOURSAT_SVG_GENERATORS.items()
        ),
    ),
    search_hint="Search FIG. 37, evolute, Green...",
)


def export_goursat_figures(fig_dir: Path) -> list[Path]:
    """Write the cover and every vector figure as SVG; keep the original scans in `figures_raw`."""
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = fig_dir.parent / "figures_raw"
    if not raw_dir.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)
        for existing_png in sorted(fig_dir.glob("fig_*.png")):
            _ = shutil.copy2(existing_png, raw_dir / existing_png.name)
    cover = fig_dir / "book_cover.svg"
    _ = cover.write_text(generate_goursat_cover_svg(), encoding="utf-8")
    assets = render_figures(GOURSAT_FIGURE_BOOK, fig_dir)
    return [
        cover,
        *(fig_dir / a.filename for a in assets.values() if a.fig_id != "cover"),
    ]


def export_goursat_web_gallery(web_dir: Path) -> Path:
    web_dir = Path(web_dir)
    if web_dir.suffix.lower() == ".html":
        web_dir = web_dir.parent
    _ = render_figures(GOURSAT_FIGURE_BOOK, web_dir, web_dir)
    return web_dir / "index.html"
