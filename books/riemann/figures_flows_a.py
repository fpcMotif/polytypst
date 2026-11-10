"""Figs. 21-26 (§ 11): streamings finite everywhere on the anchor-ring and on surfaces p = 2 and p = 3,
seen from above, with the apparent boundary an equipotential curve or a stream-line.

Figs. 21 and 22 are exact: meridians are radii and curves of latitude are circles. Each later pair is a
streaming and its conjugate on one surface. One harmonic function u, solved by the method of fundamental
solutions (a sum of logarithmic charges fitted to the boundary values), gives both: the stream-lines of
Figs. 23 and 25 are the gradient lines of u, and those of Figs. 24 and 26 are its level curves."""

from __future__ import annotations

import cmath
import itertools
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import contourpy
import numpy as np
from matplotlib.path import Path as Polygon

from .figures import HEAVY, INK, Frame, _arrowhead, _d, _label, _stroke, _svg

OUTLINE = 2.0
Curve = list[complex]


def P(x: float, y: float) -> complex:
    """A point read off the scan crop, x right and y down, as a complex number with y up."""
    return complex(x, -y)


def _circle(center: complex, r: float, steps: int = 360) -> Curve:
    return [center + r * cmath.exp(2j * math.pi * k / steps) for k in range(steps + 1)]


def _closed_spline(points: Sequence[complex], per_span: int = 40) -> Curve:
    """A smooth closed curve through `points` (periodic Catmull-Rom)."""
    n = len(points)
    out: Curve = []
    for i in range(n):
        p0, p1, p2, p3 = (points[(i + k) % n] for k in (-1, 0, 1, 2))
        for s in range(per_span):
            t = s / per_span
            out.append(
                0.5
                * (
                    2 * p1
                    + (p2 - p0) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                    + (3 * p1 - p0 - 3 * p2 + p3) * t**3
                )
            )
    out.append(out[0])
    return out


def _signed_area(curve: Curve) -> float:
    return 0.5 * sum((a.conjugate() * b).imag for a, b in itertools.pairwise(curve))


def _resample(curve: Curve, count: int) -> Curve:
    lengths = np.cumsum([0.0, *(abs(b - a) for a, b in itertools.pairwise(curve))])
    targets = np.linspace(0, lengths[-1], count, endpoint=False)
    xs = np.interp(targets, lengths, [z.real for z in curve])
    ys = np.interp(targets, lengths, [z.imag for z in curve])
    return [complex(x, y) for x, y in zip(xs, ys, strict=True)]


def _inward(curve: Curve) -> list[complex]:
    """Unit normals pointing into the region the closed curve encloses."""
    sign = 1 if _signed_area(curve) > 0 else -1
    n = len(curve)
    return [
        sign
        * 1j
        * (curve[(k + 1) % n] - curve[k - 1])
        / abs(curve[(k + 1) % n] - curve[k - 1])
        for k in range(n)
    ]


@dataclass
class Boundary:
    curve: Curve
    value: float
    hole: bool

    def polygon(self) -> Polygon:
        return Polygon([(z.real, z.imag) for z in self.curve])


