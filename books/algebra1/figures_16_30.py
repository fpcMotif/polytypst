"""3Blue1Brown-styled figure generators for Algebra I: Figures 16 to 30.

Mathematically authentic reconstructions from the source scan.
"""

import math
from .figures_common import (
    AMBER,
    AMBER_BG,
    BLUE,
    BLUE_BG,
    GREEN,
    GREEN_BG,
    INK,
    PURPLE,
    PURPLE_BG,
    RED,
    SLATE,
    arrow,
    line,
    point,
    resolve_scan_pdf,
    scan_crop_svg,
    svg_wrap,
)

SCAN_PDF = resolve_scan_pdf()


def gen_fig_16() -> str:
    """Fig 16: 2D wallpaper pattern of comma/leaf motifs showing translations and glide reflections."""
    w, h = 380, 220
    c = []
    # 4 columns x 4 rows
    cols = [70, 140, 210, 280]
    rows = [40, 80, 120, 160]

    def draw_motif(x: float, y: float, flipped: bool) -> str:
        s = 1.0 if not flipped else -1.0
        # Teardrop / comma leaf shape
        p1 = (x, y)
        p2 = (x + s * 14, y - 18)
        p3 = (x + s * 8, y - 26)
        col = BLUE if not flipped else AMBER
        bg = BLUE_BG if not flipped else AMBER_BG
        return (
            f'    <path d="M {p1[0]:.1f} {p1[1]:.1f} '
            f'C {p1[0] + s*4:.1f} {p1[1] - 10:.1f} {p2[0]:.1f} {p2[1]:.1f} {p3[0]:.1f} {p3[1]:.1f} '
            f'C {p3[0] - s*10:.1f} {p3[1] + 6:.1f} {p1[0] - s*4:.1f} {p1[1] - 8:.1f} {p1[0]:.1f} {p1[1]:.1f} Z" '
            f'fill="{bg}" stroke="{col}" stroke-width="1.6" />'
        )

    for r_idx, y in enumerate(rows):
        is_flipped = (r_idx % 2 == 1)
        for x in cols:
            c.append(draw_motif(x, y, is_flipped))

    # Base axes OA and OB
    c.append(arrow(70, 160, 140, 160, stroke=BLUE, width=1.6))
    c.append(arrow(70, 160, 70, 120, stroke=GREEN, width=1.6))
    c.append(f'    <text x="65" y="178" font-style="italic" font-size="14">O</text>')
    c.append(f'    <text x="135" y="178" font-style="italic" font-size="14">A</text>')
    c.append(f'    <text x="52" y="125" font-style="italic" font-size="14">B</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_17() -> str:
    """Fig 17: NaCl 3D cubic crystal lattice with alternating Na and Cl ions."""
    w, h = 340, 220
    ox, oy = 75, 145
    # Oblique projection vectors
    vx = (60.0, 0.0)
    vy = (-28.0, 22.0)
    vz = (0.0, -50.0)

    def p3d(ix: int, iy: int, iz: int) -> tuple[float, float]:
        return (
            ox + ix * vx[0] + iy * vy[0] + iz * vz[0],
            oy + ix * vx[1] + iy * vy[1] + iz * vz[1],
        )

    c = []
    # 4 columns (x in 0..3), 2 rows in depth (y in 0..1), 3 vertical levels (z in 0..2)
    # Background dashed lines
    for ix in range(4):
        for iz in range(3):
            p1 = p3d(ix, 1, iz)
            p2 = p3d(ix, 0, iz)
            c.append(line(p1[0], p1[1], p2[0], p2[1], stroke=SLATE, width=1.0, dash="3,3"))

    # Horizontal and vertical grid lines
    for iy in range(2):
        for iz in range(3):
            for ix in range(3):
                p1 = p3d(ix, iy, iz)
                p2 = p3d(ix + 1, iy, iz)
                c.append(line(p1[0], p1[1], p2[0], p2[1], stroke=SLATE, width=1.1))
        for ix in range(4):
            for iz in range(2):
                p1 = p3d(ix, iy, iz)
                p2 = p3d(ix, iy, iz + 1)
                c.append(line(p1[0], p1[1], p2[0], p2[1], stroke=SLATE, width=1.1))

    # Alternating ions: Na (filled black, r=4.2), Cl (open blue circle, r=4.5)
    for iz in range(3):
        for iy in range(2):
            for ix in range(4):
                px, py = p3d(ix, iy, iz)
                is_na = (ix + iy + iz) % 2 == 0
                if is_na:
                    c.append(f'    <circle cx="{px:.1f}" cy="{py:.1f}" r="4.2" fill="{INK}" stroke="#ffffff" stroke-width="1.0" />')
                else:
                    c.append(f'    <circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#ffffff" stroke="{BLUE}" stroke-width="1.8" />')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_18() -> str:
    """Fig 18: Oriented regular 7-gon (heptagon) with directed edges."""
    w, h = 260, 240
    cx, cy, r = 130, 115, 75
    c = []
    n = 7
    pts = []
    for i in range(n):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))

    # Directed polygon edges
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        c.append(arrow(p1[0], p1[1], p2[0], p2[1], stroke=BLUE, width=2.0))
        c.append(f'    <circle cx="{p1[0]:.1f}" cy="{p1[1]:.1f}" r="3.6" fill="{INK}" />')

    c.append(f'    <text x="{cx}" y="{cy + 6}" text-anchor="middle" font-style="italic" font-size="16" fill="{SLATE}">D_7</text>')
    return svg_wrap(w, h, "\n".join(c))


