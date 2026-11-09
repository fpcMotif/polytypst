"""3Blue1Brown-styled parametric vector geometric illustrations for Michael Spivak:
A Comprehensive Introduction to Differential Geometry, Vol. 3.

Provides both:
1. Monochrome mode: Crisp, elegant publication-quality black-and-white vector graphics (#0f172a, fine strokes, clean hatching).
2. 3Blue1Brown Colorful mode: Vibrant pedagogical color palette (3b1b blue, amber/gold, teal, rose/coral, emerald, violet)
   with soft gradient fills, radial illumination, glowing curves, and math typography.

All figures render as scalable SVGs and compile to 300-DPI PNGs for Typst and LaTeX inclusion.
"""

import math
from collections.abc import Callable
from pathlib import Path

import pymupdf


def _marker_defs(colorful: bool) -> str:
    if not colorful:
        return """
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#0f172a" />
    </marker>
    <marker id="arr-axis" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#334155" />
    </marker>
    <pattern id="hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#475569" stroke-width="1.1" />
    </pattern>
"""
    return """
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#1e293b" />
    </marker>
    <marker id="arr-axis" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#475569" />
    </marker>
    <marker id="arr-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#2563eb" />
    </marker>
    <marker id="arr-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#d97706" />
    </marker>
    <marker id="arr-rose" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#e11d48" />
    </marker>
    <marker id="arr-teal" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#0891b2" />
    </marker>
    <marker id="arr-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#059669" />
    </marker>
    <linearGradient id="blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.30" />
      <stop offset="100%" stop-color="#1d4ed8" stop-opacity="0.08" />
    </linearGradient>
    <linearGradient id="amber-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#d97706" stop-opacity="0.10" />
    </linearGradient>
    <linearGradient id="teal-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.30" />
      <stop offset="100%" stop-color="#0891b2" stop-opacity="0.08" />
    </linearGradient>
    <linearGradient id="rose-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e" stop-opacity="0.30" />
      <stop offset="100%" stop-color="#be123c" stop-opacity="0.08" />
    </linearGradient>
    <radialGradient id="sphere-glow" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#f0f9ff" stop-opacity="0.95" />
      <stop offset="55%" stop-color="#bae6fd" stop-opacity="0.75" />
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.35" />
    </radialGradient>
    <pattern id="hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
    </pattern>
"""


def _svg_wrap(viewbox: str, content: str, colorful: bool) -> str:
    defs = _marker_defs(colorful)
    font_family = '"New Computer Modern", "Latin Modern Math", "STIX Two Math", "Times New Roman", serif'
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
# Figure 1: Dupin Indicatrix of an Elliptic Point (p. 53, 58)
# =========================================================================

def generate_fig_dupin_elliptic(colorful: bool = False) -> str:
    """Dupin Indicatrix for an elliptic point (k1, k2 > 0)."""
    c_axis = "#475569" if not colorful else "#64748b"
    c_curve = "#0f172a" if not colorful else "#2563eb"
    c_fill = "none" if not colorful else "url(#blue-grad)"
    c_vec = "#0f172a" if not colorful else "#d97706"
    arr_axis = 'marker-end="url(#arr-axis)"'
    arr_vec = 'marker-end="url(#arr)"' if not colorful else 'marker-end="url(#arr-amber)"'

    body = f"""
    <!-- Coordinate axes -->
    <line x1="60" y1="180" x2="380" y2="180" stroke="{c_axis}" stroke-width="1.3" {arr_axis} />
    <line x1="220" y1="300" x2="220" y2="60" stroke="{c_axis}" stroke-width="1.3" {arr_axis} />
    <text x="395" y="180" fill="{c_axis}" font-style="italic">X₁</text>
    <text x="220" y="45" fill="{c_axis}" font-style="italic">X₂</text>
    
    <!-- Dupin Ellipse: k1 x^2 + k2 y^2 = 1 -->
    <ellipse cx="220" cy="180" rx="120" ry="75" fill="{c_fill}" stroke="{c_curve}" stroke-width="2.2" />
    
    <!-- Principal axes markers -->
    <circle cx="340" cy="180" r="3.5" fill="{c_curve}" />
    <circle cx="100" cy="180" r="3.5" fill="{c_curve}" />
    <circle cx="220" cy="105" r="3.5" fill="{c_curve}" />
    <circle cx="220" cy="255" r="3.5" fill="{c_curve}" />
    
    <text x="340" y="200" font-size="12" fill="{c_axis}">1/√k₁</text>
    <text x="190" y="105" font-size="12" fill="{c_axis}">1/√k₂</text>
    
    <!-- Direction vector X at angle theta -->
    <line x1="220" y1="180" x2="305" y2="128" stroke="{c_vec}" stroke-width="1.8" {arr_vec} />
    <text x="325" y="125" font-size="13" font-style="italic" fill="{c_vec}">X(θ)</text>
    
    <!-- Angle arc theta -->
    <path d="M 255 180 A 35 35 0 0 0 249 162" fill="none" stroke="{c_axis}" stroke-width="1.1" />
    <text x="265" y="170" font-size="11" fill="{c_axis}">θ</text>
    
    <!-- Equation label -->
    <text x="220" y="325" font-size="13" fill="#0f172a">k₁x² + k₂y² = 1  (k₁, k₂ > 0)</text>
"""
    return _svg_wrap("0 0 440 350", body, colorful)


