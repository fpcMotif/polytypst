from pathlib import Path

import numpy as np
import pytest
from PIL import ImageFont

from polytypst.facsimile_lines import (
    ScanLine,
    TableCell,
    Unread,
    face_index,
    line_segments,
    main_band,
    order_lines,
    page_segments,
    place_unread,
    row_labels,
    rules_typst,
    set_line,
    split_unread,
    transcript_atoms,
    unread_bands,
)
from polytypst.facsimile_text import chunks
from polytypst.parity.words import PT_PER_PX

SONGTI = Path("/System/Library/Fonts/Supplemental/Songti.ttc")
pytestmark = pytest.mark.skipif(not SONGTI.exists(), reason="needs the Songti face")


def font() -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(SONGTI), 100, index=face_index(SONGTI, "Songti SC"))


def ink_line(text: str, size: float, spread: float = 1.0, left: float = 50.0, top: float = 100.0) -> ScanLine:
    l, t, r, b = font().getbbox(text, anchor="ls")
    return ScanLine(text, left, left + (r - l) * size / 100 * spread, top, top + (b - t) * size / 100)


def texts(segments) -> list[str]:
    return ["".join(a.text for a in seg) for seg in segments]


def test_the_face_is_the_regular_weight_typst_sets() -> None:
    assert font().getname() == ("Songti SC", "Regular")


def test_transcript_text_is_cut_where_the_scan_breaks_its_lines_even_where_the_ocr_drops_characters() -> None:
    atoms = transcript_atoms(chunks("甲的乙丙丁戊己"))
    lines = [ScanLine("甲乙丙", 0, 1, 0, 1), ScanLine("丁戊己", 0, 1, 2, 3)]
    assert texts(line_segments(atoms, lines)) == ["甲的乙丙", "丁戊己"]


def test_a_line_box_overlapping_its_neighbours_keeps_only_its_own_ink_rows() -> None:
    profile = np.array([0, 4, 4, 0, 0, 0, 0, 9, 9, 9, 9, 9, 0, 1, 9, 9, 0, 0, 0, 0, 5])
    assert main_band(profile) == (7, 16)


def test_a_table_rule_on_the_scan_is_drawn_as_a_line_and_a_rule_inside_a_figure_is_not() -> None:
    ink = np.zeros((1000, 1000), bool)
    ink[400:402, 100:700] = True
    ink[100:600, 800:802] = True
    ink[900:902, 100:700] = True
    out = rules_typst(ink, [(0.0, 900 * PT_PER_PX - 5, 1000 * PT_PER_PX, 1000 * PT_PER_PX)])
    assert len(out) == 2
    assert any("angle: 90deg" in o for o in out) and any(f"length: {600 * PT_PER_PX:.2f}pt" in o for o in out)


def test_a_skewed_rule_keeps_the_thickness_it_is_printed_at() -> None:
    ink = np.zeros((1000, 1000), bool)
    for k in range(5):
        ink[400 + 2 * k : 402 + 2 * k, 100 + 150 * k : 250 + 150 * k] = True
    out = rules_typst(ink, [])
    assert len(out) == 1 and f"stroke: {2 * PT_PER_PX:.2f}pt" in out[0]


def test_a_skewed_rule_keeps_its_end_steps_shorter_than_a_rule() -> None:
    ink = np.zeros((1000, 1000), bool)
    ink[400:402, 100:180] = True
    ink[402:404, 180:600] = True
    ink[404:406, 600:680] = True
    out = rules_typst(ink, [])
    assert len(out) == 1 and f"dx: {100 * PT_PER_PX:.2f}pt" in out[0] and f"length: {580 * PT_PER_PX:.2f}pt" in out[0]


def test_glyph_strokes_on_a_text_row_do_not_join_into_a_rule() -> None:
    ink = np.zeros((1000, 1000), bool)
    for k in range(12):
        ink[400:402, 100 + 50 * k : 140 + 50 * k] = True
    assert rules_typst(ink, []) == []


def table_lines(rows: list[list[tuple[str, float]]]) -> list[ScanLine]:
    return order_lines([ScanLine(t, x, x + 20, 100 + 20 * r, 108 + 20 * r) for r, row in enumerate(rows) for t, x in row])


def test_a_row_label_the_ocr_missed_is_cut_from_the_row_above_and_set_in_the_label_column() -> None:
    lines = table_lines([
        [("aq", 60), ("1.69", 150), ("3.32", 220)],
        [("0.20", 150), ("0.18", 220)],
        [("ex", 62), ("0.01", 150), ("0.12", 220)],
    ])
    segments = line_segments(transcript_atoms(chunks("aq 1.69 3.32 debt 0.20 0.18 ex 0.01 0.12")), lines)
    assert texts(segments)[2] == "3.32 debt"
    [(above, cut, row, left)] = row_labels(lines, segments, gap=20.0)
    assert (above, row, left) == (2, 3, 61.0)
    assert "".join(a.text for a in segments[above][cut:]).strip() == "debt"
    assert "".join(a.text for a in segments[above][:cut]).strip() == "3.32"


