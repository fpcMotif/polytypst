from __future__ import annotations

from collections.abc import Callable, Sequence

from scripts.book2_figures.engine import (
    Annotation,
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    render_figure_svg,
)

COUNTRIES_7 = ["日本", "韩国", "德国", "法国", "英国", "意大利", "美国"]


def _years(first: int, last: int) -> list[float]:
    return [float(y) for y in range(first, last + 1)]


def _fixed_ticks(values: Sequence[float], digits: int) -> list[float | tuple[float, str]]:
    return [(v, f"{v:.{digits}f}".replace("-", "−")) for v in values]


def _stacked_up_and_down(
    xs: Sequence[float], parts: Sequence[tuple[str, int, Sequence[float]]], width: float
) -> list[BarSeries]:
    up = [0.0] * len(xs)
    down = [0.0] * len(xs)
    bars: list[BarSeries] = []
    for label, color_idx, values in parts:
        bottoms = []
        for i, v in enumerate(values):
            if v >= 0:
                bottoms.append(up[i])
                up[i] += v
            else:
                bottoms.append(down[i])
                down[i] += v
        bars.append(
            BarSeries(x=list(xs), y=list(values), label=label, color_idx=color_idx, width=width, bottom=bottoms, opacity=1.0)
        )
    return bars


def _fig_10_1(mode: ThemeMode = "mono") -> str:
    periods = ["1970—1975", "1975—1980", "1980—1985", "1985—1990", "1990—1995", "1995—2000", "2000—2005"]
    xs = [float(i) for i in range(len(periods))]
    hours = [-0.63, 0.73, 0.25, 0.24, -0.65, -1.05, -1.2]
    quality = [0.86, 0.87, 0.75, 0.49, 0.45, 0.46, 0.33]
    capital = [1.33, 1.12, 1.82, 1.99, 1.31, 0.85, 0.75]
    tfp = [2.51, 1.79, 1.46, 2.42, -0.12, 0.53, 1.8]
    growth = [4.04, 4.55, 4.3, 5.15, 0.95, 0.77, 1.17]
    panel = PanelSpec(
        xlim=(-0.5, 6.5),
        ylim=(-2.0, 6.0),
        xticks=list(zip(xs, periods)),
        yticks=_fixed_ticks([-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 2),
        xlabel="年",
        ylabel="%",
        bars=_stacked_up_and_down(
            xs,
            [("工时增加", 3, hours), ("劳动力质量提高", 4, quality), ("资本服务投入增加的贡献", 0, capital), ("TFP增长率", 1, tfp)],
            0.46,
        )[::-1],
        lines=[LineSeries(x=xs, y=growth, label="实质增加值增长率", color_idx=0, width=2.2)],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-1", title="图 10-1 增长的因素分解——基于市场经济和增加值", panels=[panel], width=900, height=560)
    return render_figure_svg(spec, mode)


def _fig_10_2(mode: ThemeMode = "mono") -> str:
    series = [
        ("韩国", "solid", 0, 2.6, 1970, [0.344, 0.337, 0.330, 0.336, 0.332, 0.305, 0.295, 0.278, 0.255, 0.225, 0.183, 0.175, 0.166, 0.161,
                                        0.159, 0.159, 0.157, 0.155, 0.149, 0.140, 0.129, 0.120, 0.112, 0.108, 0.106, 0.105]),
        ("日本", "dashdot", 0, 1.8, 1971, [0.328, 0.310, 0.285, 0.245, 0.215, 0.202, 0.190, 0.189, 0.187, 0.180, 0.171, 0.163, 0.159,
                                          0.158, 0.157, 0.157, 0.156, 0.158, 0.159, 0.158, 0.154, 0.145, 0.132, 0.124]),
        ("意大利", "solid", 0, 1.1, 1970, [0.140, 0.139, 0.137, 0.143, 0.148, 0.140, 0.140, 0.142, 0.143, 0.149, 0.154, 0.149, 0.146,
                                          0.143, 0.144, 0.144, 0.145, 0.145, 0.145, 0.145, 0.141, 0.138, 0.135, 0.133, 0.134]),
        ("美国", "dotted", 2, 1.6, 1961, [0.106, 0.110, 0.110, 0.112, 0.115, 0.116, 0.112, 0.110, 0.106, 0.099, 0.100, 0.101, 0.104,
                                         0.098, 0.097, 0.098, 0.103, 0.106, 0.104, 0.098, 0.098, 0.097, 0.099, 0.103, 0.104, 0.105,
                                         0.106, 0.107, 0.106, 0.104, 0.098, 0.096, 0.098, 0.103]),
        ("德国", "longdash", 0, 1.8, 1961, [0.137, 0.132, 0.129, 0.130, 0.128, 0.125, 0.121, 0.129, 0.130, 0.126, 0.121, 0.118, 0.116,
                                           0.109, 0.106, 0.107, 0.108, 0.108, 0.107, 0.103, 0.099, 0.098, 0.100, 0.103, 0.106, 0.108,
                                           0.109, 0.111, 0.113, 0.111, 0.109, 0.107, 0.104, 0.103]),
        ("英国", "solid", 5, 2.4, 1971, [0.104, 0.106, 0.113, 0.103, 0.093, 0.098, 0.103, 0.106, 0.103, 0.096, 0.093, 0.096, 0.099,
                                        0.103, 0.105, 0.106, 0.107, 0.108, 0.110, 0.112, 0.114, 0.113, 0.110, 0.112]),
        ("加拿大", "dashed", 0, 1.8, 1970, [0.139, 0.139, 0.143, 0.152, 0.153, 0.150, 0.147, 0.146, 0.149, 0.155, 0.153, 0.143, 0.128,
                                           0.139, 0.144, 0.144, 0.140, 0.140, 0.140, 0.137, 0.130, 0.121, 0.113, 0.107, 0.104]),
        ("法国", "dotted", 0, 2.2, 1976, [0.103, 0.105, 0.106, 0.105, 0.100, 0.100, 0.101, 0.102, 0.104, 0.106, 0.107, 0.108, 0.110,
                                         0.110, 0.105, 0.099, 0.099, 0.101, 0.104]),
    ]
    panel = PanelSpec(
        xlim=(1961.0, 1995.0),
        ylim=(0.0, 0.4),
        xticks=[float(y) for y in range(1965, 1996, 5)],
        yticks=_fixed_ticks([0.0, 0.1, 0.2, 0.3, 0.4], 1),
        xlabel="年",
        lines=[
            LineSeries(
                x=_years(start, start + len(ys) - 1), y=ys, label=label, color_idx=ci, style=style, width=width, fixed_style=True
            )
            for label, style, ci, width, start, ys in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-2", title="图 10-2 七个主要 OECD 国家和韩国的资本总回报率的变化", panels=[panel], width=900, height=560)
    return render_figure_svg(spec, mode)


def _fig_10_3(mode: ThemeMode = "mono") -> str:
    series = [
        ("日本", "square", 0, "solid", 1.6, _years(1981, 2005),
         [2.27, 2.36, 2.50, 2.57, 2.70, 2.69, 2.78, 2.77, 2.86, 2.93, 2.93, 2.89, 2.86, 2.81, 2.93, 2.98, 3.10, 3.22, 3.23,
          3.26, 3.37, 3.43, 3.43, 3.43, 3.57]),
        ("美国", "triangle", 0, "solid", 1.6, _years(1981, 2004),
         [2.37, 2.53, 2.59, 2.64, 2.76, 2.74, 2.70, 2.66, 2.64, 2.69, 2.74, 2.65, 2.53, 2.44, 2.55, 2.57, 2.61, 2.65, 2.70,
          2.77, 2.77, 2.69, 2.70, 2.70]),
        ("法国", "circle", 0, "solid", 1.6, _years(1981, 2005),
         [1.90, 1.98, 2.00, 2.09, 2.14, 2.14, 2.18, 2.20, 2.24, 2.34, 2.34, 2.34, 2.39, 2.34, 2.30, 2.28, 2.20, 2.16, 2.17,
          2.17, 2.22, 2.26, 2.19, 2.16, 2.16]),
        ("EU-25", None, 5, "solid", 3.6, _years(1995, 2003), [1.81, 1.79, 1.79, 1.81, 1.87, 1.88, 1.89, 1.90, 1.90]),
        ("中国", "circle", 3, "solid", 1.6, _years(2002, 2005), [1.07, 1.13, 1.22, 1.34]),
        ("日本（自然科学）", "square", 3, "solid", 1.6, _years(1981, 2005),
         [2.05, 2.14, 2.27, 2.34, 2.47, 2.46, 2.51, 2.52, 2.65, 2.70, 2.70, 2.66, 2.63, 2.57, 2.68, 2.74, 2.85, 2.97, 2.97,
          3.00, 3.09, 3.14, 3.14, 3.14, 3.27]),
        ("德国", "triangle", 3, "solid", 1.6, _years(1981, 2005),
         [2.32, 2.41, 2.43, 2.43, 2.62, 2.62, 2.75, 2.75, 2.73, 2.61, 2.48, 2.38, 2.29, 2.20, 2.21, 2.22, 2.27, 2.28, 2.41,
          2.49, 2.49, 2.50, 2.52, 2.52, 2.52]),
        ("英国", "cross", 0, "solid", 1.4, [1981.0, *_years(1983, 2004)],
         [2.40, 2.21, 2.23, 2.25, 2.27, 2.21, 2.15, 2.16, 2.17, 2.08, 2.04, 2.06, 2.03, 1.97, 1.87, 1.81, 1.81, 1.89, 1.89,
          1.83, 1.83, 1.79, 1.73]),
        ("韩国", None, 0, "dashed", 1.2, _years(1991, 2005),
         [1.85, 1.93, 2.12, 2.33, 2.38, 2.42, 2.50, 2.39, 2.28, 2.45, 2.60, 2.55, 2.70, 2.85, 3.00]),
    ]
    end_labels = [(3.55, 3.55), (3.27, 3.27), (3.29, 3.01), (2.68, 2.68), (2.51, 2.48), (2.13, 2.13), (1.89, 1.89),
                  (1.73, 1.69), (1.34, 1.34)]
    panel = PanelSpec(
        xlim=(1980.5, 2007.4),
        ylim=(1.0, 4.0),
        xticks=[float(y) for y in range(1981, 2006, 2)],
        yticks=_fixed_ticks([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], 1),
        xlabel="财年",
        ylabel="%",
        zero_line=False,
        vlines=[(2005.5, "", "solid")],
        lines=[
            *(
                LineSeries(x=xs, y=ys, label=label, color_idx=ci, style=style, marker=marker, width=width, fixed_style=True)
                for label, marker, ci, style, width, xs, ys in series
            ),
            LineSeries(x=[2001.4, 2002.0], y=[1.0, 1.07], color_idx=3, width=1.6, fixed_style=True),
        ],
        annotations=[
            Annotation(x=2005.8, y=y, text=f"{text:.2f}", dx=0, dy=0, arrow=False, align="start", fontsize=10.5)
            for text, y in end_labels
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-3", title="图 10-3 主要国家研究支出占 GDP 比重的变化", panels=[panel], width=900, height=580)
    return render_figure_svg(spec, mode)


def _growth_panel(title: str, labor: list[float], capital: list[float], tfp: list[float], growth: list[float]) -> PanelSpec:
    xs = [float(i) for i in range(7)]
    return PanelSpec(
        title=title,
        xlim=(-0.5, 6.5),
        ylim=(-2.0, 10.0),
        xticks=list(zip(xs, COUNTRIES_7)),
        yticks=_fixed_ticks([-2.0, 0.0, 2.0, 4.0, 6.0, 8.0, 10.0], 1),
        ylabel="年均（%）",
        bars=_stacked_up_and_down(
            xs, [("劳动力投入增加的贡献", 0, labor), ("资本服务投入增加的贡献", 1, capital), ("TFP增长率", 4, tfp)], 0.72
        )[::-1],
        lines=[LineSeries(x=xs, y=growth, label="实际增加值增长率", color_idx=0, marker="square", width=1.6)],
        legend_loc="bottom",
    )


def _fig_10_4(mode: ThemeMode = "mono") -> str:
    panels = [
        _growth_panel(
            "1980—1995",
            [0.39, 2.21, -0.22, -0.11, -0.31, 0.28, 1.13],
            [2.01, 5.59, 1.2, 0.7, 1.16, 0.78, 1.11],
            [1.5, 1.82, 0.81, 1.19, 1.5, 0.8, 0.71],
            [3.9, 9.48, 1.89, 1.78, 2.45, 1.87, 2.95],
        ),
        _growth_panel(
            "1995—2005",
            [-0.53, 0.69, -0.42, 0.68, 0.76, 0.74, 0.64],
            [1.08, 5.05, 0.95, 0.86, 1.49, 1.01, 1.3],
            [0.49, -0.94, 0.4, 0.84, 0.92, -0.74, 1.67],
            [0.98, 4.78, 0.95, 2.35, 3.19, 1.18, 3.65],
        ),
    ]
    spec = FigureSpec(
        fig_id="10-4", title="图 10-4 主要发达国家增长的因素分解——基于市场经济和增加值", panels=panels, cols=2, width=1300, height=780
    )
    return render_figure_svg(spec, mode)


def _tfp_panel(
    title: str, ylim: tuple[float, float], ystep: float, early: list[float], late: list[float | None],
    late_bottom: list[float] | None = None, tick_labels: dict[float, str] | None = None, legend: bool = False,
) -> PanelSpec:
    xs = [float(i) for i in range(7)]
    late_x = [x + 0.18 for x, v in zip(xs, late) if v is not None]
    late_y = [v for v in late if v is not None]
    n = round((ylim[1] - ylim[0]) / ystep)
    ticks = [ylim[0] + ystep * i for i in range(n + 1)]
    labels = tick_labels or {}
    return PanelSpec(
        title=title,
        xlim=(-0.5, 6.5),
        ylim=ylim,
        xticks=list(zip(xs, COUNTRIES_7)),
        yticks=[(v, labels.get(v, f"{v:.1f}".replace("-", "−"))) for v in ticks],
        bars=[
            BarSeries(x=[x - 0.18 for x in xs], y=early, label="1980—1995" if legend else "", color_idx=2, width=0.36, opacity=1.0),
            BarSeries(x=late_x, y=late_y, label="1995—2005" if legend else "", color_idx=3, width=0.36, bottom=late_bottom, opacity=1.0),
        ],
        legend_loc="bottom" if legend else "none",
    )


def _fig_10_5(mode: ThemeMode = "mono") -> str:
    uk_bar_printed_from_plus_0_23 = [0.0, 0.0, 0.0, 0.0, 0.23, 0.0, 0.0]
    panels = [
        _tfp_panel("机电、邮政和通信", (0.0, 10.0), 1.0,
                   [7.06, 8.25, 2.07, 3.16, 3.86, 2.28, 4.56], [5.35, 7.65, 4.65, 5.86, 3.65, 2.64, 8.63]),
        _tfp_panel("机电以外的制造业", (-1.5, 3.0), 0.5,
                   [1.4, 2.6, 1.2, 1.4, 2.7, 1.9, 0.9], [-0.69, -0.42, 1.3, 1.78, -1.06, 1.2, 2.2],
                   late_bottom=uk_bar_printed_from_plus_0_23),
        _tfp_panel("第一产业、建筑、水电燃气", (-3.0, 3.0), 1.0,
                   [-0.3, -0.8, 0.8, 2.5, 1.4, 2.0, -0.7], [0.9, -2.5, 1.5, 0.38, 1.1, -0.9, 2.1]),
        _tfp_panel("金融和对企业服务", (-5.0, 4.0), 1.0,
                   [0.7, 3.0, -0.5, -0.9, -1.1, -2.3, -0.35], [-0.15, -4.6, -3.3, -0.8, 1.1, -0.4, 0.4]),
        _tfp_panel("商业和运输", (-2.0, 4.0), 1.0,
                   [3.1, 1.9, 1.6, 2.5, 2.1, 1.0, 1.27], [0.9, -1.5, 1.5, 0.38, 1.08, -0.95, 2.1]),
        _tfp_panel("对个人和社会服务", (-3.0, 1.5), 0.5,
                   [-2.1, -2.0, -0.3, -1.4, -0.82, -2.0, -0.23], [-0.1, -2.7, -0.7, 0.9, -0.7, -2.0, None],
                   tick_labels={-3.0: "−4.0"}, legend=True),
    ]
    spec = FigureSpec(fig_id="10-5", title="图 10-5 市场经济中 TFP 增长率（按行业和国家）", panels=panels, rows=3, cols=2, width=1300, height=1700)
    return render_figure_svg(spec, mode)


def _fig_10_6(mode: ThemeMode = "mono") -> str:
    series = [
        ("日本", "square", 0, "solid", 1.6, 1980,
         [0.3, 0.42, 0.5, 0.6, 0.72, 0.85, 1.0, 1.12, 1.3, 1.48, 1.38, 1.45, 1.52, 1.5, 1.48, 1.72, 2.15, 2.28, 2.38, 2.55,
          2.57, 2.92, 2.88, 3.05, 3.22, 3.8]),
        ("韩国", "cross", 0, "solid", 1.4, 1980,
         [1.0, 1.08, 1.2, 1.27, 1.35, 1.42, 1.75, 1.85, 1.88, 2.0, 2.1, 2.4, 2.42, 2.5, 2.78, 3.1, 3.9, 4.1, 3.48, 4.15,
          5.1, 4.35, 4.05, 3.58, 3.55, 3.6]),
        ("美国", "triangle", 3, "solid", 1.6, 1980,
         [0.85, 0.95, 1.0, 1.1, 1.15, 1.25, 1.38, 1.45, 1.65, 1.8, 1.9, 2.05, 2.3, 2.4, 2.78, 3.1, 3.8, 4.95, 6.15, 7.75,
          8.95, 9.05, 8.8, 9.25, 9.85, 11.2]),
        ("英国", None, 0, "dotted", 1.6, 1980,
         [0.85, 0.95, 1.0, 1.05, 1.15, 1.28, 1.35, 1.45, 1.85, 2.3, 2.45, 2.38, 2.4, 2.5, 2.8, 3.5, 4.1, 4.5, 6.1, 7.5,
          9.0, 9.9, 10.4, 10.35, 11.25, 12.65]),
        ("法国", None, 0, "dashed", 1.6, 1980,
         [0.4, 0.45, 0.52, 0.6, 0.7, 0.8, 0.95, 1.05, 1.25, 1.38, 1.42, 1.45, 1.45, 1.48, 1.55, 1.8, 2.15, 2.4, 2.9, 3.2,
          3.4, 3.8, 3.7, 3.65, 3.65]),
        ("德国", "circle", 3, "solid", 1.6, 1991,
         [1.85, 1.95, 1.95, 2.0, 2.1, 2.45, 2.55, 3.25, 4.15, 4.75, 5.05, 5.1, 5.2, 5.2, 6.4]),
        ("意大利", None, 5, "solid", 2.0, 1980,
         [0.75, 0.8, 0.85, 0.9, 1.0, 1.1, 1.2, 1.35, 1.5, 1.65, 1.72, 1.75, 1.8, 1.8, 1.85, 2.0, 1.9, 2.25, 2.5, 2.9,
          3.65, 3.95, 3.85, 3.75, 4.2, 3.85]),
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2005.5),
        ylim=(0.0, 14.0),
        xticks=[float(y) for y in range(1980, 2005, 2)],
        yticks=[0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0],
        xlabel="年",
        ylabel="%",
        lines=[
            LineSeries(
                x=_years(start, start + len(ys) - 1), y=ys, label=label, color_idx=ci, style=style, marker=marker,
                width=width, fixed_style=True,
            )
            for label, marker, ci, style, width, start, ys in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-6", title="图 10-6 ICC 投资占 GDP 比重——主要发达国家比较", panels=[panel], width=900, height=540)
    return render_figure_svg(spec, mode)


def _asset_panel(title: str, last: int, intangible: list[float], tangible: list[float]) -> PanelSpec:
    xs = _years(1980, last)
    return PanelSpec(
        title=title,
        xlim=(1979.5, last + 0.5),
        ylim=(6.0, 26.0),
        xticks=[float(y) for y in range(1980, last + 1, 2)],
        xtick_vertical=True,
        yticks=[float(v) for v in range(6, 27, 2)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=intangible, label="无形资产投资/GDP", color_idx=1, marker="square", width=1.6, fixed_style=True),
            LineSeries(x=xs, y=tangible, label="有形资产投资/GDP", color_idx=0, marker="square", width=1.6, fixed_style=True),
        ],
        legend_loc="bottom",
    )


def _fig_10_7(mode: ThemeMode = "mono") -> str:
    panels = [
        _asset_panel(
            "日本",
            2005,
            [6.65, 6.95, 7.3, 7.6, 7.75, 8.25, 8.45, 8.6, 8.85, 9.25, 9.45, 9.6, 9.65, 9.5, 9.45, 9.5, 9.75, 10.2, 10.9,
             11.0, 11.4, 11.6, 11.5, 11.45, 11.4, 11.5],
            [23.0, 22.2, 21.5, 20.9, 21.2, 21.5, 21.05, 21.55, 22.6, 23.45, 24.45, 24.3, 23.6, 22.8, 20.85, 20.95, 21.25,
             21.3, 20.7, 19.35, 18.75, 19.05, 20.05, 18.85, 19.35, 19.55],
        ),
        _asset_panel(
            "美国",
            2003,
            [9.3, 10.0, 10.4, 9.9, 10.2, 10.5, 10.4, 10.4, 10.6, 10.75, 11.0, 11.25, 11.1, 11.15, 11.1, 11.6, 12.1, 12.75,
             13.2, 13.5, 14.15, 13.9, 13.35, 13.15],
            [16.6, 17.1, 16.85, 15.0, 15.7, 15.65, 14.6, 13.9, 13.75, 13.75, 13.2, 12.25, 11.7, 12.0, 12.5, 13.2, 13.35,
             13.7, 13.9, 13.95, 14.0, 13.1, 11.45, 11.25],
        ),
    ]
    spec = FigureSpec(fig_id="10-7", title="图 10-7 无形和有形资产投资占 GDP 比重", panels=panels, cols=2, width=1300, height=820)
    return render_figure_svg(spec, mode)


def _fig_10_8(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1970, 2006, 5)]
    panel = PanelSpec(
        xlim=(1970.0, 2005.0),
        ylim=(100.0, 240.0),
        xticks=xs,
        yticks=[float(v) for v in range(100, 241, 20)],
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=[100.0, 122.9, 134.1, 163.7, 189.2, 198.2, 216.8, 230.7], label="制造业", color_idx=0,
                       marker="circle", width=1.6, fixed_style=True),
            LineSeries(x=xs, y=[100.0, 107.3, 118.6, 119.3, 133.2, 129.8, 130.7, 139.0],
                       label="非制造业（仅市场经济，不包括住房和未分类部门）", color_idx=0, marker="square", width=1.6, fixed_style=True),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-8", title="图 10-8 制造业和非制造业的 TFP（基于增加值）增长（1970 = 100）", panels=[panel], width=900, height=540)
    return render_figure_svg(spec, mode)


def _fig_10_9(mode: ThemeMode = "mono") -> str:
    series = [
        ("日本：制造业名义总增加值 / 名义GDP", "dashed", 0, 1.8, _years(1971, 2005),
         [0.359, 0.351, 0.344, 0.347, 0.335, 0.304, 0.306, 0.300, 0.296, 0.293, 0.292, 0.291, 0.290, 0.290, 0.293, 0.296,
          0.294, 0.281, 0.279, 0.280, 0.280, 0.280, 0.280, 0.270, 0.260, 0.245, 0.245, 0.245, 0.243, 0.236, 0.233, 0.230,
          0.222, 0.217, 0.216]),
        ("日本：制造业就业人数 / 总就业人数", "dotted", 0, 1.8, _years(1971, 2005),
         [0.266, 0.266, 0.265, 0.270, 0.268, 0.256, 0.251, 0.248, 0.240, 0.237, 0.239, 0.240, 0.237, 0.236, 0.238, 0.240,
          0.241, 0.238, 0.235, 0.237, 0.238, 0.239, 0.240, 0.242, 0.237, 0.232, 0.223, 0.222, 0.217, 0.212, 0.212, 0.208,
          0.206, 0.198, 0.193]),
        ("美国：制造业名义总增加值 / 名义GDP", "solid", 0, 2.8,
         [1960.5, 1961.44, 1962.51, 1964.86, 1965.61, 1966.93, 1967.96, 1968.9, 1969.99, 1970.97, 1971.91, 1974.07,
          1976.14, 1978.3, 1980.37, 1981.49, 1982.53, 1983.18, 1984.5, 1985.53, 1986.76, 1987.88, 1989.01, 1989.76,
          1991.08, 1992.58, 1994.84, 1995.96, 1997.09, 1998.22, 1999.91, 2001.98, 2003.29, 2004.33],
         [0.269, 0.26, 0.267, 0.268, 0.271, 0.272, 0.264, 0.264, 0.256, 0.239, 0.233, 0.232, 0.216, 0.227, 0.222, 0.21,
          0.209, 0.201, 0.196, 0.199, 0.19, 0.186, 0.187, 0.192, 0.183, 0.176, 0.17, 0.173, 0.174, 0.167, 0.164, 0.156,
          0.14, 0.138]),
        ("美国：制造业就业人数 / 总就业人数", "solid", 0, 1.1,
         [1960.5, 1961.44, 1962.79, 1964.62, 1966.93, 1969.99, 1971.91, 1973.13, 1974.16, 1975.1, 1976.14, 1979.05,
          1980.37, 1981.31, 1982.53, 1983.18, 1984.12, 1985.63, 1986.94, 1988.82, 1990.04, 1992.58, 1995.02, 1997.28,
          1999.91, 2001.98, 2004.33],
         [0.283, 0.277, 0.277, 0.271, 0.276, 0.263, 0.241, 0.239, 0.241, 0.236, 0.219, 0.218, 0.215, 0.207, 0.204, 0.197,
          0.19, 0.189, 0.182, 0.173, 0.17, 0.159, 0.152, 0.146, 0.14, 0.131, 0.119]),
    ]
    panel = PanelSpec(
        xlim=(1960.0, 2005.0),
        ylim=(0.1, 0.4),
        xticks=[float(y) for y in range(1960, 2006, 5)],
        yticks=[(v, f"{v:g}") for v in [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]],
        xlabel="年",
        zero_line=False,
        vlines=[(float(y), "", "solid") for y in range(1965, 2005, 5)],
        lines=[
            LineSeries(x=xs, y=ys, label=label, color_idx=ci, style=style, width=width, fixed_style=True)
            for label, style, ci, width, xs, ys in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="10-9", title="图 10-9 制造业在宏观经济整体中的份额——日美比较", panels=[panel], width=900, height=560)
    return render_figure_svg(spec, mode)


def _decomposition_figure(
    fig_id: str, title: str, periods: list[str], parts: list[tuple[str, int, list[float]]], line: tuple[str, list[float]],
    ylim: tuple[float, float], ystep: float, legend_order: list[str], mode: ThemeMode,
) -> str:
    xs = [float(i) for i in range(len(periods))]
    n = round((ylim[1] - ylim[0]) / ystep)
    panel = PanelSpec(
        xlim=(-0.5, len(periods) - 0.5),
        ylim=ylim,
        xticks=list(zip(xs, periods)),
        yticks=_fixed_ticks([ylim[0] + ystep * i for i in range(n + 1)], 1),
        xlabel="期间",
        ylabel="%",
        bars=sorted(_stacked_up_and_down(xs, parts, 0.38), key=lambda b: legend_order.index(b.label)),
        lines=[LineSeries(x=xs, y=line[1], label=line[0], color_idx=0, marker="square", width=1.6)],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], width=900, height=600)
    return render_figure_svg(spec, mode)


def _fig_10_10(mode: ThemeMode = "mono") -> str:
    return _decomposition_figure(
        "10-10",
        "图 10-10 劳动生产率增长的因素分解",
        ["1981—1985", "1985—1990", "1990—1995", "1995—2000", "2000—2003 年"],
        [
            ("内部效应", 2, [3.52, 4.48, 2.8, 1.32, 1.27]),
            ("再配置效应", 0, [-0.59, -0.37, 0.12, 0.0, 0.22]),
            ("进入效应", 1, [1.26, 1.73, 1.16, 0.92, 1.57]),
            ("退出效应", 4, [-0.6, -0.42, -0.40, -0.46, -1.39]),
        ],
        ("劳动生产率增长率", [3.55, 5.42, 3.79, 1.72, 1.62]),
        (-2.0, 7.0),
        1.0,
        ["进入效应", "退出效应", "再配置效应", "内部效应"],
        mode,
    )


def _fig_10_11(mode: ThemeMode = "mono") -> str:
    return _decomposition_figure(
        "10-11",
        "图 10-11 TFP 增长的因素分解",
        ["1981—1985", "1985—1990", "1990—1995", "1995—2000 年"],
        [
            ("内部效应", 2, [1.13, 1.46, 1.03, 0.56]),
            ("再配置效应", 0, [-0.29, -0.25, -0.25, -0.16]),
            ("协方差效应", 5, [0.48, 0.54, 0.56, 0.6]),
            ("进入效应", 1, [0.5, 0.6, 0.44, 0.47]),
            ("退出效应", 4, [-0.33, -0.31, -0.27, -0.39]),
        ],
        ("TFP增长率", [1.49, 2.07, 1.5, 1.09]),
        (-1.0, 3.0),
        0.5,
        ["进入效应", "退出效应", "协方差效应", "再配置效应", "内部效应"],
        mode,
    )


def _fig_10_12(mode: ThemeMode = "mono") -> str:
    points = [
        (-17.8, -0.014), (0.0, 0.168), (0.0, 0.14), (-0.3, -0.025), (0.2, -0.05), (0.8, -0.067), (-0.1, -0.078),
        (0.6, -0.113), (-0.3, -0.12), (-0.3, -0.152), (1.2, -0.162), (0.9, -0.19), (0.3, -0.229), (-0.3, -0.245),
        (1.4, -0.229), (0.0, -0.329), (1.2, -0.327), (1.2, -0.369), (-0.9, -0.357), (2.1, -0.291), (1.9, -0.047),
        (2.2, -0.123), (2.7, -0.169), (2.5, -0.19), (4.1, -0.328), (5.4, -0.03), (6.2, -0.051), (5.3, -0.114),
        (7.6, -0.131), (7.6, -0.164), (5.8, -0.255), (7.5, -0.301), (8.9, -0.095), (18.6, -0.059), (16.5, -0.303),
        (22.9, -0.328), (27.8, -0.305), (0.7, -0.458), (6.4, -0.565), (10.6, -0.675), (4.6, -0.802), (5.3, -0.874),
        (29.3, -1.043),
    ]
    labels = [
        (8.9, -0.095, "汽车", 14), (18.6, -0.11, "玻璃和玻璃制品", 6), (8.4, -0.205, "汽车零部件和附件", 0),
        (27.8, -0.27, "电子零", 14), (27.8, -0.34, "部件", 14), (0.7, -0.458, "医药", 14),
        (6.4, -0.565, "其他电气设备", 14), (10.6, -0.675, "电子计算机和附件", 10), (4.6, -0.802, "民用电子和电气设备", 14),
        (5.3, -0.874, "饮料", 10), (29.3, -1.043, "通信设备", 10),
    ]
    xs: list[float] = []
    ys: list[float | None] = []
    for x, y in points:
        xs += [x, x]
        ys += [y, None]
    panel = PanelSpec(
        xlim=(-30.0, 40.0),
        ylim=(-1.2, 0.4),
        xticks=[(float(v), f"{v}".replace("-", "−")) for v in range(-30, 41, 10)],
        yticks=list(zip([0.4, 0.2, 0.0, -0.2, -0.4, -0.6, -0.8, -1.0, -1.2],
                        ["0.4", "0.2", "0", "−0.2", "−0.4", "−0.4", "−0.8", "−1.0", "−1.2"])),
        xlabel="日本企业在亚洲的名义产值变化（1990—2002）/国内生产（1990）（%）",
        ylabel="退出效应（1990—2003）（%）",
        vlines=[(0.0, "", "solid")],
        lines=[LineSeries(x=xs, y=ys, color_idx=0, marker="diamond", style="none", fixed_style=True)],
        annotations=[
            Annotation(x=x, y=y, text=text, dx=dx, dy=0, arrow=False, align="start", fontsize=11.0)
            for x, y, text, dx in labels
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="10-12", title="图 10-12 从对东亚直接投资和劳动生产率提高的因素分解中得出的退出效应（1990—2003）",
        panels=[panel], width=860, height=680,
    )
    return render_figure_svg(spec, mode)


def _business_panel(title: str, series: list[tuple[str, str | None, int, str, float, int, list[float]]], legend: bool) -> PanelSpec:
    return PanelSpec(
        title=title,
        xlim=(1980.5, 2000.3),
        ylim=(0.0, 16.0),
        xticks=[*(float(y) for y in range(1981, 2000, 2)), 2000.0],
        xtick_vertical=True,
        yticks=[float(v) for v in range(0, 17, 2)],
        xlabel="年",
        lines=[
            LineSeries(
                x=_years(start, start + len(ys) - 1), y=ys, label=label if legend else "", color_idx=ci, style=style,
                marker=marker, width=width, fixed_style=True,
            )
            for label, marker, ci, style, width, start, ys in series
        ],
        legend_loc="bottom" if legend else "none",
    )


def _fig_10_13(mode: ThemeMode = "mono") -> str:
    opening = [
        ("所有行业：美国", "circle", 0, "solid", 1.6, 1983,
         [13.3, 14.3, 14.4, 14.45, 14.85, 13.9, 13.5, 13.85, 12.85, 13.05, 13.5, 13.85, 13.8, 13.95, 14.35]),
        ("所有行业：日本", None, 5, "solid", 2.4, 1981,
         [7.1, 6.45, 6.2, 5.95, 5.8, 6.0, 6.8, 7.4, 6.8, 6.3, 5.75, 5.2, 4.65, 4.85, 4.6, 4.75, 4.35, 4.0, 4.45, 4.9]),
        ("批发零售餐饮店：日本", None, 0, "dashed", 1.4, 1986,
         [6.5, 7.3, 7.75, 6.75, 5.9, 5.45, 5.25, 4.95, 5.1, 5.05, 4.95, 4.45, 4.25, 4.95, 5.6]),
        ("服务业：日本", "triangle", 0, "solid", 1.6, 1986,
         [7.45, 8.25, 8.8, 8.15, 7.85, 7.45, 6.65, 5.75, 5.65, 5.5, 5.75, 5.15, 4.8, 5.45, 6.4]),
        ("制造业：日本", "square", 0, "solid", 1.6, 1986,
         [4.25, 4.6, 5.1, 4.5, 4.1, 3.7, 2.85, 2.35, 2.35, 2.35, 2.35, 2.25, 1.95, 2.1, 2.3]),
    ]
    closing = [
        ("所有行业：美国", "circle", 0, "solid", 1.6, 1983,
         [12.1, 10.7, 11.85, 12.75, 11.25, 12.25, 12.5, 12.5, 12.05, 12.05, 11.7, 11.55, 12.7, 11.85, 12.15]),
        ("所有行业：日本", None, 5, "solid", 2.4, 1981,
         [3.8, 5.7, 4.25, 4.2, 4.15, 4.15, 3.7, 3.35, 3.2, 3.05, 3.35, 3.35, 3.5, 3.55, 3.75, 2.6, 2.75, 3.3, 4.15, 4.1]),
        ("批发零售餐饮店：日本", None, 0, "dashed", 1.4, 1986,
         [4.55, 4.2, 3.95, 3.85, 3.65, 3.95, 3.95, 4.0, 4.0, 4.3, 3.05, 3.35, 3.6, 4.25, 4.75]),
        ("服务业：日本", "triangle", 0, "solid", 1.6, 1986,
         [3.15, 3.05, 2.95, 2.9, 2.75, 2.95, 3.0, 3.05, 3.0, 3.1, 2.05, 2.25, 2.45, 3.35, 3.35]),
        ("制造业：日本", "square", 0, "solid", 1.6, 1986,
         [4.2, 3.7, 3.25, 3.05, 2.75, 2.95, 3.15, 3.55, 3.65, 3.8, 2.8, 2.8, 3.5, 4.35, 4.25]),
    ]
    panels = [_business_panel("面板A：开业率%", opening, True), _business_panel("面板B：倒闭率%", closing, True)]
    spec = FigureSpec(fig_id="10-13", title="图 10-13 机构的开业率和倒闭率——日美比较", panels=panels, cols=2, width=1300, height=900)
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "10-1": _fig_10_1,
        "10-2": _fig_10_2,
        "10-3": _fig_10_3,
        "10-4": _fig_10_4,
        "10-5": _fig_10_5,
        "10-6": _fig_10_6,
        "10-7": _fig_10_7,
        "10-8": _fig_10_8,
        "10-9": _fig_10_9,
        "10-10": _fig_10_10,
        "10-11": _fig_10_11,
        "10-12": _fig_10_12,
        "10-13": _fig_10_13,
    }
