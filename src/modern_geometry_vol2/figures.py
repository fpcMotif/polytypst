"""Parametric vector illustrations for Modern Geometry: Methods and Applications. Part II.

Provides both Ordinary (crisp monochrome publication vector matching Springer GTM)
and Colorful (rich, high-contrast, pedagogical 3Blue1Brown style vector with gradients
and semantic hues) editions for the monograph figures.
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
    <marker id="arr-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 L 2 5 z" fill="#0284c7" />
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
    <radialGradient id="sphere-grad" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#f0f9ff" stop-opacity="0.95" />
      <stop offset="60%" stop-color="#bae6fd" stop-opacity="0.65" />
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.30" />
    </radialGradient>
    <radialGradient id="hemi-grad" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#e0f2fe" stop-opacity="0.9" />
      <stop offset="70%" stop-color="#bae6fd" stop-opacity="0.7" />
      <stop offset="100%" stop-color="#7dd3fc" stop-opacity="0.4" />
    </radialGradient>
    <linearGradient id="torus-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fef3c7" stop-opacity="0.85" />
      <stop offset="50%" stop-color="#fde68a" stop-opacity="0.60" />
      <stop offset="100%" stop-color="#f59e0b" stop-opacity="0.30" />
    </linearGradient>
    <linearGradient id="mobius-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#e0e7ff" stop-opacity="0.85" />
      <stop offset="50%" stop-color="#c7d2fe" stop-opacity="0.65" />
      <stop offset="100%" stop-color="#818cf8" stop-opacity="0.40" />
    </linearGradient>
    <linearGradient id="singularity-grad" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#fee2e2" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#ef4444" stop-opacity="0.2" />
    </linearGradient>
    <pattern id="hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#2563eb" stroke-width="1.1" opacity="0.65" />
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
    .lbl {{ font-size: 15px; fill: #0f172a; }}
    .it {{ font-size: 16px; font-style: italic; fill: #0f172a; }}
  </style>
{content}
</svg>"""


# =========================================================================
# Figure 1: Stereographic Projection of the Sphere
# =========================================================================
def generate_fig_1(colorful: bool = False) -> str:
    cx, cy, r = 220, 150, 100
    np_x, np_y = cx, cy - r
    sp_x, sp_y = cx, cy + r

    sphere_fill = "none" if not colorful else "url(#sphere-grad)"
    plane_col = "#64748b" if not colorful else "#0284c7"
    ray_col = "#0f172a" if not colorful else "#dc2626"
    pt_fill = "#ffffff" if not colorful else "#fde047"

    pe_ry = 32
    angle = math.radians(40)
    pt_x = cx + r * math.cos(angle)
    pt_y = cy - r * math.sin(angle) * 0.85

    t = (cy - np_y) / (pt_y - np_y)
    proj_x = np_x + t * (pt_x - np_x)

    body = f"""
  <polygon points="50,150 140,210 390,210 300,150" fill="{'#f8fafc' if not colorful else '#e0f2fe'}" stroke="{plane_col}" stroke-width="1.2" opacity="0.7" />
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{sphere_fill}" stroke="#0f172a" stroke-width="1.6" />
  <ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{pe_ry}" fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="5,4" />
  <line x1="{cx}" y1="{cy - r - 25}" x2="{cx}" y2="{cy + r + 25}" class="c-dash" />
  <line x1="{np_x}" y1="{np_y}" x2="{proj_x}" y2="{cy}" stroke="{ray_col}" stroke-width="1.6" />
  <circle cx="{proj_x}" cy="{cy}" r="3.5" fill="{pt_fill}" stroke="{ray_col}" stroke-width="1.5" />
  <text x="{proj_x + 8}" y="{cy + 15}" class="it">u_N(x)</text>
  <circle cx="{pt_x}" cy="{pt_y}" r="3.8" fill="{pt_fill}" stroke="#0f172a" stroke-width="1.5" />
  <text x="{pt_x + 8}" y="{pt_y - 6}" class="it">x</text>
  <circle cx="{np_x}" cy="{np_y}" r="3.6" fill="{pt_fill}" stroke="#0f172a" stroke-width="1.5" />
  <text x="{np_x - 18}" y="{np_y - 8}" class="lbl" font-weight="bold">N</text>
  <circle cx="{sp_x}" cy="{sp_y}" r="3.6" fill="{pt_fill}" stroke="#0f172a" stroke-width="1.5" />
  <text x="{sp_x - 18}" y="{sp_y + 18}" class="lbl" font-weight="bold">S</text>
"""
    return _svg_wrap("0 0 440 300", body, colorful)


