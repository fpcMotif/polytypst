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

TITLES = {
    "13-4": "图 13-4 按年龄组划分的就业形式比例（一）",
    "13-5": "图 13-5 按年龄组划分的就业形式比例（二）",
    "14-1": "图 14-1 男女雇员人数与常用雇员人数的变化",
    "14-2": "图 14-2 关于女性在雇佣就业人员中所占比例的变化率的因素分解（1985—2007 年）",
    "14-3": "图 14-3 正规、非正规职员和员工（女性）的变化",
    "14-4": "图 14-4 按配偶关系划分的女性雇佣就业率（总数）",
    "14-5": "图 14-5 按配偶关系划分的女性雇佣就业率（未婚）",
    "14-6": "图 14-6 按配偶关系划分的女性雇佣就业率（有配偶）",
    "14-8": "图 14-8 劳动者每小时平均规定工资差距的变化",
    "14-9": "图 14-9 标准劳动者和普通劳动者各年龄段的规定工资（男性=100，高中毕业）",
    "14-10": "图 14-10 可享受育儿休假制度的性别以及生育第一胎后的女性继续就业率",
    "14-11": "图 14-11 关于生育第一胎后再就业的（统计学）生存分析：模拟",
    "15-1": "图 15-1 按年龄段划分的失业率变化",
    "15-2": "图 15-2 失业率变化趋势（上年对数差）",
    "15-3": "图 15-3 应届高中毕业生就业率和有效职位空缺率",
    "15-4": "图 15-4 应届毕业生就业者在职第一年的离职率变化",
    "15-5": "图 15-5 自由职业者人数变化",
}

AGES_20_64 =["20~24", "25~29", "30~34", "35~39", "40~44", "45~49", "50~54", "55~64"]
YEAR_SERIES_MARKERS = [("1985年", "diamond"), ("1990年", "square"), ("1995年", "triangle"), ("2000年", "cross"), ("2006年", "circle")]


def _years(first: int, last: int) -> list[float]:
    return [float(y) for y in range(first, last + 1)]


FORM_LABELS = [
    ("正规雇员", 2),
    ("非全日制员工", 1),
    ("临时员工", 3),
    ("与劳务派遣机构签约的派遣员工", 0),
    ("合同工、返聘人员", 0),
    ("其他", 4),
]


def _form_panel(title: str, ages: list[str], rows: list[list[float]], legend: bool) -> PanelSpec:
    xs = [float(i) for i in range(len(ages))]
    shares = [[row[k] if k < len(row) else 0.0 for row in rows] for k in range(5)]
    regular, part_time, temporary, contract, other = shares
    columns = [regular, part_time, temporary, [], contract, other]
    bars = []
    bottom = [0.0] * len(ages)
    for (label, color_idx), ys in zip(FORM_LABELS, columns):
        if ys and any(ys):
            bars.append(BarSeries(x=xs, y=ys, label=label, color_idx=color_idx, width=0.48, bottom=list(bottom), opacity=1.0))
            bottom = [b + y for b, y in zip(bottom, ys)]
        else:
            bars.append(BarSeries(x=[], y=[], label=label, color_idx=color_idx, width=0.48, opacity=1.0))
    return PanelSpec(
        title=title,
        xlim=(-0.5, len(ages) - 0.5),
        ylim=(0.0, 100.0),
        xticks=[(x, a) for x, a in zip(xs, ages)],
        yticks=[float(v) for v in range(0, 101, 20)],
        xlabel="年龄",
        ylabel="%",
        zero_line=False,
        bars=bars,
        legend_loc="bottom" if legend else "none",
    )


def _form_figure(fig_id: str, panels: list[tuple[str, list[str], list[list[float]]]], mode: ThemeMode) -> str:
    spec = FigureSpec(
        fig_id=fig_id,
        title=TITLES[fig_id],
        panels=[_form_panel(t, ages, rows, i == 0) for i, (t, ages, rows) in enumerate(panels)],
        rows=3,
        cols=1,
        width=860,
        height=1150,
    )
    return render_figure_svg(spec, mode)


