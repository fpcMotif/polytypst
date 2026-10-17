"""Vector figure generators for Lars Ahlfors Complex Analysis (1979 McGraw-Hill style)."""

from pathlib import Path


def generate_fig_1_1() -> str:
    """FIG. 1-1. Vector addition (Parallelogram law in complex plane)."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 300" width="100%" height="100%">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#111827" />
    </marker>
    <marker id="arrow-axis" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M 0 2 L 7 5 L 0 8 z" fill="#4b5563" />
    </marker>
  </defs>

  <style>
    .axis { stroke: #6b7280; stroke-width: 1; stroke-dasharray: 4,3; }
    .vector { stroke: #111827; stroke-width: 1.8; fill: none; }
    .diag { stroke: #1e3a8a; stroke-width: 2; fill: none; }
    .diff { stroke: #b45309; stroke-width: 1.4; stroke-dasharray: 4,3; fill: none; }
    .parallelogram { stroke: #9ca3af; stroke-width: 1.2; stroke-dasharray: 4,4; fill: none; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", "Times New Roman", serif; font-size: 15px; fill: #111827; }
    .math-italic { font-style: italic; }
    .dot { fill: #111827; }
  </style>

  <!-- Coordinate Axes -->
  <line x1="40" y1="230" x2="420" y2="230" class="axis" marker-end="url(#arrow-axis)" />
  <line x1="80" y1="270" x2="80" y2="30" class="axis" marker-end="url(#arrow-axis)" />
  <text x="425" y="235" class="label math-italic">x</text>
  <text x="75" y="24" class="label math-italic">y</text>

  <!-- Origin -->
  <circle cx="80" cy="230" r="3" class="dot" />
  <text x="64" y="246" class="label">0</text>

  <!-- Points: Origin O(80, 230), b(220, 200), a(150, 90), a+b(290, 60) -->
  <!-- Vector b -->
  <line x1="80" y1="230" x2="220" y2="200" class="vector" marker-end="url(#arrow)" />
  <circle cx="220" cy="200" r="3" class="dot" />
  <text x="228" y="212" class="label math-italic">b</text>

  <!-- Vector a -->
  <line x1="80" y1="230" x2="150" y2="90" class="vector" marker-end="url(#arrow)" />
  <circle cx="150" cy="90" r="3" class="dot" />
  <text x="135" y="82" class="label math-italic">a</text>

  <!-- Parallelogram completion -->
  <line x1="150" y1="90" x2="290" y2="60" class="parallelogram" />
  <line x1="220" y1="200" x2="290" y2="60" class="parallelogram" />

  <!-- Diagonal a + b -->
  <line x1="80" y1="230" x2="290" y2="60" class="diag" marker-end="url(#arrow)" />
  <circle cx="290" cy="60" r="3.5" class="dot" />
  <text x="302" y="62" class="label math-italic">a + b</text>

  <!-- Difference vector a - b connecting b to a -->
  <line x1="220" y1="200" x2="150" y2="90" class="diff" marker-end="url(#arrow)" />
  <text x="195" y="140" class="label math-italic" fill="#b45309">a − b</text>
</svg>"""


