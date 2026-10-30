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


def _fig_9_1(mode: ThemeMode = "mono") -> str:
    xs = _years(1973, 2007)
    school = [5.17, 5.17, 5.12, 5.08, 5.10, 5.10, 5.07, 5.05, 5.03, 5.02, 5.08, 5.08, 5.19, 5.29, 5.29, 5.33, 5.40, 5.40, 5.47, 5.52, 5.59, 5.66, 5.69, 5.77, 5.81, 5.85, 5.92, 6.04, 6.13, 6.17, 6.27, 6.42, 6.55, 6.60, 6.65]
    students = [3.09, 3.15, 3.19, 3.16, 3.09, 3.05, 3.03, 2.95, 2.88, 2.82, 2.85, 2.88, 2.93, 2.99, 3.10, 3.28, 3.49, 3.80, 4.05, 4.32, 4.65, 4.94, 5.12, 5.25, 5.34, 5.46, 5.60, 5.71, 5.88, 6.00, 6.17, 6.48, 6.70, 6.87, 7.00]
    total = [4.75, 4.71, 4.73, 4.78, 4.95, 5.00, 4.92, 5.03, 5.25, 5.60, 5.65, 5.81, 5.98, 6.10, 6.06, 5.87, 5.55, 5.35, 5.18, 4.98, 4.75, 4.63, 4.56, 4.52, 4.48, 4.37, 4.27, 4.12, 4.01, 3.89, 3.76, 3.67, 3.63, 3.62, 3.62]
    rate = [29.8, 31.0, 32.6, 32.8, 32.8, 32.5, 31.8, 31.7, 31.3, 30.6, 29.8, 29.5, 30.2, 30.1, 30.6, 30.8, 30.4, 30.5, 31.5, 32.8, 34.1, 35.8, 37.4, 38.9, 40.3, 42.3, 43.9, 44.8, 44.8, 44.7, 44.6, 45.3, 47.1, 49.0, 50.7]
    private_rate = [33.5, 35.1, 36.7, 37.0, 35.7, 35.4, 35.3, 35.0, 34.5, 33.6, 32.2, 32.9, 33.9, 33.6, 34.2, 34.3, 33.7, 33.6, 34.4, 35.0, 38.5, 40.7, 42.5, 44.8, 46.4, 48.1, 52.5, 53.0, 52.8, 52.5, 53.5, 55.0, 57.5, 59.5, 61.0]
    panel = PanelSpec(
        xlim=(1970.0, 2010.0),
        ylim=(0.0, 8.0),
        xticks=[float(y) for y in range(1970, 2011, 5)],
        yticks=[float(v) for v in range(9)],
        y2lim=(0.0, 70.0),
        y2ticks=[float(v) for v in range(0, 71, 10)],
        xlabel="年",
        y2label="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=school, label="私立初中份额（学校占比%）：左轴", color_idx=2, style="dotted", marker="diamond", width=1.6),
            LineSeries(x=xs, y=students, label="私立初中份额（学生占比%）：左轴", color_idx=4, style="longdash", marker="square", width=1.6),
            LineSeries(x=xs, y=total, label="初中生总数（百万人）：左轴", color_idx=6, style="dashdot", marker="triangle", width=1.6),
            LineSeries(x=xs, y=rate, label="高中毕业生大学升学率：右轴", color_idx=0, width=2.2, axis="y2"),
            LineSeries(x=xs, y=private_rate, label="私立高中毕业生大学升学率：右轴", color_idx=1, style="dashed", width=2.2, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="9-1", title="图 9-1 日本学校教育的发展趋势", panels=[panel], width=860, height=540)
    return render_figure_svg(spec, mode)


def _public_private(xs: list[float], public: list[float], private: list[float]) -> list[LineSeries]:
    return [
        LineSeries(x=xs, y=public, label="公立", color_idx=2, style="dotted", marker="diamond", width=1.8),
        LineSeries(x=xs, y=private, label="私立", color_idx=0, marker="square", width=1.8),
    ]


def _fig_9_2(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1977, 2008, 3)]
    public = [0.4, 0.6, 0.85, 1.1, 1.3, 1.6, 2.05, 2.5, 3.4, 3.6, 4.6]
    private = [6.5, 7.0, 7.66, 9.7, 10.35, 11.36, 12.83, 15.32, 16.74, 18.78, 20.3]
    panel = PanelSpec(
        xlim=(1975.0, 2010.0),
        ylim=(0.0, 25.0),
        xticks=[float(y) for y in range(1975, 2011, 5)],
        yticks=[0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=_public_private(xs, public, private),
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="9-2", title="图 9-2 初中教师中研究生院毕业者的比率", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_9_3(mode: ThemeMode = "mono") -> str:
    xs = _years(1973, 2007)
    public = [0.270, 0.273, 0.293, 0.298, 0.306, 0.309, 0.312, 0.317, 0.323, 0.328, 0.331, 0.331, 0.333, 0.337, 0.340, 0.348, 0.351, 0.359, 0.368, 0.376, 0.381, 0.386, 0.390, 0.395, 0.402, 0.403, 0.403, 0.406, 0.406, 0.406, 0.406, 0.406, 0.409, 0.411, 0.411]
    private = [0.389, 0.390, 0.394, 0.389, 0.386, 0.381, 0.375, 0.370, 0.362, 0.360, 0.354, 0.349, 0.340, 0.329, 0.334, 0.326, 0.331, 0.331, 0.331, 0.334, 0.334, 0.337, 0.339, 0.343, 0.343, 0.343, 0.343, 0.343, 0.343, 0.343, 0.348, 0.351, 0.349, 0.351, 0.350]
    panel = PanelSpec(
        xlim=(1972.5, 2007.5),
        ylim=(0.0, 0.45),
        xticks=[float(y) for y in range(1973, 2008, 2)],
        yticks=[(v / 100, f"{v / 100:.2f}") for v in range(0, 46, 5)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=_public_private(xs, public, private),
        legend_loc="bottom",
        xtick_vertical=True,
    )
    spec = FigureSpec(fig_id="9-3", title="图 9-3 初中教师中女性的比率", panels=[panel], width=900, height=500)
    return render_figure_svg(spec, mode)


def _fig_9_4(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1977, 2008, 3)]
    public = [290.0, 286.0, 280.0, 292.0, 295.0, 307.0, 332.0, 347.0, 371.0, 373.0, 365.0]
    private = [277.0, 287.0, 311.0, 324.0, 332.0, 340.0, 358.0, 363.0, 382.0, 380.0, 377.0]
    panel = PanelSpec(
        xlim=(1975.0, 2009.0),
        ylim=(0.0, 450.0),
        xticks=xs,
        yticks=[float(v) for v in range(0, 451, 50)],
        xlabel="年",
        ylabel="实际月工资额（千日元）",
        zero_line=False,
        lines=_public_private(xs, public, private),
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="9-4", title="图 9-4 本职教师的平均工资水平（以 2005 年消费者物价指数为基准的实际工资）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _scatter_points(pts: list[tuple[float, float]], label: str = "") -> LineSeries:
    xs: list[float] = []
    ys: list[float | None] = []
    for x, y in pts:
        xs += [x, x]
        ys += [y, None]
    return LineSeries(x=xs, y=ys, label=label, color_idx=0, marker="diamond", width=1.0)


def _fig_9_5(mode: ThemeMode = "mono") -> str:
    primary = [
        (1976.67, 130.3), (1979.38, 114.5), (1979.38, 71.1), (1979.97, 141.3), (1980.58, 173.9), (1980.58, 140.2),
        (1980.58, 117.0), (1980.58, 110.0), (1980.58, 101.3), (1980.58, 87.3), (1981.08, 126.4), (1981.08, 167.7),
        (1981.08, 81.6), (1981.10, 153.1), (1981.10, 105.8), (1981.67, 130.6), (1981.67, 169.7), (1981.69, 245.9),
        (1981.69, 95.9), (1982.18, 133.0), (1982.18, 128.0), (1982.18, 124.0), (1982.18, 156.4), (1982.18, 191.6),
        (1982.18, 102.0), (1982.18, 148.9), (1982.18, 90.0), (1982.78, 246.2), (1982.78, 149.7), (1982.78, 114.9),
        (1983.27, 103.6), (1983.30, 158.3), (1983.30, 149.0), (1983.90, 135.1), (1983.90, 98.0), (1983.90, 91.0),
        (1984.39, 132.1), (1984.99, 103.6), (1984.99, 58.5), (1986.08, 84.9),
    ]
    middle = [
        (1974.27, 93.2), (1978.10, 80.5), (1979.16, 81.4), (1980.30, 81.4), (1980.50, 102.2), (1980.50, 59.9),
        (1980.79, 74.0), (1980.79, 70.0), (1981.09, 133.7), (1981.10, 111.3), (1981.37, 105.4), (1981.58, 92.0),
        (1981.58, 88.0), (1981.59, 188.0), (1981.60, 112.3), (1981.60, 105.8), (1981.89, 122.2), (1981.89, 105.0),
        (1981.89, 103.0), (1981.89, 88.3), (1982.18, 168.6), (1982.18, 108.6), (1982.19, 99.5), (1982.21, 77.4),
        (1982.38, 151.0), (1982.38, 122.2), (1982.39, 103.9), (1982.41, 69.2), (1982.70, 133.8), (1982.70, 109.5),
        (1982.70, 106.5), (1982.70, 91.1), (1982.70, 77.4), (1982.70, 70.9), (1982.96, 97.0), (1982.96, 94.5),
        (1982.99, 119.8), (1983.00, 78.2), (1983.19, 107.9), (1983.47, 91.2), (1983.81, 107.5), (1983.82, 53.4),
        (1984.60, 76.7), (1984.92, 83.8), (1985.40, 68.3), (1985.71, 114.5),
    ]
    panels = [
        PanelSpec(
            title="（1）小学图书预算措施率和语文学力的关系",
            xlim=(1976.0, 1988.0),
            ylim=(0.0, 300.0),
            xticks=[float(y) for y in range(1976, 1989, 2)],
            yticks=[float(v) for v in range(0, 301, 50)],
            xlabel="2007年度全国学力调查平均分数（小学六年级语文A）  年",
            ylabel="2006年度小学图书预算措施率（%）",
            zero_line=False,
            lines=[_scatter_points(primary)],
            legend_loc="none",
        ),
        PanelSpec(
            title="（2）初中图书预算措施率和语文学力的关系",
            xlim=(1972.0, 1988.0),
            ylim=(0.0, 200.0),
            xticks=[float(y) for y in range(1972, 1989, 2)],
            yticks=list(zip([25.0 * i for i in range(9)], ["0", "20", "80", "100", "120", "140", "160", "180", "200"])),
            xlabel="2007年度全国学力调查平均分数（初中三年级语文A）  年",
            ylabel="2006年度初中图书预算措施率（%）",
            zero_line=False,
            lines=[_scatter_points(middle)],
            legend_loc="none",
        ),
    ]
    spec = FigureSpec(fig_id="9-5", title="图 9-5 中小学语文学力和图书预算措施率的关系", panels=panels, rows=2, cols=1, width=860, height=900)
    return render_figure_svg(spec, mode)


YEARS_1985_2006 = _years(1985, 2006)


def _wage_panel(ylim: tuple[float, float], yticks: list[float], lines: list[LineSeries], ylabel: str = "") -> PanelSpec:
    return PanelSpec(
        xlim=(1984.5, 2006.5),
        ylim=ylim,
        xticks=[float(y) for y in range(1985, 2007, 2)],
        yticks=yticks,
        xlabel="年",
        ylabel=ylabel,
        zero_line=False,
        lines=lines,
        legend_loc="bottom",
    )


def _fig_11_1(mode: ThemeMode = "mono") -> str:
    xs = YEARS_1985_2006
    male_short = [1544, 1585, 1606, 1644, 1688, 1729, 1805, 1832, 1896, 1896, 1901, 1959, 1951, 1931, 1951, 1956, 1995, 2007, 1999, 1986, 2030, 1998]
    female_general = [932, 949, 981, 1010, 1024, 1053, 1103, 1138, 1184, 1192, 1202, 1239, 1243, 1244, 1277, 1292, 1314, 1356, 1347, 1362, 1356, 1336]
    male_general = [888, 908, 928, 947, 938, 1005, 1052, 1064, 1043, 1029, 1052, 1067, 1009, 1005, 993, 1000, 1009, 981, 995, 1004, 1063, 1044]
    female_short = [680, 692, 704, 721, 726, 757, 791, 822, 836, 843, 850, 857, 847, 853, 860, 867, 874, 881, 887, 892, 932, 925]
    lines = [
        LineSeries(x=xs, y=[float(v) for v in male_short], label="男性短时间劳动者", color_idx=0, marker="square", width=1.6),
        LineSeries(x=xs, y=[float(v) for v in female_general], label="女性一般劳动者", color_idx=1, marker="square", width=1.6),
        LineSeries(x=xs, y=[float(v) for v in male_general], label="男性一般劳动者", color_idx=2, marker="triangle", width=1.6),
        LineSeries(x=xs, y=[float(v) for v in female_short], label="女性短时间劳动者", color_idx=3, marker="triangle", width=1.6),
    ]
    panel = _wage_panel((500.0, 2100.0), [float(v) for v in range(500, 2101, 200)], lines, ylabel="日元")
    spec = FigureSpec(fig_id="11-1", title="图 11-1 每小时规定工资额的变化（用以 2005 年为基准的消费者物价指数调整）", panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_11_2(mode: ThemeMode = "mono") -> str:
    xs = YEARS_1985_2006
    short = [76, 76, 76, 76, 77, 75, 75, 77, 80, 82, 80, 81, 84, 85, 87, 87, 86, 90, 89, 89, 88, 89]
    general = [60, 60, 61, 61, 61, 61, 61, 62, 62, 63, 63, 64, 64, 65, 65, 66, 66, 68, 68, 69, 67, 67]
    everyone = [57.7, 57.4, 58.2, 58.1, 57.3, 57.6, 57.9, 58.9, 58.5, 58.8, 59.3, 59.1, 59.0, 59.5, 59.7, 60.3, 59.8, 60.8, 60.9, 61.3, 61.4, 61.6]
    reference = [56.2, 56.0, 56.4, 56.6, 55.9, 55.7, 56.2, 57.3, 57.1, 57.5, 57.7, 57.8, 57.6, 58.2, 58.3, 58.9, 58.6, 60.0, 59.4, 60.1, 60.2, 60.3]
    lines = [
        LineSeries(x=xs, y=[float(v) for v in short], label="短时间劳动者", color_idx=1, marker="square", width=1.6),
        LineSeries(x=xs, y=[float(v) for v in general], label="一般劳动者", color_idx=3, marker="triangle", width=1.6),
        LineSeries(x=xs, y=everyone, label="所有劳动者", color_idx=0, marker="circle", width=1.6),
        LineSeries(x=xs, y=reference, label="所有劳动者（参考）", color_idx=2, marker="triangle", width=1.6),
    ]
    panel = _wage_panel((50.0, 95.0), [float(v) for v in range(50, 96, 5)], lines)
    spec = FigureSpec(fig_id="11-2", title="图 11-2 女性相对工资的变化（每小时规定工资额，男性 = 100）", panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_11_3(mode: ThemeMode = "mono") -> str:
    xs = YEARS_1985_2006
    male = [57, 57, 57, 57, 55, 58, 58, 58, 55, 54, 55, 54, 52, 52, 51, 51, 51, 49, 50, 51, 53, 53]
    female = [73, 73, 72, 71, 71, 72, 72, 72, 70, 71, 70, 69, 68, 68, 67, 67, 66, 65, 66, 66, 69, 70]
    everyone = [52, 52, 52, 52, 51, 51, 52, 53, 51, 52, 52, 51, 50, 51, 50, 51, 50, 50, 50, 51, 53, 54]
    lines = [
        LineSeries(x=xs, y=[float(v) for v in male], label="男性", color_idx=3, marker="triangle", width=1.6),
        LineSeries(x=xs, y=[float(v) for v in female], label="女性", color_idx=1, marker="square", width=1.6),
        LineSeries(x=xs, y=[float(v) for v in everyone], label="所有劳动者", color_idx=0, marker="circle", width=1.6),
    ]
    panel = _wage_panel((45.0, 75.0), [float(v) for v in range(45, 76, 5)], lines)
    spec = FigureSpec(fig_id="11-3", title="图 11-3 短时间劳动者相对工资的变化（每小时规定工资，一般劳动者 = 100）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_11_4(mode: ThemeMode = "mono") -> str:
    xs = _years(1982, 2006)
    actual = [0.5851, 0.5859, 0.5844, 0.5960, 0.5964, 0.6038, 0.6042, 0.6022, 0.6022, 0.6066, 0.6150, 0.6155, 0.6203, 0.6250, 0.6272, 0.6315, 0.6390, 0.6467, 0.6550, 0.6532, 0.6655, 0.6685, 0.6767, 0.6594, 0.6597]
    fixed = {
        "教育水平（1986）": [0.5884, 0.5893, 0.5875, 0.5960, 0.5964, 0.6035, 0.6022, 0.5992, 0.5986, 0.6007, 0.6083, 0.6060, 0.6093, 0.6120, 0.6132, 0.6140, 0.6192, 0.6260, 0.6318, 0.6296, 0.6397, 0.6409, 0.6464, 0.6302, 0.6305],
        "连续工龄（1986）": [0.5814, 0.5840, 0.5849, 0.5941, 0.5959, 0.6062, 0.6039, 0.6022, 0.6033, 0.6098, 0.6148, 0.6154, 0.6198, 0.6227, 0.6243, 0.6274, 0.6333, 0.6386, 0.6448, 0.6464, 0.6568, 0.6596, 0.6640, 0.6500, 0.6500],
        "年龄结构（1986）": [0.5786, 0.5813, 0.5818, 0.5941, 0.5963, 0.6058, 0.6044, 0.6039, 0.6047, 0.6094, 0.6152, 0.6161, 0.6221, 0.6260, 0.6283, 0.6313, 0.6372, 0.6455, 0.6533, 0.6531, 0.6644, 0.6663, 0.6729, 0.6566, 0.6566],
    }
    titles = ["（a）1986年的教育水平", "（b）1986年的连续工龄", "（c）1986年的年龄结构成"]
    panels = [
        PanelSpec(
            title=title,
            xlim=(1981.5, 2006.5),
            ylim=(0.56, 0.70),
            xticks=[float(y) for y in range(1982, 2007, 2)],
            yticks=[(v / 100, f"{v / 100:.2f}") for v in range(56, 71, 2)],
            xlabel="年",
            zero_line=False,
            lines=[
                LineSeries(x=xs, y=actual, label="实际", color_idx=0, marker="square", width=1.6),
                LineSeries(x=xs, y=ys, label=label, color_idx=1, marker="square", width=1.6),
            ],
            legend_loc="bottom",
        )
        for title, (label, ys) in zip(titles, fixed.items())
    ]
    spec = FigureSpec(fig_id="11-4", title="图 11-4 女性相对工资", panels=panels, rows=3, cols=1, width=860, height=1050)
    return render_figure_svg(spec, mode)


def _fig_11_5(mode: ThemeMode = "mono") -> str:
    xs = YEARS_1985_2006
    men_over_median = [90.76, 90.96, 91.25, 91.76, 91.13, 90.31, 90.19, 89.90, 89.51, 89.00, 89.37, 89.66, 89.44, 89.38, 89.23, 88.91, 88.75, 88.44, 88.31, 87.49, 87.49, 86.99]
    men_over_mean = [87.53, 87.02, 86.79, 87.52, 86.99, 86.88, 87.37, 87.26, 86.97, 86.56, 86.94, 87.14, 87.05, 86.81, 86.20, 85.70, 85.22, 84.61, 83.99, 82.80, 82.68, 81.79]
    women_over_median = [8.35, 8.35, 8.22, 8.03, 8.20, 8.50, 8.31, 8.43, 8.70, 8.78, 8.78, 8.67, 8.94, 9.38, 9.76, 10.14, 10.73, 11.76, 11.92, 12.34, 12.45, 12.7]
    women_over_mean = [5.23, 5.35, 5.50, 5.69, 5.41, 5.47, 5.41, 5.55, 5.64, 5.84, 5.93, 6.00, 6.00, 6.43, 6.31, 6.49, 7.00, 7.60, 7.60, 7.79, 7.79, 7.7]
    panel = PanelSpec(
        xlim=(1984.5, 2006.5),
        ylim=(80.0, 94.0),
        xticks=[float(y) for y in range(1985, 2007, 2)],
        yticks=[float(v) for v in range(80, 95, 2)],
        y2lim=(0.0, 14.0),
        y2ticks=[float(v) for v in range(0, 15, 2)],
        xlabel="年",
        ylabel="%",
        y2label="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=men_over_median, label="女性的中位数以上的男性（左轴）", color_idx=3, marker="triangle", width=1.6),
            LineSeries(x=xs, y=men_over_mean, label="女性的平均值以上的男性（左轴）", color_idx=1, marker="square", width=1.6),
            LineSeries(x=xs, y=women_over_median, label="男性的中位数以上的女性（右轴）", color_idx=0, marker="triangle", width=1.6, axis="y2"),
            LineSeries(x=xs, y=women_over_mean, label="男性的平均值以上的女性（右轴）", color_idx=2, marker="square", width=1.6, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="11-5", title="图 11-5 （a） 年收入在异性的中位数和平均值以上的劳动者比例", panels=[panel], width=860, height=540)
    return render_figure_svg(spec, mode)


def _label(x: float, y: float, text: str, axis: str = "y1") -> Annotation:
    return Annotation(x=x, y=y, text=text, dx=0.0, dy=0.0, arrow=False, axis=axis, fontsize=11.5)


def _fig_12_1(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1955, 2001, 5)]
    top5 = [3.45, 1.49, 2.37, 2.77, 4.52, 4.52, 5.65, 5.12, 6.43, 6.62]
    national = [1.85, 0.78, 1.33, 1.33, 2.28, 2.48, 3.34, 3.00, 4.25, 4.70]
    bottom5 = [0.78, 0.30, 0.72, 0.68, 1.32, 1.42, 1.91, 1.82, 2.50, 3.11]
    gap = [4.36, 4.21, 3.47, 3.87, 3.29, 3.02, 2.87, 2.74, 2.50, 2.01]
    panel = PanelSpec(
        xlim=(1952.0, 2003.0),
        ylim=(0.0, 7.0),
        xticks=xs,
        yticks=[(float(v), f"{v:.1f}") for v in range(8)],
        y2lim=(0.0, 5.0),
        y2ticks=[(v / 2, f"{v / 2:.1f}") for v in range(11)],
        xlabel="年",
        ylabel="完全失业率（%）",
        y2label="前5个县/后5个县平均（%）",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=top5, label="前5个县平均", color_idx=0, width=2.4),
            LineSeries(x=xs, y=national, label="全国平均", color_idx=4, style="solid", width=2.0),
            LineSeries(x=xs, y=bottom5, label="后5个县平均", color_idx=0, style="dotted", width=2.6),
            LineSeries(x=xs, y=gap, label="位居前列与位居后列的差距（右轴）", color_idx=2, style="dashed", marker="square", width=1.8, axis="y2"),
        ],
        annotations=[
            _label(1965.5, 6.35, "位居前列与位居"),
            _label(1965.5, 5.6, "后列的差距（右轴）"),
            _label(1988.0, 6.35, "前5个县平均"),
            _label(1967.0, 1.75, "全国平均"),
            _label(1986.5, 1.15, "后5个县平均"),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="12-1", title="图 12-1 战后各地区完全失业率的变化", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


YEARS_1983_2007 = _years(1983, 2007)


def _gini_panel(ylim: tuple[float, float], yticks: list[tuple[float, str]], y2lim: tuple[float, float], y2ticks: list[tuple[float, str]], y2label: str, lines: list[LineSeries], annotations: list[Annotation]) -> PanelSpec:
    return PanelSpec(
        xlim=(1982.5, 2007.5),
        ylim=ylim,
        xticks=[float(y) for y in range(1983, 2008, 2)],
        yticks=yticks,
        y2lim=y2lim,
        y2ticks=y2ticks,
        xlabel="年",
        ylabel="基尼系数",
        y2label=y2label,
        zero_line=False,
        lines=lines,
        annotations=annotations,
        legend_loc="none",
    )


def _fig_12_2(mode: ThemeMode = "mono") -> str:
    xs = YEARS_1983_2007
    regions = [0.1352, 0.1384, 0.1360, 0.1300, 0.1310, 0.1325, 0.1276, 0.1258, 0.1225, 0.1050, 0.0984, 0.1011, 0.1068, 0.0934, 0.0905, 0.0925, 0.0853, 0.0932, 0.0870, 0.0940, 0.0955, 0.0865, 0.0942, 0.0987, 0.0979]
    prefectures: list[float | None] = [None] * 14 + [0.1334, 0.1259, 0.1187, 0.1181, 0.1130, 0.1175, 0.1157, 0.1138, 0.1167, 0.1294, 0.1250]
    unemployment = [2.6, 2.7, 2.6, 2.8, 2.8, 2.5, 2.3, 2.1, 2.1, 2.2, 2.5, 2.9, 3.2, 3.4, 3.4, 4.1, 4.7, 4.7, 5.0, 5.4, 5.3, 4.7, 4.4, 4.1, 3.9]
    panel = _gini_panel(
        (0.08, 0.15),
        [(v / 100, f"{v / 100:.2f}") for v in range(8, 16)],
        (0.0, 6.0),
        [float(v) for v in range(7)],
        "完全失业率（%）",
        [
            LineSeries(x=xs, y=regions, label="地理分区的差距", color_idx=0, width=2.4),
            LineSeries(x=xs, y=prefectures, label="都道府县的差距", color_idx=0, style="dotted", width=2.6),
            LineSeries(x=xs, y=unemployment, label="完全失业率（右轴）", color_idx=2, style="dashed", marker="square", width=1.8, axis="y2"),
        ],
        [
            _label(1987.0, 0.1430, "地理分区"),
            _label(1987.0, 0.1365, "的差距"),
            _label(2003.0, 0.1250, "都道府县"),
            _label(2003.0, 0.1185, "的差距"),
            _label(1988.5, 0.0990, "完全失业率"),
            _label(1988.5, 0.0925, "（右轴）"),
        ],
    )
    spec = FigureSpec(fig_id="12-2", title="图 12-2 完全失业率的地区间差距", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _fig_12_3(mode: ThemeMode = "mono") -> str:
    xs = YEARS_1983_2007
    regions = [0.2031, 0.2225, 0.2283, 0.2050, 0.1937, 0.1996, 0.1993, 0.1930, 0.1860, 0.1686, 0.1565, 0.1625, 0.1478, 0.1268, 0.1351, 0.1247, 0.1142, 0.1121, 0.1120, 0.1046, 0.1060, 0.1300, 0.1374, 0.1390, 0.1392]
    prefectures = [0.2345, 0.2526, 0.2571, 0.2341, 0.2230, 0.2230, 0.2210, 0.2180, 0.2055, 0.2000, 0.1895, 0.1880, 0.1860, 0.1760, 0.1800, 0.1750, 0.1660, 0.1640, 0.1570, 0.1435, 0.1430, 0.1700, 0.1750, 0.1770, 0.1810]
    vacancy = [0.60, 0.65, 0.68, 0.62, 0.70, 1.01, 1.25, 1.40, 1.40, 1.08, 0.76, 0.64, 0.63, 0.70, 0.72, 0.53, 0.48, 0.59, 0.59, 0.54, 0.64, 0.83, 0.95, 1.06, 1.04]
    panel = _gini_panel(
        (0.08, 0.28),
        [(v / 100, f"{v / 100:.2f}") for v in range(8, 29, 2)],
        (0.0, 1.6),
        [(0.0, "0"), (0.2, "0.2"), (0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1"), (1.2, "1.2"), (1.4, "1.4"), (1.6, "1.6")],
        "有效职位空缺率（倍）",
        [
            LineSeries(x=xs, y=regions, label="地理分区的差距", color_idx=0, width=2.4),
            LineSeries(x=xs, y=prefectures, label="都道府县的差距", color_idx=0, style="dotted", width=2.6),
            LineSeries(x=xs, y=vacancy, label="有效职位空缺率（右轴）", color_idx=2, style="dashed", marker="square", width=1.8, axis="y2"),
        ],
        [
            _label(1994.0, 0.2600, "有效职位空缺率"),
            _label(1994.0, 0.2450, "（右轴）"),
            _label(2000.3, 0.1910, "都道府县"),
            _label(2000.3, 0.1760, "的差距"),
            _label(1993.0, 0.1400, "地理分区"),
            _label(1993.0, 0.1250, "的差距"),
        ],
    )
    spec = FigureSpec(fig_id="12-3", title="图 12-3 有效职位空缺率的地区间差距", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _fig_12_4(mode: ThemeMode = "mono") -> str:
    countries = ["意大利", "芬兰", "葡萄牙", "德国", "加拿大", "瑞典", "日本", "美国", "挪威", "英国", "西班牙", "土耳其", "比利时", "法国", "英国", "澳大利亚", "新西兰", "荷兰"]
    y1987 = [46.8, 39.6, 36.6, 33.2, 29.8, 30.2, 30.1, 28.0, 27.0, 25.1, 23.8, 21.0, 20.0, 16.0, 16.0, 15.9, 12.5, 7.1]
    y2003: list[float | None] = [79.2, 21.3, 25.6, None, 23.9, 16.3, 20.8, 14.3, 10.6, 30.9, 33.9, 38.6, 45.9, 19.2, 18.0, 8.7, 15.5, 12.4]
    idx = list(range(18))
    panel = PanelSpec(
        xlim=(-0.6, len(idx) - 0.4),
        ylim=(0.0, 90.0),
        xticks=[(float(k), countries[i]) for k, i in enumerate(idx)],
        yticks=[float(v) for v in range(0, 91, 10)],
        ylabel="变异系数（×100）",
        zero_line=False,
        bars=[
            BarSeries(x=[k - 0.19 for k in range(len(idx))], y=[y1987[i] for i in idx], label="1987年", color_idx=2, width=0.36),
            BarSeries(x=[k + 0.19 for k, i in enumerate(idx) if y2003[i] is not None], y=[v for i in idx if (v := y2003[i]) is not None], label="2003年", color_idx=0, width=0.36),
        ],
        legend_loc="bottom",
        xtick_vertical=True,
    )
    spec = FigureSpec(fig_id="12-4", title="图 12-4 OECD 成员国失业率的地区间差距（1987 年、2003 年）", panels=[panel], width=1000, height=560)
    return render_figure_svg(spec, mode)


def _fig_12_5(mode: ThemeMode = "mono") -> str:
    xs = _years(1972, 2007)
    gross_all = [3.87, 3.86, 3.59, 3.30, 3.15, 3.11, 3.00, 2.97, 2.86, 2.80, 2.77, 2.66, 2.59, 2.55, 2.55, 2.58, 2.53, 2.53, 2.55, 2.53, 2.49, 2.45, 2.41, 2.40, 2.35, 2.33, 2.29, 2.20, 2.20, 2.19, 2.14, 2.10, 2.06, 2.05, 2.00, 2.00]
    gross_men = [4.35, 4.42, 4.02, 3.72, 3.55, 3.50, 3.40, 3.33, 3.24, 3.21, 3.15, 3.05, 2.99, 2.99, 2.99, 3.03, 3.01, 3.04, 3.02, 2.97, 2.92, 2.88, 2.81, 2.79, 2.74, 2.72, 2.68, 2.61, 2.55, 2.53, 2.48, 2.43, 2.39, 2.35, 2.34, 2.32]
    net_all = [4.03, 4.10, 3.33, 2.70, 2.42, 2.33, 2.33, 2.33, 2.14, 1.96, 1.71, 1.44, 1.34, 1.46, 1.76, 2.31, 2.32, 2.27, 2.01, 1.63, 1.44, 1.25, 1.07, 0.95, 0.61, 0.73, 0.83, 0.85, 0.95, 1.13, 1.17, 1.08, 1.04, 1.22, 1.40, 1.58]
    net_men = [4.28, 4.44, 3.55, 2.85, 2.68, 2.57, 2.55, 2.49, 2.29, 2.09, 1.86, 1.59, 1.60, 1.87, 2.15, 2.62, 2.62, 2.61, 2.30, 1.88, 1.62, 1.42, 1.20, 1.05, 0.70, 0.76, 0.86, 0.88, 0.97, 1.14, 1.17, 1.12, 1.10, 1.25, 1.52, 1.68]
    panel = PanelSpec(
        xlim=(1971.5, 2007.5),
        ylim=(0.0, 5.0),
        xticks=[float(y) for y in range(1972, 2007, 2)],
        yticks=[(v / 2, f"{v / 2:.1f}") for v in range(11)],
        y2lim=(0.0, 0.45),
        y2ticks=[(v / 100, f"{v / 100:.2f}") for v in range(0, 46, 5)],
        xlabel="年",
        ylabel="总迁移率（%）",
        y2label="净迁移率（%）",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=gross_all, label="总迁移率（男女合计）", color_idx=4, style="solid", width=2.0),
            LineSeries(x=xs, y=gross_men, label="总迁移率（男性）", color_idx=5, style="dotted", width=2.4),
            LineSeries(x=xs, y=[round(v * 0.09, 4) for v in net_all], label="净迁移率（男女合计）", color_idx=0, width=2.6, axis="y2"),
            LineSeries(x=xs, y=[round(v * 0.09, 4) for v in net_men], label="净迁移率（男性）", color_idx=2, style="dotted", width=2.6, axis="y2"),
        ],
        annotations=[
            Annotation(x=1993.8, y=2.98, text="总迁移率（男性）", dx=0.0, dy=-62.0),
            Annotation(x=1986.0, y=2.60, text="总迁移率（男女合计）", dx=0.0, dy=-62.0),
            Annotation(x=1979.8, y=2.05, text="净迁移率（男女合计）", dx=0.0, dy=70.0),
            Annotation(x=1994.8, y=1.02, text="净迁移率（男性）", dx=60.0, dy=-45.0),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="12-5", title="图 12-5 都道府县之间人口迁移率的变化", panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def _milli(values: list[float | None]) -> list[float | None]:
    return [None if v is None else round(v / 1000, 5) for v in values]


def _fig_12_6(mode: ThemeMode = "mono") -> str:
    xa = _years(1983, 2003)
    sna68 = _milli([99.0, 97.6, 99.1, 101.9, 102.6, 106.5, 110.6, 111.5, 107.5, 100.1, 93.8, 88.2, 87.4, 86.4, 85.4, 81.2, 81.6, None, None, None, None])
    sna93 = _milli([None] * 7 + [109.0, 103.7, 97.7, 91.5, 85.1, 85.6, 84.5, 86.0, 85.5, 86.0, 84.7, 84.7, 87.3, 91.4])
    xb = [1982.0, 1987.0, 1992.0, 1997.0, 2002.0, 2007.0]
    nominal = [0.0658, 0.0820, 0.0779, 0.0606, 0.0588, 0.0686]
    real: list[float | None] = [0.0548, 0.0668, 0.0644, 0.0508, 0.0498, None]
    panels = [
        PanelSpec(
            title="（a）人均县民收入",
            xlim=(1982.5, 2003.5),
            ylim=(0.060, 0.120),
            xticks=[float(y) for y in range(1983, 2004, 4)],
            yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(60, 121, 10)],
            xlabel="年",
            ylabel="基尼系数",
            zero_line=False,
            lines=[
                LineSeries(x=xa, y=sna68, label="68SNA（1990年基准）", color_idx=4, style="solid", width=2.2),
                LineSeries(x=xa, y=sna93, label="93SNA（1995年基准）", color_idx=0, style="dotted", width=2.6),
            ],
            annotations=[
                Annotation(x=1986.0, y=0.1043, text="68SNA（1990年基准）", dx=-30.0, dy=-36.0, align="start"),
                Annotation(x=1996.0, y=0.0853, text="93SNA（1995年基准）", dx=0.0, dy=40.0),
            ],
            legend_loc="none",
        ),
        PanelSpec(
            title="（b）家庭收入（2人以上家庭）",
            xlim=(1980.5, 2008.5),
            ylim=(0.040, 0.085),
            xticks=xb,
            yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(40, 86, 5)],
            xlabel="年",
            ylabel="基尼系数",
            zero_line=False,
            lines=[
                LineSeries(x=xb, y=nominal, label="名义收入", color_idx=4, style="solid", width=2.2),
                LineSeries(x=xb, y=real, label="实际收入", color_idx=0, style="dotted", width=2.6),
            ],
            annotations=[
                Annotation(x=1993.0, y=0.0760, text="名义收入", dx=40.0, dy=-22.0, align="start"),
                Annotation(x=1990.2, y=0.0648, text="实际收入", dx=0.0, dy=52.0),
            ],
            legend_loc="none",
        ),
    ]
    spec = FigureSpec(fig_id="12-6", title="图 12-6 都道府县之间收入指数的差距", panels=panels, rows=1, cols=2, width=1000, height=520)
    return render_figure_svg(spec, mode)


def _two_series_gini_panel(title: str, ylim: tuple[float, float], prefectures: list[float], regions: list[float], annotations: list[Annotation]) -> PanelSpec:
    xs = _years(1982, 2006)
    top = round(ylim[1] * 1000)
    return PanelSpec(
        title=title,
        xlim=(1981.5, 2006.5),
        ylim=ylim,
        xticks=[float(y) for y in range(1982, 2007, 2)],
        yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(60, top + 1, 5)],
        xlabel="年",
        ylabel="基尼系数",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=prefectures, label="都道府县", color_idx=4, style="solid", width=2.2),
            LineSeries(x=xs, y=regions, label="地理分区", color_idx=0, style="dotted", width=2.6),
        ],
        annotations=annotations,
        legend_loc="none",
        xtick_vertical=True,
    )


def _fig_12_7(mode: ThemeMode = "mono") -> str:
    a_pref = [0.0870, 0.0860, 0.0880, 0.0890, 0.0890, 0.0890, 0.0890, 0.0920, 0.0930, 0.0880, 0.0860, 0.0840, 0.0820, 0.0810, 0.0830, 0.0780, 0.0800, 0.0770, 0.0770, 0.0790, 0.0840, 0.0820, 0.0830, 0.0870, 0.0870]
    a_reg = [0.0770, 0.0770, 0.0780, 0.0790, 0.0800, 0.0800, 0.0800, 0.0830, 0.0850, 0.0815, 0.0790, 0.0785, 0.0757, 0.0750, 0.0767, 0.0730, 0.0745, 0.0740, 0.0730, 0.0745, 0.0780, 0.0760, 0.0770, 0.0810, 0.0790]
    b_pref = [0.0980, 0.0970, 0.0990, 0.1000, 0.1010, 0.1000, 0.0990, 0.1030, 0.1040, 0.0995, 0.0955, 0.0935, 0.0910, 0.0900, 0.0920, 0.0870, 0.0895, 0.0865, 0.0860, 0.0880, 0.0945, 0.0910, 0.0935, 0.0970, 0.0985]
    b_reg = [0.0890, 0.0880, 0.0890, 0.0910, 0.0920, 0.0910, 0.0900, 0.0950, 0.0970, 0.0940, 0.0920, 0.0910, 0.0890, 0.0880, 0.0890, 0.0855, 0.0875, 0.0865, 0.0860, 0.0870, 0.0900, 0.0880, 0.0880, 0.0940, 0.0930]
    panels = [
        _two_series_gini_panel(
            "（a）基本工资",
            (0.060, 0.100),
            a_pref,
            a_reg,
            [
                Annotation(x=1992.4, y=0.0862, text="都道府县", dx=90.0, dy=-60.0),
                Annotation(x=1987.6, y=0.0795, text="地理分区", dx=0.0, dy=90.0),
            ],
        ),
        _two_series_gini_panel(
            "（b）年度工资",
            (0.060, 0.110),
            b_pref,
            b_reg,
            [
                Annotation(x=1991.7, y=0.0970, text="都道府县", dx=90.0, dy=-50.0),
                Annotation(x=1989.0, y=0.0915, text="地理分区", dx=0.0, dy=90.0),
            ],
        ),
    ]
    spec = FigureSpec(fig_id="12-7", title="图 12-7 地区间每小时工资差距", panels=panels, rows=1, cols=2, width=1000, height=620)
    return render_figure_svg(spec, mode)


def _fig_12_8(mode: ThemeMode = "mono") -> str:
    xs = _years(1993, 2006)
    general = [0.0720, 0.0710, 0.0720, 0.0721, 0.0702, 0.0730, 0.0722, 0.0722, 0.0722, 0.0762, 0.0754, 0.0753, 0.0794, 0.0817]
    salaried = [0.0630, 0.0668, 0.0624, 0.0580, 0.0620, 0.0630, 0.0620, 0.0691, 0.0670, 0.0642, 0.0702, 0.0731, 0.0711, 0.0730]
    panel = PanelSpec(
        xlim=(1992.5, 2006.5),
        ylim=(0.050, 0.085),
        xticks=[float(y) for y in xs],
        yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(50, 86, 5)],
        xlabel="年",
        ylabel="基尼系数",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=general, label="普通劳动者", color_idx=0, style="dotted", width=2.6),
            LineSeries(x=xs, y=salaried, label="工薪阶层", color_idx=4, style="solid", width=2.2),
        ],
        annotations=[
            Annotation(x=1996.6, y=0.0713, text="普通劳动者", dx=0.0, dy=-60.0),
            Annotation(x=2002.6, y=0.0668, text="工薪阶层", dx=0.0, dy=70.0),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="12-8", title="图 12-8 地理分区之间年度工资的差距", panels=[panel], width=1000, height=500)
    return render_figure_svg(spec, mode)


PERIODS_0_15 = [float(t) for t in range(16)]


def _response_panel(title: str, ylim: tuple[float, float], full: list[float], recent: list[float]) -> PanelSpec:
    lo, hi = round(ylim[0] * 1000), round(ylim[1] * 1000)
    return PanelSpec(
        title=title,
        xlim=(-0.5, 15.5),
        ylim=ylim,
        xticks=PERIODS_0_15,
        yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(lo, hi + 1, 2)],
        zero_line=lo < 0,
        lines=[
            LineSeries(x=PERIODS_0_15, y=full, label="1983—2007", color_idx=4, style="solid", width=2.2),
            LineSeries(x=PERIODS_0_15, y=recent, label="1991—2007", color_idx=0, style="dotted", width=2.6),
        ],
        legend_loc="bottom",
    )


def _fig_12_9(mode: ThemeMode = "mono") -> str:
    panels = [
        _response_panel(
            "（a）相对地区就业",
            (0.0, 0.012),
            [0.0, 0.0100, 0.0099, 0.0082, 0.0082, 0.0085, 0.0084] + [0.0084] * 9,
            [0.0, 0.0100, 0.0104, 0.0073, 0.0070, 0.0080, 0.0081, 0.0077] + [0.0078] * 8,
        ),
        _response_panel(
            "（b）相对地区失业率",
            (0.0, 0.012),
            [0.0, 0.0100, 0.0058, 0.0055, 0.0045, 0.0036, 0.0029, 0.0024, 0.0019, 0.0016, 0.0013, 0.0011, 0.0009, 0.0007, 0.0006, 0.0005],
            [0.0, 0.0096, 0.0055, 0.0054, 0.0043, 0.0035, 0.0028, 0.0023, 0.0019, 0.0015, 0.0012, 0.0010, 0.0007, 0.0005, 0.0004, 0.0003],
        ),
        _response_panel(
            "（c）各地区失业率",
            (0.0, 0.014),
            [0.0, 0.0102, 0.0127, 0.0127, 0.0116, 0.0105, 0.0094, 0.0083, 0.0071, 0.0062, 0.0055, 0.0048, 0.0042, 0.0035, 0.0029, 0.0025],
            [0.0, 0.0102, 0.0110, 0.0092, 0.0072, 0.0054, 0.0042, 0.0030, 0.0022, 0.0016, 0.0011, 0.0008, 0.0005, 0.0003, 0.0001, 0.0001],
        ),
        _response_panel(
            "（d）相对劳动力参与率",
            (-0.002, 0.012),
            [0.0, 0.0102, 0.0083, 0.0063, 0.0053, 0.0045, 0.0037, 0.0030, 0.0025, 0.0022, 0.0018, 0.0015, 0.0012, 0.0010, 0.0008, 0.0007],
            [0.0, 0.0102, 0.0075, 0.0035, 0.0018, 0.0010, 0.0004] + [0.0003] * 9,
        ),
    ]
    spec = FigureSpec(fig_id="12-9", title="图 12-9 相对地区指数对冲击的反应", panels=panels, rows=2, cols=2, width=1000, height=800)
    return render_figure_svg(spec, mode)


def _fig_12_10(mode: ThemeMode = "mono") -> str:
    xs = PERIODS_0_15
    unemployment_83 = [0.0, 0.0008, -0.0003, 0.0003, -0.0001, 0.0] + [0.0001] * 10
    unemployment_91 = [0.0, 0.0014, -0.0005, 0.0003, 0.0, 0.0] + [0.0001] * 10
    participation_83 = [0.0, -0.0075, -0.0054, -0.0023, -0.0023, -0.0027, -0.0022, -0.0017, -0.0015, -0.0013, -0.0011, -0.0010, -0.0008, -0.0007, -0.0006, -0.0005]
    participation_91 = [0.0, -0.0063, -0.0045, -0.0014, -0.0014, -0.0020, -0.0015, -0.0012, -0.0011, -0.0009, -0.0008, -0.0007, -0.0006, -0.0005, -0.0004, -0.0003]
    employment_91 = [0.0, -0.0099, -0.0095, -0.0061, -0.0062, -0.0068, -0.0064, -0.0061, -0.0059, -0.0058, -0.0057, -0.0056, -0.0055, -0.0054, -0.0053, -0.0053]
    employment_83 = [0.0, -0.0099, -0.0089, -0.0056, -0.0057, -0.0060, -0.0056, -0.0052, -0.0050, -0.0048, -0.0047, -0.0045, -0.0044, -0.0043, -0.0042, -0.0041]
    panel = PanelSpec(
        xlim=(-0.5, 15.5),
        ylim=(-0.012, 0.002),
        xticks=xs,
        yticks=[(v / 1000, "0" if v == 0 else f"{v / 1000:.3f}") for v in range(-12, 3, 2)],
        zero_line=True,
        lines=[
            LineSeries(x=xs, y=unemployment_83, label="失业率（1983—2007年）", color_idx=1, style="dashed", width=2.0),
            LineSeries(x=xs, y=participation_83, label="劳动力参与率（1983—2007年）", color_idx=4, style="longdash", width=1.8),
            LineSeries(x=xs, y=employment_83, label="就业人数（1983—2007年）", color_idx=0, style="solid", width=2.8),
            LineSeries(x=xs, y=unemployment_91, label="失业率（1991—2007年）", color_idx=2, style="dotted", width=2.0),
            LineSeries(x=xs, y=participation_91, label="劳动力参与率（1991—2007年）", color_idx=3, style="dashdot", width=2.0),
            LineSeries(x=xs, y=employment_91, label="就业人数（1991—2007年）", color_idx=5, style="solid", width=1.6),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="12-10", title="图 12-10 劳动力需求冲击的反应（1983—2007 年）", panels=[panel], width=1000, height=560)
    return render_figure_svg(spec, mode)


def _fig_12_11(mode: ThemeMode = "mono") -> str:
    ages = ["15~19", "20~24", "25~29", "30~34", "35~39", "40~44", "45~49", "50~54", "55~59", "60~64"]
    xs = [float(i) for i in range(len(ages))]
    total_80s = [19.9, 18.3, 12.9, 9.2, 6.2, 4.2, 3.4, 3.0, 2.3, 1.8]
    total_90s = [18.5, 15.6, 13.2, 9.7, 6.5, 4.3, 3.5, 2.8, 2.3, 1.8]
    men_80s = [21.0, 16.9, 13.8, 10.8, 7.8, 5.6, 4.6, 3.7, 2.6, 1.8]
    men_90s = [24.9, 20.3, 14.1, 10.4, 7.4, 5.3, 4.4, 3.6, 2.6, 1.8]
    panel = PanelSpec(
        xlim=(-0.5, 9.5),
        ylim=(0.0, 30.0),
        xticks=list(zip(xs, ages)),
        yticks=[float(v) for v in range(0, 31, 5)],
        xlabel="年龄",
        ylabel="迁往外县的人口在5年前的居民人口中所占的比例（%）",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=total_80s, label="80年代后半期（男女合计）", color_idx=4, style="dashed", width=2.4),
            LineSeries(x=xs, y=total_90s, label="90年代后半期（男女合计）", color_idx=5, style="solid", width=2.4),
            LineSeries(x=xs, y=men_80s, label="80年代后半期（男性）", color_idx=3, style="dashdot", width=2.6),
            LineSeries(x=xs, y=men_90s, label="90年代后半期（男性）", color_idx=0, style="dotted", width=2.6),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="12-11", title="图 12-11 各年龄段在都道府县之间的迁移", panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_12_12(mode: ThemeMode = "mono") -> str:
    years = [1980.0, 1985.0, 1990.0, 1995.0, 2000.0, 2005.0]
    within = [25.8, 28.2, 30.8, 32.5, 33.7, 33.3]
    outside = [6.3, 6.9, 7.8, 8.1, 8.1, 8.3]
    totals = [32.1, 35.1, 38.6, 40.7, 41.8, 41.5]
    labels: list[Annotation] = []
    for x, w, o, t in zip(years, within, outside, totals):
        labels.append(_label(x, w / 2, f"{w:.1f}"))
        labels.append(_label(x, w + o / 2, f"{o:.1f}"))
        labels.append(_label(x, t + 0.6, f"{t:.1f}"))
    panel = PanelSpec(
        xlim=(1977.5, 2007.5),
        ylim=(0.0, 46.5),
        xticks=years,
        yticks=[(float(v), f"{v:.1f}") for v in range(0, 46, 5)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        bars=[
            BarSeries(x=years, y=within, label="县内其他市区町村", color_idx=0, width=2.6),
            BarSeries(x=years, y=outside, label="县外", color_idx=1, width=2.6, bottom=within),
        ],
        annotations=[
            *labels,
            Annotation(x=1988.7, y=38.6, text="县外", dx=-40.0, dy=-30.0, align="end"),
            _label(1992.5, 8.0, "县内其他市区町村"),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="12-12", title="图 12-12 就业人员通勤率的变化", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "9-1": _fig_9_1,
        "9-2": _fig_9_2,
        "9-3": _fig_9_3,
        "9-4": _fig_9_4,
        "9-5": _fig_9_5,
        "11-1": _fig_11_1,
        "11-2": _fig_11_2,
        "11-3": _fig_11_3,
        "11-4": _fig_11_4,
        "11-5": _fig_11_5,
        "12-1": _fig_12_1,
        "12-2": _fig_12_2,
        "12-3": _fig_12_3,
        "12-4": _fig_12_4,
        "12-5": _fig_12_5,
        "12-6": _fig_12_6,
        "12-7": _fig_12_7,
        "12-8": _fig_12_8,
        "12-9": _fig_12_9,
        "12-10": _fig_12_10,
        "12-11": _fig_12_11,
        "12-12": _fig_12_12,
    }
