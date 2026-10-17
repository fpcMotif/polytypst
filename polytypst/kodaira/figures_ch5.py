import math
from collections.abc import Callable

from ..vision.diagram_engine import (
    arc_path,
    arrow_line,
    circle_contour,
    math_label,
    mid_arrow_path,
    point_dot,
    smooth_curve,
    svg_document,
    tangent_arrow,
)


def _overline_label(
    x: float,
    y: float,
    base: str,
    color: str = "#0f172a",
    anchor: str = "middle",
    bar_w: float = 11.0,
) -> str:
    lbl = math_label(x, y, base, color=color, anchor=anchor)
    bx0 = x - bar_w * 0.5 if anchor == "middle" else x
    bx1 = bx0 + bar_w
    by = y - 13.5
    bar = f'    <line x1="{bx0:.1f}" y1="{by:.1f}" x2="{bx1:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="1.2" />'
    return f"{lbl}\n{bar}"


def _ortho_arc_cmd(
    cx: float,
    cy: float,
    r_disk: float,
    deg1: float,
    deg2: float,
) -> tuple[str, float, float, float, float]:
    rad1 = math.radians(deg1)
    rad2 = math.radians(deg2)
    x1 = cx + r_disk * math.cos(rad1)
    y1 = cy - r_disk * math.sin(rad1)
    x2 = cx + r_disk * math.cos(rad2)
    y2 = cy - r_disk * math.sin(rad2)
    ccw_span = (deg2 - deg1) % 360.0
    if abs(ccw_span - 180.0) < 1e-3:
        return f"L {x2:.2f} {y2:.2f}", x1, y1, x2, y2
    short_span = ccw_span if ccw_span < 180.0 else 360.0 - ccw_span
    r_arc = r_disk * math.tan(math.radians(short_span * 0.5))
    sweep = 1 if ccw_span < 180.0 else 0
    return f"A {r_arc:.2f} {r_arc:.2f} 0 0 {sweep} {x2:.2f} {y2:.2f}", x1, y1, x2, y2


def _ortho_arc_path(
    cx: float,
    cy: float,
    r_disk: float,
    deg1: float,
    deg2: float,
    cls: str = "c-blue",
) -> str:
    cmd, x1, y1, _, _ = _ortho_arc_cmd(cx, cy, r_disk, deg1, deg2)
    return f'    <path d="M {x1:.2f} {y1:.2f} {cmd}" class="{cls}" />'


def _ideal_polygon_d(
    cx: float,
    cy: float,
    r_disk: float,
    degs: list[float],
) -> str:
    n = len(degs)
    rad0 = math.radians(degs[0])
    x0 = cx + r_disk * math.cos(rad0)
    y0 = cy - r_disk * math.sin(rad0)
    parts = [f"M {x0:.2f} {y0:.2f}"]
    for i in range(n):
        cmd, _, _, _, _ = _ortho_arc_cmd(cx, cy, r_disk, degs[i], degs[(i + 1) % n])
        parts.append(cmd)
    parts.append("Z")
    return " ".join(parts)


def fig_5_1() -> str:
    cx, cy, r0 = 190.0, 170.0, 134.0
    x1, y1, r1 = 144.0, 128.0, 48.0
    x2, y2, r2 = 236.0, 220.0, 38.0
    d_outer = (
        f"M {cx - r0:.1f} {cy:.1f} "
        f"A {r0:.1f} {r0:.1f} 0 1 0 {cx + r0:.1f} {cy:.1f} "
        f"A {r0:.1f} {r0:.1f} 0 1 0 {cx - r0:.1f} {cy:.1f} Z"
    )
    d_h1 = (
        f"M {x1 - r1:.1f} {y1:.1f} "
        f"A {r1:.1f} {r1:.1f} 0 1 1 {x1 + r1:.1f} {y1:.1f} "
        f"A {r1:.1f} {r1:.1f} 0 1 1 {x1 - r1:.1f} {y1:.1f} Z"
    )
    d_h2 = (
        f"M {x2 - r2:.1f} {y2:.1f} "
        f"A {r2:.1f} {r2:.1f} 0 1 1 {x2 + r2:.1f} {y2:.1f} "
        f"A {r2:.1f} {r2:.1f} 0 1 1 {x2 - r2:.1f} {y2:.1f} Z"
    )
    compound = f"{d_outer} {d_h1} {d_h2}"
    regions = "\n".join(
        [
            f'    <path d="{compound}" class="f-blue" fill-rule="evenodd" />',
            f'    <path d="{compound}" class="f-stipple" fill-rule="evenodd" />',
        ]
    )
    curves = "\n".join(
        [
            circle_contour(cx, cy, r0, cls="c-blue-dash"),
            circle_contour(x1, y1, r1, cls="c-blue-dash"),
            circle_contour(x2, y2, r2, cls="c-blue-dash"),
        ]
    )
    labels = "\n".join(
        [
            math_label(318.0, 66.0, "F", sub="0"),
            math_label(246.0, 128.0, "D", color="#1e3a8a"),
            math_label(x1, y1 + 5.0, "F", sub="1", anchor="middle"),
            math_label(x2, y2 + 5.0, "F", sub="2", anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 380 340",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_1",
        title="Region D with holes F_1, F_2 and outer complement F_0",
    )


def fig_5_2() -> str:
    outer_pts: list[tuple[float, float]] = []
    for i in range(36):
        ang = math.radians(i * 10.0)
        rad_x = 208.0 + 7.0 * math.sin(i * 1.9)
        rad_y = 154.0 + 6.0 * math.cos(i * 2.1)
        outer_pts.append((240.0 + rad_x * math.cos(ang), 180.0 - rad_y * math.sin(ang)))
    omega_pts = [
        (380.0, 180.0),
        (368.0, 118.0),
        (312.0, 66.0),
        (232.0, 48.0),
        (154.0, 68.0),
        (100.0, 120.0),
        (78.0, 188.0),
        (94.0, 254.0),
        (152.0, 294.0),
        (246.0, 310.0),
        (332.0, 286.0),
        (372.0, 236.0),
    ]
    outer_poly = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in outer_pts) + " Z"
    omega_poly = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in omega_pts) + " Z"
    gx0, gy0, step = 122.0, 86.0, 20.0
    row_spans: dict[int, tuple[int, int]] = {
        0: (4, 7),
        1: (2, 8),
        2: (1, 9),
        3: (1, 10),
        4: (1, 10),
        5: (0, 10),
        6: (0, 9),
        7: (0, 8),
        8: (1, 7),
    }
    grid_rects: list[str] = []
    for r, (c0, c1) in row_spans.items():
        for c in range(c0, c1):
            rx = gx0 + c * step
            ry = gy0 + r * step
            grid_rects.append(
                f'    <rect x="{rx:.1f}" y="{ry:.1f}" width="{step:.1f}" height="{step:.1f}" class="c-sub" />'
            )
    c_perim = [
        (gx0 + 4 * step, gy0),
        (gx0 + 7 * step, gy0),
        (gx0 + 7 * step, gy0 + 1 * step),
        (gx0 + 8 * step, gy0 + 1 * step),
        (gx0 + 8 * step, gy0 + 2 * step),
        (gx0 + 9 * step, gy0 + 2 * step),
        (gx0 + 9 * step, gy0 + 3 * step),
        (gx0 + 10 * step, gy0 + 3 * step),
        (gx0 + 10 * step, gy0 + 6 * step),
        (gx0 + 9 * step, gy0 + 6 * step),
        (gx0 + 9 * step, gy0 + 7 * step),
        (gx0 + 8 * step, gy0 + 7 * step),
        (gx0 + 8 * step, gy0 + 8 * step),
        (gx0 + 7 * step, gy0 + 8 * step),
        (gx0 + 7 * step, gy0 + 9 * step),
        (gx0 + 1 * step, gy0 + 9 * step),
        (gx0 + 1 * step, gy0 + 8 * step),
        (gx0 + 0 * step, gy0 + 8 * step),
        (gx0 + 0 * step, gy0 + 5 * step),
        (gx0 + 1 * step, gy0 + 5 * step),
        (gx0 + 1 * step, gy0 + 2 * step),
        (gx0 + 2 * step, gy0 + 2 * step),
        (gx0 + 2 * step, gy0 + 1 * step),
        (gx0 + 4 * step, gy0 + 1 * step),
    ]
    c_path_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in c_perim) + " Z"
    gamma_outer = [
        (228.0, 104.0),
        (172.0, 126.0),
        (156.0, 168.0),
        (138.0, 210.0),
        (164.0, 248.0),
        (208.0, 256.0),
        (224.0, 214.0),
        (236.0, 156.0),
        (216.0, 138.0),
        (178.0, 174.0),
        (182.0, 224.0),
        (232.0, 250.0),
        (276.0, 226.0),
        (294.0, 182.0),
        (272.0, 166.0),
        (228.0, 192.0),
        (206.0, 182.0),
        (228.0, 146.0),
        (282.0, 136.0),
        (310.0, 174.0),
        (298.0, 198.0),
        (276.0, 180.0),
        (266.0, 134.0),
    ]
    regions = "\n".join(
        [
            f'    <path d="{outer_poly} {omega_poly}" class="f-amber" fill-rule="evenodd" />',
            f'    <path d="{outer_poly} {omega_poly}" class="f-stipple" fill-rule="evenodd" />',
            smooth_curve(gamma_outer, cls="c-blue", closed=True, fill_cls="f-blue"),
        ]
    )
    curves = "\n".join(
        [
            smooth_curve(omega_pts, cls="c-main", closed=True),
            *grid_rects,
            f'    <path d="{c_path_d}" class="c-main" />',
            tangent_arrow(232.0, gy0, -1.0, 0.0, marker="arr"),
            tangent_arrow(gx0, gy0 + 6.5 * step, 0.0, 1.0, marker="arr"),
            tangent_arrow(gx0 + 4.2 * step, gy0 + 9 * step, 1.0, 0.0, marker="arr"),
            tangent_arrow(gx0 + 10 * step, gy0 + 4.4 * step, 0.0, -1.0, marker="arr"),
            smooth_curve(
                gamma_outer,
                cls="c-blue",
                closed=True,
                arrow_indices=[(1, True), (6, True), (16, True), (21, True)],
                marker="arr-blue",
            ),
        ]
    )
    labels = "\n".join(
        [
            math_label(376.0, 86.0, "F"),
            math_label(328.0, 236.0, "Ω"),
            math_label(178.0, 144.0, "γ", color="#1e3a8a"),
            math_label(242.0, 218.0, "Γ", color="#1e3a8a"),
            math_label(212.0, 286.0, "C"),
        ]
    )
    return svg_document(
        "0 0 480 360",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_2",
        title="Grid covering K of cycle Gamma in region Omega with complement F",
    )


