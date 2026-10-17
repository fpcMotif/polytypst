import math


def _svg_wrap(viewbox: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="100%" height="100%">\n'
        "  <defs>\n"
        '    <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0f172a" />\n'
        "    </marker>\n"
        '    <marker id="arr-blue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1e3a8a" />\n'
        "    </marker>\n"
        '    <marker id="arr-red" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">\n'
        '      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#dc2626" />\n'
        "    </marker>\n"
        '    <pattern id="hatch" width="7" height="7" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">\n'
        '      <line x1="0" y1="0" x2="0" y2="7" stroke="#1e3a8a" stroke-width="1.4" opacity="0.45" />\n'
        "    </pattern>\n"
        '    <pattern id="hatch-border" width="5" height="5" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">\n'
        '      <line x1="0" y1="0" x2="0" y2="5" stroke="#475569" stroke-width="1.3" opacity="0.55" />\n'
        "    </pattern>\n"
        '    <pattern id="stipple" width="6" height="6" patternUnits="userSpaceOnUse">\n'
        '      <circle cx="1.5" cy="1.5" r="0.85" fill="#1e3a8a" opacity="0.45" />\n'
        '      <circle cx="4.5" cy="4.5" r="0.85" fill="#1e3a8a" opacity="0.45" />\n'
        "    </pattern>\n"
        "  </defs>\n"
        "  <style>\n"
        "    .ax { stroke: #64748b; stroke-width: 1.15; fill: none; }\n"
        "    .c-main { stroke: #0f172a; stroke-width: 1.75; fill: none; }\n"
        "    .c-blue { stroke: #1e3a8a; stroke-width: 1.65; fill: none; }\n"
        "    .c-red { stroke: #dc2626; stroke-width: 1.55; fill: none; }\n"
        "    .c-green { stroke: #047857; stroke-width: 1.65; fill: none; }\n"
        "    .c-dash { stroke: #475569; stroke-width: 1.3; stroke-dasharray: 5,4; fill: none; }\n"
        "    .c-red-dash { stroke: #dc2626; stroke-width: 1.4; stroke-dasharray: 4,3; fill: none; }\n"
        "    .f-blue { fill: #dbeafe; fill-opacity: 0.65; }\n"
        "    .f-amber { fill: #fef3c7; fill-opacity: 0.72; }\n"
        "    .f-green { fill: #d1fae5; fill-opacity: 0.65; }\n"
        '    .lbl { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 15px; fill: #0f172a; }\n'
        '    .it { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 15px; font-style: italic; fill: #0f172a; }\n'
        "  </style>\n"
        f"{body}\n"
        "</svg>"
    )


def generate_fig_3_4() -> str:
    cx, cy = 230, 145
    parts = [
        f'<line x1="30" y1="{cy}" x2="430" y2="{cy}" class="ax" />',
        f'<line x1="{cx}" y1="15" x2="{cx}" y2="275" class="ax" />',
    ]
    for r in (28, 56, 92):
        parts.append(f'<circle cx="{cx}" cy="{cy - r}" r="{r}" class="c-blue" />')
        parts.append(f'<circle cx="{cx}" cy="{cy + r}" r="{r}" class="c-blue" />')
        parts.append(f'<circle cx="{cx - r}" cy="{cy}" r="{r}" class="c-red" />')
        parts.append(f'<circle cx="{cx + r}" cy="{cy}" r="{r}" class="c-red" />')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="3.2" fill="#0f172a" />')
    return _svg_wrap("0 0 460 290", "\n".join(parts))


def generate_fig_3_5() -> str:
    cx, cy = 230, 145
    parts = [
        f'<line x1="30" y1="{cy}" x2="430" y2="{cy}" class="ax" />',
        f'<line x1="{cx}" y1="15" x2="{cx}" y2="275" class="ax" />',
        f'<line x1="100" y1="{cy - 130}" x2="360" y2="{cy + 130}" class="c-dash" />',
        f'<line x1="100" y1="{cy + 130}" x2="360" y2="{cy - 130}" class="c-dash" />',
    ]
    for a in (28, 55, 84):
        for sgn in (-1, 1):
            pts1 = []
            pts2 = []
            for k in range(-22, 23):
                t = k * 0.065
                x = sgn * a * math.cosh(t)
                y = a * math.sinh(t)
                if abs(x) <= 165 and abs(y) <= 122:
                    pts1.append(f"{cx + x:.1f},{cy - y:.1f}")
                    pts2.append(f"{cx + y:.1f},{cy - x:.1f}")
            if len(pts1) > 2:
                parts.append(f'<polyline points="{" ".join(pts1)}" class="c-blue" />')
            if len(pts2) > 2:
                parts.append(f'<polyline points="{" ".join(pts2)}" class="c-red" />')
            pts3 = []
            pts4 = []
            for k in range(-22, 23):
                t = k * 0.065
                u = sgn * a * math.cosh(t)
                v = a * math.sinh(t)
                xr = (u - v) / math.sqrt(2)
                yr = (u + v) / math.sqrt(2)
                if abs(xr) <= 165 and abs(yr) <= 122:
                    pts3.append(f"{cx + xr:.1f},{cy - yr:.1f}")
                    pts4.append(f"{cx + yr:.1f},{cy - xr:.1f}")
            if len(pts3) > 2:
                parts.append(
                    f'<polyline points="{" ".join(pts3)}" class="c-green" stroke-opacity="0.75" />'
                )
            if len(pts4) > 2:
                parts.append(
                    f'<polyline points="{" ".join(pts4)}" class="c-green" stroke-opacity="0.75" />'
                )
    return _svg_wrap("0 0 460 290", "\n".join(parts))


def generate_fig_3_6() -> str:
    cx, cy = 230, 145
    parts = [
        f'<line x1="30" y1="{cy}" x2="430" y2="{cy}" class="ax" />',
        f'<line x1="{cx}" y1="15" x2="{cx}" y2="275" class="ax" />',
    ]
    for c in (3.2, 5.2, 7.2, 9.2):
        pts_r = []
        pts_l = []
        for k in range(-25, 26):
            y = k * 4.8
            x_r = c * c - (y * y) / (4.0 * c * c)
            x_l = -c * c + (y * y) / (4.0 * c * c)
            if abs(x_r) <= 180 and abs(y) <= 122:
                pts_r.append(f"{cx + x_r:.1f},{cy - y:.1f}")
            if abs(x_l) <= 180 and abs(y) <= 122:
                pts_l.append(f"{cx + x_l:.1f},{cy - y:.1f}")
        if len(pts_r) > 2:
            parts.append(f'<polyline points="{" ".join(pts_r)}" class="c-blue" />')
        if len(pts_l) > 2:
            parts.append(f'<polyline points="{" ".join(pts_l)}" class="c-red" />')
    return _svg_wrap("0 0 460 290", "\n".join(parts))


