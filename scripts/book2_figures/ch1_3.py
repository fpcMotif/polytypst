from __future__ import annotations

import re
from collections.abc import Callable
from html import escape
from typing import Literal

from scripts.book2_figures.engine import (
    FONT_STACK,
    SANS_STACK,
    Annotation,
    BandSeries,
    BarSeries,
    FigureSpec,
    LineSeries,
    PanelSpec,
    ThemeMode,
    VSpan,
    get_palette,
)
from scripts.book2_figures.engine import (
    render_figure_svg as _engine_render_figure_svg,
)

_RGBA_RE = re.compile(r'fill="rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)"')


def _rgba_to_svg11(match: re.Match[str]) -> str:
    r, g, b, a = int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4)
    return f'fill="#{r:02x}{g:02x}{b:02x}" fill-opacity="{a}"'


def render_figure_svg(spec: FigureSpec, mode: ThemeMode = "mono") -> str:
    svg = _engine_render_figure_svg(spec, mode)
    svg = _RGBA_RE.sub(_rgba_to_svg11, svg)
    return svg.replace('fill="url(#hatch_mono)"', 'fill="#cbd5e1"')


def _half_years(start: int, end: int) -> list[float]:
    pts: list[float] = []
    for y in range(start, end + 1):
        pts.append(float(y))
        pts.append(float(y) + 0.5)
    return pts


