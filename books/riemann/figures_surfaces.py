from __future__ import annotations

import cmath
import itertools
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .figures import (
    LIGHT,
    Point,
    _arrowhead,
    _cubic,
    _d,
    _dashed_d,
    _label,
    _stroke,
    _svg,
)

SCAN_TO_SVG = 0.75
PAD = 6.0

Curve = list[complex]


def _arc(c: complex, r: float, a0: float, a1: float) -> Curve:
    n = max(8, math.ceil(abs(a1 - a0) / 1.5))
    return [
        c + r * cmath.exp(1j * math.radians(a0 + (a1 - a0) * k / n))
        for k in range(n + 1)
    ]


def _ellipse(
    c: complex, a: float, b: float, axis: float, t0: float, t1: float
) -> Curve:
    turn = cmath.exp(1j * math.radians(axis))
    n = max(8, math.ceil(abs(t1 - t0) / 3))
    out: Curve = []
    for k in range(n + 1):
        t = math.radians(t0 + (t1 - t0) * k / n)
        out.append(c + turn * complex(a * math.cos(t), b * math.sin(t)))
    return out


def _bezier(p0: complex, c1: complex, c2: complex, p1: complex) -> Curve:
    pts = _cubic(
        (p0.real, p0.imag),
        (c1.real, c1.imag),
        (c2.real, c2.imag),
        (p1.real, p1.imag),
        48,
    )
    return [complex(x, y) for x, y in pts]


def _dee(c: complex, rx: float, ry: float, depth: float, corner: float) -> Curve:
    k = 0.55 * corner
    right, left = c + rx + (depth - corner) * 1j, c - rx + (depth - corner) * 1j
    foot_r, foot_l = c + rx - corner + depth * 1j, c - rx + corner + depth * 1j
    return [
        *_ellipse(c, rx, ry, 0, 180, 360),
        *_bezier(right, right + k * 1j, foot_r + k, foot_r),
        *_bezier(foot_l, foot_l - k, left + k * 1j, left),
        c - rx,
    ]


def _heading(
    curve: Curve, share: float, backward: bool = False
) -> tuple[complex, complex]:
    i = min(len(curve) - 2, int(share * (len(curve) - 1)))
    d = curve[i + 1] - curve[i]
    return curve[i], -d if backward else d


def _figure(
    solid: Sequence[Curve],
    dashed: Sequence[Curve] = (),
    labels: Sequence[tuple[str, complex]] = (),
    arrows: Sequence[tuple[complex, complex]] = (),
) -> str:
    zs = [z for c in [*solid, *dashed] for z in c]
    margin = PAD / SCAN_TO_SVG * (1 + 1j)
    lo = complex(min(z.real for z in zs), min(z.imag for z in zs)) - margin
    hi = complex(max(z.real for z in zs), max(z.imag for z in zs)) + margin

    def at(z: complex) -> Point:
        w = (z - lo) * SCAN_TO_SVG
        return w.real, w.imag

    body = _stroke([_d([at(z) for z in c]) for c in solid], LIGHT)
    body += _stroke([_dashed_d([at(z) for z in c]) for c in dashed], LIGHT)
    body += "".join(_arrowhead(at(z), math.degrees(cmath.phase(d))) for z, d in arrows)
    body += "".join(_label(text, at(z)) for text, z in labels)
    size = (hi - lo) * SCAN_TO_SVG
    return _svg(round(size.real), round(size.imag), body)


def fig_14() -> str:
    centre, body, base = 360 + 355j, 250.0, -270j

    def handle(turn: float) -> tuple[Curve, Curve]:
        rot = cmath.exp(1j * math.radians(turn))
        b1, b2 = (body * cmath.exp(1j * math.radians(a)) for a in (-122, -58))
        s1, s2 = base - 85, base + 85
        outline = [
            *_arc(0, body, -150, -122),
            *_bezier(b1, b1 + 32j * b1 / body, s1 + 30j, s1),
            *_ellipse(base, 85, 77, 0, 180, 360),
            *_bezier(s2, s2 + 30j, b2 - 32j * b2 / body, b2),
            *_arc(0, body, -58, -30),
        ]
        hole = _dee(base, 63, 58, 13, 13)
        return [centre + z * rot for z in outline], [centre + z * rot for z in hole]

    parts = [handle(turn) for turn in (0, 120, 240)]
    outline = [z for o, _ in parts for z in o]
    return _figure([[*outline, outline[0]], *(h for _, h in parts)])


