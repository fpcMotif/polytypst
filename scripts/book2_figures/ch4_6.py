from __future__ import annotations

import math
from collections.abc import Callable
from html import escape

from scripts.book2_figures.engine import (
    FONT_STACK,
    Annotation,
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    get_palette,
    render_figure_svg,
)


def _interleave_none(xs: list[float], ys: list[float]) -> tuple[list[float], list[float | None]]:
    out_x: list[float] = []
    out_y: list[float | None] = []
    for xv, yv in zip(xs, ys):
        out_x.append(xv)
        out_y.append(yv)
        out_x.append(xv)
        out_y.append(None)
    return out_x, out_y


def fig_4_1(mode: ThemeMode = "mono") -> str:
    n_months = 163
    xs = [1993.0 + i / 12.0 for i in range(n_months)]

    cgpi_anchors = [
        (1993.0, 107.6),
        (1993.5, 106.8),
        (1994.0, 105.6),
        (1994.5, 105.0),
        (1995.0, 104.7),
        (1995.5, 104.1),
        (1996.0, 103.2),
        (1996.5, 102.1),
        (1997.2, 102.0),
        (1997.33, 104.0),
        (1997.75, 103.0),
        (1998.25, 101.5),
        (1998.75, 101.3),
        (1999.25, 99.7),
        (1999.75, 100.0),
        (2000.0, 100.6),
        (2000.5, 100.0),
        (2001.0, 98.8),
        (2001.5, 97.6),
        (2002.0, 96.2),
        (2002.5, 95.6),
        (2003.0, 95.1),
        (2003.5, 94.7),
        (2004.0, 95.3),
        (2004.5, 96.5),
        (2004.9, 96.8),
        (2005.0, 95.5),
        (2005.25, 97.3),
        (2005.75, 98.7),
        (2006.25, 99.6),
        (2006.5, 101.1),
    ]

    cpi_anchors = [
        (1993.0, 99.1),
        (1993.5, 100.8),
        (1994.0, 100.4),
        (1994.3, 101.1),
        (1994.75, 101.4),
        (1995.2, 100.5),
        (1995.7, 100.9),
        (1996.1, 100.3),
        (1996.5, 101.1),
        (1997.1, 100.9),
        (1997.33, 103.1),
        (1997.75, 103.7),
        (1998.25, 103.6),
        (1998.75, 104.1),
        (1999.25, 103.3),
        (1999.75, 103.4),
        (2000.25, 102.4),
        (2000.75, 102.0),
        (2001.25, 101.6),
        (2001.75, 101.2),
        (2002.1, 100.1),
        (2002.5, 100.7),
        (2003.0, 100.1),
        (2003.5, 100.4),
        (2004.0, 99.9),
        (2004.6, 100.7),
        (2005.0, 99.7),
        (2005.5, 100.1),
        (2006.0, 99.9),
        (2006.5, 100.3),
    ]

    def interp(xv: float, pts: list[tuple[float, float]]) -> float:
        if xv <= pts[0][0]:
            return pts[0][1]
        if xv >= pts[-1][0]:
            return pts[-1][1]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    cgpi_y: list[float | None] = [
        interp(x, cgpi_anchors) + 0.14 * math.sin(i * 1.7) for i, x in enumerate(xs)
    ]
    cpi_y: list[float | None] = [
        interp(x, cpi_anchors) + 0.25 * math.sin(i * 1.3) for i, x in enumerate(xs)
    ]

    gdp_pts = [
        (1993.1, 100.5),
        (1993.8, 100.3),
        (1994.1, 102.9),
        (1994.6, 102.1),
        (1994.85, 105.8),
        (1995.1, 102.4),
        (1995.35, 104.5),
        (1995.6, 101.5),
        (1995.85, 105.2),
        (1996.1, 101.5),
        (1996.35, 104.1),
        (1996.6, 100.6),
        (1996.85, 104.0),
        (1997.1, 100.9),
        (1997.35, 104.7),
        (1997.6, 101.3),
        (1997.85, 105.0),
        (1998.1, 101.8),
        (1998.35, 104.2),
        (1998.6, 100.6),
        (1998.85, 104.5),
        (1999.1, 100.8),
        (1999.6, 99.2),
        (1999.85, 102.7),
        (2000.1, 99.4),
        (2000.35, 101.5),
        (2000.6, 97.8),
        (2000.85, 101.2),
        (2001.1, 98.1),
        (2001.35, 100.2),
        (2001.6, 96.5),
        (2001.85, 99.8),
        (2002.1, 97.0),
        (2002.35, 98.6),
        (2002.6, 95.0),
        (2002.85, 98.1),
        (2003.1, 94.5),
        (2003.35, 97.4),
        (2003.6, 93.8),
        (2003.85, 96.5),
        (2004.1, 93.4),
        (2004.35, 95.8),
        (2004.6, 92.7),
        (2004.85, 96.1),
        (2005.1, 92.2),
        (2005.35, 94.7),
        (2005.6, 91.4),
        (2005.85, 94.7),
        (2006.1, 91.1),
        (2006.35, 94.0),
    ]
    gx, gy = _interleave_none([p[0] for p in gdp_pts], [p[1] for p in gdp_pts])

    xticks = [
        (1993.0, "1993-1"),
        (1994.17, "1994-3"),
        (1995.33, "1995-5"),
        (1996.5, "1996-7"),
        (1997.67, "1997-9"),
        (1998.83, "1998-11"),
        (2000.0, "2000-1"),
        (2001.17, "2001-3"),
        (2002.33, "2002-5"),
        (2003.5, "2003-7"),
        (2004.67, "2004-9"),
        (2005.83, "2005-11"),
    ]

    spec = FigureSpec(
        fig_id="4-1",
        title="图 4-1 物价（平减指数）",
        note="资料来源：日本央行、内阁府、总务省。",
        width=880,
        height=540,
        panels=[
            PanelSpec(
                xlim=(1993.0, 2006.6),
                ylim=(90.0, 110.0),
                xticks=xticks,
                yticks=[90, 92, 94, 96, 98, 100, 102, 104, 106, 108, 110],
                y2lim=(90.0, 110.0),
                y2ticks=[90, 95, 100, 105, 110],
                xlabel="年-月",
                ylabel="2000年=100",
                y2label="2005年=100",
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(
                        x=xs,
                        y=cgpi_y,
                        label="企业商品交易价格指数（2000年为基准年，左轴）",
                        color_idx=0,
                        style="solid",
                        width=2.4,
                    ),
                    LineSeries(
                        x=xs,
                        y=cpi_y,
                        label="消费者价格指数（2005年为基准年，左轴）",
                        color_idx=2,
                        style="solid",
                        width=2.2,
                        fixed_style=True,
                    ),
                    LineSeries(
                        x=gx,
                        y=gy,
                        label="GDP平减指数（2000年为基准年，连锁法，右轴）",
                        color_idx=0,
                        style="none",
                        marker="circle",
                        axis="y2",
                    ),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_4_2(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1990, 2007)]
    counts = [
        77.0,
        58.0,
        155.0,
        196.0,
        161.0,
        724.0,
        162.0,
        214.0,
        1204.0,
        639.0,
        542.0,
        2575.0,
        5264.0,
        4763.0,
        1356.0,
        1008.0,
        961.0,
    ]
    anns = [
        Annotation(
            x=yr,
            y=val,
            text=str(int(val)),
            dx=0.0,
            dy=-6.0,
            arrow=False,
            fontsize=10.5,
        )
        for yr, val in zip(years, counts)
    ]
    spec = FigureSpec(
        fig_id="4-2",
        title="图 4-2 三家综合性报社（朝日、读卖、每日）关于通货紧缩的报道数量",
        width=860,
        height=500,
        panels=[
            PanelSpec(
                xlim=(1989.2, 2006.8),
                ylim=(0.0, 6000.0),
                xticks=[(yr, str(int(yr))) for yr in years],
                yticks=[0, 1000, 2000, 3000, 4000, 5000, 6000],
                xlabel="年",
                ylabel="件",
                zero_line=False,
                legend_loc="none",
                bars=[
                    BarSeries(
                        x=years,
                        y=counts,
                        color_idx=0,
                        width=0.56,
                        opacity=0.82,
                    )
                ],
                annotations=anns,
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_4_3(mode: ThemeMode = "mono") -> str:
    uk_pts = [
        (1784.0, 112.0),
        (1789.0, 105.0),
        (1795.0, 125.0),
        (1800.0, 150.0),
        (1805.0, 155.0),
        (1809.0, 162.0),
        (1815.0, 152.0),
        (1822.0, 126.0),
        (1827.0, 110.0),
        (1831.0, 104.0),
        (1837.0, 111.0),
        (1842.0, 106.0),
        (1848.0, 93.0),
        (1854.0, 103.0),
        (1860.0, 110.0),
        (1868.0, 112.0),
        (1874.0, 110.0),
        (1880.0, 96.0),
        (1888.0, 80.0),
        (1895.0, 71.0),
        (1902.0, 79.0),
        (1910.0, 90.0),
    ]
    us_pts = [
        (1802.0, 88.0),
        (1808.0, 88.0),
        (1814.0, 104.0),
        (1818.0, 100.0),
        (1824.0, 68.0),
        (1830.0, 61.0),
        (1836.0, 69.0),
        (1840.0, 64.0),
        (1846.0, 47.0),
        (1850.0, 54.0),
        (1855.0, 65.0),
        (1858.0, 66.0),
        (1863.0, 96.0),
        (1867.0, 110.0),
        (1870.0, 102.0),
        (1876.0, 76.0),
        (1882.0, 60.0),
        (1888.0, 48.0),
        (1895.0, 36.0),
        (1902.0, 50.0),
        (1910.0, 64.0),
    ]
    de_pts = [
        (1855.0, 124.0),
        (1858.0, 125.0),
        (1861.0, 123.0),
        (1866.0, 124.0),
        (1868.0, 128.0),
        (1874.0, 125.0),
        (1882.0, 105.0),
        (1888.0, 101.0),
        (1895.0, 95.0),
        (1900.0, 100.0),
        (1905.0, 111.0),
        (1910.0, 118.0),
    ]
    decades = [float(y) for y in range(1780, 1915, 10)]
    spec = FigureSpec(
        fig_id="4-3",
        title="图 4-3 一战前物价指数的长期变化",
        note="注：产品批发价格的9年变化平均值。资料来源：Schumpeter (1939), Business Cycles, p. 468。",
        width=860,
        height=490,
        panels=[
            PanelSpec(
                xlim=(1780.0, 1910.0),
                ylim=(0.0, 165.0),
                xticks=[(yr, str(int(yr))) for yr in decades],
                yticks=[(0.0, ""), (50.0, ""), (100.0, ""), (150.0, "")],
                xlabel="年",
                zero_line=False,
                vlines=[(yr, "", "solid") for yr in decades[1:-1]],
                legend_loc="none",
                lines=[
                    LineSeries(
                        x=[p[0] for p in uk_pts],
                        y=[p[1] for p in uk_pts],
                        label="英国",
                        color_idx=1,
                        style="dotted",
                        width=2.5,
                    ),
                    LineSeries(
                        x=[p[0] for p in us_pts],
                        y=[p[1] for p in us_pts],
                        label="美国",
                        color_idx=0,
                        style="solid",
                        width=2.6,
                    ),
                    LineSeries(
                        x=[p[0] for p in de_pts],
                        y=[p[1] for p in de_pts],
                        label="德国",
                        color_idx=2,
                        style="dashed",
                        width=2.4,
                    ),
                ],
                annotations=[
                    Annotation(x=1830.0, y=126.0, text="英国", dx=0.0, dy=-10.0, arrow=False, color_idx=1, fontsize=13.0),
                    Annotation(x=1840.0, y=68.0, text="美国", dx=0.0, dy=-12.0, arrow=False, color_idx=0, fontsize=13.0),
                    Annotation(x=1890.0, y=108.0, text="德国", dx=0.0, dy=-12.0, arrow=False, color_idx=2, fontsize=13.0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_4_4(mode: ThemeMode = "mono") -> str:
    years = [1913.0 + i * 0.25 for i in range(109)]
    x_scale = 27.0 / 26.25
    non_ag_pts = [
        (1913.0, 53.0),
        (1915.0, 47.0),
        (1916.0, 58.0),
        (1917.5, 88.0),
        (1918.5, 92.0),
        (1919.2, 88.0),
        (1920.3, 124.0),
        (1921.3, 71.0),
        (1923.0, 79.0),
        (1924.2, 71.0),
        (1925.5, 75.0),
        (1927.5, 68.0),
        (1929.2, 66.0),
        (1931.0, 54.0),
        (1932.5, 47.5),
        (1933.5, 57.0),
        (1935.5, 56.5),
        (1937.2, 62.0),
        (1938.5, 58.0),
        (1939.25, 59.5),
    ]
    all_pts = [
        (1913.0, 46.0),
        (1915.0, 44.5),
        (1916.0, 52.0),
        (1917.5, 80.0),
        (1918.5, 87.0),
        (1919.2, 86.0),
        (1920.3, 109.0),
        (1921.3, 61.0),
        (1923.0, 68.0),
        (1924.2, 63.0),
        (1925.5, 68.5),
        (1927.5, 62.5),
        (1929.2, 62.0),
        (1931.0, 47.0),
        (1932.5, 39.0),
        (1933.5, 47.0),
        (1935.5, 53.0),
        (1937.2, 57.5),
        (1938.5, 50.5),
        (1939.25, 52.0),
    ]
    ag_pts = [
        (1913.0, 39.0),
        (1914.0, 41.0),
        (1915.5, 39.5),
        (1916.5, 48.0),
        (1917.5, 81.0),
        (1918.8, 91.0),
        (1920.1, 96.0),
        (1921.3, 47.0),
        (1922.5, 55.0),
        (1924.0, 54.5),
        (1924.8, 63.0),
        (1926.8, 54.0),
        (1928.5, 60.5),
        (1929.5, 59.0),
        (1931.0, 38.0),
        (1932.5, 23.5),
        (1933.5, 33.0),
        (1935.0, 45.0),
        (1936.8, 53.0),
        (1938.0, 38.0),
        (1939.0, 35.5),
        (1939.25, 38.0),
    ]

    def interp_log(xv: float, pts: list[tuple[float, float]], wobble: float, idx: int) -> float:
        xv = 1913.0 + (xv - 1913.0) / x_scale
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                v = y0 + t * (y1 - y0) + wobble * math.sin(idx * 1.9)
                return math.log10(max(20.0, v))
        return math.log10(pts[-1][1])

    tick_vals = [20, 30, 40, 60, 80, 100, 150]
    log_ticks = [(math.log10(float(v)), str(v)) for v in tick_vals]
    v_years = [1915.0, 1920.0, 1925.0, 1930.0, 1935.0]

    spec = FigureSpec(
        fig_id="4-4",
        title="图 4-4 1913—1939 年美国产品批发价格（月度指数）",
        note="注：基于 Bureau of Labor Statistics；Board of Governors of the Federal Reserve System, Historical Chart Book, 1961。",
        width=860,
        height=510,
        panels=[
            PanelSpec(
                xlim=(1913.0, 1940.0),
                ylim=(math.log10(20.0), math.log10(150.0)),
                xticks=[(yr + 0.5, str(int(yr))) for yr in v_years],
                yticks=log_ticks,
                y2lim=(math.log10(20.0), math.log10(150.0)),
                y2ticks=log_ticks,
                xlabel="年",
                zero_line=False,
                vlines=[(yr + 1.0, "", "solid") for yr in v_years],
                legend_loc="none",
                lines=[
                    LineSeries(
                        x=years,
                        y=[interp_log(x, non_ag_pts, 0.9, i) for i, x in enumerate(years)],
                        label="非农产品",
                        color_idx=1,
                        style="dashed",
                        width=2.2,
                    ),
                    LineSeries(
                        x=years,
                        y=[interp_log(x, all_pts, 0.7, i) for i, x in enumerate(years)],
                        label="所有产品",
                        color_idx=0,
                        style="solid",
                        width=2.5,
                    ),
                    LineSeries(
                        x=years,
                        y=[interp_log(x, ag_pts, 1.1, i) for i, x in enumerate(years)],
                        label="农产品",
                        color_idx=2,
                        style="solid",
                        width=1.9,
                    ),
                ],
                annotations=[
                    Annotation(x=1934.1, y=math.log10(62.0), text="非农产品", dx=0.0, dy=-8.0, arrow=False, color_idx=1),
                    Annotation(x=1924.1, y=math.log10(48.0), text="农产品", dx=0.0, dy=12.0, arrow=False, color_idx=2),
                    Annotation(x=1932.1, y=math.log10(43.5), text="所有产品", dx=-28.0, dy=26.0, arrow=True, color_idx=0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_4_5(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1985, 2007)]
    hm = [
        6.5,
        7.0,
        12.4,
        10.6,
        11.2,
        9.4,
        1.5,
        -2.2,
        3.6,
        4.6,
        4.8,
        8.5,
        7.6,
        8.6,
        7.6,
        7.6,
        7.3,
        25.8,
        16.8,
        7.4,
        2.8,
        -13.0,
    ]
    m2cd = [
        8.4,
        8.7,
        10.4,
        11.2,
        9.9,
        11.7,
        3.6,
        0.6,
        1.1,
        2.1,
        3.0,
        3.3,
        3.1,
        4.4,
        3.6,
        2.1,
        2.8,
        3.3,
        1.7,
        1.9,
        1.8,
        1.1,
    ]
    cpi = [
        2.0,
        0.6,
        0.1,
        0.7,
        2.3,
        3.1,
        3.3,
        1.7,
        1.3,
        0.7,
        -0.1,
        0.1,
        1.8,
        0.6,
        -0.3,
        -0.7,
        -0.7,
        -0.9,
        -0.3,
        0.0,
        -0.3,
        0.3,
    ]
    spec = FigureSpec(
        fig_id="4-5",
        title="图 4-5 货币和物价的时间序列数据（日本）",
        note="资料来源：日本央行、总务省《产品零售价格统计调查》。",
        width=860,
        height=500,
        panels=[
            PanelSpec(
                xlim=(1985.0, 2006.0),
                ylim=(-15.0, 30.0),
                xticks=[(1985.0, "1985"), (1990.0, "1990"), (1995.0, "1995"), (2000.0, "2000"), (2005.0, "2005")],
                yticks=[-15, -10, -5, 0, 5, 10, 15, 20, 25, 30],
                xlabel="年",
                ylabel="%",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=years, y=hm, label="HM", color_idx=2, style="solid", marker="square", width=2.2),
                    LineSeries(x=years, y=m2cd, label="M2+CD", color_idx=1, style="dashed", marker="cross", width=2.2),
                    LineSeries(x=years, y=cpi, label="CPI", color_idx=0, style="solid", marker="circle", width=2.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_4_6(mode: ThemeMode = "mono") -> str:
    centers = [0.0, 1.0, 2.0, 3.0]
    labels = ["1986—1990", "1991—1995", "1996—2000", "2001—2005"]
    spec = FigureSpec(
        fig_id="4-6",
        title="图 4-6 每 5 年累积变化率（日本）",
        width=860,
        height=480,
        panels=[
            PanelSpec(
                xlim=(-0.6, 3.6),
                ylim=(-10.0, 70.0),
                xticks=list(zip(centers, labels)),
                yticks=[-10, 0, 10, 20, 30, 40, 50, 60, 70],
                xlabel="年",
                ylabel="%",
                legend_loc="bottom",
                bars=[
                    BarSeries(
                        x=[c - 0.22 for c in centers],
                        y=[51.0, 12.3, 39.6, 59.0],
                        label="HM",
                        color_idx=2,
                        width=0.20,
                    ),
                    BarSeries(
                        x=centers,
                        y=[52.2, 10.7, 17.0, 12.4],
                        label="M2+CD",
                        color_idx=5,
                        width=0.20,
                    ),
                    BarSeries(
                        x=[c + 0.22 for c in centers],
                        y=[7.1, 7.1, 1.4, -1.9],
                        label="CPI",
                        color_idx=0,
                        width=0.20,
                    ),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_4_7(mode: ThemeMode = "mono") -> str:
    centers = [0.0, 1.0, 2.0, 3.0]
    labels = ["1986—1990", "1991—1995", "1996—2000", "2001—2005"]
    spec = FigureSpec(
        fig_id="4-7",
        title="图 4-7 每 5 年的平均变化率（日本）",
        width=860,
        height=480,
        panels=[
            PanelSpec(
                xlim=(-0.6, 3.6),
                ylim=(-2.0, 14.0),
                xticks=list(zip(centers, labels)),
                yticks=[-2, 0, 2, 4, 6, 8, 10, 12, 14],
                xlabel="年",
                ylabel="%",
                legend_loc="bottom",
                bars=[
                    BarSeries(
                        x=[c - 0.22 for c in centers],
                        y=[10.2, 2.5, 7.9, 11.8],
                        label="HM",
                        color_idx=2,
                        width=0.20,
                    ),
                    BarSeries(
                        x=centers,
                        y=[10.5, 2.1, 3.3, 2.3],
                        label="M2+CD",
                        color_idx=5,
                        width=0.20,
                    ),
                    BarSeries(
                        x=[c + 0.22 for c in centers],
                        y=[1.4, 1.4, 0.3, -0.4],
                        label="CPI",
                        color_idx=0,
                        width=0.20,
                    ),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_5_1(mode: ThemeMode = "mono") -> str:
    xs_a = [1975.0 + i * 0.25 for i in range(124)]
    level_anchors = [
        (1975.0, 56.2),
        (1977.0, 67.2),
        (1979.0, 73.0),
        (1980.5, 81.8),
        (1982.0, 84.5),
        (1984.0, 88.0),
        (1985.0, 90.4),
        (1986.0, 93.0),
        (1988.0, 94.0),
        (1990.0, 99.9),
        (1991.0, 102.8),
        (1992.0, 103.4),
        (1993.5, 103.8),
        (1996.5, 102.0),
        (1997.5, 103.0),
        (2000.0, 100.0),
        (2003.0, 95.3),
        (2005.75, 92.2),
    ]

    def interp(xv: float, pts: list[tuple[float, float]]) -> float:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    ys_a: list[float | None] = [interp(x, level_anchors) for x in xs_a]

    xs_b = [1976.0 + i * 0.25 for i in range(120)]
    inf_anchors = [
        (1976.0, 8.8),
        (1976.5, 9.8),
        (1977.0, 9.1),
        (1977.5, 7.7),
        (1978.0, 5.8),
        (1978.5, 4.8),
        (1979.0, 4.6),
        (1979.5, 3.2),
        (1980.5, 8.3),
        (1981.5, 3.6),
        (1982.25, 2.5),
        (1982.75, 1.4),
        (1983.5, 2.4),
        (1984.75, 3.7),
        (1985.5, 2.2),
        (1986.25, 2.4),
        (1987.25, -0.4),
        (1988.0, 0.5),
        (1989.5, 1.6),
        (1990.25, 2.5),
        (1991.75, 3.1),
        (1992.75, 0.9),
        (1994.0, -0.5),
        (1996.5, -0.6),
        (1997.75, -0.3),
        (1998.75, -0.4),
        (1999.75, -1.9),
        (2001.0, -1.2),
        (2002.25, -1.5),
        (2003.0, -2.4),
        (2003.5, -1.3),
        (2004.25, -1.5),
        (2004.75, -0.5),
        (2005.75, -1.6),
    ]
    ys_b: list[float | None] = [
        interp(x, inf_anchors) + 0.18 * math.sin(i * 1.7) for i, x in enumerate(xs_b)
    ]

    spec = FigureSpec(
        fig_id="5-1",
        title="图 5-1 GDP 平减指数（1975—2005 年）",
        note="资料来源：内阁府《国民经济核算》，详见注5。",
        rows=2,
        cols=1,
        width=860,
        height=680,
        panels=[
            PanelSpec(
                title="A 价格水平（指数：2000年=100）",
                xlim=(1973.3, 2007.2),
                ylim=(56.0, 105.0),
                xticks=[(float(y), str(y)) for y in range(1975, 2006, 3)],
                yticks=[56, 63, 70, 77, 84, 91, 98, 105],
                xlabel="年",
                zero_line=False,
                legend_loc="none",
                lines=[LineSeries(x=xs_a, y=ys_a, color_idx=0, width=2.5)],
            ),
            PanelSpec(
                title="B 通货膨胀率（同比，%）",
                xlim=(1974.4, 2007.2),
                ylim=(-2.5, 10.0),
                xticks=[(float(y), str(y)) for y in range(1976, 2006, 3)],
                yticks=[-2.5, 0.0, 2.5, 5.0, 7.5, 10.0],
                xlabel="年",
                legend_loc="none",
                lines=[LineSeries(x=xs_b, y=ys_b, color_idx=1, width=2.4)],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def fig_5_2(mode: ThemeMode = "mono") -> str:
    xs = [1975.0 + i * 0.25 for i in range(124)]
    m1_anchors = [
        (1975.0, 43.0),
        (1978.0, 57.0),
        (1980.0, 68.0),
        (1981.0, 66.0),
        (1984.0, 76.0),
        (1987.0, 91.0),
        (1989.0, 108.0),
        (1990.0, 106.0),
        (1993.0, 123.0),
        (1995.0, 136.0),
        (1997.0, 171.0),
        (1999.0, 205.0),
        (2000.0, 228.0),
        (2001.0, 233.0),
        (2002.0, 275.0),
        (2003.0, 293.0),
        (2004.0, 304.0),
        (2005.75, 336.0),
    ]

    def interp(xv: float) -> float:
        for i in range(len(m1_anchors) - 1):
            x0, y0 = m1_anchors[i]
            x1, y1 = m1_anchors[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return m1_anchors[-1][1]

    ys: list[float | None] = [interp(x) for x in xs]
    spec = FigureSpec(
        fig_id="5-2",
        title="图 5-2 货币存量（1975—2005 年，M1）",
        note="资料来源：日经数据库。",
        width=860,
        height=480,
        panels=[
            PanelSpec(
                xlim=(1973.2, 2007.8),
                ylim=(0.0, 350.0),
                xticks=[(float(y), str(y)) for y in range(1975, 2006, 3)],
                yticks=[0, 50, 100, 150, 200, 250, 300, 350],
                xlabel="年",
                ylabel="万亿日元",
                zero_line=False,
                legend_loc="none",
                lines=[LineSeries(x=xs, y=ys, color_idx=0, width=2.5)],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_5_3(mode: ThemeMode = "mono") -> str:
    pts_pre95 = [
        (0.76, 1.00), (0.78, 1.02), (0.82, 1.04), (0.85, 0.99), (0.93, 0.98),
        (1.16, 0.96), (1.18, 0.95), (1.25, 1.02), (1.27, 0.93), (1.35, 1.00),
        (1.37, 1.02), (1.42, 0.95), (1.45, 0.98), (1.46, 1.02), (1.47, 1.07),
        (1.48, 0.93), (1.55, 0.96), (1.56, 1.08), (1.58, 0.92), (1.60, 1.01),
        (1.62, 0.94), (1.65, 1.09), (1.68, 0.97), (1.72, 1.08), (1.78, 1.09),
        (1.82, 0.94), (1.84, 0.97), (1.86, 0.93), (1.88, 0.99), (1.92, 0.95),
        (1.94, 0.98), (1.96, 1.11), (1.97, 1.13), (1.98, 0.99), (2.01, 0.97),
        (2.03, 0.92), (2.05, 1.08), (2.06, 1.11), (2.11, 0.91), (2.15, 0.90),
        (2.18, 1.10), (2.20, 0.96), (2.26, 1.07), (2.33, 0.96), (2.40, 1.12),
        (2.53, 0.99), (2.57, 1.06), (2.59, 1.12),
    ]
    pts_post95 = [
        (0.35, 1.05), (-0.20, 1.08),
        (-0.74, 1.12), (-0.74, 1.15), (-0.72, 1.18), (-0.72, 1.20),
        (-0.69, 1.22), (-0.68, 1.24), (-0.68, 1.26), (-0.76, 1.28),
        (-0.81, 1.32), (-0.81, 1.34), (-0.92, 1.36),
        (-1.45, 1.38), (-1.38, 1.54), (-1.56, 1.55), (-1.88, 1.41), (-1.92, 1.53),
        (-3.48, 1.45), (-3.48, 1.48), (-3.74, 1.51), (-3.90, 1.53), (-3.90, 1.60),
        (-4.77, 1.64), (-5.80, 1.76), (-6.05, 1.68), (-6.21, 1.77), (-6.39, 1.79),
        (-6.39, 1.81), (-6.60, 1.71), (-6.60, 1.86),
        (-6.88, 1.74), (-6.88, 1.79), (-6.88, 1.82), (-6.88, 1.85), (-6.88, 1.87),
        (-6.88, 1.89), (-6.88, 1.90),
        (-7.30, 1.81), (-7.30, 1.83), (-7.30, 1.85),
    ]
    x_pre, y_pre = _interleave_none([p[0] for p in pts_pre95], [p[1] for p in pts_pre95])
    x_post, y_post = _interleave_none([p[0] for p in pts_post95], [p[1] for p in pts_post95])

    spec = FigureSpec(
        fig_id="5-3",
        title="图 5-3 （M−P−Y、R）的散点图（1975—2005 年、对数）",
        note="资料来源：作者创建。",
        width=860,
        height=500,
        panels=[
            PanelSpec(
                xlim=(-8.0, 4.0),
                ylim=(0.8, 2.0),
                xticks=[(-8.0, "-8"), (-6.0, "-6"), (-4.0, "-4"), (-2.0, "-2"), (0.0, "0"), (2.0, "2"), (4.0, "4")],
                yticks=[(v, f"{v:.1f}") for v in (0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0)],
                xlabel="R",
                ylabel="M−P−Y",
                zero_line=False,
                vlines=[(0.0, "", "solid")],
                legend_loc="none",
                lines=[
                    LineSeries(
                        x=x_pre,
                        y=y_pre,
                        color_idx=1,
                        marker="square",
                    ),
                    LineSeries(
                        x=x_post,
                        y=y_post,
                        color_idx=1,
                        marker="square",
                    ),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_5_4(mode: ThemeMode = "mono") -> str:
    xs_a = [1999.0 + i * 0.25 for i in range(28)]
    lp_a: list[float | None] = [
        0.029, 0.023, 0.020, 0.013,
        0.010, 0.005, 0.001, -0.003,
        -0.007, -0.005, -0.012, -0.016,
        -0.020, -0.018, -0.029, -0.033,
        -0.038, -0.042, -0.040, -0.043,
        -0.054, -0.055, -0.056, -0.057,
        -0.058, -0.065, -0.068, -0.075,
    ]
    vec_a: list[float | None] = [
        0.029, 0.034, 0.036, 0.033,
        0.024, 0.024, 0.023, 0.027,
        0.031, 0.052, 0.067, 0.074,
        0.060, 0.054, 0.047, 0.043,
        0.042, 0.051, 0.051, 0.052,
        0.054, 0.058, 0.056, 0.056,
        0.058, 0.063, 0.070, 0.079,
    ]

    xs_b = [2001.0 + i * 0.25 for i in range(20)]
    lp_b: list[float | None] = lp_a[8:]
    vec_b: list[float | None] = [
        -0.007, 0.005, 0.015, 0.019,
        0.007, 0.001, -0.008, -0.014,
        -0.019, -0.016, -0.020, -0.023,
        -0.024, -0.025, -0.030, -0.033,
        -0.035, -0.035, -0.034, -0.033,
    ]

    xs_c = [2003.0 + i * 0.25 for i in range(12)]
    lp_c: list[float | None] = [
        -0.038, -0.0425, -0.041, -0.044,
        -0.054, -0.055, -0.057, -0.058,
        -0.059, -0.066, -0.068, -0.076,
    ]
    vec_c: list[float | None] = [
        -0.038, -0.039, -0.0425, -0.046,
        -0.046, -0.050, -0.055, -0.057,
        -0.059, -0.059, -0.061, -0.063,
    ]

    spec = FigureSpec(
        fig_id="5-4",
        title="图 5-4 GDP 平减指数的样本外预测（基于误差修正模型的预测值（虚线）、实际值（实线））",
        rows=3,
        cols=1,
        width=860,
        height=760,
        panels=[
            PanelSpec(
                title="A 包含误差修正项的1975—1998模型",
                xlim=(1998.6, 2006.0),
                ylim=(-0.08, 0.08),
                xticks=[(y + 0.5, str(y)) for y in range(1999, 2006)],
                yticks=[(v / 100, f"{v / 100:.2f}") for v in range(-8, 9, 2)],
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs_a, y=lp_a, label="LP", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs_a, y=vec_a, label="VEC", color_idx=1, style="dotted", width=2.4),
                ],
            ),
            PanelSpec(
                title="B 包含误差修正项的1975—2000模型",
                xlim=(2000.6, 2006.0),
                ylim=(-0.08, 0.02),
                xticks=[(y + 0.5, str(y)) for y in range(2001, 2006)],
                yticks=[(v / 100, f"{v / 100:.2f}") for v in range(-8, 3, 2)],
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs_b, y=lp_b, label="LP", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs_b, y=vec_b, label="VEC", color_idx=1, style="dotted", width=2.4),
                ],
            ),
            PanelSpec(
                title="C 包含误差修正项的1975—2002模型",
                xlim=(2002.6, 2006.0),
                ylim=(-0.080, -0.035),
                xticks=[(2003.5, "2003"), (2004.5, "2004"), (2005.5, "2005")],
                yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(-80, -34, 5)],
                xlabel="年",
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs_c, y=lp_c, label="LP", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs_c, y=vec_c, label="VEC", color_idx=1, style="dotted", width=2.4),
                ],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def fig_5_5(mode: ThemeMode = "mono") -> str:
    xs_b = [2001.0 + i * 0.25 for i in range(20)]
    lp_b: list[float | None] = [
        -0.007, -0.005, -0.012, -0.016,
        -0.020, -0.018, -0.029, -0.033,
        -0.038, -0.042, -0.040, -0.043,
        -0.054, -0.055, -0.056, -0.057,
        -0.058, -0.065, -0.068, -0.075,
    ]
    vec_b: list[float | None] = [
        -0.007, 0.005, 0.015, 0.019,
        0.007, 0.001, -0.008, -0.014,
        -0.019, -0.016, -0.020, -0.023,
        -0.024, -0.025, -0.030, -0.033,
        -0.035, -0.035, -0.034, -0.033,
    ]
    var1_b: list[float | None] = [
        -0.007, -0.001, 0.001, -0.002,
        -0.018, -0.026, -0.032, -0.036,
        -0.041, -0.039, -0.043, -0.047,
        -0.048, -0.050, -0.056, -0.059,
        -0.060, -0.060, -0.061, -0.064,
    ]
    var2_b: list[float | None] = [
        -0.007, -0.004, -0.004, -0.007,
        -0.019, -0.026, -0.032, -0.036,
        -0.040, -0.041, -0.045, -0.047,
        -0.048, -0.050, -0.055, -0.056,
        -0.057, -0.057, -0.059, -0.062,
    ]

    xs_c = [2003.0 + i * 0.25 for i in range(12)]
    lp_c: list[float | None] = [
        -0.038, -0.0425, -0.041, -0.044,
        -0.054, -0.055, -0.057, -0.058,
        -0.059, -0.066, -0.068, -0.076,
    ]
    vec_c: list[float | None] = [
        -0.038, -0.039, -0.0425, -0.046,
        -0.046, -0.050, -0.055, -0.057,
        -0.059, -0.059, -0.061, -0.063,
    ]
    var1_c: list[float | None] = [
        -0.038, -0.0385, -0.0425, -0.046,
        -0.046, -0.050, -0.0555, -0.057,
        -0.058, -0.058, -0.061, -0.064,
    ]
    var2_c: list[float | None] = [
        -0.038, -0.039, -0.0425, -0.0455,
        -0.045, -0.049, -0.053, -0.0535,
        -0.055, -0.0545, -0.058, -0.060,
    ]

    spec = FigureSpec(
        fig_id="5-5",
        title="图 5-5 GDP 平减指数的样本外预测（基于误差修正模型和 VAR 模型的预测值（虚线）和实际值（实线））",
        rows=2,
        cols=1,
        width=860,
        height=600,
        panels=[
            PanelSpec(
                title="B 1975—2000模型：VEC、VAR1、VAR2",
                xlim=(2000.6, 2006.0),
                ylim=(-0.08, 0.02),
                xticks=[(y + 0.5, str(y)) for y in range(2001, 2006)],
                yticks=[(v / 100, f"{v / 100:.2f}") for v in range(-8, 3, 2)],
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs_b, y=lp_b, label="LP", color_idx=5, style="solid", width=2.2, fixed_style=True),
                    LineSeries(x=xs_b, y=vec_b, label="VEC", color_idx=1, style="dotted", width=2.3),
                    LineSeries(x=xs_b, y=var1_b, label="VAR1", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs_b, y=var2_b, label="VAR2", color_idx=3, style="dashed", width=2.2),
                ],
            ),
            PanelSpec(
                title="C 1975—2002模型：VEC、VAR1、VAR2",
                xlim=(2002.6, 2006.0),
                ylim=(-0.080, -0.035),
                xticks=[(2003.5, "2003"), (2004.5, "2004"), (2005.5, "2005")],
                yticks=[(v / 1000, f"{v / 1000:.3f}") for v in range(-80, -34, 5)],
                xlabel="年",
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs_c, y=lp_c, label="LP", color_idx=5, style="solid", width=2.2, fixed_style=True),
                    LineSeries(x=xs_c, y=vec_c, label="VEC", color_idx=1, style="dotted", width=2.3),
                    LineSeries(x=xs_c, y=var1_c, label="VAR1", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs_c, y=var2_c, label="VAR2", color_idx=3, style="dashed", width=2.2),
                ],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def fig_5_6(mode: ThemeMode = "mono") -> str:
    xs = [1975.0 + i * 0.25 for i in range(124)]
    vel_anchors = [
        (1975.0, -1.12),
        (1976.0, -1.13),
        (1977.25, -1.05),
        (1979.25, -1.08),
        (1980.75, -0.94),
        (1982.5, -0.98),
        (1985.5, -0.90),
        (1987.25, -1.00),
        (1989.0, -1.00),
        (1991.0, -0.88),
        (1992.5, -0.92),
        (1995.0, -1.04),
        (1996.0, -1.17),
        (1998.0, -1.32),
        (1999.5, -1.50),
        (2000.75, -1.54),
        (2001.5, -1.68),
        (2002.75, -1.78),
        (2004.5, -1.84),
        (2005.75, -1.89),
    ]
    velhat_anchors = [
        (1975.0, 0.26),
        (1976.25, 0.20),
        (1978.5, 0.15),
        (1980.25, 0.26),
        (1981.5, 0.20),
        (1985.75, 0.20),
        (1987.25, 0.13),
        (1989.0, 0.16),
        (1991.0, 0.22),
        (1993.5, 0.10),
        (1995.0, 0.08),
        (1995.75, -0.07),
        (1998.25, -0.08),
        (1999.25, -0.35),
        (2000.25, -0.37),
        (2000.75, -0.14),
        (2001.25, -0.42),
        (2002.0, -0.68),
        (2002.5, -0.58),
        (2003.0, -0.68),
        (2004.0, -0.73),
        (2005.0, -0.66),
        (2005.75, -0.69),
    ]

    def interp(xv: float, pts: list[tuple[float, float]]) -> float:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    vel_y: list[float | None] = [interp(x, vel_anchors) for x in xs]
    velhat_y: list[float | None] = [interp(x, velhat_anchors) for x in xs]

    spec = FigureSpec(
        fig_id="5-6",
        title="图 5-6 流通速度、1975—2005（实际值（Y+P−M、实线）、估算值（1.0∗R、虚线））",
        width=860,
        height=480,
        panels=[
            PanelSpec(
                xlim=(1974.5, 2006.2),
                ylim=(-2.0, -0.8),
                xticks=[(float(y), str(y)) for y in range(1975, 2006, 3)],
                yticks=[-2.0, -1.8, -1.6, -1.4, -1.2, -1.0, -0.8],
                y2lim=(-0.8, 0.4),
                y2ticks=[-0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4],
                xlabel="年",
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=vel_y, label="VEL", color_idx=0, style="solid", width=2.5),
                    LineSeries(
                        x=xs,
                        y=velhat_y,
                        label="VELHAT",
                        color_idx=1,
                        style="dotted",
                        width=2.4,
                        axis="y2",
                    ),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_1(mode: ThemeMode = "mono") -> str:
    pal = get_palette(mode)
    W, H = 860, 290
    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="{pal.bg}"/>',
        (
            f'<text x="{W / 2:.1f}" y="34" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="16.5" font-weight="700" fill="{pal.fg}">图 6-1 住房贷款的作用</text>'
        ),
    ]
    accounts = [
        ("有住房贷款家庭", "房屋", "住房贷款", 0),
        ("金融机构", "住房贷款", "存款", 1),
        ("无住房贷款家庭", "存款", "", 2),
    ]
    col_w = 236.0
    gap = 38.0
    start_x = (W - (3 * col_w + 2 * gap)) / 2.0
    top_y = 74.0
    t_line_y = 118.0
    bot_y = 232.0

    for i, (header, asset_txt, liab_txt, c_idx) in enumerate(accounts):
        x0 = start_x + i * (col_w + gap)
        xm = x0 + col_w / 2.0
        x1 = x0 + col_w
        accent = pal.series[c_idx % len(pal.series)] if mode != "mono" else pal.axis
        card_fill = pal.panel_bg if mode != "mono" else pal.bg
        out.append(
            f'<rect x="{x0:.1f}" y="{top_y:.1f}" width="{col_w:.1f}" height="{bot_y - top_y + 16:.1f}" '
            f'rx="6" fill="{card_fill}" stroke="{pal.border}" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{xm:.1f}" y="{top_y + 29:.1f}" text-anchor="middle" font-family="{FONT_STACK}" '
            f'font-size="16" font-weight="700" fill="{pal.fg}">{escape(header)}</text>'
        )
        out.append(
            f'<line x1="{x0 + 14:.1f}" y1="{t_line_y:.1f}" x2="{x1 - 14:.1f}" y2="{t_line_y:.1f}" '
            f'stroke="{accent}" stroke-width="2.2"/>'
        )
        out.append(
            f'<line x1="{xm:.1f}" y1="{t_line_y:.1f}" x2="{xm:.1f}" y2="{bot_y:.1f}" '
            f'stroke="{accent}" stroke-width="2.2"/>'
        )
        if asset_txt:
            out.append(
                f'<text x="{x0 + 24:.1f}" y="{t_line_y + 48:.1f}" font-family="{FONT_STACK}" '
                f'font-size="15.5" font-weight="600" fill="{pal.fg}">{escape(asset_txt)}</text>'
            )
        if liab_txt:
            out.append(
                f'<text x="{xm + 14:.1f}" y="{t_line_y + 48:.1f}" font-family="{FONT_STACK}" '
                f'font-size="15.5" font-weight="600" fill="{pal.fg}">{escape(liab_txt)}</text>'
            )

    out.append("</svg>")
    return "\n".join(out)


def _survey_quarters_1982_2004() -> tuple[list[float], list[tuple[float, str]]]:
    xs = [1982.5 + i * 0.25 for i in range(88)]
    xticks = [
        (1982.5, "1982-6"),
        (1984.0, "1983-12"),
        (1985.5, "1985-6"),
        (1987.0, "1986-12"),
        (1988.5, "1988-6"),
        (1990.0, "1989-12"),
        (1991.5, "1991-6"),
        (1993.0, "1992-12"),
        (1994.5, "1994-6"),
        (1996.0, "1995-12"),
        (1997.5, "1997-6"),
        (1999.0, "1998-12"),
        (2000.5, "2000-6"),
        (2002.0, "2001-12"),
        (2003.5, "2003-6"),
    ]
    return xs, xticks


def _base_inflation_index_series(xs: list[float]) -> list[float]:
    anchors = [
        (1982.5, 79.0),
        (1983.0, 77.0),
        (1983.5, 65.0),
        (1984.0, 65.0),
        (1984.25, 72.0),
        (1984.5, 65.0),
        (1985.5, 59.0),
        (1986.25, 53.0),
        (1986.5, 44.0),
        (1987.0, 43.0),
        (1987.25, 52.0),
        (1987.5, 40.0),
        (1987.75, 51.0),
        (1988.0, 42.0),
        (1988.5, 45.0),
        (1989.0, 56.0),
        (1989.25, 80.0),
        (1989.5, 81.0),
        (1989.75, 69.0),
        (1990.0, 68.0),
        (1990.25, 76.0),
        (1990.5, 71.0),
        (1990.75, 82.0),
        (1991.0, 78.0),
        (1991.5, 67.0),
        (1991.75, 67.0),
        (1992.0, 72.0),
        (1992.25, 65.0),
        (1992.75, 58.0),
        (1993.5, 42.0),
        (1993.75, 54.0),
        (1994.0, 54.0),
        (1994.25, 69.0),
        (1994.5, 46.0),
        (1994.75, 45.0),
        (1995.0, 38.0),
        (1995.25, 38.0),
        (1995.5, 30.0),
        (1996.0, 33.0),
        (1996.5, 41.0),
        (1997.0, 62.0),
        (1997.25, 81.0),
        (1997.75, 47.0),
        (1998.0, 44.0),
        (1998.5, 36.0),
        (1998.75, 38.0),
        (1999.0, 35.0),
        (1999.25, 22.0),
        (1999.5, 22.0),
        (1999.75, 32.0),
        (2000.0, 31.0),
        (2000.5, 21.0),
        (2000.75, 26.0),
        (2001.0, 24.0),
        (2001.5, 5.5),
        (2001.75, 6.0),
        (2002.0, 1.5),
        (2002.25, 6.5),
        (2002.5, 14.0),
        (2002.75, 8.5),
        (2003.0, 15.0),
        (2003.25, 25.5),
        (2003.5, 22.0),
        (2003.75, 36.0),
        (2004.0, 29.0),
        (2004.25, 33.0),
    ]

    def interp(xv: float) -> float:
        for i in range(len(anchors) - 1):
            x0, y0 = anchors[i]
            x1, y1 = anchors[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return anchors[-1][1]

    return [interp(x) for x in xs]


def fig_6_2(mode: ThemeMode = "mono") -> str:
    xs, xticks = _survey_quarters_1982_2004()
    base = _base_inflation_index_series(xs)
    with_loan: list[float | None] = []
    no_loan: list[float | None] = []
    for x, v in zip(xs, base):
        if abs(x - 1992.5) < 1e-6 or abs(x - 1997.5) < 1e-6:
            with_loan.append(None)
            no_loan.append(None)
        else:
            with_loan.append(v)
            offset = -2.2 if x < 1991.0 else (2.4 if x < 1997.0 else 1.6)
            no_loan.append(max(0.5, v + offset))

    spec = FigureSpec(
        fig_id="6-2",
        title="图 6-2 《消费动向调查》的“通货膨胀预期”（“上升”－“下降”）（有无住房贷款）",
        width=880,
        height=480,
        panels=[
            PanelSpec(
                xlim=(1982.5, 2004.25),
                ylim=(0.0, 90.0),
                xticks=xticks,
                yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=with_loan, label="有贷款", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs, y=no_loan, label="无贷款", color_idx=1, style="dotted", width=2.2),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _survey_gaps(values: list[float]) -> list[float | None]:
    out: list[float | None] = list(values)
    out.insert(40, None)
    out.insert(60, None)
    return out


def fig_6_3(mode: ThemeMode = "mono") -> str:
    xs, xticks = _survey_quarters_1982_2004()
    y_young = _survey_gaps([
        78, 77, 73, 70, 60, 59, 58, 67, 53, 56, 55, 53, 55, 58, 57, 52, 49, 49, 51, 50,
        46, 43, 44, 37, 42, 37, 41, 70, 72, 56, 53, 60, 49, 78, 64, 47, 48, 61, 50, 50,
        51, 49, 40, 27, 45, 47, 66, 32, 31, 26, 18, 22, 18, 19, 28, 34, 45, 55, 72,
        37, 43, 28, 42, 38, 30, 20, 18, 28, 20, 12, 17, 20, 27, 21, 13, 21, 21, 4, 23,
        18, 28, 35, 25, 28, 19, 27,
    ])
    y_mid = _survey_gaps([
        79, 77, 72, 65, 65, 66, 66, 68, 64, 62, 61, 59, 58, 57, 58, 53, 48, 45, 46, 49,
        44, 46, 43, 38, 43, 45, 52, 72, 73, 68, 67, 72, 71, 79, 78, 71, 66, 68, 72, 66,
        60, 55, 45, 40, 54, 58, 67, 46, 44, 38, 35, 33, 30, 33, 34, 40, 50, 62, 79,
        49, 46, 41, 38, 38, 35, 24, 22, 30, 29, 22, 18, 18, 22, 15, 7, 5, 3, 6, 13,
        12, 22, 27, 25, 27, 29, 30,
    ])
    y_old = _survey_gaps([
        78, 76, 73, 62, 61, 65, 65, 71, 61, 61, 60, 60, 57, 57, 57, 54, 50, 38, 40, 46,
        40, 49, 43, 37, 40, 53, 57, 77, 79, 71, 68, 74, 72, 82, 81, 73, 72, 73, 77, 69,
        65, 60, 52, 48, 60, 62, 70, 53, 47, 38, 41, 37, 36, 34, 33, 40, 52, 63, 82,
        52, 44, 38, 38, 39, 33, 24, 25, 35, 32, 26, 22, 23, 25, 11, 6, 5, 2, 6, 13,
        10, 13, 21, 18, 36, 30, 32,
    ])

    spec = FigureSpec(
        fig_id="6-3",
        title="图 6-3 《消费动向调查》的“通货膨胀预期”（“上升”－“下降”）（各年龄组）",
        width=880,
        height=480,
        panels=[
            PanelSpec(
                xlim=(1982.5, 2004.25),
                ylim=(0.0, 90.0),
                xticks=xticks,
                yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=y_young, label="29岁以下", color_idx=2, style="solid", width=2.1),
                    LineSeries(x=xs, y=y_mid, label="30~59岁", color_idx=1, style="dotted", width=2.2),
                    LineSeries(x=xs, y=y_old, label="60岁以上", color_idx=0, style="solid", width=2.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_4(mode: ThemeMode = "mono") -> str:
    xs, xticks = _survey_quarters_1982_2004()
    y_low_inc = _survey_gaps([
        82, 79, 75, 67, 66, 66, 66, 71, 65, 64, 63, 61, 60, 60, 58, 54, 49, 48, 48, 53,
        47, 51, 45, 43, 46, 54, 60, 76, 78, 69, 68, 72, 75, 82, 78, 74, 68, 70, 75, 69,
        64, 59, 54, 50, 60, 63, 72, 54, 50, 45, 44, 40, 40, 38, 39, 45, 52, 63, 80,
        53, 52, 47, 43, 45, 40, 26, 27, 34, 36, 30, 25, 26, 29, 12, 14, 15, 12, 12, 16,
        18, 19, 27, 27, 38, 33, 35,
    ])
    y_high_inc = _survey_gaps([
        78, 78, 72, 65, 63, 64, 63, 69, 63, 62, 61, 60, 58, 56, 52, 48, 43, 37, 41, 44,
        40, 48, 42, 40, 42, 52, 58, 76, 82, 73, 72, 77, 73, 85, 83, 74, 67, 66, 69, 65,
        54, 47, 41, 36, 48, 53, 70, 44, 40, 34, 33, 27, 29, 28, 31, 36, 44, 55, 81,
        43, 40, 35, 32, 33, 28, 19, 17, 26, 27, 23, 17, 22, 17, 6, -1, -5, -8, 0, 6,
        4, 6, 16, 16, 27, 26, 28,
    ])

    spec = FigureSpec(
        fig_id="6-4",
        title="图 6-4 《消费动向调查》的“通货膨胀预期”（“上升”－“下降”）（各收入组）",
        width=880,
        height=480,
        panels=[
            PanelSpec(
                xlim=(1982.5, 2004.25),
                ylim=(-20.0, 100.0),
                xticks=xticks,
                yticks=[-20, 0, 20, 40, 60, 80, 100],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=y_low_inc, label="550万日元以下", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs, y=y_high_inc, label="551万日元以上", color_idx=1, style="dotted", width=2.3),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _threshold_quarters_1985_2003() -> tuple[list[float], list[tuple[float, str]]]:
    xs = [1986.0 + i * 0.25 for i in range(73)]
    xticks = [(float(y), f"{y - 1}-12") for y in range(1986, 2005, 2)]
    return xs, xticks


def _build_threshold_series(xs: list[float], no_loan: bool) -> tuple[list[float], list[float], list[float], list[float]]:
    a_anchors = [
        (1986.0, -0.0055),
        (1986.25, -0.0033),
        (1986.75, -0.0044),
        (1987.25, -0.0044),
        (1988.0, -0.0018),
        (1989.25, -0.0014),
        (1990.0, -0.0020),
        (1995.5, -0.0024),
        (1997.25, -0.0014),
        (1998.0, -0.0007),
        (1998.75, -0.0018),
        (2000.0, -0.0012),
        (2003.25, -0.0011),
        (2004.0, -0.0006),
    ]
    b_anchors = [
        (1986.0, -0.0255 if no_loan else -0.0242),
        (1986.25, -0.0158),
        (1986.75, -0.0205 if no_loan else -0.0185),
        (1987.25, -0.0202 if no_loan else -0.0182),
        (1987.5, -0.0125 if no_loan else -0.0112),
        (1988.25, -0.0064 if no_loan else -0.0066),
        (1989.25, -0.0082 if no_loan else -0.0080),
        (1989.5, -0.0198 if no_loan else -0.0175),
        (1990.0, -0.0185 if no_loan else -0.0168),
        (1990.75, -0.0102 if no_loan else -0.0095),
        (1991.0, -0.0116 if no_loan else -0.0105),
        (1991.75, -0.0106 if no_loan else -0.0096),
        (1992.0, -0.0064 if no_loan else -0.0071),
        (1993.5, -0.0074 if no_loan else -0.0079),
        (1994.5, -0.0061 if no_loan else -0.0068),
        (1995.25, -0.0058 if no_loan else -0.0064),
        (1995.5, -0.0071 if no_loan else -0.0075),
        (1996.5, -0.0023 if no_loan else -0.0036),
        (1997.25, -0.0040 if no_loan else -0.0042),
        (1997.5, -0.0076 if no_loan else -0.0066),
        (1998.0, -0.0074 if no_loan else -0.0064),
        (1998.5, -0.0114 if no_loan else -0.0108),
        (1999.0, -0.0112 if no_loan else -0.0106),
        (1999.75, -0.0057 if no_loan else -0.0063),
        (2000.75, -0.0036 if no_loan else -0.0047),
        (2001.0, -0.0044 if no_loan else -0.0053),
        (2002.0, -0.0012 if no_loan else -0.0020),
        (2003.25, 0.0004 if no_loan else -0.0009),
        (2004.0, 0.0021 if no_loan else -0.0001),
    ]

    def interp(xv: float, pts: list[tuple[float, float]]) -> float:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    a_vals = [interp(x, a_anchors) for x in xs]
    b_vals = [interp(x, b_anchors) for x in xs]
    a_se = [0.00028] * len(xs)
    b_se = [0.00145 if no_loan else 0.00125] * len(xs)
    return a_vals, a_se, b_vals, b_se


def fig_6_5(mode: ThemeMode = "mono") -> str:
    xs, xticks = _threshold_quarters_1985_2003()
    a_vals, a_se, b_vals, b_se = _build_threshold_series(xs, no_loan=False)
    spec = FigureSpec(
        fig_id="6-5",
        title="图 6-5 预期阈值的变化（有住房贷款家庭）",
        note="注：1. a、b 分别表示预期的下限和上限阈值。2. 除阈值估算值外，还表示±1 标准偏差值。",
        width=880,
        height=500,
        panels=[
            PanelSpec(
                xlim=(1986.0, 2004.0),
                ylim=(-0.03, 0.005),
                xticks=xticks,
                yticks=[(v / 1000, f"{v / 1000:g}") for v in range(-30, 6, 5)],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=[b - s for b, s in zip(b_vals, b_se)], label="b-s.e", color_idx=2, style="dotted", width=1.6),
                    LineSeries(x=xs, y=b_vals, label="b", color_idx=1, style="solid", width=2.3),
                    LineSeries(x=xs, y=[b + s for b, s in zip(b_vals, b_se)], label="b+s.e", color_idx=2, style="dashed", width=1.6),
                    LineSeries(x=xs, y=[a - s for a, s in zip(a_vals, a_se)], label="a-s.e", color_idx=3, style="solid", width=1.4),
                    LineSeries(x=xs, y=a_vals, label="a", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs, y=[a + s for a, s in zip(a_vals, a_se)], label="a+s.e", color_idx=3, style="dotted", width=1.5),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_6(mode: ThemeMode = "mono") -> str:
    xs, xticks = _threshold_quarters_1985_2003()
    a_vals, a_se, b_vals, b_se = _build_threshold_series(xs, no_loan=True)
    spec = FigureSpec(
        fig_id="6-6",
        title="图 6-6 预期阈值的变化（无住房贷款家庭）",
        note="注：1. a、b 分别表示预期的下限和上限阈值。2. 除阈值估算值外，还表示±1 标准偏差值。",
        width=880,
        height=500,
        panels=[
            PanelSpec(
                xlim=(1986.0, 2004.0),
                ylim=(-0.03, 0.005),
                xticks=xticks,
                yticks=[(v / 1000, f"{v / 1000:g}") for v in range(-30, 6, 5)],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=[b - s for b, s in zip(b_vals, b_se)], label="b-s.e", color_idx=2, style="dotted", width=1.6),
                    LineSeries(x=xs, y=b_vals, label="b", color_idx=1, style="solid", width=2.3),
                    LineSeries(x=xs, y=[b + s for b, s in zip(b_vals, b_se)], label="b+s.e", color_idx=2, style="dashed", width=1.6),
                    LineSeries(x=xs, y=[a - s for a, s in zip(a_vals, a_se)], label="a-s.e", color_idx=3, style="solid", width=1.4),
                    LineSeries(x=xs, y=a_vals, label="a", color_idx=0, style="solid", width=2.4),
                    LineSeries(x=xs, y=[a + s for a, s in zip(a_vals, a_se)], label="a+s.e", color_idx=3, style="dotted", width=1.5),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_7(mode: ThemeMode = "mono") -> str:
    xs, xticks = _threshold_quarters_1985_2003()
    actual_anchors = [
        (1986.0, 0.013),
        (1986.25, 0.015),
        (1987.0, 0.004),
        (1987.25, -0.001),
        (1987.75, 0.005),
        (1988.25, 0.006),
        (1988.75, 0.003),
        (1989.25, 0.009),
        (1989.5, 0.027),
        (1990.25, 0.031),
        (1990.5, 0.021),
        (1991.0, 0.030),
        (1991.75, 0.029),
        (1992.25, 0.021),
        (1992.5, 0.025),
        (1993.0, 0.021),
        (1993.5, 0.013),
        (1994.25, 0.009),
        (1995.0, 0.004),
        (1995.5, -0.003),
        (1996.0, 0.000),
        (1997.25, 0.004),
        (1997.5, 0.020),
        (1998.0, 0.023),
        (1998.25, 0.019),
        (1998.5, 0.000),
        (1999.0, -0.003),
        (1999.75, 0.000),
        (2000.75, -0.003),
        (2001.5, -0.009),
        (2002.75, -0.009),
        (2003.25, -0.007),
        (2003.75, -0.001),
        (2004.0, 0.000),
    ]
    exp_anchors = [
        (1986.0, 0.007),
        (1986.25, 0.016),
        (1986.5, 0.014),
        (1987.0, 0.004),
        (1987.25, -0.008),
        (1987.5, -0.007),
        (1987.75, 0.001),
        (1988.25, 0.006),
        (1988.75, 0.001),
        (1989.0, 0.005),
        (1989.25, -0.005),
        (1989.5, 0.030),
        (1990.0, 0.034),
        (1990.25, 0.045),
        (1990.5, 0.027),
        (1990.75, 0.018),
        (1991.0, 0.034),
        (1991.5, 0.029),
        (1991.75, 0.038),
        (1992.25, 0.016),
        (1992.5, 0.028),
        (1993.0, 0.022),
        (1993.5, 0.013),
        (1994.25, 0.007),
        (1994.5, 0.010),
        (1995.0, 0.003),
        (1995.25, 0.006),
        (1995.5, -0.008),
        (1996.0, -0.002),
        (1996.25, -0.004),
        (1996.5, 0.000),
        (1997.0, 0.002),
        (1997.25, -0.012),
        (1997.5, 0.018),
        (1998.0, 0.026),
        (1998.25, 0.036),
        (1998.5, 0.001),
        (1999.0, -0.009),
        (1999.25, -0.004),
        (1999.75, 0.000),
        (2000.0, -0.004),
        (2000.75, -0.001),
        (2001.0, -0.008),
        (2001.5, -0.012),
        (2002.25, -0.008),
        (2002.75, -0.011),
        (2003.25, -0.011),
        (2003.75, -0.002),
        (2004.0, -0.001),
    ]

    def interp(xv: float, pts: list[tuple[float, float]]) -> float:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    act_y: list[float | None] = [interp(x, actual_anchors) for x in xs]
    with_y: list[float | None] = [interp(x, exp_anchors) for x in xs]
    all_y: list[float | None] = [v - 0.0004 if v is not None else None for v in with_y]
    no_y: list[float | None] = [v + 0.0005 if v is not None else None for v in with_y]

    spec = FigureSpec(
        fig_id="6-7",
        title="图 6-7 预期通货膨胀率（基于可变参数模型测算）",
        width=880,
        height=490,
        panels=[
            PanelSpec(
                xlim=(1986.0, 2004.0),
                ylim=(-0.02, 0.05),
                xticks=xticks,
                yticks=[(v / 100, f"{v / 100:.2f}") for v in range(-2, 6)],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=act_y, label="通货膨胀率", color_idx=2, style="solid", width=2.4),
                    LineSeries(x=xs, y=all_y, label="全部", color_idx=1, style="dashed", width=2.0),
                    LineSeries(x=xs, y=with_y, label="有贷款", color_idx=0, style="solid", width=2.3),
                    LineSeries(x=xs, y=no_y, label="无贷款", color_idx=3, style="dotted", width=2.0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_8(mode: ThemeMode = "mono") -> str:
    xs = [1983.5 + i * 0.25 for i in range(83)]
    xticks = [(float(y), f"{y - 1}-12") for y in range(1983, 2005, 2)]
    act_anchors = [
        (1983.5, 0.019),
        (1983.75, 0.014),
        (1984.75, 0.023),
        (1985.75, 0.020),
        (1986.25, 0.015),
        (1987.25, -0.001),
        (1988.0, 0.005),
        (1988.75, 0.003),
        (1989.5, 0.027),
        (1990.25, 0.031),
        (1990.5, 0.021),
        (1991.0, 0.030),
        (1991.75, 0.029),
        (1992.25, 0.021),
        (1992.5, 0.025),
        (1993.5, 0.013),
        (1995.0, 0.004),
        (1995.5, -0.003),
        (1997.25, 0.004),
        (1997.5, 0.020),
        (1998.0, 0.023),
        (1998.5, 0.000),
        (1999.0, -0.003),
        (2000.75, -0.003),
        (2001.5, -0.009),
        (2002.75, -0.009),
        (2003.75, -0.001),
        (2004.0, 0.000),
    ]
    cp_anchors = [
        (1983.5, 0.035),
        (1983.9, 0.030),
        (1984.25, 0.038),
        (1985.0, 0.037),
        (1986.0, 0.025),
        (1987.25, 0.010),
        (1987.75, 0.015),
        (1988.5, 0.013),
        (1989.0, 0.019),
        (1989.5, 0.048),
        (1990.0, 0.044),
        (1990.25, 0.052),
        (1990.5, 0.037),
        (1991.0, 0.051),
        (1991.5, 0.044),
        (1992.25, 0.037),
        (1992.75, 0.035),
        (1993.5, 0.023),
        (1994.25, 0.028),
        (1995.5, 0.004),
        (1996.5, 0.012),
        (1997.25, 0.028),
        (1997.75, 0.033),
        (1998.25, 0.026),
        (1998.5, 0.009),
        (1999.5, 0.003),
        (1999.75, 0.006),
        (2000.5, 0.002),
        (2001.5, -0.008),
        (2002.5, -0.007),
        (2003.5, 0.006),
        (2004.0, 0.007),
    ]

    def interp(xv: float, pts: list[tuple[float, float]]) -> float:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    act_y: list[float | None] = [interp(x, act_anchors) for x in xs]
    with_y: list[float | None] = []
    all_y: list[float | None] = []
    no_y: list[float | None] = []
    for x in xs:
        if abs(x - 1992.5) < 1e-6 or abs(x - 1997.5) < 1e-6:
            with_y.append(None)
            all_y.append(None)
            no_y.append(None)
        else:
            v = interp(x, cp_anchors)
            with_y.append(v)
            all_y.append(v - 0.0006)
            no_y.append(v - 0.0010)

    spec = FigureSpec(
        fig_id="6-8",
        title="图 6-8 预期通货膨胀率（基于 Carlson-Parkin 法测算）",
        width=880,
        height=490,
        panels=[
            PanelSpec(
                xlim=(1983.0, 2004.0),
                ylim=(-0.02, 0.06),
                xticks=xticks,
                yticks=[(v / 100, f"{v / 100:.2f}") for v in range(-2, 7)],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=act_y, label="通货膨胀率", color_idx=2, style="solid", width=2.4),
                    LineSeries(x=xs, y=all_y, label="全部", color_idx=1, style="dashed", width=2.0),
                    LineSeries(x=xs, y=with_y, label="有贷款", color_idx=0, style="solid", width=2.3),
                    LineSeries(x=xs, y=no_y, label="无贷款", color_idx=3, style="dotted", width=2.0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_9(mode: ThemeMode = "mono") -> str:
    xs, xticks = _threshold_quarters_1985_2003()
    diff_anchors = [
        (1986.0, -0.00005),
        (1986.25, -0.00104),
        (1986.5, 0.00002),
        (1987.0, 0.00064),
        (1987.25, -0.00081),
        (1987.5, 0.00036),
        (1987.75, 0.00001),
        (1988.0, 0.00037),
        (1988.5, 0.00005),
        (1989.0, 0.00044),
        (1989.25, 0.00015),
        (1989.5, 0.00037),
        (1989.75, -0.00055),
        (1990.0, 0.00183),
        (1990.25, -0.00052),
        (1990.5, 0.00032),
        (1990.75, -0.00148),
        (1991.0, 0.00049),
        (1991.5, -0.00051),
        (1991.75, -0.00071),
        (1992.0, -0.00046),
        (1992.5, -0.00045),
        (1992.75, -0.00058),
        (1993.0, -0.00013),
        (1993.25, -0.00019),
        (1993.5, -0.00046),
        (1993.75, -0.00001),
        (1994.25, -0.00029),
        (1994.5, 0.00002),
        (1994.75, -0.00025),
        (1995.0, -0.00016),
        (1995.25, -0.00035),
        (1995.75, -0.00009),
        (1996.25, -0.00001),
        (1997.0, 0.00054),
        (1997.25, 0.00019),
        (1998.0, 0.00033),
        (1998.25, 0.00025),
        (1998.5, 0.00004),
        (1999.0, 0.00014),
        (1999.75, 0.00001),
        (2000.5, 0.00006),
        (2001.0, -0.00019),
        (2001.25, -0.00022),
        (2001.75, -0.00042),
        (2002.25, -0.00016),
        (2002.5, -0.00022),
        (2003.0, 0.00008),
        (2003.25, -0.00001),
        (2003.5, 0.00031),
        (2003.75, 0.00019),
        (2004.0, 0.00024),
    ]

    def interp(xv: float) -> float:
        for i in range(len(diff_anchors) - 1):
            x0, y0 = diff_anchors[i]
            x1, y1 = diff_anchors[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return diff_anchors[-1][1]

    ys: list[float | None] = [interp(x) for x in xs]
    spec = FigureSpec(
        fig_id="6-9",
        title="图 6-9 预期通货膨胀率之差（有贷款－无贷款）",
        width=880,
        height=480,
        panels=[
            PanelSpec(
                xlim=(1986.0, 2004.0),
                ylim=(-0.0015, 0.0020),
                xticks=xticks,
                yticks=[
                    (-0.0015, "-0.0015"),
                    (-0.0010, "-0.001"),
                    (-0.0005, "-0.0005"),
                    (0.0, "0"),
                    (0.0005, "0.0005"),
                    (0.0010, "0.001"),
                    (0.0015, "0.0015"),
                    (0.0020, "0.002"),
                ],
                legend_loc="none",
                lines=[LineSeries(x=xs, y=ys, color_idx=0, style="solid", width=2.4)],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _err_and_cond_var(xs: list[float], no_loan: bool) -> tuple[list[float | None], list[float | None]]:
    err_anchors = [
        (1986.0, 0.0056),
        (1986.25, 0.0005),
        (1986.5, -0.0020),
        (1986.75, 0.0002),
        (1987.0, -0.0014),
        (1987.25, 0.0064),
        (1987.5, 0.0068),
        (1987.75, 0.0035),
        (1988.25, -0.0007),
        (1988.75, 0.0028),
        (1989.0, 0.0008),
        (1989.25, 0.0150),
        (1989.5, -0.0025),
        (1989.75, -0.0020),
        (1990.0, -0.0055),
        (1990.25, -0.0138 if no_loan else -0.0132),
        (1990.75, 0.0052),
        (1991.0, -0.0032),
        (1991.5, -0.0002),
        (1991.75, -0.0088),
        (1992.25, 0.0049),
        (1992.5, -0.0020),
        (1992.75, -0.0004),
        (1993.25, -0.0020),
        (1993.5, -0.0002),
        (1994.0, -0.0015),
        (1994.25, 0.0022),
        (1994.5, -0.0008),
        (1995.0, 0.0014),
        (1995.25, -0.0033),
        (1995.5, 0.0051),
        (1996.0, 0.0023),
        (1996.25, 0.0038),
        (1996.5, 0.0016),
        (1997.0, 0.0009),
        (1997.25, 0.0166),
        (1997.5, 0.0025),
        (1997.75, 0.0011),
        (1998.0, -0.0042),
        (1998.25, -0.0171),
        (1998.5, -0.0012),
        (1999.0, 0.0059),
        (1999.25, 0.0032),
        (1999.5, 0.0031),
        (1999.75, 0.0002),
        (2000.0, 0.0022),
        (2000.25, 0.0022),
        (2000.75, -0.0022),
        (2001.0, 0.0013),
        (2001.25, 0.0014),
        (2001.5, 0.0032),
        (2001.75, 0.0016),
        (2002.25, 0.0002),
        (2002.75, 0.0019),
        (2003.0, 0.0017),
        (2003.25, 0.0037),
        (2003.5, 0.0035),
        (2003.75, 0.0012),
        (2004.0, 0.0002),
    ]
    var_anchors = [
        (1986.0, 0.000024),
        (1986.25, 0.000029),
        (1986.75, 0.000022),
        (1987.0, 0.000020),
        (1987.25, 0.000024),
        (1987.5, 0.000020),
        (1988.75, 0.000020),
        (1989.0, 0.000046 if no_loan else 0.000043),
        (1989.5, 0.000022),
        (1989.75, 0.000020),
        (1990.0, 0.000026),
        (1990.25, 0.000020),
        (1990.5, 0.000031),
        (1990.75, 0.000021),
        (1991.5, 0.000020),
        (1991.75, 0.000023),
        (1992.0, 0.000020),
        (1993.5, 0.000020),
        (1994.0, 0.000023),
        (1994.25, 0.000020),
        (1995.25, 0.000021),
        (1996.25, 0.000019),
        (1996.75, 0.000022),
        (1997.0, 0.000043 if no_loan else 0.000036),
        (1997.25, 0.000021),
        (1998.75, 0.000019),
        (1999.0, 0.000021),
        (1999.5, 0.000020),
        (2000.75, 0.000020),
        (2001.25, 0.000022),
        (2002.25, 0.000020),
        (2002.5, 0.000021),
        (2003.0, 0.000019),
        (2004.0, 0.000019),
    ]

    def interp(xv: float, pts: list[tuple[float, float]]) -> float:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= xv <= x1:
                t = (xv - x0) / max(1e-9, x1 - x0)
                return y0 + t * (y1 - y0)
        return pts[-1][1]

    return [interp(x, err_anchors) for x in xs], [interp(x, var_anchors) for x in xs]


def fig_6_10(mode: ThemeMode = "mono") -> str:
    xs, xticks = _threshold_quarters_1985_2003()
    err_y, var_y = _err_and_cond_var(xs, no_loan=False)
    spec = FigureSpec(
        fig_id="6-10",
        title="图 6-10 预测误差与条件方差（有住房贷款家庭）",
        width=890,
        height=490,
        panels=[
            PanelSpec(
                xlim=(1986.0, 2004.0),
                ylim=(-0.02, 0.02),
                xticks=xticks,
                yticks=[(v / 1000, f"{v / 1000:g}") for v in range(-20, 21, 5)],
                y2lim=(0.0, 0.00005),
                y2ticks=[(v / 1e6, f"{v / 1e6:.6f}".rstrip("0").rstrip(".")) for v in range(0, 51, 5)],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=err_y, label="预测误差", color_idx=5, style="solid", width=2.2, fixed_style=True),
                    LineSeries(x=xs, y=var_y, label="条件方差", color_idx=0, style="solid", width=2.4, axis="y2"),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_11(mode: ThemeMode = "mono") -> str:
    xs, xticks = _threshold_quarters_1985_2003()
    err_y, var_y = _err_and_cond_var(xs, no_loan=True)
    spec = FigureSpec(
        fig_id="6-11",
        title="图 6-11 预测误差与条件方差（无住房贷款家庭）",
        width=890,
        height=490,
        panels=[
            PanelSpec(
                xlim=(1986.0, 2004.0),
                ylim=(-0.02, 0.02),
                xticks=xticks,
                yticks=[(v / 1000, f"{v / 1000:g}") for v in range(-20, 21, 5)],
                y2lim=(0.0, 0.00005),
                y2ticks=[(v / 1e5, f"{v / 1e5:.5f}".rstrip("0").rstrip(".")) for v in range(6)],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=err_y, label="预测误差", color_idx=0, style="solid", width=2.3),
                    LineSeries(x=xs, y=var_y, label="条件方差", color_idx=1, style="dotted", width=2.3, axis="y2"),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_12(mode: ThemeMode = "mono") -> str:
    xs = [1991.5 + i * 0.25 for i in range(52)]
    xticks = [(float(y) + 0.5, f"{y}-6") for y in range(1991, 2004)]
    with_loan: list[float | None] = [
        0.042, 0.003, 0.030, 0.009,
        None, 0.114, 0.007, 0.065,
        0.094, 0.095, 0.065, 0.106,
        0.073, 0.105, 0.042, -0.017,
        0.004, 0.039, 0.036, 0.058,
        0.084, 0.105, 0.111, 0.114,
        None, 0.148, 0.084, 0.063,
        0.092, 0.036, 0.071, 0.061,
        0.080, 0.069, 0.083, 0.102,
        0.029, 0.058, 0.019, -0.063,
        -0.067, -0.093, -0.071, -0.087,
        0.028, -0.068, -0.023, 0.012,
        0.037, 0.126, 0.111, 0.095,
    ]
    no_loan: list[float | None] = [
        0.060, 0.052, 0.085, 0.083,
        None, 0.090, 0.077, 0.087,
        0.095, 0.096, 0.060, 0.110,
        0.101, 0.047, 0.037, 0.011,
        0.036, 0.073, 0.078, 0.086,
        0.101, 0.090, 0.122, 0.132,
        None, 0.110, 0.086, 0.110,
        0.069, 0.063, 0.095, 0.087,
        0.108, 0.112, 0.098, 0.088,
        0.105, 0.103, 0.076, -0.050,
        0.013, -0.075, -0.057, 0.002,
        0.033, -0.022, 0.014, 0.034,
        0.059, 0.127, 0.150, 0.120,
    ]

    spec = FigureSpec(
        fig_id="6-12",
        title="图 6-12 “物价上升”和“资产价值增长”预期的关系（斯皮尔曼等级相关系数；■、▲表示统计学上的显著相关性）",
        note=(
            "注：1. ■表示有住房贷款家庭在5%显著性水平上拒绝显著性为零这一零假设的情况。 "
            "2. ▲表示无住房贷款家庭在5%显著性水平上拒绝显著性为零这一零假设的情况。"
        ),
        width=890,
        height=500,
        panels=[
            PanelSpec(
                xlim=(1991.5, 2004.25),
                ylim=(-0.10, 0.25),
                xticks=xticks,
                yticks=[-0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20],
                legend_loc="bottom",
                lines=[
                    LineSeries(
                        x=xs,
                        y=with_loan,
                        label="有贷款",
                        color_idx=0,
                        style="solid",
                        marker="square",
                        width=2.2,
                    ),
                    LineSeries(
                        x=xs,
                        y=no_loan,
                        label="无贷款",
                        color_idx=1,
                        style="dashed",
                        marker="triangle",
                        width=2.2,
                    ),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "4-1": fig_4_1,
        "4-2": fig_4_2,
        "4-3": fig_4_3,
        "4-4": fig_4_4,
        "4-5": fig_4_5,
        "4-6": fig_4_6,
        "4-7": fig_4_7,
        "5-1": fig_5_1,
        "5-2": fig_5_2,
        "5-3": fig_5_3,
        "5-4": fig_5_4,
        "5-5": fig_5_5,
        "5-6": fig_5_6,
        "6-1": fig_6_1,
        "6-2": fig_6_2,
        "6-3": fig_6_3,
        "6-4": fig_6_4,
        "6-5": fig_6_5,
        "6-6": fig_6_6,
        "6-7": fig_6_7,
        "6-8": fig_6_8,
        "6-9": fig_6_9,
        "6-10": fig_6_10,
        "6-11": fig_6_11,
        "6-12": fig_6_12,
    }