def flat_atoms(cells: list[TableCell]) -> list:
    return transcript_atoms(chunks(" ".join(c.text for c in sorted(cells, key=lambda c: (c.row, c.col)))))


def table_cut(cells: list[TableCell], lines: list[ScanLine]) -> tuple[list[str], list[tuple[str, tuple[float, ...]]]]:
    segments, unread = page_segments(flat_atoms(cells), lines, [cells])
    return texts(segments), [("".join(a.text for a in u.atoms), u.box) for u in unread]


def test_a_cell_printed_over_two_scan_lines_gives_each_line_its_own_part() -> None:
    cells = [TableCell(0, 0, 1, "aq"), TableCell(0, 1, 1, "48.9 (11.2)"), TableCell(0, 2, 1, "41.8 (15.8)")]
    lines = table_lines([[("aq", 60), ("48.9", 150), ("41.8", 220)], [("(11.2)", 150), ("(15.8)", 220)]])
    assert table_cut(cells, lines) == (["aq", "48.9", "41.8", "(11.2)", "(15.8)"], [])


def test_header_cells_wrapped_over_stacked_scan_lines_keep_their_own_text() -> None:
    cells = [TableCell(0, 0, 1, "甲乙丙丁"), TableCell(0, 1, 1, "戊己庚辛"), TableCell(1, 0, 1, "1"), TableCell(1, 1, 1, "2")]
    lines = table_lines([[("甲乙", 150), ("戊己", 220)], [("丙丁", 150), ("庚辛", 220)], [("1", 150), ("2", 220)]])
    assert table_cut(cells, lines) == (["甲乙", "戊己", "丙丁", "庚辛", "1", "2"], [])


def test_a_header_spanning_columns_is_cut_before_the_columns_under_it() -> None:
    cells = [TableCell(0, 0, 3, "人口变化"), TableCell(1, 0, 1, "劳动人口"), TableCell(1, 1, 1, "年龄结构"), TableCell(1, 2, 1, "参与率")]
    cells += [TableCell(2, k, 1, v) for k, v in enumerate(["1", "2", "3"])]
    body = table_lines([[], [("劳动", 150), ("年龄", 220), ("参与率", 290)], [("人口", 150), ("结构", 220)], [("1", 150), ("2", 220), ("3", 290)]])
    lines = order_lines([ScanLine("人口变化", 200, 300, 100, 108), *body])
    assert table_cut(cells, lines)[0] == ["人口变化", "劳动", "年龄", "参与率", "人口", "结构", "1", "2", "3"]


def test_headers_the_ocr_read_as_one_line_give_it_their_cells() -> None:
    cells = [TableCell(0, 0, 1, "其中甲"), TableCell(0, 1, 1, "其中乙"), TableCell(1, 0, 1, "1"), TableCell(1, 1, 1, "2"), TableCell(2, 0, 1, "3"), TableCell(2, 1, 1, "4")]
    body = table_lines([[], [("1", 150), ("2", 220)], [("3", 150), ("4", 220)]])
    lines = order_lines([ScanLine("其中甲 其中乙", 150, 240, 100, 108), *body])
    assert table_cut(cells, lines) == (["其中甲 其中乙", "1", "2", "3", "4"], [])


def test_unread_text_with_no_ink_of_its_own_joins_the_read_line_it_follows() -> None:
    line = ScanLine("1995-", 10, 40, 10, 18)
    ink = np.zeros((200, 200), bool)
    segments = [transcript_atoms(chunks("1995")), []]
    unread = [Unread(tuple(transcript_atoms(chunks("—"))), (10, 10, 40, 18), 0, True), Unread(tuple(transcript_atoms(chunks("x"))), (10, 10, 40, 18), 1, True)]
    placed, dropped = place_unread(ink, unread, [line], segments, 4.0)
    assert placed == [] and texts(segments) == ["1995—", ""] and dropped == unread[1:]

def test_a_cell_the_ocr_missed_before_the_first_column_read_joins_no_line() -> None:
    cells = [TableCell(0, 0, 1, "出口主体"), TableCell(0, 1, 1, "亚洲"), TableCell(0, 2, 1, "48.9")]
    lines = table_lines([[("亚洲", 150), ("48.9", 220)]])
    assert table_cut(cells, lines) == (["亚洲", "48.9"], [])


