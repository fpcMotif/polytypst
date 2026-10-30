import json
import re

import pytest

from scripts.book2_figures.engine import (
    PT_PER_PX,
    SCAN_LINE_PT,
    SCAN_PAGE_ASPECT,
    FigureSpec,
    LineSeries,
    PanelSpec,
    chart_svg,
    render_figure_svg,
    scan_canvas,
)

YEARS = [float(y) for y in range(1980, 2007)]


def year_panel(xlabel: str = "年", **kw) -> PanelSpec:
    return PanelSpec(
        xlim=(1979.5, 2006.5),
        ylim=(60.0, 120.0),
        xticks=[float(y) for y in range(1980, 2007, 2)],
        yticks=[float(v) for v in range(60, 121, 10)],
        xlabel=xlabel,
        lines=[
            LineSeries(x=YEARS, y=[100.0] * len(YEARS), label="劳动时间指数1（A）", color_idx=0),
            LineSeries(x=YEARS, y=[90.0] * len(YEARS), label="就业指数（B）", color_idx=1),
            LineSeries(x=YEARS, y=[95.0] * len(YEARS), label="劳动时间×就业人数（A×B）", color_idx=2),
        ],
        **kw,
    )


def svg(panel: PanelSpec, mode: str) -> str:
    return render_figure_svg(FigureSpec(fig_id="t", title="", panels=[panel], width=860, height=500), mode)


def grid_lines(text: str) -> list[str]:
    return re.findall(r'<line [^>]*stroke="#(?:e2e8f0|000000)" stroke-width="0\.[79]"[^>]*/>', text)


def text_at(text: str, label: str) -> str:
    return next(m[0] for m in re.finditer(r"<text [^>]*>([^<]*)</text>", text) if m[1] == label)


def test_scan_style_draws_a_solid_black_grid_where_mono_draws_a_dashed_light_one():
    mono, scan = svg(year_panel(), "mono"), svg(year_panel(), "scan")
    assert all('stroke-dasharray' in g and "#e2e8f0" in g for g in grid_lines(mono))
    assert grid_lines(scan)
    assert all('stroke-dasharray' not in g and "#000000" in g for g in grid_lines(scan))


def test_scan_style_keeps_every_year_label_that_mono_thins():
    labels = [str(y) for y in range(1980, 2007, 2)]
    mono, scan = svg(year_panel(), "mono"), svg(year_panel(), "scan")
    assert not all(f">{y}</text>" in mono for y in labels)
    assert all(f">{y}</text>" in scan for y in labels)


def test_scan_style_sets_a_short_unit_after_the_last_year_and_a_long_one_under_the_axis():
    short = svg(year_panel(), "scan")
    y_unit = float(re.search(r'y="([\d.]+)"', text_at(short, "年"))[1])
    y_year = float(re.search(r'y="([\d.]+)"', text_at(short, "2006"))[1])
    assert y_unit == y_year
    long = svg(year_panel("年（×年第一季度）"), "scan")
    unit = text_at(long, "年（×年第一季度）")
    assert float(re.search(r'y="([\d.]+)"', unit)[1]) > y_year
    assert 'text-anchor="end"' in unit


def test_scan_style_sets_a_top_legend_in_one_row_under_the_axis():
    scan = svg(year_panel(legend_loc="top"), "scan")
    rows = {re.search(r'y="([\d.]+)"', text_at(scan, label))[1] for label in ("劳动时间指数1（A）", "就业指数（B）", "劳动时间×就业人数（A×B）")}
    assert len(rows) == 1
    assert float(rows.pop()) > float(re.search(r'y="([\d.]+)"', text_at(scan, "2006"))[1])


def test_scan_style_draws_no_grid_behind_a_scatter():
    points = PanelSpec(
        xlim=(-30.0, 40.0),
        ylim=(-1.2, 0.4),
        xticks=[-30.0, 0.0, 40.0],
        yticks=[-1.2, -0.4, 0.4],
        lines=[LineSeries(x=[1.0, 2.0], y=[-0.1, -0.3], marker="diamond", style="none", fixed_style=True)],
    )
    assert grid_lines(svg(points, "mono"))
    assert not grid_lines(svg(points, "scan"))


def test_chart_style_b_is_the_scan_style_set_in_the_body_fonts_and_style_a_is_mono():
    def generator(mode: str) -> str:
        return svg(year_panel(), mode)

    b = chart_svg(generator, "b")
    fonts = set(re.findall(r'font-family="([^"]+)"', b))
    assert fonts == {"'Source Serif 4', 'Songti SC', serif"}
    assert grid_lines(b) == grid_lines(svg(year_panel(), "scan"))
    assert chart_svg(generator, "a") == svg(year_panel(), "mono")


def test_a_chart_drawn_on_its_scan_canvas_prints_at_the_scan_size_and_type_scale(tmp_path):
    manifest = [{"figure_id": "3-2", "box": [0.11, 0.1, 0.5, 0.25]}, {"figure_id": "3-3", "box": [0.11, 0.1, 0.89, 0.4]}]
    (tmp_path / "figures_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with scan_canvas(tmp_path, "3-2"):
        half = svg(year_panel(), "mono")
    with scan_canvas(tmp_path, "3-3"):
        full = svg(year_panel(), "mono")
    half_width = float(re.search(r'viewBox="0 0 (\S+) ', half)[1])
    width, height = (float(v) for v in re.search(r'viewBox="0 0 (\S+) (\S+)"', full).groups())
    assert half_width * PT_PER_PX == pytest.approx(SCAN_LINE_PT / 2, abs=1)
    assert width * PT_PER_PX == pytest.approx(SCAN_LINE_PT, abs=1)
    assert height / width == pytest.approx(0.3 / 0.78 * SCAN_PAGE_ASPECT, rel=0.02)
    assert re.search(r'viewBox="0 0 516 ', svg(year_panel(), "mono"))