def generate_fig_1_2() -> str:
    """FIG. 1-2. Vector multiplication (Similar triangles in complex plane)."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 320" width="100%" height="100%">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#111827" />
    </marker>
    <marker id="arrow-axis" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M 0 2 L 7 5 L 0 8 z" fill="#4b5563" />
    </marker>
  </defs>

  <style>
    .axis { stroke: #6b7280; stroke-width: 1; stroke-dasharray: 4,3; }
    .vector { stroke: #111827; stroke-width: 1.8; fill: none; }
    .prod { stroke: #047857; stroke-width: 2.2; fill: none; }
    .tri { stroke: #9ca3af; stroke-width: 1.2; stroke-dasharray: 4,4; fill: none; }
    .arc { stroke: #4b5563; stroke-width: 1; fill: none; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", "Times New Roman", serif; font-size: 15px; fill: #111827; }
    .math-italic { font-style: italic; }
    .dot { fill: #111827; }
  </style>

  <!-- Axes -->
  <line x1="40" y1="250" x2="440" y2="250" class="axis" marker-end="url(#arrow-axis)" />
  <line x1="70" y1="290" x2="70" y2="30" class="axis" marker-end="url(#arrow-axis)" />
  <text x="445" y="255" class="label math-italic">x</text>
  <text x="65" y="24" class="label math-italic">y</text>

  <!-- Origin -->
  <circle cx="70" cy="250" r="3" class="dot" />
  <text x="54" y="266" class="label">0</text>

  <!-- Point 1 on real axis: (170, 250) -> r=100 -->
  <circle cx="170" cy="250" r="3" class="dot" />
  <text x="168" y="268" class="label">1</text>

  <!-- Vector a1: angle 25 deg, length 140 -> (70 + 140*cos(25), 250 - 140*sin(25)) = (197, 191) -->
  <line x1="70" y1="250" x2="197" y2="191" class="vector" marker-end="url(#arrow)" />
  <circle cx="197" cy="191" r="3" class="dot" />
  <text x="204" y="193" class="label math-italic">a<tspan font-size="11px" dy="3">1</tspan></text>

  <!-- Vector a2: angle 38 deg, length 180 -> (70 + 180*cos(38), 250 - 180*sin(38)) = (212, 139) -->
  <line x1="70" y1="250" x2="212" y2="139" class="vector" marker-end="url(#arrow)" />
  <circle cx="212" cy="139" r="3" class="dot" />
  <text x="218" y="138" class="label math-italic">a<tspan font-size="11px" dy="3">2</tspan></text>

  <!-- Triangle (0, 1, a1) completion -->
  <line x1="170" y1="250" x2="197" y2="191" class="tri" />

  <!-- Product a1 * a2: angle 25+38 = 63 deg, length 1.4 * 1.8 * 100 = 252 -> (70 + 252*cos(63), 250 - 252*sin(63)) = (184, 25) -->
  <line x1="70" y1="250" x2="184" y2="25" class="prod" marker-end="url(#arrow)" />
  <circle cx="184" cy="25" r="3.5" class="dot" />
  <text x="192" y="28" class="label math-italic">a<tspan font-size="11px" dy="3">1</tspan>a<tspan font-size="11px" dy="0">2</tspan></text>

  <!-- Triangle (0, a2, a1*a2) completion -->
  <line x1="212" y1="139" x2="184" y2="25" class="tri" />

  <!-- Angle arcs -->
  <!-- arc for phi1 -->
  <path d="M 120 250 A 50 50 0 0 0 115 229" class="arc" />
  <text x="127" y="243" class="label math-italic" font-size="12px">φ<tspan font-size="9px" dy="2">1</tspan></text>

  <!-- arc for phi2 -->
  <path d="M 135 250 A 65 65 0 0 0 121 210" class="arc" />
  <text x="138" y="228" class="label math-italic" font-size="12px">φ<tspan font-size="9px" dy="2">2</tspan></text>
</svg>"""