class Potential:
    """u = sum q log|z - s| + C, harmonic between the boundaries and fitted to their values."""

    def __init__(self, boundaries: Sequence[Boundary], spacing: float = 7.0) -> None:
        self.boundaries = list(boundaries)
        sources: list[complex] = []
        rows: list[complex] = []
        values: list[float] = []
        for b in self.boundaries:
            perimeter = sum(abs(q - p) for p, q in itertools.pairwise(b.curve))
            charges = _resample(b.curve, max(24, round(perimeter / spacing)))
            away = [-n if not b.hole else n for n in _inward(charges)]
            sources += [
                p + 1.6 * spacing * d for p, d in zip(charges, away, strict=True)
            ]
            points = _resample(b.curve, 3 * len(charges))
            rows += points
            values += [b.value] * len(points)
        self.sources = np.array(sources)
        z = np.array(rows)
        matrix = np.column_stack(
            [np.log(np.abs(z[:, None] - self.sources[None, :])), np.ones(len(z))]
        )
        solution, *_ = np.linalg.lstsq(matrix, np.array(values), rcond=None)
        self.charges, self.constant = solution[:-1], solution[-1]
        self.residual = float(np.max(np.abs(matrix @ solution - np.array(values))))
        self.rim = next(b for b in self.boundaries if not b.hole).polygon()
        self.holes = [b.polygon() for b in self.boundaries if b.hole]

    def u(self, z: np.ndarray) -> np.ndarray:
        return (
            np.log(np.abs(z[..., None] - self.sources)) @ self.charges + self.constant
        )

    def gradient(self, z: complex) -> complex:
        """grad u as a complex number, the velocity of the streaming whose potential is u."""
        return complex(np.sum(self.charges / (z - self.sources))).conjugate()

    def inside(self, z: complex) -> bool:
        point = (z.real, z.imag)
        return self.rim.contains_point(point) and not any(
            h.contains_point(point) for h in self.holes
        )

    def inside_grid(self, z: np.ndarray) -> np.ndarray:
        pts = np.column_stack([z.real.ravel(), z.imag.ravel()])
        ok = self.rim.contains_points(pts)
        for h in self.holes:
            ok &= ~h.contains_points(pts)
        return ok.reshape(z.shape)

    def saddle(self, guess: complex) -> complex:
        """The cross-point near `guess`: Newton's method on f'(z) = sum q/(z - s)."""
        z = guess
        for _ in range(60):
            f1 = complex(np.sum(self.charges / (z - self.sources)))
            f2 = complex(np.sum(-self.charges / (z - self.sources) ** 2))
            z -= f1 / f2
        return z

    def trace(
        self, start: complex, sign: float = 1.0, step: float = 1.2, limit: int = 6000
    ) -> Curve:
        """The gradient line from `start` (sign -1 runs against the flow) until it leaves the surface."""

        def heading(z: complex) -> complex:
            v = self.gradient(z)
            return sign * v / abs(v) if abs(v) > 1e-12 else 0j

        line = [start]
        z = start
        for _ in range(limit):
            k1 = heading(z)
            k2 = heading(z + 0.5 * step * k1)
            k3 = heading(z + 0.5 * step * k2)
            k4 = heading(z + step * k3)
            nxt = z + step * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            if not self.inside(nxt):
                lo, hi = z, nxt
                for _ in range(20):
                    mid = (lo + hi) / 2
                    lo, hi = (mid, hi) if self.inside(mid) else (lo, mid)
                line.append(lo)
                break
            if nxt == z:
                break
            line.append(nxt)
            z = nxt
        return line

    def levels(
        self, z: np.ndarray, values: Sequence[float], margin: float = 2.5
    ) -> list[Curve]:
        """Level curves of u inside the surface, stopped `margin` px short of its boundary."""
        hidden = ~self.inside_grid(z)
        near = np.zeros_like(hidden)
        for b in self.boundaries:
            for p in _resample(b.curve, 400):
                near |= np.abs(z - p) < margin
        data = np.ma.array(self.u(z), mask=hidden | near)
        gen = contourpy.contour_generator(
            z.real, z.imag, data, line_type=contourpy.LineType.Separate
        )
        return [
            [complex(x, y) for x, y in line]
            for v in values
            for line in gen.lines(v)
            if len(line) > 4
        ]


def _seed(curve: Curve, share: float, into: float, toward_inside: bool) -> complex:
    """A point `into` px off `curve` at `share` of its length, on the side the surface lies."""
    pts = _resample(curve, 720)
    k = round(share * 720) % 720
    n = _inward(pts)[k]
    return pts[k] + (n if toward_inside else -n) * into


def _length(line: Sequence[complex]) -> float:
    return sum(abs(b - a) for a, b in itertools.pairwise(line))


def _along(line: Sequence[complex], share: float) -> complex:
    left = _length(line) * share
    for a, b in itertools.pairwise(line):
        if left <= abs(b - a):
            return a + (b - a) * (left / abs(b - a) if abs(b - a) else 0)
        left -= abs(b - a)
    return line[-1]


@dataclass
class Stream:
    line: Curve
    arrows: Sequence[float] = (0.5,)


def _picture(
    frame: Frame,
    size: tuple[float, float],
    velocity: Callable[[complex], complex],
    streams: Sequence[Stream],
    outlines: Sequence[Curve] = (),
    labels: Sequence[tuple[str, complex]] = (),
    dots: Sequence[complex] = (),
) -> str:
    heads: list[str] = []
    for s in streams:
        for share in s.arrows:
            at = _along(s.line, share)
            v = velocity(at)
            if v and cmath.isfinite(v):
                heads.append(_arrowhead(frame.svg(at), frame.angle(v)))
    body = (
        _stroke([_d([frame.svg(z) for z in c]) for c in outlines], OUTLINE)
        + _stroke([_d([frame.svg(z) for z in s.line]) for s in streams], HEAVY)
        + "".join(heads)
        + "".join(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="{INK}"/>'
            for x, y in map(frame.svg, dots)
        )
        + "".join(
            _label(t, (frame.svg(at)[0], frame.svg(at)[1] + 11)) for t, at in labels
        )
    )
    return _svg(size[0], size[1], body)


