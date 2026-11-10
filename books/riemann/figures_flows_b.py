"""Klein's streamings on the anchor-ring with points m and n (Figs. 27-32), and the circles u = u0, v = v0 (Fig. 33).

Figs. 27-32 are qualitative sketches, so each stream-line is a smooth spline fitted to points read off the scan
crop, in crop pixels. Fig. 33 draws two circles fitted to the scan and marks their computed intersection."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .figures import (
    HEAVY,
    INK,
    LABEL_PX,
    Point,
    _arrowhead,
    _d,
    _label,
    _stroke,
    _svg,
)


@dataclass(frozen=True)
class Line:
    """A stream-line through `points`, in flow order, with arrowheads at the points nearest `arrows`."""

    points: list[Point]
    arrows: tuple[Point, ...] = ()


def _spline(knots: Sequence[Point], steps: int = 14) -> list[Point]:
    """A centripetal Catmull-Rom curve through `knots`."""
    if len(knots) == 2:
        (x0, y0), (x1, y1) = knots
        return [(x0 + (x1 - x0) * k / 40, y0 + (y1 - y0) * k / 40) for k in range(41)]
    ends = [
        (2 * knots[0][0] - knots[1][0], 2 * knots[0][1] - knots[1][1]),
        (2 * knots[-1][0] - knots[-2][0], 2 * knots[-1][1] - knots[-2][1]),
    ]
    pts = [ends[0], *knots, ends[1]]
    out: list[Point] = [knots[0]]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        t1 = math.dist(p0, p1) ** 0.5 or 1e-6
        t2 = t1 + (math.dist(p1, p2) ** 0.5 or 1e-6)
        t3 = t2 + (math.dist(p2, p3) ** 0.5 or 1e-6)
        for s in range(1, steps + 1):
            t = t1 + (t2 - t1) * s / steps
            times = (0.0, t1, t2, t3, t)
            out.append(
                (
                    _catmull(p0, p1, p2, p3, *times, 0),
                    _catmull(p0, p1, p2, p3, *times, 1),
                )
            )
    return out


def _catmull(
    p0: Point,
    p1: Point,
    p2: Point,
    p3: Point,
    t0: float,
    t1: float,
    t2: float,
    t3: float,
    t: float,
    axis: int,
) -> float:
    a1 = ((t1 - t) * p0[axis] + (t - t0) * p1[axis]) / (t1 - t0)
    a2 = ((t2 - t) * p1[axis] + (t - t1) * p2[axis]) / (t2 - t1)
    a3 = ((t3 - t) * p2[axis] + (t - t2) * p3[axis]) / (t3 - t2)
    b1 = ((t2 - t) * a1 + (t - t0) * a2) / (t2 - t0)
    b2 = ((t3 - t) * a2 + (t - t1) * a3) / (t3 - t1)
    return ((t2 - t) * b1 + (t - t1) * b2) / (t2 - t1)


def _arc(
    centre: Point, rx: float, ry: float, start: float, stop: float, n: int = 96
) -> list[Point]:
    """An elliptic arc from angle `start` to `stop` in degrees, counter-clockwise on the page for stop > start."""
    return [
        (
            centre[0] + rx * math.cos(math.radians(start + (stop - start) * k / n)),
            centre[1] - ry * math.sin(math.radians(start + (stop - start) * k / n)),
        )
        for k in range(n + 1)
    ]


def _line(knots: Sequence[Point], *arrows: Point) -> Line:
    return Line(_spline(knots), arrows)


def _mirrored(lines: Sequence[Line], axis: float) -> list[Line]:
    """Each line together with its reflection in the horizontal y = axis."""
    flip = [
        Line(
            [(x, 2 * axis - y) for x, y in line.points],
            tuple((x, 2 * axis - y) for x, y in line.arrows),
        )
        for line in lines
    ]
    return [*lines, *flip]


def _arrow_on(points: Sequence[Point], near: Point) -> str:
    i = min(range(len(points)), key=lambda j: math.dist(points[j], near))
    a, b = points[max(i - 2, 0)], points[min(i + 2, len(points) - 1)]
    return _arrowhead(points[i], math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


def _picture(
    size: Point,
    lines: Sequence[Line],
    labels: Sequence[tuple[str, Point]] = (),
    dots: Sequence[Point] = (),
) -> str:
    """Draw `lines`, given in crop pixels of a crop of `size`, scaled to a viewBox HEIGHT pixels high."""
    scale = HEIGHT / size[1]

    def at(p: Point) -> Point:
        return p[0] * scale, p[1] * scale

    paths = [_d([at(p) for p in line.points]) for line in lines]
    heads = "".join(
        _arrow_on([at(p) for p in line.points], at(near))
        for line in lines
        for near in line.arrows
    )
    marks = "".join(
        f'<circle cx="{at(p)[0]:.2f}" cy="{at(p)[1]:.2f}" r="4" fill="{INK}"/>'
        for p in dots
    )
    text = "".join(_label(t, at(p)) for t, p in labels)
    return _svg(
        round(size[0] * scale), HEIGHT, _stroke(paths, HEAVY) + heads + marks + text
    )


HEIGHT = 440
RING = (206.0, 207.0)


def _ring(
    rx: float = 186, ry: float = 188, hole: float = 94, centre: Point = RING
) -> list[Line]:
    """The outline of the anchor-ring seen from above and the outline of its hole."""
    return [
        Line(_arc(centre, rx, ry, 0, 360, 240)),
        Line(_arc(centre, hole, hole, 0, 360, 160)),
    ]


def fig_29() -> str:
    """Vortex-points m and n of equal and opposite intensity on the anchor-ring, two cross-points on the right."""
    cx, cy = RING
    upper = [
        _line(
            [
                (64, 86),
                (72, 79),
                (82, 71),
                (94, 61),
                (103, 54),
                (107, 51),
                (109, 54),
                (105, 60),
                (96, 68),
                (86, 77),
                (76, 88),
                (66, 98),
                (52, 100),
            ],
            (82, 71),
        ),
        _line(
            [
                (44, 119),
                (56, 119),
                (72, 110),
                (88, 93),
                (104, 76),
                (124, 64),
                (152, 54),
                (180, 47),
                (200, 41),
                (207, 32),
                (208, 19),
            ],
            (93, 87),
        ),
        _line(
            [
                (35, 137),
                (50, 138),
                (70, 130),
                (90, 112),
                (110, 92),
                (138, 74),
                (170, 63),
                *_arc((cx, cy), 146, 146, 92, 0, 40),
            ],
            (140, 75),
            (305, 99),
        ),
        _line(
            [
                (22, 172),
                (45, 174),
                (70, 167),
                (95, 149),
                (120, 128),
                (146, 108),
                (170, 97),
                (190, 97),
                (202, 103),
                (207, 113),
            ],
            (101, 145),
        ),
        _line([(20, cy), (cx - 94, cy)], (62, cy)),
        _line([(cx + 146, cy), (cx + 94, cy)], (328, cy)),
        _line([(cx + 146, cy), (cx + 186, cy)], (373, cy)),
    ]
    labels = [("m", (30, 92)), ("n", (30, 336))]
    return _picture(
        (412, 413),
        [*_ring(), *_mirrored(upper, cy)],
        labels,
        dots=[(64, 86), (64, 328)],
    )


def fig_31() -> str:
    """m and n run together into one algebraic infinity on the outline; the cross-points stay on the right."""
    cx, cy = RING
    p = (20.0, cy)
    upper = [
        _line([p, (36, 165), (43, 136), (49, 112)], (47, 128)),
        _line(
            [
                p,
                (40, 182),
                (60, 135),
                (80, 93),
                (100, 70),
                (122, 55),
                (150, 45),
                (184, 37),
                (200, 32),
                (207, 24),
                (208, 19),
            ],
            (96, 80),
        ),
        _line(
            [
                p,
                (52, 185),
                (75, 151),
                (97, 119),
                (122, 93),
                (155, 72),
                *_arc((cx, cy), 145, 145, 98, 0, 40),
            ],
            (155, 71),
        ),
        _line(
            [
                p,
                (45, 196),
                (75, 183),
                (97, 162),
                (112, 141),
                (130, 121),
                (152, 106),
                (176, 97),
                (198, 97),
                (208, 102),
                (213, 113),
            ],
            (110, 142),
        ),
        _line([p, (cx - 94, cy)], (86, cy)),
        _line([(cx + 145, cy), (cx + 94, cy)], (320, cy)),
        _line([(cx + 145, cy), (cx + 185, cy)], (378, cy)),
    ]
    return _picture((414, 414), [*_ring(185, 188), *_mirrored(upper, cy)])


def _through_axis(upper: Sequence[Point], axis: float, *arrows: Point) -> Line:
    """A line that crosses y = axis at upper[0], made of `upper` and its reflection, flowing from the reflection."""
    lower = [(x, 2 * axis - y) for x, y in reversed(upper)]
    flipped = tuple((x, 2 * axis - y) for x, y in arrows)
    return Line(_spline([*lower, *upper[1:]]), (*arrows, *flipped))


def fig_30() -> str:
    """Sources m and n of equal and opposite strength on the anchor-ring; all but one stream-line touch the outline at m and n."""
    axis, centre = 206.0, (214.0, 207.0)
    m = (70.0, 82.0)
    rx, ry = 190.0, 188.0
    hole = _arc(centre, 95, 95, 180, -180, 200)
    lines = [
        Line(_arc(centre, rx, ry, 220.5, 138.5, 60), ((24, 205),)),
        Line(
            _arc(centre, rx, ry, -139.5, 138.5, 200),
            ((404, 205), (342, 66), (327, 346)),
        ),
        Line(hole, ((119, 205), (309, 205))),
        _through_axis(
            [(44, axis), (46, 180), (50, 160), (58, 140), (66, 120), (70, 104), m],
            axis,
            (44, axis),
        ),
        _through_axis(
            [
                (62, axis),
                (64, 180),
                (70, 160),
                (78, 140),
                (85, 121),
                (88, 108),
                (85, 95),
                (79, 87),
                m,
            ],
            axis,
            (62, axis),
            (87, 112),
        ),
        _through_axis(
            [
                (78, axis),
                (82, 180),
                (88, 160),
                (100, 140),
                (115, 120),
                (124, 108),
                (132, 96),
                (138, 84),
                (139, 73),
                (135, 66),
                (127, 63),
                (116, 63),
                (104, 66),
                (92, 70),
                (81, 76),
                m,
            ],
            axis,
            (78, axis),
            (139, 74),
        ),
        _through_axis(
            [
                (95, axis),
                (98, 180),
                (104, 160),
                (116, 140),
                (135, 120),
                (150, 109),
                (170, 99),
                (200, 91),
                (222, 88),
                (242, 83),
                (254, 76),
                (259, 65),
                (255, 53),
                (245, 45),
                (225, 39),
                (200, 38),
                (178, 40),
                (158, 43),
                (138, 48),
                (118, 55),
                (98, 64),
                (84, 73),
                m,
            ],
            axis,
            (95, axis),
            (259, 62),
        ),
        _through_axis(
            [
                (106, axis),
                (109, 180),
                (117, 160),
                (130, 140),
                (150, 121),
                (172, 109),
                (200, 102),
                (240, 104),
                (275, 119),
                (298, 139),
                (315, 159),
                (332, 180),
                (358, axis),
            ],
            axis,
            (106, axis),
            (307, 148),
        ),
    ]
    upper_lane = [
        (358, axis),
        (374, 191),
        (381, 175),
        (381, 158),
        (376, 140),
        (367, 120),
        (352, 100),
        (336, 82),
        (320, 66),
        (300, 52),
        (280, 42),
        (260, 34),
        (240, 30),
        (220, 27),
        (200, 28),
        (180, 30),
        (160, 34),
        (140, 40),
        (120, 48),
        (100, 60),
        (84, 71),
        m,
    ]
    lower_lane = [(x, 2 * axis - y) for x, y in reversed(upper_lane)]
    lines += [
        Line(_spline(upper_lane), ((352, 98),)),
        Line(_spline(lower_lane), ((342, 312),)),
    ]
    labels = [("m", (46, 88)), ("n", (46, 341))]
    return _picture((428, 415), lines, labels)


def fig_32() -> str:
    """m and n of Fig. 30 run together at p on the outline; the cross-points stay on the right."""
    axis, centre = 209.0, (212.0, 209.0)
    p = (22.0, axis)
    lines = [
        Line(_arc(centre, 189, 189, 180, 540, 300), ((401, 209), (338, 60))),
        Line(
            _arc(centre, 95, 95, 180, -180, 200),
            ((117, 209), (307, 209), (212, 114), (212, 304)),
        ),
        _through_axis(
            [(41, axis), (43, 193), (40, 180), (31, 181), p], axis, (41, axis)
        ),
        _through_axis(
            [
                (56, axis),
                (58, 190),
                (62, 172),
                (68, 152),
                (72, 139),
                (71, 130),
                (65, 128),
                (57, 133),
                (48, 145),
                (40, 160),
                (33, 177),
                (27, 193),
                p,
            ],
            axis,
            (56, axis),
            (72, 137),
        ),
        _through_axis(
            [
                (74, axis),
                (77, 180),
                (83, 160),
                (95, 140),
                (108, 121),
                (116, 109),
                (122, 98),
                (125, 88),
                (123, 80),
                (116, 77),
                (106, 78),
                (94, 84),
                (81, 95),
                (67, 113),
                (54, 132),
                (43, 152),
                (34, 172),
                (27, 191),
                p,
            ],
            axis,
            (74, axis),
            (125, 86),
        ),
        _through_axis(
            [
                (92, axis),
                (94, 180),
                (101, 160),
                (112, 140),
                (130, 120),
                (143, 110),
                (158, 100),
                (178, 90),
                (200, 84),
                (222, 80),
                (240, 75),
                (250, 67),
                (252, 57),
                (246, 47),
                (235, 41),
                (218, 36),
                (200, 35),
                (180, 37),
                (160, 41),
                (140, 48),
                (120, 58),
                (100, 72),
                (80, 90),
                (62, 115),
                (47, 142),
                (35, 170),
                (27, 192),
                p,
            ],
            axis,
            (92, axis),
            (252, 60),
        ),
        _through_axis(
            [
                (106, axis),
                (108, 180),
                (116, 160),
                (129, 140),
                (151, 120),
                (171, 110),
                (200, 102),
                (225, 103),
                (250, 110),
                (275, 123),
                (298, 144),
                (316, 163),
                (332, 181),
                (346, 197),
                (355, axis),
            ],
            axis,
            (106, axis),
            (320, 168),
        ),
    ]
    upper_lane = [
        (355, axis),
        (366, 196),
        (373, 180),
        (375, 160),
        (372, 140),
        (362, 120),
        (348, 100),
        (330, 80),
        (304, 60),
        (280, 46),
        (260, 37),
        (240, 31),
        (220, 28),
        (200, 27),
        (180, 28),
        (160, 33),
        (140, 40),
        (120, 50),
        (100, 62),
        (80, 79),
        (60, 106),
        (45, 135),
        (33, 165),
        (26, 190),
        p,
    ]
    lower_lane = [(x, 2 * axis - y) for x, y in reversed(upper_lane)]
    lines += [
        Line(_spline(upper_lane), ((374, 165),)),
        Line(_spline(lower_lane), ((374, 253), (330, 352))),
    ]
    return _picture((423, 417), lines)


def _oval(
    centre: Point, a: float, b: float, start: float = 0, stop: float = 360, n: int = 240
) -> list[Point]:
    """An arc of the superellipse |x/a|^2.3 + |y/b|^2.3 = 1 that fits the boxy outline of the p = 2 surface."""
    power = 2 / 2.3
    out: list[Point] = []
    for k in range(n + 1):
        t = math.radians(start + (stop - start) * k / n)
        c, s = math.cos(t), math.sin(t)
        out.append(
            (
                centre[0] + a * math.copysign(abs(c) ** power, c),
                centre[1] - b * math.copysign(abs(s) ** power, s),
            )
        )
    return out


def _loop(upper: Sequence[Point], axis: float, *arrows: Point) -> Line:
    """A closed stream-line made of `upper`, in flow order between two points on y = axis, and its reflection
    traversed back, so that the flow on the lower half runs opposite to the flow on the upper half."""
    lower = [(x, 2 * axis - y) for x, y in reversed(upper)]
    flipped = tuple((x, 2 * axis - y) for x, y in arrows)
    return Line(_spline([*upper, *lower[1:]]), (*arrows, *flipped))


def fig_27() -> str:
    """The streaming of Fig. 23 on the p = 2 surface, its left handle drawn together into a narrow bean."""
    axis, hole = 206.0, (308.0, 206.0)
    bean = [
        (55, axis),
        (57, 177),
        (66, 150),
        (85, 120),
        (110, 94),
        (132, 82),
        (146, 79),
        (155, 84),
        (157, 95),
        (150, 110),
        (140, 128),
        (132, 155),
        (128, 180),
        (126, axis),
    ]
    upper = [
        _line([(55, axis), (9, axis)], (30, axis)),
        _line([(60, 168), (48, 153), (38, 141), (28, 131)], (44, 149)),
        _line([(81, 121), (75, 108), (71, 94), (63, 78)], (72, 99)),
        _line([(116, 89), (116, 75), (121, 60), (130, 44), (134, 32)], (120, 63)),
        _line([(126, axis), (hole[0] - 99, axis)], (161, axis)),
        _line(
            [
                (130, 168),
                (150, 172),
                (175, 167),
                (200, 152),
                (225, 133),
                (243, 121),
                (255, 118),
                (261, 121),
            ],
            (176, 167),
        ),
        _line(
            [
                (145, 124),
                (162, 127),
                (182, 122),
                (205, 108),
                (228, 93),
                (250, 80),
                (275, 70),
                (300, 65),
                (335, 65),
                (362, 70),
                (385, 81),
                (405, 97),
                (424, 120),
                (440, 148),
                (449, 177),
                (452, axis),
            ],
            (245, 84),
            (408, 102),
        ),
        _line(
            [
                (155, 91),
                (176, 90),
                (200, 82),
                (225, 68),
                (252, 51),
                (275, 40),
                (300, 34),
                (330, 34),
                (345, 33),
                (352, 27),
                (353, 21),
            ],
            (252, 51),
        ),
        _line(
            [
                (148, 79),
                (162, 69),
                (184, 56),
                (205, 46),
                (220, 38),
                (227, 30),
                (228, 22),
            ],
            (187, 54),
        ),
        _line([(452, axis), (hole[0] + 99, axis)], (430, axis)),
        _line([(452, axis), (491, axis)], (473, axis)),
    ]
    outline = [
        Line(_oval((250, axis), 241, 186)),
        Line(_arc(hole, 99, 99, 0, 360, 160)),
        Line(_spline([*bean, *[(x, 2 * axis - y) for x, y in reversed(bean[:-1])]])),
    ]
    return _picture((511, 411), [*outline, *_mirrored(upper, axis)])


def fig_28() -> str:
    """The streaming of Fig. 24 on the p = 2 surface, its left handle drawn together; every stream-line closes."""
    axis, cross = 205.0, (460.0, 205.0)
    lines = [
        Line(
            _oval((263.5, axis), 240, 185),
            ((503, 205), (400, 40), (24, 205), (155, 384)),
        ),
        Line(_arc((318, 206), 100, 100, 180, -180, 200), ((218, 205), (418, 196))),
        _loop(
            [
                cross,
                (468, 190),
                (474, 175),
                (476, 160),
                (474, 140),
                (466, 120),
                (455, 100),
                (441, 80),
                (420, 61),
                (400, 48),
                (380, 40),
                (360, 34),
                (340, 31),
                (300, 30),
                (260, 31),
                (220, 29),
                (200, 28),
                (180, 29),
                (160, 33),
                (140, 40),
                (120, 50),
                (100, 64),
                (80, 82),
                (60, 106),
                (52, 120),
                (43, 140),
                (37, 160),
                (33, 180),
                (32, axis),
            ],
            axis,
            (476, 163),
            (350, 32),
            (132, 43),
        ),
        _loop(
            [
                (201, axis),
                (203, 180),
                (210, 160),
                (220, 140),
                (237, 120),
                (260, 102),
                (280, 93),
                (300, 88),
                (320, 86),
                (340, 88),
                (360, 94),
                (380, 103),
                (402, 120),
                (420, 140),
                (431, 160),
                (441, 180),
                (450, 194),
                cross,
            ],
            axis,
            (201, axis),
            (340, 88),
            (433, 165),
        ),
        _loop(
            [
                (185, axis),
                (186, 180),
                (192, 160),
                (201, 140),
                (214, 120),
                (230, 102),
                (245, 91),
                (262, 81),
                (282, 74),
                (302, 69),
                (316, 63),
                (323, 55),
                (321, 47),
                (310, 43),
                (290, 43),
                (260, 46),
                (220, 46),
                (180, 46),
                (160, 48),
                (140, 54),
                (120, 63),
                (100, 78),
                (80, 99),
                (65, 125),
                (54, 145),
                (47, 165),
                (44, 185),
                (42, axis),
            ],
            axis,
            (185, axis),
            (323, 58),
        ),
        _loop(
            [
                (169, axis),
                (171, 180),
                (176, 160),
                (184, 140),
                (193, 120),
                (204, 100),
                (211, 86),
                (213, 74),
                (208, 64),
                (198, 58),
                (180, 56),
                (160, 60),
                (140, 66),
                (120, 78),
                (100, 95),
                (82, 117),
                (69, 140),
                (61, 160),
                (56, 180),
                (54, axis),
            ],
            axis,
            (169, axis),
            (213, 76),
        ),
        _loop(
            [
                (150, axis),
                (152, 180),
                (156, 160),
                (164, 140),
                (173, 120),
                (181, 101),
                (185, 86),
                (183, 75),
                (176, 68),
                (164, 68),
                (150, 71),
                (135, 79),
                (120, 89),
                (106, 101),
                (90, 120),
                (78, 140),
                (70, 160),
                (65, 180),
                (62, axis),
            ],
            axis,
            (150, axis),
            (184, 80),
        ),
        _loop(
            [
                (133, axis),
                (134, 180),
                (138, 160),
                (144, 140),
                (153, 120),
                (162, 104),
                (168, 93),
                (167, 85),
                (160, 81),
                (150, 81),
                (138, 86),
                (120, 99),
                (100, 120),
                (88, 140),
                (79, 160),
                (74, 180),
                (72, axis),
            ],
            axis,
            (133, axis),
            (72, axis),
        ),
    ]
    return _picture((526, 410), lines)


def _turned(text: str, at: Point, degrees: float) -> str:
    return f'<g transform="rotate({degrees:.1f} {at[0]:.1f} {at[1]:.1f})">{_label(text, at)}</g>'


def _sub(base: str) -> str:
    """`base = base0`, the subscript set upright and smaller, as the scan prints it."""
    return f'{base} = {base}<tspan dy="7" font-size="{LABEL_PX * 0.7:g}" font-style="normal">0</tspan>'


def fig_33() -> str:
    """The circles u = u0 and v = v0, which meet at the point at infinity and once more."""
    scale = HEIGHT / 318
    left, r_left = (158.0, 158.0), 140.0
    right, r_right = (343.0, 160.0), 130.0

    def at(x: float, y: float) -> Point:
        return x * scale, y * scale

    dx, dy = right[0] - left[0], right[1] - left[1]
    d = math.hypot(dx, dy)
    along = (d * d + r_left**2 - r_right**2) / (2 * d)
    across = math.sqrt(r_left**2 - along**2)
    infinity = at(
        left[0] + (along * dx + across * dy) / d,
        left[1] + (along * dy - across * dx) / d,
    )
    circles = [
        _d([at(*p) for p in _arc(left, r_left, r_left, 0, 360, 240)]),
        _d([at(*p) for p in _arc(right, r_right, r_right, 0, 360, 240)]),
    ]
    tilt = 128.0
    u_at = at(
        left[0] + 112 * math.cos(math.radians(tilt)),
        left[1] - 112 * math.sin(math.radians(tilt)),
    )
    body = (
        _stroke(circles, HEAVY)
        + f'<circle cx="{infinity[0]:.2f}" cy="{infinity[1]:.2f}" r="5.5" fill="{INK}"/>'
        + _label("∞", (infinity[0] + 4, infinity[1] - 16))
        + _turned(_sub("u"), u_at, 90 - tilt)
        + _turned(_sub("v"), at(457, 160), -90)
    )
    return _svg(round(491 * scale), HEIGHT, body)


FIGURES: dict[str, Callable[[], str]] = {
    "27": fig_27,
    "28": fig_28,
    "29": fig_29,
    "30": fig_30,
    "31": fig_31,
    "32": fig_32,
    "33": fig_33,
}
