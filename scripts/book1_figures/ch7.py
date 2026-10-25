from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from html import escape

from scripts.book2_figures.engine import (
    FONT_STACK,
    SANS_STACK,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    get_palette,
    render_figure_svg,
)


def _years(first: int, last: int) -> list[float]:
    return [float(y) for y in range(first, last + 1)]


def _fixed_ticks(lo: float, hi: float, step: float, digits: int) -> list[float | tuple[float, str]]:
    n = round((hi - lo) / step)
    return [(lo + step * i, f"{lo + step * i:.{digits}f}") for i in range(n + 1)]


def _fig_7_1(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2006)
    total = [11706, 11790, 11873, 11954, 12031, 12105, 12166, 12224, 12275, 12321, 12361, 12410, 12457, 12494,
             12527, 12557, 12586, 12616, 12647, 12667, 12693, 12732, 12749, 12769, 12779, 12777, 12805]
    working1 = [9040, 9090, 9220, 9350, 9480, 9610, 9740, 9870, 10000, 10120, 10240, 10340, 10450, 10540,
                10630, 10710, 10800, 10880, 10940, 10990, 11040, 11110, 11160, 11210, 11250, 11290, 11320]
    working2 = [7920, 7950, 8030, 8120, 8210, 8290, 8370, 8450, 8520, 8590, 8640, 8680, 8700, 8690,
                8690, 8730, 8740, 8690, 8690, 8680, 8640, 8610, 8570, 8540, 8510, 8450, 8370]
    labour = [5650, 5707, 5774, 5889, 5927, 5963, 6020, 6084, 6166, 6270, 6384, 6505, 6578, 6615,
              6645, 6666, 6711, 6787, 6793, 6779, 6766, 6752, 6689, 6666, 6642, 6650, 6657]
    employed = [5536, 5581, 5638, 5733, 5766, 5807, 5853, 5911, 6011, 6128, 6249, 6369, 6436, 6450,
                6453, 6457, 6486, 6557, 6514, 6462, 6446, 6412, 6330, 6316, 6329, 6356, 6382]
    panel = PanelSpec(
        xlim=(1979.5, 2006.5),
        ylim=(5000.0, 13000.0),
        xticks=[float(y) for y in range(1980, 2007, 2)],
        yticks=[float(v) for v in range(5000, 13001, 1000)],
        xlabel="年",
        ylabel="万人",
        lines=[
            LineSeries(x=years, y=total, label="总人口", color_idx=0, width=1.6),
            LineSeries(x=years, y=working1, label="劳动年龄人口1", color_idx=0, style="dashed", width=1.6),
            LineSeries(x=years, y=working2, label="劳动年龄人口2", color_idx=0, style="dotted", width=1.6),
            LineSeries(x=years, y=labour, label="劳动人口", color_idx=4, marker="square", width=1.6, fixed_style=True),
            LineSeries(x=years, y=employed, label="就业人数", color_idx=3, marker="triangle", width=1.6, fixed_style=True),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="7-1", title="图 7-1 总人口、劳动年龄人口、劳动人口和就业人数", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


AGE_GROUPS = ["15~19岁", "20~24岁", "25~29岁", "30~34岁", "35~39岁", "40~44岁",
              "45~49岁", "50~54岁", "55~59岁", "60~64岁", "65岁及以上"]
LEGEND_ORDER = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]


AGE_FILLS = ["#475569", "diag", "#64748b", "dots", "#94a3b8", "vert", "#cbd5e1", "horiz", "#e2e8f0", "bg", "fg"]


def _filled_rect(mode: ThemeMode, clip_id: str, x: float, y: float, w: float, h: float, fill: str, sw: float) -> list[str]:
    pal = get_palette(mode)
    colour = {"fg": pal.fg, "bg": pal.bg}.get(fill, fill)
    if fill.startswith("#") or fill in ("fg", "bg"):
        return [f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{colour}" stroke="{pal.fg}" stroke-width="{sw}"/>']
    marks: list[str] = []
    if fill == "horiz":
        marks = [f'<line x1="{x:.2f}" y1="{y + d:.2f}" x2="{x + w:.2f}" y2="{y + d:.2f}"/>' for d in _steps(1.75, 3.5, h)]
    elif fill == "vert":
        marks = [f'<line x1="{x + d:.2f}" y1="{y:.2f}" x2="{x + d:.2f}" y2="{y + h:.2f}"/>' for d in _steps(1.75, 3.5, w)]
    elif fill == "diag":
        for d in _steps(0.0, 3.6, w + h):
            u0, u1 = max(0.0, h - d), min(h, h - d + w)
            if u1 > u0:
                marks.append(
                    f'<line x1="{x + d - h + u0:.2f}" y1="{y + u0:.2f}" x2="{x + d - h + u1:.2f}" y2="{y + u1:.2f}"/>'
                )
    elif fill == "dots":
        marks = [
            f'<circle cx="{x + dx + (2.5 if round(dy / 4.5) % 2 else 0.0):.2f}" cy="{y + dy:.2f}" r="0.65" fill="{pal.fg}" stroke="none"/>'
            for dy in _steps(2.0, 4.5, h) for dx in _steps(1.5, 5.0, w)
        ]
    return [
        f'<clipPath id="{clip_id}"><rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}"/></clipPath>',
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{pal.bg}"/>',
        f'<g clip-path="url(#{clip_id})" stroke="{pal.fg}" stroke-width="0.8">{"".join(marks)}</g>',
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="none" stroke="{pal.fg}" stroke-width="{sw}"/>',
    ]


def _steps(start: float, step: float, limit: float) -> list[float]:
    return [start + step * i for i in range(int((limit - start) / step) + 1)]


def _stacked_panel(
    out: list[str], mode: ThemeMode, top: float, title: str, bars: Sequence[tuple[float, Sequence[float]]]
) -> float:
    pal = get_palette(mode)
    px0, pw, ph = 62.0, 420.0, 190.0
    py0 = top + 34.0
    py1 = py0 + ph
    out.append(
        f'<text x="{px0 + pw / 2:.1f}" y="{top + 14:.1f}" text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="13.5" font-weight="600" fill="{pal.fg}">{escape(title)}</text>'
    )
    out.append(
        f'<text x="{px0 - 6:.1f}" y="{py0 - 11:.1f}" text-anchor="end" font-family="{FONT_STACK}" '
        f'font-size="11" fill="{pal.muted}">万人</text>'
    )
    out.append(f'<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" fill="{pal.panel_bg}" stroke="{pal.border}"/>')

    def map_y(v: float) -> float:
        return py1 - v / 6000.0 * ph

    for v in range(0, 6001, 1000):
        yy = map_y(v)
        if v:
            out.append(
                f'<line x1="{px0}" y1="{yy:.2f}" x2="{px0 + pw}" y2="{yy:.2f}" stroke="{pal.grid}" '
                'stroke-width="0.9" stroke-dasharray="2.5,2.5"/>'
            )
        out.append(f'<line x1="{px0}" y1="{yy:.2f}" x2="{px0 + 4.5}" y2="{yy:.2f}" stroke="{pal.axis}" stroke-width="1.1"/>')
        out.append(
            f'<text x="{px0 - 6.5}" y="{yy + 3.8:.2f}" text-anchor="end" font-family="{SANS_STACK}" '
            f'font-size="10.5" fill="{pal.muted}">{v}</text>'
        )
    slot = pw / len(bars)
    for i, (year, tops) in enumerate(bars):
        cx = px0 + slot * (i + 0.5)
        bottom = tops[0]
        for k, top_v in enumerate(tops[1:]):
            y_top, y_bot = map_y(top_v), map_y(bottom)
            if top_v > bottom:
                out.extend(_filled_rect(mode, f"c72_{top:.0f}_{i}_{k}_{mode}", cx - 20, y_top, 40, y_bot - y_top, AGE_FILLS[k], 0.7))
            bottom = top_v
        if i:
            out.append(
                f'<line x1="{px0 + slot * i:.2f}" y1="{py1 - 4.5}" x2="{px0 + slot * i:.2f}" y2="{py1}" '
                f'stroke="{pal.axis}" stroke-width="1.1"/>'
            )
        out.append(
            f'<text x="{cx:.2f}" y="{py1 + 18}" text-anchor="middle" font-family="{SANS_STACK}" '
            f'font-size="10.5" fill="{pal.muted}">{year:.0f}</text>'
        )
    out.append(f'<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" fill="none" stroke="{pal.axis}" stroke-width="1.2"/>')
    out.append(
        f'<text x="{px0 + pw / 2:.1f}" y="{py1 + 34}" text-anchor="middle" font-family="{FONT_STACK}" '
        f'font-size="11.5" fill="{pal.muted}">年</text>'
    )
    leg_y = py1 + 54.0
    for n, k in enumerate(LEGEND_ORDER):
        lx = px0 + 6 + (n % 4) * 106.0
        ly = leg_y + (n // 4) * 16.0
        out.extend(_filled_rect(mode, f"l72_{top:.0f}_{k}_{mode}", lx, ly - 8.5, 16, 9, AGE_FILLS[k], 0.8))
        out.append(
            f'<text x="{lx + 21:.1f}" y="{ly:.1f}" font-family="{FONT_STACK}" font-size="10.8" fill="{pal.fg}">'
            f"{escape(AGE_GROUPS[k])}</text>"
        )
    return leg_y + 2 * 16.0 + 14.0


def _fig_7_2(mode: ThemeMode = "mono") -> str:
    pal = get_palette(mode)
    male = [
        (1980, [0, 434, 833, 1294, 1819, 2262, 2688, 3113, 3439, 3701, 3900, 4380]),
        (1985, [0, 471, 887, 1258, 1701, 2262, 2715, 3122, 3511, 3855, 4090, 4633]),
        (1990, [0, 507, 959, 1376, 1747, 2199, 2733, 3222, 3593, 3991, 4299, 4941]),
        (1995, [0, 434, 941, 1376, 1774, 2181, 2633, 3176, 3611, 4000, 4353, 5186]),
        (2000, [0, 389, 796, 1312, 1738, 2145, 2561, 2995, 3529, 3946, 4317, 5330]),
        (2005, [0, 326, 697, 1131, 1620, 2054, 2471, 2860, 3312, 3810, 4226, 5421]),
    ]
    female = [
        (1980, [0, 412, 779, 1235, 1769, 2224, 2671, 3082, 3433, 3748, 4002, 4658]),
        (1985, [0, 447, 849, 1243, 1664, 2198, 2671, 3100, 3485, 3870, 4159, 4974]),
        (1990, [0, 499, 928, 1331, 1708, 2277, 2706, 3152, 3581, 3984, 4317, 5289]),
        (1995, [0, 447, 919, 1340, 1734, 2137, 2592, 3117, 3581, 3984, 4370, 5569]),
        (2000, [0, 394, 806, 1261, 1699, 2102, 2504, 2942, 3476, 3923, 4317, 5779]),
        (2005, [350, 350, 700, 1112, 1585, 2014, 2434, 2820, 3266, 3792, 4221, 5946]),
    ]
    body: list[str] = []
    mid = _stacked_panel(body, mode, 8.0, "（1）男性", male)
    end = _stacked_panel(body, mode, mid, "（2）女性", female)
    W, H = 516, round(end)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f"<title>{escape('图 7-2 按年龄组划分的劳动年龄人口 1 的历年变化')}</title>",
        f'<rect width="{W}" height="{H}" fill="{pal.bg}"/>',
        *body,
        "</svg>",
    ]
    return "\n".join(out)


def _participation_lines(series: Sequence[Sequence[float]], oldest_width: float) -> list[LineSeries]:
    years = [1980.0, 1985.0, 1990.0, 1995.0, 2000.0, 2005.0]
    styles = [
        ("各年龄总和", 0, "dashed", None, 1.4),
        ("15~19岁", 0, "dotted", "square", 1.4),
        ("20~24岁", 1, "dotted", "triangle", 1.4),
        ("25~29岁", 2, "solid", "cross", 1.4),
        ("30~34岁", 0, "solid", None, 1.1),
        ("35~39岁", 5, "solid", "triangle", 2.6),
        ("40~44岁", 2, "solid", "square", 2.6),
        ("45~49岁", 2, "solid", "diamond", 2.6),
        ("50~54岁", 4, "solid", "square", 1.4),
        ("55~59岁", 0, "solid", "circle", 1.4),
        ("60~64岁", 1, "solid", "circle", 1.4),
        ("65岁及以上", 0, "solid", None, oldest_width),
    ]
    return [
        LineSeries(x=years, y=list(ys), label=label, color_idx=ci, style=style, marker=marker, width=w, fixed_style=True)
        for (label, ci, style, marker, w), ys in zip(styles, series)
    ]


def _fig_7_3(mode: ThemeMode = "mono") -> str:
    male = [
        [0.794, 0.775, 0.763, 0.764, 0.751, 0.718],
        [0.176, 0.170, 0.183, 0.179, 0.185, 0.161],
        [0.702, 0.702, 0.729, 0.750, 0.745, 0.705],
        [0.968, 0.966, 0.981, 0.962, 0.968, 0.958],
        [0.960, 0.955, 0.960, 0.965, 0.955, 0.955],
        [0.972, 0.970, 0.970, 0.975, 0.970, 0.958],
        [0.977, 0.975, 0.968, 0.978, 0.968, 0.962],
        [0.975, 0.970, 0.968, 0.962, 0.976, 0.958],
        [0.958, 0.950, 0.957, 0.968, 0.960, 0.960],
        [0.907, 0.900, 0.916, 0.927, 0.937, 0.915],
        [0.775, 0.717, 0.719, 0.741, 0.717, 0.688],
        [0.395, 0.348, 0.343, 0.346, 0.310, 0.269],
    ]
    female = [
        [0.469, 0.477, 0.489, 0.484, 0.475, 0.463],
        [0.181, 0.164, 0.177, 0.159, 0.167, 0.163],
        [0.697, 0.708, 0.746, 0.736, 0.739, 0.710],
        [0.490, 0.540, 0.611, 0.657, 0.703, 0.760],
        [0.474, 0.497, 0.504, 0.520, 0.555, 0.622],
        [0.578, 0.587, 0.625, 0.598, 0.602, 0.625],
        [0.640, 0.677, 0.685, 0.701, 0.688, 0.702],
        [0.640, 0.680, 0.719, 0.703, 0.724, 0.736],
        [0.588, 0.608, 0.651, 0.670, 0.672, 0.688],
        [0.503, 0.505, 0.535, 0.562, 0.588, 0.588],
        [0.383, 0.382, 0.390, 0.393, 0.390, 0.398],
        [0.145, 0.142, 0.147, 0.138, 0.125, 0.106],
    ]
    panels = [
        PanelSpec(
            title=title,
            xlim=(1977.5, 2007.5),
            ylim=ylim,
            xticks=[1980.0, 1985.0, 1990.0, 1995.0, 2000.0, 2005.0],
            yticks=_fixed_ticks(ylim[0], ylim[1], 0.1, 1),
            xlabel="年",
            zero_line=False,
            lines=_participation_lines(series, oldest_width),
            legend_loc="bottom",
        )
        for title, ylim, series, oldest_width in [
            ("（1）男性", (0.1, 1.0), male, 1.6),
            ("（2）女性", (0.0, 0.9), female, 3.0),
        ]
    ]
    spec = FigureSpec(fig_id="7-3", title="图 7-3 按年龄组划分的劳动力参与率的历年变化", panels=panels, rows=2, width=860, height=1200)
    return render_figure_svg(spec, mode)


def _fig_7_4(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2006)
    actual = [2092, 2092, 2080, 2080, 2102, 2093, 2092, 2092, 2092, 2069, 2033, 1995, 1954, 1905,
              1905, 1905, 1913, 1897, 1875, 1836, 1848, 1839, 1836, 1846, 1839, 1823, 1839]
    scheduled = [1926, 1926, 1923, 1918, 1928, 1920, 1920, 1920, 1902, 1879, 1856, 1836, 1813, 1774,
                 1774, 1774, 1774, 1749, 1736, 1715, 1715, 1715, 1708, 1702, 1692, 1684, 1684]
    overtime = [158, 158, 153, 155, 166, 177, 172, 177, 185, 190, 182, 172, 149, 135,
                131, 137, 142, 147, 131, 131, 132, 132, 138, 143, 146, 149, 155]
    panel = PanelSpec(
        xlim=(1979.5, 2006.5),
        ylim=(1000.0, 2200.0),
        xticks=[float(y) for y in range(1980, 2007, 2)],
        yticks=[float(v) for v in range(1000, 2201, 200)],
        y2lim=(0.0, 800.0),
        y2ticks=[float(v) for v in range(0, 801, 100)],
        xlabel="年",
        ylabel="小时",
        y2label="小时",
        lines=[
            LineSeries(x=years, y=actual, label="总实际劳动时间（左轴）", color_idx=5, width=3.0, fixed_style=True),
            LineSeries(x=years, y=scheduled, label="法定劳动时间（左轴）", color_idx=2, style="dashed", width=3.0),
            LineSeries(x=years, y=overtime, label="超额劳动时间（右轴）", color_idx=0, style="dotted", width=3.2, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="7-4", title="图 7-4 总实际劳动时间、法定劳动时间和超额劳动时间", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _index_panel(title: str, hours_label: str, a: list[float], b: list[float], ab: list[float]) -> PanelSpec:
    years = _years(1980, 2006)
    return PanelSpec(
        title=title,
        xlim=(1979.5, 2006.5),
        ylim=(60.0, 120.0),
        xticks=[float(y) for y in range(1980, 2007, 2)],
        yticks=_fixed_ticks(60.0, 120.0, 10.0, 1),
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=a, label=hours_label, color_idx=5, width=3.0, fixed_style=True),
            LineSeries(x=years, y=b, label="就业指数（B）", color_idx=2, style="dashed", width=3.0),
            LineSeries(x=years, y=ab, label="劳动时间×就业人数（A×B）", color_idx=0, marker="square", width=2.6),
        ],
        legend_loc="bottom",
    )


def _fig_7_5(mode: ThemeMode = "mono") -> str:
    a1 = [113.7, 113.6, 113.6, 113.0, 114.5, 113.9, 113.0, 113.8, 113.8, 112.8, 111.5, 109.7, 107.5, 104.2,
          103.3, 103.4, 103.6, 102.7, 101.6, 100.0, 100.8, 100.3, 99.7, 99.7, 100.0, 100.0, 100.9]
    b1 = [86.8, 87.6, 88.6, 89.7, 90.5, 91.2, 91.9, 92.7, 93.9, 95.6, 97.8, 100.0, 101.4, 101.5,
          101.5, 101.5, 101.8, 102.7, 102.2, 101.2, 101.8, 101.4, 100.6, 100.5, 100.7, 100.7, 101.1]
    ab1 = [99.2, 100.0, 100.3, 102.1, 103.8, 103.8, 104.2, 105.6, 107.3, 108.0, 108.8, 109.0, 107.3, 105.1,
           104.9, 104.9, 105.8, 106.2, 104.0, 102.4, 103.3, 101.8, 99.4, 99.4, 100.3, 100.3, 101.4]
    a2 = [111.5, 112.0, 112.0, 112.0, 112.0, 112.0, 112.0, 112.0, 112.0, 111.0, 109.4, 107.6, 105.7, 103.9,
          103.9, 103.9, 103.2, 102.1, 101.2, 101.4, 102.5, 101.0, 100.4, 100.4, 100.4, 100.2, 101.0]
    b2 = [87.2, 87.8, 88.8, 89.9, 90.7, 91.4, 92.1, 92.8, 94.0, 95.7, 97.9, 100.0, 101.4, 101.5,
          101.5, 101.8, 102.0, 103.1, 102.6, 101.5, 101.9, 101.4, 100.6, 100.6, 100.7, 100.7, 101.0]
    ab2 = [96.9, 98.4, 99.4, 101.5, 101.6, 102.5, 103.1, 104.2, 106.3, 107.3, 107.2, 108.4, 106.9, 105.5,
           105.5, 106.1, 106.1, 105.6, 104.2, 103.8, 104.2, 102.6, 101.2, 100.5, 100.6, 100.1, 101.1]
    panels = [
        _index_panel("（1）劳动时间＝基于《月度劳动统计调查》", "劳动时间指数1（A）", a1, b1, ab1),
        _index_panel("（2）劳动时间＝基于《劳动力调查》", "劳动时间指数2（A）", a2, b2, ab2),
    ]
    spec = FigureSpec(fig_id="7-5", title="图 7-5 劳动时间指数、就业指数和劳动力投入指数", panels=panels, rows=2, width=860, height=1000)
    return render_figure_svg(spec, mode)


def _education_lines(junior: list[float], senior: list[float], college: list[float], university: list[float]) -> list[LineSeries]:
    years = _years(1980, 2006)
    return [
        LineSeries(x=years, y=junior, label="初中学历", color_idx=5, style="dotted", width=2.6),
        LineSeries(x=years, y=senior, label="高中学历", color_idx=2, marker="square", width=2.4, fixed_style=True),
        LineSeries(x=years, y=college, label="高等专科学校和专科大学学历", color_idx=3, style="dashdot", width=2.4),
        LineSeries(x=years, y=university, label="大学及大学以上学历", color_idx=0, width=3.0),
    ]


def _fig_7_6(mode: ThemeMode = "mono") -> str:
    data = [
        ("（1）男女合计", [
            [33.0, 31.5, 30.0, 28.6, 27.2, 25.9, 24.6, 23.3, 22.0, 20.7, 19.5, 18.3, 17.2, 16.1,
             15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 9.0, 8.3, 7.6, 6.9, 6.0, 5.7, 5.3],
            [46.7, 47.2, 47.7, 48.4, 49.4, 50.1, 50.2, 51.1, 52.1, 52.0, 52.3, 52.5, 51.9, 51.9,
             52.0, 51.7, 51.2, 51.2, 50.7, 49.9, 48.6, 48.5, 47.9, 47.9, 47.2, 46.8, 46.8],
            [5.5, 5.8, 6.1, 6.5, 6.8, 7.1, 7.4, 7.8, 8.0, 8.4, 9.0, 9.5, 10.2, 10.7,
             11.2, 11.8, 12.3, 12.4, 12.9, 13.4, 13.9, 14.3, 14.7, 15.0, 15.6, 14.6, 14.6],
            [14.6, 15.1, 15.7, 16.0, 16.3, 16.7, 17.1, 17.5, 18.0, 18.4, 18.8, 19.2, 19.5, 19.9,
             20.3, 21.0, 21.6, 22.0, 22.6, 23.2, 24.0, 25.0, 26.0, 26.5, 27.0, 29.0, 28.8],
        ]),
        ("（2）男性", [
            [32.8, 31.3, 29.8, 28.3, 26.9, 25.5, 24.2, 23.0, 21.8, 20.6, 19.5, 18.4, 17.4, 16.4,
             15.5, 14.6, 13.8, 13.0, 12.2, 11.4, 10.7, 10.0, 9.5, 9.0, 8.5, 8.4, 8.3],
            [44.2, 44.6, 45.3, 46.0, 47.0, 48.0, 48.2, 48.7, 50.0, 50.0, 50.4, 51.3, 50.8, 51.2,
             51.2, 51.4, 51.4, 51.0, 51.2, 50.4, 50.3, 49.8, 49.5, 49.0, 48.9, 48.4, 48.3],
            [3.5, 3.5, 3.5, 3.5, 3.9, 4.3, 4.6, 4.8, 5.0, 5.3, 5.5, 5.8, 6.4, 6.8,
             7.2, 7.6, 7.6, 8.3, 8.9, 9.6, 10.0, 10.3, 10.4, 10.6, 10.7, 10.3, 10.4],
            [19.7, 20.6, 21.4, 22.0, 22.8, 23.1, 23.4, 23.9, 24.4, 25.0, 25.4, 25.8, 26.8, 26.7,
             27.5, 28.2, 28.7, 29.1, 29.8, 30.6, 31.5, 32.4, 33.2, 33.9, 34.1, 36.7, 36.7],
        ]),
        ("（3）女性", [
            [33.0, 31.5, 30.0, 28.6, 27.2, 25.8, 24.4, 23.0, 21.6, 20.2, 18.8, 17.5, 16.3, 15.2,
             14.2, 13.4, 12.6, 11.8, 10.8, 9.9, 9.0, 8.3, 7.5, 6.6, 5.8, 5.8, 5.8],
            [53.4, 53.4, 54.6, 55.0, 56.0, 56.3, 56.5, 57.0, 58.0, 58.0, 57.4, 57.4, 57.0, 57.0,
             56.4, 55.6, 54.9, 54.6, 53.6, 52.8, 51.0, 50.1, 49.3, 49.6, 47.7, 48.6, 48.8],
            [10.0, 10.5, 11.3, 12.4, 13.0, 13.5, 14.6, 15.6, 16.2, 17.6, 19.0, 20.0, 21.0, 21.6,
             22.8, 24.0, 24.6, 25.6, 27.2, 28.2, 29.0, 30.4, 30.8, 31.6, 32.6, 29.8, 30.6],
            [2.8, 2.8, 3.0, 3.2, 3.4, 3.9, 4.0, 4.0, 4.5, 4.9, 5.2, 5.6, 6.1, 6.6,
             7.3, 7.7, 8.3, 8.9, 9.6, 11.1, 12.0, 12.9, 14.1, 14.4, 15.8, 17.6, 17.3],
        ]),
    ]
    panels = [
        PanelSpec(
            title=title,
            xlim=(1979.5, 2006.5),
            ylim=(0.0, 60.0),
            xticks=[float(y) for y in range(1980, 2007, 2)],
            yticks=_fixed_ticks(0.0, 60.0, 10.0, 1),
            xlabel="年",
            ylabel="%",
            lines=_education_lines(*series),
            legend_loc="bottom" if i == 2 else "none",
        )
        for i, (title, series) in enumerate(data)
    ]
    spec = FigureSpec(fig_id="7-6", title="图 7-6 按学历划分的劳动力构成比率", panels=panels, rows=3, width=860, height=1380)
    return render_figure_svg(spec, mode)


def _fig_7_7(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2006)
    data = [
        ("（1）男性", [
            [0.940, 0.940, 0.937, 0.935, 0.940, 0.940, 0.937, 0.940, 0.940, 0.937, 0.940, 0.940, 0.932, 0.940,
             0.947, 0.953, 0.957, 0.957, 0.960, 0.966, 0.966, 0.957, 0.952, 0.952, 0.950, 0.937, 0.935],
            [1.121, 1.088, 1.057, 1.043, 1.034, 1.020, 1.000, 1.085, 0.994, 0.986, 0.986, 0.983, 0.965, 0.957,
             0.946, 0.955, 0.957, 0.957, 0.960, 0.979, 0.982, 0.993, 1.010, 1.004, 1.007, 1.035, 1.054],
            [1.277, 1.272, 1.267, 1.272, 1.278, 1.288, 1.296, 1.304, 1.308, 1.311, 1.330, 1.325, 1.308, 1.308,
             1.308, 1.299, 1.316, 1.313, 1.313, 1.316, 1.322, 1.328, 1.365, 1.367, 1.379, 1.406, 1.400],
        ]),
        ("（2）女性", [
            [0.840, 0.848, 0.848, 0.850, 0.860, 0.852, 0.852, 0.862, 0.862, 0.866, 0.865, 0.856, 0.858, 0.866,
             0.868, 0.866, 0.858, 0.858, 0.876, 0.872, 0.880, 0.877, 0.882, 0.882, 0.884, 0.884, 0.888],
            [1.103, 1.110, 1.108, 1.108, 1.110, 1.111, 1.112, 1.115, 1.112, 1.115, 1.118, 1.125, 1.112, 1.115,
             1.115, 1.128, 1.138, 1.145, 1.140, 1.137, 1.137, 1.143, 1.200, 1.188, 1.188, 1.222, 1.222],
            [1.370, 1.365, 1.360, 1.346, 1.382, 1.382, 1.383, 1.383, 1.383, 1.385, 1.401, 1.398, 1.393, 1.420,
             1.388, 1.390, 1.388, 1.378, 1.380, 1.355, 1.368, 1.383, 1.408, 1.393, 1.392, 1.428, 1.428],
        ]),
    ]
    panels = [
        PanelSpec(
            title=title,
            xlim=(1979.5, 2006.5),
            ylim=(0.6, 1.6),
            xticks=[float(y) for y in range(1980, 2007, 2)],
            yticks=_fixed_ticks(0.6, 1.6, 0.2, 3),
            xlabel="年",
            ylabel="%",
            zero_line=False,
            lines=[
                LineSeries(x=years, y=junior, label="初中学历", color_idx=5, style="dashed", width=2.6),
                LineSeries(x=years, y=college, label="高等专科学校和专科大学学历", color_idx=2, style="dotted", width=2.8),
                LineSeries(x=years, y=university, label="大学及大学以上学历", color_idx=0, width=3.0),
            ],
            legend_loc="bottom" if i == 1 else "none",
        )
        for i, (title, (junior, college, university)) in enumerate(data)
    ]
    spec = FigureSpec(fig_id="7-7", title="图 7-7 按学历划分的相对工资", panels=panels, rows=2, width=860, height=1000)
    return render_figure_svg(spec, mode)


def _quality_figure(
    fig_id: str, title: str, first: int, last: int, ylim: tuple[float, float], step: float,
    total_label: str, male: list[float], female: list[float], total: list[float], mode: ThemeMode,
) -> str:
    years = _years(first, last)
    panel = PanelSpec(
        xlim=(first - 0.5, last + 0.5),
        ylim=ylim,
        xticks=[float(y) for y in range(first, min(last, 2006) + 1, 2)],
        yticks=_fixed_ticks(ylim[0], ylim[1], step, 3),
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=male, label="男性", color_idx=5, width=3.0, fixed_style=True),
            LineSeries(x=years, y=female, label="女性", color_idx=2, style="dashed", width=3.0),
            LineSeries(x=years, y=total, label=total_label, color_idx=0, marker="triangle", width=2.6),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_7_8(mode: ThemeMode = "mono") -> str:
    male = [1.000, 1.003, 1.006, 1.009, 1.012, 1.012, 1.014, 1.016, 1.017, 1.019, 1.021, 1.023, 1.027, 1.027,
            1.029, 1.031, 1.035, 1.035, 1.038, 1.041, 1.044, 1.047, 1.052, 1.054, 1.054, 1.062, 1.059]
    female = [1.000, 1.004, 1.007, 1.011, 1.016, 1.021, 1.022, 1.028, 1.031, 1.037, 1.042, 1.046, 1.051, 1.056,
              1.061, 1.066, 1.070, 1.074, 1.082, 1.089, 1.095, 1.100, 1.108, 1.111, 1.120, 1.122, 1.119]
    total = [1.000, 1.004, 1.006, 1.008, 1.013, 1.016, 1.018, 1.021, 1.024, 1.027, 1.029, 1.031, 1.035, 1.038,
             1.041, 1.044, 1.046, 1.049, 1.052, 1.057, 1.060, 1.064, 1.068, 1.070, 1.073, 1.080, 1.080]
    return _quality_figure(
        "7-8", "图 7-8 高学历化导致的劳动力质量的变化", 1980, 2006, (0.95, 1.15), 0.05, "男女合计", male, female, total, mode
    )


def _fig_7_9(mode: ThemeMode = "mono") -> str:
    male = [1.000, 1.000, 1.000, 0.9995, 0.998, 0.996, 0.996, 0.996, 0.995, 0.994, 0.997, 0.995, 0.993, 0.988,
            0.988, 0.986, 0.984, 0.981, 0.971, 0.969, 0.966, 0.961, 0.960, 0.959]
    female = [1.000, 0.990, 0.990, 0.983, 0.980, 0.977, 0.969, 0.973, 0.970, 0.968, 0.968, 0.966, 0.964, 0.957,
              0.954, 0.946, 0.941, 0.937, 0.932, 0.927, 0.924, 0.921, 0.920, 0.918]
    total = [1.000, 0.997, 0.997, 0.994, 0.991, 0.989, 0.986, 0.988, 0.985, 0.984, 0.985, 0.983, 0.981, 0.976,
             0.975, 0.970, 0.967, 0.962, 0.956, 0.952, 0.948, 0.945, 0.944, 0.942]
    return _quality_figure(
        "7-9", "图 7-9 非正式雇佣导致的劳动力质量下降", 1984, 2007, (0.86, 1.02), 0.02, "男女总和", male, female, total, mode
    )


def _fig_7_10(mode: ThemeMode = "mono") -> str:
    male = [1.000, 1.003, 1.005, 1.006, 1.007, 1.008, 1.009, 1.012, 1.014, 1.013, 1.019, 1.019, 1.022, 1.019,
            1.023, 1.024, 1.025, 1.026, 1.021, 1.021, 1.020, 1.022, 1.022]
    female = [1.000, 1.004, 1.007, 1.011, 1.014, 1.018, 1.022, 1.026, 1.031, 1.035, 1.040, 1.043, 1.048, 1.052,
              1.060, 1.066, 1.071, 1.076, 1.082, 1.085, 1.092, 1.092, 1.092]
    total = [1.000, 1.003, 1.005, 1.007, 1.009, 1.012, 1.014, 1.018, 1.020, 1.022, 1.028, 1.030, 1.033, 1.033,
             1.039, 1.042, 1.045, 1.047, 1.047, 1.049, 1.051, 1.053, 1.052]
    return _quality_figure(
        "7-10", "图 7-10 高学历化和非正式雇佣导致的劳动力质量变化", 1984, 2006, (0.98, 1.10), 0.02, "男女总和",
        male, female, total, mode,
    )


def _diagram_svg(
    mode: ThemeMode, title: str, size: tuple[float, float], scale: float,
    lines: Sequence[tuple[float, float, float, float, str]],
    paths: Sequence[str],
    texts: Sequence[tuple[float, float, str, str, str]],
    dots: Sequence[tuple[float, float]] = (),
) -> str:
    pal = get_palette(mode)
    W, H = round(size[0] * scale), round(size[1] * scale)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f"<title>{escape(title)}</title>",
        f'<rect width="{W}" height="{H}" fill="{pal.bg}"/>',
        f'<g fill="none" stroke="{pal.fg}" stroke-width="1.3" stroke-linecap="butt">',
    ]
    for x1, y1, x2, y2, kind in lines:
        x1, y1, x2, y2 = x1 * scale, y1 * scale, x2 * scale, y2 * scale
        length = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        if kind == "dash":
            for t in _steps(0.0, 9.0, length):
                t1 = min(length, t + 5.0)
                out.append(
                    f'<line x1="{x1 + ux * t:.2f}" y1="{y1 + uy * t:.2f}" x2="{x1 + ux * t1:.2f}" y2="{y1 + uy * t1:.2f}" stroke-width="1.0"/>'
                )
            continue
        tip = 7.0 if kind == "arrow" else 0.0
        out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2 - ux * tip:.2f}" y2="{y2 - uy * tip:.2f}"/>')
        if kind == "arrow":
            bx, by = x2 - ux * tip, y2 - uy * tip
            out.append(
                f'<polygon points="{x2:.2f},{y2:.2f} {bx - uy * 3.2:.2f},{by + ux * 3.2:.2f} {bx + uy * 3.2:.2f},{by - ux * 3.2:.2f}" '
                f'fill="{pal.fg}" stroke="none"/>'
            )
    out.extend(f'<path d="{d}" transform="scale({scale})" stroke-width="{1.3 / scale:.2f}"/>' for d in paths)
    out.extend(
        f'<circle cx="{x * scale:.2f}" cy="{y * scale:.2f}" r="2.6" fill="{pal.fg}" stroke="none"/>' for x, y in dots
    )
    out.append("</g>")
    for x, y, text, kind, anchor in texts:
        style = 'font-style="italic" font-size="14"' if kind == "it" else 'font-size="13"'
        body = escape(text)
        if kind == "it" and text[-1].isdigit():
            body = f'{escape(text[:-1])}<tspan font-size="9.5" font-style="normal" dy="3">{text[-1]}</tspan>'
        out.append(
            f'<text x="{x * scale:.1f}" y="{y * scale:.1f}" text-anchor="{anchor}" font-family="{FONT_STACK}" '
            f'{style} fill="{pal.fg}">{body}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def _fig_7_11(mode: ThemeMode = "mono") -> str:
    lines = [
        (37, 35, 37, 1295, ""), (37, 1295, 1560, 1295, ""),
        (418, 297, 418, 1295, ""), (680, 297, 680, 1295, ""),
        (285, 432, 930, 928, ""), (240, 655, 883, 1145, ""), (200, 847, 932, 670, ""),
        (37, 731, 680, 731, "dash"), (37, 790, 418, 790, "dash"), (37, 990, 680, 990, "dash"),
        (475, 348, 612, 348, "arrow"), (463, 878, 560, 946, "arrow"),
        (632, 912, 632, 785, "arrow"), (905, 1083, 905, 995, "arrow"),
    ]
    texts = [
        (240, 95, "熟练劳动力的", "zh", "start"), (240, 172, "相对供给曲线", "zh", "start"),
        (428, 272, "RS", "it", "middle"), (692, 272, "RS′", "it", "middle"),
        (1008, 622, "LRD", "it", "middle"), (1160, 637, "熟练劳动力长期", "zh", "start"),
        (1160, 715, "相对需求曲线", "zh", "start"), (1000, 902, "RD′", "it", "middle"),
        (945, 1210, "RD", "it", "middle"), (1055, 1132, "熟练劳动力短期", "zh", "start"),
        (1055, 1210, "相对需求曲线", "zh", "start"), (1965, 1385, "熟练劳动力／非熟练劳动力", "zh", "end"),
    ]
    return _diagram_svg(mode, "图 7-11 定向技术进步的影响", (2000, 1420), 0.27, lines, [], texts)


def _fig_7_12(mode: ThemeMode = "mono") -> str:
    lines = [
        (183, 110, 183, 1180, ""), (183, 1180, 1560, 1180, ""),
        (937, 205, 1410, 970, ""), (530, 418, 922, 1025, ""), (405, 598, 1145, 920, ""),
        (183, 1180, 670, 630, ""), (183, 1180, 1178, 591, ""),
    ]
    paths = [
        "M 1128 287 C 1108 430 1128 540 1178 591 C 1232 655 1320 740 1420 773",
        "M 610 442 C 620 530 640 590 670 630 C 696 668 716 694 737 712 C 768 742 800 772 843 788 C 920 815 1000 820 1075 817",
    ]
    texts = [
        (85, 80, "Ls/Y", "it", "middle"), (148, 1250, "O", "it", "middle"), (1640, 1260, "Lu/Y", "it", "middle"),
        (905, 185, "W", "it", "middle"), (1432, 1045, "W", "it", "middle"),
        (1140, 242, "Y0", "it", "middle"), (1468, 792, "Y0", "it", "middle"),
        (515, 390, "V", "it", "middle"), (935, 1090, "V", "it", "middle"),
        (626, 405, "Y1", "it", "middle"), (1122, 820, "Y1", "it", "middle"),
        (348, 597, "W′", "it", "middle"), (1175, 990, "W′", "it", "middle"),
        (720, 605, "C", "it", "middle"), (778, 708, "D", "it", "middle"),
        (942, 790, "B", "it", "middle"), (1212, 568, "A", "it", "middle"),
    ]
    dots = [(670, 630), (737, 712), (843, 788), (1178, 591)]
    return _diagram_svg(mode, "图 7-12 技能偏向性技术进步", (1751, 1300), 0.3, lines, paths, texts, dots)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "7-1": _fig_7_1,
        "7-2": _fig_7_2,
        "7-3": _fig_7_3,
        "7-4": _fig_7_4,
        "7-5": _fig_7_5,
        "7-6": _fig_7_6,
        "7-7": _fig_7_7,
        "7-8": _fig_7_8,
        "7-9": _fig_7_9,
        "7-10": _fig_7_10,
        "7-11": _fig_7_11,
        "7-12": _fig_7_12,
    }
