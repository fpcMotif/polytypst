import math
from collections.abc import Callable, Sequence

from polytypst.vision.diagram_engine import smooth_curve, svg_document

from .figures_common import (
    AMBER,
    BLUE,
    GREEN,
    RED,
    Point,
    filled_pt,
    line_through,
    mvar,
    open_pt,
    panel_label,
    seg,
    txt,
)

CHAPTER_FIG_TITLES: dict[str, str] = {
    "16": "Curves on a quadric surface",
    "17": "Lines on the cubic surface",
    "18": "The standard quadratic transformation",
    "19": "Resolutions of some curve singularities",
    "20": "The Dynkin diagrams A_n, D_n, E_6, E_7 and E_8",
    "21": "The extended Dynkin diagrams A_n, D_n, E_6, E_7 and E_8",
}


def _hyperboloid_panel(
    cx: float,
    cy: float,
    curve_fn: Callable[[float], tuple[float, float]],
    t_range: tuple[float, float],
    closed: bool,
    curve_cls: str,
    curve_dash_cls: str,
    dot_color: str,
) -> tuple[str, str, str]:
    r_waist = 48.0
    a_slope = 1.42
    h_z = 104.0
    elev = math.radians(21.0)
    ca, sa = math.cos(elev), math.sin(elev)

    def _p3(x: float, y: float, z: float) -> Point:
        return (cx + x, cy - (h_z * z * ca - y * sa))

    def _surf(phi: float, z: float) -> tuple[float, float, float]:
        rad = r_waist * math.sqrt(1.0 + a_slope * a_slope * z * z)
        return (rad * math.cos(phi), rad * math.sin(phi), z)

    def _vis(x: float, y: float, z: float) -> float:
        return y * ca - (a_slope * a_slope * r_waist * r_waist / h_z) * z * sa

    sil_left: list[Point] = []
    sil_right: list[Point] = []
    for k in range(41):
        z = -1.0 + 2.0 * k / 40.0
        rad = r_waist * math.sqrt(1.0 + a_slope * a_slope * z * z)
        sil_left.append((cx - rad, cy - h_z * z * ca))
        sil_right.append((cx + rad, cy - h_z * z * ca))

    r_rim = r_waist * math.sqrt(1.0 + a_slope * a_slope)
    ry_rim = r_rim * sa
    top_cy = cy - h_z * ca
    bot_cy = cy + h_z * ca

    body_d = (
        f"M {sil_left[-1][0]:.2f} {sil_left[-1][1]:.2f} "
        f"A {r_rim:.2f} {ry_rim:.2f} 0 1 1 {sil_right[-1][0]:.2f} {sil_right[-1][1]:.2f} "
        + " ".join(f"L {p[0]:.2f} {p[1]:.2f}" for p in reversed(sil_right))
        + f" A {r_rim:.2f} {ry_rim:.2f} 0 0 1 {sil_left[0][0]:.2f} {sil_left[0][1]:.2f} "
        + " ".join(f"L {p[0]:.2f} {p[1]:.2f}" for p in sil_left)
        + " Z"
    )

    rulings: list[str] = []
    n_rul = 18
    for i in range(n_rul):
        th = 2.0 * math.pi * i / n_rul
        for sgn in (1.0, -1.0):
            vis_pts: list[Point] = []
            for k in range(33):
                z = -1.0 + 2.0 * k / 32.0
                x = r_waist * (math.cos(th) - sgn * a_slope * z * math.sin(th))
                y = r_waist * (math.sin(th) + sgn * a_slope * z * math.cos(th))
                if _vis(x, y, z) >= -1.5:
                    vis_pts.append(_p3(x, y, z))
                elif len(vis_pts) >= 2:
                    rulings.append(
                        f'    <polyline points="{" ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in vis_pts)}" class="c-sub" stroke-opacity="0.72" />'
                    )
                    vis_pts = []
            if len(vis_pts) >= 2:
                rulings.append(
                    f'    <polyline points="{" ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in vis_pts)}" class="c-sub" stroke-opacity="0.72" />'
                )

    n_samp = 220
    t0, t1 = t_range
    front_runs: list[list[Point]] = []
    back_runs: list[list[Point]] = []
    horizon_dots: list[Point] = []
    prev_vis: bool | None = None

    for k in range(n_samp + (1 if closed else 0)):
        t = t0 + (t1 - t0) * (k % n_samp if closed else k) / n_samp
        phi, z = curve_fn(t)
        x, y, zv = _surf(phi, z)
        pt2 = _p3(x, y, zv)
        is_front = _vis(x, y, zv) >= 0.0
        if prev_vis is not None and is_front != prev_vis:
            horizon_dots.append(pt2)
            if is_front:
                if back_runs:
                    back_runs[-1].append(pt2)
                front_runs.append([pt2])
            else:
                if front_runs:
                    front_runs[-1].append(pt2)
                back_runs.append([pt2])
        else:
            target = front_runs if is_front else back_runs
            if not target or prev_vis is None:
                target.append([pt2])
            else:
                target[-1].append(pt2)
        prev_vis = is_front

    if not closed:
        for t_end in (t0, t1):
            phi_e, z_e = curve_fn(t_end)
            horizon_dots.append(_p3(*_surf(phi_e, z_e)))

    bot_front = (
        f"M {cx - r_rim:.2f} {bot_cy:.2f} "
        f"A {r_rim:.2f} {ry_rim:.2f} 0 0 0 {cx + r_rim:.2f} {bot_cy:.2f}"
    )
    bot_back = (
        f"M {cx - r_rim:.2f} {bot_cy:.2f} "
        f"A {r_rim:.2f} {ry_rim:.2f} 0 0 1 {cx + r_rim:.2f} {bot_cy:.2f}"
    )

    crv_els = [
        f'    <path d="{bot_back}" class="c-dash" />',
        f'    <ellipse cx="{cx:.2f}" cy="{top_cy:.2f}" rx="{r_rim:.2f}" ry="{ry_rim:.2f}" class="c-main" />',
        f'    <path d="{bot_front}" class="c-main" />',
        smooth_curve(sil_left, cls="c-main"),
        smooth_curve(sil_right, cls="c-main"),
    ]
    for run in back_runs:
        if len(run) >= 2:
            crv_els.append(
                f'    <polyline points="{" ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in run)}" class="{curve_dash_cls}" stroke-width="1.8" />'
            )
    for run in front_runs:
        if len(run) >= 2:
            crv_els.append(
                f'    <polyline points="{" ".join(f"{p[0]:.2f},{p[1]:.2f}" for p in run)}" class="{curve_cls}" stroke-width="2.35" />'
            )

    reg_str = f'    <path d="{body_d}" class="f-blue" opacity="0.36" />\n' + "\n".join(
        rulings
    )
    lbl_str = "\n".join(
        open_pt(p[0], p[1], color=dot_color, r=3.5) for p in horizon_dots
    )
    return reg_str, "\n".join(crv_els), lbl_str


