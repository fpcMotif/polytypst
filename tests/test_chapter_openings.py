from polytypst.compiler.monograph import mark_chapter_opening


def test_the_byline_and_the_abstract_before_section_1_are_marked():
    chapter = "大竹文雄 小原美纪\n\n### 导 语\n\n本文分析收入差距。\n\n第一，老龄化。\n\n## 1 前言\n\n正文。"
    assert mark_chapter_opening(chapter) == (
        "@@BYLINE@@ 大竹文雄 小原美纪\n\n@@ABSTRACT@@\n\n本文分析收入差距。\n\n第一，老龄化。\n\n@@ENDABSTRACT@@\n\n## 1 前言\n\n正文。"
    )


def test_a_subtitle_written_as_a_heading_and_a_byline_with_a_note_are_marked():
    chapter = "### ——财政赤字与地区差距\n\n土居丈朗^[感谢。]\n\n本文分析地方财政。\n\n### 1 前言\n\n正文。"
    assert mark_chapter_opening(chapter) == (
        "@@SUBTITLE@@ ——财政赤字与地区差距\n\n@@BYLINE@@ 土居丈朗^[感谢。]\n\n"
        "@@ABSTRACT@@\n\n本文分析地方财政。\n\n@@ENDABSTRACT@@\n\n### 1 前言\n\n正文。"
    )


def test_a_byline_written_as_a_heading_is_not_taken_for_the_first_section():
    chapter = "### 三谷直纪\n\n本文分析工资结构。\n\n## 1 前言\n\n正文。"
    assert mark_chapter_opening(chapter).startswith("@@BYLINE@@ 三谷直纪\n\n@@ABSTRACT@@\n\n本文分析工资结构。")


def test_an_opening_whose_section_1_heading_is_lost_marks_no_abstract():
    chapter = "龟田启悟\n\n本文验证非凯恩斯效应。\n\n引言第一段。\n\n### 2 非凯恩斯效应的发生条件\n\n正文。"
    assert mark_chapter_opening(chapter) == (
        "@@BYLINE@@ 龟田启悟\n\n本文验证非凯恩斯效应。\n\n引言第一段。\n\n### 2 非凯恩斯效应的发生条件\n\n正文。"
    )


def test_a_chapter_without_a_byline_is_left_as_written():
    chapter = "本书的目的在于回顾。\n\n## 1 前言\n\n正文。"
    assert mark_chapter_opening(chapter) == chapter