def generate_fig_3_7() -> str:
    cx, cy = 230, 145
    parts = [
        f'<line x1="40" y1="{cy}" x2="420" y2="{cy}" class="ax" />',
        f'<line x1="{cx}" y1="15" x2="{cx}" y2="275" class="ax" />',
    ]
    for deg in (30, 60, 120, 150):
        rad = math.radians(deg)
        dx, dy = 135 * math.cos(rad), 135 * math.sin(rad)
        parts.append(
            f'<line x1="{cx - dx:.1f}" y1="{cy + dy:.1f}" x2="{cx + dx:.1f}" y2="{cy - dy:.1f}" class="c-dash" />'
        )
    for sec in range(6):
        base_deg = sec * 60.0
        for r0 in (36.0, 64.0):
            pts = []
            for k in range(-23, 24):
                deg = base_deg + k * 1.15
                rad = math.radians(deg)
                c3 = abs(math.cos(3.0 * rad))
                if c3 > 0.08:
                    r = r0 / (c3 ** (1.0 / 3.0))
                    if r <= 135:
                        pts.append(
                            f"{cx + r * math.cos(rad):.1f},{cy - r * math.sin(rad):.1f}"
                        )
            if len(pts) > 2:
                cls = "c-blue" if sec % 2 == 0 else "c-red"
                parts.append(f'<polyline points="{" ".join(pts)}" class="{cls}" />')
    return _svg_wrap("0 0 460 290", "\n".join(parts))


def generate_fig_3_8() -> str:
    body = """
  <path d="M 110 20 C 122 105, 165 182, 225 182 C 262 182, 262 108, 225 108 C 165 108, 122 185, 110 270" class="c-blue" stroke-width="2" />
  <circle cx="222" cy="145" r="4" fill="#dc2626" />
"""
    return _svg_wrap("0 0 360 290", body)


def generate_fig_3_10() -> str:
    body = """
  <line x1="30" y1="45" x2="120" y2="45" class="c-blue" stroke-width="2" />
  <line x1="120" y1="45" x2="295" y2="45" class="c-blue" stroke-width="2" />
  <line x1="295" y1="45" x2="325" y2="68" class="c-red" stroke-width="2" />
  <line x1="325" y1="68" x2="430" y2="68" class="c-blue" stroke-width="2" />

  <line x1="30" y1="68" x2="115" y2="68" class="c-blue" stroke-width="2" />
  <line x1="115" y1="68" x2="145" y2="91" class="c-red" stroke-width="2" />
  <line x1="145" y1="91" x2="295" y2="91" class="c-blue" stroke-width="2" />
  <line x1="295" y1="68" x2="325" y2="45" class="c-red" stroke-width="2" />
  <line x1="325" y1="45" x2="430" y2="45" class="c-blue" stroke-width="2" />

  <line x1="30" y1="91" x2="115" y2="91" class="c-blue" stroke-width="2" />
  <line x1="115" y1="91" x2="145" y2="68" class="c-red" stroke-width="2" />
  <line x1="145" y1="68" x2="295" y2="68" class="c-blue" stroke-width="2" />
  <line x1="295" y1="91" x2="325" y2="108" class="c-red" stroke-width="1.8" />
  <line x1="295" y1="108" x2="325" y2="91" class="c-red" stroke-width="1.8" />
  <line x1="325" y1="91" x2="430" y2="91" class="c-blue" stroke-width="2" />
"""
    return _svg_wrap("0 0 460 135", body)


def generate_fig_3_11() -> str:
    body = """
  <rect x="90" y="135" width="70" height="115" class="f-blue" />
  <rect x="90" y="135" width="70" height="115" fill="url(#hatch)" />
  <rect x="160" y="20" width="70" height="115" class="f-blue" />
  <rect x="160" y="20" width="70" height="115" fill="url(#hatch)" />
  <rect x="230" y="135" width="70" height="115" class="f-blue" />
  <rect x="230" y="135" width="70" height="115" fill="url(#hatch)" />
  <rect x="300" y="20" width="70" height="115" class="f-blue" />
  <rect x="300" y="20" width="70" height="115" fill="url(#hatch)" />
  <line x1="40" y1="135" x2="420" y2="135" class="c-main" />
  <line x1="90" y1="20" x2="90" y2="250" class="c-main" />
  <line x1="160" y1="20" x2="160" y2="250" class="c-main" />
  <line x1="230" y1="20" x2="230" y2="250" class="c-main" />
  <line x1="300" y1="20" x2="300" y2="250" class="c-main" />
  <line x1="370" y1="20" x2="370" y2="250" class="c-main" />
  <text x="76" y="152" class="lbl">−2π</text>
  <text x="142" y="152" class="lbl">−π</text>
  <text x="220" y="152" class="lbl">0</text>
  <text x="290" y="152" class="lbl">π</text>
  <text x="374" y="152" class="lbl">2π</text>
"""
    return _svg_wrap("0 0 460 270", body)


def generate_fig_4_1() -> str:
    body = """
  <path d="M 75 185 C 55 140, 110 120, 175 128 C 215 132, 222 105, 228 72 C 236 32, 315 20, 385 45 C 435 65, 435 125, 375 135 C 315 145, 295 165, 275 205 C 252 248, 115 245, 75 185 Z" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <polyline points="145,172 265,172 265,88 345,88" class="c-red" stroke-width="2" />
  <circle cx="145" cy="172" r="3.5" fill="#0f172a" />
  <circle cx="345" cy="88" r="3.5" fill="#0f172a" />
  <text x="115" y="192" class="it">(x<tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">, y</tspan><tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">)</tspan></text>
  <text x="354" y="93" class="it">(x, y)</text>
  <text x="274" y="132" class="it" fill="#dc2626">γ</text>
"""
    return _svg_wrap("0 0 460 260", body)


def generate_fig_4_2() -> str:
    body = """
  <rect x="80" y="35" width="300" height="190" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <line x1="230" y1="35" x2="230" y2="225" class="c-main" />
  <line x1="80" y1="130" x2="380" y2="130" class="c-main" />
  <!-- R1 top-left, R2 top-right, R3 bottom-left, R4 bottom-right -->
  <text x="142" y="88" class="it">R<tspan font-size="10px" dy="-6">(1)</tspan></text>
  <text x="292" y="88" class="it">R<tspan font-size="10px" dy="-6">(2)</tspan></text>
  <text x="142" y="182" class="it">R<tspan font-size="10px" dy="-6">(3)</tspan></text>
  <text x="292" y="182" class="it">R<tspan font-size="10px" dy="-6">(4)</tspan></text>
  <text x="62" y="28" class="it">(a, d)</text>
  <text x="366" y="28" class="it">(b, d)</text>
  <text x="62" y="244" class="it">(a, c)</text>
  <text x="366" y="244" class="it">(b, c)</text>
  <!-- Edge orientation arrows -->
  <line x1="175" y1="43" x2="140" y2="43" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="325" y1="43" x2="290" y2="43" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="140" y1="217" x2="175" y2="217" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="290" y1="217" x2="325" y2="217" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="88" y1="68" x2="88" y2="98" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="88" y1="162" x2="88" y2="192" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="372" y1="98" x2="372" y2="68" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="372" y1="192" x2="372" y2="162" class="c-blue" marker-end="url(#arr-blue)" />
  <!-- Interior canceling arrows -->
  <line x1="140" y1="123" x2="175" y2="123" class="c-red" marker-end="url(#arr-red)" />
  <line x1="175" y1="137" x2="140" y2="137" class="c-red" marker-end="url(#arr-red)" />
  <line x1="290" y1="123" x2="325" y2="123" class="c-red" marker-end="url(#arr-red)" />
  <line x1="325" y1="137" x2="290" y2="137" class="c-red" marker-end="url(#arr-red)" />
  <line x1="223" y1="98" x2="223" y2="68" class="c-red" marker-end="url(#arr-red)" />
  <line x1="237" y1="68" x2="237" y2="98" class="c-red" marker-end="url(#arr-red)" />
  <line x1="223" y1="192" x2="223" y2="162" class="c-red" marker-end="url(#arr-red)" />
  <line x1="237" y1="162" x2="237" y2="192" class="c-red" marker-end="url(#arr-red)" />
"""
    return _svg_wrap("0 0 460 258", body)


