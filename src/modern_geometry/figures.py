"""Parametric vector illustrations for Modern Geometry: Methods and Applications. Part I.

Provides both Ordinary (crisp monochrome publication vector matching Springer 1992)
and Colorful (rich, high-contrast, pedagogical modern vector with gradients and semantic hues)
editions for all book figures.
"""

import math
from collections.abc import Callable
from pathlib import Path


def _marker_defs(colorful: bool) -> str:
    if not colorful:
        return """
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#0f172a" />
    </marker>
    <marker id="arr-axis" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#334155" />
    </marker>
    <pattern id="hatch" width="7" height="7" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="7" stroke="#0f172a" stroke-width="1.1" />
    </pattern>
    <pattern id="hatch-dense" width="5" height="5" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="5" stroke="#0f172a" stroke-width="1.0" />
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
    <marker id="arr-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#dc2626" />
    </marker>
    <marker id="arr-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#059669" />
    </marker>
    <marker id="arr-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#d97706" />
    </marker>
    <radialGradient id="disc-glow" cx="45%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#dbeafe" stop-opacity="0.9" />
      <stop offset="65%" stop-color="#bfdbfe" stop-opacity="0.65" />
      <stop offset="100%" stop-color="#93c5fd" stop-opacity="0.35" />
    </radialGradient>
    <radialGradient id="sphere-glow" cx="35%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#f0f9ff" stop-opacity="0.95" />
      <stop offset="55%" stop-color="#bae6fd" stop-opacity="0.75" />
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.35" />
    </radialGradient>
    <linearGradient id="cone-grad-top" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fee2e2" stop-opacity="0.85" />
      <stop offset="100%" stop-color="#fca5a5" stop-opacity="0.45" />
    </linearGradient>
    <linearGradient id="cone-grad-bot" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e0e7ff" stop-opacity="0.85" />
      <stop offset="100%" stop-color="#c7d2fe" stop-opacity="0.45" />
    </linearGradient>
    <pattern id="hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#2563eb" stroke-width="1.1" opacity="0.65" />
    </pattern>
    <pattern id="hatch-dense" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="6" stroke="#059669" stroke-width="1.0" opacity="0.6" />
    </pattern>
"""


