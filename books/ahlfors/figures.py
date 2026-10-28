import math
import shutil
import tomllib
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from polytypst.vision.diagram_engine import (
    FigureBook,
    FigureSpec,
    figure_svg,
    render_figures,
)

CHAPTERS = tomllib.loads((Path(__file__).parent / "book.toml").read_text(encoding="utf-8"))["chapters"]


def generate_fig_3_4() -> str:
    cx, cy = 230, 145
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="118" fill="url(#grad-blue)" opacity="0.22" />',
        f'<line x1="25" y1="{cy}" x2="435" y2="{cy}" class="ax" marker-end="url(#arr)" />',
        f'<line x1="{cx}" y1="278" x2="{cx}" y2="12" class="ax" marker-end="url(#arr)" />',
    ]
    for r in (18, 42, 74, 110):
        parts.append(f'<circle cx="{cx}" cy="{cy - r}" r="{r}" class="c-sub-blue" />')
        parts.append(f'<circle cx="{cx}" cy="{cy + r}" r="{r}" class="c-sub-blue" />')
        parts.append(f'<circle cx="{cx - r}" cy="{cy}" r="{r}" class="c-sub-red" />')
        parts.append(f'<circle cx="{cx + r}" cy="{cy}" r="{r}" class="c-sub-red" />')
    for r in (28, 56, 92):
        parts.append(f'<circle cx="{cx}" cy="{cy - r}" r="{r}" class="c-blue" />')
        parts.append(f'<circle cx="{cx}" cy="{cy + r}" r="{r}" class="c-blue" />')
        parts.append(f'<circle cx="{cx - r}" cy="{cy}" r="{r}" class="c-red" />')
        parts.append(f'<circle cx="{cx + r}" cy="{cy}" r="{r}" class="c-red" />')
    parts.extend(
        [
            f'<circle cx="{cx}" cy="{cy}" r="14" fill="url(#glow-pole)" />',
            f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="#0f172a" class="pt" />',
            '<text x="348" y="48" class="it" fill="#dc2626">u = c</text>',
            '<text x="315" y="252" class="it" fill="#1e3a8a">v = c′</text>',
            f'<text x="{cx + 8}" y="{cy + 16}" class="lbl">0</text>',
        ]
    )
    return figure_svg(
        "0 0 460 290",
        "\n".join(parts),
        "fig-3-4",
        "Orthogonal circles under inversion w = 1/z",
    )


def generate_fig_3_5() -> str:
    cx, cy = 230, 145
    parts = [
        f'<line x1="30" y1="{cy}" x2="430" y2="{cy}" class="ax" marker-end="url(#arr)" />',
        f'<line x1="{cx}" y1="275" x2="{cx}" y2="15" class="ax" marker-end="url(#arr)" />',
        f'<line x1="100" y1="{cy - 130}" x2="360" y2="{cy + 130}" class="c-dash" />',
        f'<line x1="100" y1="{cy + 130}" x2="360" y2="{cy - 130}" class="c-dash" />',
    ]
    for a, is_sub in (
        (18, True),
        (28, False),
        (41, True),
        (55, False),
        (70, True),
        (84, False),
    ):
        cls_b = "c-sub-blue" if is_sub else "c-blue"
        cls_r = "c-sub-red" if is_sub else "c-red"
        for sgn in (-1, 1):
            pts1 = []
            pts2 = []
            for k in range(-24, 25):
                t = k * 0.06
                x = sgn * a * math.cosh(t)
                y = a * math.sinh(t)
                if abs(x) <= 168 and abs(y) <= 124:
                    pts1.append(f"{cx + x:.1f},{cy - y:.1f}")
                    pts2.append(f"{cx + y:.1f},{cy - x:.1f}")
            if len(pts1) > 2:
                parts.append(f'<polyline points="{" ".join(pts1)}" class="{cls_b}" />')
            if len(pts2) > 2:
                parts.append(f'<polyline points="{" ".join(pts2)}" class="{cls_r}" />')
            if not is_sub:
                pts3 = []
                pts4 = []
                for k in range(-24, 25):
                    t = k * 0.06
                    u = sgn * a * math.cosh(t)
                    v = a * math.sinh(t)
                    xr = (u - v) / math.sqrt(2)
                    yr = (u + v) / math.sqrt(2)
                    if abs(xr) <= 168 and abs(yr) <= 124:
                        pts3.append(f"{cx + xr:.1f},{cy - yr:.1f}")
                        pts4.append(f"{cx + yr:.1f},{cy - xr:.1f}")
                if len(pts3) > 2:
                    parts.append(
                        f'<polyline points="{" ".join(pts3)}" class="c-green" stroke-opacity="0.72" />'
                    )
                if len(pts4) > 2:
                    parts.append(
                        f'<polyline points="{" ".join(pts4)}" class="c-green" stroke-opacity="0.72" />'
                    )
    parts.extend(
        [
            f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="#0f172a" class="pt" />',
            '<text x="372" y="112" class="it" fill="#1e3a8a">x² − y² = u</text>',
            '<text x="275" y="34" class="it" fill="#047857">2xy = v</text>',
        ]
    )
    return figure_svg(
        "0 0 460 290", "\n".join(parts), "fig-3-5", "Orthogonal hyperbolas for w = z^2"
    )


def generate_fig_3_6() -> str:
    cx, cy = 230, 145
    parts = [
        f'<line x1="30" y1="{cy}" x2="430" y2="{cy}" class="ax" marker-end="url(#arr)" />',
        f'<line x1="{cx}" y1="275" x2="{cx}" y2="15" class="ax" marker-end="url(#arr)" />',
        f'<line x1="35" y1="{cy}" x2="{cx}" y2="{cy}" stroke="#0f172a" stroke-width="3.2" />',
    ]
    for c, is_sub in (
        (2.2, True),
        (3.2, False),
        (4.2, True),
        (5.2, False),
        (6.2, True),
        (7.2, False),
        (8.2, True),
        (9.2, False),
    ):
        cls_b = "c-sub-blue" if is_sub else "c-blue"
        cls_r = "c-sub-red" if is_sub else "c-red"
        pts_r = []
        pts_l = []
        for k in range(-28, 29):
            y = k * 4.4
            x_r = c * c - (y * y) / (4.0 * c * c)
            x_l = -c * c + (y * y) / (4.0 * c * c)
            if abs(x_r) <= 182 and abs(y) <= 124:
                pts_r.append(f"{cx + x_r:.1f},{cy - y:.1f}")
            if abs(x_l) <= 182 and abs(y) <= 124:
                pts_l.append(f"{cx + x_l:.1f},{cy - y:.1f}")
        if len(pts_r) > 2:
            parts.append(f'<polyline points="{" ".join(pts_r)}" class="{cls_b}" />')
        if len(pts_l) > 2:
            parts.append(f'<polyline points="{" ".join(pts_l)}" class="{cls_r}" />')
    parts.extend(
        [
            f'<circle cx="{cx}" cy="{cy}" r="12" fill="url(#glow-pole)" />',
            f'<circle cx="{cx}" cy="{cy}" r="3.6" fill="#dc2626" class="pt" />',
            f'<text x="{cx + 8}" y="{cy + 17}" class="lbl">0</text>',
        ]
    )
    return figure_svg(
        "0 0 460 290", "\n".join(parts), "fig-3-6", "Confocal parabolas for w = sqrt(z)"
    )


def generate_fig_3_7() -> str:
    cx, cy = 230, 145
    parts = [
        f'<path d="M {cx} {cy} L {cx + 135 * math.cos(math.radians(-30)):.1f} {cy - 135 * math.sin(math.radians(-30)):.1f} A 135 135 0 0 0 {cx + 135 * math.cos(math.radians(30)):.1f} {cy - 135 * math.sin(math.radians(30)):.1f} Z" fill="url(#grad-blue)" opacity="0.35" />',
        f'<line x1="40" y1="{cy}" x2="420" y2="{cy}" class="ax" marker-end="url(#arr)" />',
        f'<line x1="{cx}" y1="275" x2="{cx}" y2="15" class="ax" marker-end="url(#arr)" />',
    ]
    for deg in (30, 60, 120, 150):
        rad = math.radians(deg)
        dx, dy = 135 * math.cos(rad), 135 * math.sin(rad)
        parts.append(
            f'<line x1="{cx - dx:.1f}" y1="{cy + dy:.1f}" x2="{cx + dx:.1f}" y2="{cy - dy:.1f}" class="c-dash" />'
        )
    for sec in range(6):
        base_deg = sec * 60.0
        for r0, is_sub in ((24.0, True), (36.0, False), (50.0, True), (64.0, False)):
            pts = []
            for k in range(-24, 25):
                deg = base_deg + k * 1.1
                rad = math.radians(deg)
                c3 = abs(math.cos(3.0 * rad))
                if c3 > 0.08:
                    r = r0 / (c3 ** (1.0 / 3.0))
                    if r <= 135:
                        pts.append(
                            f"{cx + r * math.cos(rad):.1f},{cy - r * math.sin(rad):.1f}"
                        )
            if len(pts) > 2:
                if is_sub:
                    cls = "c-sub-blue" if sec % 2 == 0 else "c-sub-red"
                else:
                    cls = "c-blue" if sec % 2 == 0 else "c-red"
                parts.append(f'<polyline points="{" ".join(pts)}" class="{cls}" />')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="#0f172a" class="pt" />')
    return figure_svg(
        "0 0 460 290",
        "\n".join(parts),
        "fig-3-7",
        "Sectors and level curves for w = z^3",
    )


def generate_fig_3_8() -> str:
    body = """
  <path d="M 192 145 C 204 170, 220 182, 232 182 C 264 182, 264 108, 232 108 C 220 108, 204 120, 192 145 Z" class="f-amber" />
  <line x1="228" y1="145" x2="310" y2="145" class="c-dash" />
  <path d="M 110 20 C 122 105, 165 182, 232 182 C 264 182, 264 108, 232 108 C 165 108, 122 185, 110 270" class="c-blue" stroke-width="2.1" />
  <path d="M 140 132 L 152 146" class="c-blue" marker-end="url(#arr-blue)" />
  <path d="M 255 154 L 255 136" class="c-blue" marker-end="url(#arr-blue)" />
  <circle cx="228" cy="145" r="14" fill="url(#glow-pole)" />
  <circle cx="228" cy="145" r="3.8" fill="#dc2626" class="pt" />
  <text x="214" y="142" class="it" fill="#dc2626">w<tspan font-size="10px" dy="3">0</tspan></text>
"""
    return figure_svg("0 0 360 290", body, "fig-3-8", "Loop of image curve around w0")