ANNULUS_FRAME = Frame(origin=(220.0, 220.0), scale=1.0)
RING_OUT, RING_IN = 200.0, 100.0


def fig_21() -> str:
    """A curve of latitude is the seat of electromotive force: every stream-line is a meridian, shown as a
    piece of a radius, and the flow on the upper side runs outward."""
    streams = [
        Stream([cmath.exp(1j * t) * RING_IN, cmath.exp(1j * t) * RING_OUT])
        for t in (2 * math.pi * k / 20 for k in range(20))
    ]
    return _picture(
        ANNULUS_FRAME,
        (440, 440),
        lambda z: z / abs(z),
        streams,
        outlines=[_circle(0, RING_IN), _circle(0, RING_OUT)],
    )


def fig_22() -> str:
    """The conjugate streaming: the curves of latitude, the two boundary circles among them, are the
    stream-lines, all described counter-clockwise."""
    radii = (RING_IN, RING_IN + 34, RING_IN + 67, RING_OUT)
    streams = [
        Stream(
            _circle(0, r),
            arrows=tuple(((a % 360) / 360) for a in (185, 45 + 4 * k, 315 + 2 * k)),
        )
        for k, r in enumerate(radii)
    ]
    return _picture(ANNULUS_FRAME, (440, 440), lambda z: 1j * z, streams)


# Fig. 23's surface, p = 2, as the scan draws it: the anchor-ring with a crescent-shaped second hole.
RIM_23 = [
    P(22, 210),
    P(42, 122),
    P(110, 47),
    P(230, 14),
    P(340, 16),
    P(432, 26),
    P(490, 68),
    P(510, 150),
    P(510, 270),
    P(486, 350),
    P(420, 386),
    P(300, 393),
    P(170, 390),
    P(80, 350),
    P(32, 282),
]
CRESCENT_23 = [
    P(402, 82),
    P(448, 98),
    P(470, 152),
    P(473, 250),
    P(456, 314),
    P(414, 338),
    P(382, 330),
    P(370, 302),
    P(382, 254),
    P(388, 206),
    P(380, 156),
    P(368, 114),
    P(378, 88),
]
HOLE_23 = (P(190, 205), 88.0)


def _surface_23() -> Potential:
    return Potential(
        [
            Boundary(_closed_spline(RIM_23), 1.0, hole=False),
            Boundary(_closed_spline(CRESCENT_23), 1.0, hole=True),
            Boundary(_circle(*HOLE_23), 0.0, hole=True),
        ]
    )


FRAME_23 = Frame(origin=(6.0, 6.0), scale=1.0)
SIZE_23 = (528, 410)


def fig_23() -> str:
    """p = 2: the flow leaves the round hole and runs to the rim and to the crescent. Two cross-points
    appear on the right, one on the upper side: the stream-lines round the crescent meet there and part
    into the crescent and over the rim."""
    surface = _surface_23()
    hole, r = HOLE_23
    streams = [
        Stream(surface.trace(hole + (r + 0.6) * cmath.exp(1j * math.radians(a))))
        for a in range(-170, 190, 20)
    ]
    cross = surface.saddle(P(490, 210))
    for d in (1, -1):
        streams.append(Stream(surface.trace(cross + 0.8 * d), arrows=(0.8,)))
        streams.append(
            Stream(surface.trace(cross + 0.8j * d, -1.0)[::-1], arrows=(0.35, 0.8))
        )
    return _picture(
        FRAME_23,
        SIZE_23,
        surface.gradient,
        streams,
        outlines=[
            _closed_spline(RIM_23),
            _closed_spline(CRESCENT_23),
            _circle(*HOLE_23),
        ],
    )


def _offset(curve: Curve, gap: float, into: bool) -> Curve:
    normals = _inward(curve)
    return [p + (n if into else -n) * gap for p, n in zip(curve, normals, strict=True)]


