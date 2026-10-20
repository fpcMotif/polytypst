import math
from collections.abc import Callable

from ..vision.diagram_engine import (
    arc_path,
    arrow_line,
    axes_xy,
    circle_contour,
    math_label,
    mid_arrow_path,
    point_dot,
    smooth_curve,
    svg_document,
    tangent_arrow,
)

CHAPTER_FIG_TITLES: dict[str, str] = {
    "3_1": "Open neighborhood W = U_mu(a) inside image contour f(C) in the w-plane",
    "3_2": "Angle preservation under a conformal mapping w = f(z)",
    "3_3": "Conformal mapping w = z^2 sending concentric circles and rays to circles and doubled-angle rays",
    "3_4": "Conformal mapping w = z^2 sending a Cartesian grid to orthogonal confocal parabolas",
    "3_5": "Conformal mapping w = z^2 sending orthogonal hyperbolas to a Cartesian grid",
    "3_6": "Unit disk automorphism and similar triangles for inverse points alpha and alpha*",
    "3_7": "Stereographic projection between the Riemann sphere S and the complex plane",
    "3_8": "Cross-ratio argument relationships theta - psi = pi for four concyclic points",
    "3_9": "Cyclic orientation triples z_1 < z_2 < z_3 and z_3 < z_2 < z_1 on an oriented circle",
    "3_10": "Oriented circle C, secant line lambda through z_1 and z_2, and inscribed angle theta at z_3",
    "3_11": "Directed image line l' through z_1' and z_2' separating half-planes U' and V'",
    "3_12": "Lens domain D bounded by circular arcs C_1 and C_2 meeting at angle pi/m",
    "3_13": "Sector image f(D) of angle pi/m bounded by rays Gamma_1 and Gamma_2 in the zeta-plane",
    "3_14": "Crescent domain D between tangent circles C_1 and C_2 at the origin",
    "3_15": "Infinite horizontal strip f(D) between parallel lines l_1 and l_2 under zeta = 1/z",
}


def _plane_caption(x: float, y: float, var: str) -> str:
    return math_label(
        x,
        y,
        var,
        tail='<tspan class="lbl">-plane</tspan>',
        anchor="middle",
    )


def fig_3_1() -> str:
    ax, ay, r_w = 195.0, 138.0, 68.0
    ang = math.radians(63.0)
    tx = ax + r_w * math.cos(ang)
    ty = ay - r_w * math.sin(ang)

    regions = "\n".join(
        [
            f'    <circle cx="{ax:.1f}" cy="{ay:.1f}" r="{r_w:.1f}" class="f-amber" />',
            f'    <circle cx="{ax:.1f}" cy="{ay:.1f}" r="{r_w:.1f}" class="f-stipple" />',
        ]
    )

    outer_pts = [
        (188.0, 36.0),
        (tx, ty),
        (292.0, 66.0),
        (338.0, 108.0),
        (330.0, 156.0),
        (350.0, 218.0),
        (285.0, 268.0),
        (210.0, 258.0),
        (145.0, 262.0),
        (98.0, 218.0),
        (42.0, 182.0),
        (40.0, 115.0),
        (88.0, 52.0),
        (148.0, 26.0),
    ]
    nx, ny = math.sin(ang), math.cos(ang)
    ux, uy = math.cos(ang), -math.sin(ang)
    b0x, b0y = ax + nx * 4.0, ay + ny * 4.0
    b1x, b1y = tx + nx * 4.0, ty + ny * 4.0
    bmx, bmy = 0.5 * (b0x + b1x) + nx * 7.5, 0.5 * (b0y + b1y) + ny * 7.5
    brace_d = (
        f"M {b0x:.1f} {b0y:.1f} "
        f"Q {b0x + nx * 5.0 + ux * 8.0:.1f} {b0y + ny * 5.0 + uy * 8.0:.1f} "
        f"{bmx - ux * 3.0:.1f} {bmy - uy * 3.0:.1f} "
        f"L {bmx + nx * 3.0:.1f} {bmy + ny * 3.0:.1f} "
        f"L {bmx + ux * 3.0:.1f} {bmy + uy * 3.0:.1f} "
        f"Q {b1x + nx * 5.0 - ux * 8.0:.1f} {b1y + ny * 5.0 - uy * 8.0:.1f} "
        f"{b1x:.1f} {b1y:.1f}"
    )

    curves = "\n".join(
        [
            smooth_curve(outer_pts, cls="c-main", closed=True),
            f'    <circle cx="{ax:.1f}" cy="{ay:.1f}" r="{r_w:.1f}" class="c-sub" />',
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" class="c-blue" />',
            f'    <path d="{brace_d}" class="c-main" />',
        ]
    )

    labels = "\n".join(
        [
            point_dot(ax, ay),
            point_dot(165.0, 110.0),
            point_dot(188.0, 36.0),
            math_label(187.0, 155.0, "a"),
            math_label(158.0, 99.0, "w"),
            math_label(196.0, 32.0, "f", tail="(z)"),
            math_label(226.0, 118.0, "μ"),
            math_label(186.0, 182.0, "W"),
            math_label(280.0, 236.0, "f", tail="(C)"),
            _plane_caption(195.0, 310.0, "w"),
        ]
    )

    return svg_document(
        "0 0 420 325",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_1",
        title=CHAPTER_FIG_TITLES["3_1"],
    )