# =========================================================================
# Figure 2: Dupin Indicatrix of a Hyperbolic Point (p. 50, 59)
# =========================================================================

def generate_fig_dupin_hyperbolic(colorful: bool = False) -> str:
    """Dupin Indicatrix for a hyperbolic point (k1 > 0 > k2) with asymptotic lines."""
    c_axis = "#475569" if not colorful else "#64748b"
    c_pos = "#0f172a" if not colorful else "#2563eb"
    c_neg = "#0f172a" if not colorful else "#e11d48"
    c_asymp = "#64748b" if not colorful else "#d97706"
    arr_axis = 'marker-end="url(#arr-axis)"'

    # Asymptotic lines y = +/- (75/100) x, through (220, 180)
    # Hyperbola branches: x = 100 cosh t, y = 75 sinh t
    path_pos_r = "M 320 180 C 320 220 360 260 400 280 M 320 180 C 320 140 360 100 400 80"
    path_pos_l = "M 120 180 C 120 220 80 260 40 280 M 120 180 C 120 140 80 100 40 80"
    path_neg_t = "M 220 105 C 260 105 320 75 360 40 M 220 105 C 180 105 120 75 80 40"
    path_neg_b = "M 220 255 C 260 255 320 285 360 320 M 220 255 C 180 255 120 285 80 320"

    dash_neg = 'stroke-dasharray="4,3"' if not colorful else ""

    body = f"""
    <!-- Coordinate axes -->
    <line x1="40" y1="180" x2="400" y2="180" stroke="{c_axis}" stroke-width="1.2" {arr_axis} />
    <line x1="220" y1="330" x2="220" y2="30" stroke="{c_axis}" stroke-width="1.2" {arr_axis} />
    <text x="415" y="180" fill="{c_axis}" font-style="italic">X₁</text>
    <text x="220" y="18" fill="{c_axis}" font-style="italic">X₂</text>
    
    <!-- Asymptotes -->
    <line x1="60" y1="60" x2="380" y2="300" stroke="{c_asymp}" stroke-width="1.3" stroke-dasharray="6,4" />
    <line x1="60" y1="300" x2="380" y2="60" stroke="{c_asymp}" stroke-width="1.3" stroke-dasharray="6,4" />
    <text x="385" y="315" font-size="11" fill="{c_asymp}">Asymptote</text>
    
    <!-- Positive branches k1 x^2 - |k2| y^2 = +1 -->
    <path d="{path_pos_r}" fill="none" stroke="{c_pos}" stroke-width="2.2" />
    <path d="{path_pos_l}" fill="none" stroke="{c_pos}" stroke-width="2.2" />
    
    <!-- Negative branches k1 x^2 - |k2| y^2 = -1 -->
    <path d="{path_neg_t}" fill="none" stroke="{c_neg}" stroke-width="2.2" {dash_neg} />
    <path d="{path_neg_b}" fill="none" stroke="{c_neg}" stroke-width="2.2" {dash_neg} />
    
    <text x="335" y="165" font-size="12" fill="{c_pos}">+1</text>
    <text x="238" y="95" font-size="12" fill="{c_neg}">-1</text>
    <text x="220" y="348" font-size="13" fill="#0f172a">k₁x² + k₂y² = ±1  (k₁ > 0 > k₂)</text>
"""
    return _svg_wrap("0 0 440 370", body, colorful)


# =========================================================================
# Figure 3: Monkey Saddle Indicatrix (p. 58)
# =========================================================================

