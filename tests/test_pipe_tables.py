from polytypst.compiler.monograph import (
    format_pipe_tables_as_typst,
    panel_grid,
    rotate_text_tables,
)

TABLE = "| a | b |\n| :--- | :---: |\n| <mark>1.0</mark> | <b>2.0</b> |\n| <i>3.0<br>(4.0)</i> | 0.71** |\n"


def test_cell_tags_set_shading_bold_and_italic():
    out = format_pipe_tables_as_typst(TABLE)
    assert "table.cell(fill: luma(215))[1.0]" in out
    assert "[#strong[2.0]]" in out
    assert r"[#emph[3.0\ (4.0)]]" in out
    assert r"\<b" not in out and r"\<mark" not in out


def test_three_line_tables_fill_the_width_by_content_with_no_rules_between_rows():
    table = "| 职务 | 姓名 | 所属机构及职务 |\n| :--- | :--- | :--- |\n| 主任 | 香西 泰 | 日本经济研究中心特别研究顾问 |\n| 委员 | 伊藤 元重 | 东京大学研究生院经济学研究科教授 |\n"
    out = format_pipe_tables_as_typst(table, three_line=True)
    assert "columns: (4fr, 9fr, 30fr)" in out
    assert "luma(220)" not in out
    assert "else if y == 2 { (bottom: 1.0pt" in out
    assert "columns: 3," in format_pipe_tables_as_typst(table)


def test_asterisks_outside_tags_stay_literal():
    assert r"[0.71\*\*]" in format_pipe_tables_as_typst(TABLE)


def test_a_span_marker_centres_one_value_across_columns_in_a_data_row():
    table = '| 时间 | 总和 | 合同工 | 其他 |\n| :--- | :---: | :---: | :---: |\n| 1984年 | 15.3 | <span data-colspan="2">4.2</span> |  |\n'
    out = format_pipe_tables_as_typst(table)
    assert "[1984年], [15.3], table.cell(colspan: 2)[4.2]" in out
    assert "#strong[1984年]" not in out


def test_a_span_marker_keeps_the_cell_shading():
    table = '| a | b | c |\n| :--- | :---: | :---: |\n| x | <span data-colspan="2"><mark>1.0</mark></span> |  |\n'
    assert "table.cell(colspan: 2, fill: luma(215))[1.0]" in format_pipe_tables_as_typst(table)


def test_the_header_row_repeats_after_a_page_break():
    table = "| 时间 | 总和 | 男性 | 女性 | 其他 |\n| --- | --- | --- | --- | --- |\n| 1984年 | 15.3 | 7.7 | 29.0 | 4.2 |\n"
    out = format_pipe_tables_as_typst(table)
    assert "table.header([#strong[时间]], [#strong[总和]], [#strong[男性]], [#strong[女性]], [#strong[其他]]), [1984年]" in out


def test_a_two_level_header_repeats_both_rows():
    table = "|  | 日本 |  | 美国 |\n| --- | --- | --- | --- |\n|  | CPI | CGPI | CPI |\n| 电视 | 1.0 | 2.0 | 3.0 |\n"
    out = format_pipe_tables_as_typst(table)
    assert "table.header([], table.cell(colspan: 2)[#strong[日本]], [#strong[美国]], [], [#strong[CPI]], [#strong[CGPI]], [#strong[CPI]]), [电视]" in out


def test_a_numeric_column_lines_up_on_the_decimal_point():
    table = "| 年 | a | b | c | d |\n| --- | --- | --- | --- | --- |\n| x | 1.25 | 1 | 1 | 1 |\n| y | 10.5 | 2 | 2 | 2 |\n| z | −3 | 3 | 3 | 3 |\n"
    out = format_pipe_tables_as_typst(table)
    assert "[ 1.25]" in out
    assert "[10.5 ]" in out
    assert "[−3   ]" in out


def test_a_text_column_keeps_its_text():
    table = "| 年 | a | b | c | d |\n| --- | --- | --- | --- | --- |\n| x | 甲 | 1 | 1 | 1 |\n| y | 1.5 | 2 | 2 | 2 |\n| z | 乙 | 3 | 3 | 3 |\n"
    assert "[1.5]" in format_pipe_tables_as_typst(table)


