from dataclasses import replace

import pytest
from PIL import Image

from polytypst.book_state import book_state
from polytypst.compiler.monograph import ChapterSpec, FigureLayout, MonographSpec
from polytypst.compiler.page_cleaner import CleanPage, PageCleaner

SPEC = MonographSpec(
    domain="math",
    slug="probe",
    title="Probe",
    author="A",
    chapters=[ChapterSpec(1, "Holomorphic functions", 1, 40)],
    sections={"1.2": (5, "Power series")},
)


def test_a_note_printed_between_a_figure_and_its_caption_travels_with_that_figure():
    spec = replace(
        SPEC,
        lang="zh",
        chapters=[ChapterSpec(3, "储蓄", 1, 40)],
        figures=FigureLayout(caption_format="图 {chapter}-{number}", note_before_caption=True),
    )
    page = (
        "正文段落。\n\n注：根据总务省“劳动力调查”编制。\n\n图 3-4 完全失业率\n\n"
        "注：1. 根据“一般职业介绍情况”编制。\n\n2. 经季节性调整。\n\n图 3-5 新就业人数\n"
    )
    cleaner = PageCleaner.for_spec(spec)
    clean = cleaner.clean(page, 5)
    assert clean.body == "正文段落。"
    assert cleaner.figure_notes == {
        "3_4": "注：根据总务省“劳动力调查”编制。",
        "3_5": "注：1. 根据“一般职业介绍情况”编制。\n\n2. 经季节性调整。",
    }


def test_a_section_heading_is_placed_once_and_its_running_head_is_dropped_later():
    cleaner = PageCleaner.for_spec(SPEC)
    first = cleaner.clean("## 1.2 Power Series\n\nEvery power series converges in a disc.", 5)
    later = cleaner.clean("1.2 Power series 7\n\nThe radius is given by Hadamard.", 7)
    assert first.body == "## 1.2 Power series\n\nEvery power series converges in a disc."
    assert later.body == "The radius is given by Hadamard."


def test_a_new_cleaner_has_placed_no_headings():
    _ = PageCleaner.for_spec(SPEC).clean("## 1.2 Power Series\n\nText.", 5)
    fresh = PageCleaner.for_spec(SPEC).clean("## 1.2 Power Series\n\nText.", 5)
    assert fresh.body.startswith("## 1.2 Power series")


def test_unnumbered_cleaning_leaves_equation_tags_as_written():
    page = "Hence\n\n$$\nx = 1 \\tag{29}\n$$\n\nand so on."
    labeled = PageCleaner.for_spec(SPEC).clean(page, 5).body
    unlabeled = PageCleaner.for_spec(replace(SPEC, equation_numbering="none")).clean(page, 5).body
    assert "<eq-" in labeled
    assert unlabeled == page


@pytest.mark.parametrize("lost", ["$", "$$"])
def test_a_display_whose_opening_dollars_fell_on_the_last_page_keeps_the_next_prose_as_text(lost: str):
    align = "\\begin{align} a &= b \\\\ &= c \\end{align}"
    page = f"$${align}$$"[len(lost) :] + f"\n\nThe word zqbbbbb is plain prose.\n\n$${align}$$"
    blocks = PageCleaner.for_spec(SPEC).clean(page, 5).body.split("$$")
    assert [i for i, block in enumerate(blocks) if "zqbbbbb" in block] == [2]


def test_a_run_of_dollars_does_not_turn_the_next_prose_into_math():
    page = "$" * 19999 + "\n\nThe word zqbbbbb is plain prose.\n\n$$x = 1$$"
    blocks = PageCleaner.for_spec(SPEC).clean(page, 5).body.split("$$")
    assert [i for i, block in enumerate(blocks) if "zqbbbbb" in block] == [0]


def test_display_dollars_left_open_at_the_foot_of_a_page_are_dropped():
    assert PageCleaner.for_spec(SPEC).clean("The proof ends here.\n\n$$", 5).body == "The proof ends here."


def test_folios_watermarks_and_captions_leave_the_body():
    page = "12\n\nClibPDF - www.fastio.com\n\nThe map is shown below.\n\nFig. 1.3\n\nIt is conformal.\n\nSo is its inverse.\n\nFig. 1.4"
    assert PageCleaner.for_spec(SPEC).clean(page, 12) == CleanPage(
        "The map is shown below.\n\nIt is conformal.\n\nSo is its inverse.",
        [("1_3", "Fig. 1.3")],
        [("1_4", "Fig. 1.4")],
    )


