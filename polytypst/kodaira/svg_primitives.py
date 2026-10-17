import math


def svg_figure(
    viewbox: str,
    *,
    axes: str = "",
    regions: str = "",
    curves: str = "",
    labels: str = "",
    fig_id: str = "",
    title: str = "",
    show_grid: bool = True,
) -> str:
    vb_parts = [float(x) for x in viewbox.split()]
    vw = vb_parts[2] if len(vb_parts) == 4 else 460.0
    vh = vb_parts[3] if len(vb_parts) == 4 else 280.0
    meta_attr = f' data-fig="{fig_id}" role="img"' if fig_id else ' role="img"'
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    title_el = f"  <title>{safe_title}</title>\n" if safe_title else ""
    grid_rects = (
        f'    <rect class="canvas-bg" x="4" y="4" width="{vw - 8:.0f}" height="{vh - 8:.0f}" rx="6" fill="url(#bg-canvas)" />\n'
        f'    <rect class="canvas-grid" x="4" y="4" width="{vw - 8:.0f}" height="{vh - 8:.0f}" rx="6" fill="url(#grid-fine)" />\n'
        if show_grid
        else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="100%" height="100%"{meta_attr}>\n'
        f"{title_el}"
        "  <defs>\n"
        '    <linearGradient id="bg-canvas" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '      <stop offset="0%" stop-color="#f8fafc" stop-opacity="0.5" />\n'
        '      <stop offset="100%" stop-color="#f1f5f9" stop-opacity="0.3" />\n'
        "    </linearGradient>\n"
        '    <linearGradient id="grad-blue" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '      <stop offset="0%" stop-color="#dbeafe" stop-opacity="0.78" />\n'
        '      <stop offset="100%" stop-color="#bfdbfe" stop-opacity="0.48" />\n'
        "    </linearGradient>\n"
        '    <linearGradient id="grad-amber" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '      <stop offset="0%" stop-color="#fef3c7" stop-opacity="0.82" />\n'
        '      <stop offset="100%" stop-color="#fde68a" stop-opacity="0.52" />\n'
        "    </linearGradient>\n"
        '    <linearGradient id="grad-green" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '      <stop offset="0%" stop-color="#d1fae5" stop-opacity="0.78" />\n'
        '      <stop offset="100%" stop-color="#a7f3d0" stop-opacity="0.48" />\n'
        "    </linearGradient>\n"
        '    <linearGradient id="grad-rose" x1="0%" y1="0%" x2="100%" y2="100%">\n'
        '      <stop offset="0%" stop-color="#ffe4e6" stop-opacity="0.78" />\n'
        '      <stop offset="100%" stop-color="#fecdd3" stop-opacity="0.48" />\n'
        "    </linearGradient>\n"
        '    <radialGradient id="glow-pole" cx="50%" cy="50%" r="50%">\n'
        '      <stop offset="0%" stop-color="#ef4444" stop-opacity="0.36" />\n'
        '      <stop offset="100%" stop-color="#ef4444" stop-opacity="0.0" />\n'
        "    </radialGradient>\n"
        '    <pattern id="grid-fine" width="24" height="24" patternUnits="userSpaceOnUse">\n'
        '      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#e2e8f0" stroke-width="0.6" />\n'
        "    </pattern>\n"
        '    <pattern id="stipple" width="6" height="6" patternUnits="userSpaceOnUse">\n'
        '      <circle cx="1.5" cy="1.5" r="0.78" fill="#1e3a8a" opacity="0.38" />\n'
        '      <circle cx="4.5" cy="4.5" r="0.78" fill="#1e3a8a" opacity="0.38" />\n'
        "    </pattern>\n"
        '    <pattern id="stipple-amber" width="6" height="6" patternUnits="userSpaceOnUse">\n'
        '      <circle cx="1.5" cy="1.5" r="0.78" fill="#b45309" opacity="0.38" />\n'
        '      <circle cx="4.5" cy="4.5" r="0.78" fill="#b45309" opacity="0.38" />\n'
        "    </pattern>\n"
        '    <pattern id="hatch" width="7" height="7" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">\n'
        '      <line x1="0" y1="0" x2="0" y2="7" stroke="#1e3a8a" stroke-width="1.2" opacity="0.38" />\n'
        "    </pattern>\n"
        '    <pattern id="hatch-border" width="5" height="5" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">\n'
        '      <line x1="0" y1="0" x2="0" y2="5" stroke="#475569" stroke-width="1.15" opacity="0.45" />\n'
        "    </pattern>\n"
        '    <marker id="arr" viewBox="0 0 10 10" refX="6.8" refY="5" markerWidth="5.6" markerHeight="5.6" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.2 L 8.8 5 L 0 8.8 L 2.2 5 z" fill="#0f172a" />\n'
        "    </marker>\n"
        '    <marker id="arr-axis" viewBox="0 0 10 10" refX="7.0" refY="5" markerWidth="5.2" markerHeight="5.2" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.5 L 8.5 5 L 0 8.5 L 2.0 5 z" fill="#475569" />\n'
        "    </marker>\n"
        '    <marker id="arr-blue" viewBox="0 0 10 10" refX="6.8" refY="5" markerWidth="5.6" markerHeight="5.6" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.2 L 8.8 5 L 0 8.8 L 2.2 5 z" fill="#1e3a8a" />\n'
        "    </marker>\n"
        '    <marker id="arr-red" viewBox="0 0 10 10" refX="6.8" refY="5" markerWidth="5.6" markerHeight="5.6" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.2 L 8.8 5 L 0 8.8 L 2.2 5 z" fill="#dc2626" />\n'
        "    </marker>\n"
        '    <marker id="arr-green" viewBox="0 0 10 10" refX="6.8" refY="5" markerWidth="5.6" markerHeight="5.6" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.2 L 8.8 5 L 0 8.8 L 2.2 5 z" fill="#047857" />\n'
        "    </marker>\n"
        '    <marker id="arr-amber" viewBox="0 0 10 10" refX="6.8" refY="5" markerWidth="5.6" markerHeight="5.6" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.2 L 8.8 5 L 0 8.8 L 2.2 5 z" fill="#b45309" />\n'
        "    </marker>\n"
        "  </defs>\n"
        "  <style>\n"
        "    .ax { stroke: #475569; stroke-width: 1.15; fill: none; }\n"
        "    .c-main { stroke: #0f172a; stroke-width: 1.8; fill: none; stroke-linecap: round; stroke-linejoin: round; }\n"
        "    .c-blue { stroke: #1e3a8a; stroke-width: 1.8; fill: none; stroke-linecap: round; stroke-linejoin: round; }\n"
        "    .c-red { stroke: #dc2626; stroke-width: 1.65; fill: none; stroke-linecap: round; stroke-linejoin: round; }\n"
        "    .c-green { stroke: #047857; stroke-width: 1.7; fill: none; stroke-linecap: round; stroke-linejoin: round; }\n"
        "    .c-amber { stroke: #b45309; stroke-width: 1.65; fill: none; stroke-linecap: round; stroke-linejoin: round; }\n"
        "    .c-dash { stroke: #64748b; stroke-width: 1.15; stroke-dasharray: 5,4; fill: none; }\n"
        "    .c-blue-dash { stroke: #1e3a8a; stroke-width: 1.25; stroke-dasharray: 5,4; fill: none; }\n"
        "    .c-red-dash { stroke: #dc2626; stroke-width: 1.25; stroke-dasharray: 4,3; fill: none; }\n"
        "    .c-green-dash { stroke: #047857; stroke-width: 1.25; stroke-dasharray: 4,3; fill: none; }\n"
        "    .c-sub { stroke: #64748b; stroke-width: 0.9; fill: none; }\n"
        "    .f-blue { fill: url(#grad-blue); }\n"
        "    .f-amber { fill: url(#grad-amber); }\n"
        "    .f-green { fill: url(#grad-green); }\n"
        "    .f-rose { fill: url(#grad-rose); }\n"
        "    .f-stipple { fill: url(#stipple); }\n"
        "    .f-hatch { fill: url(#hatch); }\n"
        "    .pt { stroke: #ffffff; stroke-width: 1.25; }\n"
        "    .pt-open { fill: #ffffff; stroke-width: 1.5; }\n"
        '    .lbl { font-family: "New Computer Modern", "Latin Modern Roman", "STIX Two Math", Georgia, serif; font-size: 14.5px; fill: #0f172a; paint-order: stroke fill; stroke: #ffffff; stroke-width: 3.2px; stroke-linejoin: round; }\n'
        '    .it { font-family: "New Computer Modern", "Latin Modern Roman", "STIX Two Math", Georgia, serif; font-size: 15px; font-style: italic; fill: #0f172a; paint-order: stroke fill; stroke: #ffffff; stroke-width: 3.2px; stroke-linejoin: round; }\n'
        "  </style>\n"
        f'  <g class="layer-grid" data-layer="grid" data-step="1">\n{grid_rects}{axes}\n  </g>\n'
        f'  <g class="layer-region" data-layer="region" data-step="2">\n{regions}\n  </g>\n'
        f'  <g class="layer-curve" data-layer="curve" data-step="3">\n{curves}\n  </g>\n'
        f'  <g class="layer-label" data-layer="label" data-step="4">\n{labels}\n  </g>\n'
        "</svg>"
    )