AGES_15_65 = ["15~24", "25~34", "35~44", "45~54", "55~64", "65以上"]


def _fig_13_4(mode: ThemeMode = "mono") -> str:
    return _form_figure(
        "13-4",
        [
            ("（a）1990年，男性", [*AGES_15_65[:5], "65~以上"], [
                [80.0, 0.5, 18.3, 1.2],
                [96.6, 0.3, 1.6, 1.5],
                [96.6, 0.3, 1.8, 1.3],
                [95.5, 0.6, 0.8, 3.1],
                [77.4, 2.7, 3.5, 16.4],
                [49.3, 10.6, 9.8, 30.3],
            ]),
            ("（b）2000年，男性", AGES_15_65, [
                [61.5, 1.9, 34.7, 1.9],
                [94.0, 0.6, 3.5, 1.9],
                [95.4, 0.3, 2.3, 2.0],
                [94.8, 0.8, 2.4, 2.0],
                [81.0, 4.8, 3.5, 10.7],
                [44.8, 17.2, 11.6, 26.4],
            ]),
            ("（c）2007年，男性", AGES_15_65, [
                [54.5, 2.8, 33.3, 7.7, 1.7],
                [85.6, 1.7, 4.1, 6.9, 1.7],
                [91.8, 0.7, 1.3, 4.9, 1.3],
                [91.6, 1.1, 1.5, 3.4, 2.4],
                [74.5, 5.5, 4.1, 12.0, 3.9],
                [30.0, 20.6, 13.6, 25.3, 9.9],
            ]),
        ],
        mode,
    )


def _fig_13_5(mode: ThemeMode = "mono") -> str:
    return _form_figure(
        "13-5",
        [
            ("（a）1990年，女性", AGES_15_65, [
                [79.6, 3.8, 14.6, 2.0],
                [71.6, 18.6, 5.2, 4.6],
                [50.3, 43.1, 3.6, 3.0],
                [55.3, 38.1, 2.8, 3.8],
                [54.9, 34.2, 3.1, 7.8],
                [50.0, 35.5, 3.6, 10.9],
            ]),
            ("（b）2000年，女性", AGES_15_65, [
                [57.4, 7.8, 31.8, 3.0],
                [67.8, 18.4, 7.8, 6.0],
                [46.6, 44.1, 4.3, 5.0],
                [48.3, 45.1, 3.4, 3.2],
                [44.6, 47.1, 3.5, 4.8],
                [41.1, 44.1, 6.5, 8.3],
            ]),
            ("（c）2007年，女性", AGES_15_65, [
                [50.3, 10.0, 30.8, 7.1, 1.8],
                [57.8, 19.8, 6.5, 13.2, 2.7],
                [45.4, 37.2, 4.1, 10.6, 2.7],
                [41.5, 45.0, 3.3, 7.5, 2.7],
                [37.5, 48.8, 3.5, 6.5, 3.7],
                [33.9, 45.2, 2.4, 7.7, 10.8],
            ]),
        ],
        mode,
    )


def _odd_markers(xs: list[float], ys: list[float], color_idx: int, marker: str) -> LineSeries:
    return LineSeries(
        x=xs, y=[y if i % 2 else None for i, y in enumerate(ys)], color_idx=color_idx, marker=marker, width=1.8, hollow=False
    )


def _age_panel(rows: list[list[float | None]], ylim: tuple[float, float], step: float) -> PanelSpec:
    xs = [float(i) for i in range(len(AGES_20_64))]
    return PanelSpec(
        xlim=(-0.5, len(AGES_20_64) - 0.5),
        ylim=ylim,
        xticks=[(float(i), label) for i, label in enumerate(AGES_20_64)],
        yticks=[ylim[0] + step * i for i in range(int((ylim[1] - ylim[0]) / step) + 1)],
        xlabel="年龄",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, ((label, marker), ys) in enumerate(zip(YEAR_SERIES_MARKERS, rows))
        ],
        legend_loc="bottom",
    )


