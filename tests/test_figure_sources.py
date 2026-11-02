import json
from dataclasses import replace

from PIL import Image

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


def test_a_figure_floats_with_its_note_and_the_text_flows_past_it(tmp_path):
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    (fig_dir / "fig_10-6.svg").write_text(svg(""), encoding="utf-8")
    compiler = MonographCompiler(SPEC)
    compiler.cleaner.figure_notes["10_6"] = "注：根据财务省制作。"
    typst = compiler.format_typst(compiler.render_figure_group([("10_6", "图 10-6")], fig_dir) + "后文继续。")
    float_start = typst.index("#place(auto, float: true, clearance: 1.2em)[\n#set align(start)\n")
    float_end = typst.index("后文继续。")
    assert float_start < typst.index("fig_10-6.svg") < typst.index("根据财务省制作") < float_end
    assert typst[:float_end].rstrip().endswith("]\n]")
    sourced = replace(SPEC, paginate_like_source=True)
    assert "float: true" not in MonographCompiler(sourced).format_typst(compiler.render_figure_group([("10_6", "图 10-6")], fig_dir))


def test_each_source_that_a_figure_of_the_block_prints_leaves_the_body(tmp_path):
    typst = typst_of_page(
        tmp_path,
        {"10-6": "资料来源：日本厚生劳动省", "10-7A": "", "10-7B": "资料来源：日本厚生劳动省"},
        "（资料来源：日本厚生劳动省）\n\n（资料来源：日本厚生劳动省）\n\n后文继续。",
    )
    assert typst.count("（资料来源：日本厚生劳动省）") == 0
    assert "后文继续。" in typst


def test_a_page_link_to_a_figure_that_is_already_placed_prints_no_second_copy(tmp_path):
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    (fig_dir / "fig_6-7.svg").write_text(svg(""), encoding="utf-8")
    Image.new("RGB", (900, 600), "white").save(fig_dir / "fig_6-7.png")
    compiler = MonographCompiler(replace(SPEC, cross_references=True))
    compiler._out_dir = tmp_path
    figures = compiler.render_figure_group([("6_7", "图 6-7 预期通货膨胀率")], fig_dir)
    typst = compiler.format_typst(figures + "\n\n![图 6-7](figures/fig_6-7.png)\n\n后文继续。")
    assert typst.count("fig_6-7.") == 1
    assert "@fig-6-7]" not in typst
    assert "后文继续。" in typst


def test_a_page_link_to_a_figure_not_yet_placed_still_prints(tmp_path):
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    Image.new("RGB", (900, 600), "white").save(fig_dir / "fig_6-8.png")
    compiler = MonographCompiler(replace(SPEC, cross_references=True))
    compiler._out_dir = tmp_path
    typst = compiler.format_typst("![图 6-8](figures/fig_6-8.png)\n\n后文继续。")
    assert typst.count("fig_6-8.png") == 1


def test_a_source_that_no_figure_of_the_block_prints_stays(tmp_path):
    typst = typst_of_page(
        tmp_path,
        {"10-2": "资料来源：日本国立社会保障和人口问题研究所", "10-3": "资料来源：日本国立社会保障·人口问题研究所"},
        "（资料来源：日本国立社会保障和人口问题研究所）\n\n（资料来源：日本法务省）\n\n后文继续。",
    )
    assert "（资料来源：日本国立社会保障和人口问题研究所）" not in typst
    assert "（资料来源：日本法务省）" in typst


def test_significance_stars_in_notes_are_not_consumed_as_markdown_emphasis():
    compiler = MonographCompiler(SPEC)
    typst = compiler.format_typst("注：括号内是标准误差。*、**、***分别表示10%、5%、1%显著性水平，（*）和（**）同。")
    assert r"。\*、\*\*、\*\*\*" in typst
    assert r"（\*）和（\*\*）" in typst
    assert "#emph" not in typst and "#strong" not in typst


def test_cleaner_claims_multi_item_figure_notes_across_markdown_image():
    compiler = MonographCompiler(SPEC)
    cleaned = compiler.cleaner.clean(
        "图 2-6 实际汇率走势\n\n![图 2-6](figures/fig_2-6.png)\n\n"
        "注：1. 1973年2月以后为浮动汇率制。\n\n2. 阴影部分为经济衰退期。\n\n"
        "（资料来源：日本银行）\n\n正文段落开始。",
        10,
    ).body
    assert "1973年2月以后为浮动汇率制" in compiler.cleaner.figure_notes.get("2_6", "")
    assert "阴影部分为经济衰退期" in compiler.cleaner.figure_notes.get("2_6", "")
    assert "1973年2月以后为浮动汇率制" not in cleaned
    assert "阴影部分为经济衰退期" not in cleaned
    assert "正文段落开始。" in cleaned


def test_a_source_already_in_cleaner_figure_notes_is_dropped_when_svg_prints_it(tmp_path):
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    (fig_dir / "fig_5-2.svg").write_text(svg("资料来源：日经数据库。"), encoding="utf-8")
    compiler = MonographCompiler(SPEC)
    compiler.cleaner.figure_notes["5_2"] = "（资料来源：日经数据库）"
    typst = compiler.format_typst(compiler.render_figure_group([("5_2", "图 5-2 货币存量")], fig_dir) + "后文继续。")
    assert "（资料来源：日经数据库）" not in typst
    assert "#fig-note[" not in typst


def test_cleaner_claims_square_bracketed_sources_and_attaches_between_figure_sources_to_preceding_figure():
    compiler = MonographCompiler(replace(SPEC, figures=FigureLayout(note_before_caption=True)))
    page_text = (
        "图 2-3 隔夜拆借利率\n\n"
        "[资料来源：日经数据库]\n\n"
        "图 4-4 央行资产\n\n"
        "（资料来源：日本银行）\n\n"
        "注：各央行总资产名义 GDP 比。\n\n"
        "图 4-5 基础货币\n\n"
        "（资料来源：国际清算银行）\n\n"
        "正文开始。"
    )
    cleaned = compiler.cleaner.clean(page_text, 10).body
    assert compiler.cleaner.figure_notes.get("2_3") == "[资料来源：日经数据库]"
    assert compiler.cleaner.figure_notes.get("4_4") == "（资料来源：日本银行）"
    assert "各央行总资产名义 GDP 比" in compiler.cleaner.figure_notes.get("4_5", "")
    assert "（资料来源：国际清算银行）" in compiler.cleaner.figure_notes.get("4_5", "")
    assert cleaned.strip() == "正文开始。"