def fig_3_2() -> str:
    cx, cy = 105.0, 196.0
    ax, ay = 450.0, 200.0

    t1_deg, t2_deg = 64.0, 120.0
    t1_rad, t2_rad = math.radians(t1_deg), math.radians(t2_deg)
    lt1_x, lt1_y = cx + 112.0 * math.cos(t1_rad), cy - 112.0 * math.sin(t1_rad)
    lt2_x, lt2_y = cx + 112.0 * math.cos(t2_rad), cy - 112.0 * math.sin(t2_rad)

    w1_deg, w2_deg = 108.0, 162.0
    w1_rad, w2_rad = math.radians(w1_deg), math.radians(w2_deg)
    wt1_x, wt1_y = ax + 112.0 * math.cos(w1_rad), ay - 112.0 * math.sin(w1_rad)
    wt2_x, wt2_y = ax + 112.0 * math.cos(w2_rad), ay - 112.0 * math.sin(w2_rad)

    gamma1_pts = [(cx, cy), (132.0, 154.0), (174.0, 124.0), (226.0, 100.0)]
    gamma2_pts = [(cx, cy), (95.0, 138.0), (101.0, 78.0), (116.0, 26.0)]

    lambda1_pts = [(ax, ay), (446.0, 142.0), (458.0, 84.0), (482.0, 30.0)]
    lambda2_pts = [(ax, ay), (402.0, 158.0), (362.0, 114.0), (330.0, 66.0)]

    arc_l = arc_path(cx, cy, 48.0, t1_deg, t2_deg, cls="c-main", ccw=True)
    end_l_x = cx + 48.0 * math.cos(t2_rad)
    end_l_y = cy - 48.0 * math.sin(t2_rad)
    arr_l = tangent_arrow(
        end_l_x,
        end_l_y,
        -math.sin(t2_rad),
        -math.cos(t2_rad),
        marker="arr",
    )

    arc_r = arc_path(ax, ay, 48.0, w1_deg, w2_deg, cls="c-main", ccw=True)
    end_r_x = ax + 48.0 * math.cos(w2_rad)
    end_r_y = ay - 48.0 * math.sin(w2_rad)
    arr_r = tangent_arrow(
        end_r_x,
        end_r_y,
        -math.sin(w2_rad),
        -math.cos(w2_rad),
        marker="arr",
    )

    curves = "\n".join(
        [
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{lt1_x:.1f}" y2="{lt1_y:.1f}" class="c-sub" />',
            f'    <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{lt2_x:.1f}" y2="{lt2_y:.1f}" class="c-sub" />',
            smooth_curve(
                gamma1_pts, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                gamma2_pts, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            arc_l,
            arr_l,
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{wt1_x:.1f}" y2="{wt1_y:.1f}" class="c-sub" />',
            f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{wt2_x:.1f}" y2="{wt2_y:.1f}" class="c-sub" />',
            smooth_curve(
                lambda1_pts, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                lambda2_pts, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            arc_r,
            arr_r,
        ]
    )

    labels = "\n".join(
        [
            point_dot(cx, cy),
            point_dot(ax, ay),
            math_label(100.0, 214.0, "c"),
            math_label(232.0, 102.0, "γ", sub="1"),
            math_label(122.0, 30.0, "γ", sub="2"),
            math_label(103.0, 141.0, "θ"),
            math_label(458.0, 204.0, "a", tail=" = f(c)"),
            math_label(487.0, 34.0, "λ", sub="1"),
            math_label(320.0, 58.0, "λ", sub="2"),
            math_label(414.0, 159.0, "θ"),
            _plane_caption(110.0, 258.0, "z"),
            _plane_caption(435.0, 258.0, "w"),
        ]
    )

    return svg_document(
        "0 0 560 278",
        curve=curves,
        label=labels,
        fig_id="3_2",
        title=CHAPTER_FIG_TITLES["3_2"],
    )


def fig_3_3() -> str:
    zx, zy = 145.0, 136.0
    wx, wy = 415.0, 136.0

    ax_z, lbl_z = axes_xy(
        zx, zy, 45.0, 245.0, 36.0, 232.0, x_label="x", y_label="iy", origin_label=""
    )
    ax_w, lbl_w = axes_xy(
        wx, wy, 315.0, 515.0, 36.0, 232.0, x_label="u", y_label="iv", origin_label=""
    )

    regions = "\n".join(
        [
            f'    <circle cx="{zx:.1f}" cy="{zy:.1f}" r="74.0" class="f-blue" />',
            f'    <circle cx="{wx:.1f}" cy="{wy:.1f}" r="74.0" class="f-amber" />',
        ]
    )

    curve_parts: list[str] = []
    for r in (28.0, 51.0, 74.0):
        curve_parts.append(circle_contour(zx, zy, r, cls="c-blue"))
    for k in range(1, 8):
        if k == 4:
            continue
        ang = math.radians(k * 22.5)
        dx, dy = 82.0 * math.cos(ang), 82.0 * math.sin(ang)
        curve_parts.append(
            f'    <line x1="{zx - dx:.1f}" y1="{zy + dy:.1f}" x2="{zx + dx:.1f}" y2="{zy - dy:.1f}" class="c-sub" />'
        )

    for r in (16.0, 42.0, 74.0):
        curve_parts.append(circle_contour(wx, wy, r, cls="c-blue"))
    for deg in (45.0, 135.0):
        ang = math.radians(deg)
        dx, dy = 82.0 * math.cos(ang), 82.0 * math.sin(ang)
        curve_parts.append(
            f'    <line x1="{wx - dx:.1f}" y1="{wy + dy:.1f}" x2="{wx + dx:.1f}" y2="{wy - dy:.1f}" class="c-sub" />'
        )

    labels = "\n".join(
        [
            lbl_z,
            lbl_w,
            math_label(zx + 76.0, zy + 15.0, "1", italic=False),
            math_label(zx + 4.0, zy - 77.0, "i"),
            math_label(wx + 76.0, wy + 15.0, "1", italic=False),
            math_label(wx + 4.0, wy - 77.0, "i"),
            _plane_caption(zx, 262.0, "z"),
            _plane_caption(wx, 262.0, "w"),
        ]
    )

    return svg_document(
        "0 0 560 282",
        grid=f"{ax_z}\n{ax_w}",
        region=regions,
        curve="\n".join(curve_parts),
        label=labels,
        fig_id="3_3",
        title=CHAPTER_FIG_TITLES["3_3"],
    )


def fig_3_4() -> str:
    zx, zy = 145.0, 142.0
    wx, wy = 415.0, 142.0

    ax_z, lbl_z = axes_xy(
        zx, zy, 45.0, 245.0, 38.0, 246.0, x_label="x", y_label="iy", origin_label=""
    )
    ax_w, lbl_w = axes_xy(
        wx, wy, 305.0, 520.0, 28.0, 256.0, x_label="u", y_label="iv", origin_label=""
    )

    curve_parts: list[str] = []
    step = 18.0
    for k in (-4, -3, -2, -1, 1, 2, 3, 4):
        span = 60.0 if abs(k) == 4 else 78.0
        off = k * step
        curve_parts.append(
            f'    <line x1="{zx + off:.1f}" y1="{zy - span:.1f}" x2="{zx + off:.1f}" y2="{zy + span:.1f}" class="c-blue" />'
        )
        curve_parts.append(
            f'    <line x1="{zx - span:.1f}" y1="{zy - off:.1f}" x2="{zx + span:.1f}" y2="{zy - off:.1f}" class="c-green" />'
        )

    w_scale = 52.0
    a_vals = (0.34, 0.56, 0.78, 1.00)
    t_spans = (1.18, 1.12, 1.04, 0.94)
    for a, tmax in zip(a_vals, t_spans, strict=True):
        pts_left: list[tuple[float, float]] = []
        pts_right: list[tuple[float, float]] = []
        for idx in range(19):
            t = -tmax + 2.0 * tmax * idx / 18.0
            u_l = a * a - t * t
            v_l = 2.0 * a * t
            pts_left.append((wx + w_scale * u_l, wy - w_scale * v_l))
            u_r = t * t - a * a
            v_r = 2.0 * a * t
            pts_right.append((wx + w_scale * u_r, wy - w_scale * v_r))
        curve_parts.append(smooth_curve(pts_left, cls="c-blue"))
        curve_parts.append(smooth_curve(pts_right, cls="c-green"))

    labels = "\n".join(
        [
            lbl_z,
            lbl_w,
            math_label(zx + 3.0 * step + 3.0, zy + 15.0, "1", italic=False),
            math_label(zx + 4.0, zy - 3.0 * step - 4.0, "i"),
            _plane_caption(zx, 276.0, "z"),
            _plane_caption(wx, 276.0, "w"),
        ]
    )

    return svg_document(
        "0 0 560 296",
        grid=f"{ax_z}\n{ax_w}",
        curve="\n".join(curve_parts),
        label=labels,
        fig_id="3_4",
        title=CHAPTER_FIG_TITLES["3_4"],
    )


def fig_3_5() -> str:
    zx, zy = 145.0, 142.0
    wx, wy = 415.0, 142.0

    ax_z, lbl_z = axes_xy(
        zx, zy, 40.0, 250.0, 36.0, 248.0, x_label="x", y_label="iy", origin_label=""
    )
    ax_w, lbl_w = axes_xy(
        wx, wy, 310.0, 520.0, 36.0, 248.0, x_label="u", y_label="iv", origin_label=""
    )

    curve_parts: list[str] = [
        f'    <line x1="{zx - 68.0:.1f}" y1="{zy + 68.0:.1f}" x2="{zx + 68.0:.1f}" y2="{zy - 68.0:.1f}" class="c-sub" />',
        f'    <line x1="{zx - 68.0:.1f}" y1="{zy - 68.0:.1f}" x2="{zx + 68.0:.1f}" y2="{zy + 68.0:.1f}" class="c-sub" />',
    ]

    z_scale = 76.0
    for k in (1, 2, 3, 4):
        alpha = k * 0.22
        v_lim = 0.94 if k < 4 else 0.72
        for sgn in (-1.0, 1.0):
            pts_u_pos: list[tuple[float, float]] = []
            pts_u_neg: list[tuple[float, float]] = []
            pts_v_pos: list[tuple[float, float]] = []
            pts_v_neg: list[tuple[float, float]] = []
            for idx in range(17):
                t = -v_lim + 2.0 * v_lim * idx / 16.0
                r_pos = math.hypot(alpha, t)
                x_p = sgn * math.sqrt(0.5 * (r_pos + alpha))
                y_p = (
                    sgn
                    * (1.0 if t >= 0.0 else -1.0)
                    * math.sqrt(max(0.0, 0.5 * (r_pos - alpha)))
                )
                pts_u_pos.append((zx + z_scale * x_p, zy - z_scale * y_p))
                pts_u_neg.append((zx - z_scale * y_p, zy - z_scale * x_p))

                r_v = math.hypot(t, alpha)
                xv = sgn * math.sqrt(0.5 * (r_v + t))
                yv = sgn * math.sqrt(max(0.0, 0.5 * (r_v - t)))
                pts_v_pos.append((zx + z_scale * xv, zy - z_scale * yv))
                pts_v_neg.append((zx - z_scale * xv, zy - z_scale * yv))

            curve_parts.append(smooth_curve(pts_u_pos, cls="c-blue"))
            curve_parts.append(smooth_curve(pts_u_neg, cls="c-blue"))
            curve_parts.append(smooth_curve(pts_v_pos, cls="c-green"))
            curve_parts.append(smooth_curve(pts_v_neg, cls="c-green"))

    step = 17.5
    span = 75.0
    for k in (-4, -3, -2, -1, 1, 2, 3, 4):
        off = k * step
        curve_parts.append(
            f'    <line x1="{wx + off:.1f}" y1="{wy - span:.1f}" x2="{wx + off:.1f}" y2="{wy + span:.1f}" class="c-blue" />'
        )
        curve_parts.append(
            f'    <line x1="{wx - span:.1f}" y1="{wy - off:.1f}" x2="{wx + span:.1f}" y2="{wy - off:.1f}" class="c-green" />'
        )

    labels = "\n".join(
        [
            lbl_z,
            lbl_w,
            math_label(zx + z_scale + 4.0, zy + 15.0, "1", italic=False),
            math_label(zx + 4.0, zy - z_scale - 4.0, "i"),
            _plane_caption(zx, 276.0, "z"),
            _plane_caption(wx, 276.0, "w"),
        ]
    )

    return svg_document(
        "0 0 560 296",
        grid=f"{ax_z}\n{ax_w}",
        curve="\n".join(curve_parts),
        label=labels,
        fig_id="3_5",
        title=CHAPTER_FIG_TITLES["3_5"],
    )


def fig_3_6() -> str:
    ox, oy = 185.0, 160.0
    r = 92.0
    ax_str, lbl_ax = axes_xy(
        ox, oy, 55.0, 355.0, 22.0, 274.0, x_label="", y_label="", origin_label="0"
    )

    ang_a = math.radians(28.0)
    ang_z = math.radians(57.0)
    r_a = 0.62 * r
    r_astar = r * r / r_a
    r_ray = 195.0

    ax_pt = (ox + r_a * math.cos(ang_a), oy - r_a * math.sin(ang_a))
    astar_pt = (ox + r_astar * math.cos(ang_a), oy - r_astar * math.sin(ang_a))
    ray_end = (ox + r_ray * math.cos(ang_a), oy - r_ray * math.sin(ang_a))
    z_pt = (ox + r * math.cos(ang_z), oy - r * math.sin(ang_z))

    regions = f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r:.1f}" class="f-blue" />'

    curves = "\n".join(
        [
            circle_contour(ox, oy, r, cls="c-main"),
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{ray_end[0]:.1f}" y2="{ray_end[1]:.1f}" class="c-blue" />',
            f'    <line x1="{ox:.1f}" y1="{oy:.1f}" x2="{z_pt[0]:.1f}" y2="{z_pt[1]:.1f}" class="c-main" />',
            f'    <line x1="{z_pt[0]:.1f}" y1="{z_pt[1]:.1f}" x2="{ax_pt[0]:.1f}" y2="{ax_pt[1]:.1f}" class="c-red" />',
            f'    <line x1="{z_pt[0]:.1f}" y1="{z_pt[1]:.1f}" x2="{astar_pt[0]:.1f}" y2="{astar_pt[1]:.1f}" class="c-red" />',
        ]
    )

    labels = "\n".join(
        [
            lbl_ax,
            point_dot(z_pt[0], z_pt[1]),
            point_dot(ax_pt[0], ax_pt[1]),
            point_dot(astar_pt[0], astar_pt[1]),
            math_label(ox + r + 5.0, oy + 16.0, "1", italic=False),
            math_label(ox - 12.0, oy - r - 6.0, "i"),
            math_label(z_pt[0] + 2.0, z_pt[1] - 8.0, "z"),
            math_label(ax_pt[0] + 1.0, ax_pt[1] + 15.0, "α"),
            math_label(astar_pt[0] + 1.0, astar_pt[1] + 16.0, "α", sup="*"),
        ]
    )

    return svg_document(
        "0 0 430 296",
        grid=ax_str,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_6",
        title=CHAPTER_FIG_TITLES["3_6"],
    )


def fig_3_7() -> str:
    cx, cy = 220.0, 175.0
    r = 108.0
    nx, ny = cx, cy - r
    sx, sy = cx, cy + 97.0
    xi_x, xi_y = 292.0, 173.0
    zx, zy = 352.0, 258.0

    axes = "\n".join(
        [
            arrow_line(58.0, 149.0, 398.0, 203.0, cls="ax", marker="arr-axis"),
            '    <line x1="82.0" y1="258.0" x2="262.0" y2="150.0" class="ax" />',
            '    <line x1="262.0" y1="150.0" x2="313.0" y2="119.0" class="c-dash" />',
            arrow_line(313.0, 119.0, 366.0, 87.0, cls="ax", marker="arr-axis"),
            f'    <line x1="{cx:.1f}" y1="316.0" x2="{cx:.1f}" y2="283.0" class="ax" />',
            arrow_line(cx, 283.0, cx, 20.0, cls="ax", marker="arr-axis"),
        ]
    )

    regions = "\n".join(
        [
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-blue" />',
            f'    <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.1f}" ry="30.0" class="f-amber" />',
        ]
    )

    curves = "\n".join(
        [
            circle_contour(cx, cy, r, cls="c-main"),
            f'    <path d="M {cx - r:.1f} {cy:.1f} A {r:.1f} 30.0 0 0 0 {cx + r:.1f} {cy:.1f}" class="c-blue" />',
            f'    <path d="M {cx - r:.1f} {cy:.1f} A {r:.1f} 30.0 0 0 1 {cx + r:.1f} {cy:.1f}" class="c-blue-dash" />',
            f'    <line x1="{nx:.1f}" y1="{ny:.1f}" x2="{zx:.1f}" y2="{zy:.1f}" class="c-red" />',
        ]
    )

    labels = "\n".join(
        [
            point_dot(nx, ny),
            point_dot(sx, sy),
            point_dot(xi_x, xi_y),
            point_dot(zx, zy),
            math_label(197.0, 75.0, "N"),
            math_label(224.0, 193.0, "0", italic=False),
            math_label(300.0, 173.0, "ξ"),
            math_label(359.0, 263.0, "z"),
            math_label(384.0, 225.0, "ξ", sub="1"),
            math_label(370.0, 93.0, "ξ", sub="2"),
            math_label(198.0, 32.0, "ξ", sub="3"),
        ]
    )

    return svg_document(
        "0 0 450 332",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_7",
        title=CHAPTER_FIG_TITLES["3_7"],
    )


def _directed_vertex_arc(
    vx: float,
    vy: float,
    p_from: tuple[float, float],
    p_to: tuple[float, float],
    r: float,
    ccw: bool,
) -> str:
    deg1 = math.degrees(math.atan2(vy - p_from[1], p_from[0] - vx))
    deg2 = math.degrees(math.atan2(vy - p_to[1], p_to[0] - vx))
    arc = arc_path(vx, vy, r, deg1, deg2, cls="c-main", ccw=ccw)
    r2 = math.radians(deg2)
    ex = vx + r * math.cos(r2)
    ey = vy - r * math.sin(r2)
    sgn = 1.0 if ccw else -1.0
    dx, dy = -sgn * math.sin(r2), -sgn * math.cos(r2)
    arr = tangent_arrow(ex, ey, dx, dy, marker="arr")
    return f"{arc}\n{arr}"


def fig_3_8() -> str:
    lx, ly, r = 135.0, 124.0, 88.0
    rx, ry = 415.0, 124.0

    def pt_on(cx: float, cy: float, deg: float) -> tuple[float, float]:
        rad = math.radians(deg)
        return (cx + r * math.cos(rad), cy - r * math.sin(rad))

    lz = pt_on(lx, ly, 104.0)
    lz1 = pt_on(lx, ly, 8.0)
    lz2 = pt_on(lx, ly, -46.0)
    lz3 = pt_on(lx, ly, -134.0)

    rz2 = pt_on(rx, ry, 80.0)
    rz3 = pt_on(rx, ry, 10.0)
    rz = pt_on(rx, ry, -46.0)
    rz1 = pt_on(rx, ry, -134.0)

    l_poly = f'    <polygon points="{lz[0]:.1f},{lz[1]:.1f} {lz1[0]:.1f},{lz1[1]:.1f} {lz2[0]:.1f},{lz2[1]:.1f} {lz3[0]:.1f},{lz3[1]:.1f}" class="f-blue" />'
    r_poly = f'    <polygon points="{rz2[0]:.1f},{rz2[1]:.1f} {rz3[0]:.1f},{rz3[1]:.1f} {rz[0]:.1f},{rz[1]:.1f} {rz1[0]:.1f},{rz1[1]:.1f}" class="f-amber" />'
    regions = f"{l_poly}\n{r_poly}"

    curves = "\n".join(
        [
            circle_contour(lx, ly, r, cls="c-main"),
            f'    <polygon points="{lz[0]:.1f},{lz[1]:.1f} {lz1[0]:.1f},{lz1[1]:.1f} {lz2[0]:.1f},{lz2[1]:.1f} {lz3[0]:.1f},{lz3[1]:.1f}" class="c-blue" />',
            _directed_vertex_arc(lz[0], lz[1], lz3, lz1, 28.0, ccw=True),
            _directed_vertex_arc(lz2[0], lz2[1], lz3, lz1, 28.0, ccw=False),
            circle_contour(rx, ry, r, cls="c-main"),
            f'    <polygon points="{rz2[0]:.1f},{rz2[1]:.1f} {rz3[0]:.1f},{rz3[1]:.1f} {rz[0]:.1f},{rz[1]:.1f} {rz1[0]:.1f},{rz1[1]:.1f}" class="c-blue" />',
            _directed_vertex_arc(rz2[0], rz2[1], rz3, rz1, 28.0, ccw=False),
            _directed_vertex_arc(rz[0], rz[1], rz3, rz1, 28.0, ccw=True),
        ]
    )

    labels = "\n".join(
        [
            point_dot(lz[0], lz[1]),
            point_dot(lz1[0], lz1[1]),
            point_dot(lz2[0], lz2[1]),
            point_dot(lz3[0], lz3[1]),
            math_label(lz[0] - 4.0, lz[1] - 8.0, "z"),
            math_label(lz1[0] + 6.0, lz1[1] + 5.0, "z", sub="1"),
            math_label(lz2[0] + 5.0, lz2[1] + 13.0, "z", sub="2"),
            math_label(lz3[0] - 18.0, lz3[1] + 14.0, "z", sub="3"),
            math_label(lz[0] + 4.0, lz[1] + 43.0, "θ"),
            math_label(lz2[0] - 26.0, lz2[1] - 24.0, "ψ"),
            math_label(lx, 256.0, "θ − ψ = π", anchor="middle"),
            point_dot(rz2[0], rz2[1]),
            point_dot(rz3[0], rz3[1]),
            point_dot(rz[0], rz[1]),
            point_dot(rz1[0], rz1[1]),
            math_label(rz2[0] - 3.0, rz2[1] - 8.0, "z", sub="2"),
            math_label(rz3[0] + 6.0, rz3[1] + 5.0, "z", sub="3"),
            math_label(rz[0] + 6.0, rz[1] + 12.0, "z"),
            math_label(rz1[0] - 18.0, rz1[1] + 14.0, "z", sub="1"),
            math_label(rz2[0] + 2.0, rz2[1] + 44.0, "ψ"),
            math_label(rz[0] - 22.0, rz[1] - 28.0, "θ"),
            math_label(rx, 256.0, "θ − ψ = π", anchor="middle"),
        ]
    )

    return svg_document(
        "0 0 550 278",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_8",
        title=CHAPTER_FIG_TITLES["3_8"],
    )


def fig_3_9() -> str:
    lx, ly, r = 138.0, 124.0, 84.0
    rx, ry = 412.0, 124.0

    def pt_on(cx: float, cy: float, deg: float) -> tuple[float, float]:
        rad = math.radians(deg)
        return (cx + r * math.cos(rad), cy - r * math.sin(rad))

    lz1 = pt_on(lx, ly, 192.0)
    lz2 = pt_on(lx, ly, -14.0)
    lz3 = pt_on(lx, ly, 44.0)

    rz1 = pt_on(rx, ry, 190.0)
    rz2 = pt_on(rx, ry, 142.0)
    rz3 = pt_on(rx, ry, 44.0)

    def circle_arrow(cx: float, cy: float, deg: float) -> str:
        rad = math.radians(deg)
        px, py = cx + r * math.cos(rad), cy - r * math.sin(rad)
        return tangent_arrow(px, py, -math.sin(rad), -math.cos(rad), marker="arr-blue")

    regions = "\n".join(
        [
            f'    <circle cx="{lx:.1f}" cy="{ly:.1f}" r="{r:.1f}" class="f-blue" />',
            f'    <circle cx="{rx:.1f}" cy="{ry:.1f}" r="{r:.1f}" class="f-amber" />',
        ]
    )

    curves = "\n".join(
        [
            circle_contour(lx, ly, r, cls="c-blue"),
            circle_arrow(lx, ly, -90.0),
            circle_arrow(lx, ly, 14.0),
            circle_arrow(lx, ly, 120.0),
            circle_contour(rx, ry, r, cls="c-blue"),
            circle_arrow(rx, ry, -90.0),
            circle_arrow(rx, ry, 92.0),
            circle_arrow(rx, ry, 166.0),
        ]
    )

    labels = "\n".join(
        [
            point_dot(lz1[0], lz1[1]),
            point_dot(lz2[0], lz2[1]),
            point_dot(lz3[0], lz3[1]),
            math_label(lz1[0] - 20.0, lz1[1] + 5.0, "z", sub="1"),
            math_label(lz2[0] + 7.0, lz2[1] + 5.0, "z", sub="2"),
            math_label(lz3[0] + 7.0, lz3[1] + 2.0, "z", sub="3"),
            math_label(lx - 8.0, ly + r + 20.0, "C", sub="1"),
            math_label(lx - 52.0, ly - r - 6.0, "C", sub="2"),
            math_label(lx - 42.0, 260.0, "z", sub="1", tail=" ≺ z"),
            math_label(lx + 11.0, 260.0, "", sub="2", tail=" ≺ z"),
            math_label(lx + 49.0, 260.0, "", sub="3"),
            point_dot(rz1[0], rz1[1]),
            point_dot(rz2[0], rz2[1]),
            point_dot(rz3[0], rz3[1]),
            math_label(rz1[0] - 20.0, rz1[1] + 5.0, "z", sub="1"),
            math_label(rz2[0] - 20.0, rz2[1] - 2.0, "z", sub="2"),
            math_label(rz3[0] + 7.0, rz3[1] + 2.0, "z", sub="3"),
            math_label(rx - 8.0, ry + r + 20.0, "C", sub="1"),
            math_label(rx - 14.0, ry - r - 10.0, "C", sub="2"),
            math_label(rx - 42.0, 260.0, "z", sub="3", tail=" ≺ z"),
            math_label(rx + 11.0, 260.0, "", sub="2", tail=" ≺ z"),
            math_label(rx + 49.0, 260.0, "", sub="1"),
        ]
    )

    return svg_document(
        "0 0 550 280",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_9",
        title=CHAPTER_FIG_TITLES["3_9"],
    )


def fig_3_10() -> str:
    cx, cy, r = 225.0, 146.0, 102.0

    def pt_on(deg: float) -> tuple[float, float]:
        rad = math.radians(deg)
        return (cx + r * math.cos(rad), cy - r * math.sin(rad))

    z1 = pt_on(202.0)
    z2 = pt_on(-42.0)
    z3 = pt_on(48.0)

    dx_l, dy_l = z2[0] - z1[0], z2[1] - z1[1]
    l_start = (z1[0] - 0.38 * dx_l, z1[1] - 0.38 * dy_l)
    l_end = (z2[0] + 0.38 * dx_l, z2[1] + 0.38 * dy_l)

    def circle_arrow(deg: float) -> str:
        rad = math.radians(deg)
        px, py = cx + r * math.cos(rad), cy - r * math.sin(rad)
        return tangent_arrow(px, py, -math.sin(rad), -math.cos(rad), marker="arr-blue")

    regions = f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="f-blue" />'

    m_lam = (0.5 * (z1[0] + z2[0]), 0.5 * (z1[1] + z2[1]))
    m_31 = (0.5 * (z3[0] + z1[0]), 0.5 * (z3[1] + z1[1]))
    m_32 = (0.5 * (z3[0] + z2[0]), 0.5 * (z3[1] + z2[1]))

    curves = "\n".join(
        [
            circle_contour(cx, cy, r, cls="c-blue"),
            circle_arrow(122.0),
            circle_arrow(-90.0),
            circle_arrow(8.0),
            mid_arrow_path(
                f"M {l_start[0]:.1f} {l_start[1]:.1f} L {l_end[0]:.1f} {l_end[1]:.1f}",
                m_lam[0],
                m_lam[1],
                dx_l,
                dy_l,
                cls="c-main",
                marker="arr",
            ),
            mid_arrow_path(
                f"M {z3[0]:.1f} {z3[1]:.1f} L {z1[0]:.1f} {z1[1]:.1f}",
                m_31[0],
                m_31[1],
                z1[0] - z3[0],
                z1[1] - z3[1],
                cls="c-main",
                marker="arr",
            ),
            mid_arrow_path(
                f"M {z3[0]:.1f} {z3[1]:.1f} L {z2[0]:.1f} {z2[1]:.1f}",
                m_32[0],
                m_32[1],
                z2[0] - z3[0],
                z2[1] - z3[1],
                cls="c-main",
                marker="arr",
            ),
            _directed_vertex_arc(z3[0], z3[1], z1, z2, 38.0, ccw=True),
        ]
    )

    labels = "\n".join(
        [
            point_dot(z1[0], z1[1]),
            point_dot(z2[0], z2[1]),
            point_dot(z3[0], z3[1]),
            math_label(142.0, 62.0, "C"),
            math_label(z1[0] - 20.0, z1[1] + 16.0, "z", sub="1"),
            math_label(z2[0] + 4.0, z2[1] + 18.0, "z", sub="2"),
            math_label(z3[0] + 6.0, z3[1] + 2.0, "z", sub="3"),
            math_label(m_lam[0] - 4.0, m_lam[1] - 8.0, "λ"),
            math_label(264.0, 118.0, "θ"),
            math_label(232.0, 148.0, "U"),
            math_label(82.0, 224.0, "V"),
        ]
    )

    return svg_document(
        "0 0 430 284",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_10",
        title=CHAPTER_FIG_TITLES["3_10"],
    )


def fig_3_11() -> str:
    p0 = (65.0, 252.0)
    p1 = (365.0, 32.0)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]

    z1p = (p0[0] + 0.31 * dx, p0[1] + 0.31 * dy)
    z2p = (p0[0] + 0.70 * dx, p0[1] + 0.70 * dy)
    ml = (p0[0] + 0.50 * dx, p0[1] + 0.50 * dy)
    fz = (118.0, 72.0)
    mf = (0.5 * (z1p[0] + fz[0]), 0.5 * (z1p[1] + fz[1]))

    regions = f'    <polygon points="{p0[0]:.1f},{p0[1]:.1f} {p1[0]:.1f},{p1[1]:.1f} {p0[0]:.1f},{p1[1]:.1f}" class="f-blue" />'

    curves = "\n".join(
        [
            mid_arrow_path(
                f"M {p0[0]:.1f} {p0[1]:.1f} L {p1[0]:.1f} {p1[1]:.1f}",
                ml[0],
                ml[1],
                dx,
                dy,
                cls="c-blue",
                marker="arr-blue",
            ),
            mid_arrow_path(
                f"M {z1p[0]:.1f} {z1p[1]:.1f} L {fz[0]:.1f} {fz[1]:.1f}",
                mf[0],
                mf[1],
                fz[0] - z1p[0],
                fz[1] - z1p[1],
                cls="c-main",
                marker="arr",
            ),
        ]
    )

    labels = "\n".join(
        [
            point_dot(z1p[0], z1p[1]),
            point_dot(z2p[0], z2p[1]),
            point_dot(fz[0], fz[1]),
            math_label(z1p[0] + 4.0, z1p[1] + 17.0, "z", sub="1", sup="′"),
            math_label(z2p[0] + 6.0, z2p[1] + 15.0, "z", sub="2", sup="′"),
            math_label(ml[0] + 8.0, ml[1] + 18.0, "l", sup="′"),
            math_label(fz[0] - 24.0, fz[1] - 12.0, "f", tail="(z)"),
            math_label(215.0, 66.0, "U", sup="′"),
            math_label(308.0, 178.0, "V", sup="′"),
        ]
    )

    return svg_document(
        "0 0 420 280",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_11",
        title=CHAPTER_FIG_TITLES["3_11"],
    )


