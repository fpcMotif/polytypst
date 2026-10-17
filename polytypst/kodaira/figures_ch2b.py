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


def _double_arrow_label(
    x1: float,
    x2: float,
    y: float,
    text_svg: str,
    gap: float = 24.0,
    cls: str = "c-main",
    marker: str = "arr",
) -> tuple[str, str]:
    xm = 0.5 * (x1 + x2)
    c_parts = [
        arrow_line(xm - gap, y, x1 + 2.0, y, cls=cls, marker=marker),
        arrow_line(xm + gap, y, x2 - 2.0, y, cls=cls, marker=marker),
    ]
    return "\n".join(c_parts), text_svg


def fig_2_20() -> str:
    ax, ax_lbl = axes_xy(85, 240, 20, 435, 20, 290)
    c_pts = [
        (22.0, 258.0),
        (85.0, 204.0),
        (140.0, 160.0),
        (178.0, 146.0),
        (230.0, 158.0),
        (256.0, 148.0),
        (310.0, 102.0),
        (356.0, 52.0),
        (384.0, 18.0),
    ]
    d_outer = (
        "M 22.0 258.0 "
        "C 52.0 232.0, 70.0 216.0, 85.0 204.0 "
        "C 108.0 185.0, 124.0 170.0, 140.0 160.0 "
        "C 155.0 150.0, 166.0 146.0, 178.0 146.0 "
        "C 196.0 146.0, 214.0 158.0, 230.0 158.0 "
        "C 241.0 158.0, 248.0 153.0, 256.0 148.0 "
        "C 278.0 134.0, 294.0 118.0, 310.0 102.0 "
        "C 332.0 80.0, 362.0 46.0, 384.0 18.0 "
        "L 140.0 18.0 "
        "C 72.0 34.0, 26.0 112.0, 22.0 258.0 Z"
    )
    u_plus = (
        "M 140.0 160.0 "
        "C 155.0 150.0, 166.0 146.0, 178.0 146.0 "
        "C 196.0 146.0, 214.0 158.0, 230.0 158.0 "
        "C 241.0 158.0, 248.0 153.0, 256.0 148.0 "
        "C 278.0 134.0, 294.0 118.0, 310.0 102.0 "
        "L 310.0 18.0 L 140.0 18.0 Z"
    )
    u_minus = (
        "M 140.0 160.0 "
        "C 155.0 150.0, 166.0 146.0, 178.0 146.0 "
        "C 196.0 146.0, 214.0 158.0, 230.0 158.0 "
        "C 241.0 158.0, 248.0 153.0, 256.0 148.0 "
        "C 278.0 134.0, 294.0 118.0, 310.0 102.0 "
        "L 310.0 284.0 L 140.0 284.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_outer}" class="f-blue" />',
            f'    <path d="{d_outer}" class="f-stipple" opacity="0.55" />',
            f'    <path d="{u_plus}" class="f-blue" />',
            f'    <path d="{u_plus}" class="f-stipple" />',
            f'    <path d="{u_minus}" class="f-amber" />',
            f'    <path d="{u_minus}" class="f-stipple" />',
        ]
    )
    w_arr, w_lbl = _double_arrow_label(
        140.0,
        310.0,
        268.0,
        math_label(225.0, 273.0, "2δ", tail="(1)", italic=False, anchor="middle"),
        gap=26.0,
    )
    curves = "\n".join(
        [
            '    <line x1="140.0" y1="18.0" x2="140.0" y2="284.0" class="c-dash" />',
            '    <line x1="310.0" y1="18.0" x2="310.0" y2="284.0" class="c-dash" />',
            '    <line x1="256.0" y1="286.0" x2="256.0" y2="18.0" class="c-main" />',
            tangent_arrow(256.0, 92.0, 0.0, -1.0, marker="arr"),
            smooth_curve(
                c_pts, cls="c-blue", arrow_indices=[(6, True)], marker="arr-blue"
            ),
            w_arr,
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            point_dot(230.0, 158.0, color="#1e3a8a"),
            point_dot(256.0, 148.0, color="#0f172a", r=2.8),
            math_label(106.0, 102.0, "D"),
            math_label(184.0, 88.0, "U", sup="+", tail="(ζ)"),
            math_label(184.0, 208.0, "U", sup="−", tail="(ζ)"),
            math_label(224.0, 178.0, "ζ"),
            math_label(264.0, 38.0, "l", sub="x"),
            math_label(263.0, 156.0, "x + iφ(x)"),
            math_label(348.0, 88.0, "C", color="#1e3a8a"),
            w_lbl,
        ]
    )
    return svg_figure(
        "0 0 460 305",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_20",
        title=CHAPTER_FIG_TITLES["2_20"],
    )


def fig_2_21() -> str:
    ax, ax_lbl = axes_xy(70, 245, 20, 330, 18, 286)
    regions = (
        '    <rect x="70.0" y="53.0" width="96.0" height="96.0" class="f-blue" opacity="0.45" />\n'
        '    <rect x="70.0" y="149.0" width="96.0" height="96.0" class="f-amber" opacity="0.45" />'
    )
    c_pts = [
        (26.0, 160.0),
        (70.0, 153.0),
        (94.0, 149.0),
        (128.0, 145.0),
        (166.0, 149.0),
        (225.0, 155.0),
        (320.0, 137.0),
    ]
    curves = "\n".join(
        [
            '    <rect x="70.0" y="53.0" width="96.0" height="192.0" class="c-main" />',
            '    <line x1="70.0" y1="149.0" x2="166.0" y2="149.0" class="c-main" />',
            '    <line x1="30.0" y1="173.4" x2="318.0" y2="63.6" class="c-red" />',
            '    <line x1="26.0" y1="139.8" x2="320.0" y2="179.5" class="c-green" />',
            smooth_curve(c_pts, cls="c-blue"),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            point_dot(94.0, 149.0, color="#1e3a8a"),
            math_label(62.0, 58.0, "2iδ", anchor="end"),
            math_label(166.0, 263.0, "δ", anchor="middle"),
            math_label(106.0, 102.0, "Q", sub="01"),
            math_label(106.0, 204.0, "Q", sub="00"),
            math_label(88.0, 138.0, "ζ"),
            math_label(112.0, 167.0, "L"),
            math_label(170.0, 144.0, "y = φ(x)", color="#1e3a8a"),
            math_label(325.0, 142.0, "|C|", italic=False, color="#1e3a8a"),
            '    <text x="172.0" y="110.0" class="it" fill="#dc2626" transform="rotate(-20.8 172.0 110.0)">y = δ + (φ\'(ξ) + ε)(x − ξ)</text>',
            '    <text x="170.0" y="176.0" class="it" fill="#047857" transform="rotate(7.7 170.0 176.0)">y = δ + (φ\'(ξ) − ε)(x − ξ)</text>',
        ]
    )
    return svg_figure(
        "0 0 470 300",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_21",
        title=CHAPTER_FIG_TITLES["2_21"],
    )