def generate_fig_1_3() -> str:
    """FIG. 1-3. Stereographic projection (Riemann Sphere onto complex plane)."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 440" width="100%" height="100%">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#111827" />
    </marker>
    <marker id="arrow-axis" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M 0 2 L 7 5 L 0 8 z" fill="#4b5563" />
    </marker>
  </defs>

  <style>
    .plane { fill: #f8fafc; stroke: #94a3b8; stroke-width: 1.2; }
    .axis { stroke: #64748b; stroke-width: 1; stroke-dasharray: 4,3; }
    .sphere-contour { stroke: #1e293b; stroke-width: 1.8; fill: none; }
    .sphere-equator-front { stroke: #334155; stroke-width: 1.2; fill: none; }
    .sphere-equator-back { stroke: #94a3b8; stroke-width: 1; stroke-dasharray: 3,3; fill: none; }
    .ray { stroke: #dc2626; stroke-width: 1.6; fill: none; }
    .ray-dash { stroke: #dc2626; stroke-width: 1.2; stroke-dasharray: 3,3; fill: none; }
    .drop-line { stroke: #9ca3af; stroke-width: 1; stroke-dasharray: 3,3; fill: none; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", "Times New Roman", serif; font-size: 15px; fill: #0f172a; }
    .math-italic { font-style: italic; }
    .dot { fill: #0f172a; }
    .dot-red { fill: #dc2626; }
  </style>

  <!-- Equatorial Complex Plane (Perspective Parallelogram) -->
  <polygon points="50,250 360,250 490,190 180,190" class="plane" />
  <text x="60" y="240" class="label math-italic" fill="#64748b">ζ = 0 (ℂ)</text>

  <!-- Center O(270, 220), Radius R=110 -->
  <!-- Sphere Back Equator -->
  <ellipse cx="270" cy="220" rx="110" ry="34" class="sphere-equator-back" />

  <!-- Coordinate Axes in R^3 -->
  <!-- Vertical x3 (zeta) axis -->
  <line x1="270" y1="350" x2="270" y2="40" class="axis" marker-end="url(#arrow-axis)" />
  <text x="278" y="45" class="label math-italic">x<tspan font-size="11px" dy="3">3</tspan></text>

  <!-- x1 axis (pointing right-forward) -->
  <line x1="270" y1="220" x2="480" y2="220" class="axis" marker-end="url(#arrow-axis)" />
  <text x="485" y="225" class="label math-italic">x<tspan font-size="11px" dy="3">1</tspan></text>

  <!-- x2 axis (pointing left-forward) -->
  <line x1="270" y1="220" x2="130" y2="275" class="axis" marker-end="url(#arrow-axis)" />
  <text x="115" y="285" class="label math-italic">x<tspan font-size="11px" dy="3">2</tspan></text>

  <!-- Sphere Silhouette Circle -->
  <circle cx="270" cy="220" r="110" class="sphere-contour" />

  <!-- Sphere Front Equator -->
  <path d="M 160 220 A 110 34 0 0 0 380 220" class="sphere-equator-front" />

  <!-- Center Origin O -->
  <circle cx="270" cy="220" r="2.5" class="dot" />
  <text x="256" y="235" class="label">0</text>

  <!-- North Pole N(0,0,1) at (270, 110) -->
  <circle cx="270" cy="110" r="3.5" class="dot" />
  <text x="280" y="108" class="label math-italic">N (0,0,1)</text>

  <!-- Point P(xi, eta, zeta) on sphere surface: e.g. angle 40 deg from top right -> (340, 155) -->
  <!-- Point z = x + iy on equatorial plane: (410, 200) -->
  <!-- Projection Ray from N(270,110) through P(340,155) to z(410,200) -->
  <line x1="270" y1="110" x2="340" y2="155" class="ray" />
  <line x1="340" y1="155" x2="410" y2="200" class="ray" marker-end="url(#arrow)" />

  <!-- Point P -->
  <circle cx="340" cy="155" r="3.5" class="dot-red" />
  <text x="348" y="152" class="label math-italic" fill="#dc2626">P(x<tspan font-size="11px" dy="2">1</tspan>, x<tspan font-size="11px" dy="0">2</tspan>, x<tspan font-size="11px" dy="0">3</tspan>)</text>

  <!-- Point z on complex plane -->
  <circle cx="410" cy="200" r="3.5" class="dot-red" />
  <text x="418" y="202" class="label math-italic" fill="#dc2626">z = x + iy</text>

  <!-- Drop line from P to equator plane -->
  <line x1="340" y1="155" x2="340" y2="225" class="drop-line" />
  <circle cx="340" cy="225" r="2" fill="#9ca3af" />

  <!-- South pole S(0,0,-1) at (270, 330) -->
  <circle cx="270" cy="330" r="2.5" class="dot" />
  <text x="278" y="342" class="label math-italic">S</text>
</svg>"""