def test_a_line_the_ocr_misreads_takes_its_whole_cell() -> None:
    cells = [TableCell(r, 0, 1, t) for r, t in enumerate(["NAFTA", "欧洲", "其他"])]
    lines = table_lines([[("NAFTA", 150)], [("欭洲", 150)], [("其他", 150)]])
    assert table_cut(cells, lines) == (["NAFTA", "欧洲", "其他"], [])


def test_cell_text_between_two_read_lines_of_its_cell_is_unread_between_them() -> None:
    cells = [TableCell(0, 0, 1, "甲乙丙丁"), TableCell(0, 1, 1, "戊"), TableCell(1, 0, 1, "1"), TableCell(1, 1, 1, "2")]
    lines = table_lines([[("甲", 150), ("戊", 220)], [], [("丁", 150)], [("1", 150), ("2", 220)]])
    cut, [(text, (left, top, right, bottom))] = table_cut(cells, lines)
    assert cut == ["甲", "戊", "丁", "1", "2"]
    assert text == "乙丙" and (top, bottom) == (100, 148) and left < 150 and 170 < right < 220


def test_a_cell_the_ocr_missed_is_unread_above_the_first_read_line_of_its_column() -> None:
    cells = [TableCell(0, 0, 1, "甲"), TableCell(0, 1, 1, "乙丙"), TableCell(1, 0, 1, "1"), TableCell(1, 1, 1, "2")]
    lines = table_lines([[("甲", 150)], [("1", 150), ("2", 220)]])
    cut, [(text, box)] = table_cut(cells, lines)
    assert cut == ["甲", "1", "2"]
    left, top, right, bottom = box
    assert text == "乙丙" and (left, top, bottom) == pytest.approx((170, 100 - 0.3 * 8, 108 + 0.3 * 8)) and right > 240


def test_a_row_label_the_ocr_missed_in_a_table_cut_by_columns_is_unread_in_the_label_column() -> None:
    cells = [TableCell(r, c, 1, v) for r, row in enumerate([["aq", "1.69", "3.32"], ["debt", "0.20", "0.18"], ["ex", "0.01", "0.12"]]) for c, v in enumerate(row)]
    lines = table_lines([
        [("aq", 60), ("1.69", 150), ("3.32", 220)],
        [("0.20", 150), ("0.18", 220)],
        [("ex", 62), ("0.01", 150), ("0.12", 220)],
    ])
    cut, [(text, (left, top, right, bottom))] = table_cut(cells, lines)
    assert cut == ["aq", "1.69", "3.32", "0.20", "0.18", "ex", "0.01", "0.12"]
    assert text == "debt" and (top, bottom) == pytest.approx((120 - 0.3 * 8, 128 + 0.3 * 8)) and left < 60 and right == 150


def test_a_line_the_ocr_misread_out_of_its_column_takes_the_cell_it_reads() -> None:
    cells = [TableCell(r, c, 1, v) for r, row in enumerate([["Variable", "Mean"], ["aq", "1.69"], ["cf", "0.22"]]) for c, v in enumerate(row)]
    lines = table_lines([[("Varable", 80), ("Mean", 150)], [("aq", 58), ("1.69", 150)], [("cf", 58), ("0.22", 150)]])
    assert table_cut(cells, lines) == (["Variable", "Mean", "aq", "1.69", "cf", "0.22"], [])


def test_a_header_spanning_columns_on_a_narrow_line_leaves_the_column_under_it_to_its_own_cells() -> None:
    cells = [TableCell(0, 0, 2, "项目"), TableCell(1, 0, 1, "男性", 2), TableCell(1, 1, 1, "1980"), TableCell(2, 1, 1, "1985")]
    lines = table_lines([[("项目", 85)], [("男", 40), ("1980", 80)], [("性", 40), ("1985", 80)]])
    assert table_cut(cells, lines)[0] == ["项目", "男", "1980", "性", "1985"]


def test_unread_ink_bands_skip_read_lines_and_rules() -> None:
    ink = np.zeros((400, 400), bool)
    px = 1 / PT_PER_PX
    read = ScanLine("甲", 10, 30, 10, 20)
    ink[int(10 * px) : int(20 * px), int(10 * px) : int(30 * px)] = True
    ink[int(24 * px) : int(32 * px), int(12 * px) : int(28 * px) : 3] = True
    ink[int(32 * px) + 1, 0:400] = True
    ink[int(40 * px) : int(48 * px), int(12 * px) : int(20 * px) : 3] = True
    bands = unread_bands(ink, (0, 0, 400 * PT_PER_PX, 400 * PT_PER_PX), [read], 4.0)
    assert [(b.top, b.bottom) for b in bands] == [pytest.approx((24, 32), abs=0.3), pytest.approx((40, 48), abs=0.3)]


