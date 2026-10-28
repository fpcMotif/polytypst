from polytypst.compiler.monograph import format_pipe_tables_as_typst

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


def test_math_in_cells_keeps_its_subscripts():
    table = "|  | $P_h$ | a_b |\n| --- | --- | --- |\n| $Delta P_h$ | 1.0 | $x^*$ |\n"
    out = format_pipe_tables_as_typst(table)
    assert "[#strong[$P_h$]]" in out
    assert "[$Delta P_h$]" in out
    assert "[$x^*$]" in out
    assert r"[#strong[a\_b]]" in out