# =========================================================================
# Figure 2: Identification of Antipodal Points: RP1 ~ S1
# =========================================================================
def generate_fig_2(colorful: bool = False) -> str:
    cx, cy, r = 160, 100, 65
    c_lower = "#0f172a" if not colorful else "#2563eb"
    c_upper = "#64748b" if not colorful else "#38bdf8"
    c_wavy = "#0f172a" if not colorful else "#f59e0b"

    # Wavy line along diameter from cx - r to cx + r
    wave_d = f"M {cx - r} {cy} "
    steps = 8
    dx = (2 * r) / steps
    for i in range(steps):
        sign = 1 if i % 2 == 0 else -1
        x_mid = cx - r + (i + 0.5) * dx
        x_end = cx - r + (i + 1) * dx
        wave_d += f"Q {x_mid} {cy + sign * 5} {x_end} {cy} "

    b_cx, b_cy, b_r = cx, 235, 36

    body = f"""
  <!-- Upper coordinate axes -->
  <line x1="{cx - r - 35}" y1="{cy}" x2="{cx + r + 35}" y2="{cy}" stroke="#64748b" stroke-width="1.2" marker-end="url(#arr)" />
  <line x1="{cx}" y1="{cy + r + 25}" x2="{cx}" y2="{cy - r - 25}" stroke="#64748b" stroke-width="1.2" marker-end="url(#arr)" />
  <text x="{cx + r + 28}" y="{cy + 18}" class="it">x</text>
  <text x="{cx - 16}" y="{cy - r - 15}" class="it">y</text>

  <!-- Circle: Upper half dashed, lower half solid -->
  <path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{c_upper}" stroke-width="2.0" stroke-dasharray="5,4" />
  <path d="M {cx - r} {cy} A {r} {r} 0 0 0 {cx + r} {cy}" fill="none" stroke="{c_lower}" stroke-width="2.2" />

  <!-- Wavy diameter -->
  <path d="{wave_d}" fill="none" stroke="{c_wavy}" stroke-width="1.8" />

  <!-- Antipodal asterisk points -->
  <circle cx="{cx + 46}" cy="{cy - 46}" r="3.2" fill="none" stroke="#0f172a" stroke-width="1.5" />
  <text x="{cx + 38}" y="{cy - 40}" class="lbl" font-size="20px">∗</text>

  <circle cx="{cx - 46}" cy="{cy + 46}" r="3.2" fill="none" stroke="#0f172a" stroke-width="1.5" />
  <text x="{cx - 54}" y="{cy + 52}" class="lbl" font-size="20px">∗</text>

  <!-- Endpoints -1 and 1 -->
  <circle cx="{cx - r}" cy="{cy}" r="3.4" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" />
  <text x="{cx - r - 22}" y="{cy + 6}" class="lbl">-1</text>
  <circle cx="{cx + r}" cy="{cy}" r="3.4" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" />
  <text x="{cx + r + 8}" y="{cy + 6}" class="lbl">1</text>

  <!-- Downward arrow -->
  <line x1="{cx}" y1="{cy + r + 10}" x2="{cx}" y2="{b_cy - b_r - 12}" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr)" />

  <!-- Bottom quotient circle S1 -->
  <circle cx="{b_cx}" cy="{b_cy}" r="{b_r}" fill="{'none' if not colorful else '#dbeafe'}" stroke="{c_lower}" stroke-width="2.2" />
  <circle cx="{b_cx}" cy="{b_cy - b_r}" r="3.6" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" />
  <text x="{b_cx - 24}" y="{b_cy - b_r - 8}" class="lbl" font-weight="bold">-1 = 1</text>
"""
    return _svg_wrap("0 0 320 290", body, colorful)


