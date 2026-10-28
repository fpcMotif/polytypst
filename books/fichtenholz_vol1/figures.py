"""Vector figures for Fichtenholz Vol. 1: ordinary (publication monochrome), colorful (pedagogical), and Fletcher commutative diagrams."""

import math
from pathlib import Path


def generate_subtangent_svg(colorful: bool = False) -> str:
    ox, oy = 60, 300
    mx = 270
    my_math = 135.0
    my = oy - my_math
    
    tx = 90
    ty = oy
    
    nx = 371.25
    ny = oy
    
    px = mx
    py = oy
    
    t_ext_x = mx + 60
    t_ext_y = my - 60 * 0.75
    
    n_ext_x = mx - 40
    n_ext_y = my - 40 * (4 / 3)
    
    curve_pts: list[str] = []
    for x in range(120, 480, 5):
        dx = x - 270
        ym = 135 + 0.75 * dx + 0.0018 * (dx ** 2)
        yc = oy - ym
        curve_pts.append(f"{x},{yc:.1f}")
    curve_d = "M " + " L ".join(curve_pts)
    
    if not colorful:
        bg = "#ffffff"
        axis_color = "#334155"
        curve_color = "#0f172a"
        curve_fill = "none"
        tangent_color = "#1e293b"
        normal_color = "#1e293b"
        proj_color = "#64748b"
        text_color = "#0f172a"
        sbt_color = "#0f172a"
        sbn_color = "#0f172a"
        pt_fill = "#0f172a"
    else:
        bg = "#f8fafc"
        axis_color = "#475569"
        curve_color = "#2563eb"
        curve_fill = "url(#curve-grad)"
        tangent_color = "#dc2626"
        normal_color = "#059669"
        proj_color = "#64748b"
        text_color = "#0f172a"
        sbt_color = "#d97706"
        sbn_color = "#0891b2"
        pt_fill = "#1e293b"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 355" width="100%" height="100%">
  <defs>
    <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <polygon points="0 0, 6 3, 0 6" fill="{axis_color}" />
    </marker>
    <linearGradient id="curve-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.18" />
      <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.02" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="{bg}" />
  
  {f'<path d="{curve_d} L 475,{oy} L 120,{oy} Z" fill="{curve_fill}" />' if colorful else ''}

  <!-- Coordinate Axes -->
  <line x1="{ox - 20}" y1="{oy}" x2="510" y2="{oy}" stroke="{axis_color}" stroke-width="1.2" marker-end="url(#arr)" />
  <line x1="{ox}" y1="{oy + 20}" x2="{ox}" y2="30" stroke="{axis_color}" stroke-width="1.2" marker-end="url(#arr)" />
  <text x="515" y="{oy + 4}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="14" fill="{text_color}" font-style="italic">x</text>
  <text x="{ox - 4}" y="22" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="14" fill="{text_color}" font-style="italic">y</text>
  <text x="{ox - 14}" y="{oy + 16}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" fill="{text_color}">O</text>

  <!-- Curve y = f(x) -->
  <path d="{curve_d}" fill="none" stroke="{curve_color}" stroke-width="2.2" />
  <text x="440" y="85" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="14" fill="{curve_color}" font-style="italic">y = f(x)</text>

  <!-- Projection Line MP -->
  <line x1="{mx}" y1="{my}" x2="{px}" y2="{py}" stroke="{proj_color}" stroke-width="1.2" stroke-dasharray="4,4" />
  <text x="{mx + 8}" y="{(my + py)/2 + 4:.1f}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" fill="{text_color}" font-style="italic">y</text>

  <!-- Tangent Line TM -->
  <line x1="{tx - 25}" y1="{ty + 25 * 0.75}" x2="{t_ext_x}" y2="{t_ext_y}" stroke="{tangent_color}" stroke-width="1.8" />

  <!-- Normal Line MN -->
  <line x1="{n_ext_x}" y1="{n_ext_y}" x2="{nx + 15}" y2="{ny - 15 * (4/3)}" stroke="{normal_color}" stroke-width="1.8" />

  <!-- Right Angle Symbol at M -->
  <path d="M {mx - 10*0.8 + 10*0.6:.1f},{my - 10*(-0.6) + 10*0.8:.1f} 
           L {mx - 10*0.8 + 10*0.6 + 10*0.8:.1f},{my - 10*(-0.6) + 10*0.8 + 10*(-0.6):.1f} 
           L {mx + 10*0.6:.1f},{my + 10*0.8:.1f}" fill="none" stroke="{text_color}" stroke-width="1.0" />

  <!-- Angle alpha arc at T -->
  <path d="M {tx + 28},{ty} A 28 28 0 0 0 {tx + 28*0.8:.1f},{ty - 28*0.6:.1f}" fill="none" stroke="{text_color}" stroke-width="1.0" />
  <text x="{tx + 34}" y="{ty - 8}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" fill="{text_color}" font-style="italic">α</text>

  <!-- Points and Markers -->
  <circle cx="{mx}" cy="{my}" r="3.5" fill="{pt_fill}" />
  <text x="{mx - 6}" y="{my - 12}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="14" fill="{text_color}" font-weight="bold" font-style="italic">M(x, y)</text>

  <circle cx="{tx}" cy="{ty}" r="3" fill="{pt_fill}" />
  <text x="{tx - 6}" y="{ty + 18}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" fill="{text_color}" font-weight="bold">T</text>

  <circle cx="{px}" cy="{py}" r="3" fill="{pt_fill}" />
  <text x="{px - 4}" y="{py + 18}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" fill="{text_color}" font-weight="bold">P</text>

  <circle cx="{nx:.1f}" cy="{ny}" r="3" fill="{pt_fill}" />
  <text x="{nx - 4:.1f}" y="{ny + 18}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" fill="{text_color}" font-weight="bold">N</text>

  <!-- Subtangent Segment Bar & Label TP -->
  <line x1="{tx}" y1="{ty + 26}" x2="{px}" y2="{py + 26}" stroke="{sbt_color}" stroke-width="1.5" />
  <line x1="{tx}" y1="{ty + 22}" x2="{tx}" y2="{ty + 30}" stroke="{sbt_color}" stroke-width="1.5" />
  <line x1="{px}" y1="{py + 22}" x2="{px}" y2="{py + 30}" stroke="{sbt_color}" stroke-width="1.5" />
  <text x="{(tx + px)/2:.1f}" y="{ty + 42}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="12" fill="{sbt_color}" text-anchor="middle" font-weight="bold">次切矩 sbt = y / y′</text>

  <!-- Subnormal Segment Bar & Label PN -->
  <line x1="{px}" y1="{py + 26}" x2="{nx:.1f}" y2="{ny + 26}" stroke="{sbn_color}" stroke-width="1.5" />
  <line x1="{nx:.1f}" y1="{ny + 22}" x2="{nx:.1f}" y2="{ny + 30}" stroke="{sbn_color}" stroke-width="1.5" />
  <text x="{(px + nx)/2:.1f}" y="{ny + 42}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="12" fill="{sbn_color}" text-anchor="middle" font-weight="bold">次法矩 sbn = y · y′</text>