def generate_fig_4_3() -> str:
    body = """
  <rect x="85" y="25" width="290" height="210" fill="#f8fafc" stroke="#0f172a" stroke-width="1.8" />
  <line x1="182" y1="25" x2="182" y2="235" class="c-dash" />
  <line x1="278" y1="25" x2="278" y2="235" class="c-dash" />
  <line x1="85" y1="95" x2="375" y2="95" class="c-dash" />
  <line x1="85" y1="165" x2="375" y2="165" class="c-dash" />
  <rect x="182" y="95" width="96" height="70" class="f-amber" stroke="#1e3a8a" stroke-width="2" />
  <circle cx="226" cy="132" r="3.5" fill="#dc2626" />
  <text x="234" y="136" class="it" fill="#dc2626">ζ</text>
"""
    return _svg_wrap("0 0 460 260", body)


def generate_fig_4_4() -> str:
    body = """
  <circle cx="230" cy="135" r="110" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <polyline points="230,135 230,118 292,118 292,78" class="c-main" stroke-width="1.8" />
  <polyline points="230,135 250,135 250,78 292,78" class="c-red-dash" />
  <circle cx="230" cy="135" r="3.2" fill="#0f172a" />
  <circle cx="272" cy="105" r="3.5" fill="#dc2626" />
  <circle cx="292" cy="78" r="3.2" fill="#0f172a" />
  <text x="178" y="152" class="it">(x<tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">, y</tspan><tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">)</tspan></text>
  <text x="278" y="108" class="it" fill="#dc2626">ζ</text>
  <text x="298" y="78" class="it">z</text>
"""
    return _svg_wrap("0 0 460 270", body)


def generate_fig_4_5() -> str:
    body = """
  <line x1="50" y1="150" x2="410" y2="150" class="ax" />
  <line x1="230" y1="20" x2="210" y2="275" class="ax" />
  <path d="M 115 150 C 122 85, 178 65, 224 68 C 258 70, 295 32, 338 58 C 378 82, 362 175, 310 198 C 268 216, 240 205, 214 222 C 165 252, 108 215, 115 150 Z" class="c-blue" stroke-width="1.8" />
  <circle cx="230" cy="150" r="44" class="c-green" />
  <circle cx="230" cy="150" r="3" fill="#0f172a" />
  <circle cx="224" cy="68" r="3.2" fill="#dc2626" />
  <circle cx="226" cy="106" r="3.2" fill="#dc2626" />
  <circle cx="216" cy="194" r="3.2" fill="#dc2626" />
  <circle cx="214" cy="222" r="3.2" fill="#dc2626" />
  <text x="234" y="164" class="it">O</text>
  <text x="229" y="18" class="it">L<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="195" y="278" class="it">L<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="230" y="64" class="it">z<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="232" y="102" class="it">ζ<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="223" y="192" class="it">ζ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="220" y="234" class="it">z<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="232" y="90" class="it" fill="#dc2626">δ<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="222" y="212" class="it" fill="#dc2626">δ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="278" y="138" class="it" fill="#047857">C<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="168" y="138" class="it" fill="#047857">C<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="348" y="172" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="92" y="145" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">2</tspan></text>
"""
    return _svg_wrap("0 0 460 288", body)


def generate_fig_4_6() -> str:
    body = """
  <line x1="35" y1="165" x2="435" y2="165" class="ax" />
  <line x1="95" y1="165" x2="225" y2="75" class="c-dash" />
  <line x1="95" y1="165" x2="195" y2="222" class="c-dash" />
  <path d="M 178 165 C 188 138, 208 102, 225 75 C 248 38, 305 32, 332 68 C 355 98, 282 135, 285 165 C 288 192, 318 190, 328 162 C 336 142, 358 142, 362 165 C 368 205, 295 238, 235 245 C 198 248, 185 215, 205 195 C 222 178, 172 182, 178 165 Z" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <circle cx="95" cy="165" r="3.2" fill="#0f172a" />
  <circle cx="178" cy="165" r="3.2" fill="#dc2626" />
  <circle cx="362" cy="165" r="3.2" fill="#dc2626" />
  <circle cx="225" cy="75" r="3.2" fill="#047857" />
  <circle cx="195" cy="222" r="3.2" fill="#047857" />
  <text x="82" y="182" class="it">O</text>
  <text x="158" y="182" class="it">x<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="368" y="182" class="it">x<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="232" y="75" class="it">z<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="202" y="226" class="it">z<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="184" y="125" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="342" y="95" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">2</tspan></text>
"""
    return _svg_wrap("0 0 460 268", body)


def generate_fig_4_7() -> str:
    body = """
  <!-- Left: circle gamma around z0 -->
  <circle cx="115" cy="135" r="65" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <circle cx="115" cy="135" r="3.5" fill="#0f172a" />
  <text x="108" y="152" class="it">z<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="186" y="138" class="it" fill="#1e3a8a">γ</text>

  <!-- Right: image curve Gamma and delta-disk around w0 -->
  <path d="M 255 135 C 252 72, 335 45, 395 62 C 445 78, 442 155, 385 185 C 325 215, 258 195, 255 135 C 252 85, 355 32, 378 95 C 398 152, 342 212, 288 185 C 258 168, 256 152, 255 135 Z" class="c-blue" stroke-width="1.75" />
  <circle cx="332" cy="138" r="52" class="f-amber" stroke="#dc2626" stroke-width="1.6" />
  <circle cx="332" cy="138" r="3.5" fill="#0f172a" />
  <circle cx="318" cy="114" r="3.5" fill="#dc2626" />
  <line x1="332" y1="138" x2="375" y2="166" class="c-red" marker-end="url(#arr-red)" />
  <text x="320" y="155" class="it">w<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="326" y="116" class="it" fill="#dc2626">a</text>
  <text x="355" y="146" class="it" fill="#dc2626">δ</text>
  <text x="436" y="84" class="it" fill="#1e3a8a">Γ</text>
  <text x="312" y="232" class="lbl"><tspan class="it">w</tspan>‑plane</text>
"""
    return _svg_wrap("0 0 470 250", body)


def generate_fig_4_8() -> str:
    body = """
  <!-- w-plane -->
  <circle cx="85" cy="110" r="54" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <line x1="85" y1="110" x2="139" y2="110" class="c-red" stroke-width="2" />
  <circle cx="85" cy="110" r="3.2" fill="#0f172a" />
  <text x="58" y="192" class="lbl"><tspan class="it">w</tspan>‑plane</text>

  <!-- zeta-plane -->
  <circle cx="240" cy="110" r="54" class="f-amber" stroke="#b45309" stroke-width="1.8" />
  <line x1="240" y1="110" x2="294" y2="110" class="c-red" stroke-width="1.8" />
  <line x1="240" y1="110" x2="213" y2="63" class="c-red" stroke-width="1.8" />
  <line x1="240" y1="110" x2="213" y2="157" class="c-red" stroke-width="1.8" />
  <circle cx="240" cy="110" r="3.2" fill="#0f172a" />
  <text x="215" y="192" class="lbl"><tspan class="it">ζ</tspan>‑plane</text>

  <!-- z-plane -->
  <path d="M 352 125 C 345 75, 385 45, 422 58 C 455 70, 452 128, 425 155 C 395 182, 358 165, 352 125 Z" class="f-green" stroke="#047857" stroke-width="1.8" />
  <path d="M 402 112 Q 425 118 446 104" class="c-red" stroke-width="1.8" />
  <path d="M 402 112 Q 392 85 375 68" class="c-red" stroke-width="1.8" />
  <path d="M 402 112 Q 388 138 368 152" class="c-red" stroke-width="1.8" />
  <circle cx="402" cy="112" r="3.2" fill="#0f172a" />
  <text x="378" y="192" class="lbl"><tspan class="it">z</tspan>‑plane</text>
"""
    return _svg_wrap("0 0 480 215", body)


