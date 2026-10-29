from __future__ import annotations

from collections.abc import Callable, Sequence

from scripts.book2_figures.engine import (
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    render_figure_svg,
)

MONO_SOLID_BLACK = 0
MONO_SOLID_LIGHT = 5
MONO_SOLID_MID = 10
MONO_SOLID_SLATE = 20


def _steps(start: float, step: float, n: int) -> list[float]:
    return [start + step * i for i in range(n)]


def _year_ticks(first: int, last: int, every: int = 1) -> list[float | tuple[float, str]]:
    return [(float(y), str(y)) for y in range(first, last + 1, every)]


def _fixed_ticks(values: Sequence[float], digits: int) -> list[float | tuple[float, str]]:
    return [(v, f"{v:.{digits}f}") for v in values]


def _fig_1_1(mode: ThemeMode = "mono") -> str:
    gdp = [
        4.2, 2.1, 2.8, 3.4, 2.6, 3.1, 3.0, 2.2, 2.7, 3.9,
        3.8, 3.9, 4.0, 2.9, 3.2, 3.4, 5.5, 6.1, 5.0, 4.1,
        4.1, 5.6, 5.1, 3.2, 1.9, 0.8, -0.4, 0.4, 0.2, 0.6,
        0.3, 1.1, 4.2, 4.3, 4.0, 0.6, -2.6, 0.4, 0.7, 0.7,
    ]
    land = [
        6.4, 7.9, 9.0, 8.2, 7.6, 6.9, 5.8, 4.8, 3.8, 3.2,
        2.9, 2.8, 2.6, 2.7, 4.0, 6.5, 10.0, 9.5, 6.0, 7.2,
        9.2, 13.2, 14.8, 9.5, 2.5, -2.0, -5.0, -5.9, -5.4, -4.8,
        -4.4, -4.1, -4.3, -4.6, -4.8, -4.4, -4.1, -3.9, -4.2, -5.3,
    ]
    xs = _steps(1980.0, 0.5, len(gdp))
    spec = FigureSpec(
        fig_id="1-1",
        title="图 1-1 经济增长与地价上升率（实质）",
        width=860,
        height=520,
        panels=[
            PanelSpec(
                xlim=(1979.8, 2000.0),
                ylim=(-10.0, 20.0),
                xticks=_year_ticks(1980, 1999),
                yticks=_fixed_ticks([-10, -5, 0, 5, 10, 15, 20], 1),
                ylabel="%",
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=gdp, label="经济增长率", color_idx=MONO_SOLID_LIGHT, width=2.4),
                    LineSeries(x=xs, y=land, label="地价上升率", color_idx=MONO_SOLID_BLACK, style="dashed", width=2.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_2(mode: ThemeMode = "mono") -> str:
    land = [
        1060, 1130, 1170, 1215, 1250, 1285, 1310, 1340, 1360, 1385,
        1400, 1420, 1440, 1470, 1500, 1630, 1680, 1750, 1810, 1890,
        2050, 2210, 2270, 2270, 2220, 2160, 2100, 2050, 2000, 1960,
        1920, 1880, 1840, 1810, 1770, 1740, 1700, 1660, 1620, 1570,
        1530, 1480, 1430, 1380, 1330, 1280, 1240, 1190, 1140, 1100,
        1060, 1045,
    ]
    stock = [
        130, 140, 148, 155, 160, 150, 170, 185, 200, 225,
        250, 270, 290, 360, 410, 540, 520, 620, 700, 770,
        800, 640, 540, 540, 500, 385, 385, 450, 435, 450,
        410, 370, 430, 480, 445, 440, 375, 345, 340, 400,
        420, 395, 320, 280, 250, 240, 205, 210, 250, 265,
        270, 280,
    ]
    gni = [
        205, 235, 230, 250, 245, 265, 255, 280, 285, 300,
        295, 315, 320, 340, 330, 355, 355, 375, 380, 410,
        400, 440, 445, 470, 475, 490, 480, 490, 485, 510,
        505, 515, 505, 520, 515, 530, 520, 520, 510, 515,
        515, 520, 515, 515, 510, 510, 515, 515, 515, 520,
        520, 520,
    ]
    xs = _steps(1980.0, 0.5, len(land))
    xs[-1] = 2005.4
    spec = FigureSpec(
        fig_id="1-2",
        title="图 1-2 土地总市值与 GDP 的推移",
        width=860,
        height=520,
        panels=[
            PanelSpec(
                xlim=(1979.8, 2005.5),
                ylim=(0.0, 2500.0),
                xticks=_year_ticks(1980, 2005),
                yticks=[0, 500, 1000, 1500, 2000, 2500],
                ylabel="兆日元",
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=land, label="地价", color_idx=MONO_SOLID_LIGHT, width=2.4),
                    LineSeries(x=xs, y=stock, label="股价", color_idx=MONO_SOLID_MID, width=2.4),
                    LineSeries(x=xs, y=gni, label="国民总收入（年率换算）", color_idx=MONO_SOLID_BLACK, style="dashed", width=2.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_3(mode: ThemeMode = "mono") -> str:
    manufacturing = [
        63, 65, 67, 69.5, 72, 74, 76.5, 78, 79.5, 80, 83.5,
        83.5, 84, 83.5, 82, 79.5, 79, 77, 78, 75, 78, 76.5, 78.5, 77.5,
        80, 79, 80, 77.5, 79.5, 76, 77.5, 74.5, 73.5, 70.5, 70, 67.5,
        69.5, 67.5, 69, 71, 72.5, 68.5, 68.5, 65.5, 64, 60, 57.5,
    ]
    finance = [
        7, 7, 8, 8.5, 10, 11, 13, 15, 17.5, 20, 22.5,
        24, 28, 30, 34.5, 38, 43.5, 42.5, 48.5, 51, 60.5, 57, 58.5, 55.5,
        59, 56.5, 57, 55, 55, 55, 55.5, 55, 53, 50, 51, 49.5,
        48.5, 47.5, 45, 45, 43.5, 41.5, 41, 38, 38, 36, 37,
    ]
    construction = [
        11, 11, 11.5, 12, 13.5, 13, 14, 14.5, 15.5, 16, 17.5,
        18.5, 19, 19.5, 20.5, 20, 20.5, 21, 22, 22, 23.5, 23.5, 24.5, 25,
        27.5, 28, 29.5, 29, 30.5, 30, 31, 30.5, 31, 30, 30.5, 29.5,
        31, 30, 31, 30, 30, 28, 28.5, 25, 26, 22.5, 21,
    ]
    real_estate = [
        11, 11.5, 12, 13, 14, 15, 16, 17, 18, 19.5, 20.5,
        23.5, 26, 30, 35, 38, 40, 42, 44.5, 47.5, 52, 52, 52.5, 53,
        55, 57, 58.5, 59, 60, 60.5, 61, 62, 62.5, 62.5, 63.5, 63.5,
        65.5, 65.5, 64.5, 64, 62, 60, 59, 56.5, 56, 53.5, 51,
    ]
    wholesale = [
        53, 54, 55, 57, 59.5, 62, 64, 65.5, 67, 69, 71.5,
        73, 75, 74.5, 76, 76, 78, 78.5, 81, 82.5, 85, 86.5, 87.5, 86,
        86.5, 83.5, 84, 81, 81.5, 81.5, 81, 79.5, 79, 77.5, 77.5, 76,
        77.5, 75.5, 75, 76, 75.5, 72, 71.5, 67.5, 65, 61, 59.5,
    ]
    xs = _steps(1980.0, 0.5, len(wholesale) - 1) + [2002.75]
    spec = FigureSpec(
        fig_id="1-3",
        title="图 1-3 各行业贷款余额",
        width=860,
        height=540,
        panels=[
            PanelSpec(
                xlim=(1980.0, 2003.0),
                ylim=(0.0, 100.0),
                xticks=_year_ticks(1980, 2002),
                yticks=list(range(0, 101, 10)),
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=manufacturing, label="制造业", color_idx=MONO_SOLID_LIGHT, width=2.2),
                    LineSeries(x=xs, y=finance, label="金融/保险业", color_idx=2, style="dashed", width=2.0),
                    LineSeries(x=xs, y=construction, label="建筑业", color_idx=1, style="dotted", width=2.2),
                    LineSeries(x=xs, y=real_estate, label="房地产业", color_idx=3, style="dashdot", width=2.0),
                    LineSeries(x=xs, y=wholesale, label="批发业", color_idx=MONO_SOLID_BLACK, width=2.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_4(mode: ThemeMode = "mono") -> str:
    years = _steps(1980.0, 1.0, 24)
    nominal_growth = [
        None, 6.2, 4.9, 4.4, 7.3, 6.9, 4.4, 5.2, 7.5, 7.5, 8.4, 5.0,
        2.5, -0.7, 2.1, 1.8, 3.2, 1.2, -1.5, -1.0, 1.1, -2.0, -0.5, 0.8,
    ]
    bond_yield = [
        8.4, 8.2, 8.0, 7.7, 7.4, 6.9, 5.5, 4.9, 5.0, 5.0, 6.6, 6.3,
        5.3, 4.3, 4.2, 3.5, 3.2, 2.5, 1.6, 1.7, 1.8, 1.4, 1.4, 1.1,
    ]
    deposit_rate = [
        5.4, 4.3, 3.8, 3.8, 3.5, 3.4, 2.4, 1.8, 1.8, 2.0, 3.6, 4.1,
        3.4, 2.1, 1.6, 0.9, 0.3, 0.3, 0.3, 0.1, 0.1, 0.0, 0.0, None,
    ]
    lending_rate = [
        8.3, 7.8, 7.3, 7.1, 6.8, 6.6, 6.0, 5.3, 5.1, 5.4, 7.0, 7.5,
        6.1, 5.0, 4.0, 3.4, 2.7, 2.5, 2.4, 2.3, 2.2, 2.0, 2.0, 1.8,
    ]
    spec = FigureSpec(
        fig_id="1-4",
        title="图 1-4 利率与增长率（名义）",
        width=860,
        height=540,
        panels=[
            PanelSpec(
                xlim=(1979.6, 2003.6),
                ylim=(-4.0, 10.0),
                xticks=_year_ticks(1980, 2003),
                yticks=_fixed_ticks([-4, -2, 0, 2, 4, 6, 8, 10], 1),
                ylabel="%",
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=years, y=nominal_growth, label="名义经济增长率", color_idx=MONO_SOLID_LIGHT, width=2.2),
                    LineSeries(x=years, y=bond_yield, label="国债收益率", color_idx=MONO_SOLID_MID, width=2.2),
                    LineSeries(x=years, y=deposit_rate, label="存款利率（3个月）", color_idx=1, style="dotted", width=2.4),
                    LineSeries(x=years, y=lending_rate, label="贷款利率", color_idx=MONO_SOLID_BLACK, style="dashed", width=2.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_6(mode: ThemeMode = "mono") -> str:
    printed_years = [1970] + list(range(1973, 1999))
    share = [
        40, 43, 42.5, 45.5, 45.5, 45.5, 48, 48, 46.5, 48, 48, 49, 47.5, 49,
        51, 52, 52, 52, 52, 52, 54.5, 56, 57, 57, 57, 57, 58,
    ]
    xs = _steps(0.0, 1.0, len(share))
    spec = FigureSpec(
        fig_id="1-6",
        title="图 1-6 非贸易品市场份额（名义）",
        width=860,
        height=400,
        panels=[
            PanelSpec(
                xlim=(-0.6, 26.6),
                ylim=(0.0, 70.0),
                xticks=[(float(i), str(y)) for i, y in enumerate(printed_years)],
                yticks=list(range(0, 71, 10)),
                ylabel="%",
                xlabel="年",
                legend_loc="none",
                lines=[LineSeries(x=xs, y=share, color_idx=MONO_SOLID_SLATE, width=2.4)],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_7(mode: ThemeMode = "mono") -> str:
    yen_per_dollar = [
        200, 213, 225, 213, 218, 235, 252, 235, 226, 233, 237, 232,
        220, 228, 240, 250, 246, 225, 200, 175, 164, 157, 154, 147,
        139, 144, 126, 124, 126, 133, 126, 129, 133, 137, 141, 146,
        152, 127, 128, 133, 136, 133, 127, 125, 127, 120, 120, 115,
        107, 101, 105, 104, 101, 99, 96, 87, 81, 85, 100, 105,
        107, 110, 116, 113, 114, 120, 125, 129, 128, 115, 110, 118,
        107, 103, 102, 103, 105, 107, 112, 120, 118, 120, 128, 118,
        117, 120, 118, 116, 112, 107, 104, 104, 107, 103, 102, 107,
        111, 114, 113, 110, 115, 117, 117, 112,
    ]
    xs = _steps(1981.0, 0.25, len(yen_per_dollar))
    spec = FigureSpec(
        fig_id="1-7",
        title="图 1-7 汇率",
        width=860,
        height=420,
        panels=[
            PanelSpec(
                xlim=(1981.0, 2007.0),
                ylim=(0.0, 300.0),
                xticks=_year_ticks(1981, 2006),
                yticks=list(range(0, 301, 50)),
                ylabel="日元/美元",
                xlabel="年",
                legend_loc="none",
                lines=[LineSeries(x=xs, y=yen_per_dollar, color_idx=MONO_SOLID_SLATE, width=2.2)],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_8(mode: ThemeMode = "mono") -> str:
    real_estate = [
        9.5, 11.5, 14, 15, 16, 17, 17.5, 18, 19, 20.5, 20.5, 20,
        19, 18.5, 18.5, 17.5, 16.5, 16.5, 17, 18.5,
        19.5, 21.5, 20.5, 22, 22.5, 22.5, 20, 17, 15, 13.5, 11.5, 11,
        10.5, 11, 13, 14.5, 15.5, 11, 5, 2, -0.5, 1.5, 1, 2.5,
        3, 2.5, 4, 3, 2, 1.5, 1.5, 0.5, -0.5, 1.5, 1.5, 2,
        1.8, 1.8, 1.8, 1, -1.5, -1, -3.5, -2, -1.5, -1, 0, 1,
        -0.5, -1.5, -2, -3, -4.5, -2.5, -2.5, -5, -0.5, -7.5, -7, -6,
        -6, -6.5, -7, -6, -6.5, -7, -6, -8,
    ]
    tradables = [
        7.5, 8.5, 7.5, 7, 6.8, 6.5, 6.5, 5.5, 4.8, 4.2, 4.2, 4,
        5.8, 4.5, 5.8, 6, 3, 4.5, 1.5, 0.7,
        0.7, 0.5, -1, -2, -3, -3.3, -3.2, -2.3, -1.2, -0.5, -0.5, -1,
        0.5, 1, 2, 3.3, 2.3, 1, 2.3, 3.3, 3, 1, 3, 0,
        0, 0.5, 0, 0.5, -0.5, -1, -1.5, -2, -1.8, -1.5, -2.5, -2,
        -1.8, -1.5, -2, -2.5, -1.5, -1.5, -3, -2, -2.5, -2.5, -2, -2,
        -1, -0.5, 0.5, -1, 2.5, 3.5, 0, 4.5, -2, -1.5, -2.5, -2.5,
        -1.5, -3.5, -4.5, -5, -5.5, -7, -7.5, -7,
    ]
    non_tradables = [
        7.5, 8, 10.5, 11.8, 12, 12, 12, 12, 12, 12, 12, 12,
        10.5, 13.5, 11, 12.5, 13.5, 9.5, 13.5, 12,
        11.5, 12.5, 13, 12.5, 13.5, 14.5, 13.5, 12.5, 11.5, 10.5, 10, 11,
        10, 12, 12, 12.5, 12, 9, 6, 4, 4.5, 3, 2, 3,
        2.5, 2.5, 2.5, 1.8, 1, -0.5, -0.5, -1, -0.5, 0.5, 0, 0,
        0, 0.5, 1.5, 0.5, 1, 2, -1, 0, -0.5, -0.5, 0, 0.5,
        -1, -1, -1.5, -2, -4, -1.5, -1, -3.5, 0.5, -5, -4, -4,
        -4, -4, -4.5, -4.5, -5, -4.5, -6, -5,
    ]
    xs = _steps(1981.0, 0.25, len(real_estate))
    spec = FigureSpec(
        fig_id="1-8",
        title="图 1-8 贷款余额变化率",
        width=860,
        height=480,
        panels=[
            PanelSpec(
                xlim=(1981.0, 2003.0),
                ylim=(-10.0, 25.0),
                xticks=_year_ticks(1981, 2002),
                yticks=list(range(-10, 26, 5)),
                ylabel="%",
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=real_estate, label="房地产相关3个行业", color_idx=MONO_SOLID_LIGHT, width=2.2),
                    LineSeries(x=xs, y=tradables, label="贸易品", color_idx=MONO_SOLID_MID, width=2.2),
                    LineSeries(x=xs, y=non_tradables, label="非贸易品", color_idx=MONO_SOLID_BLACK, style="dashed", width=2.2),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _irf_panel(
    title: str,
    ylim: tuple[float, float],
    yticks: Sequence[float],
    xs: Sequence[float],
    response: Sequence[float],
    upper: Sequence[float],
    lower: Sequence[float],
) -> PanelSpec:
    return PanelSpec(
        title=title,
        xlim=(1.0, 20.0),
        ylim=ylim,
        xticks=list(range(1, 20, 2)),
        yticks=[(v, f"{v:g}") for v in yticks],
        legend_loc="none",
        lines=[
            LineSeries(x=xs, y=upper, color_idx=MONO_SOLID_BLACK, style="dashed", width=1.2),
            LineSeries(x=xs, y=lower, color_idx=MONO_SOLID_BLACK, style="dashed", width=1.2),
            LineSeries(x=xs, y=response, color_idx=MONO_SOLID_SLATE, width=3.2),
        ],
    )


def _fig_1_9(mode: ThemeMode = "mono") -> str:
    xs = [1, 3, 5, 7, 9, 11, 13, 15, 17, 20]
    xs_land = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 20]
    xs_rate = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 17, 19, 20]
    xs_loan = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 20]
    panels = [
        _irf_panel(
            "产出", (-0.02, 0.025),
            [-0.02, -0.015, -0.01, -0.005, 0, 0.005, 0.01, 0.015, 0.02, 0.025], xs,
            [0, 0.0035, 0.0055, 0.0067, 0.0072, 0.0076, 0.008, 0.0083, 0.0087, 0.0091],
            [0, 0.007, 0.0108, 0.0135, 0.0158, 0.0175, 0.0188, 0.0198, 0.0205, 0.021],
            [0, 0.0012, 0.0012, 0.0005, -0.0005, -0.0015, -0.0022, -0.0026, -0.0028, -0.0027],
        ),
        _irf_panel(
            "投资", (-0.06, 0.08), [-0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06, 0.08], xs,
            [-0.004, 0.003, 0.011, 0.018, 0.024, 0.027, 0.027, 0.027, 0.027, 0.027],
            [0.0, 0.014, 0.027, 0.04, 0.05, 0.056, 0.059, 0.06, 0.061, 0.06],
            [-0.006, -0.005, -0.002, 0.0, 0.0005, -0.0005, -0.002, -0.004, -0.0055, -0.006],
        ),
        _irf_panel(
            "地价", (-0.1, 0.25), [-0.1, -0.05, 0, 0.05, 0.1, 0.15, 0.2, 0.25], xs_land,
            [0.012, 0.032, 0.05, 0.066, 0.077, 0.082, 0.086, 0.089, 0.09, 0.089, 0.083],
            [0.01, 0.035, 0.06, 0.085, 0.107, 0.126, 0.14, 0.15, 0.155, 0.157, 0.155],
            [0.012, 0.029, 0.039, 0.045, 0.047, 0.045, 0.04, 0.033, 0.026, 0.018, 0.015],
        ),
        _irf_panel(
            "利息", (-0.006, 0.006), [-0.006, -0.004, -0.002, 0, 0.002, 0.004, 0.006], xs_rate,
            [0.0038, 0.0003, -0.0015, -0.0023, -0.0026, -0.0028, -0.0027,
             -0.0021, -0.0014, -0.0007, -0.0001, 0.0002, 0.0004, 0.0005],
            [0.0052, 0.002, 0.0002, -0.0008, -0.0012, -0.0012, -0.001,
             0.0, 0.0008, 0.0013, 0.0017, 0.0018, 0.0019, 0.0019],
            [0.0038, -0.0015, -0.0035, -0.0041, -0.0044, -0.0045, -0.0044,
             -0.0036, -0.0028, -0.002, -0.0015, -0.0011, -0.0009, -0.001],
        ),
        _irf_panel(
            "贷款", (-0.1, 0.06), [-0.1, -0.08, -0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06], xs_loan,
            [0.005, 0.01, 0.011, 0.013, 0.016, 0.019, 0.022, 0.025, 0.027, 0.029, 0.029],
            [0.007, 0.016, 0.018, 0.02, 0.025, 0.031, 0.037, 0.043, 0.048, 0.052, 0.054],
            [0.002, 0.005, 0.005, 0.005, 0.007, 0.008, 0.008, 0.008, 0.008, 0.007, 0.006],
        ),
    ]
    spec = FigureSpec(
        fig_id="1-9",
        title="图 1-9 (A) 对于地价冲击各变量的冲击反应——地价上升期",
        rows=3,
        cols=2,
        width=860,
        height=900,
        panels=panels,
    )
    return render_figure_svg(spec, mode)


def _quarter_label(x: float) -> str:
    year = int(x)
    quarter = round((x - year) * 4) + 1
    return f"{year}年第{'一二三四'[quarter - 1]}季度"


def _fig_1_10(mode: ThemeMode = "mono") -> str:
    large_boj = [
        249, 246, 244, 245, 244, 242, 240, 244, 246, 246,
        244, 248, 246, 246, 246, 246, 252, 251, 251, 251, 252, 252, 260, 262, 263, 261, 242,
        238, 241, 238, 236, 236, 238, 234, 233, 230, 233, 231, 230, 228, 230, 225, 224,
        220, 219, 219, 215, 216, 219, 220, 221, 215, 220, 220, 218, 220, 225, 227, 228,
    ]
    small_boj = [
        262, 260, 257, 260, 264, 260, 259, 263, 265, 263,
        260, 261, 259, 257, 254, 254, 258, 250, 248, 246, 248, 240, 234, 233, 231, 226, 233,
        238, 237, 236, 224, 223, 219, 216, 207, 203, 201, 198, 189, 188, 186, 188, 180,
        181, 182, 183, 175, 178, 180, 184, 181, 187, 188, 188, 184, 186, 186, 186, 185,
    ]
    large_mof = [
        229, 230, 233, 230, 229, 230, 229, 230, 229, 230,
        233, 229, 232, 228, 231, 229, 233, 228, 230, 226, 229, 228, 226, 224, 220, 216, 211,
        208, 206, 199, 200, 197, 197, 192, 197, 191, 188, 184, 178, 173, 168, 165, 163,
        165, 164, 161, 156, 153, 153, 152, 154, 156, 157, 155, 154, 151, 153, 153, 154,
    ]
    small_mof = [
        198, 195, 189, 190, 191, 191, 205, 215, 222, 228,
        203, 198, 203, 203, 202, 206, 207, 199, 211, 206, 205, 205, 210, 206, 217, 213, 206,
        204, 201, 207, 201, 189, 197, 190, 179, 172, 178, 176, 162, 159, 159, 160, 178,
        174, 174, 177, 163, 154, 154, 147, 157, 158, 157, 158, 155, 157, 161, 154, 155,
    ]
    xs = _steps(1993.75, 0.25, len(large_boj))
    tick_xs = _steps(1993.75, 0.75, 20)

    def scaled(values: Sequence[float]) -> list[float]:
        return [v * 10000 for v in values]

    spec = FigureSpec(
        fig_id="1-10",
        title="图 1-10 贷款余额的变化",
        width=860,
        height=540,
        panels=[
            PanelSpec(
                xlim=(1993.6, 2008.3),
                ylim=(0.0, 3000000.0),
                xticks=[(x, _quarter_label(x)) for x in tick_xs],
                yticks=[(v, str(v)) for v in range(0, 3000001, 500000)],
                ylabel="亿日元",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=scaled(large_mof), label="大企业（法季）", color_idx=MONO_SOLID_LIGHT, width=2.2),
                    LineSeries(x=xs, y=scaled(small_mof), label="中小企业（法季）", color_idx=2, style="dotted", width=2.4),
                    LineSeries(x=xs, y=scaled(large_boj), label="大企业（日银）", color_idx=MONO_SOLID_MID, width=2.4),
                    LineSeries(x=xs, y=scaled(small_boj), label="中小企业（日银）", color_idx=MONO_SOLID_BLACK, style="dashed", width=2.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_11(mode: ThemeMode = "mono") -> str:
    years = _steps(1993.0, 1.0, 13)
    deferred_tax_top = [0, 0, 0, 0, 0, 0, 1.95, 1.8, 1.65, 2.8, 2.5, 1.8, 1.5]
    tier1_top = [5.0, 5.2, 5.25, 4.75, 4.8, 5.0, 6.3, 6.85, 6.5, 5.8, 5.05, 6.1, 6.7]
    securities_top = [6.7, 7.2, 6.1, 6.3, 5.6, 5.25, 6.6, 7.55, 6.5, 6.05, 5.25, 6.6, 7.3]
    allowance_top = [7.2, 7.55, 6.5, 6.7, 6.0, 5.7, 7.3, 8.3, 7.25, 7.05, 6.75, 7.75, 8.1]
    subordinated_top = [9.5, 9.95, 9.0, 9.6, 9.25, 9.5, 11.5, 12.0, 9.75, 9.85, 9.55, 10.8, 11.25]
    tier2_end = [-0.2, -0.2, 9.0, -0.3, -0.1, 9.75, 11.65, 12.2, 11.7, 11.1, 10.6, 12.0, 12.35]
    tier2_bottom = [0.0 if end < 0 else top for end, top in zip(tier2_end, subordinated_top)]

    def layer(label: str, color_idx: int, bottom: Sequence[float], top: Sequence[float]) -> BarSeries:
        return BarSeries(
            x=years,
            y=[t - b for b, t in zip(bottom, top)],
            bottom=list(bottom),
            label=label,
            color_idx=color_idx,
            width=0.45,
            opacity=1.0,
        )

    spec = FigureSpec(
        fig_id="1-11",
        title="图 1-11 大银行的自有资本构成项目（1993—2005）",
        width=860,
        height=540,
        panels=[
            PanelSpec(
                xlim=(1992.4, 2005.6),
                ylim=(-2.0, 14.0),
                xticks=_year_ticks(1993, 2005),
                yticks=list(range(-2, 15, 2)),
                ylabel="%",
                xlabel="年",
                legend_loc="bottom",
                bars=[
                    layer("其他Tier2", 4, tier2_bottom, tier2_end),
                    layer("劣后债权", 2, allowance_top, subordinated_top),
                    layer("坏账准备", 1, securities_top, allowance_top),
                    layer("有价证券评估收益", 5, tier1_top, securities_top),
                    layer("其他Tier1", 3, deferred_tax_top, tier1_top),
                    layer("递延税金资产", 0, [0.0] * 13, deferred_tax_top),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_1_12(mode: ThemeMode = "mono") -> str:
    years = _steps(2000.0, 1.0, 8)
    spec = FigureSpec(
        fig_id="1-12",
        title="图 1-12 地价上升率（商业用地）",
        width=860,
        height=520,
        panels=[
            PanelSpec(
                xlim=(1999.5, 2007.5),
                ylim=(-15.0, 35.0),
                xticks=_year_ticks(2000, 2007),
                yticks=list(range(-15, 36, 5)),
                ylabel="%",
                xlabel="年",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=years, y=[-6.4, -7.0, -6.8, -4.2, -0.8, 2.0, 12.0, 23.5], label="千代田区",
                               color_idx=MONO_SOLID_LIGHT, marker="square", width=2.2),
                    LineSeries(x=years, y=[-5.2, -2.0, -1.4, -0.9, 0.9, 5.0, 20.5, 29.5], label="港区",
                               color_idx=MONO_SOLID_MID, marker="cross", width=2.2),
                    LineSeries(x=years, y=[-9.2, -7.6, -6.6, -5.7, -3.6, -1.1, 4.6, 12.6], label="东京圈",
                               color_idx=1, style="dashed", marker="circle", width=2.2),
                    LineSeries(x=years, y=[-11.3, -10.9, -10.5, -10.0, -7.6, -3.0, 4.0, 8.3], label="大阪圈",
                               color_idx=MONO_SOLID_BLACK, width=2.4),
                    LineSeries(x=years, y=[-6.4, -6.7, -7.0, -7.2, -5.9, -4.5, -1.5, 1.7], label="全国平均",
                               color_idx=MONO_SOLID_BLACK, style="dotted", width=2.6),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_2_1(mode: ThemeMode = "mono") -> str:
    years = _steps(1950.0, 1.0, 58)
    markup_2000 = [
        0.1, 0.0, 0.05, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.2,
        0.8, 1.1, 1.0, 0.9, 1.2, 1.1, 1.8, 2.4, 2.6, 2.7, 2.4, 2.8, 2.5, 2.2, 4.0, 4.2,
        3.3, 3.7, 2.8, 1.8, 2.1, 2.0, 2.0, 2.0, 2.0, 1.9, 1.7, 1.6, 1.4, 1.3, 1.3, 1.3, 1.2,
    ]
    markup_4000 = [
        -0.1, -0.3, -0.05, -0.1, -0.4, -0.1, -0.1, -0.2, -0.25, -0.3, -0.2,
        -0.2, -0.25, -0.2, -0.2, -0.25, -0.25, -0.2, 0.0, 0.05,
        0.05, 0.05, 0.0, 0.0, 0.3,
        1.8, 2.5, 2.0, 2.1, 2.3, 2.0, 3.0, 3.6, 3.7, 4.2, 3.8, 4.5, 3.9, 3.3, 7.5, 6.9,
        5.3, 7.2, 4.1, 3.0, 3.5, 3.4, 3.3, 3.25, 3.2, 3.2, 2.8, 2.8, 2.3, 2.2, 2.2, 2.2, 2.1,
    ]
    markup_10000 = [
        -0.5, -0.7, -0.3, -0.2, -0.4, -0.2, -0.5, -0.8, -1.1, -0.4, -0.3,
        -0.2, -0.4, -0.45, -0.35, -0.45, -0.45, -0.45, -0.1, 0.4,
        0.3, 0.3, 0.15, 0.2, 0.3,
        4.0, 5.3, 4.1, 3.6, 5.2, 4.0, 6.5, 7.7, 7.7, 7.7, 8.2, 10.7, 7.8, 5.5, 12.0, 12.5,
        9.8, 12.2, 8.0, 6.0, 5.7, 5.7, 5.5, 5.5, 5.4, 5.3, 5.4, 5.6, 3.45, 3.4, 3.4, 3.4, 3.3,
    ]
    farmland_price = [
        1, 1, 1, 1, 2, 2, 2, 2, 2, 8,
        10, 11, 12, 13, 14, 15, 16, 17, 20, 22,
        25, 28, 35, 48, 64, 68, 70, 72, 88, 100, 140, 145, 150, 153, 157, 180,
        203, 265, 400, 388, 365, 453, 360, 310, 307, 300, 294, 292, 286, 282, 279,
        277, 272, 265, 265, 257, 254, 252,
    ]
    spec = FigureSpec(
        fig_id="2-1",
        title="图 2-1 农业用地针对市场价格的加价率",
        width=860,
        height=540,
        panels=[
            PanelSpec(
                xlim=(1949.5, 2007.5),
                ylim=(-2.0, 14.0),
                y2lim=(0.0, 500.0),
                xticks=_year_ticks(1950, 2005, 5),
                yticks=_fixed_ticks(range(-2, 15, 2), 1),
                y2ticks=list(range(0, 501, 50)),
                ylabel="针对市场地价的加价率",
                y2label="1000日元",
                xlabel="年",
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=years, y=markup_2000, label="2000m²", color_idx=2, style="dotted", width=2.4),
                    LineSeries(x=years, y=markup_4000, label="4000m²", color_idx=MONO_SOLID_LIGHT, width=2.2),
                    LineSeries(x=years, y=markup_10000, label="10000m²", color_idx=1, style="dashed", width=2.4),
                    LineSeries(x=years, y=farmland_price, label="农业用地地价（右轴）", color_idx=MONO_SOLID_BLACK,
                               axis="y2", width=2.6),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def _fig_2_2(mode: ThemeMode = "mono") -> str:
    years = _steps(1950.0, 1.0, 58)
    markup_500: list[float | None] = [
        None, None, 0.0, 0.03, 0.08, 0.14, 0.07, 0.16, 0.14, 0.18,
        0.24, 0.2, 0.31, 0.37, 0.39, 0.41, 0.36, 0.41, 0.39, 0.15,
        0.19, 0.21, 0.25, 0.29, 0.34, 0.11, 0.1, 0.1, 0.12, 0.13,
        0.19, 0.25, 0.28, 0.3, 0.31, 0.28, 0.24, 0.5, 0.68, 0.57,
        0.65, 0.7, 0.69, 0.6, 0.47, 0.38, 0.3, 0.23, 0.22, 0.24,
        0.18, 0.13, 0.12, 0.1, 0.08, 0.075, 0.07, 0.06,
    ]
    markup_1000: list[float | None] = [
        None, 0.0, 0.0, 0.05, 0.14, 0.21, 0.18, 0.22, 0.21, 0.18,
        0.13, 0.15, 0.19, 0.13, 0.13, 0.16, 0.19, 0.16, 0.18, 0.22,
        0.26, 0.27, 0.26, 0.33, 0.43, 0.24, 0.24, 0.21, 0.22, 0.22,
        0.23, 0.26, 0.31, 0.33, 0.34, 0.31, 0.26, -0.05, 0.2, 0.18,
        0.2, 0.4, 0.37, 0.36, 0.33, 0.17, 0.24, 0.25, 0.24, 0.27,
        0.24, 0.2, 0.19, 0.17, 0.15, 0.14, 0.14, 0.13,
    ]
    markup_1500: list[float | None] = [
        0.65, 0.0, 0.0, 0.08, 0.13, 0.18, 0.12, 0.1, 0.11, 0.08,
        0.05, 0.07, 0.05, 0.06, 0.03, 0.03, 0.03, 0.0, 0.2, 0.25,
        0.26, 0.13, -0.01, 0.2, -0.23, 0.25, 0.18, 0.2, 0.2, 0.21,
        0.29, 0.25, 0.17, 0.11, 0.04, -0.02, -0.07, 0.03, 0.29, 0.29,
        0.3, 0.56, 0.38, 0.27, 0.15, -0.05, -0.05, 0.02, 0.04, 0.08,
        0.09, 0.06, 0.08, 0.12, 0.16, 0.15, 0.14, 0.13,
    ]
    housing_price: list[float | None] = [
        None, None, None, None, None, None, None, 0, 0, 2,
        9, 13, 17, 20, 23, 26, 30, 34, 34, 34,
        43, 52, 60, 68, 77, 103, 124, 111, 111, 116,
        124, 154, 189, 223, 249, 261, 274, 283, 377, 771,
        1020, 1011, 1020, 1020, 917, 754, 626, 580, 514, 429,
        411, 390, 364, 351, 334, 321, 309, 309,
    ]
    spec = FigureSpec(
        fig_id="2-2",
        title="图 2-2 住宅用地针对市场价格的加价率",
        width=860,
        height=540,
        panels=[
            PanelSpec(
                xlim=(1949.5, 2007.5),
                ylim=(-0.4, 1.0),
                y2lim=(0.0, 1200.0),
                xticks=_year_ticks(1950, 2005, 5),
                yticks=_fixed_ticks([-0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0], 1),
                y2ticks=list(range(0, 1201, 200)),
                ylabel="针对市场地价的加价率",
                y2label="1000日元",
                xlabel="年",
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=years, y=markup_500, label="500m²", color_idx=MONO_SOLID_LIGHT, width=2.2),
                    LineSeries(x=years, y=markup_1000, label="1000m²", color_idx=2, style="dashed", width=2.2),
                    LineSeries(x=years, y=markup_1500, label="1500m²", color_idx=1, style="dotted", width=2.6),
                    LineSeries(x=years, y=housing_price, label="住宅用地地价（右轴）", color_idx=MONO_SOLID_BLACK,
                               axis="y2", width=2.6),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "2-2": _fig_2_2,
        "2-1": _fig_2_1,
        "1-12": _fig_1_12,
        "1-11": _fig_1_11,
        "1-10": _fig_1_10,
        "1-9": _fig_1_9,
        "1-8": _fig_1_8,
        "1-7": _fig_1_7,
        "1-6": _fig_1_6,
        "1-1": _fig_1_1,
        "1-2": _fig_1_2,
        "1-3": _fig_1_3,
        "1-4": _fig_1_4,
    }