def _arc_outside(curve: Curve, center: complex, radius: float) -> Curve:
    """The one arc of a closed curve left after cutting out the points within `radius` of `center`."""
    pts = curve[:-1]
    cut = [abs(p - center) < radius for p in pts]
    start = next(k for k in range(len(pts)) if cut[k - 1] and not cut[k])
    rolled = pts[start:] + pts[:start]
    return rolled[: next(k for k, p in enumerate(rolled) if abs(p - center) < radius)]


def _separatrix(
    rim: Curve, hole: Curve, cross: complex, gap: float = 11.0, reach: float = 40.0
) -> Curve:
    """The stream-line through the cross-point, drawn `gap` px inside the rim and outside the hole: it runs
    round the rim, crosses itself at `cross` and runs round the hole. The exact curve hugs both boundaries
    too closely to see, since u at the cross-point differs from its boundary value by about 1e-8."""
    outer = _arc_outside(
        _resample(_offset(rim, gap, True), 900) + [rim[0]], cross, reach
    )
    inner = _arc_outside(
        _resample(_offset(hole, gap, False), 600) + [hole[0]], cross, reach
    )
    if outer[0].imag > cross.imag:
        outer = outer[::-1]
    if inner[0].imag > cross.imag:
        inner = inner[::-1]

    def join(a: Curve, b: Curve) -> Curve:
        p0, p1 = a[-1], b[0]
        t0 = (a[-1] - a[-2]) / abs(a[-1] - a[-2])
        t1 = (b[1] - b[0]) / abs(b[1] - b[0])
        k = 0.45 * abs(p1 - p0)
        c0, c1 = p0 + k * t0, p1 - k * t1
        return [
            (1 - t) ** 3 * p0
            + 3 * (1 - t) ** 2 * t * c0
            + 3 * (1 - t) * t**2 * c1
            + t**3 * p1
            for t in np.linspace(0, 1, 60)[1:-1]
        ]

    return [*outer, *join(outer, inner), *inner, *join(inner, outer), outer[0]]


def fig_24() -> str:
    """The conjugate streaming on the same surface: the stream-lines are the curves u = const, among them
    the boundaries, and the one through the cross-point crosses itself there."""
    surface = _surface_23()
    cross = surface.saddle(P(490, 210))
    xs, ys = np.meshgrid(np.linspace(10, 520, 900), np.linspace(-400, -5, 700))
    lines = surface.levels(xs + 1j * ys, [0.2, 0.45, 0.8])
    rim, crescent = _closed_spline(RIM_23), _closed_spline(CRESCENT_23)
    streams = [
        Stream(line, arrows=(0.25, 0.75) if _length(line) > 500 else (0.5,))
        for line in lines
    ]
    streams += [
        Stream(_separatrix(rim, crescent, cross), arrows=(0.2, 0.42, 0.7, 0.9)),
        Stream(rim, arrows=(0.05, 0.3, 0.55, 0.8)),
        Stream(crescent, arrows=(0.2, 0.7)),
        Stream(_circle(*HOLE_23), arrows=(0.1, 0.45, 0.8)),
    ]

    def velocity(z: complex) -> complex:
        return 1j * surface.gradient(z)

    return _picture(FRAME_23, SIZE_23, velocity, streams)


# Figs. 25-26's surface, p = 3: three lobes round three holes, joined at a, b and at the bottom.
TOP, LEFT, RIGHT = P(214, 104), P(106, 299), P(311, 300)
HOLE_R = (64.0, 59.0, 60.0)
LOBE_R = 96.0
BLEND = 0.034
# The rim's potential, set so that the stream-line through c in Fig. 26 runs midway between the lower holes
# and the rim, as the scan draws it.
RIM_U = 0.25


def _rim_25() -> Curve:
    xs, ys = np.meshgrid(np.linspace(-40, 460, 800), np.linspace(-440, 40, 760))
    z = xs + 1j * ys
    stack = np.stack([np.abs(z - c) - LOBE_R for c in (TOP, LEFT, RIGHT)])
    smooth_min = -np.log(np.sum(np.exp(-BLEND * stack), axis=0)) / BLEND
    gen = contourpy.contour_generator(
        xs, ys, smooth_min, line_type=contourpy.LineType.Separate
    )
    outline = max(gen.lines(0.0), key=len)
    curve = [complex(x, y) for x, y in outline]
    return [*curve, curve[0]]


def _surface_25() -> Potential:
    return Potential(
        [
            Boundary(_rim_25(), RIM_U, hole=False),
            Boundary(_circle(TOP, HOLE_R[0]), 1.0, hole=True),
            Boundary(_circle(LEFT, HOLE_R[1]), 0.0, hole=True),
            Boundary(_circle(RIGHT, HOLE_R[2]), 0.0, hole=True),
        ]
    )


