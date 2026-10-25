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


def _points(pts: list[tuple[float, float]]) -> tuple[list[float], list[float | None]]:
    xs: list[float] = []
    ys: list[float | None] = []
    for xv, yv in pts:
        xs.extend([xv, xv])
        ys.extend([yv, None])
    return xs, ys


def fig_11_1(mode: ThemeMode = "mono") -> str:
    decades = ["20世纪70年代", "20世纪80年代", "20世纪90年代", "2000年以来"]
    series = [
        ("制造业", [-6.1, -1.7, -5.7, -0.6], 4),
        ("服务产业", [6.9, 2.9, 9.1, 1.9], 1),
        ("其中服务业", [2.4, 3.1, 6.3, 1.2], 3),
        ("其他", [0.5, -1.1, -3.4, -1.4], 0),
    ]
    offsets = [-0.3, -0.1, 0.1, 0.3]
    bars = [
        BarSeries(x=[i + off for i in range(4)], y=vals, label=label, color_idx=c, width=0.18, opacity=1.0)
        for (label, vals, c), off in zip(series, offsets)
    ]
    panel = PanelSpec(
        xlim=(-0.5, 3.5),
        ylim=(-8.0, 10.0),
        xticks=[(i, d) for i, d in enumerate(decades)],
        yticks=[(v, f"{v:.1f}") for v in range(-8, 11, 2)],
        ylabel="百分率（%）",
        bars=bars,
        annotations=[
            Annotation(x=2.45, y=y, text=text, dx=0, dy=0, arrow=False, fontsize=9.5, align="start")
            for y, text in [
                (-2.6, "（GDP份额）"),
                (-3.8, "1970年 ⇒ 2006年"),
                (-5.0, "制造业 37.5% ⇒ 23.2%"),
                (-6.2, "服务产业 47.2% ⇒ 68.2%"),
                (-7.4, "其他 15.2% ⇒ 8.6%"),
            ]
        ],
        legend_loc="top",
    )
    spec = FigureSpec(
        fig_id="11-1",
        title="图 11-1 每10年名义 GDP占比变化",
        panels=[panel],
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def fig_11_2(mode: ThemeMode = "mono") -> str:
    years = list(range(1980, 2004))
    gdp = [1.00, 0.99, 1.00, 1.01, 1.04, 1.065, 1.04, 1.02, 1.03, 1.055, 1.08, 1.07,
           1.035, 0.97, 0.95, 0.97, 0.985, 0.99, 0.93, 0.95, 1.00, 0.95, 0.93, 1.01]
    emp = [1.00, 0.99, 0.965, 0.96, 0.99, 0.98, 0.962, 0.943, 0.936, 0.936, 0.935, 0.93,
           0.882, 0.84, 0.818, 0.79, 0.765, 0.73, 0.71, 0.68, 0.66, 0.645, 0.635, 0.625]
    prod = [1.00, 1.025, 1.06, 1.035, 1.06, 1.09, 1.105, 1.09, 1.105, 1.125, 1.157, 1.16,
            1.157, 1.16, 1.17, 1.266, 1.315, 1.35, 1.31, 1.38, 1.51, 1.49, 1.51, 1.69]
    defl = [1.00, 1.01, 1.04, 1.02, 0.983, 0.908, 0.906, 0.883, 0.868, 0.86, 0.852, 0.837,
            0.82, 0.793, 0.78, 0.756, 0.747, 0.72, 0.76, 0.727, 0.69, 0.678, 0.688, 0.653]
    panel = PanelSpec(
        xlim=(1979.5, 2003.5),
        ylim=(0.0, 1.8),
        xticks=[(y, str(y)) for y in range(1980, 2002, 3)],
        yticks=[(v / 10, f"{v / 10:.2f}") for v in range(0, 19, 2)],
        ylabel="（制造业/服务产业、1980年=1）",
        xlabel="年",
        lines=[
            LineSeries(x=years, y=gdp, label="实际GDP", color_idx=5, style="dotted", marker="diamond", width=2.0),
            LineSeries(x=years, y=emp, label="就业人数", color_idx=2, style="dashed", marker="square", width=2.0),
            LineSeries(x=years, y=prod, label="人均实际生产率", color_idx=4, style="longdash", marker="triangle", width=2.0),
            LineSeries(x=years, y=defl, label="平减指数", color_idx=0, style="solid", marker="triangle", width=2.4),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="11-2",
        title="图 11-2 制造业和服务产业相对变化",
        panels=[panel],
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def fig_11_3(mode: ThemeMode = "mono") -> str:
    manu = [
        (0.561, 0.71), (0.596, 0.77), (0.625, 1.07), (0.625, 0.6), (0.644, 0.79), (0.666, 0.83), (0.684, 0.58),
        (0.697, 0.88), (0.704, 0.73), (0.729, 0.98), (0.732, 0.64), (0.759, 0.73), (0.764, 0.83), (0.765, 0.49),
        (0.772, 0.59), (0.778, 0.74), (0.786, 0.84), (0.81, 0.91), (0.818, 1.04), (0.83, 0.83), (0.833, 0.74),
        (0.834, 1.03), (0.844, 1.14), (0.848, 2.12), (0.85, 0.87), (0.851, 1.01), (0.862, 0.96), (0.867, 0.8),
        (0.871, 1.04), (0.876, 0.93), (0.879, 0.89), (0.887, 0.78), (0.899, 0.98), (0.902, 0.92), (0.906, 1.09),
        (0.917, 1.03), (0.917, 0.84), (0.926, 0.94), (0.934, 0.81), (0.938, 0.96), (0.963, 0.88), (0.966, 0.96),
        (0.979, 0.99), (0.984, 2.29), (0.99, 1.29), (1.008, 0.93), (1.009, 2.19), (1.037, 0.96), (1.086, 0.9),
        (1.149, 2.91),
    ]
    serv = [
        (0.771, 3.14), (0.846, 0.74), (0.895, 1.02), (0.918, 0.96), (0.94, 1.1), (0.961, 1.39), (0.961, 0.89),
        (0.967, 1.55), (0.971, 1.14), (0.993, 1.6), (0.995, 1.35), (0.999, 0.95), (1.001, 0.76), (1.028, 1.39),
        (1.04, 0.98), (1.075, 1.1), (1.083, 1.26), (1.093, 1.19), (1.112, 1.73), (1.118, 1.07), (1.13, 1.16),
        (1.146, 1.04), (1.154, 1.09), (1.173, 1.26), (1.175, 0.96), (1.195, 1.19), (1.201, 1.91), (1.218, 1.3),
        (1.232, 1.08), (1.285, 1.17), (1.295, 0.82), (1.303, 1.38), (1.346, 1.35), (1.35, 1.06), (1.387, 1.9),
        (1.403, 1.78), (1.413, 1.15), (1.434, 1.83), (1.564, 1.4), (1.878, 1.82), (2.033, 0.99), (2.466, 1.65),
    ]
    yticks = [(v / 2, f"{v / 2:g}") for v in range(8)]
    mx, my = _points(manu)
    sx, sy = _points(serv)
    panels = [
        PanelSpec(
            title="（1）20世纪90年代的制造业",
            xlim=(0.0, 1.4),
            ylim=(0.0, 3.5),
            xticks=[(v / 5, f"{v / 5:g}") for v in range(8)],
            yticks=yticks,
            xlabel="员工数量",
            ylabel="实际产出额",
            hlines=[(1.0, "", "solid")],
            vlines=[(1.0, "", "solid")],
            lines=[LineSeries(x=mx, y=my, color_idx=0, marker="diamond", width=0.0)],
            legend_loc="none",
        ),
        PanelSpec(
            title="（2）20世纪90年代的服务产业",
            xlim=(0.0, 3.0),
            ylim=(0.0, 3.5),
            xticks=[(v / 2, f"{v / 2:g}") for v in range(7)],
            yticks=yticks,
            xlabel="员工数量",
            ylabel="实际产出额",
            hlines=[(1.0, "", "solid")],
            vlines=[(1.0, "", "solid")],
            lines=[LineSeries(x=sx, y=sy, color_idx=0, marker="diamond", width=0.0)],
            legend_loc="none",
        ),
    ]
    spec = FigureSpec(
        fig_id="11-3",
        title="图 11-3 制造业和服务产业实际产出额以及雇佣者数增长的比较",
        panels=panels,
        rows=2,
        cols=1,
        width=860,
        height=900,
    )
    return render_figure_svg(spec, mode)


def _share_panel(values: list[float], ylim: tuple[float, float], notes: list[Annotation]) -> PanelSpec:
    years = list(range(1982, 2004))
    return PanelSpec(
        xlim=(1981.5, 2003.5),
        ylim=ylim,
        xticks=[(y, str(y)) for y in range(1982, 2003, 2)],
        yticks=list(range(int(ylim[0]), int(ylim[1]) + 1)),
        ylabel="%",
        xlabel="年",
        lines=[LineSeries(x=years, y=values, color_idx=0, marker="diamond", width=2.4)],
        annotations=notes,
        legend_loc="none",
    )


def fig_11_4(mode: ThemeMode = "mono") -> str:
    values = [39.85, 39.85, 40.25, 41.05, 41.0, 40.95, 40.05, 40.45, 40.25, 40.4, 39.55,
              38.9, 38.95, 39.6, 38.65, 38.85, 38.0, 37.1, 37.7, 38.7, 38.45, 37.8]
    notes = [
        Annotation(x=1986, y=41.0, text="1986年41.0%", dx=0, dy=-14, arrow=False, fontsize=10.5),
        Annotation(x=1991.4, y=40.4, text="1991年40.4%", dx=0, dy=-4, arrow=False, fontsize=10.5, align="start"),
        Annotation(x=1999.6, y=37.1, text="1999年37.1%", dx=0, dy=14, arrow=False, fontsize=10.5),
        Annotation(x=2003.3, y=37.8, text="2003年", dx=0, dy=16, arrow=False, fontsize=10.5, align="end"),
        Annotation(x=2003.3, y=37.8, text="37.8%", dx=0, dy=38, arrow=False, fontsize=10.5, align="end"),
    ]
    spec = FigureSpec(
        fig_id="11-4",
        title="图 11-4 初中、高中毕业者在制造业中雇佣占比",
        panels=[_share_panel(values, (35.0, 42.0), notes)],
        width=860,
        height=460,
    )
    return render_figure_svg(spec, mode)


def fig_11_5(mode: ThemeMode = "mono") -> str:
    values = [28.25, 29.5, 29.2, 29.6, 29.35, 29.3, 29.05, 28.5, 28.55, 28.2, 27.7,
              28.4, 29.1, 29.5, 28.9, 28.6, 27.65, 27.45, 26.3, 27.3, 27.0, 26.0]
    notes = [
        Annotation(x=1995.4, y=29.5, text="1995年29.5%", dx=0, dy=-6, arrow=False, fontsize=10.5, align="start"),
        Annotation(x=1992, y=27.7, text="1992年27.7%", dx=0, dy=16, arrow=False, fontsize=10.5, align="start"),
        Annotation(x=2003.3, y=26.0, text="2003年26.0%", dx=0, dy=16, arrow=False, fontsize=10.5, align="end"),
    ]
    spec = FigureSpec(
        fig_id="11-5",
        title="图 11-5 大学毕业者在制造业中雇佣占比",
        panels=[_share_panel(values, (24.0, 30.0), notes)],
        note="资料来源：根据日本厚生劳动省《薪酬构造基本统计调查》(各年度) 制作",
        width=860,
        height=460,
    )
    return render_figure_svg(spec, mode)


def fig_11_6(mode: ThemeMode = "mono") -> str:
    ages = ["30～34", "35～39", "40～44", "45～49", "50～54", "55～59"]
    junior = [-15, -10, -19, -28, -57, -115]
    senior = [-38, -56, -37, -53, -72, -118]
    college = [0, -31, -21, -29, -32, -49]
    base = [j + s for j, s in zip(junior, senior)]
    panel = PanelSpec(
        xlim=(-0.5, 5.5),
        ylim=(-350.0, 50.0),
        xticks=[(i, a) for i, a in enumerate(ages)],
        yticks=list(range(-350, 51, 50)),
        ylabel="1000人",
        xlabel="年龄",
        bars=[
            BarSeries(x=list(range(6)), y=junior, label="初中毕业", color_idx=4, width=0.48, opacity=1.0),
            BarSeries(x=list(range(6)), y=senior, bottom=junior, label="高中毕业", color_idx=1, width=0.48,
                      opacity=1.0),
            BarSeries(x=[0, 5], y=[4, -6], bottom=[0, base[5]], label="高等专业学校·短期大学毕业", color_idx=3,
                      width=0.48, opacity=1.0),
            BarSeries(x=[1, 2, 3, 4, 5], y=college[1:], bottom=[*base[1:5], base[5] - 6], label="大学毕业",
                      color_idx=0, width=0.48, opacity=1.0),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="11-6",
        title="图 11-6 1990—2000年的制造业中的雇佣变化（学历x年龄）",
        panels=[panel],
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def fig_11_7(mode: ThemeMode = "mono") -> str:
    years = list(range(1981, 2004))
    retail = [568, 608, 575, 605, 621, 562, 642, 716, 741, 771, 824, 900, 713, 553, 613, 678, 749, 737, 844, 932,
              956, 867, 987]
    service = [393, 397, 412, 432, 395, 437, 426, 465, 494, 592, 649, 660, 608, 608, 595, 683, 749, 603, 668, 692,
               722, 722, 735]
    manu = [644, 631, 660, 687, 635, 601, 539, 581, 591, 647, 649, 611, 521, 487, 493, 434, 491, 342, 408, 372, 373,
            342, 331]
    transport = [106, 97, 89, 93, 85, 86, 92, 101, 102, 108, 136, 142, 180, 126, 109, 118, 157, 169, 129, 120, 130,
                 122, 126]
    finance = [176, 180, 163, 166, 172, 170, 178, 177, 185, 202, 210, 171, 137, 159, 179, 135, 116, 93, 120, 106, 95,
               90, 102]
    shares = [
        (1140, "1991年 ⇒ 2003年"),
        (1055, "制造业 26.5% ⇒ 14.2%"),
        (970, "服务业 26.4% ⇒ 32.6%"),
        (885, "批发零售等 33.4% ⇒ 42.9%"),
    ]
    panel = PanelSpec(
        xlim=(1980.5, 2003.5),
        ylim=(0.0, 1200.0),
        xticks=[(y, str(y)) for y in range(1981, 2004, 2)],
        yticks=list(range(0, 1201, 200)),
        ylabel="1000人",
        xlabel="年",
        lines=[
            LineSeries(x=years, y=retail, label="批发、零售业及饮食店", color_idx=5, style="dotted", marker="diamond",
                       width=2.0),
            LineSeries(x=years, y=service, label="服务业", color_idx=2, style="dashed", marker="diamond", width=2.0),
            LineSeries(x=years, y=manu, label="制造业", color_idx=0, style="solid", marker="circle", width=2.4),
            LineSeries(x=years, y=transport, label="运输、通信业", color_idx=4, style="longdash", marker="cross",
                       width=2.0),
            LineSeries(x=years, y=finance, label="金融、保险业", color_idx=3, style="dashdot", marker="triangle",
                       width=2.0),
        ],
        annotations=[
            Annotation(x=1981.0, y=y, text=text, dx=0, dy=0, arrow=False, fontsize=10.0, align="start")
            for y, text in shares
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="11-7",
        title="图 11-7 未就业者希望入职产业",
        panels=[panel],
        width=860,
        height=600,
    )
    return render_figure_svg(spec, mode)


def fig_11_8(mode: ThemeMode = "mono") -> str:
    years = list(range(1981, 2004))
    mm_f = [72.9, 64.7, 75.9, 73.3, 72.8, 69.6, 67.7, 66.1, 65.6, 59.4, 55.4, 55.3, 50.4, 52.9, 57.5, 62.1, 53.9,
            46.1, 47.1, 53.2, 45.5, 42.9, 54.9]
    mm_m = [64.2, 64.9, 69.4, 74.0, 72.6, 68.1, 61.9, 69.2, 65.6, 62.6, 65.8, 63.6, 58.9, 57.3, 63.9, 54.8, 61.1,
            54.4, 60.2, 54.9, 53.5, 55.6, 60.2]
    ms_f = [8.4, 13.2, 6.6, 10.0, 11.2, 9.3, 8.4, 11.5, 12.0, 15.6, 18.1, 14.9, 13.9, 13.8, 17.0, 19.1, 20.3, 20.5,
            17.8, 18.6, 24.3, 19.6, 23.9]
    ms_m = [9.5, 10.5, 9.8, 6.6, 7.8, 7.7, 11.5, 8.1, 10.1, 13.0, 10.9, 12.1, 19.2, 14.5, 11.1, 15.2, 16.5, 23.4,
            18.0, 19.5, 21.7, 20.6, 19.5]
    panel = PanelSpec(
        xlim=(1980.5, 2003.5),
        ylim=(0.0, 80.0),
        xticks=[(y, str(y)) for y in range(1981, 2004, 3)],
        yticks=list(range(0, 81, 10)),
        ylabel="%",
        xlabel="年",
        lines=[
            LineSeries(x=years, y=mm_m, label="制造业→制造业（男性）", color_idx=2, style="dashed", marker="square",
                       width=2.0),
            LineSeries(x=years, y=mm_f, label="制造业→制造业（女性）", color_idx=0, style="solid", marker="square",
                       width=2.4),
            LineSeries(x=years, y=ms_m, label="制造业→服务业（男性）", color_idx=2, style="dashed", marker="triangle",
                       width=2.0),
            LineSeries(x=years, y=ms_f, label="制造业→服务业（女性）", color_idx=0, style="solid", marker="triangle",
                       width=2.4),
        ],
        annotations=[
            Annotation(x=1993.5, y=74.0, text="从制造业向制造业的变动", dx=0, dy=0, arrow=False),
            Annotation(x=2000.3, y=64.0, text="男性", dx=0, dy=0, arrow=False),
            Annotation(x=1998.6, y=38.5, text="女性", dx=0, dy=0, arrow=False),
            Annotation(x=1988.0, y=26.0, text="从制造业向服务业的变动", dx=0, dy=0, arrow=False),
            Annotation(x=2003.0, y=25.0, text="女性", dx=-48, dy=-36),
            Annotation(x=1995.0, y=10.5, text="男性", dx=36, dy=20),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="11-8",
        title="图 11-8 前职为制造业的转职者的目标就业行业",
        panels=[panel],
        width=860,
        height=500,
    )
    return render_figure_svg(spec, mode)


PREFACE_REER = [
    (1990.0, 115.5), (1990.103, 110.0), (1990.189, 106.5), (1990.275, 108.5), (1990.395, 109.0), (1990.481, 111.5),
    (1990.567, 110.5), (1990.653, 117.0), (1990.739, 122.0), (1990.825, 123.0), (1990.911, 120.0), (1990.997, 119.5),
    (1991.082, 122.0), (1991.168, 119.5), (1991.289, 120.0), (1991.426, 119.5), (1991.512, 121.0), (1991.598, 121.0),
    (1991.684, 125.0), (1991.821, 125.0), (1991.942, 128.0), (1992.027, 125.0), (1992.113, 121.0), (1992.199, 120.0),
    (1992.337, 123.0), (1992.457, 122.0), (1992.577, 127.5), (1992.715, 127.5), (1992.887, 127.0), (1993.007, 132.0),
    (1993.144, 138.0), (1993.265, 141.0), (1993.368, 144.5), (1993.436, 145.0), (1993.54, 150.5), (1993.625, 147.0),
    (1993.746, 144.0), (1993.832, 141.0), (1993.918, 141.5), (1994.021, 147.0), (1994.124, 148.0), (1994.227, 147.0),
    (1994.296, 147.5), (1994.399, 152.0), (1994.467, 149.0), (1994.57, 150.0), (1994.639, 149.0), (1994.742, 149.0),
    (1994.863, 145.5), (1994.948, 145.0), (1995.034, 146.0), (1995.12, 155.0), (1995.206, 165.0), (1995.292, 162.0),
    (1995.378, 162.0), (1995.464, 157.0), (1995.533, 146.0), (1995.636, 138.0), (1995.722, 137.0), (1995.808, 135.0),
    (1995.893, 135.0), (1995.979, 130.0), (1996.065, 130.0), (1996.151, 128.0), (1996.237, 127.0), (1996.323, 125.0),
    (1996.409, 125.0), (1996.495, 124.0), (1996.581, 125.0), (1996.667, 122.0), (1996.753, 120.5), (1996.838, 120.0),
    (1996.924, 118.0), (1997.01, 112.0), (1997.096, 113.0), (1997.182, 113.0), (1997.268, 118.0), (1997.354, 123.0),
    (1997.44, 123.5), (1997.526, 122.0), (1997.612, 120.5), (1997.698, 120.5), (1997.784, 118.0), (1997.869, 119.0),
    (1997.955, 125.0), (1998.041, 126.0), (1998.127, 122.0), (1998.213, 118.0), (1998.299, 116.0), (1998.385, 113.0),
    (1998.471, 112.5), (1998.557, 110.0), (1998.643, 117.0), (1998.729, 127.0), (1998.814, 128.0), (1998.9, 132.0),
    (1998.986, 136.0), (1999.072, 132.0), (1999.158, 130.0), (1999.244, 126.5), (1999.33, 128.0), (1999.416, 129.0),
    (1999.502, 135.0), (1999.588, 142.0), (1999.674, 143.0), (1999.759, 145.0), (1999.845, 148.0), (1999.931, 144.0),
    (2000.017, 139.5), (2000.103, 141.0), (2000.189, 142.5), (2000.275, 141.0), (2000.361, 141.0), (2000.447, 139.5),
    (2000.533, 140.5), (2000.619, 141.5), (2000.704, 140.5), (2000.79, 140.0), (2000.876, 136.0), (2000.962, 128.0),
    (2001.048, 130.0), (2001.134, 125.0), (2001.22, 123.0), (2001.306, 124.5), (2001.392, 125.0), (2001.478, 123.0),
    (2001.564, 124.0), (2001.649, 127.0), (2001.735, 125.5), (2001.821, 125.5), (2001.907, 121.0), (2001.993, 115.5),
    (2002.079, 115.5), (2002.165, 116.0), (2002.251, 115.0), (2002.337, 117.5), (2002.423, 118.5), (2002.509, 123.0),
    (2002.595, 122.5), (2002.68, 120.0), (2002.766, 117.0), (2002.852, 118.5), (2002.938, 117.5), (2003.024, 118.0),
    (2003.11, 117.0), (2003.196, 116.5), (2003.282, 116.5), (2003.368, 117.5), (2003.454, 115.5), (2003.54, 115.5),
    (2003.625, 116.5), (2003.711, 122.0), (2003.797, 124.0), (2003.883, 123.5), (2003.969, 123.5), (2004.055, 123.5),
    (2004.141, 121.0), (2004.227, 119.5), (2004.313, 121.0), (2004.399, 116.0), (2004.485, 118.5), (2004.57, 119.0),
    (2004.656, 118.0), (2004.742, 117.5), (2004.828, 117.0), (2004.914, 120.0), (2005.0, 120.0), (2005.086, 120.5),
    (2005.172, 117.0), (2005.258, 115.0), (2005.344, 114.0), (2005.43, 115.0), (2005.515, 114.0), (2005.601, 111.0),
    (2005.687, 110.5), (2005.773, 106.0), (2005.859, 104.0), (2005.945, 103.0), (2006.031, 103.5), (2006.117, 102.5),
    (2006.203, 102.5), (2006.289, 101.5), (2006.375, 104.0), (2006.46, 102.0), (2006.546, 101.0), (2006.632, 101.0),
    (2006.718, 100.5), (2006.804, 99.5), (2006.89, 99.0), (2006.976, 96.0), (2007.062, 96.0), (2007.148, 97.0),
    (2007.234, 94.0), (2007.32, 92.0), (2007.405, 91.0), (2007.491, 91.0), (2007.577, 96.0), (2007.663, 96.5),
    (2007.749, 94.5), (2007.835, 96.5), (2007.921, 96.0), (2008.007, 98.0), (2008.093, 99.0), (2008.179, 102.0),
    (2008.265, 100.0), (2008.351, 98.0), (2008.436, 95.5), (2008.522, 95.5), (2008.608, 97.0), (2008.694, 101.0),
    (2008.78, 112.0), (2008.866, 120.0), (2008.952, 126.0), (2009.0, 127.0),
]


def fig_preface_exchange_rate(mode: ThemeMode = "mono") -> str:
    panel = PanelSpec(
        xlim=(1990.0, 2009.0),
        ylim=(80.0, 170.0),
        xticks=[(y, str(y)) for y in range(1990, 2010)],
        yticks=list(range(80, 171, 10)),
        ylabel="（1973年3月=100）",
        xlabel="年",
        lines=[LineSeries(x=[p[0] for p in PREFACE_REER], y=[p[1] for p in PREFACE_REER], color_idx=0, width=1.6)],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="preface_exchange_rate",
        title="实际有效汇率的走势（1990年1月—2009年1月）",
        subtitle="实际有效汇率的走势（1990年1月—2009年1月）",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "11-1": fig_11_1,
        "11-2": fig_11_2,
        "11-3": fig_11_3,
        "11-4": fig_11_4,
        "11-5": fig_11_5,
        "11-6": fig_11_6,
        "11-7": fig_11_7,
        "11-8": fig_11_8,
        "preface_exchange_rate": fig_preface_exchange_rate,
    }