def fig_3_12() -> str:
    bx, by = 58.0, 176.0
    dx_pt, dy_pt = 422.0, 60.0
    mx, my = 0.5 * (bx + dx_pt), 0.5 * (by + dy_pt)

    c1_pts = [(bx, by), (165.0, 182.0), (275.0, 154.0), (dx_pt, dy_pt)]
    c2_pts = [(bx, by), (155.0, 96.0), (275.0, 52.0), (dx_pt, dy_pt)]
    lens_d = (
        f"M {bx:.1f} {by:.1f} "
        f"C 165.0 184.0, 290.0 156.0, {dx_pt:.1f} {dy_pt:.1f} "
        f"C 285.0 42.0, 155.0 82.0, {bx:.1f} {by:.1f} Z"
    )

    regions = "\n".join(
        [
            f'    <path d="{lens_d}" class="f-amber" />',
            f'    <path d="{lens_d}" class="f-stipple" />',
        ]
    )

    deg_t1 = -9.0
    deg_l = math.degrees(math.atan2(by - dy_pt, dx_pt - bx))
    deg_t2 = 51.0
    t1_end = (
        bx + 136.0 * math.cos(math.radians(deg_t1)),
        by - 136.0 * math.sin(math.radians(deg_t1)),
    )
    t2_end = (
        bx + 114.0 * math.cos(math.radians(deg_t2)),
        by - 114.0 * math.sin(math.radians(deg_t2)),
    )

    arc_psi = arc_path(bx, by, 64.0, deg_t1, deg_l, cls="c-main", ccw=True)
    psi_end_x = bx + 64.0 * math.cos(math.radians(deg_l))
    psi_end_y = by - 64.0 * math.sin(math.radians(deg_l))
    arr_psi = tangent_arrow(
        psi_end_x,
        psi_end_y,
        -math.sin(math.radians(deg_l)),
        -math.cos(math.radians(deg_l)),
        marker="arr",
    )

    arc_pim = arc_path(bx, by, 84.0, deg_t1, deg_t2, cls="c-main", ccw=True)
    pim_end_x = bx + 84.0 * math.cos(math.radians(deg_t2))
    pim_end_y = by - 84.0 * math.sin(math.radians(deg_t2))
    arr_pim = tangent_arrow(
        pim_end_x,
        pim_end_y,
        -math.sin(math.radians(deg_t2)),
        -math.cos(math.radians(deg_t2)),
        marker="arr",
    )

    lx_arr = bx + 0.38 * (dx_pt - bx)
    ly_arr = by + 0.38 * (dy_pt - by)

    curves = "\n".join(
        [
            smooth_curve(
                c1_pts, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            smooth_curve(
                c2_pts, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"
            ),
            mid_arrow_path(
                f"M {bx:.1f} {by:.1f} L {dx_pt:.1f} {dy_pt:.1f}",
                lx_arr,
                ly_arr,
                dx_pt - bx,
                dy_pt - by,
                cls="c-main",
                marker="arr",
            ),
            arrow_line(bx, by, t1_end[0], t1_end[1], cls="c-main", marker="arr"),
            arrow_line(bx, by, t2_end[0], t2_end[1], cls="c-main", marker="arr"),
            arc_psi,
            arr_psi,
            arc_pim,
            arr_pim,
        ]
    )

    labels = "\n".join(
        [
            point_dot(bx, by),
            point_dot(mx, my),
            point_dot(dx_pt, dy_pt),
            math_label(38.0, 184.0, "β"),
            math_label(429.0, 64.0, "δ"),
            math_label(mx - 4.0, my + 18.0, "μ"),
            math_label(184.0, 124.0, "L"),
            math_label(254.0, 184.0, "C", sub="1"),
            math_label(214.0, 48.0, "C", sub="2"),
            math_label(272.0, 88.0, "D"),
            math_label(106.0, 177.0, "ψ"),
            math_label(132.0, 132.0, "π/m"),
            _plane_caption(240.0, 238.0, "z"),
        ]
    )

    return svg_document(
        "0 0 480 258",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_12",
        title=CHAPTER_FIG_TITLES["3_12"],
    )


def fig_3_13() -> str:
    ox, oy = 68.0, 232.0
    deg_psi = 27.0
    deg_top = 60.0

    r_edge = 330.0
    g1_end = (ox + r_edge, oy)
    g2_end = (
        ox + 245.0 * math.cos(math.radians(deg_top)),
        oy - 245.0 * math.sin(math.radians(deg_top)),
    )
    g_end = (
        ox + 302.0 * math.cos(math.radians(deg_psi)),
        oy - 302.0 * math.sin(math.radians(deg_psi)),
    )

    wedge_d = (
        f"M {ox:.1f} {oy:.1f} L {g1_end[0]:.1f} {g1_end[1]:.1f} "
        f"Q 388.0 105.0 {g2_end[0]:.1f} {g2_end[1]:.1f} Z"
    )
    regions = "\n".join(
        [
            f'    <path d="{wedge_d}" class="f-amber" />',
            f'    <path d="{wedge_d}" class="f-stipple" />',
        ]
    )

    e_psi = (
        ox + 150.0 * math.cos(math.radians(deg_psi)),
        oy - 150.0 * math.sin(math.radians(deg_psi)),
    )
    g_arr = (
        ox + 215.0 * math.cos(math.radians(deg_psi)),
        oy - 215.0 * math.sin(math.radians(deg_psi)),
    )
    g1_arr = (ox + 205.0, oy)
    g2_arr = (
        ox + 155.0 * math.cos(math.radians(deg_top)),
        oy - 155.0 * math.sin(math.radians(deg_top)),
    )

    arc_psi = arc_path(ox, oy, 76.0, 0.0, deg_psi, cls="c-main", ccw=True)
    psi_end_x = ox + 76.0 * math.cos(math.radians(deg_psi))
    psi_end_y = oy - 76.0 * math.sin(math.radians(deg_psi))
    arr_psi = tangent_arrow(
        psi_end_x,
        psi_end_y,
        -math.sin(math.radians(deg_psi)),
        -math.cos(math.radians(deg_psi)),
        marker="arr",
    )

    arc_pim = arc_path(ox, oy, 96.0, 0.0, deg_top, cls="c-main", ccw=True)
    pim_end_x = ox + 96.0 * math.cos(math.radians(deg_top))
    pim_end_y = oy - 96.0 * math.sin(math.radians(deg_top))
    arr_pim = tangent_arrow(
        pim_end_x,
        pim_end_y,
        -math.sin(math.radians(deg_top)),
        -math.cos(math.radians(deg_top)),
        marker="arr",
    )

    curves = "\n".join(
        [
            mid_arrow_path(
                f"M {ox:.1f} {oy:.1f} L {g1_end[0]:.1f} {g1_end[1]:.1f}",
                g1_arr[0],
                g1_arr[1],
                1.0,
                0.0,
                cls="c-blue",
                marker="arr-blue",
            ),
            mid_arrow_path(
                f"M {ox:.1f} {oy:.1f} L {g2_end[0]:.1f} {g2_end[1]:.1f}",
                g2_arr[0],
                g2_arr[1],
                g2_end[0] - ox,
                g2_end[1] - oy,
                cls="c-blue",
                marker="arr-blue",
            ),
            mid_arrow_path(
                f"M {ox:.1f} {oy:.1f} L {g_end[0]:.1f} {g_end[1]:.1f}",
                g_arr[0],
                g_arr[1],
                g_end[0] - ox,
                g_end[1] - oy,
                cls="c-main",
                marker="arr",
            ),
            arc_psi,
            arr_psi,
            arc_pim,
            arr_pim,
        ]
    )

    labels = "\n".join(
        [
            point_dot(e_psi[0], e_psi[1]),
            math_label(48.0, 239.0, "0", italic=False),
            math_label(264.0, 254.0, "Γ", sub="1"),
            math_label(134.0, 92.0, "Γ", sub="2"),
            math_label(254.0, 172.0, "Γ"),
            math_label(e_psi[0] - 4.0, e_psi[1] + 20.0, "e", sup="iψ"),
            math_label(202.0, 118.0, "f", tail="(D)"),
            math_label(122.0, 224.0, "ψ"),
            math_label(138.0, 172.0, "π/m"),
        ]
    )

    return svg_document(
        "0 0 430 278",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_13",
        title=CHAPTER_FIG_TITLES["3_13"],
    )


def fig_3_14() -> str:
    ox, oy = 210.0, 254.0
    r1, r2 = 100.0, 50.0
    c1y = oy - r1
    c2y = oy - r2

    crescent_d = (
        f"M {ox - r1:.1f} {c1y:.1f} "
        f"A {r1:.1f} {r1:.1f} 0 1 0 {ox + r1:.1f} {c1y:.1f} "
        f"A {r1:.1f} {r1:.1f} 0 1 0 {ox - r1:.1f} {c1y:.1f} Z "
        f"M {ox - r2:.1f} {c2y:.1f} "
        f"A {r2:.1f} {r2:.1f} 0 1 1 {ox + r2:.1f} {c2y:.1f} "
        f"A {r2:.1f} {r2:.1f} 0 1 1 {ox - r2:.1f} {c2y:.1f} Z"
    )

    axes = "\n".join(
        [
            f'    <line x1="55.0" y1="{oy:.1f}" x2="365.0" y2="{oy:.1f}" class="ax" />',
            f'    <line x1="{ox:.1f}" y1="296.0" x2="{ox:.1f}" y2="18.0" class="ax" />',
        ]
    )

    regions = "\n".join(
        [
            f'    <path d="{crescent_d}" fill-rule="evenodd" class="f-amber" />',
            f'    <path d="{crescent_d}" fill-rule="evenodd" class="f-stipple" />',
        ]
    )

    curves = "\n".join(
        [
            circle_contour(
                ox, c1y, r1, cls="c-blue", arrow_deg=42.0, ccw=True, marker="arr-blue"
            ),
            circle_contour(
                ox, c2y, r2, cls="c-blue", arrow_deg=34.0, ccw=True, marker="arr-blue"
            ),
        ]
    )

    labels = "\n".join(
        [
            point_dot(ox, oy),
            point_dot(ox, c2y),
            point_dot(ox, c1y),
            point_dot(ox, 118.0),
            point_dot(ox - r1, c1y),
            math_label(195.0, 272.0, "0", italic=False),
            math_label(178.0, 150.0, "i/2"),
            math_label(217.0, 122.0, "μ"),
            math_label(198.0, 48.0, "i"),
            math_label(88.0, 160.0, "z", sub="1"),
            math_label(155.0, 130.0, "D"),
            math_label(294.0, 86.0, "C", sub="1"),
            math_label(264.0, 178.0, "C", sub="2"),
        ]
    )

    return svg_document(
        "0 0 420 312",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_14",
        title=CHAPTER_FIG_TITLES["3_14"],
    )


def fig_3_15() -> str:
    vx = 230.0
    y1, y2 = 88.0, 192.0
    x0, x1 = 40.0, 420.0

    axes = f'    <line x1="{vx:.1f}" y1="20.0" x2="{vx:.1f}" y2="250.0" class="ax" />'

    regions = "\n".join(
        [
            f'    <rect x="{x0:.1f}" y="{y1:.1f}" width="{x1 - x0:.1f}" height="{y2 - y1:.1f}" class="f-amber" />',
            f'    <rect x="{x0:.1f}" y="{y1:.1f}" width="{x1 - x0:.1f}" height="{y2 - y1:.1f}" class="f-stipple" />',
        ]
    )

    curves = "\n".join(
        [
            mid_arrow_path(
                f"M {x1:.1f} {y1:.1f} L {x0:.1f} {y1:.1f}",
                174.0,
                y1,
                -1.0,
                0.0,
                cls="c-blue",
                marker="arr-blue",
            ),
            mid_arrow_path(
                f"M {x1:.1f} {y2:.1f} L {x0:.1f} {y2:.1f}",
                134.0,
                y2,
                -1.0,
                0.0,
                cls="c-blue",
                marker="arr-blue",
            ),
        ]
    )

    labels = "\n".join(
        [
            point_dot(vx, y1),
            point_dot(126.0, y1),
            point_dot(vx, y2),
            math_label(236.0, 80.0, "−i"),
            math_label(98.0, 78.0, "−i − 1"),
            math_label(236.0, 212.0, "−2i"),
            math_label(346.0, 78.0, "l", sub="1"),
            math_label(346.0, 212.0, "l", sub="2"),
            math_label(304.0, 146.0, "f", tail="(D)"),
        ]
    )

    return svg_document(
        "0 0 460 268",
        grid=axes,
        region=regions,
        curve=curves,
        label=labels,
        fig_id="3_15",
        title=CHAPTER_FIG_TITLES["3_15"],
    )


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "3_1": fig_3_1,
    "3_2": fig_3_2,
    "3_3": fig_3_3,
    "3_4": fig_3_4,
    "3_5": fig_3_5,
    "3_6": fig_3_6,
    "3_7": fig_3_7,
    "3_8": fig_3_8,
    "3_9": fig_3_9,
    "3_10": fig_3_10,
    "3_11": fig_3_11,
    "3_12": fig_3_12,
    "3_13": fig_3_13,
    "3_14": fig_3_14,
    "3_15": fig_3_15,
}
