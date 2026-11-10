"""Figs. 35–43: the anchor-ring rectangle and annulus, and the two-sheeted surface with branch-points ±1, ±1/κ.

The curves of Figs. 40–43 are computed: z = sn(W, κ) carries the surface onto the rectangle, and the
annulus is the anchor ring seen from above, its tube angle got back from η by the ring's own conformal map."""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Sequence

import numpy as np

from .figures import (
    FINE,
    FONT,
    HEAVY,
    INK,
    LABEL_PX,
    LIGHT,
    Point,
    _arrowhead,
    _d,
    _dashed_d,
    _grid,
    _levels_of,
    _stroke,
    _svg,
    _thin,
)

AGM_STEPS = 10
HATCH_GAP = 7.0
HATCH_WIDTH = 0.85
SMALL_PX = 24

Mapper = Callable[[complex], Point]


def _agm_tail(m: float) -> tuple[list[float], list[float]]:
    a, b, c = 1.0, math.sqrt(1 - m), math.sqrt(m)
    a_s, c_s = [a], [c]
    for _ in range(AGM_STEPS):
        a, b, c = (a + b) / 2, math.sqrt(a * b), (a - b) / 2
        a_s.append(a)
        c_s.append(c)
    return a_s, c_s


def _quarter_period(k: float) -> float:
    return math.pi / (2 * _agm_tail(k * k)[0][-1])


