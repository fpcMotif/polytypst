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

YEARS_1990_2006 = [float(y) for y in range(1990, 2007)]


def _fig_1_1(mode: ThemeMode = "mono") -> str:
    series = [
        ("（指标1）", "cross", [66.8, 67.3, 68.7, 70.0, 71.3, 72.0, 72.6, 72.6, 74.2, 73.5, 73.5, 74.6, 73.4, 72.6, 71.3, 70.4, 71.0]),
        ("（指标2）", "diamond", [86.4, 85.8, 86.5, 86.7, 87.8, 88.3, 88.4, 88.5, 90.0, 89.2, 88.4, 89.0, 87.2, 86.1, 84.2, 82.8, 82.9]),
        ("（指标3）", "square", [87.0, 87.9, 89.2, 89.4, 90.1, 89.6, 87.3, 86.7, 88.6, 87.7, 86.6, 87.3, 86.0, 85.0, 84.3, 83.9, 84.9]),
        ("（指标4）", "triangle", [73.9, 74.7, 77.4, 78.9, 81.2, 81.5, 80.7, 80.8, 83.0, 82.9, 82.2, 83.1, 82.4, 81.6, 80.0, 78.8, 78.9]),
        ("（指标5）", "cross", [66.8, 66.7, 66.6, 66.6, 67.0, 67.0, 66.0, 66.0, 66.5, 66.0, 65.0, 64.6, 63.5, 62.5, 61.0, 60.8, 60.3]),
    ]
    panel = PanelSpec(
        xlim=(1989.5, 2006.5),
        ylim=(60.0, 95.0),
        xticks=[float(y) for y in range(1990, 2007, 2)],
        yticks=[60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=YEARS_1990_2006, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="1-1", title="图 1-1 劳动分配率的变化", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_1_2(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1997, 2007)]
    wage = [0.0074, -0.0029, -0.00375, 0.0009, -0.0023, -0.0081, -0.0088, -0.0022, 0.0, 0.0009]
    prod = [-0.00305, 0.0028, -0.0004, -0.002, 0.0062, 0.0003, -0.0029, -0.0023, 0.00145, -0.00185]
    share = [0.00435, -0.0003, -0.0041, -0.0012, 0.0038, -0.0079, -0.0116, -0.0043, 0.0015, -0.0012]
    prod_bottom = [w if (w < 0) == (p < 0) else 0.0 for w, p in zip(wage, prod)]
    panel = PanelSpec(
        xlim=(1996.5, 2006.5),
        ylim=(-0.014, 0.011),
        xticks=years,
        yticks=[(v, f"{v:.3f}".replace("-", "−")) for v in [-0.014, -0.009, -0.004, 0.001, 0.006, 0.011]],
        xlabel="年",
        bars=[
            BarSeries(x=years, y=wage, label="雇员人均工资", color_idx=2, width=0.72),
            BarSeries(x=years, y=prod, label="生产率", color_idx=1, width=0.72, bottom=prod_bottom),
        ],
        lines=[LineSeries(x=years, y=share, label="劳动分配率", color_idx=0, marker="square", width=2.2)],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="1-2", title="图 1-2 劳动分配率变化的因素分析", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _wage_index_figure(fig_id: str, title: str, series: list[tuple[str, str, list[float]]], mode: ThemeMode) -> str:
    years = [float(y) for y in range(1989, 2004)]
    panel = PanelSpec(
        xlim=(1988.5, 2003.5),
        ylim=(0.6, 1.4),
        xticks=years,
        yticks=[0.6, 0.7, 0.8, 0.9, (1.0, "1.0"), 1.1, 1.2, 1.3, 1.4],
        xlabel="年",
        ylabel="(1995年=1)",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], width=1000, height=600)
    return render_figure_svg(spec, mode)


def _fig_1_3(mode: ThemeMode = "mono") -> str:
    series = [
        ("行业合计（1000人以上）", "diamond", [0.909, 0.935, 0.951, 0.950, 0.958, 0.981, 1.0, 1.029, 1.048, 1.044, 1.054, 1.082, 1.111, 1.103, 1.116]),
        ("行业合计（100~999人）", "square", [0.872, 0.908, 0.931, 0.932, 0.958, 0.977, 1.0, 1.020, 1.030, 1.026, 1.030, 1.054, 1.072, 1.079, 1.079]),
        ("制造业（1000人以上）", "triangle", [0.829, 0.862, 0.880, 0.883, 0.909, 0.946, 0.997, 1.077, 1.120, 1.116, 1.137, 1.196, 1.226, 1.249, 1.325]),
        ("制造业（100~999人）", "cross", [0.795, 0.825, 0.868, 0.886, 0.913, 0.952, 0.994, 1.055, 1.099, 1.108, 1.111, 1.179, 1.192, 1.201, 1.255]),
    ]
    return _wage_index_figure("1-3", "图 1-3 工资的时间序列变化 1 (现金工资总额)", series, mode)


def _fig_1_4(mode: ThemeMode = "mono") -> str:
    series = [
        ("行业合计（1000人以上）", "diamond", [0.917, 0.939, 0.952, 0.942, 0.948, 0.971, 0.999, 1.035, 1.054, 1.053, 1.067, 1.102, 1.135, 1.134, 1.171]),
        ("行业合计（100~999人）", "square", [0.875, 0.910, 0.929, 0.926, 0.945, 0.968, 0.998, 1.023, 1.041, 1.030, 1.046, 1.072, 1.101, 1.111, 1.132]),
        ("制造业（1000人以上）", "triangle", [0.833, 0.864, 0.878, 0.878, 0.894, 0.947, 0.998, 1.071, 1.132, 1.118, 1.136, 1.225, 1.243, 1.260, 1.362]),
        ("制造业（100~999人）", "cross", [0.792, 0.820, 0.855, 0.860, 0.899, 0.948, 0.992, 1.064, 1.118, 1.096, 1.117, 1.212, 1.221, 1.234, 1.311]),
    ]
    return _wage_index_figure("1-4", "图 1-4 工资的时间序列变化 2 (固定支付工资)", series, mode)


def _fig_1_5(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1985, 2006)]
    series = [
        ("金融机构", "diamond", 0, [39.8, 41.3, 42.5, 44.0, 43.3, 42.9, 42.9, 42.8, 42.1, 42.7, 41.3, 42.0, 42.0, 40.9, 36.4, 39.0, 39.0, 38.8, 34.4, 32.6, 31.5]),
        ("其中的投资信托", "square", 1, [1.8, 1.8, 2.6, 2.9, 3.8, 3.7, 3.4, 3.1, 2.8, 2.5, 2.3, 1.9, 1.9, 1.5, 2.4, 2.9, 3.5, 4.1, 4.1, 3.8, 4.1]),
        ("非金融企业", "triangle", 3, [28.9, 30.0, 30.0, 29.3, 29.7, 30.1, 29.1, 28.4, 28.0, 27.9, 27.1, 26.0, 24.6, 25.3, 25.8, 22.1, 21.9, 21.8, 21.7, 21.9, 21.2]),
        ("个人", "circle", 4, [22.2, 20.0, 20.0, 20.0, 20.7, 20.2, 20.2, 20.7, 19.9, 19.7, 19.3, 19.3, 19.0, 18.9, 18.0, 19.3, 19.3, 20.1, 20.1, 20.1, 18.9]),
        ("外国投资者", "cross", 2, [6.9, 5.2, 4.2, 4.4, 4.4, 4.7, 6.2, 6.2, 7.7, 8.0, 10.5, 11.7, 13.1, 13.9, 18.6, 18.5, 18.1, 17.4, 21.7, 23.4, 26.7]),
    ]
    panel = PanelSpec(
        xlim=(1984.5, 2005.5),
        ylim=(0.0, 50.0),
        xticks=[1985.0, 1990.0, 1995.0, 2000.0, 2005.0],
        yticks=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0],
        xlabel="年",
        ylabel="%",
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=ci, marker=marker, width=1.8)
            for label, marker, ci, ys in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="1-5", title="图 1-5 各投资部门持股比例（按金额计算）", panels=[panel], width=860, height=540)
    return render_figure_svg(spec, mode)