def generate_fig_3_1() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 250" width="100%" height="100%">
  <defs>
    <marker id="arrow-map" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1e3a8a" />
    </marker>
    <pattern id="stipple-amber" width="6" height="6" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="0.8" fill="#b45309" opacity="0.45" />
      <circle cx="4.5" cy="4.5" r="0.8" fill="#b45309" opacity="0.45" />
    </pattern>
  </defs>
  <style>
    .outline { stroke: #0f172a; stroke-width: 1.8; fill: none; stroke-linejoin: round; }
    .div-line { stroke: #1e3a8a; stroke-width: 1.5; fill: none; }
    .hidden-arc { stroke: #b45309; stroke-width: 1.5; stroke-dasharray: 4,3; fill: none; }
    .omega1 { fill: #dbeafe; fill-opacity: 0.72; }
    .omega2 { fill: #fef3c7; fill-opacity: 0.78; }
    .overlap { fill: #c7d2fe; fill-opacity: 0.75; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 16px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>

  <!-- Left: Domain Omega = Omega_1 U Omega_2 -->
  <path d="M 82 132 C 78 68, 128 32, 172 44 C 204 53, 206 94, 178 106 C 160 114, 156 124, 158 132 Z" class="omega1" />
  <path d="M 82 132 C 80 185, 118 218, 168 212 C 204 208, 206 168, 178 152 C 162 142, 158 136, 158 132 Z" class="omega2" />
  <path d="M 82 132 C 80 185, 118 218, 168 212 C 204 208, 206 168, 178 152 C 162 142, 158 136, 158 132 Z" fill="url(#stipple-amber)" />
  <path d="M 82 132 C 78 68, 128 32, 172 44 C 204 53, 206 94, 178 106 C 160 114, 156 124, 158 132 C 158 136, 162 142, 178 152 C 206 168, 204 208, 168 212 C 118 218, 80 185, 82 132 Z" class="outline" />
  <path d="M 82 132 C 108 123, 134 123, 158 132" class="div-line" />
  <text x="128" y="86" class="label math-italic" fill="#1e3a8a">Ω<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="128" y="182" class="label math-italic" fill="#92400e">Ω<tspan font-size="11px" dy="3">2</tspan></text>

  <!-- Mapping arrow f(z) -->
  <path d="M 225 128 Q 268 108 310 128" stroke="#1e3a8a" stroke-width="1.6" fill="none" marker-end="url(#arrow-map)" />
  <text x="252" y="108" class="label math-italic" fill="#1e3a8a">w = f(z)</text>

  <!-- Right: Doubly-covered image Omega'_1 U Omega'_2 with self-overlapping lobe -->
  <!-- Lower sheet Omega'_2 -->
  <path d="M 346 136 C 344 192, 392 222, 446 212 C 488 204, 502 152, 476 126 C 456 108, 428 124, 426 146 C 424 162, 404 164, 398 144 C 396 138, 372 136, 346 136 Z" class="omega2" />
  <path d="M 346 136 C 344 192, 392 222, 446 212 C 488 204, 502 152, 476 126 C 456 108, 428 124, 426 146 C 424 162, 404 164, 398 144 C 396 138, 372 136, 346 136 Z" fill="url(#stipple-amber)" />
  <!-- Upper sheet Omega'_1 -->
  <path d="M 346 136 C 344 76, 394 44, 448 54 C 490 62, 504 114, 476 142 C 456 160, 428 144, 426 122 C 424 106, 404 104, 398 124 C 396 132, 372 136, 346 136 Z" class="omega1" />
  <!-- Doubly covered overlap lens -->
  <path d="M 432 132 C 446 114, 470 114, 482 132 C 470 152, 446 152, 432 132 Z" class="overlap" />
  <!-- Outlines & hidden boundary -->
  <path d="M 346 136 C 344 76, 394 44, 448 54 C 490 62, 504 114, 476 142 C 456 160, 428 144, 426 122 C 424 106, 404 104, 398 124 C 396 132, 396 138, 398 144 C 404 164, 424 162, 426 146" class="outline" />
  <path d="M 346 136 C 344 192, 392 222, 446 212 C 488 204, 502 152, 476 126" class="outline" />
  <path d="M 426 146 C 428 124, 456 108, 476 126" class="hidden-arc" />
  <line x1="346" y1="136" x2="397" y2="136" class="div-line" />
  <text x="412" y="86" class="label math-italic" fill="#1e3a8a">Ω′<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="404" y="196" class="label math-italic" fill="#92400e">Ω′<tspan font-size="11px" dy="3">2</tspan></text>
</svg>"""


def generate_fig_3_2() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 260" width="100%" height="100%">
  <style>
    .circle-c { stroke: #1e3a8a; stroke-width: 1.8; fill: #eff6ff; fill-opacity: 0.55; }
    .ray { stroke: #0f172a; stroke-width: 1.5; fill: none; }
    .orth { stroke: #dc2626; stroke-width: 1.4; stroke-dasharray: 4,3; fill: none; }
    .tangent { stroke: #047857; stroke-width: 1.5; fill: none; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 15px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>
  <circle cx="150" cy="135" r="88" class="circle-c" />
  <text x="82" y="66" class="label math-italic" fill="#1e3a8a">C (|z − a| = R)</text>
  <!-- Ray from a(150,135) through z(205,113) to z*(288,80) -->
  <line x1="150" y1="135" x2="325" y2="65" class="ray" />
  <!-- Tangent segment from z*(288,80) to T(183,53) and perpendicular chord through z -->
  <line x1="150" y1="135" x2="183" y2="53" class="tangent" />
  <line x1="183" y1="53" x2="288" y2="80" class="tangent" />
  <line x1="183" y1="53" x2="205" y2="113" class="orth" />
  <circle cx="150" cy="135" r="3.2" fill="#0f172a" />
  <text x="135" y="152" class="label math-italic">a</text>
  <circle cx="205" cy="113" r="3.5" fill="#dc2626" />
  <text x="204" y="132" class="label math-italic" fill="#dc2626">z</text>
  <circle cx="288" cy="80" r="3.5" fill="#dc2626" />
  <text x="288" y="100" class="label math-italic" fill="#dc2626">z*</text>
  <text x="152" y="92" class="label math-italic" fill="#047857">R</text>
</svg>"""


def generate_fig_3_3() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" width="100%" height="100%">
  <style>
    .c1 { stroke: #1e3a8a; stroke-width: 1.4; fill: none; }
    .c2 { stroke: #dc2626; stroke-width: 1.4; stroke-dasharray: 4,3; fill: none; }
    .axis { stroke: #64748b; stroke-width: 1.1; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 15px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>
  <line x1="30" y1="150" x2="470" y2="150" class="axis" />
  <line x1="250" y1="20" x2="250" y2="280" class="axis" />
  <!-- C1 circles through a(170,150) and b(330,150) -->
  <circle cx="250" cy="150" r="80" class="c1" />
  <circle cx="250" cy="105" r="92" class="c1" />
  <circle cx="250" cy="195" r="92" class="c1" />
  <circle cx="250" cy="60" r="120" class="c1" />
  <circle cx="250" cy="240" r="120" class="c1" />
  <!-- C2 Apollonius circles around a and b -->
  <circle cx="145" cy="150" r="32" class="c2" />
  <circle cx="120" cy="150" r="64" class="c2" />
  <circle cx="355" cy="150" r="32" class="c2" />
  <circle cx="380" cy="150" r="64" class="c2" />
  <circle cx="170" cy="150" r="3.8" fill="#0f172a" />
  <circle cx="330" cy="150" r="3.8" fill="#0f172a" />
  <text x="156" y="168" class="label math-italic">a</text>
  <text x="336" y="168" class="label math-italic">b</text>
  <text x="348" y="54" class="label math-italic" fill="#1e3a8a">C<tspan font-size="11px" dy="3">1</tspan></text>
  <text x="415" y="102" class="label math-italic" fill="#dc2626">C<tspan font-size="11px" dy="3">2</tspan></text>
</svg>"""


def generate_fig_3_9() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 280" width="100%" height="100%">
  <style>
    .axis { stroke: #64748b; stroke-width: 1.2; }
    .slit { stroke: #0f172a; stroke-width: 3; }
    .ellipse { stroke: #1e3a8a; stroke-width: 1.6; fill: none; }
    .hyperbola { stroke: #dc2626; stroke-width: 1.4; stroke-dasharray: 4,3; fill: none; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 15px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>
  <line x1="30" y1="140" x2="470" y2="140" class="axis" />
  <line x1="250" y1="20" x2="250" y2="260" class="axis" />
  <line x1="160" y1="140" x2="340" y2="140" class="slit" />
  <ellipse cx="250" cy="140" rx="115" ry="68" class="ellipse" />
  <ellipse cx="250" cy="140" rx="165" ry="108" class="ellipse" />
  <path d="M 110 35 Q 215 140 110 245" class="hyperbola" />
  <path d="M 390 35 Q 285 140 390 245" class="hyperbola" />
  <path d="M 60 65 Q 192 140 60 215" class="hyperbola" />
  <path d="M 440 65 Q 308 140 440 215" class="hyperbola" />
  <circle cx="160" cy="140" r="3.5" fill="#0f172a" />
  <circle cx="340" cy="140" r="3.5" fill="#0f172a" />
  <text x="145" y="160" class="label">−1</text>
  <text x="336" y="160" class="label">+1</text>
</svg>"""


def generate_fig_7_4() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 290" width="100%" height="100%">
  <style>
    .axis { stroke: #334155; stroke-width: 1.4; }
    .vert { stroke: #1e3a8a; stroke-width: 1.6; fill: none; }
    .semi { stroke: #dc2626; stroke-width: 1.6; fill: none; }
    .shade-left { fill: #dbeafe; fill-opacity: 0.75; }
    .shade-right { fill: #fef3c7; fill-opacity: 0.75; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 15px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>
  <!-- Shaded fundamental region of lambda(tau) -->
  <path d="M 150 25 L 150 240 A 70 70 0 0 1 220 170 L 220 25 Z" class="shade-left" />
  <path d="M 220 25 L 220 170 A 70 70 0 0 1 290 240 L 290 25 Z" class="shade-right" />
  <!-- Real axis -->
  <line x1="40" y1="240" x2="420" y2="240" class="axis" />
  <!-- Vertical lines Re(tau) = -1, 0, 1 -->
  <line x1="150" y1="240" x2="150" y2="20" class="vert" />
  <line x1="220" y1="240" x2="220" y2="20" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,3" />
  <line x1="290" y1="240" x2="290" y2="20" class="vert" />
  <line x1="360" y1="240" x2="360" y2="20" stroke="#94a3b8" stroke-width="1.1" stroke-dasharray="3,3" />
  <!-- Semicircles -->
  <path d="M 150 240 A 70 70 0 0 1 290 240" class="semi" />
  <path d="M 220 240 A 70 70 0 0 1 360 240" stroke="#94a3b8" stroke-width="1.2" fill="none" />
  <path d="M 150 240 A 35 35 0 0 1 220 240" class="semi" />
  <path d="M 220 240 A 35 35 0 0 1 290 240" class="semi" />
  <text x="145" y="260" class="label">−1</text>
  <text x="216" y="260" class="label">0</text>
  <text x="286" y="260" class="label">1</text>
  <text x="356" y="260" class="label">2</text>
  <text x="176" y="105" class="label math-italic" fill="#1e3a8a">Ω</text>
  <text x="246" y="105" class="label math-italic" fill="#b45309">Ω′</text>
</svg>"""


def generate_bonus_fig_2_1() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 280" width="100%" height="100%">
  <style>
    .axis { stroke: #64748b; stroke-width: 1.1; stroke-dasharray: 4,3; }
    .disk { fill: #dbeafe; fill-opacity: 0.55; stroke: #1e3a8a; stroke-width: 1.8; stroke-dasharray: 5,3; }
    .subdisk { fill: #d1fae5; fill-opacity: 0.65; stroke: #047857; stroke-width: 1.5; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 14.5px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>
  <line x1="40" y1="150" x2="420" y2="150" class="axis" />
  <line x1="180" y1="265" x2="180" y2="25" class="axis" />
  <circle cx="230" cy="135" r="96" class="disk" />
  <circle cx="230" cy="135" r="58" class="subdisk" />
  <!-- Center z0 -->
  <circle cx="230" cy="135" r="3.2" fill="#0f172a" />
  <text x="216" y="152" class="label math-italic">z<tspan font-size="10px" dy="3">0</tspan></text>
  <!-- Radius R to singularity zs -->
  <line x1="230" y1="135" x2="305" y2="75" stroke="#dc2626" stroke-width="1.6" />
  <circle cx="305" cy="75" r="4" fill="#dc2626" />
  <text x="313" y="74" class="label math-italic" fill="#dc2626">z<tspan font-size="10px" dy="3">s</tspan> (singularity)</text>
  <text x="262" y="100" class="label math-italic" fill="#dc2626">R</text>
  <!-- Compact subdisk radius r -->
  <line x1="230" y1="135" x2="176" y2="114" stroke="#047857" stroke-width="1.5" />
  <text x="195" y="118" class="label math-italic" fill="#047857">r &lt; R</text>
  <text x="288" y="220" class="label math-italic" fill="#1e3a8a">|z − z<tspan font-size="10px" dy="3">0</tspan><tspan dy="-3">| &lt; R</tspan></text>
</svg>"""


def generate_bonus_fig_4_cauchy() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 265" width="100%" height="100%">
  <defs>
    <marker id="arrow-ccw" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1e3a8a" />
    </marker>
    <marker id="arrow-cw" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#dc2626" />
    </marker>
  </defs>
  <style>
    .region { fill: #eff6ff; fill-opacity: 0.72; stroke: #1e3a8a; stroke-width: 2; }
    .hole { fill: #ffffff; stroke: #dc2626; stroke-width: 1.6; stroke-dasharray: 4,2; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 15px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>
  <path d="M 95 140 C 85 65, 175 30, 265 42 C 365 55, 405 115, 385 175 C 365 230, 255 240, 165 222 C 110 210, 102 180, 95 140 Z" class="region" marker-mid="url(#arrow-ccw)" />
  <circle cx="245" cy="135" r="36" class="hole" />
  <circle cx="245" cy="135" r="3.5" fill="#dc2626" />
  <line x1="245" y1="135" x2="281" y2="135" stroke="#dc2626" stroke-width="1.3" />
  <text x="234" y="152" class="label math-italic" fill="#dc2626">z</text>
  <text x="258" y="128" class="label math-italic" fill="#dc2626">δ</text>
  <text x="135" y="95" class="label math-italic" fill="#1e3a8a">Ω</text>
  <text x="368" y="78" class="label math-italic" fill="#1e3a8a">γ</text>
  <text x="268" y="185" class="label math-italic" fill="#dc2626">C<tspan font-size="10px" dy="3">δ</tspan></text>
</svg>"""


def generate_bonus_fig_5_laurent() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 275" width="100%" height="100%">
  <style>
    .outer { fill: #fef3c7; fill-opacity: 0.65; stroke: #b45309; stroke-width: 1.8; stroke-dasharray: 5,3; }
    .inner { fill: #ffffff; stroke: #1e3a8a; stroke-width: 1.8; stroke-dasharray: 5,3; }
    .path-c { fill: none; stroke: #047857; stroke-width: 2; }
    .label { font-family: "New Computer Modern", "Latin Modern Roman", serif; font-size: 14.5px; fill: #0f172a; }
    .math-italic { font-style: italic; }
  </style>
  <circle cx="230" cy="138" r="105" class="outer" />
  <circle cx="230" cy="138" r="74" class="path-c" />
  <circle cx="230" cy="138" r="42" class="inner" />
  <circle cx="230" cy="138" r="3.2" fill="#0f172a" />
  <text x="220" y="154" class="label math-italic">a</text>
  <line x1="230" y1="138" x2="272" y2="138" stroke="#1e3a8a" stroke-width="1.3" />
  <text x="246" y="132" class="label math-italic" fill="#1e3a8a">r<tspan font-size="10px" dy="3">1</tspan></text>
  <line x1="230" y1="138" x2="156" y2="64" stroke="#b45309" stroke-width="1.3" />
  <text x="176" y="108" class="label math-italic" fill="#b45309">r<tspan font-size="10px" dy="3">2</tspan></text>
  <circle cx="282" cy="96" r="3.5" fill="#dc2626" />
  <text x="290" y="98" class="label math-italic" fill="#dc2626">z</text>
  <text x="285" y="185" class="label math-italic" fill="#047857">C</text>
</svg>"""


def generate_all_ahlfors_figures(out_dir: Path) -> None:
    """Generate and write all Ahlfors figures to out_dir."""
    import shutil

    from polytypst.ahlfors.figures_extra import EXTRA_SVG_GENERATORS

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_fig_dir = out_dir.parent / "figures_raw"
    if not raw_fig_dir.exists():
        raw_fig_dir.mkdir(parents=True, exist_ok=True)
        for png_path in sorted(out_dir.glob("fig_*.png")):
            shutil.copy2(png_path, raw_fig_dir / png_path.name)

    for stale in (
        "fig_1_1.png",
        "fig_1_1_vector_addition.png",
        "fig_1_2.png",
        "fig_1_2_vector_multiplication.png",
        "fig_1_3.png",
        "fig_7_0.png",
    ):
        stale_path = out_dir / stale
        if stale_path.exists():
            stale_path.unlink()

    core_generators = {
        "fig_1_1_vector_addition.svg": generate_fig_1_1,
        "fig_1_2_vector_multiplication.svg": generate_fig_1_2,
        "fig_1_3_stereographic_projection.svg": generate_fig_1_3,
        "fig_3_1.svg": generate_fig_3_1,
        "fig_3_2.svg": generate_fig_3_2,
        "fig_3_3.svg": generate_fig_3_3,
        "fig_3_9.svg": generate_fig_3_9,
        **EXTRA_SVG_GENERATORS,
    }
    for name, fn in core_generators.items():
        (out_dir / name).write_text(fn(), encoding="utf-8")


def generate_colorful_ahlfors_figures(src_fig_dir: Path, color_fig_dir: Path) -> None:
    import shutil

    from polytypst.ahlfors.figures_extra import (
        BONUS_SVG_GENERATORS,
        EXTRA_SVG_GENERATORS,
        export_web_figures_gallery,
    )

    src_fig_dir = Path(src_fig_dir)
    color_fig_dir = Path(color_fig_dir)
    color_fig_dir.mkdir(parents=True, exist_ok=True)
    raw_fig_dir = src_fig_dir.parent / "figures_raw"
    if not raw_fig_dir.exists():
        raw_fig_dir.mkdir(parents=True, exist_ok=True)
        for png_path in sorted(src_fig_dir.glob("fig_*.png")):
            shutil.copy2(png_path, raw_fig_dir / png_path.name)

    generate_all_ahlfors_figures(src_fig_dir)

    svg_generators = {
        **EXTRA_SVG_GENERATORS,
        **BONUS_SVG_GENERATORS,
    }
    for name, fn in svg_generators.items():
        (color_fig_dir / name).write_text(fn(), encoding="utf-8")

    export_web_figures_gallery(src_fig_dir.parent / "web_figures")