def test_unread_text_is_shared_over_its_bands_by_ink_width() -> None:
    bands = [ScanLine("", 0, 10, 0, 8), ScanLine("", 0, 20, 10, 18), ScanLine("", 0, 10, 20, 28)]
    out = split_unread(transcript_atoms(chunks("甲乙丙丁")), bands)
    assert [("".join(a.text for a in seg), band.top) for seg, band in out] == [("甲", 0), ("乙丙", 10), ("丁", 20)]


def test_unread_text_with_fewer_characters_than_bands_takes_the_widest_bands() -> None:
    bands = [ScanLine("", 0, 10, 0, 8), ScanLine("", 0, 2, 10, 18), ScanLine("", 0, 10, 20, 28)]
    out = split_unread(transcript_atoms(chunks("甲乙")), bands)
    assert [("".join(a.text for a in seg), band.top) for seg, band in out] == [("甲", 0), ("乙", 20)]


def test_a_row_that_starts_with_text_gets_no_row_label() -> None:
    lines = table_lines([
        [("主席", 60), ("伊藤元重", 150), ("东京大学教授", 220)],
        [("浦田秀次郎", 150), ("早稻田大学教授", 220)],
    ])
    segments = line_segments(transcript_atoms(chunks("主席 伊藤元重 东京大学教授 委员 浦田秀次郎 早稻田大学教授")), lines)
    assert row_labels(lines, segments, gap=20.0) == []


def test_prose_lines_get_no_row_labels() -> None:
    lines = table_lines([[("这一点，借款余额占总资产的比例", 60)], [("生产率，这是一个解释变量", 60)]])
    segments = line_segments(transcript_atoms(chunks("这一点，借款余额占总资产的比例和三大股东 生产率，这是一个解释变量")), lines)
    assert row_labels(lines, segments, gap=20.0) == []


def test_cells_on_one_row_read_left_to_right_before_the_next_row() -> None:
    right, left, below = ScanLine("b", 200, 220, 10, 20), ScanLine("a", 50, 70, 11, 21), ScanLine("c", 50, 70, 40, 50)
    assert [ln.text for ln in order_lines([below, right, left])] == ["a", "b", "c"]


def test_a_line_is_set_at_the_size_its_ink_shows_and_spread_to_its_ink_width() -> None:
    text = "家庭储蓄行为的主要特点及其变化"
    line = ink_line(text, 10.7, spread=1.03)
    out = set_line(transcript_atoms(chunks(text)), line, font(), 9.0, {})
    assert out.mismatch is None
    assert out.size == pytest.approx(10.7, abs=0.05)
    assert out.tracking > 0
    assert "scale(" not in out.typst and "fit(" not in out.typst


def test_a_line_near_the_page_size_takes_the_page_size_and_closes_up_to_a_narrower_ink_width() -> None:
    text = "家庭储蓄行为的主要特点及其变化"
    out = set_line(transcript_atoms(chunks(text)), ink_line(text, 10.6, spread=0.92), font(), 10.5, {})
    assert out.mismatch is None
    assert out.size == pytest.approx(10.5)
    assert out.tracking < 0
    assert "scale(" not in out.typst and "fit(" not in out.typst


def test_a_narrower_latin_line_is_set_smaller_and_keeps_its_word_spaces() -> None:
    text = "Review of Economics and Statistics"
    out = set_line(transcript_atoms(chunks(text)), ink_line(text, 10.5, spread=0.92), font(), 10.5, {})
    assert out.mismatch is None and out.tracking == pytest.approx(0, abs=0.01)
    assert out.size == pytest.approx(10.5 * 0.92, abs=0.05)
    assert "spacing: 100% + 0.000pt" in out.typst


def test_a_line_running_down_a_sideways_page_is_set_upright_and_turned() -> None:
    text = "家庭储蓄行为"
    across = ink_line(text, 10.7)
    down = ScanLine(text, across.top, across.top + (across.bottom - across.top), across.left, across.right)
    out = set_line(transcript_atoms(chunks(text)), down, font(), 10.7, {})
    assert out.mismatch is None and "rotate(-90deg" in out.typst


def test_sideways_columns_read_left_to_right_and_each_column_bottom_to_top() -> None:
    low, high, next_column = ScanLine("a", 10, 20, 300, 400), ScanLine("b", 11, 21, 100, 200), ScanLine("c", 40, 50, 300, 400)
    assert [ln.text for ln in order_lines([next_column, high, low])] == ["a", "b", "c"]


def test_a_line_whose_transcript_is_far_wider_than_its_ink_is_reported_and_never_squeezed() -> None:
    line = ink_line("家庭储蓄", 10.7)
    out = set_line(transcript_atoms(chunks("家庭储蓄行为的主要特点")), line, font(), 10.7, {})
    assert out.mismatch == "width"
    assert out.size == pytest.approx(10.7) and out.tracking == 0
    assert "scale(" not in out.typst and "fit(" not in out.typst