PHILLIPS_TITLES = ["（1）日本", "（2）美国", "（3）加拿大", "（4）英国", "（5）法国", "（6）意大利"]


def _phillips_figure(
    fig_id: str, title: str, points: list[list[tuple[float, float]]], ylims: list[tuple[float, float]], mode: ThemeMode
) -> str:
    panels = []
    for name, pts, ylim in zip(PHILLIPS_TITLES, points, ylims):
        step = 2.0 if ylim[0] < 0 else 1.0
        panels.append(
            PanelSpec(
                title=name,
                xlim=(0.0, 12.0),
                ylim=ylim,
                xticks=[float(v) for v in range(0, 13, 2)],
                yticks=[
                    (v, f"{v:g}".replace("-", "−"))
                    for v in (ylim[0] + step * i for i in range(int((ylim[1] - ylim[0]) / step) + 1))
                ],
                xlabel="失业率（%）",
                ylabel="名义工资变化率（%）",
                scatters=[([p[0] for p in pts], [p[1] for p in pts], [], 0, False)],
                legend_loc="none",
            )
        )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=panels, rows=3, cols=2, width=860, height=1280)
    return render_figure_svg(spec, mode)


def _fig_2_1(mode: ThemeMode = "mono") -> str:
    points = [
        [(2.05, 6.79), (2.11, 5.4), (2.15, 4.89), (2.18, 7.14), (2.21, 3.44), (2.35, 4.34), (2.44, 5.14), (2.57, 1.44),
         (2.6, 3.68), (2.73, 4.75), (2.75, 2.97), (2.85, 3.14), (2.85, 1.58)],
        [(5.23, 2.87), (5.49, 1.76), (5.61, 2.94), (6.2, 2.06), (6.74, 4.07), (7.01, 3.81), (7.04, 8.47), (7.18, 4.08),
         (7.52, 3.88), (7.53, 3.26), (7.54, 8.54), (9.6, 6.19), (9.7, 9.81)],
        [(7.51, 9.77), (7.58, 5.25), (7.92, 3.84), (8.16, 5.12), (8.91, 3.37), (9.77, 2.87), (10.37, 7.08), (10.73, 3.7),
         (11.31, 3.41), (11.4, 4.68), (12.0, 4.06)],
        [(6.9, 8.51), (7.08, 8.63), (8.5, 7.89), (8.58, 9.02), (9.85, 7.74), (10.34, 7.45), (10.97, 8.65), (11.2, 8.8),
         (11.2, 8.5)],
        [(8.49, 3.95), (8.9, 3.09), (8.98, 4.57), (9.43, 3.1), (9.66, 7.0), (9.75, 5.56), (9.9, 3.95)],
        [(8.5, 6.98), (8.8, 9.37), (8.91, 5.84), (9.64, 4.66), (9.76, 6.2), (9.76, 5.9)],
    ]
    return _phillips_figure("2-1", "图 2-1 各国的菲利普斯曲线（1980—1992 年）", points, [(0.0, 10.0)] * 6, mode)


