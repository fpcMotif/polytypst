"""3Blue1Brown-styled parametric 2D textbook vector figures for Kostrikin: Linear Algebra.

Generates both:
1. Monochrome edition: Crisp, high-contrast black-and-white publication vectors (0f172a / white)
2. Colorful edition: Vibrant 3Blue1Brown pedagogical color palette (blue, teal, yellow, coral, green, purple)

All 31 figures are rendered as scalable SVG vectors and compiled to 300-DPI raster PNGs.
"""

import math
from collections.abc import Callable
from pathlib import Path

import pymupdf

# =========================================================================
# Shared SVG Definitions and Styling
# =========================================================================

def _marker_defs(colorful: bool) -> str:
    if not colorful:
        return """
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#0f172a" />
    </marker>
    <marker id="arr-rev" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto">
      <path d="M 9 1.5 L 0 5 L 9 8.5 L 7 5 z" fill="#0f172a" />
    </marker>
    <pattern id="hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#475569" stroke-width="1.2" />
    </pattern>
"""
    return """
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#1e293b" />
    </marker>
    <marker id="arr-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#2563eb" />
    </marker>
    <marker id="arr-teal" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#0891b2" />
    </marker>
    <marker id="arr-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#d97706" />
    </marker>
    <marker id="arr-coral" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#e11d48" />
    </marker>
    <marker id="arr-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#7c3aed" />
    </marker>
    <marker id="arr-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#059669" />
    </marker>
    <linearGradient id="blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#1d4ed8" stop-opacity="0.08" />
    </linearGradient>
    <linearGradient id="amber-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.30" />
      <stop offset="100%" stop-color="#d97706" stop-opacity="0.10" />
    </linearGradient>
    <linearGradient id="teal-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#0891b2" stop-opacity="0.08" />
    </linearGradient>
    <linearGradient id="rose-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#e11d48" stop-opacity="0.08" />
    </linearGradient>
    <pattern id="hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.4" />
    </pattern>
"""


def _svg_wrap(viewbox: str, content: str, colorful: bool) -> str:
    defs = _marker_defs(colorful)
    font_family = '"New Computer Modern", "Latin Modern Math", "STIX Two Math", "Songti SC", "Times New Roman", serif'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="100%" height="100%">
  <defs>
{defs}
  </defs>
  <rect width="100%" height="100%" fill="#ffffff" />
  <g font-family='{font_family}' font-size="14" text-anchor="middle" dominant-baseline="central">
{content}
  </g>