def axes_xy(
    ox: float,
    oy: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    x_label: str = "x",
    y_label: str = "iy",
    origin_label: str = "0",
    origin_dx: float = -13.0,
    origin_dy: float = 15.0,
) -> tuple[str, str]:
    ax_parts = [
        f'    <line x1="{x0:.1f}" y1="{oy:.1f}" x2="{x1:.1f}" y2="{oy:.1f}" class="ax" marker-end="url(#arr-axis)" />',
        f'    <line x1="{ox:.1f}" y1="{y1:.1f}" x2="{ox:.1f}" y2="{y0:.1f}" class="ax" marker-end="url(#arr-axis)" />',
    ]
    lbl_parts: list[str] = []
    if x_label:
        lbl_parts.append(
            f'    <text x="{x1 + 5:.1f}" y="{oy + 5:.1f}" class="it">{x_label}</text>'
        )
    if y_label:
        lbl_parts.append(
            f'    <text x="{ox - 18:.1f}" y="{y0 + 4:.1f}" class="it">{y_label}</text>'
        )
    if origin_label:
        lbl_parts.append(
            f'    <text x="{ox + origin_dx:.1f}" y="{oy + origin_dy:.1f}" class="lbl">{origin_label}</text>'
        )
    return "\n".join(ax_parts), "\n".join(lbl_parts)


