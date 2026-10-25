from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

from scripts.book2_figures.engine import (
    Annotation,
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    render_figure_svg,
)


def _labels(
    xs: Sequence[float],
    ys: Sequence[float],
    texts: Sequence[str],
    dys: Sequence[float],
    axis: Literal["y1", "y2"] = "y1",
) -> list[Annotation]:
    return [
        Annotation(
            x=x, y=y, text=t, dx=0.0, dy=dy, arrow=False, fontsize=9.0, axis=axis
        )
        for x, y, t, dy in zip(xs, ys, texts, dys)
    ]


def _markers(
    xs: Sequence[float], ys: Sequence[float], marker: str, color_idx: int
) -> LineSeries:
    """Unconnected markers: a None after every point makes each point its own segment."""
    mx: list[float] = []
    my: list[float | None] = []
    for x, y in zip(xs, ys):
        mx += [x, x]
        my += [y, None]
    return LineSeries(x=mx, y=my, marker=marker, color_idx=color_idx, width=0.0)


def _fig_7_2(mode: ThemeMode = "mono") -> str:
    years = [
        "1980",
        "1985",
        "1990",
        "1994",
        "1995",
        "1996",
        "1997",
        "1998",
        "1999",
        "2000",
        "2001",
        "2002",
        "2003",
        "2004",
        "2005",
    ]
    xs = [float(i) for i in range(len(years))]
    spend = [
        307332.0,
        325854.0,
        353731.0,
        408548.0,
        421417.0,
        431409.0,
        438067.0,
        445362.0,
        468878.0,
        480914.0,
        486589.0,
        475472.0,
        475922.0,
        476320.0,
        472829.0,
    ]
    share = [
        11.7,
        12.2,
        14.7,
        14.3,
        14.7,
        14.9,
        15.0,
        15.4,
        15.4,
        14.1,
        14.8,
        15.7,
        16.3,
        17.1,
        17.1,
    ]
    spend_dy = [
        22.0,
        -14.0,
        22.0,
        -14.0,
        22.0,
        -14.0,
        22.0,
        -14.0,
        22.0,
        -14.0,
        22.0,
        -14.0,
        22.0,
        -14.0,
        22.0,
    ]
    panel = PanelSpec(
        xlim=(-0.6, 14.6),
        ylim=(0.0, 500000.0),
        yticks=[float(v) for v in range(0, 500001, 50000)],
        y2lim=(0.0, 35.0),
        y2ticks=[(float(v), f"{v:.1f}") for v in range(0, 36, 5)],
        xticks=[(x, y) for x, y in zip(xs, years)],
        xlabel="年",
        ylabel="亿日元",
        y2label="%",
        zero_line=False,
        lines=[
            LineSeries(
                x=xs,
                y=spend,
                label="一般支出费用",
                color_idx=0,
                marker="diamond",
                width=2.0,
            ),
            LineSeries(
                x=xs,
                y=share,
                label="国库负担的医疗费用在一般支出中的占比（右轴）",
                color_idx=1,
                marker="square",
                width=2.0,
                axis="y2",
            ),
        ],
        annotations=_labels(xs, spend, [f"{v:.0f}" for v in spend], spend_dy)
        + _labels(xs, share, [f"{v:.1f}" for v in share], [-14.0] * len(xs), axis="y2"),
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-2",
        title="图 7-2 国库负担的医疗费在国家一般支出中的占比",
        panels=[panel],
        width=1060,
        height=560,
    )
    return render_figure_svg(spec, mode)