def _catmull_closed_1d(vals: Sequence[float], u: float) -> float:
    n = len(vals)
    pos = (u % 1.0) * n
    idx = math.floor(pos) % n
    f = pos - math.floor(pos)
    p0 = vals[(idx - 1) % n]
    p1 = vals[idx]
    p2 = vals[(idx + 1) % n]
    p3 = vals[(idx + 2) % n]
    return 0.5 * (
        (2.0 * p1)
        + (-p0 + p2) * f
        + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * f * f
        + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * f * f * f
    )


def fig_16() -> str:
    def _curve_a(t: float) -> tuple[float, float]:
        phi = 0.52 * math.pi + 1.24 * math.cos(t) + 0.16 * math.sin(2.0 * t)
        z = -0.18 + 0.64 * math.sin(t) - 0.14 * math.cos(2.0 * t)
        return (phi, max(-0.96, min(0.96, z)))

    b_base_phis = (
        0.06,
        -0.48 * math.pi,
        -0.96 * math.pi,
        -1.34 * math.pi,
        -1.70 * math.pi,
        -1.56 * math.pi,
        -1.84 * math.pi,
    )
    n_b = len(b_base_phis)
    b_phi_offsets = tuple(
        b_base_phis[k] + 2.0 * math.pi * (k / n_b) for k in range(n_b)
    )
    b_zs = (0.98, 0.24, -0.56, -0.84, -0.16, 0.10, 0.38)

    def _curve_b(u: float) -> tuple[float, float]:
        phi = -2.0 * math.pi * u + _catmull_closed_1d(b_phi_offsets, u)
        zv = _catmull_closed_1d(b_zs, u)
        return (phi, max(-0.99, min(0.99, zv)))

    reg_a, crv_a, dots_a = _hyperboloid_panel(
        138.0,
        148.0,
        _curve_a,
        (0.0, 2.0 * math.pi),
        True,
        "c-blue",
        "c-blue-dash",
        BLUE,
    )
    reg_b, crv_b, dots_b = _hyperboloid_panel(
        426.0,
        148.0,
        _curve_b,
        (0.0, 1.0),
        True,
        "c-red",
        "c-red-dash",
        RED,
    )
    labels = "\n".join(
        [
            dots_a,
            dots_b,
            panel_label(138.0, 308.0, "a"),
            panel_label(426.0, 308.0, "b"),
        ]
    )
    return svg_document(
        "0 0 564 322",
        region=f"{reg_a}\n{reg_b}",
        curve=f"{crv_a}\n{crv_b}",
        label=labels,
        fig_id="16",
        title=CHAPTER_FIG_TITLES["16"],
        show_grid=False,
    )