def generate_fig_monkey_saddle(colorful: bool = False) -> str:
    """Monkey Saddle Dupin Indicatrix: 3-fold symmetry z = x^3 - 3xy^2."""
    c_axis = "#475569" if not colorful else "#64748b"
    c_pos = "#0f172a" if not colorful else "#2563eb"
    c_neg = "#0f172a" if not colorful else "#f59e0b"
    c_ray = "#94a3b8" if not colorful else "#cbd5e1"
    arr_axis = 'marker-end="url(#arr-axis)"'

    # Build 3 hyperbolic-like branches rotated by 120 deg
    cx, cy = 220, 200
    r = 130
    
    # Generate parametric curves for r^3 cos(3 theta) = +/- 1
    # Angles theta where cos(3 theta) > 0 and < 0
    rays = ""
    for k in range(6):
        ang = k * math.pi / 3
        x2 = cx + (r + 30) * math.cos(ang)
        y2 = cy - (r + 30) * math.sin(ang)
        rays += f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c_ray}" stroke-width="1.0" stroke-dasharray="3,3" />\n'

    # 3 continuous branches (+d) and 3 dashed branches (-d)
    branches = ""
    for k in range(3):
        # Continuous branch centered at 2k * pi / 3
        mid_ang = 2 * k * math.pi / 3
        pts_pos: list[str] = []
        for step in range(-25, 26):
            t = (step / 25.0) * (math.pi / 6 * 0.92)
            theta = mid_ang + t
            val = math.cos(3 * t)
            if val > 0.05:
                rho = float(50.0 / (val ** (1.0 / 3.0)))
                if rho < r + 20:
                    px = float(cx + rho * math.cos(theta))
                    py = float(cy - rho * math.sin(theta))
                    pts_pos.append(f"{px:.1f},{py:.1f}")
        if pts_pos:
            branches += f'<polyline points="{" ".join(pts_pos)}" fill="none" stroke="{c_pos}" stroke-width="2.3" />\n'

        # Dashed branch centered at (2k + 1) * pi / 3
        mid_ang_neg = (2 * k + 1) * math.pi / 3
        pts_neg: list[str] = []
        for step in range(-25, 26):
            t = (step / 25.0) * (math.pi / 6 * 0.92)
            theta = mid_ang_neg + t
            val = -math.cos(3 * (t + math.pi / 3))
            if val > 0.05:
                rho = float(50.0 / (val ** (1.0 / 3.0)))
                if rho < r + 20:
                    px = float(cx + rho * math.cos(theta))
                    py = float(cy - rho * math.sin(theta))
                    pts_neg.append(f"{px:.1f},{py:.1f}")
        if pts_neg:
            dash = 'stroke-dasharray="5,4"' if not colorful else 'stroke-dasharray="6,3"'
            branches += f'<polyline points="{" ".join(pts_neg)}" fill="none" stroke="{c_neg}" stroke-width="2.3" {dash} />\n'

    body = f"""
    <!-- Coordinate axes -->
    <line x1="50" y1="{cy}" x2="390" y2="{cy}" stroke="{c_axis}" stroke-width="1.2" {arr_axis} />
    <line x1="{cx}" y1="360" x2="{cx}" y2="40" stroke="{c_axis}" stroke-width="1.2" {arr_axis} />
    <text x="405" y="{cy}" fill="{c_axis}">x</text>
    <text x="{cx}" y="25" fill="{c_axis}">y</text>
    
    <!-- Asymptotic rays at multiples of 60 deg -->
    {rays}
    
    <!-- 3-fold symmetric cubic curves -->
    {branches}
    
    <!-- Legend -->
    <line x1="90" y1="375" x2="130" y2="375" stroke="{c_pos}" stroke-width="2.2" />
    <text x="180" y="375" font-size="12" fill="{c_pos}">z = +d (solid)</text>
    
    <line x1="260" y1="375" x2="300" y2="375" stroke="{c_neg}" stroke-width="2.2" stroke-dasharray="5,4" />
    <text x="350" y="375" font-size="12" fill="{c_neg}">z = -d (dashed)</text>
"""
    return _svg_wrap("0 0 440 400", body, colorful)


# =========================================================================
# Figure 4: The Gauss Map nu: M -> S^2 (p. 75, 83)
# =========================================================================

