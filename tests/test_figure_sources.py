import json
from dataclasses import replace

from polytypst.compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographCompiler,
    MonographSpec,
)

SPEC = MonographSpec(
    slug="probe",
    title="探针",
    author="甲",
    lang="zh",
    domain="economics",
    chapters=[ChapterSpec(10, "外国劳动者", 1, 40)],
)


def svg(note: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg"><text>{note}</text></svg>'


def typst_of_page(tmp_path, notes: dict[str, str], body: str) -> str:
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    for fid, note in notes.items():
        (fig_dir / f"fig_{fid}.svg").write_text(svg(note), encoding="utf-8")
    compiler = MonographCompiler(SPEC)
    figures = compiler.render_figure_group([(fid.replace("-", "_", 1), f"图 {fid}") for fid in notes], fig_dir)
    return compiler.format_typst(figures + body)


def test_a_redrawn_chart_prints_at_its_share_of_the_scan_text_line(tmp_path):
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    manifest = []
    for fid, left, right in (("10-1", 0.2, 0.59), ("10-2", 0.1, 0.95)):
        (fig_dir / f"fig_{fid}.svg").write_text(svg(""), encoding="utf-8")
        manifest.append({"figure_id": fid, "caption": f"图 {fid}", "image_rel_path": f"figures/fig_{fid}.png",
                         "source_page": 5, "box": [left, 0.1, right, 0.4]})
    (tmp_path / "figures_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    spec = replace(SPEC, figures=FigureLayout(svg_single_pct=100, svg_scan_text_width=0.78))
    compiler = MonographCompiler(spec)
    half = compiler.make_figure_typst("10_1", "图 10-1", fig_dir)
    wide = compiler.make_figure_typst("10_2", "图 10-2", fig_dir)
    assert 'fig_10-1.svg", width: 50%' in half
    assert 'fig_10-2.svg", width: 100%' in wide


def test_a_figure_note_prints_under_its_figure_as_a_note_block_not_body_text(tmp_path):
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    (fig_dir / "fig_10-6.svg").write_text(svg(""), encoding="utf-8")
    compiler = MonographCompiler(SPEC)
    compiler.cleaner.figure_notes["10_6"] = "注：1. 数据来源为财务省。\n\n2. 由笔者测算。"
    figures = compiler.render_figure_group([("10_6", "图 10-6")], fig_dir)
    typst = compiler.format_typst(figures + "（资料来源：日本法务省）\n\n后文继续。")
    note = typst[typst.index("#fig-note[") : typst.index("后文继续。")]
    assert typst.index("fig_10-6.svg") < typst.index("#fig-note[")
    assert "数据来源为财务省" in note and "由笔者测算" in note and "（资料来源：日本法务省）" in note
    assert note.rstrip().endswith("]") and note.count("#fig-note[") == 1
    assert "#let fig-note(body)" in compiler.build_typst_preamble()


def test_each_source_that_a_figure_of_the_block_prints_leaves_the_body(tmp_path):
    typst = typst_of_page(
        tmp_path,
        {"10-6": "资料来源：日本厚生劳动省", "10-7A": "", "10-7B": "资料来源：日本厚生劳动省"},
        "（资料来源：日本厚生劳动省）\n\n（资料来源：日本厚生劳动省）\n\n后文继续。",
    )
    assert typst.count("（资料来源：日本厚生劳动省）") == 0
    assert "后文继续。" in typst


def test_a_source_that_no_figure_of_the_block_prints_stays(tmp_path):
    typst = typst_of_page(
        tmp_path,
        {"10-2": "资料来源：日本国立社会保障和人口问题研究所", "10-3": "资料来源：日本国立社会保障·人口问题研究所"},
        "（资料来源：日本国立社会保障和人口问题研究所）\n\n（资料来源：日本法务省）\n\n后文继续。",
    )
    assert "（资料来源：日本国立社会保障和人口问题研究所）" not in typst
    assert "（资料来源：日本法务省）" in typst
