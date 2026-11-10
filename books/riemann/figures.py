"""Vector redraws of Klein's figures, black ink on white, labels in the book's own type.

Stream-line figures are computed from the complex potential the text names, not traced from the scan."""

from __future__ import annotations

import cmath
import itertools
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import contourpy
import numpy as np

INK = "#000000"
FONT = "'New Computer Modern', 'New Computer Modern Math', serif"
HEAVY = 2.8
LIGHT = 1.6
FINE = 1.3
LABEL_PX = 32
DASH_ON, DASH_OFF = 5.0, 4.5

Point = tuple[float, float]


@dataclass(frozen=True)
class Frame:
    """Maps the complex plane onto SVG pixels: `scale` px per unit, turned `turn` radians about `origin`."""

    origin: Point
    scale: float = 1.0
    turn: float = 0.0

    def svg(self, z: complex) -> Point:
        w = z * cmath.exp(1j * self.turn) * self.scale
        return self.origin[0] + w.real, self.origin[1] - w.imag

    def angle(self, d: complex) -> float:
        w = d * cmath.exp(1j * self.turn)
        return math.degrees(math.atan2(-w.imag, w.real))


def _d(points: Sequence[Point]) -> str:
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)


def _dashed_d(
    points: Sequence[Point], gap_from: Point | None = None, gap: float = 0.0
) -> str:
    dense: list[Point] = [points[0]]
    for (x0, y0), (x1, y1) in itertools.pairwise(points):
        n = max(1, math.ceil(math.hypot(x1 - x0, y1 - y0) / 0.5))
        dense.extend(
            (x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(1, n + 1)
        )
    dashes: list[list[Point]] = []
    run = 0.0
    for a, b in itertools.pairwise(dense):
        far = (
            gap_from is None or math.hypot(a[0] - gap_from[0], a[1] - gap_from[1]) > gap
        )
        if run % (DASH_ON + DASH_OFF) < DASH_ON and far:
            if dashes and dashes[-1][-1] == a:
                dashes[-1].append(b)
            else:
                dashes.append([a, b])
        run += math.hypot(b[0] - a[0], b[1] - a[1])
    return " ".join(_d(d) for d in dashes)


def _arrowhead(at: Point, angle: float) -> str:
    return (
        f'<path d="M9,0 L-6.5,-5.5 L-3,0 L-6.5,5.5 Z" fill="{INK}" '
        f'transform="translate({at[0]:.2f},{at[1]:.2f}) rotate({angle:.2f})"/>'
    )


def _stroke(paths: Sequence[str], width: float) -> str:
    body = "".join(f'<path d="{d}"/>' for d in paths if d)
    return f'<g fill="none" stroke="{INK}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{body}</g>'


def _label(text: str, at: Point, anchor: str = "middle") -> str:
    return (
        f'<text x="{at[0]:.1f}" y="{at[1]:.1f}" font-family="{FONT}" font-style="italic" '
        f'font-size="{LABEL_PX}" text-anchor="{anchor}" fill="{INK}">{text}</text>'
    )


def _svg(width: float, height: float, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}" height="{height:g}" '
        f'viewBox="0 0 {width:g} {height:g}">{body}</svg>'
    )


def _cubic(p0: Point, c1: Point, c2: Point, p1: Point, steps: int = 96) -> list[Point]:
    out: list[Point] = []
    for k in range(steps + 1):
        t = k / steps
        u = 1 - t
        out.append(
            (
                u**3 * p0[0]
                + 3 * u * u * t * c1[0]
                + 3 * u * t * t * c2[0]
                + t**3 * p1[0],
                u**3 * p0[1]
                + 3 * u * u * t * c1[1]
                + 3 * u * t * t * c2[1]
                + t**3 * p1[1],
            )
        )
    return out


def _midpoint(points: Sequence[complex]) -> tuple[complex, complex]:
    """The point halfway along a polyline, and the chord direction there."""
    lengths = [abs(b - a) for a, b in itertools.pairwise(points)]
    half = sum(lengths) / 2
    for (a, b), step in zip(itertools.pairwise(points), lengths, strict=True):
        if half <= step:
            return a + (b - a) * (half / step if step else 0), b - a
        half -= step
    return points[-1], points[-1] - points[-2]