def generate_fig_gauss_map(colorful: bool = False) -> str:
    """The Spherical Gauss Normal Map nu: M -> S^2."""
    c_surf = "#0f172a" if not colorful else "#2563eb"
    c_fill_m = "none" if not colorful else "url(#blue-grad)"
    c_sphere_fill = "#f8fafc" if not colorful else "url(#sphere-glow)"
    c_arr = "#0f172a" if not colorful else "#d97706"
    c_vec = "#0f172a" if not colorful else "#e11d48"
    arr_map = 'marker-end="url(#arr)"' if not colorful else 'marker-end="url(#arr-amber)"'
    arr_n = 'marker-end="url(#arr)"' if not colorful else 'marker-end="url(#arr-rose)"'

    body = f"""
    <!-- Surface M on Left -->
    <g transform="translate(20, 20)">
      <path d="M 40 220 Q 90 120 180 150 Q 230 170 240 240 Q 140 270 40 220 Z" 
            fill="{c_fill_m}" stroke="{c_surf}" stroke-width="2.0" />
      <path d="M 70 190 Q 140 160 210 200" fill="none" stroke="{c_surf}" stroke-width="1.0" stroke-dasharray="3,3" />
      <text x="140" y="235" font-size="16" font-style="italic" fill="{c_surf}">M</text>
      
      <!-- Point p and Normal Vector nu(p) -->
      <circle cx="140" cy="165" r="3.5" fill="{c_vec}" />
      <text x="135" y="180" font-size="12" fill="{c_vec}">p</text>
      <line x1="140" y1="165" x2="155" y2="95" stroke="{c_vec}" stroke-width="2.2" {arr_n} />
      <text x="175" y="100" font-size="14" font-style="italic" fill="{c_vec}">ν(p)</text>
    </g>
    
    <!-- Mapping Arrow nu -->
    <path d="M 270 150 Q 320 120 370 145" fill="none" stroke="{c_arr}" stroke-width="2.2" {arr_map} />
    <text x="320" y="115" font-size="18" font-style="italic" fill="{c_arr}">ν</text>
    
    <!-- Unit Sphere S^2 on Right -->
    <g transform="translate(360, 40)">
      <circle cx="120" cy="140" r="85" fill="{c_sphere_fill}" stroke="#334155" stroke-width="1.8" />
      <!-- Equatorial ellipse -->
      <ellipse cx="120" cy="140" rx="85" ry="24" fill="none" stroke="#64748b" stroke-width="1.1" stroke-dasharray="4,3" />
      <path d="M 35 140 A 85 24 0 0 0 205 140" fill="none" stroke="#334155" stroke-width="1.2" />
      
      <!-- Normal vector mapped to point on S^2 -->
      <line x1="120" y1="140" x2="165" y2="78" stroke="{c_vec}" stroke-width="2.2" {arr_n} />
      <circle cx="165" cy="78" r="3.5" fill="{c_vec}" />
      <text x="195" y="80" font-size="14" font-style="italic" fill="{c_vec}">ν(p) ∈ S²</text>
      <text x="120" y="190" font-size="16" font-style="italic" fill="#334155">S²</text>
    </g>
    
    <text x="300" y="325" font-size="13" fill="#0f172a">Gaussian Curvature  K = lim Area(ν(U)) / Area(U)</text>
"""
    return _svg_wrap("0 0 600 350", body, colorful)


# =========================================================================
# Figure 5: Tangent Developable and Cuspidal Edge (p. 152, 153)
# =========================================================================

def generate_fig_developable_cusp(colorful: bool = False) -> str:
    """Tangent developable surface along a space curve showing cuspidal edge."""
    c_curve = "#0f172a" if not colorful else "#7c3aed"
    c_sheet1 = "none" if not colorful else "url(#blue-grad)"
    c_sheet2 = "none" if not colorful else "url(#teal-grad)"
    c_rule = "#64748b" if not colorful else "#0284c7"

    # Space curve c(s)
    curve_path = "M 80 240 Q 200 180 320 200 T 460 120"
    
    # Rulings tangent to curve
    rulings = ""
    for px, py, dx, dy in [
        (100, 225, 45, -35),
        (150, 202, 55, -25),
        (200, 190, 60, -10),
        (260, 193, 60, 5),
        (320, 200, 55, -20),
        (380, 170, 50, -45),
        (430, 135, 40, -50),
    ]:
        rulings += f'<line x1="{px - dx}" y1="{py - dy}" x2="{px + dx * 1.5}" y2="{py + dy * 1.5}" stroke="{c_rule}" stroke-width="1.1" opacity="0.75" />\n'

    body = f"""
    <!-- Developable Surface Sheets -->
    <path d="M 60 280 L 100 225 L 200 190 L 320 200 L 460 120 L 520 60 L 400 60 L 260 90 L 140 130 Z" 
          fill="{c_sheet1}" stroke="none" />
    <path d="M 40 180 L 100 225 L 200 190 L 320 200 L 460 120 L 480 190 L 340 260 L 180 260 Z" 
          fill="{c_sheet2}" stroke="none" />
          
    <!-- Rulings (tangent lines) -->
    {rulings}
    
    <!-- Cuspidal Edge Curve c(s) -->
    <path d="{curve_path}" fill="none" stroke="{c_curve}" stroke-width="3.0" />
    
    <text x="340" y="225" font-size="14" font-style="italic" fill="{c_curve}">c(s) (Cuspidal Edge)</text>
    <text x="440" y="80" font-size="13" fill="{c_rule}">Ruling lines c(s) + t c'(s)</text>
    <text x="260" y="315" font-size="13" fill="#0f172a">Tangent Developable Surface (K = 0 everywhere)</text>
"""
    return _svg_wrap("0 0 540 340", body, colorful)