</svg>"""


def generate_epicycloid_svg(colorful: bool = False) -> str:
    cx, cy = 250, 180
    R = 80.0
    m = 1.0 / 3.0
    r = R * m
    
    pts: list[str] = []
    for step in range(361):
        t = math.radians(step * 3)
        x = (R + r) * math.cos(m * t) - r * math.cos((1 + m) * t)
        y = (R + r) * math.sin(m * t) - r * math.sin((1 + m) * t)
        pts.append(f"{cx + x:.1f},{cy - y:.1f}")
    curve_d = "M " + " L ".join(pts)
    
    t_curr = math.pi / 2.5
    ang_center = m * t_curr
    center_c_x = cx + (R + r) * math.cos(ang_center)
    center_c_y = cy - (R + r) * math.sin(ang_center)
    
    bx = cx + R * math.cos(ang_center)
    by = cy - R * math.sin(ang_center)
    
    mx = cx + (R + r) * math.cos(m * t_curr) - r * math.cos((1 + m) * t_curr)
    my = cy - ((R + r) * math.sin(m * t_curr) - r * math.sin((1 + m) * t_curr))
    
    ax = cx + R
    ay = cy
    
    if not colorful:
        bg = "#ffffff"
        axis_color = "#334155"
        fixed_c_color = "#475569"
        roll_c_color = "#475569"
        curve_color = "#0f172a"
        line_color = "#1e293b"
        text_color = "#0f172a"
        pt_fill = "#0f172a"
    else:
        bg = "#f8fafc"
        axis_color = "#64748b"
        fixed_c_color = "#3b82f6"
        roll_c_color = "#10b981"
        curve_color = "#dc2626"
        line_color = "#6366f1"
        text_color = "#0f172a"
        pt_fill = "#1e293b"
        
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 345" width="100%" height="100%">
  <defs>
    <marker id="arr-epi" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <polygon points="0 0, 6 3, 0 6" fill="{axis_color}" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="{bg}" />

  <!-- Fixed Circle (center O, radius R) -->
  <circle cx="{cx}" cy="{cy}" r="{R}" fill="{fixed_c_color}" fill-opacity="{0.08 if colorful else 0.0}" stroke="{fixed_c_color}" stroke-width="1.6" stroke-dasharray="{ 'none' if not colorful else '4,3' }" />
  <line x1="{cx - 120}" y1="{cy}" x2="{cx + 180}" y2="{cy}" stroke="{axis_color}" stroke-width="1.0" marker-end="url(#arr-epi)" />
  <line x1="{cx}" y1="{cy + 130}" x2="{cx}" y2="{cy - 140}" stroke="{axis_color}" stroke-width="1.0" marker-end="url(#arr-epi)" />
  <text x="{cx + 185}" y="{cy + 4}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" font-style="italic" fill="{text_color}">x</text>
  <text x="{cx - 4}" y="{cy - 145}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" font-style="italic" fill="{text_color}">y</text>
  <text x="{cx - 14}" y="{cy + 15}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" fill="{text_color}">O</text>

  <!-- Rolling Circle (center C, radius r) -->
  <circle cx="{center_c_x:.1f}" cy="{center_c_y:.1f}" r="{r:.1f}" fill="{roll_c_color}" fill-opacity="{0.12 if colorful else 0.0}" stroke="{roll_c_color}" stroke-width="1.5" />
  <circle cx="{center_c_x:.1f}" cy="{center_c_y:.1f}" r="3" fill="{pt_fill}" />
  <text x="{center_c_x + 6:.1f}" y="{center_c_y - 6:.1f}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" font-weight="bold" fill="{text_color}">C</text>

  <!-- Center line OC -->
  <line x1="{cx}" y1="{cy}" x2="{center_c_x:.1f}" y2="{center_c_y:.1f}" stroke="{line_color}" stroke-width="1.2" stroke-dasharray="3,3" />

  <!-- Radii CB and CM -->
  <line x1="{center_c_x:.1f}" y1="{center_c_y:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{roll_c_color}" stroke-width="1.4" />
  <line x1="{center_c_x:.1f}" y1="{center_c_y:.1f}" x2="{mx:.1f}" y2="{my:.1f}" stroke="{roll_c_color}" stroke-width="1.4" />

  <!-- Points A, B, M -->
  <circle cx="{ax}" cy="{ay}" r="3" fill="{pt_fill}" />
  <text x="{ax + 6}" y="{ay + 14}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" font-weight="bold" fill="{text_color}">A</text>

  <circle cx="{bx:.1f}" cy="{by:.1f}" r="3" fill="{pt_fill}" />
  <text x="{bx + 6:.1f}" y="{by + 12:.1f}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="13" font-weight="bold" fill="{text_color}">B</text>

  <circle cx="{mx:.1f}" cy="{my:.1f}" r="4" fill="{curve_color}" />
  <text x="{mx + 8:.1f}" y="{my - 6:.1f}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="14" font-weight="bold" font-style="italic" fill="{curve_color}">M</text>

  <!-- Epicycloid Trajectory Path -->
  <path d="{curve_d}" fill="none" stroke="{curve_color}" stroke-width="2.2" />

  <!-- Angle labels -->
  <text x="{cx + 36}" y="{cy - 8}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="12" fill="{text_color}" font-style="italic">mt</text>
  <text x="{center_c_x - 8:.1f}" y="{center_c_y + 16:.1f}" font-family="New Computer Modern, Latin Modern Roman, serif" font-size="12" fill="{text_color}" font-style="italic">t</text>
</svg>"""


