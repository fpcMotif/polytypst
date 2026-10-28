from polytypst.compiler.monograph import ChapterSpec, MonographCompiler, MonographSpec

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