</svg>"""


# =========================================================================
# Figure Generators 1 to 31
# =========================================================================

def generate_fig_1(colorful: bool = False) -> str:
    """Fig 1: 3D binary hypercube F_2^3 and parity subspace Pi_3."""
    c_edge = "#64748b" if not colorful else "#94a3b8"
    c_tetra = "#0f172a" if not colorful else "#2563eb"
    c_fill = "none" if not colorful else "url(#blue-grad)"
    c_pt_odd = "#94a3b8" if not colorful else "#cbd5e1"
    c_pt_even = "#0f172a" if not colorful else "#e11d48"

    # Isometric projection of [0,1]^3
    # v0=(0,0,0), v1=(1,0,0), v2=(0,1,0), v3=(1,1,0)
    # v4=(0,0,1), v5=(1,0,1), v6=(0,1,1), v7=(1,1,1)
    pts = {
        "000": (180, 240),
        "100": (290, 210),
        "010": (90, 190),
        "110": (200, 160),
        "001": (180, 120),
        "101": (290, 90),
        "011": (90, 70),
        "111": (200, 40),
    }
    # Cube edges
    cube_lines = [
        ("000", "100"), ("000", "010"), ("100", "110"), ("010", "110"),
        ("001", "101"), ("001", "011"), ("101", "111"), ("011", "111"),
        ("000", "001"), ("100", "101"), ("010", "011"), ("110", "111")
    ]
    edges_svg = "\n".join(
        f'<line x1="{pts[p1][0]}" y1="{pts[p1][1]}" x2="{pts[p2][0]}" y2="{pts[p2][1]}" stroke="{c_edge}" stroke-width="1.2" stroke-dasharray="3 3" />'
        for p1, p2 in cube_lines
    )
    # Even parity tetrahedron: 000, 110, 101, 011
    tetra_poly = f'<polygon points="{pts["000"][0]},{pts["000"][1]} {pts["110"][0]},{pts["110"][1]} {pts["101"][0]},{pts["101"][1]}" fill="{c_fill}" stroke="{c_tetra}" stroke-width="2.2" stroke-linejoin="round" />'
    tetra_lines = [
        ("000", "011"), ("110", "011"), ("101", "011")
    ]
    tetra_edges = "\n".join(
        f'<line x1="{pts[p1][0]}" y1="{pts[p1][1]}" x2="{pts[p2][0]}" y2="{pts[p2][1]}" stroke="{c_tetra}" stroke-width="2.2" stroke-linecap="round" />'
        for p1, p2 in tetra_lines
    )
    # Vertices
    v_svg: list[str] = []
    even_keys = {"000", "110", "101", "011"}
    for k, (x, y) in pts.items():
        is_even = k in even_keys
        col = c_pt_even if is_even else c_pt_odd
        r = "6" if is_even else "4"
        v_svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}" stroke="#ffffff" stroke-width="1.5" />')
        # Labels
        dx = 15 if x >= 180 else -15
        dy = 12 if y >= 140 else -12
        v_svg.append(f'<text x="{x + dx}" y="{y + dy}" font-size="11" fill="{c_tetra if is_even else c_edge}">({k[0]},{k[1]},{k[2]})</text>')

    body = f"""
    {edges_svg}
    {tetra_poly}
    {tetra_edges}
    {''.join(v_svg)}
    <text x="200" y="270" font-size="13" font-weight="bold" fill="{c_tetra}">Π₃ = &#123; (ε₁, ε₂, ε₃) | ε₁ + ε₂ + ε₃ ≡ 0 (mod 2) &#125;</text>
    """
    return _svg_wrap("0 0 380 290", body, colorful)


def generate_fig_2(colorful: bool = False) -> str:
    """Fig 2: 2D plane with subspace L and direct sum complements M."""
    c_axis = "#475569" if not colorful else "#64748b"
    c_l = "#0f172a" if not colorful else "#2563eb"
    c_m1 = "#334155" if not colorful else "#059669"
    c_m2 = "#334155" if not colorful else "#d97706"
    arr_l = "arr" if not colorful else "arr-blue"
    arr_m1 = "arr" if not colorful else "arr-green"
    arr_m2 = "arr" if not colorful else "arr-amber"

    body = f"""
    <!-- Coordinate axes -->
    <line x1="40" y1="150" x2="340" y2="150" stroke="{c_l}" stroke-width="2.6" marker-end="url(#{arr_l})" />
    <line x1="180" y1="260" x2="180" y2="30" stroke="{c_axis}" stroke-width="1.2" marker-end="url(#arr)" />
    <text x="330" y="135" font-weight="bold" fill="{c_l}">L (x轴)</text>
    <text x="195" y="40" fill="{c_axis}">y</text>
    <text x="168" y="165" font-style="italic" fill="#0f172a">O</text>

    <!-- Complements M, M' -->
    <line x1="70" y1="260" x2="290" y2="40" stroke="{c_m1}" stroke-width="2.2" stroke-linecap="round" marker-end="url(#{arr_m1})" />
    <text x="305" y="50" font-weight="bold" fill="{c_m1}">M</text>

    <line x1="90" y1="40" x2="270" y2="260" stroke="{c_m2}" stroke-width="1.8" stroke-dasharray="5 3" marker-end="url(#{arr_m2})" />
    <text x="285" y="250" font-weight="bold" fill="{c_m2}">M′</text>

    <circle cx="180" cy="150" r="4.5" fill="#0f172a" />
    <text x="180" y="275" font-size="12" fill="#475569">V = L ⊕ M = L ⊕ M′</text>
    """
    return _svg_wrap("0 0 380 290", body, colorful)


def generate_fig_3(colorful: bool = False) -> str:
    """Fig 3: Vector difference triangle z = y - x and angle phi."""
    c_x = "#0f172a" if not colorful else "#2563eb"
    c_y = "#0f172a" if not colorful else "#0891b2"
    c_z = "#0f172a" if not colorful else "#e11d48"
    c_arc = "#d97706" if colorful else "#475569"
    arr_x = "arr" if not colorful else "arr-blue"
    arr_y = "arr" if not colorful else "arr-teal"
    arr_z = "arr" if not colorful else "arr-coral"

    ox, oy = 70, 220
    px, py = 280, 220
    qx, qy = 230, 70

    body = f"""
    <!-- Vector x -->
    <line x1="{ox}" y1="{oy}" x2="{px}" y2="{py}" stroke="{c_x}" stroke-width="2.6" marker-end="url(#{arr_x})" />
    <!-- Vector y -->
    <line x1="{ox}" y1="{oy}" x2="{qx}" y2="{qy}" stroke="{c_y}" stroke-width="2.6" marker-end="url(#{arr_y})" />
    <!-- Difference z = y - x -->
    <line x1="{px}" y1="{py}" x2="{qx}" y2="{qy}" stroke="{c_z}" stroke-width="2.6" marker-end="url(#{arr_z})" />

    <!-- Angle arc -->
    <path d="M 120 220 A 50 50 0 0 0 106 172" fill="none" stroke="{c_arc}" stroke-width="1.8" />
    <text x="135" y="195" font-style="italic" fill="{c_arc}" font-size="15">φ</text>

    <!-- Labels -->
    <text x="175" y="240" font-weight="bold" fill="{c_x}">x</text>
    <text x="135" y="130" font-weight="bold" fill="{c_y}">y</text>
    <text x="275" y="140" font-weight="bold" fill="{c_z}">z = y − x</text>
    <text x="55" y="235" font-style="italic" fill="#0f172a">O</text>
    <circle cx="{ox}" cy="{oy}" r="4" fill="#0f172a" />
    <circle cx="{px}" cy="{py}" r="4" fill="{c_x}" />
    <circle cx="{qx}" cy="{qy}" r="4" fill="{c_y}" />
    """
    return _svg_wrap("0 0 360 270", body, colorful)


def generate_fig_4(colorful: bool = False) -> str:
    """Fig 4: Symplectic eigenvalues 4-fold symmetry around unit circle."""
    c_axis = "#64748b" if not colorful else "#94a3b8"
    c_circ = "#0f172a" if not colorful else "#3b82f6"
    c_pt = "#0f172a" if not colorful else "#e11d48"
    c_ray = "#94a3b8" if not colorful else "#cbd5e1"

    cx, cy = 180, 140
    r = 85
    # lambda = 1.6 * exp(i * 38 deg)
    theta = math.radians(38)
    r_out = r * 1.55
    r_in = r / 1.55

    l1_x, l1_y = cx + r_out * math.cos(theta), cy - r_out * math.sin(theta)
    l2_x, l2_y = cx + r_out * math.cos(theta), cy + r_out * math.sin(theta)
    l3_x, l3_y = cx + r_in * math.cos(theta), cy - r_in * math.sin(theta)
    l4_x, l4_y = cx + r_in * math.cos(theta), cy + r_in * math.sin(theta)

    body = f"""
    <!-- Complex axes -->
    <line x1="30" y1="{cy}" x2="330" y2="{cy}" stroke="{c_axis}" stroke-width="1.2" marker-end="url(#arr)" />
    <line x1="{cx}" y1="260" x2="{cx}" y2="20" stroke="{c_axis}" stroke-width="1.2" marker-end="url(#arr)" />
    <text x="325" y="{cy + 15}" fill="{c_axis}">Re</text>
    <text x="{cx + 15}" y="25" fill="{c_axis}">Im</text>

    <!-- Unit circle -->
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c_circ}" stroke-width="2" />
    <text x="{cx + r - 12}" y="{cy + 16}" font-size="11" fill="{c_circ}">1</text>

    <!-- Symmetry rays -->
    <line x1="{cx}" y1="{cy}" x2="{l1_x + 15}" y2="{l1_y - 10}" stroke="{c_ray}" stroke-width="1" stroke-dasharray="3 3" />
    <line x1="{cx}" y1="{cy}" x2="{l2_x + 15}" y2="{l2_y + 10}" stroke="{c_ray}" stroke-width="1" stroke-dasharray="3 3" />
    <line x1="{l1_x}" y1="{l1_y}" x2="{l2_x}" y2="{l2_y}" stroke="{c_ray}" stroke-width="1" stroke-dasharray="3 3" />

    <!-- 4 Eigenvalues -->
    <circle cx="{l1_x}" cy="{l1_y}" r="5" fill="{c_pt}" />
    <text x="{l1_x + 18}" y="{l1_y - 8}" font-weight="bold" fill="{c_pt}">λ</text>

    <circle cx="{l2_x}" cy="{l2_y}" r="5" fill="{c_pt}" />
    <text x="{l2_x + 18}" y="{l2_y + 8}" font-weight="bold" fill="{c_pt}">λ̄</text>

    <circle cx="{l3_x}" cy="{l3_y}" r="5" fill="{c_pt}" />
    <text x="{l3_x - 22}" y="{l3_y - 8}" font-weight="bold" fill="{c_pt}">λ̄⁻¹</text>

    <circle cx="{l4_x}" cy="{l4_y}" r="5" fill="{c_pt}" />
    <text x="{l4_x - 20}" y="{l4_y + 12}" font-weight="bold" fill="{c_pt}">λ⁻¹</text>
    """
    return _svg_wrap("0 0 360 280", body, colorful)


def generate_fig_5(colorful: bool = False) -> str:
    """Fig 5: Affine coordinate frame transformation {o; e_i} to {o'; e'_i}."""
    c_f1 = "#0f172a" if not colorful else "#2563eb"
    c_f2 = "#334155" if not colorful else "#7c3aed"
    c_trans = "#e11d48" if colorful else "#0f172a"
    arr1 = "arr" if not colorful else "arr-blue"
    arr2 = "arr" if not colorful else "arr-purple"
    arr_t = "arr" if not colorful else "arr-coral"

    o1_x, o1_y = 60, 220
    o2_x, o2_y = 180, 160
    px, py = 310, 70

    body = f"""
    <!-- Origin 1 frame -->
    <line x1="{o1_x}" y1="{o1_y}" x2="{o1_x + 75}" y2="{o1_y}" stroke="{c_f1}" stroke-width="2.2" marker-end="url(#{arr1})" />
    <line x1="{o1_x}" y1="{o1_y}" x2="{o1_x}" y2="{o1_y - 75}" stroke="{c_f1}" stroke-width="2.2" marker-end="url(#{arr1})" />
    <line x1="{o1_x}" y1="{o1_y}" x2="{o1_x - 35}" y2="{o1_y + 35}" stroke="{c_f1}" stroke-width="2.2" marker-end="url(#{arr1})" />
    <text x="{o1_x - 12}" y="{o1_y + 10}" font-weight="bold" fill="{c_f1}">o</text>
    <text x="{o1_x + 85}" y="{o1_y + 5}" fill="{c_f1}">e₁</text>
    <text x="{o1_x - 8}" y="{o1_y - 85}" fill="{c_f1}">e₂</text>

    <!-- Transition vector oo' -->
    <line x1="{o1_x}" y1="{o1_y}" x2="{o2_x}" y2="{o2_y}" stroke="{c_trans}" stroke-width="2.4" stroke-dasharray="5 3" marker-end="url(#{arr_t})" />
    <text x="110" y="175" font-weight="bold" fill="{c_trans}">oo′</text>

    <!-- Origin 2 frame -->
    <line x1="{o2_x}" y1="{o2_y}" x2="{o2_x + 70}" y2="{o2_y - 20}" stroke="{c_f2}" stroke-width="2.2" marker-end="url(#{arr2})" />
    <line x1="{o2_x}" y1="{o2_y}" x2="{o2_x + 10}" y2="{o2_y - 70}" stroke="{c_f2}" stroke-width="2.2" marker-end="url(#{arr2})" />
    <text x="{o2_x - 12}" y="{o2_y + 12}" font-weight="bold" fill="{c_f2}">o′</text>
    <text x="{o2_x + 85}" y="{o2_y - 25}" fill="{c_f2}">e′₁</text>
    <text x="{o2_x + 15}" y="{o2_y - 82}" fill="{c_f2}">e′₂</text>

    <!-- Point p and position vectors -->
    <line x1="{o1_x}" y1="{o1_y}" x2="{px}" y2="{py}" stroke="{c_f1}" stroke-width="1.6" marker-end="url(#{arr1})" />
    <line x1="{o2_x}" y1="{o2_y}" x2="{px}" y2="{py}" stroke="{c_f2}" stroke-width="1.6" marker-end="url(#{arr2})" />
    <circle cx="{px}" cy="{py}" r="5" fill="#0f172a" />
    <text x="{px + 15}" y="{py - 5}" font-weight="bold" fill="#0f172a">p</text>
    <text x="210" y="110" fill="{c_f1}">op</text>
    <text x="260" y="130" fill="{c_f2}">o′p</text>
    """
    return _svg_wrap("0 0 380 270", body, colorful)


def generate_fig_6(colorful: bool = False) -> str:
    """Fig 6: Intersecting affine planes Pi and Pi' in 3D."""
    c_p1 = "#2563eb" if colorful else "#0f172a"
    c_p2 = "#059669" if colorful else "#334155"
    fill1 = "url(#blue-grad)" if colorful else "none"
    fill2 = "url(#teal-grad)" if colorful else "none"

    body = f"""
    <!-- Plane 1 -->
    <polygon points="50,180 180,80 320,80 190,180" fill="{fill1}" stroke="{c_p1}" stroke-width="2" />
    <!-- Plane 2 (intersecting) -->
    <polygon points="120,230 180,50 250,50 190,230" fill="{fill2}" stroke="{c_p2}" stroke-width="2" />
    <!-- Line of intersection -->
    <line x1="180" y1="80" x2="190" y2="180" stroke="#e11d48" stroke-width="3" stroke-linecap="round" />

    <text x="80" y="140" font-weight="bold" fill="{c_p1}">Π</text>
    <text x="225" y="210" font-weight="bold" fill="{c_p2}">Π′</text>
    <text x="210" y="130" font-weight="bold" fill="#e11d48">L = Π ∩ Π′</text>
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_7(colorful: bool = False) -> str:
    """Fig 7: 3D affine simplex (tetrahedron) with barycentric coordinates."""
    c_edge = "#0f172a" if not colorful else "#1e3a8a"
    fill_face = "url(#blue-grad)" if colorful else "none"

    p0 = (60, 210)
    p1 = (270, 230)
    p2 = (310, 150)
    p3 = (170, 40)

    body = f"""
    <!-- Faces -->
    <polygon points="{p0[0]},{p0[1]} {p1[0]},{p1[1]} {p3[0]},{p3[1]}" fill="{fill_face}" stroke="{c_edge}" stroke-width="2" />
    <polygon points="{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]}" fill="{fill_face}" stroke="{c_edge}" stroke-width="2" />
    <!-- Hidden edge p0-p2 -->
    <line x1="{p0[0]}" y1="{p0[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="{c_edge}" stroke-width="1.5" stroke-dasharray="4 4" />
    <!-- Edge p0-p3 -->
    <line x1="{p0[0]}" y1="{p0[1]}" x2="{p3[0]}" y2="{p3[1]}" stroke="{c_edge}" stroke-width="2" />

    <!-- Vertices -->
    <circle cx="{p0[0]}" cy="{p0[1]}" r="4.5" fill="#e11d48" />
    <text x="{p0[0] - 18}" y="{p0[1] + 5}" font-weight="bold">p₀</text>

    <circle cx="{p1[0]}" cy="{p1[1]}" r="4.5" fill="#e11d48" />
    <text x="{p1[0] + 15}" y="{p1[1] + 10}" font-weight="bold">p₁</text>

    <circle cx="{p2[0]}" cy="{p2[1]}" r="4.5" fill="#e11d48" />
    <text x="{p2[0] + 15}" y="{p2[1] - 5}" font-weight="bold">p₂</text>

    <circle cx="{p3[0]}" cy="{p3[1]}" r="4.5" fill="#e11d48" />
    <text x="{p3[0]}" y="{p3[1] - 15}" font-weight="bold">p₃</text>
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_8(colorful: bool = False) -> str:
    """Fig 8: Triangle interior point p as convex combination."""
    c_tri = "#0f172a" if not colorful else "#2563eb"
    c_ray = "#d97706" if colorful else "#64748b"
    fill = "url(#blue-grad)" if colorful else "none"

    p0 = (60, 220)
    p1 = (300, 220)
    p2 = (180, 50)
    # p on ray from p0 to q on p1-p2
    qx, qy = 240, 135
    px, py = 150, 177

    body = f"""
    <polygon points="{p0[0]},{p0[1]} {p1[0]},{p1[1]} {p2[0]},{p2[1]}" fill="{fill}" stroke="{c_tri}" stroke-width="2.2" />
    <!-- Ray p0 -> q -->
    <line x1="{p0[0]}" y1="{p0[1]}" x2="{qx}" y2="{qy}" stroke="{c_ray}" stroke-width="1.8" stroke-dasharray="4 3" />

    <circle cx="{p0[0]}" cy="{p0[1]}" r="4.5" fill="{c_tri}" />
    <text x="{p0[0] - 15}" y="{p0[1] + 5}" font-weight="bold">p₀</text>

    <circle cx="{p1[0]}" cy="{p1[1]}" r="4.5" fill="{c_tri}" />
    <text x="{p1[0] + 15}" y="{p1[1] + 5}" font-weight="bold">p₁</text>

    <circle cx="{p2[0]}" cy="{p2[1]}" r="4.5" fill="{c_tri}" />
    <text x="{p2[0]}" y="{p2[1] - 15}" font-weight="bold">p₂</text>

    <circle cx="{px}" cy="{py}" r="5" fill="#e11d48" />
    <text x="{px + 12}" y="{py - 10}" font-weight="bold" fill="#e11d48">p</text>

    <circle cx="{qx}" cy="{qy}" r="4" fill="{c_ray}" />
    <text x="{qx + 15}" y="{qy}" font-style="italic" fill="{c_ray}">q</text>
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_9(colorful: bool = False) -> str:
    """Fig 9: Convex set M and line segments joining points."""
    c_m = "#0f172a" if not colorful else "#059669"
    c_seg = "#e11d48" if colorful else "#0f172a"
    fill = "url(#teal-grad)" if colorful else "none"

    body = f"""
    <!-- Smooth convex set M -->
    <path d="M 80 180 C 40 100, 120 40, 240 50 C 330 60, 340 160, 270 210 C 200 240, 120 230, 80 180 Z"
          fill="{fill}" stroke="{c_m}" stroke-width="2.4" />
    <text x="290" y="80" font-weight="bold" fill="{c_m}" font-size="16">M</text>

    <!-- Segment q1 - q2 -->
    <line x1="120" y1="160" x2="230" y2="120" stroke="{c_seg}" stroke-width="2.2" stroke-linecap="round" />
    <circle cx="120" cy="160" r="4.5" fill="{c_seg}" />
    <text x="105" y="175" font-weight="bold" fill="{c_seg}">q₁</text>
    <circle cx="230" cy="120" r="4.5" fill="{c_seg}" />
    <text x="245" y="115" font-weight="bold" fill="{c_seg}">q₂</text>

    <!-- Point p and segments -->
    <circle cx="180" cy="190" r="4.5" fill="{c_seg}" />
    <text x="180" y="210" font-weight="bold" fill="{c_seg}">p</text>
    <line x1="180" y1="190" x2="120" y2="160" stroke="{c_seg}" stroke-width="1.4" stroke-dasharray="3 3" />
    <line x1="180" y1="190" x2="230" y2="120" stroke="{c_seg}" stroke-width="1.4" stroke-dasharray="3 3" />
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_10(colorful: bool = False) -> str:
    """Fig 10: Central quadric curve (ellipse) and symmetry axes."""
    c_axis = "#64748b" if not colorful else "#94a3b8"
    c_curve = "#0f172a" if not colorful else "#2563eb"
    fill = "url(#blue-grad)" if colorful else "none"

    cx, cy = 180, 140
    rx, ry = 110, 65

    body = f"""
    <!-- Axes through center o -->
    <line x1="40" y1="{cy}" x2="320" y2="{cy}" stroke="{c_axis}" stroke-width="1.2" marker-end="url(#arr)" />
    <line x1="{cx}" y1="240" x2="{cx}" y2="40" stroke="{c_axis}" stroke-width="1.2" marker-end="url(#arr)" />
    <text x="315" y="{cy - 12}" fill="{c_axis}">x + o</text>
    <text x="{cx + 25}" y="45" fill="{c_axis}">y + o</text>
    <text x="{cx - 15}" y="{cy + 15}" font-style="italic">o</text>

    <!-- Quadric ellipse -->
    <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{c_curve}" stroke-width="2.4" />

    <!-- Symmetric points x and -x -->
    <line x1="{cx - 80}" y1="{cy - 45}" x2="{cx + 80}" y2="{cy + 45}" stroke="#e11d48" stroke-width="1.5" stroke-dasharray="4 3" />
    <circle cx="{cx + 80}" cy="{cy + 45}" r="4.5" fill="#e11d48" />
    <text x="{cx + 95}" y="{cy + 55}" font-weight="bold" fill="#e11d48">x</text>

    <circle cx="{cx - 80}" cy="{cy - 45}" r="4.5" fill="#e11d48" />
    <text x="{cx - 95}" y="{cy - 55}" font-weight="bold" fill="#e11d48">−x</text>
    """
    return _svg_wrap("0 0 360 270", body, colorful)


