import itertools
import re
import shutil
import subprocess
from pathlib import Path

import pymupdf
import pytest

from polytypst.compiler.tables import (
    continued_table_split,
    layout_tables,
    merge_continued_tables,
)

PAGE_WIDTH_PT, MARGIN_PT = 442, 56
BOOK_STYLE = Path(__file__).parent.parent / "books" / "styles" / "japan_economy.typ"


def compiled_words(tmp_path, typst: str) -> list[tuple[float, float, float, float, str]]:
    if not shutil.which("typst"):
        pytest.skip("typst is not installed")
    table_rules = [line for line in BOOK_STYLE.read_text().splitlines() if line.startswith(("#show table", "#set table"))]
    page = (
        f"#set page(width: {PAGE_WIDTH_PT}pt, height: 663pt, margin: {MARGIN_PT}pt)\n"
        '#set text(font: ("Songti SC", "STSong", "New Computer Modern"), size: 10pt, lang: "zh")\n'
        + "\n".join(table_rules)
        + "\n"
    )
    (tmp_path / "t.typ").write_text(page + typst, encoding="utf-8")
    subprocess.run(["typst", "compile", str(tmp_path / "t.typ"), str(tmp_path / "t.pdf")], check=True)
    return [w[:5] for p in pymupdf.open(tmp_path / "t.pdf") for w in p.get_text("words")]


MIN_GAP_PT = 3
GLUED_NUMBERS = re.compile(r"\d\.\d+[−\-]?\d+\.\d")
NUMBER_WORD = re.compile(r"[−\-+(]?[\d.,]+[)%*]*")


def overprinted(words) -> list[tuple[str, str]]:
    """Neighbouring numbers on one line that overlap or sit closer than MIN_GAP_PT, and words that are two numbers
    printed with no gap between them."""
    words = [w for w in words if w[4].strip("  ")]
    rows: dict[int, list] = {}
    for w in words:
        rows.setdefault(round(w[3]), []).append(w)
    pairs = [(w[4], "") for w in words if GLUED_NUMBERS.search(w[4])]
    for row in rows.values():
        row.sort(key=lambda w: w[0])
        pairs += [
            (a[4], b[4])
            for a, b in itertools.pairwise(row)
            if b[0] - a[2] < MIN_GAP_PT and NUMBER_WORD.fullmatch(a[4].strip(" ")) and NUMBER_WORD.fullmatch(b[4].strip(" "))
        ]
    return pairs


def row(*cells: str) -> str:
    return "| " + " | ".join(cells) + " |\n"


def wide_regression_table() -> str:
    years = ("Pooled", "1982", "1987", "1992", "1997", "2002")
    table = row("被解释变量<br>估计方法", "劳动时间等级中位数（15～60）<br>OLS", *[""] * 11) + row(*["---"] * 13)
    table += row("Sample", *(cell for y in years for cell in (y, "")))
    table += row("", *["Coef.", "s. e."] * 6)
    table += row("供电供气供热及水务行业", "-496.4", "4.236", "-307.1", "8.055", "-368.9", "8.610", "-514.5", "9.345", "-596.5", "10.055", "-602.0", "9.712")
    table += row("年龄", "0.298", "0.003", "0.226", "0.007", "0.245", "0.007", "0.311", "0.006", "0.282", "0.006", "0.417", "0.007")
    table += row("日工", "-266.2", "7.443", "-145.2", "11.842", "-188.6", "14.507", "-301.0", "16.167", "-353.8", "18.886", "-305.0", "19.020")
    table += row("服务业", "-7.1", "3.506", "8.2", "6.197", "14.8", "6.951", "-17.8", "7.300", "-5.2", "8.286", "-3.5", "9.178")
    table += row("公务", "276.8", "7.517", "99.3", "12.348", "179.0", "14.676", "319.8", "16.229", "455.7", "18.432", "461.7", "19.710")
    return table