def fig_5_3() -> str:
    x0, y0, s = 90.0, 62.0, 180.0
    x1, y1 = x0 + s, y0 + s
    xm, ym = x0 + s * 0.5, y0 + s * 0.5
    regions = f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{s:.1f}" height="{s:.1f}" class="f-blue" />'
    curves = "\n".join(
        [
            f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{s:.1f}" height="{s:.1f}" class="c-blue" />',
            tangent_arrow(xm, y1, 1.0, 0.0, marker="arr-blue"),
            tangent_arrow(x1, ym, 0.0, -1.0, marker="arr-blue"),
            tangent_arrow(xm, y0, -1.0, 0.0, marker="arr-blue"),
            tangent_arrow(x0, ym, 0.0, 1.0, marker="arr-blue"),
        ]
    )
    labels = "\n".join(
        [
            math_label(xm, ym + 5.0, "Q", sub="λ", anchor="middle"),
            math_label(
                xm, y1 + 24.0, "C", sub="4λ−3", anchor="middle", color="#1e3a8a"
            ),
            math_label(x1 + 12.0, ym + 5.0, "C", sub="4λ−2", color="#1e3a8a"),
            math_label(
                xm, y0 - 14.0, "C", sub="4λ−1", anchor="middle", color="#1e3a8a"
            ),
            math_label(
                x0 - 12.0, ym + 5.0, "C", sub="4λ", anchor="end", color="#1e3a8a"
            ),
        ]
    )
    return svg_document(
        "0 0 360 310",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_3",
        title="Oriented boundary sides of square Q_lambda",
    )