def generate_fig_11(colorful: bool = False) -> str:
    """Fig 11: Quadric cone with vertex o."""
    c_cone = "#0f172a" if not colorful else "#2563eb"
    fill = "url(#blue-grad)" if colorful else "none"

    ox, oy = 180, 140
    rw, rh = 70, 20

    body = f"""
    <!-- Upper cone -->
    <ellipse cx="{ox}" cy="50" rx="{rw}" ry="{rh}" fill="{fill}" stroke="{c_cone}" stroke-width="2" />
    <line x1="{ox - rw}" y1="50" x2="{ox}" y2="{oy}" stroke="{c_cone}" stroke-width="2" />
    <line x1="{ox + rw}" y1="50" x2="{ox}" y2="{oy}" stroke="{c_cone}" stroke-width="2" />

    <!-- Lower cone -->
    <ellipse cx="{ox}" cy="230" rx="{rw}" ry="{rh}" fill="{fill}" stroke="{c_cone}" stroke-width="2" />
    <line x1="{ox - rw}" y1="230" x2="{ox}" y2="{oy}" stroke="{c_cone}" stroke-width="2" />
    <line x1="{ox + rw}" y1="230" x2="{ox}" y2="{oy}" stroke="{c_cone}" stroke-width="2" />

    <!-- Vertex o -->
    <circle cx="{ox}" cy="{oy}" r="4.5" fill="#e11d48" />
    <text x="{ox + 18}" y="{oy}" font-weight="bold" fill="#e11d48">o (顶点)</text>
    <text x="{ox}" y="270" font-size="12" fill="#475569">x²/a² + y²/b² − z²/c² = 0</text>
    """
    return _svg_wrap("0 0 360 290", body, colorful)