def _fig_2_2(mode: ThemeMode = "mono") -> str:
    points = [
        [(2.44, 1.23), (2.84, 0.49), (3.02, 2.19), (3.34, 2.98), (3.34, 2.45), (4.03, 0.7), (4.04, 2.89), (4.38, 1.8),
         (4.64, -0.6), (4.66, 2.23), (4.99, 1.73), (5.27, -0.88), (5.39, -0.08)],
        [(3.98, 3.02), (4.15, 2.44), (4.47, 3.01), (4.59, 2.53), (4.68, 3.35), (4.86, 3.25), (5.13, 2.57), (5.42, 2.53),
         (5.49, 2.94), (5.82, 3.09), (5.98, 3.58), (6.1, 2.57), (6.88, 2.42)],
        [(6.3, 0.5), (6.82, 1.93), (6.82, 2.62), (7.22, 1.93), (7.22, 2.62), (7.62, 1.32), (7.64, 3.05), (7.74, 2.86),
         (8.32, 2.02), (9.12, 0.69), (9.54, 1.39), (9.66, 2.99), (10.44, 1.67), (11.48, 2.39)],
        [(4.6, 3.5), (4.73, 3.65), (4.87, 3.45), (4.95, 4.57), (5.09, 4.23), (5.25, 4.0), (5.26, 3.59), (5.88, 4.43),
         (6.11, 4.12), (6.81, 4.23), (7.9, 4.34), (8.51, 4.92), (9.29, 4.62), (10.25, 6.41)],
        [(8.37, 4.61), (8.69, 4.42), (9.04, 2.39), (9.08, 3.47), (9.28, 2.88), (9.3, 2.63), (10.5, 2.1), (11.09, 1.9),
         (11.09, 2.75), (11.14, 3.53), (11.5, 2.74), (11.6, 2.47), (11.71, 2.05)],
        [(6.81, 2.69), (7.7, 2.91), (7.96, 2.55), (8.39, 2.76), (8.6, 1.98), (9.13, 2.08), (9.8, 5.29), (10.14, 2.31),
         (10.67, 3.62), (10.92, 2.76), (11.22, 2.96), (11.23, 3.34), (11.4, 3.03), (11.47, 3.54)],
    ]
    ylims = [(-2.0, 10.0)] + [(0.0, 10.0)] * 5
    return _phillips_figure("2-2", "图 2-2 各国的菲利普斯曲线 (1993—2006 年)", points, ylims, mode)