def test_default_caption_pattern_matches_single_numbers_and_cjk():
    page = "The curve is smooth.\n\nFig. 5\n\nNext paragraph.\n\nAnother paragraph.\n\n图 131"
    assert PageCleaner.for_spec(SPEC).clean(page, 12) == CleanPage(
        "The curve is smooth.\n\nNext paragraph.\n\nAnother paragraph.",
        [("5", "Figure 5")],
        [("131", "图 131")],
    )


def test_a_chinese_caption_keeps_its_number_style_and_title():
    page = "注：笔者使用 JIP2006 计算。\n\n图 1-1 进口渗透和就业（1990—2000 年）\n\n虽然这些数字会使人认为。\n\n下面将首先讨论。"
    cleaned = PageCleaner.for_spec(SPEC).clean(page, 32)
    assert cleaned.top_figures + cleaned.bottom_figures == [("1_1", "图 1-1 进口渗透和就业（1990—2000 年）")]


@pytest.mark.parametrize("source", ["（资料来源：日本厚生劳动省）", "资料来源：日本厚生劳动省", "注：单位为万人"])
def test_the_source_line_of_one_figure_stays_when_the_next_caption_follows_it(source: str):
    page = f"图 10-6 全体劳动者的薪酬\n\n{source}\n\n图 10-7 新员工的薪酬\n\n后文继续。"
    assert source in PageCleaner.for_spec(SPEC).clean(page, 313).body.splitlines()


def test_the_figure_manifest_decides_which_page_holds_a_caption(tmp_path):
    from polytypst.vision.figure_extractor import (
        ExtractedFigure,
        write_figures_manifest,
    )

    chinese = replace(
        SPEC,
        figures=replace(
            SPEC.figures,
            caption_pattern=r"^图\s*(?P<chapter>\d+)-(?P<number>\d+)\s*(?P<title>.+)$",
            caption_format="图 {chapter}-{number}",
        ),
    )
    title = "假设医疗并未引起死亡率下降时的 GDP 与存在医疗保险制度的现实 GDP 比较（SNA97，模型估算时间 1977—2001 年）"
    caption_page = f"图 7-6 所示为医疗的效果，而且\n\n正文。\n\n图 7-6 {title}\n\n下面讨论。"
    prose_line = "图 1-1 为财政收支的变化柱状图。从名义值来看，政府支"
    prose_page = f"正文。\n\n{prose_line}\n\n下面讨论。"
    unaided = PageCleaner.for_spec(chinese, tmp_path)
    caption_alone = unaided.clean(caption_page, 32)
    prose_alone = unaided.clean(prose_page, 33)
    assert caption_alone.top_figures + caption_alone.bottom_figures == []
    assert prose_alone.top_figures + prose_alone.bottom_figures != []

    write_figures_manifest(
        tmp_path / "figures_manifest.json",
        [
            ExtractedFigure("7-6", f"图 7-6 {title}", "figures/fig_7-6.png", 32),
            ExtractedFigure("1-1", "图 1-1 一般会计财政收支", "figures/fig_1-1.png", 34),
        ],
    )
    cleaner = PageCleaner.for_spec(chinese, tmp_path)
    caption = cleaner.clean(caption_page, 32)
    assert caption.top_figures + caption.bottom_figures == [("7_6", f"图 7-6 {title}")]
    prose = cleaner.clean(prose_page, 33)
    assert prose.top_figures + prose.bottom_figures == []
    assert prose_line in prose.body