def fig_17() -> str:
    y_top, y_bot = 52.0, 244.0
    xs = (62.0, 156.0, 250.0, 344.0, 438.0)

    vert_lines: list[str] = []
    diag_lines: list[str] = []
    lbls: list[str] = [
        mvar(514.0, y_top - 8.0, "L", color=BLUE),
        mvar(512.0, y_bot - 8.0, "M", color=BLUE),
    ]

    for idx, xv in enumerate(xs, start=1):
        s_idx = str(idx)
        vert_lines.append(seg((xv, 18.0), (xv, 278.0), cls="c-main", stroke_width=2.0))
        diag_lines.append(
            seg((xv - 14.0, 108.0), (xv + 48.0, 30.0), cls="c-red", stroke_width=2.0)
        )
        diag_lines.append(
            seg((xv - 14.0, 192.0), (xv + 48.0, 272.0), cls="c-green", stroke_width=2.0)
        )
        lbls.append(mvar(xv + 20.0, 28.0, "L", sub=s_idx, color=RED))
        lbls.append(mvar(xv + 7.0, 154.0, "L", sub=s_idx, prime="\u2032"))
        lbls.append(mvar(xv + 26.0, 284.0, "L", sub=s_idx, prime="\u2033", color=GREEN))

    curves = "\n".join(
        [
            seg((20.0, y_top), (522.0, y_top), cls="c-blue", stroke_width=2.2),
            seg((20.0, y_bot), (522.0, y_bot), cls="c-blue", stroke_width=2.2),
            *vert_lines,
            *diag_lines,
        ]
    )
    return svg_document(
        "0 0 548 298",
        curve=curves,
        label="\n".join(lbls),
        fig_id="17",
        title=CHAPTER_FIG_TITLES["17"],
        show_grid=False,
    )


def _curved_arrow(
    p0: Point, c1: Point, c2: Point, p3: Point, cls: str, marker: str
) -> str:
    d = (
        f"M {p0[0]:.1f} {p0[1]:.1f} "
        f"C {c1[0]:.1f} {c1[1]:.1f}, {c2[0]:.1f} {c2[1]:.1f}, {p3[0]:.1f} {p3[1]:.1f}"
    )
    return f'    <path d="{d}" class="{cls}" marker-end="url(#{marker})" />'