def generate_fig_12(colorful: bool = False) -> str:
    """Fig 12: Quadric cylinder with direction u."""
    c_cyl = "#0f172a" if not colorful else "#0891b2"
    c_u = "#e11d48" if colorful else "#0f172a"
    arr_u = "arr" if not colorful else "arr-coral"
    fill = "url(#teal-grad)" if colorful else "none"

    rw, rh = 65, 20
    top_x, top_y = 200, 60
    bot_x, bot_y = 140, 220

    body = f"""
    <!-- Cylinder body fill -->
    <polygon points="{top_x - rw},{top_y} {top_x + rw},{top_y} {bot_x + rw},{bot_y} {bot_x - rw},{bot_y}" fill="{fill}" stroke="none" />
    <!-- Rulings -->
    <line x1="{top_x - rw}" y1="{top_y}" x2="{bot_x - rw}" y2="{bot_y}" stroke="{c_cyl}" stroke-width="2" />
    <line x1="{top_x + rw}" y1="{top_y}" x2="{bot_x + rw}" y2="{bot_y}" stroke="{c_cyl}" stroke-width="2" />

    <!-- Top and bottom ellipses -->
    <ellipse cx="{top_x}" cy="{top_y}" rx="{rw}" ry="{rh}" fill="{fill}" stroke="{c_cyl}" stroke-width="2" />
    <path d="M {bot_x - rw} {bot_y} A {rw} {rh} 0 0 0 {bot_x + rw} {bot_y}" fill="none" stroke="{c_cyl}" stroke-width="2" />
    <path d="M {bot_x - rw} {bot_y} A {rw} {rh} 0 0 1 {bot_x + rw} {bot_y}" fill="none" stroke="{c_cyl}" stroke-width="1.2" stroke-dasharray="4 3" />

    <!-- Direction vector u -->
    <line x1="280" y1="180" x2="{280 + (top_x - bot_x) * 0.5}" y2="{180 + (top_y - bot_y) * 0.5}" stroke="{c_u}" stroke-width="2.6" marker-end="url(#{arr_u})" />
    <text x="{290 + (top_x - bot_x) * 0.5}" y="{170 + (top_y - bot_y) * 0.5}" font-weight="bold" fill="{c_u}">u</text>
    """
    return _svg_wrap("0 0 360 270", body, colorful)


def generate_fig_13(colorful: bool = False) -> str:
    """Fig 13: Ellipsoid with 3 principal axes."""
    c_e = "#0f172a" if not colorful else "#2563eb"
    c_axis = "#94a3b8"
    fill = "url(#blue-grad)" if colorful else "none"

    cx, cy = 180, 140
    a, b = 110, 65

    body = f"""
    <!-- Main outline -->
    <ellipse cx="{cx}" cy="{cy}" rx="{a}" ry="{b}" fill="{fill}" stroke="{c_e}" stroke-width="2.4" />

    <!-- Internal cross-sections -->
    <!-- Horizontal equator -->
    <path d="M {cx - a} {cy} A {a} 22 0 0 0 {cx + a} {cy}" fill="none" stroke="{c_e}" stroke-width="1.4" />
    <path d="M {cx - a} {cy} A {a} 22 0 0 1 {cx + a} {cy}" fill="none" stroke="{c_e}" stroke-width="1.2" stroke-dasharray="3 3" />

    <!-- Vertical meridian -->
    <ellipse cx="{cx}" cy="{cy}" rx="30" ry="{b}" fill="none" stroke="{c_e}" stroke-width="1.2" stroke-dasharray="4 3" />

    <!-- Axes -->
    <line x1="40" y1="{cy}" x2="320" y2="{cy}" stroke="{c_axis}" stroke-width="1" stroke-dasharray="3 3" />
    <line x1="{cx}" y1="230" x2="{cx}" y2="50" stroke="{c_axis}" stroke-width="1" stroke-dasharray="3 3" />
    <text x="{cx + a - 15}" y="{cy - 12}" fill="{c_e}">a</text>
    <text x="{cx + 12}" y="65" fill="{c_e}">c</text>
    <text x="180" y="260" font-size="12" fill="#475569">x²/a² + y²/b² + z²/c² = 1</text>
    """
    return _svg_wrap("0 0 360 280", body, colorful)


