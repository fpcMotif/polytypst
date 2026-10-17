import math
from collections.abc import Callable

from ..vision.diagram_engine import (
    arrow_line,
    circle_contour,
    math_label,
    point_dot,
    smooth_curve,
    svg_document,
    tangent_arrow,
)

CHAPTER_FIG_TITLES: dict[str, str] = {
    "4_1": "Chain of overlapping domains D_0, D_1, ..., D_n for analytic continuation",
    "4_2": "Branches of log z: overlapping sectors D_0, D_1, D_2 and strips W_k",
    "4_3": "Direct analytic continuation by power series from c_0 to c_1",
    "4_4": "Concatenation of two curves gamma = gamma_1 . gamma_2",
    "4_5": "Piecewise concatenation of curves gamma = gamma_1 . gamma_2 ... gamma_n",
    "4_6": "Convergence disks U_s and U_t of radii r(s) and r(t) along a curve gamma",
    "4_7": "Subdivision of a curve gamma into subarcs gamma_k inside overlapping domains U_k",
    "4_8": "Continuous homotopy family of curves gamma_s between c_0 and c_1 in Omega",
    "4_9": "Homotopy contraction of a closed loop gamma with base point c_0 in Omega",
    "4_10": "Closed curve gamma contractible to a point c inside a region Omega",
    "4_11": "Simply connected comb domain Omega in the unit square with vertical slits",
    "4_12": "Polygonal line L(sigma) connecting rational grid vertices from c_0 to c",
    "4_13": "Linear homotopy Gamma(t, s) between a curve gamma and polygonal line gamma_n",
    "4_14": "Piecewise smooth integration path gamma from c_0 to z in region Omega",
    "4_15": "Overlapping disks U(gamma(s)) and U(gamma(t)) containing z along gamma",
    "4_16": "Decomposition of path gamma = alpha . beta with terminal arc beta in U(gamma(b))",
    "4_17": "Polygonal approximation gamma_s and segment mu inside disk U(lambda(s))",
    "4_18": "Slit annular domain D bounded by C_R, C_epsilon, and cut [epsilon, R]",
    "4_19": "Paths gamma_1 and gamma_2 meeting at common initial point c_0",
    "4_20": "Closed loops alpha around 2 and beta around 0 with branch cut along R^-",
    "4_21": "Homotopy deformation of loop beta into keyhole contour lambda^-1 . C_epsilon . lambda",
}


def _blob_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    rot_deg: float = 0.0,
    wobble: float = 0.06,
    n: int = 12,
) -> list[tuple[float, float]]:
    rot = math.radians(rot_deg)
    cr, sr = math.cos(rot), math.sin(rot)
    pts: list[tuple[float, float]] = []
    for k in range(n):
        ang = 2.0 * math.pi * k / n
        scale = 1.0 + wobble * math.cos(3.0 * ang + 0.4) - 0.04 * math.sin(2.0 * ang)
        lx = rx * scale * math.cos(ang)
        ly = ry * scale * math.sin(ang)
        px = cx + lx * cr - ly * sr
        py = cy + lx * sr + ly * cr
        pts.append((px, py))
    return pts


def _smooth_closed_d(points: list[tuple[float, float]]) -> str:
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


def _directed_segment(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    cls: str = "c-blue",
    marker: str = "arr-blue",
    frac: float = 0.54,
) -> str:
    mx = x1 + (x2 - x1) * frac
    my = y1 + (y2 - y1) * frac
    line_el = f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" />'
    arr_el = tangent_arrow(mx, my, x2 - x1, y2 - y1, marker=marker)
    return f"{line_el}\n{arr_el}"


def fig_4_1() -> str:
    cx0, cy0 = 230.0, 145.0
    ring_r = 76.0
    centers_cfg = [
        (0.0, 48.0, 40.0, 12.0, "f-blue"),
        (45.0, 46.0, 38.0, -25.0, "f-amber"),
        (90.0, 50.0, 40.0, 8.0, "f-blue"),
        (135.0, 46.0, 38.0, 35.0, "f-amber"),
        (180.0, 44.0, 42.0, -10.0, "f-blue"),
        (225.0, 46.0, 38.0, 28.0, "f-amber"),
        (270.0, 52.0, 40.0, -6.0, "f-blue"),
        (315.0, 46.0, 39.0, 22.0, "f-amber"),
    ]
    reg_parts: list[str] = []
    cur_parts: list[str] = []
    for deg, rx, ry, rot, fcls in centers_cfg:
        rad = math.radians(deg)
        bx = cx0 + ring_r * math.cos(rad)
        by = cy0 - ring_r * math.sin(rad)
        pts = _blob_points(bx, by, rx, ry, rot_deg=rot, wobble=0.07)
        d = _smooth_closed_d(pts)
        reg_parts.append(f'    <path d="{d}" class="{fcls}" />')
        reg_parts.append(f'    <path d="{d}" class="f-stipple" />')
        cur_parts.append(f'    <path d="{d}" class="c-blue-dash" />')

    axes_el = f'    <circle cx="{cx0:.1f}" cy="{cy0:.1f}" r="{ring_r:.1f}" class="c-sub" stroke-dasharray="3,4" />'
    lbl_parts = [
        math_label(306.0, 148.0, "D", sub="0", anchor="middle"),
        math_label(284.0, 88.0, "D", sub="1", anchor="middle"),
        math_label(224.0, 68.0, "D", sub="2", anchor="middle"),
        math_label(222.0, 226.0, "D", sub="n−1", anchor="middle"),
        math_label(286.0, 206.0, "D", sub="n", anchor="middle"),
    ]
    return svg_document(
        "0 0 460 290",
        grid=axes_el,
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_1",
        title=CHAPTER_FIG_TITLES["4_1"],
    )


