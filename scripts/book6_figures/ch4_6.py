from __future__ import annotations

from collections.abc import Callable, Sequence

from scripts.book2_figures.engine import (
    Annotation,
    BandSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    render_figure_svg,
)

_PLACE = {
    "a": (0.0, -6.0, "middle"),
    "b": (0.0, 4.0, "middle"),
    "r": (9.0, 0.0, "start"),
    "l": (-9.0, 0.0, "end"),
    "rb": (8.0, 4.0, "start"),
    "lb": (-8.0, 4.0, "end"),
    "ra": (6.0, -6.0, "start"),
    "la": (-6.0, -6.0, "end"),
}


def _labels(points: Sequence[tuple[float, float, str, str]]) -> list[Annotation]:
    out = []
    for x, y, text, pos in points:
        dx, dy, align = _PLACE[pos]
        out.append(Annotation(x=x, y=y, text=text, dx=dx, dy=dy, arrow=False, align=align, fontsize=10.5))
    return out


def _years(a: int, b: int) -> list[float]:
    return [float(y) for y in range(a, b + 1)]


def _fig_4_1(mode: ThemeMode = "mono") -> str:
    ys = [1.3, 1.4, 1.9, 2.0, 2.0, 2.2, 2.1, 2.0, 2.2, 2.4, 2.6, 2.7, 2.6, 2.8, 2.8, 2.5, 2.3, 2.1, 2.1, 2.2,
          2.5, 2.9, 3.2, 3.4, 3.4, 4.1, 4.7, 4.7, 5.0, 5.4, 5.3, 4.7, 4.4, 4.1, 3.9]
    labels = [
        (1973, 1.3, "1.3", "ra"), (1978, 2.2, "2.2", "a"), (1980, 2.0, "2.0", "b"), (1984, 2.7, "2.7", "a"),
        (1987, 2.8, "2.8", "ra"), (1991, 2.1, "2.1", "b"), (1997, 3.4, "3.4", "b"), (1998, 4.1, "4.1", "rb"),
        (2000, 4.7, "4.7", "rb"), (2002, 5.4, "5.4", "a"), (2007, 3.9, "3.9", "lb"),
    ]
    panel = PanelSpec(
        xlim=(1972.5, 2007.5),
        ylim=(1.0, 6.0),
        xticks=[float(y) for y in range(1973, 2008, 2)],
        yticks=[(v / 2, f"{v / 2:.1f}") for v in range(2, 13)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[LineSeries(x=_years(1973, 2007), y=ys, color_idx=0, marker="diamond", width=1.8)],
        annotations=_labels(labels),
        legend_loc="none",
    )
    spec = FigureSpec(fig_id="4-1", title="图 4-1 完全失业率的变化（年平均）", panels=[panel], width=860, height=480)
    return render_figure_svg(spec, mode)


def _fig_4_2(mode: ThemeMode = "mono") -> str:
    over15 = [62.1, 61.6, 61.4, 61.1, 60.9, 61.1, 61.4, 61.9, 62.4, 62.6, 62.2, 61.8, 61.4, 61.4, 61.5, 60.7,
              59.9, 59.5, 59.0, 57.9, 57.6, 57.6, 57.7, 57.9, 58.1]
    age15_64 = [67.4, 67.3, 67.0, 66.8, 66.6, 66.9, 67.4, 68.0, 68.9, 69.6, 69.3, 69.2, 69.0, 69.2, 70.0, 69.4,
                68.9, 68.9, 68.8, 68.3, 68.4, 68.7, 69.3, 69.9, 70.7]
    labels = [
        (1983, 62.1, "62.1", "a"), (1992, 62.6, "62.6", "a"), (1997, 61.5, "61.5", "a"), (2002, 57.9, "57.9", "b"),
        (2007, 58.1, "58.1", "a"), (1983, 67.4, "67.4", "a"), (1992, 69.6, "69.6", "a"), (1997, 70.0, "70.0", "a"),
        (2002, 68.3, "68.3", "b"), (2007, 70.7, "70.7", "a"),
    ]
    xs = _years(1983, 2007)
    panel = PanelSpec(
        xlim=(1982.5, 2007.5),
        ylim=(50.0, 75.0),
        xticks=[float(y) for y in range(1983, 2008, 2)],
        yticks=[(float(v), f"{v:.1f}") for v in range(50, 76, 5)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=over15, label="就业率（15岁以上）", color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=xs, y=age15_64, label="就业率（15~64岁）", color_idx=1, marker="square", width=1.8),
        ],
        annotations=_labels(labels),
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="4-2", title="图 4-2 就业率的变化 (年平均)", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_4_3(mode: ThemeMode = "mono") -> str:
    over30 = [79.0, 80.8, 81.9, 82.3, 82.4, 81.1, 81.0, 82.1, 82.6, 83.5, 84.8, 86.5, 87.2, 87.6, 88.2, 89.2,
              90.0, 90.5, 91.9, 94.4, 97.3, 100.5, 102.6, 103.8, 103.9, 103.4, 103.0, 103.7, 103.9, 103.4,
              102.8, 102.2, 100.7, 98.8, 99.3, 100.0, 101.0, 102.4]
    over5 = [91.0, 93.4, 95.9, 97.7, 98.7, 99.3, 100.5, 101.2, 101.1, 100.6, 100.3, 99.8, 99.2, 98.6, 99.3,
             100.0, 100.8, 102.5]
    panel = PanelSpec(
        xlim=(1969.5, 2007.5),
        ylim=(70.0, 110.0),
        xticks=[float(y) for y in range(1970, 2007, 2)],
        yticks=[(float(v), f"{v:.1f}") for v in range(70, 111, 5)],
        xlabel="年",
        zero_line=False,
        lines=[
            LineSeries(x=_years(1970, 1989), y=over30[:20], label="30人以上", color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=_years(1989, 2007), y=over30[19:], color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=_years(1990, 2007), y=over5, label="5人以上", color_idx=1, marker="square", width=1.8),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="4-3", title="图 4-3 常用就业指数的变化（2005 年 = 100）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_4_4(mode: ThemeMode = "mono") -> str:
    creation = [4.9, 4.8, 4.9, 4.6, 3.9, 3.9, 3.7, 4.2, 4.0, 3.4, 3.6, 3.5, 3.7, 3.8, 3.6, 3.8, 3.9]
    destruction = [3.9, 3.8, 3.4, 3.4, 4.0, 4.5, 4.3, 4.0, 4.6, 4.7, 4.5, 4.9, 5.5, 5.2, 5.0, 4.1, 4.0]
    labels = [
        (1989, 4.9, "4.9", "b"), (1991, 4.9, "4.9", "a"), (1998, 3.4, "3.4", "b"), (2001, 3.7, "3.7", "b"),
        (1989, 3.9, "3.9", "b"), (1991, 3.4, "3.4", "b"), (1998, 4.7, "4.7", "b"), (2001, 5.5, "5.5", "l"),
    ]
    xs = _years(1989, 2005)
    panel = PanelSpec(
        xlim=(1988.5, 2005.5),
        ylim=(0.0, 6.0),
        xticks=xs,
        yticks=[(float(v), f"{v:.1f}") for v in range(7)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=creation, label="就业创造率（存续）", color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=xs, y=destruction, label="就业破坏率（存续）", color_idx=1, marker="square", width=1.8),
        ],
        annotations=_labels(labels),
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="4-4", title="图 4-4 总体经济（常用劳动者、员工在 5 人以上的企业）", panels=[panel], width=860, height=500
    )
    return render_figure_svg(spec, mode)


def _fig_4_5(mode: ThemeMode = "mono") -> str:
    net = [4.7, 6.7, 3.5, 6.7, 1.9, 3.2, 2.7, -0.7, 0.9, 2.4]
    entry_exit = [3.5, 5.5, 3.7, 7.4, 3.0, 3.4, 3.6, 0.7, 2.3, 4.0]
    survivors = [1.1, 1.0, -0.1, -0.8, -1.2, -0.3, -0.9, -1.5, -1.4, -1.7]
    xs = _years(1991, 2000)
    panel = PanelSpec(
        xlim=(1990.5, 2000.5),
        ylim=(-3.0, 8.0),
        xticks=xs,
        yticks=[float(v) for v in range(-3, 9)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=net, label="就业净增率", color_idx=0, marker="circle", width=1.8),
            LineSeries(x=xs, y=entry_exit, label="开业停业效应下的净增", color_idx=1, marker="square", width=1.8),
            LineSeries(x=xs, y=survivors, label="存续效应下的净增", color_idx=2, marker="triangle", width=1.8),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="4-5", title="图 4-5 开业停业效应和存续效应（就业净增减）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_4_6(mode: ThemeMode = "mono") -> str:
    cre_s = [4.7, 4.6, 4.0, 3.8, 3.5, 4.0, 3.6, 3.6, 3.3, 3.4]
    des_s = [3.6, 3.6, 4.0, 4.5, 4.6, 4.1, 4.5, 4.9, 4.6, 5.0]
    cre_o = [6.1, 6.9, 5.4, 9.1, 6.0, 6.2, 5.7, 4.4, 5.1, 6.5]
    des_c = [2.5, 1.3, 1.7, 1.8, 3.0, 2.9, 2.1, 3.5, 2.8, 2.6]
    xs = _years(1991, 2000)
    pos_cre_s = ["b", "b", "a", "b", "la", "b", "b", "la", "lb", "r"]
    pos_des_s = ["b", "b", "b", "a", "r", "a", "rb", "a", "rb", "a"]
    pos_cre_o = ["a", "a", "a", "a", "a", "ra", "r", "rb", "a", "r"]
    pos_des_c = ["b", "ra", "b", "b", "b", "b", "b", "b", "b", "rb"]
    labels = []
    for ys, poss in ((cre_s, pos_cre_s), (des_s, pos_des_s), (cre_o, pos_cre_o), (des_c, pos_des_c)):
        labels += [(x, y, f"{y:.1f}", p) for x, y, p in zip(xs, ys, poss)]
    panel = PanelSpec(
        xlim=(1990.5, 2000.5),
        ylim=(0.0, 10.0),
        xticks=xs,
        yticks=[float(v) for v in range(11)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=cre_s, label="就业创造率（存续）", color_idx=0, marker="square", width=1.6),
            LineSeries(x=xs, y=des_s, label="就业破坏率（存续）", color_idx=1, marker="square", width=1.6),
            LineSeries(x=xs, y=cre_o, label="就业创造率（开业）", color_idx=2, marker="circle", width=1.6),
            LineSeries(x=xs, y=des_c, label="就业破坏率（停业）", color_idx=3, marker="circle", width=1.6),
        ],
        annotations=_labels(labels),
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="4-6", title="图 4-6 开业停业效应和存续效应 (就业创造和就业破坏)", panels=[panel], width=860, height=560
    )
    return render_figure_svg(spec, mode)


def _fig_4_7(mode: ThemeMode = "mono") -> str:
    net = [2.7, -1.3, 0.9, 2.2, 2.9, -0.4, 3.6, 1.0, -0.1]
    survivors = [-0.8, -1.4, -1.2, -1.5, -1.8, -1.3, -1.6, -0.1, -0.3]
    entry_exit = [3.4, 0.2, 2.1, 3.7, 4.8, 1.0, 5.2, 1.3, 0.2]
    xs = _years(1997, 2005)
    panel = PanelSpec(
        xlim=(1996.5, 2005.5),
        ylim=(-3.0, 6.0),
        xticks=xs,
        yticks=[float(v) for v in range(-3, 7)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=net, label="就业净增率", color_idx=0, marker="circle", width=1.8),
            LineSeries(x=xs, y=survivors, label="存续效应下的净增", color_idx=1, marker="triangle", width=1.8),
            LineSeries(x=xs, y=entry_exit, label="开业停业效应下的净增", color_idx=2, marker="square", width=1.8),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="4-7", title="图 4-7 开业停业效应和存续效应（就业净增减）", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_4_8(mode: ThemeMode = "mono") -> str:
    entry_exit = [3.4, 0.2, 2.0, 3.6, 4.8, 0.9, 5.2, 1.1, 0.2]
    creation = [6.1, 4.5, 5.3, 6.6, 7.2, 5.1, 7.9, 5.7, 4.4]
    destruction = [2.6, 4.3, 3.2, 2.9, 2.4, 4.1, 2.7, 4.5, 4.3]
    xs = _years(1997, 2005)
    panel = PanelSpec(
        xlim=(1996.5, 2005.5),
        ylim=(0.0, 9.0),
        xticks=xs,
        yticks=[float(v) for v in range(10)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=entry_exit, label="开业停业效应下的净增", color_idx=0, marker="square", width=1.8),
            LineSeries(x=xs, y=creation, label="就业创造率（开业）", color_idx=1, marker="circle", width=1.8),
            LineSeries(x=xs, y=destruction, label="就业破坏率（停业）", color_idx=2, marker="circle", width=1.8),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="4-8", title="图 4-8 开业停业效应下就业创造和就业破坏的分解", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_5_2(mode: ThemeMode = "mono") -> str:
    canada = [1923, 1902, 1897, 1896, 1880, 1862, 1854, 1847, 1840, 1832, 1819, 1799, 1787, 1784, 1784, 1787, 1787,
              1793, 1805, 1799, 1787, 1772, 1763, 1765, 1777, 1783, 1783, 1768, 1765, 1768, 1767, 1762, 1750, 1741,
              1753, 1741, 1739]
    france = [2011, 2000, 1979, 1950, 1936, 1911, 1911, 1896, 1870, 1855, 1841, 1805, 1770, 1754, 1745, 1730, 1721,
              1718, 1718, 1702, 1702, 1699, 1690, 1685, 1673, 1652, 1656, 1648, 1639, 1630, 1594, 1576, 1539, 1533,
              1554, 1560, 1567]
    italy = [2144, 2095, 2070, 2052, 2021, 2001, 2000, 1965, 1955, 1947, 1948, 1941, 1932, 1924, 1907, 1893, 1889,
             1884, 1902, 1902, 1901, 1891, 1877, 1864, 1858, 1855, 1870, 1861, 1873, 1870, 1855, 1837, 1828, 1825,
             1825, 1819, 1801]
    japan = [2244, 2241, 2229, 2201, 2137, 2112, 2129, 2129, 2124, 2127, 2121, 2106, 2102, 2098, 2109, 2097, 2098,
             2098, 2093, 2070, 2031, 2000, 1965, 1905, 1898, 1884, 1892, 1861, 1842, 1810, 1816, 1807, 1801, 1801,
             1792, 1780, 1783]
    uk = [1941, 1902, 1872, 1925, 1887, 1882, 1865, 1847, 1839, 1817, 1772, 1718, 1730, 1718, 1733, 1765, 1766, 1757,
          1798, 1787, 1772, 1768, 1736, 1729, 1741, 1744, 1743, 1743, 1738, 1726, 1714, 1717, 1698, 1677, 1672, 1677,
          1671]
    us = [1906, 1897, 1887, 1893, 1865, 1842, 1844, 1847, 1839, 1832, 1819, 1815, 1805, 1824, 1842, 1840, 1834, 1839,
          1845, 1854, 1836, 1824, 1827, 1834, 1840, 1846, 1840, 1849, 1852, 1852, 1840, 1819, 1807, 1804, 1804, 1804,
          1801]
    korea = [2878, 2895, 2904, 2923, 2919, 2897, 2922, 2891, 2842, 2743, 2687, 2671, 2650, 2666, 2650, 2656, 2644,
             2590, 2497, 2502, 2518, 2504, 2463, 2433, 2396, 2352, 2303]
    xs = _years(1970, 2006)

    def line(ys: list[int], label: str, idx: int, style: str = "solid", width: float = 1.6, axis: str = "y1") -> LineSeries:
        x = xs[len(xs) - len(ys):]
        return LineSeries(x=x, y=[float(v) for v in ys], label=label, color_idx=idx, style=style, width=width, axis=axis)

    panel = PanelSpec(
        xlim=(1969.5, 2006.5),
        ylim=(1500.0, 2300.0),
        xticks=[float(y) for y in range(1970, 2007, 2)],
        yticks=[float(v) for v in range(1500, 2301, 100)],
        y2lim=(2200.0, 3000.0),
        y2ticks=[float(v) for v in range(2200, 3001, 100)],
        xlabel="年",
        zero_line=False,
        lines=[
            line(canada, "加拿大", 3),
            line(france, "法国", 1, width=2.2),
            line(italy, "意大利", 5, style="plain"),
            line(japan, "日本", 2, width=1.8),
            line(uk, "英国", 4, style="plain", width=1.3),
            line(us, "美国", 4),
            line(korea, "韩国（右轴）", 0, width=3.0, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="5-2", title="图 5-2 OECD 主要国家就业人员人均年实际劳动时间", panels=[panel], width=860, height=540)
    return render_figure_svg(spec, mode)


def _fig_5_3(mode: ThemeMode = "mono") -> str:
    holidays = [93.0, 94.0, 94.1, 95.4, 98.5, 101.9, 105.5, 108.6, 110.0, 110.8, 110.8, 111.8, 112.4, 112.5, 113.2,
                112.8, 112.6, 113.0, 113.0, 113.2, 113.2, 112.9]
    hours = [46.3, 46.4, 46.4, 46.4, 45.8, 45.3, 44.6, 43.5, 42.9, 42.7, 42.9, 42.6, 42.0, 41.7, 41.6, 42.2, 41.6,
             41.4, 41.2, 41.2, 41.0, 40.9]
    xs = _years(1985, 2006)
    panel = PanelSpec(
        xlim=(1984.5, 2006.5),
        ylim=(90.0, 115.0),
        xticks=xs,
        yticks=[float(v) for v in range(90, 116, 5)],
        y2lim=(40.0, 50.0),
        y2ticks=[float(v) for v in range(40, 51, 2)],
        xlabel="年",
        ylabel="天",
        y2label="小时",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=holidays, label="全年假日天数", color_idx=0, width=2.2),
            LineSeries(x=xs, y=hours, label="就业人员人均周劳动时间（右轴）", color_idx=2, width=2.2, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="5-3", title="图 5-3 全年假日天数", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_5_4(mode: ThemeMode = "mono") -> str:
    leave = [8.2, 7.8, 7.5, 7.6, 7.6, 7.9, 8.2, 8.6, 9.0, 9.1, 9.1, 9.5, 9.4, 9.4, 9.1, 9.0, 8.9, 8.8, 8.8, 8.5, 8.4, 8.4]
    two_day = [27.3, 28.1, 28.7, 29.8, 36.4, 39.2, 45.6, 50.8, 52.5, 54.1, 57.7, 59.1, 60.6, 59.1, 58.5, 57.6, 56.6,
               57.1, 56.6, 60.3, 60.0, 59.0]
    xs = _years(1985, 2006)
    panel = PanelSpec(
        xlim=(1984.5, 2006.5),
        ylim=(6.0, 10.0),
        xticks=xs,
        yticks=[(v / 2, f"{v / 2:.1f}") for v in range(12, 21)],
        y2lim=(25.0, 65.0),
        y2ticks=[float(v) for v in range(25, 66, 5)],
        xlabel="年",
        ylabel="天",
        y2label="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=leave, label="休年假天数", color_idx=0, width=2.2),
            LineSeries(x=xs, y=two_day, label="双休制全面实施比例", color_idx=2, width=2.2, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="5-4", title="图 5-4 休年假天数与双休制全面实施比例", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _short_long(fid: str, title: str, under35: list[float], over60: list[float]) -> FigureSpec:
    xs = _years(1955, 2007)
    panel = PanelSpec(
        xlim=(1954.5, 2007.5),
        ylim=(0.0, 30.0),
        xticks=[float(y) for y in range(1955, 2006, 5)],
        yticks=[float(v) for v in range(0, 31, 5)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=under35, label="不到35小时", color_idx=0, width=2.2),
            LineSeries(x=xs, y=over60, label="60小时以上", color_idx=2, width=2.2),
        ],
        legend_loc="bottom",
    )
    return FigureSpec(fig_id=fid, title=title, panels=[panel], width=860, height=500)


def _fig_5_5(mode: ThemeMode = "mono") -> str:
    under35 = [8.5, 7.4, 7.4, 6.8, 6.6, 6.2, 6.2, 5.6, 6.0, 5.8, 6.1, 6.2, 6.5, 6.3, 6.3, 6.6, 7.1, 7.0, 7.9, 8.5,
               9.9, 8.7, 8.6, 8.9, 9.6, 10.0, 10.1, 10.5, 10.6, 11.0, 11.0, 11.6, 11.7, 12.2, 13.1, 15.1, 16.4, 17.4,
               18.2, 18.6, 17.7, 19.5, 21.1, 21.4, 21.5, 20.3, 23.0, 23.4, 24.1, 23.7, 23.9, 22.7, 24.6]
    over60 = [22.0, 23.3, 23.4, 22.4, 22.1, 21.4, 19.8, 16.2, 15.5, 14.4, 13.4, 13.4, 16.8, 15.5, 15.1, 14.3, 13.4,
              13.6, 13.6, 12.0, 10.8, 11.8, 12.4, 13.4, 13.8, 13.9, 14.0, 14.8, 15.6, 15.7, 15.9, 16.5, 16.9, 17.2,
              16.8, 15.4, 14.2, 12.0, 10.7, 10.5, 10.9, 10.8, 10.5, 10.6, 11.3, 11.6, 11.7, 12.1, 12.1, 12.0, 11.5,
              10.5, 10.0]
    return render_figure_svg(_short_long("5-5", "图 5-5 短时间和长时间劳动者的比例", under35, over60), mode)


def _fig_5_6(mode: ThemeMode = "mono") -> str:
    under35 = [2.6, 2.3, 2.3, 2.2, 2.1, 2.1, 1.9, 1.9, 1.9, 1.8, 2.0, 2.1, 2.3, 2.1, 2.1, 2.3, 2.3, 2.3, 2.7, 3.0,
               3.4, 3.0, 3.0, 3.1, 3.4, 3.5, 3.5, 3.5, 3.5, 3.7, 3.9, 4.0, 4.0, 4.1, 4.5, 5.4, 6.0, 6.5, 6.9, 7.2,
               6.7, 7.4, 8.3, 8.5, 8.6, 7.9, 9.0, 9.1, 9.6, 9.5, 9.6, 9.2, 10.1]
    over60 = [25.6, 26.9, 26.9, 26.1, 25.7, 25.0, 23.6, 19.1, 18.5, 17.5, 16.2, 16.9, 20.2, 18.8, 18.4, 17.4, 16.8,
              16.8, 17.1, 15.5, 14.0, 14.9, 16.0, 16.6, 17.5, 17.5, 17.9, 18.4, 19.8, 19.8, 20.4, 20.5, 21.3, 21.7,
              21.5, 21.0, 18.6, 17.1, 14.9, 14.5, 15.0, 15.0, 14.9, 14.8, 15.1, 16.5, 16.4, 16.9, 17.2, 17.0, 16.6,
              15.6, 15.0]
    return render_figure_svg(
        _short_long("5-6", "图 5-6 短时间和长时间劳动者的劳动时间在总劳动时间中的占比", under35, over60), mode
    )


def _fig_5_7(mode: ThemeMode = "mono") -> str:
    large = [49.9, 50.0, 49.5, 48.7, 48.5, 48.3, 47.3, 45.9, 46.7, 47.3, 47.5, 47.7, 48.1, 48.4, 48.5, 49.2, 49.3,
             49.7, 49.4, 50.0, 50.4, 49.9, 49.2, 48.3, 47.0, 46.2, 46.0, 46.5, 46.6, 46.3, 46.4, 46.7, 47.6, 47.4,
             47.3, 47.1, 47.1, 47.0, 46.9, 46.2]
    small = [53.1, 53.0, 52.8, 52.2, 52.5, 52.5, 51.5, 50.5, 51.2, 51.7, 52.1, 52.0, 52.0, 52.0, 52.2, 52.5, 52.4,
             52.5, 52.5, 52.6, 52.6, 52.3, 51.6, 50.9, 49.9, 48.8, 48.5, 48.5, 48.3, 47.6, 47.3, 47.1, 47.7, 47.1,
             47.3, 47.1, 47.1, 46.5, 46.9]
    panel = PanelSpec(
        xlim=(1961.5, 2007.5),
        ylim=(40.0, 54.0),
        xticks=[float(y) for y in range(1962, 2008, 5)],
        yticks=[float(v) for v in range(40, 55, 2)],
        xlabel="年",
        ylabel="小时",
        zero_line=False,
        lines=[
            LineSeries(x=_years(1968, 2007), y=large, label="企业规模500人以上", color_idx=0, width=2.2),
            LineSeries(x=_years(1968, 2006), y=small, label="企业规模1~29人", color_idx=2, width=2.2),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="5-7", title="图 5-7 不同企业规模 周平均劳动时间", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_5_10(mode: ThemeMode = "mono") -> str:
    jan = [41.4, 39.8, None, 43.2, 46.9, 45.6, 44.8, 43.0, 43.2, 43.9, 45.2, 43.0, 42.3, 40.9, 41.4, 44.9, 44.1,
           43.2, 42.8, 42.9, 43.9, 45.6, 42.8, 43.3, 40.9, 43.6, 43.2, 42.8, 40.9, 42.7, 43.4, 42.9, 42.7, 39.0,
           40.0, 39.7, 36.8, 37.0]
    jun = [12.5, 15.8, None, 14.0, 18.6, 19.7, 18.1, 17.9, 17.5, 15.4, 19.3, 16.8, 18.0, 18.3, 15.3, 16.3, 17.7,
           16.5, 17.7, 17.1, 17.6, 19.4, 17.5, 22.6, 19.5, 17.8, 20.4, 17.7, 17.7, 20.1, 20.7, 21.2, 22.0, 21.4,
           20.4, 19.5, 15.6, 16.3]
    xs = _years(1970, 2007)
    panel = PanelSpec(
        xlim=(1969.5, 2007.5),
        ylim=(0.0, 50.0),
        xticks=[float(y) for y in range(1970, 2007, 2)],
        yticks=[float(v) for v in range(0, 51, 5)],
        xlabel="年",
        ylabel="小时",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=jan, label="1月", color_idx=0, width=2.2),
            LineSeries(x=xs, y=jun, label="6月", color_idx=2, width=2.2),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="5-10", title="图 5-10 1 月和 6 月两次调查的差异", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_5_8(mode: ThemeMode = "mono") -> str:
    series = [
        ("30~34岁", [52.9, 52.9, 51.8, 50.5, 51.3, 52.0, 52.3, 52.4, 52.5, 52.5, 52.7, 53.1, 53.0, 53.1, 53.2, 53.5, 53.6,
                    53.3, 53.0, 52.2, 50.9, 50.0, 49.6, 50.1, 50.1, 49.7, 49.5, 49.9, 50.8, 50.2, 50.2, 50.2, 50.4, 50.0,
                    50.0, 49.5]),
        ("35~39岁", [52.6, 52.4, 52.0, 50.3, 50.8, 51.5, 51.7, 51.8, 51.8, 51.9, 52.2, 52.7, 52.7, 52.6, 53.0, 53.2, 53.4,
                    53.0, 52.8, 52.2, 50.7, 50.0, 49.6, 50.1, 50.0, 49.7, 49.5, 49.9, 50.7, 50.2, 50.2, 49.9, 50.0, 50.0,
                    49.5, 48.7]),
        ("40~44岁", [52.0, 52.1, 51.2, 50.0, 51.2, 51.5, 52.1, 52.2, 52.2, 52.4, 52.6, 53.0, 53.0, 53.1, 53.1, 53.5, 53.6,
                    53.3, 52.6, 51.8, 50.4, 49.5, 49.2, 49.4, 49.4, 48.8, 48.8, 49.1, 50.0, 49.8, 49.8, 49.8, 49.8, 49.8,
                    49.7, 49.3]),
        ("45~49岁", [51.6, 51.5, 51.2, 49.3, 49.9, 50.5, 51.1, 51.3, 51.3, 51.6, 52.0, 52.4, 52.5, 52.6, 52.5, 52.9, 53.4,
                    53.0, 52.3, 51.4, 50.1, 49.1, 48.6, 49.0, 48.8, 48.3, 48.1, 48.4, 49.0, 48.6, 48.6, 48.9, 49.1, 48.9,
                    48.9, 48.4]),
        ("50~54岁", [51.4, 51.5, 50.5, 49.0, 49.5, 49.8, 50.2, 50.1, 50.1, 50.0, 50.4, 51.0, 51.0, 51.4, 51.3, 51.7, 52.2,
                    51.9, 51.3, 50.6, 49.4, 48.4, 48.3, 48.5, 48.0, 47.4, 47.5, 47.5, 48.1, 47.7, 47.6, 47.4, 47.7, 47.6,
                    47.7, 47.2]),
    ]
    xs = _years(1972, 2007)
    panel = PanelSpec(
        xlim=(1961.5, 2007.5),
        ylim=(46.0, 54.0),
        xticks=[float(y) for y in range(1962, 2008, 5)],
        yticks=[float(v) for v in range(46, 55)],
        xlabel="年",
        ylabel="小时",
        zero_line=False,
        lines=[LineSeries(x=xs, y=ys, label=label, color_idx=i, width=1.8) for i, (label, ys) in enumerate(series)],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id="5-8", title="图 5-8 各年龄段 周平均劳动时间", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_5_12(mode: ThemeMode = "mono") -> str:
    first_x = [1970.85, 1971.5, 1971.85]
    first = [(208.7, 186.2, 169.9), (207.3, 185.1, 169.5), (206.4, 184.6, 169.4)]
    second_x = [1973.5] + [y / 2 for y in range(3948, 4015)] + [2007.4]
    second = [
        (207.0, 182.3, 167.0), (204.7, 180.3, 164.7), (202.7, 177.2, 163.3), (200.8, 174.5, 162.2),
        (200.4, 172.2, 161.4), (200.4, 173.0, 161.8), (200.3, 174.1, 162.8), (200.8, 174.4, 162.9),
        (201.2, 174.4, 162.8), (201.8, 174.4, 162.9), (202.3, 174.7, 162.8), (202.7, 174.9, 162.9),
        (203.1, 175.8, 162.9), (203.1, 176.0, 162.9), (202.8, 175.8, 162.3), (202.1, 175.1, 161.9),
        (201.5, 174.9, 161.9), (201.4, 174.7, 161.6), (201.3, 174.6, 161.7), (201.3, 174.5, 161.8),
        (201.5, 174.4, 161.6), (201.4, 174.6, 161.9), (201.2, 175.7, 161.9), (201.4, 175.7, 161.4),
        (201.7, 175.5, 161.6), (201.8, 175.5, 161.6), (202.1, 175.4, 161.5), (202.3, 175.2, 161.4),
        (202.4, 175.2, 161.3), (202.3, 176.0, 161.5), (202.3, 175.6, 160.6), (201.8, 174.6, 159.6),
        (200.7, 173.7, 158.6), (200.4, 172.7, 157.2), (198.1, 171.4, 156.2), (195.9, 170.0, 154.9),
        (193.6, 168.7, 153.8), (192.4, 166.7, 153.1), (190.7, 165.0, 152.7), (188.1, 162.4, 151.1),
        (186.6, 160.0, 149.3), (186.1, 159.1, 148.5), (186.1, 158.7, 148.2), (186.3, 158.6, 147.9),
        (187.0, 158.8, 148.0), (187.2, 159.3, 147.8), (186.4, 159.7, 147.6), (184.8, 159.1, 147.0),
        (183.6, 158.3, 146.6), (181.6, 157.3, 145.8), (181.5, 156.3, 145.4), (181.5, 155.1, 144.9),
        (181.7, 153.6, 143.3), (183.0, 153.8, 143.2), (183.8, 154.2, 143.5), (183.4, 154.2, 143.1),
        (181.7, 153.9, 143.1), (180.2, 153.5, 142.6), (180.4, 153.3, 142.4), (180.3, 153.1, 142.3),
        (180.2, 153.6, 141.9), (180.3, 153.7, 141.5), (180.4, 153.2, 141.4), (180.4, 152.5, 140.3),
        (179.0, 152.6, 140.2), (178.0, 152.7, 140.4), (177.7, 152.9, 140.5), (177.8, 153.4, 140.7),
        (176.0, 153.5, 140.8),
    ]
    labels = ["事业所调查中的过小申报部分（12个月移动平均）", "规定外（12个月移动平均）", "规定（12个月移动平均）"]
    bands = []
    for xs, rows, labelled in ((second_x, second, True), (first_x, first, False)):
        for i, label in enumerate(labels):
            bands.append(
                BandSeries(
                    x=xs,
                    y_low=[130.0] * len(xs),
                    y_high=[r[i] for r in rows],
                    label=label if labelled else "",
                    color_idx=i,
                    show_edges=False,
                )
            )
    panel = PanelSpec(
        xlim=(1970.0, 2007.6),
        ylim=(130.0, 210.0),
        xticks=[float(y) for y in range(1970, 2007, 2)],
        yticks=[float(v) for v in range(130, 211, 10)],
        xlabel="年",
        ylabel="小时",
        zero_line=False,
        bands=bands,
        legend_loc="bottom",
        xtick_vertical=True,
    )
    spec = FigureSpec(fig_id="5-12", title="图 5-12 月平均劳动时间明细", panels=[panel], width=860, height=540)
    return render_figure_svg(spec, mode)


def _fig_6_1(mode: ThemeMode = "mono") -> str:
    ys = [2, 2, 2, 2, 1, 1, 2, 1, 2, 1, 1, 2, 1, 1, 1, 2, 2, 2, 3, 4, 5, 4, 3, 3, 3, 2, 2, 2, 3, 3, 3, 5, 7, 4, 4, 3]
    xs = [1994.0 + (i + 0.5) / 4 for i in range(len(ys))]
    panel = PanelSpec(
        xlim=(1994.0, 2003.0),
        ylim=(0.0, 8.0),
        xticks=[(y + 0.5, str(y)) for y in range(1994, 2003)],
        yticks=[float(v) for v in range(9)],
        xlabel="年",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs[:18], y=[float(v) for v in ys[:18]], color_idx=0, marker="diamond", width=1.8),
            LineSeries(x=xs[17:], y=[float(v) for v in ys[17:]], color_idx=0, marker="diamond", width=1.8),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="6-1", title="图 6-1 制造业企业实施自愿辞职和解雇的比例 1994—2002 年", panels=[panel], width=860, height=480
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "4-1": _fig_4_1,
        "4-2": _fig_4_2,
        "4-3": _fig_4_3,
        "4-4": _fig_4_4,
        "4-5": _fig_4_5,
        "4-6": _fig_4_6,
        "4-7": _fig_4_7,
        "4-8": _fig_4_8,
        "5-2": _fig_5_2,
        "5-3": _fig_5_3,
        "5-4": _fig_5_4,
        "5-5": _fig_5_5,
        "5-6": _fig_5_6,
        "5-7": _fig_5_7,
        "5-8": _fig_5_8,
        "5-10": _fig_5_10,
        "5-12": _fig_5_12,
        "6-1": _fig_6_1,
    }