def _fig_7_3(mode: ThemeMode = "mono") -> str:
    years = [
        "1985",
        "1992",
        "1993",
        "1994",
        "1995",
        "1996",
        "1997",
        "1998",
        "1999",
        "2000",
        "2001",
        "2002",
        "2003",
    ]
    xs = [float(i) for i in range(len(years))]
    elderly = [4.1, 6.9, 7.5, 8.2, 8.9, 9.7, 10.3, 10.9, 11.8, 11.2, 11.7, 11.7, 10.6]
    national = [
        16.0,
        23.5,
        24.4,
        25.8,
        27.0,
        28.5,
        29.1,
        29.8,
        30.9,
        30.4,
        31.3,
        31.1,
        33.1,
    ]
    share = [6.2, 6.3, 6.6, 6.9, 7.2, 7.3, 7.4, 7.8, 8.3, 8.0, 8.5, 8.6, 9.0]
    panel = PanelSpec(
        xlim=(-0.6, 12.6),
        ylim=(0.0, 50.0),
        yticks=[(float(v), f"{v:.1f}") for v in range(0, 51, 5)],
        y2lim=(0.0, 10.0),
        y2ticks=[(float(v), f"{v:.1f}") for v in range(11)],
        xticks=[(x, y) for x, y in zip(xs, years)],
        xlabel="年",
        ylabel="万亿日元",
        y2label="%",
        zero_line=False,
        bars=[
            BarSeries(x=xs, y=elderly, label="老年人医疗费", color_idx=1, width=0.45),
            BarSeries(
                x=xs,
                y=national,
                bottom=elderly,
                label="国民医疗费",
                color_idx=4,
                width=0.45,
            ),
        ],
        lines=[
            LineSeries(
                x=xs,
                y=share,
                label="国民医疗费在国民收入中的占比（右轴）",
                color_idx=0,
                marker="triangle",
                width=2.0,
                axis="y2",
            ),
        ],
        annotations=_labels(
            xs, elderly, [f"{v:.1f}" for v in elderly], [-2.0] * len(xs)
        )
        + _labels(
            xs,
            [e + n / 2 for e, n in zip(elderly, national)],
            [f"{v:.1f}" for v in national],
            [6.0] * len(xs),
        )
        + _labels(xs, share, [f"{v:.1f}" for v in share], [-12.0] * len(xs), axis="y2"),
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-3",
        title="图 7-3 国民收入、国民医疗费和老年人医疗费的经年变化",
        panels=[panel],
        width=940,
        height=560,
    )
    return render_figure_svg(spec, mode)


def _fig_7_5(mode: ThemeMode = "mono") -> str:
    years = [
        "1955",
        "1960",
        "1965",
        "1970",
        "1975",
        "1980",
        "1985",
        "1990",
        "1993",
        "1996",
        "1999",
        "2002",
        "2004",
    ]
    xs = [float(i) for i in range(len(years))]
    no_bed = [
        33832.0,
        35200.0,
        37192.0,
        39800.0,
        44010.0,
        49300.0,
        52765.0,
        57900.0,
        61745.0,
        68600.0,
        73013.0,
        79500.0,
        82286.0,
    ]
    bed = [
        17517.0,
        23400.0,
        27332.0,
        28500.0,
        29104.0,
        28600.0,
        26162.0,
        23700.0,
        22383.0,
        20600.0,
        18487.0,
        16500.0,
        14765.0,
    ]
    hosp = [
        5119.0,
        5960.0,
        7047.0,
        7850.0,
        8294.0,
        8730.0,
        9608.0,
        9610.0,
        9844.0,
        9100.0,
        9286.0,
        9050.0,
        9077.0,
    ]
    labelled = [0, 2, 4, 6, 8, 10, 12]
    panel = PanelSpec(
        xlim=(-0.6, 12.6),
        ylim=(0.0, 90000.0),
        yticks=[float(v) for v in range(0, 90001, 10000)],
        xticks=[(x, y) for x, y in zip(xs, years)],
        xlabel="年",
        ylabel="设施数量（家）",
        zero_line=False,
        lines=[
            LineSeries(
                x=xs, y=hosp, label="医院", color_idx=2, marker="triangle", width=2.0
            ),
            LineSeries(
                x=xs, y=bed, label="有床诊所", color_idx=1, marker="square", width=2.0
            ),
            LineSeries(
                x=xs,
                y=no_bed,
                label="无床诊所",
                color_idx=0,
                marker="circle",
                width=2.0,
            ),
        ],
        annotations=_labels(
            [xs[i] for i in labelled],
            [no_bed[i] for i in labelled],
            [f"{no_bed[i]:.0f}" for i in labelled],
            [-14.0] * 7,
        )
        + _labels(
            [xs[i] for i in labelled],
            [bed[i] for i in labelled],
            [f"{bed[i]:.0f}" for i in labelled],
            [-14.0, 12, -14, -14, -14, -14, -14],
        )
        + _labels(
            [xs[i] for i in labelled],
            [hosp[i] for i in labelled],
            [f"{hosp[i]:.0f}" for i in labelled],
            [-14.0] * 7,
        ),
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-5",
        title="图 7-5 医疗机构（医科）数量的变化",
        panels=[panel],
        width=940,
        height=560,
    )
    return render_figure_svg(spec, mode)