def fig_4_2() -> str:
    zx, zy, zr = 132.0, 138.0, 88.0
    wx, wy0 = 392.0, 156.0
    w_left, w_right = 298.0, 486.0

    def _sector_d(deg1: float, deg2: float, r: float) -> str:
        r1, r2 = math.radians(deg1), math.radians(deg2)
        x1, y1 = zx + r * math.cos(r1), zy - r * math.sin(r1)
        x2, y2 = zx + r * math.cos(r2), zy - r * math.sin(r2)
        return f"M {zx:.1f} {zy:.1f} L {x1:.2f} {y1:.2f} A {r:.1f} {r:.1f} 0 0 0 {x2:.2f} {y2:.2f} Z"

    d0_path = _sector_d(-90.0, 90.0, zr)
    d1_path = _sector_d(30.0, 210.0, zr)
    d2_path = _sector_d(150.0, 330.0, zr)

    strips = [
        ("W", "3", 36.0, 74.0, "f-blue"),
        ("W", "2", 56.0, 110.0, "f-amber"),
        ("W", "1", 92.0, 146.0, "f-green"),
        ("W", "0", 128.0, 182.0, "f-blue"),
        ("W", "−1", 164.0, 218.0, "f-amber"),
    ]
    reg_parts = [
        f'    <path d="{d0_path}" class="f-blue" />',
        f'    <path d="{d1_path}" class="f-green" />',
        f'    <path d="{d2_path}" class="f-amber" />',
        f'    <circle cx="{zx:.1f}" cy="{zy:.1f}" r="{zr:.1f}" class="f-hatch" />',
    ]
    for _, _, y_top, y_bot, fcls in strips:
        h = y_bot - y_top
        reg_parts.append(
            f'    <rect x="{w_left:.1f}" y="{y_top:.1f}" width="{w_right - w_left:.1f}" height="{h:.1f}" class="{fcls}" />'
        )
    reg_parts.append(
        f'    <rect x="{w_left:.1f}" y="36.0" width="{w_right - w_left:.1f}" height="182.0" class="f-hatch" />'
    )

    ax_parts = [
        f'    <line x1="{zx - zr - 10:.1f}" y1="{zy:.1f}" x2="{zx + zr + 10:.1f}" y2="{zy:.1f}" class="ax" />',
        f'    <line x1="{zx:.1f}" y1="{zy + zr + 10:.1f}" x2="{zx:.1f}" y2="{zy - zr - 10:.1f}" class="ax" />',
        arrow_line(wx, 232.0, wx, 24.0, cls="ax", marker="arr-axis"),
        f'    <line x1="{w_left - 8:.1f}" y1="{wy0:.1f}" x2="{w_right + 8:.1f}" y2="{wy0:.1f}" class="ax" />',
    ]

    dx30 = zr * math.cos(math.radians(30.0))
    dy30 = zr * math.sin(math.radians(30.0))
    cur_parts = [
        f'    <circle cx="{zx:.1f}" cy="{zy:.1f}" r="{zr:.1f}" class="c-blue-dash" />',
        f'    <line x1="{zx:.1f}" y1="{zy - zr:.1f}" x2="{zx:.1f}" y2="{zy + zr:.1f}" class="c-main" />',
        f'    <line x1="{zx - dx30:.1f}" y1="{zy + dy30:.1f}" x2="{zx + dx30:.1f}" y2="{zy - dy30:.1f}" class="c-blue" />',
        f'    <line x1="{zx - dx30:.1f}" y1="{zy - dy30:.1f}" x2="{zx + dx30:.1f}" y2="{zy + dy30:.1f}" class="c-green" />',
    ]
    for y_line in [
        38.0,
        56.0,
        74.0,
        92.0,
        110.0,
        128.0,
        146.0,
        164.0,
        182.0,
        200.0,
        218.0,
    ]:
        cur_parts.append(
            f'    <line x1="{w_left:.1f}" y1="{y_line:.1f}" x2="{w_right:.1f}" y2="{y_line:.1f}" class="c-sub" />'
        )
    for y_tick in [48.0, 84.0, 120.0, 156.0, 192.0]:
        cur_parts.append(
            f'    <line x1="{wx - 4:.1f}" y1="{y_tick:.1f}" x2="{wx + 4:.1f}" y2="{y_tick:.1f}" class="c-main" />'
        )

    lbl_parts = [
        point_dot(zx, zy, open_dot=True),
        math_label(zx - 11.0, zy + 15.0, "0", italic=False),
        math_label(zx + 52.0, zy + 6.0, "D", sub="0", anchor="middle"),
        math_label(zx - 26.0, zy - 42.0, "D", sub="1", anchor="middle"),
        math_label(zx - 26.0, zy + 54.0, "D", sub="2", anchor="middle"),
        math_label(zx, 262.0, "z", tail="-plane", anchor="middle"),
        math_label(wx - 8.0, 51.0, "2πi", italic=False, anchor="end", size=13.0),
        math_label(wx - 8.0, 88.0, "4πi/3", italic=False, anchor="end", size=13.0),
        math_label(wx - 8.0, 124.0, "2πi/3", italic=False, anchor="end", size=13.0),
        math_label(wx - 8.0, 160.0, "0", italic=False, anchor="end", size=13.0),
        math_label(wx - 8.0, 196.0, "−2πi/3", italic=False, anchor="end", size=13.0),
        math_label(wx + 44.0, 52.0, "W", sub="3", anchor="middle", size=13.5),
        math_label(wx + 44.0, 88.0, "W", sub="2", anchor="middle", size=13.5),
        math_label(wx + 44.0, 124.0, "W", sub="1", anchor="middle", size=13.5),
        math_label(wx + 44.0, 160.0, "W", sub="0", anchor="middle", size=13.5),
        math_label(wx + 44.0, 196.0, "W", sub="−1", anchor="middle", size=13.5),
        math_label(wx, 262.0, "w", tail="-plane", anchor="middle"),
    ]
    return svg_document(
        "0 0 530 284",
        grid="\n".join(ax_parts),
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_2",
        title=CHAPTER_FIG_TITLES["4_2"],
    )


def fig_4_3() -> str:
    c0x, c0y, r0 = 186.0, 128.0, 104.0
    ang_c1 = math.radians(-30.0)
    dist = 62.0
    c1x = c0x + dist * math.cos(ang_c1)
    c1y = c0y - dist * math.sin(ang_c1)
    rho = r0 - dist
    r1 = 94.0

    ang_r0 = math.radians(60.0)
    r0_end_x = c0x + r0 * math.cos(ang_r0)
    r0_end_y = c0y - r0 * math.sin(ang_r0)

    ang_r1 = math.radians(18.0)
    r1_end_x = c1x + r1 * math.cos(ang_r1)
    r1_end_y = c1y - r1 * math.sin(ang_r1)

    rho_end_x = c1x + rho * math.cos(ang_c1)
    rho_end_y = c1y - rho * math.sin(ang_c1)

    axes_el = f'    <line x1="{c0x:.1f}" y1="{c0y:.1f}" x2="{rho_end_x:.1f}" y2="{rho_end_y:.1f}" class="c-sub" stroke-dasharray="3,3" />'
    reg_parts = [
        f'    <circle cx="{c0x:.1f}" cy="{c0y:.1f}" r="{r0:.1f}" class="f-blue" />',
        f'    <circle cx="{c1x:.1f}" cy="{c1y:.1f}" r="{r1:.1f}" class="f-amber" />',
        f'    <circle cx="{c0x:.1f}" cy="{c0y:.1f}" r="{r0:.1f}" class="f-stipple" />',
        f'    <circle cx="{c1x:.1f}" cy="{c1y:.1f}" r="{r1:.1f}" class="f-stipple" />',
        f'    <circle cx="{c1x:.1f}" cy="{c1y:.1f}" r="{rho:.1f}" class="f-blue" />',
        f'    <circle cx="{c1x:.1f}" cy="{c1y:.1f}" r="{rho:.1f}" class="f-hatch" />',
    ]
    cur_parts = [
        circle_contour(c0x, c0y, r0, cls="c-blue"),
        circle_contour(c1x, c1y, r1, cls="c-amber"),
        circle_contour(c1x, c1y, rho, cls="c-main"),
        arrow_line(c0x, c0y, r0_end_x, r0_end_y, cls="c-blue", marker="arr-blue"),
        arrow_line(c1x, c1y, r1_end_x, r1_end_y, cls="c-amber", marker="arr-amber"),
        arrow_line(c1x, c1y, rho_end_x, rho_end_y, cls="c-main", marker="arr"),
    ]
    lbl_parts = [
        point_dot(c0x, c0y),
        point_dot(c1x, c1y),
        math_label(c0x - 20.0, c0y + 14.0, "c", sub="0"),
        math_label(c1x - 22.0, c1y + 10.0, "c", sub="1"),
        math_label(c0x + 34.0, c0y - 38.0, "r", sub="0"),
        math_label(c1x + 56.0, c1y - 4.0, "r", sub="1"),
        math_label(c1x + 4.0, c1y + 24.0, "ρ"),
    ]
    return svg_document(
        "0 0 430 286",
        grid=axes_el,
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_3",
        title=CHAPTER_FIG_TITLES["4_3"],
    )