def test_a_short_stub_column_fits_its_labels_and_long_columns_get_more_room():
    table = "| 时间 | 非正式雇员总和 | 临时员工 | 派遣员工 | 其他 |\n| --- | --- | --- | --- | --- |\n| 1984年 | 15.3 | 2.6 | — | 4.2 |\n"
    assert "columns: (auto, " in format_pipe_tables_as_typst(table)
    wide = "| 概念 | 内阁府 | 日本银行 | IMF | OECD |\n| --- | --- | --- | --- | --- |\n| 潜在GDP（增长率）的概念 | 在平均运营率下使用生产要素时可达成的GDP。 | 中期可持续的GDP。 | 产出。 | 产出。 |\n"
    assert "columns: (23fr, 30fr, 17fr, auto, auto)" in format_pipe_tables_as_typst(wide)


def test_a_span_marker_does_not_widen_its_column():
    table = '| 时间 | 总和 | 临时 | 合同工 | 其他 |\n| --- | --- | --- | --- | --- |\n| 1984年 | 15.3 | 2.6 | <span data-colspan="2">4.2</span> |  |\n| 2002年 | 29.4 | 6.8 | 4.7 | 2.5 |\n'
    assert "columns: (auto, 4fr, 3fr, 3fr, 3fr)" in format_pipe_tables_as_typst(table)


def test_a_panel_label_stays_with_its_table():
    text = "（3）女性\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    out = format_pipe_tables_as_typst(text)
    assert "#block(sticky: true)[（3）女性]" in out
    sentence = "下表显示了各年的数值，供读者参考。\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    assert "sticky" not in format_pipe_tables_as_typst(sentence)
    heading = "==== 历史小组委员会\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    assert "sticky" not in format_pipe_tables_as_typst(heading)
    pagebreak = "@@PAGEBREAK@@ 续表\n\n| 时间 | 总和 |\n| --- | --- |\n| 1984年 | 29.0 |\n"
    assert "sticky" not in format_pipe_tables_as_typst(pagebreak)


TEXT_TABLE = (
    "|  | 内阁府 | 日本银行 | IMF | OECD |\n| --- | --- | --- | --- | --- |\n"
    "| 潜在GDP的概念 | 在平均运营率下使用生产要素时可达成的GDP。 | 中期可持续发展的经济增长轨道和潜在水平。 "
    "| 可维持的不会使通货膨胀率上升的最大生产量。 | 不会使通货膨胀发生的可持续增长路径。 |\n"
)
NUMBER_TABLE = "| 时间 | 总和 | 男性 | 女性 |\n| --- | --- | --- | --- |\n| 1984年 | 15.3 | 7.7 | 29.0 |\n"
CAPTION = "#v(0.6em)\n#block(sticky: true, width: 100%)[#align(center)[#strong[表1-1 比较]]]\n#v(0.2em)"


def test_a_text_heavy_table_moves_to_a_landscape_page_with_its_caption_continuation_and_note():
    text = f"正文。\n\n{CAPTION}\n\n@@TABLEBLOCK0@@\n\n#block(sticky: true)[续表]\n\n@@TABLEBLOCK1@@\n\n注：根据内阁府制作。\n\n下一段正文。\n"
    out = rotate_text_tables(text, [TEXT_TABLE, TEXT_TABLE])
    assert f"正文。\n\n#page(flipped: true)[\n#set table.cell(breakable: false)\n{CAPTION}\n\n@@TABLEBLOCK0@@\n\n#block(sticky: true)[续表]\n\n@@TABLEBLOCK1@@\n\n注：根据内阁府制作。\n]\n\n下一段正文。" in out


def test_prose_columns_read_left_aligned_with_a_rule_between_rows():
    out = format_pipe_tables_as_typst(TEXT_TABLE + TEXT_TABLE.splitlines()[2] + "\n", three_line=True)
    assert "align: (col, row) => if row < 1 { center + horizon } else { left + top },\n  inset: (x: 0.5em, y: 0.6em)," in out
    assert "else { (bottom: 0.3pt + luma(190)) }" in out
    assert "#set par(justify: false)\n#table(" in out
    assert "align: (col, row) => if col == 0" in format_pipe_tables_as_typst(NUMBER_TABLE, three_line=True)
    one = "| 年 | 说明 |\n| --- | --- |\n| 1991 | 综上所述，日本经济保持强劲的国内需求，企业盈利持续增长。 |\n"
    assert "else { left + top }" in format_pipe_tables_as_typst(one)