# =========================================================================
# Figure 3: The Real Projective Plane RP2 as Lower Hemisphere D2
# =========================================================================
def generate_fig_3(colorful: bool = False) -> str:
    cx, cy = 190, 150
    rx, ry = 110, 36
    r_bowl = 100

    bowl_fill = "none" if not colorful else "url(#hemi-grad)"
    axis_col = "#64748b" if not colorful else "#475569"
    rad_col = "#0f172a" if not colorful else "#dc2626"

    # Radial arrows on the boundary equator identifying antipodal points
    arrows: list[str] = []
    num_arrows = 10
    for i in range(num_arrows):
        theta = (2 * math.pi * i) / num_arrows
        ax = cx + (rx - 4) * math.cos(theta)
        ay = cy + (ry - 4) * math.sin(theta)
        arr_marker = "arr" if not colorful else "arr-red"
        arrows.append(f'<line x1="{cx}" y1="{cy}" x2="{ax}" y2="{ay}" stroke="{rad_col}" stroke-width="1.3" marker-end="url(#{arr_marker})" />')

    arrows_svg = "\n  ".join(arrows)

    body = f"""
  <!-- 3D Axes -->
  <!-- z axis -->
  <line x1="{cx}" y1="{cy + r_bowl + 30}" x2="{cx}" y2="35" stroke="{axis_col}" stroke-width="1.4" marker-end="url(#arr)" />
  <text x="{cx - 16}" y="32" class="it">z</text>
  
  <!-- x axis (down-left) -->
  <line x1="{cx}" y1="{cy}" x2="{cx - 130}" y2="{cy + 75}" stroke="{axis_col}" stroke-width="1.4" marker-end="url(#arr)" />
  <text x="{cx - 146}" y="{cy + 82}" class="it">x</text>

  <!-- y axis (right-up) -->
  <line x1="{cx}" y1="{cy}" x2="{cx + 145}" y2="{cy - 55}" stroke="{axis_col}" stroke-width="1.4" marker-end="url(#arr)" />
  <text x="{cx + 152}" y="{cy - 52}" class="it">y</text>

  <!-- Lower hemisphere bowl -->
  <path d="M {cx - rx} {cy} A {rx} {r_bowl} 0 0 0 {cx + rx} {cy}" fill="{bowl_fill}" stroke="#0f172a" stroke-width="2.2" />

  <!-- Equator boundary disk (ellipse) -->
  <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{'#f8fafc' if not colorful else '#fef9c3'}" stroke="#0f172a" stroke-width="2.0" opacity="0.85" />

  <!-- Radial arrows showing antipodal identification -->
  {arrows_svg}

  <!-- Origin -->
  <circle cx="{cx}" cy="{cy}" r="3.2" fill="#ffffff" stroke="#0f172a" stroke-width="1.5" />
"""
    return _svg_wrap("0 0 380 300", body, colorful)


# =========================================================================
# Figure 11: The Torus Embedded in R3
# =========================================================================
def generate_fig_11(colorful: bool = False) -> str:
    cx, cy = 230, 150
    rx_out, ry_out = 160, 95
    rx_in, ry_in = 65, 38

    torus_fill = "none" if not colorful else "url(#torus-grad)"
    curve_col = "#0f172a" if not colorful else "#2563eb"
    merid_col = "#64748b" if not colorful else "#dc2626"

    body = f"""
  <ellipse cx="{cx}" cy="{cy}" rx="{rx_out}" ry="{ry_out}" fill="{torus_fill}" stroke="#0f172a" stroke-width="2.0" />
  <path d="M {cx - rx_in} {cy - 4} Q {cx} {cy + ry_in + 8} {cx + rx_in} {cy - 4}" fill="none" stroke="#0f172a" stroke-width="1.8" />
  <path d="M {cx - rx_in + 12} {cy + 6} Q {cx} {cy - ry_in - 2} {cx + rx_in - 12} {cy + 6}" fill="none" stroke="#0f172a" stroke-width="1.6" />
  <ellipse cx="{cx}" cy="{cy + 25}" rx="135" ry="32" fill="none" stroke="{curve_col}" stroke-width="1.8" stroke-dasharray="6,4" />
  <text x="{cx + 140}" y="{cy + 30}" class="it" fill="{curve_col}">β</text>
  <ellipse cx="{cx - 100}" cy="{cy}" rx="24" ry="72" fill="none" stroke="{merid_col}" stroke-width="1.8" />
  <text x="{cx - 138}" y="{cy - 40}" class="it" fill="{merid_col}">α</text>
  <line x1="{cx - 100}" y1="{cy - 72}" x2="{cx - 70}" y2="{cy - 72}" stroke="{'#0f172a' if not colorful else '#059669'}" stroke-width="2.0" marker-end="url(#{'arr' if not colorful else 'arr-green'})" />
  <text x="{cx - 65}" y="{cy - 78}" class="it" fill="{'#0f172a' if not colorful else '#059669'}">ξ</text>
"""
    return _svg_wrap("0 0 460 300", body, colorful)