def fig_4_4() -> str:
    c0 = (56.0, 166.0)
    c1 = (214.0, 56.0)
    c2 = (408.0, 162.0)

    pts1 = [c0, (104.0, 104.0), (160.0, 102.0), c1]
    pts2 = [c1, (266.0, 96.0), (344.0, 96.0), c2]

    axes_el = f'    <line x1="{c0[0]:.1f}" y1="{c0[1]:.1f}" x2="{c2[0]:.1f}" y2="{c2[1]:.1f}" class="c-sub" stroke-dasharray="3,4" />'
    cur_parts = [
        smooth_curve(pts1, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"),
        smooth_curve(
            pts2, cls="c-green", arrow_indices=[(1, True)], marker="arr-green"
        ),
    ]
    lbl_parts = [
        point_dot(*c0),
        point_dot(*c1),
        point_dot(*c2),
        math_label(c0[0] - 24.0, c0[1] + 8.0, "c", sub="0"),
        math_label(c1[0] - 8.0, c1[1] - 12.0, "c", sub="1"),
        math_label(c2[0] - 4.0, c2[1] + 22.0, "c", sub="2"),
        math_label(130.0, 128.0, "γ", sub="1"),
        math_label(318.0, 124.0, "γ", sub="2"),
    ]
    return svg_document(
        "0 0 460 216",
        grid=axes_el,
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_4",
        title=CHAPTER_FIG_TITLES["4_4"],
    )


def fig_4_5() -> str:
    c0 = (56.0, 156.0)
    c1 = (146.0, 62.0)
    c2 = (172.0, 152.0)
    p3 = (278.0, 44.0)
    p4 = (332.0, 146.0)
    p5 = (378.0, 66.0)
    cn = (464.0, 114.0)

    axes_el = f'    <line x1="{c0[0]:.1f}" y1="{c0[1]:.1f}" x2="{cn[0]:.1f}" y2="{cn[1]:.1f}" class="c-sub" stroke-dasharray="3,4" />'
    cur_parts = [
        smooth_curve(
            [c0, (98.0, 102.0), c1],
            cls="c-blue",
            arrow_indices=[(0, True)],
            marker="arr-blue",
        ),
        smooth_curve(
            [c1, (154.0, 116.0), c2],
            cls="c-blue",
            arrow_indices=[(0, True)],
            marker="arr-blue",
        ),
        smooth_curve(
            [c2, (218.0, 90.0), p3],
            cls="c-blue",
            arrow_indices=[(0, True)],
            marker="arr-blue",
        ),
        smooth_curve(
            [p3, (262.0, 102.0), (284.0, 134.0), p4],
            cls="c-blue",
            arrow_indices=[(1, True)],
            marker="arr-blue",
        ),
        smooth_curve(
            [p4, (352.0, 102.0), p5],
            cls="c-blue",
            arrow_indices=[(0, True)],
            marker="arr-blue",
        ),
        smooth_curve(
            [p5, (408.0, 102.0), cn],
            cls="c-blue",
            arrow_indices=[(1, True)],
            marker="arr-blue",
        ),
    ]
    lbl_parts = [
        point_dot(*c0),
        point_dot(*c1),
        point_dot(*c2),
        point_dot(*p3),
        point_dot(*p4),
        point_dot(*p5),
        point_dot(*cn),
        math_label(c0[0] - 8.0, c0[1] + 22.0, "c", sub="0"),
        math_label(c1[0] - 4.0, c1[1] - 10.0, "c", sub="1"),
        math_label(c2[0] - 6.0, c2[1] + 22.0, "c", sub="2"),
        math_label(cn[0] - 6.0, cn[1] + 22.0, "c", sub="n"),
        math_label(82.0, 94.0, "γ", sub="1"),
        math_label(132.0, 124.0, "γ", sub="2"),
        math_label(224.0, 98.0, "γ", sub="3"),
        math_label(408.0, 126.0, "γ", sub="n"),
    ]
    return svg_document(
        "0 0 510 210",
        grid=axes_el,
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_5",
        title=CHAPTER_FIG_TITLES["4_5"],
    )


def fig_4_6() -> str:
    c0 = (36.0, 82.0)
    gs = (206.0, 124.0)
    gt = (244.0, 156.0)
    rs = 74.0
    rt = 84.0

    ang_s = math.radians(70.0)
    rs_end = (gs[0] + rs * math.cos(ang_s), gs[1] - rs * math.sin(ang_s))
    ang_t = math.radians(32.0)
    rt_end = (gt[0] + rt * math.cos(ang_t), gt[1] - rt * math.sin(ang_t))

    gamma_pts = [
        c0,
        (106.0, 36.0),
        (158.0, 68.0),
        gs,
        gt,
        (308.0, 176.0),
        (366.0, 162.0),
        (414.0, 134.0),
    ]
    reg_parts = [
        f'    <circle cx="{gs[0]:.1f}" cy="{gs[1]:.1f}" r="{rs:.1f}" class="f-blue" />',
        f'    <circle cx="{gt[0]:.1f}" cy="{gt[1]:.1f}" r="{rt:.1f}" class="f-amber" />',
    ]
    cur_parts = [
        circle_contour(gs[0], gs[1], rs, cls="c-blue"),
        circle_contour(gt[0], gt[1], rt, cls="c-amber"),
        arrow_line(gs[0], gs[1], rs_end[0], rs_end[1], cls="c-blue", marker="arr-blue"),
        arrow_line(
            gt[0], gt[1], rt_end[0], rt_end[1], cls="c-amber", marker="arr-amber"
        ),
        smooth_curve(gamma_pts, cls="c-main", arrow_indices=[(5, True)], marker="arr"),
    ]
    lbl_parts = [
        point_dot(*c0),
        point_dot(*gs),
        point_dot(*gt),
        math_label(c0[0] - 8.0, c0[1] + 22.0, "c", sub="0"),
        math_label(gs[0] - 42.0, gs[1] + 18.0, "γ(s)"),
        math_label(gt[0] - 42.0, gt[1] + 18.0, "γ(t)"),
        math_label(gs[0] + 16.0, gs[1] - 24.0, "r(s)"),
        math_label(gt[0] + 34.0, gt[1] - 8.0, "r(t)"),
        math_label(364.0, 178.0, "γ"),
    ]
    return svg_document(
        "0 0 460 264",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_6",
        title=CHAPTER_FIG_TITLES["4_6"],
    )


def fig_4_7() -> str:
    blobs = [
        (106.0, 114.0, 64.0, 66.0, -10.0, "f-blue"),
        (174.0, 134.0, 62.0, 68.0, 15.0, "f-amber"),
        (256.0, 162.0, 68.0, 64.0, -12.0, "f-blue"),
        (348.0, 166.0, 62.0, 66.0, 18.0, "f-amber"),
        (408.0, 108.0, 66.0, 64.0, -8.0, "f-blue"),
    ]
    reg_parts: list[str] = []
    cur_parts: list[str] = []
    for bx, by, rx, ry, rot, fcls in blobs:
        pts = _blob_points(bx, by, rx, ry, rot_deg=rot, wobble=0.06)
        d = _smooth_closed_d(pts)
        reg_parts.append(f'    <path d="{d}" class="{fcls}" />')
        reg_parts.append(f'    <path d="{d}" class="f-stipple" />')
        cur_parts.append(f'    <path d="{d}" class="c-blue-dash" />')

    c0 = (70.0, 96.0)
    c1 = (142.0, 108.0)
    c2 = (212.0, 146.0)
    c3 = (302.0, 178.0)
    cn = (376.0, 136.0)
    c_star = (434.0, 102.0)

    cur_parts.extend(
        [
            smooth_curve(
                [c0, (98.0, 114.0), (122.0, 94.0), c1],
                cls="c-main",
                arrow_indices=[(1, True)],
                marker="arr",
            ),
            smooth_curve(
                [c1, (168.0, 98.0), (182.0, 138.0), c2],
                cls="c-main",
                arrow_indices=[(1, True)],
                marker="arr",
            ),
            smooth_curve(
                [c2, (238.0, 172.0), (266.0, 198.0), c3],
                cls="c-main",
                arrow_indices=[(1, True)],
                marker="arr",
            ),
            smooth_curve(
                [c3, (336.0, 202.0), (350.0, 152.0), cn],
                cls="c-main",
                arrow_indices=[(1, True)],
                marker="arr",
            ),
            smooth_curve(
                [cn, (394.0, 82.0), (416.0, 90.0), c_star],
                cls="c-main",
                arrow_indices=[(1, True)],
                marker="arr",
            ),
        ]
    )
    lbl_parts = [
        point_dot(*c0),
        point_dot(*c1),
        point_dot(*c2),
        point_dot(*c3),
        point_dot(*cn),
        point_dot(*c_star),
        math_label(c0[0] - 12.0, c0[1] + 22.0, "c", sub="0"),
        math_label(c1[0] - 8.0, c1[1] + 22.0, "c", sub="1"),
        math_label(c2[0] - 12.0, c2[1] + 22.0, "c", sub="2"),
        math_label(cn[0] + 6.0, cn[1] + 16.0, "c", sub="n"),
        math_label(c_star[0] + 6.0, c_star[1] + 10.0, "c", sub="*"),
        math_label(94.0, 92.0, "γ", sub="0"),
        math_label(182.0, 106.0, "γ", sub="1"),
        math_label(254.0, 182.0, "γ", sub="2"),
        math_label(402.0, 72.0, "γ", sub="n"),
        math_label(86.0, 156.0, "U", sub="0"),
        math_label(156.0, 188.0, "U", sub="1"),
        math_label(228.0, 222.0, "U", sub="2"),
        math_label(426.0, 152.0, "U", sub="n"),
    ]
    return svg_document(
        "0 0 500 260",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_7",
        title=CHAPTER_FIG_TITLES["4_7"],
    )


def fig_4_8() -> str:
    outer_pts = _blob_points(
        232.0, 146.0, 198.0, 122.0, rot_deg=-4.0, wobble=0.07, n=16
    )
    hole_pts = _blob_points(342.0, 194.0, 44.0, 28.0, rot_deg=-24.0, wobble=0.05, n=10)
    outer_d = _smooth_closed_d(outer_pts)
    hole_d = _smooth_closed_d(hole_pts)
    omega_d = f"{outer_d} {hole_d}"

    c0 = (96.0, 152.0)
    c1 = (346.0, 98.0)

    family = [
        ([c0, (176.0, 66.0), (272.0, 52.0), c1], "c-main", "arr"),
        ([c0, (178.0, 92.0), (268.0, 76.0), c1], "c-blue", "arr-blue"),
        ([c0, (182.0, 118.0), (266.0, 98.0), c1], "c-blue", "arr-blue"),
        ([c0, (188.0, 144.0), (266.0, 124.0), c1], "c-blue", "arr-blue"),
        ([c0, (194.0, 174.0), (266.0, 152.0), c1], "c-blue", "arr-blue"),
        ([c0, (202.0, 206.0), (268.0, 182.0), c1], "c-main", "arr"),
    ]
    reg_parts = [
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-blue" />',
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-stipple" />',
    ]
    cur_parts = [
        f'    <path d="{outer_d}" class="c-blue-dash" />',
        f'    <path d="{hole_d}" class="c-blue-dash" />',
    ]
    for pts, cls, mrk in family:
        cur_parts.append(
            smooth_curve(pts, cls=cls, arrow_indices=[(1, True)], marker=mrk)
        )

    lbl_parts = [
        point_dot(*c0),
        point_dot(*c1),
        math_label(c0[0] - 24.0, c0[1] + 6.0, "c", sub="0"),
        math_label(c1[0] + 8.0, c1[1] + 6.0, "c", sub="1"),
        math_label(208.0, 48.0, "γ", sub="1"),
        math_label(224.0, 134.0, "γ", sub="s"),
        math_label(220.0, 226.0, "γ", sub="0"),
        math_label(250.0, 248.0, "Ω"),
    ]
    return svg_document(
        "0 0 460 286",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_8",
        title=CHAPTER_FIG_TITLES["4_8"],
    )


def fig_4_9() -> str:
    outer_pts = _blob_points(
        232.0, 150.0, 192.0, 128.0, rot_deg=12.0, wobble=0.07, n=16
    )
    hole_pts = _blob_points(304.0, 212.0, 68.0, 36.0, rot_deg=-18.0, wobble=0.05, n=10)
    outer_d = _smooth_closed_d(outer_pts)
    hole_d = _smooth_closed_d(hole_pts)
    omega_d = f"{outer_d} {hole_d}"

    c0 = (114.0, 122.0)
    scales = [1.0, 0.76, 0.56, 0.38, 0.23, 0.11]

    reg_parts = [
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-blue" />',
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-stipple" />',
    ]
    cur_parts = [
        f'    <path d="{outer_d}" class="c-blue-dash" />',
        f'    <path d="{hole_d}" class="c-blue-dash" />',
    ]
    for idx, s in enumerate(scales):
        w = 186.0 * s
        h_up = 76.0 * s
        h_dn = 54.0 * s
        pts = [
            c0,
            (c0[0] + 0.48 * w, c0[1] + h_dn),
            (c0[0] + w, c0[1] + 0.12 * h_dn),
            (c0[0] + 0.92 * w, c0[1] - 0.58 * h_up),
            (c0[0] + 0.46 * w, c0[1] - h_up),
        ]
        cls = "c-main" if idx == 0 else "c-blue"
        mrk = "arr" if idx == 0 else "arr-blue"
        arr = [(2, True)] if s >= 0.2 else None
        cur_parts.append(
            smooth_curve(pts, cls=cls, closed=True, arrow_indices=arr, marker=mrk)
        )

    lbl_parts = [
        point_dot(*c0),
        math_label(c0[0] - 26.0, c0[1] + 5.0, "c", sub="0"),
        math_label(308.0, 102.0, "γ"),
        math_label(346.0, 148.0, "Ω"),
    ]
    return svg_document(
        "0 0 460 296",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_9",
        title=CHAPTER_FIG_TITLES["4_9"],
    )


def fig_4_10() -> str:
    outer_pts = _blob_points(232.0, 146.0, 198.0, 124.0, rot_deg=6.0, wobble=0.07, n=16)
    hole_pts = _blob_points(342.0, 162.0, 44.0, 62.0, rot_deg=16.0, wobble=0.06, n=12)
    outer_d = _smooth_closed_d(outer_pts)
    hole_d = _smooth_closed_d(hole_pts)
    omega_d = f"{outer_d} {hole_d}"

    cx, cy = 162.0, 134.0
    radii = [(92.0, 78.0), (68.0, 56.0), (44.0, 36.0), (20.0, 18.0)]

    reg_parts = [
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-blue" />',
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-stipple" />',
    ]
    cur_parts = [
        f'    <path d="{outer_d}" class="c-blue-dash" />',
        f'    <path d="{hole_d}" class="c-blue-dash" />',
    ]
    for idx, (rx, ry) in enumerate(radii):
        pts = _blob_points(cx, cy, rx, ry, rot_deg=-10.0, wobble=0.05, n=12)
        cls = "c-main" if idx == 0 else "c-blue"
        mrk = "arr" if idx == 0 else "arr-blue"
        cur_parts.append(
            smooth_curve(
                pts, cls=cls, closed=True, arrow_indices=[(11, False)], marker=mrk
            )
        )

    lbl_parts = [
        point_dot(cx, cy),
        math_label(cx - 5.0, cy + 16.0, "c"),
        math_label(260.0, 114.0, "γ"),
        math_label(306.0, 82.0, "Ω"),
    ]
    return svg_document(
        "0 0 460 288",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_10",
        title=CHAPTER_FIG_TITLES["4_10"],
    )


def fig_4_11() -> str:
    x0, y0 = 104.0, 26.0
    side = 236.0
    x1, y1 = x0 + side, y0 + side
    ymid = y0 + 0.5 * side

    reg_parts = [
        f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{side:.1f}" height="{side:.1f}" class="f-blue" />',
    ]
    ax_parts = [
        f'    <line x1="{x0:.1f}" y1="{ymid:.1f}" x2="{x1:.1f}" y2="{ymid:.1f}" class="c-sub" stroke-dasharray="3,4" />',
    ]
    cur_parts = [
        f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{side:.1f}" height="{side:.1f}" class="c-main" />',
    ]
    for k in range(1, 7):
        xk = x0 + side * (2.0 ** (-k))
        cur_parts.append(
            f'    <line x1="{xk:.2f}" y1="{y0:.1f}" x2="{xk:.2f}" y2="{ymid:.1f}" class="c-blue" />'
        )

    lbl_parts = [
        math_label(x0 - 6.0, y1 + 20.0, "0", italic=False, anchor="middle"),
        math_label(x1 + 2.0, y1 + 20.0, "1", italic=False, anchor="middle"),
        math_label(x0 - 14.0, y0 + 8.0, "i", anchor="end"),
        math_label(x0 + 0.52 * side, y0 + 0.66 * side, "Ω", anchor="middle"),
    ]
    return svg_document(
        "0 0 440 296",
        grid="\n".join(ax_parts),
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_11",
        title=CHAPTER_FIG_TITLES["4_11"],
    )


def fig_4_12() -> str:
    pts = [
        (36.0, 108.0),
        (104.0, 148.0),
        (168.0, 144.0),
        (254.0, 74.0),
        (358.0, 40.0),
        (448.0, 72.0),
        (466.0, 144.0),
        (446.0, 212.0),
    ]
    axes_el = f'    <line x1="{pts[0][0]:.1f}" y1="{pts[0][1]:.1f}" x2="{pts[-1][0]:.1f}" y2="{pts[-1][1]:.1f}" class="c-sub" stroke-dasharray="3,4" />'
    cur_parts: list[str] = []
    for i in range(len(pts) - 1):
        cur_parts.append(
            _directed_segment(
                pts[i][0],
                pts[i][1],
                pts[i + 1][0],
                pts[i + 1][1],
                cls="c-blue",
                marker="arr-blue",
            )
        )

    lbl_parts = [point_dot(px, py) for px, py in pts]
    lbl_parts.extend(
        [
            math_label(pts[0][0] - 8.0, pts[0][1] + 22.0, "c", sub="0"),
            math_label(pts[1][0] - 6.0, pts[1][1] + 22.0, "c", sub="1"),
            math_label(pts[3][0] - 8.0, pts[3][1] - 10.0, "c", sub="k"),
            math_label(pts[4][0] - 4.0, pts[4][1] - 10.0, "c", sub="k+1"),
            math_label(pts[6][0] + 8.0, pts[6][1] + 6.0, "c", sub="m"),
            math_label(pts[7][0] - 4.0, pts[7][1] + 20.0, "c"),
            math_label(248.0, 122.0, "L(σ)"),
        ]
    )
    return svg_document(
        "0 0 510 246",
        grid=axes_el,
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_12",
        title=CHAPTER_FIG_TITLES["4_12"],
    )


def fig_4_13() -> str:
    c0 = (44.0, 126.0)
    gt1 = (88.0, 186.0)
    gt2 = (168.0, 178.0)
    gtk = (242.0, 92.0)
    gt = (326.0, 44.0)
    gtk1 = (386.0, 62.0)
    gt_mid = (440.0, 152.0)
    gtm = (432.0, 206.0)
    c_end = (406.0, 248.0)

    c1 = (102.0, 174.0)
    p2 = (160.0, 166.0)
    ck = (254.0, 120.0)
    gnt = (326.0, 112.0)
    ck1 = (378.0, 106.0)
    pm1 = (458.0, 146.0)
    cm = (468.0, 198.0)
    gts = (326.0, 74.0)

    poly_pts = [c0, c1, p2, ck, ck1, pm1, cm, c_end]
    poly_d = " ".join(
        [f"M {poly_pts[0][0]:.1f} {poly_pts[0][1]:.1f}"]
        + [f"L {px:.1f} {py:.1f}" for px, py in poly_pts[1:]]
    )
    gamma_pts = [c0, gt1, gt2, gtk, gt, gtk1, gt_mid, gtm, c_end]

    axes_el = f'    <line x1="{gt[0]:.1f}" y1="{gt[1]:.1f}" x2="{gnt[0]:.1f}" y2="{gnt[1]:.1f}" class="c-red-dash" />'
    cur_parts = [
        f'    <path d="{poly_d}" class="c-blue" />',
        smooth_curve(gamma_pts, cls="c-main"),
        f'    <line x1="{gt[0]:.1f}" y1="{gt[1]:.1f}" x2="{gnt[0]:.1f}" y2="{gnt[1]:.1f}" class="c-red" />',
    ]
    dots = [
        c0,
        gt1,
        gt2,
        gtk,
        gt,
        gtk1,
        gt_mid,
        gtm,
        c_end,
        c1,
        p2,
        ck,
        gnt,
        ck1,
        pm1,
        cm,
        gts,
    ]
    lbl_parts = [point_dot(px, py) for px, py in dots]
    lbl_parts.extend(
        [
            math_label(c0[0] - 22.0, c0[1] + 4.0, "c", sub="0"),
            math_label(c1[0] - 4.0, c1[1] - 10.0, "c", sub="1"),
            math_label(gt1[0] - 38.0, gt1[1] + 22.0, "γ(t", sub="1", tail=")"),
            math_label(gtk[0] - 54.0, gtk[1] + 2.0, "γ(t", sub="k", tail=")"),
            math_label(ck[0] - 8.0, ck[1] + 18.0, "c", sub="k"),
            math_label(gt[0] - 16.0, gt[1] - 12.0, "γ(t)"),
            math_label(gts[0] + 8.0, gts[1] + 5.0, "Γ(t, s)"),
            math_label(gnt[0] - 24.0, gnt[1] + 22.0, "γ", sub="n", tail="(t)"),
            math_label(gtk1[0] + 6.0, gtk1[1] - 4.0, "γ(t", sub="k+1", tail=")"),
            math_label(ck1[0] - 10.0, ck1[1] + 18.0, "c", sub="k+1"),
            math_label(gtm[0] - 56.0, gtm[1] + 2.0, "γ(t", sub="m", tail=")"),
            math_label(cm[0] + 8.0, cm[1] + 5.0, "c", sub="m"),
            math_label(c_end[0] - 6.0, c_end[1] + 18.0, "c"),
        ]
    )
    return svg_document(
        "0 0 516 278",
        grid=axes_el,
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_13",
        title=CHAPTER_FIG_TITLES["4_13"],
    )


def fig_4_14() -> str:
    outer_pts = _blob_points(
        230.0, 146.0, 198.0, 124.0, rot_deg=-3.0, wobble=0.06, n=16
    )
    hole1_pts = _blob_points(172.0, 114.0, 52.0, 44.0, rot_deg=10.0, wobble=0.04, n=12)
    hole2_pts = _blob_points(358.0, 186.0, 34.0, 48.0, rot_deg=24.0, wobble=0.05, n=12)
    outer_d = _smooth_closed_d(outer_pts)
    h1_d = _smooth_closed_d(hole1_pts)
    h2_d = _smooth_closed_d(hole2_pts)
    omega_d = f"{outer_d} {h1_d} {h2_d}"

    c0 = (84.0, 194.0)
    v1 = (142.0, 210.0)
    v2 = (196.0, 168.0)
    v3 = (242.0, 194.0)
    v4 = (310.0, 170.0)
    v5 = (320.0, 112.0)
    z_pt = (312.0, 52.0)

    reg_parts = [
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-blue" />',
        f'    <path d="{omega_d}" fill-rule="evenodd" class="f-stipple" />',
    ]
    cur_parts = [
        f'    <path d="{outer_d}" class="c-blue-dash" />',
        f'    <path d="{h1_d}" class="c-blue-dash" />',
        f'    <path d="{h2_d}" class="c-blue-dash" />',
        smooth_curve([c0, (114.0, 198.0), v1], cls="c-main"),
        smooth_curve([v1, (168.0, 188.0), v2], cls="c-main"),
        smooth_curve([v2, (220.0, 178.0), v3], cls="c-main"),
        smooth_curve(
            [v3, (276.0, 180.0), v4],
            cls="c-main",
            arrow_indices=[(0, True)],
            marker="arr",
        ),
        smooth_curve([v4, (310.0, 140.0), v5], cls="c-main"),
        smooth_curve([v5, (310.0, 84.0), z_pt], cls="c-main"),
    ]
    lbl_parts = [point_dot(px, py) for px, py in [c0, v1, v2, v3, v4, v5, z_pt]]
    lbl_parts.extend(
        [
            math_label(c0[0] - 8.0, c0[1] + 22.0, "c", sub="0"),
            math_label(z_pt[0] - 4.0, z_pt[1] - 10.0, "z"),
            math_label(266.0, 204.0, "γ"),
            math_label(252.0, 102.0, "Ω"),
        ]
    )
    return svg_document(
        "0 0 460 288",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_14",
        title=CHAPTER_FIG_TITLES["4_14"],
    )


def fig_4_15() -> str:
    gs = (196.0, 142.0)
    gt = (264.0, 128.0)
    rs = 104.0
    rt = 94.0
    z_pt = (238.0, 68.0)

    gamma_pts = [
        (26.0, 264.0),
        (82.0, 224.0),
        (140.0, 174.0),
        gs,
        gt,
        (348.0, 106.0),
        (434.0, 38.0),
    ]
    axes_el = f'    <line x1="{gs[0]:.1f}" y1="{gs[1]:.1f}" x2="{z_pt[0]:.1f}" y2="{z_pt[1]:.1f}" class="c-sub" stroke-dasharray="3,3" />'
    reg_parts = [
        f'    <circle cx="{gs[0]:.1f}" cy="{gs[1]:.1f}" r="{rs:.1f}" class="f-blue" />',
        f'    <circle cx="{gt[0]:.1f}" cy="{gt[1]:.1f}" r="{rt:.1f}" class="f-amber" />',
        f'    <circle cx="{gs[0]:.1f}" cy="{gs[1]:.1f}" r="{rs:.1f}" class="f-stipple" />',
        f'    <circle cx="{gt[0]:.1f}" cy="{gt[1]:.1f}" r="{rt:.1f}" class="f-stipple" />',
    ]
    cur_parts = [
        circle_contour(gs[0], gs[1], rs, cls="c-blue-dash"),
        circle_contour(gt[0], gt[1], rt, cls="c-dash"),
        f'    <line x1="{gt[0]:.1f}" y1="{gt[1]:.1f}" x2="{z_pt[0]:.1f}" y2="{z_pt[1]:.1f}" class="c-red" />',
        smooth_curve(
            gamma_pts, cls="c-main", arrow_indices=[(0, True), (2, True)], marker="arr"
        ),
    ]
    lbl_parts = [
        point_dot(*gs),
        point_dot(*gt),
        point_dot(*z_pt),
        math_label(66.0, 246.0, "γ"),
        math_label(100.0, 122.0, "U(γ(s))"),
        math_label(gs[0] - 12.0, gs[1] + 24.0, "γ(s)"),
        math_label(gt[0] - 10.0, gt[1] + 24.0, "γ(t)"),
        math_label(z_pt[0] - 6.0, z_pt[1] - 10.0, "z"),
    ]
    return svg_document(
        "0 0 460 284",
        grid=axes_el,
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_15",
        title=CHAPTER_FIG_TITLES["4_15"],
    )


def fig_4_16() -> str:
    omega_pts = _blob_points(
        204.0, 146.0, 156.0, 122.0, rot_deg=14.0, wobble=0.06, n=16
    )
    omega_d = _smooth_closed_d(omega_pts)

    gb = (232.0, 114.0)
    rb = 62.0
    z_pt = (268.0, 92.0)
    c0 = (64.0, 224.0)

    alpha_pts = [c0, (104.0, 164.0), (158.0, 132.0), gb]
    beta_pts = [gb, (252.0, 106.0), z_pt]

    reg_parts = [
        f'    <path d="{omega_d}" class="f-blue" />',
        f'    <path d="{omega_d}" class="f-stipple" />',
        f'    <circle cx="{gb[0]:.1f}" cy="{gb[1]:.1f}" r="{rb:.1f}" class="f-amber" />',
        f'    <circle cx="{gb[0]:.1f}" cy="{gb[1]:.1f}" r="{rb:.1f}" class="f-hatch" />',
    ]
    cur_parts = [
        f'    <path d="{omega_d}" class="c-blue-dash" />',
        circle_contour(gb[0], gb[1], rb, cls="c-amber"),
        smooth_curve(alpha_pts, cls="c-main", arrow_indices=[(1, True)], marker="arr"),
        smooth_curve(
            beta_pts, cls="c-blue", arrow_indices=[(0, True)], marker="arr-blue"
        ),
    ]
    lbl_parts = [
        point_dot(*c0),
        point_dot(*gb),
        point_dot(*z_pt),
        math_label(116.0, 138.0, "α"),
        math_label(244.0, 98.0, "β"),
        math_label(z_pt[0] + 6.0, z_pt[1] - 4.0, "z"),
        math_label(gb[0] - 18.0, gb[1] + 22.0, "γ(b)"),
        math_label(gb[0] - 38.0, gb[1] + 46.0, "U(γ(b))"),
        math_label(184.0, 226.0, "Ω"),
    ]
    return svg_document(
        "0 0 430 286",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_16",
        title=CHAPTER_FIG_TITLES["4_16"],
    )


def fig_4_17() -> str:
    ls = (264.0, 152.0)
    lu = (344.0, 96.0)
    ru = 122.0
    corner = (98.0, 108.0)
    gs_start = (28.0, 260.0)

    lambda_s_pts = [(80.0, 268.0), (132.0, 166.0), (196.0, 120.0), ls]
    lambda_su_pts = [ls, (312.0, 168.0), (342.0, 142.0), lu]
    lambda_rest_pts = [lu, (348.0, 48.0), (392.0, 26.0), (434.0, 20.0)]

    reg_parts = [
        f'    <circle cx="{ls[0]:.1f}" cy="{ls[1]:.1f}" r="{ru:.1f}" class="f-blue" />',
        f'    <circle cx="{ls[0]:.1f}" cy="{ls[1]:.1f}" r="{ru:.1f}" class="f-stipple" />',
    ]
    cur_parts = [
        circle_contour(ls[0], ls[1], ru, cls="c-blue-dash"),
        _directed_segment(
            gs_start[0],
            gs_start[1],
            corner[0],
            corner[1],
            cls="c-blue",
            marker="arr-blue",
            frac=0.45,
        ),
        _directed_segment(
            corner[0],
            corner[1],
            ls[0],
            ls[1],
            cls="c-blue",
            marker="arr-blue",
            frac=0.35,
        ),
        _directed_segment(
            ls[0], ls[1], lu[0], lu[1], cls="c-red", marker="arr-red", frac=0.52
        ),
        smooth_curve(
            lambda_s_pts, cls="c-main", arrow_indices=[(0, True)], marker="arr"
        ),
        smooth_curve(
            lambda_su_pts, cls="c-main", arrow_indices=[(1, True)], marker="arr"
        ),
        smooth_curve(
            lambda_rest_pts, cls="c-main", arrow_indices=[(1, True)], marker="arr"
        ),
    ]
    lbl_parts = [
        point_dot(*ls),
        point_dot(*lu),
        math_label(34.0, 182.0, "γ", sub="s"),
        math_label(102.0, 240.0, "λ", sup="s"),
        math_label(ls[0] - 48.0, ls[1] + 24.0, "λ(s)"),
        math_label(288.0, 118.0, "μ"),
        math_label(340.0, 168.0, "λ", sub="s", sup="u"),
        math_label(lu[0] + 10.0, lu[1] + 6.0, "λ(u)"),
        math_label(ls[0] - 38.0, ls[1] + 76.0, "U(λ(s))"),
    ]
    return svg_document(
        "0 0 460 292",
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_17",
        title=CHAPTER_FIG_TITLES["4_17"],
    )


def fig_4_18() -> str:
    ox, oy = 216.0, 144.0
    r_outer = 114.0
    r_inner = 32.0
    minus1_x = ox - 64.0
    eps_x = ox + r_inner
    big_r_x = ox + r_outer

    annulus_d = (
        f"M {ox - r_outer:.1f} {oy:.1f} "
        f"A {r_outer:.1f} {r_outer:.1f} 0 1 0 {ox + r_outer:.1f} {oy:.1f} "
        f"A {r_outer:.1f} {r_outer:.1f} 0 1 0 {ox - r_outer:.1f} {oy:.1f} Z "
        f"M {ox - r_inner:.1f} {oy:.1f} "
        f"A {r_inner:.1f} {r_inner:.1f} 0 1 0 {ox + r_inner:.1f} {oy:.1f} "
        f"A {r_inner:.1f} {r_inner:.1f} 0 1 0 {ox - r_inner:.1f} {oy:.1f} Z"
    )
    axes_el = f'    <line x1="{ox - r_outer - 14:.1f}" y1="{oy:.1f}" x2="{ox + r_outer + 14:.1f}" y2="{oy:.1f}" class="ax" />'
    reg_parts = [
        f'    <path d="{annulus_d}" fill-rule="evenodd" class="f-blue" />',
        f'    <path d="{annulus_d}" fill-rule="evenodd" class="f-stipple" />',
    ]
    cur_parts = [
        circle_contour(
            ox, oy, r_outer, cls="c-main", arrow_deg=48.0, ccw=True, marker="arr"
        ),
        circle_contour(
            ox, oy, r_inner, cls="c-blue", arrow_deg=48.0, ccw=True, marker="arr-blue"
        ),
        _directed_segment(
            eps_x, oy, big_r_x, oy, cls="c-red", marker="arr-red", frac=0.56
        ),
    ]
    lbl_parts = [
        point_dot(minus1_x, oy),
        point_dot(ox, oy),
        point_dot(eps_x, oy),
        point_dot(big_r_x, oy),
        math_label(ox - 62.0, oy - 56.0, "D"),
        math_label(minus1_x - 14.0, oy + 22.0, "−1", italic=False),
        math_label(ox - 5.0, oy + 20.0, "0", italic=False),
        math_label(eps_x + 6.0, oy + 16.0, "ε"),
        math_label(big_r_x + 8.0, oy + 6.0, "R"),
        math_label(ox + 24.0, oy - 24.0, "C", sub="ε"),
        math_label(ox + 84.0, oy - 88.0, "C", sub="R"),
    ]
    return svg_document(
        "0 0 440 288",
        grid=axes_el,
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_18",
        title=CHAPTER_FIG_TITLES["4_18"],
    )


def fig_4_19() -> str:
    c0 = (70.0, 232.0)
    c1 = (388.0, 96.0)
    c2 = (82.0, 28.0)

    pts1 = [c0, (194.0, 222.0), (316.0, 134.0), c1]
    pts2 = [c2, (62.0, 78.0), (104.0, 166.0), c0]

    axes_el = f'    <line x1="{c2[0]:.1f}" y1="{c2[1]:.1f}" x2="{c1[0]:.1f}" y2="{c1[1]:.1f}" class="c-sub" stroke-dasharray="3,4" />'
    cur_parts = [
        smooth_curve(pts1, cls="c-blue", arrow_indices=[(1, True)], marker="arr-blue"),
        smooth_curve(
            pts2, cls="c-green", arrow_indices=[(1, True)], marker="arr-green"
        ),
    ]
    lbl_parts = [
        point_dot(*c0),
        point_dot(*c1),
        point_dot(*c2),
        math_label(c0[0] - 26.0, c0[1] + 6.0, "c", sub="0"),
        math_label(c1[0] + 8.0, c1[1] + 5.0, "c", sub="1"),
        math_label(c2[0] + 8.0, c2[1] + 5.0, "c", sub="2"),
        math_label(284.0, 182.0, "γ", sub="1"),
        math_label(54.0, 138.0, "γ", sub="2"),
    ]
    return svg_document(
        "0 0 450 266",
        grid=axes_el,
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_19",
        title=CHAPTER_FIG_TITLES["4_19"],
    )


def fig_4_20() -> str:
    oy = 140.0
    r = 86.0
    x0 = 216.0
    x1 = x0 + r
    x2 = x1 + r

    axes_el = (
        f'    <line x1="22.0" y1="{oy:.1f}" x2="498.0" y2="{oy:.1f}" class="ax" />'
    )
    reg_parts = [
        f'    <circle cx="{x0:.1f}" cy="{oy:.1f}" r="{r:.1f}" class="f-blue" />',
        f'    <circle cx="{x2:.1f}" cy="{oy:.1f}" r="{r:.1f}" class="f-amber" />',
    ]
    cur_parts = [
        f'    <line x1="26.0" y1="{oy:.1f}" x2="{x0:.1f}" y2="{oy:.1f}" class="c-red" />',
        circle_contour(
            x0, oy, r, cls="c-blue", arrow_deg=56.0, ccw=True, marker="arr-blue"
        ),
        circle_contour(
            x2, oy, r, cls="c-amber", arrow_deg=54.0, ccw=True, marker="arr-amber"
        ),
    ]
    lbl_parts = [
        point_dot(x0, oy),
        point_dot(x1, oy),
        point_dot(x2, oy),
        math_label(x0 + 6.0, oy + 5.0, "0", italic=False),
        math_label(x1 + 6.0, oy + 5.0, "1", italic=False),
        math_label(x2 + 6.0, oy + 5.0, "2", italic=False),
        math_label(x0 + 54.0, oy - 78.0, "β"),
        math_label(x2 + 56.0, oy - 74.0, "α"),
    ]
    return svg_document(
        "0 0 516 280",
        grid=axes_el,
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_20",
        title=CHAPTER_FIG_TITLES["4_20"],
    )


def fig_4_21() -> str:
    ox, oy = 216.0, 144.0
    r_outer = 112.0
    r_inner = 38.0
    eps_x = ox + r_inner
    one_x = ox + r_outer

    axes_el = f'    <line x1="{ox - r_outer - 12:.1f}" y1="{oy:.1f}" x2="{ox + r_outer + 12:.1f}" y2="{oy:.1f}" class="ax" />'
    reg_parts = [
        f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r_outer:.1f}" class="f-blue" />',
        f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r_inner:.1f}" class="f-amber" />',
    ]
    cur_parts = [
        circle_contour(
            ox, oy, r_outer, cls="c-main", arrow_deg=44.0, ccw=True, marker="arr"
        ),
        circle_contour(
            ox, oy, r_inner, cls="c-blue", arrow_deg=88.0, ccw=True, marker="arr-blue"
        ),
        _directed_segment(
            eps_x, oy, one_x, oy, cls="c-red", marker="arr-red", frac=0.52
        ),
    ]
    lbl_parts = [
        point_dot(ox, oy),
        point_dot(eps_x, oy),
        point_dot(one_x, oy),
        math_label(ox - 5.0, oy + 20.0, "0", italic=False),
        math_label(eps_x + 5.0, oy + 15.0, "ε"),
        math_label(one_x + 8.0, oy + 5.0, "1", italic=False),
        math_label(ox - 6.0, oy - 48.0, "C", sub="ε"),
        math_label(0.5 * (eps_x + one_x) - 4.0, oy - 10.0, "λ"),
        math_label(ox + 84.0, oy - 86.0, "β"),
    ]
    return svg_document(
        "0 0 432 288",
        grid=axes_el,
        region="\n".join(reg_parts),
        curve="\n".join(cur_parts),
        label="\n".join(lbl_parts),
        fig_id="4_21",
        title=CHAPTER_FIG_TITLES["4_21"],
    )


CHAPTER_SVG_GENERATORS: dict[str, Callable[[], str]] = {
    "4_1": fig_4_1,
    "4_2": fig_4_2,
    "4_3": fig_4_3,
    "4_4": fig_4_4,
    "4_5": fig_4_5,
    "4_6": fig_4_6,
    "4_7": fig_4_7,
    "4_8": fig_4_8,
    "4_9": fig_4_9,
    "4_10": fig_4_10,
    "4_11": fig_4_11,
    "4_12": fig_4_12,
    "4_13": fig_4_13,
    "4_14": fig_4_14,
    "4_15": fig_4_15,
    "4_16": fig_4_16,
    "4_17": fig_4_17,
    "4_18": fig_4_18,
    "4_19": fig_4_19,
    "4_20": fig_4_20,
    "4_21": fig_4_21,
}
