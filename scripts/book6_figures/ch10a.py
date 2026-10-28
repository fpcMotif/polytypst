from __future__ import annotations

from collections.abc import Callable

from scripts.book2_figures.engine import (
    Annotation,
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    render_figure_svg,
)

YEARS_1982_2007 = [float(y) for y in range(1982, 2008)]


def _fig_10_1(mode: ThemeMode = "mono") -> str:
    series = [
        ("个人间差距（男女合计）", "diamond", [3.073, 3.110, 3.134, 3.114, 3.128, 3.136, 3.143, 3.165, 3.158, 3.105, 3.031, 3.035, 3.009, 3.004, 3.004, 3.006, 2.967, 2.960, 2.960, 2.960, 2.969, 2.943, 2.954, 3.112, 3.112, 3.066]),
        ("男性间差距", "square", [2.701, 2.701, 2.760, 2.767, 2.767, 2.780, 2.785, 2.840, 2.840, 2.804, 2.783, 2.763, 2.763, 2.778, 2.763, 2.778, 2.745, 2.734, 2.754, 2.761, 2.798, 2.765, 2.785, 2.908, 2.899, 2.873]),
        ("女性间差距", "triangle", [2.217, 2.198, 2.198, 2.288, 2.297, 2.317, 2.343, 2.336, 2.308, 2.297, 2.255, 2.244, 2.233, 2.244, 2.264, 2.273, 2.246, 2.277, 2.306, 2.299, 2.328, 2.341, 2.341, 2.473, 2.475, 2.468]),
    ]
    panel = PanelSpec(
        xlim=(1981.5, 2007.5),
        ylim=(2.0, 3.4),
        xticks=[float(y) for y in range(1982, 2008, 2)],
        yticks=[(v / 100, f"{v / 100:.2f}") for v in range(200, 341, 20)],
        xlabel="年",
        ylabel="倍率",
        zero_line=False,
        lines=[
            LineSeries(x=YEARS_1982_2007, y=ys, label=label, color_idx=2 * i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        annotations=[
            Annotation(1981.7, 3.25, "↑差距大", dx=0, dy=0, arrow=False, align="start"),
            Annotation(1981.7, 2.04, "差距小↓", dx=0, dy=0, arrow=False, align="start"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-1", title="图 10-1 工资差距（1982—2007 年）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_10_2(mode: ThemeMode = "mono") -> str:
    all_ages = [2.693, 2.702, 2.769, 2.759, 2.760, 2.776, 2.782, 2.829, 2.829, 2.806, 2.788, 2.753, 2.759, 2.771, 2.764, 2.766, 2.741, 2.737, 2.748, 2.760, 2.790, 2.759, 2.790, 2.908, 2.887, 2.873]
    young = [
        ("35~39岁", "square", [2.003, 1.996, 1.969, 1.977, 2.026, 2.025, 2.038, 2.053, 2.080, 2.023, 2.001, 1.976, 1.999, 2.021, 2.015, 2.010, 1.998, 2.002, 2.042, 2.040, 2.066, 2.082, 2.127, 2.151, 2.176, 2.192]),
        ("30~34岁", "triangle", [1.816, 1.815, 1.820, 1.827, 1.853, 1.860, 1.904, 1.915, 1.883, 1.858, 1.838, 1.804, 1.797, 1.812, 1.815, 1.817, 1.813, 1.815, 1.832, 1.835, 1.843, 1.852, 1.866, 1.897, 1.907, 1.916]),
        ("25~29岁", "cross", [1.733, 1.733, 1.718, 1.691, 1.691, 1.697, 1.701, 1.724, 1.721, 1.690, 1.661, 1.660, 1.654, 1.664, 1.660, 1.669, 1.647, 1.634, 1.634, 1.639, 1.650, 1.674, 1.704, 1.742, 1.750, 1.749]),
        ("20~24岁", "cross", [1.617, 1.606, 1.597, 1.604, 1.588, 1.587, 1.599, 1.616, 1.610, 1.601, 1.566, 1.582, 1.553, 1.549, 1.549, 1.543, 1.532, 1.543, 1.541, 1.549, 1.554, 1.557, 1.586, 1.608, 1.621, 1.606]),
    ]
    old = [
        ("（不分年龄段）", "diamond", [2.692, 2.696, 2.763, 2.763, 2.763, 2.782, 2.782, 2.833, 2.830, 2.806, 2.780, 2.758, 2.768, 2.776, 2.768, 2.771, 2.740, 2.742, 2.747, 2.753, 2.782, 2.761, 2.782, 2.905, 2.892, 2.871]),
        ("55~59岁", "square", [2.966, 2.992, 3.053, 3.010, 2.988, 3.049, 3.075, 3.114, 3.066, 3.012, 2.953, 2.870, 2.891, 2.919, 2.863, 2.869, 2.942, 2.943, 2.997, 3.007, 3.111, 3.059, 3.038, 3.211, 3.211, 3.119]),
        ("50~54岁", "triangle", [2.915, 2.901, 2.885, 2.901, 2.901, 2.904, 2.900, 2.950, 2.864, 2.763, 2.726, 2.730, 2.725, 2.727, 2.715, 2.731, 2.745, 2.755, 2.818, 2.789, 2.906, 2.837, 2.854, 2.954, 2.955, 2.947]),
        ("45~49岁", "cross", [2.619, 2.603, 2.599, 2.595, 2.602, 2.540, 2.521, 2.585, 2.540, 2.471, 2.435, 2.428, 2.449, 2.451, 2.428, 2.467, 2.459, 2.495, 2.532, 2.513, 2.555, 2.554, 2.607, 2.688, 2.715, 2.776]),
        ("40~44岁", "cross", [2.282, 2.260, 2.257, 2.253, 2.269, 2.219, 2.221, 2.282, 2.269, 2.207, 2.231, 2.207, 2.200, 2.234, 2.207, 2.223, 2.231, 2.224, 2.303, 2.278, 2.313, 2.317, 2.341, 2.444, 2.434, 2.509]),
    ]
    xticks = [float(y) for y in range(1982, 2008, 3)]
    left_lines = [
        LineSeries(x=YEARS_1982_2007, y=ys, label=label, color_idx=2 * i, marker=marker, width=1.6)
        for i, (label, marker, ys) in enumerate(young)
    ]
    left_lines.append(
        LineSeries(x=YEARS_1982_2007, y=all_ages, label="（不分年龄段）（右轴）", color_idx=8, marker="diamond", width=2.2, axis="y2")
    )
    left = PanelSpec(
        title="（1）20~39岁",
        xlim=(1981.5, 2007.5),
        ylim=(1.5, 2.25),
        xticks=xticks,
        yticks=[(1.5, "1.50"), (1.75, "1.75"), (2.0, "2.00"), (2.25, "2.25")],
        y2lim=(2.0, 3.5),
        y2ticks=[(2.0, "2.00"), (2.5, "2.50"), (3.0, "3.00"), (3.5, "3.50")],
        xlabel="年",
        zero_line=False,
        lines=left_lines,
        legend_loc="bottom",
    )
    right = PanelSpec(
        title="（2）40~59岁",
        xlim=(1981.5, 2007.5),
        ylim=(2.0, 3.5),
        xticks=xticks,
        yticks=[(2.0, "2.00"), (2.5, "2.50"), (3.0, "3.00"), (3.5, "3.50")],
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=YEARS_1982_2007, y=ys, label=label, color_idx=8 if i == 0 else 2 * (i - 1), marker=marker, width=2.2 if i == 0 else 1.6)
            for i, (label, marker, ys) in enumerate(old)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="10-2",
        title="图 10-2 按年龄划分（同一年龄段内）的工资差距（男性，1982—2007 年）",
        panels=[left, right],
        cols=2,
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def _fig_10_3(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1995, 2008)]
    panels_data = [
        ("（1）20~24岁", (1.16, 1.30), 0.02,
         [1.276, 1.272, 1.264, 1.255, 1.256, 1.251, 1.255, 1.255, 1.258, 1.266, 1.254, 1.266, 1.256],
         [1.211, 1.215, 1.220, 1.220, 1.229, 1.228, 1.231, 1.236, 1.236, 1.249, 1.280, 1.280, 1.279]),
        ("（2）25~29岁", (1.20, 1.32), 0.02,
         [1.276, 1.271, 1.264, 1.255, 1.255, 1.252, 1.255, 1.254, 1.258, 1.266, 1.254, 1.266, 1.255],
         [1.256, 1.257, 1.258, 1.248, 1.252, 1.250, 1.258, 1.265, 1.274, 1.282, 1.314, 1.310, 1.307]),
        ("（3）30~34岁", (1.32, 1.42), 0.02,
         [1.365, 1.372, 1.377, 1.367, 1.375, 1.371, 1.382, 1.383, 1.387, 1.388, 1.395, 1.398, 1.404],
         [1.330, 1.324, 1.322, 1.327, 1.322, 1.339, 1.330, 1.333, 1.336, 1.344, 1.359, 1.367, 1.367]),
        ("（4）35~39岁", (1.38, 1.50), 0.02,
         [1.433, 1.446, 1.441, 1.424, 1.427, 1.426, 1.436, 1.444, 1.460, 1.469, 1.468, 1.479, 1.497],
         [1.410, 1.394, 1.396, 1.401, 1.404, 1.430, 1.421, 1.428, 1.425, 1.446, 1.462, 1.469, 1.464]),
        ("（5）40~44岁", (1.48, 1.60), 0.02,
         [1.500, 1.489, 1.487, 1.494, 1.491, 1.505, 1.513, 1.524, 1.518, 1.519, 1.552, 1.560, 1.580],
         [1.493, 1.484, 1.496, 1.497, 1.496, 1.534, 1.511, 1.518, 1.532, 1.546, 1.582, 1.566, 1.591]),
        ("（6）45~49岁", (1.50, 1.70), 0.05,
         [1.557, 1.552, 1.552, 1.552, 1.559, 1.562, 1.562, 1.562, 1.564, 1.574, 1.608, 1.612, 1.651],
         [1.576, 1.570, 1.594, 1.590, 1.609, 1.630, 1.616, 1.641, 1.640, 1.661, 1.678, 1.691, 1.687]),
        ("（7）50~54岁", (1.60, 1.85), 0.05,
         [1.661, 1.661, 1.625, 1.623, 1.624, 1.627, 1.613, 1.629, 1.611, 1.613, 1.625, 1.629, 1.655],
         [1.647, 1.635, 1.685, 1.700, 1.696, 1.737, 1.732, 1.789, 1.767, 1.773, 1.821, 1.820, 1.787]),
        ("（8）55~59岁", (1.60, 1.90), 0.05,
         [1.759, 1.741, 1.722, 1.724, 1.667, 1.703, 1.680, 1.705, 1.678, 1.663, 1.697, 1.706, 1.703],
         [1.664, 1.648, 1.668, 1.708, 1.772, 1.765, 1.795, 1.833, 1.830, 1.833, 1.898, 1.885, 1.832]),
    ]
    high_label = "高收入阶层（第9十分位数/中位数）"
    low_label = "低收入阶层（中位数/第1十分位数）"
    panels = []
    for idx, (title, ylim, step, high, low) in enumerate(panels_data):
        n = round((ylim[1] - ylim[0]) / step)
        panels.append(
            PanelSpec(
                title=title,
                xlim=(1994.6, 2007.4),
                ylim=ylim,
                xticks=[float(y) for y in range(1995, 2008, 2)],
                yticks=[(ylim[0] + step * i, f"{ylim[0] + step * i:.2f}") for i in range(n + 1)],
                xlabel="年",
                ylabel="倍",
                zero_line=False,
                lines=[
                    LineSeries(x=years, y=high, label=high_label if idx == 6 else "", color_idx=2, marker="diamond", width=1.6),
                    LineSeries(x=years, y=low, label=low_label if idx == 7 else "", color_idx=0, marker="square", width=1.6),
                ],
                legend_loc="bottom" if idx >= 6 else "none",
            )
        )
    spec = FigureSpec(
        fig_id="10-3",
        title="图 10-3 高收入阶层内部工资差距与低收入阶层内部工资差距（男性）",
        panels=panels,
        rows=4,
        cols=2,
        width=1120,
        height=700,
    )
    return render_figure_svg(spec, mode)


PERIOD_TICKS = [(0.0, "1991—1992"), (1.0, "1996—1997"), (2.0, "2001—2002"), (3.0, "2006—2007")]
AGE_MARKERS = [
    ("不分年龄段", "diamond", 0),
    ("20~24岁", "square", 2),
    ("25~29岁", "triangle", 4),
    ("30~34岁", "cross", 6),
    ("35~39岁", "cross", 8),
    ("40~44岁", "circle", 10),
    ("45~49岁", "square", 1),
    ("50~54岁", "triangle", 3),
    ("55~59岁", "circle", 5),
]


def _period_panel(values: list[list[float]], ylim: tuple[float, float], yticks: list[tuple[float, str]], ylabel: str) -> PanelSpec:
    return PanelSpec(
        xlim=(-0.5, 3.5),
        ylim=ylim,
        xticks=PERIOD_TICKS,
        yticks=yticks,
        xlabel="年",
        ylabel=ylabel,
        zero_line=False,
        lines=[
            LineSeries(x=[0.0, 1.0, 2.0, 3.0], y=ys, label=label, color_idx=c, marker=marker, width=1.8)
            for (label, marker, c), ys in zip(AGE_MARKERS, values)
        ],
        legend_loc="bottom",
    )


def _fig_10_4_1(mode: ThemeMode = "mono") -> str:
    values = [
        [59.75, 59.82, 59.65, 58.48],
        [92.40, 92.97, 92.69, 90.03],
        [89.47, 91.44, 89.92, 86.64],
        [83.72, 84.63, 83.52, 81.10],
        [78.70, 78.99, 77.42, 73.97],
        [73.50, 73.50, 71.29, 67.42],
        [67.47, 68.33, 66.86, 62.76],
        [62.23, 62.76, 61.66, 60.31],
        [58.52, 59.26, 57.13, 57.13],
    ]
    panel = _period_panel(values, (50.0, 95.0), [(float(v), str(v)) for v in range(50, 96, 5)], "")
    spec = FigureSpec(fig_id="10-4.1", title="图 10-4.1 中薪阶层占比（中位数的 75%～150%）", panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def _fig_10_4_2(mode: ThemeMode = "mono") -> str:
    values = [
        [0.2266, 0.2253, 0.2295, 0.2385],
        [0.1058, 0.1019, 0.1019, 0.1101],
        [0.1222, 0.1174, 0.1191, 0.1327],
        [0.1441, 0.1415, 0.1432, 0.1540],
        [0.1610, 0.1627, 0.1672, 0.1809],
        [0.1773, 0.1790, 0.1884, 0.2081],
        [0.1966, 0.1946, 0.2030, 0.2216],
        [0.2188, 0.2128, 0.2216, 0.2304],
        [0.2387, 0.2278, 0.2360, 0.2433],
    ]
    panel = _period_panel(values, (0.10, 0.25), [(0.10, "0.10"), (0.15, "0.15"), (0.20, "0.20"), (0.25, "0.25")], "两极分化↑")
    spec = FigureSpec(fig_id="10-4.2", title="图 10-4.2 工资的沃尔夫森极化指数", panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def _fig_10_5(mode: ThemeMode = "mono") -> str:
    gini = [0.266, 0.273, 0.273, 0.278, 0.281, 0.283, 0.283, 0.286, 0.287, 0.285, 0.286, 0.286, 0.290, 0.288, 0.286, 0.289, 0.292, 0.292, 0.295, 0.297, 0.297, 0.303, 0.310, 0.311, 0.321, 0.320]
    panel = PanelSpec(
        xlim=(1981.5, 2007.5),
        ylim=(0.24, 0.34),
        xticks=[float(y) for y in range(1982, 2008, 2)],
        yticks=[(v / 100, f"{v / 100:.2f}") for v in range(24, 35, 2)],
        xlabel="年",
        zero_line=False,
        lines=[LineSeries(x=YEARS_1982_2007, y=gini, color_idx=0, marker="diamond", width=1.8)],
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="10-5", title="图 10-5 工资差距——基尼系数（男性），《民间工资实态统计调查》", panels=[panel], width=860, height=440)
    return render_figure_svg(spec, mode)


SURVEY_TICKS = [(0.0, "1987"), (1.0, "1992"), (2.0, "1997"), (3.0, "2002"), (4.0, "2007")]
SURVEY_X = [0.0, 1.0, 2.0, 3.0, 4.0]


def _fig_10_6_1(mode: ThemeMode = "mono") -> str:
    employees = [0.315, 0.316, 0.317, 0.330, 0.339]
    regular = [0.275, 0.276, 0.276, 0.279, 0.281]
    labels = [Annotation(x, y, f"{y:.3f}", dy=26 if i != 3 else -16, arrow=False) for i, (x, y) in enumerate(zip(SURVEY_X, employees))]
    labels += [Annotation(x, y, f"{y:.3f}", dy=20, arrow=False) for x, y in zip(SURVEY_X, regular)]
    panel = PanelSpec(
        xlim=(-0.5, 4.5),
        ylim=(0.26, 0.36),
        xticks=SURVEY_TICKS,
        yticks=[(v / 100, f"{v / 100:.2f}") for v in range(26, 37, 2)],
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=SURVEY_X, y=employees, label="雇员", color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=SURVEY_X, y=regular, label="其中正规雇员", color_idx=2, marker="square", width=1.8),
        ],
        annotations=labels,
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-6.1", title="图 10-6.1 雇员的收入差距——基尼系数 (男性，不分年龄段)", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


SURVEY_AGES = [
    ("55~59岁", "diamond", 0),
    ("50~54岁", "square", 2),
    ("45~49岁", "triangle", 4),
    ("40~44岁", "cross", 6),
    ("35~39岁", "cross", 8),
    ("30~34岁", "circle", 10),
    ("25~29岁", "square", 1),
    ("20~24岁", "triangle", 3),
]


def _survey_age_figure(fig_id: str, title: str, values: list[list[float]], mode: ThemeMode) -> str:
    panel = PanelSpec(
        xlim=(-0.5, 4.5),
        ylim=(0.15, 0.40),
        xticks=SURVEY_TICKS,
        yticks=[(v / 100, f"{v / 100:.2f}") for v in range(15, 41, 5)],
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=SURVEY_X, y=ys, label=label, color_idx=c, marker=marker, width=1.8)
            for (label, marker, c), ys in zip(SURVEY_AGES, values)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_10_6_2(mode: ThemeMode = "mono") -> str:
    values = [
        [0.3620, 0.3324, 0.3135, 0.3241, 0.3252],
        [0.3149, 0.2911, 0.2781, 0.2997, 0.2961],
        [0.2746, 0.2629, 0.2557, 0.2660, 0.2772],
        [0.2431, 0.2416, 0.2344, 0.2480, 0.2661],
        [0.2244, 0.2180, 0.2122, 0.2295, 0.2460],
        [0.2019, 0.1970, 0.1938, 0.2143, 0.2267],
        [0.1840, 0.1768, 0.1817, 0.2033, 0.2143],
        [0.1805, 0.1826, 0.1849, 0.2171, 0.2071],
    ]
    return _survey_age_figure("10-6.2", "图 10-6.2 雇员的收入差距——基尼系数（男性雇员，按年龄划分）", values, mode)


def _fig_10_6_3(mode: ThemeMode = "mono") -> str:
    values = [
        [0.3062, 0.2938, 0.2805, 0.2805, 0.2724],
        [0.2787, 0.2683, 0.2593, 0.2593, 0.2622],
        [0.2506, 0.2427, 0.2375, 0.2408, 0.2499],
        [0.2229, 0.2209, 0.2172, 0.2258, 0.2394],
        [0.2091, 0.2042, 0.1998, 0.2105, 0.2201],
        [0.1912, 0.1848, 0.1816, 0.1949, 0.2033],
        [0.1738, 0.1651, 0.1695, 0.1776, 0.1839],
        [0.1709, 0.1715, 0.1643, 0.1689, 0.1672],
    ]
    return _survey_age_figure("10-6.3", "图 10-6.3 雇员的收入差距——基尼系数（男性正规雇员，按年龄划分）", values, mode)


def _fig_10_8(mode: ThemeMode = "mono") -> str:
    xs = [0.0, 1.0, 2.0]
    series = [
        ("不分年龄段", "diamond", 0, [12.49, 15.86, 17.43]),
        ("25~29岁", "triangle", 2, [7.75, 12.73, 14.17]),
        ("30~34岁", "cross", 4, [4.60, 7.21, 8.52]),
        ("35~39岁", "cross", 6, [3.98, 5.71, 7.19]),
        ("40~49岁", "circle", 8, [4.34, 6.12, 6.63]),
        ("50~59岁", "square", 1, [6.38, 9.33, 10.70]),
    ]
    lines = [LineSeries(x=xs, y=ys, label=label, color_idx=c, marker=marker, width=1.8) for label, marker, c, ys in series]
    lines.append(LineSeries(x=xs, y=[21.0, 31.73, 29.88], label="20~24岁（右轴）", color_idx=10, marker="square", width=1.8, axis="y2"))
    panel = PanelSpec(
        xlim=(-0.5, 2.5),
        ylim=(0.0, 20.0),
        xticks=[(0.0, "1997"), (1.0, "2002"), (2.0, "2007")],
        yticks=[float(v) for v in range(0, 21, 5)],
        y2lim=(0.0, 40.0),
        y2ticks=[float(v) for v in range(0, 41, 10)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=lines,
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-8", title="图 10-8 年收入低于 200 万日元的人群比例（男性，雇员，%）", panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def _fig_10_9(mode: ThemeMode = "mono") -> str:
    values = [
        [0.2650, 0.2681, 0.2803, 0.2942, 0.2995],
        [0.1424, 0.1457, 0.1494, 0.1680, 0.1597],
        [0.1563, 0.1417, 0.1500, 0.1597, 0.1736],
        [0.1494, 0.1430, 0.1570, 0.1700, 0.1838],
        [0.1791, 0.1705, 0.1573, 0.1835, 0.1974],
        [0.2047, 0.1868, 0.1927, 0.2060, 0.2200],
        [0.2130, 0.2206, 0.2093, 0.2279, 0.2365],
        [0.2571, 0.2597, 0.2438, 0.2584, 0.2620],
        [0.3336, 0.3051, 0.2955, 0.3064, 0.3091],
    ]
    panel = PanelSpec(
        xlim=(-0.5, 4.5),
        ylim=(0.10, 0.35),
        xticks=SURVEY_TICKS,
        yticks=[(v / 100, f"{v / 100:.2f}") for v in range(10, 36, 5)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=SURVEY_X, y=ys, label=label, color_idx=c, marker=marker, width=1.8)
            for (label, marker, c), ys in zip(AGE_MARKERS, values)
        ],
        annotations=[Annotation(-0.4, 0.115, "两极分化↑", dy=0, arrow=False, align="start")],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-9", title="图 10-9 雇员收入的沃尔夫森极化指数（男性）", panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def _fig_10_7(mode: ThemeMode = "mono") -> str:
    years = [("1997年", 2, [13.1, 7.9, 7.5]), ("2002年", 1, [26.2, 13.9, 11.0]), ("2007年", 3, [27.3, 18.7, 13.9])]
    bars = []
    labels = []
    for k, (label, c, ys) in enumerate(years):
        xs = [i + (k - 1) * 0.22 for i in range(3)]
        bars.append(BarSeries(x=xs, y=ys, label=label, color_idx=c, width=0.22))
        labels += [Annotation(x, y, f"{y:.1f}", dy=-6, arrow=False) for x, y in zip(xs, ys)]
    panel = PanelSpec(
        xlim=(-0.5, 2.5),
        ylim=(0.0, 30.0),
        xticks=[(0.0, "20~24岁"), (1.0, "25~29岁"), (2.0, "30~34岁")],
        yticks=[0.0, 10.0, 20.0, 30.0],
        ylabel="%",
        bars=bars,
        annotations=labels,
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-7", title="图 10-7 年轻雇员中非正规雇员的比例（男性）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_10_10(mode: ThemeMode = "mono") -> str:
    ratio = [1.1544, 1.1846, 1.1942, 1.2269, 1.2547, 1.2677, 1.2704, 1.2988, 1.3050, 1.3046, 1.3111, 1.3382, 1.3398, 1.3346, 1.3368, 1.3370, 1.3295, 1.3118, 1.3215, 1.3190, 1.3190, 1.3111, 1.3231, 1.3341, 1.3139, 1.3396]
    panel = PanelSpec(
        xlim=(1981.5, 2007.5),
        ylim=(1.1, 1.4),
        xticks=[float(y) for y in range(1982, 2008, 2)],
        yticks=[(1.1, "1.1"), (1.2, "1.2"), (1.3, "1.3"), (1.4, "1.4")],
        xlabel="年",
        ylabel="倍",
        zero_line=False,
        lines=[LineSeries(x=YEARS_1982_2007, y=ratio, color_idx=0, marker="diamond", width=1.8)],
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="10-10", title="图 10-10 不同学历间工资差距（男性，不分年龄段）", panels=[panel], width=860, height=460)
    return render_figure_svg(spec, mode)


def _fig_10_11(mode: ThemeMode = "mono") -> str:
    young = ["35~39岁", "30~34岁", "25~29岁", "20~24岁"]
    old = ["55~59岁", "50~54岁", "45~49岁", "40~44岁"]
    panels_data = [
        ("（1）工资差距（20~29岁，30~39岁）", young, (1.0, 1.4), 0.1, "{:.1f}", [
            [1.137, 1.143, 1.147, 1.149, 1.147, 1.138, 1.143, 1.144, 1.112, 1.124, 1.129, 1.139, 1.153, 1.167, 1.176, 1.173, 1.191, 1.167, 1.205, 1.203, 1.201, 1.230, 1.237, 1.246, 1.243, 1.235],
            [1.069, 1.067, 1.069, 1.075, 1.083, 1.087, 1.085, 1.097, 1.112, 1.108, 1.096, 1.114, 1.104, 1.112, 1.132, 1.135, 1.123, 1.135, 1.148, 1.151, 1.163, 1.145, 1.157, 1.161, 1.159, 1.176],
            [1.028, 1.028, 1.025, 1.041, 1.045, 1.058, 1.052, 1.042, 1.063, 1.065, 1.069, 1.072, 1.072, 1.076, 1.081, 1.084, 1.076, 1.082, 1.073, 1.077, 1.088, 1.106, 1.099, 1.103, 1.109, 1.098],
            [1.057, 1.067, 1.073, 1.074, 1.062, 1.087, 1.087, 1.103, 1.115, 1.123, 1.108, 1.115, 1.099, 1.088, 1.088, 1.088, 1.094, 1.088, 1.094, 1.099, 1.115, 1.135, 1.117, 1.108, 1.115, 1.112],
        ]),
        ("（1）工资差距（40~49岁，50~59岁）", old, (1.1, 1.5), 0.1, "{:.1f}", [
            [1.219, 1.266, 1.272, 1.266, 1.250, 1.288, 1.266, 1.400, 1.404, 1.340, 1.286, 1.346, 1.358, 1.318, 1.309, 1.315, 1.340, 1.340, 1.416, 1.345, 1.316, 1.300, 1.337, 1.230, 1.230, 1.216],
            [1.193, 1.236, 1.230, 1.297, 1.353, 1.372, 1.318, 1.326, 1.335, 1.313, 1.331, 1.309, 1.301, 1.327, 1.316, 1.298, 1.291, 1.297, 1.319, 1.287, 1.264, 1.256, 1.247, 1.207, 1.178, 1.235],
            [1.280, 1.303, 1.275, 1.270, 1.290, 1.287, 1.254, 1.299, 1.299, 1.207, 1.198, 1.206, 1.219, 1.226, 1.240, 1.209, 1.226, 1.188, 1.236, 1.240, 1.233, 1.256, 1.287, 1.287, 1.246, 1.300],
            [1.200, 1.212, 1.209, 1.216, 1.216, 1.222, 1.169, 1.207, 1.199, 1.180, 1.180, 1.177, 1.167, 1.155, 1.166, 1.183, 1.204, 1.190, 1.230, 1.238, 1.230, 1.220, 1.262, 1.246, 1.271, 1.311],
        ]),
        ("（2）大学等学历毕业人员的相对供给（对数值）（20~29岁，30~39岁）", young, (3.0, 5.0), 0.5, "{:.1f}", [
            [3.909, 3.957, 3.979, 3.979, 3.952, 3.952, 3.943, 3.994, 4.084, 4.174, 4.268, 4.304, 4.389, 4.410, 4.450, 4.430, 4.400, 4.430, 4.457, 4.450, 4.440, 4.440, 4.417, 4.575, 4.575, 4.474],
            [4.074, 4.068, 4.112, 4.146, 4.202, 4.287, 4.337, 4.399, 4.399, 4.416, 4.461, 4.445, 4.439, 4.390, 4.457, 4.450, 4.430, 4.450, 4.496, 4.496, 4.480, 4.490, 4.470, 4.520, 4.510, 4.520],
            [4.382, 4.427, 4.473, 4.470, 4.512, 4.456, 4.430, 4.445, 4.439, 4.437, 4.473, 4.456, 4.445, 4.417, 4.440, 4.440, 4.440, 4.460, 4.470, 4.480, 4.530, 4.581, 4.586, 4.665, 4.733, 4.733],
            [3.682, 3.643, 3.575, 3.479, 3.518, 3.476, 3.514, 3.540, 3.482, 3.513, 3.592, 3.518, 3.490, 3.455, 3.517, 3.613, 3.698, 3.748, 3.804, 3.832, 3.883, 4.018, 4.069, 4.029, 4.187, 4.153],
        ]),
        ("（2）大学等学历毕业人员的相对供给（对数值）（40~49岁，50~59岁）", old, (3.0, 5.0), 0.5, "{:.1f}", [
            [3.194, 3.239, 3.199, 3.159, 3.194, 3.251, 3.376, 3.347, 3.347, 3.427, 3.353, 3.330, 3.302, 3.369, 3.305, 3.324, 3.350, 3.438, 3.430, 3.468, 3.603, 3.637, 3.706, 3.832, 3.765, 3.761],
            [3.553, 3.571, 3.594, 3.548, 3.571, 3.582, 3.502, 3.542, 3.498, 3.496, 3.498, 3.519, 3.519, 3.540, 3.546, 3.649, 3.695, 3.725, 3.765, 3.788, 3.872, 3.843, 3.929, 4.028, 4.122, 4.187],
            [3.713, 3.708, 3.696, 3.599, 3.656, 3.616, 3.616, 3.627, 3.650, 3.673, 3.719, 3.794, 3.811, 3.832, 3.838, 3.849, 3.906, 3.941, 4.009, 4.114, 4.231, 4.306, 4.365, 4.459, 4.437, 4.381],
            [3.698, 3.685, 3.712, 3.695, 3.719, 3.776, 3.759, 3.851, 3.849, 3.849, 3.885, 3.862, 3.954, 4.025, 4.125, 4.159, 4.259, 4.328, 4.379, 4.439, 4.448, 4.406, 4.360, 4.537, 4.448, 4.446],
        ]),
    ]
    markers = [("diamond", 0), ("square", 2), ("triangle", 4), ("cross", 6)]
    panels = []
    for title, labels, ylim, step, fmt, values in panels_data:
        n = round((ylim[1] - ylim[0]) / step)
        panels.append(
            PanelSpec(
                title=title,
                xlim=(1981.5, 2007.5),
                ylim=ylim,
                xticks=[float(y) for y in range(1982, 2008, 5)],
                yticks=[(ylim[0] + step * i, fmt.format(ylim[0] + step * i)) for i in range(n + 1)],
                xlabel="年",
                ylabel="倍",
                zero_line=False,
                lines=[
                    LineSeries(x=YEARS_1982_2007, y=ys, label=label, color_idx=c, marker=marker, width=1.5)
                    for label, (marker, c), ys in zip(labels, markers, values)
                ],
                legend_loc="bottom",
            )
        )
    spec = FigureSpec(
        fig_id="10-11",
        title="图 10-11 不同年龄段的不同学历间工资差距及相对供给（男性）",
        panels=panels,
        rows=2,
        cols=2,
        width=860,
        height=820,
    )
    return render_figure_svg(spec, mode)


def _fig_10_12(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(2001, 2008)]
    series = [
        ("55~59岁", "diamond", 0, [2.518, 2.700, 2.688, 2.689, 2.773, 2.709, 2.926]),
        ("50~54岁", "square", 2, [2.228, 2.364, 2.376, 2.455, 2.456, 2.449, 2.624]),
        ("45~49岁", "triangle", 4, [2.185, 2.254, 2.264, 2.346, 2.323, 2.397, 2.497]),
        ("40~44岁", "cross", 6, [2.078, 2.097, 2.162, 2.163, 2.201, 2.259, 2.307]),
        ("35~39岁", "cross", 8, [1.933, 1.966, 2.000, 2.027, 2.030, 2.080, 2.090]),
        ("30~34岁", "circle", 10, [1.790, 1.809, 1.853, 1.832, 1.873, 1.894, 1.921]),
        ("25~29岁", "square", 1, [1.564, 1.576, 1.600, 1.610, 1.656, 1.671, 1.647]),
    ]
    panel = PanelSpec(
        xlim=(2000.5, 2007.5),
        ylim=(1.4, 3.0),
        xticks=years,
        yticks=[(v / 10, f"{v / 10:.3f}") for v in range(14, 31, 2)],
        xlabel="年",
        zero_line=False,
        lines=[LineSeries(x=years, y=ys, label=label, color_idx=c, marker=marker, width=1.8) for label, marker, c, ys in series],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="10-12",
        title="图 10-12 同等学历人群内部的工资差距（研究生院和大学毕业人员、男性、按年龄划分）",
        panels=[panel],
        width=860,
        height=500,
    )
    return render_figure_svg(spec, mode)


def _fig_10_13(mode: ThemeMode = "mono") -> str:
    groups = ["不分年龄段", "20~24岁", "25~29岁", "30~34岁", "35~39岁", "40~44岁", "45~49岁", "50~54岁", "55~59岁"]
    totals = [10.6, 27.7, 24.3, 17.8, 20.1, 17.9, 17.4, 11.2, 11.8]
    within = [7.05, 23.1, 20.0, 17.3, 15.3, 12.85, 10.15, 10.45, 9.4]
    variance = [10.59, 27.47, 24.12, 17.91, 19.66, 17.76, 17.18, 10.95, 11.66]
    xs = [float(i) for i in range(len(groups))]
    panel = PanelSpec(
        xlim=(-0.5, len(groups) - 0.5),
        ylim=(0.0, 30.0),
        xticks=list(zip(xs, groups)),
        yticks=[float(v) for v in range(0, 31, 5)],
        bars=[
            BarSeries(x=xs, y=[t - w for t, w in zip(totals, within)], bottom=within, label="不同学历间差距的贡献", color_idx=2, width=0.4),
            BarSeries(x=xs, y=within, label="同等学历人群内部工资差距的贡献", color_idx=3, width=0.4),
        ],
        lines=[LineSeries(x=xs, y=variance, label="对数化后方差的变化率", color_idx=0, marker="diamond", width=2.0)],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-13", title="图 10-13 工资差距的扩大与不同学历间差距的贡献", panels=[panel], width=1100, height=560)
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "10-7": _fig_10_7,
        "10-10": _fig_10_10,
        "10-11": _fig_10_11,
        "10-12": _fig_10_12,
        "10-13": _fig_10_13,
        "10-1": _fig_10_1,
        "10-2": _fig_10_2,
        "10-3": _fig_10_3,
        "10-4.1": _fig_10_4_1,
        "10-4.2": _fig_10_4_2,
        "10-5": _fig_10_5,
        "10-6.1": _fig_10_6_1,
        "10-6.2": _fig_10_6_2,
        "10-6.3": _fig_10_6_3,
        "10-8": _fig_10_8,
        "10-9": _fig_10_9,
    }