def test_a_manifest_figure_whose_caption_the_transcript_lost_is_placed_on_its_page(tmp_path):
    from polytypst.vision.figure_extractor import (
        ExtractedFigure,
        write_figures_manifest,
    )

    chinese = replace(
        SPEC,
        figures=replace(
            SPEC.figures,
            caption_pattern=r"^图\s*(?P<chapter>\d+)-(?P<number>\d+(?:\.\d+)?)\s*(?P<title>.+)$",
            caption_format="图 {chapter}-{number}",
        ),
    )
    write_figures_manifest(
        tmp_path / "figures_manifest.json",
        [
            ExtractedFigure("9-5", "图 9-5 对美内外价格要素分解（同比）", "figures/fig_9-5.png", 34),
            ExtractedFigure("9-6", "图 9-6 对美单位劳动力成本", "figures/fig_9-6.png", 34),
            ExtractedFigure("10-4.1", "图 10-4.1 中薪阶层占比", "figures/fig_10-4.1.png", 35),
        ],
    )
    cleaner = PageCleaner.for_spec(chinese, tmp_path)
    lost = cleaner.clean("正文。\n\n图 9-6 对美单位劳动力成本\n\n下面讨论。", 34)
    assert lost.top_figures + lost.bottom_figures == [
        ("9_6", "图 9-6 对美单位劳动力成本"),
        ("9_5", "图 9-5 对美内外价格要素分解（同比）"),
    ]
    assert cleaner.clean("正文。", 35).bottom_figures == [("10_4.1", "图 10-4.1 中薪阶层占比")]
    assert cleaner.clean("正文。", 36).bottom_figures == []


def test_a_two_line_caption_takes_its_whole_text_from_the_manifest(tmp_path):
    from polytypst.vision.figure_extractor import (
        ExtractedFigure,
        write_figures_manifest,
    )

    chinese = replace(
        SPEC,
        figures=replace(
            SPEC.figures,
            caption_pattern=r"^图\s*(?P<chapter>\d+)-(?P<number>\d+(?:\.\d+)?)\s*(?P<title>.+)$",
            caption_format="图 {chapter}-{number}",
        ),
    )
    caption = "图 10-4.2 工资的沃尔夫森极化指数"
    write_figures_manifest(
        tmp_path / "figures_manifest.json",
        [
            ExtractedFigure("10-4.2", caption, "figures/fig_10-4.2.png", 35),
            ExtractedFigure("1-4", "图 1-4", "figures/fig_1-4.png", 36),
        ],
    )
    cleaner = PageCleaner.for_spec(chinese, tmp_path)
    page = "注：规定工资。\n\n图 10-4.2 工资的沃尔夫\n\n森极化指数\n\n当差距整体上扩大时。"
    cleaned = cleaner.clean(page, 35)
    assert cleaned.top_figures + cleaned.bottom_figures == [("10_4.2", caption)]
    assert cleaned.body == "注：规定工资。\n\n当差距整体上扩大时。"
    zh_page = "图 10-4.1 中薪阶层占比\n\n（中位数的 75%~150%）\n\n正文。"
    write_figures_manifest(
        tmp_path / "figures_manifest.json",
        [ExtractedFigure("10-4.1", "图 10-4.1 中薪阶层占比（中位数的 75%~150%）", "figures/fig_10-4.1.png", 37)],
    )
    zh = PageCleaner.for_spec(replace(chinese, lang="zh"), tmp_path).clean(zh_page, 37)
    assert zh.top_figures + zh.bottom_figures == [("10_4.1", "图 10-4.1 中薪阶层占比（中位数的 75%～150%）")]
    assert zh.body == "正文。"
    bare = cleaner.clean("图 1-4 日本制造业的产业结构变化\n\n正文。", 36)
    assert bare.top_figures + bare.bottom_figures == [("1_4", "图 1-4 日本制造业的产业结构变化")]


def test_missing_figure_emits_orphaned_caption_and_require_vector_skips_png(tmp_path):
    from polytypst.compiler.monograph import MonographCompiler

    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    (fig_dir / "fig_1.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03"
    )
    vec_spec = replace(SPEC, require_vector_figures=True)
    compiler = MonographCompiler(vec_spec)
    rendered = compiler.render_figure_group([("1", "Figure 1"), ("2", "Figure 2")], fig_dir)
    assert 'image("figures/fig_1.png"' not in rendered
    assert "#emph[Figure 1]" in rendered
    assert "#emph[Figure 2]" in rendered


def test_a_figure_continued_on_the_next_page_is_labelled_once(tmp_path):
    from polytypst.compiler.monograph import MonographCompiler

    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    Image.new("RGB", (400, 300), "white").save(fig_dir / "fig_7-6.png")
    compiler = MonographCompiler(replace(SPEC, cross_references=True))
    first = compiler.render_figure_group([("7_6", "图 7-6 拆借利率")], fig_dir)
    continued = compiler.render_figure_group([("7_6", "图 7-6 拆借利率（续）")], fig_dir)
    assert first.count("<fig-7-6>") == 1
    assert "<fig-7-6>" not in continued
    assert 'image("figures/fig_7-6.png"' in continued