def generate_fig_4_9() -> str:
    body = """
  <path d="M 65 140 C 55 58, 155 25, 265 32 C 375 40, 405 95, 392 165 C 378 232, 268 252, 155 242 C 82 235, 72 195, 65 140 Z" fill="url(#hatch-border)" />
  <path d="M 92 140 C 85 75, 168 48, 258 54 C 348 60, 372 105, 362 162 C 350 212, 258 228, 165 220 C 105 215, 98 182, 92 140 Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" />
  <ellipse cx="222" cy="142" rx="76" ry="48" class="f-blue" />
  <ellipse cx="222" cy="142" rx="76" ry="48" fill="url(#stipple)" stroke="#1e3a8a" stroke-width="1.5" />
  <!-- Grid of squares covering A -->
  <g stroke="#0f172a" stroke-width="1.1" fill="none">
    <rect x="130" y="86" width="184" height="112" />
    <line x1="176" y1="86" x2="176" y2="198" />
    <line x1="222" y1="86" x2="222" y2="198" />
    <line x1="268" y1="86" x2="268" y2="198" />
    <line x1="130" y1="124" x2="314" y2="124" />
    <line x1="130" y1="161" x2="314" y2="161" />
  </g>
  <circle cx="242" cy="136" r="3" fill="#dc2626" />
  <text x="248" y="140" class="it" fill="#dc2626">a</text>
  <text x="182" y="156" class="it" fill="#1e3a8a">A</text>
  <text x="320" y="165" class="it">γ</text>
  <text x="366" y="176" class="it">B</text>
"""
    return _svg_wrap("0 0 450 265", body)


def generate_fig_4_10() -> str:
    body = """
  <path d="M 85 150 C 78 65, 165 22, 265 28 C 345 34, 368 95, 385 145 C 402 198, 345 255, 245 258 C 142 260, 92 215, 85 150 Z" fill="url(#hatch-border)" />
  <path d="M 105 150 C 98 78, 175 40, 260 45 C 330 50, 348 102, 365 145 C 380 190, 330 238, 242 240 C 155 242, 112 202, 105 150 Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.5" />
  <polygon points="135,95 165,95 165,65 285,65 285,95 315,95 315,125 345,125 345,185 315,185 315,215 165,215 165,185 135,185" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <g stroke="#64748b" stroke-width="0.7" opacity="0.65">
    <line x1="165" y1="65" x2="165" y2="215" />
    <line x1="195" y1="65" x2="195" y2="215" />
    <line x1="225" y1="65" x2="225" y2="215" />
    <line x1="255" y1="65" x2="255" y2="215" />
    <line x1="285" y1="65" x2="285" y2="215" />
    <line x1="315" y1="95" x2="315" y2="215" />
    <line x1="135" y1="95" x2="315" y2="95" />
    <line x1="135" y1="125" x2="345" y2="125" />
    <line x1="135" y1="155" x2="345" y2="155" />
    <line x1="135" y1="185" x2="345" y2="185" />
  </g>
  <rect x="225" y="95" width="30" height="30" class="f-amber" stroke="#b45309" stroke-width="1.5" />
  <rect x="195" y="155" width="30" height="30" class="f-amber" stroke="#b45309" stroke-width="1.5" />
  <path d="M 162 128 C 168 102, 215 112, 232 138 C 248 164, 295 172, 298 142 C 300 112, 255 78, 222 92 C 192 104, 156 154, 162 128 Z" class="c-red" stroke-width="1.6" />
  <text x="138" y="168" class="it" fill="#1e3a8a">Γ<tspan font-size="10px" dy="3">δ</tspan></text>
  <text x="232" y="208" class="it" fill="#1e3a8a">Ω<tspan font-size="10px" dy="3">δ</tspan></text>
  <text x="292" y="176" class="it" fill="#dc2626">γ</text>
"""
    return _svg_wrap("0 0 460 275", body)


def generate_fig_4_11() -> str:
    body = """
  <line x1="40" y1="75" x2="410" y2="75" class="c-dash" />
  <line x1="40" y1="135" x2="410" y2="135" class="c-dash" />
  <line x1="40" y1="195" x2="410" y2="195" class="c-dash" />
  <line x1="165" y1="20" x2="165" y2="255" class="c-dash" />
  <line x1="225" y1="20" x2="225" y2="255" class="c-dash" />
  <line x1="285" y1="20" x2="285" y2="255" class="c-dash" />
  <path d="M 85 198 C 68 155, 118 132, 165 108 C 205 88, 202 45, 252 38 C 318 28, 368 78, 355 142 C 342 202, 252 238, 155 242 C 102 244, 92 220, 85 198 Z" class="c-blue" stroke-width="1.8" />
  <rect x="115" y="165" width="50" height="30" class="f-blue" stroke="#0f172a" stroke-width="1.6" />
  <rect x="165" y="135" width="60" height="30" class="f-blue" stroke="#0f172a" stroke-width="1.6" />
  <rect x="225" y="75" width="60" height="60" class="f-blue" stroke="#0f172a" stroke-width="1.6" />
  <path d="M 278 182 C 285 162, 312 152, 315 168 C 318 182, 295 202, 282 195 C 275 190, 275 186, 278 182 Z" class="f-amber" stroke="#b45309" stroke-width="1.5" />
"""
    return _svg_wrap("0 0 450 268", body)


def generate_fig_4_12() -> str:
    body = """
  <path d="M 105 215 L 105 45 L 355 45 L 355 215 L 246 215 A 16 16 0 0 1 214 215 Z" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <circle cx="230" cy="215" r="3.2" fill="#dc2626" />
  <text x="226" y="206" class="lbl">0</text>
  <text x="72" y="36" class="it">−X<tspan font-size="10px" dy="3">1</tspan><tspan dy="-3"> + iY</tspan></text>
  <text x="332" y="36" class="it">X<tspan font-size="10px" dy="3">2</tspan><tspan dy="-3"> + iY</tspan></text>
"""
    return _svg_wrap("0 0 460 250", body)


def generate_fig_4_13() -> str:
    body = """
  <path d="M 75 195 A 155 155 0 0 1 385 195 L 258 195 A 28 28 0 0 0 202 195 Z" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
"""
    return _svg_wrap("0 0 460 225", body)


def generate_fig_4_14() -> str:
    body = """
  <path d="M 338 124 A 110 110 0 1 0 338 136 L 248 136 A 20 20 0 1 1 248 124 Z" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <line x1="275" y1="118" x2="312" y2="118" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="312" y1="142" x2="275" y2="142" class="c-red" marker-end="url(#arr-red)" />
  <path d="M 128 155 A 102 102 0 0 1 128 105" class="c-blue" marker-end="url(#arr-blue)" />
  <path d="M 205 118 A 26 26 0 0 0 205 142" class="c-red" marker-end="url(#arr-red)" />
"""
    return _svg_wrap("0 0 460 260", body)