def generate_fig_3_10() -> str:
    body = """
  <line x1="130" y1="22" x2="130" y2="115" class="c-dash" />
  <line x1="310" y1="22" x2="310" y2="115" class="c-dash" />
  <line x1="30" y1="42" x2="292" y2="42" class="c-blue" stroke-width="2.1" />
  <path d="M 292 42 C 304 42, 316 68, 328 68" class="c-red" stroke-width="2" />
  <line x1="328" y1="68" x2="430" y2="68" class="c-blue" stroke-width="2.1" />

  <line x1="30" y1="68" x2="112" y2="68" class="c-blue" stroke-width="2.1" />
  <path d="M 112 68 C 124 68, 136 94, 148 94" class="c-red" stroke-width="2" />
  <line x1="148" y1="94" x2="292" y2="94" class="c-blue" stroke-width="2.1" />
  <path d="M 292 68 C 304 68, 316 42, 328 42" class="c-red" stroke-width="2" />
  <line x1="328" y1="42" x2="430" y2="42" class="c-blue" stroke-width="2.1" />

  <line x1="30" y1="94" x2="112" y2="94" class="c-blue" stroke-width="2.1" />
  <path d="M 112 94 C 124 94, 136 68, 148 68" class="c-red" stroke-width="2" />
  <line x1="148" y1="68" x2="292" y2="68" class="c-blue" stroke-width="2.1" />
  <path d="M 292 94 C 304 94, 316 112, 328 112" class="c-red" stroke-width="1.8" />
  <path d="M 292 112 C 304 112, 316 94, 328 94" class="c-red" stroke-width="1.8" />
  <line x1="328" y1="94" x2="430" y2="94" class="c-blue" stroke-width="2.1" />
"""
    return figure_svg(
        "0 0 460 135",
        body,
        "fig-3-10",
        "Riemann surface sheet exchange across branch cuts",
    )


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
  <line x1="35" y1="135" x2="425" y2="135" class="c-main" marker-end="url(#arr)" />
  <line x1="230" y1="255" x2="230" y2="14" class="c-main" marker-end="url(#arr)" />
  <line x1="90" y1="20" x2="90" y2="250" class="c-main" />
  <line x1="160" y1="20" x2="160" y2="250" class="c-main" />
  <line x1="300" y1="20" x2="300" y2="250" class="c-main" />
  <line x1="370" y1="20" x2="370" y2="250" class="c-main" />
  <text x="72" y="153" class="lbl">−2π</text>
  <text x="140" y="153" class="lbl">−π</text>
  <text x="218" y="153" class="lbl">0</text>
  <text x="288" y="153" class="lbl">π</text>
  <text x="373" y="153" class="lbl">2π</text>
"""
    return figure_svg("0 0 460 270", body, "fig-3-11", "Fundamental strips of cos z")


def generate_fig_4_1() -> str:
    body = """
  <path d="M 75 185 C 55 140, 110 120, 175 128 C 215 132, 222 105, 228 72 C 236 32, 315 20, 385 45 C 435 65, 435 125, 375 135 C 315 145, 295 165, 275 205 C 252 248, 115 245, 75 185 Z" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <polyline points="145,172 265,172 265,88 345,88" class="c-red" stroke-width="2" />
  <line x1="190" y1="172" x2="215" y2="172" class="c-red" marker-end="url(#arr-red)" />
  <line x1="265" y1="142" x2="265" y2="118" class="c-red" marker-end="url(#arr-red)" />
  <line x1="295" y1="88" x2="318" y2="88" class="c-red" marker-end="url(#arr-red)" />
  <circle cx="145" cy="172" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="265" cy="172" r="3.0" fill="#dc2626" class="pt" />
  <circle cx="265" cy="88" r="3.0" fill="#dc2626" class="pt" />
  <circle cx="345" cy="88" r="3.6" fill="#0f172a" class="pt" />
  <text x="115" y="192" class="it">(x<tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">, y</tspan><tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">)</tspan></text>
  <text x="354" y="93" class="it">(x, y)</text>
  <text x="276" y="135" class="it" fill="#dc2626">γ</text>
  <text x="115" y="152" class="it" fill="#1e3a8a">Ω</text>
"""
    return figure_svg(
        "0 0 460 260", body, "fig-4-1", "Axis-parallel polygonal path in region Omega"
    )


def generate_fig_4_2() -> str:
    body = """
  <rect x="80" y="35" width="300" height="190" class="f-blue" stroke="#0f172a" stroke-width="1.8" />
  <rect x="230" y="35" width="150" height="95" class="f-amber" opacity="0.45" />
  <line x1="230" y1="35" x2="230" y2="225" class="c-main" />
  <line x1="80" y1="130" x2="380" y2="130" class="c-main" />
  <text x="142" y="88" class="it">R<tspan font-size="10px" dy="-6">(1)</tspan></text>
  <text x="292" y="88" class="it">R<tspan font-size="10px" dy="-6">(2)</tspan></text>
  <text x="142" y="182" class="it">R<tspan font-size="10px" dy="-6">(3)</tspan></text>
  <text x="292" y="182" class="it">R<tspan font-size="10px" dy="-6">(4)</tspan></text>
  <text x="62" y="28" class="it">(a, d)</text>
  <text x="366" y="28" class="it">(b, d)</text>
  <text x="62" y="244" class="it">(a, c)</text>
  <text x="366" y="244" class="it">(b, c)</text>
  <line x1="175" y1="43" x2="140" y2="43" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="325" y1="43" x2="290" y2="43" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="140" y1="217" x2="175" y2="217" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="290" y1="217" x2="325" y2="217" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="88" y1="68" x2="88" y2="98" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="88" y1="162" x2="88" y2="192" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="372" y1="98" x2="372" y2="68" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="372" y1="192" x2="372" y2="162" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="140" y1="123" x2="175" y2="123" class="c-red" marker-end="url(#arr-red)" />
  <line x1="175" y1="137" x2="140" y2="137" class="c-red" marker-end="url(#arr-red)" />
  <line x1="290" y1="123" x2="325" y2="123" class="c-red" marker-end="url(#arr-red)" />
  <line x1="325" y1="137" x2="290" y2="137" class="c-red" marker-end="url(#arr-red)" />
  <line x1="223" y1="98" x2="223" y2="68" class="c-red" marker-end="url(#arr-red)" />
  <line x1="237" y1="68" x2="237" y2="98" class="c-red" marker-end="url(#arr-red)" />
  <line x1="223" y1="192" x2="223" y2="162" class="c-red" marker-end="url(#arr-red)" />
  <line x1="237" y1="162" x2="237" y2="192" class="c-red" marker-end="url(#arr-red)" />
"""
    return figure_svg(
        "0 0 460 258", body, "fig-4-2", "Bisection of rectangle in Cauchy-Goursat proof"
    )


def generate_fig_4_3() -> str:
    body = """
  <rect x="85" y="25" width="290" height="210" class="f-blue" opacity="0.45" stroke="#0f172a" stroke-width="1.8" />
  <line x1="182" y1="25" x2="182" y2="235" class="c-dash" />
  <line x1="278" y1="25" x2="278" y2="235" class="c-dash" />
  <line x1="85" y1="95" x2="375" y2="95" class="c-dash" />
  <line x1="85" y1="165" x2="375" y2="165" class="c-dash" />
  <rect x="182" y="95" width="96" height="70" class="f-amber" stroke="#1e3a8a" stroke-width="2" />
  <line x1="245" y1="95" x2="215" y2="95" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="215" y1="165" x2="245" y2="165" class="c-blue" marker-end="url(#arr-blue)" />
  <circle cx="226" cy="132" r="14" fill="url(#glow-pole)" />
  <circle cx="226" cy="132" r="3.8" fill="#dc2626" class="pt" />
  <text x="234" y="136" class="it" fill="#dc2626">ζ</text>
  <text x="102" y="52" class="it" fill="#1e3a8a">R</text>
  <text x="192" y="116" class="it" fill="#b45309">R<tspan font-size="10px" dy="3">0</tspan></text>