def fig_15() -> str:
    c = 400 + 315j
    axis = 137.0
    mid = c + 222.5 * cmath.exp(1j * math.radians(axis))
    circles = [_arc(c, r, 0, 360) for r in (300, 225, 145)]
    return _figure(
        [*circles, _ellipse(mid, 77.5, 18, axis, 180, 360)],
        [_ellipse(mid, 77.5, 18, axis, 0, 180)],
        labels=[("A", 288 + 476j), ("B", 627 + 286j)],
    )


def fig_16() -> str:
    body, body_r = 560 + 977j, 724.0
    tube, tube_r = 583 + 220j, 205.0
    hub = 587 + 170j
    b1, b2 = (body + body_r * cmath.exp(1j * math.radians(a)) for a in (-108.5, -64.6))
    s1, s2 = tube - tube_r, tube + tube_r
    outline = [
        *_arc(body, body_r, -131, -108.5),
        *_bezier(b1, b1 + 34j * (b1 - body) / body_r, s1 + 40j, s1),
        *_arc(tube, tube_r, 180, 360),
        *_bezier(s2, s2 + 40j, b2 - 34j * (b2 - body) / body_r, b2),
        *_arc(body, body_r, -64.6, -50.6),
    ]
    top = tube + tube_r * cmath.exp(1j * math.radians(-103))
    foot = complex(
        top.real, hub.imag - 90 * math.sqrt(1 - ((top.real - hub.real) / 152) ** 2)
    )
    meridian = (top + foot) / 2
    half = abs(foot - top) / 2
    axis = math.degrees(cmath.phase(foot - top))
    return _figure(
        [
            outline,
            _dee(hub, 177, 115, 95, 35),
            _dee(hub, 152, 90, 70, 30),
            _ellipse(meridian, half, 11, axis, 180, 360),
        ],
        [_ellipse(meridian, half, 11, axis, 0, 180)],
    )


@dataclass(frozen=True)
class Ring:
    outer: complex
    inner: complex
    big: float
    small: float

    def at(self, across: float, angle: float) -> complex:
        c = self.outer + (self.inner - self.outer) * across
        r = self.big + (self.small - self.big) * across
        return c + r * cmath.exp(1j * math.radians(angle))

    def path(
        self, s0: float, a0: float, s1: float, a1: float, bow: float = 0.0
    ) -> Curve:
        out: Curve = []
        for k in range(121):
            t = k / 120
            ease = t * t * (3 - 2 * t)
            out.append(
                self.at(
                    s0 + (s1 - s0) * ease,
                    a0 + (a1 - a0) * t + bow * math.sin(math.pi * t),
                )
            )
        return out

    def rims(self) -> list[Curve]:
        return [
            _arc(self.outer, self.big, 0, 360),
            _arc(self.inner, self.small, 0, 360),
        ]


def fig_17() -> str:
    ring = Ring(339.6 + 314.4j, 342 + 332.4j, 282, 141)
    touches = [(0, -157), (1, -90), (0, -39), (1, 47), (0, 88), (1, 168), (0, 203)]
    legs = [
        ring.path(s0, a0, s1, a1) for (s0, a0), (s1, a1) in itertools.pairwise(touches)
    ]
    return _figure([*ring.rims(), *legs[0::2]], legs[1::2])


def fig_18() -> str:
    ring = Ring(1128 + 318j, 1114.8 + 320.4j, 282, 139)
    outer_turns = (-161, -166.5, -173)
    inner_turns = (-145, -159, -172)

    def lat(angle: float) -> float:
        return 0.45 + 0.15 * math.sin(math.radians(angle))

    fronts = [ring.path(0, a, 1, b, bow=3) for a, b in zip(outer_turns, inner_turns)]
    backs = [
        ring.path(0, a, 1, b, bow=-3) for a, b in zip(outer_turns, inner_turns[1:])
    ]
    latitude = [ring.at(lat(-215 - k), -215 - k) for k in range(251)]
    return _figure(
        [*ring.rims(), *fronts],
        [
            ring.path(lat(-105), -105, 1, inner_turns[0]),
            *backs,
            ring.path(0, outer_turns[-1], lat(-215), -215),
            latitude,
        ],
    )