def _fig_7_6(mode: ThemeMode = "mono") -> str:
    years = [float(y) for y in range(1996, 2025)]
    gdpr = [
        521.2,
        513.3,
        511.8,
        525.9,
        536.9,
        517.0,
        521.6,
        529.1,
        539.5,
        545.6,
        555.6,
        564.6,
        570.9,
        578.4,
        585.1,
        590.7,
        595.9,
        602.4,
        607.9,
        613.4,
        615.3,
        620.8,
        623.6,
        626.0,
        628.8,
        630.7,
        633.2,
        635.4,
        637.3,
    ]
    gdpr2 = [
        521.2,
        513.3,
        511.8,
        525.9,
        536.9,
        513.4,
        517.0,
        525.0,
        534.1,
        538.8,
        545.3,
        550.0,
        552.9,
        558.6,
        561.0,
        564.7,
        564.8,
        569.6,
        570.2,
        570.0,
        572.3,
        572.4,
        572.6,
        577.8,
        579.3,
        582.1,
        585.5,
        588.7,
        590.7,
    ]
    panel = PanelSpec(
        xlim=(1995.5, 2024.5),
        ylim=(350.0, 700.0),
        yticks=[float(v) for v in range(350, 701, 50)],
        xticks=[float(y) for y in range(1997, 2025, 3)],
        xlabel="年",
        ylabel="实际GDP",
        zero_line=False,
        lines=[
            LineSeries(
                x=years, y=gdpr, label="GDPR", color_idx=0, marker="circle", width=2.0
            ),
            LineSeries(
                x=years,
                y=gdpr2,
                label="GDPR2（假设：1995年以后死亡率未下降）",
                color_idx=1,
                marker="square",
                width=2.0,
            ),
        ],
        legend_loc="bottom",
    )
    spec = FigureSpec(
        fig_id="7-6",
        title="图 7-6 假设医疗并未引起死亡率下降时的 GDP 与存在医疗保险制度的现实 GDP 比较（SNA97，模型估算时间 1977—2001 年）",
        panels=[panel],
    )
    return render_figure_svg(spec, mode)