def arrow_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    cls: str = "c-main",
    marker: str = "arr",
    both: bool = False,
) -> str:
    m_start = f' marker-start="url(#{marker})"' if both else ""
    m_end = f' marker-end="url(#{marker})"' if marker else ""
    return f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}"{m_start}{m_end} />'


def tangent_arrow(
    x: float,
    y: float,
    dx: float,
    dy: float,
    marker: str = "arr-blue",
) -> str:
    norm = math.hypot(dx, dy)
    if norm < 1e-6:
        return ""
    ux, uy = dx / norm, dy / norm
    x0, y0 = x - ux * 2.5, y - uy * 2.5
    x1, y1 = x + ux * 1.5, y + uy * 1.5
    return f'    <line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" stroke="none" fill="none" marker-end="url(#{marker})" />'


def mid_arrow_path(
    d: str,
    mx: float,
    my: float,
    dx: float,
    dy: float,
    cls: str = "c-blue",
    marker: str = "arr-blue",
) -> str:
    p = f'    <path d="{d}" class="{cls}" />'
    t = tangent_arrow(mx, my, dx, dy, marker=marker)
    return f"{p}\n{t}" if t else p


def circle_contour(
    cx: float,
    cy: float,
    r: float,
    cls: str = "c-blue",
    fill_cls: str = "",
    arrow_deg: float | None = None,
    ccw: bool = True,
    marker: str = "arr-blue",
) -> str:
    parts: list[str] = []
    if fill_cls:
        parts.append(
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="{fill_cls}" />'
        )
    parts.append(
        f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="{cls}" />'
    )
    if arrow_deg is not None:
        rad = math.radians(arrow_deg)
        px = cx + r * math.cos(rad)
        py = cy - r * math.sin(rad)
        sgn = 1.0 if ccw else -1.0
        dx = -sgn * math.sin(rad)
        dy = -sgn * math.cos(rad)
        parts.append(tangent_arrow(px, py, dx, dy, marker=marker))
    return "\n".join(parts)