"""
    return figure_svg(
        "0 0 460 260",
        body,
        "fig-4-3",
        "Isolating exceptional point zeta inside subrectangle",
    )


def generate_fig_4_4() -> str:
    body = """
  <circle cx="230" cy="135" r="110" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <polyline points="230,135 230,118 292,118 292,78" class="c-main" stroke-width="1.9" />
  <polyline points="230,135 250,135 250,78 292,78" class="c-red-dash" />
  <circle cx="272" cy="105" r="12" fill="url(#glow-pole)" />
  <circle cx="230" cy="135" r="3.5" fill="#0f172a" class="pt" />
  <circle cx="272" cy="105" r="3.6" fill="#dc2626" class="pt" />
  <circle cx="292" cy="78" r="3.5" fill="#0f172a" class="pt" />
  <text x="178" y="154" class="it">(x<tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">, y</tspan><tspan font-size="11px" dy="3">0</tspan><tspan dy="-3">)</tspan></text>
  <text x="278" y="108" class="it" fill="#dc2626">ζ</text>
  <text x="298" y="78" class="it">z</text>
  <text x="145" y="88" class="it" fill="#1e3a8a">Δ</text>
"""
    return figure_svg(
        "0 0 460 270",
        body,
        "fig-4-4",
        "Rectangular path avoiding exceptional point in disk",
    )


def generate_fig_4_5() -> str:
    body = """
  <line x1="50" y1="150" x2="410" y2="150" class="ax" />
  <line x1="230" y1="20" x2="210" y2="275" class="ax" />
  <path d="M 115 150 C 122 85, 178 65, 224 68 C 258 70, 295 32, 338 58 C 378 82, 362 175, 310 198 C 268 216, 240 205, 214 222 C 165 252, 108 215, 115 150 Z" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" />
  <circle cx="230" cy="150" r="44" class="f-green" stroke="#047857" stroke-width="1.7" />
  <circle cx="230" cy="150" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="224" cy="68" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="226" cy="106" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="216" cy="194" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="214" cy="222" r="3.5" fill="#dc2626" class="pt" />
  <text x="234" y="164" class="it">O</text>
  <text x="235" y="22" class="it">L<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="192" y="274" class="it">L<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="231" y="64" class="it">z<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="233" y="102" class="it">ζ<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="224" y="191" class="it">ζ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="221" y="235" class="it">z<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="233" y="88" class="it" fill="#dc2626">δ<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="223" y="212" class="it" fill="#dc2626">δ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="278" y="138" class="it" fill="#047857">C<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="168" y="138" class="it" fill="#047857">C<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="348" y="172" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="92" y="145" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">2</tspan></text>
"""
    return figure_svg(
        "0 0 460 288", body, "fig-4-5", "Winding number decomposition by radial rays"
    )


def generate_fig_4_6() -> str:
    body = """
  <line x1="35" y1="165" x2="435" y2="165" class="ax" marker-end="url(#arr)" />
  <line x1="95" y1="165" x2="225" y2="75" class="c-dash" />
  <line x1="95" y1="165" x2="195" y2="222" class="c-dash" />
  <path d="M 178 165 C 188 138, 208 102, 225 75 C 248 38, 305 32, 332 68 C 355 98, 282 135, 285 165 C 288 192, 318 190, 328 162 C 336 142, 358 142, 362 165 C 368 205, 295 238, 235 245 C 198 248, 185 215, 205 195 C 222 178, 172 182, 178 165 Z" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />
  <circle cx="95" cy="165" r="3.5" fill="#0f172a" class="pt" />
  <circle cx="178" cy="165" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="362" cy="165" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="225" cy="75" r="3.5" fill="#047857" class="pt" />
  <circle cx="195" cy="222" r="3.5" fill="#047857" class="pt" />
  <text x="82" y="183" class="it">O</text>
  <text x="158" y="183" class="it">x<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="368" y="183" class="it">x<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="232" y="75" class="it">z<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="202" y="226" class="it">z<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="184" y="125" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="342" y="95" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">2</tspan></text>
"""
    return figure_svg(
        "0 0 460 268",
        body,
        "fig-4-6",
        "Jordan curve arc decomposition and winding index",
    )


def generate_fig_4_7() -> str:
    body = """
  <circle cx="115" cy="135" r="65" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />
  <circle cx="115" cy="135" r="3.6" fill="#0f172a" class="pt" />
  <text x="108" y="153" class="it">z<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="186" y="138" class="it" fill="#1e3a8a">γ</text>
  <text x="88" y="232" class="lbl"><tspan class="it">z</tspan>‑plane</text>

  <path d="M 196 122 Q 224 106 248 122" class="c-blue" marker-end="url(#arr-blue)" />
  <text x="214" y="106" class="it" fill="#1e3a8a">f</text>

  <path d="M 262 135 C 258 72, 338 45, 398 62 C 446 78, 444 155, 388 185 C 328 215, 264 195, 262 135 C 258 85, 358 32, 382 95 C 402 152, 346 212, 292 185 C 264 168, 262 152, 262 135 Z" class="c-blue" stroke-width="1.8" />
  <circle cx="336" cy="138" r="52" class="f-amber" stroke="#dc2626" stroke-width="1.65" />
  <circle cx="336" cy="138" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="322" cy="114" r="3.6" fill="#dc2626" class="pt" />
  <line x1="336" y1="138" x2="379" y2="166" class="c-red" marker-end="url(#arr-red)" />
  <text x="322" y="155" class="it">w<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="328" y="115" class="it" fill="#dc2626">a</text>
  <text x="358" y="146" class="it" fill="#dc2626">δ</text>
  <text x="438" y="84" class="it" fill="#1e3a8a">Γ</text>
  <text x="312" y="232" class="lbl"><tspan class="it">w</tspan>‑plane</text>
"""
    return figure_svg(
        "0 0 470 250",
        body,
        "fig-4-7",
        "Open mapping theorem image curve Gamma around w0",
    )


def generate_fig_4_8() -> str:
    body = """
  <circle cx="85" cy="110" r="54" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />
  <line x1="85" y1="110" x2="139" y2="110" class="c-red" stroke-width="2.2" />
  <circle cx="85" cy="110" r="3.5" fill="#0f172a" class="pt" />
  <text x="72" y="128" class="it">w<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="58" y="192" class="lbl"><tspan class="it">w</tspan>‑plane</text>

  <circle cx="240" cy="110" r="54" class="f-amber" stroke="#b45309" stroke-width="1.85" />
  <path d="M 240 110 L 294 110 A 54 54 0 0 0 213 63 Z" class="f-blue" opacity="0.55" />
  <path d="M 240 110 L 213 157 A 54 54 0 0 0 294 110 Z" class="f-green" opacity="0.55" />
  <line x1="240" y1="110" x2="294" y2="110" class="c-red" stroke-width="1.9" />
  <line x1="240" y1="110" x2="213" y2="63" class="c-red" stroke-width="1.9" />
  <line x1="240" y1="110" x2="213" y2="157" class="c-red" stroke-width="1.9" />
  <circle cx="240" cy="110" r="3.5" fill="#0f172a" class="pt" />
  <text x="215" y="192" class="lbl"><tspan class="it">ζ</tspan>‑plane</text>

  <path d="M 352 125 C 345 75, 385 45, 422 58 C 455 70, 452 128, 425 155 C 395 182, 358 165, 352 125 Z" class="f-green" stroke="#047857" stroke-width="1.85" />
  <path d="M 402 112 Q 425 118 446 104" class="c-red" stroke-width="1.9" />
  <path d="M 402 112 Q 392 85 375 68" class="c-red" stroke-width="1.9" />
  <path d="M 402 112 Q 388 138 368 152" class="c-red" stroke-width="1.9" />
  <circle cx="402" cy="112" r="3.5" fill="#0f172a" class="pt" />
  <text x="406" y="128" class="it">z<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="378" y="192" class="lbl"><tspan class="it">z</tspan>‑plane</text>
"""
    return figure_svg(
        "0 0 480 215",
        body,
        "fig-4-8",
        "Local normal form at a multiple root of order m = 3",
    )


def generate_fig_4_9() -> str:
    body = """
  <path d="M 65 140 C 55 58, 155 25, 265 32 C 375 40, 405 95, 392 165 C 378 232, 268 252, 155 242 C 82 235, 72 195, 65 140 Z" fill="url(#hatch-border)" />
  <path d="M 92 140 C 85 75, 168 48, 258 54 C 348 60, 372 105, 362 162 C 350 212, 258 228, 165 220 C 105 215, 98 182, 92 140 Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.65" />
  <ellipse cx="222" cy="142" rx="76" ry="48" class="f-blue" />
  <ellipse cx="222" cy="142" rx="76" ry="48" fill="url(#stipple)" stroke="#1e3a8a" stroke-width="1.55" />
  <g stroke="#0f172a" stroke-width="1.15" fill="none">
    <rect x="130" y="86" width="184" height="112" />
    <line x1="176" y1="86" x2="176" y2="198" />
    <line x1="222" y1="86" x2="222" y2="198" />
    <line x1="268" y1="86" x2="268" y2="198" />
    <line x1="130" y1="124" x2="314" y2="124" />
    <line x1="130" y1="161" x2="314" y2="161" />
  </g>
  <circle cx="242" cy="136" r="3.4" fill="#dc2626" class="pt" />
  <text x="248" y="140" class="it" fill="#dc2626">a</text>
  <text x="182" y="156" class="it" fill="#1e3a8a">A</text>
  <text x="320" y="165" class="it">γ</text>
  <text x="366" y="176" class="it">B</text>
"""
    return figure_svg(
        "0 0 450 265",
        body,
        "fig-4-9",
        "Separation of compact set A and closed set B by grid",
    )


def generate_fig_4_10() -> str:
    body = """
  <path d="M 85 150 C 78 65, 165 22, 265 28 C 345 34, 368 95, 385 145 C 402 198, 345 255, 245 258 C 142 260, 92 215, 85 150 Z" fill="url(#hatch-border)" />
  <path d="M 105 150 C 98 78, 175 40, 260 45 C 330 50, 348 102, 365 145 C 380 190, 330 238, 242 240 C 155 242, 112 202, 105 150 Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.55" />
  <polygon points="135,95 165,95 165,65 285,65 285,95 315,95 315,125 345,125 345,185 315,185 315,215 165,215 165,185 135,185" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />
  <g stroke="#64748b" stroke-width="0.75" opacity="0.65">
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
  <rect x="225" y="95" width="30" height="30" class="f-amber" stroke="#b45309" stroke-width="1.55" />
  <rect x="195" y="155" width="30" height="30" class="f-amber" stroke="#b45309" stroke-width="1.55" />
  <path d="M 162 128 C 168 102, 215 112, 232 138 C 248 164, 295 172, 298 142 C 300 112, 255 78, 222 92 C 192 104, 156 154, 162 128 Z" class="c-red" stroke-width="1.7" />
  <text x="138" y="168" class="it" fill="#1e3a8a">Γ<tspan font-size="10px" dy="3">δ</tspan></text>
  <text x="232" y="208" class="it" fill="#1e3a8a">Ω<tspan font-size="10px" dy="3">δ</tspan></text>
  <text x="292" y="176" class="it" fill="#dc2626">γ</text>
"""
    return figure_svg(
        "0 0 460 275", body, "fig-4-10", "Grid approximation of general Cauchy cycle"
    )


def generate_fig_4_11() -> str:
    body = """
  <line x1="40" y1="75" x2="410" y2="75" class="c-dash" />
  <line x1="40" y1="135" x2="410" y2="135" class="c-dash" />
  <line x1="40" y1="195" x2="410" y2="195" class="c-dash" />
  <line x1="165" y1="20" x2="165" y2="255" class="c-dash" />
  <line x1="225" y1="20" x2="225" y2="255" class="c-dash" />
  <line x1="285" y1="20" x2="285" y2="255" class="c-dash" />
  <path d="M 85 198 C 68 155, 118 132, 165 108 C 205 88, 202 45, 252 38 C 318 28, 368 78, 355 142 C 342 202, 252 238, 155 242 C 102 244, 92 220, 85 198 Z" class="c-blue" stroke-width="1.85" />
  <rect x="115" y="165" width="50" height="30" class="f-blue" stroke="#0f172a" stroke-width="1.65" />
  <rect x="165" y="135" width="60" height="30" class="f-blue" stroke="#0f172a" stroke-width="1.65" />
  <rect x="225" y="75" width="60" height="60" class="f-blue" stroke="#0f172a" stroke-width="1.65" />
  <path d="M 278 182 C 285 162, 312 152, 315 168 C 318 182, 295 202, 282 195 C 275 190, 275 186, 278 182 Z" class="f-amber" stroke="#b45309" stroke-width="1.6" />
"""
    return figure_svg(
        "0 0 450 268", body, "fig-4-11", "Decomposition of cycle into rectangular mesh"
    )


def generate_fig_4_12() -> str:
    body = """
  <line x1="55" y1="215" x2="405" y2="215" class="ax" marker-end="url(#arr)" />
  <line x1="230" y1="240" x2="230" y2="18" class="ax" marker-end="url(#arr)" />
  <path d="M 105 215 L 105 45 L 355 45 L 355 215 L 248 215 A 18 18 0 0 1 212 215 Z" class="f-blue" stroke="#0f172a" stroke-width="1.85" />
  <line x1="255" y1="45" x2="205" y2="45" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="105" y1="115" x2="105" y2="145" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="355" y1="145" x2="355" y2="115" class="c-blue" marker-end="url(#arr-blue)" />
  <circle cx="230" cy="215" r="12" fill="url(#glow-pole)" />
  <circle cx="230" cy="215" r="3.5" fill="#dc2626" class="pt" />
  <text x="226" y="234" class="lbl">0</text>
  <text x="92" y="234" class="it">−X<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="348" y="234" class="it">X<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="72" y="36" class="it">−X<tspan font-size="10px" dy="3">1</tspan><tspan dy="-3"> + iY</tspan></text>
  <text x="332" y="36" class="it">X<tspan font-size="10px" dy="3">2</tspan><tspan dy="-3"> + iY</tspan></text>
"""
    return figure_svg(
        "0 0 460 250",
        body,
        "fig-4-12",
        "Indented rectangular contour in upper half plane",
    )


def generate_fig_4_13() -> str:
    body = """
  <line x1="45" y1="195" x2="415" y2="195" class="ax" marker-end="url(#arr)" />
  <line x1="230" y1="215" x2="230" y2="16" class="ax" marker-end="url(#arr)" />
  <path d="M 75 195 A 155 155 0 0 1 385 195 L 258 195 A 28 28 0 0 0 202 195 Z" class="f-blue" stroke="#0f172a" stroke-width="1.85" />
  <path d="M 305 62 A 155 155 0 0 0 265 44" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="130" y1="195" x2="160" y2="195" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="305" y1="195" x2="335" y2="195" class="c-blue" marker-end="url(#arr-blue)" />
  <circle cx="230" cy="195" r="14" fill="url(#glow-pole)" />
  <circle cx="230" cy="195" r="3.6" fill="#dc2626" class="pt" />
  <text x="65" y="213" class="it">−R</text>
  <text x="190" y="213" class="it">−ε</text>
  <text x="226" y="213" class="lbl">0</text>
  <text x="254" y="213" class="it">ε</text>
  <text x="380" y="213" class="it">R</text>
"""
    return figure_svg(
        "0 0 460 225", body, "fig-4-13", "Indented semicircular contour for sin x / x"
    )


def generate_fig_4_14() -> str:
    body = """
  <line x1="55" y1="130" x2="415" y2="130" class="ax" marker-end="url(#arr)" />
  <line x1="228" y1="130" x2="395" y2="130" stroke="#dc2626" stroke-width="3.2" />
  <path d="M 338 122 A 110 110 0 1 0 338 138 L 248 138 A 20 20 0 1 1 248 122 Z" class="f-blue" stroke="#0f172a" stroke-width="1.85" />
  <line x1="272" y1="117" x2="312" y2="117" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="312" y1="143" x2="272" y2="143" class="c-red" marker-end="url(#arr-red)" />
  <path d="M 122 155 A 108 108 0 0 1 122 105" class="c-blue" marker-end="url(#arr-blue)" />
  <path d="M 208 118 A 22 22 0 0 0 208 142" class="c-red" marker-end="url(#arr-red)" />
  <circle cx="228" cy="130" r="14" fill="url(#glow-pole)" />
  <circle cx="228" cy="130" r="3.6" fill="#dc2626" class="pt" />
  <text x="222" y="158" class="lbl">0</text>
  <text x="148" y="42" class="it" fill="#1e3a8a">C<tspan font-size="10px" dy="3">R</tspan></text>
  <text x="182" y="135" class="it" fill="#dc2626">C<tspan font-size="10px" dy="3">ε</tspan></text>
"""
    return figure_svg(
        "0 0 460 260",
        body,
        "fig-4-14",
        "Keyhole contour around positive real branch cut",
    )


def generate_fig_4_15() -> str:
    body = """
  <circle cx="220" cy="135" r="105" class="f-blue" stroke="#0f172a" stroke-width="1.85" />
  <line x1="220" y1="135" x2="265" y2="87" class="c-dash" />
  <line x1="142" y1="205" x2="294" y2="61" class="c-blue" stroke-width="1.75" />
  <line x1="265" y1="40" x2="265" y2="230" class="c-red" stroke-width="1.75" />
  <circle cx="220" cy="135" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="265" cy="87" r="3.8" fill="#dc2626" class="pt" />
  <circle cx="265" cy="40" r="3.4" fill="#1e3a8a" class="pt" />
  <circle cx="265" cy="230" r="3.4" fill="#1e3a8a" class="pt" />
  <text x="202" y="132" class="it">O</text>
  <text x="273" y="96" class="it" fill="#dc2626">z</text>
  <text x="262" y="32" class="it">e<tspan font-size="11px" dy="-5">iθ</tspan></text>
  <text x="262" y="248" class="it">e<tspan font-size="11px" dy="-5">iθ*</tspan></text>
"""
    return figure_svg(
        "0 0 450 265",
        body,
        "fig-4-15",
        "Chord geometry of Poisson kernel on the unit disk",
    )


def generate_fig_5_1() -> str:
    body = """
  <rect x="105" y="32" width="230" height="216" class="f-blue" opacity="0.35" />
  <polyline points="335,126 335,32 105,32 105,248 335,248 335,154" class="c-blue" stroke-width="1.85" />
  <line x1="245" y1="32" x2="205" y2="32" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="105" y1="115" x2="105" y2="165" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="205" y1="248" x2="245" y2="248" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="335" y1="95" x2="335" y2="65" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="335" y1="215" x2="335" y2="185" class="c-blue" marker-end="url(#arr-blue)" />

  <path d="M 385 130 L 238 130 A 20 20 0 1 0 238 150 L 385 150" class="c-red" stroke-width="1.9" />
  <line x1="315" y1="130" x2="282" y2="130" class="c-red" marker-end="url(#arr-red)" />
  <line x1="282" y1="150" x2="315" y2="150" class="c-red" marker-end="url(#arr-red)" />
  <line x1="220" y1="140" x2="380" y2="140" class="ax" marker-end="url(#arr)" />
  <line x1="220" y1="258" x2="220" y2="16" class="ax" marker-end="url(#arr)" />

  <circle cx="220" cy="140" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="220" cy="108" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="220" cy="78" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="220" cy="48" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="220" cy="172" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="220" cy="202" r="3.5" fill="#dc2626" class="pt" />
  <circle cx="220" cy="232" r="3.5" fill="#dc2626" class="pt" />

  <text x="275" y="24" class="it" fill="#1e3a8a">C<tspan font-size="10px" dy="3">n</tspan></text>
  <text x="292" y="122" class="it" fill="#dc2626">C</text>
  <text x="228" y="112" class="it">2πi</text>
  <text x="228" y="52" class="it">2nπi</text>
"""
    return figure_svg(
        "0 0 450 268", body, "fig-5-1", "Hankel contour for Riemann zeta function"
    )


def generate_fig_6_1() -> str:
    body = """
  <polygon points="65,75 145,52 195,98 168,162 92,172" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />
  <line x1="168" y1="162" x2="215" y2="62" class="c-dash" />
  <path d="M 182 112 A 22 22 0 0 1 170 120" class="c-red" stroke-width="1.8" />
  <path d="M 192 112 A 22 22 0 0 0 203 87" class="c-green" stroke-width="1.8" />
  <text x="115" y="124" class="it" fill="#1e3a8a">Ω</text>
  <text x="203" y="106" class="it">z<tspan font-size="10px" dy="3">k</tspan></text>
  <text x="148" y="112" class="it" fill="#dc2626">α<tspan font-size="10px" dy="3">k</tspan><tspan dy="-3">π</tspan></text>
  <text x="168" y="78" class="it" fill="#047857">β<tspan font-size="10px" dy="3">k</tspan><tspan dy="-3">π</tspan></text>

  <path d="M 226 118 Q 248 104 268 118" class="c-blue" marker-end="url(#arr-blue)" />

  <circle cx="355" cy="118" r="74" class="f-amber" stroke="#0f172a" stroke-width="1.85" />
  <circle cx="345" cy="45" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="426" cy="96" r="3.8" fill="#dc2626" class="pt" />
  <circle cx="405" cy="172" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="342" cy="191" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="282" cy="102" r="3.6" fill="#0f172a" class="pt" />
  <text x="434" y="100" class="it" fill="#dc2626">w<tspan font-size="10px" dy="3">k</tspan></text>
"""
    return figure_svg(
        "0 0 470 215", body, "fig-6-1", "Schwarz-Christoffel polygon vertex angles"
    )


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
  <rect x="230" y="85" width="78" height="50" class="f-amber" opacity="0.45" />
  <rect x="152" y="135" width="78" height="50" class="f-green" opacity="0.42" />
  <rect x="152" y="85" width="156" height="100" fill="none" stroke="#0f172a" stroke-width="1.95" />
  <line x1="230" y1="85" x2="230" y2="185" class="c-main" />
  <line x1="152" y1="135" x2="308" y2="135" class="c-main" />
  <circle cx="191" cy="135" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="191" cy="85" r="3.5" fill="#dc2626" class="pt" />
  <text x="182" y="115" class="it">R<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="260" y="115" class="it">R<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="182" y="165" class="it">R<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="260" y="165" class="it">R<tspan font-size="10px" dy="3">3</tspan></text>
  <text x="180" y="150" class="it">O</text>
  <text x="182" y="77" class="it" fill="#dc2626">iK′</text>
  <text x="122" y="152" class="it">−K/2</text>
  <text x="234" y="152" class="it">K/2</text>
"""
    return figure_svg(
        "0 0 460 268",
        body,
        "fig-6-2",
        "Reflection lattice of rectangles for elliptic integral",
    )


def generate_fig_6_3() -> str:
    body = """
  <path d="M 55 75 C 48 35, 95 20, 138 28 C 175 35, 182 85, 155 112 C 125 138, 62 122, 55 75 Z" fill="url(#hatch-border)" />
  <path d="M 68 75 C 62 45, 98 32, 132 38 C 162 44, 168 82, 145 102 C 120 124, 74 110, 68 75 Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.55" />
  <ellipse cx="102" cy="65" rx="12" ry="8" class="f-blue" stroke="#1e3a8a" stroke-width="1.45" />
  <ellipse cx="118" cy="90" rx="14" ry="9" class="f-amber" stroke="#b45309" stroke-width="1.45" />
  <text x="116" y="68" class="it" font-size="12px">E<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="135" y="92" class="it" font-size="12px">E<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="148" y="48" class="it" font-size="12px">E<tspan font-size="9px" dy="2">3</tspan></text>

  <circle cx="325" cy="72" r="52" fill="#f8fafc" stroke="#1e3a8a" stroke-width="1.65" />
  <ellipse cx="305" cy="56" rx="11" ry="8" class="f-blue" stroke="#1e3a8a" stroke-width="1.45" />
  <ellipse cx="338" cy="86" rx="13" ry="8" class="f-amber" stroke="#b45309" stroke-width="1.45" />
  <text x="319" y="58" class="it" font-size="12px">E<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="314" y="88" class="it" font-size="12px">E<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="382" y="72" class="it" font-size="12px">C<tspan font-size="9px" dy="2">3</tspan></text>

  <path d="M 55 205 C 48 152, 98 138, 145 148 C 185 158, 188 218, 155 248 C 122 272, 62 252, 55 205 Z" fill="#f8fafc" stroke="#0f172a" stroke-width="1.65" />
  <circle cx="112" cy="216" r="28" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.55" />
  <ellipse cx="122" cy="168" rx="14" ry="8" class="f-amber" stroke="#b45309" stroke-width="1.45" />
  <text x="140" y="172" class="it" font-size="12px">E<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="142" y="236" class="it" font-size="12px">C<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="178" y="236" class="it" font-size="12px">C<tspan font-size="9px" dy="2">3</tspan></text>

  <path d="M 265 205 C 258 148, 315 132, 362 142 C 398 152, 398 220, 365 248 C 332 272, 272 252, 265 205 Z" fill="#f8fafc" stroke="#0f172a" stroke-width="1.65" />
  <circle cx="332" cy="196" r="28" fill="#ffffff" stroke="#047857" stroke-width="1.55" />
  <ellipse cx="322" cy="240" rx="14" ry="8" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.55" />
  <text x="340" y="244" class="it" font-size="12px">C<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="362" y="218" class="it" font-size="12px">C<tspan font-size="9px" dy="2">2</tspan></text>
  <text x="392" y="218" class="it" font-size="12px">C<tspan font-size="9px" dy="2">3</tspan></text>
"""
    return figure_svg(
        "0 0 440 275",
        body,
        "fig-6-3",
        "Iterative circularization of multiply connected region",
    )


def generate_fig_6_4() -> str:
    body = """
  <path d="M 65 118 C 58 55, 118 28, 168 38 C 215 48, 212 132, 182 168 C 148 205, 72 182, 65 118 Z" class="f-blue" stroke="#0f172a" stroke-width="1.85" />
  <ellipse cx="132" cy="112" rx="15" ry="24" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.65" />
  <ellipse cx="172" cy="128" rx="9" ry="13" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.65" />
  <ellipse cx="98" cy="76" rx="13" ry="9" transform="rotate(-35 98 76)" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.65" />
  <text x="108" y="152" class="it">C<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="155" y="156" class="it">C<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="118" y="72" class="it">C<tspan font-size="10px" dy="3">3</tspan></text>
  <text x="208" y="88" class="it">C<tspan font-size="10px" dy="3">4</tspan></text>

  <circle cx="355" cy="108" r="82" class="f-amber" stroke="#0f172a" stroke-width="1.65" />
  <circle cx="355" cy="108" r="65" class="c-sub-blue" stroke-dasharray="3,3" />
  <circle cx="355" cy="108" r="48" fill="#ffffff" stroke="#0f172a" stroke-width="1.65" />
  <path d="M 294 82 A 66 66 0 0 1 322 51" stroke="#dc2626" stroke-width="3.4" stroke-linecap="round" fill="none" />
  <path d="M 388 165 A 66 66 0 0 0 416 134" stroke="#dc2626" stroke-width="3.4" stroke-linecap="round" fill="none" />
"""
    return figure_svg(
        "0 0 465 210", body, "fig-6-4", "Conformal mapping onto concentric slit annulus"
    )


def generate_fig_6_5() -> str:
    body = """
  <path d="M 48 95 C 62 95, 68 42, 75 40 C 82 42, 88 95, 115 95" class="c-sub-blue" />
  <path d="M 48 125 C 62 125, 68 152, 75 154 C 82 152, 88 125, 115 125" class="c-sub-blue" />
  <line x1="75" y1="45" x2="75" y2="145" stroke="#1e3a8a" stroke-width="3.4" stroke-linecap="round" />
  <line x1="135" y1="22" x2="135" y2="48" stroke="#1e3a8a" stroke-width="3.4" stroke-linecap="round" />
  <line x1="130" y1="112" x2="130" y2="148" stroke="#1e3a8a" stroke-width="3.4" stroke-linecap="round" />
  <text x="92" y="180" class="it">(a)</text>

  <line x1="215" y1="78" x2="415" y2="78" class="c-sub-blue" />
  <line x1="215" y1="110" x2="415" y2="110" class="c-sub-blue" />
  <line x1="215" y1="142" x2="415" y2="142" class="c-sub-blue" />
  <line x1="225" y1="95" x2="302" y2="95" stroke="#047857" stroke-width="3.4" stroke-linecap="round" />
  <line x1="335" y1="125" x2="385" y2="125" stroke="#047857" stroke-width="3.4" stroke-linecap="round" />
  <line x1="378" y1="68" x2="405" y2="68" stroke="#047857" stroke-width="3.4" stroke-linecap="round" />
  <text x="295" y="180" class="it">(b)</text>
"""
    return figure_svg(
        "0 0 450 200", body, "fig-6-5", "Vertical and horizontal canonical slit regions"
    )


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
                pts.append(
                    f'<circle cx="{px}" cy="{py}" r="3.1" fill="#0f172a" class="pt" />'
                )
    p_w1 = (ox + w1x, oy + w1y)
    p_w2 = (ox + w2x, oy + w2y)
    p_w12 = (ox + w1x + w2x, oy + w1y + w2y)
    p_w1p = (ox + w1x + w2x, oy + w1y + w2y)
    p_w2p = (ox + w1x, oy + w1y + 2 * w2y)
    p_top = (ox + 2 * w1x + w2x, oy + 2 * w1y + 3 * w2y)
    body = (
        f"""
  <polygon points="{ox},{oy} {p_w1p[0]},{p_w1p[1]} {p_top[0]},{p_top[1]} {p_w2p[0]},{p_w2p[1]}" class="f-amber" opacity="0.55" />
  <polygon points="{ox},{oy} {p_w1[0]},{p_w1[1]} {p_w12[0]},{p_w12[1]} {p_w2[0]},{p_w2[1]}" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />
  <polygon points="{ox},{oy} {p_w1p[0]},{p_w1p[1]} {p_top[0]},{p_top[1]} {p_w2p[0]},{p_w2p[1]}" class="c-red-dash" />
  <line x1="{ox}" y1="{oy}" x2="{p_w1[0]}" y2="{p_w1[1]}" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="{ox}" y1="{oy}" x2="{p_w2[0]}" y2="{p_w2[1]}" class="c-blue" marker-end="url(#arr-blue)" />
"""
        + "\n".join(pts)
        + f"""
  <text x="{ox - 6}" y="{oy + 18}" class="it">O</text>
  <text x="{p_w1[0] + 6}" y="{p_w1[1] + 4}" class="it" fill="#1e3a8a">ω<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="{p_w2[0] - 24}" y="{p_w2[1] + 4}" class="it" fill="#1e3a8a">ω<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="{p_w1p[0] - 24}" y="{p_w1p[1] - 6}" class="it" fill="#dc2626">ω′<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="{p_w2p[0] + 8}" y="{p_w2p[1] + 4}" class="it" fill="#dc2626">ω′<tspan font-size="10px" dy="3">2</tspan></text>
"""
    )
    return figure_svg(
        "0 0 460 275",
        body,
        "fig-7-1",
        "Period module lattice and equivalent basis parallelograms",
    )


def generate_fig_7_2() -> str:
    body = """
  <path d="M 185 20 L 185 162 A 90 90 0 0 1 275 162 L 275 20 Z" class="f-uhp" />
  <path d="M 185 20 L 185 162 A 90 90 0 0 1 275 162 L 275 20 Z" fill="url(#stipple)" />
  <line x1="75" y1="240" x2="385" y2="240" class="c-main" stroke-width="1.45" />
  <line x1="230" y1="240" x2="230" y2="18" class="ax" stroke-dasharray="4,3" />
  <path d="M 140 240 A 90 90 0 0 1 320 240" class="c-main" stroke-width="1.45" />
  <path d="M 230 150 A 90 90 0 0 1 275 162" class="c-blue" stroke-width="2.7" />
  <line x1="185" y1="20" x2="185" y2="162" class="c-main" stroke-width="1.6" />
  <line x1="275" y1="20" x2="275" y2="162" class="c-blue" stroke-width="2.5" />
  <line x1="185" y1="162" x2="185" y2="240" class="c-dash" />
  <line x1="275" y1="162" x2="275" y2="240" class="c-dash" />
  <circle cx="230" cy="150" r="3.6" fill="#dc2626" class="pt" />
  <circle cx="185" cy="162" r="3.4" fill="#047857" class="pt" />
  <circle cx="275" cy="162" r="3.4" fill="#1e3a8a" class="pt" />
  <text x="225" y="142" class="it" fill="#dc2626">i</text>
  <text x="130" y="258" class="lbl">−1</text>
  <text x="172" y="258" class="lbl">−½</text>
  <text x="226" y="258" class="lbl">0</text>
  <text x="270" y="258" class="lbl">½</text>
  <text x="316" y="258" class="lbl">1</text>
"""
    return figure_svg(
        "0 0 460 272", body, "fig-7-2", "Fundamental region of the unimodular group"
    )


def generate_fig_7_3() -> str:
    body = """
  <path d="M 150 38 L 150 235 A 80 80 0 0 1 310 235 L 310 38 Z" class="f-uhp" />
  <line x1="95" y1="235" x2="365" y2="235" class="c-main" stroke-width="1.45" />
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
    return figure_svg(
        "0 0 460 268",
        body,
        "fig-7-3",
        "Truncated fundamental contour for modular function lambda(tau)",
    )


def generate_fig_7_4_exact() -> str:
    body = """
  <path d="M 230 18 L 230 140 A 100 100 0 0 1 280 153.4 L 280 18 Z" class="f-uhp" />
  <path d="M 230 18 L 230 140 A 100 100 0 0 1 280 153.4 L 280 18 Z" fill="url(#stipple)" />

  <path d="M 130 18 L 130 140 A 100 100 0 0 1 180 153.4 L 180 18 Z" class="f-uhp" />
  <path d="M 130 18 L 130 140 A 100 100 0 0 1 180 153.4 L 180 18 Z" fill="url(#stipple)" />

  <path d="M 180 153.4 A 100 100 0 0 1 230 140 L 230 240 A 100 100 0 0 0 180 153.4 Z" class="f-uhp" />
  <path d="M 180 153.4 A 100 100 0 0 1 230 140 L 230 240 A 100 100 0 0 0 180 153.4 Z" fill="url(#stipple)" />

  <path d="M 280 153.4 A 100 100 0 0 1 330 140 L 330 240 A 100 100 0 0 0 280 153.4 Z" class="f-uhp" />
  <path d="M 280 153.4 A 100 100 0 0 1 330 140 L 330 240 A 100 100 0 0 0 280 153.4 Z" fill="url(#stipple)" />

  <path d="M 130 240 A 100 100 0 0 1 180 153.4 L 180 190 A 50 50 0 0 0 130 240 Z" class="f-uhp" />
  <path d="M 130 240 A 100 100 0 0 1 180 153.4 L 180 190 A 50 50 0 0 0 130 240 Z" fill="url(#stipple)" />

  <path d="M 230 240 A 100 100 0 0 1 280 153.4 L 280 190 A 50 50 0 0 0 230 240 Z" class="f-uhp" />
  <path d="M 230 240 A 100 100 0 0 1 280 153.4 L 280 190 A 50 50 0 0 0 230 240 Z" fill="url(#stipple)" />

  <line x1="75" y1="240" x2="385" y2="240" class="c-main" stroke-width="1.45" />

  <line x1="130" y1="18" x2="130" y2="240" class="c-main" stroke-width="1.45" />
  <line x1="180" y1="153.4" x2="180" y2="190" class="c-main" stroke-width="1.25" />
  <line x1="230" y1="18" x2="230" y2="240" class="c-main" stroke-width="1.35" />
  <line x1="280" y1="153.4" x2="280" y2="190" class="c-main" stroke-width="1.25" />
  <line x1="330" y1="18" x2="330" y2="240" class="c-main" stroke-width="1.45" />

  <line x1="180" y1="18" x2="180" y2="153.4" stroke="#1e3a8a" stroke-width="2.5" />
  <line x1="280" y1="18" x2="280" y2="153.4" stroke="#1e3a8a" stroke-width="2.5" />
  <path d="M 180 153.4 A 100 100 0 0 1 280 153.4" stroke="#1e3a8a" stroke-width="2.5" fill="none" />

  <path d="M 130 240 A 100 100 0 0 1 330 240" class="c-main" stroke-width="1.45" />
  <path d="M 130 140 A 100 100 0 0 1 230 240" class="c-main" stroke-width="1.35" />
  <path d="M 230 240 A 100 100 0 0 1 330 140" class="c-main" stroke-width="1.35" />
  <path d="M 130 240 A 50 50 0 0 1 230 240" class="c-main" stroke-width="1.5" />
  <path d="M 230 240 A 50 50 0 0 1 330 240" class="c-main" stroke-width="1.5" />

  <text x="196" y="95" class="it">Δ′</text>
  <text x="248" y="95" class="it" fill="#1e3a8a">Δ</text>
  <text x="118" y="258" class="lbl">−1</text>
  <text x="226" y="258" class="lbl">0</text>
  <text x="326" y="258" class="lbl">1</text>
"""
    return figure_svg(
        "0 0 460 272",
        body,
        "fig-7-4",
        "Twelve modular subregions of congruence subgroup Gamma(2)",
    )


def generate_fig_8_1() -> str:
    body = """
  <path d="M 75 152 C 68 72, 165 25, 265 32 C 365 40, 398 112, 378 182 C 355 248, 235 262, 145 242 C 92 228, 80 195, 75 152 Z" class="f-blue" stroke="#0f172a" stroke-width="1.85" />
  <path d="M 175 132 C 172 95, 222 78, 262 88 C 295 98, 295 148, 262 162 C 222 175, 178 162, 175 132 Z" fill="url(#hatch-border)" stroke="#0f172a" stroke-width="1.65" />
  <path d="M 142 175 C 188 214, 262 218, 322 175" class="c-sub-blue" stroke-dasharray="3,3" />
  <path d="M 142 175 C 185 232, 268 232, 322 175" class="c-blue" stroke-width="1.85" />
  <path d="M 142 175 C 192 198, 258 205, 322 175" class="c-green" stroke-width="1.85" />
  <path d="M 142 175 C 115 95, 195 45, 275 58 C 332 68, 348 128, 322 175" class="c-red" stroke-width="1.85" />
  <circle cx="142" cy="175" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="322" cy="175" r="3.6" fill="#0f172a" class="pt" />
  <text x="102" y="132" class="it">Ω</text>
  <text x="235" y="232" class="it" fill="#1e3a8a">γ<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="218" y="203" class="it" fill="#047857">γ<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="336" y="105" class="it" fill="#dc2626">γ<tspan font-size="10px" dy="3">3</tspan></text>
"""
    return figure_svg(
        "0 0 450 272",
        body,
        "fig-8-1",
        "Homotopic and non-homotopic paths around an obstacle",
    )


def generate_fig_8_2() -> str:
    body = """
  <line x1="75" y1="185" x2="235" y2="185" class="c-main" stroke-width="1.5" marker-end="url(#arr)" />
  <line x1="75" y1="185" x2="75" y2="30" class="c-main" stroke-width="1.5" marker-end="url(#arr)" />
  <rect x="75" y="65" width="120" height="120" class="f-blue" stroke="#1e3a8a" stroke-width="1.65" />
  <line x1="112" y1="65" x2="112" y2="185" class="c-red" stroke-width="1.5" />
  <line x1="75" y1="105" x2="195" y2="105" class="c-blue" stroke-width="1.35" />
  <line x1="75" y1="145" x2="195" y2="145" class="c-blue" stroke-width="1.35" />
  <text x="68" y="24" class="it">u</text>
  <text x="240" y="190" class="it">t</text>

  <path d="M 285 132 C 325 72, 378 58, 425 82" class="c-blue" stroke-width="1.85" />
  <path d="M 285 132 C 330 98, 378 82, 425 82" class="c-blue" stroke-width="1.4" />
  <path d="M 285 132 C 335 128, 382 108, 425 82" class="c-blue" stroke-width="1.4" />
  <path d="M 285 132 C 345 158, 392 132, 425 82" class="c-blue" stroke-width="1.85" />
  <path d="M 322 92 Q 342 115 332 142" class="c-red" stroke-width="1.85" />
  <circle cx="285" cy="132" r="3.5" fill="#0f172a" class="pt" />
  <circle cx="425" cy="82" r="3.5" fill="#0f172a" class="pt" />
"""
    return figure_svg(
        "0 0 465 210",
        body,
        "fig-8-2",
        "Parameter square (t, u) and homotopy curve family",
    )


def generate_fig_8_3() -> str:
    body = """
  <rect x="65" y="35" width="115" height="145" fill="#f8fafc" stroke="#64748b" stroke-width="1.35" />
  <rect x="65" y="108" width="115" height="72" class="f-blue" stroke="#0f172a" stroke-width="2.5" />
  <line x1="188" y1="158" x2="188" y2="128" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="138" y1="116" x2="108" y2="116" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="56" y1="128" x2="56" y2="158" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="108" y1="172" x2="138" y2="172" class="c-blue" marker-end="url(#arr-blue)" />
  <text x="114" y="148" class="it">R<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="195" y="148" class="it" fill="#1e3a8a">π<tspan font-size="10px" dy="3">1</tspan></text>

  <rect x="275" y="35" width="115" height="145" fill="#f8fafc" stroke="#64748b" stroke-width="1.35" />
  <path d="M 275 180 L 275 35 L 390 35 L 390 108 L 282 108 L 282 180" class="f-amber" stroke="#0f172a" stroke-width="2.5" />
  <line x1="398" y1="88" x2="398" y2="58" class="c-red" marker-end="url(#arr-red)" />
  <line x1="348" y1="27" x2="318" y2="27" class="c-red" marker-end="url(#arr-red)" />
  <line x1="266" y1="92" x2="266" y2="122" class="c-red" marker-end="url(#arr-red)" />
  <line x1="290" y1="158" x2="290" y2="128" class="c-red" marker-end="url(#arr-red)" />
  <line x1="318" y1="116" x2="348" y2="116" class="c-red" marker-end="url(#arr-red)" />
  <text x="325" y="76" class="it">R<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="405" y="76" class="it" fill="#dc2626">π<tspan font-size="10px" dy="3">2</tspan></text>
"""
    return figure_svg(
        "0 0 460 205", body, "fig-8-3", "Period paths pi1 and pi2 on rectangular cells"
    )


def generate_fig_8_4() -> str:
    body = """
  <circle cx="230" cy="135" r="105" class="f-blue" stroke="#0f172a" stroke-width="1.85" />
  <circle cx="230" cy="135" r="52" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.85" />
  <circle cx="282" cy="135" r="28" class="f-amber" opacity="0.55" stroke="#b45309" stroke-width="1.1" stroke-dasharray="3,2" />
  <circle cx="256" cy="90" r="28" class="f-amber" opacity="0.55" stroke="#b45309" stroke-width="1.1" stroke-dasharray="3,2" />
  <circle cx="204" cy="90" r="28" class="f-amber" opacity="0.55" stroke="#b45309" stroke-width="1.1" stroke-dasharray="3,2" />
  <circle cx="230" cy="135" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="282" cy="135" r="3.6" fill="#dc2626" class="pt" />
  <circle cx="256" cy="90" r="3.6" fill="#dc2626" class="pt" />
  <circle cx="204" cy="90" r="3.6" fill="#dc2626" class="pt" />
  <circle cx="178" cy="135" r="3.6" fill="#dc2626" class="pt" />
  <text x="290" y="140" class="it">P<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="260" y="84" class="it">P<tspan font-size="10px" dy="3">k</tspan></text>
  <text x="172" y="82" class="it">P<tspan font-size="10px" dy="3">k+1</tspan></text>
  <text x="150" y="140" class="it">P′<tspan font-size="10px" dy="3">0</tspan></text>
"""
    return figure_svg(
        "0 0 460 265",
        body,
        "fig-8-4",
        "Analytic continuation chain along inner boundary of annulus",
    )


def generate_bonus_fig_6_riemann() -> str:
    body = """
  <path d="M 48 135 C 42 68, 95 28, 152 42 C 198 54, 212 96, 188 128 C 168 154, 195 192, 152 214 C 102 238, 54 198, 48 135 Z" class="f-blue" stroke="#1e3a8a" stroke-width="2" />
  <ellipse cx="122" cy="128" rx="42" ry="34" class="c-sub-blue" stroke-dasharray="4,3" />
  <ellipse cx="122" cy="128" rx="22" ry="18" class="c-sub-blue" stroke-dasharray="3,2" />
  <path d="M 122 128 Q 148 112 188 128" class="c-sub-red" />
  <path d="M 122 128 Q 118 88 132 39" class="c-sub-red" />
  <path d="M 122 128 Q 88 138 48 135" class="c-sub-red" />
  <path d="M 122 128 Q 128 168 136 218" class="c-sub-red" />
  <line x1="122" y1="128" x2="158" y2="128" class="c-red" stroke-width="1.8" marker-end="url(#arr-red)" />
  <circle cx="122" cy="128" r="3.8" fill="#0f172a" class="pt" />
  <text x="108" y="146" class="it">z<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="75" y="75" class="it" fill="#1e3a8a">Ω ≠ ℂ</text>

  <path d="M 218 118 Q 252 96 286 118" class="c-blue" stroke-width="1.8" marker-end="url(#arr-blue)" />
  <text x="226" y="96" class="it" fill="#1e3a8a">w = f(z)</text>
  <text x="218" y="142" class="it" font-size="12.5px" fill="#047857">f′(z<tspan font-size="9px" dy="2">0</tspan><tspan dy="-2">) &gt; 0</tspan></text>

  <circle cx="372" cy="128" r="76" class="f-green" stroke="#047857" stroke-width="2" />
  <circle cx="372" cy="128" r="52" class="c-sub-blue" stroke-dasharray="4,3" />
  <circle cx="372" cy="128" r="28" class="c-sub-blue" stroke-dasharray="3,2" />
  <line x1="296" y1="128" x2="448" y2="128" class="c-sub-red" />
  <line x1="372" y1="52" x2="372" y2="204" class="c-sub-red" />
  <line x1="372" y1="128" x2="412" y2="128" class="c-red" stroke-width="1.8" marker-end="url(#arr-red)" />
  <circle cx="372" cy="128" r="3.8" fill="#0f172a" class="pt" />
  <text x="362" y="145" class="lbl">0</text>
  <text x="348" y="224" class="it" fill="#047857">|w| &lt; 1</text>
"""
    return figure_svg(
        "0 0 475 245",
        body,
        "fig-bonus-6-riemann",
        "Canonical conformal bijection of Riemann Mapping Theorem",
    )


def generate_bonus_fig_7_torus() -> str:
    body = """
  <polygon points="45,185 145,185 185,75 85,75" class="f-blue" stroke="#0f172a" stroke-width="1.5" />
  <line x1="45" y1="185" x2="145" y2="185" class="c-blue" stroke-width="2.2" marker-end="url(#arr-blue)" />
  <line x1="85" y1="75" x2="185" y2="75" class="c-blue" stroke-width="2.2" marker-end="url(#arr-blue)" />
  <line x1="45" y1="185" x2="85" y2="75" class="c-red" stroke-width="2.2" marker-end="url(#arr-red)" />
  <line x1="145" y1="185" x2="185" y2="75" class="c-red" stroke-width="2.2" marker-end="url(#arr-red)" />
  <circle cx="45" cy="185" r="3.5" fill="#0f172a" class="pt" />
  <text x="34" y="202" class="lbl">0</text>
  <text x="92" y="203" class="it" fill="#1e3a8a">ω<tspan font-size="10px" dy="3">1</tspan><tspan dy="-3"> (a)</tspan></text>
  <text x="18" y="128" class="it" fill="#dc2626">ω<tspan font-size="10px" dy="3">2</tspan><tspan dy="-3"> (b)</tspan></text>

  <path d="M 198 130 Q 225 112 252 130" class="c-main" marker-end="url(#arr)" />
  <text x="208" y="110" class="it">ℂ / Λ</text>

  <ellipse cx="358" cy="132" rx="88" ry="56" fill="url(#grad-torus)" stroke="#1e3a8a" stroke-width="1.85" />
  <path d="M 322 126 Q 358 148 394 126" class="c-main" stroke-width="1.6" />
  <path d="M 332 132 Q 358 114 384 132" class="c-main" stroke-width="1.6" fill="#ffffff" />
  <ellipse cx="358" cy="132" rx="64" ry="36" class="c-blue" stroke-width="1.9" stroke-dasharray="5,3" />
  <path d="M 358 96 C 374 96, 374 168, 358 168 C 344 168, 344 96, 358 96 Z" class="c-red" stroke-width="1.9" />
  <text x="405" y="172" class="it" fill="#1e3a8a">a‑cycle</text>
  <text x="348" y="88" class="it" fill="#dc2626">b‑cycle</text>
"""
    return figure_svg(
        "0 0 470 230",
        body,
        "fig-bonus-7-torus",
        "Quotient of period parallelogram onto complex torus C/Lambda",
    )


def generate_fig_1_1_art() -> str:
    body = """
  <polygon points="80,230 220,200 290,60 150,90" class="f-blue" opacity="0.45" />
  <line x1="40" y1="230" x2="420" y2="230" class="ax" marker-end="url(#arr)" />
  <line x1="80" y1="270" x2="80" y2="26" class="ax" marker-end="url(#arr)" />
  <line x1="150" y1="90" x2="290" y2="60" class="c-dash" />
  <line x1="220" y1="200" x2="290" y2="60" class="c-dash" />
  <line x1="80" y1="230" x2="220" y2="200" class="c-main" marker-end="url(#arr)" />
  <line x1="80" y1="230" x2="150" y2="90" class="c-main" marker-end="url(#arr)" />
  <line x1="80" y1="230" x2="290" y2="60" class="c-blue" stroke-width="2.1" marker-end="url(#arr-blue)" />
  <line x1="220" y1="200" x2="150" y2="90" class="c-red-dash" marker-end="url(#arr-red)" />
  <circle cx="80" cy="230" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="220" cy="200" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="150" cy="90" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="290" cy="60" r="3.8" fill="#1e3a8a" class="pt" />
  <text x="425" y="235" class="it">x</text>
  <text x="75" y="22" class="it">y</text>
  <text x="64" y="246" class="lbl">0</text>
  <text x="228" y="212" class="it">b</text>
  <text x="135" y="82" class="it">a</text>
  <text x="302" y="62" class="it" fill="#1e3a8a">a + b</text>
  <text x="195" y="140" class="it" fill="#dc2626">a − b</text>
"""
    return figure_svg(
        "0 0 460 300",
        body,
        "fig-1-1",
        "Vector addition and parallelogram law in complex plane",
    )


def generate_fig_1_2_art() -> str:
    body = """
  <polygon points="70,250 170,250 197,191" class="f-amber" opacity="0.58" />
  <polygon points="70,250 212,139 184,25" class="f-blue" opacity="0.48" />
  <line x1="40" y1="250" x2="440" y2="250" class="ax" marker-end="url(#arr)" />
  <line x1="70" y1="290" x2="70" y2="26" class="ax" marker-end="url(#arr)" />
  <line x1="170" y1="250" x2="197" y2="191" class="c-dash" />
  <line x1="212" y1="139" x2="184" y2="25" class="c-dash" />
  <line x1="70" y1="250" x2="197" y2="191" class="c-main" marker-end="url(#arr)" />
  <line x1="70" y1="250" x2="212" y2="139" class="c-main" marker-end="url(#arr)" />
  <line x1="70" y1="250" x2="184" y2="25" class="c-green" stroke-width="2.2" marker-end="url(#arr-green)" />
  <path d="M 120 250 A 50 50 0 0 0 115 229" class="c-red" />
  <path d="M 135 250 A 65 65 0 0 0 121 210" class="c-blue" />
  <circle cx="70" cy="250" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="170" cy="250" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="197" cy="191" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="212" cy="139" r="3.4" fill="#0f172a" class="pt" />
  <circle cx="184" cy="25" r="3.8" fill="#047857" class="pt" />
  <text x="445" y="255" class="it">x</text>
  <text x="65" y="22" class="it">y</text>
  <text x="54" y="266" class="lbl">0</text>
  <text x="168" y="268" class="lbl">1</text>
  <text x="204" y="193" class="it">a<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="218" y="138" class="it">a<tspan font-size="11px" dy="3">2</tspan></text>
  <text x="192" y="28" class="it" fill="#047857">a<tspan font-size="11px" dy="3">1</tspan><tspan dy="-3">a</tspan><tspan font-size="11px" dy="3">2</tspan></text>
  <text x="126" y="243" class="it" font-size="12px" fill="#dc2626">φ<tspan font-size="9px" dy="2">1</tspan></text>
  <text x="138" y="228" class="it" font-size="12px" fill="#1e3a8a">φ<tspan font-size="9px" dy="2">2</tspan></text>
"""
    return figure_svg(
        "0 0 480 320", body, "fig-1-2", "Complex multiplication via similar triangles"
    )


def generate_fig_1_3_art() -> str:
    body = """
  <polygon points="50,250 360,250 490,190 180,190" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.3" />
  <circle cx="270" cy="220" r="110" fill="url(#grad-torus)" opacity="0.45" stroke="#0f172a" stroke-width="1.85" />
  <ellipse cx="270" cy="220" rx="110" ry="34" class="c-dash" />
  <path d="M 160 220 A 110 34 0 0 0 380 220" class="c-main" stroke-width="1.4" />
  <polygon points="270,110 270,220 410,200" class="f-amber" opacity="0.35" />
  <line x1="270" y1="350" x2="270" y2="38" class="ax" marker-end="url(#arr)" />
  <line x1="270" y1="220" x2="480" y2="220" class="ax" marker-end="url(#arr)" />
  <line x1="270" y1="220" x2="130" y2="275" class="ax" marker-end="url(#arr)" />
  <line x1="270" y1="220" x2="410" y2="200" class="c-blue" stroke-dasharray="4,3" />
  <line x1="340" y1="155" x2="340" y2="210" class="c-dash" />
  <line x1="270" y1="110" x2="410" y2="200" class="c-red" stroke-width="1.9" marker-end="url(#arr-red)" />
  <circle cx="270" cy="220" r="3.2" fill="#0f172a" class="pt" />
  <circle cx="270" cy="110" r="3.6" fill="#0f172a" class="pt" />
  <circle cx="270" cy="330" r="3.2" fill="#0f172a" class="pt" />
  <circle cx="340" cy="155" r="3.8" fill="#dc2626" class="pt" />
  <circle cx="410" cy="200" r="3.8" fill="#dc2626" class="pt" />
  <text x="62" y="240" class="it" fill="#475569">x<tspan font-size="10px" dy="3">3</tspan><tspan dy="-3"> = 0 (ℂ)</tspan></text>
  <text x="278" y="45" class="it">x<tspan font-size="11px" dy="3">3</tspan></text>
  <text x="485" y="225" class="it">x<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="112" y="285" class="it">x<tspan font-size="11px" dy="3">2</tspan></text>
  <text x="256" y="236" class="lbl">0</text>
  <text x="280" y="108" class="it">N (0,0,1)</text>
  <text x="278" y="344" class="it">S</text>
  <text x="348" y="152" class="it" fill="#dc2626">P(x<tspan font-size="11px" dy="2">1</tspan><tspan dy="-2">, x</tspan><tspan font-size="11px" dy="2">2</tspan><tspan dy="-2">, x</tspan><tspan font-size="11px" dy="2">3</tspan><tspan dy="-2">)</tspan></text>
  <text x="418" y="202" class="it" fill="#dc2626">z = x + iy</text>
"""
    return figure_svg(
        "0 0 540 375",
        body,
        "fig-1-3",
        "Stereographic projection from Riemann sphere to complex plane",
    )


def generate_fig_3_1_art() -> str:
    body = """
  <path d="M 82 132 C 78 68, 128 32, 172 44 C 204 53, 206 94, 178 106 C 160 114, 156 124, 158 132 Z" class="f-blue" />
  <path d="M 82 132 C 80 185, 118 218, 168 212 C 204 208, 206 168, 178 152 C 162 142, 158 136, 158 132 Z" class="f-amber" />
  <path d="M 82 132 C 78 68, 128 32, 172 44 C 204 53, 206 94, 178 106 C 160 114, 156 124, 158 132 C 158 136, 162 142, 178 152 C 206 168, 204 208, 168 212 C 118 218, 80 185, 82 132 Z" class="c-main" stroke-width="1.85" />
  <path d="M 82 132 C 108 123, 134 123, 158 132" class="c-blue" />
  <text x="128" y="86" class="it" fill="#1e3a8a">Ω<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="128" y="182" class="it" fill="#b45309">Ω<tspan font-size="11px" dy="3">2</tspan></text>

  <path d="M 225 128 Q 268 108 310 128" class="c-blue" marker-end="url(#arr-blue)" />
  <text x="246" y="108" class="it" fill="#1e3a8a">w = f(z)</text>

  <path d="M 346 136 C 344 192, 392 222, 446 212 C 488 204, 502 152, 476 126 C 456 108, 428 124, 426 146 C 424 162, 404 164, 398 144 C 396 138, 372 136, 346 136 Z" class="f-amber" />
  <path d="M 346 136 C 344 76, 394 44, 448 54 C 490 62, 504 114, 476 142 C 456 160, 428 144, 426 122 C 424 106, 404 104, 398 124 C 396 132, 372 136, 346 136 Z" class="f-blue" />
  <path d="M 432 132 C 446 114, 470 114, 482 132 C 470 152, 446 152, 432 132 Z" class="f-green" opacity="0.65" />
  <path d="M 346 136 C 344 76, 394 44, 448 54 C 490 62, 504 114, 476 142 C 456 160, 428 144, 426 122 C 424 106, 404 104, 398 124 C 396 132, 396 138, 398 144 C 404 164, 424 162, 426 146" class="c-main" stroke-width="1.85" />
  <path d="M 346 136 C 344 192, 392 222, 446 212 C 488 204, 502 152, 476 126" class="c-main" stroke-width="1.85" />
  <path d="M 426 146 C 428 124, 456 108, 476 126" class="c-red-dash" />
  <line x1="346" y1="136" x2="397" y2="136" class="c-blue" />
  <text x="412" y="86" class="it" fill="#1e3a8a">Ω′<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="404" y="196" class="it" fill="#b45309">Ω′<tspan font-size="11px" dy="3">2</tspan></text>
"""
    return figure_svg(
        "0 0 560 250",
        body,
        "fig-3-1",
        "Riemann surface sheets for overlapping conformal image",
    )


def generate_fig_3_2_art() -> str:
    body = """
  <circle cx="150" cy="135" r="88" class="f-blue" stroke="#1e3a8a" stroke-width="1.85" />
  <polygon points="150,135 183,53 288,80" class="f-amber" opacity="0.45" />
  <circle cx="246.5" cy="96.6" r="55" class="c-sub-blue" stroke-dasharray="4,3" />
  <line x1="150" y1="135" x2="335" y2="61" class="c-main" marker-end="url(#arr)" />
  <line x1="150" y1="135" x2="183" y2="53" class="c-green" stroke-width="1.7" />
  <line x1="183" y1="53" x2="288" y2="80" class="c-green" stroke-width="1.7" />
  <line x1="183" y1="53" x2="205" y2="113" class="c-red-dash" />
  <circle cx="150" cy="135" r="3.5" fill="#0f172a" class="pt" />
  <circle cx="183" cy="53" r="3.4" fill="#047857" class="pt" />
  <circle cx="205" cy="113" r="3.6" fill="#dc2626" class="pt" />
  <circle cx="288" cy="80" r="3.6" fill="#dc2626" class="pt" />
  <text x="82" y="66" class="it" fill="#1e3a8a">C (|z − a| = R)</text>
  <text x="135" y="152" class="it">a</text>
  <text x="204" y="132" class="it" fill="#dc2626">z</text>
  <text x="288" y="100" class="it" fill="#dc2626">z*</text>
  <text x="152" y="92" class="it" fill="#047857">R</text>
"""
    return figure_svg(
        "0 0 480 260", body, "fig-3-2", "Geometric inversion across a circle"
    )


def generate_fig_3_3_art() -> str:
    body = """
  <line x1="30" y1="150" x2="470" y2="150" class="ax" marker-end="url(#arr)" />
  <line x1="250" y1="280" x2="250" y2="20" class="ax" marker-end="url(#arr)" />
  <circle cx="250" cy="150" r="80" class="c-blue" />
  <circle cx="250" cy="122" r="85" class="c-sub-blue" />
  <circle cx="250" cy="178" r="85" class="c-sub-blue" />
  <circle cx="250" cy="95" r="97" class="c-blue" />
  <circle cx="250" cy="205" r="97" class="c-blue" />
  <circle cx="250" cy="55" r="124" class="c-blue" />
  <circle cx="250" cy="245" r="124" class="c-blue" />
  <circle cx="156" cy="150" r="18" class="c-sub-red" />
  <circle cx="145" cy="150" r="32" class="c-red-dash" />
  <circle cx="132" cy="150" r="48" class="c-sub-red" />
  <circle cx="118" cy="150" r="66" class="c-red-dash" />
  <circle cx="344" cy="150" r="18" class="c-sub-red" />
  <circle cx="355" cy="150" r="32" class="c-red-dash" />
  <circle cx="368" cy="150" r="48" class="c-sub-red" />
  <circle cx="382" cy="150" r="66" class="c-red-dash" />
  <circle cx="170" cy="150" r="12" fill="url(#glow-pole)" />
  <circle cx="330" cy="150" r="12" fill="url(#glow-pole)" />
  <circle cx="170" cy="150" r="3.8" fill="#0f172a" class="pt" />
  <circle cx="330" cy="150" r="3.8" fill="#0f172a" class="pt" />
  <text x="156" y="168" class="it">a</text>
  <text x="336" y="168" class="it">b</text>
  <text x="348" y="54" class="it" fill="#1e3a8a">C<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="415" y="102" class="it" fill="#dc2626">C<tspan font-size="11px" dy="3">2</tspan></text>
"""
    return figure_svg(
        "0 0 500 300",
        body,
        "fig-3-3",
        "Orthogonal Steiner and Apollonius circle families",
    )


def generate_fig_3_9_art() -> str:
    body = """
  <line x1="30" y1="140" x2="470" y2="140" class="ax" marker-end="url(#arr)" />
  <line x1="250" y1="260" x2="250" y2="20" class="ax" marker-end="url(#arr)" />
  <ellipse cx="250" cy="140" rx="96" ry="38" class="c-sub-blue" />
  <ellipse cx="250" cy="140" rx="115" ry="68" class="c-blue" />
  <ellipse cx="250" cy="140" rx="140" ry="88" class="c-sub-blue" />
  <ellipse cx="250" cy="140" rx="165" ry="108" class="c-blue" />
  <path d="M 110 35 Q 215 140 110 245" class="c-red-dash" />
  <path d="M 390 35 Q 285 140 390 245" class="c-red-dash" />
  <path d="M 85 50 Q 204 140 85 230" class="c-sub-red" />
  <path d="M 415 50 Q 296 140 415 230" class="c-sub-red" />
  <path d="M 60 65 Q 192 140 60 215" class="c-red-dash" />
  <path d="M 440 65 Q 308 140 440 215" class="c-red-dash" />
  <line x1="160" y1="140" x2="340" y2="140" stroke="#0f172a" stroke-width="3.4" stroke-linecap="round" />
  <circle cx="160" cy="140" r="3.6" fill="#dc2626" class="pt" />
  <circle cx="340" cy="140" r="3.6" fill="#dc2626" class="pt" />
  <text x="145" y="160" class="lbl">−1</text>
  <text x="336" y="160" class="lbl">+1</text>
"""
    return figure_svg(
        "0 0 500 280", body, "fig-3-9", "Confocal ellipses and hyperbolas for w = cos z"
    )


def generate_bonus_fig_2_1_art() -> str:
    body = """
  <line x1="40" y1="150" x2="420" y2="150" class="ax" marker-end="url(#arr)" />
  <line x1="180" y1="265" x2="180" y2="25" class="ax" marker-end="url(#arr)" />
  <circle cx="230" cy="135" r="96" class="f-blue" stroke="#1e3a8a" stroke-width="1.8" stroke-dasharray="5,3" />
  <circle cx="230" cy="135" r="58" class="f-green" stroke="#047857" stroke-width="1.6" />
  <line x1="230" y1="135" x2="305" y2="75" class="c-red" marker-end="url(#arr-red)" />
  <line x1="230" y1="135" x2="176" y2="114" class="c-green" marker-end="url(#arr-green)" />
  <circle cx="305" cy="75" r="14" fill="url(#glow-pole)" />
  <circle cx="230" cy="135" r="3.5" fill="#0f172a" class="pt" />
  <circle cx="305" cy="75" r="4.0" fill="#dc2626" class="pt" />
  <text x="216" y="152" class="it">z<tspan font-size="10px" dy="3">0</tspan></text>
  <text x="315" y="74" class="it" fill="#dc2626">z<tspan font-size="10px" dy="3">s</tspan><tspan dy="-3"> (singularity)</tspan></text>
  <text x="262" y="100" class="it" fill="#dc2626">R</text>
  <text x="188" y="116" class="it" fill="#047857">r &lt; R</text>
  <text x="288" y="220" class="it" fill="#1e3a8a">|z − z<tspan font-size="10px" dy="3">0</tspan><tspan dy="-3">| &lt; R</tspan></text>
"""
    return figure_svg(
        "0 0 460 280",
        body,
        "fig-bonus-2-1",
        "Power series disk of convergence obstructed by nearest singularity",
    )


def generate_bonus_fig_4_cauchy_art() -> str:
    body = """
  <path d="M 95 140 C 85 65, 175 30, 265 42 C 365 55, 405 115, 385 175 C 365 230, 255 240, 165 222 C 110 210, 102 180, 95 140 Z" class="f-blue" stroke="#1e3a8a" stroke-width="2" />
  <ellipse cx="245" cy="135" rx="88" ry="56" class="c-sub-blue" stroke-dasharray="4,3" />
  <circle cx="245" cy="135" r="36" fill="#ffffff" stroke="#dc2626" stroke-width="1.75" stroke-dasharray="4,2" />
  <line x1="278" y1="39" x2="255" y2="37" class="c-blue" marker-end="url(#arr-blue)" />
  <line x1="258" y1="99" x2="235" y2="99" class="c-red" marker-end="url(#arr-red)" />
  <line x1="245" y1="135" x2="281" y2="135" class="c-red" />
  <circle cx="245" cy="135" r="14" fill="url(#glow-pole)" />
  <circle cx="245" cy="135" r="3.6" fill="#dc2626" class="pt" />
  <text x="234" y="152" class="it" fill="#dc2626">z</text>
  <text x="258" y="128" class="it" fill="#dc2626">δ</text>
  <text x="135" y="95" class="it" fill="#1e3a8a">Ω</text>
  <text x="368" y="78" class="it" fill="#1e3a8a">γ</text>
  <text x="268" y="185" class="it" fill="#dc2626">C<tspan font-size="10px" dy="3">δ</tspan></text>
"""
    return figure_svg(
        "0 0 480 265",
        body,
        "fig-bonus-4-cauchy",
        "Homology deformation onto small circle for Cauchy Integral Formula",
    )


def generate_bonus_fig_5_laurent_art() -> str:
    body = """
  <circle cx="230" cy="138" r="105" class="f-amber" stroke="#b45309" stroke-width="1.8" stroke-dasharray="5,3" />
  <circle cx="230" cy="138" r="74" class="c-green" stroke-width="2.1" />
  <circle cx="230" cy="138" r="42" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.8" stroke-dasharray="5,3" />
  <line x1="230" y1="138" x2="272" y2="138" class="c-blue" />
  <line x1="230" y1="138" x2="156" y2="64" stroke="#b45309" stroke-width="1.5" />
  <circle cx="230" cy="138" r="3.5" fill="#0f172a" class="pt" />
  <circle cx="282" cy="96" r="3.8" fill="#dc2626" class="pt" />
  <text x="220" y="154" class="it">a</text>
  <text x="246" y="132" class="it" fill="#1e3a8a">r<tspan font-size="10px" dy="3">1</tspan></text>
  <text x="176" y="108" class="it" fill="#b45309">r<tspan font-size="10px" dy="3">2</tspan></text>
  <text x="290" y="98" class="it" fill="#dc2626">z</text>
  <text x="285" y="185" class="it" fill="#047857">C</text>
"""
    return figure_svg(
        "0 0 460 275",
        body,
        "fig-bonus-5-laurent",
        "Concentric annulus r1 < |z - a| < r2 for Laurent expansion",
    )


EXTRA_SVG_GENERATORS = {
    "fig_1_1_vector_addition.svg": generate_fig_1_1_art,
    "fig_1_2_vector_multiplication.svg": generate_fig_1_2_art,
    "fig_1_3_stereographic_projection.svg": generate_fig_1_3_art,
    "fig_3_1.svg": generate_fig_3_1_art,
    "fig_3_2.svg": generate_fig_3_2_art,
    "fig_3_3.svg": generate_fig_3_3_art,
    "fig_3_4.svg": generate_fig_3_4,
    "fig_3_5.svg": generate_fig_3_5,
    "fig_3_6.svg": generate_fig_3_6,
    "fig_3_7.svg": generate_fig_3_7,
    "fig_3_8.svg": generate_fig_3_8,
    "fig_3_9.svg": generate_fig_3_9_art,
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

BONUS_SVG_GENERATORS = {
    "fig_bonus_2_1.svg": generate_bonus_fig_2_1_art,
    "fig_bonus_4_cauchy.svg": generate_bonus_fig_4_cauchy_art,
    "fig_bonus_5_laurent.svg": generate_bonus_fig_5_laurent_art,
    "fig_bonus_6_riemann.svg": generate_bonus_fig_6_riemann,
    "fig_bonus_7_torus.svg": generate_bonus_fig_7_torus,
}


def _figure_spec(filename: str, build: Callable[[], str]) -> FigureSpec:
    fig_id = filename.removeprefix("fig_").removesuffix(".svg")
    parts = fig_id.removeprefix("bonus_").split("_")
    if fig_id.startswith("bonus_"):
        label = f"Bonus {parts[0]} · {' '.join(parts[1:]) or 'illustration'}"
    else:
        label = f"Fig. {parts[0]}.{parts[1]}"
    return FigureSpec(fig_id=fig_id, label=label, chapter=int(parts[0]), build=build)


AHLFORS_FIGURE_BOOK = FigureBook(
    slug="ahlfors_complete",
    title="Lars Ahlfors · Complex Analysis",
    subtitle=(
        f"{len(EXTRA_SVG_GENERATORS)} Canonical Textbook Figures + "
        f"{len(BONUS_SVG_GENERATORS)} Master Pedagogical Illustrations · Web-Ready Layered SVGs"
    ),
    figures=tuple(
        _figure_spec(name, build)
        for name, build in {**EXTRA_SVG_GENERATORS, **BONUS_SVG_GENERATORS}.items()
    ),
    chapter_titles={ch["number"]: ch["title"] for ch in CHAPTERS},
    search_hint="Search Fig. 3.8, Riemann, torus...",
)
AHLFORS_CANONICAL_BOOK = replace(
    AHLFORS_FIGURE_BOOK,
    figures=tuple(
        f for f in AHLFORS_FIGURE_BOOK.figures if not f.fig_id.startswith("bonus_")
    ),
)

_STALE_SCANS = (
    "fig_1_1.png",
    "fig_1_1_vector_addition.png",
    "fig_1_2.png",
    "fig_1_2_vector_multiplication.png",
    "fig_1_3.png",
    "fig_7_0.png",
)


def _keep_original_scans(fig_dir: Path) -> None:
    raw_dir = fig_dir.parent / "figures_raw"
    if raw_dir.exists():
        return
    raw_dir.mkdir(parents=True)
    for png_path in sorted(fig_dir.glob("fig_*.png")):
        _ = shutil.copy2(png_path, raw_dir / png_path.name)


def generate_all_ahlfors_figures(out_dir: Path) -> None:
    """Write the canonical figures as SVG, replacing the scans they reproduce."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _keep_original_scans(out_dir)
    for stale in _STALE_SCANS:
        (out_dir / stale).unlink(missing_ok=True)
    _ = render_figures(AHLFORS_CANONICAL_BOOK, out_dir)


def generate_colorful_ahlfors_figures(src_fig_dir: Path, color_fig_dir: Path) -> None:
    """Write canonical and bonus figures for the illustrated edition, plus the web gallery."""
    src_fig_dir = Path(src_fig_dir)
    generate_all_ahlfors_figures(src_fig_dir)
    _ = render_figures(
        AHLFORS_FIGURE_BOOK, Path(color_fig_dir), src_fig_dir.parent / "web_figures"
    )
