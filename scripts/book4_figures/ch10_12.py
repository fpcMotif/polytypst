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


def _quarters(start: int, values: list[float]) -> list[float]:
    return [start + 0.25 * i for i in range(len(values))]


def _fig_10_1(mode: ThemeMode = "mono") -> str:
    small = [
        24, 25, 23, 25, 28, 30, 30, 30, 31, 28, 26, 22, 14, 11, 13, 5,
        2, 3, 3.5, 2, 4.5, 4, 3, 2.5, 2, 3.5, 4.5, 2, 4, 6, 8, 9.5,
        10, 11, 13, 14, 14, 11.5, 13, 13.5, 11.5, 10, 0, -16, -18, -19, -19, -17,
        -13, -9, -6, -4, -3, -2, -2.5, -3.5, -3, -2.5, -5, -7, -8.5, -9, -9.5, -10,
        -9.5, -8, -5, -3.5, -1, 1, 3, 5, 6, 7.5, 8.5, 10, 11.5, 11, 9, 9,
        9, 8.5, 7.5, 6, 4, 2,
    ]
    mid = [
        40, 39.5, 37, 37, 38, 36.5, 35, 37, 37, 34, 31, 22, 11, 13, 4, -2,
        -12, -5, -4.5, -3.5, 1.5, -0.5, 0.5, 1, 1.5, 4, 7, 9, 10, 12, 14, 15,
        17, 20, 22.5, 22.5, 21, 21.5, 21.5, 21, 21, 18, 5, -15, -16, -18, -20, -16,
        -10, -6, -3, 0, 2.5, 3.5, 4, 4.5, 5, 3.5, -1, -4.5, -3.5, -5, -6.5, -7,
        -7, -4, -2, -2, 2, 7, 8.5, 10, 11, 14.5, 14.5, 15.5, 16, 15.5, 15, 16.5,
        15.5, 15, 14, 12.5, 12, 10.5,
    ]
    large = [
        43, 45, 43, 41, 41, 43, 39, 36, 36, 34.5, 31, 22, 8, 2, 0, -18,
        -38, -31, -26, -21, -7, -7, -7, -4, -2, 5, 12, 15, 18, 19.5, 23, 25,
        27, 30, 34, 35, 34, 33, 33, 34, 32, 30, 28, 11, -28, -18, -20, -22,
        -12, -3, 4, 9, 13, 16, 18, 16.5, 17, 16.5, 16, 10, 5, 5, 5, 3,
        4, 6, 8, 8.5, 12, 16, 17, 19.5, 22, 23, 24, 25, 26.5, 24.5, 24.5, 24.5,
        24, 23.5, 23, 23, 22, 17,
    ]
    panel = PanelSpec(
        xlim=(1986.75, 2008.6),
        ylim=(-50.0, 50.0),
        xticks=[(float(y), f"{y}年1月") for y in (1988, 1993, 1998, 2003, 2008)],
        yticks=[float(v) for v in range(-50, 51, 10)],
        ylabel="（%）",
        lines=[
            LineSeries(x=_quarters(1987, small), y=small, label="中小企业", color_idx=2, style="dotted", width=2.4),
            LineSeries(x=_quarters(1987, mid), y=mid, label="中坚企业", color_idx=1, style="dashed", width=2.0),
            LineSeries(x=_quarters(1987, large), y=large, label="大企业", color_idx=0, style="solid", width=2.4),
        ],
    )
    spec = FigureSpec(fig_id="10-1", title="图 10-1 金融机构对信贷投放的态度 DI", panels=[panel])
    return render_figure_svg(spec, mode)


def _employment_response(fig_id: str, title: str, sme: list[float], large: list[float], mode: ThemeMode) -> str:
    xs = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    panel = PanelSpec(
        xlim=(-0.5, 5.5),
        ylim=(-3.0, 0.5),
        xticks=xs,
        yticks=[-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5],
        ylabel="（%）",
        lines=[
            LineSeries(x=xs, y=sme, label="中小、中坚企业", color_idx=0, style="solid", width=2.2),
            LineSeries(x=xs, y=large, label="大企业", color_idx=1, style="dashed", width=2.4),
        ],
    )
    return render_figure_svg(FigureSpec(fig_id=fig_id, title=title, panels=[panel]), mode)