def generate_fig_4_15() -> str:
    body = """
  <circle cx="220" cy="135" r="105" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <line x1="142" y1="205" x2="294" y2="61" class="c-blue" />
  <line x1="265" y1="40" x2="265" y2="230" class="c-red" />
  <circle cx="220" cy="135" r="3.5" fill="#0f172a" />
  <circle cx="265" cy="87" r="3.5" fill="#dc2626" />
  <text x="202" y="130" class="it">O</text>
  <text x="272" y="96" class="it" fill="#dc2626">z</text>
  <text x="262" y="32" class="it">e<tspan font-size="11px" dy="-5">iθ</tspan></text>
  <text x="262" y="248" class="it">e<tspan font-size="11px" dy="-5">iθ*</tspan></text>
"""
    return _svg_wrap("0 0 450 265", body)


def generate_fig_5_1() -> str:
    body = """
  <polyline points="335,126 335,32 105,32 105,248 335,248 335,154" class="c-blue" stroke-width="1.8" />
  <line x1="245" y1="32" x2="205" y2="32" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="105" y1="115" x2="105" y2="165" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="205" y1="248" x2="245" y2="248" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="335" y1="95" x2="335" y2="65" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="335" y1="215" x2="335" y2="185" class="c-blue" marker-end="url(#arr-blue)" />

  <!-- Hankel contour C -->
  <path d="M 385 130 L 238 130 A 20 20 0 1 0 238 150 L 385 150" class="c-red" stroke-width="1.8" />
  <line x1="315" y1="130" x2="282" y2="130" class="c-red" marker-end="url(#arr-red)" />
  <line x1="282" y1="150" x2="315" y2="150" class="c-red" marker-end="url(#arr-red)" />
  <line x1="220" y1="140" x2="380" y2="140" class="ax" marker-end="url(#arr)" />

  <!-- Poles along imaginary axis -->
  <circle cx="220" cy="140" r="3" fill="#0f172a" />
  <circle cx="220" cy="108" r="3" fill="#dc2626" />
  <circle cx="220" cy="78" r="3" fill="#dc2626" />
  <circle cx="220" cy="48" r="3" fill="#dc2626" />
  <circle cx="220" cy="172" r="3" fill="#dc2626" />
  <circle cx="220" cy="202" r="3" fill="#dc2626" />
  <circle cx="220" cy="232" r="3" fill="#dc2626" />

  <text x="275" y="24" class="it" fill="#1e3a8a">C<tspan font-size="10px" dy="3">n</tspan></text>
  <text x="292" y="122" class="it" fill="#dc2626">C</text>
  <text x="228" y="112" class="it">2πi</text>
  <text x="228" y="52" class="it">2nπi</text>
"""
    return _svg_wrap("0 0 450 268", body)


def generate_fig_6_1() -> str:
    body = """
  <polygon points="65,75 145,52 195,98 168,162 92,172" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <line x1="168" y1="162" x2="215" y2="62" class="c-dash" />
  <path d="M 182 112 A 22 22 0 0 1 170 120" class="c-red" />
  <path d="M 192 112 A 22 22 0 0 0 203 87" class="c-green" />
  <text x="85" y="128" class="it" fill="#1e3a8a">Ω</text>
  <text x="203" y="106" class="it">z<tspan font-size="10px" dy="3">k</tspan></text>
  <text x="152" y="112" class="it" fill="#dc2626">α<tspan font-size="10px" dy="3">k</tspan><tspan dy="-3">π</tspan></text>
  <text x="168" y="78" class="it" fill="#047857">β<tspan font-size="10px" dy="3">k</tspan><tspan dy="-3">π</tspan></text>

  <circle cx="345" cy="118" r="74" class="f-amber" stroke="#0f172a" stroke-width="1.8" />
  <circle cx="335" cy="45" r="3.5" fill="#0f172a" />
  <circle cx="416" cy="96" r="3.5" fill="#dc2626" />
  <circle cx="395" cy="172" r="3.5" fill="#0f172a" />
  <circle cx="332" cy="191" r="3.5" fill="#0f172a" />
  <circle cx="272" cy="102" r="3.5" fill="#0f172a" />
  <text x="424" y="100" class="it" fill="#dc2626">w<tspan font-size="10px" dy="3">k</tspan></text>
"""
    return _svg_wrap("0 0 470 215", body)


def generate_fig_6_2() -> str:
    body = """
  <g class="c-dash">
    <line x1="45" y1="35" x2="415" y2="35" />
    <line x1="45" y1="85" x2="415" y2="85" />
    <line x1="45" y1="135" x2="415" y2="135" />
    <line x1="45" y1="185" x2="415" y2="185" />
    <line x1="45" y1="235" x2="415" y2="235" />
    <line x1="75" y1="15" x2="75" y2="255" />
    <line x1="152" y1="15" x2="152" y2="255" />
    <line x1="230" y1="15" x2="230" y2="255" />
    <line x1="308" y1="15" x2="308" y2="255" />
    <line x1="385" y1="15" x2="385" y2="255" />
  </g>
  <rect x="152" y="85" width="78" height="50" class="f-blue" />
  <rect x="152" y="85" width="78" height="50" fill="url(#stipple)" />
  <rect x="152" y="85" width="156" height="100" fill="none" stroke="#0f172a" stroke-width="1.9" />
  <line x1="230" y1="85" x2="230" y2="185" class="c-main" />
  <line x1="152" y1="135" x2="308" y2="135" class="c-main" />
  <circle cx="191" cy="135" r="3.2" fill="#0f172a" />
  <circle cx="191" cy="85" r="3.2" fill="#dc2626" />
  <text x="182" y="115" class="it">R<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="260" y="115" class="it">R<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="182" y="165" class="it">R<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="260" y="165" class="it">R<tspan font-size="10px" dy="3">3</tspan></text>
  <text x="180" y="150" class="it">O</text>
  <text x="182" y="77" class="it" fill="#dc2626">iK′</text>
  <text x="122" y="152" class="it">−K/2</text>
  <text x="234" y="152" class="it">K/2</text>
"""
    return _svg_wrap("0 0 460 268", body)