def fig_5_4() -> str:
    cx, cy, r = 230.0, 138.0, 96.0
    deg_b, deg_a = 190.0, 22.0
    xb = cx + r * math.cos(math.radians(deg_b))
    yb = cy - r * math.sin(math.radians(deg_b))
    xa = cx + r * math.cos(math.radians(deg_a))
    ya = cy - r * math.sin(math.radians(deg_a))
    c1_pts = [(32.0, 250.0), (84.0, 194.0), (xb, yb), (186.0, 128.0), (cx, cy)]
    c2_pts = [(cx, cy), (272.0, 134.0), (xa, ya), (376.0, 62.0), (414.0, 40.0)]
    regions = f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-blue" opacity="0.35" />'
    curves = "\n".join(
        [
            circle_contour(
                cx, cy, r, cls="c-main", arrow_deg=270.0, ccw=True, marker="arr"
            ),
            smooth_curve(
                c1_pts, cls="c-blue", arrow_indices=[(0, True)], marker="arr-blue"
            ),
            smooth_curve(
                c2_pts, cls="c-blue", arrow_indices=[(2, True)], marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(cx, cy, color="#0f172a"),
            point_dot(xb, yb, color="#1e3a8a", r=2.8),
            point_dot(xa, ya, color="#1e3a8a", r=2.8),
            math_label(44.0, 258.0, "C", sub="1", color="#1e3a8a"),
            math_label(392.0, 32.0, "C", sub="2", color="#1e3a8a"),
            math_label(xb - 8.0, yb - 4.0, "λ", sub="r", tail="(β)", anchor="end"),
            math_label(xa + 8.0, ya + 12.0, "λ", sub="r", tail="(α)"),
            math_label(cx, cy + 24.0, "γ", tail="(a)", anchor="middle"),
            math_label(cx, cy + r + 22.0, "λ", sub="r", anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 440 280",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_4",
        title="Circle lambda_r centered at gamma(a) intersecting C_1 and C_2",
    )


def fig_5_5() -> str:
    qx, qy, r = 236.0, 226.0, 62.0
    deg_b, deg_a = 152.0, 348.0
    xb = qx + r * math.cos(math.radians(deg_b))
    yb = qy - r * math.sin(math.radians(deg_b))
    xa = qx + r * math.cos(math.radians(deg_a))
    ya = qy - r * math.sin(math.radians(deg_a))
    c_pts = [
        (34.0, 192.0),
        (98.0, 168.0),
        (xb, yb),
        (qx, qy),
        (xa, ya),
        (362.0, 198.0),
        (414.0, 138.0),
    ]
    top_pts = [
        (414.0, 138.0),
        (402.0, 82.0),
        (348.0, 38.0),
        (256.0, 26.0),
        (142.0, 26.0),
        (56.0, 56.0),
        (28.0, 128.0),
        (34.0, 192.0),
    ]
    reg_pts = c_pts + top_pts[1:-1]
    regions = "\n".join(
        [
            smooth_curve(reg_pts, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(reg_pts, cls="c-sub", closed=True, fill_cls="f-stipple"),
        ]
    )
    curves = "\n".join(
        [
            smooth_curve(c_pts, cls="c-main", arrow_indices=[(4, True)], marker="arr"),
            circle_contour(
                qx, qy, r, cls="c-blue", arrow_deg=90.0, ccw=False, marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(qx, qy, color="#0f172a"),
            point_dot(xb, yb, color="#1e3a8a"),
            point_dot(xa, ya, color="#1e3a8a"),
            math_label(218.0, 106.0, "D", color="#1e3a8a"),
            math_label(qx + 4.0, qy - r - 8.0, "λ", color="#1e3a8a", anchor="middle"),
            math_label(xb - 8.0, yb + 12.0, "λ", sub="r", tail="(β)", anchor="end"),
            math_label(xa + 6.0, ya + 18.0, "λ", sub="r", tail="(α)"),
            math_label(qx - 4.0, qy + 20.0, "q", anchor="middle"),
            math_label(374.0, 206.0, "C"),
        ]
    )
    return svg_document(
        "0 0 440 310",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_5",
        title="Arc lambda of circle lambda_r inside region D at boundary point q",
    )


def fig_5_6() -> str:
    qx, qy, rq = 118.0, 218.0, 58.0
    px, py, rp = 348.0, 152.0, 58.0
    gamma_left = [
        (42.0, 286.0),
        (80.0, 248.0),
        (qx, qy),
        (178.0, 202.0),
        (234.0, 202.0),
    ]
    gamma_right = [
        (234.0, 202.0),
        (274.0, 168.0),
        (px, py),
        (412.0, 166.0),
        (456.0, 198.0),
    ]
    top_pts = [
        (456.0, 198.0),
        (452.0, 96.0),
        (392.0, 42.0),
        (264.0, 28.0),
        (114.0, 24.0),
        (42.0, 62.0),
        (26.0, 178.0),
        (42.0, 286.0),
    ]
    reg_pts = gamma_left + gamma_right[1:] + top_pts[1:-1]
    w_pts = [(100.0, 174.0), (98.0, 198.0), (114.0, 210.0)]
    z_pts = [(346.0, 102.0), (358.0, 118.0), (349.0, 144.0)]
    regions = "\n".join(
        [
            smooth_curve(reg_pts, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(reg_pts, cls="c-sub", closed=True, fill_cls="f-stipple"),
        ]
    )
    curves = "\n".join(
        [
            smooth_curve(
                gamma_left, cls="c-main", arrow_indices=[(2, True)], marker="arr"
            ),
            smooth_curve(
                gamma_right, cls="c-main", arrow_indices=[(0, True)], marker="arr"
            ),
            circle_contour(qx, qy, rq, cls="c-blue"),
            circle_contour(px, py, rp, cls="c-blue"),
            arrow_line(
                qx, qy, qx + rq - 2.0, qy - 3.0, cls="c-blue", marker="arr-blue"
            ),
            arrow_line(px, py, px + 46.0, py + 34.0, cls="c-blue", marker="arr-blue"),
            smooth_curve(w_pts, cls="c-red"),
            smooth_curve(z_pts, cls="c-red"),
        ]
    )
    labels = "\n".join(
        [
            point_dot(qx, qy, color="#0f172a"),
            point_dot(px, py, color="#0f172a"),
            point_dot(w_pts[0][0], w_pts[0][1], color="#dc2626", r=2.9),
            point_dot(w_pts[1][0], w_pts[1][1], color="#dc2626", r=2.9),
            point_dot(w_pts[2][0], w_pts[2][1], color="#dc2626", r=2.9),
            point_dot(z_pts[0][0], z_pts[0][1], color="#dc2626", r=2.9),
            point_dot(z_pts[1][0], z_pts[1][1], color="#dc2626", r=2.9),
            point_dot(z_pts[2][0], z_pts[2][1], color="#dc2626", r=2.9),
            math_label(224.0, 112.0, "Δ", color="#1e3a8a"),
            math_label(210.0, 222.0, "Γ"),
            math_label(qx + 2.0, qy + 20.0, "Q", anchor="middle"),
            math_label(px - 4.0, py + 20.0, "P", anchor="middle"),
            math_label(qx + 30.0, qy + 13.0, "ρ", color="#1e3a8a"),
            math_label(px + 18.0, py + 28.0, "ρ", color="#1e3a8a"),
            math_label(
                w_pts[0][0] + 6.0, w_pts[0][1] + 4.0, "ω", sub="j", color="#dc2626"
            ),
            math_label(
                w_pts[1][0] - 6.0,
                w_pts[1][1] + 10.0,
                "ω",
                tail="(r)",
                anchor="end",
                color="#dc2626",
            ),
            math_label(
                w_pts[2][0] + 4.0, w_pts[2][1] - 3.0, "ω", sub="n", color="#dc2626"
            ),
            math_label(
                z_pts[0][0] - 6.0,
                z_pts[0][1] + 8.0,
                "ζ",
                sub="j",
                anchor="end",
                color="#dc2626",
            ),
            math_label(
                z_pts[1][0] + 6.0, z_pts[1][1] + 8.0, "ζ", tail="(r)", color="#dc2626"
            ),
            math_label(
                z_pts[2][0] - 6.0,
                z_pts[2][1] - 2.0,
                "ζ",
                sub="n",
                anchor="end",
                color="#dc2626",
            ),
        ]
    )
    return svg_document(
        "0 0 480 310",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_6",
        title="Disks U_rho(Q) and U_rho(P) on boundary Gamma of region Delta",
    )


def fig_5_7() -> str:
    qx, qy = 218.0, 198.0
    r_eps, r_mid, r_del = 32.0, 92.0, 132.0
    xl = qx + r_mid * math.cos(math.radians(188.0))
    yl = qy - r_mid * math.sin(math.radians(188.0))
    xr = qx + r_mid * math.cos(math.radians(10.0))
    yr = qy - r_mid * math.sin(math.radians(10.0))
    c_pts = [
        (32.0, 298.0),
        (xl, yl),
        (178.0, 192.0),
        (qx, qy),
        (256.0, 204.0),
        (xr, yr),
        (358.0, 128.0),
        (406.0, 34.0),
    ]
    top_pts = [
        (406.0, 34.0),
        (312.0, 22.0),
        (182.0, 22.0),
        (68.0, 32.0),
        (26.0, 114.0),
        (24.0, 224.0),
        (32.0, 298.0),
    ]
    reg_pts = c_pts + top_pts[1:-1]
    wx_r = qx + r_mid * math.cos(math.radians(152.0))
    wy_r = qy - r_mid * math.sin(math.radians(152.0))
    zx_r = qx + r_mid * math.cos(math.radians(42.0))
    zy_r = qy - r_mid * math.sin(math.radians(42.0))
    w_curve = [(106.0, 96.0), (wx_r, wy_r), (205.0, 183.0)]
    z_curve = [(294.0, 60.0), (zx_r, zy_r), (231.0, 182.0)]
    regions = "\n".join(
        [
            smooth_curve(reg_pts, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(reg_pts, cls="c-sub", closed=True, fill_cls="f-stipple"),
        ]
    )
    curves = "\n".join(
        [
            smooth_curve(c_pts, cls="c-main", arrow_indices=[(6, True)], marker="arr"),
            circle_contour(
                qx,
                qy,
                r_eps,
                cls="c-blue",
                arrow_deg=270.0,
                ccw=True,
                marker="arr-blue",
            ),
            circle_contour(
                qx,
                qy,
                r_mid,
                cls="c-blue",
                arrow_deg=270.0,
                ccw=True,
                marker="arr-blue",
            ),
            circle_contour(
                qx,
                qy,
                r_del,
                cls="c-blue",
                arrow_deg=270.0,
                ccw=True,
                marker="arr-blue",
            ),
            smooth_curve(w_curve, cls="c-red"),
            smooth_curve(z_curve, cls="c-red"),
        ]
    )
    labels = "\n".join(
        [
            point_dot(qx, qy, color="#0f172a"),
            point_dot(xl, yl, color="#0f172a", r=2.8),
            point_dot(xr, yr, color="#0f172a", r=2.8),
            point_dot(w_curve[0][0], w_curve[0][1], color="#dc2626"),
            point_dot(w_curve[1][0], w_curve[1][1], color="#dc2626"),
            point_dot(w_curve[2][0], w_curve[2][1], color="#dc2626"),
            point_dot(z_curve[0][0], z_curve[0][1], color="#dc2626"),
            point_dot(z_curve[1][0], z_curve[1][1], color="#dc2626"),
            point_dot(z_curve[2][0], z_curve[2][1], color="#dc2626"),
            math_label(216.0, 134.0, "D", color="#1e3a8a", anchor="middle"),
            math_label(380.0, 108.0, "C"),
            math_label(qx, qy + 16.0, "q", anchor="middle"),
            math_label(
                qx, qy + r_eps + 16.0, "λ", sub="ε", anchor="middle", color="#1e3a8a"
            ),
            math_label(
                qx, qy + r_mid - 8.0, "λ", sub="r", anchor="middle", color="#1e3a8a"
            ),
            math_label(
                qx, qy + r_del + 16.0, "λ", sub="δ", anchor="middle", color="#1e3a8a"
            ),
            math_label(
                w_curve[0][0],
                w_curve[0][1] - 10.0,
                "w",
                sub="j",
                anchor="middle",
                color="#dc2626",
            ),
            math_label(
                w_curve[1][0] + 8.0,
                w_curve[1][1] + 2.0,
                "w",
                tail="(r)",
                color="#dc2626",
            ),
            math_label(
                w_curve[2][0],
                w_curve[2][1] - 8.0,
                "w",
                sub="n",
                anchor="middle",
                color="#dc2626",
            ),
            math_label(
                z_curve[0][0] + 8.0, z_curve[0][1] + 5.0, "z", sub="j", color="#dc2626"
            ),
            math_label(
                z_curve[1][0] - 8.0,
                z_curve[1][1] + 6.0,
                "z",
                tail="(r)",
                anchor="end",
                color="#dc2626",
            ),
            math_label(
                z_curve[2][0] + 6.0, z_curve[2][1] + 12.0, "z", sub="n", color="#dc2626"
            ),
        ]
    )
    return svg_document(
        "0 0 440 360",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_7",
        title="Concentric circles lambda_varepsilon, lambda_r, lambda_delta centered at q in C",
    )


def fig_5_8() -> str:
    gamma_d = (
        "M 152.0 38.0 "
        "Q 245.0 56.0 342.0 34.0 "
        "Q 352.0 98.0 378.0 156.0 "
        "Q 374.0 212.0 344.0 266.0 "
        "Q 268.0 272.0 202.0 304.0 "
        "Q 168.0 264.0 132.0 232.0 "
        "Q 118.0 176.0 86.0 140.0 "
        "Q 126.0 92.0 152.0 38.0 Z"
    )
    inner_pts = [
        (178.0, 74.0),
        (246.0, 86.0),
        (312.0, 88.0),
        (322.0, 164.0),
        (318.0, 228.0),
        (214.0, 256.0),
        (146.0, 218.0),
        (134.0, 136.0),
    ]
    mu_pts = [(322.0, 164.0), (350.0, 150.0), (377.0, 152.0)]
    regions = "\n".join(
        [
            f'    <path d="{gamma_d}" class="f-amber" opacity="0.35" />',
            smooth_curve(inner_pts, cls="c-blue", closed=True, fill_cls="f-blue"),
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{gamma_d}" class="c-main" />',
            tangent_arrow(248.0, 46.5, -1.0, 0.04, marker="arr"),
            smooth_curve(
                inner_pts,
                cls="c-blue",
                closed=True,
                arrow_indices=[(1, False)],
                marker="arr-blue",
            ),
            smooth_curve(
                mu_pts, cls="c-red", arrow_indices=[(0, True)], marker="arr-red"
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(232.0, 158.0, color="#0f172a"),
            point_dot(322.0, 164.0, color="#1e3a8a"),
            point_dot(377.0, 152.0, color="#0f172a"),
            math_label(250.0, 32.0, "Γ = ± f̃(C)", anchor="middle"),
            math_label(
                245.0, 110.0, "f", tail="(C", sub="r", color="#1e3a8a", anchor="middle"
            ),
            math_label(275.0, 110.0, ")", italic=False, color="#1e3a8a"),
            math_label(224.0, 163.0, "f", tail="(0)", anchor="end"),
            math_label(228.0, 218.0, "Δ", sub="r", color="#1e3a8a", anchor="middle"),
            math_label(314.0, 170.0, "f", tail="(r)", anchor="end", color="#1e3a8a"),
            math_label(348.0, 142.0, "μ", color="#dc2626", anchor="middle"),
            math_label(385.0, 156.0, "f̃", tail="(1)"),
        ]
    )
    return svg_document(
        "0 0 440 320",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_8",
        title="Homologous curves Gamma and f(C_r) around f(0) with connecting path mu",
    )


def fig_5_9() -> str:
    y_axis = 160.0
    xa, xb = 104.0, 312.0
    upper_Offsets = [
        (104.0, 0.0),
        (132.0, 32.0),
        (134.0, 84.0),
        (182.0, 96.0),
        (238.0, 138.0),
        (312.0, 102.0),
        (300.0, 44.0),
        (312.0, 0.0),
    ]
    up_pts = [(x, y_axis - dy) for x, dy in upper_Offsets]
    dn_pts = [(x, y_axis + dy) for x, dy in reversed(upper_Offsets)]
    regions = "\n".join(
        [
            smooth_curve(up_pts, cls="c-blue-dash", closed=True, fill_cls="f-blue"),
            smooth_curve(up_pts, cls="c-blue-dash", closed=True, fill_cls="f-stipple"),
            smooth_curve(dn_pts, cls="c-amber", closed=True, fill_cls="f-amber"),
            smooth_curve(dn_pts, cls="c-amber", closed=True, fill_cls="f-stipple"),
        ]
    )
    curves = "\n".join(
        [
            f'    <line x1="24.0" y1="{y_axis:.1f}" x2="396.0" y2="{y_axis:.1f}" class="c-main" />',
            f'    <line x1="{xa:.1f}" y1="{y_axis:.1f}" x2="{xb:.1f}" y2="{y_axis:.1f}" class="c-blue" />',
            tangent_arrow(218.0, y_axis, 1.0, 0.0, marker="arr"),
        ]
    )
    labels = "\n".join(
        [
            point_dot(xa, y_axis, color="#0f172a", r=2.8),
            point_dot(xb, y_axis, color="#0f172a", r=2.8),
            math_label(94.0, y_axis + 18.0, "a", anchor="middle"),
            math_label(322.0, y_axis + 20.0, "b", anchor="middle"),
            math_label(220.0, 102.0, "D", color="#1e3a8a", anchor="middle"),
            _overline_label(220.0, 232.0, "D", color="#b45309", anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 420 320",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_9",
        title="Schwarz reflection of region D across real segment (a, b)",
    )


def fig_5_10() -> str:
    cx, cy, r = 220.0, 120.0, 86.0
    d_up = f"M {cx - r:.1f} {cy:.1f} A {r:.1f} {r:.1f} 0 0 1 {cx + r:.1f} {cy:.1f} Z"
    d_dn = f"M {cx - r:.1f} {cy:.1f} A {r:.1f} {r:.1f} 0 0 0 {cx + r:.1f} {cy:.1f} Z"
    regions = "\n".join(
        [
            f'    <path d="{d_up}" class="f-blue" />',
            f'    <path d="{d_dn}" class="f-amber" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <line x1="24.0" y1="{cy:.1f}" x2="416.0" y2="{cy:.1f}" class="c-main" />',
            circle_contour(
                cx, cy, r, cls="c-blue", arrow_deg=45.0, ccw=True, marker="arr-blue"
            ),
            circle_contour(
                cx, cy, r, cls="c-blue", arrow_deg=225.0, ccw=True, marker="arr-blue"
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(cx, cy, color="#0f172a"),
            math_label(cx, cy - 10.0, "c", anchor="middle"),
            math_label(cx, cy - 44.0, "V", color="#1e3a8a", anchor="middle"),
            _overline_label(cx, cy + 56.0, "V", color="#b45309", anchor="middle"),
            math_label(cx + 62.0, cy - 68.0, "C", sub="ε", color="#1e3a8a"),
            math_label(356.0, 52.0, "D", color="#1e3a8a"),
            _overline_label(362.0, 198.0, "D", color="#b45309", anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 440 240",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_10",
        title="Disk U_varepsilon(c) divided into half-disks V and V-bar",
    )


def fig_5_11() -> str:
    x0, y0 = 28.0, 246.0
    x1, y1 = 392.0, 24.0
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = uy, -ux
    px, py = 210.0, 135.0
    c0x, c0y = px - 78.0 * ux, py - 78.0 * uy
    c1x, c1y = px + 34.0 * ux, py + 34.0 * uy
    dist = 76.0
    zx, zy = px + dist * nx, py + dist * ny
    zsx, zsy = px - dist * nx, py - dist * ny
    sq = 9.0
    rx1, ry1 = px + sq * ux, py + sq * uy
    rx2, ry2 = rx1 + sq * nx, ry1 + sq * ny
    rx3, ry3 = px + sq * nx, py + sq * ny
    curves = "\n".join(
        [
            f'    <line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" class="c-main" />',
            f'    <line x1="{zx:.1f}" y1="{zy:.1f}" x2="{zsx:.1f}" y2="{zsy:.1f}" class="c-blue" />',
            f'    <path d="M {rx1:.1f} {ry1:.1f} L {rx2:.1f} {ry2:.1f} L {rx3:.1f} {ry3:.1f}" class="c-sub" />',
        ]
    )
    labels = "\n".join(
        [
            point_dot(c0x, c0y, color="#0f172a"),
            point_dot(c1x, c1y, color="#0f172a"),
            point_dot(zx, zy, color="#1e3a8a"),
            point_dot(zsx, zsy, color="#dc2626"),
            math_label(c0x + 2.0, c0y + 20.0, "c", sub="0"),
            math_label(c1x + 4.0, c1y + 18.0, "c", sub="1"),
            math_label(zx - 4.0, zy - 10.0, "z", color="#1e3a8a", anchor="middle"),
            math_label(zsx + 8.0, zsy + 14.0, "z", sup="*", color="#dc2626"),
            math_label(384.0, 50.0, "l"),
        ]
    )
    return svg_document(
        "0 0 420 270",
        curve=curves,
        label=labels,
        fig_id="5_11",
        title="Reflection z to z* across line l through c_0 and c_1",
    )


def fig_5_12() -> str:
    cx, cy, r = 152.0, 210.0, 106.0
    ang = math.radians(47.0)
    ux, uy = math.cos(ang), -math.sin(ang)
    r_z = 66.0
    r_zs = (r * r) / r_z
    r_end = 248.0
    zx, zy = cx + r_z * ux, cy + r_z * uy
    zsx, zsy = cx + r_zs * ux, cy + r_zs * uy
    ex, ey = cx + r_end * ux, cy + r_end * uy
    regions = f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-blue" opacity="0.28" />'
    curves = "\n".join(
        [
            circle_contour(cx, cy, r, cls="c-main"),
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" class="c-blue" />',
        ]
    )
    labels = "\n".join(
        [
            point_dot(cx, cy, color="#0f172a"),
            point_dot(zx, zy, color="#1e3a8a"),
            point_dot(zsx, zsy, color="#dc2626"),
            math_label(cx - 8.0, cy - 4.0, "c", anchor="end"),
            math_label(zx - 8.0, zy - 6.0, "z", color="#1e3a8a", anchor="end"),
            math_label(
                zsx - 8.0, zsy - 8.0, "z", sup="*", color="#dc2626", anchor="end"
            ),
        ]
    )
    return svg_document(
        "0 0 380 340",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_12",
        title="Inversion z to z* with respect to circle centered at c",
    )


def fig_5_13() -> str:
    cx, cy, r = 148.0, 142.0, 110.0
    deg1, deg2 = -32.0, 36.0
    inner_polars = [
        (36.0, 110.0),
        (28.0, 88.0),
        (14.0, 68.0),
        (0.0, 74.0),
        (-16.0, 84.0),
        (-32.0, 110.0),
    ]
    d_in_pts: list[tuple[float, float]] = []
    d_out_pts: list[tuple[float, float]] = []
    for deg, rho in inner_polars:
        rad = math.radians(deg)
        d_in_pts.append((cx + rho * math.cos(rad), cy - rho * math.sin(rad)))
        rho_inv = (r * r) / rho
        d_out_pts.append((cx + rho_inv * math.cos(rad), cy - rho_inv * math.sin(rad)))
    arc_steps = [deg1 + (deg2 - deg1) * i / 12.0 for i in range(13)]
    arc_pts = [
        (cx + r * math.cos(math.radians(d)), cy - r * math.sin(math.radians(d)))
        for d in arc_steps
    ]
    reg_d = d_in_pts + arc_pts[1:-1]
    reg_ds = d_out_pts + arc_pts[1:-1]
    regions = "\n".join(
        [
            smooth_curve(reg_d, cls="c-blue-dash", closed=True, fill_cls="f-blue"),
            smooth_curve(reg_d, cls="c-blue-dash", closed=True, fill_cls="f-stipple"),
            smooth_curve(reg_ds, cls="c-amber", closed=True, fill_cls="f-amber"),
            smooth_curve(reg_ds, cls="c-amber", closed=True, fill_cls="f-stipple"),
        ]
    )
    curves = "\n".join(
        [
            circle_contour(
                cx, cy, r, cls="c-main", arrow_deg=222.0, ccw=True, marker="arr"
            ),
            arc_path(cx, cy, r, deg1, deg2, cls="c-blue", ccw=True),
        ]
    )
    labels = "\n".join(
        [
            point_dot(cx, cy, color="#0f172a"),
            math_label(cx, cy + 18.0, "c", anchor="middle"),
            math_label(58.0, 236.0, "C"),
            math_label(224.0, 142.0, "D", color="#1e3a8a", anchor="middle"),
            math_label(268.0, 144.0, "γ", color="#1e3a8a"),
            math_label(318.0, 114.0, "D", sup="*", color="#b45309", anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 440 280",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_13",
        title="Reflection of region D into D* across arc gamma of circle C",
    )


def fig_5_14() -> str:
    ox, oy, r = 132.0, 148.0, 94.0
    th1, th2, th3 = 0.0, -82.0, 58.0
    c1 = (ox + r * math.cos(math.radians(th1)), oy - r * math.sin(math.radians(th1)))
    c2 = (ox + r * math.cos(math.radians(th2)), oy - r * math.sin(math.radians(th2)))
    c3 = (ox + r * math.cos(math.radians(th3)), oy - r * math.sin(math.radians(th3)))
    p2 = (c1[0], oy - r * math.tan(math.radians(th3 * 0.5)))
    p3 = (c1[0], oy - r * math.tan(math.radians(th2 * 0.5)))
    half_23 = math.radians((th3 - th2) * 0.5)
    mid_23 = math.radians((th3 + th2) * 0.5)
    dist_p1 = r / math.cos(half_23)
    p1 = (ox + dist_p1 * math.cos(mid_23), oy - dist_p1 * math.sin(mid_23))
    r_g3 = math.hypot(c1[0] - p3[0], c1[1] - p3[1])
    vx, vy = c3[0] - p3[0], c3[1] - p3[1]
    d_p3_c3 = math.hypot(vx, vy)
    d_inv = (r_g3 * r_g3) / d_p3_c3
    c3_star = (p3[0] + vx * d_inv / d_p3_c3, p3[1] + vy * d_inv / d_p3_c3)
    th3_star = math.degrees(math.atan2(oy - c3_star[1], c3_star[0] - ox))
    tri_d = _ideal_polygon_d(ox, oy, r, [th1, th3, th2])
    tri_d3s = _ideal_polygon_d(ox, oy, r, [th1, th2, th3_star])
    regions = "\n".join(
        [
            f'    <path d="{tri_d}" class="f-blue" />',
            f'    <path d="{tri_d}" class="f-stipple" />',
            f'    <path d="{tri_d3s}" class="f-amber" opacity="0.55" />',
        ]
    )
    curves = "\n".join(
        [
            circle_contour(ox, oy, r, cls="c-main"),
            _ortho_arc_path(ox, oy, r, th2, th3, cls="c-blue"),
            _ortho_arc_path(ox, oy, r, th3, th1, cls="c-blue"),
            _ortho_arc_path(ox, oy, r, th1, th2, cls="c-blue"),
            _ortho_arc_path(ox, oy, r, th2, th3_star, cls="c-amber"),
            _ortho_arc_path(ox, oy, r, th3_star, th1, cls="c-amber"),
            f'    <line x1="{c1[0]:.1f}" y1="28.0" x2="{c1[0]:.1f}" y2="288.0" class="c-sub" />',
            '    <line x1="112.0" y1="22.0" x2="452.0" y2="237.0" class="c-sub" />',
            '    <line x1="42.0" y1="257.0" x2="462.0" y2="198.0" class="c-sub" />',
            f'    <line x1="{c3[0]:.1f}" y1="{c3[1]:.1f}" x2="{p3[0]:.1f}" y2="{p3[1]:.1f}" class="c-dash" />',
        ]
    )
    labels = "\n".join(
        [
            point_dot(c1[0], c1[1], color="#0f172a"),
            point_dot(c2[0], c2[1], color="#0f172a"),
            point_dot(c3[0], c3[1], color="#0f172a"),
            point_dot(c3_star[0], c3_star[1], color="#b45309", r=2.9),
            point_dot(p1[0], p1[1], color="#0f172a"),
            point_dot(p2[0], p2[1], color="#0f172a"),
            point_dot(p3[0], p3[1], color="#0f172a"),
            math_label(18.0, 148.0, "C"),
            math_label(c1[0] + 6.0, c1[1] + 5.0, "c", sub="1"),
            math_label(c2[0] - 14.0, c2[1] + 16.0, "c", sub="2"),
            math_label(c3[0] - 12.0, c3[1] - 10.0, "c", sub="3"),
            math_label(p1[0] - 8.0, p1[1] + 20.0, "P", sub="1"),
            math_label(p2[0] + 7.0, p2[1] + 2.0, "P", sub="2"),
            math_label(p3[0] + 7.0, p3[1] + 18.0, "P", sub="3"),
            math_label(166.0, 148.0, "D", color="#1e3a8a"),
            math_label(142.0, 154.0, "γ", sub="1", color="#1e3a8a"),
            math_label(178.0, 122.0, "γ", sub="2", color="#1e3a8a"),
            math_label(155.0, 184.0, "γ", sub="3", color="#1e3a8a"),
            math_label(178.0, 180.0, "D", sub="3", sup="*", color="#b45309"),
        ]
    )
    return svg_document(
        "0 0 480 310",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_14",
        title="Ideal curvilinear triangle D orthogonal to circle C with reflection D_3*",
    )


def fig_5_15() -> str:
    cx, cy, r = 230.0, 220.0, 186.0
    shaded_tris = [
        [0.0, 122.0, 242.0],
        [122.0, 84.0, 58.0],
        [58.0, 34.0, 0.0],
        [182.0, 158.0, 122.0],
        [242.0, 208.0, 182.0],
        [242.0, 280.0, 302.0],
        [302.0, 328.0, 360.0],
        [182.0, 189.0, 196.0],
        [196.0, 202.0, 208.0],
        [208.0, 215.0, 222.0],
        [222.0, 231.0, 242.0],
        [242.0, 255.0, 264.0],
        [264.0, 272.0, 280.0],
        [280.0, 286.0, 292.0],
        [292.0, 297.0, 302.0],
        [302.0, 309.0, 316.0],
        [316.0, 322.0, 328.0],
        [328.0, 335.0, 342.0],
        [342.0, 350.0, 360.0],
    ]
    white_tris = [
        [0.0, 58.0, 122.0],
        [122.0, 182.0, 242.0],
        [242.0, 302.0, 360.0],
        [182.0, 196.0, 208.0],
        [208.0, 222.0, 242.0],
        [242.0, 264.0, 280.0],
        [280.0, 292.0, 302.0],
        [302.0, 316.0, 328.0],
        [328.0, 342.0, 360.0],
    ]
    reg_parts: list[str] = []
    curve_parts: list[str] = [circle_contour(cx, cy, r, cls="c-main")]
    for tri in shaded_tris:
        d = _ideal_polygon_d(cx, cy, r, tri)
        reg_parts.append(f'    <path d="{d}" class="f-blue" />')
        reg_parts.append(f'    <path d="{d}" class="f-stipple" />')
        curve_parts.append(f'    <path d="{d}" class="c-blue" />')
    for tri in white_tris:
        d = _ideal_polygon_d(cx, cy, r, tri)
        curve_parts.append(f'    <path d="{d}" class="c-blue" />')
    v_c1 = (
        cx + r * math.cos(math.radians(122.0)),
        cy - r * math.sin(math.radians(122.0)),
    )
    v_c2 = (
        cx + r * math.cos(math.radians(242.0)),
        cy - r * math.sin(math.radians(242.0)),
    )
    v_c3 = (cx + r, cy)
    v_c11 = (
        cx + r * math.cos(math.radians(302.0)),
        cy - r * math.sin(math.radians(302.0)),
    )
    labels = "\n".join(
        [
            point_dot(v_c1[0], v_c1[1], color="#0f172a"),
            point_dot(v_c2[0], v_c2[1], color="#0f172a"),
            point_dot(v_c3[0], v_c3[1], color="#0f172a"),
            point_dot(v_c11[0], v_c11[1], color="#0f172a"),
            math_label(v_c1[0] - 16.0, v_c1[1] - 6.0, "c", sub="1"),
            math_label(v_c2[0] - 8.0, v_c2[1] + 18.0, "c", sub="2"),
            math_label(v_c3[0] + 6.0, v_c3[1] + 5.0, "c", sub="3"),
            math_label(v_c11[0] + 6.0, v_c11[1] + 14.0, "c", sub="11"),
            math_label(222.0, 224.0, "D", color="#1e3a8a", anchor="middle"),
            math_label(266.0, 152.0, "D", sub="2"),
            math_label(132.0, 224.0, "D", sub="3"),
            math_label(266.0, 298.0, "D", sub="1"),
            math_label(248.0, 182.0, "γ", sub="2", color="#1e3a8a"),
            math_label(176.0, 224.0, "γ", sub="3", color="#1e3a8a"),
            math_label(250.0, 266.0, "γ", sub="1", color="#1e3a8a"),
            math_label(238.0, 88.0, "D", sub="23", color="#1e3a8a", anchor="middle"),
            math_label(334.0, 140.0, "D", sub="21", color="#1e3a8a", anchor="middle"),
            math_label(98.0, 180.0, "D", sub="32", color="#1e3a8a", anchor="middle"),
            math_label(104.0, 278.0, "D", sub="31", color="#1e3a8a", anchor="middle"),
            math_label(98.0, 314.0, "D", sub="313", anchor="middle"),
            math_label(242.0, 358.0, "D", sub="13", color="#1e3a8a", anchor="middle"),
            math_label(328.0, 314.0, "D", sub="12", color="#1e3a8a", anchor="middle"),
            math_label(364.0, 298.0, "D", sub="121", anchor="middle"),
            math_label(222.0, 338.0, "γ", sub="31", color="#1e3a8a", anchor="middle"),
            math_label(306.0, 334.0, "γ", sub="21", color="#1e3a8a", anchor="middle"),
            math_label(198.0, 362.0, "γ", sub="113"),
            math_label(262.0, 380.0, "γ", sub="213"),
            math_label(334.0, 342.0, "γ", sub="312"),
            math_label(344.0, 272.0, "γ", sub="112"),
        ]
    )
    return svg_document(
        "0 0 460 440",
        region="\n".join(reg_parts),
        curve="\n".join(curve_parts),
        label=labels,
        fig_id="5_15",
        title="Modular tessellation of the unit disk by reflections of ideal triangle D",
    )


def fig_5_16() -> str:
    cx, cy, r = 190.0, 180.0, 146.0
    degs = [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]
    poly_d = _ideal_polygon_d(cx, cy, r, degs)
    regions = "\n".join(
        [
            f'    <path d="{poly_d}" class="f-blue" />',
            f'    <path d="{poly_d}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            circle_contour(cx, cy, r, cls="c-main"),
            f'    <path d="{poly_d}" class="c-blue" />',
        ]
    )
    labels = math_label(cx, cy + 6.0, "S", sup="(1)", color="#1e3a8a", anchor="middle")
    return svg_document(
        "0 0 380 360",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_16",
        title="Ideal hexagon S^(1) = D union D_1 union D_2 union D_3 in unit disk",
    )


def fig_5_17() -> str:
    cx, cy, r = 190.0, 180.0, 146.0
    degs = [
        0.0,
        34.0,
        58.0,
        82.0,
        120.0,
        158.0,
        180.0,
        202.0,
        240.0,
        278.0,
        302.0,
        326.0,
    ]
    poly_d = _ideal_polygon_d(cx, cy, r, degs)
    regions = "\n".join(
        [
            f'    <path d="{poly_d}" class="f-blue" />',
            f'    <path d="{poly_d}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            circle_contour(cx, cy, r, cls="c-main"),
            f'    <path d="{poly_d}" class="c-blue" />',
        ]
    )
    labels = math_label(cx, cy + 6.0, "S", sup="(2)", color="#1e3a8a", anchor="middle")
    return svg_document(
        "0 0 380 360",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_17",
        title="Reflected ideal polygon S^(2) in the unit disk",
    )


def fig_5_18() -> str:
    verts = [
        (348.0, 98.0),
        (228.0, 34.0),
        (150.0, 96.0),
        (86.0, 70.0),
        (38.0, 146.0),
        (74.0, 242.0),
        (194.0, 274.0),
        (256.0, 216.0),
        (342.0, 228.0),
    ]
    poly_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in verts) + " Z"
    edge_arrows: list[str] = []
    n = len(verts)
    for i in range(n):
        p1 = verts[i]
        p2 = verts[(i + 1) % n]
        mx = 0.5 * (p1[0] + p2[0])
        my = 0.5 * (p1[1] + p2[1])
        edge_arrows.append(
            tangent_arrow(mx, my, p2[0] - p1[0], p2[1] - p1[1], marker="arr-blue")
        )
    cl = verts[5]
    ext_dx = cl[0] - verts[4][0]
    ext_dy = cl[1] - verts[4][1]
    ext_len = math.hypot(ext_dx, ext_dy)
    ext_end = (cl[0] + 46.0 * ext_dx / ext_len, cl[1] + 46.0 * ext_dy / ext_len)
    deg_ext = math.degrees(math.atan2(-ext_dy, ext_dx))
    deg_next = math.degrees(math.atan2(-(verts[6][1] - cl[1]), verts[6][0] - cl[0]))
    regions = "\n".join(
        [
            f'    <path d="{poly_d}" class="f-blue" />',
            f'    <path d="{poly_d}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <path d="{poly_d}" class="c-blue" />',
            *edge_arrows,
            f'    <line x1="{cl[0]:.1f}" y1="{cl[1]:.1f}" x2="{ext_end[0]:.1f}" y2="{ext_end[1]:.1f}" class="c-dash" />',
            arc_path(
                cl[0],
                cl[1],
                26.0,
                deg_ext,
                deg_next,
                cls="c-red",
                ccw=True,
                arrow_mid=True,
                marker="arr-red",
            ),
        ]
    )
    labels = "\n".join(
        [
            point_dot(verts[0][0], verts[0][1], color="#0f172a"),
            point_dot(verts[1][0], verts[1][1], color="#0f172a"),
            point_dot(verts[4][0], verts[4][1], color="#0f172a"),
            point_dot(verts[5][0], verts[5][1], color="#0f172a"),
            point_dot(verts[8][0], verts[8][1], color="#0f172a"),
            math_label(196.0, 162.0, "D", color="#1e3a8a", anchor="middle"),
            math_label(verts[0][0] + 8.0, verts[0][1] + 5.0, "c", sub="0", tail=" = c"),
            math_label(verts[0][0] + 50.0, verts[0][1] + 8.0, "n", size=10.5),
            math_label(verts[1][0], verts[1][1] - 10.0, "c", sub="1", anchor="middle"),
            math_label(294.0, 60.0, "γ", sub="1", color="#1e3a8a"),
            math_label(182.0, 58.0, "γ", sub="2", color="#1e3a8a", anchor="end"),
            math_label(
                verts[4][0] - 6.0, verts[4][1] + 4.0, "c", sub="λ−1", anchor="end"
            ),
            math_label(50.0, 200.0, "γ", sub="λ", color="#1e3a8a", anchor="end"),
            math_label(
                verts[5][0] - 8.0, verts[5][1] + 6.0, "c", sub="λ", anchor="end"
            ),
            math_label(94.0, 276.0, "θ", sub="λ", color="#dc2626"),
            math_label(126.0, 276.0, "γ", sub="λ+1", color="#1e3a8a"),
            math_label(verts[8][0] + 8.0, verts[8][1] + 5.0, "c", sub="n−1"),
            math_label(352.0, 168.0, "γ", sub="n", color="#1e3a8a"),
            math_label(220.0, 304.0, "n = 9", italic=False, anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 500 320",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_18",
        title="Polygonal region D (n = 9) with exterior angle theta_lambda at c_lambda",
    )


def fig_5_19() -> str:
    wx, wy, rw = 364.0, 92.0, 78.0
    ux, uy, ru = 364.0, 294.0, 86.0
    cx, cy, rs = 76.0, 188.0, 74.0
    deg1, deg2 = -15.0, 118.0
    r1 = math.radians(deg1)
    r2 = math.radians(deg2)
    p_in = (cx + 106.0 * math.cos(r2), cy - 106.0 * math.sin(r2))
    p_out = (cx + 114.0 * math.cos(r1), cy - 114.0 * math.sin(r1))
    s_arc1 = (cx + rs * math.cos(r1), cy - rs * math.sin(r1))
    s_arc2 = (cx + rs * math.cos(r2), cy - rs * math.sin(r2))
    d_w = f"M {wx - rw:.1f} {wy:.1f} A {rw:.1f} {rw:.1f} 0 0 1 {wx + rw:.1f} {wy:.1f} Z"
    d_u = f"M {ux - ru:.1f} {uy:.1f} A {ru:.1f} {ru:.1f} 0 0 1 {ux + ru:.1f} {uy:.1f} Z"
    d_s = (
        f"M {cx:.1f} {cy:.1f} L {s_arc1[0]:.1f} {s_arc1[1]:.1f} "
        f"A {rs:.1f} {rs:.1f} 0 0 0 {s_arc2[0]:.1f} {s_arc2[1]:.1f} Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{d_w}" class="f-blue" />',
            f'    <path d="{d_w}" class="f-stipple" />',
            f'    <path d="{d_s}" class="f-amber" />',
            f'    <path d="{d_s}" class="f-stipple" />',
            f'    <path d="{d_u}" class="f-green" />',
            f'    <path d="{d_u}" class="f-stipple" />',
        ]
    )
    curves = "\n".join(
        [
            f'    <line x1="248.0" y1="{wy:.1f}" x2="480.0" y2="{wy:.1f}" class="c-main" />',
            arc_path(wx, wy, rw, 0.0, 180.0, cls="c-blue-dash", ccw=True),
            f'    <line x1="{p_in[0]:.1f}" y1="{p_in[1]:.1f}" x2="{cx:.1f}" y2="{cy:.1f}" class="c-main" />',
            tangent_arrow(
                0.5 * (p_in[0] + cx),
                0.5 * (p_in[1] + cy),
                cx - p_in[0],
                cy - p_in[1],
                marker="arr",
            ),
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{p_out[0]:.1f}" y2="{p_out[1]:.1f}" class="c-main" />',
            tangent_arrow(
                0.5 * (cx + p_out[0]),
                0.5 * (cy + p_out[1]),
                p_out[0] - cx,
                p_out[1] - cy,
                marker="arr",
            ),
            arc_path(cx, cy, rs, deg1, deg2, cls="c-dash", ccw=True),
            arc_path(cx, cy, 18.0, deg1, deg2, cls="c-amber", ccw=True),
            f'    <line x1="{ux - ru:.1f}" y1="{uy:.1f}" x2="{ux + ru:.1f}" y2="{uy:.1f}" class="c-main" />',
            arc_path(ux, uy, ru, 0.0, 180.0, cls="c-green-dash", ccw=True),
            mid_arrow_path(
                "M 224.0 94.0 Q 192.0 102.0 166.0 122.0",
                168.0,
                120.5,
                -1.0,
                0.78,
                cls="c-blue",
                marker="arr-blue",
            ),
            mid_arrow_path(
                "M 196.0 190.0 Q 228.0 198.0 256.0 220.0",
                254.0,
                218.4,
                1.0,
                0.78,
                cls="c-red",
                marker="arr-red",
            ),
            arrow_line(364.0, 118.0, 364.0, 176.0, cls="c-green", marker="arr-green"),
        ]
    )
    labels = "\n".join(
        [
            point_dot(wx - rw, wy, color="#0f172a"),
            point_dot(wx, wy, color="#1e3a8a"),
            point_dot(wx + rw, wy, color="#0f172a"),
            point_dot(cx, cy, color="#0f172a"),
            point_dot(ux - ru, uy, color="#0f172a"),
            point_dot(ux, uy, color="#047857"),
            point_dot(ux + ru, uy, color="#0f172a"),
            math_label(wx, wy - 34.0, "W", sub="λ", color="#1e3a8a", anchor="middle"),
            math_label(wx - rw, wy + 18.0, "a", anchor="middle"),
            math_label(wx, wy + 18.0, "a", sub="λ", color="#1e3a8a", anchor="middle"),
            math_label(wx + rw, wy + 18.0, "b", anchor="middle"),
            math_label(108.0, 156.0, "S", sub="λ", color="#b45309", anchor="middle"),
            math_label(94.0, 178.0, "ω", sub="λ", color="#b45309"),
            math_label(cx - 6.0, cy + 14.0, "c", sub="λ", anchor="end"),
            math_label(42.0, 148.0, "γ", sub="λ", anchor="end"),
            math_label(122.0, 222.0, "γ", sub="λ+1"),
            math_label(190.0, 96.0, "φ", color="#1e3a8a", anchor="middle"),
            math_label(232.0, 192.0, "q", sub="λ", color="#dc2626"),
            math_label(372.0, 152.0, "Φ", sub="λ", color="#047857"),
            math_label(
                ux,
                uy - 36.0,
                "U",
                sub="ρ",
                sup="+",
                tail="(0)",
                color="#047857",
                anchor="middle",
            ),
            math_label(ux - ru, uy + 20.0, "−ρ", anchor="middle"),
            math_label(ux, uy + 20.0, "0", italic=False, anchor="middle"),
            math_label(ux + ru, uy + 20.0, "ρ", anchor="middle"),
        ]
    )
    return svg_document(
        "0 0 500 330",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="5_19",
        title="Schwarz-Christoffel corner mapping from W_lambda to S_lambda and U_rho^+(0)",
    )


CHAPTER_FIG_TITLES: dict[str, str] = {
    "5_1": "Region D with holes F_1, F_2 and outer complement F_0",
    "5_2": "Grid covering K of cycle Gamma in region Omega with complement F",
    "5_3": "Oriented boundary sides of square Q_lambda",
    "5_4": "Circle lambda_r centered at gamma(a) intersecting C_1 and C_2",
    "5_5": "Arc lambda of circle lambda_r inside region D at boundary point q",
    "5_6": "Disks U_rho(Q) and U_rho(P) on boundary Gamma of region Delta",
    "5_7": "Concentric circles lambda_varepsilon, lambda_r, lambda_delta centered at q in C",
    "5_8": "Homologous curves Gamma and f(C_r) around f(0) with connecting path mu",
    "5_9": "Schwarz reflection of region D across real segment (a, b)",
    "5_10": "Disk U_varepsilon(c) divided into half-disks V and V-bar",
    "5_11": "Reflection z to z* across line l through c_0 and c_1",
    "5_12": "Inversion z to z* with respect to circle centered at c",
    "5_13": "Reflection of region D into D* across arc gamma of circle C",
    "5_14": "Ideal curvilinear triangle D orthogonal to circle C with reflection D_3*",
    "5_15": "Modular tessellation of the unit disk by reflections of ideal triangle D",
    "5_16": "Ideal hexagon S^(1) = D union D_1 union D_2 union D_3 in unit disk",
    "5_17": "Reflected ideal polygon S^(2) in the unit disk",
    "5_18": "Polygonal region D (n = 9) with exterior angle theta_lambda at c_lambda",
    "5_19": "Schwarz-Christoffel corner mapping from W_lambda to S_lambda and U_rho^+(0)",
}

CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "5_1": fig_5_1,
    "5_2": fig_5_2,
    "5_3": fig_5_3,
    "5_4": fig_5_4,
    "5_5": fig_5_5,
    "5_6": fig_5_6,
    "5_7": fig_5_7,
    "5_8": fig_5_8,
    "5_9": fig_5_9,
    "5_10": fig_5_10,
    "5_11": fig_5_11,
    "5_12": fig_5_12,
    "5_13": fig_5_13,
    "5_14": fig_5_14,
    "5_15": fig_5_15,
    "5_16": fig_5_16,
    "5_17": fig_5_17,
    "5_18": fig_5_18,
    "5_19": fig_5_19,
}