def _jacobi_real(u: np.ndarray, k: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """sn, cn, dn of real u by the descending AGM (Abramowitz and Stegun 16.4)."""
    m = k * k
    a_s, c_s = _agm_tail(m)
    phi = 2.0**AGM_STEPS * a_s[-1] * u
    for n in range(AGM_STEPS, 0, -1):
        phi = (phi + np.arcsin(np.clip(c_s[n] / a_s[n] * np.sin(phi), -1, 1))) / 2
    sn, cn = np.sin(phi), np.cos(phi)
    return sn, cn, np.sqrt(1 - m * sn * sn)


def _jacobi(
    w: np.ndarray | complex, k: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """sn, cn, dn of complex w, from the real functions of Re w (modulus k) and Im w (modulus k')."""
    w = np.asarray(w, dtype=complex)
    k1 = math.sqrt(1 - k * k)
    s, c, d = _jacobi_real(w.real, k)
    s1, c1, d1 = _jacobi_real(w.imag, k1)
    with np.errstate(divide="ignore", invalid="ignore"):
        den = c1 * c1 + k * k * s * s * s1 * s1
        sn = (s * d1 + 1j * c * d * s1 * c1) / den
        cn = (c * c1 - 1j * s * d * s1 * d1) / den
        dn = (d * c1 * d1 - 1j * k * k * s * c * s1) / den
    return sn, cn, dn


def _modulus_for(aspect: float) -> float:
    """The κ whose period rectangle 4K by 2K' has this width to height."""
    lo, hi = 0.05, 0.99
    for _ in range(60):
        k = (lo + hi) / 2
        ratio = 2 * _quarter_period(k) / _quarter_period(math.sqrt(1 - k * k))
        lo, hi = (lo, k) if ratio > aspect else (k, hi)
    return (lo + hi) / 2


# The scan draws the rectangle of Figs. 38, 40 and 41 about 1.89 times as wide as high.
KAPPA = _modulus_for(1.89)
K = _quarter_period(KAPPA)
K1 = _quarter_period(math.sqrt(1 - KAPPA * KAPPA))
# The rectangle is u in [-K, 3K], v in [-K', K']: +1 sits at its centre, the points infinity on its long sides.
CENTRE = complex(K, 0)

# The annulus of Figs. 36, 39, 42 and 43: inner radius half the outer one, as the scan draws it.
RING_R, RING_RHO = 3.0, 1.0


def _sn(w: np.ndarray | complex) -> np.ndarray:
    return _jacobi(w, KAPPA)[0]


def _stream(w: complex) -> complex:
    """Direction of increasing x along the curves y = const.: the conjugate of dz/dW = cn dn."""
    _, cn, dn = _jacobi(w, KAPPA)
    return complex(np.conj(cn * dn))


# Text: letters italic, numerals, signs and infinity upright, all in New Computer Modern.


# Advance widths in em of New Computer Modern, so each glyph is placed as its own text and every SVG renderer agrees.
ADVANCE = {
    " ": 0.333,
    "+": 0.68,
    "−": 0.68,
    "=": 0.778,
    "∞": 1.0,
    "O": 0.763,
    "Y": 0.75,
    "π": 0.57,
    "ξ": 0.44,
}


def _math(
    text: str,
    at: Point,
    anchor: str = "middle",
    size: float = LABEL_PX,
    turn: float = 0,
) -> str:
    widths = [ADVANCE.get(ch, 0.5) * size for ch in text]
    x = at[0] - {"start": 0.0, "middle": 0.5, "end": 1.0}[anchor] * sum(widths)
    glyphs: list[str] = []
    for ch, width in zip(text, widths, strict=True):
        if ch != " ":
            style = "italic" if ch.isalpha() and ch != "Y" else "normal"
            glyphs.append(
                f'<text x="{x:.1f}" y="{at[1]:.1f}" font-family="{FONT}" font-size="{size:g}" '
                f'font-style="{style}" fill="{INK}">{ch}</text>'
            )
        x += width
    rotate = f' transform="rotate({turn:g} {at[0]:.1f} {at[1]:.1f})"' if turn else ""
    return f"<g{rotate}>{''.join(glyphs)}</g>"


def _frac(sign: str, at: Point, size: float = SMALL_PX) -> str:
    """sign 1/κ as a built-up fraction, its bar centred on `at`."""
    x, y = at
    half = size * 0.36
    out = _math("1", (x, y - size * 0.18), size=size)
    out += _math("κ", (x, y + size * 0.78), size=size)
    out += f'<path d="M{x - half:.1f},{y:.1f} L{x + half:.1f},{y:.1f}" stroke="{INK}" stroke-width="1.1"/>'
    if sign:
        out += _math(sign, (x - half - 2, y + size * 0.3), anchor="end", size=size)
    return out


def _tick(at: Point, length: float = 8.0) -> str:
    return _d([(at[0], at[1] - length), (at[0], at[1] + length)])


# Hatching: parallel lines rising to the right, cut to the region by sampling each line finely.


def _hatch(
    inside: Callable[[float, float], bool], box: tuple[float, float, float, float]
) -> str:
    x0, y0, x1, y1 = box
    step = HATCH_GAP * math.sqrt(2)
    paths: list[str] = []
    c = x0 + y0 + step / 2
    while c < x1 + y1:
        xs = np.arange(max(x0, c - y1), min(x1, c - y0), 0.25)
        run: list[Point] = []
        for x in xs:
            p = (float(x), float(c - x))
            if inside(*p):
                run.append(p)
            elif run:
                paths.append(_d([run[0], run[-1]]))
                run = []
        if len(run) > 1:
            paths.append(_d([run[0], run[-1]]))
        c += step
    return _stroke(paths, HATCH_WIDTH)


# The rectangle, in pixels.

RECT_W = 560.0
RECT_H = RECT_W * (2 * K1) / (4 * K)
RECT_LEFT = 66.0
RECT_TOP = 76.0
RECT_SIZE = (RECT_LEFT * 2 + RECT_W, RECT_TOP * 2 + RECT_H)


def _rect_px(w: complex) -> Point:
    return (
        RECT_LEFT + (w.real + K) / (4 * K) * RECT_W,
        RECT_TOP + (K1 - w.imag) / (2 * K1) * RECT_H,
    )


def _rect_box() -> tuple[float, float, float, float]:
    return RECT_LEFT, RECT_TOP, RECT_LEFT + RECT_W, RECT_TOP + RECT_H


def _rect_outline(width: float) -> str:
    x0, y0, x1, y1 = _rect_box()
    return _stroke([_d([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])], width)


def _rect_labels() -> str:
    """The values of z at the corners, the edge midpoints and the centre row, as Figs. 38, 40, 41 print them."""
    x0, y0, x1, y1 = _rect_box()
    xs = [x0 + RECT_W * j / 4 for j in range(5)]
    ym = (y0 + y1) / 2
    out = ""
    for j, x in enumerate(xs):
        for y, up in ((y0, True), (y1, False)):
            if j % 2:
                out += _math("∞", (x, y - 14 if up else y + 34))
            else:
                bar = y - 30 if up else y + 34
                out += _frac("+" if j == 2 else "−", (x + 6, bar))
    out += _math("−1", (x0 - 8, ym + 9), anchor="end", size=SMALL_PX + 2)
    out += _math("−1", (x1 + 8, ym + 9), anchor="start", size=SMALL_PX + 2)
    return out


def _rect_ticks() -> str:
    x0, y0, _, y1 = _rect_box()
    xs = [x0 + RECT_W * j / 4 for j in (1, 3)]
    return _stroke([_tick((x, y), 6) for x in xs for y in (y0, y1)], LIGHT)


# The annulus, in pixels: angle from u, tube angle from v by the anchor ring's conformal map.

RING_OUTER = 170.0
RING_SCALE = RING_OUTER / (RING_R + RING_RHO)


def _ring_px_for(centre: Point) -> Mapper:
    squeeze = math.sqrt((RING_R - RING_RHO) / (RING_R + RING_RHO))

    def to_px(w: complex) -> Point:
        theta = (K - w.real) * math.pi / (2 * K)
        half = math.pi * w.imag / (2 * K1)
        alpha = 2 * math.atan2(squeeze * math.sin(half), math.cos(half))
        r = (RING_R - RING_RHO * math.cos(alpha)) * RING_SCALE
        return centre[0] + r * math.cos(theta), centre[1] - r * math.sin(theta)

    return to_px


def _circle(centre: Point, r: float, steps: int = 360) -> str:
    return _d(
        [
            (
                centre[0] + r * math.cos(2 * math.pi * j / steps),
                centre[1] + r * math.sin(2 * math.pi * j / steps),
            )
            for j in range(steps + 1)
        ]
    )


def _ring_inner() -> float:
    return (RING_R - RING_RHO) * RING_SCALE


# Curves on the W rectangle, carried to pixels.


def _curves(
    lines: Sequence[Sequence[complex]],
    to_px: Mapper,
    width: float,
    arrows: bool = False,
    shortest: float = 40.0,
) -> str:
    paths: list[str] = []
    heads: list[str] = []
    for line in lines:
        px = [to_px(w) for w in line]
        paths.append(_d(_thin(px)))
        if not arrows:
            continue
        lengths = [
            math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in itertools.pairwise(px)
        ]
        total = sum(lengths)
        if total < shortest:
            continue
        left = total / 2
        for j, step in enumerate(lengths):
            if left <= step:
                break
            left -= step
        w = line[j]
        v = _stream(w)
        if not v or not math.isfinite(abs(v)):
            continue
        a, b = to_px(w), to_px(w + v / abs(v) * 1e-4)
        heads.append(
            _arrowhead(px[j], math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        )
    return _stroke(paths, width) + "".join(heads)


def _level_set(
    levels: Sequence[float], take: Callable[[np.ndarray], np.ndarray], v0: float
) -> list[list[complex]]:
    """Curves where take(sn W) is each level, over u in [-K, 3K] and v in [v0, K']."""
    z = _grid(-K, 3 * K, v0, K1, n=1400)
    sn = _sn(z)
    values = take(sn)
    hidden = ~np.isfinite(values) | (np.abs(sn) > 60)
    return _levels_of(z, np.where(hidden, 0.0, values), hidden, levels)


X_LEVELS = (0.0, 0.3, 0.62, 1.0, 1.2, 1.9, 3.2, -0.3, -0.62, -1.0, -1.2, -1.9, -3.2)
Y_LEVELS = (0.25, 0.9, -0.25, -0.9)
# The ring squeezes the strip next to its inner rim, so Fig. 43 takes levels clear of the real axis.
RING_Y_LEVELS = (0.6, 1.8, -0.6, -1.8)


def _edge(
    a: complex, b: complex, cuts: Sequence[float], along: Callable[[complex], float]
) -> list[list[complex]]:
    """The straight run from a to b on the W rectangle, cut at the critical points, nudged off the poles."""
    marks = sorted({along(a), along(b), *cuts})
    lo, hi = min(along(a), along(b)), max(along(a), along(b))
    marks = [m for m in marks if lo - 1e-12 <= m <= hi + 1e-12]
    pieces: list[list[complex]] = []
    for m0, m1 in itertools.pairwise(marks):
        p0 = a + (b - a) * (m0 - along(a)) / (along(b) - along(a))
        p1 = a + (b - a) * (m1 - along(a)) / (along(b) - along(a))
        pieces.append([p0 + (p1 - p0) * t / 60 for t in range(61)])
    return pieces


def _real_runs(v_rows: Sequence[float]) -> list[list[complex]]:
    """The sides and the centre lines of the rectangle, where z is real, split where x turns or is infinite."""
    u_cuts = [-K, 0.0, K, 2 * K, 3 * K]
    runs: list[list[complex]] = []
    for v in v_rows:
        runs += _edge(complex(-K, v), complex(3 * K, v), u_cuts, lambda w: w.real)
    for u in (-K, K, 3 * K):
        runs += _edge(
            complex(u, min(v_rows)), complex(u, max(v_rows)), [0.0], lambda w: w.imag
        )
    return runs


# The figures.


def fig_35() -> str:
    """The anchor ring cut open: the rectangle -π ≤ ξ ≤ π, -p ≤ η ≤ p, its four quarters numbered."""
    w, h = 560.0, 560.0 / 1.89
    left, top = 150.0, 72.0
    cx, cy = left + w / 2, top + h / 2
    size = (left * 2 + w, top * 2 + h)
    axes = [
        _dashed_d([(cx, 6), (cx, top)]),
        _dashed_d([(cx, top + h), (cx, size[1] - 6)]),
        _dashed_d([(14, cy), (left, cy)]),
        _dashed_d([(left + w, cy), (size[0] - 14, cy)]),
    ]
    frame = [
        _d(
            [
                (left, top),
                (left + w, top),
                (left + w, top + h),
                (left, top + h),
                (left, top),
            ]
        )
    ]
    cross = [_d([(cx, top), (cx, top + h)]), _d([(left, cy), (left + w, cy)])]
    body = _stroke(axes, LIGHT) + _stroke(frame, HEAVY + 0.8) + _stroke(cross, LIGHT)
    body += _math("η =", (cx - 8, top + 40), anchor="end") + _math(
        "+p", (cx + 8, top + 40), anchor="start"
    )
    body += _math("η =", (cx - 8, top + h - 16), anchor="end") + _math(
        "−p", (cx + 8, top + h - 16), anchor="start"
    )
    for text, fx, fy in (
        ("1", 0.25, 0.3),
        ("2", 0.75, 0.3),
        ("3", 0.75, 0.76),
        ("4", 0.25, 0.76),
    ):
        body += _math(text, (left + w * fx, top + h * fy + 10))
    body += _math("ξ = −π", (left + 30, cy), turn=-90)
    body += _math("ξ = +π", (left + w - 30, cy), turn=90)
    return _svg(*size, body)


def fig_36() -> str:
    """The anchor ring seen from above: the cut ξ = ±π on the left, ξ = 0 on the right."""
    centre = (190.0, 262.0)
    outer, inner = RING_OUTER, _ring_inner()
    cx, cy = centre
    dots = [
        _dashed_d([(cx, cy - outer), (cx, 14)]),
        _dashed_d([(cx, cy), (cx, cy - inner)]),
        _dashed_d([(cx, cy), (cx + inner, cy)]),
        _dashed_d([(cx + outer, cy), (cx + outer + 70, cy)]),
    ]
    body = (
        _stroke(dots, FINE)
        + _stroke([_circle(centre, outer)], HEAVY)
        + _stroke([_circle(centre, inner)], LIGHT)
    )
    body += _stroke([_d([(cx - outer, cy), (cx - inner, cy)])], HEAVY)
    body += _stroke([_d([(cx + inner, cy), (cx + outer, cy)])], LIGHT)
    body += _math("Y", (cx + 10, 46), anchor="start")
    body += _math("O", (cx - 22, cy + 12), anchor="end")
    mid = (outer + inner) / 2
    body += _math("η = +p", (cx, cy - outer + 36))
    body += _math("η = +p", (cx, cy + outer - 14))
    for text, angle in (("2", 135), ("2", 45), ("1", -135), ("1", -45)):
        a = math.radians(angle)
        body += _math(text, (cx + mid * math.cos(a), cy - mid * math.sin(a) + 11))
    body += _math("ξ = +π", (cx - mid + 6, cy - 9), size=SMALL_PX - 2)
    body += _math("ξ = −π", (cx - mid + 6, cy + 26), size=SMALL_PX - 2)
    body += _math("ξ = 0", (cx + mid, cy + 26), size=SMALL_PX - 2)
    return _svg(cx + outer + 90, 440, body)


def fig_37() -> str:
    """The upper half-sheet: the real axis from -∞ to +∞, branch-lines from ±1 to ±1/κ, the half-plane above hatched."""
    size = (960.0, 220.0)
    axis_y, left, right = 128.0, 70.0, 890.0
    unit = 112.0
    mid = (left + right) / 2
    xs = {"far": 3.05 * unit}
    hatch = _hatch(
        lambda x, y: left < x < right and 10 < y < axis_y - 1.5,
        (left, 10, right, axis_y),
    )
    body = hatch
    body += _stroke([_d([(left + 6, axis_y), (right - 6, axis_y)])], LIGHT)
    body += _stroke(
        [
            _d([(mid - xs["far"], axis_y), (mid - unit, axis_y)]),
            _d([(mid + unit, axis_y), (mid + xs["far"], axis_y)]),
        ],
        HEAVY + 1.0,
    )
    body += _arrowhead((left, axis_y), 180) + _arrowhead((right, axis_y), 0)
    ticks = [mid - xs["far"], mid - unit, mid, mid + unit, mid + xs["far"]]
    body += _stroke([_tick((x, axis_y), 9) for x in ticks], LIGHT)
    body += _math("∞", (left - 14, axis_y + 9), anchor="end")
    body += _math("∞", (right + 14, axis_y + 9), anchor="start")
    body += _math("−1", (mid - unit, axis_y + 38), size=SMALL_PX + 2)
    body += _math("0", (mid, axis_y + 38), size=SMALL_PX + 2)
    body += _math("+1", (mid + unit, axis_y + 38), size=SMALL_PX + 2)
    body += _frac("−", (mid - xs["far"] + 6, axis_y + 38))
    body += _frac("+", (mid + xs["far"] + 6, axis_y + 38))
    return _svg(*size, body)


def fig_38() -> str:
    """The two-sheeted surface cut open: the period rectangle of sn, the two positive half-sheets hatched."""
    x0, y0, x1, y1 = _rect_box()
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2

    def shaded(x: float, y: float) -> bool:
        upper_left = x0 < x < xm - 1 and y0 < y < ym - 1
        lower_right = xm + 1 < x < x1 and ym + 1 < y < y1
        return upper_left or lower_right

    body = _hatch(shaded, _rect_box())
    body += _rect_outline(LIGHT)
    body += _stroke(
        [_d([(x0, y0), (x0, y1)]), _d([(xm, y0), (xm, y1)]), _d([(x1, y0), (x1, y1)])],
        HEAVY,
    )
    body += _stroke([_d([(x0, ym), (x1, ym)])], LIGHT)
    body += _rect_ticks()
    body += _stroke([_tick((x0 + RECT_W * j / 4, ym), 6) for j in (1, 3)], LIGHT)
    body += _rect_labels()
    body += _math("0", (x0 + RECT_W / 4, ym + 30), size=SMALL_PX)
    body += _math("0", (x0 + 3 * RECT_W / 4, ym + 30), size=SMALL_PX)
    body += _math("+1", (xm - 4, ym + 30), anchor="end", size=SMALL_PX)
    return _svg(*RECT_SIZE, body)


def fig_39() -> str:
    """The same surface on the anchor ring seen from above: the upper half hatched, branch-lines heavy."""
    centre = (250.0, 222.0)
    outer, inner = RING_OUTER, _ring_inner()
    cx, cy = centre

    def shaded(x: float, y: float) -> bool:
        r = math.hypot(x - cx, y - cy)
        return y < cy - 1 and inner + 0.8 < r < outer - 0.8

    body = _hatch(shaded, (cx - outer, cy - outer, cx + outer, cy))
    body += _stroke([_circle(centre, outer), _circle(centre, inner)], LIGHT)
    body += _stroke(
        [
            _d([(cx - outer, cy), (cx - inner, cy)]),
            _d([(cx + inner, cy), (cx + outer, cy)]),
        ],
        HEAVY,
    )
    body += _stroke(
        [
            _tick((cx, cy - outer)),
            _tick((cx, cy + outer)),
            _tick((cx, cy - inner)),
            _tick((cx, cy + inner)),
        ],
        LIGHT,
    )
    body += _math("∞", (cx, cy - outer - 14))
    body += _math("∞", (cx, cy + outer + 34))
    body += _math("0", (cx, cy - inner + 30), size=SMALL_PX)
    body += _math("0", (cx, cy + inner - 14), size=SMALL_PX)
    body += _math("−1", (cx - inner + 8, cy - 8), anchor="start", size=SMALL_PX)
    body += _math("+1", (cx + inner - 8, cy - 8), anchor="end", size=SMALL_PX)
    body += _frac("−", (cx - outer - 26, cy + 4))
    body += _frac("+", (cx + outer + 34, cy + 4))
    return _svg(cx * 2, 440, body)


def fig_40() -> str:
    """The curves x = const. of the two-sheeted surface on the rectangle: they cross at ±1 and run into the points ∞."""
    lines = _level_set(X_LEVELS, np.real, -K1)
    body = _curves(lines, _rect_px, FINE + 0.2)
    body += _rect_outline(LIGHT)
    body += _rect_labels()
    xm, ym = _rect_px(CENTRE)
    body += _math("+", (xm - 8, ym + 9), anchor="end", size=SMALL_PX)
    body += _math("1", (xm + 8, ym + 9), anchor="start", size=SMALL_PX)
    return _svg(*RECT_SIZE, body)


def fig_41() -> str:
    """The curves y = const. on the rectangle, as stream-lines flowing toward increasing x."""
    lines = _level_set(Y_LEVELS, np.imag, -K1)
    runs = _real_runs([-K1, 0.0, K1])
    body = _curves(lines, _rect_px, LIGHT, arrows=True, shortest=60)
    body += _curves(runs, _rect_px, LIGHT, arrows=True, shortest=60)
    body += _rect_labels()
    xm, ym = _rect_px(CENTRE)
    body += _math("+1", (xm - 6, ym + 28), anchor="end", size=SMALL_PX - 2)
    return _svg(*RECT_SIZE, body)


def _ring_frame(centre: Point) -> tuple[Mapper, str]:
    to_px = _ring_px_for(centre)
    cx, cy = centre
    inner = _ring_inner()
    labels = _math("∞", (cx, cy - RING_OUTER - 14)) + _math(
        "∞", (cx, cy + RING_OUTER + 34)
    )
    labels += _math("0", (cx, cy - inner + 28), size=SMALL_PX - 2)
    labels += _math("0", (cx, cy + inner - 12), size=SMALL_PX - 2)
    labels += _math("−1", (cx - inner + 8, cy + 8), anchor="start", size=SMALL_PX - 2)
    labels += _math("+1", (cx + inner - 8, cy + 8), anchor="end", size=SMALL_PX - 2)
    labels += _frac("−", (cx - RING_OUTER - 26, cy + 4))
    labels += _frac("+", (cx + RING_OUTER + 34, cy + 4))
    return to_px, labels


def fig_42() -> str:
    """The curves x = const. on the annulus: cross-points at ±1 and ±1/κ, simple infinities at the two points ∞."""
    centre = (250.0, 222.0)
    to_px, labels = _ring_frame(centre)
    lines = _level_set(X_LEVELS, np.real, 0.0)
    body = _curves(lines, to_px, FINE + 0.2)
    body += _stroke(
        [_circle(centre, RING_OUTER), _circle(centre, _ring_inner())], LIGHT
    )
    return _svg(centre[0] * 2, 440, body + labels)


def fig_43() -> str:
    """The curves y = const. on the annulus, as stream-lines; the rims and the branch-lines carry the flow too."""
    centre = (250.0, 222.0)
    to_px, labels = _ring_frame(centre)
    lines = _level_set(RING_Y_LEVELS, np.imag, 0.0)
    runs = _real_runs([0.0, K1])
    runs = [r for r in runs if not all(abs(w.real - 3 * K) < 1e-9 for w in r)]
    body = _curves(lines, to_px, LIGHT, arrows=True, shortest=60)
    body += _curves(runs, to_px, LIGHT, arrows=True, shortest=60)
    return _svg(centre[0] * 2, 440, body + labels)


FIGURES: dict[str, Callable[[], str]] = {
    "35": fig_35,
    "36": fig_36,
    "37": fig_37,
    "38": fig_38,
    "39": fig_39,
    "40": fig_40,
    "41": fig_41,
    "42": fig_42,
    "43": fig_43,
}
