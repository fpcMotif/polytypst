"""3Blue1Brown-styled figure generators for Algebra I: Figures 31 to 45.

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
    PURPLE,
    PURPLE_BG,
    RED,
    SLATE,
    arrow,
    line,
    point,
    pt_labeled,
    resolve_scan_pdf,
    scan_crop_svg,
    svg_wrap,
)

SCAN_PDF = resolve_scan_pdf()


def gen_fig_31() -> str:
    """Fig 31: Hyperbolic fundamental octagon with identified side pairs."""
    w, h = 300, 280
    cx, cy, r = 150, 140, 95
    c = []
    pts = []
    # Regular octagon
    for i in range(8):
        a = -math.pi / 2 + i * 2 * math.pi / 8
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    # Outer polygon
    poly_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
    c.append(f'    <path d="{poly_d}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="2.2" />')

    # Direction arrows on edges
    labels = ["a_2", "a_1", "b_1", "a_1'", "b_1'", "a_2'", "b_2'", "b_2"]
    for i in range(8):
        p1 = pts[i]
        p2 = pts[(i + 1) % 8]
        # Midpoint for label
        mx = (p1[0] + p2[0]) / 2 + (p1[0] + p2[0] - 2 * cx) * 0.18
        my = (p1[1] + p2[1]) / 2 + (p1[1] + p2[1] - 2 * cy) * 0.18 + 5
        c.append(f'    <text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" font-style="italic" font-size="14">{labels[i]}</text>')
        # Arrow on side
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        c.append(arrow(p1[0], p1[1], mid_x, mid_y, stroke=BLUE, width=1.6))

    # Internal curved pairing arrows (connecting paired sides across the octagon)
    # Right pair (a1 and a1')
    c.append(f'    <path d="M 185 80 C 170 120 170 160 185 200" fill="none" stroke="{SLATE}" stroke-width="1.6" marker-end="url(#arr)" marker-start="url(#arr-rev)" />')
    c.append(f'    <path d="M 165 95 C 195 130 195 150 165 185" fill="none" stroke="{SLATE}" stroke-width="1.6" marker-end="url(#arr)" marker-start="url(#arr-rev)" />')
    # Left pair (a2 and a2')
    c.append(f'    <path d="M 115 80 C 130 120 130 160 115 200" fill="none" stroke="{SLATE}" stroke-width="1.6" marker-end="url(#arr)" marker-start="url(#arr-rev)" />')
    c.append(f'    <path d="M 135 95 C 105 130 105 150 135 185" fill="none" stroke="{SLATE}" stroke-width="1.6" marker-end="url(#arr)" marker-start="url(#arr-rev)" />')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_32() -> str:
    """Fig 32: Modular group fundamental domain in upper half plane."""
    w, h = 380, 220
    ox, oy = 190, 185
    scale = 85.0
    c = []
    # Real axis
    c.append(line(25, oy, 355, oy, stroke=INK, width=2.0))

    # Semicircles of radius 1 centered at -1, 0, 1
    # 1. Circle at x = 0 (unit circle)
    c.append(f'    <path d="M {ox - scale} {oy} A {scale} {scale} 0 0 1 {ox + scale} {oy}" fill="none" stroke="{INK}" stroke-width="1.8" />')
    # 2. Circle at x = -1
    c.append(f'    <path d="M {ox - 2*scale} {oy} A {scale} {scale} 0 0 1 {ox} {oy}" fill="none" stroke="{SLATE}" stroke-width="1.4" />')
    # 3. Circle at x = +1
    c.append(f'    <path d="M {ox} {oy} A {scale} {scale} 0 0 1 {ox + 2*scale} {oy}" fill="none" stroke="{SLATE}" stroke-width="1.4" />')

    # Shaded fundamental domain D
    x_l = ox - 0.5 * scale
    x_r = ox + 0.5 * scale
    arc_y = oy - math.sqrt(0.75) * scale
    c.append(
        f'    <path d="M {x_l} 35 L {x_l} {arc_y:.1f} '
        f'A {scale} {scale} 0 0 1 {x_r} {arc_y:.1f} '
        f'L {x_r} 35 Z" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" />'
    )
    # Dashed vertical lines
    c.append(line(x_l, oy, x_l, 35, stroke=SLATE, width=1.2, dash="4,3"))
    c.append(line(x_r, oy, x_r, 35, stroke=SLATE, width=1.2, dash="4,3"))

    # Region D and D' labels
    c.append(f'    <text x="{ox}" y="{oy - 105}" text-anchor="middle" font-size="16" font-weight="bold" fill="{BLUE}">D</text>')
    c.append(f'    <text x="{ox}" y="{oy - 50}" text-anchor="middle" font-size="16" font-style="italic" fill="{SLATE}">D\'</text>')

    # Axis tick labels
    c.append(f'    <text x="{ox - scale}" y="{oy + 18}" text-anchor="middle" font-size="13">−1</text>')
    c.append(f'    <text x="{x_l}" y="{oy + 18}" text-anchor="middle" font-size="13">−1/2</text>')
    c.append(f'    <text x="{ox}" y="{oy + 18}" text-anchor="middle" font-size="13">0</text>')
    c.append(f'    <text x="{x_r}" y="{oy + 18}" text-anchor="middle" font-size="13">1/2</text>')
    c.append(f'    <text x="{ox + scale}" y="{oy + 18}" text-anchor="middle" font-size="13">1</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_33() -> str:
    """Fig 33: Cayley graph / regular 4-valent tree of free group F_2 = <x, y>."""
    w, h = 380, 260
    cx, cy = 190, 130
    c = []
    # Origin e
    c.append(point(cx, cy, r=4.2, fill=INK))
    c.append(f'    <text x="{cx + 6}" y="{cy - 8}" font-size="14" font-weight="bold">e</text>')

    # Main horizontal axis (x-direction, single arrow)
    c.append(line(30, cy, 350, cy, stroke=INK, width=1.8))
    # Points along x: x^-2, x^-1, x, x^2
    xs = [
        (cx - 110, "x⁻²", -1),
        (cx - 55, "x⁻¹", -1),
        (cx + 55, "x", 1),
        (cx + 110, "x²", 1),
    ]
    for x, lbl, direction in xs:
        c.append(point(x, cy, r=3.8, fill=BLUE))
        c.append(f'    <text x="{x + 8}" y="{cy - 8}" font-size="13">{lbl}</text>')
        # Arrow on segment
        arr_x = x - direction * 25
        c.append(arrow(arr_x - direction * 5, cy, arr_x + direction * 5, cy, stroke=BLUE, width=1.8))
        # Vertical cross branches at x
        c.append(line(x, cy - 45, x, cy + 45, stroke=SLATE, width=1.4))
        c.append(arrow(x, cy - 10, x, cy - 25, stroke=GREEN, width=1.4))
        c.append(arrow(x, cy + 10, x, cy + 25, stroke=GREEN, width=1.4))

    # Main vertical axis (y-direction, double arrow)
    c.append(line(cx, 30, cx, 230, stroke=INK, width=1.8))
    ys = [
        (cy - 65, "y", -1),
        (cy + 65, "y⁻¹", 1),
    ]
    for y, lbl, direction in ys:
        c.append(point(cx, y, r=3.8, fill=GREEN))
        c.append(f'    <text x="{cx + 8}" y="{y + 4}" font-size="13">{lbl}</text>')
        # Horizontal cross branches at y
        c.append(line(cx - 45, y, cx + 45, y, stroke=SLATE, width=1.4))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_34() -> str:
    """Fig 34: Bouquet of 4 circles (four-leaf clover bouquet)."""
    w, h = 260, 240
    cx, cy, r = 130, 120, 52
    c = []
    # 4 Petals arranged symmetrically at 45, 135, 225, 315 deg
    angles = [math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4]
    for a in angles:
        tip_x = cx + r * 1.5 * math.cos(a)
        tip_y = cy + r * 1.5 * math.sin(a)
        # Left and right control points
        cp1_x = cx + r * 1.2 * math.cos(a - 0.6)
        cp1_y = cy + r * 1.2 * math.sin(a - 0.6)
        cp2_x = cx + r * 1.2 * math.cos(a + 0.6)
        cp2_y = cy + r * 1.2 * math.sin(a + 0.6)
        c.append(
            f'    <path d="M {cx} {cy} C {cp1_x:.1f} {cp1_y:.1f} {tip_x:.1f} {tip_y:.1f} {tip_x:.1f} {tip_y:.1f} '
            f'C {tip_x:.1f} {tip_y:.1f} {cp2_x:.1f} {cp2_y:.1f} {cx} {cy} Z" '
            f'fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" />'
        )

    # Center origin
    c.append(point(cx, cy, r=4.5, fill=INK))
    return svg_wrap(w, h, "\n".join(c))


def gen_fig_35() -> str:
    """Fig 35: Surface of genus p=2 (Sphere with 2 handles)."""
    w, h = 280, 250
    cx, cy, r = 140, 155, 65
    c = []
    # Sphere base
    c.append(f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="2.2" />')

    # Handle 1 (outer)
    c.append('    <path d="M 115 95 C 105 45 155 35 168 85" fill="none" stroke="{BLUE}" stroke-width="2.0" />')
    c.append('    <path d="M 100 105 C 85 30 175 15 185 98" fill="none" stroke="{BLUE}" stroke-width="2.0" />')

    # Handle 2 (lower inner)
    c.append('    <path d="M 105 135 C 95 110 135 105 145 130" fill="none" stroke="{BLUE}" stroke-width="1.8" />')
    c.append('    <path d="M 95 145 C 80 95 150 90 160 140" fill="none" stroke="{BLUE}" stroke-width="1.8" />')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_36() -> str:
    """Fig 36: Trefoil knot with marked arcs A, B, C and loop gamma."""
    w, h = 340, 240
    cx, cy = 135, 125
    c = []
    # Trefoil knot arcs
    # Left loop (C)
    c.append('    <path d="M 130 95 C 80 50 60 110 90 145 C 110 170 145 155 140 120" fill="none" stroke="{BLUE}" stroke-width="2.6" stroke-linecap="round" />')
    # Bottom loop (A)
    c.append('    <path d="M 148 110 C 165 135 150 190 115 185 C 85 180 95 140 120 125" fill="none" stroke="{BLUE}" stroke-width="2.6" stroke-linecap="round" />')
    # Right loop (B)
    c.append('    <path d="M 110 135 C 135 145 185 135 180 100 C 175 75 130 70 115 98" fill="none" stroke="{BLUE}" stroke-width="2.6" stroke-linecap="round" />')

    # Arc labels A, B, C
    c.append(f'    <text x="145" y="165" font-style="italic" font-size="16" fill="{INK}">A</text>')
    c.append(f'    <text x="188" y="95" font-style="italic" font-size="16" fill="{INK}">B</text>')
    c.append(f'    <text x="130" y="70" font-style="italic" font-size="16" fill="{INK}">C</text>')

    # Hook loop gamma around strand B
    c.append('    <ellipse cx="180" cy="105" rx="8" ry="12" fill="none" stroke="{INK}" stroke-width="1.5" />')
    c.append(line(188, 102, 280, 102, stroke=INK, width=1.5))
    c.append(line(188, 108, 280, 108, stroke=INK, width=1.5))
    c.append(f'    <text x="290" y="108" font-style="italic" font-size="16">γ</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_37() -> str:
    """Fig 37: 3-Strand Braid diagrams: (a) basic braid, (b) product, (c) closure."""
    w, h = 420, 200
    c = []
    # (a) Braid with 3 strands
    x1_l = [45, 45, 45]
    x1_r = [145, 145, 145]
    y1 = [55, 85, 115]
    # Vertical bars AB and CD
    c.append(line(45, 35, 45, 135, stroke=INK, width=2.0))
    c.append(line(145, 35, 145, 135, stroke=INK, width=2.0))
    c.append(f'    <text x="45" y="28" text-anchor="middle" font-size="13">B</text>')
    c.append(f'    <text x="45" y="148" text-anchor="middle" font-size="13">A</text>')
    c.append(f'    <text x="145" y="28" text-anchor="middle" font-size="13">C</text>')
    c.append(f'    <text x="145" y="148" text-anchor="middle" font-size="13">D</text>')
    for i in range(3):
        c.append(point(45, y1[i], r=3.5))
        c.append(point(145, y1[i], r=3.5))
        c.append(f'    <text x="32" y="{y1[i]+4}" font-size="12">P_{i+1}</text>')
        c.append(f'    <text x="156" y="{y1[i]+4}" font-size="12">Q_{i+1}</text>')

    # 3 intertwining strands
    c.append(f'    <path d="M 45 55 C 80 55 80 85 115 85 C 135 85 135 55 145 55" fill="none" stroke="{BLUE}" stroke-width="2.0" />')
    c.append(f'    <path d="M 45 85 C 65 85 75 115 95 115 C 120 115 130 85 145 85" fill="none" stroke="{RED}" stroke-width="2.0" />')
    c.append(f'    <path d="M 45 115 C 75 115 95 55 145 115" fill="none" stroke="{GREEN}" stroke-width="2.0" />')
    c.append(f'    <text x="95" y="172" text-anchor="middle" font-size="13">(a)</text>')

    # (b) Concatenation of two braids
    ox2 = 195
    c.append(line(ox2, 45, ox2, 125, stroke=SLATE, width=1.5))
    c.append(line(ox2 + 60, 45, ox2 + 60, 125, stroke=INK, width=1.8))
    c.append(line(ox2 + 120, 45, ox2 + 120, 125, stroke=SLATE, width=1.5))
    # Intertwined strands
    c.append(f'    <path d="M {ox2} 55 C {ox2+30} 85 {ox2+40} 85 {ox2+60} 85 C {ox2+90} 55 {ox2+100} 55 {ox2+120} 55" fill="none" stroke="{BLUE}" stroke-width="1.8" />')
    c.append(f'    <path d="M {ox2} 85 C {ox2+20} 55 {ox2+40} 55 {ox2+60} 55 C {ox2+80} 115 {ox2+100} 115 {ox2+120} 115" fill="none" stroke="{RED}" stroke-width="1.8" />')
    c.append(f'    <path d="M {ox2} 115 C {ox2+30} 115 {ox2+40} 115 {ox2+60} 115 C {ox2+80} 85 {ox2+100} 85 {ox2+120} 85" fill="none" stroke="{GREEN}" stroke-width="1.8" />')
    c.append(f'    <text x="{ox2 + 60}" y="172" text-anchor="middle" font-size="13">(b)</text>')

    # (c) Braid closure in rectangle
    ox3 = 345
    c.append(f'    <rect x="{ox3}" y="45" width="60" height="80" fill="{BLUE_BG}" stroke="{INK}" stroke-width="1.6" />')
    c.append(line(ox3, 60, ox3 + 60, 60, stroke=SLATE, width=1.2))
    c.append(f'    <path d="M {ox3} 80 Q {ox3+30} 105 {ox3+60} 80" fill="none" stroke="{RED}" stroke-width="1.8" />')
    c.append(f'    <path d="M {ox3} 105 Q {ox3+30} 80 {ox3+60} 105" fill="none" stroke="{BLUE}" stroke-width="1.8" />')
    c.append(f'    <text x="{ox3 + 30}" y="172" text-anchor="middle" font-size="13">(c)</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_38() -> str:
    """Fig 38: Steiner tree minimal networks connecting square vertices (D_4 symmetry)."""
    w, h = 380, 190
    c = []
    # (a) Horizontal bridge EF
    ax, ay = 50, 45
    bx, by = 130, 45
    cx, cy = 130, 125
    dx, dy = 50, 125
    c.append(f'    <polygon points="{ax},{ay} {bx},{by} {cx},{cy} {dx},{dy}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="1.8" />')
    ex, ey = 75, 85
    fx, fy = 105, 85
    # Steiner tree lines
    c.append(line(ax, ay, ex, ey, stroke=BLUE, width=2.0))
    c.append(line(dx, dy, ex, ey, stroke=BLUE, width=2.0))
    c.append(line(ex, ey, fx, fy, stroke=BLUE, width=2.2))
    c.append(line(bx, by, fx, fy, stroke=BLUE, width=2.0))
    c.append(line(cx, cy, fx, fy, stroke=BLUE, width=2.0))
    c.append(f'    <text x="{ax-12}" y="{ay-4}" font-size="13">A</text>')
    c.append(f'    <text x="{bx+6}" y="{ay-4}" font-size="13">B</text>')
    c.append(f'    <text x="{cx+6}" y="{cy+14}" font-size="13">C</text>')
    c.append(f'    <text x="{dx-12}" y="{cy+14}" font-size="13">D</text>')
    c.append(f'    <text x="{ex-14}" y="{ey+4}" font-size="12">E</text>')
    c.append(f'    <text x="{fx+6}" y="{fy+4}" font-size="12">F</text>')
    c.append(f'    <text x="90" y="160" text-anchor="middle" font-size="13">(a)</text>')

    # (b) Vertical bridge E'F'
    ox = 210
    a2, b2 = (ox + 50, 45), (ox + 130, 45)
    c2, d2 = (ox + 130, 125), (ox + 50, 125)
    c.append(f'    <polygon points="{a2[0]},{a2[1]} {b2[0]},{b2[1]} {c2[0]},{c2[1]} {d2[0]},{d2[1]}" fill="{AMBER_BG}" stroke="{INK}" stroke-width="1.8" />')
    ep = (ox + 90, 70)
    fp = (ox + 90, 100)
    c.append(line(a2[0], a2[1], ep[0], ep[1], stroke=AMBER, width=2.0))
    c.append(line(b2[0], b2[1], ep[0], ep[1], stroke=AMBER, width=2.0))
    c.append(line(ep[0], ep[1], fp[0], fp[1], stroke=AMBER, width=2.2))
    c.append(line(d2[0], d2[1], fp[0], fp[1], stroke=AMBER, width=2.0))
    c.append(line(c2[0], c2[1], fp[0], fp[1], stroke=AMBER, width=2.0))
    c.append(f'    <text x="{a2[0]-12}" y="{a2[1]-4}" font-size="13">A</text>')
    c.append(f'    <text x="{b2[0]+6}" y="{a2[1]-4}" font-size="13">B</text>')
    c.append(f'    <text x="{c2[0]+6}" y="{c2[1]+14}" font-size="13">C</text>')
    c.append(f'    <text x="{d2[0]-12}" y="{c2[1]+14}" font-size="13">D</text>')
    c.append(f'    <text x="{ep[0]+6}" y="{ep[1]+4}" font-size="12">E\'</text>')
    c.append(f'    <text x="{fp[0]+6}" y="{fp[1]+4}" font-size="12">F\'</text>')
    c.append(f'    <text x="{ox + 90}" y="160" text-anchor="middle" font-size="13">(b)</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_39() -> str:
    """Fig 39: Stern-Gerlach atomic beam splitting (clean scan crop)."""
    return scan_crop_svg(SCAN_PDF, 176, (0.32, 0.16, 0.68, 0.38), dpi=200)


def gen_fig_40() -> str:
    """Fig 40: Bouquet of two circles X v Y (Figure-eight)."""
    w, h = 440, 220
    c = []
    # Circle X (Top Left)
    c.append(f'    <circle cx="125" cy="65" r="38" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.2" />')
    c.append(arrow(125, 103, 100, 97, stroke=BLUE, width=2.2, marker="arr-blue"))
    c.append(point(163, 65, r=4.2, fill=INK))
    c.append(f'    <text x="75" y="70" font-style="italic" font-size="17" fill="{BLUE}">X</text>')
    c.append(f'    <text x="176" y="62" font-style="italic" font-size="16">x₀</text>')

    # Circle Y (Top Right)
    c.append(f'    <circle cx="305" cy="65" r="38" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.2" />')
    c.append(arrow(305, 103, 330, 97, stroke=AMBER, width=2.2, marker="arr-amber"))
    c.append(point(267, 65, r=4.2, fill=INK))
    c.append(f'    <text x="355" y="70" font-style="italic" font-size="17" fill="{AMBER}">Y</text>')
    c.append(f'    <text x="246" y="62" font-style="italic" font-size="16">y₀</text>')

    # Curved connecting arrows
    c.append('    <path d="M 172 75 C 190 95 205 125 210 148" fill="none" stroke="#64748b" stroke-width="1.4" marker-end="url(#arr)" stroke-linecap="round" />')
    c.append('    <path d="M 258 75 C 240 95 225 125 220 148" fill="none" stroke="#64748b" stroke-width="1.4" marker-end="url(#arr)" stroke-linecap="round" />')

    # Bouquet X v Y (Horizontal figure-eight at bottom)
    c.append(f'    <path d="M 215 155 C 175 120 120 125 120 155 C 120 185 175 190 215 155 Z" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.2" stroke-linejoin="round" />')
    c.append(f'    <path d="M 215 155 C 255 120 310 125 310 155 C 310 185 255 190 215 155 Z" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.2" stroke-linejoin="round" />')
    c.append(point(215, 155, r=4.5, fill=INK))
    c.append(f'    <text x="215" y="206" text-anchor="middle" font-style="italic" font-size="16" fill="{INK}">X ∨ Y</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_41() -> str:
    """Fig 41: Suspension Sigma X from cylinder X x I."""
    w, h = 460, 220
    c = []
    # LEFT: Cylinder X x I
    c.append(f'    <path d="M 65 45 L 65 150 A 50 14 0 0 0 165 150 L 165 45 Z" fill="{BLUE_BG}" />')
    # Bottom ellipse
    c.append(f'    <path d="M 65 150 A 50 14 0 0 1 165 150" fill="none" stroke="{SLATE}" stroke-width="1.3" stroke-dasharray="3,3" />')
    c.append(f'    <path d="M 65 150 A 50 14 0 0 0 165 150" fill="none" stroke="{BLUE}" stroke-width="2.0" />')
    # Equator ellipse
    c.append(f'    <path d="M 65 98 A 50 14 0 0 1 165 98" fill="none" stroke="{SLATE}" stroke-width="1.3" stroke-dasharray="3,3" />')
    c.append(f'    <path d="M 65 98 A 50 14 0 0 0 165 98" fill="none" stroke="{BLUE}" stroke-width="2.0" />')
    # Walls
    c.append(line(65, 45, 65, 150, stroke=BLUE, width=2.0))
    c.append(line(165, 45, 165, 150, stroke=BLUE, width=2.0))
    # Top ellipse
    c.append(f'    <ellipse cx="115" cy="45" rx="50" ry="14" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.0" />')
    # Seam I x x0
    c.append(line(115, 45, 115, 164, stroke=INK, width=1.6))
    c.append(point(115, 112, r=4.0, fill=INK))
    # Labels
    c.append(f'    <text x="42" y="32" font-style="italic" font-size="15">X × 0</text>')
    c.append(line(78, 34, 105, 42, stroke=SLATE, width=1.1))
    c.append(f'    <text x="42" y="174" font-style="italic" font-size="15">X × 1</text>')
    c.append(line(78, 168, 105, 156, stroke=SLATE, width=1.1))
    c.append(f'    <text x="56" y="105" font-style="italic" font-size="14">I × x₀</text>')
    c.append(f'    <text x="122" y="117" font-style="italic" font-size="14">x₀</text>')

    # Mapping arrows
    c.append('    <path d="M 170 30 C 215 15 270 15 312 28" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arr)" />')
    c.append('    <path d="M 170 170 C 215 185 270 185 312 172" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arr)" />')

    # RIGHT: Suspension Cone Sigma X
    c.append(f'    <polygon points="320,30 265,100 320,116" fill="{PURPLE_BG}" stroke="none" />')
    c.append(f'    <polygon points="320,30 375,100 320,116" fill="{PURPLE_BG}" stroke="none" />')
    c.append(f'    <polygon points="320,170 265,100 320,116" fill="{PURPLE_BG}" stroke="none" />')
    c.append(f'    <polygon points="320,170 375,100 320,116" fill="{PURPLE_BG}" stroke="none" />')
    c.append(f'    <path d="M 265 100 A 55 16 0 0 1 375 100" fill="none" stroke="{SLATE}" stroke-width="1.3" stroke-dasharray="3,3" />')
    c.append(f'    <path d="M 265 100 A 55 16 0 0 0 375 100" fill="none" stroke="{PURPLE}" stroke-width="2.2" />')
    c.append(line(320, 30, 265, 100, stroke=INK, width=1.8))
    c.append(line(320, 30, 375, 100, stroke=INK, width=1.8))
    c.append(line(320, 170, 265, 100, stroke=INK, width=1.8))
    c.append(line(320, 170, 375, 100, stroke=INK, width=1.8))
    c.append(line(320, 30, 320, 116, stroke=PURPLE, width=1.6))
    c.append(line(320, 170, 320, 116, stroke=PURPLE, width=1.6))
    c.append(point(320, 30, r=4.0))
    c.append(point(320, 170, r=4.0))
    c.append(point(320, 116, r=4.2, fill=PURPLE))
    c.append(f'    <text x="328" y="122" font-style="italic" font-size="14" fill="{PURPLE}">x₀</text>')
    c.append(f'    <text x="320" y="202" text-anchor="middle" font-style="italic" font-size="15" fill="{PURPLE}">ΣX</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_42() -> str:
    """Fig 42: Circle pinch map S^1 -> S^1 v S^1."""
    w, h = 380, 180
    c = []
    # Left: circle S^1 with points 0 and 1/2
    cx, cy, r = 110, 95, 45
    c.append(f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{BLUE_BG}" stroke="{BLUE}" stroke-width="2.2" />')
    c.append(point(cx - r, cy, r=4.0, fill=INK))
    c.append(point(cx + r, cy, r=4.0, fill=INK))
    c.append(f'    <text x="{cx - r - 16}" y="{cy + 5}" font-style="italic" font-size="15">0</text>')
    c.append(f'    <text x="{cx + r + 8}" y="{cy - 6}" font-style="italic" font-size="15">1/2</text>')

    # Right: vertical figure-eight
    rx, ry = 280, 95
    loop_r = 30
    c.append(f'    <circle cx="{rx}" cy="{ry - loop_r}" r="{loop_r}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.2" />')
    c.append(f'    <circle cx="{rx}" cy="{ry + loop_r}" r="{loop_r}" fill="{AMBER_BG}" stroke="{AMBER}" stroke-width="2.2" />')
    c.append(point(rx, ry, r=4.5, fill=INK))

    # Curved mapping arrows from 0 and 1/2 to figure-eight waist
    c.append('    <path d="M 158 88 C 200 80 235 85 272 93" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arr)" />')
    c.append('    <path d="M 68 100 C 120 145 220 135 272 97" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arr)" />')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_43() -> str:
    """Fig 43: Suspension of 2 discrete points S({x, x0}) = S^1."""
    w, h = 380, 180
    c = []
    # Left: two vertical intervals x x I and x0 x I
    ix1, ix2 = 80, 140
    y_t, y_b = 40, 140
    c.append(line(ix1, y_t, ix1, y_b, stroke=BLUE, width=2.2))
    c.append(line(ix2, y_t, ix2, y_b, stroke=GREEN, width=2.2))
    c.append(f'    <text x="35" y="95" font-size="13">R={{x, x₀}}</text>')
    c.append(f'    <text x="{ix1 - 10}" y="{y_t - 8}" font-size="13">x × 1</text>')
    c.append(f'    <text x="{ix1 - 10}" y="{y_b + 18}" font-size="13">x × 0</text>')
    c.append(f'    <text x="{ix2 - 12}" y="{y_t - 8}" font-size="13">x₀ × 1</text>')
    c.append(f'    <text x="{ix2 - 12}" y="{y_b + 18}" font-size="13">x₀ × 0</text>')

    # Center: cone converging to point
    cx = 220
    c.append(f'    <ellipse cx="{cx}" cy="90" rx="14" ry="48" fill="{BLUE_BG}" stroke="{SLATE}" stroke-width="1.4" />')
    c.append(line(cx, 42, 280, 90, stroke=SLATE, width=1.3))
    c.append(line(cx, 138, 280, 90, stroke=SLATE, width=1.3))
    c.append(line(cx, 90, 280, 90, stroke=SLATE, width=1.3))
    c.append(point(280, 90, r=4.2, fill=INK))

    # Curved mapping arrows
    c.append('    <path d="M 80 40 C 130 15 190 15 215 45" fill="none" stroke="#475569" stroke-width="1.4" marker-end="url(#arr)" />')
    c.append('    <path d="M 140 40 C 170 25 195 25 218 55" fill="none" stroke="#475569" stroke-width="1.4" marker-end="url(#arr)" />')

    # Right: circle S^1
    sx, sy, sr = 325, 90, 36
    c.append(f'    <circle cx="{sx}" cy="{sy}" r="{sr}" fill="{PURPLE_BG}" stroke="{PURPLE}" stroke-width="2.2" />')
    c.append(point(sx - sr, sy, r=4.0, fill=INK))
    c.append(f'    <text x="{sx}" y="{sy + 5}" text-anchor="middle" font-size="13">S¹</text>')

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_44() -> str:
    """Fig 44: Triangulated 2-sphere with vertices a, b, c, d, e, f."""
    w, h = 280, 260
    cx, cy, r = 140, 130, 80
    c = []
    # Sphere outline
    c.append(f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{BLUE_BG}" stroke="{INK}" stroke-width="2.0" />')

    # Vertices
    top = (cx, cy - r)
    bot = (cx, cy + r)
    vb = (cx - r, cy)
    vd = (cx + r, cy)
    vc = (cx - 15, cy + 30)
    ve = (cx + 25, cy - 25)

    # Equator ellipse: front solid, back dashed
    c.append(f'    <path d="M {cx-r} {cy} A {r} 24 0 0 0 {cx+r} {cy}" fill="none" stroke="{INK}" stroke-width="1.6" />')
    c.append(f'    <path d="M {cx-r} {cy} A {r} 24 0 0 1 {cx+r} {cy}" fill="none" stroke="{SLATE}" stroke-width="1.2" stroke-dasharray="4,3" />')

    # Front triangulation arcs
    c.append(f'    <path d="M {top[0]} {top[1]} Q {cx-35} {cy} {bot[0]} {bot[1]}" fill="none" stroke="{BLUE}" stroke-width="1.8" />')
    # Back triangulation arc dashed
    c.append(f'    <path d="M {top[0]} {top[1]} Q {cx+35} {cy} {bot[0]} {bot[1]}" fill="none" stroke="{SLATE}" stroke-width="1.3" stroke-dasharray="4,3" />')

    # Vertex dots and labels
    c.append(pt_labeled(top[0], top[1], "a", dy=-8))
    c.append(pt_labeled(bot[0], bot[1], "f", dy=18))
    c.append(pt_labeled(vb[0], vb[1], "b", dx=-16, dy=4))
    c.append(pt_labeled(vd[0], vd[1], "d", dx=8, dy=4))
    c.append(pt_labeled(vc[0], vc[1], "c", dx=6, dy=-6, fill=RED))
    c.append(pt_labeled(ve[0], ve[1], "e", dx=6, dy=-6, fill=MUTED))

    return svg_wrap(w, h, "\n".join(c))


def gen_fig_45() -> str:
    """Fig 45: Homology cycles on torus and double torus."""
    w, h = 420, 180
    c = []
    # (a) Torus on left
    t1x, t1y = 110, 85
    c.append(f'    <ellipse cx="{t1x}" cy="{t1y}" rx="72" ry="46" fill="{BLUE_BG}" stroke="{INK}" stroke-width="2.0" />')
    # Inner hole
    c.append(f'    <path d="M {t1x-28} {t1y-6} Q {t1x} {t1y+15} {t1x+28} {t1y-6}" fill="none" stroke="{INK}" stroke-width="1.8" />')
    c.append(f'    <path d="M {t1x-20} {t1y+2} Q {t1x} {t1y-10} {t1x+20} {t1y+2}" fill="none" stroke="{INK}" stroke-width="1.5" />')
    # Meridian cycles c and c'
    # Meridian c: front solid, back dashed
    c1x = t1x - 36
    c.append(f'    <path d="M {c1x} {t1y-23} A 10 23 0 0 0 {c1x} {t1y+23}" fill="none" stroke="{RED}" stroke-width="1.8" />')
    c.append(f'    <path d="M {c1x} {t1y-23} A 10 23 0 0 1 {c1x} {t1y+23}" fill="none" stroke="{RED}" stroke-width="1.4" stroke-dasharray="3,3" />')
    c.append(f'    <text x="{c1x-18}" y="{t1y+6}" font-style="italic" font-size="14" fill="{RED}">c</text>')

    # Meridian c': front solid, back dashed
    c2x = t1x + 36
    c.append(f'    <path d="M {c2x} {t1y-23} A 10 23 0 0 0 {c2x} {t1y+23}" fill="none" stroke="{RED}" stroke-width="1.8" />')
    c.append(f'    <path d="M {c2x} {t1y-23} A 10 23 0 0 1 {c2x} {t1y+23}" fill="none" stroke="{RED}" stroke-width="1.4" stroke-dasharray="3,3" />')
    c.append(f'    <text x="{c2x+14}" y="{t1y+6}" font-style="italic" font-size="14" fill="{RED}">c\'</text>')
    c.append(f'    <text x="{t1x}" y="160" text-anchor="middle" font-size="13">(a)</text>')

    # (b) Double torus on right
    t2x, t2y = 295, 85
    outline = (
        f"M {t2x-68} {t2y} "
        f"C {t2x-68} {t2y-46} {t2x} {t2y-46} {t2x} {t2y-18} "
        f"C {t2x} {t2y-46} {t2x+68} {t2y-46} {t2x+68} {t2y} "
        f"C {t2x+68} {t2y+46} {t2x} {t2y+46} {t2x} {t2y+18} "
        f"C {t2x} {t2y+46} {t2x-68} {t2y+46} {t2x-68} {t2y} Z"
    )
    c.append(f'    <path d="{outline}" fill="{AMBER_BG}" stroke="{INK}" stroke-width="2.0" />')
    # Holes left and right
    c.append(f'    <path d="M {t2x-45} {t2y-4} Q {t2x-32} {t2y+10} {t2x-19} {t2y-4}" fill="none" stroke="{INK}" stroke-width="1.6" />')
    c.append(f'    <path d="M {t2x-40} {t2y+2} Q {t2x-32} {t2y-6} {t2x-24} {t2y+2}" fill="none" stroke="{INK}" stroke-width="1.4" />')
    c.append(f'    <path d="M {t2x+19} {t2y-4} Q {t2x+32} {t2y+10} {t2x+45} {t2y-4}" fill="none" stroke="{INK}" stroke-width="1.6" />')
    c.append(f'    <path d="M {t2x+24} {t2y+2} Q {t2x+32} {t2y-6} {t2x+40} {t2y+2}" fill="none" stroke="{INK}" stroke-width="1.4" />')

    # Bounding waist cycle d: front solid, back dashed
    c.append(f'    <path d="M {t2x} {t2y-18} A 7 18 0 0 0 {t2x} {t2y+18}" fill="none" stroke="{GREEN}" stroke-width="2.0" />')
    c.append(f'    <path d="M {t2x} {t2y-18} A 7 18 0 0 1 {t2x} {t2y+18}" fill="none" stroke="{GREEN}" stroke-width="1.4" stroke-dasharray="3,3" />')
    c.append(f'    <text x="{t2x+16}" y="{t2y+5}" font-style="italic" font-size="14" fill="{GREEN}">d</text>')
    c.append(f'    <text x="{t2x}" y="160" text-anchor="middle" font-size="13">(b)</text>')

    return svg_wrap(w, h, "\n".join(c))