def bracketed_t_values_table() -> str:
    table = row("", "const.", "bt", "Y_temp", "G_temp", "trend", "st (-1)", "Y_type", "G_type", "ρ", "Akaikecr.", "adj. R-2")
    table += row(*["---"] * 12) + row("①主模型", *[""] * 11)
    for n, values, t_values in (
        ("（1）", ("-0.0036", "-0.0272", "-0.7824", "0.7452"), ("(-0.2425)", "(-1.112)", "(-1.818)", "(1.9161)")),
        ("（2）", ("-0.0116", "-0.0168", "-0.66051", "0.491979"), ("(-0.9882)", "(-0.8330)", "(-1.6565)", "(1.7194)")),
        ("（3）", ("-0.0028", "-0.0284", "-0.6463", "2.1631"), ("(-0.2061)", "(-1.2070)", "(-1.5844)", "(1.9794)")),
    ):
        table += row(n, *values, "", "", "struc.", "Kalman", "0.9081", "-6.9433", "0.8174")
        table += row("", *t_values, "", "", "", "", "(15.122)", "", "")
    return table


@pytest.mark.parametrize("table", [wide_regression_table(), bracketed_t_values_table()], ids=["coef-se", "t-values"])
def test_a_number_table_too_wide_for_the_text_prints_at_7pt_or_more_with_no_overprint(tmp_path, table):
    out = layout_tables(f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n注：数据。\n", [table])
    if not shutil.which("typst"):
        pytest.skip("typst is not installed")
    table_rules = [line for line in BOOK_STYLE.read_text().splitlines() if line.startswith(("#show table", "#set table"))]
    page = f"#set page(width: {PAGE_WIDTH_PT}pt, height: 663pt, margin: {MARGIN_PT}pt)\n" + "\n".join(table_rules) + "\n"
    (tmp_path / "t.typ").write_text(page + '#set text(font: ("Songti SC", "STSong"), lang: "zh")\n' + out, encoding="utf-8")
    subprocess.run(["typst", "compile", str(tmp_path / "t.typ"), str(tmp_path / "t.pdf")], check=True)
    doc = pymupdf.open(tmp_path / "t.pdf")
    words = [w[:5] for p in doc for w in p.get_text("words")]
    assert overprinted(words) == []
    assert all(w[2] <= p.rect.width - MARGIN_PT + 0.5 for p in doc for w in p.get_text("words"))
    sizes = [s["size"] for p in doc for b in p.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"] if NUMBER_WORD.fullmatch(s["text"].strip("  "))]
    assert sizes and min(sizes) >= 7


def test_a_number_table_too_wide_for_the_text_moves_to_a_landscape_page():
    out = layout_tables(f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n注：数据。\n", [wide_regression_table()])
    assert out.startswith("#page(flipped: true)")


def test_a_table_wider_than_the_text_prints_no_number_over_its_neighbour_and_stays_inside_the_margins(tmp_path):
    years = ("Pooled", "1982", "1987", "1992", "1997", "2002")
    table = row("被解释变量<br>估计方法", "劳动时间等级中位数（15～60）<br>OLS", *[""] * 11) + row(*["---"] * 13)
    table += row("Sample", *(cell for y in years for cell in (y, "")))
    table += row("", *["Coef.", "s. e."] * 6)
    table += row("女性虚拟变量", "-4.316", "0.018", "-3.618", "0.041", "-4.179", "0.042", "-4.174", "0.037", "-4.403", "0.038", "-5.254", "0.044")
    table += row("年龄", "0.298", "0.003", "0.226", "0.007", "0.245", "0.007", "0.311", "0.006", "0.282", "0.006", "0.417", "0.007")
    table += row("已婚、非户主、普通家庭", "-2.296", "0.021", "-1.537", "0.046", "-1.971", "0.047", "-2.301", "0.042", "-2.698", "0.044", "-2.959", "0.050")
    table += row("大专、高等专科学校学历", "-0.672", "0.021", "-0.531", "0.055", "-0.576", "0.053", "-0.906", "0.043", "-0.710", "0.041", "-0.249", "0.045")
    words = compiled_words(tmp_path, layout_tables(table, []))
    assert overprinted(words) == []
    assert max(w[2] for w in words) <= PAGE_WIDTH_PT - MARGIN_PT + 0.5


def test_a_long_table_breaks_across_pages_and_no_row_runs_past_the_bottom_margin(tmp_path):
    if not shutil.which("typst"):
        pytest.skip("typst is not installed")
    table = row("year", "a", "b", "c", "d") + row(*["---"] * 5)
    table += "".join(row(f"Y{1900 + i}", "1.25", "−3.5", "10.0", "2") for i in range(80))
    page = f"#set page(width: {PAGE_WIDTH_PT}pt, height: 663pt, margin: {MARGIN_PT}pt)\n"
    (tmp_path / "t.typ").write_text(page + layout_tables(table, []), encoding="utf-8")
    subprocess.run(["typst", "compile", str(tmp_path / "t.typ"), str(tmp_path / "t.pdf")], check=True)
    doc = pymupdf.open(tmp_path / "t.pdf")
    assert len(doc) >= 2
    assert all(w[3] <= 663 - MARGIN_PT + 0.5 for p in doc for w in p.get_text("words"))
    assert sum("Y1979" in p.get_text() for p in doc) == 1


def test_a_long_spanning_header_does_not_squeeze_the_number_columns_under_it(tmp_path):
    groups = ("1958年至X年：无常数项", "1958年至X年：有常数项", "1958年至X年：常数项+时间趋势")
    table = row(*(cell for g in groups for cell in (g, "", "", ""))) + row(*["---"] * 12)
    table += row(*["X", "t-Statistic", "Prob.*", "lag"] * 3)
    table += "".join(row(*[year, "−1.2262", "0.1973", "0"] * 3) for year in ("1989", "1990", "2005"))
    words = compiled_words(tmp_path, layout_tables(table, []))
    assert overprinted(words) == []
    assert max(w[2] for w in words) <= PAGE_WIDTH_PT - MARGIN_PT + 0.5

TABLE = "| a | b |\n| :--- | :---: |\n| <mark>1.0</mark> | <b>2.0</b> |\n| <i>3.0<br>(4.0)</i> | 0.71** |\n"


def test_cell_tags_set_shading_bold_and_italic():
    out = layout_tables(TABLE, [])
    assert "table.cell(fill: luma(215))[1.0]" in out
    assert "[#strong[2.0]]" in out
    assert r"[#emph[3.0\ (4.0)]]" in out
    assert r"\<b" not in out and r"\<mark" not in out


def test_three_line_tables_fill_the_width_by_content_with_no_rules_between_rows():
    table = "| 职务 | 姓名 | 所属机构及职务 |\n| :--- | :--- | :--- |\n| 主任 | 香西 泰 | 日本经济研究中心特别研究顾问 |\n| 委员 | 伊藤 元重 | 东京大学研究生院经济学研究科教授 |\n"
    out = layout_tables(table, [], three_line=True)
    assert "columns: (4fr, 9fr, 30fr)" in out
    assert "luma(220)" not in out
    assert "else if y == 2 { (bottom: 1.0pt" in out
    assert "columns: 3," in layout_tables(table, [])


def test_asterisks_outside_tags_stay_literal():
    assert r"[0.71\*\*]" in layout_tables(TABLE, [])


def test_a_span_marker_centres_one_value_across_columns_in_a_data_row():
    table = '| 时间 | 总和 | 合同工 | 其他 |\n| :--- | :---: | :---: | :---: |\n| 1984年 | 15.3 | <span data-colspan="2">4.2</span> |  |\n'
    out = layout_tables(table, [])
    assert "[1984年], [15.3], table.cell(colspan: 2)[4.2]" in out
    assert "#strong[1984年]" not in out


def test_a_span_marker_keeps_the_cell_shading():
    table = '| a | b | c |\n| :--- | :---: | :---: |\n| x | <span data-colspan="2"><mark>1.0</mark></span> |  |\n'
    assert "table.cell(colspan: 2, fill: luma(215))[1.0]" in layout_tables(table, [])


def test_the_header_row_repeats_after_a_page_break():
    table = "| 时间 | 总和 | 男性 | 女性 | 其他 |\n| --- | --- | --- | --- | --- |\n| 1984年 | 15.3 | 7.7 | 29.0 | 4.2 |\n"
    out = layout_tables(table, [])
    assert "table.header([#strong[时间]], [#strong[总和]], [#strong[男性]], [#strong[女性]], [#strong[其他]]), [1984年]" in out


def test_a_two_level_header_repeats_both_rows():
    table = "|  | 日本 |  | 美国 |\n| --- | --- | --- | --- |\n|  | CPI | CGPI | CPI |\n| 电视 | 1.0 | 2.0 | 3.0 |\n"
    out = layout_tables(table, [])
    assert "table.header([], table.cell(colspan: 2)[#strong[日本]], [#strong[美国]], [], [#strong[CPI]], [#strong[CGPI]], [#strong[CPI]]), [电视]" in out


def test_a_numeric_column_lines_up_on_the_decimal_point():
    table = "| 年 | a | b | c | d |\n| --- | --- | --- | --- | --- |\n| x | 1.25 | 1 | 1 | 1 |\n| y | 10.5 | 2 | 2 | 2 |\n| z | −3 | 3 | 3 | 3 |\n"
    out = layout_tables(table, [])
    assert "[ 1.25]" in out
    assert "[10.5 ]" in out
    assert "[−3   ]" in out


def test_a_text_column_keeps_its_text():
    table = "| 年 | a | b | c | d |\n| --- | --- | --- | --- | --- |\n| x | 甲 | 1 | 1 | 1 |\n| y | 1.5 | 2 | 2 | 2 |\n| z | 乙 | 3 | 3 | 3 |\n"
    assert "[1.5]" in layout_tables(table, [])


def test_a_short_stub_column_fits_its_labels_and_long_columns_get_more_room():
    table = "| 时间 | 非正式雇员总和 | 临时员工 | 派遣员工 | 其他 |\n| --- | --- | --- | --- | --- |\n| 1984年 | 15.3 | 2.6 | — | 4.2 |\n"
    assert "let weights = (0, " in layout_tables(table, [])
    wide = "| 概念 | 内阁府 | 日本银行 | IMF | OECD |\n| --- | --- | --- | --- | --- |\n| 潜在GDP（增长率）的概念 | 在平均运营率下使用生产要素时可达成的GDP。 | 中期可持续的GDP。 | 产出。 | 产出。 |\n"
    assert "columns: (23fr, 30fr, 17fr, auto, auto)" in layout_tables(wide, [])


def test_a_span_marker_does_not_widen_its_column():
    table = '| 时间 | 总和 | 临时 | 合同工 | 其他 |\n| --- | --- | --- | --- | --- |\n| 1984年 | 15.3 | 2.6 | <span data-colspan="2">4.2</span> |  |\n| 2002年 | 29.4 | 6.8 | 4.7 | 2.5 |\n'
    assert "let weights = (0, 4, 3, 3, 3, )" in layout_tables(table, [])


def test_a_panel_label_stays_with_its_table():
    text = "（3）女性\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    out = layout_tables(text, [])
    assert "#block(sticky: true)[（3）女性]" in out
    sentence = "下表显示了各年的数值，供读者参考。\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    assert "sticky" not in layout_tables(sentence, [])
    heading = "==== 历史小组委员会\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    assert "sticky" not in layout_tables(heading, [])
    pagebreak = "@@PAGEBREAK@@ 续表\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    assert "sticky" not in layout_tables(pagebreak, [])


def test_a_stashed_table_keeps_its_label_on_its_page():
    out = layout_tables("（3）女性\n\n@@TABLEBLOCK0@@\n", [NUMBER_TABLE := "| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"])
    assert out.startswith("#block(sticky: true)[（3）女性]\n\n\n#align(center)[")
    assert "@@TABLEBLOCK" not in out and NUMBER_TABLE not in out


TEXT_TABLE = (
    "|  | 内阁府 | 日本银行 | IMF | OECD |\n| --- | --- | --- | --- | --- |\n"
    "| 潜在GDP的概念 | 在平均运营率下使用生产要素时可达成的GDP。 | 中期可持续发展的经济增长轨道和潜在水平。 "
    "| 可维持的不会使通货膨胀率上升的最大生产量。 | 不会使通货膨胀发生的可持续增长路径。 |\n"
)
NUMBER_TABLE = "| 时间 | 总和 | 男性 | 女性 |\n| --- | --- | --- | --- |\n| 1984年 | 15.3 | 7.7 | 29.0 |\n"
CAPTION = "#v(0.6em)\n#block(sticky: true, width: 100%)[#align(center)[#strong[表1-1 比较]]]\n#v(0.2em)"


def test_a_text_heavy_table_moves_to_a_landscape_page_with_its_caption_continuation_and_note():
    text = f"正文。\n\n{CAPTION}\n\n@@TABLEBLOCK0@@\n\n#block(sticky: true)[续表]\n\n@@TABLEBLOCK1@@\n\n注：根据内阁府制作。\n\n下一段正文。\n"
    out = layout_tables(text, [TEXT_TABLE, TEXT_TABLE])
    assert out.startswith(f"正文。\n\n#page(flipped: true)[\n#set table.cell(breakable: false)\n{CAPTION}\n\n\n#align(center)[")
    assert "\n]\n\n\n\n#block(sticky: true)[续表]\n\n\n#align(center)[" in out
    assert out.endswith("\n]\n\n\n\n注：根据内阁府制作。\n]\n\n下一段正文。\n")
    assert out.count("#table(") == 2


def test_prose_columns_read_left_aligned_with_a_rule_between_rows():
    out = layout_tables(TEXT_TABLE + TEXT_TABLE.splitlines()[2] + "\n", [], three_line=True)
    assert "align: (col, row) => if row < 1 { center + horizon } else { left + top },\n  inset: (x: 0.5em, y: 0.6em)," in out
    assert "else { (bottom: 0.3pt + luma(190)) }" in out
    assert "#set par(justify: false)\n#table(" in out
    assert "align: (col, row) => if col == 0" in layout_tables(NUMBER_TABLE, [], three_line=True)
    one = "| 年 | 说明 |\n| --- | --- |\n| 1991 | 综上所述，日本经济保持强劲的国内需求，企业盈利持续增长。 |\n"
    assert "else { left + top }" in layout_tables(one, [])


def test_column_panels_become_a_grid_with_the_notes_below_one_per_line():
    section = (
        f"{CAPTION}\n\n单位：%\n\n#block(sticky: true)[（1）男女总和]\n\n@@TABLEBLOCK0@@\n\n"
        "#block(sticky: true)[（2）男性]\n\n@@TABLEBLOCK1@@\n\n@@TABLEBLOCK2@@\n\n"
        "注：1. 数据是比例。\n2\\. 1984年起的数据。\n3. 根据总务省编制。\n\n"
    )
    out = layout_tables(f"@@FLIPPED3@@{section}@@FLIPPED0@@", [NUMBER_TABLE] * 3)
    assert out.startswith(
        f"@@FLIPPED1@@{CAPTION}\n\n单位：%\n\n"
        "#set table(inset: (x: 3pt, y: 1pt))\n#grid(columns: (1fr,) * 3, column-gutter: 1.5em,\n"
        "[#block(sticky: true)[（1）男女总和]\n\n\n#align(center)["
    )
    assert out.count("#table(") == 3
    assert out.endswith(
        "#block(above: 0.8em)[#set text(size: 8.5pt)\n#set par(first-line-indent: 0pt, leading: 0.55em)\n"
        "注：1. 数据是比例。\\\n2\\. 1984年起的数据。\\\n3. 根据总务省编制。]\n\n@@FLIPPED0@@"
    )
    scattered = "@@FLIPPED2@@正文。\n\n@@TABLEBLOCK0@@\n\n正文。\n\n@@TABLEBLOCK1@@\n@@FLIPPED0@@"
    out = layout_tables(scattered, [NUMBER_TABLE] * 2)
    assert out.startswith("@@FLIPPED2@@正文。") and "#grid(" not in out
    labelled = "单位：%\n\n#block(sticky: true)[（1）总和]\n\n@@TABLEBLOCK0@@\n\n#block(sticky: true)[（2）男性]\n\n@@TABLEBLOCK1@@\n"
    assert layout_tables(f"@@FLIPPED2@@{labelled}@@FLIPPED0@@", [NUMBER_TABLE] * 2).startswith(
        "@@FLIPPED1@@\n\n#set table(inset: (x: 3pt, y: 1pt))\n#grid(columns: (1fr,) * 2, column-gutter: 1.5em,\n"
        "[#block(sticky: true)[（1）总和#h(1fr)单位：%]\n\n\n#align(center)["
    )


def test_a_page_break_before_a_continuation_stays_inside_the_landscape_page():
    text = f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n@@PAGEBREAK@@ 续表\n\n@@TABLEBLOCK1@@\n\n正文。\n"
    out = layout_tables(text, [TEXT_TABLE, TEXT_TABLE])
    assert out.startswith("#page(flipped: true)[") and "@@PAGEBREAK@@" not in out
    assert "\n]\n\n\n\n#block(sticky: true)[续表]\n\n\n#align(center)[" in out
    assert out.endswith("\n]\n\n\n]\n\n正文。\n")


def test_a_wide_table_of_phrases_moves_to_a_landscape_page():
    wide = (
        "|  | 日期 | 内容 | 波动率 | 基准年 | 波动率 | 主要原因 |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        "| 1 | 1995年3月31日 | 引导市场利率走低（低于中央银行贴现率） | 0.2%（1995/02） | 1990年 | 0.1% | 担心物价过度下跌，从金融层面支持经济活动 |\n"
        "| 2 | 1995年4月14日 | 下调中央银行贴现率 | −0.2%（1995/05） | 1990年 | −0.1% | 金融对经济活动的支持 |\n"
    )
    text = f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n正文。\n"
    assert layout_tables(text, [wide]).startswith("#page(flipped: true)")
    assert "columns: (auto, 13fr, 30fr, 16fr, auto, auto, 30fr)," in layout_tables(wide, [], three_line=True)
    regression = (
        "| 变量 | (1) | (2) | (3) | (4) | (5) | (6) |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        "| 国内供需缺口 | 0.123***（0.045） | 0.118***（0.044） | 0.101**（0.047） | 0.097**（0.046） "
        "| 0.089*（0.049） | 0.085*（0.048） |\n"
    )
    assert "flipped" not in layout_tables(text, [regression])


def test_a_numeric_table_stays_upright():
    out = layout_tables(f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n注：数据。\n", [NUMBER_TABLE])
    assert out.startswith(f"{CAPTION}\n\n\n#align(center)[") and "flipped" not in out


def test_math_in_cells_keeps_its_subscripts():
    table = "|  | $P_h$ | a_b |\n| --- | --- | --- |\n| $Delta P_h$ | 1.0 | $x^*$ |\n"
    out = layout_tables(table, [])
    assert "[#strong[$P_h$]]" in out
    assert "[$Delta P_h$]" in out
    assert "[$x^*$]" in out
    assert r"[#strong[a\_b]]" in out


def test_a_continued_table_merges_with_its_preceding_table_and_drops_the_repeated_header():
    text = (
        "附表 1-1 进口渗透率\n\n单位：%\n\n"
        "| 年份 | 1980 | 1985 |\n| --- | --- | --- |\n| 制造业合计 | 5.41 | 5.53 |\n\n"
        "续表\n\n"
        "| 年份 | 1980 | 1985 |\n| --- | --- | --- |\n| 有机化学基础产品 | 1.32 | 1.23 |\n\n"
        "@@PAGEBREAK@@\n\n续表\n\n"
        "| 年份 | 1980 | 1985 |\n| --- | --- | --- |\n| 精密机械 | 1.20 | 12.01 |\n"
    )
    merged = merge_continued_tables(text)
    assert "续表" not in merged
    assert "@@PAGEBREAK@@" not in merged
    assert merged.count("| 年份 | 1980 | 1985 |") == 1
    out = layout_tables(text, [], three_line=True, merge_continued=True)
    assert out.count("#table(") == 1
    assert "[制造业合计]" in out and "[有机化学基础产品]" in out and "[精密机械]" in out
    assert layout_tables(text, [], three_line=True).count("#table(") == 3


def test_a_continued_table_without_repeated_headers_keeps_all_continuation_rows():
    text = (
        "| 时间 | 过程 |\n| --- | --- |\n| 1989年12月 | 股价峰值 |\n\n"
        "续表\n\n"
        "| 1991年9月 | 地价峰值 |\n| --- | --- |\n| 1992年8月 | 股价暴跌 |\n"
    )
    merged = merge_continued_tables(text)
    assert "续表" not in merged
    assert "| 1991年9月 | 地价峰值 |" in merged
    assert "| 1992年8月 | 股价暴跌 |" in merged


def test_a_page_that_opens_with_a_continued_table_splits_after_the_table_and_its_notes():
    page = "续表\n\n| 年 | 值 |\n| --- | --- |\n| 1990 | 1.0 |\n\n注：根据内阁府制作。\n资料来源：日本银行。\n\n正文接着说。\n"
    assert continued_table_split(page) == (
        "续表\n\n| 年 | 值 |\n| --- | --- |\n| 1990 | 1.0 |\n\n注：根据内阁府制作。\n资料来源：日本银行。",
        "正文接着说。\n",
    )
    assert continued_table_split("@@PAGEBREAK@@ 续表\n\n| 年 | 值 |\n| --- | --- |\n")[1] == ""
    assert continued_table_split("正文。\n\n续表\n\n| 年 | 值 |\n") is None