def _inside_pieces(
    points: Sequence[complex], inside: Callable[[complex], bool]
) -> list[list[complex]]:
    pieces: list[list[complex]] = []
    current: list[complex] = []
    for z in points:
        if inside(z):
            current.append(z)
        elif current:
            pieces.append(current)
            current = []
    if current:
        pieces.append(current)
    return [p for p in pieces if len(p) > 1]


def _circle_through_zero(
    center: complex, inside: Callable[[complex], bool], steps: int = 720
) -> list[list[complex]]:
    """The circle through 0 centred at `center`, from 0 round to 0, cut to the region `inside`."""
    r = abs(center)
    start = cmath.phase(-center)
    points = [
        center + r * cmath.exp(1j * (start + 2 * math.pi * k / steps))
        for k in range(steps + 1)
    ]
    return _inside_pieces(points, inside)


def fig_4() -> str:
    """A simple algebraic infinity, w = A/(z - z0). Both families are circles through the pole:
    stream-lines (heavy) tangent to the axis, equipotential curves (dotted) tangent to its normal."""
    radius = 200.0
    # The scan draws the pole's axis rising about 35 degrees to the right.
    frame = Frame(origin=(220.0, 220.0), turn=math.radians(35))

    def inside(z: complex) -> bool:
        return abs(z) <= radius

    def velocity(z: complex) -> complex:
        return (-1 / z**2).conjugate()

    pole = frame.svg(0)
    dotted: list[str] = []
    for share in (10.0, 4.0, 2.0, 1.2, 0.8, 0.12):
        for side in (1, -1):
            for piece in _circle_through_zero(side * share * radius + 0j, inside):
                dotted.append(
                    _dashed_d([frame.svg(z) for z in piece], pole, 0.06 * radius)
                )
    dotted.append(
        _dashed_d(
            [frame.svg(1j * radius), frame.svg(-1j * radius)], pole, 0.06 * radius
        )
    )

    heavy: list[str] = []
    heads: list[str] = []
    for share in (6.0, 2.5, 1.3, 0.8, 0.17):
        for side in (1, -1):
            for piece in _circle_through_zero(side * share * radius * 1j, inside):
                heavy.append(_d([frame.svg(z) for z in piece]))
                n = len(piece)
                if abs(piece[0]) < 1e-6 and abs(piece[-1]) < 1e-6:
                    z = piece[n // 2]
                else:
                    z = (
                        piece[int(0.85 * n)]
                        if abs(piece[0]) < abs(piece[-1])
                        else piece[int(0.15 * n)]
                    )
                heads.append(_arrowhead(frame.svg(z), frame.angle(velocity(z))))
    heavy.append(_d([frame.svg(-radius + 0j), frame.svg(radius + 0j)]))
    heads.extend(
        _arrowhead(frame.svg(x), frame.angle(velocity(x)))
        for x in (0.88 * radius + 0j, -0.88 * radius + 0j)
    )

    dot = f'<circle cx="{pole[0]:.2f}" cy="{pole[1]:.2f}" r="2.4" fill="{INK}"/>'
    return _svg(
        440, 440, _stroke(dotted, LIGHT) + _stroke(heavy, HEAVY) + "".join(heads) + dot
    )


def fig_10() -> str:
    """Two simple algebraic infinities about to coalesce, w = 1/(z + a) - 1/(z - a), with the cross-point
    between them at 0. Each stream-line Im(1/(z^2 - a^2)) = k is the preimage under z -> z^2 - a^2 of a
    circle through 0, so it runs from pole to pole."""
    a = 1.0
    half_w, half_h = 2.2, 1.15
    frame = Frame(origin=(450.0, 240.0), scale=200.0)

    def inside(z: complex) -> bool:
        return (z.real / half_w) ** 2 + (z.imag / half_h) ** 2 <= 1

    def velocity(z: complex) -> complex:
        return (1 / (z - a) ** 2 - 1 / (z + a) ** 2).conjugate()

    lines: list[list[complex]] = []
    for k in (0.12, 0.3, 0.55, 0.95, 1.7, 3.6):
        for sign in (1, -1):
            center = -1j / (2 * sign * k)
            r = abs(center)
            start = cmath.phase(-center)
            branch: list[complex] = []
            previous = complex(a, 0)
            for step in range(1, 1440):
                w = center + r * cmath.exp(1j * (start + 2 * math.pi * step / 1440))
                z = cmath.sqrt(w + a * a)
                z = z if abs(z - previous) <= abs(z + previous) else -z
                branch.append(z)
                previous = z
            last_pole = a if abs(branch[-1] - a) < abs(branch[-1] + a) else -a
            branch = [complex(a, 0), *branch, complex(last_pole, 0)]
            lines.append(branch)
            lines.append([-z for z in branch])

    for ends in ((-half_w, -a), (-a, 0), (0, a), (a, half_w)):
        lines.append(
            [complex(ends[0] + (ends[1] - ends[0]) * t / 40, 0) for t in range(41)]
        )
    for top in (half_h, -half_h):
        lines.append([complex(0, top * t / 40) for t in range(41)])

    heavy: list[str] = []
    heads: list[str] = []
    for line in lines:
        for piece in _inside_pieces(line, inside):
            heavy.append(_d([frame.svg(z) for z in piece]))
            length = sum(abs(q - p) for p, q in itertools.pairwise(piece))
            if length > 0.18:
                mid, _ = _midpoint(piece)
                heads.append(_arrowhead(frame.svg(mid), frame.angle(velocity(mid))))
    return _svg(900, 480, _stroke(heavy, HEAVY) + "".join(heads))


def fig_11() -> str:
    """A lens of film I in the region II, as the scan draws it."""
    scale = 0.5

    def p(x: float, y: float) -> Point:
        return (x - 80) * scale, (y - 330) * scale

    tip, end = p(105, 495), p(965, 895)
    upper = _cubic(tip, p(300, 330), p(1000, 420), end)
    lower = _cubic(tip, p(250, 700), p(700, 910), end)
    labels = (
        _label("I", p(550, 600)) + _label("II", p(890, 500)) + _label("II", p(290, 790))
    )
    return _svg(470, 300, _stroke([_d(upper), _d(lower)], FINE) + labels)


def fig_12() -> str:
    """Two films I and II meeting along a common edge, in the region III, as the scan draws it."""
    scale = 0.5

    def p(x: float, y: float) -> Point:
        return (x - 960) * scale, (y - 170) * scale

    tip, end = p(985, 405), p(1965, 1070)
    outer = _cubic(tip, p(1100, 180), p(2200, 150), end)
    middle = _cubic(tip, p(1350, 370), p(1850, 700), end)
    lower = _cubic(tip, p(1080, 750), p(1450, 1090), end)
    labels = (
        _label("I", p(1710, 420))
        + _label("II", p(1420, 700))
        + _label("III", p(1150, 870))
    )
    return _svg(560, 470, _stroke([_d(outer), _d(middle), _d(lower)], FINE) + labels)


def fig_34() -> str:
    """A meridian section of the anchor-ring: axis of rotation Z through O, tube centre at distance R,
    tube radius rho, and the angle alpha a point of the section makes with the line to O."""
    axis_x, o_y = 60.0, 200.0
    center = (330.0, o_y)
    rho = 85.0
    alpha = math.radians(45)
    tip = (center[0] - rho * math.cos(alpha), center[1] - rho * math.sin(alpha))
    sag = _cubic(
        (axis_x, o_y), (150, o_y + 42), (250, o_y + 42), (center[0] - 8, o_y + 6), 48
    )
    lines = [
        _d([(axis_x, 30.0), (axis_x, 330.0)]),
        _d([(axis_x, o_y), center]),
        _d([center, tip]),
    ]
    ring = f'<circle cx="{center[0]:g}" cy="{center[1]:g}" r="{rho:g}" fill="none" stroke="{INK}" stroke-width="{FINE}"/>'
    labels = (
        _label("Z", (axis_x - 10, 40), "end")
        + _label("O", (axis_x - 12, o_y + 11), "end")
        + _label("R", (190, o_y + 70))
        + _label("ρ", (tip[0] + 38, tip[1] + 16))
        + _label("α", (center[0] - 48, o_y - 10))
    )
    return _svg(
        440, 340, _stroke(lines, FINE) + _stroke([_d(sag)], FINE) + ring + labels
    )


Grid = np.ndarray
Velocity = Callable[[complex], complex]


def _grid(x0: float, x1: float, y0: float, y1: float, n: int = 1000) -> Grid:
    # An even count keeps grid nodes off the axes, where many of these fields vanish exactly.
    xs = np.linspace(x0, x1, n)
    ys = np.linspace(y0, y1, 2 * round(n * (y1 - y0) / (x1 - x0) / 2))
    x, y = np.meshgrid(xs, ys)
    return x + 1j * y


def _level_lines(
    z: Grid, values: np.ndarray, hidden: np.ndarray, level: float
) -> list[list[complex]]:
    hidden = hidden | ~np.isfinite(values)
    data = np.ma.array(np.where(hidden, 0.0, values), mask=hidden)
    gen = contourpy.contour_generator(
        z.real, z.imag, data, line_type=contourpy.LineType.Separate
    )
    return [
        [complex(x, y) for x, y in line] for line in gen.lines(level) if len(line) > 2
    ]


def _levels_of(
    z: Grid, values: np.ndarray, hidden: np.ndarray, levels: Sequence[float]
) -> list[list[complex]]:
    return [line for level in levels for line in _level_lines(z, values, hidden, level)]


def _arg_lines(
    z: Grid, g: np.ndarray, hidden: np.ndarray, angles: Sequence[float]
) -> list[list[complex]]:
    """The curves arg g = c. Contouring Im(g e^-ic) = 0 where Re(g e^-ic) > 0 avoids the jump of arg."""
    lines: list[list[complex]] = []
    for c in angles:
        turned = g * cmath.exp(-1j * c)
        lines.extend(_level_lines(z, turned.imag, hidden | (turned.real <= 0), 0.0))
    return lines


def _segment(a: complex, b: complex, steps: int = 40) -> list[complex]:
    return [a + (b - a) * k / steps for k in range(steps + 1)]


def _length(points: Sequence[complex]) -> float:
    return sum(abs(b - a) for a, b in itertools.pairwise(points))


def _along(points: Sequence[complex], share: float) -> complex:
    left = _length(points) * share
    for a, b in itertools.pairwise(points):
        step = abs(b - a)
        if left <= step:
            return a + (b - a) * (left / step if step else 0)
        left -= step
    return points[-1]


def _thin(points: Sequence[Point], tol: float = 0.6) -> list[Point]:
    kept = [points[0]]
    for p in points[1:-1]:
        if math.hypot(p[0] - kept[-1][0], p[1] - kept[-1][1]) >= tol:
            kept.append(p)
    kept.append(points[-1])
    return kept


def _flow_svg(
    frame: Frame,
    size: Point,
    velocity: Velocity,
    heavy: Sequence[Sequence[complex]],
    dotted: Sequence[Sequence[complex]] = (),
    poles: Sequence[complex] = (),
    shortest: float = 0.12,
    long: float = 1.1,
) -> str:
    """Stream-lines as heavy lines with an arrow in the direction of flow, equipotential curves dotted."""
    paths: list[str] = []
    heads: list[str] = []
    for line in heavy:
        paths.append(_d(_thin([frame.svg(z) for z in line])))
        length = _length(line)
        if length < shortest:
            continue
        for share in (0.5,) if length < long else (0.3, 0.7):
            at = _along(line, share)
            v = velocity(at)
            if v and cmath.isfinite(v):
                heads.append(_arrowhead(frame.svg(at), frame.angle(v)))
    dashes = [_dashed_d(_thin([frame.svg(z) for z in line])) for line in dotted]
    marks = "".join(
        f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.2" fill="{INK}"/>'
        for x, y in map(frame.svg, poles)
    )
    return _svg(
        size[0],
        size[1],
        _stroke(dashes, LIGHT) + _stroke(paths, HEAVY) + "".join(heads) + marks,
    )


def _vertex_levels(radii: Sequence[float]) -> list[float]:
    """Levels of Im(-i z^3) whose curves come nearest the cross-point at these radii."""
    return [s * r**3 for r in radii for s in (1, -1)]


CROSS_RADII = (0.5, 0.75, 0.95)


def _cross_point(dotted: bool) -> str:
    """A cross-point of multiplicity two, w = -i z^3: three stream-lines flow in and three flow out."""
    z = _grid(-1, 1, -1, 1)
    hidden = np.abs(z) > 1
    f = -1j * z**3
    heavy = _levels_of(z, f.imag, hidden, _vertex_levels(CROSS_RADII))
    heavy += [_segment(0, cmath.exp(1j * math.radians(30 + 60 * k))) for k in range(6)]
    dots: list[list[complex]] = []
    if dotted:
        dots = _levels_of(z, f.real, hidden, _vertex_levels(CROSS_RADII))
        dots += [_segment(0, cmath.exp(1j * math.radians(60 * k))) for k in range(6)]
    frame = Frame(origin=(220.0, 220.0), scale=200.0)
    return _flow_svg(
        frame,
        (440, 440),
        lambda p: (-3j * p * p).conjugate(),
        heavy,
        dots,
        long=math.inf,
    )


def fig_1() -> str:
    return _cross_point(dotted=True)


def fig_2() -> str:
    return _cross_point(dotted=False)


def fig_3() -> str:
    """Two simple cross-points close together, w = -i(z^3 - 3 e^2 z): Fig. 2 pulled apart."""
    eps = 0.39 * cmath.exp(1j * 3 * math.pi / 4)
    z = _grid(-1, 1, -1, 1)
    hidden = np.abs(z) > 1
    f = -1j * (z**3 - 3 * eps**2 * z)
    saddle = (-1j * (eps**3 - 3 * eps**2 * eps)).imag
    heavy = _levels_of(
        z, f.imag, hidden, [0.0, saddle, -saddle, *_vertex_levels(CROSS_RADII[1:])]
    )
    frame = Frame(origin=(220.0, 220.0), scale=200.0)
    return _flow_svg(
        frame,
        (440, 440),
        lambda p: (-3j * (p * p - eps**2)).conjugate(),
        heavy,
        long=math.inf,
    )


def fig_5() -> str:
    """A two-fold algebraic infinity, w = -1/z^2: every curve passes twice through the pole."""
    z = _grid(-1, 1, -1, 1)
    hidden = (np.abs(z) > 1) | (np.abs(z) < 0.01)
    f = -1 / z**2
    levels = [s * c for c in (0.6, 1.6, 4.5) for s in (1, -1)]
    heavy = _levels_of(z, f.imag, hidden, levels)
    heavy += [
        _segment(
            0.012 * cmath.exp(1j * math.pi * k / 2), cmath.exp(1j * math.pi * k / 2)
        )
        for k in range(4)
    ]
    dots = _levels_of(z, f.real, hidden, levels)
    dots += [
        _segment(
            0.012 * cmath.exp(1j * math.pi * (k / 2 + 0.25)),
            cmath.exp(1j * math.pi * (k / 2 + 0.25)),
        )
        for k in range(4)
    ]
    frame = Frame(origin=(220.0, 220.0), scale=200.0)
    return _flow_svg(
        frame, (440, 440), lambda p: (2 / p**3).conjugate(), heavy, dots, poles=(0,)
    )


# Figs. 6 and 7 draw the pair the way the scan does, on an axis rising about 37 degrees to the right.
PAIR_TURN = math.radians(37)
PAIR_HALF = 0.55


def fig_6() -> str:
    """A source and a sink about to coalesce into Fig. 4, w = log(z - a) - log(z + a): the stream-lines
    are the circles through both points."""
    a = PAIR_HALF
    z = _grid(-1, 1, -1, 1)
    hidden = np.abs(z) > 1
    heavy = _arg_lines(
        z, (z - a) / (z + a), hidden, [math.pi * k / 6 for k in range(1, 12) if k != 6]
    )
    heavy += [_segment(-a, a), _segment(a + 0.01, 1), _segment(-1, -a - 0.01)]
    frame = Frame(origin=(220.0, 220.0), scale=200.0, turn=PAIR_TURN)
    return _flow_svg(
        frame,
        (440, 440),
        lambda p: (1 / (p - a) - 1 / (p + a)).conjugate(),
        heavy,
        poles=(a, -a),
    )


def fig_7() -> str:
    """Two vortex-points about to coalesce into Fig. 4, w = i(log(z - a) - log(z + a)): the stream-lines
    are the circles of Apollonius about the two points."""
    a = PAIR_HALF
    z = _grid(-1, 1, -1, 1)
    hidden = (np.abs(z) > 1) | (np.abs(z - a) < 0.01) | (np.abs(z + a) < 0.01)
    levels = [0.0, *(s * c for c in (0.45, 1.0, 1.8, 2.8) for s in (1, -1))]
    heavy = _levels_of(z, np.log(np.abs((z - a) / (z + a))), hidden, levels)
    frame = Frame(origin=(220.0, 220.0), scale=200.0, turn=PAIR_TURN)
    return _flow_svg(
        frame,
        (440, 440),
        lambda p: (1j * (1 / (p - a) - 1 / (p + a))).conjugate(),
        heavy,
        poles=(a, -a),
    )


TRIPLE = 0.46


def fig_8() -> str:
    """Two sources and a sink of twice their strength coalescing into Fig. 5, w = log(1 - a^2/z^2)."""
    a = TRIPLE
    z = _grid(-1, 1, -1, 1)
    hidden = (
        (np.abs(z) > 1)
        | (np.abs(z) < 0.01)
        | (np.abs(np.abs(z.real) - a) + np.abs(z.imag) < 0.01)
    )
    heavy = _arg_lines(
        z,
        1 - a * a / z**2,
        hidden,
        [s * math.radians(c) for c in (10, 25, 45, 75, 110, 150) for s in (1, -1)],
    )
    heavy += [
        _segment(-1, -a - 0.01),
        _segment(-a + 0.01, -0.01),
        _segment(0.01, a - 0.01),
        _segment(a + 0.01, 1),
    ]
    heavy += [_segment(0.01j, 1j), _segment(-1j, -0.01j)]

    def velocity(p: complex) -> complex:
        return ((2 * a * a / p**3) / (1 - a * a / p**2)).conjugate()

    frame = Frame(origin=(220.0, 220.0), scale=200.0)
    return _flow_svg(frame, (440, 440), velocity, heavy, poles=(a, 0, -a))


def fig_9() -> str:
    """Two vortex-points and one of twice their opposite intensity coalescing into Fig. 5,
    w = -i log(1 - b^2/z^2), with b on the diagonal so the far field matches Fig. 5."""
    b = TRIPLE * cmath.exp(1j * 3 * math.pi / 4)
    z = _grid(-1, 1, -1, 1)
    hidden = (
        (np.abs(z) > 1)
        | (np.abs(z) < 0.01)
        | (np.abs(z - b) < 0.01)
        | (np.abs(z + b) < 0.01)
    )
    levels = [s * c for c in (0.12, 0.45, 1.0, 1.9) for s in (1, -1)]
    heavy = _levels_of(z, np.log(np.abs(1 - b * b / z**2)), hidden, levels)

    def velocity(p: complex) -> complex:
        return (-1j * (2 * b * b / p**3) / (1 - b * b / p**2)).conjugate()

    frame = Frame(origin=(220.0, 220.0), scale=200.0)
    return _flow_svg(frame, (440, 440), velocity, heavy, poles=(b, 0, -b))


def _icosahedral(z: np.ndarray | complex) -> np.ndarray | complex:
    z5 = z**5
    num = -(z5**4 + 1) + 228 * (z5**3 - z5) - 494 * z5**2
    return num**3 / (1728 * z5 * (z5**2 + 11 * z5 - 1) ** 5)


def _sphere(z: complex) -> np.ndarray:
    """Inverse stereographic projection from the north pole; z = 0 is the south pole."""
    r2 = abs(z) ** 2
    return np.array([2 * z.real, 2 * z.imag, r2 - 1]) / (r2 + 1)


def fig_13() -> str:
    """One of the 20 triangles of the icosahedron on the sphere, with the stream-lines Im w = const of
    Klein's icosahedral function. The triangle is drawn in gnomonic projection, which keeps its great-circle
    edges and medians straight; there w is real, so they are stream-lines too."""
    golden = 2 * math.cos(2 * math.pi / 5)
    corners = [
        _sphere(0j),
        _sphere(golden + 0j),
        _sphere(golden * cmath.exp(2j * math.pi / 5)),
    ]
    center = sum(corners) / np.linalg.norm(sum(corners))
    up = corners[0] - corners[0].dot(center) * center
    up /= np.linalg.norm(up)
    right = np.cross(up, center)

    def plane(p: np.ndarray) -> complex:
        q = p / p.dot(center)
        return complex(q.dot(right), q.dot(up))

    def stereo(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        p = center[:, None, None] + x * right[:, None, None] + y * up[:, None, None]
        p = p / np.linalg.norm(p, axis=0)
        return (p[0] + 1j * p[1]) / (1 - p[2])

    def to_z(at: complex) -> complex:
        return complex(stereo(np.array([[at.real]]), np.array([[at.imag]]))[0, 0])

    tips = [plane(c) for c in corners]
    mids = [plane((corners[i] + corners[(i + 1) % 3]) / 2) for i in range(3)]
    grid = _grid(
        min(t.real for t in tips),
        max(t.real for t in tips),
        min(t.imag for t in tips),
        max(t.imag for t in tips),
        1200,
    )
    zs = stereo(grid.real, grid.imag)
    with np.errstate(all="ignore"):
        values = np.imag(_icosahedral(zs))

    def outside(p: np.ndarray) -> np.ndarray:
        a, b, c = tips
        side = [
            ((q - p0).conjugate() * (p - p0)).imag for p0, q in ((a, b), (b, c), (c, a))
        ]
        return ~(
            ((side[0] >= 0) & (side[1] >= 0) & (side[2] >= 0))
            | ((side[0] <= 0) & (side[1] <= 0) & (side[2] <= 0))
        )

    hidden = outside(grid) | np.any([np.abs(grid - t) < 0.012 for t in tips], axis=0)
    heavy = _levels_of(
        grid, values, hidden, [s * c for c in (0.3, 1.2) for s in (1, -1)]
    )
    for tip, mid in itertools.product(tips, mids):
        if abs(tip - mid) < abs(tips[0] - tips[1]) * 0.6:
            heavy.append(_segment(tip, mid))
    heavy += [_segment(0, p) for p in (*tips, *mids)]

    def velocity(at: complex) -> complex:
        zc = to_z(at)
        h = 1e-6 * max(1.0, abs(zc))
        slope = (_icosahedral(zc + h) - _icosahedral(zc - h)) / (2 * h)
        step = slope.conjugate() / abs(slope) * 1e-5 * max(1.0, abs(zc))
        return plane(_sphere(zc + step)) - at

    side = abs(tips[1] - tips[2])
    frame = Frame(origin=(240.0, 40.0 + 230.0), scale=230.0 / abs(tips[0]))
    return _flow_svg(
        frame, (480, 410), velocity, heavy, shortest=0.06 * side, long=0.9 * side
    )


FIGURES: dict[str, Callable[[], str]] = {
    "1": fig_1,
    "2": fig_2,
    "3": fig_3,
    "4": fig_4,
    "5": fig_5,
    "6": fig_6,
    "7": fig_7,
    "8": fig_8,
    "9": fig_9,
    "13": fig_13,
    "10": fig_10,
    "11": fig_11,
    "12": fig_12,
    "34": fig_34,
}


def all_figures() -> dict[str, Callable[[], str]]:
    """This module's figures and those of its sibling modules, which import their helpers from here."""
    from . import figures_flows_a, figures_flows_b, figures_maps, figures_surfaces

    found = dict(FIGURES)
    for part in (figures_surfaces, figures_flows_a, figures_flows_b, figures_maps):
        if twice := sorted(set(found) & set(part.FIGURES)):
            raise ValueError(f"{part.__name__} redefines figures {twice}")
        found.update(part.FIGURES)
    return found


def draw_figures(out_dir: Path) -> list[Path]:
    """Write each redrawn figure beside the scan crops; the build prints an SVG in place of its PNG."""
    folder = out_dir / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for fid, draw in all_figures().items():
        path = folder / f"fig_{fid}.svg"
        path.write_text(draw(), encoding="utf-8")
        written.append(path)
    return written