def gen_fig_1_1(mode: ThemeMode = "mono") -> str:
    xs = _half_years(1985, 2001)
    r_act = [
        6.2, 6.8, 5.4, 4.5, 4.0, 3.5, 3.6, 4.0, 4.6, 5.8,
        7.2, 8.1, 7.9, 6.6, 4.9, 4.0, 3.2, 2.6, 2.1, 2.1,
        1.9, 0.5, 0.5, 0.5, 0.4, 0.5, 0.6, 0.6, 0.4, 0.1,
        0.1, 0.0, 0.2, -0.1,
    ]
    r_diff = [
        -2.5, -2.5, -2.5, -2.5, -2.5, -2.5, -2.5, -2.5, 4.8, 4.4,
        3.9, 3.5, 3.5, 3.7, 3.7, 3.6, 3.5, 3.4, 3.4, 3.3,
        3.3, 3.2, 3.1, 3.1, 3.0, 3.0, 2.9, 2.8, 2.7, 2.6,
        2.5, 2.5, 2.4, 2.3,
    ]
    r_sim = [a + d for a, d in zip(r_act, r_diff)]

    gap_act = [
        0.0, -0.1, -1.1, -1.3, -2.6, -0.9, 0.2, 0.9, 1.3, 1.5,
        2.2, 3.2, 3.1, 2.0, 1.0, 0.3, -0.5, -2.5, -2.4, -2.1,
        -2.5, -1.6, -0.8, 0.7, 1.0, 0.3, -1.2, -1.2, -1.9, -1.9,
        -0.9, 0.1, 0.1, -1.8,
    ]
    gap_diff = [
        0.4, 0.9, 1.6, 1.9, 2.0, 2.1, 1.9, 1.5, 0.8, -0.1,
        -0.2, 0.1, 0.15, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05,
        0.05, 0.05, 0.05, 0.05, 0.0, 0.0, -0.05, -0.1, -0.1, -0.1,
        -0.15, -0.15, -0.2, -0.2,
    ]
    gap_sim = [a + d for a, d in zip(gap_act, gap_diff)]

    cpi_act = [
        2.0, 1.6, 0.8, 0.3, 0.5, 0.6, 0.7, 0.8, 1.6, 2.1,
        2.5, 2.9, 2.8, 2.5, 2.2, 1.7, 1.2, 1.1, 0.5, -0.3,
        -0.5, -0.1, 0.2, 0.4, 0.3, -0.2, -0.2, 0.0, 0.0, -0.3,
        -0.7, -1.0, -1.0, -1.1,
    ]
    cpi_diff = [
        0.1, 0.3, 0.8, 1.3, 1.8, 2.1, 2.3, 2.5, 2.6, 2.6,
        2.5, 2.2, 2.2, 2.25, 2.25, 2.25, 2.25, 2.2, 2.15, 2.1,
        2.05, 2.0, 1.95, 1.9, 1.85, 1.8, 1.75, 1.7, 1.65, 1.6,
        1.55, 1.5, 1.45, 1.4,
    ]
    cpi_sim = [a + d for a, d in zip(cpi_act, cpi_diff)]

    gdp_act = [
        5.6, 5.2, 3.1, 3.0, 2.9, 5.0, 7.1, 6.4, 5.6, 4.8,
        4.8, 5.4, 4.5, 2.2, 1.1, 0.8, 0.9, -0.3, 0.0, 2.1,
        1.5, 1.9, 3.3, 3.4, 2.4, 0.4, -1.5, -0.9, -0.2, -0.2,
        1.8, 2.6, 1.3, -1.4,
    ]
    gdp_diff = [
        0.5, 1.0, 1.2, 0.9, 0.45, 0.15, 0.0, -0.2, -0.6, -1.2,
        -1.6, -1.1, 0.1, 0.3, 0.15, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
    ]
    gdp_sim = [a + d for a, d in zip(gdp_act, gdp_diff)]

    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1985, 2002, 2)]
    spec = FigureSpec(
        fig_id="1-1",
        title="图 1-1 日元升值萧条期的利率下调（在 1985—1988 年的 4 年间下调 2.5%）",
        note="资料来源：翁、木村、原（2008）",
        rows=2,
        cols=2,
        width=920,
        height=640,
        panels=[
            PanelSpec(
                title="（1）名义短期利率（3个月）",
                xlim=(1984.7, 2001.8),
                ylim=(-3.0, 12.0),
                xticks=xt,
                yticks=list(range(-3, 13)),
                ylabel="%",
                xlabel="年",
                bars=[BarSeries(x=xs, y=r_diff, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=r_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=r_sim, label="实施额外宽松货币政策的情况", color_idx=1, style="dashed", width=2.1),
                ],
            ),
            PanelSpec(
                title="（2）GDP 缺口",
                xlim=(1984.7, 2001.8),
                ylim=(-3.0, 5.0),
                xticks=xt,
                yticks=[-3, -2, -1, 0, 1, 2, 3, 4, 5],
                ylabel="%",
                xlabel="年",
                bars=[BarSeries(x=xs, y=gap_diff, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=gap_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=gap_sim, label="实施额外宽松货币政策的情况", color_idx=1, style="dashed", width=2.1),
                ],
            ),
            PanelSpec(
                title="（3）综合 CPI（剔除生鲜和公共费用）",
                xlim=(1984.7, 2001.8),
                ylim=(-2.0, 6.0),
                xticks=xt,
                yticks=[-2, -1, 0, 1, 2, 3, 4, 5, 6],
                ylabel="（同比，%）",
                xlabel="年",
                bars=[BarSeries(x=xs, y=cpi_diff, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=cpi_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=cpi_sim, label="实施额外宽松货币政策的情况", color_idx=1, style="dashed", width=2.1),
                ],
            ),
            PanelSpec(
                title="（4）GDP 增长率",
                xlim=(1984.7, 2001.8),
                ylim=(-3.0, 8.0),
                xticks=xt,
                yticks=list(range(-3, 9)),
                ylabel="（同比，%）",
                xlabel="年",
                bars=[BarSeries(x=xs, y=gdp_diff, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=gdp_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=gdp_sim, label="实施额外宽松货币政策的情况", color_idx=1, style="dashed", width=2.1),
                ],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_1_2(mode: ThemeMode = "mono") -> str:
    xs = _half_years(1990, 2001)
    r_act = [
        7.4, 8.3, 8.0, 6.7, 5.0, 3.9, 3.3, 2.5, 2.25, 2.25,
        1.7, 0.65, 0.55, 0.5, 0.5, 0.6, 0.8, 0.65, 0.25, 0.17,
        0.08, 0.35, 0.17, -0.08,
    ]
    r_diff = [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.15, -1.15, 0.75,
        -1.8, -0.75, -0.7, 0.85, 1.05, 0.75, -0.85, -0.8, -0.42, 0.85,
        1.25, 0.55, 0.28, 0.3,
    ]
    r_sim = [a + d for a, d in zip(r_act, r_diff)]
    scan_missing_bars = (15, 21, 22)
    r_bar = [0.0 if i in scan_missing_bars else d for i, d in enumerate(r_diff)]

    gap_act = [
        2.3, 3.3, 3.1, 2.1, 1.1, 0.1, -0.4, -2.4, -2.4, -1.9,
        -2.4, -1.4, -0.2, 0.9, 1.1, 0.5, -1.0, -1.1, -1.8, -1.9,
        -0.8, 0.2, 0.2, -1.7,
    ]
    gap_diff = [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.45, 0.65,
        0.5, 0.35, 0.5, 0.4, 0.25, 0.1, 0.2, 0.4, 0.65, 0.55,
        0.4, 0.35, 0.2, 0.38,
    ]
    gap_sim = [a + d for a, d in zip(gap_act, gap_diff)]

    cpi_act = [
        2.2, 2.7, 2.9, 2.8, 2.6, 2.4, 1.8, 1.2, 1.1, 0.6,
        -0.3, -0.5, -0.1, 0.2, 0.4, 0.3, -0.2, -0.2, 0.0, 0.0,
        -0.3, -0.7, -1.0, -1.05,
    ]
    cpi_diff = [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.15, 0.28, 0.38,
        0.52, 0.52, 0.58, 0.60, 0.63, 0.60, 0.68, 0.78, 0.90, 1.00,
        1.00, 1.00, 1.00, 1.08,
    ]
    cpi_sim = [a + d for a, d in zip(cpi_act, cpi_diff)]

    gdp_act = [
        4.9, 5.4, 4.4, 2.2, 1.2, 0.8, 1.1, -0.2, 0.0, 2.1,
        1.6, 2.0, 3.4, 3.5, 2.5, 0.6, -1.6, -1.0, 0.0, -0.1,
        1.6, 2.7, 1.5, -1.2,
    ]
    gdp_diff = [
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.35, 0.45,
        0.1, -0.2, 0.1, 0.1, -0.2, -0.25, 0.1, 0.35, 0.48, 0.15,
        -0.15, -0.28, 0.0, 0.2,
    ]
    gdp_sim = [a + d for a, d in zip(gdp_act, gdp_diff)]

    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in [1990, 1992, 1994, 1996, 1998, 2000, 2001]]
    spec = FigureSpec(
        fig_id="1-2",
        title="图 1-2 非线性规则 1 的模拟",
        note="资料来源：翁、木村、原（2008）",
        rows=2,
        cols=2,
        width=920,
        height=640,
        panels=[
            PanelSpec(
                title="（2）GDP 缺口",
                xlim=(1989.7, 2001.8),
                ylim=(-3.0, 4.0),
                xticks=xt,
                yticks=[-3, -2, -1, 0, 1, 2, 3, 4],
                ylabel="%",
                xlabel="年",
                bars=[BarSeries(x=xs, y=gap_diff, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=gap_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=gap_sim, label="非线性规则", color_idx=1, style="dashed", width=2.1),
                ],
            ),
            PanelSpec(
                title="（1）名义短期利率（3个月）",
                xlim=(1989.7, 2001.8),
                ylim=(-3.0, 9.0),
                xticks=xt,
                yticks=list(range(-3, 10)),
                ylabel="%",
                xlabel="年",
                bars=[BarSeries(x=xs, y=r_bar, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=r_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=r_sim, label="非线性规则", color_idx=1, style="dashed", width=2.1),
                ],
            ),
            PanelSpec(
                title="（4）GDP 增长率",
                xlim=(1989.7, 2001.8),
                ylim=(-3.0, 8.0),
                xticks=xt,
                yticks=list(range(-3, 9)),
                ylabel="（同比，%）",
                xlabel="年",
                bars=[BarSeries(x=xs, y=gdp_diff, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=gdp_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=gdp_sim, label="非线性规则", color_idx=1, style="dashed", width=2.1),
                ],
            ),
            PanelSpec(
                title="（3）综合 CPI（剔除生鲜和公共费用）",
                xlim=(1989.7, 2001.8),
                ylim=(-2.0, 4.0),
                xticks=xt,
                yticks=[-2, -1, 0, 1, 2, 3, 4],
                ylabel="（同比，%）",
                xlabel="年",
                bars=[BarSeries(x=xs, y=cpi_diff, label="模拟结果－实际值", color_idx=2, width=0.38, hatch=True)],
                lines=[
                    LineSeries(x=xs, y=cpi_act, label="实际值", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=cpi_sim, label="非线性规则", color_idx=1, style="dashed", width=2.1),
                ],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_2_1(mode: ThemeMode = "mono") -> str:
    spec = FigureSpec(
        fig_id="2-1",
        title="图 2-1 Borio 和 Filardo（2007）估算的国内供需缺口和全球供需缺口参数的时间变化",
        note="注：条形代表各国家估算值的简单平均值。",
        width=820,
        height=460,
        panels=[
            PanelSpec(
                xlim=(0.3, 4.7),
                ylim=(-0.05, 0.45),
                xticks=[
                    (1.0, "1975—1995"),
                    (2.0, "1985—2005"),
                    (3.0, "1975—1995"),
                    (4.0, "1985—2005"),
                ],
                yticks=[0.0, 0.1, 0.2, 0.3],
                legend_loc="none",
                bars=[
                    BarSeries(x=[1.0, 2.0], y=[-0.039, 0.286], label="全球缺口（ϕ）", color_idx=0, width=0.55),
                    BarSeries(
                        x=[3.0, 4.0],
                        y=[0.255, 0.088],
                        label="国内缺口（β）",
                        color_idx=1,
                        width=0.55,
                        hatch=True,
                    ),
                ],
                annotations=[
                    Annotation(x=1.5, y=0.40, text="全球缺口（ϕ）", dy=0.0, arrow=False, color_idx=0, fontsize=13.0),
                    Annotation(x=3.5, y=0.40, text="国内缺口（β）", dy=0.0, arrow=False, color_idx=1, fontsize=13.0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_2_2(mode: ThemeMode = "mono") -> str:
    pal = get_palette(mode)
    W, H = 860, 512
    countries: list[tuple[str, float | None, float | None]] = [
        ("BE", 0.49, -0.04),
        ("CA", 0.49, 0.33),
        ("CH", 0.42, 0.15),
        ("DE", 0.26, 0.19),
        ("FR", 0.40, 0.17),
        ("GB", 0.49, 0.19),
        ("IT", 0.77, 0.10),
        ("JP", 0.24, 0.36),
        ("NL", 0.40, 0.18),
        ("SE", 0.72, -0.10),
        ("US", 0.47, 0.26),
        ("XM", 0.43, 0.13),
        ("ES", 0.47, 0.03),
        ("AU", 0.77, 0.11),
        ("AT", 0.80, 0.68),
        ("NO", 0.74, 0.10),
        ("NZ", None, None),
    ]
    px0, py0, pw, ph = 58.0, 78.0, 728.0, 320.0
    px1, py1 = px0 + pw, py0 + ph
    ylo, yhi = -0.2, 1.0

    def map_x(idx: int) -> float:
        return px0 + (idx + 0.5) / len(countries) * pw

    def map_y(yv: float) -> float:
        return py1 - (yv - ylo) / (yhi - ylo) * ph

    down_col = pal.series[0]
    up_col = pal.series[1]
    title_str = escape("图 2-2 Borio 和 Filardo（2007）估算的通货膨胀对国内供需缺口敏感性的时间变化")
    sub_str = escape("通货膨胀对国内宽松措施的敏感性持续下降 1980—2005*）")
    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        "<defs>",
        f'<marker id="arr_down_{mode}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M 0 1.5 L 8.5 5 L 0 8.5 z" fill="{down_col}"/></marker>',
        f'<marker id="arr_up_{mode}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 1.2 L 9 5 L 0 8.8 z" fill="{up_col}"/></marker>',
        "</defs>",
        f'<rect width="{W}" height="{H}" fill="{pal.bg}"/>',
        f'<text x="{W / 2:.1f}" y="28.0" text-anchor="middle" font-family="{FONT_STACK}" font-size="16.5" font-weight="700" fill="{pal.fg}">{title_str}</text>',
        f'<text x="{W / 2:.1f}" y="49.0" text-anchor="middle" font-family="{FONT_STACK}" font-size="12.5" fill="{pal.muted}">{sub_str}</text>',
        f'<rect x="{px0:.2f}" y="{py0:.2f}" width="{pw:.2f}" height="{ph:.2f}" fill="{pal.panel_bg}" stroke="{pal.axis}" stroke-width="1.2"/>',
    ]

    for yv in [-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        yy = map_y(yv)
        lab = f"{yv:.1f}" if abs(yv) > 1e-6 else "0"
        dash_attr = "" if abs(yv) < 1e-6 else 'stroke-dasharray="2.5,2.5"'
        out.append(
            f'<line x1="{px0:.2f}" y1="{yy:.2f}" x2="{px1:.2f}" y2="{yy:.2f}" '
            f'stroke="{pal.zero if abs(yv) < 1e-6 else pal.grid}" stroke-width="{1.3 if abs(yv) < 1e-6 else 0.9}" '
            f"{dash_attr}/>"
        )
        out.append(
            f'<line x1="{px1 - 5:.2f}" y1="{yy:.2f}" x2="{px1:.2f}" y2="{yy:.2f}" stroke="{pal.axis}" stroke-width="1.1"/>'
        )
        out.append(
            f'<text x="{px1 + 7:.2f}" y="{yy + 4:.2f}" text-anchor="start" font-family="{SANS_STACK}" font-size="10.8" fill="{pal.muted}">{lab}</text>'
        )

    for i, (code, y0, y1_val) in enumerate(countries):
        xx = map_x(i)
        is_jp = code == "JP"
        col = up_col if is_jp else down_col
        sw = "2.5" if is_jp else "1.8"
        out.append(
            f'<line x1="{xx:.2f}" y1="{py1 - 5:.2f}" x2="{xx:.2f}" y2="{py1:.2f}" stroke="{pal.axis}" stroke-width="1.0"/>'
        )
        out.append(
            f'<text x="{xx:.2f}" y="{py1 + 17:.2f}" text-anchor="middle" font-family="{SANS_STACK}" '
            f'font-size="10.8" font-weight="{"700" if is_jp else "500"}" fill="{col if is_jp else pal.fg}">{code}</text>'
        )
        if y0 is None or y1_val is None:
            continue
        sy0 = map_y(y0)
        sy1 = map_y(y1_val)
        line_y2 = sy1 + 6.0 if is_jp else sy1 - 6.0
        out.append(
            f'<line x1="{xx:.2f}" y1="{sy0:.2f}" x2="{xx:.2f}" y2="{line_y2:.2f}" stroke="{col}" stroke-width="{sw}"/>'
        )
        if is_jp:
            out.append(
                f'<polygon points="{xx:.2f},{sy1:.2f} {xx - 4.5:.2f},{sy1 + 8.5:.2f} {xx + 4.5:.2f},{sy1 + 8.5:.2f}" fill="{col}"/>'
            )
        else:
            out.append(
                f'<polygon points="{xx:.2f},{sy1:.2f} {xx - 4.0:.2f},{sy1 - 7.8:.2f} {xx + 4.0:.2f},{sy1 - 7.8:.2f}" fill="{col}"/>'
            )

    note_lines = [
        "注：AT 奥地利；AU 澳大利亚；BE 比利时；CA 加拿大；CH 瑞士；DE 德国；ES 西班牙；FR 法国；GB 英国；IT 意大利；",
        "JP 日本；NL 荷兰；NO 挪威；NZ 新西兰；SE 瑞典；US 美国；XM 欧元区。",
        "*）这表明 1980—1992 年之间以及 1993—2005 年之间国内产出缺口变化对通货膨胀的年度影响；年度影响的估算公式是",
        "β×(1+γ+γ²+γ³)，基于估算等式 πₜ = c + γπₜ₋₁ + βGapᴰₜ₋₁ + εₜ 而计算，详见图 1。",
    ]
    for k, line in enumerate(note_lines):
        out.append(
            f'<text x="26.0" y="{H - 60 + 16 * k:.1f}" font-family="{FONT_STACK}" font-size="10.5" fill="{pal.muted}">'
            f"{escape(line)}</text>"
        )
    out.append("</svg>")
    return "\n".join(out)


def gen_fig_2_3(mode: ThemeMode = "mono") -> str:
    xs = [1987.5 + 0.5 * i for i in range(38)]
    uk_y = [
        0.68, 0.45, 0.48, 0.50, 0.42, 0.18, 0.35, 0.32, 0.52, 0.65,
        0.60, 0.62, 0.72, 0.62, 0.52, 0.50, 0.52, 0.56, 0.54, 0.62,
        0.56, 0.70, 0.68, 0.58, 0.65, 0.60, -0.18, -0.35, -0.28, -0.28,
        -0.18, -0.45, -0.22, -0.18, -0.36, -0.10, 0.25, 0.62,
    ]
    uk_se = [0.28] * 26 + [0.34] * 12

    jp_y = [
        0.02, -0.15, -0.18, -0.17, -0.25, -0.20, -0.20, -0.22, -0.21, -0.18,
        -0.14, -0.18, -0.16, -0.04, -0.06, 0.12, 0.15, 0.15, 0.06, 0.05,
        0.06, 0.22, 0.30, 0.26, 0.28, 0.30, 0.32, 0.31, 0.34, 0.22,
        0.18, 0.09, 0.18, 0.16, 0.14, 0.15, 0.16, 0.12,
    ]
    jp_se = [0.22 - 0.002 * i for i in range(38)]

    nl_y = [
        0.15, 0.25, 0.12, 0.08, 0.01, -0.12, -0.20, -0.08, -0.04, 0.08,
        0.11, 0.16, 0.22, 0.19, 0.04, 0.18, 0.28, 0.30, 0.31, 0.35,
        0.36, 0.38, 0.56, 0.54, 0.40, 0.06, 0.18, 0.14, 0.12, 0.10,
        0.07, 0.05, 0.02, -0.02, -0.03, 0.01, 0.02, 0.03,
    ]
    nl_se = [0.22 if i < 25 else 0.13 for i in range(38)]

    us_y = [
        0.16, 0.17, 0.16, 0.15, 0.18, 0.12, 0.06, 0.21, 0.08, 0.15,
        0.23, 0.22, 0.15, 0.20, 0.20, 0.18, 0.14, 0.12, 0.11, 0.08,
        0.15, 0.14, 0.20, 0.20, 0.26, 0.22, 0.01, -0.10, -0.16, -0.22,
        -0.36, 0.05, 0.15, 0.21, 0.19, 0.21, 0.21, 0.20,
    ]
    us_se = [0.18 if i < 25 else 0.11 for i in range(38)]

    def make_panel(title: str, yvals: list[float], se: list[float], c_idx: int) -> PanelSpec:
        return PanelSpec(
            title=title,
            xlim=(1987.5, 2006.0),
            ylim=(-2.0, 1.45),
            xticks=[1990, 1995, 2000, 2005],
            yticks=[(v / 10, f"{v / 10:.1f}") for v in range(-20, 13, 4)],
            legend_loc="none",
            bands=[
                BandSeries(
                    x=xs,
                    y_low=[v - s for v, s in zip(yvals, se)],
                    y_high=[v + s for v, s in zip(yvals, se)],
                    label="90% 置信区间",
                    color_idx=c_idx,
                    show_edges=False,
                )
            ],
            lines=[LineSeries(x=xs, y=yvals, label="国内产出缺口系数", color_idx=c_idx, width=2.2)],
        )

    spec = FigureSpec(
        fig_id="2-3",
        title="图 2-3 使用 Ihrig 等（2007）的各国数据估算结果示例",
        note="资料来源：Ihrig 等（2007），阴影部分为 90% 具有显著性",
        rows=2,
        cols=2,
        width=900,
        height=760,
        panels=[
            make_panel("英国", uk_y, uk_se, 0),
            make_panel("日本", jp_y, jp_se, 1),
            make_panel("荷兰", nl_y, nl_se, 2),
            make_panel("美国", us_y, us_se, 3),
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_2_4(mode: ThemeMode = "mono") -> str:
    xs = [1976.0 + 0.5 * i for i in range(43)]
    k_boj = [
        -0.38, -0.22, -0.10, -0.02, 0.15, 0.05, 0.08, -0.02, -0.04, 0.12,
        0.20, 0.18, 0.17, 0.16, 0.18, 0.15, 0.18, 0.21, 0.22, 0.21,
        0.22, 0.21, 0.26, 0.24, 0.23, 0.32, 0.35, 0.38, 0.36, 0.37,
        0.15, 0.16, 0.22, 0.03, 0.06, 0.08, 0.10, 0.04, 0.06, 0.09,
        0.02, 0.08, -0.01,
    ]
    k_boj_se = [0.26 if i < 8 else (0.11 if i < 32 else 0.15) for i in range(43)]

    k_hp = [
        -0.65, -0.55, -0.58, -0.28, 0.08, 0.06, 0.10, 0.08, 0.28, 0.34,
        0.50, 0.42, 0.38, 0.36, 0.34, 0.32, 0.36, 0.42, 0.60, 0.62,
        0.55, 0.42, 0.35, 0.28, 0.30, 0.22, 0.24, 0.20, 0.22, 0.38,
        0.30, 0.22, 0.20, 0.08, 0.06, 0.02, 0.01, 0.05, -0.02, 0.04,
        -0.08, -0.04, -0.02,
    ]
    k_hp_se = [0.28 if i < 8 else (0.14 if i < 28 else 0.11) for i in range(43)]

    lam_boj = [
        0.78, 0.75, 0.66, 0.56, 0.57, 0.52, 0.47, 0.45, 0.48, 0.60,
        0.68, 0.62, 0.56, 0.66, 0.54, 0.58, 0.56, 0.52, 0.47, 0.52,
        0.48, 0.49, 0.36, 0.41, 0.38, 0.24, 0.06, 0.15, 0.12, 0.14,
        0.48, 0.56, 0.60, 0.74, 0.72, 0.64, 0.62, 0.48, 0.58, 0.52,
        0.64, 0.62, 0.56,
    ]
    lam_boj_se = [0.16 if i < 25 else 0.22 for i in range(43)]

    lam_hp = [
        0.79, 0.72, 0.64, 0.58, 0.54, 0.55, 0.44, 0.41, 0.46, 0.52,
        0.42, 0.39, 0.46, 0.38, 0.43, 0.40, 0.34, 0.22, 0.07, 0.12,
        0.28, 0.46, 0.52, 0.62, 0.66, 0.71, 0.70, 0.77, 0.72, 0.58,
        0.62, 0.57, 0.72, 0.70, 0.74, 0.70, 0.68, 0.56, 0.62, 0.52,
        0.72, 0.68, 0.60,
    ]
    lam_hp_se = [0.16 if i < 22 else 0.20 for i in range(43)]

    lr_boj = [
        -2.4, -1.0, -0.4, -0.05, 0.35, 0.12, 0.18, -0.05, -0.08, 0.25,
        0.62, 0.48, 0.36, 0.46, 0.38, 0.36, 0.38, 0.42, 0.40, 0.45,
        0.41, 0.40, 0.40, 0.40, 0.38, 0.41, 0.39, 0.42, 0.41, 0.43,
        0.32, 0.38, 0.50, 0.04, 0.18, 0.18, 0.22, 0.08, 0.12, 0.16,
        0.04, 0.15, -0.02,
    ]
    lr_hp = [
        -5.2, -2.1, -1.8, -0.6, 0.18, 0.14, 0.20, 0.15, 0.52, 0.70,
        0.88, 0.68, 0.65, 0.58, 0.58, 0.56, 0.62, 0.68, 0.72, 0.75,
        0.74, 0.76, 0.72, 0.74, 0.78, 0.76, 0.80, 0.84, 0.82, 0.88,
        0.65, 0.58, 0.72, 0.32, 0.36, 0.12, 0.05, 0.10, -0.08, 0.06,
        -0.42, -0.25, -0.08,
    ]

    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1976, 1997, 4)]
    spec = FigureSpec(
        fig_id="2-4",
        title="图 2-4 木村等人（2008）对诱导式菲利普斯曲线的估算结果",
        subtitle="通货膨胀率：CPI，测算期：40 个季度",
        rows=3,
        cols=2,
        width=920,
        height=1300,
        panels=[
            PanelSpec(
                title="（1）产出缺口：BOJ 缺口",
                xlim=(1976.0, 1997.0),
                ylim=(-1.5, 1.0),
                xticks=xt,
                yticks=[-1.5, -1.0, -0.5, 0.0, 0.5, 1.0],
                xlabel="（估算起始期，年）",
                bands=[
                    BandSeries(
                        x=xs,
                        y_low=[v - 2 * s for v, s in zip(k_boj, k_boj_se)],
                        y_high=[v + 2 * s for v, s in zip(k_boj, k_boj_se)],
                        label="置信区间（±2标准偏差）",
                        color_idx=1,
                        show_edges=False,
                    ),
                    BandSeries(
                        x=xs,
                        y_low=[v - s for v, s in zip(k_boj, k_boj_se)],
                        y_high=[v + s for v, s in zip(k_boj, k_boj_se)],
                        label="置信区间（±1标准偏差）",
                        color_idx=0,
                        show_edges=False,
                    ),
                ],
                lines=[LineSeries(x=xs, y=k_boj, label="斜率（κ）", color_idx=0, width=2.2)],
            ),
            PanelSpec(
                title="（2）产出缺口：HP 缺口",
                xlim=(1976.0, 1997.0),
                ylim=(-1.5, 1.0),
                xticks=xt,
                yticks=[-1.5, -1.0, -0.5, 0.0, 0.5, 1.0],
                xlabel="（估算起始期，年）",
                bands=[
                    BandSeries(
                        x=xs,
                        y_low=[v - 2 * s for v, s in zip(k_hp, k_hp_se)],
                        y_high=[v + 2 * s for v, s in zip(k_hp, k_hp_se)],
                        color_idx=1,
                        show_edges=False,
                    ),
                    BandSeries(
                        x=xs,
                        y_low=[v - s for v, s in zip(k_hp, k_hp_se)],
                        y_high=[v + s for v, s in zip(k_hp, k_hp_se)],
                        color_idx=0,
                        show_edges=False,
                    ),
                ],
                lines=[LineSeries(x=xs, y=k_hp, label="斜率（κ）", color_idx=0, width=2.2)],
            ),
            PanelSpec(
                xlim=(1976.0, 1997.0),
                ylim=(-0.6, 1.2),
                xticks=xt,
                yticks=[-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2],
                xlabel="（估算起始期，年）",
                bands=[
                    BandSeries(
                        x=xs,
                        y_low=[v - 2 * s for v, s in zip(lam_boj, lam_boj_se)],
                        y_high=[v + 2 * s for v, s in zip(lam_boj, lam_boj_se)],
                        color_idx=1,
                        show_edges=False,
                    ),
                    BandSeries(
                        x=xs,
                        y_low=[v - s for v, s in zip(lam_boj, lam_boj_se)],
                        y_high=[v + s for v, s in zip(lam_boj, lam_boj_se)],
                        color_idx=0,
                        show_edges=False,
                    ),
                ],
                lines=[LineSeries(x=xs, y=lam_boj, label="惯性（Σλ）", color_idx=0, width=2.2)],
            ),
            PanelSpec(
                xlim=(1976.0, 1997.0),
                ylim=(-0.6, 1.2),
                xticks=xt,
                yticks=[-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2],
                xlabel="（估算起始期，年）",
                bands=[
                    BandSeries(
                        x=xs,
                        y_low=[v - 2 * s for v, s in zip(lam_hp, lam_hp_se)],
                        y_high=[v + 2 * s for v, s in zip(lam_hp, lam_hp_se)],
                        color_idx=1,
                        show_edges=False,
                    ),
                    BandSeries(
                        x=xs,
                        y_low=[v - s for v, s in zip(lam_hp, lam_hp_se)],
                        y_high=[v + s for v, s in zip(lam_hp, lam_hp_se)],
                        color_idx=0,
                        show_edges=False,
                    ),
                ],
                lines=[LineSeries(x=xs, y=lam_hp, label="惯性（Σλ）", color_idx=0, width=2.2)],
            ),
            PanelSpec(
                xlim=(1976.0, 1997.0),
                ylim=(-3.0, 1.0),
                xticks=xt,
                yticks=[-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0],
                xlabel="（估算起始期，年）",
                lines=[LineSeries(x=xs, y=lr_boj, label="效果完全显现下时的斜率（κ/(1−Σλ)）", color_idx=0, width=2.2)],
            ),
            PanelSpec(
                xlim=(1976.0, 1997.0),
                ylim=(-6.0, 2.0),
                xticks=xt,
                yticks=[-6.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0],
                xlabel="（估算起始期，年）",
                lines=[LineSeries(x=xs, y=lr_hp, label="效果完全显现下时的斜率（κ/(1−Σλ)）", color_idx=0, width=2.2)],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_2_5(mode: ThemeMode = "mono") -> str:
    xs60 = [1995.0 + 0.5 * i for i in range(25)]
    g60_no = [
        -0.025, -0.012, -0.012, -0.02, -0.022, -0.022, -0.035, -0.02, 0.015, 0.03,
        0.125, 0.135, 0.135, 0.15, 0.16, 0.20, 0.225, 0.21, 0.235, 0.225,
        0.215, 0.22, 0.21, 0.205, 0.18,
    ]
    g60_no_se = [0.045] * 10 + [0.05] * 8 + [0.07] + [0.05] * 6

    xs40 = [1990.0 + 0.5 * i for i in range(35)]
    g40_no = [
        -0.035, -0.022, -0.03, -0.02, -0.005, 0.005, -0.02, -0.015, 0.0, 0.0,
        0.10, 0.105, 0.11, 0.125, 0.14, 0.20, 0.25, 0.29, 0.30, 0.31,
        0.295, 0.30, 0.28, 0.28, 0.23, 0.21, 0.20, 0.13, 0.14, 0.125,
        0.12, 0.11, 0.07, 0.05, 0.03,
    ]
    g40_no_se = [
        0.095, 0.085, 0.075, 0.065, 0.06, 0.055, 0.05, 0.05, 0.05, 0.05,
        0.05, 0.05, 0.055, 0.06, 0.065, 0.07, 0.07, 0.07, 0.07, 0.07,
        0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.065, 0.065,
        0.065, 0.065, 0.065, 0.065, 0.065,
    ]

    xs_int = [
        1995.0, 1995.47, 1995.9, 1996.13, 1996.42, 1996.79, 1997.23, 1997.6, 1998.03, 1998.4,
        1998.62, 1998.84, 1999.13, 1999.57, 1999.87, 2000.09, 2000.6, 2000.89, 2001.11, 2001.4,
        2001.7, 2001.92, 2002.2, 2002.5, 2002.87, 2003.17, 2003.39, 2003.68, 2003.97, 2004.19,
        2004.63, 2004.93, 2005.22, 2005.44, 2005.66, 2005.88, 2006.1, 2006.54, 2006.83, 2007.12,
    ]
    g60_int = [
        0.46, 0.52, 0.60, 0.62, 0.75, 0.78, 0.82, 1.02, 1.10, 1.12,
        1.17, 1.12, 1.12, 1.39, 0.95, 0.72, 0.72, 1.14, 0.85, 0.62,
        0.25, 0.18, 0.40, 0.60, 1.00, 1.50, 1.45, 1.80, 1.60, 1.47,
        1.47, 1.20, 1.22, 1.18, 1.12, 1.12, 1.30, 1.32, 1.20, 1.25,
    ]
    g60_int_se = [
        0.28, 0.29, 0.29, 0.30, 0.30, 0.30, 0.31, 0.31, 0.32, 0.32,
        0.32, 0.32, 0.33, 0.36, 0.37, 0.37, 0.48, 0.56, 0.62, 0.70,
        0.80, 0.84, 0.75, 0.68, 0.64, 0.78, 0.70, 0.66, 0.64, 0.62,
        0.60, 0.58, 0.55, 0.52, 0.50, 0.50, 0.48, 0.48, 0.47, 0.46,
    ]

    xs_cross = [
        1995.2, 1995.6, 1996.1, 1996.47, 1996.98, 1997.48, 1998.06, 1998.5, 1998.85, 1999.14,
        1999.65, 2000.15, 2000.8, 2001.02, 2001.38, 2001.67, 2001.96, 2002.32, 2002.54, 2002.9,
        2003.19, 2003.4, 2003.69, 2003.98, 2004.27, 2004.63, 2004.91, 2005.27, 2005.71, 2005.92,
        2006.14, 2006.57, 2006.79, 2007.08,
    ]
    cross_60 = [
        -2.2, -2.6, -2.9, -3.7, -4.0, -5.0, -5.3, -5.6, -5.2, -5.5,
        -6.8, -3.3, -3.3, -5.6, -3.8, -2.8, -0.3, -1.5, -2.3, -3.8,
        -7.0, -6.6, -8.5, -7.3, -6.6, -6.6, -5.3, -5.4, -5.0, -5.0,
        -5.9, -6.0, -5.6, -5.8,
    ]
    cross_60_se = [
        1.4, 1.4, 1.4, 1.45, 1.5, 1.5, 1.55, 1.6, 1.65, 1.7,
        1.85, 1.85, 2.4, 3.2, 3.6, 4.0, 4.5, 4.4, 4.2, 4.1,
        3.95, 3.7, 3.5, 3.3, 3.15, 3.05, 2.9, 2.75, 2.6, 2.55,
        2.5, 2.45, 2.4, 2.4,
    ]

    xt60: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1995, 2008)]
    xt40: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1990, 2008)]

    def make_panel(
        title: str,
        xvals: list[float],
        yvals: list[float],
        se: list[float],
        xlim: tuple[float, float],
        ylim: tuple[float, float],
        xticks: list[float | tuple[float, str]],
        yticks: list[float | tuple[float, str]],
        ylabel: str,
        legend_loc: Literal["top", "bottom", "none"] = "none",
    ) -> PanelSpec:
        return PanelSpec(
            title=title,
            xlim=xlim,
            ylim=ylim,
            xticks=xticks,
            yticks=yticks,
            ylabel=ylabel,
            legend_loc=legend_loc,
            xlabel="估算结束期",
            bands=[
                BandSeries(
                    x=xvals,
                    y_low=[v - 2 * s for v, s in zip(yvals, se)],
                    y_high=[v + 2 * s for v, s in zip(yvals, se)],
                    label="±2×标准偏差",
                    color_idx=1,
                    show_edges=True,
                    edge_style="solid",
                ),
                BandSeries(
                    x=xvals,
                    y_low=[v - s for v, s in zip(yvals, se)],
                    y_high=[v + s for v, s in zip(yvals, se)],
                    label="±标准偏差",
                    color_idx=0,
                    show_edges=True,
                    edge_style="dashed",
                ),
            ],
            lines=[LineSeries(x=xvals, y=yvals, color_idx=0, width=2.3)],
        )

    spec = FigureSpec(
        fig_id="2-5",
        title="图 2-5 滚动估算结果",
        rows=2,
        cols=2,
        width=920,
        height=640,
        panels=[
            make_panel(
                "（1）不含与开放度的交叉项（60期）",
                xs60,
                g60_no,
                g60_no_se,
                (1995.0, 2007.2),
                (-0.2, 0.5),
                xt60,
                [-0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
                "国内供需缺口",
            ),
            make_panel(
                "（参考）不含与开放度的交叉项（40期）",
                xs40,
                g40_no,
                g40_no_se,
                (1990.0, 2007.2),
                (-0.3, 0.5),
                xt40,
                [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
                "国内供需缺口",
            ),
            make_panel(
                "（2）包含与开放度的交叉项（60期）",
                xs_int,
                g60_int,
                g60_int_se,
                (1995.0, 2007.2),
                (-2.0, 4.0),
                xt60,
                [-2, -1, 0, 1, 2, 3, 4],
                "国内供需缺口",
            ),
            make_panel(
                "　",
                xs_cross,
                cross_60,
                cross_60_se,
                (1995.0, 2007.2),
                (-20.0, 15.0),
                xt60,
                [-20, -15, -10, -5, 0, 5, 10, 15],
                "国内供需缺口×开放度",
                legend_loc="bottom",
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_2_6(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1980, 2007)]
    open_jp = [
        0.29, 0.28, 0.29, 0.27, 0.26, 0.27, 0.20, 0.17, 0.17, 0.18,
        0.19, 0.18, 0.17, 0.16, 0.16, 0.16, 0.18, 0.20, 0.19, 0.18,
        0.20, 0.20, 0.21, 0.22, 0.24, 0.27, 0.30,
    ]
    open_uk = [
        0.56, 0.49, 0.52, 0.51, 0.54, 0.59, 0.53, 0.52, 0.50, 0.50,
        0.51, 0.47, 0.48, 0.51, 0.53, 0.56, 0.59, 0.58, 0.55, 0.54,
        0.56, 0.59, 0.56, 0.53, 0.53, 0.56, 0.61,
    ]
    open_us = [
        0.20, 0.20, 0.19, 0.17, 0.18, 0.18, 0.17, 0.18, 0.19, 0.20,
        0.20, 0.20, 0.20, 0.20, 0.21, 0.23, 0.23, 0.24, 0.23, 0.24,
        0.26, 0.24, 0.22, 0.23, 0.25, 0.26, 0.28,
    ]

    imp_jp = [
        0.16, 0.14, 0.14, 0.13, 0.12, 0.12, 0.09, 0.07, 0.07, 0.08,
        0.09, 0.09, 0.08, 0.07, 0.07, 0.07, 0.09, 0.10, 0.09, 0.08,
        0.09, 0.10, 0.10, 0.10, 0.11, 0.13, 0.145,
    ]
    imp_uk = [
        0.275, 0.23, 0.25, 0.245, 0.265, 0.295, 0.265, 0.265, 0.265, 0.27,
        0.28, 0.25, 0.24, 0.255, 0.265, 0.28, 0.295, 0.285, 0.28, 0.275,
        0.285, 0.305, 0.29, 0.28, 0.28, 0.295, 0.325,
    ]
    imp_us = [
        0.105, 0.105, 0.10, 0.09, 0.095, 0.10, 0.10, 0.105, 0.11, 0.11,
        0.11, 0.105, 0.105, 0.11, 0.115, 0.12, 0.12, 0.125, 0.125, 0.135,
        0.15, 0.14, 0.135, 0.14, 0.15, 0.16, 0.168,
    ]

    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1980, 2007, 2)]
    spec = FigureSpec(
        fig_id="2-6",
        title="图 2-6 开放度和进口份额的变化",
        rows=1,
        cols=2,
        width=900,
        height=440,
        panels=[
            PanelSpec(
                title="开放度",
                xlim=(1980.0, 2006.0),
                ylim=(0.0, 0.7),
                xticks=xt,
                yticks=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                xlabel="年",
                lines=[
                    LineSeries(x=xs, y=open_jp, label="日本", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=open_uk, label="英国", color_idx=1, width=2.3),
                    LineSeries(x=xs, y=open_us, label="美国", color_idx=2, style="dashed", width=2.3),
                ],
            ),
            PanelSpec(
                title="进口份额",
                xlim=(1980.0, 2006.0),
                ylim=(0.0, 0.35),
                xticks=xt,
                yticks=[0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35],
                xlabel="年",
                lines=[
                    LineSeries(x=xs, y=imp_jp, label="日本", color_idx=0, width=2.3),
                    LineSeries(x=xs, y=imp_uk, label="英国", color_idx=1, width=2.3),
                    LineSeries(x=xs, y=imp_us, label="美国", color_idx=2, style="dashed", width=2.3),
                ],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_1(mode: ThemeMode = "mono") -> str:
    pts = [
        (1985.5, 6.2), (1985.81, 8.3), (1985.98, 7.0), (1986.22, 4.5), (1986.46, 4.7),
        (1986.7, 3.9), (1986.95, 4.4), (1987.26, 3.3), (1987.67, 3.5), (1987.91, 4.0),
        (1988.22, 3.5), (1988.51, 4.1), (1988.87, 4.2), (1989.11, 4.4), (1989.48, 5.4),
        (1989.84, 6.4), (1990.32, 7.5), (1990.8, 8.2), (1991.16, 8.25), (1991.52, 7.5),
        (1991.89, 5.7), (1992.25, 4.8), (1992.61, 4.0), (1993.09, 3.3), (1993.45, 3.2),
        (1993.69, 2.5), (1994.3, 2.0), (1994.78, 2.3), (1995.14, 2.2), (1995.26, 1.3),
        (1995.5, 0.9), (1995.69, 0.45), (1997.43, 0.48), (1998.51, 0.45), (1998.87, 0.25),
        (1999.23, 0.02), (2000.44, 0.02), (2000.61, 0.25), (2001.16, 0.25), (2001.33, 0.02),
        (2006.34, 0.02), (2006.58, 0.25), (2007.07, 0.27), (2007.19, 0.5), (2007.9, 0.5),
    ]
    xs = [p[0] for p in pts]
    ys: list[float | None] = [p[1] for p in pts]
    xt: list[float | tuple[float, str]] = [(y + 0.5, f"{y}-7") for y in range(1985, 2008)]
    spec = FigureSpec(
        fig_id="3-1",
        title="图 3-1 日本国内银行间拆借市场利率的变化情况",
        note="资料来源：日本银行",
        width=860,
        height=440,
        panels=[
            PanelSpec(
                xlim=(1985.5, 2007.8),
                ylim=(0.0, 9.0),
                xticks=xt,
                yticks=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                ylabel="（月平均，单位：%）",
                zero_line=False,
                legend_loc="none",
                lines=[LineSeries(x=xs, y=ys, color_idx=0, width=2.3, area_fill=True)],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_2(mode: ThemeMode = "mono") -> str:
    xs = [1995.0 + 0.25 * i for i in range(51)]
    cpi_y2 = [
        0.5, -0.1, -0.3, 0.1, 0.1, -0.2, 0.1, 0.2, 0.3, 0.6,
        0.8, 1.1, 0.9, 0.3, -0.1, -0.5, -0.2, -0.1, -0.1, -0.1,
        -0.2, -0.3, -0.5, -0.5, -0.9, -0.9, -1.1, -0.9, -0.9, -0.9,
        -0.9, -0.8, -0.6, -0.4, -0.2, 0.0, -0.1, -0.3, -0.1, -0.2,
        -0.2, 0.1, -0.2, -0.2, 0.1, 0.0, 0.2, 0.3, -0.1, -0.1,
        0.4,
    ]
    ci_y1 = [
        91.3, 93.8, 91.6, 92.9, 94.5, 95.4, 97.3, 99.0, 101.4, 103.1,
        102.5, 100.3, 98.1, 94.3, 92.1, 90.8, 90.8, 92.1, 93.8, 96.0,
        98.1, 100.3, 101.7, 102.6, 100.8, 96.8, 93.2, 90.2, 90.4, 92.1,
        95.5, 96.0, 97.3, 97.6, 99.8, 102.0, 104.4, 105.5, 106.6, 106.4,
        106.5, 107.2, 108.0, 110.7, 111.6, 112.9, 113.7, 113.2, 113.5, 113.7,
        114.3,
    ]
    xt: list[float | tuple[float, str]] = [
        (y + h / 2, f"{y}-{1 + 6 * h}") for y in range(1995, 2008) for h in (0, 1)
    ]
    spec = FigureSpec(
        fig_id="3-2",
        title="图 3-2 日本消费者物价上涨率及景气动向指数的变化情况",
        note="资料来源：总务省、内阁府",
        width=880,
        height=460,
        panels=[
            PanelSpec(
                xlim=(1994.8, 2007.8),
                ylim=(85.0, 115.0),
                xticks=xt,
                yticks=[85, 90, 95, 100, 105, 110, 115],
                ylabel="（2000年＝100）",
                y2lim=(-1.5, 1.5),
                y2ticks=[-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5],
                y2label="（同比，%）",
                legend_loc="bottom",
                hlines=[(100.0, "", "solid")],
                bars=[
                    BarSeries(
                        x=xs,
                        y=cpi_y2,
                        label="消费者物价指数同比变化（右轴）",
                        color_idx=1,
                        width=0.18,
                        axis="y2",
                        hatch=True,
                    )
                ],
                lines=[
                    LineSeries(
                        x=xs,
                        y=ci_y1,
                        label="景气动向指数（CI，同步指数类）（左轴）",
                        color_idx=0,
                        marker="circle",
                        width=2.2,
                        axis="y1",
                    )
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_3(mode: ThemeMode = "mono") -> str:
    xs = [1995.0 + 0.25 * i for i in range(45)]
    jgb20 = [
        5.0, 4.3, 3.8, 3.8, 3.8, 4.1, 4.0, 3.7, 3.5, 3.6,
        3.0, 2.9, 2.75, 2.7, 2.4, 1.4, 3.0, 2.3, 2.9, 2.7,
        2.4, 2.2, 2.3, 2.6, 2.4, 1.6, 2.1, 2.0, 2.1, 2.1,
        2.0, 1.8, 1.5, 1.1, 1.0, 1.9, 1.9, 2.2, 2.5, 2.2,
        2.1, 2.0, 1.95, 2.1, 2.05,
    ]
    jgb10 = [
        4.8, 3.9, 3.0, 3.2, 3.1, 3.5, 3.4, 3.0, 2.7, 2.8,
        2.5, 2.2, 1.9, 1.8, 1.5, 0.8, 2.1, 1.5, 1.9, 1.8,
        1.75, 1.75, 1.8, 1.85, 1.6, 1.2, 1.3, 1.35, 1.4, 1.4,
        1.3, 1.15, 0.85, 0.65, 0.6, 1.4, 1.3, 1.5, 1.8, 1.5,
        1.4, 1.3, 1.25, 1.5, 1.5,
    ]
    jgb5 = [
        4.2, 3.0, 2.1, 1.9, 2.1, 2.6, 2.6, 2.1, 1.6, 1.8,
        1.6, 1.3, 1.2, 1.1, 1.0, 0.5, 1.4, 0.9, 1.1, 1.0,
        1.1, 1.05, 1.15, 1.15, 0.9, 0.5, 0.4, 0.45, 0.5, 0.55,
        0.45, 0.35, 0.3, 0.25, 0.3, 0.6, 0.6, 0.6, 0.9, 0.65,
        0.55, 0.5, 0.45, 0.7, 1.0,
    ]
    call = [
        2.25, 1.4, 0.9, 0.47, 0.47, 0.47, 0.47, 0.47, 0.48, 0.48,
        0.48, 0.47, 0.46, 0.45, 0.4, 0.3, 0.2, 0.03, 0.02, 0.02,
        0.02, 0.02, 0.05, 0.25, 0.25, 0.02, 0.001, 0.001, 0.001, 0.001,
        0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001,
        0.001, 0.001, 0.001, 0.001, 0.002,
    ]
    xt: list[float | tuple[float, str]] = [(float(y), f"{y}-1") for y in range(1995, 2007)]
    spec = FigureSpec(
        fig_id="3-3",
        title="图 3-3 利率的变化情况",
        note="资料来源：白川（2006）",
        width=880,
        height=460,
        panels=[
            PanelSpec(
                xlim=(1995.0, 2006.1),
                ylim=(0.0, 5.0),
                xticks=xt,
                yticks=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                ylabel="%",
                zero_line=False,
                vspans=[
                    VSpan(x0=1999.1, x1=2000.6, label="零利率", color_idx=0),
                    VSpan(x0=2001.2, x1=2006.1, label="量化宽松", color_idx=1),
                ],
                vlines=[(1999.1, "", "solid"), (2000.6, "", "solid"), (2001.2, "", "solid")],
                lines=[
                    LineSeries(x=xs, y=jgb5, label="5年国债", color_idx=1, style="dashed", width=2.0),
                    LineSeries(x=xs, y=jgb10, label="10年国债", color_idx=0, width=2.4),
                    LineSeries(x=xs, y=jgb20, label="20年国债", color_idx=2, width=1.9),
                    LineSeries(x=xs, y=call, label="银行间拆借市场利率（隔夜）", color_idx=3, width=2.2),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_4(mode: ThemeMode = "mono") -> str:
    xs = [1998.0 + 0.25 * i for i in range(33)]
    sp_top = [
        0.65, 1.08, 1.06, 1.15, 1.28, 1.48, 1.22, 0.98, 0.80, 0.66,
        0.55, 0.56, 0.57, 0.58, 0.62, 0.54, 0.62, 0.98, 1.14, 0.88,
        0.78, 0.76, 0.58, 0.46, 0.58, 0.48, 0.36, 0.32, 0.30, 0.26,
        0.24, 0.26, 0.30,
    ]
    sp_mid = [
        0.55, 0.92, 0.82, 0.85, 0.96, 1.06, 0.88, 0.75, 0.58, 0.46,
        0.40, 0.38, 0.36, 0.40, 0.46, 0.40, 0.38, 0.56, 0.46, 0.38,
        0.36, 0.30, 0.22, 0.18, 0.20, 0.17, 0.15, 0.14, 0.15, 0.14,
        0.15, 0.15, 0.16,
    ]
    sp_bot = [
        0.38, 0.46, 0.46, 0.50, 0.50, 0.54, 0.38, 0.31, 0.28, 0.26,
        0.27, 0.28, 0.26, 0.25, 0.27, 0.23, 0.18, 0.25, 0.24, 0.18,
        0.10, 0.10, 0.10, 0.12, 0.10, 0.09, 0.09, 0.09, 0.09, 0.09,
        0.09, 0.09, 0.09,
    ]
    xt: list[float | tuple[float, str]] = [(float(y), f"{y - 1}-12") for y in range(1998, 2007)]
    spec = FigureSpec(
        fig_id="3-4",
        title="图 3-4 信用利差的变化情况",
        note="资料来源：白川（2006）",
        width=860,
        height=440,
        panels=[
            PanelSpec(
                xlim=(1998.0, 2006.0),
                ylim=(0.0, 1.5),
                xticks=xt,
                yticks=[0.0, 0.5, 1.0, 1.5],
                ylabel="%",
                zero_line=False,
                vspans=[
                    VSpan(x0=1999.2, x1=2000.65, label="零利率", color_idx=0),
                    VSpan(x0=2001.2, x1=2006.0, label="量化宽松", color_idx=1),
                ],
                vlines=[(1999.2, "", "solid"), (2000.65, "", "solid"), (2001.2, "", "solid")],
                lines=[
                    LineSeries(x=xs, y=sp_top, label="AA", color_idx=1, style="dotted", width=2.1),
                    LineSeries(x=xs, y=sp_mid, label="A", color_idx=0, width=2.8),
                    LineSeries(x=xs, y=sp_bot, label="BBB", color_idx=0, width=1.2),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_5(mode: ThemeMode = "mono") -> str:
    spec = FigureSpec(
        fig_id="3-5",
        title="图 3-5 市场实际利率与实际均衡利率的收益率曲线：3 个案例",
        rows=3,
        cols=1,
        width=760,
        height=680,
        panels=[
            PanelSpec(
                title="案例1",
                xlim=(0.0, 10.0),
                ylim=(0.0, 10.0),
                xticks=[(9.0, "（对象期间）")],
                yticks=[(-1.0, "")],
                ylabel="（利率）",
                legend_loc="none",
                zero_line=False,
                lines=[
                    LineSeries(x=[0.4, 9.9], y=[2.9, 7.7], label="市场实际利率", color_idx=1, width=2.5),
                    LineSeries(x=[0.5, 9.9], y=[1.3, 6.4], label="实际均衡利率", color_idx=0, width=2.5),
                ],
                annotations=[
                    Annotation(x=6.8, y=6.8, text="市场实际利率", dy=-14, arrow=False, color_idx=1),
                    Annotation(x=7.2, y=4.6, text="实际均衡利率", dy=16, arrow=False, color_idx=0),
                ],
            ),
            PanelSpec(
                title="案例2",
                xlim=(0.0, 10.0),
                ylim=(0.0, 10.0),
                xticks=[(9.0, "（对象期间）")],
                yticks=[(-1.0, "")],
                ylabel="（利率）",
                legend_loc="none",
                zero_line=False,
                lines=[
                    LineSeries(x=[0.4, 7.7], y=[3.9, 6.2], label="实际均衡利率", color_idx=0, width=2.5),
                    LineSeries(x=[0.4, 7.9], y=[2.4, 4.6], label="市场实际利率（受零利率下限约束）", color_idx=1, width=2.5),
                    LineSeries(x=[0.4, 7.9], y=[0.95, 3.1], label="市场实际利率（无零利率下限）", color_idx=2, style="dashed", width=2.1),
                ],
                annotations=[
                    Annotation(x=5.6, y=6.6, text="实际均衡利率", dy=-14, arrow=False, color_idx=0),
                    Annotation(x=5.6, y=2.4, text="市场实际利率", dy=16, arrow=False, color_idx=2),
                    Annotation(x=8.2, y=4.5, text="", dx=0, dy=34, arrow=True, color_idx=1),
                    Annotation(x=8.5, y=6.2, text="市场实际", dy=0, arrow=False, color_idx=1, fontsize=10.5, align="start"),
                    Annotation(x=8.5, y=5.0, text="利率因零", dy=0, arrow=False, color_idx=1, fontsize=10.5, align="start"),
                    Annotation(x=8.5, y=3.8, text="利率下限", dy=0, arrow=False, color_idx=1, fontsize=10.5, align="start"),
                    Annotation(x=8.5, y=2.6, text="的存在而", dy=0, arrow=False, color_idx=1, fontsize=10.5, align="start"),
                    Annotation(x=8.5, y=1.4, text="上升", dy=0, arrow=False, color_idx=1, fontsize=10.5, align="start"),
                ],
            ),
            PanelSpec(
                title="案例3",
                xlim=(0.0, 10.0),
                ylim=(0.0, 10.0),
                xticks=[(9.0, "（对象期间）")],
                yticks=[(-1.0, "")],
                ylabel="（利率）",
                legend_loc="none",
                zero_line=False,
                lines=[
                    LineSeries(x=[1.0, 3.55, 9.7], y=[1.6, 5.7, 8.6], label="实际均衡利率", color_idx=0, width=2.5),
                    LineSeries(x=[0.9, 9.85], y=[3.05, 7.75], label="市场实际利率", color_idx=1, width=2.5),
                ],
                annotations=[
                    Annotation(x=6.0, y=7.4, text="实际均衡利率", dy=-14, arrow=False, color_idx=0),
                    Annotation(x=5.8, y=5.6, text="市场实际利率", dy=18, arrow=False, color_idx=1),
                ],
            ),
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_6(mode: ThemeMode = "mono") -> str:
    pal = get_palette(mode)
    W, H = 860, 480
    c_ret = pal.panel_bg if mode == "mono" else pal.fills[0]
    c_rf = pal.panel_bg
    c_exp = pal.panel_bg if mode == "mono" else pal.fills[2]
    c_prem = "#475569" if mode == "mono" else pal.fills[1]
    stroke_col = pal.fg if mode == "mono" else pal.axis

    base_y = 356.0
    col_w = 72.0

    c1_x = 268.0
    c1_ret_h = 230.0
    c1_rf_h = 76.0
    c1_exp_h = 56.0
    c1_prem_h = 58.0

    c2_x = 468.0
    c2_ret_h = 230.0
    c2_rf_h = 76.0
    c2_exp_h = 56.0
    c2_prem_h = 190.0

    title_3_6 = escape("图 3-6 风险溢价的波动")
    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        "<defs>",
        f'<pattern id="hatch_{mode}" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="6" stroke="{pal.fg}" stroke-width="1.5" stroke-opacity="0.6"/></pattern>',
        "</defs>",
        f'<rect width="{W}" height="{H}" fill="{pal.bg}"/>',
        f'<text x="{W / 2:.1f}" y="28.0" text-anchor="middle" font-family="{FONT_STACK}" font-size="16.5" font-weight="700" fill="{pal.fg}">{title_3_6}</text>',
        f'<rect x="26" y="210" width="190" height="48" fill="{pal.panel_bg}" stroke="{pal.axis}" stroke-width="1.3"/>',
        f'<text x="121" y="239" text-anchor="middle" font-family="{FONT_STACK}" font-size="14.5" font-weight="600" fill="{pal.fg}">投资回报率</text>',
        f'<path d="M 254 {base_y - c1_ret_h:.1f} Q 238 {base_y - c1_ret_h:.1f} 238 {base_y - c1_ret_h / 2:.1f} Q 238 {base_y:.1f} 254 {base_y:.1f}" fill="none" stroke="{pal.fg}" stroke-width="1.6"/>',
        f'<rect x="{c1_x:.1f}" y="{base_y - c1_ret_h:.1f}" width="{col_w:.1f}" height="{c1_ret_h:.1f}" fill="{c_ret}" fill-opacity="{0.15 if mode == "mono" else 0.78}" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="{c1_x + col_w:.1f}" y="{base_y - c1_rf_h:.1f}" width="{col_w:.1f}" height="{c1_rf_h:.1f}" fill="{c_rf}" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="{c1_x + col_w:.1f}" y="{base_y - c1_rf_h - c1_exp_h:.1f}" width="{col_w:.1f}" height="{c1_exp_h:.1f}" fill="{c_exp}" fill-opacity="{1.0 if mode == "mono" else 0.72}" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="{c1_x + col_w:.1f}" y="{base_y - c1_rf_h - c1_exp_h - c1_prem_h:.1f}" width="{col_w:.1f}" height="{c1_prem_h:.1f}" fill="{c_prem}" fill-opacity="0.85" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="{c2_x:.1f}" y="{base_y - c2_ret_h:.1f}" width="{col_w:.1f}" height="{c2_ret_h:.1f}" fill="{c_ret}" fill-opacity="{0.15 if mode == "mono" else 0.78}" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="{c2_x + col_w:.1f}" y="{base_y - c2_rf_h:.1f}" width="{col_w:.1f}" height="{c2_rf_h:.1f}" fill="{c_rf}" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="{c2_x + col_w:.1f}" y="{base_y - c2_rf_h - c2_exp_h:.1f}" width="{col_w:.1f}" height="{c2_exp_h:.1f}" fill="{c_exp}" fill-opacity="{1.0 if mode == "mono" else 0.72}" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="{c2_x + col_w:.1f}" y="{base_y - c2_rf_h - c2_exp_h - c2_prem_h:.1f}" width="{col_w:.1f}" height="{c2_prem_h:.1f}" fill="{c_prem}" fill-opacity="0.85" stroke="{stroke_col}" stroke-width="1.5"/>',
        f'<rect x="642" y="96" width="192" height="78" fill="{pal.panel_bg}" stroke="{pal.axis}" stroke-width="1.3"/>',
        f'<text x="738" y="128" text-anchor="middle" font-family="{FONT_STACK}" font-size="14" font-weight="600" fill="{pal.fg}">信用风险的波动</text>',
        f'<text x="738" y="152" text-anchor="middle" font-family="{FONT_STACK}" font-size="13.5" fill="{pal.muted}">（风险溢价）</text>',
        f'<rect x="642" y="232" width="192" height="44" fill="{pal.panel_bg}" stroke="{pal.axis}" stroke-width="1.3"/>',
        f'<text x="738" y="259" text-anchor="middle" font-family="{FONT_STACK}" font-size="14" font-weight="600" fill="{pal.fg}">信用风险的期望值</text>',
        f'<rect x="642" y="294" width="192" height="44" fill="{pal.panel_bg}" stroke="{pal.axis}" stroke-width="1.3"/>',
        f'<text x="738" y="321" text-anchor="middle" font-family="{FONT_STACK}" font-size="14" font-weight="600" fill="{pal.fg}">无风险利率</text>',
        f'<rect x="44" y="382" width="372" height="68" fill="{pal.panel_bg}" stroke="{pal.axis}" stroke-width="1.3"/>',
        f'<text x="230" y="422" text-anchor="middle" font-family="{FONT_STACK}" font-size="14.5" font-weight="600" fill="{pal.fg}">案例1　风险溢价较低的案例</text>',
        f'<rect x="462" y="382" width="372" height="68" fill="{pal.panel_bg}" stroke="{pal.axis}" stroke-width="1.3"/>',
        f'<text x="648" y="422" text-anchor="middle" font-family="{FONT_STACK}" font-size="14.5" font-weight="600" fill="{pal.fg}">案例2　风险溢价较高的案例</text>',
        "</svg>",
    ]
    return "\n".join(out)


def gen_fig_3_7(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1985, 2007)]
    exp_1y = [
        4.7, 3.1, 2.5, 3.6, 4.2, 4.3, 3.5, 3.0, 2.4, 0.8,
        1.85, 1.7, 1.5, 0.9, -0.2, 0.95, 1.35, -0.35, 0.3, 1.5,
        1.5, 2.0,
    ]
    exp_3y = [
        4.4, 3.5, 2.9, 3.1, 3.5, 3.68, 3.56, 3.5, 3.1, 2.2,
        2.4, 2.2, 1.95, 1.75, 1.25, 1.55, 1.75, 1.25, 1.1, 1.68,
        1.72, 2.02,
    ]
    exp_5y = [
        4.5, 3.4, 2.75, 3.3, 3.7, 3.88, 3.5, 3.42, 2.9, 1.7,
        2.2, 2.0, 1.82, 1.42, 0.9, 1.35, 1.55, 0.7, 0.8, 1.58,
        1.6, 2.0,
    ]
    real_r: list[float | None] = [
        5.1, 4.1, 3.1, 3.4, 4.1, 5.1, 4.2, 2.0, 1.7, 1.55,
        0.9, 0.25, -0.15, 0.5, 0.12, 0.68, 0.9, 0.88, 0.22, 0.25,
        -0.1, None,
    ]
    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1985, 2007, 2)] + [(2006.0, "2006")]
    spec = FigureSpec(
        fig_id="3-7",
        title="图 3-7 日本的中长期预期增长率与实际利率",
        note=(
            "注：1. 企业的预期增长率（见《企业行为问卷调查》〈内阁府经济社会综合研究所〉）利用线性插值进行了补全。"
            "2. 短期实际利率＝无担保隔夜拆借利率－CPI（剔除生鲜食品）的同比变化率。资料来源：白川，2006"
        ),
        width=860,
        height=460,
        panels=[
            PanelSpec(
                xlim=(1984.6, 2006.4),
                ylim=(-1.0, 6.0),
                xticks=xt,
                yticks=[-1, 0, 1, 2, 3, 4, 5, 6],
                ylabel="年平均，%",
                xlabel="年",
                lines=[
                    LineSeries(x=xs, y=exp_1y, label="企业的预期实际GDP增长率：1年后", color_idx=0, width=2.4),
                    LineSeries(x=xs, y=exp_3y, label="3年后", color_idx=2, width=2.2),
                    LineSeries(x=xs, y=exp_5y, label="5年后", color_idx=4, width=2.1),
                    LineSeries(x=xs, y=real_r, label="短期实际利率", color_idx=1, style="dashed", width=2.4),
                ],
                annotations=[
                    Annotation(x=1991.0, y=4.2, text="短期实际利率", dx=38, dy=-34, arrow=True, color_idx=1),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_8(mode: ThemeMode = "mono") -> str:
    q_labels = [
        "99II", "99III", "99IV", "00I", "00II",
        "01II", "01III", "01IV", "02I", "02II", "02III", "02IV",
        "03I", "03II", "03III", "03IV",
    ]
    xs = [float(i) for i in range(len(q_labels))]
    xs_left = [x - 0.17 for x in xs]
    xs_right = [x + 0.17 for x in xs]
    no_eff = [
        0.35, 0.32, 0.20, 0.27, 0.24,
        0.08, 0.08, 0.07, 0.055, 0.045, 0.055, 0.085,
        0.125, 0.36, 0.59, 0.65,
    ]
    with_eff = [
        0.25, 0.26, 0.15, 0.22, 0.18,
        0.05, 0.055, 0.055, 0.045, 0.03, 0.03, 0.035,
        0.05, 0.09, 0.205, 0.185,
    ]
    xt: list[float | tuple[float, str]] = [(float(i), lab) for i, lab in enumerate(q_labels)]
    spec = FigureSpec(
        fig_id="3-8",
        title="图 3-8 长期政策效应的推算",
        note="资料来源：Oda、Nobuyuki 和 Kazuo Ueda，2005",
        width=880,
        height=460,
        panels=[
            PanelSpec(
                title="① 3年期利率",
                xlim=(-0.8, 15.8),
                ylim=(0.0, 0.7),
                xticks=xt,
                yticks=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                ylabel="%",
                xlabel="年 / 季度",
                zero_line=False,
                vlines=[(4.5, "", "dashed")],
                bars=[
                    BarSeries(x=xs_left, y=no_eff, label="无长期政策效应", color_idx=1, width=0.32, hatch=True),
                    BarSeries(x=xs_right, y=with_eff, label="有长期政策效应", color_idx=0, width=0.32),
                ],
                annotations=[
                    Annotation(x=2.0, y=0.42, text="实行零利率政策时", dy=0, arrow=False, color_idx=0, fontsize=12.5),
                    Annotation(x=9.5, y=0.30, text="实行量化宽松政策时", dy=0, arrow=False, color_idx=1, fontsize=12.5),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_9(mode: ThemeMode = "mono") -> str:
    pts = [
        (-0.04, 11.8, "造纸及纸浆"),
        (0.09, 11.1, "木材及木制品"),
        (0.00, -2.3, "食品"),
        (0.37, -1.4, "金属制品"),
        (0.72, 5.8, "石油和煤炭制品"),
        (1.40, 15.9, "纺织"),
        (1.75, 17.3, "陶瓷及土石制品"),
        (1.70, 13.3, "其他"),
        (1.70, 9.0, "化学"),
        (2.64, 11.5, "精密机械"),
        (2.80, 16.8, "机电"),
        (3.00, 16.2, "有色金属"),
        (3.85, 23.3, "钢铁"),
        (4.20, 10.8, "运输机械"),
        (4.85, 23.9, "通用机械"),
    ]
    sx = [p[0] for p in pts]
    sy = [p[1] for p in pts]
    label_centers = {
        "造纸及纸浆": (-0.42, 14.8),
        "木材及木制品": (0.65, 11.5),
        "食品": (-0.34, -2.4),
        "金属制品": (0.81, -1.7),
        "石油和煤炭制品": (0.88, 3.4),
        "纺织": (1.13, 17.2),
        "陶瓷及土石制品": (1.81, 20.6),
        "其他": (1.97, 14.6),
        "化学": (1.72, 6.6),
        "精密机械": (2.63, 8.9),
        "机电": (2.71, 19.6),
        "有色金属": (3.37, 13.9),
        "钢铁": (3.58, 25.4),
        "运输机械": (4.28, 8.3),
        "通用机械": (4.47, 26.2),
    }
    labels = [
        Annotation(x=lx, y=ly - 1.0, text=name, dy=0.0, arrow=False, fontsize=12.0)
        for name, (lx, ly) in label_centers.items()
    ]
    spec = FigureSpec(
        fig_id="3-9",
        title="图 3-9 制造业大型企业的设备投资与出口的关系（按行业）",
        note="资料来源：日本银行调查统计局（2007）",
        width=860,
        height=460,
        panels=[
            PanelSpec(
                xlim=(-1.0, 5.2),
                ylim=(-5.0, 30.0),
                xticks=[-1, 0, 1, 2, 3, 4, 5],
                yticks=[-5, 0, 5, 10, 15, 20, 25, 30],
                xlabel="2003—2006年度销售额增长率的平均出口贡献度（%）",
                ylabel="（2003—2006年度设备投资平均增长率，%）",
                scatters=[(sx, sy, [], 0, False)],
                annotations=labels,
                legend_loc="none",
                lines=[
                    LineSeries(
                        x=[-0.5, 4.85],
                        y=[3.9, 21.6],
                        color_idx=1,
                        style="dotted",
                        width=2.0,
                    )
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_10(mode: ThemeMode = "mono") -> str:
    xs = [1990.0 + 17.95 / 71 * i for i in range(72)]
    nom = [
        102, 96, 99, 110, 109, 109, 110, 114, 117, 112, 114, 119,
        121, 130, 139, 145, 139, 146, 152, 152, 151, 173, 168, 147,
        142, 139, 139, 134, 126, 136, 134, 143, 132, 127, 145, 153,
        146, 149, 165, 171, 165, 169, 171, 165, 153, 156, 155, 143,
        145, 154, 151, 153, 152, 151, 162, 162, 158, 160, 163, 160,
        156, 151, 145, 146, 145, 141, 138, 140, 133, 140, 142, 141,
    ]
    real = [
        102, 96, 98, 109, 106, 106, 107, 109, 111, 106, 108, 112,
        113, 120, 128, 129, 124, 130, 130, 129, 128, 144, 136, 121,
        118, 113, 110, 106, 100, 108, 106, 110, 104, 99, 112, 119,
        113, 113, 126, 129, 123, 124, 124, 113, 110, 110, 111, 103,
        104, 109, 105, 105, 104, 103, 110, 108, 104, 105, 106, 103,
        100, 96, 92, 91, 91, 89, 88, 86, 82, 86, 87, 86,
    ]
    xt: list[float | tuple[float, str]] = [(float(y), f"{y}-1") for y in range(1990, 2008)]
    spec = FigureSpec(
        fig_id="3-10",
        title="图 3-10 日元的名义有效汇率与实际有效汇率的变化情况",
        note="注：1990年1月＝100。资料来源：日本银行",
        width=860,
        height=440,
        panels=[
            PanelSpec(
                xlim=(1990.0, 2008.0),
                ylim=(50.0, 190.0),
                xticks=xt,
                yticks=[50, 70, 90, 110, 130, 150, 170, 190],
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs, y=nom, label="名义有效汇率", color_idx=0, width=2.4),
                    LineSeries(x=xs, y=real, label="实际有效汇率", color_idx=1, width=2.3),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_11(mode: ThemeMode = "mono") -> str:
    years = [2000, 2001, 2002, 2003, 2004, 2005, 2006]
    xs_l = [float(y) - 0.16 for y in years]
    xs_r = [float(y) + 0.16 for y in years]
    net_chg = [48.2, 45.8, -4.6, -2.8, 13.0, -5.2, 34.5]
    fx_eff = [13.5, 20.0, -10.8, -10.8, -2.2, 24.3, 15.5]
    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in years]
    spec = FigureSpec(
        fig_id="3-11",
        title="图 3-11 日本对外净资产的增减情况",
        note="资料来源：财务省“日本对外资产负债余额”",
        width=840,
        height=440,
        panels=[
            PanelSpec(
                xlim=(1999.3, 2006.7),
                ylim=(-20.0, 60.0),
                xticks=xt,
                yticks=[-20, -10, 0, 10, 20, 30, 40, 50, 60],
                ylabel="万亿日元",
                xlabel="年",
                legend_loc="bottom",
                bars=[
                    BarSeries(x=xs_l, y=net_chg, label="对外净资产增减", color_idx=1, width=0.28, hatch=True),
                    BarSeries(x=xs_r, y=fx_eff, label="汇率的影响因素", color_idx=0, width=0.28),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_12(mode: ThemeMode = "mono") -> str:
    vals = [
        500, 920, 1060, 1160, 1250, 950, 960,
        800, 840, 880, 920, 990, 1000, 1010, 1020,
        1120, 1200, 1200, 320, 330, 330, 340, 350,
        350, 360, 360, 370, 3850, 3700, 3460, 3380,
        3220, 3000, 2760, 2630, 2680, 2630, 2650, 2570,
        600, 600, 600, 600, 600, 600, 640, 800,
        870, 780, 1130, 1040, 1150, 1550, 1120, 1120,
        1050, 640, 580, 540, 500, 380, 500, 380,
        510, 510, 510, 560, 560, 600, 520, 570,
        600, 630, 690, 710, 800, 810, 830, 1000,
        900, 920, 390, 390, 200, 200, 200, 200,
    ][:83] + [200] * 8 + [180] * 10 + [150] * 8 + [130] * 3
    xs_full = [1995.605 + 0.085 * i for i in range(len(vals))]
    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1995, 2008)]
    spec = FigureSpec(
        fig_id="3-12",
        title="图 3-12 日本银行特别融资余额的变化情况",
        note="资料来源：日本银行官网",
        width=880,
        height=440,
        panels=[
            PanelSpec(
                xlim=(1995.0, 2007.2),
                ylim=(0.0, 4000.0),
                xticks=xt,
                yticks=[0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000],
                ylabel="（单位：10亿日元）",
                xlabel="年",
                zero_line=False,
                legend_loc="none",
                bars=[BarSeries(x=xs_full, y=vals, color_idx=0, width=0.085)],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_13(mode: ThemeMode = "mono") -> str:
    pts = [
        (-29.6, -6.35), (-22.8, -4.55), (-16.4, -6.35), (-13.7, -5.5), (-11.75, -8.0),
        (-7.3, -0.8), (-6.9, -4.4), (-6.9, -6.35), (-3.6, -0.8), (-2.1, -0.55),
        (-1.07, -0.15), (-1.5, -2.7), (-3.0, -4.3), (-1.4, -5.1), (-4.0, -6.6),
        (-1.5, -6.9), (-1.4, -8.5), (-25.2, -13.7), (-19.3, -22.2), (-14.8, -22.7),
        (-12.2, -21.1), (-10.0, -21.6), (-4.15, -21.2), (-2.85, -19.2),
        (2.14, -1.29), (4.5, -1.63), (5.6, -1.46), (8.55, -2.3), (10.2, -2.15),
        (10.2, -3.2), (9.26, -4.55), (6.17, -3.26), (7.83, -3.52), (4.04, -3.7),
        (4.04, -4.55), (2.97, -5.5), (4.63, -5.58), (6.53, -5.32), (6.05, -6.87),
        (8.19, -6.44), (2.49, -8.58), (4.15, -7.98), (4.63, -9.44), (7.6, -8.84),
        (6.17, -10.56), (9.85, -9.61), (5.04, -12.6), (3.98, -15.1), (5.4, -16.1),
        (13.8, -0.17), (16.1, -1.03), (18.9, -0.43), (21.25, -1.03), (21.8, -1.63),
        (14.4, -2.23), (17.2, -2.32), (22.2, -3.7), (26.5, -2.66), (13.2, -4.46),
        (14.8, -4.55), (14.8, -7.98), (25.0, -5.84), (25.0, -6.78),
        (40.5, -6.27), (46.1, -5.06), (52.6, -3.43), (72.5, -3.43), (37.1, -11.0), (49.2, -12.7),
        (16.9, -18.5), (18.0, -17.2), (19.7, -17.9), (22.8, -20.0), (31.0, -23.0),
        (18.4, -29.4), (45.8, -31.0), (42.0, -48.0),
    ]
    label_centers = [
        ("ca", -29.85, -8.1), ("us", -23.6, -6.5), ("de", -17.1, -8.5), ("uk20", -14.7, -3.35),
        ("fr81", -12.0, -1.1), ("ca20", -7.3, -2.7), ("be", -6.5, -8.4), ("fr", -12.05, -10.55),
        ("sp", -25.8, -15.9), ("au’90", -25.3, -23.6), ("nz", -15.0, -24.2), ("au", -11.9, -19.3),
    ]
    labels = [
        Annotation(x=lx, y=ly - 1.0, text=name, dy=0.0, arrow=False, fontsize=12.0)
        for name, lx, ly in label_centers
    ]
    labels.append(Annotation(x=-10.0, y=-21.6, text="nz’20", dx=18.0, dy=26.0, arrow=True, fontsize=12.0))
    spec = FigureSpec(
        fig_id="3-13",
        title="图 3-13 通货紧缩案例与经济活动",
        note="资料来源：Bordo 和 Filardo，2005",
        width=840,
        height=780,
        panels=[
            PanelSpec(
                xlim=(-40.0, 80.0),
                ylim=(-60.0, 0.0),
                xticks=[-40, -20, 0, 20, 40, 60, 80],
                yticks=[-60, -50, -40, -30, -20, -10, 0],
                xlabel="产出的变化",
                ylabel="物价的峰谷变化",
                zero_line=False,
                legend_loc="none",
                vlines=[(0.0, "", "solid")],
                lines=[
                    LineSeries(
                        x=[p[0] for p in pts],
                        y=[p[1] for p in pts],
                        color_idx=0,
                        style="none",
                        marker="diamond",
                        hollow=False,
                    )
                ],
                annotations=labels,
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_14(mode: ThemeMode = "mono") -> str:
    us_pts = [
        (0.0, 1.53), (0.28, 0.92), (0.41, 1.58), (0.51, 1.58), (0.57, 1.48), (0.64, 1.25),
        (0.79, 1.25), (0.81, 1.58), (0.89, 1.58), (0.92, 1.38), (0.98, 1.38), (1.0, 1.58),
        (1.07, 1.58), (1.24, 0.92), (1.41, 1.58), (1.71, 1.45), (1.85, 2.2), (1.97, 1.6),
        (2.17, 1.3), (2.34, 2.68), (2.73, 2.0), (3.0, 1.32), (3.16, 1.45), (3.25, 2.08),
        (3.47, 1.35), (3.6, 1.5), (3.69, 1.2), (3.98, 1.03), (4.1, 1.17), (4.27, 0.83),
        (4.6, 0.65), (4.64, 0.5), (4.84, 0.58), (5.08, 0.64), (5.25, 0.6), (5.51, 0.69),
        (5.69, 0.55), (5.93, 0.67), (6.25, 0.67), (6.46, 0.55), (6.84, 0.69), (7.0, 0.48),
        (7.21, 0.33), (7.55, 0.53), (7.71, 0.53), (7.8, 0.86), (8.06, 0.99), (8.28, 0.88),
        (8.49, 0.92), (8.65, 0.85), (8.67, 0.7), (8.78, 0.67), (8.83, 0.7), (9.45, 0.7),
        (9.52, 0.67), (9.66, 0.67), (9.86, 0.82), (9.96, 0.82),
    ]
    xs_all_us = [p[0] for p in us_pts]
    ys_all_us: list[float | None] = [p[1] for p in us_pts]

    jp_pts = [
        (4.36, 0.0), (4.49, 0.1), (4.6, 0.1), (4.67, 0.06), (4.87, 0.18), (5.06, 0.05),
        (5.35, 0.05), (5.59, 0.2), (5.7, 0.13), (5.8, 0.15), (5.88, 0.37), (5.94, 0.2),
        (6.15, 0.05), (6.68, 0.05), (6.86, 0.1), (6.97, 0.08), (7.07, 0.12), (7.23, 0.05),
        (9.13, 0.05), (9.24, 0.0),
    ]
    xs_jp = [p[0] for p in jp_pts]
    jp_sp: list[float | None] = [p[1] for p in jp_pts]
    xt: list[float | tuple[float, str]] = [
        (float(i), f"{30 + i}/{1995 + i}") for i in range(10)
    ]
    spec = FigureSpec(
        fig_id="3-14",
        title="图 3-14 信用利差——近几年的日本与 20 世纪 30 年代美国的比较",
        note="资料来源：Baba、Nishioka、Oda、Shirakawa、Ueda、Ugai，2005",
        width=860,
        height=440,
        panels=[
            PanelSpec(
                xlim=(0.0, 10.0),
                ylim=(0.0, 3.0),
                xticks=xt,
                yticks=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
                ylabel="%",
                xlabel="（美国）/（日本）",
                zero_line=False,
                legend_loc="bottom",
                lines=[
                    LineSeries(x=xs_all_us, y=ys_all_us, label="美国信用利差", color_idx=1, width=2.4),
                    LineSeries(x=xs_jp, y=jp_sp, label="日本信用利差", color_idx=0, width=2.5),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def gen_fig_3_15(mode: ThemeMode = "mono") -> str:
    xs = [float(y) for y in range(1985, 2007)]
    world_all = [
        13.0, 13.2, 15.1, 16.4, 17.6, 18.8, 17.6, 17.0, 18.8, 17.8,
        18.2, 20.6, 23.9, 28.1, 32.8, 40.0, 42.5, 40.8, 40.8, 43.6,
        44.4, 49.6,
    ]
    xs_ex_us = [float(y) for y in range(1985, 2003)] + [2002.75] + [float(y) for y in range(2003, 2007)]
    world_ex_us = [
        11.2, 11.0, 9.2, 10.8, 12.5, 12.6, 10.4, 9.9, 12.4, 11.6,
        16.3, 20.6, 24.8, 27.7, 29.3, 29.4, 29.0, 27.2, 20.0, 26.2,
        29.8, 30.2, 29.0,
    ]
    xt: list[float | tuple[float, str]] = [(float(y), str(y)) for y in range(1986, 2007, 2)]
    spec = FigureSpec(
        fig_id="3-15",
        title="图 3-15 跨境储蓄与全球储蓄之比的变化情况",
        note="资料来源：Higgins 和 Klitgaard，2007",
        width=840,
        height=440,
        panels=[
            PanelSpec(
                xlim=(1985.0, 2006.2),
                ylim=(0.0, 50.0),
                xticks=xt,
                yticks=[0, 10, 20, 30, 40, 50],
                ylabel="5年移动平均值（百分比）",
                xlabel="年",
                zero_line=False,
                lines=[
                    LineSeries(x=xs, y=world_all, label="全球（包括美国）", color_idx=0, width=2.5),
                    LineSeries(x=xs_ex_us, y=world_ex_us, label="全球（不包括美国）", color_idx=1, width=2.3),
                ],
                legend_loc="none",
                annotations=[
                    Annotation(x=1997.5, y=44.0, text="全球（不包括美国）", dy=0.0, arrow=False, color_idx=0),
                ],
            )
        ],
    )
    return render_figure_svg(spec, mode)


def get_generators() -> dict[str, Callable[[ThemeMode], str]]:
    return {
        "1-1": gen_fig_1_1,
        "1-2": gen_fig_1_2,
        "2-1": gen_fig_2_1,
        "2-2": gen_fig_2_2,
        "2-3": gen_fig_2_3,
        "2-4": gen_fig_2_4,
        "2-5": gen_fig_2_5,
        "2-6": gen_fig_2_6,
        "3-1": gen_fig_3_1,
        "3-2": gen_fig_3_2,
        "3-3": gen_fig_3_3,
        "3-4": gen_fig_3_4,
        "3-5": gen_fig_3_5,
        "3-6": gen_fig_3_6,
        "3-7": gen_fig_3_7,
        "3-8": gen_fig_3_8,
        "3-9": gen_fig_3_9,
        "3-10": gen_fig_3_10,
        "3-11": gen_fig_3_11,
        "3-12": gen_fig_3_12,
        "3-13": gen_fig_3_13,
        "3-14": gen_fig_3_14,
        "3-15": gen_fig_3_15,
    }