def generate_fig_6_3() -> str:
    body = """
  <!-- Top-left: E1, E2, E3 -->
  <path d="M 55 75 C 48 35, 95 20, 138 28 C 175 35, 182 85, 155 112 C 125 138, 62 122, 55 75 Z" fill="url(#hatch-border)" />
  <path d="M 68 75 C 62 45, 98 32, 132 38 C 162 44, 168 82, 145 102 C 120 124, 74 110, 68 75 Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.5" />
  <ellipse cx="102" cy="65" rx="12" ry="8" class="f-blue" stroke="#1e3a8a" stroke-width="1.4" />
  <ellipse cx="118" cy="90" rx="14" ry="9" class="f-amber" stroke="#b45309" stroke-width="1.4" />
  <text x="116" y="68" class="it" font-size="12px">E<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="135" y="92" class="it" font-size="12px">E<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="148" y="48" class="it" font-size="12px">E<tspan font-size="9px" dy="2">3</tspan></text>

  <!-- Top-right: disk C3 with E1, E2 -->
  <circle cx="325" cy="72" r="52" fill="#f8fafc" stroke="#1e3a8a" stroke-width="1.6" />
  <ellipse cx="305" cy="56" rx="11" ry="8" class="f-blue" stroke="#1e3a8a" stroke-width="1.4" />
  <ellipse cx="338" cy="86" rx="13" ry="8" class="f-amber" stroke="#b45309" stroke-width="1.4" />
  <text x="319" y="58" class="it" font-size="12px">E<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="314" y="88" class="it" font-size="12px">E<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="382" y="72" class="it" font-size="12px">C<tspan font-size="9px" dy="2">3</tspan></text>

  <!-- Bottom-left: C3, C1 circle, E2 -->
  <path d="M 55 205 C 48 152, 98 138, 145 148 C 185 158, 188 218, 155 248 C 122 272, 62 252, 55 205 Z" fill="#f8fafc" stroke="#0f172a" stroke-width="1.6" />
  <circle cx="112" cy="216" r="28" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.5" />
  <ellipse cx="122" cy="168" rx="14" ry="8" class="f-amber" stroke="#b45309" stroke-width="1.4" />
  <text x="140" y="172" class="it" font-size="12px">E<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="142" y="236" class="it" font-size="12px">C<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="178" y="236" class="it" font-size="12px">C<tspan font-size="9px" dy="2">3</tspan></text>

  <!-- Bottom-right: C3, C2 circle, C1 oval -->
  <path d="M 265 205 C 258 148, 315 132, 362 142 C 398 152, 398 220, 365 248 C 332 272, 272 252, 265 205 Z" fill="#f8fafc" stroke="#0f172a" stroke-width="1.6" />
  <circle cx="332" cy="196" r="28" fill="#ffffff" stroke="#047857" stroke-width="1.5" />
  <ellipse cx="322" cy="240" rx="14" ry="8" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.5" />
  <text x="340" y="244" class="it" font-size="12px">C<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="362" y="218" class="it" font-size="12px">C<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="392" y="218" class="it" font-size="12px">C<tspan font-size="9px" dy="2">3</tspan></text>
"""
    return _svg_wrap("0 0 440 275", body)


def generate_fig_6_4() -> str:
    body = """
  <path d="M 65 118 C 58 55, 118 28, 168 38 C 215 48, 212 132, 182 168 C 148 205, 72 182, 65 118 Z" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <ellipse cx="132" cy="112" rx="15" ry="24" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.6" />
  <ellipse cx="172" cy="128" rx="9" ry="13" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.6" />
  <ellipse cx="98" cy="76" rx="13" ry="9" transform="rotate(-35 98 76)" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.6" />
  <text x="108" y="152" class="it">C<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="155" y="156" class="it">C<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="118" y="72" class="it">C<tspan font-size="10px" dy="3">3</tspan></text>
  <text x="208" y="88" class="it">C<tspan font-size="10px" dy="3">4</tspan></text>

  <circle cx="355" cy="108" r="82" class="f-amber" stroke="#0f172a" stroke-width="1.6" />
  <circle cx="355" cy="108" r="48" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" />
  <path d="M 294 82 A 66 66 0 0 1 322 51" stroke="#dc2626" stroke-width="3.2" fill="none" />
  <path d="M 388 165 A 66 66 0 0 0 416 134" stroke="#dc2626" stroke-width="3.2" fill="none" />
"""
    return _svg_wrap("0 0 465 210", body)


def generate_fig_6_5() -> str:
    body = """
  <!-- (a) vertical slits -->
  <line x1="75" y1="45" x2="75" y2="145" stroke="#1e3a8a" stroke-width="3.2" />
  <line x1="135" y1="22" x2="135" y2="48" stroke="#1e3a8a" stroke-width="3.2" />
  <line x1="130" y1="112" x2="130" y2="148" stroke="#1e3a8a" stroke-width="3.2" />
  <text x="92" y="180" class="it">(a)</text>

  <!-- (b) horizontal slits -->
  <line x1="225" y1="95" x2="302" y2="95" stroke="#047857" stroke-width="3.2" />
  <line x1="335" y1="125" x2="385" y2="125" stroke="#047857" stroke-width="3.2" />
  <line x1="378" y1="68" x2="405" y2="68" stroke="#047857" stroke-width="3.2" />
  <text x="295" y="180" class="it">(b)</text>
"""
    return _svg_wrap("0 0 450 200", body)


def generate_fig_7_1() -> str:
    ox, oy = 215, 195
    w1x, w1y = 52, -26
    w2x, w2y = -58, -44
    pts = []
    for m in range(-2, 3):
        for n in range(-1, 3):
            px = ox + m * w1x + n * w2x
            py = oy + m * w1y + n * w2y
            if 35 <= px <= 425 and 15 <= py <= 265:
                pts.append(f'<circle cx="{px}" cy="{py}" r="2.8" fill="#0f172a" />')
    p_w1 = (ox + w1x, oy + w1y)
    p_w2 = (ox + w2x, oy + w2y)
    p_w12 = (ox + w1x + w2x, oy + w1y + w2y)
    p_w1p = (ox + w1x + w2x, oy + w1y + w2y)
    p_w2p = (ox + w1x, oy + w1y + 2 * w2y)
    p_top = (ox + 2 * w1x + w2x, oy + 2 * w1y + 3 * w2y)
    body = (
        "\n".join(pts)
        + f"""
  <polygon points="{ox},{oy} {p_w1[0]},{p_w1[1]} {p_w12[0]},{p_w12[1]} {p_w2[0]},{p_w2[1]}" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <polygon points="{ox},{oy} {p_w1p[0]},{p_w1p[1]} {p_top[0]},{p_top[1]} {p_w2p[0]},{p_w2p[1]}" class="c-red-dash" />
  <text x="{ox - 6}" y="{oy + 18}" class="it">O</text>
  <text x="{p_w1[0] + 6}" y="{p_w1[1] + 4}" class="it" fill="#1e3a8a">ω<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="{p_w2[0] - 24}" y="{p_w2[1] + 4}" class="it" fill="#1e3a8a">ω<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="{p_w1p[0] - 22}" y="{p_w1p[1] - 6}" class="it" fill="#dc2626">ω′<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="{p_w2p[0] + 8}" y="{p_w2p[1] + 4}" class="it" fill="#dc2626">ω′<tspan font-size="10px" dy="3">2</tspan></text>
"""
    )
    return _svg_wrap("0 0 460 275", body)


def generate_fig_7_2() -> str:
    body = """
  <!-- Fundamental region |tau| >= 1, -1/2 <= Re(tau) <= 1/2 -->
  <path d="M 185 20 L 185 162 A 90 90 0 0 1 275 162 L 275 20 Z" class="f-blue" />
  <path d="M 185 20 L 185 162 A 90 90 0 0 1 275 162 L 275 20 Z" fill="url(#stipple)" />
  <line x1="75" y1="240" x2="385" y2="240" class="c-main" stroke-width="1.4" />
  <path d="M 140 240 A 90 90 0 0 1 320 240" class="c-main" stroke-width="1.4" />
  <path d="M 230 150 A 90 90 0 0 1 275 162" class="c-blue" stroke-width="2.6" />
  <line x1="185" y1="20" x2="185" y2="162" class="c-main" stroke-width="1.6" />
  <line x1="275" y1="20" x2="275" y2="162" class="c-blue" stroke-width="2.4" />
  <line x1="185" y1="162" x2="185" y2="240" class="c-dash" />
  <line x1="275" y1="162" x2="275" y2="240" class="c-dash" />
  <circle cx="230" cy="150" r="3.2" fill="#dc2626" />
  <text x="226" y="143" class="it" fill="#dc2626">i</text>
  <text x="130" y="258" class="lbl">−1</text>
  <text x="172" y="258" class="lbl">−½</text>
  <text x="226" y="258" class="lbl">0</text>
  <text x="270" y="258" class="lbl">½</text>
  <text x="316" y="258" class="lbl">1</text>
"""
    return _svg_wrap("0 0 460 272", body)


