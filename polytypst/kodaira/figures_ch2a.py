import math
from collections.abc import Callable

from .svg_primitives import (
    arc_path,
    arrow_line,
    axes_xy,
    circle_contour,
    math_label,
    mid_arrow_path,
    point_dot,
    smooth_curve,
    svg_figure,
    tangent_arrow,
)

CHAPTER_FIG_TITLES: dict[str, str] = {
    "2_1": "Piecewise smooth curve C = C_1 + C_2 + C_3 + C_4 from gamma(a) to gamma(b)",
    "2_2": "Piecewise smooth closed Jordan curve C = C_1 C_2 C_3 C_4 C_5",
    "2_3": "Local tangent-normal coordinate system w = u + iv at boundary point gamma(c) of D",
    "2_4": "Local neighborhood U divided by C: v = psi(u) into U^(+) and U^(-)",
    "2_5": "Curve lambda crossing C at gamma(t_0) at angle theta between U^(-) and U^(+)",
    "2_6": "Small circle lambda centered at vertex gamma(a_k) intersecting C_k and C_(k+1)",
    "2_7": "Annular domain D = {z : epsilon < |z| < R} with boundary C_R - C_epsilon",
    "2_8": "Parameter rectangle K = [a, b] x [0, 1] in the (t, s)-plane",
    "2_9": "Upper half-annulus cell Gamma(K) = {t e^(is) : epsilon <= t <= R, 0 <= s <= pi}",
    "2_10": "Smooth cells Gamma(K) bounded by y = phi(x) and y = psi(x) over [a, b]",
    "2_11": "Semidisk cell Gamma(K) on [-2, 0] centered at -1",
    "2_12": "Interior E and boundary sides L_1, L_2, L_3, L_4 of parameter rectangle K",
    "2_13": "Cell Gamma(E) with pinched vertical sides and boundary C_1 C_3",
    "2_14": "Smooth cell Gamma(K) with parameter curves gamma_(1/3) and _c gamma and boundary angles",
    "2_15": "Degenerate semidisk cell with parameter curves gamma_(1/3) and _c gamma converging to 0",
    "2_16": "Cellular decomposition of a closed disk into five cells Gamma_1(K_1) through Gamma_5(K_5)",
    "2_17": "Grid of squares Q_(hk) of side delta covering [D] with boundary cells R_j",
    "2_18": "Boundary curve C intersecting adjacent grid squares Q_(hk) and Q_(h'k')",
    "2_19": "Subdivision of corner-cut grid squares into smooth cells and rectangles",
}