def fig_2_22() -> str:
    ax, ax_lbl = axes_xy(105, 252, 30, 350, 18, 290)
    cell_d = (
        "M 105.0 58.0 L 245.0 58.0 L 245.0 160.0 "
        "C 215.0 150.0, 195.0 147.0, 175.0 147.0 "
        "C 152.0 147.0, 130.0 151.0, 105.0 158.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{cell_d}" class="f-blue" />',
            f'    <path d="{cell_d}" class="f-stipple" />',
        ]
    )
    c_pts = [
        (68.0, 171.0),
        (105.0, 158.0),
        (175.0, 147.0),
        (245.0, 160.0),
        (282.0, 172.0),
    ]
    curves = "\n".join(
        [
            '    <rect x="105.0" y="58.0" width="140.0" height="194.0" class="c-main" />',
            smooth_curve(c_pts, cls="c-blue"),
            tangent_arrow(186.0, 147.8, 1.0, 0.08, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            math_label(97.0, 63.0, "2iδ", anchor="end"),
            math_label(245.0, 270.0, "δ", anchor="middle"),
            math_label(175.0, 114.0, "[D] ∩ R", italic=False, anchor="middle"),
            math_label(175.0, 170.0, "y = φ(x)", anchor="middle", color="#1e3a8a"),
            math_label(287.0, 176.0, "C", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 390 305",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_22",
        title=CHAPTER_FIG_TITLES["2_22"],
    )


def fig_2_23() -> str:
    ax, ax_lbl = axes_xy(88, 242, 24, 370, 18, 282)
    cell_d = (
        "M 88.0 74.0 L 276.0 74.0 L 276.0 120.0 "
        "C 230.0 140.0, 198.0 151.0, 168.0 162.0 "
        "C 138.0 173.0, 112.0 184.0, 88.0 198.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{cell_d}" class="f-blue" />',
            f'    <path d="{cell_d}" class="f-stipple" />',
        ]
    )
    c_pts = [
        (52.0, 222.0),
        (88.0, 198.0),
        (168.0, 162.0),
        (276.0, 120.0),
        (332.0, 84.0),
    ]
    curves = "\n".join(
        [
            '    <rect x="88.0" y="74.0" width="188.0" height="168.0" class="c-main" />',
            smooth_curve(c_pts, cls="c-blue"),
            tangent_arrow(182.0, 156.5, 1.0, -0.40, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            point_dot(88.0, 198.0, color="#1e3a8a", r=2.8),
            point_dot(276.0, 120.0, color="#1e3a8a"),
            math_label(80.0, 79.0, "iδ", anchor="end"),
            math_label(80.0, 196.0, "iη", anchor="end"),
            math_label(276.0, 260.0, "δ", anchor="middle"),
            math_label(283.0, 136.0, "ζ", sub="1"),
            math_label(337.0, 86.0, "C", color="#1e3a8a"),
            math_label(
                168.0, 122.0, "[D] ∩ Q", sub="00", italic=False, anchor="middle"
            ),
            '    <text x="115.0" y="205.0" class="it" fill="#1e3a8a" transform="rotate(-22.0 115.0 205.0)">y = φ(x)</text>',
        ]
    )
    return svg_figure(
        "0 0 410 295",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_23",
        title=CHAPTER_FIG_TITLES["2_23"],
    )


def fig_2_24() -> str:
    ax_l, lbl_l = axes_xy(56, 214, 16, 240, 20, 252)
    ax_r, lbl_r = axes_xy(320, 214, 280, 504, 20, 252)

    reg_l_cell = (
        "M 56.0 68.0 L 140.0 68.0 L 140.0 214.0 C 118.0 182.0, 90.0 144.0, 56.0 122.0 Z"
    )
    reg_r_cell = "M 320.0 122.0 C 354.0 144.0, 382.0 182.0, 404.0 214.0 L 320.0 214.0 Z"
    regions = "\n".join(
        [
            f'    <path d="{reg_l_cell}" class="f-blue" />',
            f'    <path d="{reg_l_cell}" class="f-stipple" />',
            '    <rect x="140.0" y="68.0" width="44.0" height="146.0" class="f-amber" />',
            '    <rect x="140.0" y="68.0" width="44.0" height="146.0" class="f-stipple" />',
            f'    <path d="{reg_r_cell}" class="f-blue" />',
            f'    <path d="{reg_r_cell}" class="f-stipple" />',
        ]
    )
    c_left = [
        (30.0, 110.0),
        (56.0, 122.0),
        (102.0, 162.0),
        (140.0, 214.0),
        (178.0, 250.0),
        (206.0, 266.0),
    ]
    c_right = [(x + 264.0, y) for x, y in c_left]
    curves = "\n".join(
        [
            '    <rect x="56.0" y="68.0" width="128.0" height="146.0" class="c-main" />',
            '    <line x1="140.0" y1="68.0" x2="140.0" y2="214.0" class="c-main" />',
            smooth_curve(c_left, cls="c-blue"),
            tangent_arrow(102.0, 162.0, 0.72, 0.85, marker="arr-blue"),
            '    <rect x="320.0" y="68.0" width="128.0" height="146.0" class="c-main" />',
            smooth_curve(c_right, cls="c-blue"),
            tangent_arrow(366.0, 162.0, -0.72, -0.85, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            lbl_l,
            lbl_r,
            math_label(48.0, 73.0, "iδ", anchor="end"),
            math_label(48.0, 128.0, "iη", anchor="end"),
            math_label(138.0, 232.0, "ξ", anchor="middle"),
            math_label(184.0, 232.0, "δ", anchor="middle"),
            math_label(211.0, 270.0, "C", color="#1e3a8a"),
            math_label(132.0, 270.0, "ρ'(τ) &gt; 0", anchor="middle"),
            math_label(312.0, 73.0, "iδ", anchor="end"),
            math_label(312.0, 128.0, "iη", anchor="end"),
            math_label(402.0, 232.0, "ξ", anchor="middle"),
            math_label(448.0, 232.0, "δ", anchor="middle"),
            math_label(475.0, 270.0, "C", color="#1e3a8a"),
            math_label(
                356.0,
                198.0,
                "[D] ∩ Q",
                sub="00",
                italic=False,
                anchor="middle",
                size=13.5,
            ),
            math_label(396.0, 270.0, "ρ'(τ) &lt; 0", anchor="middle"),
        ]
    )
    return svg_figure(
        "0 0 530 285",
        axes=f"{ax_l}\n{ax_r}",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_24",
        title=CHAPTER_FIG_TITLES["2_24"],
    )


def fig_2_25() -> str:
    cx, cy = 220.0, 195.0
    step = 17.0
    delta = 3.0 * step
    R_clip = 166.0

    grid_lines: list[str] = []
    for k in range(-9, 10):
        y = cy + k * step
        dy = abs(y - cy)
        if dy >= R_clip:
            continue
        xh = math.sqrt(max(0.0, R_clip * R_clip - dy * dy))
        x_left, x_right = cx - xh, cx + xh
        if abs(k) < 4.5 and (k % 3 != 0):
            grid_lines.append(
                f'    <line x1="{x_left:.1f}" y1="{y:.1f}" x2="{cx - 1.5 * delta:.1f}" y2="{y:.1f}" class="c-sub" />'
            )
            grid_lines.append(
                f'    <line x1="{cx + 1.5 * delta:.1f}" y1="{y:.1f}" x2="{x_right:.1f}" y2="{y:.1f}" class="c-sub" />'
            )
        else:
            cls = "c-main" if abs(k) <= 4.5 and k % 3 == 0 else "c-sub"
            grid_lines.append(
                f'    <line x1="{x_left:.1f}" y1="{y:.1f}" x2="{x_right:.1f}" y2="{y:.1f}" class="{cls}" />'
            )

    for h in range(-9, 10):
        x = cx + h * step
        dx = abs(x - cx)
        if dx >= R_clip:
            continue
        yh = math.sqrt(max(0.0, R_clip * R_clip - dx * dx))
        y_top, y_bot = cy - yh, cy + yh
        if abs(h) < 4.5 and (h % 3 != 0):
            grid_lines.append(
                f'    <line x1="{x:.1f}" y1="{y_top:.1f}" x2="{x:.1f}" y2="{cy - 1.5 * delta:.1f}" class="c-sub" />'
            )
            grid_lines.append(
                f'    <line x1="{x:.1f}" y1="{cy + 1.5 * delta:.1f}" x2="{x:.1f}" y2="{y_bot:.1f}" class="c-sub" />'
            )
        else:
            cls = "c-main" if abs(h) <= 4.5 and h % 3 == 0 else "c-sub"
            grid_lines.append(
                f'    <line x1="{x:.1f}" y1="{y_top:.1f}" x2="{x:.1f}" y2="{y_bot:.1f}" class="{cls}" />'
            )

    zx, zy = cx + 5.0, cy - 6.0
    sector_d = (
        f"M {zx:.1f} {zy:.1f} "
        "C 256.0 132.0, 304.0 78.0, 354.0 34.0 "
        "L 390.0 78.0 "
        "C 332.0 102.0, 278.0 142.0, 225.0 189.0 Z"
    )
    regions = "\n".join(
        [
            f'    <rect x="{cx - 1.5 * delta:.1f}" y="{cy - 1.5 * delta:.1f}" width="{3 * delta:.1f}" height="{3 * delta:.1f}" fill="#ffffff" opacity="0.72" />',
            f'    <path d="{sector_d}" class="f-blue" />',
            f'    <path d="{sector_d}" class="f-stipple" />',
        ]
    )
    c_jm1 = f"M 354.0 34.0 C 304.0 78.0, 256.0 132.0, {zx:.1f} {zy:.1f}"
    c_j = f"M {zx:.1f} {zy:.1f} C 278.0 142.0, 332.0 102.0, 390.0 78.0"
    d_arr, d_lbl = _double_arrow_label(
        cx - 0.5 * delta,
        cx + 0.5 * delta,
        cy + 1.0 * delta,
        math_label(cx, cy + 1.0 * delta + 5.0, "δ", anchor="middle"),
        gap=10.0,
    )
    curves = "\n".join(
        grid_lines
        + [
            f'    <rect x="{cx - 1.5 * delta:.1f}" y="{cy - 1.5 * delta:.1f}" width="{3 * delta:.1f}" height="{3 * delta:.1f}" class="c-main" />',
            mid_arrow_path(
                c_jm1, 255.0, 138.0, -0.62, 0.78, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                c_j, 268.0, 152.0, 0.76, -0.65, cls="c-blue", marker="arr-blue"
            ),
            d_arr,
        ]
    )
    labels = "\n".join(
        [
            point_dot(zx, zy, color="#1e3a8a"),
            math_label(zx - 18.0, zy + 12.0, "ζ", sub="j"),
            math_label(352.0, 26.0, "C", sub="j−1", color="#1e3a8a"),
            math_label(395.0, 82.0, "C", sub="j", color="#1e3a8a"),
            math_label(380.0, 56.0, "[D]", italic=False),
            d_lbl,
        ]
    )
    return svg_figure(
        "0 0 440 390",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_25",
        title=CHAPTER_FIG_TITLES["2_25"],
        show_grid=False,
    )


def fig_2_26() -> str:
    reg_5_l = (
        "M 68.0 26.0 L 132.0 26.0 L 132.0 96.0 C 112.0 84.0, 92.0 80.0, 68.0 76.0 Z"
    )
    reg_5_r = (
        "M 132.0 26.0 L 196.0 26.0 L 196.0 68.0 C 174.0 74.0, 154.0 84.0, 132.0 96.0 Z"
    )

    reg_6_tl = "M 296.0 26.0 L 360.0 26.0 L 360.0 96.0 L 296.0 96.0 Z"
    reg_6_bl = "M 296.0 96.0 L 360.0 96.0 C 354.0 116.0, 351.0 136.0, 348.0 154.0 L 296.0 154.0 Z"
    reg_6_tr = (
        "M 360.0 26.0 L 424.0 26.0 L 424.0 88.0 C 402.0 98.0, 382.0 100.0, 360.0 96.0 Z"
    )

    regions = "\n".join(
        [
            f'    <path d="{reg_5_l}" class="f-blue" />',
            f'    <path d="{reg_5_l}" class="f-stipple" />',
            f'    <path d="{reg_5_r}" class="f-amber" />',
            f'    <path d="{reg_5_r}" class="f-stipple" />',
            f'    <path d="{reg_6_tl}" class="f-blue" />',
            f'    <path d="{reg_6_tl}" class="f-stipple" />',
            f'    <path d="{reg_6_bl}" class="f-amber" />',
            f'    <path d="{reg_6_bl}" class="f-stipple" />',
            f'    <path d="{reg_6_tr}" class="f-green" />',
            f'    <path d="{reg_6_tr}" class="f-stipple" />',
        ]
    )

    c5_in = "M 34.0 58.0 C 50.0 68.0, 58.0 73.0, 68.0 76.0 C 92.0 80.0, 112.0 84.0, 132.0 96.0"
    c5_out = "M 132.0 96.0 C 154.0 84.0, 174.0 74.0, 196.0 68.0 C 208.0 65.0, 218.0 64.0, 228.0 64.0"

    c6_in = "M 332.0 188.0 C 340.0 174.0, 345.0 164.0, 348.0 154.0 C 351.0 136.0, 354.0 116.0, 360.0 96.0"
    c6_out = "M 360.0 96.0 C 382.0 100.0, 402.0 98.0, 424.0 88.0 C 438.0 80.0, 450.0 70.0, 464.0 66.0"

    curves = "\n".join(
        [
            '    <rect x="68.0" y="26.0" width="128.0" height="128.0" class="c-main" />',
            '    <line x1="132.0" y1="26.0" x2="132.0" y2="96.0" class="c-main" />',
            mid_arrow_path(
                c5_in, 94.0, 81.0, 0.96, 0.25, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                c5_out, 206.0, 66.0, 0.96, -0.22, cls="c-blue", marker="arr-blue"
            ),
            '    <rect x="296.0" y="26.0" width="128.0" height="128.0" class="c-main" />',
            '    <line x1="360.0" y1="26.0" x2="360.0" y2="96.0" class="c-main" />',
            '    <line x1="296.0" y1="96.0" x2="360.0" y2="96.0" class="c-main" />',
            mid_arrow_path(
                c6_in, 345.0, 163.0, 0.28, -0.96, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                c6_out, 442.0, 77.0, 0.88, -0.48, cls="c-blue", marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(132.0, 96.0, color="#1e3a8a"),
            point_dot(360.0, 96.0, color="#1e3a8a"),
            math_label(12.0, 48.0, "C", sub="j−1", color="#1e3a8a"),
            math_label(214.0, 52.0, "C", sub="j", color="#1e3a8a"),
            math_label(126.0, 118.0, "ζ", sub="j"),
            math_label(132.0, 186.0, "(5)", italic=False, anchor="middle"),
            math_label(296.0, 194.0, "C", sub="j−1", color="#1e3a8a"),
            math_label(468.0, 72.0, "C", sub="j", color="#1e3a8a"),
            math_label(342.0, 88.0, "ζ", sub="j"),
            math_label(368.0, 186.0, "(6)", italic=False, anchor="middle"),
        ]
    )
    return svg_figure(
        "0 0 500 210",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_26",
        title=CHAPTER_FIG_TITLES["2_26"],
    )


def fig_2_27() -> str:
    ax, ax_lbl = axes_xy(92, 222, 22, 425, 18, 294)
    u_strip = (
        "M 156.0 34.0 "
        "C 188.0 32.0, 222.0 35.0, 254.0 33.0 "
        "C 286.0 31.0, 320.0 35.0, 352.0 34.0 "
        "L 352.0 288.0 "
        "C 320.0 290.0, 286.0 286.0, 254.0 288.0 "
        "C 222.0 290.0, 188.0 286.0, 156.0 288.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{u_strip}" class="f-blue" />',
            f'    <path d="{u_strip}" class="f-stipple" />',
        ]
    )
    c_jm1 = "M 215.0 48.0 C 223.0 74.0, 221.0 104.0, 212.0 132.0 C 207.0 146.0, 206.0 153.0, 206.0 158.0"
    c_j = (
        "M 206.0 158.0 "
        "C 222.0 165.0, 238.0 169.0, 254.0 169.0 "
        "C 292.0 169.0, 326.0 148.0, 352.0 124.0 "
        "C 378.0 98.0, 402.0 66.0, 424.0 42.0"
    )
    arr_l, lbl_l = _double_arrow_label(
        156.0,
        254.0,
        268.0,
        math_label(205.0, 273.0, "δ", tail="(1)", italic=False, anchor="middle"),
        gap=20.0,
    )
    arr_r, lbl_r = _double_arrow_label(
        254.0,
        352.0,
        268.0,
        math_label(303.0, 273.0, "δ", tail="(1)", italic=False, anchor="middle"),
        gap=20.0,
    )
    curves = "\n".join(
        [
            '    <line x1="156.0" y1="34.0" x2="156.0" y2="288.0" class="c-dash" />',
            '    <line x1="352.0" y1="34.0" x2="352.0" y2="288.0" class="c-dash" />',
            '    <line x1="254.0" y1="222.0" x2="254.0" y2="284.0" class="c-dash" />',
            '    <line x1="206.0" y1="218.0" x2="206.0" y2="226.0" class="c-main" />',
            '    <line x1="254.0" y1="218.0" x2="254.0" y2="226.0" class="c-main" />',
            mid_arrow_path(
                c_jm1, 220.0, 82.0, -0.05, 1.0, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                c_j, 396.0, 72.0, 0.68, -0.73, cls="c-blue", marker="arr-blue"
            ),
            arr_l,
            arr_r,
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            point_dot(206.0, 158.0, color="#1e3a8a"),
            point_dot(254.0, 169.0, color="#0f172a"),
            math_label(226.0, 56.0, "C", sub="j−1", color="#1e3a8a"),
            math_label(429.0, 48.0, "C", sub="j", color="#1e3a8a"),
            math_label(256.0, 114.0, "U(ζ)", italic=True),
            math_label(182.0, 165.0, "ζ", sub="j"),
            math_label(250.0, 156.0, "ζ"),
            math_label(200.0, 244.0, "ξ", sub="j"),
            math_label(249.0, 244.0, "ξ"),
            lbl_l,
            lbl_r,
        ]
    )
    return svg_figure(
        "0 0 465 312",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_27",
        title=CHAPTER_FIG_TITLES["2_27"],
    )


def fig_2_28() -> str:
    ax, ax_lbl = axes_xy(72, 258, 20, 355, 18, 294)
    regions = (
        '    <rect x="72.0" y="63.0" width="195.0" height="195.0" class="f-blue" opacity="0.28" />\n'
        '    <rect x="137.0" y="128.0" width="65.0" height="65.0" class="f-amber" opacity="0.45" />'
    )
    c_m = "M 236.0 22.0 C 224.0 44.0, 218.0 63.0, 214.0 98.0 C 210.0 132.0, 200.0 156.0, 182.0 178.0"
    c_1 = "M 182.0 178.0 C 214.0 164.0, 242.0 138.0, 267.0 106.0 C 282.0 87.0, 296.0 76.0, 314.0 68.0"
    curves = "\n".join(
        [
            '    <rect x="72.0" y="63.0" width="195.0" height="195.0" class="c-main" />',
            '    <line x1="137.0" y1="63.0" x2="137.0" y2="258.0" class="c-sub" />',
            '    <line x1="202.0" y1="63.0" x2="202.0" y2="258.0" class="c-sub" />',
            '    <line x1="72.0" y1="128.0" x2="267.0" y2="128.0" class="c-sub" />',
            '    <line x1="72.0" y1="193.0" x2="267.0" y2="193.0" class="c-sub" />',
            mid_arrow_path(
                c_m, 222.0, 52.0, -0.32, 0.95, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                c_1, 284.0, 88.0, 0.78, -0.62, cls="c-blue", marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            point_dot(182.0, 178.0, color="#1e3a8a"),
            point_dot(267.0, 106.0, color="#0f172a", r=2.7),
            math_label(64.0, 68.0, "3iδ", anchor="end"),
            math_label(267.0, 276.0, "3δ", anchor="middle"),
            math_label(242.0, 26.0, "C", sub="m", color="#1e3a8a"),
            math_label(318.0, 72.0, "C", sub="1", color="#1e3a8a"),
            math_label(274.0, 114.0, "3δ + iy", sub="1"),
            math_label(274.0, 168.0, "L", sub="1"),
            math_label(162.0, 54.0, "L", sub="2"),
            math_label(46.0, 168.0, "L", sub="3"),
            math_label(162.0, 278.0, "L", sub="4"),
            math_label(164.0, 185.0, "ζ", sub="1"),
        ]
    )
    return svg_figure(
        "0 0 440 305",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_28",
        title=CHAPTER_FIG_TITLES["2_28"],
    )


def fig_2_29() -> str:
    ax_l, lbl_l = axes_xy(54, 222, 16, 252, 18, 262)
    ax_r, lbl_r = axes_xy(332, 222, 294, 530, 18, 262)

    reg_l_left = "M 54.0 64.0 L 110.0 64.0 L 110.0 222.0 L 54.0 222.0 Z"
    reg_l_top = "M 110.0 64.0 L 190.0 64.0 L 190.0 90.0 C 162.0 94.0, 136.0 112.0, 110.0 136.0 Z"
    reg_l_bot = "M 110.0 136.0 C 136.0 162.0, 162.0 182.0, 190.0 188.0 L 190.0 222.0 L 110.0 222.0 Z"

    reg_r_mid = (
        "M 388.0 136.0 "
        "C 414.0 112.0, 440.0 94.0, 468.0 90.0 "
        "L 468.0 188.0 "
        "C 440.0 182.0, 414.0 162.0, 388.0 136.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{reg_l_left}" class="f-blue" />',
            f'    <path d="{reg_l_left}" class="f-stipple" />',
            f'    <path d="{reg_l_top}" class="f-blue" />',
            f'    <path d="{reg_l_top}" class="f-stipple" />',
            f'    <path d="{reg_l_bot}" class="f-blue" />',
            f'    <path d="{reg_l_bot}" class="f-stipple" />',
            f'    <path d="{reg_r_mid}" class="f-blue" />',
            f'    <path d="{reg_r_mid}" class="f-stipple" />',
        ]
    )

    c1_l = "M 110.0 136.0 C 136.0 112.0, 162.0 94.0, 190.0 90.0 C 212.0 87.0, 228.0 76.0, 244.0 64.0"
    cm_l = "M 248.0 202.0 C 228.0 193.0, 210.0 191.0, 190.0 188.0 C 162.0 182.0, 136.0 162.0, 110.0 136.0"

    cm_r = "M 522.0 72.0 C 504.0 74.0, 488.0 86.0, 468.0 90.0 C 440.0 94.0, 414.0 112.0, 388.0 136.0"
    c1_r = "M 388.0 136.0 C 414.0 162.0, 440.0 182.0, 468.0 188.0 C 488.0 191.0, 506.0 191.0, 524.0 191.0"

    curves = "\n".join(
        [
            '    <rect x="54.0" y="64.0" width="136.0" height="158.0" class="c-main" />',
            '    <line x1="110.0" y1="64.0" x2="110.0" y2="222.0" class="c-main" />',
            '    <line x1="82.0" y1="222.0" x2="82.0" y2="168.0" class="c-main" stroke-width="2.6" />',
            '    <line x1="166.0" y1="260.0" x2="166.0" y2="20.0" class="c-main" />',
            tangent_arrow(166.0, 78.0, 0.0, -1.0, marker="arr"),
            tangent_arrow(166.0, 162.0, 0.0, -1.0, marker="arr"),
            mid_arrow_path(
                c1_l, 178.0, 92.5, 0.96, -0.22, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                cm_l, 150.0, 170.0, -0.82, -0.57, cls="c-blue", marker="arr-blue"
            ),
            '    <line x1="214.0" y1="60.0" x2="223.0" y2="78.0" class="c-sub" />',
            '    <line x1="224.0" y1="176.0" x2="217.0" y2="192.0" class="c-sub" />',
            '    <rect x="332.0" y="64.0" width="136.0" height="158.0" class="c-main" />',
            '    <line x1="388.0" y1="218.0" x2="388.0" y2="225.0" class="c-main" />',
            '    <line x1="444.0" y1="260.0" x2="444.0" y2="20.0" class="c-main" />',
            tangent_arrow(444.0, 78.0, 0.0, -1.0, marker="arr"),
            tangent_arrow(444.0, 162.0, 0.0, -1.0, marker="arr"),
            mid_arrow_path(
                cm_r, 430.0, 104.0, -0.86, 0.50, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                c1_r, 456.0, 185.0, 0.94, 0.34, cls="c-blue", marker="arr-blue"
            ),
            '    <line x1="490.0" y1="60.0" x2="498.0" y2="78.0" class="c-sub" />',
            '    <line x1="502.0" y1="172.0" x2="494.0" y2="190.0" class="c-sub" />',
        ]
    )
    labels = "\n".join(
        [
            lbl_l,
            lbl_r,
            point_dot(110.0, 136.0, color="#1e3a8a"),
            point_dot(388.0, 136.0, color="#1e3a8a"),
            math_label(46.0, 69.0, "3iδ", anchor="end"),
            math_label(92.0, 140.0, "ζ", sub="1"),
            math_label(78.0, 162.0, "z"),
            math_label(106.0, 240.0, "ξ", sub="1"),
            math_label(155.0, 240.0, "x"),
            math_label(190.0, 240.0, "3δ", anchor="middle"),
            math_label(162.0, 274.0, "l", sub="x"),
            math_label(182.0, 52.0, "y = φ", sub="1", tail="(x)"),
            math_label(192.0, 168.0, "y = φ", sub="m", tail="(x)"),
            math_label(248.0, 68.0, "C", sub="1", color="#1e3a8a"),
            math_label(252.0, 208.0, "C", sub="m", color="#1e3a8a"),
            math_label(324.0, 69.0, "3iδ", anchor="end"),
            math_label(370.0, 142.0, "ζ", sub="1"),
            math_label(384.0, 240.0, "ξ", sub="1"),
            math_label(433.0, 240.0, "x"),
            math_label(468.0, 240.0, "3δ", anchor="middle"),
            math_label(440.0, 274.0, "l", sub="x"),
            math_label(460.0, 52.0, "y = φ", sub="m", tail="(x)"),
            math_label(468.0, 166.0, "y = φ", sub="1", tail="(x)"),
            math_label(526.0, 76.0, "C", sub="m", color="#1e3a8a"),
            math_label(528.0, 195.0, "C", sub="1", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 565 285",
        axes=f"{ax_l}\n{ax_r}",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_29",
        title=CHAPTER_FIG_TITLES["2_29"],
    )


def fig_2_30() -> str:
    ax, ax_lbl = axes_xy(74, 264, 24, 386, 18, 298)
    reg_left = (
        "M 120.0 110.0 L 231.0 110.0 L 186.0 188.0 "
        "C 168.0 158.0, 130.0 138.0, 120.0 110.0 Z"
    )
    reg_right = (
        "M 231.0 110.0 L 284.0 110.0 L 284.0 172.0 "
        "C 246.0 174.0, 212.0 176.0, 186.0 188.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{reg_left}" class="f-blue" />',
            f'    <path d="{reg_left}" class="f-stipple" />',
            f'    <path d="{reg_right}" class="f-amber" />',
            f'    <path d="{reg_right}" class="f-stipple" />',
        ]
    )
    cm_path = (
        "M 146.0 24.0 "
        "C 132.0 54.0, 114.0 84.0, 120.0 110.0 "
        "C 130.0 138.0, 168.0 158.0, 186.0 188.0"
    )
    c1_path = (
        "M 186.0 188.0 "
        "C 212.0 176.0, 246.0 174.0, 284.0 172.0 "
        "C 322.0 168.0, 354.0 152.0, 384.0 134.0"
    )
    curves = "\n".join(
        [
            '    <rect x="74.0" y="110.0" width="210.0" height="154.0" class="c-main" />',
            '    <line x1="231.0" y1="110.0" x2="231.0" y2="264.0" class="c-main" />',
            '    <line x1="122.0" y1="298.0" x2="282.0" y2="22.0" class="c-red" />',
            mid_arrow_path(
                cm_path, 131.0, 56.0, -0.38, 0.92, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                c1_path, 352.0, 152.0, 0.88, -0.48, cls="c-blue", marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            point_dot(74.0, 188.0, color="#0f172a", r=2.8),
            point_dot(180.0, 264.0, color="#0f172a", r=2.8),
            point_dot(186.0, 188.0, color="#1e3a8a"),
            math_label(66.0, 115.0, "3iδ", anchor="end"),
            math_label(66.0, 193.0, "iη", sub="1", anchor="end"),
            math_label(175.0, 282.0, "ξ", sub="1"),
            math_label(224.0, 282.0, "x", sub="3"),
            math_label(284.0, 282.0, "3δ", anchor="middle"),
            math_label(162.0, 194.0, "ζ", sub="1"),
            math_label(140.0, 18.0, "C", sub="m", color="#1e3a8a"),
            math_label(388.0, 138.0, "C", sub="1", color="#1e3a8a"),
            math_label(264.0, 28.0, "l", color="#dc2626"),
            '    <text x="136.0" y="92.0" class="it" fill="#1e3a8a" transform="rotate(-68.0 136.0 92.0)">x = ψ<tspan font-size="10.5px" dy="3.2">m</tspan><tspan dy="-3.2">(y)</tspan></text>',
            '    <text x="226.0" y="96.0" class="it" fill="#dc2626" transform="rotate(-60.0 226.0 96.0)">x = λ(y)</text>',
            '    <text x="255.0" y="106.0" class="it" fill="#dc2626" transform="rotate(-60.0 255.0 106.0)">y = μ(x)</text>',
            '    <text x="304.0" y="185.0" class="it" fill="#1e3a8a" transform="rotate(-22.0 304.0 185.0)">y = φ<tspan font-size="10.5px" dy="3.2">1</tspan><tspan dy="-3.2">(x)</tspan></text>',
        ]
    )
    return svg_figure(
        "0 0 430 312",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_30",
        title=CHAPTER_FIG_TITLES["2_30"],
    )


def fig_2_31() -> str:
    d_total = (
        "M 38.0 176.0 "
        "C 82.0 156.0, 122.0 112.0, 158.0 70.0 "
        "C 176.0 52.0, 192.0 40.0, 208.0 32.0 "
        "C 224.0 24.0, 238.0 19.0, 250.0 16.0 "
        "C 272.0 11.0, 294.0 9.0, 312.0 9.0 "
        "C 324.0 45.0, 328.0 92.0, 326.0 156.0 "
        "C 324.0 218.0, 328.0 265.0, 320.0 304.0 "
        "C 292.0 304.0, 270.0 303.0, 250.0 302.0 "
        "C 214.0 299.0, 184.0 292.0, 158.0 282.0 "
        "C 112.0 262.0, 72.0 222.0, 38.0 176.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_total}" class="f-blue" />',
            f'    <path d="{d_total}" class="f-stipple" />',
            '    <rect x="158.0" y="122.0" width="92.0" height="94.0" class="f-amber" opacity="0.55" />',
        ]
    )
    outer_top = (
        "M 312.0 9.0 "
        "C 294.0 9.0, 272.0 11.0, 250.0 16.0 "
        "C 238.0 19.0, 224.0 24.0, 208.0 32.0 "
        "C 192.0 40.0, 176.0 52.0, 158.0 70.0 "
        "C 122.0 112.0, 82.0 156.0, 38.0 176.0"
    )
    outer_bot = (
        "M 38.0 176.0 "
        "C 72.0 222.0, 112.0 262.0, 158.0 282.0 "
        "C 184.0 292.0, 214.0 299.0, 250.0 302.0 "
        "C 270.0 303.0, 292.0 304.0, 320.0 304.0"
    )
    curves = "\n".join(
        [
            f'    <path d="{outer_top}" class="c-blue" />',
            f'    <path d="{outer_bot}" class="c-blue" />',
            tangent_arrow(182.0, 48.0, -0.78, 0.62, marker="arr-blue"),
            tangent_arrow(104.0, 126.0, -0.70, 0.71, marker="arr-blue"),
            tangent_arrow(96.0, 238.0, 0.72, 0.69, marker="arr-blue"),
            tangent_arrow(204.0, 296.0, 0.98, 0.18, marker="arr-blue"),
            tangent_arrow(288.0, 303.5, 1.0, 0.03, marker="arr-blue"),
            '    <line x1="158.0" y1="70.0" x2="158.0" y2="282.0" class="c-main" />',
            '    <line x1="208.0" y1="32.0" x2="208.0" y2="122.0" class="c-main" />',
            '    <line x1="250.0" y1="16.0" x2="250.0" y2="302.0" class="c-main" />',
            '    <line x1="208.0" y1="32.0" x2="320.0" y2="32.0" class="c-main" />',
            '    <line x1="158.0" y1="122.0" x2="326.0" y2="122.0" class="c-main" />',
            '    <line x1="158.0" y1="216.0" x2="325.0" y2="216.0" class="c-main" />',
            arrow_line(153.0, 110.0, 153.0, 94.0, cls="c-sub", marker="arr"),
            arrow_line(153.0, 178.0, 153.0, 160.0, cls="c-sub", marker="arr"),
            arrow_line(163.0, 160.0, 163.0, 178.0, cls="c-sub", marker="arr"),
            arrow_line(153.0, 260.0, 153.0, 242.0, cls="c-sub", marker="arr"),
            arrow_line(163.0, 242.0, 163.0, 260.0, cls="c-sub", marker="arr"),
            arrow_line(192.0, 127.0, 174.0, 127.0, cls="c-sub", marker="arr"),
            arrow_line(236.0, 127.0, 218.0, 127.0, cls="c-sub", marker="arr"),
            arrow_line(196.0, 211.0, 214.0, 211.0, cls="c-sub", marker="arr"),
            arrow_line(214.0, 221.0, 196.0, 221.0, cls="c-sub", marker="arr"),
            arrow_line(245.0, 178.0, 245.0, 160.0, cls="c-sub", marker="arr"),
            arrow_line(255.0, 160.0, 255.0, 178.0, cls="c-sub", marker="arr"),
            arrow_line(245.0, 260.0, 245.0, 242.0, cls="c-sub", marker="arr"),
        ]
    )
    labels = "\n".join(
        [
            math_label(52.0, 154.0, "C", sub="3", color="#1e3a8a"),
            math_label(166.0, 42.0, "C", sub="6", color="#1e3a8a"),
            math_label(194.0, 316.0, "C", sub="4", color="#1e3a8a"),
            math_label(278.0, 320.0, "C", sub="8", color="#1e3a8a"),
            math_label(82.0, 188.0, "Γ", sub="3", tail="(K)"),
            math_label(162.0, 92.0, "Γ", sub="6", tail="(K)", size=13.5),
            math_label(210.0, 84.0, "Γ", sub="7", tail="(K)", size=13.5),
            math_label(184.0, 174.0, "Γ", sub="5", tail="(K)"),
            math_label(184.0, 258.0, "Γ", sub="4", tail="(K)"),
            math_label(282.0, 174.0, "Γ", sub="9", tail="(K)"),
            math_label(282.0, 258.0, "Γ", sub="8", tail="(K)"),
            math_label(132.0, 108.0, "C", sub="36", size=13.0),
            math_label(132.0, 174.0, "C", sub="35", size=13.0),
            math_label(166.0, 174.0, "C", sub="53", size=13.0),
            math_label(132.0, 258.0, "C", sub="34", size=13.0),
            math_label(166.0, 258.0, "C", sub="43", size=13.0),
            math_label(174.0, 141.0, "C", sub="56", size=13.0),
            math_label(220.0, 141.0, "C", sub="57", size=13.0),
            math_label(196.0, 206.0, "C", sub="54", size=13.0),
            math_label(196.0, 236.0, "C", sub="45", size=13.0),
            math_label(224.0, 174.0, "C", sub="59", size=13.0),
            math_label(258.0, 174.0, "C", sub="95", size=13.0),
            math_label(224.0, 258.0, "C", sub="48", size=13.0),
        ]
    )
    return svg_figure(
        "0 0 380 330",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_31",
        title=CHAPTER_FIG_TITLES["2_31"],
    )


def _multiply_connected_paths() -> tuple[str, str, str]:
    outer = (
        "M 62.0 104.0 "
        "C 104.0 54.0, 178.0 18.0, 240.0 22.0 "
        "C 298.0 26.0, 320.0 66.0, 332.0 108.0 "
        "C 346.0 154.0, 362.0 198.0, 326.0 232.0 "
        "C 288.0 264.0, 206.0 254.0, 134.0 254.0 "
        "C 66.0 254.0, 32.0 218.0, 36.0 168.0 "
        "C 39.0 136.0, 46.0 122.0, 62.0 104.0 Z"
    )
    hole_1 = (
        "M 116.0 144.0 "
        "C 138.0 138.0, 152.0 156.0, 168.0 172.0 "
        "C 184.0 188.0, 182.0 216.0, 158.0 222.0 "
        "C 128.0 228.0, 92.0 212.0, 88.0 184.0 "
        "C 85.0 162.0, 98.0 148.0, 116.0 144.0 Z"
    )
    hole_2 = (
        "M 232.0 68.0 "
        "C 254.0 46.0, 292.0 52.0, 286.0 80.0 "
        "C 280.0 102.0, 274.0 116.0, 282.0 134.0 "
        "C 290.0 152.0, 274.0 166.0, 256.0 160.0 "
        "C 240.0 154.0, 236.0 130.0, 226.0 112.0 "
        "C 218.0 96.0, 218.0 82.0, 232.0 68.0 Z"
    )
    return outer, hole_1, hole_2


def fig_2_32() -> str:
    outer, hole_1, hole_2 = _multiply_connected_paths()
    compound = f"{outer} {hole_1} {hole_2}"
    regions = "\n".join(
        [
            f'    <path d="{compound}" fill-rule="evenodd" class="f-blue" />',
            f'    <path d="{compound}" fill-rule="evenodd" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{outer}" class="c-blue" />',
            f'    <path d="{hole_1}" class="c-blue" />',
            f'    <path d="{hole_2}" class="c-blue" />',
            tangent_arrow(136.0, 54.0, -0.82, 0.57, marker="arr-blue"),
            tangent_arrow(128.0, 144.0, 0.92, 0.38, marker="arr-blue"),
            tangent_arrow(221.0, 88.0, 0.25, -0.96, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            math_label(114.0, 48.0, "C", color="#1e3a8a"),
            math_label(112.0, 168.0, "C", color="#1e3a8a"),
            math_label(232.0, 96.0, "C", color="#1e3a8a"),
            math_label(236.0, 198.0, "[D]", italic=False),
        ]
    )
    return svg_figure(
        "0 0 390 275",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_32",
        title=CHAPTER_FIG_TITLES["2_32"],
    )


def fig_2_33() -> str:
    inner_cell = (
        "M 76.0 208.0 "
        "C 162.0 194.0, 266.0 226.0, 356.0 214.0 "
        "C 334.0 166.0, 336.0 124.0, 352.0 82.0 "
        "C 268.0 78.0, 184.0 46.0, 114.0 78.0 "
        "C 120.0 122.0, 102.0 166.0, 76.0 208.0 Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{inner_cell}" class="f-blue" />',
            f'    <path d="{inner_cell}" class="f-stipple" />',
        ]
    )
    g0 = "M 32.0 248.0 C 146.0 218.0, 268.0 258.0, 392.0 242.0"
    g1 = "M 74.0 58.0 C 178.0 16.0, 286.0 64.0, 408.0 56.0"
    ga = "M 32.0 248.0 C 56.0 186.0, 90.0 122.0, 74.0 58.0"
    gb = "M 392.0 242.0 C 378.0 182.0, 362.0 112.0, 408.0 56.0"

    g0e = "M 76.0 208.0 C 162.0 194.0, 266.0 226.0, 356.0 214.0"
    g1e = "M 114.0 78.0 C 184.0 46.0, 268.0 78.0, 352.0 82.0"
    gae = "M 76.0 208.0 C 102.0 166.0, 120.0 122.0, 114.0 78.0"
    gbe = "M 356.0 214.0 C 336.0 166.0, 336.0 124.0, 352.0 82.0"

    curves = "\n".join(
        [
            mid_arrow_path(g0, 212.0, 238.0, 0.98, 0.14, cls="c-main", marker="arr"),
            mid_arrow_path(g1, 248.0, 42.0, 0.98, 0.16, cls="c-main", marker="arr"),
            mid_arrow_path(ga, 68.0, 144.0, 0.24, -0.97, cls="c-main", marker="arr"),
            mid_arrow_path(gb, 376.0, 146.0, 0.04, -1.0, cls="c-main", marker="arr"),
            mid_arrow_path(
                g0e, 218.0, 209.0, 0.98, 0.15, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                g1e, 246.0, 68.0, 0.98, 0.18, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                gae, 106.0, 142.0, 0.24, -0.97, cls="c-blue", marker="arr-blue"
            ),
            mid_arrow_path(
                gbe, 341.0, 146.0, -0.04, -1.0, cls="c-blue", marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            math_label(250.0, 26.0, "γ", sub="1"),
            math_label(192.0, 258.0, "γ", sub="0"),
            '    <text x="36.0" y="148.0" class="it"><tspan font-size="10.5px" dy="3.2">a</tspan><tspan dy="-3.2">γ</tspan></text>',
            '    <text x="386.0" y="152.0" class="it"><tspan font-size="10.5px" dy="3.2">b</tspan><tspan dy="-3.2">γ</tspan></text>',
            math_label(228.0, 92.0, "γ", sub="1", sup="ε", color="#1e3a8a"),
            math_label(214.0, 198.0, "γ", sub="0", sup="ε", color="#1e3a8a"),
            '    <text x="112.0" y="152.0" class="it" fill="#1e3a8a"><tspan font-size="10.5px" dy="3.2">a</tspan><tspan dy="-3.2">γ</tspan><tspan font-size="10.5px" dy="-5.0">ε</tspan></text>',
            '    <text x="302.0" y="156.0" class="it" fill="#1e3a8a"><tspan font-size="10.5px" dy="3.2">b</tspan><tspan dy="-3.2">γ</tspan><tspan font-size="10.5px" dy="-5.0">ε</tspan></text>',
            math_label(218.0, 144.0, "Γ(K", sup="ε", tail=")", anchor="middle"),
        ]
    )
    return svg_figure(
        "0 0 440 275",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_33",
        title=CHAPTER_FIG_TITLES["2_33"],
    )


def fig_2_34() -> str:
    outer, hole_1, hole_2 = _multiply_connected_paths()
    wx, wy, wr = 180.0, 108.0, 24.0
    hole_w = (
        f"M {wx - wr:.1f} {wy:.1f} "
        f"A {wr:.1f} {wr:.1f} 0 1 0 {wx + wr:.1f} {wy:.1f} "
        f"A {wr:.1f} {wr:.1f} 0 1 0 {wx - wr:.1f} {wy:.1f} Z"
    )
    compound = f"{outer} {hole_1} {hole_2} {hole_w}"
    regions = "\n".join(
        [
            f'    <path d="{compound}" fill-rule="evenodd" class="f-blue" />',
            f'    <path d="{compound}" fill-rule="evenodd" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{outer}" class="c-blue" />',
            f'    <path d="{hole_1}" class="c-blue" />',
            f'    <path d="{hole_2}" class="c-blue" />',
            tangent_arrow(136.0, 54.0, -0.82, 0.57, marker="arr-blue"),
            tangent_arrow(128.0, 144.0, 0.92, 0.38, marker="arr-blue"),
            tangent_arrow(221.0, 88.0, 0.25, -0.96, marker="arr-blue"),
            circle_contour(
                wx, wy, wr, cls="c-red", arrow_deg=85.0, ccw=True, marker="arr-red"
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(wx, wy, color="#dc2626"),
            math_label(148.0, 32.0, "C", color="#1e3a8a"),
            math_label(112.0, 168.0, "C", color="#1e3a8a"),
            math_label(232.0, 96.0, "C", color="#1e3a8a"),
            math_label(172.0, 76.0, "C", sub="ε", color="#dc2626"),
            math_label(174.0, 124.0, "w"),
            math_label(182.0, 198.0, "[D] − U", sub="ε", tail="(w)", italic=False),
        ]
    )
    return svg_figure(
        "0 0 390 275",
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_34",
        title=CHAPTER_FIG_TITLES["2_34"],
    )


def fig_2_35() -> str:
    ox, oy = 225.0, 195.0
    R_big, r_eps = 144.0, 25.0
    ax, ax_lbl = axes_xy(ox, oy, 20, 425, 16, 228, origin_label="")
    annulus = (
        f"M {ox + r_eps:.1f} {oy:.1f} "
        f"L {ox + R_big:.1f} {oy:.1f} "
        f"A {R_big:.1f} {R_big:.1f} 0 0 0 {ox - R_big:.1f} {oy:.1f} "
        f"L {ox - r_eps:.1f} {oy:.1f} "
        f"A {r_eps:.1f} {r_eps:.1f} 0 0 1 {ox + r_eps:.1f} {oy:.1f} Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{annulus}" class="f-blue" />',
            f'    <path d="{annulus}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            arc_path(ox, oy, R_big, 0.0, 180.0, cls="c-blue", ccw=True),
            tangent_arrow(
                ox + R_big * math.cos(math.radians(68.0)),
                oy - R_big * math.sin(math.radians(68.0)),
                -math.sin(math.radians(68.0)),
                -math.cos(math.radians(68.0)),
                marker="arr-blue",
            ),
            arc_path(ox, oy, r_eps, 180.0, 0.0, cls="c-red", ccw=False),
            tangent_arrow(
                ox + r_eps * math.cos(math.radians(58.0)),
                oy - r_eps * math.sin(math.radians(58.0)),
                math.sin(math.radians(58.0)),
                math.cos(math.radians(58.0)),
                marker="arr-red",
            ),
            f'    <line x1="{ox - R_big:.1f}" y1="{oy:.1f}" x2="{ox - r_eps:.1f}" y2="{oy:.1f}" class="c-blue" />',
            tangent_arrow(ox - 0.5 * (R_big + r_eps), oy, 1.0, 0.0, marker="arr-blue"),
            f'    <line x1="{ox + r_eps:.1f}" y1="{oy:.1f}" x2="{ox + R_big:.1f}" y2="{oy:.1f}" class="c-blue" />',
            tangent_arrow(ox + 0.5 * (R_big + r_eps), oy, 1.0, 0.0, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            math_label(ox - R_big, oy + 20.0, "−R", anchor="middle"),
            math_label(ox - r_eps - 4.0, oy + 20.0, "−ε", anchor="middle"),
            math_label(ox + r_eps + 4.0, oy + 20.0, "ε", anchor="middle"),
            math_label(ox + R_big, oy + 20.0, "R", anchor="middle"),
            math_label(ox + 52.0, 52.0, "C", sub="R", color="#1e3a8a"),
            math_label(ox + 4.0, oy - r_eps - 8.0, "−C", sub="ε", color="#dc2626"),
            math_label(ox + 8.0, 118.0, "[D]", italic=False),
        ]
    )
    return svg_figure(
        "0 0 455 240",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_35",
        title=CHAPTER_FIG_TITLES["2_35"],
    )


def fig_2_36() -> str:
    ox, oy = 86.0, 222.0
    R_sec = 228.0
    ax, ax_lbl = axes_xy(ox, oy, 22, 392, 18, 250)
    x_top = ox + R_sec * math.cos(math.radians(45.0))
    y_top = oy - R_sec * math.sin(math.radians(45.0))
    sector_d = (
        f"M {ox:.1f} {oy:.1f} "
        f"L {ox + R_sec:.1f} {oy:.1f} "
        f"A {R_sec:.1f} {R_sec:.1f} 0 0 0 {x_top:.1f} {y_top:.1f} Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{sector_d}" class="f-blue" />',
            f'    <path d="{sector_d}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{ox + R_sec:.1f}" y2="{oy:.1f}" class="c-blue" />',
            tangent_arrow(ox + 0.54 * R_sec, oy, 1.0, 0.0, marker="arr-blue"),
            arc_path(
                ox,
                oy,
                R_sec,
                0.0,
                45.0,
                cls="c-blue",
                ccw=True,
                arrow_mid=True,
                marker="arr-blue",
            ),
            f'    <line x1="{x_top:.1f}" y1="{y_top:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" class="c-blue" />',
            tangent_arrow(
                ox + 0.54 * (x_top - ox),
                oy + 0.54 * (y_top - oy),
                -1.0,
                1.0,
                marker="arr-blue",
            ),
            arc_path(ox, oy, 52.0, 0.0, 45.0, cls="c-main", ccw=True),
            tangent_arrow(
                ox + 52.0 * math.cos(math.radians(36.0)),
                oy - 52.0 * math.sin(math.radians(36.0)),
                -math.sin(math.radians(36.0)),
                -math.cos(math.radians(36.0)),
                marker="arr",
            ),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            math_label(ox + R_sec, oy + 20.0, "R", anchor="middle"),
            math_label(306.0, 136.0, "C", sub="R", color="#1e3a8a"),
            math_label(144.0, 126.0, "−L", color="#1e3a8a"),
            math_label(222.0, 168.0, "[D]", italic=False, anchor="middle"),
            math_label(148.0, 198.0, "π", italic=True, anchor="middle"),
            '    <line x1="141.0" y1="202.0" x2="155.0" y2="202.0" class="c-main" stroke-width="1.2" />',
            math_label(148.0, 216.0, "4", italic=False, anchor="middle"),
        ]
    )
    return svg_figure(
        "0 0 420 260",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_36",
        title=CHAPTER_FIG_TITLES["2_36"],
    )


def fig_2_37() -> str:
    ox, oy = 216.0, 200.0
    R_semi = 144.0
    ax, ax_lbl = axes_xy(ox, oy, 20, 415, 16, 232, origin_label="")
    semi_d = (
        f"M {ox - R_semi:.1f} {oy:.1f} "
        f"L {ox + R_semi:.1f} {oy:.1f} "
        f"A {R_semi:.1f} {R_semi:.1f} 0 0 0 {ox - R_semi:.1f} {oy:.1f} Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{semi_d}" class="f-blue" />',
            f'    <path d="{semi_d}" class="f-stipple" />',
            f'    <circle cx="{ox:.1f}" cy="{oy - 52.0:.1f}" r="14.0" fill="url(#glow-pole)" />',
        ]
    )
    curves = "\n".join(
        [
            arc_path(ox, oy, R_semi, 0.0, 180.0, cls="c-blue", ccw=True),
            tangent_arrow(
                ox + R_semi * math.cos(math.radians(68.0)),
                oy - R_semi * math.sin(math.radians(68.0)),
                -math.sin(math.radians(68.0)),
                -math.cos(math.radians(68.0)),
                marker="arr-blue",
            ),
            f'    <line x1="{ox - R_semi:.1f}" y1="{oy:.1f}" x2="{ox + R_semi:.1f}" y2="{oy:.1f}" class="c-blue" />',
            tangent_arrow(ox + 58.0, oy, 1.0, 0.0, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            point_dot(ox, oy - 52.0, color="#dc2626"),
            math_label(ox + 8.0, oy - 47.0, "i", color="#dc2626"),
            math_label(ox - R_semi, oy + 20.0, "−R", anchor="middle"),
            math_label(ox + R_semi, oy + 20.0, "R", anchor="middle"),
            math_label(ox + 52.0, 54.0, "C", sub="R", color="#1e3a8a"),
        ]
    )
    return svg_figure(
        "0 0 445 245",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_37",
        title=CHAPTER_FIG_TITLES["2_37"],
    )


def _subrect_ccw_arrows(x0: float, y0: float, w: float, h: float) -> str:
    xm, ym = x0 + 0.5 * w, y0 + 0.5 * h
    return "\n".join(
        [
            arrow_line(
                xm - 14.0,
                y0 + h - 7.0,
                xm + 14.0,
                y0 + h - 7.0,
                cls="c-sub",
                marker="arr",
            ),
            arrow_line(
                x0 + w - 7.0,
                ym + 13.0,
                x0 + w - 7.0,
                ym - 13.0,
                cls="c-sub",
                marker="arr",
            ),
            arrow_line(
                xm + 14.0, y0 + 7.0, xm - 14.0, y0 + 7.0, cls="c-sub", marker="arr"
            ),
            arrow_line(
                x0 + 7.0, ym - 13.0, x0 + 7.0, ym + 13.0, cls="c-sub", marker="arr"
            ),
        ]
    )


def fig_2_38() -> str:
    ax, ax_lbl = axes_xy(74, 240, 22, 402, 18, 276, x_label="t", y_label="is")
    x0, y0, w, h = 144.0, 54.0, 204.0, 140.0
    hw, hh = 0.5 * w, 0.5 * h
    regions = "\n".join(
        [
            f'    <rect x="{x0:.1f}" y="{y0 + hh:.1f}" width="{hw:.1f}" height="{hh:.1f}" class="f-blue" />',
            f'    <rect x="{x0 + hw:.1f}" y="{y0 + hh:.1f}" width="{hw:.1f}" height="{hh:.1f}" class="f-amber" />',
            f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{hw:.1f}" height="{hh:.1f}" class="f-green" />',
            f'    <rect x="{x0 + hw:.1f}" y="{y0:.1f}" width="{hw:.1f}" height="{hh:.1f}" class="f-rose" />',
            f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" class="c-main" />',
            f'    <line x1="{x0 + hw:.1f}" y1="{y0:.1f}" x2="{x0 + hw:.1f}" y2="{y0 + h:.1f}" class="c-main" />',
            f'    <line x1="{x0:.1f}" y1="{y0 + hh:.1f}" x2="{x0 + w:.1f}" y2="{y0 + hh:.1f}" class="c-main" />',
            f'    <line x1="74.0" y1="{y0:.1f}" x2="80.0" y2="{y0:.1f}" class="c-main" />',
            f'    <line x1="74.0" y1="{y0 + h:.1f}" x2="80.0" y2="{y0 + h:.1f}" class="c-main" />',
            f'    <line x1="{x0:.1f}" y1="234.0" x2="{x0:.1f}" y2="240.0" class="c-main" />',
            f'    <line x1="{x0 + w:.1f}" y1="234.0" x2="{x0 + w:.1f}" y2="240.0" class="c-main" />',
            _subrect_ccw_arrows(x0, y0, hw, hh),
            _subrect_ccw_arrows(x0 + hw, y0, hw, hh),
            _subrect_ccw_arrows(x0, y0 + hh, hw, hh),
            _subrect_ccw_arrows(x0 + hw, y0 + hh, hw, hh),
        ]
    )
    labels = "\n".join(
        [
            ax_lbl,
            math_label(66.0, y0 + 5.0, "iy", anchor="end"),
            math_label(66.0, y0 + h + 5.0, "ib", anchor="end"),
            math_label(x0, 258.0, "a", anchor="middle"),
            math_label(x0 + w, 258.0, "x", anchor="middle"),
            math_label(x0 + 0.5 * hw, y0 + 0.5 * hh + 5.0, "K'''", anchor="middle"),
            math_label(x0 + 1.5 * hw, y0 + 0.5 * hh + 5.0, "K''''", anchor="middle"),
            math_label(x0 + 0.5 * hw, y0 + 1.5 * hh + 5.0, "K'", anchor="middle"),
            math_label(x0 + 1.5 * hw, y0 + 1.5 * hh + 5.0, "K''", anchor="middle"),
        ]
    )
    return svg_figure(
        "0 0 430 285",
        axes=ax,
        regions=regions,
        curves=curves,
        labels=labels,
        fig_id="2_38",
        title=CHAPTER_FIG_TITLES["2_38"],
    )


CHAPTER_FIG_TITLES: dict[str, str] = {
    "2_20": "Neighborhood U(ζ) split by C into U⁺(ζ) and U⁻(ζ) of width 2δ(1)",
    "2_21": "Rectangle R = Q₀₀ ∪ Q₀₁ and tangent sector lines at ζ on L",
    "2_22": "Cell [D] ∩ R bounded below by y = φ(x) in R",
    "2_23": "Cell [D] ∩ Q₀₀ when C intersects opposite vertical sides of Q₀₀",
    "2_24": "Decomposition of [D] ∩ Q₀₀ when C meets adjacent sides (ρ'(τ) > 0 and ρ'(τ) < 0)",
    "2_25": "Subdivided δ/3 grid around the 3δ × 3δ square centered at corner ζ_j",
    "2_26": "Corner cell configurations (5) and (6) at vertex ζ_j",
    "2_27": "Neighborhood U(ζ) of width 2δ(1) containing vertex ζ_j and point ζ on C_j",
    "2_28": "3δ × 3δ square Q₁ with sides L₁, L₂, L₃, L₄ and arcs C₁, C_m at ζ₁",
    "2_29": "Regions in Q₁ bounded by y = φ₁(x) and y = φ_m(x) intersected by vertical line l_x",
    "2_30": "Auxiliary line l (x = λ(y), y = μ(x)) dividing the corner cell at ζ₁",
    "2_31": "Cellular decomposition Γ_λ(K) with oriented internal and boundary edges",
    "2_32": "Multiply connected closed region [D] with positively oriented boundary C",
    "2_33": "Inset cell Γ(K^ε) with boundary γ₀^ε + _bγ^ε − γ₁^ε − _aγ^ε inside Γ(K)",
    "2_34": "Punctured region [D] − U_ε(w) with small circle C_ε around interior point w",
    "2_35": "Indented upper half-annulus [D] = {ε ≤ |z| ≤ R, 0 ≤ arg z ≤ π} for ∫(sin x / x)dx",
    "2_36": "Circular sector [D] = {0 ≤ r ≤ R, 0 ≤ θ ≤ π/4} for Fresnel integrals",
    "2_37": "Upper semicircle contour [−R, R] + C_R enclosing pole z = i",
    "2_38": "Goursat rectangle bisection of K into K', K'', K''', K'''' in the (t, is)-plane",
}


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "2_20": fig_2_20,
    "2_21": fig_2_21,
    "2_22": fig_2_22,
    "2_23": fig_2_23,
    "2_24": fig_2_24,
    "2_25": fig_2_25,
    "2_26": fig_2_26,
    "2_27": fig_2_27,
    "2_28": fig_2_28,
    "2_29": fig_2_29,
    "2_30": fig_2_30,
    "2_31": fig_2_31,
    "2_32": fig_2_32,
    "2_33": fig_2_33,
    "2_34": fig_2_34,
    "2_35": fig_2_35,
    "2_36": fig_2_36,
    "2_37": fig_2_37,
    "2_38": fig_2_38,
}