def generate_fig_7_3() -> str:
    body = """
  <path d="M 150 38 L 150 235 A 80 80 0 0 1 310 235 L 310 38 Z" class="f-blue" />
  <line x1="95" y1="235" x2="365" y2="235" class="c-main" stroke-width="1.4" />
  <line x1="150" y1="20" x2="150" y2="235" class="c-main" stroke-width="2" />
  <line x1="310" y1="20" x2="310" y2="235" class="c-main" stroke-width="2" />
  <path d="M 150 235 A 80 80 0 0 1 310 235" class="c-main" stroke-width="2" />
  <line x1="150" y1="38" x2="310" y2="38" class="c-red-dash" />
  <circle cx="150" cy="207" r="28" class="c-red-dash" />
  <circle cx="310" cy="207" r="28" class="c-red-dash" />
  <line x1="230" y1="231" x2="230" y2="239" class="c-main" />
  <text x="146" y="254" class="lbl">0</text>
  <text x="306" y="254" class="lbl">1</text>
  <text x="316" y="42" class="it" fill="#dc2626">t<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="224" y="118" class="it" fill="#1e3a8a">Ω</text>
"""
    return _svg_wrap("0 0 460 268", body)


def generate_fig_7_4_exact() -> str:
    body = """
  <!-- 6 Shaded images of Delta inside -1 <= Re(tau) <= 1 -->
  <!-- 1. Strip 0 <= x <= 1/2, |tau| >= 1 (Delta itself) -->
  <path d="M 230 18 L 230 140 A 100 100 0 0 1 280 153.4 L 280 18 Z" class="f-blue" />
  <path d="M 230 18 L 230 140 A 100 100 0 0 1 280 153.4 L 280 18 Z" fill="url(#stipple)" />

  <!-- 2. Strip -1 <= x <= -1/2, |tau + 1| >= 1 -->
  <path d="M 130 18 L 130 140 A 100 100 0 0 1 180 153.4 L 180 18 Z" class="f-blue" />
  <path d="M 130 18 L 130 140 A 100 100 0 0 1 180 153.4 L 180 18 Z" fill="url(#stipple)" />

  <!-- 3. Curvilinear triangle in -1/2 <= x <= 0 bounded by |tau|=1, |tau+1|=1, x=0 -->
  <path d="M 180 153.4 A 100 100 0 0 1 230 140 L 230 240 A 100 100 0 0 0 180 153.4 Z" class="f-blue" />
  <path d="M 180 153.4 A 100 100 0 0 1 230 140 L 230 240 A 100 100 0 0 0 180 153.4 Z" fill="url(#stipple)" />

  <!-- 4. Curvilinear triangle in 1/2 <= x <= 1 bounded by |tau-1|=1, |tau|=1, x=1 -->
  <path d="M 280 153.4 A 100 100 0 0 1 330 140 L 330 240 A 100 100 0 0 0 280 153.4 Z" class="f-blue" />
  <path d="M 280 153.4 A 100 100 0 0 1 330 140 L 330 240 A 100 100 0 0 0 280 153.4 Z" fill="url(#stipple)" />

  <!-- 5. Curvilinear triangle in -1 <= x <= -1/2 between |tau|=1, |tau+1/2|=1/2, x=-1/2 -->
  <path d="M 130 240 A 100 100 0 0 1 180 153.4 L 180 190 A 50 50 0 0 0 130 240 Z" class="f-blue" />
  <path d="M 130 240 A 100 100 0 0 1 180 153.4 L 180 190 A 50 50 0 0 0 130 240 Z" fill="url(#stipple)" />

  <!-- 6. Curvilinear triangle in 0 <= x <= 1/2 between |tau-1|=1, |tau-1/2|=1/2, x=1/2 -->
  <path d="M 230 240 A 100 100 0 0 1 280 153.4 L 280 190 A 50 50 0 0 0 230 240 Z" class="f-blue" />
  <path d="M 230 240 A 100 100 0 0 1 280 153.4 L 280 190 A 50 50 0 0 0 230 240 Z" fill="url(#stipple)" />

  <!-- Real axis -->
  <line x1="75" y1="240" x2="385" y2="240" class="c-main" stroke-width="1.4" />

  <!-- Vertical lines x = -1, -1/2, 0, 1/2, 1 -->
  <line x1="130" y1="18" x2="130" y2="240" class="c-main" stroke-width="1.4" />
  <line x1="180" y1="153.4" x2="180" y2="190" class="c-main" stroke-width="1.2" />
  <line x1="230" y1="18" x2="230" y2="240" class="c-main" stroke-width="1.3" />
  <line x1="280" y1="153.4" x2="280" y2="190" class="c-main" stroke-width="1.2" />
  <line x1="330" y1="18" x2="330" y2="240" class="c-main" stroke-width="1.4" />

  <!-- Bold boundary of modular fundamental domain Delta' U Delta -->
  <line x1="180" y1="18" x2="180" y2="153.4" stroke="#1e3a8a" stroke-width="2.5" />
  <line x1="280" y1="18" x2="280" y2="153.4" stroke="#1e3a8a" stroke-width="2.5" />
  <path d="M 180 153.4 A 100 100 0 0 1 280 153.4" stroke="#1e3a8a" stroke-width="2.5" fill="none" />

  <!-- Semicircles and quarter-circles -->
  <path d="M 130 240 A 100 100 0 0 1 330 240" class="c-main" stroke-width="1.4" />
  <path d="M 130 140 A 100 100 0 0 1 230 240" class="c-main" stroke-width="1.3" />
  <path d="M 230 240 A 100 100 0 0 1 330 140" class="c-main" stroke-width="1.3" />
  <path d="M 130 240 A 50 50 0 0 1 230 240" class="c-main" stroke-width="1.5" />
  <path d="M 230 240 A 50 50 0 0 1 330 240" class="c-main" stroke-width="1.5" />

  <text x="196" y="95" class="it">Δ′</text>
  <text x="248" y="95" class="it" fill="#1e3a8a">Δ</text>
  <text x="118" y="258" class="lbl">−1</text>
  <text x="226" y="258" class="lbl">0</text>
  <text x="326" y="258" class="lbl">1</text>
"""
    return _svg_wrap("0 0 460 272", body)