def fig_18() -> str:
    left_patch = [
        (16.0, 138.0),
        (24.0, 62.0),
        (78.0, 42.0),
        (134.0, 88.0),
        (146.0, 168.0),
        (114.0, 246.0),
        (48.0, 262.0),
        (18.0, 212.0),
    ]
    mid_patch = [
        (206.0, 138.0),
        (224.0, 46.0),
        (294.0, 16.0),
        (362.0, 48.0),
        (376.0, 142.0),
        (356.0, 238.0),
        (286.0, 266.0),
        (218.0, 232.0),
    ]
    right_patch = [
        (434.0, 146.0),
        (456.0, 64.0),
        (524.0, 32.0),
        (566.0, 72.0),
        (568.0, 178.0),
        (536.0, 246.0),
        (466.0, 250.0),
        (436.0, 202.0),
    ]

    xi1, xi2, xi0 = (58.0, 108.0), (62.0, 208.0), (108.0, 162.0)
    eta0, eta2, eta1 = (468.0, 136.0), (520.0, 92.0), (524.0, 184.0)

    hv = [
        (244.0, 98.0),
        (291.0, 64.0),
        (338.0, 96.0),
        (340.0, 164.0),
        (292.0, 196.0),
        (244.0, 166.0),
    ]
    hex_edges = [
        line_through(hv[5], hv[0], -0.30, 1.30, cls="c-blue", stroke_width=2.0),
        line_through(hv[0], hv[1], -0.30, 1.30, cls="c-red", stroke_width=2.0),
        line_through(hv[1], hv[2], -0.30, 1.30, cls="c-blue", stroke_width=2.0),
        line_through(hv[2], hv[3], -0.30, 1.30, cls="c-red", stroke_width=2.0),
        line_through(hv[3], hv[4], -0.30, 1.30, cls="c-blue", stroke_width=2.0),
        line_through(hv[4], hv[5], -0.30, 1.30, cls="c-red", stroke_width=2.0),
    ]

    regions = "\n".join(
        [
            smooth_curve(left_patch, cls="c-sub", closed=True, fill_cls="f-blue"),
            smooth_curve(mid_patch, cls="c-sub", closed=True, fill_cls="f-amber"),
            smooth_curve(right_patch, cls="c-sub", closed=True, fill_cls="f-green"),
        ]
    )
    curves = "\n".join(
        [
            smooth_curve(left_patch, cls="c-main", closed=True),
            smooth_curve(mid_patch, cls="c-main", closed=True),
            smooth_curve(right_patch, cls="c-main", closed=True),
            line_through(xi1, xi2, -0.26, 1.26, cls="c-main", stroke_width=2.0),
            line_through(xi2, xi0, -0.28, 1.28, cls="c-main", stroke_width=2.0),
            line_through(xi1, xi0, -0.28, 1.28, cls="c-main", stroke_width=2.0),
            *hex_edges,
            line_through(eta2, eta1, -0.28, 1.28, cls="c-main", stroke_width=2.0),
            line_through(eta0, eta2, -0.28, 1.28, cls="c-main", stroke_width=2.0),
            line_through(eta0, eta1, -0.28, 1.28, cls="c-main", stroke_width=2.0),
            _curved_arrow(
                (314.0, 80.0),
                (302.0, 22.0),
                (156.0, 36.0),
                (68.0, 98.0),
                "c-blue",
                "arr-blue",
            ),
            _curved_arrow(
                (242.0, 132.0),
                (196.0, 138.0),
                (154.0, 148.0),
                (118.0, 158.0),
                "c-blue",
                "arr-blue",
            ),
            _curved_arrow(
                (316.0, 180.0),
                (318.0, 260.0),
                (164.0, 260.0),
                (72.0, 214.0),
                "c-blue",
                "arr-blue",
            ),
            _curved_arrow(
                (268.0, 80.0),
                (264.0, 20.0),
                (412.0, 34.0),
                (508.0, 84.0),
                "c-red",
                "arr-red",
            ),
            _curved_arrow(
                (341.0, 130.0),
                (378.0, 128.0),
                (416.0, 130.0),
                (454.0, 134.0),
                "c-red",
                "arr-red",
            ),
            _curved_arrow(
                (268.0, 180.0),
                (264.0, 258.0),
                (426.0, 252.0),
                (512.0, 192.0),
                "c-red",
                "arr-red",
            ),
        ]
    )
    labels = "\n".join(
        [
            mvar(64.0, 74.0, "P", sup="2", bold_base=True, color=BLUE),
            mvar(314.0, 38.0, "X"),
            mvar(532.0, 66.0, "P", sup="2", bold_base=True, overbar=True, color=GREEN),
            mvar(64.0, 140.0, "\u03be", sub="1", size=14.0),
            mvar(84.0, 165.0, "\u03be", sub="0", size=14.0),
            mvar(65.0, 190.0, "\u03be", sub="2", size=14.0),
            mvar(56.0, 252.0, "L", sub="0", size=14.5),
            mvar(118.0, 142.0, "L", sub="1", size=14.5),
            mvar(114.0, 198.0, "L", sub="2", size=14.5),
            mvar(252.0, 138.0, "M", sub="0", prime="\u2032", color=BLUE, size=13.0),
            mvar(266.0, 104.0, "L", sub="2", prime="\u2032", color=RED, size=13.0),
            mvar(298.0, 104.0, "M", sub="1", prime="\u2032", color=BLUE, size=13.0),
            mvar(314.0, 138.0, "L", sub="0", prime="\u2032", color=RED, size=13.0),
            mvar(298.0, 172.0, "M", sub="2", prime="\u2032", color=BLUE, size=13.0),
            mvar(266.0, 172.0, "L", sub="1", prime="\u2032", color=RED, size=13.0),
            mvar(482.0, 141.0, "\u03b7", sub="0", size=14.0),
            mvar(499.0, 120.0, "\u03b7", sub="2", size=14.0),
            mvar(500.0, 162.0, "\u03b7", sub="1", size=14.0),
            mvar(540.0, 88.0, "M", sub="1", size=14.5),
            mvar(542.0, 198.0, "M", sub="2", size=14.5),
            mvar(514.0, 232.0, "M", sub="0", size=14.5),
            mvar(148.0, 48.0, "\u03c6", color=BLUE),
            mvar(166.0, 134.0, "\u03c6", color=BLUE),
            mvar(174.0, 248.0, "\u03c6", color=BLUE),
            mvar(416.0, 46.0, "\u03c8", color=RED),
            mvar(394.0, 120.0, "\u03c8", color=RED),
            mvar(386.0, 232.0, "\u03c8", color=RED),
        ]
    )
    return svg_document(
        "0 0 584 282",
        region=regions,
        curve=curves,
        label=labels,
        fig_id="18",
        title=CHAPTER_FIG_TITLES["18"],
        show_grid=False,
    )