def _fig_7_7(mode: ThemeMode = "mono") -> str:
    cancer = [
        (0.2441, 238),
        (0.2544, 231),
        (0.2583, 223),
        (0.2657, 237),
        (0.2683, 277),
        (0.2683, 261),
        (0.2740, 273),
        (0.2767, 234),
        (0.2794, 195),
        (0.2815, 174),
        (0.2819, 212),
        (0.2840, 276),
        (0.2833, 251),
        (0.2846, 190),
        (0.2860, 214),
        (0.2905, 267),
        (0.2889, 227),
        (0.2932, 188),
        (0.2956, 218),
        (0.2996, 228),
        (0.2996, 218),
        (0.3083, 208),
        (0.3105, 261),
        (0.3127, 277),
        (0.3120, 243),
        (0.3152, 224),
        (0.3164, 212),
        (0.3251, 236),
        (0.3364, 273),
        (0.3354, 242),
        (0.3383, 248),
        (0.3385, 223),
        (0.3422, 223),
        (0.3441, 284),
        (0.3512, 250),
        (0.3599, 249),
        (0.3656, 240),
        (0.3706, 258),
        (0.3736, 286),
        (0.3746, 265),
        (0.3880, 242),
        (0.3988, 255),
        (0.4058, 235),
        (0.4096, 265),
        (0.4265, 260),
        (0.4550, 166),
    ]
    circulatory = [
        (0.2448, 262),
        (0.2544, 308),
        (0.2648, 267),
        (0.2683, 296),
        (0.2740, 325),
        (0.2762, 228),
        (0.2786, 207),
        (0.2833, 282),
        (0.2833, 243),
        (0.2864, 250),
        (0.2877, 286),
        (0.2889, 308),
        (0.2926, 207),
        (0.2963, 250),
        (0.2979, 195),
        (0.2843, 186),
        (0.3080, 214),
        (0.3102, 283),
        (0.3123, 317),
        (0.3123, 307),
        (0.3148, 264),
        (0.3154, 238),
        (0.3248, 263),
        (0.3231, 236),
        (0.3373, 304),
        (0.3379, 291),
        (0.3385, 261),
        (0.3422, 270),
        (0.3429, 313),
        (0.3512, 220),
        (0.3591, 287),
        (0.3648, 263),
        (0.3689, 291),
        (0.3733, 342),
        (0.3733, 329),
        (0.3880, 265),
        (0.3988, 309),
        (0.4091, 273),
        (0.4075, 233),
        (0.4267, 310),
        (0.4555, 159),
    ]
    cerebro = [
        (0.2448, 128),
        (0.2531, 162),
        (0.2602, 92),
        (0.2660, 120),
        (0.2685, 130),
        (0.2691, 138),
        (0.2753, 169),
        (0.2778, 97),
        (0.2802, 120),
        (0.2806, 109),
        (0.2802, 87),
        (0.2806, 94),
        (0.2856, 92),
        (0.2889, 160),
        (0.2889, 128),
        (0.2905, 120),
        (0.2926, 92),
        (0.2963, 113),
        (0.2981, 80),
        (0.3000, 101),
        (0.3074, 151),
        (0.3091, 103),
        (0.3102, 137),
        (0.3120, 147),
        (0.3140, 129),
        (0.3148, 119),
        (0.3204, 122),
        (0.3235, 110),
        (0.3260, 122),
        (0.3375, 142),
        (0.3375, 125),
        (0.3370, 111),
        (0.3429, 150),
        (0.3429, 125),
        (0.3499, 100),
        (0.3591, 130),
        (0.3648, 118),
        (0.3689, 132),
        (0.3733, 179),
        (0.3733, 157),
        (0.3880, 122),
        (0.3985, 131),
        (0.4058, 93),
        (0.4087, 120),
        (0.4280, 148),
        (0.4550, 61),
    ]
    suicide = [
        (0.2448, 30),
        (0.2544, 11),
        (0.2574, 96),
        (0.2673, 76),
        (0.2691, 55),
        (0.2651, 33),
        (0.2747, 35),
        (0.2762, 41),
        (0.2796, 14),
        (0.2815, 6),
        (0.2840, 152),
        (0.2833, 12),
        (0.2846, 33),
        (0.2870, 19),
        (0.2891, 46),
        (0.2905, 19),
        (0.2932, 26),
        (0.2963, 26),
        (0.2979, 11),
        (0.3004, 5),
        (0.3091, 37),
        (0.3099, 76),
        (0.3117, 44),
        (0.3140, 33),
        (0.3148, 21),
        (0.3235, 11),
        (0.3260, 11),
        (0.3360, 13),
        (0.3373, 30),
        (0.3383, 19),
        (0.3404, 23),
        (0.3435, 22),
        (0.3414, 77),
        (0.3508, 4),
        (0.3596, 101),
        (0.3656, 19),
        (0.3696, 39),
        (0.3720, 50),
        (0.3743, 42),
        (0.3888, 23),
        (0.4000, 13),
        (0.4083, 10),
        (0.4265, 21),
        (0.4547, 35),
    ]

    def series(pts: list[tuple[float, int]], marker: str, idx: int) -> LineSeries:
        return _markers([p[0] for p in pts], [float(p[1]) for p in pts], marker, idx)

    panel = PanelSpec(
        xlim=(0.2, 0.5),
        ylim=(0.0, 400.0),
        xticks=[0.2, 0.3, 0.4, 0.5],
        yticks=[0.0, 100.0, 200.0, 300.0, 400.0],
        xlabel="贫困线以下人口的平均收入相对于整体平均收入的比值",
        ylabel="人口每10万人的死亡率",
        zero_line=False,
        lines=[
            series(cancer, "diamond", 0),
            series(circulatory, "cross", 2),
            series(cerebro, "triangle", 1),
            series(suicide, "triangle", 4),
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="7-7",
        title="图 7-7 贫困率与不同死因的死亡人数",
        panels=[panel],
        note="◆ 恶性肿瘤　　× 循环器官疾病　　△ 脑血管疾病　　▲ 自杀",
    )
    return render_figure_svg(spec, mode)


def _fig_7_8(mode: ThemeMode = "mono") -> str:
    x1 = [
        0.509,
        0.51,
        0.511,
        0.509,
        0.51,
        0.51,
        0.519,
        0.529,
        0.538,
        0.539,
        0.539,
        0.559,
        0.568,
        0.57,
        0.568,
        0.568,
        0.572,
        0.568,
        0.577,
        0.578,
        0.576,
        0.578,
        0.589,
        0.589,
        0.589,
        0.589,
        0.588,
        0.586,
        0.599,
        0.619,
        0.618,
        0.619,
        0.62,
        0.622,
        0.622,
        0.626,
        0.627,
        0.629,
        0.629,
        0.628,
        0.639,
        0.638,
        0.645,
        0.647,
        0.648,
        0.657,
        0.689,
        0.689,
    ]
    y1 = [
        3280,
        3330,
        3080,
        2920,
        2830,
        2020,
        2830,
        2950,
        3190,
        3130,
        2800,
        3120,
        3330,
        3300,
        2830,
        2720,
        2610,
        2090,
        3080,
        2560,
        2360,
        2040,
        3540,
        3340,
        2920,
        2650,
        2520,
        2470,
        3040,
        3660,
        3430,
        2570,
        2400,
        3250,
        2220,
        2360,
        3310,
        3510,
        2870,
        2020,
        2620,
        2250,
        2970,
        2860,
        3090,
        2750,
        3660,
        2830,
    ]
    x2 = [
        0.508,
        0.51,
        0.511,
        0.508,
        0.519,
        0.526,
        0.538,
        0.54,
        0.54,
        0.558,
        0.566,
        0.568,
        0.57,
        0.568,
        0.568,
        0.577,
        0.578,
        0.576,
        0.578,
        0.578,
        0.588,
        0.588,
        0.586,
        0.589,
        0.591,
        0.592,
        0.598,
        0.588,
        0.619,
        0.618,
        0.619,
        0.619,
        0.618,
        0.621,
        0.625,
        0.627,
        0.628,
        0.627,
        0.628,
        0.638,
        0.638,
        0.647,
        0.648,
        0.65,
    ]
    y2 = [
        1810,
        2190,
        1760,
        720,
        1290,
        1490,
        1060,
        1200,
        4680,
        2900,
        2260,
        2080,
        2580,
        4140,
        900,
        4230,
        2900,
        1700,
        1180,
        900,
        1990,
        1760,
        1130,
        1810,
        1630,
        1520,
        1630,
        1000,
        5970,
        5340,
        4000,
        1900,
        900,
        750,
        1900,
        2260,
        2490,
        3050,
        1000,
        9190,
        5050,
        1310,
        2040,
        1180,
    ]
    x3 = [
        0.508,
        0.51,
        0.513,
        0.511,
        0.519,
        0.529,
        0.539,
        0.542,
        0.539,
        0.56,
        0.57,
        0.573,
        0.571,
        0.576,
        0.58,
        0.579,
        0.588,
        0.589,
        0.589,
        0.59,
        0.591,
        0.59,
        0.59,
        0.591,
        0.6,
        0.62,
        0.621,
        0.62,
        0.62,
        0.62,
        0.625,
        0.631,
        0.63,
        0.63,
        0.631,
        0.631,
        0.64,
        0.64,
        0.647,
        0.649,
        0.649,
    ]
    y3 = [
        1601,
        1555,
        1489,
        1450,
        1424,
        1654,
        1587,
        1541,
        1330,
        1484,
        1601,
        1374,
        1294,
        1282,
        1500,
        1064,
        1413,
        1349,
        1335,
        1443,
        1436,
        1330,
        1706,
        1720,
        1500,
        1665,
        1580,
        1436,
        1321,
        1167,
        1642,
        1642,
        1436,
        1392,
        1236,
        1149,
        1282,
        1144,
        1564,
        1564,
        1328,
    ]
    xticks = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75]
    xlabel = "贫困线以下人口平均收入相对于整体平均收入的比值"
    ylabel = "70岁以上死亡率（相对于人口10万人）"
    p1 = PanelSpec(
        title="循环器官疾病（不含最大值与最小值）",
        xlim=(0.4, 0.75),
        ylim=(0.0, 4000.0),
        xticks=xticks,
        yticks=[float(v) for v in range(0, 4001, 500)],
        xlabel=xlabel,
        ylabel=ylabel,
        zero_line=False,
        lines=[_markers(x1, [float(v) for v in y1], "diamond", 0)],
        legend_loc="none",
    )
    p2 = PanelSpec(
        title="脑血管疾病（收入比值90%区间）",
        xlim=(0.4, 0.75),
        ylim=(0.0, 10000.0),
        xticks=xticks,
        yticks=[float(v) for v in range(0, 10001, 1000)],
        xlabel=xlabel,
        ylabel=ylabel,
        zero_line=False,
        lines=[
            _markers(x2, [float(v) for v in y2], "diamond", 0),
            LineSeries(
                x=[0.51, 0.645],
                y=[10930 * 0.51 - 4101.6, 10930 * 0.645 - 4101.6],
                color_idx=2,
                width=2.4,
            ),
        ],
        annotations=[
            Annotation(
                x=0.745,
                y=8200.0,
                text="（y=10930x−4101.6，R²=0.0704）",
                dy=6.0,
                arrow=False,
                fontsize=10.0,
                align="end",
            )
        ],
        legend_loc="none",
    )
    p3 = PanelSpec(
        title="恶性肿瘤（收入比值90%区间）",
        xlim=(0.4, 0.7),
        ylim=(1000.0, 2000.0),
        xticks=xticks[:-1],
        yticks=[float(v) for v in range(1000, 2001, 100)],
        xlabel=xlabel,
        ylabel=ylabel,
        zero_line=False,
        lines=[
            _markers(x3, [float(v) for v in y3], "diamond", 0),
            LineSeries(
                x=[0.51, 0.65],
                y=[-867.44 * 0.51 + 1958.5, -867.44 * 0.65 + 1958.5],
                color_idx=2,
                width=2.4,
            ),
        ],
        annotations=[
            Annotation(
                x=0.695,
                y=1950.0,
                text="（y=−867.44x+1958.5，R²=0.0521）",
                dy=6.0,
                arrow=False,
                fontsize=10.0,
                align="end",
            )
        ],
        legend_loc="none",
    )
    spec = FigureSpec(
        fig_id="7-8",
        title="图 7-8 70 岁及以上人口贫困率与不同伤病死因相对于人口 10 万人的死亡率",
        panels=[p1, p2, p3],
        rows=3,
        cols=1,
        width=860,
        height=1300,
    )
    return render_figure_svg(spec, mode)