# =========================================================================
# Figure 6: Spivak's Flat Möbius Strip (p. 159)
# =========================================================================

def generate_fig_mobius_flat(colorful: bool = False) -> str:
    """Spivak's Flat Möbius Strip in R^3 (K = 0 developable non-orientable band)."""
    c_band = "#0f172a" if not colorful else "#2563eb"
    c_fill1 = "none" if not colorful else "url(#blue-grad)"
    c_fill2 = "none" if not colorful else "url(#amber-grad)"
    c_dash = "#64748b"

    body = f"""
    <!-- Front loop of Möbius strip -->
    <path d="M 120 200 Q 80 120 180 90 Q 280 60 380 110 Q 450 150 430 220 Q 400 280 290 280 Q 180 280 120 200 Z" 
          fill="{c_fill1}" stroke="{c_band}" stroke-width="2.2" />
          
    <!-- Half-twist fold in strip -->
    <path d="M 230 180 Q 290 220 330 170 Q 300 130 230 180 Z" 
          fill="{c_fill2}" stroke="{c_band}" stroke-width="1.8" />
          
    <!-- Centerline ruling curve -->
    <path d="M 140 195 Q 110 135 190 110 Q 280 85 365 125 Q 420 160 405 215 Q 380 260 285 260 Q 190 260 140 195 Z" 
          fill="none" stroke="{c_dash}" stroke-width="1.2" stroke-dasharray="4,4" />
          
    <text x="260" y="55" font-size="15" fill="#0f172a">C^∞ Flat Möbius Strip in ℝ³</text>
    <text x="260" y="315" font-size="13" fill="#475569">Constructed by gluing developable tangent sheets (K = 0)</text>
"""
    return _svg_wrap("0 0 520 340", body, colorful)


# =========================================================================
# Figure 7: Geodesic Polar Coordinates and Gauss Lemma (p. 184, 252)
# =========================================================================

def generate_fig_geodesic_polar(colorful: bool = False) -> str:
    """Geodesic polar coordinates: geodesic rays perpendicular to geodesic circles."""
    c_surf = "#0f172a" if not colorful else "#2563eb"
    c_fill = "none" if not colorful else "url(#blue-grad)"
    c_geo = "#0f172a" if not colorful else "#d97706"
    c_circ = "#475569" if not colorful else "#0891b2"
    arr_geo = 'marker-end="url(#arr)"' if not colorful else 'marker-end="url(#arr-amber)"'

    body = f"""
    <!-- Curved Surface patch -->
    <path d="M 60 260 Q 120 80 270 70 Q 420 60 480 240 Q 280 320 60 260 Z" 
          fill="{c_fill}" stroke="{c_surf}" stroke-width="1.8" />
          
    <!-- Base point p -->
    <circle cx="160" cy="200" r="4.0" fill="{c_geo}" />
    <text x="145" y="210" font-size="14" font-weight="bold" fill="{c_geo}">p</text>
    
    <!-- Geodesic circles (orthogonal trajectories) -->
    <path d="M 195 130 A 80 75 0 0 1 230 240" fill="none" stroke="{c_circ}" stroke-width="1.6" stroke-dasharray="4,3" />
    <path d="M 235 95 A 140 135 0 0 1 300 275" fill="none" stroke="{c_circ}" stroke-width="1.6" stroke-dasharray="4,3" />
    <path d="M 275 75 A 195 185 0 0 1 365 295" fill="none" stroke="{c_circ}" stroke-width="1.6" stroke-dasharray="4,3" />
    <text x="385" y="280" font-size="12" fill="{c_circ}">r = const</text>
    
    <!-- Radial geodesics emanating from p -->
    <path d="M 160 200 Q 230 160 380 130" fill="none" stroke="{c_geo}" stroke-width="2.0" {arr_geo} />
    <path d="M 160 200 Q 260 195 410 195" fill="none" stroke="{c_geo}" stroke-width="2.0" {arr_geo} />
    <path d="M 160 200 Q 240 230 380 255" fill="none" stroke="{c_geo}" stroke-width="2.0" {arr_geo} />
    <text x="425" y="130" font-size="13" font-style="italic" fill="{c_geo}">γ(r)</text>
    
    <!-- Right angle indicator -->
    <rect x="230" y="185" width="10" height="10" fill="none" stroke="{c_geo}" stroke-width="1.0" />
    
    <text x="270" y="340" font-size="13" fill="#0f172a">Gauss's Lemma: Geodesic rays are perpendicular to geodesic spheres</text>
"""
    return _svg_wrap("0 0 540 360", body, colorful)