def _uv_figure(
    fig_id: str,
    title: str,
    points: list[tuple[float, float]],
    xlim: tuple[float, float],
    xstep: float,
    ystep: float,
    diagonal: tuple[float, float],
    annotations: list[Annotation],
    mode: ThemeMode,
) -> str:
    n_x = round((xlim[1] - xlim[0]) / xstep)
    n_y = round(5.0 / ystep)
    panel = PanelSpec(
        xlim=xlim,
        ylim=(2.0, 7.0),
        xticks=[(xlim[0] + xstep * i, f"{xlim[0] + xstep * i:.1f}") for i in range(n_x + 1)],
        yticks=[(2.0 + ystep * i, f"{2.0 + ystep * i:.1f}") for i in range(n_y + 1)],
        xlabel="空岗率（%）",
        ylabel="就业失业率（%）",
        zero_line=False,
        lines=[
            LineSeries(x=list(diagonal), y=list(diagonal), color_idx=0, width=2.0),
            LineSeries(x=[p[0] for p in points], y=[p[1] for p in points], color_idx=0, marker="diamond", width=1.8),
        ],
        annotations=annotations,
        legend_loc="none",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_3_1(mode: ThemeMode = "mono") -> str:
    points = [
        (2.38, 3.62), (2.33, 3.46), (2.15, 3.68), (2.35, 3.80), (3.01, 3.36), (3.31, 2.97), (3.40, 2.75), (3.29, 2.69),
        (2.75, 2.72), (2.19, 3.09), (2.00, 3.50), (2.07, 3.84), (2.33, 4.07), (2.47, 4.10), (2.06, 4.94), (1.96, 5.57),
        (2.40, 5.62), (2.50, 5.96), (2.41, 6.28), (2.72, 6.14), (3.22, 5.53), (3.55, 5.20), (3.72, 4.83), (3.51, 4.50),
    ]
    annotations = [
        Annotation(x=2.41, y=6.28, text="2002年", dx=-50, dy=0, align="end"),
        Annotation(x=3.51, y=4.50, text="2007年", dx=-50, dy=0, align="end"),
        Annotation(x=2.47, y=4.10, text="1997年", dx=45, dy=10, align="start"),
        Annotation(x=2.38, y=3.58, text="1984年", dx=35, dy=35, align="start"),
        Annotation(x=3.40, y=2.75, text="1990年", dx=40, dy=0, align="start"),
        Annotation(x=2.00, y=3.48, text="1994年", dx=-12, dy=45, align="middle"),
        Annotation(x=2.15, y=3.66, text="1986年", dx=-25, dy=80, align="end"),
    ]
    return _uv_figure(
        "3-1", "图 3-1 失业率和空岗率（职业稳定业务统计）变化", points, (1.8, 4.0), 0.2, 1.0, (2.0, 4.0), annotations, mode
    )


def _fig_3_2(mode: ThemeMode = "mono") -> str:
    points = [
        (2.13, 3.50), (1.71, 3.74), (1.40, 3.63), (1.68, 3.49), (2.02, 3.45), (4.80, 2.92), (5.39, 2.71), (6.10, 2.64),
        (4.70, 2.68), (2.82, 3.04), (2.00, 3.23), (1.59, 3.83), (1.82, 4.06), (1.68, 4.01), (0.81, 4.92), (0.80, 5.62),
        (1.10, 5.63), (0.90, 5.93), (0.81, 6.29), (0.70, 6.13), (1.00, 5.49), (1.10, 5.14), (1.10, 4.75),
    ]
    annotations = [
        Annotation(x=0.81, y=6.29, text="2002年", dx=30, dy=-25, align="start"),
        Annotation(x=1.10, y=4.75, text="2006年", dx=30, dy=-80, align="start"),
        Annotation(x=1.82, y=4.06, text="1996年", dx=-5, dy=-60, align="middle"),
        Annotation(x=1.40, y=3.63, text="1986年", dx=-50, dy=-35, align="end"),
        Annotation(x=4.80, y=2.92, text="1989年", dx=-20, dy=-45, align="middle"),
        Annotation(x=2.82, y=3.04, text="1993年", dx=-50, dy=30, align="end"),
    ]
    return _uv_figure(
        "3-2", "图 3-2 失业率和空岗率（就业趋势调查）变化", points, (0.0, 7.0), 1.0, 0.5, (2.1, 7.0), annotations, mode
    )


def _fig_3_3(mode: ThemeMode = "mono") -> str:
    survey = [2.01, 1.43, 1.73, 2.0, 4.75, 5.42, 6.09, 4.70, 2.86, 2.14, 1.59, 1.68, 1.76, 0.82, 0.78, 1.08, 0.87, 0.78, 0.68, 0.95, 1.07, 1.08]
    placement = [2.36, 2.33, 2.16, 2.38, 2.96, 3.28, 3.39, 3.27, 2.73, 2.17, 2.04, 2.02, 2.28, 2.43, 2.04, 1.96, 2.36, 2.46, 2.40, 2.67, 3.14, 3.44, 3.66, 3.48]
    panel = PanelSpec(
        xlim=(1983.5, 2007.5),
        ylim=(0.0, 7.0),
        xticks=[float(y) for y in range(1984, 2007, 2)],
        yticks=[float(v) for v in range(8)],
        xlabel="年",
        ylabel="%",
        lines=[
            LineSeries(x=[float(y) for y in range(1985, 2007)], y=survey, label="就业趋势调查空岗率", color_idx=1, width=2.4),
            LineSeries(x=[float(y) for y in range(1984, 2008)], y=placement, label="职业稳定业务统计空岗率", color_idx=0, width=2.4),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="3-3", title="图 3-3 空岗统计比较", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _cv_figure(
    fig_id: str,
    title: str,
    x0: int,
    series: list[tuple[str, str, int, list[float]]],
    ylim: tuple[float, float],
    ystep: float,
    mode: ThemeMode,
    ylabel: str = "变异系数",
) -> str:
    n = max(start - x0 + len(ys) for _, _, start, ys in series)
    years = [float(x0 + i) for i in range(n)]
    panel = PanelSpec(
        xlim=(x0 - 0.5, x0 + n - 0.5),
        ylim=ylim,
        xticks=years[::2],
        yticks=[(ylim[0] + ystep * i, f"{ylim[0] + ystep * i:.2f}") for i in range(round((ylim[1] - ylim[0]) / ystep) + 1)],
        xlabel="年",
        ylabel=ylabel,
        zero_line=False,
        lines=[
            LineSeries(x=[float(start + j) for j in range(len(ys))], y=ys, label=label, color_idx=i, marker=marker, width=1.8)
            for i, (label, marker, start, ys) in enumerate(series)
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_3_5(mode: ThemeMode = "mono") -> str:
    series = [
        ("新职位空缺率", "square", 1983, [0.298, 0.339, 0.346, 0.316, 0.302, 0.328, 0.336, 0.323, 0.315, 0.299, 0.276, 0.258, 0.222,
                                    0.208, 0.222, 0.215, 0.194, 0.195, 0.195, 0.175, 0.177, 0.209, 0.222, 0.224, 0.220]),
        ("有效职位空缺率", "triangle", 1983, [0.353, 0.392, 0.399, 0.361, 0.327, 0.329, 0.320, 0.312, 0.317, 0.319, 0.316, 0.313, 0.284,
                                      0.249, 0.263, 0.242, 0.224, 0.215, 0.201, 0.191, 0.193, 0.220, 0.235, 0.238, 0.238]),
    ]
    return _cv_figure("3-5", "图 3-5 按地区划分基于职位空缺率的劳动力供需差异", 1983, series, (0.0, 0.45), 0.05, mode)


def _fig_3_6(mode: ThemeMode = "mono") -> str:
    series = [
        ("各地区", "square", 1983, [0.245, 0.258, 0.260, 0.240, 0.237, 0.242, 0.231, 0.226, 0.221, 0.195, 0.182, 0.187, 0.195,
                                     0.175, 0.173, 0.170, 0.158, 0.169, 0.158, 0.169, 0.173, 0.157, 0.170, 0.181, 0.179]),
        ("各都道府县", "triangle", 1997, [0.240, 0.231, 0.218, 0.221, 0.213, 0.213, 0.216, 0.212, 0.220, 0.241, 0.238]),
    ]
    return _cv_figure("3-6", "图 3-6 按地区和都道府县划分基于失业率的劳动力供需差异", 1983, series, (0.0, 0.30), 0.05, mode)


def _fig_3_7(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1983, 2007)]
    region = [11.45, 10.75, 12.3, 11.55, 9.6, 10.6, 10.3, 10.6, 11.3, 10.7, 11.5, 10.0, 12.8, 11.0, 9.2, 8.6, 9.3, 8.6, 9.3, 7.65, 8.0, 9.2, 9.2, 9.2]
    prefecture = [19.8, 18.05, 20.2, 19.1, 17.9, 18.05, 18.6, 19.7, 19.3, 19.2, 19.0, 17.0, 20.3, 18.8, 16.4, 15.5, 16.1, 15.8, 16.6, 14.5, 14.0, 16.6, 15.5, 15.65]
    panel = PanelSpec(
        xlim=(1982.5, 2006.5),
        ylim=(0.0, 25.0),
        xticks=years[::2],
        yticks=[0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
        xlabel="年",
        ylabel="流入率（%）",
        lines=[
            LineSeries(x=years, y=region, label="地区外", color_idx=1, width=2.4),
            LineSeries(x=years, y=prefecture, label="县外", color_idx=0, width=2.4),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="3-7", title="图 3-7 来自地区外和都道府县外的流入就业人员比例", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _diamond_points(pts: list[tuple[float, float]]) -> LineSeries:
    xs: list[float] = []
    ys: list[float | None] = []
    for x, y in pts:
        xs += [x, x]
        ys += [y, None]
    return LineSeries(x=xs, y=ys, color_idx=0, marker="diamond")


def _fig_3_8(mode: ThemeMode = "mono") -> str:
    points_2002 = [
        (0.293, 14.90), (0.404, 16.27), (0.410, 20.51), (0.411, 14.24), (0.411, 12.75), (0.413, 11.20), (0.418, 10.72),
        (0.419, 16.26), (0.420, 11.79), (0.420, 14.28), (0.422, 15.09), (0.427, 14.83), (0.429, 14.50), (0.448, 11.34),
        (0.452, 9.16), (0.455, 11.16), (0.458, 9.42), (0.472, 13.25), (0.484, 13.25), (0.494, 15.40), (0.496, 13.25),
        (0.509, 13.25), (0.509, 12.49), (0.514, 12.33), (0.531, 10.47), (0.534, 8.77), (0.541, 12.54), (0.573, 14.43),
        (0.582, 15.99), (0.599, 13.85), (0.611, 9.27), (0.619, 13.21), (0.632, 9.27), (0.633, 11.78), (0.633, 11.04),
        (0.643, 18.90), (0.663, 16.10), (0.663, 8.93), (0.703, 9.62), (0.708, 9.98), (0.730, 8.78), (0.743, 10.12),
        (0.751, 10.47), (0.761, 14.09), (0.771, 14.32), (0.789, 16.01), (0.832, 15.04),
    ]
    points_2006 = [
        (0.440, 7.09), (0.489, 12.42), (0.604, 13.12), (0.610, 22.67), (0.612, 11.95), (0.644, 9.95), (0.690, 18.23),
        (0.764, 15.98), (0.799, 6.85), (0.806, 15.55), (0.809, 30.23), (0.824, 12.66), (0.850, 22.20), (0.890, 16.68),
        (0.890, 15.96), (0.891, 7.82), (0.895, 11.12), (0.908, 11.55), (0.916, 20.37), (0.929, 11.86), (0.929, 17.62),
        (0.954, 11.94), (0.988, 11.89), (1.007, 8.53), (1.038, 13.13), (1.056, 13.43), (1.057, 12.78), (1.106, 16.25),
        (1.112, 10.32), (1.126, 12.69), (1.191, 14.24), (1.220, 9.96), (1.247, 15.66), (1.258, 8.53), (1.260, 9.91),
        (1.281, 10.51), (1.283, 9.93), (1.296, 17.31), (1.304, 9.77), (1.346, 16.41), (1.356, 11.16), (1.371, 11.39),
        (1.408, 11.15), (1.416, 13.86), (1.416, 15.24), (1.581, 9.81), (1.851, 13.57),
    ]
    panels = [
        PanelSpec(
            title="2002年",
            xlim=(0.0, 1.0),
            ylim=(0.0, 25.0),
            xticks=[(v / 10, f"{v / 10:.2f}") for v in range(0, 11, 2)],
            yticks=[(float(v), f"{v:.2f}") for v in range(0, 26, 5)],
            xlabel="有效职位空缺率",
            ylabel="县内转移人员占县内就业人员比率",
            lines=[_diamond_points(points_2002)],
            legend_loc="none",
        ),
        PanelSpec(
            title="2006年",
            xlim=(0.0, 2.0),
            ylim=(0.0, 35.0),
            xticks=[(v / 2, f"{v / 2:.2f}") for v in range(5)],
            yticks=[(float(v), f"{v:.2f}") for v in range(0, 36, 5)],
            xlabel="有效职位空缺率",
            lines=[_diamond_points(points_2006)],
            legend_loc="none",
        ),
    ]
    spec = FigureSpec(
        fig_id="3-8", title="图 3-8 有效职位空缺率和县内转移人员/就业人员比率", panels=panels, cols=2, width=860, height=480
    )
    return render_figure_svg(spec, mode)


def _fig_3_9(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1983, 2007)]
    series = [
        ("就业率行业合计", "triangle", 0, [13.7, 14.8, 15.3, 14.7, 14.3, 15.8, 16.1, 16.9, 16.6, 15.6, 14.4, 12.8, 13.4, 13.7, 14.2, 13.9, 14.0, 14.7, 15.2, 14.6, 14.6, 15.6, 17.3, 16.2]),
        ("离职率行业合计", "circle", 1, [12.75, 14.4, 14.7, 14.2, 13.8, 14.85, 15.2, 15.3, 15.2, 14.5, 13.8, 13.8, 14.3, 13.9, 15.2, 15.1, 15.1, 15.9, 16.8, 16.6, 16.2, 15.9, 17.5, 16.2]),
        ("制造业就业率", "square", 3, [12.55, 13.9, 14.0, 12.2, 11.6, 13.8, 13.7, 14.2, 13.7, 12.55, 10.4, 9.85, 10.4, 9.75, 10.4, 8.8, 10.05, 9.85, 10.25, 9.3, 9.6, 11.1, 11.9, 11.8]),
        ("制造业离职率", "cross", 2, [12.3, 12.3, 13.4, 13.6, 12.3, 12.9, 13.4, 13.3, 12.9, 12.1, 12.1, 11.7, 12.0, 11.5, 12.0, 12.4, 12.55, 12.1, 14.0, 13.2, 11.9, 11.5, 11.6, 10.9]),
        ("服务业就业率", "square", 4, [16.1, 17.0, 18.3, 16.7, 16.8, 18.7, 19.2, 19.85, 20.25, 18.9, 18.0, 17.2, 15.8, 17.8, 18.2, 18.2, 16.4, 16.7, 18.8, 17.1, 18.1, 21.3, 22.2, 22.0]),
        ("服务业离职率", "diamond", 5, [14.2, 15.6, 16.1, 14.5, 14.8, 16.8, 17.5, 17.5, 18.0, 16.7, 16.3, 16.5, 15.6, 15.6, 17.65, 16.9, 16.9, 17.0, 18.3, 17.3, 18.6, 20.9, 22.0, 21.7]),
    ]
    panel = PanelSpec(
        xlim=(1982.5, 2006.5),
        ylim=(0.0, 25.0),
        xticks=years[::2],
        yticks=[0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
        xlabel="年",
        ylabel="就业率和离职率（%）",
        lines=[
            LineSeries(x=years, y=ys, label=label, color_idx=ci, marker=marker, width=1.8)
            for label, marker, ci, ys in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="3-9", title="图 3-9 就业率和离职率（按行业划分）", panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def _fig_3_11(mode: ThemeMode = "mono") -> str:
    gap_x = [
        1980.02, 1980.29, 1980.54, 1981.04, 1981.29, 1981.52, 1981.79, 1982.04, 1982.29, 1982.56, 1982.82, 1983.3, 1983.54,
        1983.8, 1984.05, 1984.29, 1984.54, 1984.8, 1985.04, 1985.29, 1985.55, 1985.79, 1986.3, 1987.04, 1987.33, 1988.09,
        1988.33, 1988.62, 1989.09, 1989.36, 1989.85, 1990.11, 1990.58, 1990.83, 1991.11, 1991.61, 1991.82, 1992.88,
        1993.11, 1993.54, 1993.9, 1994.13, 1994.39, 1994.64, 1994.9, 1995.16, 1995.62, 1995.89, 1996.42, 1996.72,
        1997.13, 1997.5, 1997.95, 1998.44, 1998.77, 1999.0, 1999.18, 1999.45, 1999.68, 2000.18, 2000.47, 2000.7,
        2000.97, 2001.17, 2001.94, 2002.19, 2002.7, 2003.2, 2003.72, 2004.22, 2004.46, 2004.69, 2004.96, 2005.75,
        2005.98, 2006.22, 2006.74, 2007.24, 2007.47, 2007.74, 2007.98, 2008.25, 2008.74, 2009.03,
    ]
    gap_y = [
        1.89, 1.31, 1.31, 1.59, 1.32, 1.39, 0.7, 0.88, 1.61, 0.48, 0.48, -0.47, -0.44, -0.96, -1.22, -0.8, -0.32, -0.8,
        0.71, 0.47, 0.3, 1.0, -0.63, -1.45, -1.91, 0.91, 0.63, 1.32, 3.0, 0.51, 2.44, 1.61, 3.44, 2.76, 3.36, 1.84, 1.76,
        -0.77, -0.02, -2.3, -3.14, -2.74, -3.22, -2.66, -3.3, -3.42, -2.05, -2.3, -1.33, -1.33, 0.39, -1.17, -1.21,
        -4.22, -4.02, -4.02, -5.0, -4.54, -4.94, -3.03, -3.03, -3.11, -2.43, -2.23, -4.72, -4.48, -3.43, -4.12, -3.11,
        -1.2, -1.81, -1.53, -2.1, -0.6, -0.6, -0.79, -0.16, 1.04, 0.4, 0.52, 1.32, 1.32, -0.64, -4.0,
    ]
    unemployment = [
        1.9, 1.96, 2.02, 2.2, 2.18, 2.29, 2.18, 2.19, 2.19, 2.27, 2.38, 2.42, 2.64, 2.7, 2.7, 2.6, 2.66, 2.7, 2.7, 2.7, 2.59,
        2.59, 2.6, 2.79, 2.69, 2.79, 2.79, 2.8, 2.88, 3.01, 2.8, 2.69, 2.7, 2.63, 2.49, 2.46, 2.33, 2.29, 2.24, 2.19, 2.08,
        2.09, 2.09, 2.09, 2.09, 2.09, 2.09, 2.09, 2.1, 2.09, 2.16, 2.3, 2.29, 2.36, 2.45, 2.62, 2.8, 2.81, 2.9, 2.95, 2.91,
        3.05, 3.15, 3.26, 3.35, 3.41, 3.4, 3.31, 3.36, 3.33, 3.3, 3.44, 3.49, 3.85, 4.18, 4.35, 4.46, 4.64, 4.71, 4.71,
        4.7, 4.81, 4.71, 4.72, 4.71, 4.83, 4.98, 5.19, 5.41, 5.31, 5.42, 5.42, 5.32, 5.32, 5.41, 5.18, 5.01, 4.93, 4.7,
        4.81, 4.5, 4.51, 4.44, 4.33, 4.37, 4.23, 4.22, 4.06, 4.01, 4.02, 3.84, 3.84, 3.83, 3.83, 4.02, 4.02, 4.02,
    ]
    panel = PanelSpec(
        xlim=(1980.0, 2009.05),
        ylim=(-6.0, 4.0),
        xticks=[float(y) for y in range(1980, 2009, 2)],
        yticks=[(float(v), f"{v:.1f}".replace("-", "−")) for v in range(-6, 5)],
        y2lim=(6.0, 0.0),
        y2ticks=[(float(v), f"{v:.1f}") for v in range(7)],
        xlabel="年",
        ylabel="%",
        y2label="%",
        lines=[
            LineSeries(x=gap_x, y=gap_y, color_idx=0, width=1.1),
            LineSeries(x=[1980.0 + i / 4 for i in range(len(unemployment))], y=unemployment, color_idx=0, width=3.0, axis="y2"),
        ],
        annotations=[
            Annotation(x=2007.2, y=1.0, text="GDP缺口", dx=-75, dy=-50, align="end"),
            Annotation(x=1993.0, y=0.55, text="完全失业率", dx=-30, dy=130),
            Annotation(x=1993.0, y=0.55, text="（刻度右侧，轴反转）", dx=-30, dy=160, arrow=False),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="3-11", title="图 3-11 失业率与 GDP 缺口", panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "1-1": _fig_1_1,
        "1-2": _fig_1_2,
        "1-3": _fig_1_3,
        "1-4": _fig_1_4,
        "1-5": _fig_1_5,
        "2-1": _fig_2_1,
        "2-2": _fig_2_2,
        "3-1": _fig_3_1,
        "3-2": _fig_3_2,
        "3-3": _fig_3_3,
        "3-5": _fig_3_5,
        "3-6": _fig_3_6,
        "3-7": _fig_3_7,
        "3-8": _fig_3_8,
        "3-9": _fig_3_9,
        "3-11": _fig_3_11,
    }