YEARS_90S = [float(y) for y in range(1990, 1999)]
AGE_GROUPS = ("29岁以下", "30~39岁", "40~49岁", "50~59岁", "60岁以上")
AGE_STYLE = (
    ("circle", 0),
    ("square", 2),
    ("triangle", 4),
    ("cross", 3),
    ("triangle", 1),
)


def _age_panel(
    rows: Sequence[Sequence[float]],
    ylim: tuple[float, float],
    yticks: Sequence[float],
    ylabel: str,
    names: Sequence[str] = AGE_GROUPS,
    future: Sequence[Sequence[float]] = (),
) -> PanelSpec:
    lines = (
        [
            LineSeries(
                x=YEARS_90S,
                y=list(future[0]),
                label="未来一代（1992年推算）",
                color_idx=7,
                marker="circle",
                width=2.0,
            ),
            LineSeries(
                x=YEARS_90S,
                y=list(future[1]),
                label="未来一代（1997年推算）",
                color_idx=5,
                marker="square",
                width=2.4,
            ),
        ]
        if future
        else []
    )
    lines += [
        LineSeries(
            x=YEARS_90S,
            y=list(row),
            label=name,
            color_idx=idx,
            marker=marker,
            width=2.0,
        )
        for row, name, (marker, idx) in zip(rows, names, AGE_STYLE)
    ]
    return PanelSpec(
        xlim=(1989.5, 1998.5),
        ylim=ylim,
        yticks=list(yticks),
        xticks=YEARS_90S,
        xlabel="年",
        ylabel=ylabel,
        lines=lines,
        legend_loc="bottom",
    )


