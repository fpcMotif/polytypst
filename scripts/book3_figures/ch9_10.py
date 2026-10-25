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


def _stack3(
    near: list[float], mid: list[float], far: list[float]
) -> tuple[list[float], list[float], list[float]]:
    near_b: list[float] = []
    mid_b: list[float] = []
    far_b: list[float] = []
    for a, b, c in zip(near, mid, far):
        pos = 0.0
        neg = 0.0
        if b >= 0:
            mid_b.append(pos)
            pos += b
        if a >= 0:
            near_b.append(pos)
            pos += a
        else:
            near_b.append(neg)
            neg += a
        if b < 0:
            mid_b.append(neg)
            neg += b
        if c >= 0:
            far_b.append(pos)
            pos += c
        else:
            far_b.append(neg)
            neg += c
    return near_b, mid_b, far_b


def _ppp_figure(
    fig_id: str,
    title: str,
    subtitle: str,
    note: str,
    years: list[int],
    ppp: list[float],
    nominal: list[float],
    gap: list[float],
    ylim: tuple[float, float],
    yticks: list[float],
    y2lim: tuple[float, float],
    y2ticks: list[float],
    mode: ThemeMode,
) -> str:
    xs = [float(i) for i in range(len(years))]
    panel = PanelSpec(
        xlim=(-0.5, len(years) - 0.5),
        ylim=ylim,
        xticks=[(float(i), str(y)) for i, y in enumerate(years)],
        yticks=yticks,
        y2lim=y2lim,
        y2ticks=y2ticks,
        xlabel="年",
        y2label="倍",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=ppp, label="购买力平价", color_idx=2, style="dashed", marker="square", width=2.2),
            LineSeries(x=xs, y=nominal, label="名义汇率", color_idx=1, style="dotted", marker="diamond", width=2.2),
            LineSeries(x=xs, y=gap, label="内外价格差（倒数）", color_idx=0, style="solid", width=2.6, axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, subtitle=subtitle, panels=[panel], note=note, width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_9_1(mode: ThemeMode = "mono") -> str:
    return _ppp_figure(
        "9-1",
        "图 9-1 对纽约的购买力平价、名义汇率、内外价格差的推移（泡沫期）",
        "",
        "资料来源：基于生计成本调查（1999年）的购买力平价及内外价格差的概况（2000年）",
        list(range(1985, 1991)),
        [193.0, 191.0, 186.0, 180.0, 173.0, 169.0],
        [238.0, 168.0, 145.0, 128.0, 138.0, 145.0],
        [1.23, 0.90, 0.81, 0.71, 0.78, 0.84],
        (0.0, 300.0),
        [0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0],
        (0.0, 1.4),
        [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4],
        mode,
    )


def _fig_9_2(mode: ThemeMode = "mono") -> str:
    return _ppp_figure(
        "9-2",
        "图 9-2 对纽约购买力平价、名义汇率、内外价格差推移（20世纪90年代）",
        "内外价格差的推移（20世纪90年代）",
        "资料来源：基于生计成本调查（1999 年）的购买力平价及内外价格差的概况（2000 年）",
        list(range(1990, 2000)),
        [169.0, 171.0, 166.0, 156.0, 155.0, 150.0, 143.0, 141.0, 139.0, 135.0],
        [143.0, 134.0, 127.0, 111.0, 102.0, 94.0, 109.0, 121.0, 130.0, 114.0],
        [0.85, 0.79, 0.76, 0.71, 0.66, 0.63, 0.75, 0.85, 0.93, 0.83],
        (0.0, 180.0),
        [0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0],
        (0.0, 1.0),
        [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, (1.0, "1")],
        mode,
    )


def _fig_9_3(mode: ThemeMode = "mono") -> str:
    years = list(range(1990, 2000))
    xs = [float(i) for i in range(len(years))]
    panel = PanelSpec(
        xlim=(-0.5, len(years) - 0.5),
        ylim=(-2.0, 7.0),
        xticks=[(float(i), str(y)) for i, y in enumerate(years)],
        yticks=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        xlabel="年",
        ylabel="%",
        lines=[
            LineSeries(
                x=xs,
                y=[3.7, 3.6, 0.4, 0.7, 0.9, -0.9, -0.1, 1.8, 0.8, -1.3],
                label="日本",
                color_idx=2,
                style="dashed",
                marker="square",
            ),
            LineSeries(
                x=xs,
                y=[6.3, 3.0, 3.0, 2.0, 2.6, 2.5, 3.2, 1.7, 1.4, 2.5],
                label="美国",
                color_idx=0,
                style="solid",
                marker="square",
            ),
        ],
        legend_loc="top",
    )
    spec = FigureSpec(
        fig_id="9-3",
        title="图 9-3 日本和美国的 CPI（综合）的变化率",
        subtitle="（各年11月的前一年同期比）",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def _fig_9_4(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1980, 2006)]
    ulc = [
        1.23, 1.19, 0.96, 1.06, 1.06, 0.96, 1.37, 1.57, 1.67, 1.49,
        1.23, 1.30, 1.37, 1.53, 1.70, 1.78, 1.49, 1.33, 1.26, 1.34, 1.29,
    ]
    ulc_tail = [1.29, 1.12, 1.05, 1.00, 1.03, 0.86]
    gap = [
        1.02, 1.00, 0.86, 0.86, 0.86, 0.86, 1.20, 1.37, 1.53, 1.40,
        1.31, 1.40, 1.49, 1.64, 1.74, 1.87, 1.57, 1.45, 1.32, 1.45,
        1.45, 1.23, 1.18, 1.22, 1.23, 1.08,
    ]
    rate = [
        227.0, 221.0, 249.0, 238.0, 238.0, 239.0, 169.0, 145.0, 128.0, 140.0,
        144.0, 135.0, 127.0, 112.0, 102.0, 94.0, 109.0, 121.0, 128.0, 113.0,
        109.0, 122.0, 125.0, 112.0, 109.0, 116.0,
    ]
    rate_inv = [2.0 - r / 150.0 for r in rate]
    panel = PanelSpec(
        xlim=(1979.5, 2005.5),
        ylim=(0.0, 2.0),
        xticks=[(float(y), str(y)) for y in range(1980, 2005, 2)] + [(2005.0, "2005")],
        yticks=[(v / 10, f"{v / 10:.1f}") for v in range(0, 21, 2)],
        y2lim=(0.0, 2.0),
        y2ticks=[(2.0 - v / 150.0, str(v)) for v in range(0, 301, 50)],
        xlabel="年",
        ylabel="美国=1",
        y2label="日元/美元",
        zero_line=False,
        lines=[
            LineSeries(x=years, y=gap, label="对美内外价格差", color_idx=2, style="solid", width=2.4),
            LineSeries(
                x=years[:21], y=ulc, label="对美单位劳动力成本（制造业）", color_idx=1,
                style="dashed", marker="square", width=2.0,
            ),
            LineSeries(x=years[20:], y=ulc_tail, color_idx=1, style="dashed", width=2.0),
            LineSeries(
                x=years, y=rate_inv, label="汇率（右轴）", color_idx=0, style="solid",
                marker="square", width=2.6, axis="y2",
            ),
        ],
        annotations=[
            Annotation(x=2000.6, y=1.36, text="对美内外价格差", dx=10.0, dy=-70.0, align="middle"),
            Annotation(x=1986.2, y=0.80, text="汇率（右轴）", dx=70.0, dy=55.0, align="start"),
            Annotation(x=2002.4, y=1.02, text="对美单位劳动力成本（制造业）", dx=20.0, dy=125.0, align="end"),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="9-4",
        title="图 9-4 对美内外价格和对美单位劳动成本（制造业）",
        subtitle="（1）对美内外价格差和对美单位劳动力成本（制造业）",
        panels=[panel],
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def _factor_figure(
    fig_id: str,
    title: str,
    subtitle: str,
    near: list[float],
    mid: list[float],
    far: list[float],
    total: list[float],
    labels: tuple[str, str, str, str],
    ylim: tuple[float, float],
    yticks: list[float],
    annotations: list[Annotation],
    mode: ThemeMode,
) -> str:
    years = [float(y) for y in range(1981, 2007)]
    near_b, mid_b, far_b = _stack3(near, mid, far)
    panel = PanelSpec(
        xlim=(1980.4, 2006.6),
        ylim=ylim,
        xticks=[(float(y), str(y)) for y in range(1981, 2006, 2)],
        yticks=[(v, f"{v:.1f}") for v in yticks],
        xlabel="年",
        ylabel="（前年比、%）",
        bars=[
            BarSeries(x=years, y=mid, bottom=mid_b, label=labels[1], color_idx=2, width=0.7, opacity=0.95),
            BarSeries(x=years, y=near, bottom=near_b, label=labels[0], color_idx=3, width=0.7, opacity=0.95),
            BarSeries(x=years, y=far, bottom=far_b, label=labels[2], color_idx=0, width=0.7, opacity=0.95),
        ],
        lines=[LineSeries(x=years, y=total, label=labels[3], color_idx=0, style="solid", width=2.4)],
        annotations=annotations,
        legend_loc="none",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, subtitle=subtitle, panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_9_5(mode: ThemeMode = "mono") -> str:
    fx = [
        0.3, 0.8, 2.3, 4.6, 7.1, 9.7, 10.4, 9.2, 7.4, 5.8, 5.3, 5.3, 4.8,
        3.4, 1.1, -0.1, -0.3, -0.8, -1.0, -1.2, -1.3, 0.4, 1.1, 1.2, 1.0, 0.7,
    ]
    jp = [
        2.8, 2.6, 2.4, 2.1, 2.0, 1.6, 1.5, 1.6, 1.7, 1.7, 1.6, 1.2, 0.8,
        0.5, 0.0, -1.7, -1.6, -1.4, -1.6, -1.8, -1.7, -1.4, -1.4, -1.4, -1.4, -1.3,
    ]
    us = [
        -5.9, -5.2, -4.6, -4.0, -3.4, -3.3, -3.3, -3.3, -3.3, -3.2, -3.1, -2.7, -2.5,
        -2.2, -2.1, -1.6, -2.8, -2.3, -0.9, -0.4, -0.5, -2.1, -2.5, -2.5, -2.5, -2.5,
    ]
    total = [
        -1.9, -1.5, 1.0, 3.8, 6.9, 8.8, 9.8, 8.8, 6.9, 4.7, 4.2, 4.1, 3.6,
        2.8, 0.5, -2.0, -4.2, -3.7, -3.3, -3.4, -3.6, -3.2, -2.6, -2.8, -2.9, -3.1,
    ]
    return _factor_figure(
        "9-5",
        "图 9-5 对美内外价格的要素分解（同比）",
        "（2）对美内外价格差的要因分解（同比）",
        fx,
        jp,
        us,
        total,
        ("汇率要因", "日本的物价要因", "美国的物价要因", "合计"),
        (-10.0, 15.0),
        [-10.0, -5.0, 0.0, 5.0, 10.0, 15.0],
        [
            Annotation(x=1990.0, y=7.4, text="汇率要因", dx=60.0, dy=-70.0, align="start"),
            Annotation(x=2001.0, y=-0.1, text="日本的物价要因", dx=-30.0, dy=-110.0, align="middle"),
            Annotation(x=1993.0, y=-2.6, text="美国的物价要因", dx=-40.0, dy=34.0, align="middle"),
            Annotation(x=1993.0, y=-2.6, text="（向下意味着美国的物价上升）", dx=-40.0, dy=60.0, arrow=False, align="middle"),
        ],
        mode,
    )


def _fig_9_6(mode: ThemeMode = "mono") -> str:
    fx = [
        0.8, 0.6, 0.4, 2.85, 5.9, 9.1, 9.6, 8.4, 6.1, 4.6, 4.1, 4.1, 3.4,
        1.7, 1.4, 1.4, 1.8, 1.9, 1.6, 1.0, 0.8, 0.3, -1.9, -1.7, -1.4, -1.3,
    ]
    wage = [
        -2.0, -1.6, 0.15, -0.7, -0.2, 0.0, 0.6, 0.9, 0.9, 0.6, 0.3, -0.2, 0.0,
        0.7, -0.7, -1.1, -1.6, -1.9, -2.3, -2.5, -2.5, -2.2, -0.4, -0.6, -0.9, -0.9,
    ]
    prod = [
        -2.0, -1.7, -1.1, -0.4, -1.25, -2.0, -2.8, -3.8, -4.3, -4.0, -2.9, -1.5, -0.6,
        -0.6, -1.0, -3.5, -4.6, -4.6, -3.9, -3.7, -3.8, -3.4, -2.9, -2.7, -3.1, -3.4,
    ]
    total = [
        -3.0, -2.6, -0.1, 1.5, 4.4, 7.0, 7.2, 5.4, 3.0, 1.4, 1.5, 2.4, 2.8,
        1.8, -0.6, -3.3, -4.3, -4.4, -4.5, -5.0, -5.3, -5.4, -4.9, -4.9, -5.1, -5.4,
    ]
    return _factor_figure(
        "9-6",
        "图 9-6 对美内外价格差和对美单位劳动力成本（制造业，同比）",
        "（3）对美单位劳动力成本的要因分解（制造业，同比）",
        fx,
        wage,
        prod,
        total,
        ("内外价格差要因", "薪金增长率之差", "劳动生产率的增长率之差", "合计"),
        (-8.0, 12.0),
        [-8.0, -4.0, 0.0, 4.0, 8.0, 12.0],
        [
            Annotation(x=1990.0, y=5.2, text="内外价格差要因", dx=0.0, dy=-72.0, align="middle"),
            Annotation(x=2003.0, y=0.0, text="薪金增长率之差", dx=-30.0, dy=-150.0, arrow=False, align="middle"),
            Annotation(x=2003.0, y=0.0, text="（向下意味着日本的增长率低）", dx=-30.0, dy=-125.0, align="middle"),
            Annotation(x=1991.0, y=-2.9, text="劳动生产率的增长率之差", dx=-60.0, dy=30.0, align="middle"),
            Annotation(x=1991.0, y=-2.9, text="（向下意味着日本的增长率高）", dx=-60.0, dy=56.0, arrow=False, align="middle"),
        ],
        mode,
    )


def _fig_10_1(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1978, 2008)]
    values = [
        76.7, 77.5, 78.3, 79.3, 80.2, 81.7, 84.1, 85.0, 86.7, 88.4,
        94.1, 98.4, 107.5, 121.9, 128.2, 132.1, 135.4, 136.2, 141.5, 148.3,
        151.2, 155.6, 168.6, 177.8, 185.2, 191.5, 197.4, 201.2, 208.5, 215.3,
    ]
    panel = PanelSpec(
        xlim=(1977.4, 2007.6),
        ylim=(0.0, 250.0),
        xticks=[(float(y), str(y)) for y in range(1978, 2007, 2)],
        yticks=[0.0, 50.0, 100.0, 150.0, 200.0, 250.0],
        xlabel="年",
        ylabel="万人",
        zero_line=False,
        bars=[BarSeries(x=years, y=values, color_idx=1, width=0.55, opacity=0.9)],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="10-1",
        title="图 10-1 外国劳动者数量的变化",
        panels=[panel],
        note="资料来源：日本法务省",
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def _fig_10_2(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1947, 2007)]
    births = [
        268.0, 268.0, 270.0, 234.0, 214.0, 201.0, 187.0, 177.0, 173.0, 167.0,
        157.0, 165.0, 163.0, 161.0, 159.0, 162.0, 166.0, 172.0, 182.0, 136.0,
        194.0, 187.0, 189.0, 193.0, 200.0, 204.0, 209.0, 203.0, 190.0, 183.0,
        176.0, 171.0, 164.0, 158.0, 153.0, 152.0, 151.0, 149.0, 143.0, 138.0,
        135.0, 131.0, 125.0, 122.0, 122.0, 121.0, 119.0, 124.0, 119.0, 121.0,
        119.0, 120.0, 118.0, 119.0, 117.0, 115.0, 112.0, 111.0, 106.0, 109.0,
    ]
    tfr = [
        4.54, 4.40, 4.32, 3.65, 3.26, 2.98, 2.69, 2.48, 2.37, 2.22,
        2.04, 2.11, 2.04, 2.00, 1.96, 1.98, 2.00, 2.05, 2.14, 1.58,
        2.23, 2.13, 2.13, 2.13, 2.16, 2.14, 2.14, 2.05, 1.91, 1.85,
        1.80, 1.79, 1.77, 1.75, 1.74, 1.77, 1.80, 1.81, 1.76, 1.72,
        1.69, 1.66, 1.57, 1.54, 1.53, 1.50, 1.46, 1.50, 1.42, 1.43,
        1.39, 1.38, 1.34, 1.36, 1.33, 1.32, 1.29, 1.29, 1.26, 1.32,
    ]
    panel = PanelSpec(
        xlim=(1946.3, 2006.7),
        ylim=(0.0, 300.0),
        xticks=[(float(y), str(y)) for y in range(1947, 2007, 3)],
        yticks=[0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0],
        y2lim=(0.0, 5.0),
        y2ticks=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        xlabel="年",
        ylabel="万人",
        y2label="%",
        zero_line=False,
        bars=[BarSeries(x=years, y=births, label="出生人数（左轴）", color_idx=1, width=0.62, hatch=True, opacity=0.9)],
        lines=[
            LineSeries(x=years, y=tfr, label="总生育率（右轴）", color_idx=0, style="solid", marker="square", width=2.0, axis="y2"),
        ],
        annotations=[
            Annotation(x=1949.0, y=270.0, text="第1次生育高峰", dx=30.0, dy=-4.0, arrow=False, align="start"),
            Annotation(x=1949.4, y=270.0, text="270万人", dx=40.0, dy=10.0, align="start"),
            Annotation(x=1949.0, y=4.32, text="4.32", dx=40.0, dy=36.0, arrow=False, align="start", axis="y2"),
            Annotation(x=1966.0, y=136.0, text="136万人", dx=0.0, dy=-90.0, align="middle"),
            Annotation(x=1966.0, y=136.0, text="丙午", dx=0.0, dy=-118.0, arrow=False, align="middle"),
            Annotation(x=1966.0, y=1.58, text="1.58", dx=0.0, dy=22.0, arrow=False, align="middle", axis="y2"),
            Annotation(x=1973.0, y=209.0, text="208万人", dx=40.0, dy=-28.0, align="start"),
            Annotation(x=1973.0, y=209.0, text="第2次生育高峰", dx=32.0, dy=-62.0, arrow=False, align="start"),
            Annotation(x=1972.0, y=2.16, text="2.14", dx=0.0, dy=-24.0, arrow=False, align="middle", axis="y2"),
            Annotation(x=2006.0, y=109.0, text="109万人", dx=0.0, dy=-60.0, align="end"),
            Annotation(x=2006.0, y=109.0, text="2006年", dx=0.0, dy=-88.0, arrow=False, align="end"),
            Annotation(x=2006.0, y=1.32, text="1.32", dx=-8.0, dy=-18.0, arrow=False, align="end", axis="y2"),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="10-2",
        title="图 10-2 出生人数以及总生育率年度变化",
        panels=[panel],
        note="资料来源：日本国立社会保障和人口问题研究所",
        width=860,
        height=560,
    )
    return render_figure_svg(spec, mode)


def _fig_10_3(mode: ThemeMode = "mono") -> str:
    groups = ["2005", "10", "15", "20", "25", "30"]
    young = [17.6, 16.5, 14.8, 13.2, 12.0, 11.1]
    working = [84.4, 81.3, 76.8, 73.6, 71.0, 67.4]
    old = [25.8, 29.4, 33.8, 35.9, 36.4, 36.7]
    offs = (-0.24, 0.0, 0.24)
    anns: list[Annotation] = []
    for vals, off in zip((young, working, old), offs):
        for i, v in enumerate(vals):
            anns.append(Annotation(x=i + off, y=v, text=f"{v:.1f}", dx=0.0, dy=-2.0, arrow=False, fontsize=9.5))
    panel = PanelSpec(
        xlim=(-0.5, 5.5),
        ylim=(0.0, 93.0),
        xticks=[(float(i), g) for i, g in enumerate(groups)],
        yticks=[(0.0, "0.00")] + [(float(v), f"{v:.1f}") for v in range(10, 91, 10)],
        xlabel="年",
        ylabel="人口（100万人）",
        zero_line=False,
        bars=[
            BarSeries(x=[i + offs[0] for i in range(6)], y=young, label="0～14岁", color_idx=2, width=0.24, opacity=0.95),
            BarSeries(x=[i + offs[1] for i in range(6)], y=working, label="15～64岁", color_idx=3, width=0.24, opacity=0.95),
            BarSeries(x=[i + offs[2] for i in range(6)], y=old, label="65岁以上", color_idx=0, width=0.24, opacity=0.95),
        ],
        annotations=anns,
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="10-3",
        title="图 10-3 各年龄段人口的展望",
        panels=[panel],
        note="资料来源：日本国立社会保障·人口问题研究所",
        width=860,
        height=520,
    )
    return render_figure_svg(spec, mode)


def _fig_10_4(mode: ThemeMode = "mono") -> str:
    ages = ["15～19", "20～24", "25～29", "30～34", "35～39", "40～44", "45～49", "50～54", "55～59", "60～64", "65～"]
    xs = [float(i) for i in range(len(ages))]
    series = [
        ("1990年", [17.6, 74.8, 61.1, 51.3, 63.0, 69.0, 72.0, 65.0, 53.7, 38.8, 16.2], 0, "solid", "square"),
        ("1995年", [15.5, 73.6, 66.4, 54.0, 60.3, 69.6, 70.5, 67.2, 56.5, 39.6, 15.0], 1, "dashed", "square"),
        ("2000年", [17.0, 72.9, 70.1, 57.5, 61.5, 70.0, 71.1, 67.7, 58.3, 39.8, 14.2], 2, "dotted", "diamond"),
        ("2005年", [16.8, 69.4, 74.8, 62.9, 61.6, 71.0, 73.7, 69.0, 60.3, 40.0, 12.2], 3, "dashdot", "triangle"),
    ]
    panel = PanelSpec(
        xlim=(-0.5, len(ages) - 0.5),
        ylim=(0.0, 80.0),
        xticks=[(float(i), a) for i, a in enumerate(ages)],
        yticks=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0],
        xlabel="年龄段",
        ylabel="%",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=ys, label=lab, color_idx=ci, style=st, marker=mk, width=1.8)
            for lab, ys, ci, st, mk in series
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="10-4",
        title="图 10-4 女性各年龄段劳动力参与率（M 型曲线）",
        panels=[panel],
        width=900,
        height=520,
    )
    return render_figure_svg(spec, mode)


def _wage_figure(
    fig_id: str,
    title: str,
    note: str,
    first: tuple[str, list[float]],
    second: tuple[str, list[float]],
    ylim: tuple[float, float],
    yticks: list[float],
    mode: ThemeMode,
) -> str:
    ages = ["20～24", "25～29", "30～34", "35～39", "40～44", "45～49", "50～54", "55～59"]
    xs = [float(i) for i in range(len(ages))]
    panel = PanelSpec(
        xlim=(-0.5, len(ages) - 0.5),
        ylim=ylim,
        xticks=[(float(i), a) for i, a in enumerate(ages)],
        yticks=yticks,
        xlabel="年龄段",
        ylabel="1000日元",
        zero_line=False,
        lines=[
            LineSeries(x=xs, y=first[1], label=first[0], color_idx=2, style="dashed", marker="diamond", width=2.2),
            LineSeries(x=xs, y=second[1], label=second[0], color_idx=0, style="solid", marker="square", width=2.4),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(fig_id=fig_id, title=title, panels=[panel], note=note, width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_10_6(mode: ThemeMode = "mono") -> str:
    return _wage_figure(
        "10-6",
        "图 10-6 标准劳动者各年龄段薪酬（大学毕业，月收入）",
        "资料来源：日本厚生劳动省",
        ("女性", [201.0, 240.0, 296.0, 352.0, 400.0, 457.0, 513.0, 567.0]),
        ("男性", [225.0, 268.0, 340.0, 411.0, 485.0, 567.0, 648.0, 657.0]),
        (0.0, 700.0),
        [0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0],
        mode,
    )


def _fig_10_7a(mode: ThemeMode = "mono") -> str:
    return _wage_figure(
        "10-7A",
        "图 10-7A 新员工各年龄段的薪酬（女性，月收入）",
        "",
        ("生产劳动者", [154.0, 150.0, 136.0, 136.0, 135.0, 134.0, 126.0, 126.0]),
        ("全体劳动者", [178.0, 189.0, 188.0, 182.0, 167.0, 169.0, 158.0, 167.0]),
        (0.0, 400.0),
        [0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0],
        mode,
    )


def _fig_10_7b(mode: ThemeMode = "mono") -> str:
    return _wage_figure(
        "10-7B",
        "图 10-7B 新员工各年龄段的薪酬（男性，月收入）",
        "资料来源：日本厚生劳动省",
        ("生产劳动者", [180.0, 204.0, 217.0, 236.0, 233.0, 234.0, 232.0, 222.0]),
        ("全体劳动者", [198.0, 231.0, 275.0, 303.0, 290.0, 285.0, 289.0, 292.0]),
        (0.0, 600.0),
        [0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
        mode,
    )


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "9-1": _fig_9_1,
        "9-2": _fig_9_2,
        "9-3": _fig_9_3,
        "9-4": _fig_9_4,
        "9-5": _fig_9_5,
        "9-6": _fig_9_6,
        "10-1": _fig_10_1,
        "10-2": _fig_10_2,
        "10-3": _fig_10_3,
        "10-4": _fig_10_4,
        "10-6": _fig_10_6,
        "10-7A": _fig_10_7a,
        "10-7B": _fig_10_7b,
    }
