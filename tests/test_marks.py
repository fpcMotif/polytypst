from dataclasses import replace
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from polytypst.compiler import marks
from polytypst.compiler.monograph import MonographCompiler, adhoc_spec

PROSE = st.text(st.characters(codec="utf-8", exclude_characters="@\\#$*_[]`<>\n\r"), min_size=1, max_size=12).map(str.strip).filter(bool)
LINE = st.text(st.characters(codec="utf-8", exclude_characters="@\n\r"), min_size=1, max_size=12).map(str.strip).filter(bool)
PAGE = st.integers(min_value=1, max_value=999)

MARKED_BLOCKS = st.one_of(
    PROSE,
    st.just(marks.PAGE_BREAK),
    st.integers(min_value=0, max_value=4).map(marks.landscape),
    LINE.map(marks.subtitle),
    LINE.map(marks.byline),
    st.tuples(LINE, PROSE).map(lambda t: marks.contents_line(t[0], t[1].count(" ") + 1)),
    LINE.map(marks.contents_head),
    st.lists(PROSE, min_size=1, max_size=3).map(lambda blocks: "\n\n".join(marks.abstract("", blocks))),
)
CHAPTER = st.lists(MARKED_BLOCKS, min_size=1, max_size=8).map("\n\n".join)
PAGINATED = st.lists(
    st.one_of(
        PROSE,
        PAGE.map(marks.source_page),
        PAGE.map(marks.page_top),
        PAGE.map(marks.page_end),
        st.sampled_from([marks.NO_INDENT, marks.JUSTIFY_END, marks.LINE_BREAK, marks.HYPHEN_BREAK, marks.PAGE_BREAK]),
    ),
    min_size=1,
    max_size=8,
).map(" ".join)


@pytest.mark.slow
@given(CHAPTER)
def test_no_marker_survives_the_markdown_writer(text):
    assert "@@" not in marks.to_markdown(text)


@pytest.mark.slow
@given(CHAPTER, st.booleans())
def test_no_marker_survives_the_typst_writer(text, paginate):
    assert "@@" not in marks.to_typst(text, paginate=paginate)


@pytest.mark.slow
@given(PAGINATED)
def test_no_source_page_marker_survives_a_paginated_typst_writer(text):
    assert "@@" not in marks.to_typst(text, paginate=True)


@pytest.mark.slow
@given(CHAPTER)
def test_the_markdown_writer_is_idempotent(text):
    once = marks.to_markdown(text)
    assert marks.to_markdown(once) == once


@pytest.mark.slow
@given(st.one_of(CHAPTER, PAGINATED), st.booleans())
def test_the_typst_writer_is_idempotent(text, paginate):
    once = marks.to_typst(text, paginate=paginate)
    assert marks.to_typst(once, paginate=paginate) == once


@given(PROSE)
def test_a_footnote_round_trips_through_its_pattern(body):
    assert marks.FOOTNOTE_RE.fullmatch(marks.footnote(body))[1] == body


def test_chapter_opening_marks_become_the_preamble_calls_of_a_chapter_style():
    opening = "\n\n".join(
        [marks.subtitle("——财政赤字"), marks.byline("土居丈朗"), *marks.abstract("", ["本文分析地方财政。"])]
    )
    assert marks.to_typst(opening, paginate=False) == (
        "#chapter-subtitle[——财政赤字]\n\n#chapter-byline[土居丈朗]\n\n#chapter-abstract(note: [])[\n\n本文分析地方财政。\n\n]"
    )


def test_chapter_opening_marks_keep_their_text_in_markdown():
    opening = "\n\n".join(
        [marks.subtitle("——财政赤字"), marks.byline("土居丈朗"), *marks.abstract("", ["本文分析地方财政。"])]
    )
    assert marks.to_markdown(opening) == "*——财政赤字*\n\n土居丈朗\n\n\n\n本文分析地方财政。\n\n"


def test_contents_marks_become_contents_lines_in_typst_and_plain_lines_in_markdown():
    text = marks.contents_head("Part I") + "\n\n" + marks.contents_line("Analysis of flat surfaces", 235)
    assert marks.to_typst(text, paginate=False) == '#contents-head[Part I]\n\n#contents-line("235")[Analysis of flat surfaces]'
    assert marks.to_markdown(text) == "Part I\n\nAnalysis of flat surfaces 235"


def test_a_page_break_breaks_the_page_only_in_a_book_set_page_by_page():
    text = f"First.\n\n{marks.PAGE_BREAK}\n\nSecond."
    assert marks.to_typst(text, paginate=True) == "First.\n\n\n#pagebreak()\n\n\nSecond."
    assert marks.to_typst(text, paginate=False) == "First.\n\nSecond."
    assert marks.to_markdown(text) == "First.\n\nSecond."


def test_a_landscape_run_turns_the_page_and_shrinks_its_text_until_the_page_turns_back():
    text = f"{marks.landscape(2)}\n\n#set text(size: 10pt)\n\n{marks.landscape(0)}\n\nAfter."
    assert marks.to_typst(text, paginate=False) == (
        "\n#set page(flipped: true, columns: 2)\n#set table(inset: (x: 4pt, y: 1.6pt))\n\n\n#set text(size: 8.00pt)\n\n"
        "\n#set page(flipped: false, columns: 1)\n#set table(inset: 5pt)\n\n\nAfter."
    )
    assert marks.to_markdown(text) == "\n\n#set text(size: 10pt)\n\nAfter."


CODE_CALL = st.from_regex(r"[a-z_]{1,8}\([a-z0-9, =]{0,10}\)", fullmatch=True)
CJK = st.text(st.characters(min_codepoint=0x4E00, max_codepoint=0x9FFF), min_size=2, max_size=12)
CIRCLED_SPEC = replace(adhoc_spec(Path("Probe.pdf"), 1, lang="zh"), footnote_style="circled", footnote_numbering="circled")


@pytest.mark.slow
@given(st.lists(st.tuples(CODE_CALL, CJK), min_size=1, max_size=4), CJK, st.booleans())
def test_no_marker_survives_typst_when_a_code_block_holds_circled_callouts(callouts, prose, code_after):
    circled = "①②③④"
    code = "\n".join(f"{call} {circled[i]}" for i, (call, _) in enumerate(callouts))
    listing = "\n\n".join(f"{circled[i]} {call}\n{text}。" for i, (call, text) in enumerate(callouts))
    page = f"```python\n{code}\n```\n\n{prose}。\n\n{listing}\n\n{prose}。\n"
    if code_after:
        page += "\n```python\nN = 500\n```\n"
    compiler = MonographCompiler(CIRCLED_SPEC)
    assert "@@" not in compiler.format_typst(compiler.cleaner.clean(page, 1).body)