def _fig_14_1(mode: ThemeMode = "mono") -> str:
    years = _years(1990, 2006)
    left = [
        ("男性雇员人数（左轴）", "diamond", [2993, 3086, 3148, 3187, 3203, 3219, 3241, 3266, 3249, 3227, 3224, 3200, 3173, 3164, 3154, 3166, 3150]),
        ("男性常用雇员人数（左轴）", "triangle", [2831, 2923, 2985, 3024, 3027, 3041, 3060, 3073, 3051, 3018, 3001, 2975, 2931, 2910, 2902, 2904, 2939]),
    ]
    right = [
        ("女性雇员人数（右轴）", "square", [1834, 1924, 1968, 2006, 2031, 2048, 2084, 2127, 2126, 2117, 2143, 2170, 2161, 2185, 2201, 2236, 2279]),
        ("女性常用雇员人数（右轴）", "cross", [1484, 1559, 1607, 1636, 1662, 1665, 1698, 1722, 1706, 1687, 1691, 1706, 1680, 1691, 1722, 1733, 1778]),
    ]
    lines = [
        LineSeries(x=years, y=[float(v) for v in ys], label=label, color_idx=i, marker=marker, width=1.8, axis=axis)
        for i, (label, marker, ys, axis) in enumerate(
            [(*s, "y1") for s in left] + [(*s, "y2") for s in right]
        )
    ]
    panel = PanelSpec(
        xlim=(1989.5, 2006.5),
        ylim=(2300.0, 3300.0),
        y2lim=(1400.0, 2400.0),
        xticks=years,
        yticks=[float(v) for v in range(2300, 3301, 100)],
        y2ticks=[float(v) for v in range(1400, 2401, 100)],
        xlabel="年",
        ylabel="万人",
        y2label="万人",
        zero_line=False,
        lines=lines,
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="14-1", title=TITLES["14-1"], panels=[panel], width=960, height=540)
    return render_figure_svg(spec, mode)


