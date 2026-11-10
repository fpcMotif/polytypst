import json
import re
from dataclasses import replace

import pytest

from polytypst.charts.engine import (
    PT_PER_PX,
    SCAN_LINE_PT,
    SCAN_PAGE_ASPECT,
    FigureSpec,
    LineSeries,
    PanelSpec,
    chart_svg,
    finish_chart,
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
    return re.findall(r'<line [^>]*stroke="#(?:c4c4c4|000000)" stroke-width="0\.(?:48|7)"[^>]*/>', text)


def plot_box(text: str) -> tuple[float, ...]:
    return tuple(float(v) for v in re.search(r'<clipPath [^>]*><rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', text).groups())


def text_at(text: str, label: str) -> str:
    return next(m[0] for m in re.finditer(r"<text [^>]*>([^<]*)</text>", text) if m[1] == label)


def test_scan_style_draws_a_solid_black_grid_where_mono_draws_a_solid_light_grey_one():
    mono, scan = svg(year_panel(), "mono"), svg(year_panel(), "scan")
    assert grid_lines(mono)
    assert all('stroke-dasharray' not in g and "#c4c4c4" in g for g in grid_lines(mono))
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


@pytest.mark.parametrize("mode", ["mono", "scan"])
def test_an_inside_legend_stacks_one_series_per_row_in_the_plot_top_left(mode):
    text = svg(year_panel(legend_loc="inside"), mode)
    px0, py0, pw, ph = plot_box(text)
    spots = [
        tuple(float(v) for v in re.search(r'x="([\d.]+)" y="([\d.]+)"', text_at(text, label)).groups())
        for label in ("劳动时间指数1（A）", "就业指数（B）", "劳动时间×就业人数（A×B）")
    ]
    assert len({x for x, _ in spots}) == 1
    assert [y for _, y in spots] == sorted({y for _, y in spots})
    assert all(px0 < x < px0 + pw / 2 and py0 < y < py0 + ph / 2 for x, y in spots)


@pytest.mark.parametrize("mode", ["mono", "color"])
def test_an_open_frame_draws_only_the_left_and_bottom_axes(mode):
    text = svg(year_panel(open_frame=True), mode)
    assert not re.search(r'<rect [^>]*fill="none" stroke="#(?:000000|334155)"', text)
    frame = re.search(r'<path d="M ([\d.]+),([\d.]+) L ([\d.]+),([\d.]+) L ([\d.]+),([\d.]+)" fill="none" stroke="#(?:000000|334155)"', text)
    x0, y0, x1, y1, x2, y2 = (float(v) for v in frame.groups())
    assert x0 == x1 and y1 == y2 and y0 < y1 and x2 > x1


def test_the_book_style_frames_every_mono_chart_left_and_bottom_and_boxes_colour_charts():
    assert re.search(r'<path d="M [\d.,]+ L [\d.,]+ L [\d.,]+" fill="none" stroke="#000000" stroke-width="0.8"/>', svg(year_panel(), "mono"))
    assert re.search(r'<rect [^>]*fill="none" stroke="#334155"', svg(year_panel(), "color"))


def test_the_book_style_keeps_a_right_axis_when_a_chart_has_a_second_scale():
    text = svg(year_panel(y2lim=(0.0, 10.0), y2ticks=[0.0, 5.0, 10.0]), "mono")
    frame = re.search(r'<path d="M ([\d.]+),([\d.]+) L [\d.,]+ L [\d.,]+ L ([\d.]+),([\d.]+)" fill="none" stroke="#000000"', text)
    assert frame and frame[2] == frame[4]


def test_the_book_style_points_ticks_out_of_the_plot_and_marks_unlabelled_years_with_short_ticks():
    text = svg(year_panel(), "mono")
    _px0, py0, _pw, ph = plot_box(text)
    bottom = py0 + ph
    x_ticks = [
        round(float(m[4]) - float(m[2]), 2)
        for m in re.finditer(r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)" stroke="#000000"', text)
        if m[1] == m[3] and float(m[2]) == bottom
    ]
    labelled = [y for y in range(1980, 2007, 2) if f">{y}</text>" in text]
    assert sorted({round(t, 2) for t in x_ticks}) == [2.4, 4.48]
    assert x_ticks.count(4.48) == len(labelled) and x_ticks.count(2.4) == 14 - len(labelled)


def test_the_book_style_prints_tick_labels_at_7_8_pt_and_series_labels_at_8_pt():
    text = svg(year_panel(), "mono")
    assert f'font-size="{7.8 / PT_PER_PX:.2f}"' in text_at(text, "1980")
    assert f'font-size="{8.0 / PT_PER_PX:.1f}"' in text_at(text, "就业指数（B）")


def test_bare_tick_values_share_one_number_of_decimals():
    index = replace(year_panel(), ylim=(0.8, 1.6), yticks=[0.8, 1.0, 1.2, 1.4, 1.6])
    text = svg(index, "mono")
    assert all(f">{v}</text>" in text for v in ("0.8", "1.0", "1.2", "1.4", "1.6"))
    assert ">−2</text>" in svg(replace(year_panel(), ylim=(-2.0, 2.0), yticks=[-2.0, 0.0, 2.0]), "mono")


def test_the_book_style_holds_series_strokes_between_0_9_and_1_25_pt_in_pure_greys():
    panel = year_panel()
    panel.lines[0].width, panel.lines[1].width = 0.5, 4.0
    widths = [float(w) for w in re.findall(r'<path d="M [^"]+" fill="none" stroke="#[0-9a-f]{6}" stroke-width="([\d.]+)" stroke-linecap', svg(panel, "mono"))]
    assert min(widths) == pytest.approx(0.9 / PT_PER_PX, abs=0.01)
    assert max(widths) == pytest.approx(1.25 / PT_PER_PX, abs=0.01)
    strokes = set(re.findall(r'stroke="#([0-9a-f]{6})"', svg(panel, "mono")))
    assert all(s[0:2] == s[2:4] == s[4:6] for s in strokes)


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


@pytest.mark.slow
def test_chart_style_b_is_the_scan_style_set_in_the_body_fonts_and_style_a_is_mono():
    def generator(mode: str) -> str:
        return svg(year_panel(), mode)

    b = chart_svg(generator, "b")
    fonts = set(re.findall(r'font-family="([^"]+)"', b))
    assert fonts == {"'Source Serif 4', 'Songti SC', serif"}
    assert grid_lines(b) == grid_lines(svg(year_panel(), "scan"))
    assert chart_svg(generator, "a") == finish_chart(svg(year_panel(), "mono"))


@pytest.mark.slow
def test_a_printed_chart_is_set_in_one_type_family_and_trimmed_to_its_ink():
    raw = svg(year_panel(), "mono")
    done = finish_chart(raw)
    assert len(set(re.findall(r'font-family="([^"]+)"', done))) == 1
    raw_w = float(re.search(r'viewBox="0 0 ([\d.]+)', raw)[1])
    x, y, w, h = (float(v) for v in re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', done).groups())
    assert x > 0 and y > 0 and w < raw_w
    assert re.search(rf'<svg[^>]* width="{w:.1f}" height="{h:.1f}"', done)


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


def test_four_series_multimodal_encoding_uses_dual_grey_and_white_knockout_stacking():
    xs = [2010.0, 2012.0, 2014.0]
    panel = PanelSpec(
        xlim=(2010.0, 2014.0),
        ylim=(0.8, 1.6),
        xticks=xs,
        yticks=[0.8, 1.0, 1.2, 1.4, 1.6],
        lines=[
            LineSeries(x=xs, y=[1.0, 1.2, 1.4], label="劳动生产率", color_idx=0, marker="circle"),
            LineSeries(x=xs, y=[1.0, 1.1, 1.3], label="技术进步率", color_idx=1, marker="circle"),
            LineSeries(x=xs, y=[1.0, 0.95, 0.9], label="绿色全要素", color_idx=2, marker="triangle"),
            LineSeries(x=xs, y=[1.0, 1.05, 1.15], label="资本生产率", color_idx=3, marker="square"),
        ],
    )
    text = svg(panel, "mono")
    line_paths = list(re.finditer(r'<path d="M [^"]+" fill="none" stroke="(#[0-9a-f]{6})" stroke-width="([\d.]+)" stroke-linecap', text))
    assert [m[1] for m in line_paths] == ["#000000", "#000000", "#666666", "#666666"]
    assert [float(m[2]) for m in line_paths] == [2.0, 1.84, 2.0, 1.76]
    hollow_pos = text.index('fill="#ffffff" stroke="#000000"')
    solid_pos = text.index('fill="#000000" stroke="#000000"')
    assert line_paths[-1].end() < hollow_pos < solid_pos


def test_render_figure_svg_omits_source_and_note_citations_from_svg_and_lint_catches_baked_notes():
    from scripts.figure_lint import lint_svg

    spec_with_source = FigureSpec(fig_id="5-3", title="", panels=[year_panel()], note="资料来源：作者创建。", width=860, height=500)
    rendered_source = render_figure_svg(spec_with_source, "mono")
    assert "资料来源" not in rendered_source

    spec_with_note = FigureSpec(fig_id="2-2", title="", panels=[year_panel()], note="注：阴影表示经济衰退期。", width=860, height=500)
    rendered_note = render_figure_svg(spec_with_note, "mono")
    assert "阴影表示" not in rendered_note

    spec_with_in_chart = FigureSpec(fig_id="11-1", title="", panels=[year_panel()], note="数值越大，离岸程度越高", width=860, height=500)
    rendered_in_chart = render_figure_svg(spec_with_in_chart, "mono")
    assert "数值越大，离岸程度越高" in rendered_in_chart

    bad_svg = rendered_source.replace("</svg>", '<text x="68" y="490" font-size="10">资料来源：作者创建。</text></svg>')
    rules = {f.rule for f in lint_svg(bad_svg)}
    assert "baked_note" in rules


def test_annotations_and_scatter_labels_render_outside_panel_clip_path():
    from polytypst.charts.engine import Annotation

    panel = replace(
        year_panel(),
        annotations=[Annotation(x=2005.0, y=100.0, text="市场实际利率因零利率下限上升", dx=10, dy=0, arrow=False, align="start")],
    )
    rendered = svg(panel, "mono")
    clipped_groups = re.findall(r'<g clip-path="url\(#[^)]+\)">(.*?)</g>', rendered, re.DOTALL)
    assert all("市场实际利率因零利率下限上升" not in g for g in clipped_groups)
    assert "市场实际利率因零利率下限上升" in rendered