def _svg_wrap(viewbox: str, content: str, colorful: bool) -> str:
    defs = _marker_defs(colorful)
    font_family = '"New Computer Modern", "Latin Modern Roman", "STIX Two Math", "Times New Roman", serif'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="100%" height="100%">
  <defs>{defs}  </defs>
  <style>
    text {{ font-family: {font_family}; }}
    .ax {{ stroke: {'#334155' if not colorful else '#475569'}; stroke-width: 1.25; fill: none; }}
    .c-main {{ stroke: {'#0f172a' if not colorful else '#1e293b'}; stroke-width: 1.8; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
    .c-dash {{ stroke: {'#64748b' if not colorful else '#94a3b8'}; stroke-width: 1.15; stroke-dasharray: 5,4; fill: none; }}
    .lbl {{ font-size: 16px; fill: #0f172a; }}
    .it {{ font-size: 18px; font-style: italic; fill: #0f172a; }}
  </style>
{content}
</svg>"""


# =========================================================================
# Figure 1: 3D Cartesian Coordinate System & Projection of Point P
# =========================================================================
def generate_fig_1(colorful: bool = False) -> str:
    ox, oy = 90, 220
    # Axis vectors: x1 down-left/down-right, x2 right, x3 up
    x1_end = (175, 275)
    x2_end = (340, 220)
    x3_end = (90, 45)
    
    # Point P coordinates
    p_x1, p_x2, p_x3 = 45, 150, 110
    # In projection
    base_x = ox + (x1_end[0] - ox) * (p_x1 / 85) + p_x2
    base_y = oy + (x1_end[1] - oy) * (p_x1 / 85)
    px = base_x
    py = base_y - p_x3

    pt_col = "#0f172a" if not colorful else "#1e293b"
    pt_fill = "#ffffff" if not colorful else "#fef08a"
    ax_x1 = "#0f172a" if not colorful else "#2563eb"
    ax_x2 = "#0f172a" if not colorful else "#059669"
    ax_x3 = "#0f172a" if not colorful else "#dc2626"
    arr_x1 = "arr" if not colorful else "arr-blue"
    arr_x2 = "arr" if not colorful else "arr-green"
    arr_x3 = "arr" if not colorful else "arr-red"

    body = f"""
  <!-- Axes -->
  <line x1="{ox}" y1="{oy}" x2="{x1_end[0]}" y2="{x1_end[1]}" stroke="{ax_x1}" stroke-width="1.6" marker-end="url(#{arr_x1})" />
  <line x1="{ox}" y1="{oy}" x2="{x2_end[0]}" y2="{x2_end[1]}" stroke="{ax_x2}" stroke-width="1.6" marker-end="url(#{arr_x2})" />
  <line x1="{ox}" y1="{oy}" x2="{x3_end[0]}" y2="{x3_end[1]}" stroke="{ax_x3}" stroke-width="1.6" marker-end="url(#{arr_x3})" />

  <!-- Origin -->
  <circle cx="{ox}" cy="{oy}" r="3.2" fill="{pt_fill}" stroke="{pt_col}" stroke-width="1.4" />
  <text x="{ox - 16}" y="{oy + 16}" class="it">0</text>

  <!-- Labels on axes -->
  <text x="{x1_end[0] + 8}" y="{x1_end[1] + 12}" class="it" fill="{ax_x1}">x¹</text>
  <text x="{x2_end[0] + 8}" y="{x2_end[1] + 5}" class="it" fill="{ax_x2}">x²</text>
  <text x="{x3_end[0] - 18}" y="{x3_end[1] + 4}" class="it" fill="{ax_x3}">x³</text>

  <!-- Projection lines in plane x1-x2 -->
  <line x1="{ox + (x1_end[0]-ox)*(p_x1/85)}" y1="{oy + (x1_end[1]-oy)*(p_x1/85)}" x2="{base_x}" y2="{base_y}" class="c-dash" />
  <line x1="{ox + p_x2}" y1="{oy}" x2="{base_x}" y2="{base_y}" class="c-dash" />
  <line x1="{base_x}" y1="{base_y}" x2="{px}" y2="{py}" class="c-dash" stroke-width="1.3" />

  <!-- Point P -->
  <circle cx="{px}" cy="{py}" r="3.8" fill="{pt_fill}" stroke="{pt_col}" stroke-width="1.6" />
  <text x="{px + 10}" y="{py - 6}" class="it" font-weight="bold">P = (x¹, x², x³)</text>
"""
    return _svg_wrap("0 0 440 310", body, colorful)

# =========================================================================
# Figure 2: World-Line of a Point-Particle in Space-Time (t, x1, x2)
# =========================================================================
def generate_fig_2(colorful: bool = False) -> str:
    ox, oy = 140, 220
    x1_axis = (320, 220)
    x2_axis = (60, 280)
    t_axis = (140, 35)

    c_curve = "#0f172a" if not colorful else "#2563eb"
    c_pt = "#0f172a" if not colorful else "#dc2626"
    fill_pt = "#ffffff" if not colorful else "#fef08a"

    body = f"""
  <!-- Space-time coordinate axes (t, x1, x2) -->
  <line x1="{ox}" y1="{oy}" x2="{x1_axis[0]}" y2="{x1_axis[1]}" class="ax" marker-end="url(#arr-axis)" />
  <line x1="{ox}" y1="{oy}" x2="{x2_axis[0]}" y2="{x2_axis[1]}" class="ax" marker-end="url(#arr-axis)" />
  <line x1="{ox}" y1="{oy}" x2="{t_axis[0]}" y2="{t_axis[1]}" class="ax" marker-end="url(#arr-axis)" />

  <text x="{x1_axis[0] + 10}" y="{x1_axis[1] + 5}" class="it">x¹</text>
  <text x="{x2_axis[0] - 16}" y="{x2_axis[1] + 12}" class="it">x²</text>
  <text x="{t_axis[0] - 18}" y="{t_axis[1] + 4}" class="it">t</text>
  <text x="{ox - 16}" y="{oy + 16}" class="it">0</text>

  <!-- World-line curve ascending in time -->
  <path d="M 120 200 C 160 160 210 170 200 110 S 240 70 250 50" fill="none" stroke="{c_curve}" stroke-width="2.4" />
  <text x="258" y="55" class="it" font-weight="bold" fill="{c_curve}">x(t)</text>

  <!-- Initial and final points -->
  <circle cx="120" cy="200" r="3.6" fill="{fill_pt}" stroke="{c_pt}" stroke-width="1.6" />
  <text x="75" y="202" class="it">P(t₁)</text>
  <line x1="120" y1="200" x2="{ox}" y2="200" class="c-dash" />
  <text x="{ox - 22}" y="204" class="it">t₁</text>

  <circle cx="250" cy="50" r="3.6" fill="{fill_pt}" stroke="{c_pt}" stroke-width="1.6" />
  <text x="260" y="42" class="it">P(t₂)</text>
  <line x1="250" y1="50" x2="{ox}" y2="50" class="c-dash" />
  <text x="{ox - 22}" y="54" class="it">t₂</text>
"""
    return _svg_wrap("0 0 380 300", body, colorful)

# =========================================================================
# Figure 3: Spherical Polar Coordinates (r, theta, phi) in 3-Space
# =========================================================================
def generate_fig_3(colorful: bool = False) -> str:
    ox, oy = 160, 220
    x_axis = (70, 280)
    y_axis = (350, 220)
    z_axis = (160, 40)

    # Point P in space
    px, py = 270, 100
    base_x, base_y = 270, 255

    pt_col = "#0f172a" if not colorful else "#1e293b"
    pt_fill = "#ffffff" if not colorful else "#fef08a"
    r_col = "#0f172a" if not colorful else "#dc2626"
    arc_col = "#334155" if not colorful else "#d97706"

    body = f"""
  <!-- Axes -->
  <line x1="{ox}" y1="{oy}" x2="{x_axis[0]}" y2="{x_axis[1]}" class="ax" marker-end="url(#arr-axis)" />
  <line x1="{ox}" y1="{oy}" x2="{y_axis[0]}" y2="{y_axis[1]}" class="ax" marker-end="url(#arr-axis)" />
  <line x1="{ox}" y1="{oy}" x2="{z_axis[0]}" y2="{z_axis[1]}" class="ax" marker-end="url(#arr-axis)" />

  <text x="{x_axis[0] - 12}" y="{x_axis[1] + 16}" class="it">x</text>
  <text x="{y_axis[0] + 10}" y="{y_axis[1] + 5}" class="it">y</text>
  <text x="{z_axis[0] - 16}" y="{z_axis[1] + 4}" class="it">z</text>
  <text x="{ox - 16}" y="{oy + 16}" class="it">0</text>

  <!-- Projection lines -->
  <line x1="{ox}" y1="{oy}" x2="{base_x}" y2="{base_y}" class="c-dash" />
  <line x1="{base_x}" y1="{base_y}" x2="{px}" y2="{py}" class="c-dash" />

  <!-- Radius vector r -->
  <line x1="{ox}" y1="{oy}" x2="{px}" y2="{py}" stroke="{r_col}" stroke-width="1.8" marker-end="url(#{'arr' if not colorful else 'arr-red'})" />
  <text x="{(ox + px)//2 - 12}" y="{(oy + py)//2 - 8}" class="it" font-weight="bold" fill="{r_col}">r</text>

  <!-- Angle theta arc (from z-axis to r) -->
  <path d="M 160 160 A 60 60 0 0 1 204 172" fill="none" stroke="{arc_col}" stroke-width="1.4" />
  <text x="188" y="152" class="it" fill="{arc_col}">θ</text>

  <!-- Angle phi arc (in xy plane from x-axis to base) -->
  <path d="M 125 244 A 45 45 0 0 0 195 233" fill="none" stroke="{arc_col}" stroke-width="1.4" />
  <text x="156" y="258" class="it" fill="{arc_col}">φ</text>

  <!-- Point P -->
  <circle cx="{px}" cy="{py}" r="3.6" fill="{pt_fill}" stroke="{pt_col}" stroke-width="1.5" />
  <text x="{px + 10}" y="{py - 5}" class="it" font-weight="bold">P = (r, θ, φ)</text>
"""
    return _svg_wrap("0 0 420 310", body, colorful)


# =========================================================================
# Figure 5: Galilean Reference Frames in Motion
# =========================================================================
def generate_fig_5(colorful: bool = False) -> str:
    # Fixed frame (x1, x2, x3)
    o1_x, o1_y = 90, 220
    # Moving frame (x'1, x'2, x'3) displaced along x1 by 110px
    o2_x, o2_y = 200, 255

    c1 = "#0f172a" if not colorful else "#2563eb"
    c2 = "#0f172a" if not colorful else "#dc2626"
    v_col = "#0f172a" if not colorful else "#059669"

    body = f"""
  <!-- Fixed frame S -->
  <line x1="{o1_x}" y1="{o1_y}" x2="210" y2="258" stroke="{c1}" stroke-width="1.6" marker-end="url(#arr-axis)" />
  <line x1="{o1_x}" y1="{o1_y}" x2="210" y2="165" stroke="{c1}" stroke-width="1.6" marker-end="url(#arr-axis)" />
  <line x1="{o1_x}" y1="{o1_y}" x2="{o1_x}" y2="40" stroke="{c1}" stroke-width="1.6" marker-end="url(#arr-axis)" />
  <text x="{o1_x - 22}" y="45" class="it" fill="{c1}">x³</text>
  <text x="216" y="165" class="it" fill="{c1}">x²</text>

  <!-- Moving frame S' -->
  <line x1="{o2_x}" y1="{o2_y}" x2="330" y2="295" stroke="{c2}" stroke-width="1.6" marker-end="url(#arr-axis)" />
  <line x1="{o2_x}" y1="{o2_y}" x2="320" y2="200" stroke="{c2}" stroke-width="1.6" marker-end="url(#arr-axis)" />
  <line x1="{o2_x}" y1="{o2_y}" x2="{o2_x}" y2="75" stroke="{c2}" stroke-width="1.6" marker-end="url(#arr-axis)" />
  <text x="{o2_x - 24}" y="80" class="it" fill="{c2}">x′³</text>
  <text x="326" y="200" class="it" fill="{c2}">x′²</text>
  <text x="336" y="302" class="it" fill="{c2}">x¹, x′¹</text>

  <!-- Velocity vector v -->
  <line x1="240" y1="240" x2="295" y2="258" stroke="{v_col}" stroke-width="2.0" marker-end="url(#{'arr' if not colorful else 'arr-green'})" />
  <text x="304" y="258" class="it" font-weight="bold" fill="{v_col}">v</text>
"""
    return _svg_wrap("0 0 440 320", body, colorful)


# =========================================================================
# Figure 7: Light Cone (Isotropic Cone) in Pseudo-Euclidean Space R^3_1
# =========================================================================
def generate_fig_7(colorful: bool = False) -> str:
    cx, cy = 200, 160
    rw, rh = 60, 22
    h = 100

    cone_top = f"M {cx - rw} {cy - h} L {cx} {cy} L {cx + rw} {cy - h}"
    cone_bot = f"M {cx - rw} {cy + h} L {cx} {cy} L {cx + rw} {cy + h}"

    fill_top = "none" if not colorful else "url(#cone-grad-top)"
    fill_bot = "none" if not colorful else "url(#cone-grad-bot)"
    line_col = "#0f172a" if not colorful else "#1e293b"

    body = f"""
  <!-- Axes -->
  <line x1="{cx}" y1="285" x2="{cx}" y2="35" class="ax" marker-end="url(#arr-axis)" />
  <line x1="90" y1="210" x2="310" y2="110" class="ax" marker-end="url(#arr-axis)" />
  <line x1="120" y1="110" x2="300" y2="215" class="ax" marker-end="url(#arr-axis)" />

  <text x="{cx - 22}" y="42" class="it">x⁰</text>
  <text x="316" y="112" class="it">x²</text>
  <text x="306" y="222" class="it">x¹</text>

  <!-- Upper cone filled/outlined -->
  <path d="M {cx - rw} {cy - h} L {cx} {cy} L {cx + rw} {cy - h} A {rw} {rh} 0 0 1 {cx - rw} {cy - h} Z" fill="{fill_top}" stroke="none" />
  <path d="{cone_top}" stroke="{line_col}" stroke-width="1.8" fill="none" />
  <ellipse cx="{cx}" cy="{cy - h}" rx="{rw}" ry="{rh}" stroke="{line_col}" stroke-width="1.6" fill="none" />

  <!-- Lower cone filled/outlined -->
  <path d="M {cx - rw} {cy + h} L {cx} {cy} L {cx + rw} {cy + h} A {rw} {rh} 0 0 0 {cx - rw} {cy + h} Z" fill="{fill_bot}" stroke="none" />
  <path d="{cone_bot}" stroke="{line_col}" stroke-width="1.8" fill="none" />
  <ellipse cx="{cx}" cy="{cy + h}" rx="{rw}" ry="{rh}" stroke="{line_col}" stroke-width="1.6" stroke-dasharray="4,3" fill="none" />

  <!-- Time-like vector inside cone -->
  <line x1="{cx}" y1="{cy}" x2="225" y2="75" stroke="{'#0f172a' if not colorful else '#dc2626'}" stroke-width="2.2" marker-end="url(#{'arr' if not colorful else 'arr-red'})" />
  <text x="235" y="80" class="it" font-weight="bold" fill="{'#0f172a' if not colorful else '#dc2626'}">|ξ₊|² &gt; 0</text>

  <!-- Isotropic (light) vector on cone boundary -->
  <line x1="{cx}" y1="{cy}" x2="{cx - rw * 0.7}" y2="{cy - h * 0.7}" stroke="{'#0f172a' if not colorful else '#d97706'}" stroke-width="2.2" marker-end="url(#{'arr' if not colorful else 'arr-amber'})" />
  <text x="55" y="150" class="it" font-weight="bold" fill="{'#0f172a' if not colorful else '#d97706'}">|ξ₀|² = 0</text>

  <!-- Space-like vector outside cone -->
  <line x1="{cx}" y1="{cy}" x2="270" y2="155" stroke="{'#0f172a' if not colorful else '#2563eb'}" stroke-width="2.2" marker-end="url(#{'arr' if not colorful else 'arr-blue'})" />
  <text x="250" y="135" class="it" font-weight="bold" fill="{'#0f172a' if not colorful else '#2563eb'}">|ξ₋|² &lt; 0</text>
"""
    return _svg_wrap("0 0 420 320", body, colorful)

# =========================================================================
# Figure 8: World-Lines of Particles With and Without Mass
# =========================================================================
def generate_fig_8(colorful: bool = False) -> str:
    c_cone = "#0f172a" if not colorful else "#3b82f6"
    c_valid = "#0f172a" if not colorful else "#059669"
    c_photon = "#0f172a" if not colorful else "#d97706"
    c_forbid = "#64748b" if not colorful else "#dc2626"

    body = f"""
  <!-- Lower cones -->
  <g transform="translate(120, 230)">
    <polygon points="0,0 -20,-35 20,-35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <polygon points="0,0 -20,35 20,35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <ellipse cx="0" cy="-35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" />
    <ellipse cx="0" cy="35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" stroke-dasharray="3,3" />
  </g>
  <g transform="translate(180, 230)">
    <polygon points="0,0 -20,-35 20,-35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <polygon points="0,0 -20,35 20,35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <ellipse cx="0" cy="-35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" />
    <ellipse cx="0" cy="35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" stroke-dasharray="3,3" />
  </g>

  <!-- Upper cones -->
  <g transform="translate(150, 90)">
    <polygon points="0,0 -20,-35 20,-35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <polygon points="0,0 -20,35 20,35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <ellipse cx="0" cy="-35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" />
    <ellipse cx="0" cy="35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" stroke-dasharray="3,3" />
  </g>
  <g transform="translate(200, 90)">
    <polygon points="0,0 -20,-35 20,-35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <polygon points="0,0 -20,35 20,35" fill="none" stroke="{c_cone}" stroke-width="1.4" />
    <ellipse cx="0" cy="-35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" />
    <ellipse cx="0" cy="35" rx="20" ry="7" fill="none" stroke="{c_cone}" stroke-width="1.2" stroke-dasharray="3,3" />
  </g>

  <!-- World-line of particle with mass (inside light cone) -->
  <path d="M 120 270 Q 115 170 150 50" fill="none" stroke="{c_valid}" stroke-width="2.2" />
  <text x="100" y="45" class="it" font-weight="bold" fill="{c_valid}">m &gt; 0</text>

  <!-- World-line of photon (massless, on cone surface) -->
  <path d="M 135 270 L 210 50" fill="none" stroke="{c_photon}" stroke-width="2.0" stroke-dasharray="6,3" />
  <text x="215" y="45" class="it" font-weight="bold" fill="{c_photon}">m = 0</text>

  <!-- Forbidden space-like curve -->
  <path d="M 180 270 Q 185 180 300 150" fill="none" stroke="{c_forbid}" stroke-width="1.8" />
  <text x="230" y="180" class="it" fill="{c_forbid}">v &gt; c</text>
"""
    return _svg_wrap("0 0 380 300", body, colorful)


# =========================================================================
# Figure 11: The (theta, phi)-Plane and North Pole Pinching
# =========================================================================
def generate_fig_11(colorful: bool = False) -> str:
    cx, cy = 180, 160
    r = 90
    body = f"""
  <!-- Disc/Circle of radius pi -->
  <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{ '#0f172a' if not colorful else '#2563eb' }" stroke-width="1.8" fill="{ 'none' if not colorful else 'url(#disc-glow)' }" />

  <!-- Axes -->
  <line x1="60" y1="{cy}" x2="300" y2="{cy}" class="ax" marker-end="url(#arr-axis)" />
  <line x1="{cx}" y1="260" x2="{cx}" y2="60" class="ax" marker-end="url(#arr-axis)" />

  <text x="306" y="{cy + 5}" class="it">φ</text>
  <text x="{cx - 15}" y="52" class="it">θ</text>
  <text x="{cx - 15}" y="{cy + 16}" class="it">0</text>

  <!-- Arc AB highlighted on circle boundary -->
  <path d="M {cx + r*0.707} {cy - r*0.707} A {r} {r} 0 0 1 {cx + r*0.965} {cy - r*0.258}" stroke="{ '#0f172a' if not colorful else '#dc2626' }" stroke-width="3.2" fill="none" />

  <circle cx="{cx + r*0.707}" cy="{cy - r*0.707}" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.5" />
  <text x="{cx + r*0.707 + 8}" y="{cy - r*0.707 - 4}" class="it" font-weight="bold">A</text>

  <circle cx="{cx + r*0.965}" cy="{cy - r*0.258}" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.5" />
  <text x="{cx + r*0.965 + 8}" y="{cy - r*0.258 + 4}" class="it" font-weight="bold">B</text>

  <!-- Radius vector to arc point -->
  <line x1="{cx}" y1="{cy}" x2="{cx + 60}" y2="{cy - 40}" stroke="{'#0f172a' if not colorful else '#059669'}" stroke-width="1.6" />
  <text x="{cx + 25}" y="{cy - 25}" class="it" fill="{'#0f172a' if not colorful else '#059669'}">θ</text>
  <text x="{cx + 42}" y="{cy - 8}" class="it" fill="{'#0f172a' if not colorful else '#d97706'}">φ</text>

  <!-- Label theta = pi -->
  <text x="{cx + 60}" y="{cy + 85}" class="it" font-weight="bold">θ = π</text>
"""
    return _svg_wrap("0 0 380 300", body, colorful)


# =========================================================================
# Figure 12: Stereographic Projection of the 2-Sphere
# =========================================================================
def generate_fig_12(colorful: bool = False) -> str:
    cx, cy = 160, 180
    r = 80
    nx, ny = cx, cy - r # North pole N
    
    # Point on sphere at angle theta
    angle = math.radians(45)
    px = cx + r * math.sin(angle)
    py = cy - r * math.cos(angle)
    
    # Ray from N through P hits equator line (y = cy) at rx
    # rx - cx = (px - cx) * (cy - ny) / (py - ny)
    rx = cx + (px - cx) * r / (py - ny)

    body = f"""
  <!-- Equator plane & vertical axis -->
  <line x1="40" y1="{cy}" x2="350" y2="{cy}" class="ax" marker-end="url(#arr-axis)" />
  <line x1="{cx}" y1="280" x2="{cx}" y2="50" class="ax" marker-end="url(#arr-axis)" />

  <!-- Sphere section (circle) -->
  <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{'#0f172a' if not colorful else '#1e3a8a'}" stroke-width="2.0" fill="{'none' if not colorful else 'url(#sphere-glow)'}" />

  <!-- North Pole N -->
  <circle cx="{nx}" cy="{ny}" r="3.4" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" />
  <text x="{nx - 18}" y="{ny - 5}" class="it" font-weight="bold">N</text>

  <!-- Center O -->
  <circle cx="{cx}" cy="{cy}" r="3.0" fill="#ffffff" stroke="#0f172a" stroke-width="1.4" />
  <text x="{cx - 15}" y="{cy + 16}" class="it">0</text>

  <!-- Radius to P -->
  <line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" stroke="{'#0f172a' if not colorful else '#059669'}" stroke-width="1.6" />
  <text x="{(cx + px)//2 + 5}" y="{(cy + py)//2 + 10}" class="it">θ</text>

  <!-- Projection ray from N through P to R on equator -->
  <line x1="{nx}" y1="{ny}" x2="{rx}" y2="{cy}" stroke="{'#0f172a' if not colorful else '#dc2626'}" stroke-width="1.8" />

  <!-- Point P on sphere -->
  <circle cx="{px}" cy="{py}" r="3.6" fill="{'#ffffff' if not colorful else '#fef08a'}" stroke="#0f172a" stroke-width="1.6" />
  <text x="{px + 8}" y="{py - 6}" class="it" font-weight="bold">θ, φ</text>

  <!-- Projected point (r, phi) -->
  <circle cx="{rx}" cy="{cy}" r="3.6" fill="{'#ffffff' if not colorful else '#fef08a'}" stroke="#0f172a" stroke-width="1.6" />
  <text x="{rx - 15}" y="{cy + 22}" class="it" font-weight="bold">r, φ</text>
"""
    return _svg_wrap("0 0 380 300", body, colorful)


# =========================================================================
# Figure 13: Spherical Cap / Disc of Radius Rho on Sphere
# =========================================================================
def generate_fig_13(colorful: bool = False) -> str:
    cx, cy = 180, 190
    r = 95
    # Disc cut at z = r*cos(theta_0)
    theta_0 = math.radians(40)
    cut_y = cy - r * math.cos(theta_0)
    cut_rx = r * math.sin(theta_0)
    cut_ry = 18

    body = f"""
  <!-- Axes -->
  <line x1="{cx}" y1="290" x2="{cx}" y2="40" class="ax" marker-end="url(#arr-axis)" />
  <line x1="70" y1="250" x2="290" y2="130" class="ax" marker-end="url(#arr-axis)" />
  <line x1="80" y1="120" x2="280" y2="260" class="ax" marker-end="url(#arr-axis)" />

  <text x="{cx - 16}" y="45" class="it">z</text>
  <text x="296" y="132" class="it">y</text>
  <text x="68" y="262" class="it">x</text>

  <!-- Sphere silhouette -->
  <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{'#0f172a' if not colorful else '#1e3a8a'}" stroke-width="1.8" fill="{'none' if not colorful else 'url(#sphere-glow)'}" />

  <!-- Equator / disc slice with cone rays -->
  <ellipse cx="{cx}" cy="{cut_y}" rx="{cut_rx}" ry="{cut_ry}" stroke="{'#0f172a' if not colorful else '#2563eb'}" stroke-width="1.6" fill="{'none' if not colorful else '#dbeafe'}" opacity="0.8" />

  <!-- Cone lines from center O to cut boundary -->
  <line x1="{cx}" y1="{cy}" x2="{cx - cut_rx}" y2="{cut_y}" class="c-dash" />
  <line x1="{cx}" y1="{cy}" x2="{cx + cut_rx}" y2="{cut_y}" stroke="{'#0f172a' if not colorful else '#dc2626'}" stroke-width="1.6" />

  <!-- Center O and North Pole N -->
  <circle cx="{cx}" cy="{cy}" r="3.0" fill="#ffffff" stroke="#0f172a" stroke-width="1.4" />
  <circle cx="{cx}" cy="{cy - r}" r="3.2" fill="#ffffff" stroke="#0f172a" stroke-width="1.5" />
  <text x="{cx - 18}" y="{cy - r - 6}" class="it" font-weight="bold">N</text>

  <!-- Angle theta_0 arc -->
  <path d="M {cx} {cy - 35} A 35 35 0 0 1 {cx + 22} {cy - 27}" fill="none" stroke="{'#0f172a' if not colorful else '#d97706'}" stroke-width="1.4" />
  <text x="{cx + 12}" y="{cy - 42}" class="it" fill="{'#0f172a' if not colorful else '#d97706'}">θ<tspan dy="3" font-size="10">0</tspan></text>

  <!-- Radius rho along sphere surface -->
  <text x="{cx + cut_rx/2 + 5}" y="{cut_y - 12}" class="it" font-weight="bold" fill="{'#0f172a' if not colorful else '#dc2626'}">ρ</text>
"""
    return _svg_wrap("0 0 380 320", body, colorful)


# =========================================================================
# Figure 16: Poincaré Unit Disc / Klein Model
# =========================================================================
def generate_fig_16(colorful: bool = False) -> str:
    cx, cy = 120, 130
    r = 68
    pt_col = "#0f172a" if not colorful else "#1e293b"
    pt_fill = "#ffffff" if not colorful else "#fef08a"
    disc_stroke = "#0f172a" if not colorful else "#1d4ed8"
    disc_fill = "url(#hatch)" if not colorful else "url(#disc-glow)"
    hatch_overlay = "" if not colorful else f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#hatch)" stroke="{disc_stroke}" stroke-width="2.2" />'

    body = f"""
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{disc_fill}" stroke="{disc_stroke}" stroke-width="2.0" />
  {hatch_overlay}

  <!-- Coordinate axes u and v -->
  <line x1="25" y1="{cy}" x2="225" y2="{cy}" stroke="{'#0f172a' if not colorful else '#334155'}" stroke-width="1.3" marker-end="url(#{'arr' if not colorful else 'arr-axis'})" />
  <text x="232" y="{cy + 5}" class="it" font-weight="{'normal' if not colorful else 'bold'}">u</text>

  <line x1="{cx}" y1="230" x2="{cx}" y2="30" stroke="{'#0f172a' if not colorful else '#334155'}" stroke-width="1.3" marker-end="url(#{'arr' if not colorful else 'arr-axis'})" />
  <text x="{cx - 17}" y="32" class="it" font-weight="{'normal' if not colorful else 'bold'}">v</text>

  <!-- Points 0, 1, i -->
  <circle cx="{cx}" cy="{cy}" r="3.4" fill="{pt_fill}" stroke="{pt_col}" stroke-width="1.5" />
  <text x="{cx - 10}" y="{cy + 17}" class="it">0</text>

  <circle cx="{cx + r}" cy="{cy}" r="3.4" fill="{pt_fill}" stroke="{pt_col}" stroke-width="1.5" />
  <text x="{cx + r - 2}" y="{cy + 17}" class="it">1</text>

  <circle cx="{cx}" cy="{cy - r}" r="3.4" fill="{pt_fill}" stroke="{pt_col}" stroke-width="1.5" />
  <text x="{cx + 7}" y="{cy - r - 2}" class="it">i</text>

  <!-- (Z) region label -->
  <text x="{cx - 47}" y="{cy - 28}" class="it" font-weight="bold" fill="{'#0f172a' if not colorful else '#1e3a8a'}">(Z)</text>
"""
    return _svg_wrap("0 0 260 260", body, colorful)


# =========================================================================
# Figure 31: Triangulated 2D Surface with Cancelling Internal Edges
# =========================================================================
def generate_fig_31(colorful: bool = False) -> str:
    # A triangulated polygon showing orientation of boundaries and internal edge cancellations
    tri_stroke = "#0f172a" if not colorful else "#1e3a8a"
    tri_fill = "none" if not colorful else "#eff6ff"
    edge_cancel = "#64748b" if not colorful else "#dc2626"

    body = f"""
  <!-- Triangles forming a surface patch -->
  <polygon points="60,180 150,70 230,170" fill="{tri_fill}" stroke="{tri_stroke}" stroke-width="1.8" />
  <polygon points="150,70 270,60 230,170" fill="{tri_fill}" stroke="{tri_stroke}" stroke-width="1.8" />
  <polygon points="270,60 340,150 230,170" fill="{tri_fill}" stroke="{tri_stroke}" stroke-width="1.8" />
  <polygon points="230,170 340,150 290,240" fill="{tri_fill}" stroke="{tri_stroke}" stroke-width="1.8" />
  <polygon points="60,180 230,170 170,250" fill="{tri_fill}" stroke="{tri_stroke}" stroke-width="1.8" />
  <polygon points="170,250 230,170 290,240" fill="{tri_fill}" stroke="{tri_stroke}" stroke-width="1.8" />

  <!-- Opposing orientation arrows on internal shared edges -->
  <!-- Edge (150,70) to (230,170) -->
  <line x1="185" y1="114" x2="195" y2="126" stroke="{edge_cancel}" stroke-width="2.0" marker-end="url(#{'arr' if not colorful else 'arr-red'})" />
  <line x1="195" y1="126" x2="185" y2="114" stroke="{edge_cancel}" stroke-width="2.0" marker-end="url(#{'arr' if not colorful else 'arr-red'})" />

  <!-- Vertices -->
  <circle cx="60" cy="180" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.4" />
  <circle cx="150" cy="70" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.4" />
  <circle cx="270" cy="60" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.4" />
  <circle cx="340" cy="150" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.4" />
  <circle cx="290" cy="240" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.4" />
  <circle cx="170" cy="250" r="3.2" fill="#fff" stroke="#0f172a" stroke-width="1.4" />
  <circle cx="230" cy="170" r="3.5" fill="#fef08a" stroke="#0f172a" stroke-width="1.6" />

  <!-- Label T -->
  <text x="140" y="145" class="it" font-weight="bold" font-size="18px">T<tspan dy="4" font-size="12">1</tspan></text>
  <text x="215" y="105" class="it" font-weight="bold" font-size="18px">T<tspan dy="4" font-size="12">2</tspan></text>
  <text x="280" y="130" class="it" font-weight="bold" font-size="18px">T<tspan dy="4" font-size="12">3</tspan></text>
  <text x="255" y="200" class="it" font-weight="bold" font-size="18px">T<tspan dy="4" font-size="12">4</tspan></text>
  <text x="150" y="210" class="it" font-weight="bold" font-size="18px">T<tspan dy="4" font-size="12">5</tspan></text>
"""
    return _svg_wrap("0 0 400 300", body, colorful)


# =========================================================================
# Figure 32: Oriented Simplex Circuit
# =========================================================================
def generate_fig_32(colorful: bool = False) -> str:
    edge_col = "#0f172a" if not colorful else "#2563eb"
    arr = "arr" if not colorful else "arr-blue"
    fill = "none" if not colorful else "#eff6ff"
    body = f"""
  <polygon points="80,220 280,220 180,60" fill="{fill}" stroke="{edge_col}" stroke-width="2.0" />

  <!-- Directed edge arrows counter-clockwise -->
  <line x1="80" y1="220" x2="195" y2="220" stroke="{edge_col}" stroke-width="2.0" marker-end="url(#{arr})" />
  <line x1="280" y1="220" x2="225" y2="132" stroke="{edge_col}" stroke-width="2.0" marker-end="url(#{arr})" />
  <line x1="180" y1="60" x2="125" y2="148" stroke="{edge_col}" stroke-width="2.0" marker-end="url(#{arr})" />

  <!-- Vertices 0, 1, 2 -->
  <circle cx="80" cy="220" r="3.6" fill="#fff" stroke="#0f172a" stroke-width="1.6" />
  <text x="60" y="235" class="it" font-weight="bold">P<tspan dy="4" font-size="11">0</tspan></text>

  <circle cx="280" cy="220" r="3.6" fill="#fff" stroke="#0f172a" stroke-width="1.6" />
  <text x="290" y="235" class="it" font-weight="bold">P<tspan dy="4" font-size="11">1</tspan></text>

  <circle cx="180" cy="60" r="3.6" fill="#fff" stroke="#0f172a" stroke-width="1.6" />
  <text x="175" y="45" class="it" font-weight="bold">P<tspan dy="4" font-size="11">2</tspan></text>

  <!-- Induced counter-clockwise orientation symbol in center -->
  <path d="M 195 150 A 18 18 0 1 0 170 160" fill="none" stroke="{'#0f172a' if not colorful else '#dc2626'}" stroke-width="1.8" marker-end="url(#{'arr' if not colorful else 'arr-red'})" />
"""
    return _svg_wrap("0 0 360 270", body, colorful)


# =========================================================================
# Figure 45: Planar Curve gamma with Tangent dot(gamma) and Normal n
# =========================================================================
def generate_fig_45(colorful: bool = False) -> str:
    # Coordinate origin and axes
    ox, oy = 60, 240
    # Point P on curve
    px, py = 190, 130

    curve_col = "#0f172a" if not colorful else "#2563eb"
    tan_col = "#0f172a" if not colorful else "#059669"
    norm_col = "#0f172a" if not colorful else "#dc2626"
    arc_col = "#64748b" if not colorful else "#d97706"
    pt_fill = "#ffffff" if not colorful else "#fef08a"

    body = f"""
  <!-- Axes -->
  <line x1="40" y1="{oy}" x2="360" y2="{oy}" stroke="{'#0f172a' if not colorful else '#334155'}" stroke-width="1.3" marker-end="url(#{'arr' if not colorful else 'arr-axis'})" />
  <text x="368" y="{oy + 5}" class="it">x</text>

  <line x1="{ox}" y1="260" x2="{ox}" y2="40" stroke="{'#0f172a' if not colorful else '#334155'}" stroke-width="1.3" marker-end="url(#{'arr' if not colorful else 'arr-axis'})" />
  <text x="{ox - 18}" y="45" class="it">y</text>
  <text x="{ox - 16}" y="{oy + 18}" class="it">0</text>

  <!-- Curve gamma -->
  <path d="M 100 80 Q 150 160 220 120 T 320 180" fill="none" stroke="{curve_col}" stroke-width="2.4" />
  <text x="330" y="185" class="it" font-weight="bold" fill="{curve_col}">γ</text>

  <!-- Tangent vector dot(gamma) at P -->
  <line x1="{px}" y1="{py}" x2="{px + 70}" y2="{py - 40}" stroke="{tan_col}" stroke-width="2.2" marker-end="url(#{'arr' if not colorful else 'arr-green'})" />
  <text x="{px + 75}" y="{py - 42}" class="it" font-weight="bold" fill="{tan_col}">γ̇</text>

  <!-- Normal vector n perpendicular to tangent -->
  <line x1="{px}" y1="{py}" x2="{px - 40}" y2="{py - 70}" stroke="{norm_col}" stroke-width="2.2" marker-end="url(#{'arr' if not colorful else 'arr-red'})" />
  <text x="{px - 48}" y="{py - 76}" class="it" font-weight="bold" fill="{norm_col}">n</text>

  <!-- Horizontal dashed line from P -->
  <line x1="{px}" y1="{py}" x2="{px + 90}" y2="{py}" class="c-dash" />

  <!-- Angle theta arc between horizontal and tangent -->
  <path d="M {px + 45} {py} A 45 45 0 0 0 {px + 38} {py - 22}" fill="none" stroke="{arc_col}" stroke-width="1.6" />
  <text x="{px + 52}" y="{py - 12}" class="it" fill="{arc_col}">θ</text>

  <!-- Point P -->
  <circle cx="{px}" cy="{py}" r="3.8" fill="{pt_fill}" stroke="#0f172a" stroke-width="1.6" />
  <text x="{px - 15}" y="{py + 18}" class="it" font-weight="bold">P</text>
"""
    return _svg_wrap("0 0 400 290", body, colorful)


# Figure registry: map from figure ID to its generator function
FIGURE_GENERATORS: dict[int, Callable[[bool], str]] = {
    1: generate_fig_1,
    2: generate_fig_2,
    3: generate_fig_3,
    5: generate_fig_5,
    7: generate_fig_7,
    8: generate_fig_8,
    11: generate_fig_11,
    12: generate_fig_12,
    13: generate_fig_13,
    16: generate_fig_16,
    31: generate_fig_31,
    32: generate_fig_32,
    45: generate_fig_45,
}

def generate_modern_geometry_figures(out_dir_mono: Path, out_dir_color: Path) -> None:
    """Generate both monochrome (ordinary) and colorful figures for the monograph editions."""
    out_dir_mono.mkdir(parents=True, exist_ok=True)
    out_dir_color.mkdir(parents=True, exist_ok=True)

    # 1. Generate code-drawn vector SVGs
    for fid, gen in FIGURE_GENERATORS.items():
        svg_mono = gen(False)
        svg_color = gen(True)
        _ = (out_dir_mono / f"fig_{fid}.svg").write_text(svg_mono, encoding="utf-8")
        _ = (out_dir_color / f"fig_{fid}.svg").write_text(svg_color, encoding="utf-8")