def _fig_10_2(mode: ThemeMode = "mono") -> str:
    return _employment_response(
        "10-2",
        "图 10-2 针对销售额冲击的雇用调整：机电",
        [-3.0, -0.3, -0.38, -0.06, 0.0, 0.05],
        [-0.92, -0.38, -0.2, -0.07, -0.04, 0.0],
        mode,
    )


def _fig_10_3(mode: ThemeMode = "mono") -> str:
    return _employment_response(
        "10-3",
        "图 10-3 针对销售额冲击的雇用调整：房地产",
        [-2.62, 0.12, -0.42, 0.07, -0.05, 0.03],
        [-1.76, -0.7, -0.36, -0.2, -0.08, -0.03],
        mode,
    )


def _fig_11_2(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1981, 2006)]
    cabinet = [
        0, 0.5, 0.8, 1, 1.2, 1.5, 2, 2, 2, 2.5, 4, 6.5, 9, 14, 23, 32, 40, 61, 75, 82, 89, 97, 104.5, 113, 118,
    ]
    fsa_years = [float(y) for y in range(1992, 2006)]
    fsa = [1, 5.5, 10.5, 23, 30.5, 44.5, 57.5, 64.5, 70, 80.5, 86.5, 92, 95, 95]
    panel = PanelSpec(
        xlim=(1980.5, 2005.5),
        ylim=(0.0, 140.0),
        xticks=[float(y) for y in range(1981, 2006, 2)],
        yticks=[float(v) for v in range(0, 141, 20)],
        xlabel="年",
        ylabel="（万亿日元）",
        legend_loc="bottom",
        lines=[
            LineSeries(x=years, y=cabinet, label="内阁府", color_idx=0, style="solid", marker="circle", width=2.0),
            LineSeries(x=fsa_years, y=fsa, label="金融厅", color_idx=1, style="dashed", marker="square", width=2.2),
        ],
    )
    spec = FigureSpec(fig_id="11-2", title="图 11-2 不良债务处理金额（累计金额）的变化", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_11_3(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1981, 2006)]
    sna = [
        570, 590, 600, 590, 610, 620, 640, 680, 700, 780, 820, 870, 890,
        910, 920, 940, 1010, 970, 960, 960, 950, 950, 950, 960, 990,
    ]
    utilization = [
        620, 625, 630, 665, 670, 650, 700, 760, 810, 880, 915, 905, 880,
        885, 895, 920, 970, 920, 920, 940, 890, 900, 930, 990, 1030,
    ]
    tobin = [
        30, 60, 175, 245, 330, 475, 425, 575, 535, 175, 200, 295, 495,
        700, 865, 780, 730, 970, 1520, 1260, 1150, 1240, 1820, 1640, 2440,
    ]
    npl_years = [float(y) for y in range(1995, 2006)]
    npl = [895, 900, 900, 895, 885, 870, 860, 850, 845, 855, 870]
    panel = PanelSpec(
        xlim=(1980.5, 2005.5),
        ylim=(0.0, 3000.0),
        xticks=[float(y) for y in range(1981, 2006, 2)],
        yticks=[float(v) for v in range(0, 3001, 500)],
        xlabel="年",
        ylabel="（万亿日元）",
        legend_loc="bottom",
        lines=[
            LineSeries(x=years, y=sna, label="SNA", color_idx=2, style="solid", marker="circle", width=1.8),
            LineSeries(x=years, y=utilization, label="资本利用率调整", color_idx=1, style="dashdot", marker="square", width=1.8),
            LineSeries(x=years, y=tobin, label="托宾 q", color_idx=0, style="solid", marker="triangle", width=1.8),
            LineSeries(x=npl_years, y=npl, label="不良债权调整", color_idx=3, style="dashed", marker="cross", width=2.0),
        ],
    )
    spec = FigureSpec(fig_id="11-3", title="图 11-3 资本的变化", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_11_4(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1981, 2006)]
    sna = [
        1.89, 1.9, 1.9, 1.86, 1.82, 1.82, 1.85, 1.84, 1.83, 1.9, 1.95, 2.04, 2.14,
        2.15, 2.14, 2.13, 2.17, 2.27, 2.31, 2.28, 2.31, 2.32, 2.33, 2.33, 2.37,
    ]
    utilization = [
        2.0, 1.92, 2.08, 2.03, 1.98, 1.91, 2.0, 2.08, 2.06, 2.2, 2.11, 2.0, 1.99,
        2.21, 2.19, 2.21, 2.15, 2.15, 2.26, 2.27, 2.04, 2.24, 2.33, 2.36, 2.52,
    ]
    npl_years = [float(y) for y in range(1992, 2006)]
    npl = [2.02, 2.1, 2.13, 2.14, 2.1, 2.1, 2.19, 2.19, 2.13, 2.15, 2.15, 2.12, 2.11, 2.13]
    panel = PanelSpec(
        xlim=(1980.5, 2005.5),
        ylim=(0.0, 3.0),
        xticks=[float(y) for y in range(1981, 2006, 2)],
        yticks=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        xlabel="年",
        legend_loc="bottom",
        lines=[
            LineSeries(x=years, y=sna, label="SNA", color_idx=2, style="solid", marker="circle", width=1.8),
            LineSeries(x=years, y=utilization, label="资本利用率调整", color_idx=0, style="solid", marker="square", width=2.0),
            LineSeries(x=npl_years, y=npl, label="不良债权调整", color_idx=1, style="dashed", marker="cross", width=2.0),
        ],
    )
    spec = FigureSpec(fig_id="11-4", title="图 11-4 资本系数的变化", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_12_1(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1983, 2008)]
    stock = [
        93, 112, 128, 190, 245, 290, 350, 275, 235, 170, 196, 195, 200,
        192, 155, 137, 188, 140, 103, 85, 106, 115, 160, 170, 150,
    ]
    land = [
        82.5, 86, 91.5, 103, 129, 167, 209, 277, 286, 243, 196, 174, 151,
        135, 123, 117, 107, 98, 89, 82, 75, 69, 67, 69, 72,
    ]
    loans = [
        213, 250, 284, 319, 348, 378, 415, 445, 465, 475, 481, 482, 487,
        489, 494, 490, 469, 465, 449, 432, 413, 403, 408, 415, 417,
    ]
    panel = PanelSpec(
        xlim=(1982.5, 2007.5),
        ylim=(0.0, 400.0),
        y2lim=(0.0, 600.0),
        xticks=[float(y) for y in range(1983, 2008, 3)],
        yticks=[float(v) for v in range(0, 401, 50)],
        y2ticks=[float(v) for v in range(0, 601, 100)],
        xlabel="年",
        ylabel="（指数）",
        y2label="（万亿日元）",
        legend_loc="bottom",
        lines=[
            LineSeries(x=years, y=stock, label="股价", color_idx=2, style="dotted", width=2.4),
            LineSeries(x=years, y=land, label="地价（右轴）", color_idx=1, style="dashed", width=2.2),
            LineSeries(x=years, y=loans, color_idx=0, style="solid", width=2.4, axis="y2"),
        ],
        annotations=[
            Annotation(x=2001.5, y=500.0, text="银行贷款", arrow=False, axis="y2", dy=-4.0),
        ],
    )
    spec = FigureSpec(fig_id="12-1", title="图 12-1 日本的股价、地价和银行贷款", panels=[panel])
    return render_figure_svg(spec, mode)