# =========================================================================
# Figure 8: Gauss-Bonnet Geodesic Triangle (p. 302, 303)
# =========================================================================

def generate_fig_gauss_bonnet(colorful: bool = False) -> str:
    """The Gauss-Bonnet Theorem on a Geodesic Triangle with Parallel Transport."""
    c_fill_tri = "none" if not colorful else "url(#amber-grad)"
    c_edge = "#0f172a" if not colorful else "#1d4ed8"
    c_vec = "#0f172a" if not colorful else "#e11d48"
    c_arr = 'marker-end="url(#arr)"' if not colorful else 'marker-end="url(#arr-rose)"'

    # Vertices of geodesic triangle on curved surface
    v1 = (250, 70)   # Top A
    v2 = (110, 250)  # Left B
    v3 = (390, 250)  # Right C

    body = f"""
    <!-- Curved Surface background -->
    <path d="M 50 280 Q 90 40 250 30 Q 410 40 450 280 Q 250 320 50 280 Z" 
          fill="none" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="3,3" />
          
    <!-- Geodesic Triangle -->
    <path d="M {v1[0]} {v1[1]} Q 160 170 {v2[0]} {v2[1]} Q 250 270 {v3[0]} {v3[1]} Q 340 170 {v1[0]} {v1[1]} Z" 
          fill="{c_fill_tri}" stroke="{c_edge}" stroke-width="2.5" />
          
    <!-- Vertices -->
    <circle cx="{v1[0]}" cy="{v1[1]}" r="4" fill="{c_edge}" />
    <circle cx="{v2[0]}" cy="{v2[1]}" r="4" fill="{c_edge}" />
    <circle cx="{v3[0]}" cy="{v3[1]}" r="4" fill="{c_edge}" />
    <text x="{v1[0]}" y="{v1[1] - 15}" font-size="15" font-weight="bold" fill="{c_edge}">A (α)</text>
    <text x="{v2[0] - 25}" y="{v2[1] + 15}" font-size="15" font-weight="bold" fill="{c_edge}">B (β)</text>
    <text x="{v3[0] + 25}" y="{v3[1] + 15}" font-size="15" font-weight="bold" fill="{c_edge}">C (γ)</text>
    
    <!-- Parallel Transport Vector along path -->
    <!-- Start at B, transport to C -->
    <line x1="180" y1="256" x2="195" y2="215" stroke="{c_vec}" stroke-width="2.0" {c_arr} />
    <!-- Along C to A -->
    <line x1="330" y1="180" x2="355" y2="150" stroke="{c_vec}" stroke-width="2.0" {c_arr} />
    <!-- Along A to B returning with angular shift -->
    <line x1="175" y1="150" x2="150" y2="175" stroke="{c_vec}" stroke-width="2.0" {c_arr} />
    
    <!-- Formula -->
    <text x="250" y="185" font-size="15" font-style="italic" fill="#0f172a">∬_Δ K dA</text>
    <text x="250" y="325" font-size="14" font-weight="bold" fill="#0f172a">∬_Δ K dA = (α + β + γ) - π</text>
"""
    return _svg_wrap("0 0 500 360", body, colorful)


# =========================================================================
# Figure 9: Quadric Surface - Sphere (p. 161)
# =========================================================================