# =========================================================================
# Figure 12: Smooth Bump Function with Compact Support
# =========================================================================
def generate_fig_12(colorful: bool = False) -> str:
    ox, oy = 210, 180
    ax_x1, ax_x2 = 40, 380
    ax_y_top = 45

    curve_col = "#0f172a" if not colorful else "#2563eb"
    area_fill = "none" if not colorful else "#dbeafe"

    body = f"""
  <line x1="{ax_x1}" y1="{oy}" x2="{ax_x2}" y2="{oy}" stroke="#334155" stroke-width="1.4" marker-end="url(#arr)" />
  <line x1="{ox}" y1="{oy + 25}" x2="{ox}" y2="{ax_y_top}" stroke="#334155" stroke-width="1.4" marker-end="url(#arr)" />
  <text x="{ax_x2 + 8}" y="{oy + 5}" class="it">t</text>
  <text x="{ox - 22}" y="{ax_y_top + 5}" class="it">φ(t)</text>
  <text x="{ox - 14}" y="{oy + 18}" class="lbl">0</text>
  <line x1="{ox - 110}" y1="{oy - 4}" x2="{ox - 110}" y2="{oy + 4}" stroke="#334155" stroke-width="1.2" />
  <text x="{ox - 118}" y="{oy + 20}" class="lbl">-1</text>
  <line x1="{ox + 110}" y1="{oy - 4}" x2="{ox + 110}" y2="{oy + 4}" stroke="#334155" stroke-width="1.2" />
  <text x="{ox + 106}" y="{oy + 20}" class="lbl">1</text>
  <line x1="{ox - 4}" y1="{oy - 95}" x2="{ox + 4}" y2="{oy - 95}" stroke="#334155" stroke-width="1.2" />
  <text x="{ox - 18}" y="{oy - 92}" class="lbl">1</text>
  <path d="M 50 {oy} L {ox - 110} {oy} C {ox - 65} {oy}, {ox - 75} {oy - 95}, {ox - 40} {oy - 95} L {ox + 40} {oy - 95} C {ox + 75} {oy - 95}, {ox + 65} {oy}, {ox + 110} {oy} L 370 {oy}" 
        fill="{area_fill}" stroke="{curve_col}" stroke-width="2.2" stroke-linecap="round" />
"""
    return _svg_wrap("0 0 420 230", body, colorful)


# =========================================================================
# Figure 19: Transversal Intersection of Submanifolds
# =========================================================================
def generate_fig_19(colorful: bool = False) -> str:
    surf_fill = "none" if not colorful else "#f1f5f9"
    sub_fill = "none" if not colorful else "#fef08a"
    sub_col = "#0f172a" if not colorful else "#d97706"
    fM_col = "#0f172a" if not colorful else "#2563eb"

    body = f"""
  <path d="M 40 80 Q 200 40 380 90 L 340 250 Q 180 280 20 220 Z" fill="{surf_fill}" stroke="#64748b" stroke-width="1.2" />
  <text x="350" y="80" class="it" font-weight="bold">N</text>
  <path d="M 190 70 L 250 110 L 210 240 L 150 200 Z" fill="{sub_fill}" stroke="{sub_col}" stroke-width="1.8" opacity="0.8" />
  <text x="140" y="215" class="it" fill="{sub_col}" font-weight="bold">P</text>
  <path d="M 70 170 Q 200 130 330 180" fill="none" stroke="{fM_col}" stroke-width="2.4" />
  <text x="335" y="185" class="it" fill="{fM_col}" font-weight="bold">f(M)</text>
  <circle cx="200" cy="147" r="4.2" fill="#ffffff" stroke="#dc2626" stroke-width="2.0" />
  <text x="206" y="142" class="it" fill="#dc2626" font-weight="bold">f(x)</text>
  <line x1="200" y1="147" x2="260" y2="135" stroke="{fM_col}" stroke-width="1.8" marker-end="url(#{'arr' if not colorful else 'arr-blue'})" />
  <text x="264" y="132" class="it" fill="{fM_col}">df(T_x M)</text>
  <line x1="200" y1="147" x2="175" y2="95" stroke="{sub_col}" stroke-width="1.8" marker-end="url(#{'arr' if not colorful else 'arr-amber'})" />
  <text x="142" y="92" class="it" fill="{sub_col}">T_{{f(x)}} P</text>
"""
    return _svg_wrap("0 0 420 280", body, colorful)


