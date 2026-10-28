from __future__ import annotations

from collections.abc import Callable

from scripts.book2_figures.engine import (
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    render_figure_svg,
)


def _years(start: int, end: int) -> list[float]:
    return [float(y) for y in range(start, end + 1)]


def _year_ticks(last: int, last_label: str) -> list[tuple[float, str]]:
    last_x = last + 0.5 if last_label == "年" else float(last)
    return [(float(y), str(y)) for y in range(1980, 2006, 5)] + [(last_x, last_label)]


def fig_7_1(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2008)
    usd = [
        228.0, 221.0, 248.0, 238.0, 238.0, 238.0, 169.0, 145.0, 129.0, 139.0,
        145.0, 135.0, 128.0, 112.0, 102.0, 95.0, 109.0, 122.0, 131.0, 115.0,
        109.0, 123.0, 126.0, 117.0, 109.0, 109.0, 117.0, 119.0, 103.0,
    ]
    eur = [
        314.0, 248.0, 245.0, 211.0, 189.0, 182.0, 165.0, 169.0, 152.0, 152.0,
        184.0, 168.0, 165.0, 132.0, 123.0, 124.0, 138.0, 138.0, 147.0, 123.0,
        100.0, 110.0, 119.0, 131.0, 134.0, 137.0, 147.0, 160.0, 152.0,
    ]
    panel = PanelSpec(
        xlim=(1979.6, 2008.4),
        ylim=(90.0, 320.0),
        xticks=_year_ticks(2008, "2008年"),
        yticks=[100.0, 150.0, 200.0, 250.0, 300.0, 320.0],
        zero_line=False,
        lines=[
            LineSeries(x=years, y=usd, label="日元/美元汇率", color_idx=0, style="dotted", marker="circle"),
            LineSeries(x=years, y=eur, label="日元/欧元汇率", color_idx=1, style="solid", marker="square"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-1",
        title="图 7-1 日元/美元、日元/欧元的汇率（年平均值）",
        panels=[panel],
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def _effective_rate_figure(
    fig_id: str,
    title: str,
    ylim: tuple[float, float],
    yticks: list[float],
    imf: list[float],
    bis: list[float],
    boj: list[float],
    mode: ThemeMode,
) -> str:
    years = _years(1980, 2008)
    panel = PanelSpec(
        xlim=(1979.5, 2008.5),
        ylim=ylim,
        xticks=_year_ticks(2008, "年"),
        yticks=yticks,
        zero_line=False,
        lines=[
            LineSeries(x=years, y=imf, label="IMF指数", color_idx=2, style="dotted", marker="square"),
            LineSeries(x=years, y=bis, label="BIS指数", color_idx=1, style="dashed", marker="circle"),
            LineSeries(x=years, y=boj, label="BOJ指数", color_idx=0, style="solid", width=2.6),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], width=860, height=560)
    return render_figure_svg(spec, mode)


def fig_7_2(mode: ThemeMode = "mono") -> str:
    imf = [
        100.0, 112.0, 107.0, 116.0, 122.0, 127.0, 163.0, 175.0, 195.0, 186.0,
        167.0, 182.0, 190.0, 231.0, 249.0, 260.0, 227.0, 212.0, 199.0, 234.0,
        262.0, 237.0, 225.0, 224.0, 228.0, 223.0, 210.0, 199.0, 222.0,
    ]
    bis = [
        100.0, 112.0, 107.0, 118.0, 126.0, 130.0, 166.0, 177.0, 195.0, 182.0,
        165.0, 179.0, 188.0, 228.0, 244.0, 257.0, 224.0, 212.0, 210.0, 240.0,
        263.0, 242.0, 230.0, 230.0, 234.0, 225.0, 210.0, 201.0, 230.0,
    ]
    boj = [
        100.0, 110.0, 102.0, 112.0, 117.0, 121.0, 166.0, 178.0, 196.0, 185.0,
        172.0, 188.0, 198.0, 235.0, 258.0, 273.0, 240.0, 226.0, 237.0, 269.0,
        290.0, 267.0, 257.0, 268.0, 279.0, 270.0, 250.0, 238.0, 268.0,
    ]
    return _effective_rate_figure(
        "7-2",
        "图 7-2 日元名义有效汇率（1980年=100）",
        (100.0, 300.0),
        [float(v) for v in range(100, 301, 20)],
        imf,
        bis,
        boj,
        mode,
    )


def fig_7_3(mode: ThemeMode = "mono") -> str:
    imf = [
        100.0, 108.0, 95.0, 101.0, 103.0, 102.0, 129.0, 136.0, 144.0, 137.0,
        124.0, 134.0, 138.0, 164.0, 174.0, 183.0, 155.0, 148.0, 138.0, 156.0,
        165.0, 147.0, 132.0, 126.0, 127.0, 125.0, 115.0, 107.0, 119.0,
    ]
    bis = [
        100.0, 106.0, 96.5, 104.4, 107.6, 109.0, 137.0, 144.0, 151.0, 140.0,
        123.0, 131.0, 135.5, 160.0, 168.0, 172.0, 146.0, 138.0, 134.0, 150.0,
        159.0, 142.0, 131.6, 129.0, 129.0, 120.5, 110.5, 103.0, 114.0,
    ]
    boj = [
        99.0, 101.0, 90.0, 95.0, 96.0, 96.5, 127.0, 133.0, 138.0, 127.0,
        116.0, 124.0, 127.0, 143.0, 150.5, 151.0, 128.0, 120.0, 122.0, 138.0,
        143.0, 127.0, 120.0, 120.5, 121.0, 113.0, 103.0, 96.0, 105.0,
    ]
    return _effective_rate_figure(
        "7-3",
        "图 7-3 日元的实际有效汇率（1980年=100）",
        (80.0, 190.0),
        [float(v) for v in range(80, 191, 10)],
        imf,
        bis,
        boj,
        mode,
    )


def fig_7_4(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2008)
    current = [
        -25.0, 12.0, 15.0, 57.0, 92.0, 120.0, 143.0, 120.0, 102.0, 88.0,
        64.0, 92.0, 142.0, 148.0, 132.0, 107.0, 71.0, 114.0, 157.0, 129.0,
        129.0, 105.0, 139.0, 157.0, 186.0, 182.0, 201.0, 248.0, 162.0,
    ]
    capital = [
        -20.0, 2.0, 42.0, 53.0, 96.0, 130.0, 123.0, 61.0, 83.0, 74.0,
        51.0, 94.0, 130.0, 115.0, 87.0, 62.0, 40.0, 149.0, 170.0, 64.0,
        93.0, 60.0, 82.0, -77.0, -9.0, 139.0, 126.0, 224.0, 195.0,
    ]
    reserve_years = _years(1985, 2008)
    reserve = [
        0.0, 26.0, 55.0, 20.0, -18.0, -13.0, -13.0, -1.0, 28.0, 26.0,
        55.0, 36.0, 9.0, -12.0, 86.0, 51.0, 48.0, 60.0, 215.0, 172.0,
        24.0, 35.0, 42.0, 30.0,
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2008.5),
        ylim=(-100.0, 250.0),
        xticks=_year_ticks(2008, "年"),
        yticks=[-100.0, -50.0, 0.0, 50.0, 100.0, 150.0, 200.0, 250.0],
        lines=[
            LineSeries(x=years, y=current, label="经常收支", color_idx=2, style="solid", width=2.0),
            LineSeries(x=years, y=capital, label="资本收支的负值", color_idx=1, style="dashed", width=2.4),
            LineSeries(x=reserve_years, y=reserve, label="外汇储备增减", color_idx=0, style="solid", marker="circle"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-4",
        title="图 7-4 日本的国际收支：经常收支、资本收支、外汇储备的增减（1000亿日元）",
        panels=[panel],
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def fig_7_5(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2007)
    current = [
        -1.0, 0.4, 0.6, 1.8, 2.8, 3.7, 4.2, 3.4, 2.7, 2.1,
        1.5, 2.0, 3.0, 3.0, 2.7, 2.1, 1.4, 2.2, 3.0, 2.6,
        2.5, 2.2, 2.9, 3.2, 3.8, 3.7, 3.9, 4.9,
    ]
    goods = [
        0.2, 1.7, 1.7, 2.6, 3.45, 4.0, 4.45, 3.8, 3.1, 2.7,
        2.3, 2.8, 3.3, 3.2, 3.0, 2.5, 1.8, 2.4, 3.1, 2.8,
        2.5, 1.7, 2.4, 2.5, 2.8, 2.1, 1.9, 2.4,
    ]
    services = [
        -1.15, -1.15, -1.0, -1.0, -0.9, -0.7, -0.65, -0.8, -1.0, -1.2,
        -1.4, -1.2, -1.2, -1.0, -1.0, -1.1, -1.3, -1.2, -1.2, -1.2,
        -1.0, -1.1, -1.0, -0.7, -0.8, -0.5, -0.4, -0.5,
    ]
    income = [
        0.05, -0.15, 0.1, 0.2, 0.3, 0.5, 0.5, 0.75, 0.7, 0.8,
        0.75, 0.7, 0.9, 0.9, 0.8, 0.8, 1.2, 1.4, 1.4, 1.3,
        1.35, 1.7, 1.7, 1.7, 1.9, 2.3, 2.7, 3.2,
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2007.5),
        ylim=(-2.0, 5.0),
        xticks=_year_ticks(2007, "年"),
        yticks=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        ylabel="%",
        lines=[
            LineSeries(x=years, y=current, label="经常收支", color_idx=2, style="dotted", width=2.0),
            LineSeries(x=years, y=goods, label="货物贸易收支", color_idx=1, style="dashed", marker="circle"),
            LineSeries(x=years, y=services, label="服务贸易收支", color_idx=4, style="dashdot"),
            LineSeries(x=years, y=income, label="所得收支", color_idx=0, style="solid", marker="square"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-5",
        title="图 7-5 1980—2007年日本经常收支和其明细（占GDP比率变化）",
        panels=[panel],
        note="资料来源：根据日本财务省网站内容制作",
        width=860,
        height=580,
    )
    return render_figure_svg(spec, mode)


def fig_7_6(mode: ThemeMode = "mono") -> str:
    rate_points = [
        (0.0, 153.8), (0.4, 153.1), (1.0, 153.6), (1.3, 153.2), (1.8, 153.6), (2.4, 153.5),
        (2.5, 152.3), (2.8, 151.8), (3.1, 152.0), (3.5, 151.5), (3.8, 150.2), (4.1, 149.2),
        (4.4, 147.8), (5.0, 146.2), (5.2, 146.7), (5.8, 146.2), (6.1, 146.4), (6.3, 142.7),
        (6.8, 142.5), (7.0, 141.2), (7.2, 142.9), (8.2, 142.1), (8.3, 139.7), (8.7, 138.3),
        (9.1, 140.5), (9.96, 138.6), (10.8, 139.8), (11.3, 139.4), (11.6, 139.8), (12.0, 139.7),
        (12.5, 142.1), (12.9, 143.4), (13.2, 142.1), (13.6, 145.4), (13.8, 142.1), (14.0, 144.2),
        (14.9, 143.2), (15.2, 143.9), (15.7, 144.8), (16.9, 145.3), (17.3, 146.0), (17.7, 146.9),
        (18.1, 149.2), (18.7, 150.1), (19.1, 150.9), (19.6, 151.1), (19.8, 148.6), (20.0, 152.9),
        (20.6, 152.9), (20.9, 150.2), (21.7, 150.4), (21.9, 149.9), (22.4, 150.6), (22.6, 152.2),
        (22.8, 150.9), (23.0, 151.8), (23.6, 151.3), (24.0, 150.1), (24.4, 150.1), (24.6, 146.0),
        (25.0, 142.8), (25.4, 142.2), (25.6, 143.2), (25.8, 142.1), (26.5, 141.8), (26.7, 140.9),
        (27.0, 141.8), (27.6, 141.4), (27.8, 142.5), (28.4, 144.6), (28.8, 142.7), (29.6, 144.2),
        (30.1, 144.0), (30.5, 146.4), (30.9, 146.8), (31.6, 146.8), (31.9, 144.9), (32.4, 143.7),
        (32.7, 142.0), (33.1, 143.0),
    ]
    week_labels = ["2/23", "3/30", "5/4", "6/8", "7/13", "8/17", "9/21"]
    panel = PanelSpec(
        xlim=(0.0, 33.2),
        ylim=(135.0, 165.0),
        xticks=[(5.0 * i, f"1987/{label}") for i, label in enumerate(week_labels)],
        yticks=[135.0, 140.0, 145.0, 150.0, 155.0, 160.0, 165.0],
        ylabel="日元/美元汇率",
        zero_line=False,
        lines=[
            LineSeries(x=[0.0, 5.85, 5.95, 33.2], y=[161.3, 161.3, 153.3, 153.3], color_idx=2, style="dashed", width=2.6),
            LineSeries(x=[0.0, 5.85, 5.95, 33.2], y=[145.7, 145.7, 138.6, 138.6], color_idx=2, style="dashed", width=2.6),
            LineSeries(x=[p[0] for p in rate_points], y=[p[1] for p in rate_points], color_idx=0, style="solid", width=2.2),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="7-6",
        title="图 7-6 《卢浮宫协议》下的日元/美元的汇率目标区（1987年2月23日—10月16日）",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def fig_7_7(mode: ThemeMode = "mono") -> str:
    rate_points = [
        (1993.0, 124.8), (1993.1, 117.8), (1993.21, 115.9), (1993.33, 111.3), (1993.4, 106.6),
        (1993.52, 105.9), (1993.63, 104.3), (1993.75, 108.2), (1993.86, 109.0), (1993.96, 111.7),
        (1994.05, 109.7), (1994.11, 104.3), (1994.24, 102.8), (1994.35, 102.0), (1994.43, 98.5),
        (1994.54, 99.7), (1994.7, 98.9), (1994.77, 97.4), (1994.92, 99.3), (1995.04, 98.1),
        (1995.15, 96.6), (1995.23, 91.2), (1995.3, 83.5), (1995.38, 83.1), (1995.49, 85.0),
        (1995.59, 98.1), (1995.68, 99.3), (1995.8, 101.6), (1995.91, 103.6), (1996.03, 106.3),
        (1996.14, 106.3), (1996.25, 104.7), (1996.37, 108.6), (1996.48, 107.8), (1996.6, 109.3),
        (1996.79, 113.6), (1996.9, 116.3), (1997.02, 122.1), (1997.13, 120.9), (1997.28, 126.7),
        (1997.36, 115.9), (1997.43, 114.4), (1997.55, 118.6), (1997.7, 120.5), (1997.78, 119.0),
        (1997.89, 128.2), (1997.97, 129.8), (1998.08, 126.7), (1998.19, 132.1), (1998.27, 132.5),
        (1998.35, 139.0), (1998.54, 144.1), (1998.65, 140.6), (1998.73, 134.4), (1998.78, 115.9),
        (1998.88, 123.6), (1998.95, 115.5), (1999.07, 119.0), (1999.22, 120.5), (1999.41, 121.3),
        (1999.49, 118.6), (1999.67, 109.7), (1999.79, 104.3), (1999.94, 102.0), (2000.09, 107.8),
        (2000.24, 106.6), (2000.4, 105.1), (2000.52, 109.3), (2000.63, 107.4), (2000.82, 110.5),
        (2000.97, 115.1), (2001.12, 116.7), (2001.2, 124.8), (2001.31, 123.2), (2001.39, 119.0),
        (2001.5, 124.4), (2001.62, 119.0), (2001.77, 122.1), (2001.88, 124.0), (2001.96, 131.3),
        (2002.15, 133.6), (2002.27, 132.1), (2002.45, 119.8), (2002.6, 118.2), (2002.79, 122.1),
        (2002.91, 120.5), (2003.06, 118.2), (2003.21, 119.8), (2003.37, 119.4), (2003.52, 119.4),
        (2003.71, 112.0), (2003.86, 111.3), (2004.01, 105.9), (2004.2, 107.4), (2004.32, 110.5),
        (2004.47, 108.6), (2004.54, 111.7), (2004.7, 109.7), (2004.89, 103.6), (2005.0, 104.0),
    ]
    interventions = [
        (1993.27, 640.0), (1993.35, 500.0), (1993.6, 760.0), (1994.11, 290.0), (1994.19, 250.0),
        (1994.27, 200.0), (1994.45, 430.0), (1994.6, 50.0), (1994.7, 100.0), (1994.85, 150.0),
        (1994.92, 130.0), (1995.11, 50.0), (1995.19, 1650.0), (1995.29, 470.0), (1995.38, 50.0),
        (1995.53, 780.0), (1995.67, 1650.0), (1996.12, 1560.0), (1997.94, -1080.0),
        (1998.27, -2830.0), (1998.45, 180.0), (1999.03, 620.0), (1999.45, 3480.0),
        (1999.54, 1310.0), (1999.69, 1000.0), (1999.85, 1090.0), (1999.94, 300.0),
        (2000.04, 600.0), (2000.19, 1000.0), (2000.28, 1350.0), (2001.69, 3130.0),
        (2002.35, 2080.0), (2002.45, 1830.0), (2003.02, 640.0), (2003.11, 1030.0),
        (2003.21, 510.0), (2003.36, 3850.0), (2003.44, 590.0), (2003.53, 1990.0),
        (2003.62, 400.0), (2003.71, 5100.0), (2003.78, 1610.0), (2003.87, 1540.0),
        (2003.96, 2590.0), (2004.05, 6830.0), (2004.13, 3450.0), (2004.22, 4500.0),
    ]
    panel = PanelSpec(
        xlim=(1993.0, 2005.0),
        ylim=(-4000.0, 8000.0),
        y2lim=(80.0, 150.0),
        xticks=[(float(y), str(y)) for y in range(1993, 2005)] + [(2005.0, "年")],
        yticks=[-4000.0, -2000.0, 0.0, 2000.0, 4000.0, 6000.0, 8000.0],
        y2ticks=[80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
        ylabel="10亿日元",
        y2label="日元/美元汇率",
        bars=[
            BarSeries(
                x=[p[0] for p in interventions],
                y=[p[1] for p in interventions],
                label="外汇市场干预",
                color_idx=0,
                width=0.06,
            ),
        ],
        lines=[
            LineSeries(
                x=[p[0] for p in rate_points],
                y=[p[1] for p in rate_points],
                label="日元/美元汇率（右轴）",
                color_idx=2,
                style="solid",
                width=2.0,
                axis="y2",
            ),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-7",
        title="图 7-7 日元/美元汇率和外汇市场干预（1993年1月—2004年12月）",
        panels=[panel],
        note="资料来源：日本财务省，IMF",
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def fig_7_8(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2007)
    household = [
        7.9, 9.65, 8.65, 10.1, 9.65, 10.9, 9.6, 8.6, 7.2, 9.75,
        10.75, 11.85, 6.7, 7.2, 5.35, 6.8, 4.5, 5.2, 6.8, 5.65,
        6.85, 4.0, 1.7, 2.8, 1.35, 1.8, 1.65, 3.45,
    ]
    corporate = [
        -3.45, -4.3, -3.45, -3.5, -3.9, -6.1, -4.65, -4.95, -5.55, -10.05,
        -11.8, -11.9, -4.8, -2.3, 0.25, -1.35, 0.95, -0.25, 6.2, 3.35,
        2.3, 2.9, 7.7, 7.0, 7.0, 7.15, 2.35, 1.25,
    ]
    government = [
        -4.4, -4.0, -4.0, -4.2, -2.8, -1.5, -1.3, -0.4, 0.5, 1.3,
        2.0, 1.6, 0.5, -2.3, -4.2, -4.9, -5.2, -4.4, -11.3, -7.8,
        -7.8, -6.7, -8.2, -8.2, -6.7, -6.9, -1.9, -2.9,
    ]
    overseas = [
        -1.1, 0.4, 0.6, 1.7, 2.7, 3.6, 4.2, 3.4, 2.5, 2.1,
        1.5, 1.6, 2.9, 3.0, 2.6, 1.9, 1.2, 2.1, 2.5, 2.0,
        2.2, 1.8, 2.6, 2.9, 3.4, 3.3, 3.5, 4.4,
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2007.5),
        ylim=(-15.0, 15.0),
        xticks=_year_ticks(2007, "年"),
        yticks=[-15.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0],
        ylabel="%",
        lines=[
            LineSeries(x=years, y=household, label="家计部门", color_idx=3, style="dotted", marker="square"),
            LineSeries(x=years, y=corporate, label="法人企业部门", color_idx=2, style="dashdot", marker="circle"),
            LineSeries(x=years, y=government, label="政府部门", color_idx=1, style="dashed", width=2.4),
            LineSeries(x=years, y=overseas, label="海外部门的负值", color_idx=0, style="solid", width=2.6),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-8",
        title="图 7-8 日本各部门的储蓄—投资均衡（GDP 占比）",
        panels=[panel],
        note="资料来源：根据内阁府的国民经济核算账户制作",
        width=860,
        height=580,
    )
    return render_figure_svg(spec, mode)


def fig_7_9(mode: ThemeMode = "mono") -> str:
    years = _years(1980, 2007)
    nominal = [
        100.0, 100.0, 100.0, 99.7, 95.2, 95.6, 100.0, 105.8, 106.9, 107.7,
        107.3, 107.7, 113.0, 122.5, 130.6, 130.6, 126.2, 127.2, 128.8, 132.0,
        129.2, 138.2, 140.7, 137.1, 134.6, 132.0, 131.4, 129.6,
    ]
    real = [
        100.0, 98.9, 97.1, 96.6, 94.0, 89.2, 94.0, 97.5, 97.1, 96.3,
        94.9, 94.3, 98.3, 103.8, 107.5, 105.2, 102.6, 102.0, 105.2, 105.5,
        100.1, 106.9, 109.3, 103.4, 98.6, 94.9, 91.3, 87.2,
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2007.5),
        ylim=(80.0, 145.0),
        xticks=_year_ticks(2007, "年"),
        yticks=[80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0],
        ylabel="（1980年=100）",
        zero_line=False,
        lines=[
            LineSeries(
                x=years, y=nominal, label="非贸易品部门的生产/贸易品部门的生产比率（名义值）",
                color_idx=2, style="dotted", marker="square",
            ),
            LineSeries(x=[1980.0, 2007.0], y=[100.0, 138.9], label="趋势线", color_idx=3, style="dashed", width=2.0),
            LineSeries(
                x=years, y=real, label="非贸易品部门的生产/贸易品部门的生产比率（实际值）",
                color_idx=1, style="solid", marker="circle",
            ),
            LineSeries(x=[1980.0, 2007.0], y=[100.0, 99.3], label="趋势线", color_idx=0, style="dashdot", width=2.0),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-9",
        title="图 7-9 非贸易品部门的生产/贸易品部门的生产比率（名义值和实际值）",
        panels=[panel],
        width=860,
        height=600,
    )
    return render_figure_svg(spec, mode)


def fig_7_10(mode: ThemeMode = "mono") -> str:
    reserves = [
        18.0, 20.0, 20.0, 17.0, 20.0, 20.0, 36.0, 72.0, 87.0, 72.0,
        66.0, 59.0, 59.0, 87.0, 117.0, 167.0, 207.0, 207.0, 200.0, 272.0,
        344.0, 385.0, 454.0, 654.0, 824.0, 824.0, 878.0, 952.0,
    ]
    panel = PanelSpec(
        xlim=(1979.5, 2007.5),
        ylim=(0.0, 1000.0),
        xticks=_year_ticks(2007, "年"),
        yticks=[0.0, 200.0, 400.0, 600.0, 800.0, 1000.0],
        ylabel="10亿美元",
        zero_line=False,
        lines=[LineSeries(x=_years(1980, 2007), y=reserves, color_idx=0, style="solid", marker="circle")],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="7-10",
        title="图 7-10 日本外汇储备额（1980—2007年）",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def fig_8_1(mode: ThemeMode = "mono") -> str:
    sna68 = [
        11.85, 12.8, 12.5, 12.3, 13.7, 14.5, 15.9, 15.6, 14.9, 15.4,
        15.8, 15.0, 14.1, 16.9, 17.1, 17.7, 17.8, 18.2, 20.5, 23.3,
        22.9, 23.3, 21.9, 21.0, 18.3, 18.0, 18.5, 16.85, 16.2, 15.9,
        15.7, 15.7, 13.9, 13.1, 13.0, 12.1, 13.5, 13.3, 13.5, 13.4,
        13.85, 13.5, 12.7, 13.5,
    ]
    sna68_years = _years(1955, 1998)
    sna93_years = [*_years(1980, 2001), 2003.0]
    sna93 = [
        15.45, 16.2, 15.0, 14.5, 14.3, 13.8, 13.05, 11.7, 11.9, 12.15,
        12.55, 13.1, 12.55, 11.95, 11.2, 10.4, 8.6, 8.7, 10.0, 9.3,
        8.3, 5.75, 6.4,
    ]
    sna2000 = [9.3, 9.1, 9.9, 8.7, 7.5, 4.4, 4.35, 3.45, 3.1, 3.3, 2.9]
    panel = PanelSpec(
        xlim=(1954.5, 2006.5),
        ylim=(0.0, 25.0),
        xticks=[(float(y), str(y)) for y in range(1955, 2006, 5)],
        yticks=[(v, f"{v:.1f}") for v in (0.0, 5.0, 10.0, 15.0, 20.0, 25.0)],
        ylabel="储蓄率（%）",
        zero_line=False,
        lines=[
            LineSeries(x=sna68_years[:24], y=sna68[:24], label="68SNA", color_idx=3, style="dotted", marker="square"),
            LineSeries(x=sna68_years[23:], y=sna68[23:], color_idx=3, style="dotted", marker="square"),
            LineSeries(x=sna93_years, y=sna93, label="93SNA", color_idx=2, style="dashed", marker="triangle"),
            LineSeries(
                x=_years(1996, 2006), y=sna2000, label="93SNA（2000年基准改定）",
                color_idx=0, style="solid", marker="diamond",
            ),
        ],
        legend_loc="top",
    )
    spec = FigureSpec(
        fig_id="8-1",
        title="图 8-1 日本的家庭净储蓄率的变化，1955—2006年",
        panels=[panel],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def fig_8_2(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1955, 2006, 5)]
    child = [54.3, 47.0, 38.0, 35.2, 36.0, 34.7, 31.5, 26.3, 23.1, 21.1, 20.6]
    elderly = [8.6, 8.6, 9.4, 10.2, 12.0, 13.5, 15.1, 17.2, 20.9, 25.9, 30.5]
    panel = PanelSpec(
        xlim=(1952.5, 2007.5),
        ylim=(0.0, 60.0),
        xticks=[(y, str(int(y))) for y in years],
        yticks=[(v, f"{v:.1f}") for v in (0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0)],
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=child, label="儿童人口比率", color_idx=1, style="dotted", marker="square"),
            LineSeries(x=years, y=elderly, label="老年人口比率", color_idx=0, style="solid", marker="triangle"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="8-2",
        title="图 8-2 日本的人口年龄构成的变化，1955—2005年",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "7-1": fig_7_1,
        "7-2": fig_7_2,
        "7-3": fig_7_3,
        "7-4": fig_7_4,
        "7-5": fig_7_5,
        "7-6": fig_7_6,
        "7-7": fig_7_7,
        "7-8": fig_7_8,
        "7-9": fig_7_9,
        "7-10": fig_7_10,
        "8-1": fig_8_1,
        "8-2": fig_8_2,
    }