def generate_fig_sphere_quadric(colorful: bool = False) -> str:
    """Quadric Surface: Sphere with inward normal vector field and umbilics."""
    c_sphere = "#0f172a" if not colorful else "#2563eb"
    c_fill = "#f8fafc" if not colorful else "url(#sphere-glow)"
    c_vec = "#0f172a" if not colorful else "#e11d48"
    arr_n = 'marker-end="url(#arr)"' if not colorful else 'marker-end="url(#arr-rose)"'

    body = f"""
    <!-- Sphere circle -->
    <circle cx="200" cy="160" r="110" fill="{c_fill}" stroke="{c_sphere}" stroke-width="2.2" />
    
    <!-- Equator and Meridian circles -->
    <ellipse cx="200" cy="160" rx="110" ry="32" fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,3" />
    <path d="M 90 160 A 110 32 0 0 0 310 160" fill="none" stroke="{c_sphere}" stroke-width="1.2" />
    
    <ellipse cx="200" cy="160" rx="32" ry="110" fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,3" />
    <path d="M 200 50 A 32 110 0 0 1 200 270" fill="none" stroke="{c_sphere}" stroke-width="1.2" />
    
    <!-- Inward normal vector v = -1/R p -->
    <circle cx="270" cy="110" r="3.5" fill="{c_vec}" />
    <line x1="270" y1="110" x2="225" y2="142" stroke="{c_vec}" stroke-width="2.2" {arr_n} />
    <text x="295" y="105" font-size="13" font-style="italic" fill="{c_vec}">v = -Id/R</text>
    
    <text x="200" y="305" font-size="13" fill="#0f172a">All points are umbilic: k₁ = k₂ = 1/R,  K = 1/R²</text>
"""
    return _svg_wrap("0 0 400 330", body, colorful)


# =========================================================================
# Figure 10: Quadric Surface - Ellipsoid (p. 161)
# =========================================================================

def generate_fig_ellipsoid_quadric(colorful: bool = False) -> str:
    """Quadric Surface: Triaxial Ellipsoid x^2/a^2 + y^2/b^2 + z^2/c^2 = 1."""
    c_ell = "#0f172a" if not colorful else "#2563eb"
    c_fill = "none" if not colorful else "url(#blue-grad)"
    c_axis = "#475569" if not colorful else "#64748b"

    body = f"""
    <!-- Axes -->
    <line x1="40" y1="160" x2="360" y2="160" stroke="{c_axis}" stroke-width="1.2" />
    <line x1="200" y1="260" x2="200" y2="60" stroke="{c_axis}" stroke-width="1.2" />
    <line x1="130" y1="210" x2="270" y2="110" stroke="{c_axis}" stroke-width="1.2" />
    
    <!-- Outer boundary ellipse (xy) -->
    <ellipse cx="200" cy="160" rx="140" ry="80" fill="{c_fill}" stroke="{c_ell}" stroke-width="2.2" />
    
    <!-- Principal cross sections -->
    <ellipse cx="200" cy="160" rx="140" ry="30" fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,3" />
    <path d="M 60 160 A 140 30 0 0 0 340 160" fill="none" stroke="{c_ell}" stroke-width="1.3" />
    
    <ellipse cx="200" cy="160" rx="40" ry="80" fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,3" />
    <path d="M 200 80 A 40 80 0 0 1 200 240" fill="none" stroke="{c_ell}" stroke-width="1.3" />
    
    <text x="365" y="160" font-size="12" fill="{c_axis}">a</text>
    <text x="200" y="45" font-size="12" fill="{c_axis}">c</text>
    <text x="278" y="105" font-size="12" fill="{c_axis}">b</text>
    <text x="200" y="295" font-size="13" fill="#0f172a">x²/a² + y²/b² + z²/c² = 1</text>
"""
    return _svg_wrap("0 0 400 320", body, colorful)


# =========================================================================
# Figure 11: Minimal Surface - Catenoid (p. 171)
# =========================================================================

def generate_fig_catenoid_minimal(colorful: bool = False) -> str:
    """Minimal Surface: Catenoid x = a cosh(z/a), showing H = 0, K < 0."""
    c_cat = "#0f172a" if not colorful else "#0891b2"
    c_fill = "none" if not colorful else "url(#teal-grad)"

    body = f"""
    <!-- Top and bottom circles -->
    <ellipse cx="200" cy="70" rx="110" ry="24" fill="{c_fill}" stroke="{c_cat}" stroke-width="2.0" />
    <ellipse cx="200" cy="250" rx="110" ry="24" fill="{c_fill}" stroke="{c_cat}" stroke-width="2.0" />
    
    <!-- Waist circle (inner throat circle) -->
    <ellipse cx="200" cy="160" rx="60" ry="16" fill="none" stroke="#e11d48" stroke-width="1.8" stroke-dasharray="4,3" />
    <path d="M 140 160 A 60 16 0 0 0 260 160" fill="none" stroke="#e11d48" stroke-width="2.0" />
    <text x="290" y="160" font-size="12" fill="#e11d48">Throat z=0</text>
    
    <!-- Catenary profile curves -->
    <path d="M 90 70 Q 140 160 90 250" fill="none" stroke="{c_cat}" stroke-width="2.4" />
    <path d="M 310 70 Q 260 160 310 250" fill="none" stroke="{c_cat}" stroke-width="2.4" />
    
    <text x="200" y="300" font-size="13" fill="#0f172a">Catenoid: k_meridian = -k_parallel ⇒ H = 0 (Minimal Surface)</text>
"""
    return _svg_wrap("0 0 400 330", body, colorful)


