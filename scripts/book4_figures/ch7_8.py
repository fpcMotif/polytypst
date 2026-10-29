from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Literal

from scripts.book2_figures.engine import (
    PRINT_SCALE,
    Annotation,
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    render_figure_svg,
)

Arrow = tuple[float, float, float, float]
Align = Literal["start", "middle", "end"]


PLOT_RECT = re.compile(r'<rect x="[\d.]+" y="[\d.]+" width="([\d.]+)" height="([\d.]+)" fill="none"')


def _plot_size(spec: FigureSpec, mode: ThemeMode) -> tuple[float, float]:
    match = PLOT_RECT.search(render_figure_svg(spec, mode))
    if match is None:
        raise ValueError(f"no plot frame in figure {spec.fig_id}")
    return float(match.group(1)), float(match.group(2))


def _with_arrows(spec: FigureSpec, arrows: Sequence[Arrow], mode: ThemeMode) -> FigureSpec:
    panel = spec.panels[0]
    pw, ph = _plot_size(spec, mode)
    sx = pw / (panel.xlim[1] - panel.xlim[0])
    sy = ph / (panel.ylim[1] - panel.ylim[0])
    extra = [
        Annotation(x=x1, y=y1, text="", dx=(x0 - x1) * sx / PRINT_SCALE, dy=-(y0 - y1) * sy / PRINT_SCALE)
        for x0, y0, x1, y1 in arrows
    ]
    panel.annotations = [*panel.annotations, *extra]
    return spec


def _drop_empty(bar: BarSeries) -> BarSeries:
    keep = [i for i, y in enumerate(bar.y) if y != 0]
    bottom = None if bar.bottom is None else [bar.bottom[i] for i in keep]
    return replace(bar, x=[bar.x[i] for i in keep], y=[bar.y[i] for i in keep], bottom=bottom)


def _label(x: float, y: float, text: str, align: Align = "middle", size: float = 11.0) -> Annotation:
    return Annotation(x=x, y=y, text=text, dx=0.0, dy=0.0, arrow=False, fontsize=size, align=align)


ASAHI_MONTHS = 89
ASAHI_YEAR_TICKS: list[float | tuple[float, str]] = [
    (2.0, "1992"),
    *[(5 + 12 * k + 5.5, str(1993 + k)) for k in range(7)],
]


def _monthly(counts: dict[int, int], present: Sequence[range]) -> list[float | None]:
    shown = {m for r in present for m in r}
    return [float(counts.get(m, 0)) if m in shown else None for m in range(ASAHI_MONTHS)]


def _asahi_panel(title: str, lines: list[LineSeries], ymax: int, ystep: int, ylabel: str = "") -> PanelSpec:
    return PanelSpec(
        title=title,
        xlim=(-0.5, ASAHI_MONTHS - 0.5),
        ylim=(0, ymax),
        xticks=ASAHI_YEAR_TICKS,
        yticks=[float(v) for v in range(0, ymax + 1, ystep)],
        ylabel=ylabel,
        xlabel="年",
        legend_loc="bottom",
        lines=lines,
    )


def _asahi_lines(series: Sequence[tuple[str, list[float | None]]]) -> list[LineSeries]:
    styles = [(5, "dotted"), (2, "dashed"), (0, "solid")] if len(series) == 3 else [(5, "dotted"), (0, "solid")]
    xs = [float(m) for m in range(ASAHI_MONTHS)]
    return [
        LineSeries(x=xs, y=ys, label=label, color_idx=c, style=s, width=2.0)
        for (label, ys), (c, s) in zip(series, styles)
    ]