def fig_19() -> str:
    t1_bot, t1_l, t1_r = (86.0, 98.0), (40.0, 32.0), (132.0, 32.0)
    t2_b, t2_m, t2_t = (248.0, 146.0), (248.0, 90.0), (248.0, 32.0)
    t3_b, t3_m, t3_l, t3_r = (426.0, 146.0), (426.0, 92.0), (380.0, 32.0), (472.0, 32.0)

    curves = "\n".join(
        [
            seg(t1_bot, t1_l, cls="c-blue", stroke_width=2.3),
            seg(t1_bot, t1_r, cls="c-blue", stroke_width=2.3),
            seg(t2_b, t2_m, cls="c-green", stroke_width=2.3),
            seg(t2_m, t2_t, cls="c-green", stroke_width=2.3),
            seg(t3_b, t3_m, cls="c-red", stroke_width=2.3),
            seg(t3_m, t3_l, cls="c-red", stroke_width=2.3),
            seg(t3_m, t3_r, cls="c-red", stroke_width=2.3),
        ]
    )
    eq1 = (
        '    <text x="88.0" y="146.0" class="lbl" text-anchor="middle">'
        '<tspan class="it">y</tspan><tspan font-size="10.5px" dy="-5.5">2</tspan>'
        '<tspan dy="5.5"> = </tspan>'
        '<tspan class="it">x</tspan><tspan font-size="10.5px" dy="-5.5">2</tspan>'
        '<tspan dy="5.5"> + </tspan>'
        '<tspan class="it">x</tspan><tspan font-size="10.5px" dy="-5.5">3</tspan></text>'
    )
    eq2 = (
        '    <text x="316.0" y="132.0" class="lbl" text-anchor="middle">'
        '<tspan class="it">y</tspan><tspan font-size="10.5px" dy="-5.5">2</tspan>'
        '<tspan dy="5.5"> = </tspan>'
        '<tspan class="it">x</tspan><tspan font-size="10.5px" dy="-5.5">5</tspan></text>'
    )
    eq3 = (
        '    <text x="506.0" y="138.0" class="lbl" text-anchor="middle">'
        '<tspan class="it">y</tspan><tspan font-size="10.5px" dy="-5.5">2</tspan>'
        '<tspan dy="5.5"> = </tspan>'
        '<tspan class="it">x</tspan><tspan font-size="10.5px" dy="-5.5">2</tspan>'
        '<tspan dy="5.5" class="it">y</tspan><tspan font-size="10.5px" dy="-5.5">4</tspan>'
        '<tspan dy="5.5"> + </tspan>'
        '<tspan class="it">x</tspan><tspan font-size="10.5px" dy="-5.5">4</tspan></text>'
    )
    labels = "\n".join(
        [
            filled_pt(*t1_bot, color=BLUE, r=4.6),
            filled_pt(*t1_l, color=AMBER, r=4.6),
            filled_pt(*t1_r, color=AMBER, r=4.6),
            txt(t1_bot[0] + 13.0, t1_bot[1] + 5.0, "2"),
            txt(t1_l[0] + 12.0, t1_l[1] + 6.0, "1"),
            txt(t1_r[0] + 12.0, t1_r[1] + 6.0, "1"),
            filled_pt(*t2_b, color=GREEN, r=4.6),
            filled_pt(*t2_m, color=GREEN, r=4.6),
            filled_pt(*t2_t, color=AMBER, r=4.6),
            txt(t2_b[0] + 12.0, t2_b[1] + 5.0, "2"),
            txt(t2_m[0] + 12.0, t2_m[1] + 5.0, "2"),
            txt(t2_t[0] + 12.0, t2_t[1] + 5.0, "1"),
            filled_pt(*t3_b, color=RED, r=4.6),
            filled_pt(*t3_m, color=RED, r=4.6),
            filled_pt(*t3_l, color=AMBER, r=4.6),
            filled_pt(*t3_r, color=AMBER, r=4.6),
            txt(t3_b[0] + 12.0, t3_b[1] + 5.0, "2"),
            txt(t3_m[0] + 13.0, t3_m[1] + 5.0, "2"),
            txt(t3_l[0] + 12.0, t3_l[1] + 6.0, "1"),
            txt(t3_r[0] + 12.0, t3_r[1] + 6.0, "1"),
            eq1,
            eq2,
            eq3,
        ]
    )
    return svg_document(
        "0 0 572 174",
        curve=curves,
        label=labels,
        fig_id="19",
        title=CHAPTER_FIG_TITLES["19"],
        show_grid=False,
    )