def _fig_14_2(mode: ThemeMode = "mono") -> str:
    xs = [0.0, 1.0, 2.0]
    within = [3.73, 2.74, 1.03]
    structure = [1.97, 0.76, 1.16]
    error = [0.0, 0.10, -0.09]
    totals = [5.70, 3.60, 2.10]
    error_bottom = [a + b if e >= 0 else 0.0 for a, b, e in zip(within, structure, error)]
    panel = PanelSpec(
        xlim=(-0.5, 2.5),
        ylim=(-1.0, 7.0),
        xticks=[(0.0, "1985—2007年"), (1.0, "其中1985—1997年"), (2.0, "其中1997—2007年")],
        yticks=[(float(v), f"{v:.2f}") for v in range(-1, 8)],
        ylabel="%",
        bars=[
            BarSeries(x=[1.0, 2.0], y=error[1:], label="误差", color_idx=0, width=0.4, bottom=error_bottom[1:]),
            BarSeries(x=xs, y=structure, label="行业结构比例的变化导致的女性比例的上升", color_idx=2, width=0.4, bottom=within),
            BarSeries(x=xs, y=within, label="由于各行业女性比例的上升而导致的整体女性比例的上升", color_idx=3, width=0.4),
        ],
        lines=[LineSeries(x=xs, y=totals, label="女性在雇佣就业人员中所占的比例", color_idx=1, marker="circle", width=2.0)],
        annotations=[
            Annotation(0.0, 5.70, "5.70", dy=-14, arrow=False),
            Annotation(0.12, 5.70, "（整体女性比例上升）", dy=-14, arrow=False, align="start"),
            Annotation(0.0, 4.55, "1.97", dy=0, arrow=False),
            Annotation(0.0, 1.70, "3.73", dy=0, arrow=False),
            Annotation(1.0, 3.60, "3.60", dy=-14, arrow=False),
            Annotation(1.25, 3.55, "0.10", dy=-6, arrow=False, align="start"),
            Annotation(1.0, 2.95, "0.76", dy=0, arrow=False),
            Annotation(1.0, 1.20, "2.74", dy=0, arrow=False),
            Annotation(2.0, 2.10, "2.10", dy=-14, arrow=False),
            Annotation(2.0, 1.45, "1.16", dy=0, arrow=False),
            Annotation(2.0, 0.35, "1.03", dy=0, arrow=False),
            Annotation(2.25, -0.09, "-0.09", dy=4, arrow=False, align="start"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="14-2", title=TITLES["14-2"], panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def _fig_14_3(mode: ThemeMode = "mono") -> str:
    years = _years(1988, 2008)
    series = [
        ("正规职员和员工（女性）", "diamond", [1003, 1040, 1047, 1119, 1135, 1141, 1166, 1155, 1166, 1166, 1159, 1086, 1076, 1077, 1054, 1011, 987, 1007, 1003, 1002, 1007]),
        ("非正规职员和员工（女性）", "square", [548, 590, 647, 666, 703, 716, 719, 743, 769, 838, 866, 898, 934, 986, 983, 1061, 1097, 1081, 1130, 1188, 1184]),
    ]
    panel = PanelSpec(
        xlim=(1987.5, 2008.5),
        ylim=(500.0, 1200.0),
        xticks=years,
        yticks=[float(v) for v in range(500, 1201, 100)],
        xlabel="年",
        ylabel="万人",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=[float(v) for v in ys], label=label, color_idx=i, marker=marker, width=1.8, hollow=False)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
        xtick_vertical=True,
    )
    spec = FigureSpec(fig_id="14-3", title=TITLES["14-3"], panels=[panel], width=1000, height=520)
    return render_figure_svg(spec, mode)


def _fig_14_4(mode: ThemeMode = "mono") -> str:
    rows: list[list[float | None]] = [
        [64.6, 43.4, 33.5, 39.3, 45.1, 42.7, 36.0, 20.2],
        [70.1, 53.0, 38.7, 45.0, 50.1, 50.1, 43.4, 23.8],
        [68.0, 58.6, 43.9, 48.2, 54.6, 54.5, 49.2, 30.0],
        [64.8, 62.2, 48.3, 51.4, 57.0, 58.0, 52.9, 33.1],
        [64.8, 68.6, 56.0, 55.7, 62.7, 64.1, 58.7, 38.8],
    ]
    spec = FigureSpec(fig_id="14-4", title=TITLES["14-4"], panels=[_age_panel(rows, (0.0, 80.0), 10.0)], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_14_5(mode: ThemeMode = "mono") -> str:
    rows: list[list[float | None]] = [
        [72.4, 77.4, 64.8, 61.7, 59.6, 55.1, 52.4, 36.4],
        [74.6, 83.8, 73.1, 64.8, 60.0, 56.6, 56.4, 32.9],
        [71.9, 83.4, 77.6, 71.6, 63.7, 57.6, 53.6, 37.1],
        [68.4, 82.1, 77.7, 73.7, 65.3, 59.3, 54.9, 37.9],
        [None, 84.5, 80.8, 77.5, 73.0, 67.7, 62.2, 44.3],
    ]
    spec = FigureSpec(fig_id="14-5", title=TITLES["14-5"], panels=[_age_panel(rows, (0.0, 90.0), 10.0)], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_14_6(mode: ThemeMode = "mono") -> str:
    rows: list[list[float | None]] = [
        [30.3, 27.2, 28.1, 34.7, 42.7, 40.7, 32.6, 16.8],
        [32.5, 31.4, 31.4, 41.0, 47.6, 48.2, 41.1, 21.1],
        [35.5, 34.5, 34.1, 43.8, 52.4, 52.6, 46.5, 27.0],
        [35.0, 37.4, 36.4, 45.4, 54.5, 56.0, 50.1, 30.5],
        [36.5, 44.4, 41.6, 47.9, 58.7, 62.1, 56.9, 36.2],
    ]
    spec = FigureSpec(fig_id="14-6", title=TITLES["14-6"], panels=[_age_panel(rows, (0.0, 70.0), 10.0)], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_14_8(mode: ThemeMode = "mono") -> str:
    years = _years(1988, 2006)
    series = [
        ("女性普通劳动者", "diamond", [60.9, 60.5, 60.5, 60.9, 62.1, 62.4, 62.5, 62.8, 63.2, 63.8, 64.4, 65.4, 66.2, 65.9, 67.5, 67.5, 68.8, 66.9, 66.9]),
        ("男性短时间劳动者", "square", [57.0, 55.2, 57.6, 58.0, 57.6, 54.6, 54.0, 55.1, 54.0, 51.5, 51.6, 50.6, 51.1, 50.6, 48.7, 50.0, 50.5, 52.3, 52.2]),
        ("女性短时间劳动者", "triangle", [43.7, 43.1, 43.7, 43.8, 44.6, 43.7, 44.4, 44.5, 43.9, 43.5, 44.2, 43.8, 44.2, 43.7, 43.8, 44.4, 45.1, 46.1, 46.6]),
    ]
    panel = PanelSpec(
        xlim=(1987.5, 2006.5),
        ylim=(40.0, 75.0),
        xticks=years,
        yticks=[float(v) for v in range(40, 76, 5)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="14-8", title=TITLES["14-8"], panels=[panel], width=1000, height=520)
    return render_figure_svg(spec, mode)


def _fig_14_9(mode: ThemeMode = "mono") -> str:
    ages = ["18~19", "20~24", "25~29", "30~34", "35~39", "40~44", "45~49", "50~54", "55~59"]
    xs = [float(i) for i in range(len(ages))]
    series = [
        ("2006年标准劳动者", "diamond", [91.4, 88.9, 85.0, 81.1, 76.8, 74.2, 74.8, 71.7, 70.6]),
        ("2006年普通劳动者平均", "triangle", [90.6, 87.8, 81.3, 75.2, 69.2, 62.3, 59.9, 56.0, 58.4]),
    ]
    panel = PanelSpec(
        xlim=(-0.5, len(ages) - 0.5),
        ylim=(50.0, 95.0),
        xticks=[(float(i), a) for i, a in enumerate(ages)],
        yticks=[float(v) for v in range(50, 96, 5)],
        xlabel="年龄",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="14-9", title=TITLES["14-9"], panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_14_10(mode: ThemeMode = "mono") -> str:
    xs = [0.0, 1.0, 2.0]
    with_leave = [42.86, 30.91, 50.0]
    without_leave = [23.73, 18.07, 20.41]
    panel = PanelSpec(
        xlim=(-0.5, 2.5),
        ylim=(0.0, 60.0),
        xticks=[(0.0, "在1992—1994年生育第一胎"), (1.0, "在1995—1999年生育第一胎"), (2.0, "在2000年以后生育第一胎")],
        yticks=[float(v) for v in range(0, 61, 10)],
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=with_leave, label="已制定育儿休假制度时的继续就业率", color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=xs, y=without_leave, label="未制定育儿休假制度时的继续就业率", color_idx=1, marker="square", width=1.8),
        ],
        annotations=[
            Annotation(x, y, text, dy=-8, arrow=False)
            for x, y, text in zip(xs * 2, with_leave + without_leave, ["42.86", "30.91", "50", "23.73", "18.07", "20.41"])
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="14-10", title=TITLES["14-10"], panels=[panel], width=960, height=520)
    return render_figure_svg(spec, mode)


def _fig_14_11(mode: ThemeMode = "mono") -> str:
    later = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 9.9]
    series = [
        ("夫妻均为大学毕业生，在修订版均等法实施后（1997年以后）生育，失业率为4.0%", [1.3, *later], [100.0, 97.4, 91.7, 86.6, 78.8, 75.2, 69.5, 63.8, 59.2, 53.5]),
        ("夫妻均为大学毕业生，在育儿休假法实施后（1993年以后）至修订版均等法实施前生育，失业率为4.0%", [1.7, *later], [98.7, 97.9, 93.3, 89.1, 84.0, 78.8, 73.6, 69.3, 63.8, 58.6]),
        ("夫妻均为大学毕业生，在均等法实施后至育儿休假法实施前生育，失业率为4.0%", [1.75, *later], [99.0, 98.4, 95.6, 92.8, 89.3, 86.0, 82.2, 78.3, 75.2, 70.7]),
        ("夫妻均为大学毕业生，在均等法实施前（1986年以前）生育，失业率为4.0%", [1.75, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 9.3, 9.6, 9.9], [99.5, 99.3, 97.6, 95.6, 93.8, 91.2, 88.6, 86.0, 83.7, 83.7, 81.7, 80.9]),
    ]
    colors = [5, 2, 1, 0]
    panel = PanelSpec(
        xlim=(1.0, 10.0),
        ylim=(0.0, 100.0),
        xticks=[float(v) for v in range(1, 11)],
        yticks=[float(v) for v in range(0, 101, 10)],
        xlabel="生育第一胎后的年数",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=ys, label=label, color_idx=c, width=2.6, style="solid")
            for c, (label, xs, ys) in zip(colors, series)
        ],
        annotations=[
            Annotation(1.15, 64.0, "↓生育第一胎后失业的女性比例", dy=0, arrow=False, align="start", fontsize=11.0),
            Annotation(1.15, 4.0, "↑生育第一胎后继续雇佣就业的女性比例", dy=0, arrow=False, align="start", fontsize=11.0),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="14-11", title=TITLES["14-11"], panels=[panel], width=1000, height=620)
    return render_figure_svg(spec, mode)


def _fig_15_1(mode: ThemeMode = "mono") -> str:
    years = _years(1971, 2007)
    series = [
        ("整体", "square", [1.23, 1.36, 1.21, 1.36, 1.85, 1.94, 1.94, 2.20, 2.12, 2.01, 2.20, 2.40, 2.68, 2.72, 2.68, 2.82, 2.89, 2.54, 2.28, 2.16, 2.16, 2.23, 2.59, 2.94, 3.25, 3.44, 3.51, 4.22, 4.77, 4.84, 5.10, 5.48, 5.36, 4.84, 4.49, 4.29, 4.00]),
        ("15~34岁", "diamond", [1.58, 1.87, 1.63, 1.77, 2.39, 2.32, 2.68, 2.89, 2.75, 2.72, 2.94, 3.15, 3.44, 3.58, 3.58, 3.77, 3.84, 3.59, 3.27, 3.18, 3.25, 3.43, 3.94, 4.32, 4.81, 5.12, 5.20, 6.04, 6.93, 6.95, 7.29, 7.69, 7.62, 6.97, 6.64, 6.19, 5.88]),
        ("35~54岁", "triangle", [0.83, 0.83, 0.83, 0.92, 1.33, 1.39, 1.33, 1.61, 1.42, 1.38, 1.55, 1.63, 1.92, 1.94, 1.85, 1.99, 1.99, 1.76, 1.54, 1.42, 1.40, 1.44, 1.71, 2.02, 2.18, 2.23, 2.30, 2.87, 3.30, 3.35, 3.67, 4.16, 4.00, 3.75, 3.54, 3.36, 3.30]),
        ("55岁及以上", "cross", [1.47, 1.54, 1.36, 1.47, 1.96, 2.51, 2.47, 2.56, 2.54, 2.54, 2.77, 2.89, 3.18, 3.27, 3.30, 3.30, 3.34, 2.99, 2.59, 2.25, 2.16, 2.06, 2.47, 2.94, 3.13, 3.42, 3.37, 4.20, 4.51, 4.60, 4.82, 4.82, 4.86, 3.99, 3.70, 3.49, 2.99]),
    ]
    panel = PanelSpec(
        xlim=(1970.5, 2007.5),
        ylim=(0.0, 8.0),
        xticks=[float(y) for y in range(1971, 2008, 2)],
        yticks=[float(v) for v in range(9)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.8, hollow=False)
            for i, (label, marker, ys) in enumerate(series)
        ]
        + [_odd_markers(years, ys, i, marker) for i, (_, marker, ys) in enumerate(series)],
        legend_loc="bottom",
        xtick_vertical=True,
    )
    spec = FigureSpec(fig_id="15-1", title=TITLES["15-1"], panels=[panel], width=1000, height=540)
    return render_figure_svg(spec, mode)


def _fig_15_2(mode: ThemeMode = "mono") -> str:
    years = _years(1972, 2007)
    young = [0.0718, -0.0686, 0.0412, 0.120, 0.0118, 0.0275, 0.0404, -0.0255, -0.0067, 0.0392, 0.0267, 0.0431, 0.0176, 0.0, 0.0282, 0.0027, -0.0314, -0.0365, -0.0125, 0.0118, 0.0216, 0.0620, 0.0471, 0.0463, 0.0302, 0.0118, 0.0675, 0.0620, 0.0031, 0.0282, 0.0235, -0.0008, -0.0333, -0.0176, -0.0259, -0.0204]
    middle = [-0.0118, -0.0184, 0.075, 0.169, 0.0255, -0.0176, 0.0725, -0.0451, -0.0275, 0.0588, 0.0314, 0.0686, 0.0196, -0.0314, 0.0294, 0.0098, -0.0667, -0.0667, -0.0314, 0.0039, 0.0125, 0.0706, 0.0682, 0.0431, 0.0149, 0.0176, 0.0961, 0.0725, 0.0059, 0.0471, 0.0569, -0.0059, -0.0243, -0.0196, -0.0224, -0.0157]
    panel = PanelSpec(
        xlim=(1971.5, 2007.5),
        ylim=(-0.10, 0.20),
        xticks=[float(y) for y in range(1972, 2007, 2)],
        yticks=[(v / 100, f"{v / 100:.2f}") for v in range(-10, 21, 5)],
        xlabel="年",
        ylabel="% 上年对数差",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=young, label="15~34岁", color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=years, y=middle, label="35~54岁", color_idx=1, width=1.8),
            _odd_markers(years, young, 0, "diamond"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="15-2", title=TITLES["15-2"], panels=[panel], width=1000, height=520)
    return render_figure_svg(spec, mode)


def _fig_15_3(mode: ThemeMode = "mono") -> str:
    years = _years(1992, 2007)
    panel = PanelSpec(
        xlim=(1991.5, 2007.5),
        ylim=(92.0, 101.0),
        y2lim=(0.0, 3.5),
        xticks=years,
        yticks=[float(v) for v in range(92, 102)],
        y2ticks=[(v / 10, f"{v / 10:.1f}") for v in range(0, 36, 5)],
        xlabel="年",
        ylabel="%",
        y2label="倍",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=[99.7, 99.4, 98.9, 98.6, 98.3, 98.4, 98.1, 96.6, 95.6, 95.8, 94.6, 94.8, 95.7, 96.9, 97.9, 98.1], label="就业率", color_idx=0, marker="square", width=1.8),
            LineSeries(x=years, y=[3.40, 3.21, 2.56, 1.96, 1.88, 1.87, 1.93, 1.65, 1.33, 1.32, 1.34, 1.36, 1.29, 1.52, 1.60, 1.80], label="有效职位空缺率", color_idx=1, marker="diamond", width=1.8, axis="y2", hollow=False),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="15-3", title=TITLES["15-3"], panels=[panel], width=960, height=480)
    return render_figure_svg(spec, mode)


def _fig_15_4(mode: ThemeMode = "mono") -> str:
    years = _years(1987, 2007)
    series = [
        ("初中毕业", "diamond", [40.0, 41.4, 41.5, 43.2, 42.3, 42.3, 43.7, 43.7, 46.0, 47.9, 46.5, 47.9, 45.3, 49.4, 50.9, 48.1, 48.2, 46.8, 45.7, 46.8, 42.9]),
        ("高中毕业", "square", [20.0, 21.3, 21.3, 21.3, 20.4, 19.4, 18.8, 20.1, 21.7, 24.1, 24.5, 24.1, 24.1, 26.4, 26.4, 25.7, 25.7, 25.3, 25.6, 24.4, 22.1]),
        ("短期大学等毕业", "triangle", [13.5, 14.3, 14.1, 14.3, 14.1, 13.9, 13.7, 14.6, 16.4, 17.9, 17.6, 16.8, 17.6, 19.3, 19.3, 19.2, 19.4, 20.0, 20.1, 20.1, 19.1]),
        ("大学毕业", "cross", [10.9, 11.1, 11.1, 10.1, 9.9, 9.9, 9.5, 11.3, 12.4, 13.9, 13.9, 13.1, 14.0, 15.9, 15.9, 15.4, 16.1, 15.4, 15.4, 15.1, 13.1]),
    ]
    panel = PanelSpec(
        xlim=(1986.5, 2007.5),
        ylim=(0.0, 60.0),
        xticks=[float(y) for y in range(1987, 2008, 2)],
        yticks=[float(v) for v in range(0, 61, 10)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="15-4", title=TITLES["15-4"], panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_15_5(mode: ThemeMode = "mono") -> str:
    years = ["1982", "1987", "1992", "1997", "2002", "2003", "2004", "2005", "2006", "2007"]
    xs = [float(i) for i in range(len(years))]
    young = [34, 57, 72, 102, 117, 119, 115, 104, 95, 89]
    older = [17, 23, 29, 49, 91, 98, 99, 97, 92, 92]
    totals = [50, 79, 101, 151, 208, 217, 214, 201, 187, 181]
    annotations = []
    for x, y, o, t in zip(xs, young, older, totals):
        annotations.append(Annotation(x, y + o, str(t), dy=-12, arrow=False))
        annotations.append(Annotation(x, y + o / 2 - 3.0, str(o), dy=0, arrow=False))
        annotations.append(Annotation(x, y / 2 - 3.0, str(y), dy=0, arrow=False))
    panel = PanelSpec(
        xlim=(-0.5, len(years) - 0.5),
        ylim=(0.0, 250.0),
        xticks=[(x, y) for x, y in zip(xs, years)],
        yticks=[float(v) for v in range(0, 251, 50)],
        xlabel="年",
        ylabel="万人",
        zero_line=False,
        bars=[
            BarSeries(x=xs, y=[float(v) for v in older], label="25~34岁", color_idx=4, width=0.62, bottom=[float(v) for v in young]),
            BarSeries(x=xs, y=[float(v) for v in young], label="15~24岁", color_idx=1, width=0.62),
        ],
        annotations=annotations,
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="15-5", title=TITLES["15-5"], panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "13-4": _fig_13_4,
        "13-5": _fig_13_5,
        "14-1": _fig_14_1,
        "14-2": _fig_14_2,
        "14-3": _fig_14_3,
        "14-4": _fig_14_4,
        "14-5": _fig_14_5,
        "14-6": _fig_14_6,
        "14-8": _fig_14_8,
        "14-9": _fig_14_9,
        "14-10": _fig_14_10,
        "14-11": _fig_14_11,
        "15-1": _fig_15_1,
        "15-2": _fig_15_2,
        "15-3": _fig_15_3,
        "15-4": _fig_15_4,
        "15-5": _fig_15_5,
    }