ALL_FAVOR = {
    -1: 1, 0: 6, 1: 3, 2: 1, 4: 1, 5: 1, 6: 3, 7: 1, 15: 2, 16: 11, 17: 3, 33: 4, 34: 15, 35: 16, 36: 5,
    37: 13, 38: 4, 39: 3, 40: 8, 41: 3, 42: 7, 43: 5, 50: 1, 52: 1, 53: 7, 54: 4, 55: 2, 56: 1, 63: 30,
    64: 12, 65: 10, 66: 10, 67: 8, 68: 2, 69: 17, 70: 35, 71: 14, 72: 12, 73: 10, 74: 19, 75: 13, 76: 7,
    77: 6, 78: 14, 79: 9, 80: 7, 81: 9, 82: 4, 83: 2, 84: 6, 85: 3, 86: 5, 87: 3, 88: 1,
}
ALL_CONDITIONAL = {
    -1: 4, 0: 4, 1: 3, 2: 1, 4: 1, 5: 1, 6: 2, 15: 1, 16: 3, 17: 2, 28: 1, 29: 2, 30: 1, 31: 1, 33: 1,
    34: 6, 35: 10, 36: 4, 37: 12, 38: 4, 39: 3, 40: 14, 41: 14, 42: 14, 43: 44, 44: 2, 45: 1, 46: 1,
    53: 5, 54: 3, 55: 1, 56: 1, 57: 1, 62: 7, 63: 21, 64: 25, 65: 13, 66: 15, 67: 7, 68: 2, 69: 8,
    70: 25, 71: 43, 72: 45, 73: 55, 74: 28, 75: 14, 76: 7, 77: 5, 78: 11, 79: 15, 80: 4, 81: 9, 82: 6,
    83: 2, 84: 1, 85: 2, 86: 1, 87: 2,
}
ALL_AGAINST = {
    -1: 3, 0: 14, 1: 8, 2: 2, 3: 1, 5: 2, 6: 5, 7: 1, 8: 1, 15: 2, 16: 10, 17: 4, 21: 1, 26: 2, 27: 4,
    28: 4, 29: 2, 30: 3, 31: 3, 33: 1, 34: 6, 35: 14, 36: 3, 37: 12, 38: 5, 39: 4, 40: 19, 41: 21,
    42: 28, 43: 51, 44: 5, 45: 3, 46: 5, 50: 2, 53: 1, 54: 4, 55: 1, 56: 1, 57: 1, 58: 1, 61: 1, 62: 1,
    63: 6, 64: 4, 65: 10, 66: 10, 67: 8, 68: 2, 69: 5, 70: 17, 71: 17, 72: 11, 73: 9, 74: 9, 75: 17,
    76: 5, 77: 1, 78: 10, 79: 2, 80: 2, 81: 9, 82: 7, 83: 9, 84: 7, 85: 5, 86: 1, 87: 2, 88: 2,
}
FRONT_FAVOR = {
    0: 6, 1: 4, 2: 2, 3: 1, 15: 3, 16: 4, 17: 1, 20: 1, 33: 1, 34: 15, 35: 12, 36: 4, 37: 12, 38: 6,
    39: 5, 40: 13, 41: 3, 42: 5, 43: 2, 44: 1, 54: 7, 55: 2, 56: 1, 63: 29, 64: 12, 65: 14, 66: 10,
    67: 6, 68: 5, 69: 15, 70: 25, 71: 12, 72: 12, 73: 10, 74: 20, 75: 12, 76: 6, 77: 7, 78: 14, 79: 7,
    80: 6, 81: 1, 82: 4, 83: 1, 84: 3, 85: 7, 86: 1, 87: 4, 88: 1,
}
FRONT_CONDITIONAL = {
    0: 4, 1: 3, 2: 2, 3: 1, 15: 2, 16: 4, 17: 1, 28: 1, 29: 2, 34: 6, 35: 10, 36: 5, 37: 11, 38: 5,
    39: 5, 40: 14, 41: 12, 42: 6, 43: 15, 44: 5, 45: 2, 46: 1, 54: 5, 55: 1, 56: 2, 57: 1, 62: 2,
    63: 18, 64: 24, 65: 13, 66: 13, 67: 9, 68: 6, 69: 5, 70: 11, 71: 35, 72: 45, 73: 55, 74: 30, 75: 9,
    76: 6, 77: 6, 78: 12, 79: 15, 80: 5, 81: 5, 82: 1, 83: 1, 84: 1, 85: 1, 86: 1, 87: 1, 88: 1,
}
FRONT_AGAINST = {
    0: 12, 1: 10, 2: 3, 3: 1, 6: 5, 7: 1, 8: 1, 15: 2, 16: 10, 17: 4, 27: 4, 28: 4, 29: 2, 30: 3, 31: 3,
    34: 6, 35: 13, 36: 5, 37: 11, 38: 5, 39: 5, 40: 14, 41: 10, 42: 10, 43: 10, 44: 4, 45: 2, 46: 1,
    54: 3, 55: 1, 56: 1, 57: 1, 58: 1, 60: 1, 61: 1, 62: 1, 63: 4, 64: 4, 65: 7, 66: 9, 67: 6, 68: 2,
    69: 5, 70: 4, 71: 9, 72: 9, 73: 7, 74: 7, 75: 4, 76: 4, 78: 10, 79: 1, 80: 2, 81: 8, 82: 7, 83: 7,
    84: 4, 85: 4, 88: 1,
}


def _fig_7_1(mode: ThemeMode = "mono") -> str:
    xs = [float(m) for m in range(-1, ASAHI_MONTHS)]

    def series(counts: dict[int, int], start: int = -1) -> list[float | None]:
        return [float(counts.get(m, 0)) if m >= start else None for m in range(-1, ASAHI_MONTHS)]

    def lines(named: Sequence[tuple[str, list[float | None]]]) -> list[LineSeries]:
        return [replace(line, x=xs) for line in _asahi_lines(named)]

    front_total = {m: FRONT_FAVOR.get(m, 0) + FRONT_CONDITIONAL.get(m, 0) for m in range(ASAHI_MONTHS)}
    front_title = "对不良债权的公共资金导入（1~14版）"
    panels = [
        _asahi_panel(
            "关于对不良债权的公共资金投入",
            lines([("赞成", series(ALL_FAVOR)), ("有条件赞成", series(ALL_CONDITIONAL)), ("反对（批判）", series(ALL_AGAINST))]),
            60,
            10,
            "件数",
        ),
        _asahi_panel(
            front_title,
            lines(
                [("赞成", series(FRONT_FAVOR, 0)), ("有条件赞成", series(FRONT_CONDITIONAL, 0)), ("反对", series(FRONT_AGAINST, 0))]
            ),
            60,
            10,
        ),
        _asahi_panel(
            front_title,
            lines([("赞成（包括有条件赞成）", series(front_total, 0)), ("反对", series(FRONT_AGAINST, 0))]),
            70,
            10,
        ),
    ]
    for panel in panels:
        panel.xlim = (-1.5, ASAHI_MONTHS - 0.5)
    spec = FigureSpec(
        fig_id="7-1",
        title="图 7-1 从《朝日新闻》报道来看对公共资金投入的赞成与否（一）",
        panels=panels,
        rows=3,
        width=860,
        height=1300,
    )
    return render_figure_svg(spec, mode)