# =========================================================================
# Figure 40: Phase Portraits of Vector Fields (Saddle, Node, Focus, Center)
# =========================================================================
def generate_fig_40(colorful: bool = False) -> str:
    c_saddle = "#0f172a" if not colorful else "#dc2626"
    c_node = "#0f172a" if not colorful else "#2563eb"
    c_focus = "#0f172a" if not colorful else "#059669"
    c_center = "#0f172a" if not colorful else "#7c3aed"

    body = f"""
  <g transform="translate(10, 10)">
    <rect x="0" y="0" width="180" height="150" fill="none" stroke="#cbd5e1" stroke-width="1.0" rx="4" />
    <text x="12" y="24" class="lbl" font-weight="bold">(a) Saddle (ind = -1)</text>
    <line x1="15" y1="75" x2="165" y2="75" stroke="#94a3b8" stroke-width="1.0" />
    <line x1="90" y1="15" x2="90" y2="135" stroke="#94a3b8" stroke-width="1.0" />
    <path d="M 30 35 Q 80 70 80 20" fill="none" stroke="{c_saddle}" stroke-width="1.4" marker-mid="url(#arr)" />
    <path d="M 150 35 Q 100 70 100 20" fill="none" stroke="{c_saddle}" stroke-width="1.4" />
    <path d="M 30 115 Q 80 80 80 130" fill="none" stroke="{c_saddle}" stroke-width="1.4" />
    <path d="M 150 115 Q 100 80 100 130" fill="none" stroke="{c_saddle}" stroke-width="1.4" />
    <circle cx="90" cy="75" r="3.2" fill="#ffffff" stroke="{c_saddle}" stroke-width="1.5" />
  </g>
  <g transform="translate(210, 10)">
    <rect x="0" y="0" width="180" height="150" fill="none" stroke="#cbd5e1" stroke-width="1.0" rx="4" />
    <text x="12" y="24" class="lbl" font-weight="bold">(b) Node (ind = +1)</text>
    <line x1="15" y1="75" x2="165" y2="75" stroke="#94a3b8" stroke-width="1.0" />
    <line x1="90" y1="15" x2="90" y2="135" stroke="#94a3b8" stroke-width="1.0" />
    <line x1="90" y1="75" x2="145" y2="40" stroke="{c_node}" stroke-width="1.4" marker-end="url(#{'arr' if not colorful else 'arr-blue'})" />
    <line x1="90" y1="75" x2="145" y2="110" stroke="{c_node}" stroke-width="1.4" marker-end="url(#{'arr' if not colorful else 'arr-blue'})" />
    <line x1="90" y1="75" x2="35" y2="40" stroke="{c_node}" stroke-width="1.4" marker-end="url(#{'arr' if not colorful else 'arr-blue'})" />
    <line x1="90" y1="75" x2="35" y2="110" stroke="{c_node}" stroke-width="1.4" marker-end="url(#{'arr' if not colorful else 'arr-blue'})" />
    <circle cx="90" cy="75" r="3.2" fill="#ffffff" stroke="{c_node}" stroke-width="1.5" />
  </g>
  <g transform="translate(10, 180)">
    <rect x="0" y="0" width="180" height="150" fill="none" stroke="#cbd5e1" stroke-width="1.0" rx="4" />
    <text x="12" y="24" class="lbl" font-weight="bold">(c) Focus (ind = +1)</text>
    <line x1="15" y1="75" x2="165" y2="75" stroke="#94a3b8" stroke-width="1.0" />
    <line x1="90" y1="15" x2="90" y2="135" stroke="#94a3b8" stroke-width="1.0" />
    <path d="M 90 75 Q 94 65 102 75 Q 110 90 90 95 Q 65 95 65 70 Q 65 40 100 40 Q 140 40 140 85" fill="none" stroke="{c_focus}" stroke-width="1.5" marker-end="url(#{'arr' if not colorful else 'arr-green'})" />
    <circle cx="90" cy="75" r="3.2" fill="#ffffff" stroke="{c_focus}" stroke-width="1.5" />
  </g>
  <g transform="translate(210, 180)">
    <rect x="0" y="0" width="180" height="150" fill="none" stroke="#cbd5e1" stroke-width="1.0" rx="4" />
    <text x="12" y="24" class="lbl" font-weight="bold">(d) Center (ind = +1)</text>
    <line x1="15" y1="75" x2="165" y2="75" stroke="#94a3b8" stroke-width="1.0" />
    <line x1="90" y1="15" x2="90" y2="135" stroke="#94a3b8" stroke-width="1.0" />
    <ellipse cx="90" cy="75" rx="25" ry="18" fill="none" stroke="{c_center}" stroke-width="1.4" />
    <ellipse cx="90" cy="75" rx="50" ry="36" fill="none" stroke="{c_center}" stroke-width="1.4" />
    <ellipse cx="90" cy="75" rx="72" ry="52" fill="none" stroke="{c_center}" stroke-width="1.4" />
    <circle cx="90" cy="75" r="3.2" fill="#ffffff" stroke="{c_center}" stroke-width="1.5" />
  </g>
"""
    return _svg_wrap("0 0 400 340", body, colorful)


