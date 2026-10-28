from polytypst import books_cli
from polytypst.figure_leaks import page_leaks

P416 = "就业形态的变化如图所示。\n\n□ 正规雇员\n\n■ 非正规雇员\n\n图 13-5 雇佣形态的推移\n\n此后非正规雇员的比率持续上升。\n"
P416_CROP = ["□正规雇员", "■非正规雇员", "图13-5雇佣形态的推移", "1990", "2007"]


def test_a_legend_copied_from_the_figure_crop_is_a_leak():
    assert [(line, text) for line, _, text in page_leaks(P416, P416_CROP)] == [(2, "□ 正规雇员"), (4, "■ 非正规雇员")]


def test_a_page_fixup_that_drops_the_legend_clears_the_leak():
    fixups = ((r"(?m)^[□■] \S+\n*", ""),)
    assert page_leaks(P416, P416_CROP, fixups) == []


def test_body_text_outside_the_crop_is_not_a_leak():
    assert page_leaks(P416, ["1990", "2007"]) == []


def test_rules_lists_the_figure_text_leak(capsys):
    assert books_cli.main("rules", []) == 0
    row = next(line.split() for line in capsys.readouterr().out.splitlines() if " FIGURE_TEXT_LEAK " in line)
    assert row[:4] == ["transcript", "FIGURE_TEXT_LEAK", "count", "audit"]
    assert row[4].startswith("src/figure_leaks.py:")