def _dynkin_graph(
    nodes: Sequence[Point],
    edges: Sequence[tuple[int, int]],
    edge_cls: str,
    node_color: str,
) -> tuple[str, str]:
    e_els = [seg(nodes[i], nodes[j], cls=edge_cls, stroke_width=2.2) for i, j in edges]
    n_els = [open_pt(p[0], p[1], color=node_color, r=5.0) for p in nodes]
    return "\n".join(e_els), "\n".join(n_els)


def fig_20() -> str:
    step = 32.0
    an_nodes = [(38.0 + k * step, 56.0) for k in range(3)] + [
        (166.0, 56.0),
        (198.0, 56.0),
    ]
    an_edges = [(0, 1), (1, 2), (3, 4)]

    dn_nodes = (
        [(312.0 + k * step, 56.0) for k in range(3)]
        + [(440.0, 56.0), (472.0, 56.0)]
        + [(498.0, 30.0), (498.0, 82.0)]
    )
    dn_edges = [(0, 1), (1, 2), (3, 4), (4, 5), (4, 6)]

    e_step = 26.0
    e6_nodes = [(24.0 + k * e_step, 148.0) for k in range(5)] + [
        (24.0 + 2 * e_step, 182.0)
    ]
    e6_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5)]

    e7_nodes = [(174.0 + k * e_step, 148.0) for k in range(6)] + [
        (174.0 + 2 * e_step, 182.0)
    ]
    e7_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (2, 6)]

    e8_nodes = [(350.0 + k * e_step, 148.0) for k in range(7)] + [
        (350.0 + 2 * e_step, 182.0)
    ]
    e8_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (2, 7)]

    ea, na = _dynkin_graph(an_nodes, an_edges, "c-blue", BLUE)
    ed, nd = _dynkin_graph(dn_nodes, dn_edges, "c-green", GREEN)
    ee6, ne6 = _dynkin_graph(e6_nodes, e6_edges, "c-red", RED)
    ee7, ne7 = _dynkin_graph(e7_nodes, e7_edges, "c-amber", AMBER)
    ee8, ne8 = _dynkin_graph(e8_nodes, e8_edges, "c-red", RED)

    curves = f"{ea}\n{ed}\n{ee6}\n{ee7}\n{ee8}"
    labels = "\n".join(
        [
            na,
            nd,
            ne6,
            ne7,
            ne8,
            txt(134.0, 60.0, "\u22ef", anchor="middle", size=17.0),
            txt(408.0, 60.0, "\u22ef", anchor="middle", size=17.0),
            mvar(114.0, 98.0, "A", sub="n", color=BLUE, bold_base=True),
            txt(
                258.0,
                98.0,
                '(<tspan class="it">n</tspan> is the number of vertexes)',
                anchor="middle",
                size=13.5,
            ),
            mvar(412.0, 98.0, "D", sub="n", color=GREEN, bold_base=True),
            mvar(96.0, 184.0, "E", sub="6", color=RED, bold_base=True),
            mvar(256.0, 184.0, "E", sub="7", color=AMBER, bold_base=True),
            mvar(442.0, 184.0, "E", sub="8", color=RED, bold_base=True),
        ]
    )
    return svg_document(
        "0 0 540 206",
        curve=curves,
        label=labels,
        fig_id="20",
        title=CHAPTER_FIG_TITLES["20"],
        show_grid=False,
    )


