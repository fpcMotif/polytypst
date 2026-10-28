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


def _xy(points: list[tuple[float, float]]) -> tuple[list[float], list[float | None]]:
    return [p[0] for p in points], [p[1] for p in points]


def _years(start: int, values: list[float | None]) -> tuple[list[float], list[float | None]]:
    return [float(start + i) for i in range(len(values))], list(values)


def fig_1_1(mode: ThemeMode = "mono") -> str:
    pts = [
        (-13.0, 35.0), (-42.2, 24.5), (-35.2, 17.0), (-24.2, 15.4), (-20.5, 13.7),
        (-8.3, 18.3), (12.2, 19.0), (-13.0, 10.4), (-11.9, 9.6), (-34.5, 8.0),
        (-28.4, 7.3), (-26.3, 7.8), (-31.6, 5.5), (-43.1, 5.3), (-43.0, 1.0),
        (-28.4, 2.4), (-26.3, 0.6), (-24.8, 1.3), (-22.0, 0.8), (-19.4, -2.2),
        (-19.3, 0.3), (-19.0, 3.4), (-18.9, -0.2), (-18.3, 1.0), (-17.0, 3.4),
        (-17.0, 1.0), (-16.3, 2.1), (-16.5, 0.7), (-15.9, 0.2), (-15.8, 3.4),
        (-14.3, 2.0), (-13.3, -0.2), (-11.5, 1.4), (-11.1, 4.0), (-9.9, 2.6),
        (-9.8, -0.4), (-9.7, -1.2), (-8.7, 1.4), (-7.4, 0.7), (-6.3, 2.3),
        (-6.3, -0.3), (-5.2, 5.8), (-4.0, 0.0), (-3.9, -0.8), (-3.2, -0.5),
        (-1.8, -0.8), (-0.5, 1.6), (-0.5, -0.8), (0.8, 2.9), (2.3, 1.6),
        (5.0, 0.1), (4.6, -5.1),
    ]
    labels = [
        (-15.5, 30.5, "电子应用装置"),
        (-44.0, 27.0, "民生用电机"),
        (-11.0, 14.0, "化学纤维"),
        (7.0, 15.0, "半导体·IC"),
        (-49.0, 7.5, "纤维产品"),
        (-48.5, 0.0, "钢铁"),
        (0.5, 5.0, "电子零部件"),
    ]
    spec = FigureSpec(
        fig_id="1-1",
        title="图 1-1 进口渗透和就业（1990—2000年）",
        panels=[
            PanelSpec(
                xlim=(-50.0, 20.0),
                ylim=(-10.0, 40.0),
                xticks=[(-50, "−50"), (-40, "−40"), (-30, "−30"), (-20, "−20"), (-10, "−10"), (0, "0"), (10, "10"), (20, "20%")],
                yticks=[(-10, "−10"), (0, "0"), (10, "10"), (20, "20"), (30, "30"), (40, "40")],
                xlabel="就业人数变化率",
                ylabel="进口渗透率的增长（%）",
                vlines=[(0.0, "", "solid")],
                scatters=[([p[0] for p in pts], [p[1] for p in pts], [], 0, False)],
                annotations=[
                    Annotation(x=x, y=y, text=t, dx=0.0, dy=0.0, arrow=False, align="start", fontsize=11.0)
                    for x, y, t in labels
                ],
                legend_loc="none",
            )
        ],
    )
    return render_figure_svg(spec, mode)


