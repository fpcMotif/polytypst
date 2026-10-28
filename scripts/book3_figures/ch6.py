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


def _text_lines(x: float, y_top: float, step: float, texts: list[str], size: float = 9.5) -> list[Annotation]:
    return [
        Annotation(x=x, y=y_top - i * step, text=t, dx=0.0, dy=0.0, arrow=False, fontsize=size, align="start")
        for i, t in enumerate(texts)
    ]


def _arrow(x: float, y: float, dx: float, dy: float) -> Annotation:
    return Annotation(x=x, y=y, text="", dx=dx, dy=dy, arrow=True)


def fig_6_1(mode: ThemeMode = "mono") -> str:
    labels = []
    for year in range(1993, 2008):
        labels += [f"{year}年6月", f"{year}年12月"]
    labels.append("2008年3月")
    values = [
        71.5, 72.5, 81.0, 93.0, 108.0, 112.5, 115.5, 118.5, 123.5, 110.0,
        98.5, 86.0, 75.0, 65.5, 59.5, 55.0, 52.5, 49.0, 42.5, 40.0,
        39.5, 41.0, 45.0, 50.5, 55.0, 57.0, 61.5, 66.0, 74.0, 76.0, 77.0,
    ]
    xs = list(range(len(values)))
    spec = FigureSpec(
        fig_id="6-1",
        title="图 6-1 日系银行对亚洲授信（离岸除外；1993年6月—2008年3月）",
        panels=[
            PanelSpec(
                xlim=(-0.6, len(values) - 0.4),
                ylim=(0.0, 180.0),
                xticks=[(i, labels[i]) for i in range(0, len(values), 4)],
                yticks=[0, 20, 40, 60, 80, 100, 120],
                ylabel="10亿美元",
                legend_loc="none",
                bars=[BarSeries(x=xs, y=values, color_idx=1, width=0.5, hatch=True)],
                annotations=[
                    *_text_lines(9.8, 168.0, 13.0, [
                        "•亚洲金融危机（▼）",
                        "•日本国内的不良债权问题，经营健全化计划（▼）",
                        "•新资产评估·信用风险管理方法的导入（▼）",
                    ]),
                    *_text_lines(14.3, 108.0, 13.0, [
                        "•日系银行的经营及财务状况的改善（▲）",
                        "•媲美欧美银行（？）唯一的海外市场（▲）",
                        "•国际业务的再强化（▲）",
                    ]),
                    *_text_lines(-0.3, 168.0, 13.0, [
                        "•日系企业的直接投资（▲）",
                        "•亚洲市场的魅力（高增长、",
                        "资金需求、收益性）（▲）",
                    ]),
                    _arrow(12.3, 80.0, 0.0, -95.0),
                    _arrow(25.5, 63.0, -130.0, -18.0),
                    _arrow(4.0, 98.0, 0.0, -55.0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_3(mode: ThemeMode = "mono") -> str:
    years = list(range(1985, 2008))
    tops = [
        (43, 59, 119, 130), (55, 75, 147, 160), (67, 87, 167, 181), (81, 102, 203, 219),
        (112, 141, 271, 291), (113, 139, 235, 258), (107, 131, 214, 233), (93, 115, 184, 201),
        (82, 103, 177, 193), (79, 97, 167, 185), (90, 112, 168, 181), (100, 123, 169, 179),
        (82, 103, 138, 148), (56, 73, 91, 98), (40, 57, 76, 82), (39, 68, 95, 103),
        (35, 62, 78, 84), (25, 58, 70, 78), (20, 54, 65, 76), (22, 53, 66, 74),
        (27, 62, 76, 83), (32, 69, 83, 93), (38, 77, 98, 109),
    ]
    xs = list(range(len(years)))
    layers = []
    fills = [(0, False), (3, False), (5, False), (2, True)]
    for k, (cidx, hatch) in enumerate(fills):
        bottom = [float(t[k - 1]) if k else 0.0 for t in tops]
        height = [float(t[k]) - b for t, b in zip(tops, bottom)]
        layers.append(BarSeries(x=xs, y=height, bottom=bottom, color_idx=cidx, width=0.5, hatch=hatch))
    spec = FigureSpec(
        fig_id="6-3",
        title="图 6-3 日系银行国际业务领域的资金运用余额（1985—2007年度）",
        panels=[
            PanelSpec(
                xlim=(-0.6, len(years) - 0.4),
                ylim=(0.0, 300.0),
                xticks=[(i, str(y)) for i, y in enumerate(years)],
                yticks=[0, 50, 100, 150, 200, 250, 300],
                ylabel="万亿日元",
                xlabel="年",
                legend_loc="none",
                bars=layers,
                annotations=[
                    *_text_lines(9.0, 282.0, 18.0, [
                        "•泡沫经济破灭导致的资产质量恶化",
                        "•巴塞尔自有资本比率规制的严格限制",
                    ]),
                    *_text_lines(13.5, 210.0, 18.0, [
                        "•考虑经营健全化计划下撤退",
                        "成本（后述）国际业务缩小",
                    ]),
                    *_text_lines(16.5, 138.0, 18.0, ["•国际业务再强化"]),
                    _arrow(6.4, 228.0, 75.0, -33.0),
                    _arrow(17.6, 88.0, -90.0, -110.0),
                    _arrow(20.6, 96.0, -32.0, -40.0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_4(mode: ThemeMode = "mono") -> str:
    labels = ["新加坡", "中国香港", "韩国", "泰国", "马来西亚", "印度尼西亚"]
    values = [0.8, 1.2, 3.9, 4.3, 5.5, 9.5]
    spec = FigureSpec(
        fig_id="6-4",
        title="图 6-4 20世纪80年代后半期亚洲主要日系银行业务收益率",
        panels=[
            PanelSpec(
                xlim=(-0.5, 5.5),
                ylim=(0.0, 10.0),
                xticks=list(enumerate(labels)),
                yticks=[(v, f"{v:.1f}") for v in range(11)],
                ylabel="%",
                legend_loc="none",
                bars=[BarSeries(x=list(range(6)), y=values, color_idx=1, width=0.46, hatch=True)],
                annotations=_text_lines(-0.42, 9.45, 0.62, [
                    "•除中国香港及新加坡以外的亚洲各国及地区，由",
                    "于当时金融及资本市场欠发达且经济持续高速增",
                    "长，所以对银行融资需求旺盛，容易确保高收益",
                    "•可对亚洲企业进行包括存款贷款、汇款及汇兑在",
                    "内的综合交易，而这对于欧美企业则言难以实现。",
                    "因此，对于日系银行而言，在接近日本国内中小",
                    "企业交易的收益方面存在优势",
                ], size=9.0),
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_5(mode: ThemeMode = "mono") -> str:
    groups = [
        ([88, 89, 79, 67.5, 59, 51, 41.5, 38, 34, 32.5, 30.5, 27, 26, 26, 26], 0, False),
        ([28.5, 33, 28, 24.5, 23.5, 24.5, 24.5, 27, 25, 23.5, 23.5, 27.5, 22.5, 22, 24], 3, False),
        ([78, 85, 79, 66.5, 67.5, 69, 74, 71, 66.5, 63.5, 64.5, 72.5, 73, 82, 87], 2, True),
    ]
    step = 0.875 / 15
    bars = [
        BarSeries(
            x=[g - 0.4375 + step * (i + 0.5) for i in range(15)],
            y=[float(v) for v in vals],
            color_idx=cidx,
            width=step,
            hatch=hatch,
            opacity=1.0,
        )
        for g, (vals, cidx, hatch) in enumerate(groups)
    ]
    spec = FigureSpec(
        fig_id="6-5",
        title="图 6-5 各国银行对亚洲金融危机3国授信余额的演变（1996—2003年年末，每半期）",
        panels=[
            PanelSpec(
                xlim=(-0.5, 2.5),
                ylim=(0.0, 90.0),
                xticks=[(0, "日系银行"), (1, "美系银行"), (2, "欧系银行")],
                yticks=list(range(0, 91, 10)),
                ylabel="10亿美元",
                legend_loc="none",
                bars=bars,
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_6(mode: ThemeMode = "mono") -> str:
    labels = ["日本国内", "海外总体", "美洲", "欧洲", "亚洲"]
    spec = FigureSpec(
        fig_id="6-6",
        title="图 6-6 主要日系银行地区细分资产收益率",
        panels=[
            PanelSpec(
                xlim=(-0.5, 4.5),
                ylim=(-1.2, 0.6),
                xticks=list(enumerate(labels)),
                yticks=[(v / 10, f"{v / 10:.1f}".replace("-", "−")) for v in range(-12, 7, 2)],
                ylabel="%",
                legend_loc="bottom",
                bars=[
                    BarSeries(x=[i - 0.15 for i in range(5)], y=[-1.14, 0.32, 0.60, 0.12, 0.15], label="1997年度",
                              color_idx=2, width=0.29, hatch=True),
                    BarSeries(x=[0.15, 2.15, 3.15, 4.15], y=[-0.95, 0.54, -0.08, -0.84], label="1998年度",
                              color_idx=3, width=0.29),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_7(mode: ThemeMode = "mono") -> str:
    pts = [
        (145, 25), (150, 5), (175, 0), (200, 5), (210, 0), (240, 5), (250, 0), (280, 0), (300, 5), (320, 3),
        (350, 5), (385, 5), (395, 18), (410, 10), (420, 20), (435, 25), (445, 50), (450, 35), (465, 28),
        (475, 20), (490, 20), (495, 8), (510, 25), (515, 5), (530, 8), (550, 5), (565, 18), (580, 20),
        (600, 15), (610, 6), (650, 6), (690, 8), (700, 13), (735, 15), (760, 5), (775, 12), (800, 8),
        (820, 6), (860, 6), (880, 20), (890, 22), (900, 12), (910, 15), (940, 10), (960, 12), (985, 22),
        (1000, 13), (1010, 6), (1040, 8), (1075, 6), (1090, 12), (1110, 7), (1140, 5), (1175, 3),
        (1190, 0), (1210, 3), (1220, 12), (1235, 40), (1245, 60), (1255, 85), (1258, 100), (1262, 50),
        (1270, 65), (1285, 72), (1295, 40), (1305, 38), (1325, 55), (1345, 55), (1355, 25), (1365, 20),
        (1380, 18), (1390, 30), (1400, 22), (1420, 20), (1430, 17), (1460, 18), (1475, 42), (1490, 28),
        (1505, 32), (1525, 34), (1545, 36), (1555, 46), (1565, 38), (1580, 52), (1595, 46), (1605, 65),
        (1615, 69), (1625, 58), (1640, 50), (1655, 30), (1670, 20), (1680, 35), (1700, 20), (1715, 15),
        (1720, 20), (1735, 20), (1750, 0), (1765, 3), (1780, 2), (1800, 1), (1820, 0), (1835, 1),
    ]
    xs = [1995.0 + (px - 145) / 382.0 for px, _ in pts]
    ys: list[float | None] = [float(v) for _, v in pts]
    ticks = [(1995.0 + i * 0.5, f"{1995 + i // 2}/{1 if i % 2 == 0 else 7}") for i in range(9)]
    spec = FigureSpec(
        fig_id="6-7",
        title="图 6-7 日本溢价演变",
        note="资料来源：笔者根据 Bloomberg 等制作",
        panels=[
            PanelSpec(
                xlim=(1995.0, 1999.45),
                ylim=(0.0, 100.0),
                xticks=ticks,
                yticks=[0, 20, 40, 60, 80, 100],
                ylabel="基点",
                xlabel="时间",
                legend_loc="none",
                lines=[LineSeries(x=xs, y=ys, color_idx=0, width=1.2)],
                annotations=[
                    *_text_lines(1995.18, 94.0, 6.0, [
                        "• 山一证券，破产，1997年11月",
                        "• 三洋证券，会社更生法适用申请，1997年11月",
                        "• 北海道拓殖银行，营业让渡，1997年11月",
                    ], size=9.0),
                    *_text_lines(1995.18, 74.0, 6.0, [
                        "• 日本长期信用银行，特别公共管理，1998年10月",
                        "• 日本债券信用银行，特别公共管理，1998年12月",
                    ], size=9.0),
                    *_text_lines(1998.14, 94.0, 6.0, [
                        "• 1999年2月12日，金融政策",
                        "决策会议：无担保拆息（隔",
                        "夜拆借利率）零利率政策",
                        "• 外国银行的日元负利率",
                        "融资",
                    ], size=9.0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_8(mode: ThemeMode = "mono") -> str:
    labels = [f"1996年{m}月" for m in range(3, 13)] + [f"1997年{m}月" for m in range(1, 13)] + [
        f"1998年{m}月" for m in range(1, 10)
    ]
    rupiah = [
        2330, 2340, 2330, 2300, 2300, 2270, 2320, 2330, 2300, 2300,
        2300, 2330, 2400, 2400, 2400, 2400, 2430, 2830, 2960, 3600, 3450, 4850,
        9600, 8900, 9600, 7850, 9800, 13450, 14150, 11900,
    ]
    rate: list[float | None] = [
        12.2, 15.4, 14.9, 13.8, 13.8, 15.4, 14.6, 14.6, 13.0, 12.9,
        12.9, 12.9, 10.6, 13.7, 13.7, 13.7, 15.8, 64.9, 53.0, 41.0, 43.0, 41.0,
        57.0, 65.0, 52.0, 71.0, 64.0, 65.0, 76.0, 81.5, 67.0,
    ]
    spec = FigureSpec(
        fig_id="6-8",
        title="图 6-8 印度尼西亚：危机前后的卢比汇率、短期利率的演变",
        note="资料来源：IMF，International Financial Statistics",
        height=560,
        panels=[
            PanelSpec(
                xlim=(-0.6, len(labels) - 0.4),
                ylim=(0.0, 14000.0),
                xticks=[(i, labels[i]) for i in range(0, len(labels), 5)],
                yticks=list(range(0, 14001, 2000)),
                y2lim=(0.0, 85.8),
                y2ticks=[(0, "0.00"), (10, "10.0")] + [(v, f"{v}.00") for v in range(20, 81, 10)],
                ylabel="卢比/美元",
                y2label="%",
                legend_loc="bottom",
                bars=[BarSeries(x=list(range(len(rupiah))), y=[float(v) for v in rupiah], label="卢比汇率",
                                color_idx=4, width=0.45, opacity=1.0)],
                lines=[LineSeries(x=list(range(len(rate))), y=rate, label="银行间汇率（右轴）", color_idx=2,
                                  width=3.0, axis="y2")],
                annotations=[
                    *_text_lines(0.3, 11200.0, 900.0, [
                        "• Why did markets not anticipate this？",
                        "（Duenas，1998）",
                        "• 是否能说市场真的没有预知？",
                    ], size=9.0),
                    *_text_lines(0.3, 7400.0, 900.0, [
                        "• Letter of Intent（1997/10/31）",
                        "• IMF Stand-by Credit（1997/11/5）",
                        "• Memorandum of Economic and",
                        "Financial Policies（1998/1/15）",
                    ], size=9.0),
                    Annotation(x=26.8, y=13300.0, text="卢比汇率（Rupia per US dollar，左轴）", dx=-30.0, dy=-3.0,
                               fontsize=9.5, align="end"),
                    Annotation(x=17.3, y=61.0, text="银行间汇率（%，右轴）", dx=62.0, dy=-50.0, axis="y2",
                               fontsize=9.5),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_9(mode: ThemeMode = "mono") -> str:
    labels = [f"1997年{m}月" for m in range(6, 13)] + [f"1998年{m}月" for m in range(1, 10)]
    spot = [2.9, 3.3, 2.9, 2.9, 2.3, 2.1, 1.9, 1.05, 0.82, 0.91, 0.72, 0.46, 0.39, 0.43, 0.53, 0.5]
    total = [9.1, 9.5, 7.3, 7.1, 6.1, 5.3, 5.0, 2.14, 1.71, 1.86, 1.9, 1.43, 1.17, 1.21, 1.22, 1.06]
    xs = list(range(len(labels)))
    spec = FigureSpec(
        fig_id="6-9",
        title="图 6-9 印度尼西亚：外汇交易额",
        note="资料来源：笔者使用内野（2008）的数据制作",
        panels=[
            PanelSpec(
                xlim=(-0.6, len(labels) - 0.4),
                ylim=(0.0, 10.0),
                xticks=list(enumerate(labels)),
                yticks=list(range(11)),
                ylabel="10亿美元",
                legend_loc="bottom",
                bars=[
                    BarSeries(x=xs, y=spot, label="即期", color_idx=2, width=0.4, hatch=True),
                    BarSeries(x=xs, y=[t - s for t, s in zip(total, spot)], bottom=spot, label="掉期",
                              color_idx=3, width=0.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_10(mode: ThemeMode = "mono") -> str:
    labels = [f"1997年{m}月" for m in range(4, 13)] + [f"1998年{m}月" for m in range(1, 7)]
    values = [15.3, 17.0, 19.2, 17.5, 17.0, 21.2, 20.8, 38.1, 67.2, 68.5, 69.4, 43.2, 39.3, 52.7, 63.6]
    spec = FigureSpec(
        fig_id="6-10",
        title="图 6-10 印度尼西亚中央银行对商业银行信用",
        note="资料来源：IMF，International Financial Statistics",
        panels=[
            PanelSpec(
                xlim=(-0.6, len(values) - 0.4),
                ylim=(0.0, 70.0),
                xticks=list(enumerate(labels)),
                yticks=list(range(0, 71, 10)),
                ylabel="万亿卢比",
                legend_loc="none",
                bars=[BarSeries(x=list(range(len(values))), y=values, color_idx=3, width=0.52)],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_11(mode: ThemeMode = "mono") -> str:
    labels = ["1990年3月", "1994年3月", "2000年3月", "2001年3月", "2002年3月", "2007年3月", "2007年9月"]
    asia = [104.5, 162.0, 131.0, 123.0, 103.0, 85.0, 72.0]
    total = [327.0, 420.0, 242.0, 224.0, 183.0, 139.0, 131.0]
    xs = list(range(len(labels)))
    spec = FigureSpec(
        fig_id="6-11",
        title="图 6-11 日系银行各地区海外支行数量的演变",
        note="资料来源：日系银行 IR 资料等",
        panels=[
            PanelSpec(
                xlim=(-0.6, len(labels) - 0.4),
                ylim=(0.0, 450.0),
                xticks=list(enumerate(labels)),
                yticks=list(range(0, 451, 50)),
                ylabel="家",
                legend_loc="bottom",
                bars=[
                    BarSeries(x=xs, y=[t - a for t, a in zip(total, asia)], bottom=asia, label="美洲、欧洲等的海外支行",
                              color_idx=2, width=0.4, hatch=True),
                    BarSeries(x=xs, y=asia, label="亚洲地区的海外支行", color_idx=3, width=0.4),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_12(mode: ThemeMode = "mono") -> str:
    labels = ["对民间企业的融资", "其中的日系企业", "其中的非日系企业"]
    spec = FigureSpec(
        fig_id="6-12",
        title="图 6-12 主要日系银行对亚洲5国各借款方的敞口",
        note="资料来源：日系银行 IR 资料等",
        panels=[
            PanelSpec(
                xlim=(-0.5, 2.5),
                ylim=(0.0, 30.0),
                xticks=list(enumerate(labels)),
                yticks=list(range(0, 31, 5)),
                ylabel="10亿美元",
                legend_loc="bottom",
                bars=[
                    BarSeries(x=[i - 0.13 for i in range(3)], y=[27.95, 10.84, 17.08], label="1998年6月",
                              color_idx=2, width=0.26, hatch=True),
                    BarSeries(x=[i + 0.13 for i in range(3)], y=[26.5, 10.6, 15.6], label="1998年12月",
                              color_idx=3, width=0.26),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_13(mode: ThemeMode = "mono") -> str:
    years = list(range(1983, 2008))
    japan: list[float | None] = [
        45, 64, 89, 138, 172, 182, 201, 232, 246, 265, 302, 350, 331, 274, 257,
        159, 153, 153, 121, 102, 93, 111, 125, 162, 213,
    ]
    europe: list[float | None] = [
        51, 55, 66, 93, 111, 125, 127, 153, 155, 166, 264, 322, 405, 484, 557,
        465, 438, 410, 405, 429, 503, 595, 671, 850, 1149,
    ]
    us: list[float | None] = [
        41, 45, 47, 47, 47, 41, 47, 47, 47, 57, 66, 76, 89, 106, 106,
        102, 98, 108, 104, 104, 121, 178, 181, 232, 289,
    ]
    xticks = [(y, f"{y}年" if y == 2007 else str(y)) for y in range(1983, 2008, 2)]
    spec = FigureSpec(
        fig_id="6-13",
        title="图 6-13 各国银行对亚洲授信余额演变（1983—2007年年末）",
        note="资料来源：BIS，Consolidated International Banking Statistics",
        panels=[
            PanelSpec(
                xlim=(1982.5, 2007.6),
                ylim=(0.0, 1200.0),
                xticks=xticks,
                yticks=list(range(0, 1201, 200)),
                ylabel="10亿美元",
                legend_loc="bottom",
                lines=[
                    LineSeries(x=years, y=japan, label="日系银行", color_idx=2, style="dotted", marker="circle"),
                    LineSeries(x=years, y=europe, label="欧洲银行", color_idx=1, style="dashed", marker="triangle"),
                    LineSeries(x=years, y=us, label="美国银行", color_idx=0, marker="square", width=2.6),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_14(mode: ThemeMode = "mono") -> str:
    labels = ["UBS", "德国银行", "高盛银行", "美林"]
    spec = FigureSpec(
        fig_id="6-14",
        title="图 6-14 欧美投资银行亚洲地区收益份额（亚洲地区收益在净收入中的份额）",
        note="资料来源：笔者根据各银行 IR 资料等制作",
        panels=[
            PanelSpec(
                xlim=(-0.5, 3.5),
                ylim=(0.0, 20.0),
                xticks=list(enumerate(labels)),
                yticks=[0, 5, 10, 15, 20],
                ylabel="%",
                legend_loc="bottom",
                bars=[
                    BarSeries(x=[i - 0.11 for i in range(4)], y=[5.6, 6.9, 9.9, 5.9], label="1998年",
                              color_idx=2, width=0.22, hatch=True),
                    BarSeries(x=[i + 0.11 for i in range(4)], y=[8.4, 12.0, 19.7, 10.9], label="2006年",
                              color_idx=3, width=0.22),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def fig_6_15(mode: ThemeMode = "mono") -> str:
    labels = ["海外", "其中美洲", "其中欧洲", "其中亚洲"]
    series = [
        ("2005年", [0.625, 0.673, 0.48, 0.703], 2, True),
        ("2006年", [0.709, 0.766, 0.492, 0.841], 1, False),
        ("2007年", [0.163, 0.679, -0.80, 0.779], 3, False),
    ]
    spec = FigureSpec(
        fig_id="6-15",
        title="图 6-15 主要日系银行各地区资产收益率",
        height=620,
        panels=[
            PanelSpec(
                xlim=(-0.5, 3.5),
                ylim=(-0.8, 1.0),
                xticks=list(enumerate(labels)),
                yticks=[(v / 10, f"{v / 10:.2f}".replace("-", "−")) for v in range(-8, 11, 2)],
                ylabel="%",
                legend_loc="bottom",
                bars=[
                    BarSeries(x=[i + (k - 1) * 0.22 for i in range(4)], y=vals, label=lab, color_idx=cidx,
                              width=0.22, hatch=hatch)
                    for k, (lab, vals, cidx, hatch) in enumerate(series)
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "6-1": fig_6_1,
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
        "6-13": fig_6_13,
        "6-14": fig_6_14,
        "6-15": fig_6_15,
    }