def generate_fig_14(colorful: bool = False) -> str:
    """Fig 14: Hyperboloid of one sheet (single-sheet ruled hyperboloid)."""
    c_h = "#0f172a" if not colorful else "#059669"
    fill = "url(#teal-grad)" if colorful else "none"

    cx, cy = 180, 140
    top_w, top_h = 80, 22
    mid_w, mid_h = 42, 12

    body = f"""
    <!-- Waist ellipse -->
    <ellipse cx="{cx}" cy="{cy}" rx="{mid_w}" ry="{mid_h}" fill="none" stroke="{c_h}" stroke-width="1.5" stroke-dasharray="3 3" />
    <!-- Side hyperbolic profiles -->
    <path d="M {cx - top_w} 40 Q {cx - mid_w} {cy} {cx - top_w} 240" fill="none" stroke="{c_h}" stroke-width="2.2" />
    <path d="M {cx + top_w} 40 Q {cx + mid_w} {cy} {cx + top_w} 240" fill="none" stroke="{c_h}" stroke-width="2.2" />

    <!-- Top and bottom ellipses -->
    <ellipse cx="{cx}" cy="40" rx="{top_w}" ry="{top_h}" fill="{fill}" stroke="{c_h}" stroke-width="2" />
    <ellipse cx="{cx}" cy="240" rx="{top_w}" ry="{top_h}" fill="{fill}" stroke="{c_h}" stroke-width="2" />

    <!-- Ruled lines -->
    <line x1="{cx - top_w + 30}" y1="40" x2="{cx + top_w - 15}" y2="240" stroke="{c_h}" stroke-width="1" stroke-opacity="0.6" />
    <line x1="{cx + top_w - 30}" y1="40" x2="{cx - top_w + 15}" y2="240" stroke="{c_h}" stroke-width="1" stroke-opacity="0.6" />
    <text x="180" y="275" font-size="12" fill="#475569">x²/a² + y²/b² − z²/c² = 1 (单叶双曲面)</text>
    """
    return _svg_wrap("0 0 360 290", body, colorful)


def generate_fig_15(colorful: bool = False) -> str:
    """Fig 15: Hyperboloid of two sheets."""
    c_h = "#0f172a" if not colorful else "#7c3aed"
    fill = "url(#purple-grad)" if colorful else "none"

    cx = 180
    body = f"""
    <!-- Upper sheet -->
    <path d="M 110 40 Q 180 110 250 40" fill="{fill}" stroke="{c_h}" stroke-width="2.2" />
    <ellipse cx="{cx}" cy="40" rx="70" ry="18" fill="{fill}" stroke="{c_h}" stroke-width="1.8" />
    <circle cx="{cx}" cy="105" r="3.5" fill="#e11d48" />
    <text x="{cx + 15}" y="105" font-size="11" fill="#e11d48">c</text>

    <!-- Lower sheet -->
    <path d="M 110 240 Q 180 170 250 240" fill="{fill}" stroke="{c_h}" stroke-width="2.2" />
    <ellipse cx="{cx}" cy="240" rx="70" ry="18" fill="{fill}" stroke="{c_h}" stroke-width="1.8" />
    <circle cx="{cx}" cy="175" r="3.5" fill="#e11d48" />
    <text x="{cx + 15}" y="175" font-size="11" fill="#e11d48">−c</text>

    <text x="180" y="275" font-size="12" fill="#475569">x²/a² − y²/b² − z²/c² = 1 (双叶双曲面)</text>
    """
    return _svg_wrap("0 0 360 290", body, colorful)


def generate_fig_16(colorful: bool = False) -> str:
    """Fig 16: Elliptic paraboloid."""
    c_p = "#0f172a" if not colorful else "#2563eb"
    fill = "url(#blue-grad)" if colorful else "none"

    cx = 180
    body = f"""
    <!-- Parabolic profile -->
    <path d="M 100 60 Q 180 230 260 60" fill="{fill}" stroke="{c_p}" stroke-width="2.4" />
    <!-- Elliptic top rim -->
    <ellipse cx="{cx}" cy="60" rx="80" ry="22" fill="{fill}" stroke="{c_p}" stroke-width="2" />
    <!-- Internal ellipse contour -->
    <path d="M 130 140 A 50 14 0 0 0 230 140" fill="none" stroke="{c_p}" stroke-width="1.2" stroke-dasharray="3 3" />

    <!-- Vertex -->
    <circle cx="{cx}" cy="225" r="4.5" fill="#e11d48" />
    <text x="{cx}" y="245" font-size="12" fill="#e11d48">顶点 O</text>
    <text x="180" y="270" font-size="12" fill="#475569">z = x²/a² + y²/b² (椭圆抛物面)</text>
    """
    return _svg_wrap("0 0 360 290", body, colorful)


def generate_fig_17(colorful: bool = False) -> str:
    """Fig 17: Hyperbolic paraboloid (saddle surface)."""
    c_s = "#0f172a" if not colorful else "#d97706"
    fill = "url(#amber-grad)" if colorful else "none"

    body = f"""
    <!-- Saddle shape -->
    <path d="M 80 100 Q 180 180 280 100 L 250 200 Q 180 130 110 200 Z" fill="{fill}" stroke="{c_s}" stroke-width="2" />
    <!-- Central saddle parabolas -->
    <path d="M 120 70 Q 180 170 240 70" fill="none" stroke="{c_s}" stroke-width="2" />
    <path d="M 180 145 Q 180 190 180 230" fill="none" stroke="#e11d48" stroke-width="1.5" stroke-dasharray="3 3" />

    <circle cx="180" cy="145" r="4.5" fill="#e11d48" />
    <text x="180" y="130" font-weight="bold" fill="#e11d48">马鞍点</text>
    <text x="180" y="260" font-size="12" fill="#475569">z = x²/a² − y²/b² (双曲抛物面)</text>
    """
    return _svg_wrap("0 0 360 280", body, colorful)


def generate_fig_18(colorful: bool = False) -> str:
    """Fig 18: Projective plane RP^2 sphere model with antipodal identification."""
    c_s = "#0f172a" if not colorful else "#2563eb"
    c_pt = "#e11d48"
    fill = "url(#blue-grad)" if colorful else "none"

    cx, cy = 180, 140
    r = 85

    body = f"""
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{c_s}" stroke-width="2.2" />
    <!-- Equator ellipse -->
    <ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="24" fill="none" stroke="{c_s}" stroke-width="1.2" stroke-dasharray="4 3" />

    <!-- Antipodal pair t and t' -->
    <line x1="{cx - 65}" y1="{cy - 50}" x2="{cx + 65}" y2="{cy + 50}" stroke="{c_pt}" stroke-width="1.8" stroke-dasharray="4 3" />
    <circle cx="{cx - 65}" cy="{cy - 50}" r="5" fill="{c_pt}" />
    <text x="{cx - 80}" y="{cy - 55}" font-weight="bold" fill="{c_pt}">t</text>

    <circle cx="{cx + 65}" cy="{cy + 50}" r="5" fill="{c_pt}" />
    <text x="{cx + 80}" y="{cy + 55}" font-weight="bold" fill="{c_pt}">t′</text>

    <text x="180" y="260" font-size="12" fill="#475569">S² 径对点对等同: t ↔ t′</text>
    """
    return _svg_wrap("0 0 360 280", body, colorful)