def fig_21() -> str:
    an_pts = [
        (24.0, 52.0),
        (46.0, 24.0),
        (80.0, 24.0),
        (102.0, 52.0),
        (102.0, 86.0),
        (76.0, 114.0),
    ]
    an_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]

    dn_pts = [
        (166.0, 34.0),
        (166.0, 92.0),
        (192.0, 63.0),
        (224.0, 63.0),
        (292.0, 63.0),
        (324.0, 63.0),
        (350.0, 34.0),
        (350.0, 92.0),
    ]
    dn_edges = [(0, 2), (1, 2), (2, 3), (4, 5), (5, 6), (5, 7)]

    e6_step = 28.0
    e6_pts = [(404.0 + k * e6_step, 34.0) for k in range(5)] + [
        (404.0 + 2 * e6_step, 66.0),
        (404.0 + 2 * e6_step, 98.0),
    ]
    e6_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5), (5, 6)]

    e7_step = 28.0
    e7_pts = [(34.0 + k * e7_step, 184.0) for k in range(7)] + [
        (34.0 + 3 * e7_step, 220.0)
    ]
    e7_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (3, 7)]

    e8_step = 28.0
    e8_pts = [(296.0 + k * e8_step, 184.0) for k in range(8)] + [
        (296.0 + 2 * e8_step, 220.0)
    ]
    e8_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (2, 8)]

    ea, na = _dynkin_graph(an_pts, an_edges, "c-blue", BLUE)
    ed, nd = _dynkin_graph(dn_pts, dn_edges, "c-green", GREEN)
    ee6, ne6 = _dynkin_graph(e6_pts, e6_edges, "c-red", RED)
    ee7, ne7 = _dynkin_graph(e7_pts, e7_edges, "c-amber", AMBER)
    ee8, ne8 = _dynkin_graph(e8_pts, e8_edges, "c-red", RED)

    curves = f"{ea}\n{ed}\n{ee6}\n{ee7}\n{ee8}"
    labels = "\n".join(
        [
            na,
            nd,
            ne6,
            ne7,
            ne8,
            txt(24.0, 82.0, "\u22ee", anchor="middle", size=16.0),
            txt(48.0, 118.0, "\u22ef", anchor="middle", size=16.0),
            txt(258.0, 67.0, "\u22ef", anchor="middle", size=17.0),
            mvar(
                62.0,
                74.0,
                "A",
                sub="n",
                color=BLUE,
                bold_base=True,
                tilde=True,
                anchor="middle",
            ),
            mvar(
                258.0,
                98.0,
                "D",
                sub="n",
                color=GREEN,
                bold_base=True,
                tilde=True,
                anchor="middle",
            ),
            txt(
                204.0,
                142.0,
                '(the number of vertexes is <tspan class="it">n</tspan> + 1)',
                anchor="middle",
                size=13.5,
            ),
            mvar(492.0, 76.0, "E", sub="6", color=RED, bold_base=True, tilde=True),
            mvar(144.0, 222.0, "E", sub="7", color=AMBER, bold_base=True, tilde=True),
            mvar(384.0, 222.0, "E", sub="8", color=RED, bold_base=True, tilde=True),
        ]
    )
    return svg_document(
        "0 0 544 242",
        curve=curves,
        label=labels,
        fig_id="21",
        title=CHAPTER_FIG_TITLES["21"],
        show_grid=False,
    )


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "16": fig_16,
    "17": fig_17,
    "18": fig_18,
    "19": fig_19,
    "20": fig_20,
    "21": fig_21,
}