def generate_all_fichtenholz_figures(fig_dir: Path, color_dir: Path | None = None) -> None:
    """Generate both ordinary and colorful vector diagrams."""
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    
    # Ordinary (monochrome) figures
    _ = (fig_dir / "fig_131_subtangent_ordinary.svg").write_text(generate_subtangent_svg(False), encoding="utf-8")
    _ = (fig_dir / "fig_131_subtangent.svg").write_text(generate_subtangent_svg(False), encoding="utf-8")
    _ = (fig_dir / "fig_131.svg").write_text(generate_subtangent_svg(False), encoding="utf-8")
    _ = (fig_dir / "fig_119_epicycloid_ordinary.svg").write_text(generate_epicycloid_svg(False), encoding="utf-8")
    _ = (fig_dir / "fig_119_epicycloid.svg").write_text(generate_epicycloid_svg(False), encoding="utf-8")
    _ = (fig_dir / "fig_119.svg").write_text(generate_epicycloid_svg(False), encoding="utf-8")
    
    # Colorful (pedagogical) figures
    if color_dir is not None:
        color_dir = Path(color_dir)
        color_dir.mkdir(parents=True, exist_ok=True)
        _ = (color_dir / "fig_131_subtangent_color.svg").write_text(generate_subtangent_svg(True), encoding="utf-8")
        _ = (color_dir / "fig_131_subtangent.svg").write_text(generate_subtangent_svg(True), encoding="utf-8")
        _ = (color_dir / "fig_131.svg").write_text(generate_subtangent_svg(True), encoding="utf-8")
        _ = (color_dir / "fig_119_epicycloid_color.svg").write_text(generate_epicycloid_svg(True), encoding="utf-8")
        _ = (color_dir / "fig_119_epicycloid.svg").write_text(generate_epicycloid_svg(True), encoding="utf-8")
        _ = (color_dir / "fig_119.svg").write_text(generate_epicycloid_svg(True), encoding="utf-8")
    
    print(f"Generated figures into {fig_dir} and {color_dir}")