FRAME_25 = Frame(origin=(14.0, 4.0), scale=1.0)
SIZE_25 = (440, 400)


def _rim_labels(rim: Curve, surface: Potential) -> list[tuple[str, complex]]:
    """Labels a and b just outside the rim at the cross-points where the flow across it changes direction."""
    pts = _resample(rim, 1440)
    normals = _inward(pts)
    flux = [
        (surface.gradient(p + 2 * n) * n.conjugate()).real
        for p, n in zip(pts, normals, strict=True)
    ]
    turns = [
        k
        for k in range(len(pts))
        if flux[k - 1] * flux[k] < 0 and pts[k].imag > TOP.imag - 100
    ]
    left = min(
        (k for k in turns if pts[k].real < TOP.real),
        key=lambda k: abs(pts[k] - P(80, 168)),
    )
    right = min(
        (k for k in turns if pts[k].real > TOP.real),
        key=lambda k: abs(pts[k] - P(332, 168)),
    )
    return [(name, pts[k] - 24 * normals[k]) for name, k in (("a", left), ("b", right))]


def fig_25() -> str:
    """p = 3, the curves of latitude on every handle the seats of electromotive force: the flow runs from
    the two lower holes up into the top one, out over the rim below and in over the rim above. Cross-points
    at a and b on the rim and at c between the lower holes."""
    surface = _surface_25()
    rim = _rim_25()
    streams: list[Stream] = []
    for center, r, angles in (
        (LEFT, HOLE_R[1], range(-180, 180, 30)),
        (RIGHT, HOLE_R[2], range(0, 360, 30)),
    ):
        for a in angles:
            if (
                math.cos(math.radians(a + 15) - cmath.phase(P(208, 291) - center))
                > 0.94
            ):
                continue
            line = surface.trace(
                center + (r + 0.6) * cmath.exp(1j * math.radians(a + 15))
            )
            streams.append(Stream(line))
    for a in range(20, 170, 20):
        line = surface.trace(
            TOP + (HOLE_R[0] + 0.6) * cmath.exp(1j * math.radians(a)), -1.0
        )
        if abs(line[-1] - TOP) > HOLE_R[0] + 20 and all(
            abs(line[-1] - c) > 70 for c in (LEFT, RIGHT)
        ):
            streams.append(Stream(line[::-1]))
    c = surface.saddle(P(212, 238))
    for d in (1j, -1j):
        streams.append(Stream(surface.trace(c + 0.8 * d)))
    return _picture(
        FRAME_25,
        SIZE_25,
        surface.gradient,
        streams,
        outlines=[
            rim,
            _circle(TOP, HOLE_R[0]),
            _circle(LEFT, HOLE_R[1]),
            _circle(RIGHT, HOLE_R[2]),
        ],
        labels=[*_rim_labels(rim, surface), ("c", c + P(-14, 16))],
    )


def fig_26() -> str:
    """The conjugate streaming: the meridians of every handle are the seats of electromotive force. The
    stream-lines are the curves u = const; the one through c crosses itself there, and the one through a
    and b runs from the rim under the top hole."""
    surface = _surface_25()
    rim = _rim_25()
    c = surface.saddle(P(212, 238))
    u_c = float(surface.u(np.array([c]))[0])
    xs, ys = np.meshgrid(np.linspace(-20, 440, 900), np.linspace(-410, 10, 820))
    lines = surface.levels(xs + 1j * ys, [u_c, RIM_U, 0.6])
    streams = [
        Stream(line, arrows=(0.25, 0.75) if _length(line) > 450 else (0.5,))
        for line in lines
    ]
    streams += [Stream(rim, arrows=(0.08, 0.3, 0.5, 0.7, 0.92))]
    streams += [
        Stream(_circle(center, r), arrows=(0.25, 0.75))
        for center, r in zip((TOP, LEFT, RIGHT), HOLE_R, strict=True)
    ]

    def velocity(z: complex) -> complex:
        return 1j * surface.gradient(z)

    return _picture(
        FRAME_25,
        SIZE_25,
        velocity,
        streams,
        labels=[*_rim_labels(rim, surface), ("c", c + P(2, 34))],
    )


FIGURES: dict[str, Callable[[], str]] = {
    "21": fig_21,
    "22": fig_22,
    "23": fig_23,
    "24": fig_24,
    "25": fig_25,
    "26": fig_26,
}