def _fig_8_1(mode: ThemeMode = "mono") -> str:
    rows = [
        [24.1, 25.1, 25.8, 23.3, 22.8, 23.9, 23.4, 23.3, 23.3],
        [29.4, 30.3, 31.1, 29.5, 28.7, 30.0, 30.6, 29.9, 29.9],
        [39.056, 40.1, 40.1, 38.0, 36.7, 37.2, 37.7, 37.2, 37.279],
        [45.4, 46.5, 45.0, 43.9, 41.6, 44.1, 44.3, 46.5, 42.7],
        [22.1, 21.8, 20.6, 20.0, 19.5, 19.5, 20.1, 21.0, 20.0],
    ]
    panel = _age_panel(
        [[v * 1000 for v in r] for r in rows],
        (0.0, 50000.0),
        [float(v) for v in range(0, 50001, 5000)],
        "千日元",
    )
    spec = FigureSpec(fig_id="8-1", title="图 8-1 负担额的变化", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_8_2(mode: ThemeMode = "mono") -> str:
    rows = [
        [3.704, 4.0, 4.7, 3.4, 4.6, 4.8, 4.6, 4.0, 4.504],
        [4.198, 4.6, 4.7, 4.4, 4.7, 4.6, 4.6, 4.4, 5.425],
        [4.210, 4.6, 4.2, 4.6, 4.8, 4.8, 4.8, 4.7, 5.887],
        [6.418, 5.6, 5.6, 5.1, 5.0, 5.0, 5.1, 5.1, 5.325],
        [35.911, 37.0, 37.7, 39.3, 39.9, 41.6, 41.6, 41.2, 41.449],
    ]
    panel = _age_panel(
        [[v * 1000 for v in r] for r in rows],
        (0.0, 45000.0),
        [float(v) for v in range(0, 45001, 5000)],
        "千日元",
    )
    spec = FigureSpec(fig_id="8-2", title="图 8-2 收益额的变化", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_8_3(mode: ThemeMode = "mono") -> str:
    rows = [
        [20.1, 20.7, 20.7, 19.3, 18.1, 18.1, 18.1, 19.3, 19.3],
        [25.8, 25.6, 25.8, 24.4, 23.6, 25.6, 25.8, 24.9, 24.4],
        [34.6, 35.2, 35.5, 33.2, 31.9, 32.1, 32.4, 31.4, 31.4],
        [38.5, 40.8, 38.8, 38.5, 36.1, 38.9, 38.9, 39.8, 37.5],
        [-14.1, -15.2, -16.8, -20.2, -20.3, -22.2, -21.2, -20.3, -21.0],
    ]
    panel = _age_panel(
        [[v * 1000 for v in r] for r in rows],
        (-30000.0, 50000.0),
        [float(v) for v in range(-30000, 50001, 10000)],
        "千日元",
    )
    spec = FigureSpec(fig_id="8-3", title="图 8-3 净负担额的变化", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_8_4(mode: ThemeMode = "mono") -> str:
    future_97 = [78.153, 81.0, 86.7, 87.1, 85.3, 91.0, 91.0, 95.4, 96.646]
    future_92 = future_97[:7] + [89.1, 90.8]
    rows = [
        [74.052, 76.1, 74.0, 66.5, 61.7, 63.2, 64.3, 66.5, 63.697],
        [65.4, 67.0, 63.9, 57.3, 54.3, 55.1, 57.3, 58.9, 54.3],
        [49.5, 49.9, 45.7, 40.7, 36.5, 36.5, 37.9, 39.8, 35.9],
        [16.8, 16.8, 13.3, 9.4, 5.9, 5.9, 6.6, 9.2, 5.5],
        [-26.0, -28.7, -31.7, -35.4, -37.6, -41.8, -40.3, -37.4, -39.8],
    ]
    panel = _age_panel(
        rows,
        (-60.0, 120.0),
        [float(v) for v in range(-60, 121, 20)],
        "百万日元",
        names=("29岁以上", *AGE_GROUPS[1:]),
        future=(future_92, future_97),
    )
    spec = FigureSpec(fig_id="8-4", title="图 8-4 终身净负担额的变化", panels=[panel])
    return render_figure_svg(spec, mode)


def _fig_8_5(mode: ThemeMode = "mono") -> str:
    future_97 = [105.5, 107.2, 116.5, 129.4, 138.2, 140.1, 140.1, 141.6, 151.7]
    future_92 = future_97[:7] + [132.3, 139.1]
    rows = [
        [100.0, 99.6, 99.6, 99.3, 98.9, 98.9, 98.6, 98.6, 98.2],
        [88.9, 87.8, 86.7, 86.7, 85.3, 86.0, 86.4, 84.6, 84.2],
        [66.3, 65.9, 62.7, 59.5, 58.4, 55.2, 55.6, 57.3, 53.4],
        [21.9, 21.9, 18.3, 11.5, 7.5, 6.8, 7.2, 13.3, 6.1],
        [-36.2, -39.4, -43.7, -55.6, -62.0, -66.7, -64.2, -59.5, -64.5],
    ]
    panel = _age_panel(
        rows,
        (-100.0, 200.0),
        [float(v) for v in range(-100, 201, 50)],
        "%",
        names=("29岁以上", *AGE_GROUPS[1:]),
        future=(future_92, future_97),
    )
    spec = FigureSpec(
        fig_id="8-5",
        title="图 8-5 终身净负担的变化（以 20 岁一代为基准）",
        panels=[panel],
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "7-2": _fig_7_2,
        "7-3": _fig_7_3,
        "7-5": _fig_7_5,
        "7-6": _fig_7_6,
        "7-7": _fig_7_7,
        "7-8": _fig_7_8,
        "8-1": _fig_8_1,
        "8-2": _fig_8_2,
        "8-3": _fig_8_3,
        "8-4": _fig_8_4,
        "8-5": _fig_8_5,
    }