def test_a_sub_numbered_figure_caption_loses_its_whole_number(tmp_path):
    from polytypst.compiler.monograph import MonographCompiler

    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    Image.new("RGB", (400, 300), "white").save(fig_dir / "fig_10-4.2.png")
    compiler = MonographCompiler(replace(SPEC, cross_references=True))
    placed = compiler.render_figure_group([("10_4.2", "图 10-4.2 工资的沃尔夫森极化指数")], fig_dir)
    missing = compiler.render_figure_group([("10_6.3", "图 10-6.3 女性")], fig_dir)
    assert "caption: [工资的沃尔夫森极化指数]" in placed
    assert "caption: [女性]" in missing


def test_a_cross_referenced_figure_caption_prints_its_chapter_number(tmp_path):
    import subprocess

    import pymupdf

    from polytypst.compiler.monograph import MonographCompiler

    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    Image.new("RGB", (400, 300), "white").save(fig_dir / "fig_7-7.png")
    figure = MonographCompiler(replace(SPEC, cross_references=True)).render_figure_group(
        [("7_7", "图 7-7 日元/美元汇率")], fig_dir
    )
    source = tmp_path / "f.typ"
    _ = source.write_text(f"#show figure.where(kind: image): set figure(supplement: [图])\n{figure}\n", encoding="utf-8")
    _ = subprocess.run(["typst", "compile", str(source)], check=True, capture_output=True)
    text = pymupdf.open(tmp_path / "f.pdf")[0].get_text()
    assert "图 7-7" in text.replace(" ", " ")


def test_a_latex_footnote_escapes_underscores_and_ampersands_outside_math():
    from polytypst.compiler.monograph import latex_footnotes

    note = latex_footnotes("x@@FNSTART@@LOG ( LENDING_SA ) & M0 $a_1$@@FNEND@@")
    assert note == r"x \footnote{LOG ( LENDING\_SA ) \& M0 $a_1$}"


def test_an_ampersand_in_a_source_heading_is_escaped_for_latex():
    from polytypst.compiler.monograph import latex_safe_markdown

    heading = r"\sourcesubsection{美国储贷协会危机（S&L Crisis）}"
    assert latex_safe_markdown(heading) == r"\sourcesubsection{美国储贷协会危机（S\&L Crisis）}"


def test_two_inline_notes_in_one_chinese_paragraph_stay_footnotes_in_latex(tmp_path):
    from polytypst.compiler.monograph import MonographCompiler

    md = tmp_path / "b.md"
    _ = md.write_text("法定劳动时间得以缩短^[有人指出，调查存在少报的倾向。]。从以下事实可以看出景气^[波谷是在1986年11月。]。\n", encoding="utf-8")
    tex = tmp_path / "b.tex"
    MonographCompiler(replace(SPEC, lang="zh"))._write_latex(md, tex)
    body = tex.read_text(encoding="utf-8")
    assert body.count(r"\footnote{") == 2
    assert r"\textsuperscript" not in body


def test_figure_book_verifies_completeness_against_manifest_and_transcripts(tmp_path):
    from polytypst.vision.diagram_engine import FigureBook, FigureSpec
    from polytypst.vision.figure_extractor import (
        ExtractedFigure,
        write_figures_manifest,
    )

    write_figures_manifest(
        tmp_path / "figures_manifest.json",
        [
            ExtractedFigure("1", "Fig. 1", "figures/fig_1.png", 10),
            ExtractedFigure("2", "Fig. 2", "figures/fig_2.png", 12),
        ],
    )
    md_dir = book_state(tmp_path) / "markdown_pages"
    md_dir.mkdir(parents=True)
    (md_dir / "p_0015.md").write_text("Text.\n\n图 3\n", encoding="utf-8")

    book = FigureBook(
        slug="demo",
        title="Demo",
        subtitle="",
        figures=(FigureSpec("1", "Fig. 1", 1, lambda: "<svg/>"),),
    )
    assert book.verify_completeness(tmp_path) == ["2", "3"]

