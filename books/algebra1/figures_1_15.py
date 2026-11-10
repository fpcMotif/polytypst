"""3Blue1Brown-styled figure generators for Algebra I: Figures 1 to 15.

Mathematically authentic reconstructions from the source scan.
"""

import math
from .figures_common import (
    AMBER,
    AMBER_BG,
    BLUE,
    BLUE_BG,
    GREEN,
    INK,
    MUTED,
    RED,
    SLATE,
    arrow,
    line,
    point,
    pt_labeled,
    svg_wrap,
)


def gen_fig_1() -> str:
    """Fig 1: 4-point affine plane over F_2."""
    w, h = 260, 220
    c = []
    # Points A, B, C, D
    # A=(70, 150), B=(70, 70), C=(170, 150), D=(170, 70)
    ax, ay = 70, 150
    bx, by = 70, 70
    cx, cy = 170, 150
    dx, dy = 170, 70

    # Extended horizontal and vertical lines
    c.append(line(35, ay, 205, ay, stroke=SLATE, width=1.4))
    c.append(line(35, by, 205, by, stroke=SLATE, width=1.4))
    c.append(line(ax, 35, ax, 185, stroke=SLATE, width=1.4))
    c.append(line(cx, 35, cx, 185, stroke=SLATE, width=1.4))

    # Extended diagonals
    c.append(line(ax - 20, ay + 20, dx + 20, dy - 20, stroke=BLUE, width=1.6, dash="5,4"))
    c.append(line(bx - 20, by - 20, cx + 20, cy + 20, stroke=BLUE, width=1.6, dash="5,4"))

    # Square polygon highlight
    c.append(f'    <polygon points="{ax},{ay} {bx},{by} {dx},{dy} {cx},{cy}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="2.0" />')

    # Points with labels
    c.append(pt_labeled(ax, ay, "A", dx=-16, dy=16, r=4.5, fill=BLUE))
    c.append(pt_labeled(bx, by, "B", dx=-16, dy=-8, r=4.5, fill=BLUE))
    c.append(pt_labeled(cx, cy, "C", dx=8, dy=16, r=4.5, fill=BLUE))
    c.append(pt_labeled(dx, dy, "D", dx=8, dy=-8, r=4.5, fill=BLUE))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_2() -> str:
    """Fig 2: 9-point affine plane over F_3."""
    w, h = 280, 260
    c = []
    xs = [60, 140, 220]
    ys = [60, 140, 220]
    labels = [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G", "H", "I"],
    ]

    # Grid background square
    c.append(f'    <rect x="60" y="60" width="160" height="160" fill="{BLUE_BG}" stroke="{INK}" stroke-width="2.0" />')

    # Extended orthogonal grid lines
    for x in xs:
        c.append(line(x, 25, x, 245, stroke=SLATE, width=1.4))
    for y in ys:
        c.append(line(25, y, 245, y, stroke=SLATE, width=1.4))

    # Diagonals
    c.append(line(xs[0], ys[0], xs[2], ys[2], stroke=BLUE, width=1.4, dash="4,3"))
    c.append(line(xs[0], ys[2], xs[2], ys[0], stroke=BLUE, width=1.4, dash="4,3"))
    c.append(line(xs[0], ys[1], xs[1], ys[0], stroke=GREEN, width=1.2, dash="3,3"))
    c.append(line(xs[1], ys[2], xs[2], ys[1], stroke=GREEN, width=1.2, dash="3,3"))
    c.append(line(xs[1], ys[0], xs[2], ys[2], stroke=AMBER, width=1.2, dash="3,3"))
    c.append(line(xs[0], ys[1], xs[1], ys[2], stroke=AMBER, width=1.2, dash="3,3"))

    # 9 points
    for r_idx in range(3):
        for c_idx in range(3):
            px, py = xs[c_idx], ys[r_idx]
            lbl = labels[r_idx][c_idx]
            c.append(pt_labeled(px, py, lbl, dx=8, dy=-6, r=4.2, fill=INK))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_3() -> str:
    """Fig 3: Addition table for F_2."""
    w, h = 180, 170
    c = []
    # Cayley table grid
    c.append(f'    <rect x="25" y="20" width="130" height="130" rx="8" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.8" />')
    c.append(line(68, 20, 68, 150, stroke=BLUE, width=1.8))
    c.append(line(25, 63, 155, 63, stroke=BLUE, width=1.8))

    # Header
    c.append(f'    <text x="46" y="47" text-anchor="middle" font-size="20" font-weight="bold" fill="{BLUE}">+</text>')
    c.append(f'    <text x="96" y="47" text-anchor="middle" font-size="18" font-weight="bold">0</text>')
    c.append(f'    <text x="133" y="47" text-anchor="middle" font-size="18" font-weight="bold">1</text>')

    # Rows
    c.append(f'    <text x="46" y="93" text-anchor="middle" font-size="18" font-weight="bold">0</text>')
    c.append(f'    <text x="96" y="93" text-anchor="middle" font-size="18">0</text>')
    c.append(f'    <text x="133" y="93" text-anchor="middle" font-size="18">1</text>')

    c.append(f'    <text x="46" y="131" text-anchor="middle" font-size="18" font-weight="bold">1</text>')
    c.append(f'    <text x="96" y="131" text-anchor="middle" font-size="18">1</text>')
    c.append(f'    <text x="133" y="131" text-anchor="middle" font-size="18">0</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_4() -> str:
    """Fig 4: Multiplication table for F_2."""
    w, h = 180, 170
    c = []
    c.append(f'    <rect x="25" y="20" width="130" height="130" rx="8" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.8" />')
    c.append(line(68, 20, 68, 150, stroke="{AMBER}", width=1.8))
    c.append(line(25, 63, 155, 63, stroke="{AMBER}", width=1.8))

    c.append(f'    <text x="46" y="47" text-anchor="middle" font-size="18" font-weight="bold" fill="{AMBER}">×</text>')
    c.append(f'    <text x="96" y="47" text-anchor="middle" font-size="18" font-weight="bold">0</text>')
    c.append(f'    <text x="133" y="47" text-anchor="middle" font-size="18" font-weight="bold">1</text>')

    c.append(f'    <text x="46" y="93" text-anchor="middle" font-size="18" font-weight="bold">0</text>')
    c.append(f'    <text x="96" y="93" text-anchor="middle" font-size="18">0</text>')
    c.append(f'    <text x="133" y="93" text-anchor="middle" font-size="18">0</text>')

    c.append(f'    <text x="46" y="131" text-anchor="middle" font-size="18" font-weight="bold">1</text>')
    c.append(f'    <text x="96" y="131" text-anchor="middle" font-size="18">0</text>')
    c.append(f'    <text x="133" y="131" text-anchor="middle" font-size="18">1</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_5() -> str:
    """Fig 5: Geometric addition on line a via parallel line b."""
    w, h = 380, 160
    y_a, y_b = 115, 55
    c = []
    # Parallel lines a and b
    c.append(line(20, y_b, 350, y_b, stroke=SLATE, width=1.5))
    c.append(line(20, y_a, 350, y_a, stroke=INK, width=2.0))
    c.append(f'    <text x="325" y="{y_b - 8}" font-style="italic" font-size="15">b</text>')
    c.append(f'    <text x="325" y="{y_a - 8}" font-style="italic" font-size="15">a</text>')

    # Points on line a: 0, A, B, C
    x_0, x_a, x_b, x_c = 45, 115, 195, 265
    c.append(pt_labeled(x_0, y_a, "0", dy=-8))
    c.append(pt_labeled(x_a, y_a, "A", dy=-8))
    c.append(pt_labeled(x_b, y_a, "B", dy=-8))
    c.append(pt_labeled(x_c, y_a, "C", dy=-8))

    # Points on line b: U, V
    x_u, x_v = 95, 165
    c.append(pt_labeled(x_u, y_b, "U", dy=-8))
    c.append(pt_labeled(x_v, y_b, "V", dy=-8))

    # Parallel lines: OU || AV
    c.append(line(x_0 - 10, y_a + 12, x_u + 25, y_b - 30, stroke=BLUE, width=1.8))
    c.append(line(x_a - 10, y_a + 12, x_v + 25, y_b - 30, stroke=BLUE, width=1.8))

    # Parallel lines: VC || UB
    c.append(line(x_u - 15, y_b - 12, x_b + 25, y_a + 20, stroke=GREEN, width=1.8))
    c.append(line(x_v - 15, y_b - 12, x_c + 25, y_a + 20, stroke=GREEN, width=1.8))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_6() -> str:
    """Fig 6: Geometric multiplication on line a via line b through 0."""
    w, h = 380, 160
    ox, oy = 55, 95
    c = []
    # Line a (horizontal)
    c.append(line(30, oy, 355, oy, stroke=INK, width=2.0))
    c.append(f'    <text x="330" y="{oy - 8}" font-style="italic" font-size="15">a</text>')

    # Line b (inclined through 0)
    c.append(line(35, oy + 15, 270, 20, stroke=SLATE, width=1.6))
    c.append(f'    <text x="255" y="16" font-style="italic" font-size="15">b</text>')

    # Points on line a: 0, E, A, B, C
    xe, xa, xb, xc = 95, 120, 195, 270
    c.append(pt_labeled(ox, oy, "0", dx=-12, dy=-6))
    c.append(pt_labeled(xe, oy, "E", dy=20))
    c.append(pt_labeled(xa, oy, "A", dy=-8))
    c.append(pt_labeled(xb, oy, "B", dy=-8))
    c.append(pt_labeled(xc, oy, "C", dy=-8))

    # Points on line b: U, V
    xu, yu = 95, 75
    xv, yv = 195, 42
    c.append(pt_labeled(xu, yu, "U", dx=6, dy=-6))
    c.append(pt_labeled(xv, yv, "V", dx=-2, dy=-8))

    # EU || BV
    c.append(line(xe, oy + 25, xu, yu - 20, stroke=BLUE, width=1.6))
    c.append(line(xb, oy + 25, xv, yv - 20, stroke=BLUE, width=1.6))

    # VC || UA
    c.append(line(xu - 15, yu - 15, xa + 15, oy + 15, stroke=GREEN, width=1.6))
    c.append(line(xv - 20, yv - 18, xc + 25, oy + 22, stroke=GREEN, width=1.6))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_7() -> str:
    """Fig 7: Conic secant parametrization through (x_0, y_0) and (x, y)."""
    w, h = 340, 180
    cx, cy = 170, 95
    rx, ry = 80, 48
    c = []
    # Ellipse
    c.append(f'    <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="2.0" />')

    # Secant line
    p0_ang = 2.45
    p1_ang = -0.65
    x0 = cx + rx * math.cos(p0_ang)
    y0 = cy + ry * math.sin(p0_ang)
    x1 = cx + rx * math.cos(p1_ang)
    y1 = cy + ry * math.sin(p1_ang)

    # Extended line
    dx = x1 - x0
    dy = y1 - y0
    c.append(line(x0 - dx * 0.35, y0 - dy * 0.35, x1 + dx * 0.35, y1 + dy * 0.35, stroke="{BLUE}", width=1.8))

    c.append(pt_labeled(x0, y0, "(x₀, y₀)", dx=-10, dy=-10, r=4.5, fill=RED))
    c.append(pt_labeled(x1, y1, "(x, y)", dx=10, dy=8, r=4.5, fill=BLUE))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_8() -> str:
    """Fig 8: Function g with compact support [0, 1/2]."""
    w, h = 260, 180
    ox, oy = 50, 130
    c = []
    c.append(arrow(30, oy, 230, oy, width=1.5))
    c.append(arrow(ox, 150, ox, 25, width=1.5))
    c.append(f'    <text x="225" y="{oy + 16}" font-style="italic">x</text>')
    c.append(f'    <text x="{ox - 14}" y="32" font-style="italic">y</text>')

    # Linear descent from (ox, 80) to (ox + 50, oy)
    c.append(line(ox, 80, ox + 50, oy, stroke=BLUE, width=2.4))
    # Flat zero from (ox + 50, oy) to (ox + 100, oy)
    c.append(line(ox + 50, oy, ox + 150, oy, stroke=BLUE, width=2.8))

    # Ticks
    c.append(pt_labeled(ox + 50, oy, "1/2", dy=18, r=3.2))
    c.append(pt_labeled(ox + 100, oy, "1", dy=18, r=3.2))
    c.append(f'    <text x="{ox + 30}" y="70" font-style="italic" font-size="16" fill="{BLUE}">g</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_9() -> str:
    """Fig 9: Function f with compact support [1/2, 1]."""
    w, h = 260, 180
    ox, oy = 50, 130
    c = []
    c.append(arrow(30, oy, 230, oy, width=1.5))
    c.append(arrow(ox, 150, ox, 25, width=1.5))
    c.append(f'    <text x="225" y="{oy + 16}" font-style="italic">x</text>')
    c.append(f'    <text x="{ox - 14}" y="32" font-style="italic">y</text>')

    # Flat zero from ox to ox + 50
    c.append(line(ox, oy, ox + 50, oy, stroke=GREEN, width=2.8))
    # Linear ascent from (ox + 50, oy) to (ox + 100, 55)
    c.append(line(ox + 50, oy, ox + 100, 55, stroke=GREEN, width=2.4))
    # Dashed drop
    c.append(line(ox + 100, 55, ox + 100, oy, stroke=MUTED, width=1.2, dash="3,3"))

    c.append(pt_labeled(ox + 50, oy, "1/2", dy=18, r=3.2))
    c.append(pt_labeled(ox + 100, oy, "1", dy=18, r=3.2))
    c.append(point(ox + 100, 55, r=3.6, fill=GREEN))
    c.append(f'    <text x="{ox + 72}" y="75" font-style="italic" font-size="16" fill="{GREEN}">f</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_10() -> str:
    """Fig 10: Quaternion multiplication cycle i -> j -> k -> i."""
    w, h = 240, 220
    cx, cy, r = 120, 110, 65
    c = []
    # 3 circular arcs with arrows
    # i at top (angle -pi/2), j at right-bottom (pi/6), k at left-bottom (5pi/6)
    angles = [-math.pi / 2, math.pi / 6, 5 * math.pi / 6]
    labels = ["i", "j", "k"]

    for i in range(3):
        a_start = angles[i] + 0.35
        a_end = angles[(i + 1) % 3] - 0.35
        x1 = cx + r * math.cos(a_start)
        y1 = cy + r * math.sin(a_start)
        x2 = cx + r * math.cos(a_end)
        y2 = cy + r * math.sin(a_end)
        c.append(f'    <path d="M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}" fill="none" stroke="{BLUE}" stroke-width="2.0" marker-end="url(#arr-blue)" />')

    for i, lbl in enumerate(labels):
        x = cx + r * math.cos(angles[i])
        y = cy + r * math.sin(angles[i])
        c.append(f'    <text x="{x:.1f}" y="{y + 6:.1f}" text-anchor="middle" font-style="italic" font-size="20" font-weight="bold" fill="{INK}">{lbl}</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_11() -> str:
    """Fig 11: Desargues' Theorem (Perspective triangles)."""
    w, h = 380, 240
    c = []
    # Perspective center O
    ox, oy = 75, 40

    # Triangle ABC
    a = (145, 115)
    b = (195, 195)
    c_pt = (235, 130)

    # Triangle A'B'C'
    ap = (155, 75)
    bp = (195, 105)
    cp = (215, 70)

    # Rays from O extending through pairs
    for p, pp, extend in [(a, ap, 1.4), (b, bp, 1.3), (c_pt, cp, 1.3)]:
        dx = p[0] - ox
        dy = p[1] - oy
        c.append(line(ox, oy, ox + dx * extend, oy + dy * extend, stroke=SLATE, width=1.1))

    # Outer triangle ABC
    c.append(f'    <polygon points="{a[0]},{a[1]} {b[0]},{b[1]} {c_pt[0]},{c_pt[1]}" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" />')
    # Inner triangle A'B'C'
    c.append(f'    <polygon points="{ap[0]},{ap[1]} {bp[0]},{bp[1]} {cp[0]},{cp[1]}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.0" />')

    # Desargues dashed line
    c.append(line(ap[0], ap[1], cp[0] + 30, cp[1] - 8, stroke=RED, width=1.3, dash="4,3"))

    c.append(pt_labeled(ox, oy, "O", dx=-12, dy=-4, r=4.0))
    c.append(pt_labeled(a[0], a[1], "A", dx=-16, dy=4))
    c.append(pt_labeled(b[0], b[1], "B", dx=6, dy=12))
    c.append(pt_labeled(c_pt[0], c_pt[1], "C", dx=8, dy=4))
    c.append(pt_labeled(ap[0], ap[1], "A'", dx=-16, dy=-4))
    c.append(pt_labeled(bp[0], bp[1], "B'", dx=-16, dy=12))
    c.append(pt_labeled(cp[0], cp[1], "C'", dx=8, dy=-4))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_12() -> str:
    """Fig 12: Pappus' Theorem on two lines."""
    w, h = 380, 180
    c = []
    # Two lines l1 and l2 intersecting at left
    c.append(line(40, 115, 350, 65, stroke=SLATE, width=1.4))
    c.append(line(40, 125, 340, 180, stroke=SLATE, width=1.4))

    # Points on line 1: P_1, P_5, P_3
    p1 = (135, 100)
    p5 = (200, 89)
    p3 = (295, 74)

    # Points on line 2: P_4, P_2, P_6
    p4 = (110, 137)
    p2 = (185, 151)
    p6 = (265, 166)

    # Cross connections
    c.append(line(p1[0], p1[1], p2[0], p2[1], stroke=BLUE, width=1.5))
    c.append(line(p5[0], p5[1], p4[0], p4[1], stroke=BLUE, width=1.5))

    c.append(line(p5[0], p5[1], p6[0], p6[1], stroke=GREEN, width=1.5))
    c.append(line(p3[0], p3[1], p2[0], p2[1], stroke=GREEN, width=1.5))

    c.append(line(p1[0], p1[1], p6[0], p6[1], stroke=AMBER, width=1.5))
    c.append(line(p3[0], p3[1], p4[0], p4[1], stroke=AMBER, width=1.5))

    # Collinear intersection line (dashed)
    c.append(line(80, 102, 280, 130, stroke=RED, width=1.6, dash="5,4"))

    c.append(pt_labeled(p1[0], p1[1], "P₁", dy=-8))
    c.append(pt_labeled(p5[0], p5[1], "P₅", dy=-8))
    c.append(pt_labeled(p3[0], p3[1], "P₃", dy=-8))
    c.append(pt_labeled(p4[0], p4[1], "P₄", dy=18))
    c.append(pt_labeled(p2[0], p2[1], "P₂", dy=18))
    c.append(pt_labeled(p6[0], p6[1], "P₆", dy=18))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_13() -> str:
    """Fig 13: Complete quadrilateral (harmonic conjugate configuration)."""
    w, h = 320, 180
    c = []
    a = (65, 135)
    b = (145, 135)
    d = (120, 60)
    c_pt = (175, 85)

    # Triangle ABD
    c.append(f'    <polygon points="{a[0]},{a[1]} {b[0]},{b[1]} {d[0]},{d[1]}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="1.8" />')
    # Extended lines
    c.append(line(a[0], a[1], 265, 135, stroke=SLATE, width=1.4))
    c.append(line(d[0], d[1], 210, 105, stroke=SLATE, width=1.4))
    c.append(line(b[0], b[1], 185, 65, stroke=SLATE, width=1.4))

    # Diagonal lines and intersections
    c.append(line(a[0], a[1], c_pt[0], c_pt[1], stroke=BLUE, width=1.4))
    c.append(line(d[0], d[1], b[0], b[1], stroke=BLUE, width=1.4))

    # Points
    c.append(pt_labeled(a[0], a[1], "A", dx=-14, dy=12))
    c.append(pt_labeled(b[0], b[1], "B", dy=18))
    c.append(pt_labeled(c_pt[0], c_pt[1], "C", dx=6, dy=-6))
    c.append(pt_labeled(d[0], d[1], "D", dx=-8, dy=-8, fill=BLUE))
    c.append(point(240, 135, r=4.2, fill="#ffffff", stroke=INK, stroke_width=1.6))
    c.append(point(130, 93, r=4.2, fill="#ffffff", stroke=INK, stroke_width=1.6))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_14() -> str:
    """Fig 14: Branched real algebraic curve with branch points."""
    w, h = 380, 180
    ox, oy = 190, 95
    c = []
    # Real axis x and vertical axis y
    c.append(arrow(35, oy, 355, oy, width=1.6))
    c.append(arrow(ox, 160, ox, 25, width=1.4))
    c.append(f'    <text x="350" y="{oy + 18}" font-style="italic">x</text>')
    c.append(f'    <text x="{ox - 14}" y="28" font-style="italic">y</text>')
    c.append(f'    <text x="{ox - 12}" y="{oy - 6}" font-size="13">0</text>')

    # Left oval between -2 and -1
    x1, x2 = 90, 140
    cx_l = (x1 + x2) / 2
    r_l = (x2 - x1) / 2
    c.append(f'    <ellipse cx="{cx_l}" cy="{oy}" rx="{r_l}" ry="24" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" />')
    c.append(pt_labeled(x1, oy, "x₁", dx=-12, dy=-8, fill=RED))
    c.append(f'    <text x="{x1 - 4}" y="{oy + 18}" font-size="12">-2</text>')
    c.append(pt_labeled(x2, oy, "x₂", dx=6, dy=-8, fill=RED))
    c.append(f'    <text x="{x2 - 4}" y="{oy + 18}" font-size="12">-1</text>')
    c.append(f'    <text x="{cx_l}" y="{oy - 28}" text-anchor="middle" font-size="14" fill="{BLUE}">+</text>')
    c.append(f'    <text x="{cx_l}" y="{oy + 34}" text-anchor="middle" font-size="14" fill="{BLUE}">−</text>')

    # Right oval between 1 and 2
    x3, x4 = 240, 290
    cx_r = (x3 + x4) / 2
    r_r = (x4 - x3) / 2
    c.append(f'    <ellipse cx="{cx_r}" cy="{oy}" rx="{r_r}" ry="24" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.0" />')
    c.append(pt_labeled(x3, oy, "x₃", dx=-14, dy=-8, fill=RED))
    c.append(f'    <text x="{x3 - 2}" y="{oy + 18}" font-size="12">1</text>')
    c.append(pt_labeled(x4, oy, "x₄", dx=6, dy=-8, fill=RED))
    c.append(f'    <text x="{x4 - 2}" y="{oy + 18}" font-size="12">2</text>')
    c.append(f'    <text x="{cx_r}" y="{oy - 28}" text-anchor="middle" font-size="14" fill="{AMBER}">+</text>')
    c.append(f'    <text x="{cx_r}" y="{oy + 34}" text-anchor="middle" font-size="14" fill="{AMBER}">−</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_15() -> str:
    """Fig 15: Triangle symmetry classification: (a) Scalene, (b) Isosceles, (c) Equilateral."""
    w, h = 420, 180
    c = []
    # (a) Scalene triangle
    c.append(f'    <polygon points="50,135 70,60 160,35" fill="none" stroke="{INK}" stroke-width="2.0" stroke-linejoin="round" />')
    c.append(f'    <text x="105" y="160" text-anchor="middle" font-size="14">(a)</text>')

    # (b) Isosceles triangle
    ix_l, ix_r, iy_b, iy_t = 190, 245, 135, 45
    c.append(f'    <polygon points="{ix_l},{iy_b} {(ix_l+ix_r)/2},{iy_t} {ix_r},{iy_b}" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" stroke-linejoin="round" />')
    # Equal side ticks
    c.append(line(204, 88, 212, 92, stroke=BLUE, width=1.6))
    c.append(line(223, 88, 231, 92, stroke=BLUE, width=1.6))
    c.append(f'    <text x="{(ix_l+ix_r)/2}" y="160" text-anchor="middle" font-size="14">(b)</text>')

    # (c) Equilateral triangle
    ex_l, ex_r, ey_b, ey_t = 275, 355, 135, 65
    c.append(f'    <polygon points="{ex_l},{ey_b} {(ex_l+ex_r)/2},{ey_t} {ex_r},{ey_b}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.0" stroke-linejoin="round" />')
    # 3 equal ticks
    c.append(line(292, 98, 298, 104, stroke=AMBER, width=1.6))
    c.append(line(332, 98, 338, 104, stroke=AMBER, width=1.6))
    c.append(line(315, 130, 315, 140, stroke=AMBER, width=1.6))
    c.append(f'    <text x="{(ex_l+ex_r)/2}" y="160" text-anchor="middle" font-size="14">(c)</text>')

    return svg_wrap(w, h, "\n".join(c))