def gen_fig_19() -> str:
    """Fig 19: Dual Platonic solids: Tetrahedron, Octahedron, Icosahedron."""
    w, h = 420, 180
    c = []

    # 1. Tetrahedron
    tx, ty = 75, 95
    t_top = (tx, ty - 55)
    t_left = (tx - 45, ty + 40)
    t_right = (tx + 45, ty + 25)
    t_back = (tx - 5, ty + 35)

    c.append(f'    <polygon points="{t_top[0]},{t_top[1]} {t_left[0]},{t_left[1]} {t_right[0]},{t_right[1]}" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" stroke-linejoin="round" />')
    c.append(line(t_top[0], t_top[1], t_back[0], t_back[1], stroke=SLATE, width=1.4, dash="3,3"))
    c.append(line(t_left[0], t_left[1], t_back[0], t_back[1], stroke=SLATE, width=1.4, dash="3,3"))
    c.append(line(t_right[0], t_right[1], t_back[0], t_back[1], stroke=SLATE, width=1.4, dash="3,3"))
    c.append(f'    <text x="{tx}" y="160" text-anchor="middle" font-size="14">Tetrahedron</text>')

    # 2. Octahedron
    ox, oy = 205, 95
    o_top = (ox, oy - 60)
    o_bot = (ox, oy + 60)
    o_l = (ox - 45, oy)
    o_r = (ox + 45, oy)
    o_fl = (ox - 15, oy + 25)
    o_fr = (ox + 15, oy - 25)

    # Front faces
    c.append(f'    <polygon points="{o_top[0]},{o_top[1]} {o_l[0]},{o_l[1]} {o_fl[0]},{o_fl[1]}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.8" />')
    c.append(f'    <polygon points="{o_top[0]},{o_top[1]} {o_r[0]},{o_r[1]} {o_fl[0]},{o_fl[1]}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.8" />')
    c.append(f'    <polygon points="{o_bot[0]},{o_bot[1]} {o_l[0]},{o_l[1]} {o_fl[0]},{o_fl[1]}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.8" />')
    c.append(f'    <polygon points="{o_bot[0]},{o_bot[1]} {o_r[0]},{o_r[1]} {o_fl[0]},{o_fl[1]}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.8" />')
    # Back hidden edges
    c.append(line(o_top[0], o_top[1], o_fr[0], o_fr[1], stroke=SLATE, width=1.2, dash="3,3"))
    c.append(line(o_bot[0], o_bot[1], o_fr[0], o_fr[1], stroke=SLATE, width=1.2, dash="3,3"))
    c.append(line(o_l[0], o_l[1], o_fr[0], o_fr[1], stroke=SLATE, width=1.2, dash="3,3"))
    c.append(line(o_r[0], o_r[1], o_fr[0], o_fr[1], stroke=SLATE, width=1.2, dash="3,3"))
    c.append(f'    <text x="{ox}" y="160" text-anchor="middle" font-size="14">Octahedron</text>')

    # 3. Icosahedron
    ix, iy = 335, 95
    ir = 55
    ico = []
    for i in range(6):
        a = i * math.pi / 3 - math.pi / 6
        ico.append((ix + ir * math.cos(a), iy + ir * math.sin(a)))
    # Outer hexagon
    c.append(f'    <polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in ico)}" fill="{GREEN_BG}" stroke="{GREEN}" stroke-width="1.8" />')
    # Inner triangles
    v_top = (ix, iy - 28)
    v_bot = (ix, iy + 28)
    c.append(line(v_top[0], v_top[1], ico[0][0], ico[0][1], stroke=GREEN, width=1.4))
    c.append(line(v_top[0], v_top[1], ico[1][0], ico[1][1], stroke=GREEN, width=1.4))
    c.append(line(v_top[0], v_top[1], ico[2][0], ico[2][1], stroke=GREEN, width=1.4))
    c.append(line(v_bot[0], v_bot[1], ico[3][0], ico[3][1], stroke=GREEN, width=1.4))
    c.append(line(v_bot[0], v_bot[1], ico[4][0], ico[4][1], stroke=GREEN, width=1.4))
    c.append(line(v_bot[0], v_bot[1], ico[5][0], ico[5][1], stroke=GREEN, width=1.4))
    c.append(line(v_top[0], v_top[1], v_bot[0], v_bot[1], stroke=SLATE, width=1.2, dash="3,3"))
    c.append(f'    <text x="{ix}" y="160" text-anchor="middle" font-size="14">Icosahedron</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_20() -> str:
    """Fig 20: 5 rotation axes of D_5 on regular pentagon."""
    w, h = 260, 230
    cx, cy, r = 130, 110, 68
    c = []
    pts = []
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    c.append(f'    <polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.2" />')

    # 5 rotation axes through vertices and opposite midpoints
    for i in range(5):
        vx, vy = pts[i]
        opp_x = (pts[(i + 2) % 5][0] + pts[(i + 3) % 5][0]) / 2
        opp_y = (pts[(i + 2) % 5][1] + pts[(i + 3) % 5][1]) / 2
        dx, dy = opp_x - vx, opp_y - vy
        c.append(line(vx - dx * 0.25, vy - dy * 0.25, opp_x + dx * 0.3, opp_y + dy * 0.3, stroke=RED, width=1.5, dash="6,3,2,3"))

    for px, py in pts:
        c.append(point(px, py, r=3.8, fill=INK))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_21() -> str:
    """Fig 21: Octahedron inscribed in a regular tetrahedron."""
    w, h = 280, 240
    c = []
    # Regular tetrahedron vertices
    top = (140, 25)
    left = (45, 185)
    right = (235, 185)
    front = (140, 215)

    # Outer tetrahedron frame
    c.append(f'    <polygon points="{top[0]},{top[1]} {left[0]},{left[1]} {front[0]},{front[1]}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="1.8" />')
    c.append(f'    <polygon points="{top[0]},{top[1]} {right[0]},{right[1]} {front[0]},{front[1]}" fill="{AMBER_BG}" stroke="{INK}" stroke-width="1.8" />')
    c.append(line(left[0], left[1], right[0], right[1], stroke=SLATE, width=1.2, dash="4,3"))

    # Midpoints of 6 edges (vertices of inscribed octahedron)
    m1 = ((top[0] + left[0]) / 2, (top[1] + left[1]) / 2)
    m2 = ((top[0] + right[0]) / 2, (top[1] + right[1]) / 2)
    m3 = ((top[0] + front[0]) / 2, (top[1] + front[1]) / 2)
    m4 = ((left[0] + front[0]) / 2, (left[1] + front[1]) / 2)
    m5 = ((right[0] + front[0]) / 2, (right[1] + front[1]) / 2)
    m6 = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)

    # Inscribed octahedron edges
    octa_edges = [(m1, m2), (m2, m3), (m3, m1), (m4, m5), (m3, m4), (m3, m5), (m1, m4), (m2, m5)]
    for p1, p2 in octa_edges:
        c.append(line(p1[0], p1[1], p2[0], p2[1], stroke=RED, width=2.0))
    for p1, p2 in [(m1, m6), (m2, m6), (m4, m6), (m5, m6)]:
        c.append(line(p1[0], p1[1], p2[0], p2[1], stroke=RED, width=1.4, dash="3,3"))

    for p in [m1, m2, m3, m4, m5, m6]:
        c.append(point(p[0], p[1], r=4.2, fill=RED))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_22() -> str:
    """Fig 22: Molecular symmetry: H3C-CCl3, C2H6, CH4, UF6."""
    w, h = 420, 220
    c = []

    # 1. H3C-CCl3 (C_3)
    x1 = 60
    c.append(f'    <ellipse cx="{x1}" cy="50" rx="30" ry="12" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.6" />')
    c.append(line(x1 - 30, 50, x1, 80, stroke=BLUE, width=1.6))
    c.append(line(x1 + 30, 50, x1, 80, stroke=BLUE, width=1.6))
    c.append(line(x1, 80, x1, 110, stroke=INK, width=2.4))
    c.append(f'    <ellipse cx="{x1}" cy="140" rx="30" ry="12" fill="{GREEN_BG}" stroke="{GREEN}" stroke-width="1.6" />')
    c.append(line(x1 - 30, 140, x1, 110, stroke=GREEN, width=1.6))
    c.append(line(x1 + 30, 140, x1, 110, stroke=GREEN, width=1.6))
    c.append(f'    <text x="{x1}" y="180" text-anchor="middle" font-size="12">H₃C–CCl₃</text>')

    # 2. C2H6 (D_3)
    x2 = 160
    c.append(f'    <ellipse cx="{x2}" cy="50" rx="30" ry="12" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.6" />')
    c.append(line(x2 - 30, 50, x2, 80, stroke=BLUE, width=1.6))
    c.append(line(x2 + 30, 50, x2, 80, stroke=BLUE, width=1.6))
    c.append(line(x2, 80, x2, 110, stroke=INK, width=2.4))
    c.append(f'    <ellipse cx="{x2}" cy="140" rx="30" ry="12" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.6" />')
    c.append(line(x2 - 30, 140, x2, 110, stroke=BLUE, width=1.6))
    c.append(line(x2 + 30, 140, x2, 110, stroke=BLUE, width=1.6))
    c.append(f'    <text x="{x2}" y="180" text-anchor="middle" font-size="12">C₂H₆</text>')

    # 3. CH4 (T)
    x3 = 265
    top3, bot3, l3, r3 = (x3, 55), (x3, 140), (x3 - 35, 110), (x3 + 35, 95)
    c.append(f'    <polygon points="{top3[0]},{top3[1]} {l3[0]},{l3[1]} {bot3[0]},{bot3[1]}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.6" />')
    c.append(f'    <polygon points="{top3[0]},{top3[1]} {r3[0]},{r3[1]} {bot3[0]},{bot3[1]}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.6" />')
    c.append(line(l3[0], l3[1], r3[0], r3[1], stroke=SLATE, width=1.1, dash="3,3"))
    c.append(point((top3[0] + bot3[0]) / 2, (top3[1] + bot3[1]) / 2, r=4.0, fill=INK))
    c.append(f'    <text x="{x3}" y="180" text-anchor="middle" font-size="12">CH₄</text>')

    # 4. UF6 (O)
    x4 = 365
    top4, bot4 = (x4, 45), (x4, 150)
    l4, r4 = (x4 - 38, 98), (x4 + 38, 98)
    fl4, fr4 = (x4 - 15, 115), (x4 + 15, 80)
    c.append(line(top4[0], top4[1], l4[0], l4[1], stroke=PURPLE, width=1.6))
    c.append(line(top4[0], top4[1], r4[0], r4[1], stroke=PURPLE, width=1.6))
    c.append(line(top4[0], top4[1], fl4[0], fl4[1], stroke=PURPLE, width=1.6))
    c.append(line(bot4[0], bot4[1], l4[0], l4[1], stroke=PURPLE, width=1.6))
    c.append(line(bot4[0], bot4[1], r4[0], r4[1], stroke=PURPLE, width=1.6))
    c.append(line(bot4[0], bot4[1], fl4[0], fl4[1], stroke=PURPLE, width=1.6))
    c.append(line(l4[0], l4[1], fl4[0], fl4[1], stroke=PURPLE, width=1.6))
    c.append(line(fl4[0], fl4[1], r4[0], r4[1], stroke=PURPLE, width=1.6))
    c.append(point(x4, 98, r=4.2, fill=INK))
    c.append(f'    <text x="{x4}" y="180" text-anchor="middle" font-size="12">UF₆</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_23() -> str:
    """Fig 23: The 5 2D Bravais lattice cells."""
    w, h = 420, 160
    c = []
    # 1. General (C_1, C_2)
    c.append(f'    <polygon points="30,105 75,105 95,65 50,65" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.8" />')
    c.append(f'    <text x="62" y="125" text-anchor="middle" font-size="11">general</text>')
    c.append(f'    <text x="62" y="142" text-anchor="middle" font-size="11" fill="{SLATE}">C₁, C₂</text>')

    # 2. Rectangular (C_1, C_2, D_1, D_2)
    c.append(f'    <rect x="120" y="65" width="55" height="40" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.8" />')
    c.append(f'    <text x="147" y="125" text-anchor="middle" font-size="11">rectangular</text>')
    c.append(f'    <text x="147" y="142" text-anchor="middle" font-size="11" fill="{SLATE}">C₁, D₂</text>')

    # 3. Rhombic (C_1, C_2, D_1, D_2)
    c.append(f'    <polygon points="205,85 240,60 275,85 240,110" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="1.8" />')
    c.append(line(205, 85, 275, 85, stroke=AMBER, width=1.2, dash="3,3"))
    c.append(f'    <text x="240" y="125" text-anchor="middle" font-size="11">rhombic</text>')
    c.append(f'    <text x="240" y="142" text-anchor="middle" font-size="11" fill="{SLATE}">D₁, D₂</text>')

    # 4. Square (C_1, C_2, C_4, D_1, D_2, D_4)
    c.append(f'    <rect x="300" y="65" width="40" height="40" fill="{GREEN_BG}" stroke="{GREEN}" stroke-width="1.8" />')
    c.append(f'    <text x="320" y="125" text-anchor="middle" font-size="11">square</text>')
    c.append(f'    <text x="320" y="142" text-anchor="middle" font-size="11" fill="{SLATE}">D₄</text>')

    # 5. Hexagonal
    c.append(f'    <polygon points="365,105 400,105 418,65 383,65" fill="{PURPLE_BG}" stroke="{PURPLE}" stroke-width="1.8" />')
    c.append(line(365, 105, 418, 65, stroke=PURPLE, width=1.4))
    c.append(f'    <text x="392" y="125" text-anchor="middle" font-size="11">hexagonal</text>')
    c.append(f'    <text x="392" y="142" text-anchor="middle" font-size="11" fill="{SLATE}">D₆</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_24() -> str:
    """Fig 24: Inscribed triangles in regular hexagon preserved by D_6."""
    w, h = 340, 180
    c = []
    # Left hexagon: vertex-inscribed triangle
    cx1, cy1, r = 90, 85, 55
    pts1 = [(cx1 + r * math.cos(i * math.pi / 3), cy1 + r * math.sin(i * math.pi / 3)) for i in range(6)]
    c.append(f'    <polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts1)}" fill="none" stroke="{INK}" stroke-width="1.8" />')
    tri1 = f"{pts1[0][0]:.1f},{pts1[0][1]:.1f} {pts1[2][0]:.1f},{pts1[2][1]:.1f} {pts1[4][0]:.1f},{pts1[4][1]:.1f}"
    c.append(f'    <polygon points="{tri1}" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" />')

    # Right hexagon: edge-midpoint inscribed triangle
    cx2, cy2 = 250, 85
    pts2 = [(cx2 + r * math.cos(i * math.pi / 3), cy2 + r * math.sin(i * math.pi / 3)) for i in range(6)]
    c.append(f'    <polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts2)}" fill="none" stroke="{INK}" stroke-width="1.8" />')
    m_pts = [((pts2[i][0] + pts2[(i + 1) % 6][0]) / 2, (pts2[i][1] + pts2[(i + 1) % 6][1]) / 2) for i in range(6)]
    tri2 = f"{m_pts[0][0]:.1f},{m_pts[0][1]:.1f} {m_pts[2][0]:.1f},{m_pts[2][1]:.1f} {m_pts[4][0]:.1f},{m_pts[4][1]:.1f}"
    c.append(f'    <polygon points="{tri2}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.0" />')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_25() -> str:
    """Fig 25: Hexagonal prism and cubic 3D lattice cells."""
    w, h = 340, 180
    c = []
    # Left: Rhombic prism with base of 2 equilateral triangles
    px, py = 80, 130
    c.append(f'    <polygon points="{px},{py} {px+40},{py} {px+60},{py-45} {px+20},{py-45}" fill="{AMBER_BG}" stroke="{INK}" stroke-width="1.8" />')
    c.append(line(px, py, px + 60, py - 45, stroke=SLATE, width=1.2, dash="3,3"))
    # Top face
    c.append(f'    <polygon points="{px},{py-50} {px+40},{py-50} {px+60},{py-95} {px+20},{py-95}" fill="{AMBER_BG}" stroke="{INK}" stroke-width="1.8" />')
    for dx, dy in [(0, 0), (40, 0), (60, -45), (20, -45)]:
        c.append(line(px + dx, py + dy, px + dx, py + dy - 50, stroke=INK, width=1.6))
    c.append(f'    <text x="{px + 30}" y="{py + 25}" text-anchor="middle" font-size="12">Hexagonal</text>')

    # Right: Cube
    cx, cy = 230, 130
    c.append(f'    <rect x="{cx}" y="{cy-45}" width="45" height="45" fill="{BLUE_BG}" stroke="{INK}" stroke-width="1.8" />')
    c.append(f'    <polygon points="{cx},{cy-45} {cx+20},{cy-65} {cx+65},{cy-65} {cx+45},{cy-45}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="1.8" />')
    c.append(f'    <polygon points="{cx+45},{cy-45} {cx+65},{cy-65} {cx+65},{cy-20} {cx+45},{cy}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="1.8" />')
    c.append(line(cx, cy, cx + 20, cy - 20, stroke=SLATE, width=1.2, dash="3,3"))
    c.append(line(cx + 20, cy - 20, cx + 65, cy - 20, stroke=SLATE, width=1.2, dash="3,3"))
    c.append(line(cx + 20, cy - 20, cx + 20, cy - 65, stroke=SLATE, width=1.2, dash="3,3"))
    c.append(f'    <text x="{cx + 32}" y="{cy + 25}" text-anchor="middle" font-size="12">Cubical (cube)</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_26() -> str:
    """Fig 26: 32 Crystal Classes symmetry table (clean 400 DPI crop from scan)."""
    return scan_crop_svg(SCAN_PDF, 122, (0.12, 0.08, 0.88, 0.88), dpi=200)


def gen_fig_27() -> str:
    """Fig 27: 2D array of flower-sprouts with reflection axis OB."""
    w, h = 380, 180
    c = []
    # Baseline OA and vertical reflection line OB
    c.append(line(30, 140, 350, 140, stroke=INK, width=2.0))
    c.append(line(190, 140, 190, 30, stroke=BLUE, width=2.0))
    c.append(f'    <text x="190" y="156" text-anchor="middle" font-style="italic">0</text>')
    c.append(f'    <text x="198" y="95" font-style="italic">B</text>')
    c.append(f'    <text x="250" y="156" text-anchor="middle" font-style="italic">A</text>')

    # 4 rows x 5 columns of bilateral sprout motifs
    xs = [70, 130, 190, 250, 310]
    ys = [50, 80, 110, 140]
    for y in ys:
        for x in xs:
            # 2 curved petals
            c.append(f'    <path d="M {x} {y} Q {x-14} {y-14} {x-10} {y-22} Q {x-2} {y-18} {x} {y}" fill="{GREEN_BG}" stroke="{GREEN}" stroke-width="1.3" />')
            c.append(f'    <path d="M {x} {y} Q {x+14} {y-14} {x+10} {y-22} Q {x+2} {y-18} {x} {y}" fill="{GREEN_BG}" stroke="{GREEN}" stroke-width="1.3" />')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_28() -> str:
    """Fig 28: 2D array of 4-petal propellers with reflection axis l."""
    w, h = 320, 180
    c = []
    # Axis l
    c.append(line(30, 130, 290, 130, stroke=SLATE, width=1.5))
    c.append(f'    <text x="45" y="125" font-style="italic">l</text>')

    xs = [100, 160, 220]
    ys = [50, 90, 130]

    for y in ys:
        for x in xs:
            # 4-petal propeller
            c.append(f'    <ellipse cx="{x}" cy="{y-9}" rx="4" ry="9" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.2" />')
            c.append(f'    <ellipse cx="{x}" cy="{y+9}" rx="4" ry="9" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.2" />')
            c.append(f'    <ellipse cx="{x-9}" cy="{y}" rx="9" ry="4" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.2" />')
            c.append(f'    <ellipse cx="{x+9}" cy="{y}" rx="9" ry="4" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="1.2" />')
            c.append(point(x, y, r=2.5, fill=INK))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_29() -> str:
    """Fig 29: Ornamental wallpaper art (clean 400 DPI crop from scan)."""
    return scan_crop_svg(SCAN_PDF, 131, (0.18, 0.28, 0.82, 0.56), dpi=200)


def gen_fig_30() -> str:
    """Fig 30: 3 biological symmetry photos: Campanula, Stapelia, Baobab (clean 400 DPI crop)."""
    return scan_crop_svg(SCAN_PDF, 132, (0.15, 0.28, 0.85, 0.77), dpi=200)