# =========================================================================
# Figure 47: The Möbius Strip
# =========================================================================
def generate_fig_47(colorful: bool = False) -> str:
    mob_fill = "none" if not colorful else "url(#mobius-grad)"
    line_col = "#0f172a" if not colorful else "#4338ca"
    mid_col = "#64748b" if not colorful else "#dc2626"

    body = f"""
  <path d="M 60 140 C 60 80, 180 60, 240 110 C 290 150, 360 210, 320 230 C 270 250, 140 230, 90 190 Z" 
        fill="{mob_fill}" stroke="{line_col}" stroke-width="1.8" />
  <path d="M 75 145 C 95 95, 200 90, 250 135 C 290 170, 310 210, 250 215 C 180 220, 90 185, 75 145 Z" 
        fill="none" stroke="{mid_col}" stroke-width="1.5" stroke-dasharray="5,4" />
  <line x1="85" y1="120" x2="85" y2="70" stroke="{'#0f172a' if not colorful else '#059669'}" stroke-width="2.0" marker-end="url(#{'arr' if not colorful else 'arr-green'})" />
  <text x="60" y="65" class="it" fill="{'#0f172a' if not colorful else '#059669'}">v</text>
  <line x1="85" y1="120" x2="85" y2="170" stroke="{'#0f172a' if not colorful else '#dc2626'}" stroke-width="2.0" marker-end="url(#{'arr' if not colorful else 'arr-red'})" />
  <text x="56" y="185" class="it" fill="{'#0f172a' if not colorful else '#dc2626'}">-v</text>
"""
    return _svg_wrap("0 0 400 260", body, colorful)


# =========================================================================
# Figure 55: Bouquet of Two Circles (Figure Eight)
# =========================================================================
def generate_fig_55(colorful: bool = False) -> str:
    c1_col = "#0f172a" if not colorful else "#2563eb"
    c2_col = "#0f172a" if not colorful else "#059669"
    pt_fill = "#ffffff" if not colorful else "#fde047"

    body = f"""
  <circle cx="130" cy="120" r="60" fill="{'none' if not colorful else '#dbeafe'}" stroke="{c1_col}" stroke-width="2.2" />
  <path d="M 130 60 L 126 53 L 136 60 L 126 67 Z" fill="{c1_col}" />
  <text x="124" y="45" class="it" fill="{c1_col}" font-weight="bold">a</text>
  <circle cx="270" cy="120" r="60" fill="{'none' if not colorful else '#d1fae5'}" stroke="{c2_col}" stroke-width="2.2" />
  <path d="M 270 60 L 266 53 L 276 60 L 266 67 Z" fill="{c2_col}" />
  <text x="266" y="45" class="it" fill="{c2_col}" font-weight="bold">b</text>
  <circle cx="200" cy="120" r="4.5" fill="{pt_fill}" stroke="#0f172a" stroke-width="2.0" />
  <text x="194" y="145" class="it" font-weight="bold">x₀</text>
"""
    return _svg_wrap("0 0 400 210", body, colorful)