def generate_fig_19(colorful: bool = False) -> str:
    """Fig 19: Lower hemisphere model S^2_- with boundary rim."""
    c_h = "#0f172a" if not colorful else "#0891b2"
    fill = "url(#teal-grad)" if colorful else "none"

    cx, cy = 180, 100
    r = 85

    body = f"""
    <!-- Lower hemisphere -->
    <path d="M {cx - r} {cy} A {r} {r} 0 0 0 {cx + r} {cy}" fill="{fill}" stroke="{c_h}" stroke-width="2.4" />
    <!-- Boundary circle S^1 at z = 0 -->
    <ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="25" fill="{fill}" stroke="{c_h}" stroke-width="2" />

    <!-- Orientation arrows on rim -->
    <text x="{cx}" y="{cy - 5}" font-size="12" fill="{c_h}">S¹ (z = 0)</text>
    <text x="180" y="235" font-size="12" fill="#475569">下半球面 S²₋ : x² + y² + z² = 1, z ⩽ 0</text>
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_20(colorful: bool = False) -> str:
    """Fig 20: Projective line RP^1 as pencil of lines through o and tangent circle S^1."""
    c_l = "#64748b" if not colorful else "#94a3b8"
    c_circ = "#0f172a" if not colorful else "#2563eb"
    fill = "url(#blue-grad)" if colorful else "none"

    ox, oy = 180, 200
    r = 60
    ccy = oy - r

    body = f"""
    <!-- Circle S^1 tangent at o -->
    <circle cx="{ox}" cy="{ccy}" r="{r}" fill="{fill}" stroke="{c_circ}" stroke-width="2.2" />

    <!-- Pencil of lines through o -->
    <line x1="60" y1="200" x2="300" y2="200" stroke="{c_l}" stroke-width="1.8" />
    <line x1="80" y1="250" x2="280" y2="30" stroke="{c_l}" stroke-width="1.8" />
    <line x1="180" y1="250" x2="180" y2="30" stroke="{c_l}" stroke-width="1.8" />
    <line x1="280" y1="250" x2="80" y2="30" stroke="{c_l}" stroke-width="1.8" />

    <!-- Tangent point o -->
    <circle cx="{ox}" cy="{oy}" r="5" fill="#e11d48" />
    <text x="{ox - 15}" y="{oy + 18}" font-weight="bold" fill="#e11d48">o</text>
    <text x="{ox + r + 15}" y="{ccy}" fill="{c_circ}">S¹</text>
    <text x="180" y="255" font-size="12" fill="#475569">经过固定点 o 的直线束 ≅ 射影直线 ℝℙ¹</text>
    """
    return _svg_wrap("0 0 360 270", body, colorful)


def generate_fig_21(colorful: bool = False) -> str:
    """Fig 21: Fano plane P^2(F_2) with 7 points and 7 lines."""
    c_line = "#0f172a" if not colorful else "#2563eb"
    c_circ = "#059669" if colorful else "#0f172a"
    c_pt = "#e11d48" if colorful else "#0f172a"

    # Equilateral triangle vertices
    p1 = (180, 40)
    p2 = (60, 240)
    p3 = (300, 240)
    # Midpoints
    m12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    m23 = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
    m31 = ((p3[0] + p1[0]) / 2, (p3[1] + p1[1]) / 2)
    # Center
    center = (180, 173)

    body = f"""
    <!-- Triangle edges -->
    <polygon points="{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]}" fill="none" stroke="{c_line}" stroke-width="2.2" />

    <!-- Medians -->
    <line x1="{p1[0]}" y1="{p1[1]}" x2="{m23[0]}" y2="{m23[1]}" stroke="{c_line}" stroke-width="1.8" />
    <line x1="{p2[0]}" y1="{p2[1]}" x2="{m31[0]}" y2="{m31[1]}" stroke="{c_line}" stroke-width="1.8" />
    <line x1="{p3[0]}" y1="{p3[1]}" x2="{m12[0]}" y2="{m12[1]}" stroke="{c_line}" stroke-width="1.8" />

    <!-- Inscribed circle line -->
    <circle cx="{center[0]}" cy="{center[1]}" r="67" fill="none" stroke="{c_circ}" stroke-width="2" />

    <!-- 7 Points -->
    <circle cx="{p1[0]}" cy="{p1[1]}" r="5.5" fill="{c_pt}" />
    <text x="{p1[0]}" y="{p1[1] - 14}" font-weight="bold">1</text>

    <circle cx="{p2[0]}" cy="{p2[1]}" r="5.5" fill="{c_pt}" />
    <text x="{p2[0] - 15}" y="{p2[1] + 10}" font-weight="bold">2</text>

    <circle cx="{p3[0]}" cy="{p3[1]}" r="5.5" fill="{c_pt}" />
    <text x="{p3[0] + 15}" y="{p3[1] + 10}" font-weight="bold">3</text>

    <circle cx="{m12[0]}" cy="{m12[1]}" r="5" fill="{c_pt}" />
    <text x="{m12[0] - 18}" y="{m12[1] - 5}" font-weight="bold">6</text>

    <circle cx="{m23[0]}" cy="{m23[1]}" r="5" fill="{c_pt}" />
    <text x="{m23[0]}" y="{m23[1] + 18}" font-weight="bold">4</text>

    <circle cx="{m31[0]}" cy="{m31[1]}" r="5" fill="{c_pt}" />
    <text x="{m31[0] + 18}" y="{m31[1] - 5}" font-weight="bold">5</text>

    <circle cx="{center[0]}" cy="{center[1]}" r="5.5" fill="{c_pt}" />
    <text x="{center[0] + 16}" y="{center[1] + 5}" font-weight="bold">7</text>

    <text x="180" y="275" font-size="12" fill="#475569">法诺平面 ℙ²(𝔽₂) : 7个点, 7条线</text>
    """
    return _svg_wrap("0 0 360 290", body, colorful)


def generate_fig_22(colorful: bool = False) -> str:
    """Fig 22: Three intersecting circles representing Fano coordinates x_1...x_7."""
    c_c1 = "#2563eb" if colorful else "#0f172a"
    c_c2 = "#e11d48" if colorful else "#334155"
    c_c3 = "#059669" if colorful else "#475569"

    c1 = (145, 120)
    c2 = (215, 120)
    c3 = (180, 180)
    r = 65

    body = f"""
    <circle cx="{c1[0]}" cy="{c1[1]}" r="{r}" fill="none" stroke="{c_c1}" stroke-width="2.2" />
    <circle cx="{c2[0]}" cy="{c2[1]}" r="{r}" fill="none" stroke="{c_c2}" stroke-width="2.2" />
    <circle cx="{c3[0]}" cy="{c3[1]}" r="{r}" fill="none" stroke="{c_c3}" stroke-width="2.2" />

    <!-- 7 Venn regions -->
    <text x="110" y="100" font-weight="bold" fill="{c_c1}">x₁</text>
    <text x="250" y="100" font-weight="bold" fill="{c_c2}">x₂</text>
    <text x="180" y="220" font-weight="bold" fill="{c_c3}">x₃</text>

    <text x="180" y="100" font-weight="bold">x₄</text>
    <text x="140" y="165" font-weight="bold">x₅</text>
    <text x="220" y="165" font-weight="bold">x₆</text>
    <text x="180" y="145" font-weight="bold" fill="#d97706">x₇</text>
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_23(colorful: bool = False) -> str:
    """Fig 23: Linear programming feasible polygon and objective gradient."""
    c_poly = "#0f172a" if not colorful else "#059669"
    c_grad = "#e11d48" if colorful else "#0f172a"
    arr_g = "arr" if not colorful else "arr-coral"
    fill = "url(#teal-grad)" if colorful else "none"

    body = f"""
    <!-- Coordinate axes -->
    <line x1="40" y1="230" x2="330" y2="230" stroke="#64748b" stroke-width="1.2" marker-end="url(#arr)" />
    <line x1="60" y1="250" x2="60" y2="30" stroke="#64748b" stroke-width="1.2" marker-end="url(#arr)" />

    <!-- Feasible convex polygon -->
    <polygon points="60,230 60,110 140,70 240,120 220,230" fill="{fill}" stroke="{c_poly}" stroke-width="2.4" />

    <!-- Vertices -->
    <circle cx="60" cy="110" r="4.5" fill="{c_poly}" />
    <text x="45" y="105" font-weight="bold">A</text>

    <circle cx="140" cy="70" r="4.5" fill="{c_poly}" />
    <text x="140" y="55" font-weight="bold">B (最优解)</text>

    <circle cx="240" cy="120" r="4.5" fill="{c_poly}" />
    <text x="255" y="115" font-weight="bold">C</text>

    <circle cx="220" cy="230" r="4.5" fill="{c_poly}" />
    <text x="235" y="240" font-weight="bold">D</text>

    <!-- Objective function gradient arrow -->
    <line x1="120" y1="170" x2="160" y2="105" stroke="{c_grad}" stroke-width="2.6" marker-end="url(#{arr_g})" />
    <text x="185" y="130" font-weight="bold" fill="{c_grad}">∇f</text>
    <text x="190" y="270" font-size="12" fill="#475569">线性规划可行域与极值点</text>
    """
    return _svg_wrap("0 0 360 290", body, colorful)