LATE_FAVOR = {40: 1, 43: 3, 50: 2, 55: 2, 63: 1, 82: 1, 84: 3, 86: 1, 87: 1, 88: 1}
LATE_CONDITIONAL = {29: 1, 38: 1, 41: 1, 42: 3, 43: 2, 54: 1, 63: 2, 67: 1, 71: 3, 82: 1, 84: 1, 86: 1}
LATE_AGAINST = {
    0: 2, 5: 1, 37: 1, 40: 2, 41: 9, 42: 3, 43: 2, 44: 1, 46: 2, 53: 1, 63: 1, 65: 1, 70: 2, 72: 1,
    83: 2, 84: 3, 85: 1, 86: 1, 87: 2, 88: 1,
}


def _fig_7_2(mode: ThemeMode = "mono") -> str:
    late = [range(27, ASAHI_MONTHS)]
    favor = _monthly(LATE_FAVOR, late)
    conditional = _monthly(LATE_CONDITIONAL, late)
    against = _monthly(LATE_AGAINST, [range(7), *late])
    favor_all = _monthly({m: LATE_FAVOR.get(m, 0) + LATE_CONDITIONAL.get(m, 0) for m in range(ASAHI_MONTHS)}, late)
    title = "对不良债权的公共资金导入（15版以后）"
    top = _asahi_panel(
        title, _asahi_lines([("赞成", favor), ("有条件赞成", conditional), ("反对", against)]), 10, 1, "件数"
    )
    bottom = _asahi_panel(title, _asahi_lines([("赞成（包括有条件赞成）", favor_all), ("反对", against)]), 10, 1)
    spec = FigureSpec(
        fig_id="7-2",
        title="图 7-2 从《朝日新闻》报道来看对公共资金投入的赞成与否（二）",
        panels=[top, bottom],
        rows=2,
        width=860,
        height=900,
    )
    return render_figure_svg(spec, mode)


SUPPORT = [78, 84, 81, 77, 69, 70, 71, 74, 72, 72, 49, 45, 40, 42, 38, 37, 47, 51, 61, 59, 65, 54, 47, 44, 43, 45, 48, 47, 42, 49]
NON_SUPPORT = [8, 6, 8, 9, 17, 14, 13, 15, 17, 16, 36, 40, 44, 40, 47, 46, 37, 31, 21, 23, 23, 32, 35, 40, 42, 38, 37, 34, 37, 34]
OTHER = [14, 10, 11, 14, 14, 16, 16, 11, 11, 12, 15, 15, 16, 18, 15, 17, 16, 18, 18, 18, 12, 14, 18, 16, 15, 17, 15, 19, 21, 17]


def _months(n: int) -> list[str]:
    out: list[str] = []
    year, month = 2001, 4
    for _ in range(n):
        out.append(f"{year}年{month}月")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


LABELS_29 = _months(29)
LABELS_30_AS_PRINTED = [*_months(18), "2001年10月", *_months(30)[19:]]


def _poll_lines(n_categories: int) -> list[LineSeries]:
    step = (n_categories - 1) / (len(SUPPORT) - 1)
    xs = [i * step for i in range(len(SUPPORT))]
    return [
        LineSeries(x=xs, y=SUPPORT, label="支持小泉内阁", color_idx=0, style="solid", width=2.4),
        LineSeries(x=xs, y=NON_SUPPORT, label="不支持小泉内阁", color_idx=2, style="dashed", width=2.2),
        LineSeries(x=xs, y=OTHER, label="其他 · 不知道", color_idx=5, style="dotted", width=2.2),
    ]


def _poll_panel(labels: list[str], bars: list[BarSeries], lines: list[LineSeries]) -> PanelSpec:
    n = len(labels)
    return PanelSpec(
        xlim=(-0.5, n - 0.5),
        ylim=(0, 90),
        xticks=[(float(i), lab) for i, lab in enumerate(labels)],
        yticks=[float(v) for v in range(0, 91, 10)],
        ylabel="%",
        legend_loc="bottom",
        bars=bars,
        lines=lines,
    )


def _grouped(
    groups: dict[int, Sequence[float]], series: Sequence[tuple[str, int, bool]], slots: Sequence[int], width: float
) -> list[BarSeries]:
    n = len(series)
    xs = sorted(groups)
    out: list[BarSeries] = []
    for s_idx, (label, color_idx, hatch) in enumerate(series):
        offset = (slots[s_idx] - (n - 1) / 2) * width
        out.append(
            _drop_empty(
                BarSeries(
                    x=[x + offset for x in xs],
                    y=[groups[x][s_idx] for x in xs],
                    label=label,
                    color_idx=color_idx,
                    width=width,
                    hatch=hatch,
                    opacity=1.0,
                )
            )
        )
    return out