def arc_path(
    cx: float,
    cy: float,
    r: float,
    deg1: float,
    deg2: float,
    cls: str = "c-blue",
    ccw: bool = True,
    arrow_mid: bool = False,
    marker: str = "arr-blue",
) -> str:
    r1 = math.radians(deg1)
    r2 = math.radians(deg2)
    x1, y1 = cx + r * math.cos(r1), cy - r * math.sin(r1)
    x2, y2 = cx + r * math.cos(r2), cy - r * math.sin(r2)
    span = (deg2 - deg1) % 360.0 if ccw else (deg1 - deg2) % 360.0
    large_arc = 1 if span > 180.0 else 0
    sweep = 0 if ccw else 1
    d = f"M {x1:.2f} {y1:.2f} A {r:.2f} {r:.2f} 0 {large_arc} {sweep} {x2:.2f} {y2:.2f}"
    if not arrow_mid:
        return f'    <path d="{d}" class="{cls}" />'
    mid_deg = deg1 + (span * 0.5 if ccw else -span * 0.5)
    rm = math.radians(mid_deg)
    mx, my = cx + r * math.cos(rm), cy - r * math.sin(rm)
    sgn = 1.0 if ccw else -1.0
    dx, dy = -sgn * math.sin(rm), -sgn * math.cos(rm)
    return mid_arrow_path(d, mx, my, dx, dy, cls=cls, marker=marker)


def smooth_curve(
    points: list[tuple[float, float]],
    cls: str = "c-blue",
    closed: bool = False,
    fill_cls: str = "",
    arrow_indices: list[tuple[int, bool]] | None = None,
    marker: str = "arr-blue",
) -> str:
    if len(points) < 2:
        return ""
    pts = list(points)
    n = len(pts)
    if closed:
        padded = [pts[-1]] + pts + [pts[0], pts[1]]
        count = n
    else:
        padded = [pts[0]] + pts + [pts[-1]]
        count = n - 1

    segs: list[str] = [f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"]
    mid_arrows: list[str] = []
    arrow_map = dict(arrow_indices or [])

    for i in range(count):
        p0, p1, p2, p3 = padded[i], padded[i + 1], padded[i + 2], padded[i + 3]
        c1x = p1[0] + (p2[0] - p0[0]) / 6.0
        c1y = p1[1] + (p2[1] - p0[1]) / 6.0
        c2x = p2[0] - (p3[0] - p1[0]) / 6.0
        c2y = p2[1] - (p3[1] - p1[1]) / 6.0
        segs.append(
            f"C {c1x:.2f} {c1y:.2f}, {c2x:.2f} {c2y:.2f}, {p2[0]:.2f} {p2[1]:.2f}"
        )
        if i in arrow_map:
            forward = arrow_map[i]
            mx = 0.125 * p1[0] + 0.375 * c1x + 0.375 * c2x + 0.125 * p2[0]
            my = 0.125 * p1[1] + 0.375 * c1y + 0.375 * c2y + 0.125 * p2[1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            if not forward:
                dx, dy = -dx, -dy
            mid_arrows.append(tangent_arrow(mx, my, dx, dy, marker=marker))

    if closed:
        segs.append("Z")
    d = " ".join(segs)
    out: list[str] = []
    if fill_cls:
        out.append(f'    <path d="{d}" class="{fill_cls}" />')
    out.append(f'    <path d="{d}" class="{cls}" />')
    out.extend(mid_arrows)
    return "\n".join(out)


def point_dot(
    x: float,
    y: float,
    color: str = "#0f172a",
    r: float = 3.3,
    open_dot: bool = False,
) -> str:
    if open_dot:
        return f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" stroke="{color}" class="pt-open" />'
    return f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" class="pt" />'


def math_label(
    x: float,
    y: float,
    base: str,
    sub: str = "",
    sup: str = "",
    tail: str = "",
    color: str = "#0f172a",
    italic: bool = True,
    anchor: str = "start",
    size: float = 15.0,
) -> str:
    cls = "it" if italic else "lbl"
    fill_attr = f' fill="{color}"' if color != "#0f172a" else ""
    anchor_attr = f' text-anchor="{anchor}"' if anchor != "start" else ""
    size_attr = f' font-size="{size:.1f}px"' if abs(size - 15.0) > 0.2 else ""
    inner = base
    if sub:
        inner += f'<tspan font-size="10.5px" dy="3.2">{sub}</tspan>'
        if sup:
            inner += f'<tspan font-size="10.5px" dy="-8.2">{sup}</tspan>'
            if tail:
                inner += f'<tspan dy="5.0">{tail}</tspan>'
        elif tail:
            inner += f'<tspan dy="-3.2">{tail}</tspan>'
    elif sup:
        inner += f'<tspan font-size="10.5px" dy="-5.0">{sup}</tspan>'
        if tail:
            inner += f'<tspan dy="5.0">{tail}</tspan>'
    elif tail:
        inner += tail
    return f'    <text x="{x:.1f}" y="{y:.1f}" class="{cls}"{fill_attr}{anchor_attr}{size_attr}>{inner}</text>'