def test_column_panels_become_a_grid_with_the_notes_below_one_per_line():
    section = (
        f"{CAPTION}\n\n单位：%\n\n#block(sticky: true)[（1）男女总和]\n\n@@TABLEBLOCK0@@\n\n"
        "#block(sticky: true)[（2）男性]\n\n@@TABLEBLOCK1@@\n\n@@TABLEBLOCK2@@\n\n"
        "注：1. 数据是比例。\n2\\. 1984年起的数据。\n3. 根据总务省编制。\n\n"
    )
    assert panel_grid(section, 3) == (
        f"{CAPTION}\n\n单位：%\n\n"
        "#set table(inset: (x: 3pt, y: 1pt))\n#grid(columns: (1fr,) * 3, column-gutter: 1.5em,\n"
        "[#block(sticky: true)[（1）男女总和]\n\n@@TABLEBLOCK0@@],\n"
        "[#block(sticky: true)[（2）男性]\n\n@@TABLEBLOCK1@@],\n"
        "[@@TABLEBLOCK2@@],\n)\n\n"
        "#block(above: 0.8em)[#set text(size: 8.5pt)\n#set par(first-line-indent: 0pt, leading: 0.55em)\n"
        "注：1. 数据是比例。\\\n2\\. 1984年起的数据。\\\n3. 根据总务省编制。]\n\n"
    )
    assert panel_grid("正文。\n\n@@TABLEBLOCK0@@\n\n正文。\n\n@@TABLEBLOCK1@@\n", 2) is None
    labelled = "单位：%\n\n#block(sticky: true)[（1）总和]\n\n@@TABLEBLOCK0@@\n\n#block(sticky: true)[（2）男性]\n\n@@TABLEBLOCK1@@\n"
    assert panel_grid(labelled, 2).startswith(
        "\n\n#set table(inset: (x: 3pt, y: 1pt))\n#grid(columns: (1fr,) * 2, column-gutter: 1.5em,\n"
        "[#block(sticky: true)[（1）总和#h(1fr)单位：%]\n\n@@TABLEBLOCK0@@],\n"
    )


def test_a_page_break_before_a_continuation_stays_inside_the_landscape_page():
    text = f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n@@PAGEBREAK@@ 续表\n\n@@TABLEBLOCK1@@\n\n正文。\n"
    out = rotate_text_tables(text, [TEXT_TABLE, TEXT_TABLE])
    assert out.startswith("#page(flipped: true)[") and "@@PAGEBREAK@@" not in out
    assert "#block(sticky: true)[续表]\n\n@@TABLEBLOCK1@@\n]\n\n正文。" in out


def test_a_wide_table_of_phrases_moves_to_a_landscape_page():
    wide = (
        "|  | 日期 | 内容 | 波动率 | 基准年 | 波动率 | 主要原因 |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        "| 1 | 1995年3月31日 | 引导市场利率走低（低于中央银行贴现率） | 0.2%（1995/02） | 1990年 | 0.1% | 担心物价过度下跌，从金融层面支持经济活动 |\n"
        "| 2 | 1995年4月14日 | 下调中央银行贴现率 | −0.2%（1995/05） | 1990年 | −0.1% | 金融对经济活动的支持 |\n"
    )
    text = f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n正文。\n"
    assert rotate_text_tables(text, [wide]).startswith("#page(flipped: true)")
    assert "columns: (auto, 13fr, 30fr, 16fr, auto, auto, 30fr)," in format_pipe_tables_as_typst(wide, three_line=True)
    regression = (
        "| 变量 | (1) | (2) | (3) | (4) | (5) | (6) |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        "| 国内供需缺口 | 0.123***（0.045） | 0.118***（0.044） | 0.101**（0.047） | 0.097**（0.046） "
        "| 0.089*（0.049） | 0.085*（0.048） |\n"
    )
    assert rotate_text_tables(text, [regression]) == text


def test_a_numeric_table_stays_upright():
    text = f"{CAPTION}\n\n@@TABLEBLOCK0@@\n\n注：数据。\n"
    assert rotate_text_tables(text, [NUMBER_TABLE]) == text


def test_math_in_cells_keeps_its_subscripts():
    table = "|  | $P_h$ | a_b |\n| --- | --- | --- |\n| $Delta P_h$ | 1.0 | $x^*$ |\n"
    out = format_pipe_tables_as_typst(table)
    assert "[#strong[$P_h$]]" in out
    assert "[$Delta P_h$]" in out
    assert "[$x^*$]" in out
    assert r"[#strong[a\_b]]" in out