def generate_fig_24(colorful: bool = False) -> str:
    """Fig 24: Klein disk model of hyperbolic geometry with coordinate chords."""
    c_disk = "#0f172a" if not colorful else "#2563eb"
    c_chord = "#0f172a" if not colorful else "#0891b2"
    fill = "url(#blue-grad)" if colorful else "none"

    cx, cy = 180, 140
    r = 95

    body = f"""
    <!-- Absolute boundary circle -->
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{c_disk}" stroke-width="2.6" />

    <!-- Orthogonal coordinate chords through center -->
    <line x1="{cx - r}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="{c_chord}" stroke-width="1.8" />
    <line x1="{cx}" y1="{cy - r}" x2="{cx}" y2="{cy + r}" stroke="{c_chord}" stroke-width="1.8" />

    <!-- Center e_0 -->
    <circle cx="{cx}" cy="{cy}" r="5" fill="#e11d48" />
    <text x="{cx + 15}" y="{cy + 15}" font-weight="bold" fill="#e11d48">e₀</text>

    <!-- Basis vectors on chords -->
    <circle cx="{cx + 50}" cy="{cy}" r="3.5" fill="{c_disk}" />
    <text x="{cx + 50}" y="{cy - 12}" fill="{c_disk}">e₁</text>
    <circle cx="{cx}" cy="{cy - 50}" r="3.5" fill="{c_disk}" />
    <text x="{cx + 15}" y="{cy - 50}" fill="{c_disk}">e₂</text>

    <text x="180" y="265" font-size="12" fill="#475569">克莱因模型 Φ₀(Λ̃) ≅ 开单位球</text>
    """
    return _svg_wrap("0 0 360 280", body, colorful)


def generate_fig_25(colorful: bool = False) -> str:
    """Fig 25: Hyperbolic chord l and perpendicular h from center e."""
    c_disk = "#64748b" if not colorful else "#94a3b8"
    c_chord = "#0f172a" if not colorful else "#2563eb"
    c_perp = "#e11d48"

    cx, cy = 180, 140
    r = 90

    # Chord l: horizontal at y = cy + 40
    chord_y = cy + 40
    dx = math.sqrt(r*r - 40*40)

    body = f"""
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c_disk}" stroke-width="2" />
    <text x="{cx + r - 15}" y="{cy - r + 20}" fill="{c_disk}">Λ</text>

    <!-- Center e -->
    <circle cx="{cx}" cy="{cy}" r="4.5" fill="#0f172a" />
    <text x="{cx - 15}" y="{cy - 5}" font-weight="bold">e</text>

    <!-- Chord l -->
    <line x1="{cx - dx}" y1="{chord_y}" x2="{cx + dx}" y2="{chord_y}" stroke="{c_chord}" stroke-width="2.4" />
    <text x="{cx + dx + 15}" y="{chord_y + 5}" font-weight="bold" fill="{c_chord}">l</text>

    <!-- Perpendicular h -->
    <line x1="{cx}" y1="{cy}" x2="{cx}" y2="{chord_y}" stroke="{c_perp}" stroke-width="2.2" />
    <text x="{cx + 15}" y="{cy + 20}" font-weight="bold" fill="{c_perp}">h</text>
    <!-- Right angle square -->
    <rect x="{cx}" y="{chord_y - 12}" width="12" height="12" fill="none" stroke="{c_perp}" stroke-width="1.2" />
    """
    return _svg_wrap("0 0 360 270", body, colorful)


def generate_fig_26(colorful: bool = False) -> str:
    """Fig 26: Failure of parallel postulate in hyperbolic geometry."""
    c_disk = "#64748b" if not colorful else "#94a3b8"
    c_line = "#0f172a" if not colorful else "#2563eb"
    c_p = "#e11d48"
    c_ray = "#d97706" if colorful else "#475569"

    cx, cy = 180, 140
    r = 90
    px, py = 180, 85

    body = f"""
    <!-- Disk boundary -->
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c_disk}" stroke-width="2" />

    <!-- Line l (horizontal chord at bottom) -->
    <line x1="{cx - 75}" y1="190" x2="{cx + 75}" y2="190" stroke="{c_line}" stroke-width="2.4" />
    <text x="{cx + 90}" y="195" font-weight="bold" fill="{c_line}">l</text>

    <!-- External point p -->
    <circle cx="{px}" cy="{py}" r="5" fill="{c_p}" />
    <text x="{px}" y="{py - 14}" font-weight="bold" fill="{c_p}">p</text>

    <!-- Limiting parallel rays to endpoints of l -->
    <line x1="{px}" y1="{py}" x2="{cx - 75}" y2="190" stroke="{c_ray}" stroke-width="1.8" stroke-dasharray="4 3" />
    <line x1="{px}" y1="{py}" x2="{cx + 75}" y2="190" stroke="{c_ray}" stroke-width="1.8" stroke-dasharray="4 3" />

    <!-- Multiple non-intersecting lines through p -->
    <line x1="105" y1="95" x2="255" y2="75" stroke="{c_line}" stroke-width="1.8" />
    <line x1="110" y1="75" x2="250" y2="95" stroke="{c_line}" stroke-width="1.8" />
    <text x="180" y="260" font-size="12" fill="#475569">经过 p 有无数条与 l 不相交的平行线</text>
    """
    return _svg_wrap("0 0 360 280", body, colorful)