_IMPORT_TOTAL = [
    (1985.0, 210), (1985.25, 212), (1985.5, 205), (1985.75, 192), (1986.0, 175), (1986.25, 168),
    (1986.5, 128), (1986.75, 106), (1987.0, 113), (1987.5, 115), (1988.0, 118), (1988.5, 110),
    (1989.0, 112), (1989.25, 106), (1989.75, 120), (1990.0, 122), (1990.5, 130), (1990.75, 124),
    (1991.0, 132), (1991.5, 118), (1992.0, 112), (1992.5, 110), (1993.0, 106), (1993.5, 100),
    (1994.0, 92), (1994.5, 90), (1995.0, 92), (1995.5, 87), (1995.75, 92), (1996.0, 96),
    (1996.5, 100), (1997.0, 108), (1997.33, 115), (1997.6, 106), (1998.0, 110), (1998.5, 105),
    (1998.8, 108), (1999.1, 92), (1999.5, 96), (2000.0, 94), (2000.5, 97), (2001.0, 98),
    (2001.5, 101), (2002.0, 97), (2002.5, 100), (2003.0, 97), (2003.5, 98), (2004.0, 94),
    (2004.5, 103), (2005.0, 104), (2005.25, 102), (2005.5, 112), (2006.0, 124), (2006.5, 131),
    (2006.9, 141), (2007.1, 137), (2007.35, 140), (2007.5, 150),
]