# =========================================================================
# Figure 56: The Bouquet S1 v S2
# =========================================================================
def generate_fig_56(colorful: bool = False) -> str:
    s2_col = "#0f172a" if not colorful else "#0284c7"
    s1_col = "#0f172a" if not colorful else "#2563eb"
    sphere_fill = "none" if not colorful else "url(#sphere-grad)"
    cx_s, cy_s, r_s = 250, 140, 65

    body = f"""
  <!-- Sphere S2 -->
  <circle cx="{cx_s}" cy="{cy_s}" r="{r_s}" fill="{sphere_fill}" stroke="{s2_col}" stroke-width="2.0" />
  <ellipse cx="{cx_s}" cy="{cy_s}" rx="{r_s}" ry="20" fill="none" stroke="{s2_col}" stroke-width="1.2" stroke-dasharray="4,3" />
  <text x="{cx_s + r_s + 10}" y="{cy_s + 6}" class="it" font-weight="bold">S²</text>

  <!-- Circle S1 attached at base point x0 -->
  <circle cx="{cx_s - r_s - 45}" cy="{cy_s}" r="45" fill="{'none' if not colorful else '#fef08a'}" stroke="{s1_col}" stroke-width="2.2" />
  <text x="{cx_s - r_s - 95}" y="{cy_s + 6}" class="it" font-weight="bold">S¹</text>

  <!-- Common base point -->
  <circle cx="{cx_s - r_s}" cy="{cy_s}" r="4.5" fill="#ffffff" stroke="#dc2626" stroke-width="2.0" />
  <text x="{cx_s - r_s - 8}" y="{cy_s + 22}" class="it" font-weight="bold">x₀</text>
"""
    return _svg_wrap("0 0 380 260", body, colorful)


# =========================================================================
# Figure 104: Limit Cycle & Poincaré Return Map
# =========================================================================
def generate_fig_104(colorful: bool = False) -> str:
    cx, cy = 200, 130
    lc_col = "#0f172a" if not colorful else "#2563eb"
    sec_col = "#64748b" if not colorful else "#dc2626"
    traj_col = "#0f172a" if not colorful else "#059669"

    body = f"""
  <ellipse cx="{cx}" cy="{cy}" rx="90" ry="60" fill="none" stroke="{lc_col}" stroke-width="2.5" />
  <text x="{cx + 60}" y="{cy - 50}" class="it" fill="{lc_col}" font-weight="bold">γ₀</text>
  <line x1="{cx}" y1="{cy - 85}" x2="{cx}" y2="{cy + 15}" stroke="{sec_col}" stroke-width="2.0" stroke-linecap="round" />
  <text x="{cx + 8}" y="{cy - 75}" class="it" fill="{sec_col}" font-weight="bold">T</text>
  <circle cx="{cx}" cy="{cy - 40}" r="3.5" fill="#ffffff" stroke="{sec_col}" stroke-width="1.6" />
  <text x="{cx - 20}" y="{cy - 36}" class="it">r</text>
  <circle cx="{cx}" cy="{cy - 52}" r="3.5" fill="#ffffff" stroke="{sec_col}" stroke-width="1.6" />
  <text x="{cx - 32}" y="{cy - 50}" class="it">f(r)</text>
  <path d="M {cx} {cy - 40} C {cx + 70} {cy - 40}, {cx + 105} {cy}, {cx + 80} {cy + 45} C {cx + 50} {cy + 75}, {cx - 70} {cy + 75}, {cx - 95} {cy + 30} C {cx - 110} {cy - 30}, {cx - 50} {cy - 60}, {cx} {cy - 52}"
        fill="none" stroke="{traj_col}" stroke-width="1.6" stroke-dasharray="5,3" marker-end="url(#{'arr' if not colorful else 'arr-green'})" />
"""
    return _svg_wrap("0 0 400 240", body, colorful)