# =========================================================================
# Figure 12: Surface of Revolution - Pseudosphere (p. 171, 247)
# =========================================================================

def generate_fig_pseudosphere(colorful: bool = False) -> str:
    """The Pseudosphere (Beltrami's surface of constant negative curvature K = -1/a^2)."""
    c_pseudo = "#0f172a" if not colorful else "#7c3aed"
    c_fill = "none" if not colorful else "url(#rose-grad)"

    body = f"""
    <!-- Central axis of revolution -->
    <line x1="200" y1="320" x2="200" y2="30" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,4" />
    
    <!-- Equator rim -->
    <ellipse cx="200" cy="180" rx="120" ry="25" fill="{c_fill}" stroke="{c_pseudo}" stroke-width="2.2" />
    
    <!-- Upper horn tapering to cusp at top -->
    <path d="M 80 180 Q 170 120 198 40" fill="none" stroke="{c_pseudo}" stroke-width="2.2" />
    <path d="M 320 180 Q 230 120 202 40" fill="none" stroke="{c_pseudo}" stroke-width="2.2" />
    
    <!-- Lower horn tapering to cusp at bottom -->
    <path d="M 80 180 Q 170 240 198 310" fill="none" stroke="{c_pseudo}" stroke-width="2.2" />
    <path d="M 320 180 Q 230 240 202 310" fill="none" stroke="{c_pseudo}" stroke-width="2.2" />
    
    <text x="200" y="345" font-size="13" fill="#0f172a">Pseudosphere: Constant Gaussian Curvature K = -1/a²</text>
"""
    return _svg_wrap("0 0 400 360", body, colorful)


# =========================================================================
# Registry and Batch Export
# =========================================================================

FIGURE_GENERATORS: dict[str, Callable[[bool], str]] = {
    "fig_dupin_elliptic": generate_fig_dupin_elliptic,
    "fig_dupin_hyperbolic": generate_fig_dupin_hyperbolic,
    "fig_monkey_saddle": generate_fig_monkey_saddle,
    "fig_gauss_map": generate_fig_gauss_map,
    "fig_developable_cusp": generate_fig_developable_cusp,
    "fig_mobius_flat": generate_fig_mobius_flat,
    "fig_geodesic_polar": generate_fig_geodesic_polar,
    "fig_gauss_bonnet": generate_fig_gauss_bonnet,
    "fig_sphere_quadric": generate_fig_sphere_quadric,
    "fig_ellipsoid_quadric": generate_fig_ellipsoid_quadric,
    "fig_catenoid_minimal": generate_fig_catenoid_minimal,
    "fig_pseudosphere": generate_fig_pseudosphere,
}


def generate_all_spivak_figures(out_dir_mono: Path, out_dir_color: Path) -> None:
    """Generate all figures in both crisp monochrome and vibrant 3Blue1Brown color."""
    out_dir_mono.mkdir(parents=True, exist_ok=True)
    out_dir_color.mkdir(parents=True, exist_ok=True)

    for fig_id, generator in FIGURE_GENERATORS.items():
        # Monochrome SVG + PNG
        svg_mono = generator(False)
        svg_mono_path = out_dir_mono / f"{fig_id}.svg"
        _ = svg_mono_path.write_text(svg_mono, encoding="utf-8")
        _svg_to_png(svg_mono_path, out_dir_mono / f"{fig_id}.png")

        # 3b1b Colorful SVG + PNG
        svg_color = generator(True)
        svg_color_path = out_dir_color / f"{fig_id}.svg"
        _ = svg_color_path.write_text(svg_color, encoding="utf-8")
        _svg_to_png(svg_color_path, out_dir_color / f"{fig_id}.png")

    print(f"Generated {len(FIGURE_GENERATORS)} figures in monochrome -> {out_dir_mono}")
    print(f"Generated {len(FIGURE_GENERATORS)} figures in 3b1b color -> {out_dir_color}")


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    """Render SVG to 300-DPI raster PNG using PyMuPDF."""
    doc = pymupdf.open(svg_path)
    page = doc[0]
    pix = page.get_pixmap(dpi=300)
    pix.save(png_path)
    doc.close()


if __name__ == "__main__":
    import sys

    from polytypst.paths import OUTPUT

    out_m = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT / "spivak_vol3" / "figures"
    out_c = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT / "spivak_vol3" / "figures_color"
    generate_all_spivak_figures(out_m, out_c)
