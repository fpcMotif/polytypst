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


def _years(start: int, end: int) -> list[float]:
    return [float(y) for y in range(start, end + 1)]


def _odd_year_ticks(start: int, end: int, step: int = 2) -> list[tuple[float, str]]:
    return [(float(y), str(y)) for y in range(start, end + 1, step)]


def fig_3_1(mode: ThemeMode = "mono") -> str:
    xs = _years(1977, 2006)
    us = [
        2.0, 2.1, 1.4, 1.65, 3.0, 3.1, 4.3, 7.7, 9.3, 8.55,
        7.55, 6.05, 6.2, 5.5, 5.1, 5.5, 5.55, 5.6, 4.25, 3.55,
        5.0, 6.65, 6.95, 7.55, 7.05, 7.6, 6.6, 6.95, 7.7, 9.0,
    ]
    other = [
        0.55, 1.8, -3.0, -4.2, -1.0, -1.25, 0.6, 0.3, 1.6, 5.2,
        4.05, 3.95, 2.75, 2.1, 5.4, 8.05, 7.85, 6.8, 5.75, 3.2,
        5.0, 7.35, 5.4, 3.2, -0.5, 2.3, 3.65, 5.05, 1.0, -1.1,
    ]
    rate = [
        268.0, 210.0, 219.0, 227.0, 221.0, 249.0, 237.0, 237.0, 238.0, 168.0,
        144.0, 128.0, 138.0, 145.0, 135.0, 127.0, 111.0, 102.0, 94.0, 109.0,
        121.0, 131.0, 114.0, 108.0, 122.0, 125.0, 116.0, 108.0, 110.0, 116.0,
    ]
    panel = PanelSpec(
        xlim=(1976.4, 2006.6),
        ylim=(-6.0, 16.0),
        xticks=_odd_year_ticks(1977, 2005),
        yticks=[-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0],
        y2lim=(0.0, 300.0),
        y2ticks=[0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0],
        xlabel="年",
        ylabel="万亿日元",
        y2label="日元/美元",
        bars=[
            BarSeries(
                x=xs,
                y=other,
                bottom=[u if o > 0 else 0.0 for u, o in zip(us, other)],
                label="贸易支付额（美国以外）",
                color_idx=2,
                width=0.7,
                hatch=True,
            ),
            BarSeries(x=xs, y=us, label="贸易收支额（美国国内）", color_idx=3, width=0.7),
        ],
        lines=[
            LineSeries(x=xs, y=rate, label="汇率（右轴）", color_idx=0, marker="circle", width=2.4, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="3-1",
        title="图 3-1 日本对美贸易收支变化（1977—2006年）",
        panels=[panel],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_3_2(mode: ThemeMode = "mono") -> str:
    xs = _years(1977, 2007)
    japan = [
        0.0, -1.1, -1.0, -0.9, -1.6, -2.2, -3.6, -3.6, -4.4, -5.4,
        -5.5, -4.9, -4.5, -3.6, -3.8, -3.7, -4.8, -5.3, -4.4, -3.3,
        -4.2, -5.5, -6.5, -7.3, -6.1, -6.4, -6.0, -6.7, -7.1, -7.7,
        -7.3,
    ]
    total = [
        -2.6, -2.7, -2.5, -2.0, -1.6, -2.7, -5.7, -10.8, -12.1, -13.7,
        -15.0, -11.5, -9.3, -8.0, -4.0, -4.3, -7.4, -9.8, -10.0, -10.3,
        -11.1, -16.7, -26.4, -37.9, -36.6, -41.5, -50.0, -60.9, -71.5, -75.5,
        -70.0,
    ]
    rate = [
        271.0, 212.0, 221.0, 229.0, 222.0, 252.0, 240.0, 240.0, 240.0, 169.0,
        145.0, 129.0, 138.0, 145.0, 135.0, 127.0, 111.0, 102.0, 94.0, 110.0,
        122.0, 131.0, 114.0, 108.0, 122.0, 125.0, 116.0, 108.0, 110.0, 116.0,
        118.0,
    ]
    panel = PanelSpec(
        xlim=(1976.4, 2007.6),
        ylim=(-80.0, 10.0),
        xticks=_odd_year_ticks(1977, 2007),
        yticks=[-80.0, -70.0, -60.0, -50.0, -40.0, -30.0, -20.0, -10.0, 0.0, 10.0],
        y2lim=(0.0, 300.0),
        y2ticks=[0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0],
        xlabel="年",
        ylabel="百亿美元",
        y2label="日元/美元",
        bars=[
            BarSeries(
                x=xs,
                y=[t - j for t, j in zip(total, japan)],
                bottom=japan,
                label="贸易支付额（日本以外）",
                color_idx=2,
                width=0.7,
                hatch=True,
            ),
            BarSeries(x=xs, y=japan, label="贸易收支额（日本国内）", color_idx=3, width=0.7),
        ],
        lines=[
            LineSeries(x=xs, y=rate, label="汇率（右轴）", color_idx=0, marker="circle", width=2.4, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="3-2",
        title="图 3-2 美国贸易逆差变化（1977—2007年）",
        panels=[panel],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_3_3(mode: ThemeMode = "mono") -> str:
    xs = _years(1980, 2008)
    america = [
        57.4, 59.7, 60.9, 61.8, 48.9, 42.4, 37.6, 37.0, 35.3, 35.3,
        34.2, 33.6, 36.0, 37.4, 37.8, 37.7, 37.8, 38.6, 38.1, 37.1,
        36.6, 32.5, 29.4, 27.4, 26.1, 25.7, 25.0, 24.7, 23.4,
    ]
    japan = [
        13.5, 13.5, 13.5, 13.6, 35.1, 39.1, 43.6, 42.8, 44.0, 43.5,
        42.6, 42.8, 37.8, 36.0, 34.5, 33.5, 32.2, 30.4, 27.9, 28.8,
        29.6, 30.5, 28.5, 29.9, 28.3, 26.7, 26.1, 26.0, 26.4,
    ]
    europe = [
        39.1, 36.6, 35.4, 33.4, 25.6, 28.0, 27.0, 26.4, 25.7, 25.7,
        26.3, 26.0, 26.4, 26.1, 26.1, 26.4, 27.0, 27.8, 30.2, 28.0,
        27.4, 28.2, 26.6, 26.3, 25.1, 24.5, 23.5, 23.5, 23.0,
    ]
    asia = [
        14.9, 14.9, 14.9, 15.5, 15.0, 14.8, 16.4, 18.5, 19.9, 19.9,
        21.6, 22.6, 24.7, 25.9, 26.4, 27.3, 27.9, 28.7, 29.8, 31.1,
        31.6, 33.6, 40.7, 42.0, 45.4, 48.5, 49.9, 51.4, 53.3,
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2008.5),
        ylim=(10.0, 70.0),
        xticks=_odd_year_ticks(1980, 2008),
        yticks=[10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=america, label="美洲", color_idx=5, style="dashed", marker="square"),
            LineSeries(x=xs, y=japan, label="日本", color_idx=2, style="dotted", marker="cross"),
            LineSeries(x=xs, y=europe, label="欧洲", color_idx=4, style="dashdot", marker="triangle"),
            LineSeries(x=xs, y=asia, label="亚洲大洋洲", color_idx=0, style="solid", marker="circle", width=2.6),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="3-3",
        title="图 3-3 全球半导体市场各区域出货额比例的变化（1980—2008年）",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


REER_POINTS: list[tuple[float, float]] = [
    (1975.0, 89.4), (1975.15, 91.2), (1975.54, 88.8), (1975.93, 88.2), (1976.08, 87.1),
    (1976.31, 88.2), (1976.5, 89.4), (1976.7, 92.9), (1976.89, 90.9), (1977.28, 94.1),
    (1977.57, 96.5), (1977.76, 102.4), (1977.95, 100.6), (1978.14, 105.9), (1978.43, 116.5),
    (1978.63, 121.2), (1978.82, 118.2), (1979.11, 110.6), (1979.3, 102.4), (1979.59, 100.0),
    (1979.69, 97.6), (1979.82, 88.8), (1979.98, 90.6), (1980.17, 89.4), (1980.36, 102.4),
    (1980.56, 98.8), (1980.75, 104.7), (1980.98, 107.1), (1981.23, 100.0), (1981.52, 94.7),
    (1981.71, 94.7), (1981.91, 98.2), (1982.1, 90.6), (1982.29, 89.4), (1982.68, 82.9),
    (1982.87, 93.5), (1983.16, 92.9), (1983.45, 91.8), (1983.84, 94.7), (1984.22, 97.1),
    (1984.42, 92.4), (1984.8, 91.8), (1985.09, 89.4), (1985.48, 94.7), (1985.77, 105.9),
    (1986.06, 118.8), (1986.35, 125.9), (1986.58, 133.5), (1986.83, 123.5), (1987.02, 125.9),
    (1987.31, 133.0), (1987.5, 124.7), (1987.7, 130.6), (1987.98, 140.0), (1988.27, 139.4),
    (1988.56, 131.2), (1988.85, 137.6), (1989.24, 129.4), (1989.43, 120.0), (1989.72, 120.0),
    (1990.01, 115.3), (1990.24, 107.1), (1990.49, 111.8), (1990.78, 122.4), (1991.17, 119.4),
    (1991.55, 121.2), (1991.94, 127.6), (1992.17, 120.0), (1992.52, 127.1), (1992.9, 127.6),
    (1993.29, 140.0), (1993.58, 150.0), (1993.87, 140.6), (1994.16, 148.2), (1994.45, 151.2),
    (1994.84, 145.3), (1995.03, 145.9), (1995.26, 165.3), (1995.41, 160.0), (1995.64, 138.8),
    (1995.99, 129.4), (1996.57, 121.2), (1997.05, 111.8), (1997.44, 122.9), (1997.73, 118.8),
    (1998.02, 125.9), (1998.5, 110.6), (1998.79, 125.9), (1998.99, 135.3), (1999.27, 127.1),
    (1999.56, 138.8), (1999.85, 147.6), (2000.04, 139.4), (2000.43, 141.2), (2000.82, 140.0),
    (2001.01, 128.2), (2001.2, 122.9), (2001.59, 126.5), (2001.98, 115.3), (2002.17, 115.3),
    (2002.46, 122.9), (2002.75, 117.6), (2003.33, 115.9), (2003.72, 121.2), (2004.01, 118.8),
    (2004.3, 114.1), (2004.98, 120.0), (2005.46, 110.6), (2005.75, 103.5), (2006.23, 101.2),
    (2006.62, 98.8), (2007.1, 91.8), (2007.3, 90.6), (2007.59, 95.9), (2008.07, 102.4),
    (2008.45, 95.9), (2008.59, 96.5), (2008.78, 121.2), (2008.94, 128.2), (2009.1, 128.2),
]


def fig_3_4(mode: ThemeMode = "mono") -> str:
    panel = PanelSpec(
        xlim=(1975.0, 2009.1),
        ylim=(60.0, 180.0),
        xticks=_odd_year_ticks(1975, 2009),
        yticks=[60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0],
        xlabel="年",
        ylabel="1973年3月＝100（指数）",
        zero_line=False,
        lines=[
            LineSeries(
                x=[p[0] for p in REER_POINTS],
                y=[p[1] for p in REER_POINTS],
                color_idx=0,
                width=1.4,
            ),
        ],
        annotations=[
            Annotation(x=1979.6, y=146.0, text="↑ 日元升值", dx=0.0, dy=0.0, arrow=False, align="start"),
            Annotation(x=1979.6, y=129.0, text="↓ 日元贬值", dx=0.0, dy=0.0, arrow=False, align="start"),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="3-4",
        title="图 3-4 实际有效汇率变化（1975年1月—2009年2月）",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def fig_3_5(mode: ThemeMode = "mono") -> str:
    xs = _years(1983, 2007)
    ys = [
        28.2, 30.3, 31.5, 44.1, 45.6, 49.7, 50.3, 49.8, 51.8, 50.1,
        53.0, 55.8, 59.9, 58.9, 60.2, 62.7, 61.4, 61.6, 61.6, 61.1,
        62.3, 60.9, 57.5, 57.3, 54.8,
    ]
    above = [
        True, False, False, True, False, True, True, False, True, False,
        True, False, True, False, True, True, False, True, True, False,
        True, True, False, True, False,
    ]
    shifted = {1: "end", 2: "start", 5: "end", 6: "start", 14: "end", 15: "start"}
    aligns = [shifted.get(i, "middle") for i in range(len(xs))]
    panel = PanelSpec(
        xlim=(1982.5, 2007.6),
        ylim=(0.0, 70.0),
        xticks=_odd_year_ticks(1983, 2007),
        yticks=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[LineSeries(x=xs, y=ys, color_idx=2, marker="circle", width=2.2)],
        annotations=[
            Annotation(
                x=x,
                y=y,
                text=f"{y:.1f}",
                dx={"start": 6.0, "middle": 0.0, "end": -6.0}[al],
                dy=-9.0 if up else 9.0,
                arrow=False,
                fontsize=10.5,
                align=al,
            )
            for x, y, up, al in zip(xs, ys, above, aligns)
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="3-5",
        title="图 3-5 产品进口比例变化（1983—2007年）",
        panels=[panel],
        width=860,
        height=500,
    )
    return render_figure_svg(spec, mode)


def fig_3_6(mode: ThemeMode = "mono") -> str:
    xs = _years(1981, 2007)
    export = [
        2.15, -0.6, 3.78, 4.93, 1.93, 0.33, -2.2, 2.15, 4.15, 2.2,
        2.97, 1.93, -2.86, -4.55, -2.24, 0.91, 0.0, -3.96, -2.48, -2.4,
        -0.94, -4.35, -1.73, -2.26, 0.99, 2.04, 2.04,
    ]
    domestic = [
        0.63, 1.18, 1.4, 0.0, 0.5, 0.85, 1.32, 1.65, 1.65, 1.87,
        1.76, 0.94, 0.6, 0.55, 0.31, 0.33, 1.1, -0.36, -0.66, -0.05,
        -0.46, -1.07, -0.2, 0.44, 0.31, 0.11, 0.22,
    ]
    manuf = [
        1.34, -0.47, 1.9, 2.31, 0.99, -0.6, -1.13, 1.93, 2.13, 1.49,
        2.97, 1.32, -2.53, -2.26, -2.72, -0.83, -0.3, -4.19, -2.73, -1.9,
        -2.86, -4.85, -3.67, -2.46, -0.77, 1.67, 0.25,
    ]
    nonmanuf = [
        1.67, 2.04, 2.39, 0.55, 0.69, 2.07, 2.15, 2.37, 2.67, 2.72,
        2.37, 1.46, 1.8, 0.91, 1.19, 1.24, 1.67, 0.36, -0.22, 0.36,
        0.28, -0.47, 0.46, 0.64, 0.72, 0.61, 0.28,
    ]
    panel = PanelSpec(
        xlim=(1980.5, 2007.5),
        ylim=(-6.0, 6.0),
        xticks=_odd_year_ticks(1981, 2007),
        yticks=[(-6.0, "-6.0"), (-4.0, "-4.0"), (-2.0, "-2.0"), (0.0, "0.0"), (2.0, "2.0"), (4.0, "4.0"), (6.0, "6.0")],
        xlabel="年",
        ylabel="%",
        lines=[
            LineSeries(x=xs, y=export, label="出口相关行业", color_idx=5, style="dashed", marker="cross"),
            LineSeries(x=xs, y=domestic, label="内需相关行业", color_idx=2, style="dotted", marker="square", width=1.8),
            LineSeries(x=xs, y=manuf, label="制造业", color_idx=1, style="dashdot", marker="circle", width=1.8),
            LineSeries(x=xs, y=nonmanuf, label="非制造业（包括建筑）", color_idx=0, style="solid", marker="circle", width=2.4),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="3-6",
        title="图 3-6 内需相关行业、出口相关行业、制造业与非制造业",
        panels=[panel],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_3_7(mode: ThemeMode = "mono") -> str:
    xs = _years(1980, 2006)
    eu = [
        6.2, 6.7, 6.9, 7.2, 7.8, 7.8, 8.3, 8.9, 10.1, 11.6,
        13.9, 13.4, 12.7, 10.4, 10.4, 11.3, 12.4, 13.6, 14.6, 13.6,
        13.8, 13.6, 13.5, 14.5, 15.7, 16.0, 17.6,
    ]
    asia = [
        11.85, 12.1, 12.7, 12.4, 13.9, 14.3, 10.0, 10.4, 11.7, 13.9,
        15.9, 16.8, 16.8, 17.2, 19.2, 21.9, 25.5, 27.1, 22.4, 23.5,
        28.7, 29.3, 31.8, 35.5, 40.6, 45.2, 51.7,
    ]
    usa = [
        12.7, 14.1, 15.1, 16.1, 20.6, 21.9, 18.5, 16.8, 17.2, 19.6,
        20.7, 19.7, 18.7, 18.1, 18.7, 18.7, 21.0, 23.5, 24.5, 22.6,
        23.5, 22.6, 22.4, 20.6, 20.9, 22.2, 25.2,
    ]
    total = [
        61.0, 64.5, 66.5, 63.5, 71.9, 71.9, 56.1, 54.2, 56.9, 65.7,
        75.2, 73.6, 72.4, 66.8, 67.9, 72.4, 81.8, 92.1, 87.7, 82.6,
        92.1, 91.0, 94.9, 98.7, 111.1, 122.6, 142.7,
    ]
    off = 0.27
    panel = PanelSpec(
        xlim=(1979.5, 2006.5),
        ylim=(0.0, 60.0),
        xticks=[(float(y), str(y)) for y in range(1980, 2007, 2)],
        yticks=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        y2lim=(0.0, 160.0),
        y2ticks=[0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0],
        xlabel="年",
        ylabel="万亿日元",
        y2label="万亿日元",
        bars=[
            BarSeries(x=[x - off for x in xs], y=eu, label="EU（左轴）", color_idx=4, width=0.27, hatch=True),
            BarSeries(x=xs, y=asia, label="ASEAN（6国）+中国与韩国（左轴）", color_idx=0, width=0.27),
            BarSeries(x=[x + off for x in xs], y=usa, label="美国（左轴）", color_idx=1, width=0.27),
        ],
        lines=[
            LineSeries(x=xs, y=total, label="日本的贸易总额（右轴）", color_idx=0, width=2.8, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="3-7",
        title="图 3-7 日本各区域贸易总额变化（1980—2006年）",
        panels=[panel],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_3_8(mode: ThemeMode = "mono") -> str:
    xs = _years(1985, 2007)
    trade = [
        12.8, 15.1, 13.1, 11.9, 11.1, 10.0, 13.0, 15.9, 15.6, 14.8,
        12.4, 8.8, 12.1, 16.1, 13.7, 13.6, 8.4, 11.6, 12.0, 14.0,
        10.3, 9.4, 12.4,
    ]
    top = [
        14.6, 16.7, 15.6, 14.5, 14.2, 13.2, 16.5, 20.4, 20.1, 18.95,
        16.6, 14.7, 19.3, 23.0, 20.5, 18.9, 16.8, 19.9, 20.4, 23.2,
        21.6, 23.3, 28.8,
    ]
    services = [
        -2.4, -2.36, -3.14, -4.0, -5.0, -6.1, -5.6, -5.5, -4.8, -5.0,
        -5.4, -6.55, -6.3, -6.25, -5.95, -4.9, -5.2, -4.9, -3.6, -3.6,
        -2.8, -2.15, -2.6,
    ]
    bottom = [
        -2.6, -2.58, -3.45, -4.4, -5.45, -6.85, -7.25, -6.0, -5.4, -5.4,
        -6.1, -7.55, -7.3, -7.35, -7.25, -6.0, -6.1, -5.5, -4.4, -4.45,
        -3.5, -3.45, -3.8,
    ]
    current = [
        12.0, 14.3, 12.1, 10.3, 8.7, 6.8, 9.3, 14.4, 14.9, 13.6,
        10.7, 7.5, 11.7, 15.6, 13.1, 13.1, 10.7, 14.2, 15.7, 18.7,
        18.3, 19.9, 25.0,
    ]
    panel = PanelSpec(
        xlim=(1984.4, 2007.6),
        ylim=(-10.0, 35.0),
        xticks=_odd_year_ticks(1985, 2007),
        yticks=[-10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0],
        xlabel="年",
        ylabel="万亿日元",
        bars=[
            BarSeries(x=xs, y=[t - d for t, d in zip(top, trade)], bottom=trade, label="所得收支", color_idx=4, width=0.7, hatch=True),
            BarSeries(x=xs, y=trade, label="贸易收支", color_idx=1, width=0.7),
            BarSeries(x=xs, y=services, label="服务收支", color_idx=3, width=0.7),
            BarSeries(x=xs, y=[b - s for b, s in zip(bottom, services)], bottom=services, label="经常移转收支", color_idx=0, width=0.7),
        ],
        lines=[
            LineSeries(x=xs, y=current, label="经常收支", color_idx=0, marker="square", width=2.4),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="3-8",
        title="图 3-8 日本经常收支及其明细变化（1985—2007年）",
        panels=[panel],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_4_1(mode: ThemeMode = "mono") -> str:
    xs = _years(1980, 2002)
    nrp = [
        65.8, 64.0, 58.6, 76.5, 88.2, 95.2, 139.7, 136.1, 135.2, 114.9,
        102.6, 112.4, 121.2, 142.7, 171.6, 167.9, 132.9, 114.6, 113.6, 147.4,
        161.2, 124.9, 135.2,
    ]
    rate = [
        226.4, 219.9, 249.8, 239.3, 238.4, 239.0, 167.5, 144.2, 127.7, 137.6,
        144.5, 134.6, 125.6, 110.7, 101.7, 93.3, 108.6, 120.6, 130.7, 114.3,
        108.6, 121.7, 125.0,
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2002.5),
        ylim=(0.0, 180.0),
        xticks=[(float(y), str(y)) for y in range(1980, 2003)],
        yticks=[0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0],
        y2lim=(0.0, 300.0),
        y2ticks=[0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0],
        xlabel="年",
        ylabel="农业保护率（NRP）（%）",
        y2label="汇率（日元/美元）",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=nrp, label="农业保护率、NRP", color_idx=1, style="dashed", marker="circle", width=2.0),
            LineSeries(x=xs, y=rate, label="汇率", color_idx=0, style="solid", marker="square", width=2.4, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="4-1",
        title="图 4-1 泡沫、通缩期农业保护率和汇率的变化",
        panels=[panel],
        note="资料来源：Honma and Hayami（2009）",
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_4_2(mode: ThemeMode = "mono") -> str:
    xs = _years(1975, 2002)
    income_all = [
        3.92, 3.79, 3.73, 3.83, 4.35, 4.41, 4.52, 5.18, 4.82, 5.24,
        5.24, 5.28, 5.95, 7.27, 8.50, 8.86, 10.08, 12.12, 8.69, 8.06,
        7.50, 7.50, 6.43, 5.41, 5.20, 5.20, 4.63, 4.11,
    ]
    area_all = [
        2.425, 2.257, 2.159, 2.243, 2.336, 2.206, 2.131, 2.028, 1.907, 1.949,
        1.935, 1.813, 1.977, 2.061, 2.327, 2.425, 2.472, 2.444, 2.187, 2.037,
        2.084, 2.075, 1.921, 1.720, 1.710, 1.645, 1.509, 1.360,
    ]
    income_rural = [
        2.47, 2.03, 1.81, 1.94, 2.08, 2.13, 2.10, 2.34, 2.16, 2.30,
        2.35, 2.28, 2.48, 2.74, 3.17, 3.52, 3.87, 3.74, 3.26, 3.20,
        3.26, 3.41, 3.06, 2.64, 2.62, 2.61, 2.37, 2.15,
    ]
    area_rural = [
        1.825, 1.717, 1.605, 1.710, 1.766, 1.674, 1.621, 1.540, 1.453, 1.460,
        1.448, 1.345, 1.467, 1.549, 1.779, 1.878, 1.901, 1.832, 1.662, 1.593,
        1.618, 1.621, 1.494, 1.349, 1.368, 1.292, 1.177, 1.062,
    ]
    xticks = [(float(y), str(y)) for y in range(1970, 2006, 5)]
    top = PanelSpec(
        xlim=(1970.0, 2005.0),
        ylim=(0.0, 14.0),
        xticks=xticks,
        yticks=[(v, f"{v:.1f}") for v in (0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0)],
        y2lim=(0.075, 3.55),
        y2ticks=[(1.0, "1.0"), (2.0, "2.0"), (3.0, "3.0")],
        xlabel="年",
        ylabel="万亿日元，1990年价格",
        y2label="万公顷",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=income_all, label="转用收入（左轴）", color_idx=0, style="solid", marker="square", width=2.4),
            LineSeries(x=xs, y=area_all, label="转用面积（右轴）", color_idx=1, style="dashed", marker="circle", width=2.0, axis="y2"),
        ],
        annotations=[
            Annotation(x=2004.4, y=12.6, text="全部都道府县", dx=0.0, dy=0.0, arrow=False, align="end"),
        ],
        legend_loc="bottom",
    )
    bottom = PanelSpec(
        xlim=(1970.0, 2005.0),
        ylim=(0.5, 4.0),
        xticks=xticks,
        yticks=[(v, f"{v:.1f}") for v in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)],
        y2lim=(0.3, 2.016),
        y2ticks=[(1.0, "1.0"), (2.0, "2.0")],
        xlabel="年",
        ylabel="万亿日元，1990年价格",
        y2label="万公顷",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=income_rural, label="转用收入（左轴）", color_idx=0, style="solid", marker="square", width=2.4),
            LineSeries(x=xs, y=area_rural, label="转用面积（右轴）", color_idx=1, style="dashed", marker="circle", width=2.0, axis="y2"),
        ],
        annotations=[
            Annotation(x=2004.4, y=0.75, text="3大都市圈以外的都道府县", dx=0.0, dy=0.0, arrow=False, align="end"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="4-2",
        title="图 4-2 农业用地的转用面积和转用收入",
        panels=[top, bottom],
        rows=2,
        cols=1,
        note="资料来源：神门善久（2005），p. 86",
        width=860,
        height=900,
    )
    return render_figure_svg(spec, mode)


def fig_4_3(mode: ThemeMode = "mono") -> str:
    xs = _years(1960, 2006)
    calorie = [
        78.7, 77.8, 75.7, 71.9, 71.9, 72.6, 67.9, 65.7, 64.6, 61.9,
        59.7, 57.6, 56.7, 54.7, 54.7, 53.6, 52.8, 52.8, 53.6, 53.7,
        52.8, 51.7, 52.7, 51.8, 52.5, 52.6, 50.7, 49.7, 49.7, 48.7,
        47.7, 45.7, 45.5, 36.4, 45.4, 42.7, 41.6, 40.5, 39.7, 39.7,
        39.5, 39.6, 39.6, 39.6, 39.6, 39.6, 38.4,
    ]
    grain = [
        81.9, 74.7, 72.5, 62.7, 62.7, 61.4, 57.6, 55.6, 53.6, 48.6,
        45.6, 45.6, 42.1, 39.9, 39.4, 39.5, 36.4, 34.6, 33.4, 32.6,
        32.6, 32.6, 32.7, 31.4, 30.8, 30.8, 30.8, 29.5, 29.5, 29.5,
        29.6, 28.4, 28.5, 21.8, 32.7, 29.5, 28.4, 27.5, 26.5, 26.5,
        27.4, 27.5, 27.5, 26.8, 27.6, 27.6, 26.4,
    ]
    staple = [
        88.8, 83.2, 83.8, 76.3, 78.8, 80.2, 79.7, 79.1, 78.9, 75.9,
        74.0, 72.8, 70.8, 69.9, 68.8, 68.8, 68.2, 66.9, 68.2, 68.9,
        68.9, 69.0, 69.0, 68.8, 68.9, 68.9, 68.9, 67.9, 67.9, 67.9,
        66.8, 65.0, 65.5, 50.0, 73.8, 64.7, 62.9, 61.8, 59.0, 59.0,
        59.9, 59.9, 60.9, 60.0, 60.0, 60.9, 59.9,
    ]
    panel = PanelSpec(
        xlim=(1959.5, 2006.5),
        ylim=(0.0, 100.0),
        xticks=[(float(y), str(y)) for y in range(1960, 2006, 3)],
        yticks=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=calorie, label="供给热量综合自给率", color_idx=0, style="dotted", marker="circle", width=1.8),
            LineSeries(x=xs, y=grain, label="谷物自给率", color_idx=3, style="solid", marker="square", width=1.8),
            LineSeries(x=xs, y=staple, label="主食用谷物自给率", color_idx=1, style="dashed", marker="triangle", width=2.0),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="4-3",
        title="图 4-3 日本食品自给率变化",
        panels=[panel],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_5_1(mode: ThemeMode = "mono") -> str:
    xs = [float(i) for i in range(35)]
    export_left = [
        39.28, 36.52, 33.38, 34.33, 34.71, 37.58, 39.53, 40.17, 42.93, 40.06,
        40.76, 39.81, 37.73, 36.09, 35.94, 35.31, 35.88, 35.94, 36.09,
    ]
    export_right = [
        36.24, 34.29, 35.73, 35.03, 36.88, 38.64, 39.49, 40.28, 40.28, 39.49,
        38.58, 38.64,
    ]
    import_left = [
        6.75, 9.17, 10.05, 12.8, 13.66, 14.0, 15.2, 16.7, 17.9, 20.67,
        21.45, 19.0, 24.17, 22.53, 20.38, 20.38, 18.71, 22.53, 21.67,
    ]
    import_right = [
        23.41, 23.15, 23.6, 24.17, 25.56, 24.57, 25.24, 25.24, 23.76, 24.03,
        22.12, 21.13,
    ]
    gap: list[float | None] = [None] * 4
    labels = [
        "1985/3", "1987/3", "1989/3", "1991/3", "1993/3", "1994/3", "1995/3", "1996/3", "1997/3",
        "1998/3", "1999/3", "2000/3", "2001/3", "2002/3", "2003/3", "2004/3", "2005/3", "2006/3",
    ]
    panel = PanelSpec(
        xlim=(-0.6, 34.6),
        ylim=(30.0, 50.0),
        xticks=[(float(2 * i), lab) for i, lab in enumerate(labels)],
        yticks=[(30.0, "30.0"), (35.0, "35.0"), (40.0, "40.0"), (45.0, "45.0"), (50.0, "50.0")],
        y2lim=(5.0, 30.0),
        y2ticks=[(v, f"{v:.1f}") for v in (5.0, 10.0, 15.0, 20.0, 25.0, 30.0)],
        ylabel="%",
        y2label="%",
        zero_line=False,
        lines=[
            LineSeries(
                x=xs,
                y=[*import_left, *gap, *import_right],
                label="进口（右轴）",
                color_idx=1,
                style="dashed",
                marker="circle",
                width=2.0,
                axis="y2",
            ),
            LineSeries(
                x=xs,
                y=[*export_left, *gap, *export_right],
                label="出口（左轴）",
                color_idx=0,
                style="solid",
                marker="square",
                width=2.4,
            ),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="5-1",
        title="图 5-1 日本进出口结算货币中日元结算比例",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def _share_curve(y50: float, root: float, power: float) -> tuple[list[float], list[float]]:
    xs = [50.0 + 0.5 * i for i in range(int((root - 50.0) / 0.5) + 1)] + [root]
    ys = [y50 * ((root - x) / (root - 50.0)) ** power for x in xs]
    return xs, ys


def fig_5_2(mode: ThemeMode = "mono") -> str:
    curves_a = [(16.0, 96.5, 0.75), (13.8, 96.2, 0.72), (11.8, 96.0, 0.69)]
    curves_b = [(32.0, 92.5, 0.82), (24.3, 91.0, 0.78), (19.0, 88.8, 0.74)]

    def lines_for(curves: list[tuple[float, float, float]], power: float) -> list[LineSeries]:
        out: list[LineSeries] = []
        for y50, root, _gamma in curves:
            xs, ys = _share_curve(y50, root, power)
            out.append(LineSeries(x=xs, y=ys, color_idx=0, width=1.8))
        return out

    xticks = [(v, str(round(v))) for v in (50.0, 60.0, 70.0, 80.0, 90.0, 100.0)]
    panel_a = PanelSpec(
        title="（A）通货膨胀率（PPI）和美元的占有率",
        xlim=(50.0, 100.0),
        ylim=(0.0, 20.0),
        xticks=xticks,
        yticks=[0.0, 5.0, 10.0, 15.0, 20.0],
        xlabel="美元的占有率（%）",
        ylabel="通货膨胀率（%）",
        zero_line=False,
        lines=lines_for(curves_a, 1.2),
        annotations=[
            Annotation(x=51.5, y=16.4, text="γ =0.75", dx=0.0, dy=0.0, arrow=False, align="start"),
            Annotation(x=51.5, y=13.6, text="γ =0.72", dx=0.0, dy=0.0, arrow=False, align="start"),
            Annotation(x=52.5, y=5.8, text="γ =0.69", dx=0.0, dy=0.0, arrow=False, align="start"),
        ],
        legend_loc="none",
    )
    panel_b = PanelSpec(
        title="（B）通货膨胀率（CPI）和美元的占有率",
        xlim=(50.0, 100.0),
        ylim=(0.0, 32.0),
        xticks=xticks,
        yticks=[0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0],
        xlabel="美元的占有率（%）",
        ylabel="通货膨胀率（%）",
        zero_line=False,
        lines=lines_for(curves_b, 1.5),
        annotations=[
            Annotation(x=52.0, y=29.0, text="γ =0.82", dx=0.0, dy=0.0, arrow=False, align="start"),
            Annotation(x=51.3, y=23.5, text="γ =0.78", dx=0.0, dy=0.0, arrow=False, align="start"),
            Annotation(x=51.3, y=18.3, text="γ =0.74", dx=0.0, dy=0.0, arrow=False, align="start"),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="5-2",
        title="图 5-2 PPI、CPI和美元占有率",
        panels=[panel_a, panel_b],
        rows=1,
        cols=2,
        width=860,
        height=480,
    )
    return render_figure_svg(spec, mode)


RATE_POINTS: list[tuple[float, float]] = [
    (1991.0, 136.3), (1991.11, 126.7), (1991.21, 137.2), (1991.41, 140.5), (1991.62, 135.9),
    (1991.83, 129.6), (1992.04, 122.5), (1992.2, 133.0), (1992.31, 133.4), (1992.45, 127.1),
    (1992.61, 126.3), (1992.76, 118.3), (1993.07, 124.6), (1993.15, 117.9), (1993.35, 109.5),
    (1993.65, 100.3), (1993.81, 107.0), (1994.02, 111.6), (1994.18, 102.8), (1994.55, 97.0),
    (1994.89, 96.2), (1995.05, 99.9), (1995.22, 95.3), (1995.35, 79.8), (1995.42, 86.1),
    (1995.59, 86.1), (1995.72, 98.7), (1995.96, 102.0), (1996.13, 106.2), (1996.37, 107.9),
    (1996.63, 110.4), (1996.87, 113.7), (1997.12, 122.1), (1997.33, 126.3), (1997.45, 111.2),
    (1997.7, 118.7), (1997.87, 122.1), (1997.98, 130.5), (1998.15, 123.0), (1998.31, 131.3),
    (1998.48, 141.3), (1998.65, 146.4), (1998.77, 131.3), (1998.86, 114.6), (1998.94, 122.1),
    (1999.11, 108.7), (1999.23, 121.3), (1999.56, 121.3), (1999.77, 103.7), (1999.98, 101.2),
    (2000.19, 110.4), (2000.36, 102.8), (2000.68, 108.7), (2000.96, 108.7), (2001.34, 125.9),
    (2001.59, 124.6), (2001.84, 116.2), (2002.08, 133.0), (2002.29, 133.0), (2002.5, 126.3),
    (2002.66, 116.2), (2002.88, 124.6), (2003.08, 117.9), (2003.49, 117.1), (2003.74, 119.6),
    (2003.91, 109.5), (2004.24, 105.4), (2004.32, 111.2), (2004.4, 103.7), (2004.51, 113.7),
    (2004.67, 108.7),
]

INTERVENTIONS: list[tuple[float, float]] = [
    (1993.31, 1300.0), (1993.4, 1000.0), (1993.65, 1200.0), (1994.18, 800.0), (1994.5, 1300.0),
    (1994.85, 1100.0), (1995.26, 3500.0), (1995.29, 1500.0), (1995.62, 7000.0), (1995.72, 8900.0),
    (1995.76, 6300.0), (1996.18, 7800.0), (1998.03, -6800.0), (1998.34, -26000.0), (1998.51, -2200.0),
    (1999.09, 7000.0), (1999.52, 14500.0), (1999.55, 9600.0), (1999.57, 8300.0), (1999.61, 4300.0),
    (1999.75, 7000.0), (1999.97, 7600.0), (2000.06, 4000.0), (2000.08, 6000.0), (2000.26, 9000.0),
    (2000.31, 14500.0), (2001.8, 5500.0), (2001.82, 13500.0), (2002.49, 6000.0), (2002.51, 11000.0),
    (2002.58, 6000.0), (2003.18, 2500.0), (2003.26, 4000.0), (2003.46, 7500.0), (2003.48, 11000.0),
    (2003.52, 2000.0), (2003.58, 2000.0), (2003.63, 6500.0), (2003.79, 10500.0), (2003.85, 11000.0),
    (2003.92, 2500.0), (2003.98, 10000.0), (2004.04, 13500.0), (2004.07, 3000.0), (2004.14, 17500.0),
    (2004.17, 9500.0), (2004.29, 13000.0), (2004.31, 8000.0),
]


def fig_5_3(mode: ThemeMode = "mono") -> str:
    tick_dates = [
        (1991.0, "1991/1/1"), (1992.27, "1992/4/9"), (1993.55, "1993/7/19"), (1994.82, "1994/10/26"),
        (1996.09, "1996/2/2"), (1997.36, "1997/5/13"), (1998.64, "1998/8/20"), (1999.91, "1999/11/29"),
        (2001.18, "2001/3/7"), (2002.45, "2002/6/14"), (2003.73, "2003/9/23"),
    ]
    panel = PanelSpec(
        xlim=(1991.0, 2004.67),
        ylim=(-30000.0, 20000.0),
        xticks=tick_dates,
        yticks=[-30000.0, -25000.0, -20000.0, -15000.0, -10000.0, -5000.0, 0.0, 5000.0, 10000.0, 15000.0, 20000.0],
        y2lim=(80.0, 160.0),
        y2ticks=[80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0],
        ylabel="亿日元",
        y2label="汇率（日元/美元）",
        bars=[
            BarSeries(
                x=[p[0] for p in INTERVENTIONS],
                y=[p[1] for p in INTERVENTIONS],
                label="干预金额",
                color_idx=2,
                width=0.012,
                opacity=1.0,
            ),
        ],
        lines=[
            LineSeries(
                x=[p[0] for p in RATE_POINTS],
                y=[p[1] for p in RATE_POINTS],
                label="日元/美元",
                color_idx=0,
                width=1.4,
                axis="y2",
            ),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="5-3",
        title="图 5-3 日本外汇市场干预和汇率（1991—2004年）",
        panels=[panel],
        note="资料来源：根据日本财务省《外汇平衡操作的实施状况》和 Datastream 制作",
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


RESERVE_POINTS: list[tuple[float, float]] = [
    (1980.0, 140.0), (1980.24, 90.0), (1980.56, 140.0), (1980.88, 160.0), (1981.44, 200.0),
    (1982.31, 200.0), (1982.63, 120.0), (1982.95, 170.0), (1984.39, 200.0), (1985.19, 220.0),
    (1985.82, 250.0), (1986.62, 360.0), (1986.94, 470.0), (1987.26, 630.0), (1987.66, 630.0),
    (1988.06, 800.0), (1988.54, 850.0), (1988.94, 980.0), (1989.33, 960.0), (1989.81, 800.0),
    (1990.13, 710.0), (1990.61, 720.0), (1990.93, 690.0), (1991.41, 660.0), (1992.21, 690.0),
    (1993.0, 690.0), (1993.48, 960.0), (1993.8, 990.0), (1994.12, 1010.0), (1994.6, 1230.0),
    (1995.08, 1290.0), (1995.32, 1560.0), (1995.64, 1830.0), (1995.96, 1880.0), (1996.2, 2050.0),
    (1996.83, 2160.0), (1997.63, 2210.0), (1998.19, 2270.0), (1998.43, 2070.0), (1998.75, 2100.0),
    (1999.31, 2210.0), (1999.47, 2480.0), (1999.71, 2760.0), (2000.03, 2920.0), (2000.34, 3360.0),
    (2000.98, 3520.0), (2001.62, 3900.0), (2001.94, 3950.0), (2002.34, 4010.0), (2002.58, 4440.0),
    (2003.06, 4770.0), (2003.3, 5100.0), (2003.38, 5420.0), (2003.62, 5530.0), (2003.86, 6300.0),
    (2004.01, 7060.0), (2004.17, 8260.0), (2004.49, 8260.0), (2005.13, 8470.0), (2005.61, 8420.0),
    (2006.25, 8580.0), (2006.89, 8970.0), (2007.21, 9070.0), (2007.53, 9180.0), (2007.84, 9670.0),
    (2008.16, 10050.0), (2008.4, 9890.0),
]


def fig_5_4(mode: ThemeMode = "mono") -> str:
    panel = PanelSpec(
        xlim=(1980.0, 2008.45),
        ylim=(0.0, 10000.0),
        xticks=[(float(y), f"{y}M1") for y in range(1980, 2008, 3)],
        yticks=[float(v) for v in range(0, 10001, 1000)],
        ylabel="亿美元",
        zero_line=False,
        lines=[
            LineSeries(
                x=[p[0] for p in RESERVE_POINTS],
                y=[p[1] for p in RESERVE_POINTS],
                color_idx=0,
                width=1.6,
                area_fill=True,
            ),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="5-4",
        title="图 5-4 外汇储备（total reserve minus gold）的积累",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "3-1": fig_3_1,
        "3-2": fig_3_2,
        "3-3": fig_3_3,
        "3-4": fig_3_4,
        "3-5": fig_3_5,
        "3-6": fig_3_6,
        "3-7": fig_3_7,
        "3-8": fig_3_8,
        "4-1": fig_4_1,
        "4-2": fig_4_2,
        "4-3": fig_4_3,
        "5-1": fig_5_1,
        "5-2": fig_5_2,
        "5-3": fig_5_3,
        "5-4": fig_5_4,
    }