LOBE, HOLE, FILLET = 140.0, 78.0, 130.0


def _trilobe() -> tuple[
    Curve, list[Curve], dict[str, complex], dict[tuple[str, str], complex]
]:
    top = 245 + 165j
    centres = {"T": top, "R": top + 180 + 250j, "L": top - 120 + 240j}
    middle = sum(centres.values()) / 3
    order = ["T", "R", "L"]
    joins: dict[tuple[str, str], tuple[complex, complex, complex, complex]] = {}
    for a, b in zip(order, order[1:] + order[:1]):
        pa, pb = centres[a], centres[b]
        m = (pa + pb) / 2
        out = (pb - pa) * 1j / abs(pb - pa)
        if (out.conjugate() * (m - middle)).real < 0:
            out = -out
        f = m + out * math.sqrt((LOBE + FILLET) ** 2 - abs(pb - pa) ** 2 / 4)
        ta = pa + LOBE * (f - pa) / abs(f - pa)
        tb = pb + LOBE * (f - pb) / abs(f - pb)
        joins[a, b] = (f, ta, tb, f - out * FILLET)
    outline: Curve = []
    for i, name in enumerate(order):
        prev = joins[order[i - 1], name][2]
        f, ta, tb, _ = joins[name, order[(i + 1) % 3]]
        c = centres[name]
        a0 = math.degrees(cmath.phase(prev - c))
        a1 = math.degrees(cmath.phase(ta - c))
        outline += _arc(c, LOBE, a0, a0 + (a1 - a0) % 360)
        f0 = math.degrees(cmath.phase(ta - f))
        f1 = math.degrees(cmath.phase(tb - f))
        outline += _arc(f, FILLET, f0, f0 + (f1 - f0 + 540) % 360 - 180)
    holes = [_arc(c, HOLE, 0, 360) for c in centres.values()]
    pinches = {k: v[3] for k, v in joins.items()}
    return outline, holes, centres, pinches


def fig_19() -> str:
    outline, holes, centres, pinches = _trilobe()
    c = centres["L"]
    p1, p2 = pinches["L", "T"], pinches["R", "L"]
    r1, r2 = abs(p1 - c), abs(p2 - c)
    a1 = math.degrees(cmath.phase(p1 - c))
    a2 = a1 + (math.degrees(cmath.phase(p2 - c)) - a1) % 360

    def around(bulge: float) -> Curve:
        out: Curve = []
        for k in range(121):
            t = k / 120
            r = r1 + (r2 - r1) * t + bulge * math.sin(math.pi * t)
            out.append(c + r * cmath.exp(1j * math.radians(a1 + (a2 - a1) * t)))
        return out

    front, back = around(14), around(-10)
    return _figure(
        [outline, *holes, front],
        [back],
        arrows=[_heading(front, 0.42), _heading(back, 0.86, backward=True)],
    )


def fig_20() -> str:
    outline, holes, centres, _ = _trilobe()
    c = centres["L"]

    def polar(r: float, angle: float) -> complex:
        return c + r * cmath.exp(1j * math.radians(angle))

    def strand(edge: float, rim: float, r: float, inward: bool) -> Curve:
        outer, inner = polar(LOBE, edge), polar(r, rim)
        radial = cmath.exp(1j * math.radians(edge))
        along = 1j * cmath.exp(1j * math.radians(rim))
        if inward:
            return _bezier(outer, outer - 18 * radial, inner - 18 * along, inner)
        return _bezier(inner, inner + 18 * along, outer - 18 * radial, outer)

    def loop(r: float, enter: float, leave: float) -> Curve:
        return _arc(c, r, enter, leave + 360)

    front = [
        strand(153, 160, 98, True),
        loop(98, 160, 130),
        strand(139, 130, 98, False),
    ]
    back = [strand(149, 155, 87, True), loop(87, 155, 135), strand(143, 135, 87, False)]
    return _figure(
        [outline, *holes, *front],
        back,
        arrows=[
            _heading(front[1], 0.49),
            _heading(front[1], 0.04),
            _heading(front[2], 0.55),
        ],
    )


FIGURES: dict[str, Callable[[], str]] = {
    "14": fig_14,
    "15": fig_15,
    "16": fig_16,
    "17": fig_17,
    "18": fig_18,
    "19": fig_19,
    "20": fig_20,
}