def fig_2_1() -> str:
    c1 = smooth_curve(
        [(52.0, 142.0), (98.0, 84.0), (154.0, 42.0)],
        cls="c-blue",
        arrow_indices=[(0, True)],
        marker="arr-blue",
    )
    c2 = smooth_curve(
        [(154.0, 42.0), (180.0, 102.0), (218.0, 148.0)],
        cls="c-blue",
        arrow_indices=[(0, True)],
        marker="arr-blue",
    )
    c3 = smooth_curve(
        [(218.0, 148.0), (282.0, 74.0), (332.0, 44.0), (376.0, 32.0)],
        cls="c-blue",
        arrow_indices=[(0, True)],
        marker="arr-blue",
    )
    c4 = smooth_curve(
        [(376.0, 32.0), (336.0, 96.0), (372.0, 146.0), (456.0, 118.0)],
        cls="c-blue",
        arrow_indices=[(0, True)],
        marker="arr-blue",
    )
    curves = f"{c1}\n{c2}\n{c3}\n{c4}"
    labels = "\n".join(
        [
            point_dot(52.0, 142.0),
            point_dot(456.0, 118.0),
            math_label(30.0, 172.0, "γ", tail="(a)"),
            math_label(464.0, 123.0, "γ", tail="(b)"),
            math_label(66.0, 80.0, "C", sub="1", color="#1e3a8a"),
            math_label(186.0, 94.0, "C", sub="2", color="#1e3a8a"),
            math_label(264.0, 54.0, "C", sub="3", color="#1e3a8a"),
            math_label(368.0, 172.0, "C", sub="4", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 510 200",
        curves=curves,
        labels=labels,
        fig_id="2_1",
        title=CHAPTER_FIG_TITLES["2_1"],
    )


def fig_2_2() -> str:
    d_fill = (
        "M 136.0 232.0 "
        "Q 248.0 186.0 368.0 242.0 "
        "Q 392.0 168.0 432.0 102.0 "
        "Q 312.0 104.0 264.0 42.0 "
        "Q 118.0 38.0 32.0 108.0 "
        "Q 132.0 106.0 136.0 232.0 Z"
    )
    regions = f'    <path d="{d_fill}" class="f-blue" opacity="0.45" />'
    c1 = mid_arrow_path(
        "M 136.0 232.0 Q 248.0 186.0 368.0 242.0",
        250.0,
        210.0,
        1.0,
        0.04,
        cls="c-blue",
        marker="arr-blue",
    )
    c2 = mid_arrow_path(
        "M 368.0 242.0 Q 392.0 168.0 432.0 102.0",
        396.0,
        170.0,
        0.42,
        -0.91,
        cls="c-blue",
        marker="arr-blue",
    )
    c3 = mid_arrow_path(
        "M 432.0 102.0 Q 312.0 104.0 264.0 42.0",
        332.0,
        88.0,
        -0.92,
        -0.38,
        cls="c-blue",
        marker="arr-blue",
    )
    c4 = mid_arrow_path(
        "M 264.0 42.0 Q 118.0 38.0 32.0 108.0",
        136.0,
        56.0,
        -0.96,
        0.26,
        cls="c-blue",
        marker="arr-blue",
    )
    c5 = mid_arrow_path(
        "M 32.0 108.0 Q 132.0 106.0 136.0 232.0",
        112.0,
        148.0,
        0.38,
        0.92,
        cls="c-blue",
        marker="arr-blue",
    )
    curves = f"{c1}\n{c2}\n{c3}\n{c4}\n{c5}"
    labels = "\n".join(
        [
            math_label(238.0, 236.0, "C", sub="1", color="#1e3a8a"),
            math_label(402.0, 180.0, "C", sub="2", color="#1e3a8a"),
            math_label(332.0, 74.0, "C", sub="3", color="#1e3a8a"),
            math_label(112.0, 38.0, "C", sub="4", color="#1e3a8a"),
            math_label(82.0, 160.0, "C", sub="5", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 460 270",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_2",
        title=CHAPTER_FIG_TITLES["2_2"],
    )


def fig_2_3() -> str:
    d_dom = (
        "M 88.0 246.0 "
        "Q 184.0 236.0 262.0 294.0 "
        "Q 294.0 254.0 338.0 240.0 "
        "Q 336.0 188.0 336.0 162.0 "
        "Q 335.0 142.0 322.0 126.0 "
        "Q 266.0 94.0 260.0 54.0 "
        "Q 212.0 52.0 176.0 86.0 "
        "Q 132.0 122.0 80.0 100.0 "
        "Q 94.0 142.0 76.0 178.0 "
        "Q 64.0 206.0 88.0 246.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_dom}" class="f-blue" />',
            f'    <path d="{d_dom}" class="f-stipple" />',
        ]
    )
    axes = "\n".join(
        [
            arrow_line(390.0, 238.0, 254.0, 14.0, cls="c-main", marker="arr"),
            arrow_line(417.0, 68.3, 187.0, 208.0, cls="c-main", marker="arr"),
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{d_dom}" class="c-blue" />',
            tangent_arrow(176.0, 254.0, 1.0, 0.35, marker="arr-blue"),
            tangent_arrow(336.0, 186.0, 0.02, -1.0, marker="arr-blue"),
            tangent_arrow(322.0, 126.0, -0.52, -0.85, marker="arr"),
            tangent_arrow(176.0, 86.0, -0.82, 0.57, marker="arr-blue"),
            tangent_arrow(76.0, 178.0, -0.22, 0.97, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            point_dot(322.0, 126.0),
            math_label(306.0, 96.0, "γ", tail="(c)"),
            math_label(234.0, 22.0, "u"),
            math_label(160.0, 214.0, "iv"),
            math_label(192.0, 146.0, "D"),
            math_label(300.0, 196.0, "C", sub="k", color="#1e3a8a"),
            math_label(154.0, 276.0, "C", sub="1", color="#1e3a8a"),
            math_label(34.0, 190.0, "C", sub="m", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 460 320",
        axes=axes,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_3",
        title=CHAPTER_FIG_TITLES["2_3"],
    )


def fig_2_4() -> str:
    ax_lines, ax_labels = axes_xy(
        210.0,
        170.0,
        30.0,
        390.0,
        18.0,
        324.0,
        x_label="u",
        y_label="iv",
        origin_label="0",
        origin_dx=-16.0,
        origin_dy=17.0,
    )
    ticks = '    <line x1="134.0" y1="166.0" x2="134.0" y2="174.0" class="ax" />\n    <line x1="286.0" y1="166.0" x2="286.0" y2="174.0" class="ax" />'
    axes = f"{ax_lines}\n{ticks}"
    d_up = (
        "M 134.0 58.0 L 286.0 58.0 L 286.0 148.0 "
        "C 260.0 160.0, 236.0 170.0, 210.0 170.0 "
        "C 180.0 170.0, 156.0 156.0, 134.0 143.0 Z"
    )
    d_dn = (
        "M 134.0 143.0 "
        "C 156.0 156.0, 180.0 170.0, 210.0 170.0 "
        "C 236.0 170.0, 260.0 160.0, 286.0 148.0 "
        "L 286.0 282.0 L 134.0 282.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_up}" class="f-blue" />',
            f'    <path d="{d_up}" class="f-stipple" />',
            f'    <path d="{d_dn}" class="f-amber" opacity="0.65" />',
            f'    <path d="{d_dn}" class="f-stipple" />',
        ]
    )
    d_c = (
        "M 84.0 126.0 "
        "C 104.0 130.0, 118.0 135.0, 134.0 143.0 "
        "C 156.0 156.0, 180.0 170.0, 210.0 170.0 "
        "C 236.0 170.0, 260.0 160.0, 286.0 148.0 "
        "C 312.0 138.0, 332.0 140.0, 354.0 148.0"
    )
    curves = "\n".join(
        [
            f'    <path d="{d_c}" class="c-blue" />',
            tangent_arrow(264.0, 157.5, 0.92, -0.39, marker="arr-blue"),
        ]
    )
    rot_lbl = (
        '    <text x="144.0" y="138.0" class="it" '
        'transform="rotate(28 144 138)">v = ψ(u)</text>'
    )
    labels = "\n".join(
        [
            ax_labels,
            math_label(214.0, 52.0, "2iε"),
            math_label(150.0, 300.0, "−2iε"),
            math_label(100.0, 184.0, "−ε"),
            math_label(290.0, 184.0, "ε"),
            math_label(228.0, 114.0, "U", sup="(+)"),
            math_label(228.0, 232.0, "U", sup="(−)"),
            math_label(60.0, 132.0, "C", color="#1e3a8a"),
            rot_lbl,
        ]
    )
    return svg_figure(
        "0 0 420 340",
        axes=axes,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_4",
        title=CHAPTER_FIG_TITLES["2_4"],
    )


def fig_2_5() -> str:
    d_up = (
        "M 50.0 126.0 L 146.0 86.0 "
        "C 170.0 102.0, 186.0 116.0, 195.0 136.0 "
        "C 200.0 156.0, 202.0 178.0, 202.0 203.0 "
        "L 100.0 246.0 Z"
    )
    d_dn = (
        "M 146.0 86.0 L 290.0 26.0 L 340.0 146.0 L 202.0 203.0 "
        "C 202.0 178.0, 200.0 156.0, 195.0 136.0 "
        "C 186.0 116.0, 170.0 102.0, 146.0 86.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_up}" class="f-blue" />',
            f'    <path d="{d_up}" class="f-stipple" />',
            f'    <path d="{d_dn}" class="f-amber" opacity="0.6" />',
            f'    <path d="{d_dn}" class="f-stipple" />',
        ]
    )
    d_c = (
        "M 203.0 244.0 "
        "C 203.0 206.0, 201.0 162.0, 195.0 136.0 "
        "C 186.0 112.0, 166.0 98.0, 134.0 78.0 "
        "C 112.0 64.0, 106.0 44.0, 102.0 22.0"
    )
    d_lam = (
        "M 326.0 120.0 "
        "C 288.0 94.0, 244.0 102.0, 195.0 136.0 "
        "C 152.0 168.0, 118.0 212.0, 96.0 262.0"
    )
    curves = "\n".join(
        [
            f'    <path d="{d_c}" class="c-blue" />',
            tangent_arrow(146.0, 86.0, -0.82, -0.57, marker="arr-blue"),
            f'    <path d="{d_lam}" class="c-green" />',
            tangent_arrow(140.0, 188.0, -0.62, 0.78, marker="arr-green"),
            arrow_line(195.0, 136.0, 164.0, 24.0, cls="c-main", marker="arr"),
            arrow_line(195.0, 136.0, 108.0, 194.0, cls="c-main", marker="arr"),
            arc_path(
                195.0,
                136.0,
                30.0,
                106.0,
                214.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(195.0, 136.0),
            math_label(94.0, 74.0, "C", color="#1e3a8a"),
            math_label(88.0, 152.0, "U", sup="(+)"),
            math_label(244.0, 82.0, "U", sup="(−)"),
            math_label(154.0, 126.0, "θ"),
            math_label(203.0, 148.0, "γ", tail="(t₀)"),
            math_label(134.0, 208.0, "λ", color="#047857"),
        ]
    )
    return svg_figure(
        "0 0 420 280",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_5",
        title=CHAPTER_FIG_TITLES["2_5"],
    )


def fig_2_6() -> str:
    d_dom = (
        "M 276.0 272.0 "
        "C 242.0 236.0, 226.0 212.0, 216.0 176.0 "
        "C 208.0 148.0, 208.0 132.0, 210.0 118.0 "
        "C 182.0 104.0, 148.0 106.0, 114.0 120.0 "
        "C 82.0 134.0, 58.0 158.0, 42.0 184.0 "
        "C 86.0 254.0, 186.0 284.0, 276.0 272.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_dom}" class="f-blue" />',
            f'    <path d="{d_dom}" class="f-stipple" />',
        ]
    )
    circ = circle_contour(
        210.0, 118.0, 96.0, cls="c-main", arrow_deg=124.0, ccw=True, marker="arr"
    )
    c_k = (
        "M 276.0 272.0 "
        "C 242.0 236.0, 226.0 212.0, 216.0 176.0 "
        "C 208.0 148.0, 208.0 132.0, 210.0 118.0"
    )
    c_k1 = (
        "M 210.0 118.0 "
        "C 182.0 104.0, 148.0 106.0, 114.0 120.0 "
        "C 82.0 134.0, 58.0 158.0, 42.0 184.0"
    )
    c_outer = "M 42.0 184.0 C 86.0 254.0, 186.0 284.0, 276.0 272.0"
    curves = "\n".join(
        [
            circ,
            f'    <path d="{c_k}" class="c-blue" />',
            tangent_arrow(212.0, 158.0, -0.18, -0.98, marker="arr-blue"),
            f'    <path d="{c_k1}" class="c-blue" />',
            tangent_arrow(160.0, 109.0, -0.99, 0.08, marker="arr-blue"),
            f'    <path d="{c_outer}" class="c-sub" />',
            arrow_line(114.0, 120.0, 52.0, 146.0, cls="c-main", marker="arr"),
            arrow_line(114.0, 120.0, 114.0, 190.0, cls="c-main", marker="arr"),
            arc_path(
                114.0,
                120.0,
                32.0,
                203.0,
                270.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
            arrow_line(226.0, 212.0, 196.0, 158.0, cls="c-main", marker="arr"),
            arrow_line(226.0, 212.0, 166.0, 224.0, cls="c-main", marker="arr"),
            arc_path(
                226.0,
                212.0,
                30.0,
                119.0,
                191.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(210.0, 118.0),
            point_dot(114.0, 120.0),
            point_dot(226.0, 212.0),
            math_label(218.0, 120.0, "γ", tail="(a_k)"),
            math_label(146.0, 96.0, "C", sub="k+1", color="#1e3a8a"),
            math_label(220.0, 172.0, "C", sub="k", color="#1e3a8a"),
            math_label(74.0, 114.0, "λ", tail="(α)"),
            math_label(200.0, 240.0, "λ", tail="(β)"),
            math_label(86.0, 160.0, "θ"),
            math_label(182.0, 206.0, "ψ"),
        ]
    )
    return svg_figure(
        "0 0 420 295",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_6",
        title=CHAPTER_FIG_TITLES["2_6"],
    )


def fig_2_7() -> str:
    cx, cy = 195.0, 140.0
    r_out, r_in = 112.0, 36.0
    d_ann = (
        f"M {cx - r_out:.1f} {cy:.1f} "
        f"A {r_out:.1f} {r_out:.1f} 0 1 0 {cx + r_out:.1f} {cy:.1f} "
        f"A {r_out:.1f} {r_out:.1f} 0 1 0 {cx - r_out:.1f} {cy:.1f} Z "
        f"M {cx - r_in:.1f} {cy:.1f} "
        f"A {r_in:.1f} {r_in:.1f} 0 1 1 {cx + r_in:.1f} {cy:.1f} "
        f"A {r_in:.1f} {r_in:.1f} 0 1 1 {cx - r_in:.1f} {cy:.1f} Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_ann}" class="f-blue" fill-rule="evenodd" />',
            f'    <path d="{d_ann}" class="f-stipple" fill-rule="evenodd" />',
        ]
    )
    c_out = circle_contour(
        cx, cy, r_out, cls="c-blue", arrow_deg=18.0, ccw=True, marker="arr-blue"
    )
    c_in = circle_contour(
        cx, cy, r_in, cls="c-red", arrow_deg=-90.0, ccw=False, marker="arr-red"
    )
    curves = f"{c_out}\n{c_in}"
    px = cx + r_out * math.cos(math.radians(48.0))
    py = cy - r_out * math.sin(math.radians(48.0))
    labels = "\n".join(
        [
            point_dot(cx, cy),
            point_dot(px, py),
            math_label(cx - 5.0, cy + 20.0, "0", italic=False),
            math_label(144.0, 82.0, "D"),
            math_label(316.0, 110.0, "C", sub="R", color="#1e3a8a"),
            math_label(175.0, 198.0, "−C", sub="ε", color="#dc2626"),
        ]
    )
    return svg_figure(
        "0 0 400 280",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_7",
        title=CHAPTER_FIG_TITLES["2_7"],
    )


def fig_2_8() -> str:
    ax_lines, ax_labels = axes_xy(
        76.0,
        196.0,
        32.0,
        396.0,
        20.0,
        224.0,
        x_label="t",
        y_label="s",
        origin_label="0",
        origin_dx=-16.0,
        origin_dy=17.0,
    )
    tick_1 = '    <line x1="72.0" y1="78.0" x2="80.0" y2="78.0" class="ax" />'
    axes = f"{ax_lines}\n{tick_1}"
    regions = '    <rect x="136.0" y="78.0" width="190.0" height="118.0" class="f-blue" />\n    <rect x="136.0" y="78.0" width="190.0" height="118.0" class="f-stipple" />'
    curves = (
        '    <rect x="136.0" y="78.0" width="190.0" height="118.0" class="c-blue" />'
    )
    labels = "\n".join(
        [
            ax_labels,
            math_label(58.0, 83.0, "1", italic=False),
            math_label(131.0, 215.0, "a"),
            math_label(321.0, 215.0, "b"),
            math_label(224.0, 142.0, "K"),
        ]
    )
    return svg_figure(
        "0 0 440 240",
        axes=axes,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_8",
        title=CHAPTER_FIG_TITLES["2_8"],
    )


def fig_2_9() -> str:
    ox, oy = 215.0, 182.0
    r_out, r_in = 144.0, 28.0
    axes = '    <line x1="26.0" y1="182.0" x2="412.0" y2="182.0" class="ax" marker-end="url(#arr-axis)" />'
    d_cell = (
        f"M {ox - r_out:.1f} {oy:.1f} "
        f"A {r_out:.1f} {r_out:.1f} 0 0 1 {ox + r_out:.1f} {oy:.1f} "
        f"L {ox + r_in:.1f} {oy:.1f} "
        f"A {r_in:.1f} {r_in:.1f} 0 0 0 {ox - r_in:.1f} {oy:.1f} Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_cell}" class="f-blue" />',
            f'    <path d="{d_cell}" class="f-stipple" />',
        ]
    )
    curves = f'    <path d="{d_cell}" class="c-blue" />'
    labels = "\n".join(
        [
            point_dot(ox, oy),
            math_label(52.0, 205.0, "−R"),
            math_label(166.0, 204.0, "−ε"),
            math_label(210.0, 205.0, "0", italic=False),
            math_label(240.0, 204.0, "ε"),
            math_label(352.0, 205.0, "R"),
            math_label(406.0, 202.0, "x"),
            math_label(192.0, 108.0, "Γ", tail="(K)"),
        ]
    )
    return svg_figure(
        "0 0 440 230",
        axes=axes,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_9",
        title=CHAPTER_FIG_TITLES["2_9"],
    )


def fig_2_10() -> str:
    ax_c, lbl_c = axes_xy(
        44.0,
        196.0,
        18.0,
        214.0,
        22.0,
        218.0,
        x_label="x",
        y_label="iy",
        origin_label="0",
    )
    ax_d, lbl_d = axes_xy(
        274.0,
        196.0,
        248.0,
        456.0,
        22.0,
        218.0,
        x_label="x",
        y_label="iy",
        origin_label="0",
    )
    ticks = '    <line x1="74.0" y1="192.0" x2="74.0" y2="200.0" class="ax" />\n    <line x1="182.0" y1="192.0" x2="182.0" y2="200.0" class="ax" />\n    <line x1="304.0" y1="192.0" x2="304.0" y2="200.0" class="ax" />\n    <line x1="416.0" y1="192.0" x2="416.0" y2="200.0" class="ax" />'
    axes = f"{ax_c}\n{ax_d}\n{ticks}"
    d_c = (
        "M 74.0 122.0 "
        "C 92.0 104.0, 106.0 86.0, 124.0 88.0 "
        "C 146.0 92.0, 162.0 102.0, 182.0 106.0 "
        "C 162.0 118.0, 146.0 156.0, 126.0 156.0 "
        "C 106.0 156.0, 90.0 136.0, 74.0 122.0 Z"
    )
    d_d = (
        "M 304.0 52.0 "
        "C 326.0 64.0, 344.0 74.0, 358.0 72.0 "
        "C 372.0 68.0, 382.0 68.0, 416.0 104.0 "
        "C 386.0 116.0, 366.0 148.0, 340.0 152.0 "
        "C 324.0 154.0, 314.0 150.0, 304.0 146.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_c}" class="f-blue" />',
            f'    <path d="{d_c}" class="f-stipple" />',
            f'    <path d="{d_d}" class="f-blue" />',
            f'    <path d="{d_d}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{d_c}" class="c-blue" />',
            f'    <path d="{d_d}" class="c-blue" />',
        ]
    )
    labels = "\n".join(
        [
            lbl_c,
            lbl_d,
            math_label(66.0, 30.0, "(c)", italic=False),
            math_label(296.0, 30.0, "(d)", italic=False),
            math_label(70.0, 214.0, "a"),
            math_label(178.0, 214.0, "b"),
            math_label(300.0, 214.0, "a"),
            math_label(412.0, 214.0, "b"),
            math_label(106.0, 126.0, "Γ", tail="(K)"),
            math_label(338.0, 112.0, "Γ", tail="(K)"),
            '    <text x="94.0" y="76.0" class="it" transform="rotate(14 94 76)">y = ψ(x)</text>',
            '    <text x="72.0" y="146.0" class="it" transform="rotate(32 72 146)">y = φ(x)</text>',
            '    <text x="310.0" y="44.0" class="it" transform="rotate(20 310 44)">y = ψ(x)</text>',
            '    <text x="312.0" y="170.0" class="it" transform="rotate(-6 312 170)">y = φ(x)</text>',
        ]
    )
    return svg_figure(
        "0 0 480 240",
        axes=axes,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_10",
        title=CHAPTER_FIG_TITLES["2_10"],
    )


def fig_2_11() -> str:
    ax_lines, ax_labels = axes_xy(
        248.0,
        172.0,
        24.0,
        368.0,
        20.0,
        214.0,
        x_label="x",
        y_label="iy",
        origin_label="0",
        origin_dx=-15.0,
        origin_dy=18.0,
    )
    d_semi = "M 56.0 172.0 A 96.0 96.0 0 0 1 248.0 172.0 Z"
    regions = "\n".join(
        [
            f'    <path d="{d_semi}" class="f-blue" />',
            f'    <path d="{d_semi}" class="f-stipple" />',
        ]
    )
    curves = f'    <path d="{d_semi}" class="c-blue" />'
    labels = "\n".join(
        [
            ax_labels,
            point_dot(152.0, 172.0, r=2.6),
            math_label(42.0, 192.0, "−2", italic=False),
            math_label(138.0, 192.0, "−1", italic=False),
            math_label(132.0, 130.0, "Γ", tail="(K)"),
        ]
    )
    return svg_figure(
        "0 0 420 230",
        axes=ax_lines,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_11",
        title=CHAPTER_FIG_TITLES["2_11"],
    )


def fig_2_12() -> str:
    ax_lines, ax_labels = axes_xy(
        78.0,
        198.0,
        28.0,
        408.0,
        20.0,
        232.0,
        x_label="t",
        y_label="s",
        origin_label="0",
        origin_dx=-16.0,
        origin_dy=17.0,
    )
    tick_1 = '    <line x1="74.0" y1="82.0" x2="82.0" y2="82.0" class="ax" />'
    axes = f"{ax_lines}\n{tick_1}"
    regions = '    <rect x="138.0" y="82.0" width="200.0" height="116.0" class="f-blue" />\n    <rect x="138.0" y="82.0" width="200.0" height="116.0" class="f-stipple" />'
    curves = (
        '    <rect x="138.0" y="82.0" width="200.0" height="116.0" class="c-blue" />'
    )
    labels = "\n".join(
        [
            ax_labels,
            math_label(58.0, 87.0, "1", italic=False),
            math_label(133.0, 218.0, "a"),
            math_label(333.0, 218.0, "b"),
            math_label(232.0, 146.0, "E"),
            math_label(228.0, 218.0, "L", sub="1", color="#1e3a8a"),
            math_label(346.0, 148.0, "L", sub="2", color="#1e3a8a"),
            math_label(228.0, 70.0, "L", sub="3", color="#1e3a8a"),
            math_label(106.0, 146.0, "L", sub="4", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 440 250",
        axes=axes,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_12",
        title=CHAPTER_FIG_TITLES["2_12"],
    )


def fig_2_13() -> str:
    d_cell = (
        "M 56.0 126.0 "
        "C 104.0 150.0, 152.0 206.0, 198.0 206.0 "
        "C 246.0 206.0, 294.0 150.0, 348.0 108.0 "
        "C 286.0 96.0, 228.0 48.0, 178.0 48.0 "
        "C 132.0 48.0, 96.0 96.0, 56.0 126.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_cell}" class="f-blue" />',
            f'    <path d="{d_cell}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{d_cell}" class="c-blue" />',
            tangent_arrow(258.0, 174.0, 0.76, -0.65, marker="arr-blue"),
            tangent_arrow(232.0, 66.0, -0.85, -0.52, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            math_label(172.0, 134.0, "Γ", tail="(E)"),
            math_label(184.0, 36.0, "C", sub="3", color="#1e3a8a"),
            math_label(190.0, 232.0, "C", sub="1", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 400 250",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_13",
        title=CHAPTER_FIG_TITLES["2_13"],
    )


def fig_2_14() -> str:
    d_cell = (
        "M 154.0 238.0 "
        "C 192.0 222.0, 246.0 236.0, 326.0 276.0 "
        "C 374.0 288.0, 412.0 280.0, 446.0 262.0 "
        "C 402.0 198.0, 386.0 128.0, 434.0 42.0 "
        "C 372.0 50.0, 326.0 82.0, 280.0 76.0 "
        "C 214.0 66.0, 146.0 10.0, 76.0 26.0 "
        "C 122.0 72.0, 112.0 132.0, 114.0 178.0 "
        "C 118.0 202.0, 134.0 222.0, 154.0 238.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_cell}" class="f-blue" />',
            f'    <path d="{d_cell}" class="f-stipple" />',
        ]
    )
    d_g13 = (
        "M 114.0 178.0 "
        "C 172.0 152.0, 224.0 156.0, 272.0 172.0 "
        "C 324.0 190.0, 368.0 208.0, 405.0 195.0"
    )
    d_cg = (
        "M 326.0 276.0 "
        "C 292.0 234.0, 274.0 196.0, 272.0 172.0 "
        "C 270.0 140.0, 282.0 108.0, 280.0 76.0"
    )
    curves = "\n".join(
        [
            f'    <path d="{d_cell}" class="c-blue" />',
            tangent_arrow(242.0, 240.0, 0.91, 0.41, marker="arr-blue"),
            tangent_arrow(402.0, 122.0, 0.14, -0.99, marker="arr-blue"),
            tangent_arrow(188.0, 44.0, -0.91, -0.41, marker="arr-blue"),
            tangent_arrow(114.0, 106.0, 0.02, 1.0, marker="arr-blue"),
            f'    <path d="{d_g13}" class="c-green" />',
            tangent_arrow(210.0, 159.0, 0.99, 0.08, marker="arr-green"),
            f'    <path d="{d_cg}" class="c-amber" />',
            tangent_arrow(273.0, 140.0, 0.12, -0.99, marker="arr-amber"),
            arrow_line(326.0, 276.0, 382.0, 290.0, cls="c-main", marker="arr"),
            arrow_line(326.0, 276.0, 290.0, 230.0, cls="c-main", marker="arr"),
            arc_path(
                326.0,
                276.0,
                32.0,
                -14.0,
                128.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
            arrow_line(280.0, 76.0, 226.0, 68.0, cls="c-main", marker="arr"),
            arrow_line(280.0, 76.0, 270.0, 120.0, cls="c-main", marker="arr"),
            arc_path(
                280.0,
                76.0,
                28.0,
                171.0,
                257.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
            arrow_line(114.0, 178.0, 130.0, 230.0, cls="c-main", marker="arr"),
            arrow_line(114.0, 178.0, 162.0, 152.0, cls="c-main", marker="arr"),
            arc_path(
                114.0,
                178.0,
                30.0,
                -73.0,
                28.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(114.0, 178.0),
            point_dot(280.0, 76.0),
            point_dot(326.0, 276.0),
            math_label(18.0, 184.0, "Γ", tail="(a, 1/3)"),
            math_label(256.0, 60.0, "Γ", tail="(c, 1)"),
            math_label(278.0, 304.0, "Γ", tail="(c, 0)"),
            math_label(198.0, 144.0, "γ", sub="1/3", color="#047857"),
            math_label(284.0, 146.0, "", sub="c", tail="γ", color="#b45309"),
            math_label(228.0, 266.0, "C", sub="1", color="#1e3a8a"),
            math_label(410.0, 132.0, "C", sub="2", color="#1e3a8a"),
            math_label(186.0, 30.0, "C", sub="3", color="#1e3a8a"),
            math_label(84.0, 110.0, "C", sub="4", color="#1e3a8a"),
            math_label(342.0, 246.0, "θ"),
            math_label(236.0, 96.0, "ψ"),
            math_label(144.0, 198.0, "ω"),
        ]
    )
    return svg_figure(
        "0 0 480 320",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_14",
        title=CHAPTER_FIG_TITLES["2_14"],
    )


def fig_2_15() -> str:
    ax_lines, ax_labels = axes_xy(
        316.0,
        196.0,
        24.0,
        426.0,
        18.0,
        242.0,
        x_label="x",
        y_label="iy",
        origin_label="0",
        origin_dx=-15.0,
        origin_dy=18.0,
    )
    d_semi = "M 96.0 196.0 A 110.0 110.0 0 0 1 316.0 196.0 Z"
    regions = "\n".join(
        [
            f'    <path d="{d_semi}" class="f-blue" />',
            f'    <path d="{d_semi}" class="f-stipple" />',
        ]
    )
    d_cg = "M 176.0 196.0 A 70.0 70.0 0 0 1 316.0 196.0"
    curves = "\n".join(
        [
            f'    <path d="{d_semi}" class="c-blue" />',
            tangent_arrow(206.0, 86.0, -1.0, 0.0, marker="arr-blue"),
            tangent_arrow(146.0, 196.0, 1.0, 0.0, marker="arr-blue"),
            mid_arrow_path(
                "M 135.3 111.7 L 316.0 196.0",
                180.0,
                132.6,
                0.906,
                0.423,
                cls="c-green",
                marker="arr-green",
            ),
            f'    <path d="{d_cg}" class="c-amber" />',
            tangent_arrow(191.0, 151.0, 0.64, -0.77, marker="arr-amber"),
            arrow_line(135.3, 111.7, 98.0, 143.0, cls="c-main", marker="arr"),
            arc_path(
                135.3,
                111.7,
                26.0,
                220.0,
                335.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
            arrow_line(176.0, 196.0, 176.0, 148.0, cls="c-main", marker="arr"),
            arc_path(
                176.0,
                196.0,
                24.0,
                0.0,
                90.0,
                cls="c-sub",
                ccw=True,
                arrow_mid=True,
                marker="arr",
            ),
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            math_label(80.0, 218.0, "−2", italic=False),
            math_label(140.0, 220.0, "C", sub="1", color="#1e3a8a"),
            math_label(196.0, 72.0, "C", sub="4", color="#1e3a8a"),
            math_label(184.0, 116.0, "γ", sub="1/3", color="#047857"),
            math_label(178.0, 142.0, "", sub="c", tail="γ", color="#b45309"),
            math_label(130.0, 134.0, "ω"),
            math_label(196.0, 182.0, "θ"),
        ]
    )
    return svg_figure(
        "0 0 460 260",
        axes=ax_lines,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_15",
        title=CHAPTER_FIG_TITLES["2_15"],
    )


def fig_2_16() -> str:
    cx, cy, r = 200.0, 160.0, 128.0
    x0, x1 = 158.0, 242.0
    y0, y1 = 118.0, 202.0
    regions = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-blue" />',
            f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" class="f-amber" opacity="0.55" />',
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="c-blue" />',
            f'    <line x1="{x0:.1f}" y1="{y1:.1f}" x2="{x0:.1f}" y2="39.0" class="c-blue" />',
            f'    <line x1="{x0:.1f}" y1="{y0:.1f}" x2="321.0" y2="{y0:.1f}" class="c-blue" />',
            f'    <line x1="{x1:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="281.0" class="c-blue" />',
            f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="79.0" y2="{y1:.1f}" class="c-blue" />',
        ]
    )
    labels = "\n".join(
        [
            math_label(172.0, 166.0, "Γ", sub="1", tail="(K₁)"),
            math_label(172.0, 250.0, "Γ", sub="2", tail="(K₂)"),
            math_label(88.0, 140.0, "Γ", sub="3", tail="(K₃)"),
            math_label(202.0, 84.0, "Γ", sub="4", tail="(K₄)"),
            math_label(256.0, 188.0, "Γ", sub="5", tail="(K₅)"),
            math_label(152.0, 222.0, "0", italic=False),
            math_label(248.0, 212.0, "1", italic=False),
            math_label(144.0, 122.0, "i"),
            math_label(184.0, 224.0, "|C", sub="12", tail="|"),
            math_label(100.0, 224.0, "|C", sub="32", tail="|"),
            math_label(114.0, 166.0, "|C", sub="31", tail="|"),
        ]
    )
    return svg_figure(
        "0 0 400 320",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_16",
        title=CHAPTER_FIG_TITLES["2_16"],
    )


def fig_2_17() -> str:
    ox, oy, d = 44.0, 300.0, 38.0
    ax_lines, ax_labels = axes_xy(
        ox,
        oy,
        18.0,
        452.0,
        16.0,
        324.0,
        x_label="x",
        y_label="iy",
        origin_label="0",
        origin_dx=-16.0,
        origin_dy=18.0,
    )
    grid_lines: list[str] = [ax_lines]
    for h in range(1, 11):
        xh = ox + h * d
        grid_lines.append(
            f'    <line x1="{xh:.1f}" y1="20.0" x2="{xh:.1f}" y2="318.0" class="c-sub" />'
        )
    for k in range(1, 8):
        yk = oy - k * d
        grid_lines.append(
            f'    <line x1="22.0" y1="{yk:.1f}" x2="444.0" y2="{yk:.1f}" class="c-sub" />'
        )
    axes = "\n".join(grid_lines)

    d_dom = (
        "M 110.0 166.0 "
        "C 108.0 132.0, 128.0 96.0, 168.0 74.0 "
        "C 208.0 52.0, 266.0 46.0, 316.0 58.0 "
        "C 356.0 68.0, 376.0 98.0, 366.0 136.0 "
        "C 356.0 162.0, 358.0 176.0, 368.0 198.0 "
        "C 376.0 218.0, 364.0 250.0, 336.0 266.0 "
        "C 312.0 278.0, 286.0 276.0, 272.0 262.0 "
        "C 262.0 254.0, 252.0 254.0, 242.0 264.0 "
        "C 234.0 270.0, 224.0 264.0, 214.0 256.0 "
        "C 204.0 254.0, 196.0 268.0, 184.0 264.0 "
        "C 164.0 258.0, 144.0 246.0, 128.0 220.0 "
        "C 114.0 198.0, 110.0 182.0, 110.0 166.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_dom}" class="f-blue" />',
            f'    <path d="{d_dom}" class="f-stipple" />',
        ]
    )
    sub_segs = "\n".join(
        [
            f'    <line x1="120.0" y1="204.0" x2="{ox + 3 * d:.1f}" y2="204.0" class="c-blue" />',
            '    <line x1="132.0" y1="148.0" x2="132.0" y2="110.0" class="c-blue" />',
            '    <line x1="178.0" y1="110.0" x2="178.0" y2="72.0" class="c-blue" />',
            f'    <line x1="{ox + 7 * d:.1f}" y1="88.0" x2="{ox + 8 * d:.1f}" y2="88.0" class="c-blue" />',
            f'    <line x1="{ox + 6 * d:.1f}" y1="262.0" x2="340.0" y2="262.0" class="c-blue" />',
            '    <line x1="334.0" y1="224.0" x2="334.0" y2="262.0" class="c-blue" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{d_dom}" class="c-blue" />',
            tangent_arrow(212.0, 56.0, -0.98, 0.18, marker="arr-blue"),
            sub_segs,
        ]
    )
    labels = "\n".join(
        [
            ax_labels,
            math_label(48.0, 286.0, "Q", sub="00", size=13.5),
            math_label(86.0, 286.0, "Q", sub="10", size=13.5),
            math_label(124.0, 286.0, "Q", sub="20", size=13.5),
            math_label(48.0, 248.0, "Q", sub="01", size=13.5),
            math_label(86.0, 248.0, "Q", sub="11", size=13.5),
            math_label(124.0, 248.0, "Q", sub="21", size=13.5),
            math_label(48.0, 210.0, "Q", sub="02", size=13.5),
            math_label(86.0, 210.0, "Q", sub="12", size=13.5),
            math_label(314.0, 104.0, "Q", sub="75", size=13.5),
            math_label(238.0, 174.0, "[D]"),
            math_label(200.0, 46.0, "C", color="#1e3a8a"),
            math_label(166.0, 284.0, "R", sub="1", size=14.0),
            math_label(204.0, 284.0, "R", sub="2", size=14.0),
            math_label(242.0, 284.0, "R", sub="3", size=14.0),
            math_label(356.0, 174.0, "R", sub="4", size=14.0),
        ]
    )
    return svg_figure(
        "0 0 480 340",
        axes=axes,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_17",
        title=CHAPTER_FIG_TITLES["2_17"],
        show_grid=False,
    )


def fig_2_18() -> str:
    d_left_fill = (
        "M 60.0 22.0 L 156.0 22.0 L 156.0 122.0 "
        "C 138.0 116.0, 122.0 108.0, 108.0 108.0 "
        "C 92.0 108.0, 76.0 116.0, 60.0 122.0 Z"
    )
    d_right_fill = (
        "M 254.0 66.0 L 363.0 66.0 "
        "C 354.0 82.0, 350.0 98.0, 350.0 114.0 "
        "C 350.0 130.0, 354.0 146.0, 363.0 162.0 "
        "L 254.0 162.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_left_fill}" class="f-blue" />',
            f'    <path d="{d_left_fill}" class="f-stipple" />',
            f'    <path d="{d_right_fill}" class="f-blue" />',
            f'    <path d="{d_right_fill}" class="f-stipple" />',
        ]
    )
    d_c_left = (
        "M 32.0 118.0 "
        "C 44.0 124.0, 52.0 125.0, 60.0 122.0 "
        "C 76.0 116.0, 92.0 108.0, 108.0 108.0 "
        "C 122.0 108.0, 138.0 116.0, 156.0 122.0 "
        "C 166.0 125.0, 176.0 122.0, 186.0 117.0"
    )
    d_c_right = (
        "M 374.0 44.0 "
        "C 368.0 54.0, 365.0 60.0, 363.0 66.0 "
        "C 354.0 82.0, 350.0 98.0, 350.0 114.0 "
        "C 350.0 130.0, 354.0 146.0, 363.0 162.0 "
        "C 366.0 168.0, 370.0 176.0, 375.0 184.0"
    )
    curves = "\n".join(
        [
            '    <rect x="60.0" y="22.0" width="96.0" height="96.0" class="c-main" />',
            '    <rect x="60.0" y="118.0" width="96.0" height="96.0" class="c-main" />',
            f'    <path d="{d_c_left}" class="c-blue" />',
            '    <rect x="254.0" y="66.0" width="96.0" height="96.0" class="c-main" />',
            '    <rect x="350.0" y="66.0" width="96.0" height="96.0" class="c-main" />',
            f'    <path d="{d_c_right}" class="c-blue" />',
        ]
    )
    labels = "\n".join(
        [
            math_label(90.0, 74.0, "Q", sub="h'k'"),
            math_label(94.0, 170.0, "Q", sub="hk"),
            math_label(176.0, 138.0, "C", color="#1e3a8a"),
            math_label(288.0, 120.0, "Q", sub="hk"),
            math_label(384.0, 120.0, "Q", sub="h'k'"),
            math_label(368.0, 204.0, "C", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 470 230",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_18",
        title=CHAPTER_FIG_TITLES["2_18"],
    )


def fig_2_19() -> str:
    d_s1 = "M 48.0 36.0 L 102.0 36.0 L 102.0 114.0 L 24.0 114.0 L 24.0 72.0 Q 34.0 52.0 48.0 36.0 Z"
    d_s2 = "M 146.0 36.0 L 194.0 36.0 Q 208.0 52.0 224.0 66.0 L 224.0 114.0 L 146.0 114.0 Z"
    d_s3 = "M 268.0 36.0 L 346.0 36.0 L 346.0 86.0 Q 332.0 102.0 318.0 114.0 L 268.0 114.0 Z"
    d_s4 = "M 390.0 36.0 L 468.0 36.0 L 468.0 114.0 L 418.0 114.0 Q 402.0 102.0 390.0 90.0 Z"
    regions = "\n".join(
        [
            f'    <path d="{d_s1}" class="f-blue" />',
            f'    <path d="{d_s1}" class="f-stipple" />',
            f'    <path d="{d_s2}" class="f-blue" />',
            f'    <path d="{d_s2}" class="f-stipple" />',
            f'    <path d="{d_s3}" class="f-blue" />',
            f'    <path d="{d_s3}" class="f-stipple" />',
            f'    <path d="{d_s4}" class="f-blue" />',
            f'    <path d="{d_s4}" class="f-stipple" />',
        ]
    )
    curves = '    <rect x="24.0" y="36.0" width="78.0" height="78.0" class="c-main" />\n    <line x1="48.0" y1="36.0" x2="48.0" y2="114.0" class="c-blue" />\n    <path d="M 12.0 92.0 Q 34.0 50.0 68.0 20.0" class="c-blue" />\n    <rect x="146.0" y="36.0" width="78.0" height="78.0" class="c-main" />\n    <line x1="146.0" y1="66.0" x2="224.0" y2="66.0" class="c-blue" />\n    <path d="M 182.0 18.0 Q 208.0 54.0 242.0 78.0" class="c-blue" />\n    <rect x="268.0" y="36.0" width="78.0" height="78.0" class="c-main" />\n    <line x1="318.0" y1="36.0" x2="318.0" y2="114.0" class="c-blue" />\n    <path d="M 300.0 128.0 Q 334.0 104.0 358.0 66.0" class="c-blue" />\n    <rect x="390.0" y="36.0" width="78.0" height="78.0" class="c-main" />\n    <line x1="390.0" y1="90.0" x2="468.0" y2="90.0" class="c-blue" />\n    <path d="M 378.0 70.0 Q 400.0 104.0 438.0 128.0" class="c-blue" />'
    return svg_figure(
        "0 0 490 150",
        regions=regions,
        curves=curves,
        fig_id="2_19",
        title=CHAPTER_FIG_TITLES["2_19"],
    )


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "2_1": fig_2_1,
    "2_2": fig_2_2,
    "2_3": fig_2_3,
    "2_4": fig_2_4,
    "2_5": fig_2_5,
    "2_6": fig_2_6,
    "2_7": fig_2_7,
    "2_8": fig_2_8,
    "2_9": fig_2_9,
    "2_10": fig_2_10,
    "2_11": fig_2_11,
    "2_12": fig_2_12,
    "2_13": fig_2_13,
    "2_14": fig_2_14,
    "2_15": fig_2_15,
    "2_16": fig_2_16,
    "2_17": fig_2_17,
    "2_18": fig_2_18,
    "2_19": fig_2_19,
}