def generate_fig_8_1() -> str:
    body = """
  <path d="M 75 152 C 68 72, 165 25, 265 32 C 365 40, 398 112, 378 182 C 355 248, 235 262, 145 242 C 92 228, 80 195, 75 152 Z" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <path d="M 175 132 C 172 95, 222 78, 262 88 C 295 98, 295 148, 262 162 C 222 175, 178 162, 175 132 Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" />
  <path d="M 142 175 C 185 232, 268 232, 322 175" class="c-blue" stroke-width="1.8" />
  <path d="M 142 175 C 192 198, 258 205, 322 175" class="c-green" stroke-width="1.8" />
  <path d="M 142 175 C 115 95, 195 45, 275 58 C 332 68, 348 128, 322 175" class="c-red" stroke-width="1.8" />
  <circle cx="142" cy="175" r="3.5" fill="#0f172a" />
  <circle cx="322" cy="175" r="3.5" fill="#0f172a" />
  <text x="102" y="132" class="it">Ω</text>
  <text x="235" y="232" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="218" y="205" class="it" fill="#047857">γ<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="336" y="105" class="it" fill="#dc2626">γ<tspan font-size="10px" dy="3">3</tspan></text>
"""
    return _svg_wrap("0 0 450 272", body)


def generate_fig_8_2() -> str:
    body = """
  <!-- Left: (t, u) parameter square -->
  <line x1="75" y1="185" x2="235" y2="185" class="c-main" stroke-width="1.5" />
  <line x1="75" y1="185" x2="75" y2="35" class="c-main" stroke-width="1.5" />
  <rect x="75" y="65" width="120" height="120" class="f-blue" stroke="#1e3a8a" stroke-width="1.6" />
  <line x1="112" y1="65" x2="112" y2="185" class="c-blue" stroke-width="1.3" />
  <line x1="75" y1="105" x2="195" y2="105" class="c-blue" stroke-width="1.3" />
  <line x1="75" y1="145" x2="195" y2="145" class="c-blue" stroke-width="1.3" />
  <text x="70" y="26" class="it">u</text>
  <text x="240" y="190" class="it">t</text>

  <!-- Right: deformed family of curves -->
  <path d="M 285 132 C 325 72, 378 58, 425 82" class="c-blue" stroke-width="1.8" />
  <path d="M 285 132 C 330 98, 378 82, 425 82" class="c-blue" stroke-width="1.4" />
  <path d="M 285 132 C 335 128, 382 108, 425 82" class="c-blue" stroke-width="1.4" />
  <path d="M 285 132 C 345 158, 392 132, 425 82" class="c-blue" stroke-width="1.8" />
  <path d="M 322 92 Q 342 115 332 142" class="c-red" stroke-width="1.8" />
  <circle cx="285" cy="132" r="3.2" fill="#0f172a" />
  <circle cx="425" cy="82" r="3.2" fill="#0f172a" />
"""
    return _svg_wrap("0 0 465 210", body)


def generate_fig_8_3() -> str:
    body = """
  <!-- Left: R1 rectangle -->
  <rect x="65" y="35" width="115" height="145" fill="#f8fafc" stroke="#64748b" stroke-width="1.3" />
  <rect x="65" y="108" width="115" height="72" class="f-blue" stroke="#0f172a" stroke-width="2.6" />
  <line x1="188" y1="158" x2="188" y2="128" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="138" y1="116" x2="108" y2="116" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="56" y1="128" x2="56" y2="158" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="108" y1="172" x2="138" y2="172" class="c-blue" marker-end="url(#arr-blue)" />
  <text x="114" y="148" class="it">R<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="195" y="148" class="it" fill="#1e3a8a">π<tspan font-size="10px" dy="3">1</tspan></text>

  <!-- Right: R2 L-shaped region -->
  <rect x="275" y="35" width="115" height="145" fill="#f8fafc" stroke="#64748b" stroke-width="1.3" />
  <path d="M 275 180 L 275 35 L 390 35 L 390 108 L 282 108 L 282 180" class="f-amber" stroke="#0f172a" stroke-width="2.6" />
  <line x1="398" y1="88" x2="398" y2="58" class="c-red" marker-end="url(#arr-red)" />
  <line x1="348" y1="27" x2="318" y2="27" class="c-red" marker-end="url(#arr-red)" />
  <line x1="266" y1="92" x2="266" y2="122" class="c-red" marker-end="url(#arr-red)" />
  <line x1="290" y1="158" x2="290" y2="128" class="c-red" marker-end="url(#arr-red)" />
  <line x1="318" y1="116" x2="348" y2="116" class="c-red" marker-end="url(#arr-red)" />
  <text x="325" y="76" class="it">R<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="405" y="76" class="it" fill="#dc2626">π<tspan font-size="10px" dy="3">2</tspan></text>
"""
    return _svg_wrap("0 0 460 205", body)


def generate_fig_8_4() -> str:
    body = """
  <circle cx="230" cy="135" r="105" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <circle cx="230" cy="135" r="52" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.8" />
  <circle cx="230" cy="135" r="3.2" fill="#0f172a" />
  <circle cx="282" cy="135" r="3.5" fill="#dc2626" />
  <circle cx="256" cy="90" r="3.5" fill="#dc2626" />
  <circle cx="204" cy="90" r="3.5" fill="#dc2626" />
  <circle cx="178" cy="135" r="3.5" fill="#dc2626" />
  <text x="290" y="140" class="it">P<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="260" y="84" class="it">P<tspan font-size="10px" dy="3">k</tspan></text>
  <text x="172" y="82" class="it">P<tspan font-size="10px" dy="3">k+1</tspan></text>
  <text x="150" y="140" class="it">P′<tspan font-size="10px" dy="3">0</tspan></text>
"""
    return _svg_wrap("0 0 460 265", body)


EXTRA_SVG_GENERATORS = {
    "fig_3_4.svg": generate_fig_3_4,
    "fig_3_5.svg": generate_fig_3_5,
    "fig_3_6.svg": generate_fig_3_6,
    "fig_3_7.svg": generate_fig_3_7,
    "fig_3_8.svg": generate_fig_3_8,
    "fig_3_10.svg": generate_fig_3_10,
    "fig_3_11.svg": generate_fig_3_11,
    "fig_4_1.svg": generate_fig_4_1,
    "fig_4_2.svg": generate_fig_4_2,
    "fig_4_3.svg": generate_fig_4_3,
    "fig_4_4.svg": generate_fig_4_4,
    "fig_4_5.svg": generate_fig_4_5,
    "fig_4_6.svg": generate_fig_4_6,
    "fig_4_7.svg": generate_fig_4_7,
    "fig_4_8.svg": generate_fig_4_8,
    "fig_4_9.svg": generate_fig_4_9,
    "fig_4_10.svg": generate_fig_4_10,
    "fig_4_11.svg": generate_fig_4_11,
    "fig_4_12.svg": generate_fig_4_12,
    "fig_4_13.svg": generate_fig_4_13,
    "fig_4_14.svg": generate_fig_4_14,
    "fig_4_15.svg": generate_fig_4_15,
    "fig_5_1.svg": generate_fig_5_1,
    "fig_6_1.svg": generate_fig_6_1,
    "fig_6_2.svg": generate_fig_6_2,
    "fig_6_3.svg": generate_fig_6_3,
    "fig_6_4.svg": generate_fig_6_4,
    "fig_6_5.svg": generate_fig_6_5,
    "fig_7_1.svg": generate_fig_7_1,
    "fig_7_2.svg": generate_fig_7_2,
    "fig_7_3.svg": generate_fig_7_3,
    "fig_7_4.svg": generate_fig_7_4_exact,
    "fig_8_1.svg": generate_fig_8_1,
    "fig_8_2.svg": generate_fig_8_2,
    "fig_8_3.svg": generate_fig_8_3,
    "fig_8_4.svg": generate_fig_8_4,
}