def generate_fig_27(colorful: bool = False) -> str:
    """Fig 27: Hyperbolic Lambert / Saccheri quadrilateral."""
    c_quad = "#0f172a" if not colorful else "#2563eb"
    fill = "url(#blue-grad)" if colorful else "none"

    body = f"""
    <!-- Quadrilateral O-A-B-C with 3 right angles and 1 acute angle -->
    <polygon points="80,210 240,210 210,90 80,90" fill="{fill}" stroke="{c_quad}" stroke-width="2.4" />

    <!-- Right angle symbols at O, A, C -->
    <rect x="80" y="195" width="15" height="15" fill="none" stroke="{c_quad}" stroke-width="1.2" />
    <rect x="80" y="90" width="15" height="15" fill="none" stroke="{c_quad}" stroke-width="1.2" />
    <path d="M 225 210 L 225 198 L 240 198" fill="none" stroke="{c_quad}" stroke-width="1.2" />

    <!-- Acute angle at B -->
    <path d="M 195 90 A 20 20 0 0 1 204 105" fill="none" stroke="#e11d48" stroke-width="1.8" />
    <text x="185" y="112" font-size="12" fill="#e11d48">&lt; 90°</text>

    <!-- Vertex labels -->
    <text x="65" y="220" font-weight="bold">O</text>
    <text x="255" y="220" font-weight="bold">A</text>
    <text x="220" y="80" font-weight="bold">B</text>
    <text x="65" y="85" font-weight="bold">C</text>
    <text x="160" y="245" font-size="12" fill="#475569">兰伯特四边形: 内角和 &lt; 360°</text>
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_28(colorful: bool = False) -> str:
    """Fig 28: Hyperbolic triangle cannot have two obtuse angles."""
    c_tri = "#0f172a" if not colorful else "#e11d48"
    fill = "url(#rose-grad)" if colorful else "none"

    body = f"""
    <polygon points="60,180 300,180 180,60" fill="{fill}" stroke="{c_tri}" stroke-width="2.2" stroke-linejoin="round" />

    <!-- Angle arcs -->
    <path d="M 100 180 A 40 40 0 0 1 85 145" fill="none" stroke="{c_tri}" stroke-width="1.6" />
    <text x="110" y="160" font-size="13">α</text>

    <path d="M 260 180 A 40 40 0 0 0 275 145" fill="none" stroke="{c_tri}" stroke-width="1.6" />
    <text x="250" y="160" font-size="13">β</text>

    <text x="50" y="195" font-weight="bold">A</text>
    <text x="310" y="195" font-weight="bold">B</text>
    <text x="180" y="45" font-weight="bold">C</text>

    <text x="180" y="220" font-size="12" fill="#475569">罗巴切夫斯基几何中: α + β + γ &lt; π (不能有两个钝角)</text>
    """
    return _svg_wrap("0 0 360 240", body, colorful)


def generate_fig_29(colorful: bool = False) -> str:
    """Fig 29: Hyperbolic triangle altitude CD and angle defect."""
    c_tri = "#0f172a" if not colorful else "#2563eb"
    c_alt = "#e11d48"
    fill = "url(#blue-grad)" if colorful else "none"

    ax, ay = 60, 200
    bx, by = 300, 200
    cx, cy = 170, 60
    dx, dy = 170, 200

    body = f"""
    <polygon points="{ax},{ay} {bx},{by} {cx},{cy}" fill="{fill}" stroke="{c_tri}" stroke-width="2.4" />
    <!-- Altitude CD -->
    <line x1="{cx}" y1="{cy}" x2="{dx}" y2="{dy}" stroke="{c_alt}" stroke-width="2" stroke-dasharray="4 3" />
    <rect x="{dx}" y="{dy - 14}" width="14" height="14" fill="none" stroke="{c_alt}" stroke-width="1.2" />

    <circle cx="{ax}" cy="{ay}" r="4" fill="{c_tri}" />
    <text x="{ax - 15}" y="{ay + 5}" font-weight="bold">A</text>

    <circle cx="{bx}" cy="{by}" r="4" fill="{c_tri}" />
    <text x="{bx + 15}" y="{by + 5}" font-weight="bold">B</text>

    <circle cx="{cx}" cy="{cy}" r="4" fill="{c_tri}" />
    <text x="{cx}" y="{cy - 15}" font-weight="bold">C</text>

    <circle cx="{dx}" cy="{dy}" r="4" fill="{c_alt}" />
    <text x="{dx}" y="{dy + 18}" font-weight="bold" fill="{c_alt}">D</text>

    <text x="180" y="245" font-size="12" fill="#475569">垂线 CD 将高斯缺陷分解: δ(ABC) = δ(ACD) + δ(BCD)</text>
    """
    return _svg_wrap("0 0 360 260", body, colorful)


def generate_fig_30(colorful: bool = False) -> str:
    """Fig 30: Rigid hyperbolic motion aligning triangle A'B'C' to ABC."""
    c_t1 = "#0f172a" if not colorful else "#2563eb"
    c_t2 = "#475569" if not colorful else "#d97706"
    fill1 = "url(#blue-grad)" if colorful else "none"

    body = f"""
    <!-- Triangle ABC -->
    <polygon points="70,210 290,210 180,80" fill="{fill1}" stroke="{c_t1}" stroke-width="2.4" />
    <!-- Triangle A'B'C' overlaid along edge AB and AC -->
    <polygon points="70,210 240,210 150,110" fill="none" stroke="{c_t2}" stroke-width="2" stroke-dasharray="4 3" />

    <text x="50" y="220" font-weight="bold">A = A′</text>
    <text x="295" y="225" font-weight="bold" fill="{c_t1}">B</text>
    <text x="240" y="230" font-weight="bold" fill="{c_t2}">B′</text>
    <text x="185" y="65" font-weight="bold" fill="{c_t1}">C</text>
    <text x="140" y="100" font-weight="bold" fill="{c_t2}">C′</text>
    """
    return _svg_wrap("0 0 360 250", body, colorful)


def generate_fig_31(colorful: bool = False) -> str:
    """Fig 31: Nested hyperbolic triangles and defect/area comparison."""
    c_t1 = "#0f172a" if not colorful else "#2563eb"
    c_t2 = "#e11d48"
    fill1 = "url(#blue-grad)" if colorful else "none"
    fill2 = "url(#rose-grad)" if colorful else "none"

    body = f"""
    <!-- Outer triangle A'B'C' -->
    <polygon points="50,220 310,220 180,50" fill="{fill1}" stroke="{c_t1}" stroke-width="2" />

    <!-- Inner triangle ABC -->
    <polygon points="90,190 260,190 170,100" fill="{fill2}" stroke="{c_t2}" stroke-width="2.2" />

    <text x="180" y="160" font-weight="bold" fill="{c_t2}">ΔABC</text>
    <text x="180" y="75" font-weight="bold" fill="{c_t1}">ΔA′B′C′</text>

    <!-- Quadrilateral / defect complement M -->
    <text x="180" y="208" font-size="11" fill="#475569">M</text>
    <text x="180" y="250" font-size="12" fill="#475569">双曲面积正比于角缺陷: 面积 = k(π − α − β − γ)</text>
    """
    return _svg_wrap("0 0 360 270", body, colorful)


# =========================================================================
# Dispatch Registry
# =========================================================================

FIGURE_GENERATORS: dict[int, Callable[[bool], str]] = {
    1: generate_fig_1,
    2: generate_fig_2,
    3: generate_fig_3,
    4: generate_fig_4,
    5: generate_fig_5,
    6: generate_fig_6,
    7: generate_fig_7,
    8: generate_fig_8,
    9: generate_fig_9,
    10: generate_fig_10,
    11: generate_fig_11,
    12: generate_fig_12,
    13: generate_fig_13,
    14: generate_fig_14,
    15: generate_fig_15,
    16: generate_fig_16,
    17: generate_fig_17,
    18: generate_fig_18,
    19: generate_fig_19,
    20: generate_fig_20,
    21: generate_fig_21,
    22: generate_fig_22,
    23: generate_fig_23,
    24: generate_fig_24,
    25: generate_fig_25,
    26: generate_fig_26,
    27: generate_fig_27,
    28: generate_fig_28,
    29: generate_fig_29,
    30: generate_fig_30,
    31: generate_fig_31,
}


def generate_all_algebra2_figures(out_dir_mono: Path, out_dir_color: Path) -> None:
    """Generate both monochrome and colorful 3b1b-style figures as SVG and 300-DPI PNG."""
    out_dir_mono.mkdir(parents=True, exist_ok=True)
    out_dir_color.mkdir(parents=True, exist_ok=True)

    for fid, gen in sorted(FIGURE_GENERATORS.items()):
        # 1. Monochrome / Black-and-white
        svg_mono = gen(False)
        mono_svg_path = out_dir_mono / f"fig_{fid}.svg"
        mono_png_path = out_dir_mono / f"fig_{fid}.png"
        _ = mono_svg_path.write_text(svg_mono, encoding="utf-8")
        with pymupdf.open("svg", svg_mono.encode("utf-8")) as doc:
            doc[0].get_pixmap(dpi=300).save(mono_png_path)

        # 2. Colorful 3Blue1Brown aesthetic
        svg_color = gen(True)
        color_svg_path = out_dir_color / f"fig_{fid}.svg"
        color_png_path = out_dir_color / f"fig_{fid}.png"
        _ = color_svg_path.write_text(svg_color, encoding="utf-8")
        with pymupdf.open("svg", svg_color.encode("utf-8")) as doc:
            doc[0].get_pixmap(dpi=300).save(color_png_path)

    print(f"Generated {len(FIGURE_GENERATORS)} figures in monochrome -> {out_dir_mono}")
    print(f"Generated {len(FIGURE_GENERATORS)} figures in 3b1b color -> {out_dir_color}")


if __name__ == "__main__":
    base_out = Path("output/algebra2")
    generate_all_algebra2_figures(base_out / "figures", base_out / "figures_color")