# =========================================================================
# Figure 115: Kruskal-Szekeres Space-Time Diagram (Schwarzschild Black Hole)
# =========================================================================
def generate_fig_115(colorful: bool = False) -> str:
    ox, oy = 210, 160
    span = 120

    horiz_col = "#64748b" if not colorful else "#0284c7"
    sing_col = "#dc2626"
    sing_fill = "none" if not colorful else "url(#singularity-grad)"
    wline_col = "#0f172a" if not colorful else "#d97706"

    body = f"""
  <path d="M {ox - span} {oy - span + 20} Q {ox} {oy - 45} {ox + span} {oy - span + 20} L {ox + span} {oy - span - 10} L {ox - span} {oy - span - 10} Z"
        fill="{sing_fill}" stroke="none" />
  <path d="M {ox - span} {oy - span + 20} Q {ox} {oy - 45} {ox + span} {oy - span + 20}"
        fill="none" stroke="{sing_col}" stroke-width="2.5" stroke-dasharray="4,3" />
  <text x="{ox - 40}" y="{oy - 60}" class="lbl" fill="{sing_col}" font-weight="bold">r = 0 (Singularity)</text>
  <line x1="{ox - span}" y1="{oy + span}" x2="{ox + span}" y2="{oy - span}" stroke="{horiz_col}" stroke-width="1.8" />
  <line x1="{ox - span}" y1="{oy - span}" x2="{ox + span}" y2="{oy + span}" stroke="{horiz_col}" stroke-width="1.8" />
  <line x1="{ox - span - 20}" y1="{oy}" x2="{ox + span + 20}" y2="{oy}" class="ax" marker-end="url(#arr)" />
  <line x1="{ox}" y1="{oy + span + 20}" x2="{ox}" y2="{oy - span - 25}" class="ax" marker-end="url(#arr)" />
  <text x="{ox + span + 25}" y="{oy + 5}" class="it">R</text>
  <text x="{ox - 18}" y="{oy - span - 20}" class="it">τ</text>
  <text x="{ox + 75}" y="{oy + 6}" class="lbl" font-weight="bold" font-size="18px">I</text>
  <text x="{ox - 85}" y="{oy + 6}" class="lbl" font-weight="bold" font-size="18px">I′</text>
  <text x="{ox - 6}" y="{oy - 30}" class="lbl" font-weight="bold" font-size="18px">II</text>
  <text x="{ox - 8}" y="{oy + 45}" class="lbl" font-weight="bold" font-size="18px">II′</text>
  <path d="M {ox + 60} {oy + 90} Q {ox + 45} {oy} {ox + 60} {oy - 90}"
        fill="none" stroke="{wline_col}" stroke-width="2.0" marker-mid="url(#{'arr' if not colorful else 'arr-amber'})" />
  <text x="{ox + 70}" y="{oy - 70}" class="it" fill="{wline_col}">r = const.</text>
"""
    return _svg_wrap("0 0 420 320", body, colorful)


# Figure registry: map from figure ID to its generator function
FIGURE_GENERATORS: dict[int, Callable[[bool], str]] = {
    1: generate_fig_1,
    2: generate_fig_2,
    3: generate_fig_3,
    11: generate_fig_11,
    12: generate_fig_12,
    19: generate_fig_19,
    40: generate_fig_40,
    47: generate_fig_47,
    55: generate_fig_55,
    56: generate_fig_56,
    104: generate_fig_104,
    115: generate_fig_115,
}


def generate_modern_geometry_vol2_figures(out_dir_mono: Path, out_dir_color: Path) -> None:
    """Generate both monochrome (ordinary) and colorful figures for the monograph editions."""
    out_dir_mono.mkdir(parents=True, exist_ok=True)
    out_dir_color.mkdir(parents=True, exist_ok=True)

    # 1. Generate code-drawn vector SVGs
    for fid, gen in FIGURE_GENERATORS.items():
        svg_mono = gen(False)
        svg_color = gen(True)
        _ = (out_dir_mono / f"fig_{fid}.svg").write_text(svg_mono, encoding="utf-8")
        _ = (out_dir_color / f"fig_{fid}.svg").write_text(svg_color, encoding="utf-8")