Segment = tuple[str, list[float], int, float]


def _signed_stack(years: list[float], segments: list[Segment], width: float = 0.5) -> list[BarSeries]:
    up = [0.0] * len(years)
    down = [0.0] * len(years)
    bars: list[BarSeries] = []
    for label, values, color_idx, opacity in segments:
        bottoms = []
        for i, v in enumerate(values):
            if v >= 0:
                bottoms.append(up[i])
                up[i] += v
            else:
                bottoms.append(down[i])
                down[i] += v
        bars.append(
            BarSeries(x=years, y=values, label=label, color_idx=color_idx, bottom=bottoms, width=width, opacity=opacity)
        )
    return bars


def _flow_panel(years: list[float], bars: list[BarSeries], ylim: tuple[float, float], step: float, ylabel: str) -> PanelSpec:
    return PanelSpec(
        xlim=(years[0] - 0.6, years[-1] + 0.6),
        ylim=ylim,
        xticks=years,
        yticks=[ylim[0] + step * i for i in range(round((ylim[1] - ylim[0]) / step) + 1)],
        xlabel="年",
        ylabel=ylabel,
        legend_loc="bottom",
        bars=bars,
    )


FLOW_YEARS = [float(y) for y in range(1996, 2009)]


def _fig_12_6(mode: ThemeMode = "mono") -> str:
    segments: list[Segment] = [
        ("直接投资", [-2.5, -3, -3, -3, -3, -4.3, -3.5, -3, -3, -4.5, -6, -9, -13.5], 4, 0.95),
        ("股票投资", [-1, -1.5, -1.5, -3, -2, -1.7, -4.7, -0.7, -2.5, -3, -3, -2.5, -6.5], 1, 0.95),
        ("债券投资", [-10.5, -4, -11.5, -13.5, -7, -11.6, -5.8, -20, -16, -19, -5.5, -12, -13], 3, 0.95),
        ("贷款", [-1, -20, -1, 31, 6.5, -3, -7.2, 11, -4, -10, -7, -16.5, 10], 0, 0.95),
    ]
    panel = _flow_panel(FLOW_YEARS, _signed_stack(FLOW_YEARS, segments), (-50.0, 40.0), 10.0, "")
    spec = FigureSpec(fig_id="12-6", title="图 12-6 日本向世界的资本流动", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_12_7(mode: ThemeMode = "mono") -> str:
    segments: list[Segment] = [
        ("亚洲", [-0.1, 0.6, 0.6, 0.2, 0.4, 0.2, 0.2, 0.1, -0.95, -0.3, -0.7, -1.0, 0.15], 2, 0.95),
        ("北美", [-5.5, -2.85, -2.3, -4.4, -1.5, -8.0, -3.1, -7.3, -6.6, -6.3, -2.8, -2.8, -8.5], 5, 0.95),
        ("中南美", [-1.6, -2.3, -4.6, -4.6, -2.3, -3.0, -5.1, -2.1, -6.3, -4.35, -0.5, -4.05, -0.9], 4, 0.95),
        ("大洋洲", [-0.5, 0.4, 0.7, -0.25, 0.0, 0.0, -0.25, -0.5, -0.65, -0.7, -0.5, -1.3, -1.4], 1, 0.95),
        ("西欧", [-2.5, -1.9, -7.6, -8.0, -4.9, -0.2, -0.4, -8.7, -3.8, -9.0, -3.7, -5.4, -6.9], 3, 0.95),
        ("中东", [0.0, 0.3, 0.3, 0.0, 0.0, -0.2, 0.0, 0.0, -0.2, -0.15, 0.0, -0.15, 0.0], 4, 0.45),
        ("非洲", [-0.1, 0.0, 0.0, 0.0, -0.1, -0.5, 0.0, -0.15, 0.0, -0.1, -0.2, -0.1, -0.3], 0, 0.95),
    ]
    panel = _flow_panel(FLOW_YEARS, _signed_stack(FLOW_YEARS, segments), (-25.0, 5.0), 5.0, "（万亿日元）")
    spec = FigureSpec(fig_id="12-7", title="图 12-7 日本向世界的证券投资（股票投资、债券投资）", panels=[panel], height=560)
    return render_figure_svg(spec, mode)


def _fig_12_8(mode: ThemeMode = "mono") -> str:
    segments: list[Segment] = [
        ("直接投资", [-1.05, -1.55, -1.0, -0.15, -0.25, -1.0, -1.05, -0.65, 0.0, -1.85, -2.0, -2.3, -2.4], 4, 0.95),
        ("股票投资", [-0.45, 0.45, 0.2, -0.15, -0.1, 0.0, 0.2, 0.0, 0.0, -0.3, -0.6, -0.5, 0.25], 1, 0.95),
        ("债券投资", [0.0, 0.25, 0.35, -0.15, -0.1, 0.0, 0.0, 0.0, 0.0, 0.0, -0.2, -0.5, -0.1], 3, 0.95),
        ("贷款", [1.0, -5.4, 5.3, 10.8, 1.55, 0.75, -1.4, 2.65, 1.4, 0.0, 2.3, -2.55, -0.5], 0, 0.95),
    ]
    loan_outflow_2004 = [
        BarSeries(x=[2004.0], y=[-1.2], color_idx=0, bottom=[0.0], width=0.5, opacity=0.95),
        BarSeries(x=[2004.0], y=[-0.45], color_idx=1, bottom=[-1.2], width=0.5, opacity=0.95),
        BarSeries(x=[2004.0], y=[-0.45], color_idx=3, bottom=[-1.65], width=0.5, opacity=0.95),
    ]
    bars = _signed_stack(FLOW_YEARS, segments) + loan_outflow_2004
    panel = _flow_panel(FLOW_YEARS, bars, (-8.0, 12.0), 2.0, "（万亿日元）")
    spec = FigureSpec(fig_id="12-8", title="图 12-8 日本向亚洲的资本流动", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_12_10(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1989, 2009)]
    by_industry = {
        "化学": [40, 30, 40, 30, 100, 100, 100, 80, 100, 80, 60, 40, 100, 100, 200, 300, 700, 560, 380, 490],
        "金属": [60, 50, 30, 50, 80, 160, 350, 200, 180, 90, 70, 30, 170, 120, 180, 440, 410, 310, 590, 590],
        "普通机械": [30, 20, 30, 30, 250, 120, 450, 290, 240, 130, 30, 60, 150, 170, 380, 430, 490, 580, 660, 730],
        "电机": [80, 50, 160, 250, 380, 500, 900, 430, 500, 160, 40, 430, 660, 390, 490, 510, 950, 1480, 950, 1060],
        "运输设备": [20, 20, 20, 60, 130, 240, 400, 310, 150, 180, 130, 120, 270, 250, 980, 1820, 1160, 1370, 890, 1040],
        "其他制造业": [50, 70, 150, 400, 630, 780, 1130, 670, 630, 320, 230, 170, 170, 610, 450, 560, 1930, 1380, 1450, 1100],
        "非制造业": [310, 260, 290, 480, 300, 650, 860, 740, 550, 340, 200, 190, 210, 280, 720, 630, 1610, 1470, 2360, 1640],
    }
    fills = {
        "化学": (3, 0.95), "金属": (2, 0.95), "普通机械": (1, 0.95), "电机": (4, 0.95),
        "运输设备": (0, 0.95), "其他制造业": (1, 0.45), "非制造业": (5, 0.95),
    }
    legend_order = ["非制造业", "其他制造业", "运输设备", "电机", "普通机械", "金属", "化学"]
    bottoms: dict[str, list[float]] = {}
    running = [0.0] * len(years)
    for name in reversed(legend_order):
        bottoms[name] = list(running)
        running = [r + v for r, v in zip(running, by_industry[name])]
    bars = [
        BarSeries(
            x=years, y=[float(v) for v in by_industry[name]], label=name, color_idx=fills[name][0],
            opacity=fills[name][1], bottom=bottoms[name], width=0.5,
        )
        for name in legend_order
    ]
    yen = [138.0, 144.8, 134.7, 126.7, 111.2, 102.2, 94.1, 108.8, 121.0, 130.9, 113.9, 107.8, 121.5, 125.4, 115.9, 108.2, 110.2, 116.3, 117.8]
    panel = PanelSpec(
        xlim=(1988.4, 2008.6),
        ylim=(0.0, 8000.0),
        y2lim=(160.0, 80.0),
        xticks=years,
        yticks=[float(v) for v in range(0, 8001, 1000)],
        y2ticks=[float(v) for v in range(80, 161, 10)],
        xlabel="年",
        ylabel="（亿日元）",
        y2label="（日元）",
        legend_loc="bottom",
        vlines=[(2004.5, "", "dashed")],
        bars=bars,
        lines=[LineSeries(x=years[:-1], y=yen, label="日元/美元", color_idx=0, style="solid", width=1.6, axis="y2")],
    )
    spec = FigureSpec(fig_id="12-10", title="图 12-10 日本向中国的直接投资以及日元汇率", panels=[panel], height=580)
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "12-1": _fig_12_1,
        "12-6": _fig_12_6,
        "12-7": _fig_12_7,
        "12-8": _fig_12_8,
        "12-10": _fig_12_10,
        "10-1": _fig_10_1,
        "10-2": _fig_10_2,
        "10-3": _fig_10_3,
        "11-2": _fig_11_2,
        "11-3": _fig_11_3,
        "11-4": _fig_11_4,
    }