def _fig_7_3(mode: ThemeMode = "mono") -> str:
    labels = [
        "2002年10月", "2002年11月", "2002年12月", "2003年1月", "2003年2月", "2003年3月", "2003年4月",
        "2003年5月", "2003年6月", "2003年7月", "2003年8月", "2003年9月", "2003年10月", "2003年11月",
        "2004年4月", "2004年5月", "2004年7月", "2004年9月", "2004年11月", "2005年1月", "2005年2月",
        "2005年3月", "2005年4月", "2005年8月", "2006年6月", "2006年8月", "2006年9月", "2006年12月",
    ]
    favor = [2, 11, 5, 2, 5, 1, 4, 2, 3, 3, 6, 3, 1, 1, 1, 3, 2, 2, 0, 1, 2, 2, 0, 5, 1, 0, 5, 1]
    neutral = [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    against = [0, 9, 3, 1, 0, 0, 1, 0, 2, 0, 3, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 2, 1, 0, 0, 2, 0, 0]
    groups = {i: (favor[i], neutral[i], against[i]) for i in range(len(labels))}
    bars = _grouped(groups, [("赞成", 0, False), ("中立", 4, False), ("反对", 1, False)], [0, 1, 2], 0.27)
    panel = PanelSpec(
        xlim=(-0.5, len(labels) - 0.5),
        ylim=(0, 12),
        xticks=[(float(i), lab) for i, lab in enumerate(labels)],
        yticks=[float(v) for v in range(13)],
        legend_loc="bottom",
        bars=bars,
    )
    spec = FigureSpec(fig_id="7-3", title="图 7-3 从《朝日新闻》来看对竹中计划的赞成与否", panels=[panel], width=860, height=520)
    return render_figure_svg(spec, mode)


def _fig_7_4(mode: ThemeMode = "mono") -> str:
    spec = FigureSpec(
        fig_id="7-4",
        title="图 7-4 朝日新闻社舆论调查“您是支持小泉内阁还是不支持？”",
        panels=[_poll_panel(LABELS_29, [], _poll_lines(29))],
        width=860,
        height=540,
    )
    return render_figure_svg(spec, mode)


def _fig_7_5(mode: ThemeMode = "mono") -> str:
    groups = {2: (54, 31, 15), 3: (46, 36, 18), 4: (40, 44, 16), 8: (43, 46, 11), 13: (19, 64, 17)}
    bars = _grouped(groups, [("赞成不良债权处理", 0, False), ("反对不良债权处理", 4, False), ("其他", 1, False)], [0, 1, 2], 0.24)
    spec = FigureSpec(
        fig_id="7-5",
        # Scan typo: the scan prints 不良债而增加; meant 不良债权而增加.
        title=(
            "图 7-5 朝日新闻社舆论调查“政府表示，失业人数将因在2年以内最终处理大型银行的不良债权而增加。"
            "您对于即使失业人数增加，仍然推进不良债权的最终处理，是赞成还是反对？”"
        ),
        panels=[_poll_panel(LABELS_29, bars, _poll_lines(29))],
        width=860,
        height=580,
    )
    return render_figure_svg(spec, mode)


def _fig_7_6(mode: ThemeMode = "mono") -> str:
    groups = {
        4: (35, 56, 9), 5: (32, 57, 11), 7: (41, 52, 7), 9: (36, 57, 7), 10: (26, 70, 4),
        11: (30, 61, 9), 12: (32, 62, 6), 19: (27, 49, 24), 25: (26, 67, 7), 28: (28, 64, 8),
    }
    bars = _grouped(groups, [("重视结构改革", 0, False), ("重视景气对策", 4, False), ("其他", 1, False)], [0, 1, 2], 0.24)
    spec = FigureSpec(
        fig_id="7-6",
        title="图 7-6 朝日新闻社舆论调查“您是希望小泉首相积极推进结构改革？还是您希望小泉首相优先实施景气及就业对策？”",
        panels=[_poll_panel(LABELS_29, bars, _poll_lines(29))],
        width=860,
        height=580,
    )
    return render_figure_svg(spec, mode)


def _fig_7_7(mode: ThemeMode = "mono") -> str:
    groups = {
        4: (38, 48, 12, 2), 5: (24, 60, 14, 2), 7: (48, 43, 9, 0), 8: (48, 43, 8, 1),
        9: (49, 41, 9, 1), 15: (52, 38, 9, 1), 20: (60, 34, 5, 1),
    }
    bars = _grouped(
        groups,
        [("就业不安大", 0, False), ("就业不安小", 4, False), ("无就业不安", 1, False), ("其他", 2, True)],
        [0, 1, 2, 3],
        0.2,
    )
    spec = FigureSpec(
        fig_id="7-7",
        title="图 7-7 朝日新闻社舆论调查“您或您的家人对今后失去工作或收入大幅减少的不安程度有多大?”",
        panels=[_poll_panel(LABELS_30_AS_PRINTED, bars, _poll_lines(30))],
        width=860,
        height=580,
    )
    return render_figure_svg(spec, mode)


def _fig_7_8(mode: ThemeMode = "mono") -> str:
    groups = {
        0: (57, 8, 35), 2: (76, 15, 9), 3: (77, 17, 6), 7: (73, 12, 15),
        13: (79, 9, 12), 16: (74, 9, 17), 25: (73, 11, 16),
    }
    bars = _grouped(groups, [("认可结构改革", 0, False), ("其他", 1, False), ("不认可结构改革", 4, False)], [0, 2, 1], 0.24)
    support, non_support, other = _poll_lines(30)
    spec = FigureSpec(
        fig_id="7-8",
        title="图 7-8 朝日新闻社舆论调查“对于小泉首相决定推进的结构改革，您是认可还是不认可呢?”",
        panels=[_poll_panel(LABELS_30_AS_PRINTED, bars, [non_support, support, other])],
        width=860,
        height=580,
    )
    return render_figure_svg(spec, mode)


NPL_LAYER_TOPS: list[tuple[float, float, float, float, float, float]] = [
    (0, 0, 8.0, 8.0, 8.0, 8.0),
    (0, 0, 12.3, 12.3, 12.3, 12.3),
    (1.8, 12.7, 12.7, 12.7, 12.7, 12.7),
    (2.0, 13.8, 13.8, 13.8, 13.8, 13.8),
    (2.2, 13.6, 13.6, 13.6, 13.6, 13.6),
    (2.0, 13.3, 13.3, 13.3, 13.3, 13.3),
    (2.5, 12.5, 12.5, 12.5, 12.5, 12.5),
    (3.3, 13.0, 13.0, 13.0, 23.9, 23.9),
    (2.9, 13.0, 13.0, 13.0, 21.8, 25.8),
    (2.9, 13.1, 13.1, 13.1, 17.4, 21.1),
    (3.1, 13.1, 13.1, 13.1, 16.3, 19.4),
    (4.0, 13.8, 13.8, 13.8, 16.0, 18.7),
    (4.6, 13.0, 15.5, 22.0, 22.0, 22.0),
    (4.6, 13.8, 15.8, 22.0, 22.0, 22.0),
    (2.1, 15.2, 16.1, 20.3, 20.3, 20.3),
    (1.6, 14.5, 15.3, 19.3, 19.3, 19.3),
    (1.6, 14.4, 14.9, 19.8, 19.8, 19.8),
    (2.1, 13.8, 14.4, 19.3, 19.3, 19.3),
    (1.6, 12.1, 12.5, 19.3, 19.3, 19.3),
    (1.3, 12.4, 12.8, 21.8, 21.8, 21.8),
    (1.4, 15.7, 16.1, 27.6, 27.6, 27.6),
    (1.3, 12.7, 13.1, 24.6, 24.6, 24.6),
    (0.7, 8.7, 9.1, 20.5, 20.5, 20.5),
    (0.6, 8.3, 8.5, 17.5, 17.5, 17.5),
    (0.3, 6.5, 6.7, 13.6, 13.6, 13.6),
    (0.2, 8.2, 8.4, 11.7, 11.7, 11.7),
    (0.1, 4.5, 4.6, 7.2, 7.2, 7.2),
    (0.1, 3.7, 3.8, 5.9, 5.9, 5.9),
    (0, 2.2, 2.2, 4.5, 4.5, 4.5),
    (0, 1.9, 1.9, 3.7, 3.7, 3.7),
    (0, 2.1, 2.1, 3.9, 3.9, 3.9),
    (0, 2.3, 2.3, 3.8, 3.8, 3.8),
]


def _fig_8_1(mode: ThemeMode = "mono") -> str:
    tops = NPL_LAYER_TOPS
    xs = [float(i) for i in range(len(tops))]
    names = ["破产方债权", "逾期债权", "13个月以上的逾期债权", "贷款条件缓和债权", "利率减免债权", "对被支援企业的债权（参考）"]
    colors = [2, 1, 4, 3, 5, 0]
    bars: list[BarSeries] = []
    for k, (name, color_idx) in enumerate(zip(names, colors)):
        bottom = [row[k - 1] if k else 0.0 for row in tops]
        height = [round(row[k] - (row[k - 1] if k else 0.0), 3) for row in tops]
        bars.append(
            _drop_empty(BarSeries(x=xs, y=height, bottom=bottom, label=name, color_idx=color_idx, width=0.72, opacity=1.0))
        )
    panel = PanelSpec(
        xlim=(-0.6, 31.6),
        ylim=(0, 30),
        xticks=[(0, "1992/3"), (4, "1994/3"), (8, "1996/3"), (12, "1998/3"), (16, "2000/3"), (20, "2002/3"), (24, "2004/3"), (28, "2006/3")],
        yticks=[0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0],
        ylabel="万亿日元",
        xlabel="年/月末",
        legend_loc="bottom",
        bars=bars,
        lines=[
            LineSeries(x=[8.0, 25.6], y=[26.6, 8.0], color_idx=0, style="dashed", width=1.4),
            LineSeries(x=[20.0, 26.0], y=[28.5, 9.3], color_idx=0, style="solid", width=1.4),
        ],
        annotations=[
            _label(8.0, 27.4, "A", size=12.0),
            _label(19.6, 27.4, "P", size=12.0),
            _label(26.9, 10.6, "B", size=12.0),
            _label(23.8, 24.0, "金融再生", align="start"),
            _label(23.8, 22.0, "计划", align="start"),
        ],
    )
    spec = FigureSpec(fig_id="8-1", title="图 8-1 不良债权公布金额的推移（都市银行、长期信用银行、信托银行）", panels=[panel], width=860, height=600)
    spec = _with_arrows(spec, [(25.0, 8.6, 25.6, 8.0), (25.6, 11.0, 26.0, 9.3)], mode)
    return render_figure_svg(spec, mode)


def _fig_8_2(mode: ThemeMode = "mono") -> str:
    debt = [
        10246, 12327, 20606, 10818, 13150, 6587, 11413, 10726, 6884, 19851, 5512, 7387,
        11961, 14774, 11046, 9125, 7661, 7936, 6747, 11046, 10543, 8370, 9445, 4597,
        4414, 10543, 9857, 8096, 4140, 3500, 5581, 4803, 4460, 7639, 4140, 8782,
        6038, 7250, 6038, 3774, 5924, 4872, 4689, 3065, 5718, 6130, 7868, 3591,
        5855, 2744, 4940, 4003, 6862, 3637, 2882, 3866, 2836, 5924, 4117, 4803,
        5444, 2836, 4666, 5924, 3454, 2950,
    ]
    raw = [
        1531, 1700, 1627, 1600, 1716, 1430, 1709, 1586, 1455, 1709, 1414, 1400,
        1421, 1435, 1551, 1476, 1421, 1394, 1366, 1250, 1201, 1352, 1099, 1160,
        1174, 1200, 1311, 1215, 1064, 1078, 1105, 1078, 1078, 1092, 1057, 1092,
        1016, 1009, 1126, 934, 1057, 1208, 1003, 1140, 982, 1153, 1133, 1126,
        1092, 1023, 1236, 1078, 1071, 1105, 1037, 1160, 1016, 1160, 1078, 1092,
        1092, 1092, 1229, 1099, 1304, 1174,
    ]
    adjusted: list[float | None] = [
        1647, 1726, 1590, 1580, 1630, 1580, 1600, 1540, 1520, 1530, 1490, 1480,
        1510, 1483, 1428, 1455, 1430, 1394, 1380, 1256, 1250, 1250, 1153, 1200,
        1222, 1201, 1201, 1150, 1072, 1078, 1100, 1080, 1126, 1057, 1092, 1105,
        1051, 1044, 1016, 1000, 1060, 1080, 1050, 1070, 1030, 1147, 1126, 1099,
        1078, 1078, 1119, 1078, 1092, 1092, 1071, 1105, 1078, 1085, 1085, 1099,
        1126, 1133, 1126, 1099, None, None,
    ]
    xs = [float(i) for i in range(len(debt))]
    panel = PanelSpec(
        xlim=(-0.5, 65.5),
        ylim=(500, 2000),
        y2lim=(0, 25000),
        xticks=[(min(12 * k + 5.5, 62.5), str(2002 + k)) for k in range(6)],
        xlabel="年",
        yticks=[500.0, 1000.0, 1500.0, 2000.0],
        y2ticks=[0.0, 5000.0, 10000.0, 15000.0, 20000.0, 25000.0],
        ylabel="件数",
        y2label="亿日元",
        legend_loc="bottom",
        bars=[BarSeries(x=xs, y=debt, label="负债总额（右轴）", color_idx=3, width=0.72, axis="y2", opacity=1.0)],
        lines=[
            LineSeries(x=xs, y=raw, label="原数值", color_idx=5, style="solid", width=2.2),
            LineSeries(x=xs, y=adjusted, label="调整季节因素后的数值", color_idx=0, style="dashed", width=2.2),
        ],
    )
    spec = FigureSpec(fig_id="8-2", title="图 8-2 破产件数、负债总额的变迁", panels=[panel], width=860, height=540)
    return render_figure_svg(spec, mode)


def _fig_8_3(mode: ThemeMode = "mono") -> str:
    years = list(range(1980, 2007))
    real_assets = [
        26000, 33000, 45000, 55000, 57000, 68000, 96000, 104000, 118000, 201000, 116000, 94000, 69000, 47000,
        36000, 26000, 25000, 21000, 35000, 28000, 17000, 1000, 1000, -5000, -6000, -16000, 18000,
    ]
    with_stocks = [
        42000, 55000, 66000, 78000, 103000, 124000, 183000, 213000, 271000, 388000, 231000, 212000, 212000, 147000,
        140000, 133000, 114000, 86000, 86000, 111000, 95000, 69000, 60000, 89000, 110000, 171000, 174000,
    ]
    xs = [float(y) for y in years]
    panel = PanelSpec(
        xlim=(1979.4, 2006.6),
        ylim=(-50000, 450000),
        xticks=[float(y) for y in range(1980, 2007, 2)],
        yticks=[float(v) for v in range(-50000, 450001, 50000)],
        ylabel="10亿日元",
        xlabel="年",
        legend_loc="bottom",
        bars=[
            BarSeries(x=[x - 0.17 for x in xs], y=real_assets, label="实际资产", color_idx=2, width=0.32, hatch=True, opacity=1.0),
            BarSeries(x=[x + 0.17 for x in xs], y=with_stocks, label="实际资产：股票", color_idx=0, width=0.32, opacity=1.0),
        ],
        annotations=[
            _label(1996.5, 268000, "资本毁损的时代"),
            _label(2003.4, 268000, "资本恢复的时代"),
        ],
    )
    spec = FigureSpec(fig_id="8-3", title="图 8-3 民间金融机构自有资本的变化（以国民所得统计为统计口径）", panels=[panel], width=860, height=540)
    spec = _with_arrows(spec, [(1989.9, 324000, 2001.8, 84000), (2002.3, 79000, 2006.2, 234000)], mode)
    return render_figure_svg(spec, mode)


def _fig_8_4(mode: ThemeMode = "mono") -> str:
    labels = ["平成6.3", "7.3", "8.3", "9.3", "10.3", "11.3", "12.3", "13.3", "14.3", "15.3", "16.3", "17.3", "18.3"]
    losses = [3.9, 5.3, 11.1, 6.2, 10.8, 10.4, 5.3, 4.2, 7.7, 5.0, 3.2, 1.7, 0.05]
    profits = [3.1, 2.8, 4.8, 4.5, 3.5, 2.4, 3.0, 2.9, 2.8, 2.8, 3.4, 4.2, 3.6]
    xs = [float(i) for i in range(len(labels))]
    panel = PanelSpec(
        xlim=(-0.6, 12.6),
        ylim=(0, 15),
        xticks=list(zip(xs, labels)),
        yticks=[0.0, 5.0, 10.0, 15.0],
        ylabel="万亿日元",
        xlabel="年.月",
        legend_loc="top",
        bars=[
            BarSeries(x=[x + 0.15 for x in xs], y=losses, label="不良债权处置损失", color_idx=1, width=0.28, opacity=1.0),
            BarSeries(x=[x - 0.15 for x in xs], y=profits, label="业务净利润", color_idx=4, width=0.28, opacity=1.0),
        ],
    )
    spec = FigureSpec(fig_id="8-4", title="图 8-4 不良债权处置损失和业务净利润的推移", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


JAPAN_PREMIUM_VERTICES = [
    (0.0, 0.098), (1.1, 0.128), (2.1, 0.128), (3.2, 0.162), (4.0, 0.088), (5.1, 0.062), (6.1, 0.128),
    (7.1, 0.063), (8.2, 0.062), (9.3, 0.032), (11.0, 0.667), (12.2, 0.693), (14.3, 0.298), (15.0, 0.221),
    (16.0, 0.221), (17.0, 0.178), (18.0, 0.381), (19.0, 0.311), (20.0, 0.344), (21.0, 0.447), (23.0, 0.467),
    (24.0, 0.371), (24.1, 0.072), (25.2, 0.158), (26.1, 0.172), (27.4, 0.0), (28.5, 0.01), (29.1, 0.01),
    (30.3, 0.037), (31.2, 0.012), (32.2, 0.0), (33.3, 0.088), (35.4, 0.052), (36.4, 0.003), (37.2, 0.013),
    (38.3, -0.007), (39.3, 0.005), (41.3, 0.025), (42.2, 0.0), (43.2, 0.035), (44.3, 0.003), (45.3, -0.007),
    (45.9, -0.007), (47.3, 0.015), (48.9, 0.011), (49.9, 0.0), (53.2, 0.0), (53.6, -0.009), (54.8, 0.021),
    (55.8, 0.033), (57.0, -0.002), (59.1, -0.013), (59.8, 0.025), (60.0, -0.011), (61.9, 0.053), (64.2, 0.003),
    (65.4, 0.015), (68.9, 0.015), (70.9, 0.043), (72.2, 0.013), (77.1, 0.013), (78.1, 0.025), (78.9, 0.013),
    (80.4, 0.025), (81.8, 0.023), (82.8, 0.018), (83.8, 0.0), (84.0, 0.051), (85.2, 0.019), (86.0, 0.019),
    (87.5, 0.005), (88.9, 0.018), (90.9, 0.018), (92.2, 0.003), (93.4, 0.003), (95.0, 0.018), (96.0, 0.005),
]


def _fig_8_5(mode: ThemeMode = "mono") -> str:
    pts = JAPAN_PREMIUM_VERTICES
    labels = ["平成8.12", "9.12", "10.12", "11.12", "12.12", "13.12", "14.12", "15.12"]
    panel = PanelSpec(
        xlim=(0.0, 96.5),
        ylim=(-0.1, 0.7),
        xticks=[(12.0 * i, lab) for i, lab in enumerate(labels)],
        yticks=[(v / 10, f"{v / 10:.1f}") for v in range(-1, 8)],
        ylabel="%",
        xlabel="年.月",
        legend_loc="none",
        lines=[LineSeries(x=[p[0] for p in pts], y=[p[1] for p in pts], color_idx=1, style="solid", width=2.4)],
        annotations=[
            _label(14.0, 0.632, "佐佐波委员会", align="start"),
            _label(16.0, 0.575, "早期健全化法", align="start"),
            _label(93.0, 0.635, "月末", align="end"),
        ],
    )
    spec = FigureSpec(fig_id="8-5", title="图 8-5 日本溢价的变化", panels=[panel], width=860, height=500)
    return render_figure_svg(spec, mode)


def _fig_8_6(mode: ThemeMode = "mono") -> str:
    years = list(range(1980, 2007))
    totals = [
        41000, 46000, 50000, 54000, 59000, 67000, 77000, 102000, 150000, 190000, 198000, 205000, 208000, 210000,
        207000, 190000, 198000, 188000, 227000, 213000, 201000, 172000, 139000, 157000, 166000, 196000, 202000,
    ]
    public = {1998: 62000, 1999: 61000, 2000: 62000, 2001: 60000, 2002: 61000, 2003: 79000, 2004: 73000, 2005: 54000, 2006: 28000}
    private = [float(t - public.get(y, 0)) for y, t in zip(years, totals)]
    pub = [float(public.get(y, 0)) for y in years]
    xs = [float(y) for y in years]
    panel = PanelSpec(
        xlim=(1979.4, 2006.6),
        ylim=(0, 250000),
        xticks=[(float(y), f"{y}年度") for y in years],
        yticks=[float(v) for v in range(0, 250001, 50000)],
        ylabel="亿日元",
        legend_loc="bottom",
        vlines=[(1987.5, "", "solid")],
        bars=[
            BarSeries(x=xs, y=private, label="股东资本－公共资金", color_idx=3, width=0.55, opacity=1.0),
            BarSeries(x=xs, y=pub, bottom=private, label="公共资金余额", color_idx=2, width=0.55, opacity=1.0, hatch=True),
        ],
        annotations=[
            _label(1979.8, 233500, "股东资本截至1987年末", align="start"),
            _label(1979.8, 213500, "为单体股东资本←", align="start"),
            _label(1988.4, 233500, "→股东资本自1988年末", align="start"),
            _label(1988.4, 213500, "起为Tier1资本", align="start"),
            _label(2002.5, 233500, "公共资本注入"),
            _label(2002.5, 213500, "（早期健全化法）"),
        ],
    )
    spec = FigureSpec(fig_id="8-6", title="图 8-6 大型银行的股东资本的变化", panels=[panel], width=860, height=560)
    spec = _with_arrows(spec, [(2000.6, 228000, 1998.3, 227000)], mode)
    return render_figure_svg(spec, mode)


def _fig_8_7(mode: ThemeMode = "mono") -> str:
    sub = {10.0: 15500, 11.0: 13200, 11.5: 600, 12.0: 600, 12.5: 600, 12.75: 100, 13.25: 700, 14.0: 1100, 15.75: 60}
    preferred = {10.0: 3300, 11.0: 61400, 11.5: 1600, 12.0: 2550, 12.5: 400, 12.75: 2500, 13.0: 300, 15.25: 16200, 18.75: 405}
    common = {15.25: 3000}
    xs = sorted(set(sub) | set(preferred) | set(common))
    s = [float(sub.get(x, 0)) for x in xs]
    p = [float(preferred.get(x, 0)) for x in xs]
    c = [float(common.get(x, 0)) for x in xs]
    labels = ["平成10.3", "11.3", "12.3", "13.3", "14.3", "15.3", "16.3", "17.3", "18.3", "19.3"]
    panel = PanelSpec(
        xlim=(9.82, 19.24),
        ylim=(0, 80000),
        xticks=[(10.0 + i, lab) for i, lab in enumerate(labels)],
        yticks=[0.0, 20000.0, 40000.0, 60000.0, 80000.0],
        ylabel="亿日元",
        xlabel="年.月",
        legend_loc="none",
        bars=[
            _drop_empty(BarSeries(x=xs, y=s, color_idx=3, width=0.2, opacity=1.0)),
            _drop_empty(BarSeries(x=xs, y=p, bottom=s, color_idx=2, width=0.2, opacity=1.0, hatch=True)),
            _drop_empty(BarSeries(x=xs, y=c, bottom=[a + b for a, b in zip(s, p)], color_idx=0, width=0.2, opacity=1.0)),
        ],
        lines=[LineSeries(x=[10.8, 14.3], y=[23500, 23500], color_idx=0, style="solid", width=1.2)],
        annotations=[
            _label(19.15, 71200, "以季度为统计口径", align="end"),
            _label(9.92, 30100, "（金融机", align="start"),
            _label(9.92, 25500, "能稳定", align="start"),
            _label(9.92, 20900, "化法）", align="start"),
            _label(12.6, 23700, "（早期健全化法）"),
            _label(14.4, 20500, "（危机应对1号措施）", align="start"),
            _label(12.0, 48000, "优先股", align="start"),
            _label(11.6, 12300, "次级债券 次级贷款", align="start"),
            _label(14.0, 10500, "普通股", align="start"),
            _label(15.36, 11300, "（组织重组法）", align="start"),
            _label(19.17, 13500, "（金融机能强化法）", align="end"),
            _label(16.1, 5100, "次级贷款", align="start"),
            _label(16.1, 500, "60亿日元", align="start"),
            _label(19.17, 7300, "优先股", align="end"),
            _label(19.17, 2300, "405亿日元", align="end"),
        ],
    )
    spec = FigureSpec(
        fig_id="8-7",
        title="图 8-7 资本增强金额",
        subtitle="截至平成19年（2007年）3月末",
        panels=[panel],
        width=860,
        height=540,
    )
    spec = _with_arrows(
        spec,
        [
            (11.6, 49500, 11.15, 38000),
            (11.6, 14500, 11.1, 9000),
            (14.85, 13800, 15.15, 17600),
            (16.05, 10500, 15.7, 300),
            (17.65, 12000, 18.5, 300),
            (12.0, 23500, 10.8, 23500),
            (13.5, 23500, 14.3, 23500),
        ],
        mode,
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "7-1": _fig_7_1,
        "7-2": _fig_7_2,
        "7-3": _fig_7_3,
        "7-4": _fig_7_4,
        "7-5": _fig_7_5,
        "7-6": _fig_7_6,
        "7-7": _fig_7_7,
        "7-8": _fig_7_8,
        "8-1": _fig_8_1,
        "8-2": _fig_8_2,
        "8-3": _fig_8_3,
        "8-4": _fig_8_4,
        "8-5": _fig_8_5,
        "8-6": _fig_8_6,
        "8-7": _fig_8_7,
    }
