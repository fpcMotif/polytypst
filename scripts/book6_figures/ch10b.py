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


def _years(a: int, b: int) -> list[float]:
    return [float(y) for y in range(a, b + 1)]


def _fig_10_14(mode: ThemeMode = "mono") -> str:
    series = [
        ("不分年龄段", "diamond", [1.326, 1.338, 1.338, 1.344, 1.352, 1.359, 1.357, 1.350, 1.349, 1.352, 1.355, 1.362, 1.366, 1.377, 1.389, 1.370, 1.370, 1.382, 1.383, 1.391, 1.399, 1.408, 1.446, 1.443]),
        ("55~59岁", "square", [1.520, 1.531, 1.526, 1.545, 1.572, 1.585, 1.581, 1.556, 1.533, 1.546, 1.545, 1.517, 1.520, 1.514, 1.522, 1.494, 1.470, 1.479, 1.469, 1.469, 1.467, 1.466, 1.502, 1.497]),
        ("50~54岁", "triangle", [1.543, 1.568, 1.555, 1.537, 1.535, 1.551, 1.551, 1.525, 1.516, 1.513, 1.494, 1.500, 1.494, 1.488, 1.495, 1.476, 1.452, 1.452, 1.452, 1.434, 1.439, 1.462, 1.507, 1.492]),
        ("45~49岁", "cross", [1.473, 1.477, 1.464, 1.447, 1.441, 1.439, 1.428, 1.429, 1.418, 1.414, 1.410, 1.405, 1.407, 1.412, 1.403, 1.392, 1.383, 1.391, 1.389, 1.425, 1.414, 1.440, 1.484, 1.495]),
        ("40~44岁", "cross", [1.342, 1.332, 1.325, 1.331, 1.323, 1.326, 1.324, 1.319, 1.327, 1.318, 1.317, 1.328, 1.322, 1.337, 1.350, 1.338, 1.356, 1.372, 1.370, 1.374, 1.369, 1.353, 1.402, 1.403]),
        ("35~39岁", "circle", [1.222, 1.225, 1.226, 1.223, 1.223, 1.226, 1.235, 1.226, 1.232, 1.237, 1.248, 1.251, 1.272, 1.276, 1.269, 1.260, 1.266, 1.257, 1.257, 1.271, 1.270, 1.283, 1.291, 1.286]),
        ("30~34岁", "square", [1.127, 1.130, 1.130, 1.142, 1.140, 1.150, 1.156, 1.160, 1.157, 1.161, 1.162, 1.157, 1.162, 1.169, 1.170, 1.170, 1.173, 1.178, 1.185, 1.192, 1.162, 1.173, 1.190, 1.192]),
        ("25~29岁", "triangle", [1.055, 1.055, 1.072, 1.076, 1.079, 1.087, 1.085, 1.083, 1.085, 1.080, 1.078, 1.077, 1.093, 1.092, 1.092, 1.092, 1.089, 1.089, 1.099, 1.117, 1.112, 1.117, 1.121, 1.123]),
    ]
    panel = PanelSpec(
        xlim=(1983.5, 2007.5),
        ylim=(1.0, 1.6),
        xticks=[float(y) for y in range(1984, 2007, 2)],
        yticks=[(1.0, "1.0"), 1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
        xlabel="年",
        ylabel="倍",
        zero_line=False,
        lines=[
            LineSeries(x=_years(1984, 2007), y=ys, label=label, color_idx=i, marker=marker, width=1.6)
            for i, (label, marker, ys) in enumerate(series)
        ],
        annotations=[
            Annotation(x=2003.0, y=1.575, text="差距大", arrow=False, dx=0.0, dy=0.0),
            Annotation(x=2003.0, y=1.03, text="差距小", arrow=False, dx=0.0, dy=0.0),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-14", title="图 10-14 白领和蓝领间的工资差距（制造业，男性）", panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def _fig_10_15(mode: ThemeMode = "mono") -> str:
    def panel(title: str, v2000: list[float], v2005: list[float], side: list[Annotation], legend: bool) -> PanelSpec:
        return PanelSpec(
            title=title,
            xlim=(-0.6, 1.6),
            ylim=(1.4, 2.0),
            xticks=[(0, "所有接受问卷调查的企业"), (1, "成果主义企业")],
            yticks=[1.4, 1.6, 1.8, (2.0, "2.0")],
            ylabel="倍",
            zero_line=False,
            bars=[
                BarSeries(x=[-0.2, 0.8], y=[v - 1.4 for v in v2000], bottom=[1.4, 1.4], label="2000年", color_idx=0, width=0.4),
                BarSeries(x=[0.2, 1.2], y=[v - 1.4 for v in v2005], bottom=[1.4, 1.4], label="2005年", color_idx=1, width=0.4),
            ],
            annotations=[
                Annotation(x=x, y=v, text=f"{v:.2f}", arrow=False, dx=0.0, dy=-8.0)
                for x, v in zip([-0.2, 0.8, 0.2, 1.2], v2000 + v2005, strict=True)
            ]
            + side,
            legend_loc="bottom" if legend else "none",
        )

    spec = FigureSpec(
        fig_id="10-15",
        title="图 10-15 企业内工资差距 (最高级别/最低级别)",
        panels=[
            panel(
                "（1）30~39岁及以下年龄人群",
                [1.57, 1.70],
                [1.69, 1.91],
                [
                    Annotation(x=-0.55, y=1.95, text="↑差距大", arrow=False, dx=0.0, dy=0.0, align="start"),
                    Annotation(x=-0.55, y=1.89, text="差距小↓", arrow=False, dx=0.0, dy=0.0, align="start"),
                ],
                False,
            ),
            panel("（2）50~59岁", [1.50, 1.63], [1.62, 1.80], [], True),
        ],
        rows=2,
        width=860,
        height=720,
    )
    return render_figure_svg(spec, mode)


def _fig_10_16(mode: ThemeMode = "mono") -> str:
    series = [
        ("大型企业/中小企业（1000人以上/10~99人）", "diamond", [1.705, 1.707, 1.717, 1.745, 1.776, 1.779, 1.735, 1.720, 1.700, 1.653, 1.619, 1.619, 1.603, 1.603, 1.653, 1.626, 1.629, 1.610, 1.643, 1.659, 1.688, 1.685, 1.653, 1.672, 1.682, 1.649]),
        ("大型企业/中型企业（1000人以上/100~999人）", "square", [1.385, 1.378, 1.378, 1.400, 1.417, 1.414, 1.407, 1.400, 1.393, 1.360, 1.356, 1.346, 1.318, 1.325, 1.356, 1.346, 1.332, 1.325, 1.347, 1.346, 1.339, 1.353, 1.353, 1.360, 1.376, 1.366]),
        ("中型企业/中小企业（100–999人/10~99人）", "triangle", [1.228, 1.236, 1.243, 1.246, 1.250, 1.255, 1.232, 1.228, 1.214, 1.214, 1.193, 1.199, 1.214, 1.207, 1.218, 1.207, 1.218, 1.211, 1.218, 1.229, 1.262, 1.243, 1.218, 1.225, 1.218, 1.207]),
    ]
    panel = PanelSpec(
        xlim=(1981.5, 2007.5),
        ylim=(1.1, 1.8),
        xticks=[float(y) for y in range(1982, 2008, 5)],
        yticks=[1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8],
        xlabel="年",
        ylabel="倍",
        zero_line=False,
        lines=[
            LineSeries(x=_years(1982, 2007), y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-16", title="图 10-16 按企业规模划分的工资差距（男女合计）", panels=[panel], width=860, height=540)
    return render_figure_svg(spec, mode)


MALE_LARGE_SMALL = "男性，大型企业/中小企业（1000人以上/10~99人）"
FEMALE_LARGE_SMALL = "女性，大型企业/中小企业（1000人以上/10~99人）"


def _gender_panel(
    years: list[float],
    male: list[float],
    female: list[float],
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    xticks: list[float],
    yticks: list[float],
    male_label: str = MALE_LARGE_SMALL,
    female_label: str = FEMALE_LARGE_SMALL,
) -> PanelSpec:
    return PanelSpec(
        xlim=xlim,
        ylim=ylim,
        xticks=xticks,
        yticks=yticks,
        xlabel="年",
        ylabel="倍",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=male, label=male_label, color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=years, y=female, label=female_label, color_idx=1, marker="square", width=1.8),
        ],
        legend_loc="bottom",
    )


def _fig_10_17(mode: ThemeMode = "mono") -> str:
    male = [1.659, 1.667, 1.683, 1.683, 1.722, 1.724, 1.688, 1.679, 1.656, 1.604, 1.596, 1.599, 1.576, 1.584, 1.656, 1.599, 1.607, 1.623, 1.637, 1.650, 1.718, 1.707, 1.697, 1.724, 1.695, 1.693]
    female = [1.570, 1.585, 1.610, 1.662, 1.669, 1.694, 1.705, 1.669, 1.642, 1.580, 1.517, 1.517, 1.484, 1.467, 1.511, 1.490, 1.456, 1.453, 1.459, 1.467, 1.490, 1.473, 1.462, 1.442, 1.423, 1.412]
    panel = _gender_panel(
        _years(1982, 2007), male, female,
        xlim=(1981.5, 2007.5),
        ylim=(1.4, 1.8),
        xticks=[float(y) for y in range(1982, 2008, 5)],
        yticks=[1.4, 1.5, 1.6, 1.7, 1.8],
    )
    spec = FigureSpec(fig_id="10-17", title="图 10-17 不同规模企业间工资差距（按性别划分）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_10_18(mode: ThemeMode = "mono") -> str:
    years = [1987.0, 1992.0, 1997.0, 2002.0, 2007.0]
    panel = _gender_panel(
        years,
        [1.483, 1.408, 1.475, 1.541, 1.504],
        [1.439, 1.326, 1.303, 1.269, 1.217],
        xlim=(1984.5, 2009.5),
        ylim=(1.2, 1.6),
        xticks=years,
        yticks=[1.2, 1.3, 1.4, 1.5, 1.6],
    )
    spec = FigureSpec(fig_id="10-18", title="图 10-18 按企业规模划分的收入差距（雇员）（按性别划分）", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _fig_10_19(mode: ThemeMode = "mono") -> str:
    years = [1997.0, 2002.0, 2007.0]
    panel = _gender_panel(
        years,
        [1.605, 1.685, 1.688],
        [1.354, 1.434, 1.438],
        xlim=(1994.5, 2009.5),
        ylim=(1.2, 1.8),
        xticks=years,
        yticks=[1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8],
    )
    spec = FigureSpec(fig_id="10-19", title="图 10-19 按企业规模划分的收入差距（正规雇员）（按性别划分）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_10_20(mode: ThemeMode = "mono") -> str:
    years = _years(1992, 2007)
    panel = _gender_panel(
        years,
        [1.366, 1.384, 1.407, 1.407, 1.372, 1.414, 1.430, 1.438, 1.479, 1.473, 1.455, 1.491, 1.536, 1.502, 1.606, 1.606],
        [1.287, 1.270, 1.313, 1.321, 1.222, 1.286, 1.266, 1.235, 1.251, 1.235, 1.278, 1.227, 1.208, 1.180, 1.216, 1.219],
        xlim=(1991.5, 2007.5),
        ylim=(1.1, 1.7),
        xticks=years,
        yticks=[1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7],
        male_label="男性",
        female_label="女性",
    )
    spec = FigureSpec(fig_id="10-20", title="图 10-20 不同规模企业间工资差距（按性别划分）——资本金 2 亿日元以上", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _fig_10_21(mode: ThemeMode = "mono") -> str:
    all_ages = [100.0, 101.3, 101.4, 102.6, 103.9, 104.3, 105.3, 105.3, 107.1, 108.1, 108.6, 109.6, 109.0, 111.5, 110.4, 108.5]
    young = [
        ("20~24岁", "square", [100.0, 99.6, 99.2, 99.8, 101.4, 101.7, 104.3, 104.7, 105.9, 105.9, 108.3, 109.2, 108.0, 108.9, 109.5, 108.0]),
        ("25~29岁", "triangle", [100.0, 99.5, 100.4, 101.6, 103.1, 102.5, 103.5, 104.2, 103.9, 105.9, 108.2, 109.9, 108.1, 109.6, 109.4, 107.2]),
        ("30~34岁", "cross", [100.0, 98.8, 98.0, 98.6, 101.2, 101.2, 101.1, 102.5, 103.9, 106.0, 106.1, 106.6, 105.4, 106.4, 105.7, 103.0]),
        ("35~39岁", "circle", [100.0, 101.7, 101.2, 101.4, 103.1, 102.7, 104.0, 103.7, 104.6, 105.7, 105.8, 106.9, 106.9, 106.8, 107.8, 107.4]),
    ]
    old = [
        ("40~44岁", "square", [100.0, 100.5, 100.3, 100.8, 101.6, 101.5, 102.0, 102.7, 103.4, 105.2, 104.3, 105.2, 105.8, 108.1, 107.6, 104.7]),
        ("45~49岁", "triangle", [100.0, 99.3, 99.5, 99.6, 99.9, 100.3, 101.8, 102.3, 102.6, 101.8, 102.3, 103.7, 104.5, 107.5, 106.2, 105.8]),
        ("50~54岁", "cross", [100.0, 101.4, 99.9, 100.0, 101.1, 101.4, 101.1, 101.8, 102.9, 102.8, 103.5, 101.8, 103.3, 103.4, 102.8, 102.3]),
        ("55~59岁", "circle", [100.0, 99.6, 100.7, 100.1, 99.3, 99.9, 100.8, 100.9, 100.8, 102.6, 102.3, 101.3, 101.0, 102.8, 104.0, 104.0]),
    ]
    years = _years(1992, 2007)

    def panel(title: str, groups: list[tuple[str, str, list[float]]]) -> PanelSpec:
        series = [("不分年龄段", "diamond", all_ages), *groups]
        return PanelSpec(
            title=title,
            xlim=(1991.5, 2007.5),
            ylim=(95.0, 115.0),
            xticks=years,
            yticks=[95.0, 100.0, 105.0, 110.0, 115.0],
            xlabel="年",
            zero_line=False,
            lines=[
                LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.6)
                for i, (label, marker, ys) in enumerate(series)
            ],
            legend_loc="bottom",
        )

    spec = FigureSpec(
        fig_id="10-21",
        title="图 10-21 按年龄划分的不同规模企业间工资差距（男性，大型企业/中小企业）",
        panels=[
            panel("（1）40岁以下年龄段与不分年龄段时的比较", young),
            panel("（2）40岁及以上年龄段与不分年龄段时的比较", old),
        ],
        rows=2,
        width=860,
        height=900,
    )
    return render_figure_svg(spec, mode)


def _fig_10_22(mode: ThemeMode = "mono") -> str:
    ages = list(enumerate(["25~29", "30~34", "35~39", "40~44", "45~49", "50~54", "55~59"]))
    xs = [float(i) for i in range(7)]
    by_size = [
        ("（不分学历）", -0.27, [7.23, 3.01, 7.37, 4.71, 5.75, 2.38, 4.04]),
        ("高中毕业人员", 0.0, [4.99, 2.68, 1.32, 2.49, -0.37, 3.73, 3.69]),
        ("大学毕业", 0.27, [6.48, 3.76, 3.77, -5.99, 4.38, -0.76, 3.48]),
    ]
    sizes = PanelSpec(
        title="（1）不同规模企业间工资差距（同等学历人群内部）的变化",
        xlim=(-0.5, 6.5),
        ylim=(-10.0, 10.0),
        xticks=ages,
        yticks=[-10.0, -5.0, 0.0, 5.0, 10.0],
        xlabel="年龄",
        bars=[
            BarSeries(x=[x + dx for x in xs], y=ys, label=label, color_idx=i, width=0.27)
            for i, (label, dx, ys) in enumerate(by_size)
        ],
        legend_loc="bottom",
    )
    schooling = PanelSpec(
        title="（2）不同学历间工资差距的变化（不分企业规模）",
        xlim=(-0.5, 6.5),
        ylim=(-10.0, 15.0),
        xticks=ages,
        yticks=[(v, f"{v:.1f}") for v in (-10.0, -5.0, 0.0, 5.0, 10.0, 15.0)],
        xlabel="年龄",
        bars=[BarSeries(x=xs, y=[2.71, 7.41, 9.01, 10.90, 8.53, -7.31, -4.97], color_idx=0, width=0.4)],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="10-22",
        title="图 10-22 不同规模企业间工资差距（同等学历人群内部）与不同学历间工资差距的变化（1992—2007 年，%）",
        panels=[sizes, schooling],
        rows=2,
        width=860,
        height=860,
    )
    return render_figure_svg(spec, mode)


def _fig_10_23(mode: ThemeMode = "mono") -> str:
    years = _years(1994, 2006)
    labels = [
        ("10亿日元以上", "diamond"),
        ("1000万日元以上5000万日元以内", "triangle"),
        ("1亿日元以上10亿日元以内", "square"),
        ("500万日元以上100万日元以内", "cross"),
    ]
    wages = [
        [100.0, 103.0, 104.8, 105.6, 103.5, 102.5, 106.2, 107.0, 101.2, 102.4, 101.9, 102.9, 103.4],
        [100.0, 101.4, 98.9, 96.7, 96.1, 94.3, 91.9, 91.0, 94.8, 90.1, 87.5, 87.1, 88.7],
        [100.0, 102.6, 102.9, 103.0, 101.8, 99.9, 102.9, 99.3, 100.1, 96.7, 93.3, 92.4, 94.5],
        [100.0, 100.8, 97.9, 96.7, 101.0, 94.3, 93.5, 92.8, 90.6, 86.9, 87.5, 92.5, 82.1],
    ]
    profits = [
        [-77.9, 6.0, 62.5, 63.9, 37.4, 81.6, 131.0, 83.3, 138.0, 171.1, 222.5, 256.8, 276.9],
        [-39.0, -22.7, -18.4, -13.0, -23.3, -17.0, 2.5, -2.9, -1.9, 0.6, 11.0, 15.9, 6.6],
        [-60.7, -23.9, -6.0, -5.6, -9.7, 18.9, 39.9, 20.2, 37.5, 59.9, 65.8, 67.0, 78.4],
        [-38.0, -24.0, -26.9, -15.4, -27.6, -37.7, -12.0, -20.5, -29.1, -12.2, -5.5, -17.0, -4.9],
    ]

    def panel(data: list[list[float]], ylim: tuple[float, float], yticks: list[float]) -> PanelSpec:
        return PanelSpec(
            xlim=(1993.5, 2006.5),
            ylim=ylim,
            xticks=years,
            yticks=yticks,
            xlabel="年",
            zero_line=False,
            lines=[
                LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
                for i, ((label, marker), ys) in enumerate(zip(labels, data, strict=True))
            ],
            legend_loc="bottom",
        )

    spec = FigureSpec(
        fig_id="10-23",
        title="图 10-23 按企业（资本金）规模划分的工资及超额利润（男女合计）",
        panels=[
            panel(wages, (80.0, 110.0), [80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0]),
            panel(profits, (-100.0, 300.0), [-100.0, 0.0, 100.0, 200.0, 300.0]),
        ],
        cols=2,
        width=960,
        height=600,
    )
    return render_figure_svg(spec, mode)


def _fig_10_24(mode: ThemeMode = "mono") -> str:
    years = [1990.0, 1995.0, *_years(1999, 2007)]
    series = [
        ("男女合计", "diamond", [0.0100, 0.0059, 0.0049, 0.0047, 0.0054, 0.0054, 0.0056, 0.0128, 0.0144, 0.0134, 0.0141]),
        ("男性", "square", [0.0090, 0.0076, 0.0077, 0.0076, 0.0086, 0.0100, 0.0095, 0.0172, 0.0183, 0.0170, 0.0175]),
        ("女性", "triangle", [0.0314, 0.0170, 0.0127, 0.0121, 0.0121, 0.0122, 0.0114, 0.0167, 0.0194, 0.0173, 0.0174]),
    ]
    panel = PanelSpec(
        xlim=(1989.5, 2007.5),
        ylim=(0.0, 0.04),
        xticks=[1990.0, 1995.0, 2000.0, 2005.0, 2007.0],
        yticks=[(v, f"{v:.2f}") for v in (0.0, 0.01, 0.02, 0.03, 0.04)],
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-24", title="图 10-24 行业间工资差距——对数化后方差", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _fig_10_25(mode: ThemeMode = "mono") -> str:
    series = [
        ("55~59岁", "diamond", [0.0140, 0.0145, 0.0178, 0.0197, 0.0181, 0.0323, 0.0318, 0.0318, 0.0287]),
        ("50~54岁", "square", [0.0144, 0.0143, 0.0157, 0.0206, 0.0167, 0.0323, 0.0312, 0.0325, 0.0296]),
        ("45~49岁", "triangle", [0.0157, 0.0153, 0.0169, 0.0176, 0.0174, 0.0307, 0.0277, 0.0282, 0.0287]),
        ("40~44岁", "cross", [0.0133, 0.0133, 0.0140, 0.0152, 0.0156, 0.0231, 0.0256, 0.0250, 0.0268]),
        ("35~39岁", "circle", [0.0100, 0.0102, 0.0110, 0.0121, 0.0126, 0.0195, 0.0173, 0.0178, 0.0141]),
        ("30~34岁", "circle", [0.0075, 0.0069, 0.0068, 0.0074, 0.0065, 0.0093, 0.0103, 0.0091, 0.0078]),
        ("25~29岁", "triangle", [0.0020, 0.0020, 0.0021, 0.0025, 0.0024, 0.0046, 0.0045, 0.0041, 0.0032]),
        ("20~24岁", "square", [0.0009, 0.0007, 0.0011, 0.0016, 0.0009, 0.0030, 0.0025, 0.0028, 0.0023]),
    ]
    years = _years(1999, 2007)
    panel = PanelSpec(
        xlim=(1998.5, 2007.5),
        ylim=(0.0, 0.035),
        xticks=years,
        yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(0, 36, 5)],
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.4)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-25", title="图 10-25 行业间工资差距（按年龄划分，男性）——对数化后方差", panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "10-14": _fig_10_14,
        "10-15": _fig_10_15,
        "10-16": _fig_10_16,
        "10-17": _fig_10_17,
        "10-18": _fig_10_18,
        "10-19": _fig_10_19,
        "10-20": _fig_10_20,
        "10-21": _fig_10_21,
        "10-22": _fig_10_22,
        "10-23": _fig_10_23,
        "10-24": _fig_10_24,
        "10-25": _fig_10_25,
    }