def fig_1_2(mode: ThemeMode = "mono") -> str:
    export = [
        (1985.0, 168), (1985.5, 160), (1986.0, 145), (1986.5, 133), (1987.0, 134), (1987.5, 128),
        (1988.0, 126), (1988.5, 126), (1989.0, 126), (1989.5, 132), (1990.0, 136), (1990.33, 141),
        (1990.75, 132), (1991.0, 128), (1991.5, 127), (1992.0, 122), (1992.5, 124), (1993.0, 118),
        (1993.5, 110), (1994.0, 112), (1994.5, 108), (1995.0, 107), (1995.4, 100), (1995.75, 111),
        (1996.0, 112), (1996.5, 110), (1997.0, 112), (1997.5, 110), (1998.0, 116), (1998.6, 121),
        (1999.0, 105), (1999.5, 104), (2000.0, 98), (2000.5, 98), (2001.0, 100), (2001.5, 102),
        (2002.0, 98), (2002.5, 100), (2003.0, 97), (2003.5, 98), (2004.0, 92), (2004.5, 94),
        (2005.0, 94), (2005.5, 96), (2006.0, 98), (2006.5, 100), (2007.0, 102), (2007.5, 105),
    ]
    domestic = [
        (1985.0, 115), (1986.0, 112), (1986.5, 108), (1987.0, 105), (1988.0, 105), (1989.0, 105),
        (1990.0, 107), (1991.0, 109), (1992.0, 108), (1993.0, 106), (1994.0, 104), (1995.0, 103),
        (1996.0, 102), (1997.0, 101), (1998.0, 101), (1999.0, 99), (2000.0, 98), (2001.0, 97),
        (2002.0, 95), (2003.0, 94), (2004.0, 94), (2005.0, 96), (2006.0, 98), (2007.0, 99),
        (2007.5, 100),
    ]
    machinery = [
        (1985.0, 222), (1985.5, 218), (1985.8, 205), (1986.0, 190), (1986.3, 178), (1986.7, 157),
        (1987.0, 156), (1987.5, 150), (1988.0, 146), (1988.5, 138), (1989.0, 132), (1989.5, 140),
        (1990.0, 146), (1990.33, 160), (1990.75, 155), (1991.0, 143), (1991.5, 142), (1992.0, 138),
        (1992.5, 140), (1993.0, 133), (1993.5, 126), (1994.0, 120), (1994.5, 118), (1995.0, 112),
        (1995.25, 112), (1995.5, 102), (1995.75, 108), (1996.0, 110), (1996.5, 112), (1997.0, 115),
        (1997.5, 115), (1998.0, 118), (1998.7, 126), (1999.0, 110), (1999.5, 108), (2000.0, 100),
        (2000.5, 96), (2001.0, 96), (2001.5, 93), (2002.0, 92), (2002.25, 96), (2002.75, 88),
        (2003.0, 86), (2003.5, 84), (2004.0, 80), (2004.5, 78), (2005.0, 77), (2005.5, 76),
        (2006.0, 79), (2006.5, 79), (2007.0, 81), (2007.5, 82),
    ]
    textile = [
        (1985.0, 148), (1985.5, 140), (1986.0, 128), (1986.5, 120), (1986.75, 100), (1987.0, 110),
        (1987.5, 112), (1988.0, 118), (1988.5, 110), (1989.0, 105), (1989.5, 118), (1990.0, 120),
        (1990.4, 128), (1990.75, 120), (1991.0, 116), (1991.5, 116), (1992.0, 110), (1992.5, 112),
        (1993.0, 105), (1993.5, 96), (1994.0, 93), (1994.5, 96), (1995.0, 98), (1995.5, 89),
        (1995.75, 96), (1996.0, 100), (1996.5, 102), (1997.0, 106), (1997.33, 113), (1997.75, 108),
        (1998.0, 112), (1998.7, 122), (1999.0, 110), (1999.5, 106), (2000.0, 100), (2000.5, 98),
        (2001.0, 100), (2001.5, 100), (2002.0, 98), (2002.5, 100), (2003.0, 99), (2003.5, 98),
        (2004.0, 96), (2004.5, 96), (2005.0, 95), (2005.5, 97), (2006.0, 100), (2006.5, 102),
        (2007.0, 105), (2007.5, 108),
    ]
    xticks = [(float(y), str(y)) for y in range(1985, 2008)]

    def panel(title: str, series: list[tuple[list[tuple[float, float]], str, int, str, float]]) -> PanelSpec:
        return PanelSpec(
            title=title,
            xlim=(1985.0, 2007.6),
            ylim=(0.0, 250.0),
            xticks=xticks,
            yticks=[0, 50, 100, 150, 200, 250],
            xlabel="年",
            lines=[
                LineSeries(*_xy(pts), label=label, color_idx=c, style=s, width=w)
                for pts, label, c, s, w in series
            ],
            legend_loc="top",
        )

    spec = FigureSpec(
        fig_id="1-2",
        title="图 1-2 国内、出口及进口价格变化",
        rows=2,
        height=900,
        panels=[
            panel(
                "国内、出口及进口物价（总平均）",
                [
                    (_IMPORT_TOTAL, "进口", 0, "solid", 2.8),
                    (export, "出口", 5, "solid", 2.4),
                    (domestic, "国内", 1, "dashed", 1.4),
                ],
            ),
            panel(
                "进口物价",
                [
                    (machinery, "机械器具", 0, "solid", 2.8),
                    (textile, "纤维产品", 5, "solid", 2.4),
                    (_IMPORT_TOTAL, "总平均", 1, "dashed", 1.4),
                ],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def fig_1_5(mode: ThemeMode = "mono") -> str:
    pts = [
        (-30.0, 37.2), (-19.2, 29.4), (-23.7, 23.4), (-20.2, 23.1), (-19.0, 22.3), (-18.1, 24.0),
        (-16.2, 23.0), (-15.3, 23.6), (-10.3, 23.0), (-18.6, 19.3), (-15.1, 15.0), (-8.2, 16.7),
        (-7.7, 12.7), (-5.3, 20.2), (-1.8, 21.0), (0.0, 20.2), (0.6, 17.0), (-1.1, 13.7),
        (0.3, 13.4), (-3.0, 10.6), (-4.6, 9.9), (-5.8, 9.0), (-5.8, 8.0), (-6.8, 8.6),
        (-13.6, 1.4), (0.8, 6.1), (1.5, 5.3), (3.2, 7.6), (4.1, 7.9), (4.1, 13.4),
        (5.0, 16.5), (6.0, 17.0), (6.9, 17.4), (6.0, 4.3), (9.2, 9.3), (10.4, 15.5),
        (11.5, 14.4), (10.4, 5.3), (12.5, 4.1), (16.0, 11.2), (15.3, 6.8), (16.2, 7.2),
        (21.4, 10.3), (22.8, 3.4), (23.4, 4.4), (35.9, 5.7),
    ]
    spec = FigureSpec(
        fig_id="1-5",
        title="图 1-5 与国际竞争和产业特化有关的地区性变化",
        panels=[
            PanelSpec(
                xlim=(-40.0, 40.0),
                ylim=(0.0, 40.0),
                xticks=[(-40, "−40"), (-30, "−30"), (-20, "−20"), (-10, "−10"), (0, "0"), (10, "10"), (20, "20"), (30, "30"), (40, "40%")],
                yticks=[0, 5, 10, 15, 20, 25, 30, 35, 40],
                ylabel="%",
                vlines=[(0.0, "", "solid")],
                scatters=[([p[0] for p in pts], [p[1] for p in pts], [], 0, False)],
                legend_loc="none",
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_1_6(mode: ThemeMode = "mono") -> str:
    w1990 = [
        1.44, 1.40, 1.29, 1.25, 1.23, 1.22, 1.19, 1.18, 1.17, 1.17, 1.16, 1.16, 1.15, 1.13, 1.09, 1.08,
        1.07, 1.07, 1.05, 1.03, 1.02, 1.01, 1.00, 0.98, 0.97, 0.96, 0.94, 0.93, 0.92, 0.89, 0.88, 0.88,
        0.88, 0.88, 0.87, 0.86, 0.84, 0.81, 0.79, 0.78, 0.76, 0.75, 0.73, 0.73, 0.73, 0.70, 0.66,
    ]
    w2000 = [
        1.34, 1.31, 1.23, 1.19, 1.16, 1.15, 1.13, 1.13, 1.13, 1.11, 1.11, 1.11, 1.11, 1.10, 1.07, 1.07,
        1.06, 1.06, 1.05, 1.05, 1.05, 1.04, 1.03, 1.00, 1.00, 0.98, 0.97, 0.96, 0.95, 0.94, 0.94, 0.93,
        0.93, 0.91, 0.90, 0.89, 0.88, 0.86, 0.85, 0.85, 0.84, 0.82, 0.82, 0.82, 0.77, 0.76, 0.70,
    ]
    xs = [float(i) for i in range(1, 48)]
    spec = FigureSpec(
        fig_id="1-6",
        title="图 1-6 薪酬水平的地区性变化",
        panels=[
            PanelSpec(
                xlim=(0.0, 48.0),
                ylim=(0.5, 1.5),
                xticks=[(float(i), str(i)) for i in range(1, 48)],
                yticks=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
                xlabel="地区",
                ylabel="相对工资",
                lines=[
                    LineSeries(x=xs, y=w1990, label="W(1990)", color_idx=5, style="solid", marker="circle", width=2.0),
                    LineSeries(x=xs, y=w2000, label="W(2000)", color_idx=0, style="solid", marker="triangle", width=2.0),
                ],
                annotations=[
                    Annotation(x=7.0, y=1.245, text="W(1990)", dx=0.0, dy=0.0, arrow=False, align="start"),
                    Annotation(x=8.5, y=1.01, text="W(2000)", dx=0.0, dy=0.0, arrow=False, align="start"),
                ],
                legend_loc="none",
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_2_1(mode: ThemeMode = "mono") -> str:
    manu = [400, 500, 500, 1500, 2400, 1300, 1600, 1900, 1600, 1400, 1700, 1300, 2700, 2000, 2300, 8600, 7000, 2500, 6400, 4000, 800]
    nonmanu = [100, 500, 600, 500, 600, 1500, 1100, 2300, 2300, 1500, 2100, 2300, 4000, 3300, 7800, 12500, 20800, 15000, 10800, 14500, 36500]
    total = [500, 1000, 1000, 2000, 3200, 2800, 2700, 4300, 3900, 2900, 3900, 3700, 6800, 5300, 10200, 21200, 28000, 17200, 17900, 18600, 37000]
    spec = FigureSpec(
        fig_id="2-1",
        title="图 2-1 日本对内直接投资（制造业和非制造业）",
        panels=[
            PanelSpec(
                xlim=(1983.6, 2004.4),
                ylim=(0.0, 40000.0),
                xticks=[(float(y), str(y)) for y in range(1984, 2005)],
                yticks=[0, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000],
                xlabel="年",
                ylabel="100万美元",
                lines=[
                    LineSeries(*_years(1984, manu), label="制造业", color_idx=5, style="solid", width=2.4),
                    LineSeries(*_years(1984, nonmanu), label="非制造业", color_idx=1, style="dashed", width=2.4),
                    LineSeries(*_years(1984, total), label="全部产业", color_idx=0, style="solid", width=2.8),
                ],
                legend_loc="bottom",
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_2_2(mode: ThemeMode = "mono") -> str:
    out_flow = [36, 60, 60, 145, 200, 340, 440, 480, 310, 170, 135, 180, 225, 235, 260, 240, 225, 315, 380, 320, 290, 310, 455, 505, 735]
    in_flow = [0, -2, 5, -3, 8, -5, -10, 15, 12, 25, -2, 7, 0, 2, 30, 35, 120, 95, 65, 90, 65, 78, 30, -65, 225]
    out_stock = [2590, 2720, 2730, 2490, 2780, 3020, 3060, 3420, 3740, 3880, 4510]
    in_stock = [300, 270, 260, 460, 500, 510, 790, 900, 970, 1020, 1080]
    spec = FigureSpec(
        fig_id="2-2",
        title="图 2-2 日本对外及对内直接投资流量与余额",
        note="资料来源：日本贸易振兴机构投资统计（http://www.jetro.go.jp/jpn/stats/）",
        cols=2,
        height=600,
        panels=[
            PanelSpec(
                title="（A）日本对外及对内直接投资流量",
                xlim=(1982.5, 2007.5),
                ylim=(-100.0, 800.0),
                xticks=[(float(y), str(y)) for y in range(1983, 2008, 2)],
                yticks=[(-100, "−100"), (0, "0"), (100, "100"), (200, "200"), (300, "300"), (400, "400"), (500, "500"), (600, "600"), (700, "700"), (800, "800")],
                xlabel="年",
                ylabel="亿美元",
                lines=[
                    LineSeries(*_years(1983, out_flow), label="对外直接投资流量", color_idx=0, style="solid", width=2.4),
                    LineSeries(*_years(1983, in_flow), label="对内直接投资流量", color_idx=1, style="dashed", width=2.4),
                ],
                legend_loc="bottom",
            ),
            PanelSpec(
                title="（B）日本对外及对内直接投资余额",
                xlim=(1995.5, 2006.5),
                ylim=(0.0, 5000.0),
                xticks=[(float(y), str(y)) for y in range(1996, 2007)],
                yticks=[0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000],
                xlabel="年末",
                ylabel="亿美元",
                lines=[
                    LineSeries(*_years(1996, out_stock), label="对外直接投资余额", color_idx=0, style="solid", width=2.4),
                    LineSeries(*_years(1996, in_stock), label="对内直接投资余额", color_idx=1, style="dashed", width=2.4),
                ],
                legend_loc="bottom",
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def _flow_panel(
    title: str,
    start: int,
    series: list[tuple[list[float | None], str, int, str, float]],
    ylim: tuple[float, float],
    yticks: list[tuple[float, str]],
) -> PanelSpec:
    return PanelSpec(
        title=title,
        xlim=(start - 0.5, 2007.5),
        ylim=ylim,
        xticks=[(float(y), str(y)) for y in range(start, 2008)],
        yticks=yticks,
        xlabel="年",
        ylabel="1000亿日元",
        lines=[
            LineSeries(*_years(start, ys), label=label, color_idx=c, style=s, width=w)
            for ys, label, c, s, w in series
        ],
        legend_loc="bottom",
    )


def fig_2_3(mode: ThemeMode = "mono") -> str:
    pad: list[float | None] = [None] * 11
    a_in: list[float | None] = pad + [28, 28, 31, 63, 35, 41, 58, 82, 84, 66, 77, 89]
    a_out: list[float | None] = pad + [55, 59, 64, 89, 70, 86, 98, 114, 118, 117, 140, 178]
    a_net: list[float | None] = [-15, -24, -29, -46, -63, -73, -45, -22, -16, -19, -22, -27, -32, -32, -27, -37, -47, -40, -35, -35, -52, -62, -88]
    b_in: list[float | None] = pad + [6, 8, 10, 17, 27, 18, 45, 18, 32, 30, 57, 78]
    b_out: list[float | None] = pad + [-1, 3, 5, 5, 18, 11, 32, 12, 23, 27, 57, 50]
    b_net: list[float | None] = [2, 0, 2, 0, -2, 3, 1, 4, 0, -1, -1, -2, 2, 3, 13, 9, 6, 10, 6, 6, 0, -10, 24]
    yticks = [(-100.0, "−100"), (-50.0, "−50"), (0.0, "0"), (50.0, "50"), (100.0, "100"), (150.0, "150"), (200.0, "200")]

    def series(i: list[float | None], o: list[float | None], n: list[float | None]) -> list[tuple[list[float | None], str, int, str, float]]:
        return [(i, "流入", 5, "solid", 2.4), (o, "流出", 1, "dashed", 2.4), (n, "净额", 0, "solid", 2.6)]

    spec = FigureSpec(
        fig_id="2-3",
        title="图 2-3 日本的对外直接投资与对内直接投资",
        note="资料来源：财务省国际收支统计",
        cols=2,
        height=600,
        panels=[
            _flow_panel("（A）日本的对外直接投资", 1985, series(a_in, a_out, a_net), (-100.0, 200.0), yticks),
            _flow_panel("（B）日本的对内直接投资", 1985, series(b_in, b_out, b_net), (-100.0, 200.0), yticks),
        ],
    )
    return render_figure_svg(spec, mode)


def fig_2_4(mode: ThemeMode = "mono") -> str:
    a_in: list[float | None] = [16, 13, 19, 41, 13, 16, 25, 16, 12, 15, 27, 34]
    a_out: list[float | None] = [37, 39, 39, 65, 47, 51, 55, 40, 35, 48, 61, 95]
    a_re: list[float | None] = [2, 6, 4, 1, -2, 9, 10, 5, 7, 15, 19, 23]
    b_in: list[float | None] = [3, 3, 5, 15, 23, 11, 21, 13, 26, 19, 33, 43]
    b_out: list[float | None] = [1, 1, 2, 3, 15, 7, 27, 4, 18, 16, 41, 30]
    b_re: list[float | None] = [0.5, 0.5, 0, -1, 0, 2, 2, 2, 2, 2, 3, 6]
    yticks = [(-20.0, "−20"), (0.0, "0"), (20.0, "20"), (40.0, "40"), (60.0, "60"), (80.0, "80"), (100.0, "100")]

    def series(i: list[float | None], o: list[float | None], r: list[float | None]) -> list[tuple[list[float | None], str, int, str, float]]:
        return [
            (i, "股份资本（流入）", 5, "solid", 2.4),
            (o, "股份资本（流出）", 1, "dashed", 2.4),
            (r, "再投资收益（流入）", 0, "solid", 2.6),
        ]

    spec = FigureSpec(
        fig_id="2-4",
        title="图 2-4 日本对外直接投资与对内直接投资主要项目变化",
        cols=2,
        height=620,
        panels=[
            _flow_panel("（A）对外直接投资的主要项目变化", 1996, series(a_in, a_out, a_re), (-20.0, 100.0), yticks),
            _flow_panel("（B）对内直接投资的主要项目变化", 1996, series(b_in, b_out, b_re), (-20.0, 100.0), yticks),
        ],
    )
    return render_figure_svg(spec, mode)


_OUT_IN = [21, 14, 20, 15, 14, 21, 21, 29, 27, 36, 36, 35, 57, 89, 133, 178, 161, 134, 161, 210, 183, 174]


def fig_2_5(mode: ThemeMode = "mono") -> str:
    in_in = [150, 215, 190, 205, 235, 255, 285, 235, 215, 230, 240, 290, 430, 470, 700, 1050, 1175, 1340, 1345, 1665, 2090, 2105]
    in_out = [80, 180, 155, 285, 385, 460, 305, 185, 120, 195, 210, 230, 220, 215, 250, 370, 290, 265, 215, 320, 400, 425]
    out_out = [9, 9, 10, 10, 8, 10, 14, 16, 20, 32, 34, 55, 35, 50, 70, 30, 22, 13, 8, 10, 17, 15]
    xs = [float(i) for i in range(22)]
    b1 = in_in
    b2 = [a + b for a, b in zip(b1, in_out)]
    b3 = [a + b for a, b in zip(b2, _OUT_IN)]
    spec = FigureSpec(
        fig_id="2-5",
        title="图 2-5 不同市场并购件数的情况",
        panels=[
            PanelSpec(
                xlim=(-0.6, 21.6),
                ylim=(0.0, 3000.0),
                xticks=[(float(i), str(1985 + i)) for i in range(22)],
                yticks=[0, 500, 1000, 1500, 2000, 2500, 3000],
                xlabel="年",
                ylabel="件",
                bars=[
                    BarSeries(x=xs, y=out_out, bottom=b3, label="OUT-OUT", color_idx=5, width=0.62),
                    BarSeries(x=xs, y=_OUT_IN, bottom=b2, label="OUT-IN", color_idx=4, width=0.62),
                    BarSeries(x=xs, y=in_out, bottom=b1, label="IN-OUT", color_idx=0, width=0.62),
                    BarSeries(x=xs, y=in_in, label="IN-IN", color_idx=1, width=0.62),
                ],
                legend_loc="top",
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_2_6(mode: ThemeMode = "mono") -> str:
    ratio = [8.0, 3.3, 4.7, 2.7, 1.9, 2.6, 3.0, 6.1, 6.6, 6.6, 6.3, 5.1, 7.2, 10.4, 11.1, 10.9, 9.7, 7.6, 9.3, 9.4, 6.8, 6.4]
    xs = [float(i) for i in range(22)]
    xticks = [(float(i), str(1985 + i)) for i in range(22)]
    spec = FigureSpec(
        fig_id="2-6",
        title="图 2-6 OUT-IN 并购件数与比率",
        note="资料来源：内阁府《关于最近对日投资企业动向的调查研究》，原数据为 RECOF 株式会社",
        rows=2,
        height=820,
        panels=[
            PanelSpec(
                title="（A）OUT-IN 件数",
                xlim=(-0.6, 21.6),
                ylim=(0.0, 250.0),
                xticks=xticks,
                yticks=[0, 50, 100, 150, 200, 250],
                xlabel="年",
                ylabel="件",
                bars=[BarSeries(x=xs, y=_OUT_IN, color_idx=1, width=0.55)],
                legend_loc="none",
            ),
            PanelSpec(
                title="（B）OUT-IN 比率",
                xlim=(-0.6, 21.6),
                ylim=(0.0, 12.0),
                xticks=xticks,
                yticks=[0, 2, 4, 6, 8, 10, 12],
                xlabel="年",
                ylabel="%",
                lines=[LineSeries(x=xs, y=ratio, color_idx=0, style="solid", width=2.6)],
                legend_loc="none",
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def fig_2_7(mode: ThemeMode = "mono") -> str:
    n: float | None = None
    merger: list[float | None] = [n] * 12 + [0, 0, n, 0, 0, 1, 0.5, 0, n, n]
    acquisition: list[float | None] = [4.5, 5, 6.5, 7.5, 4.5, 6.5, 3.5, 10.5, 12.5, 11, 13.5, 12, 18, 35, 40, 56, 62, 52, 56, 57.5, 43, 54]
    transfer: list[float | None] = [4.5, 1, 1, n, n, n, 1, 2, 0.5, 6, 5, 4, 10, 20, 34, 43, 32, 25, 32, 32, 19, 26]
    capital: list[float | None] = [10, 7, 9, 5.5, 6, 9, 12, 13, 9.5, 12.5, 9.5, 9.5, 17, 19, 43, 64, 48, 43, 44, 74, 77, 62]
    expansion: list[float | None] = [2, 0, n, n, n, n, n, n, n, n, 0, 0.5, 1.5, 2, 0, 2.5, 6.5, 1, 15, 29, 29, 16]
    real = [85, 125, 165, 143, 115, 103, 99, 79, 88]
    invest = [0, 3, 6, 9, 8, 42, 99, 92, 72]
    spec = FigureSpec(
        fig_id="2-7",
        title="图 2-7 OUT-IN 并购的件数及主体",
        rows=2,
        height=860,
        panels=[
            PanelSpec(
                title="（A）OUT-IN 各个形态的件数",
                xlim=(1984.5, 2006.5),
                ylim=(0.0, 90.0),
                xticks=[(float(y), str(y)) for y in range(1985, 2007)],
                yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
                xlabel="年",
                ylabel="件",
                lines=[
                    LineSeries(*_years(1985, merger), label="合并", color_idx=3, style="dashdot", width=2.8),
                    LineSeries(*_years(1985, acquisition), label="收购", color_idx=0, style="solid", width=2.8),
                    LineSeries(*_years(1985, transfer), label="事业转让", color_idx=5, style="solid", width=2.4),
                    LineSeries(*_years(1985, capital), label="资本参与", color_idx=1, style="dashed", width=2.4),
                    LineSeries(*_years(1985, expansion), label="出资扩大", color_idx=2, style="dotted", width=2.4),
                ],
                legend_loc="bottom",
            ),
            PanelSpec(
                title="（B）OUT-IN 实体公司和投资公司",
                xlim=(1997.6, 2006.4),
                ylim=(0.0, 180.0),
                xticks=[(float(y), str(y)) for y in range(1998, 2007)],
                yticks=[0, 20, 40, 60, 80, 100, 120, 140, 160, 180],
                xlabel="年",
                ylabel="家",
                lines=[
                    LineSeries(*_years(1998, real), label="实体公司", color_idx=5, style="solid", width=2.4),
                    LineSeries(*_years(1998, invest), label="投资公司", color_idx=1, style="dashed", width=2.4),
                ],
                legend_loc="bottom",
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def fig_2_8(mode: ThemeMode = "mono") -> str:
    labels = ["1980年度以前", "1980—1985年度", "1986—1990年度", "1991—1995年度", "1996—2000年度", "2001—2005年度"]
    manu = [183, 45, 62, 62, 137, 158]
    nonmanu = [243, 137, 225, 215, 418, 513]
    spec = FigureSpec(
        fig_id="2-8",
        title="图 2-8 2005 年度合计企业设立数量的年度分布",
        note="资料来源：经济产业省《第 40 次外资企业动向调查（2005 年度实绩）》",
        width=1020,
        height=560,
        panels=[
            PanelSpec(
                xlim=(-0.5, 5.5),
                ylim=(0.0, 600.0),
                xticks=[(float(i), lab) for i, lab in enumerate(labels)],
                yticks=[0, 100, 200, 300, 400, 500, 600],
                bars=[
                    BarSeries(x=[i - 0.15 for i in range(6)], y=manu, label="制造业", color_idx=2, width=0.3),
                    BarSeries(x=[i + 0.15 for i in range(6)], y=nonmanu, label="非制造业", color_idx=0, width=0.3),
                ],
                legend_loc="bottom",
            )
        ],
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "1-1": fig_1_1,
        "1-2": fig_1_2,
        "1-5": fig_1_5,
        "1-6": fig_1_6,
        "2-1": fig_2_1,
        "2-2": fig_2_2,
        "2-3": fig_2_3,
        "2-4": fig_2_4,
        "2-5": fig_2_5,
        "2-6": fig_2_6,
        "2-7": fig_2_7,
        "2-8": fig_2_8,
    }
