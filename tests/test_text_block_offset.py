import numpy as np
import pytest

from polytypst.parity.visual import page_visual, text_block_shift
from polytypst.parity.words import PT_PER_PX, without_edge_lines


def px(pt: float) -> int:
    return round(pt / PT_PER_PX)


def block(left: float = 60.0, top: float = 80.0, lines: int = 30) -> np.ndarray:
    ink = np.zeros((px(860), px(600)), dtype=bool)
    for k in range(lines):
        y = top + 20 * k
        ink[px(y) : px(y + 10), px(left) : px(left + 420)] = True
    return ink


def test_the_same_page_has_no_shift() -> None:
    assert text_block_shift(block(), block()) == (0.0, 0.0, 0.0, 0.0)


def test_a_block_set_20pt_right_and_10pt_lower_shifts_by_those_amounts() -> None:
    left, top, right, bottom = text_block_shift(block(), block(left=80.0, top=90.0))
    assert (left, top, right, bottom) == pytest.approx((20.0, 10.0, 20.0, 10.0), abs=0.5)


def test_a_scan_border_line_does_not_move_the_text_block_edge() -> None:
    scan = block()
    scan[:, 0:2] = True
    assert text_block_shift(scan, block()) == pytest.approx((0.0, 0.0, 0.0, 0.0), abs=0.5)


def test_edge_lines_are_columns_inked_down_most_of_the_page() -> None:
    scan = block()
    scan[:, 0:2] = True
    cleaned = without_edge_lines(scan)
    assert not cleaned[:, 0:2].any()
    assert (cleaned == block()).all()


def test_a_broken_line_along_the_page_side_is_an_edge_line() -> None:
    scan = block()
    scan[::40, 0:8] = True
    scan[::40, -6:] = True
    assert (without_edge_lines(scan) == block()).all()


def test_text_near_the_page_side_is_kept() -> None:
    scan = block(left=8.0)
    assert (without_edge_lines(scan) == scan).all()


def test_lighter_ink_in_the_same_place_does_not_shift_the_block() -> None:
    scan = block()
    scan[px(30) : px(42), px(200) : px(400)] = True
    rebuilt = block()
    rebuilt[px(30) : px(42), px(200) : px(400) : 4] = True
    assert text_block_shift(scan, rebuilt) == pytest.approx((0.0, 0.0, 0.0, 0.0), abs=0.5)


def test_one_indented_line_does_not_move_the_left_edge() -> None:
    rebuilt = block()
    rebuilt[px(80) : px(90), px(60) : px(90)] = False
    assert text_block_shift(block(), rebuilt) == pytest.approx((0.0, 0.0, 0.0, 0.0), abs=0.5)


def test_short_lines_on_both_pages_do_not_move_the_right_edge() -> None:
    scan, rebuilt = block(), block()
    for k in range(27):
        y = 80 + 20 * k
        scan[px(y) : px(y + 10), px(300) : px(480)] = False
        rebuilt[px(y) : px(y + 10), px(200 + 5 * k) : px(480)] = False
    assert text_block_shift(scan, rebuilt)[2] == pytest.approx(0.0, abs=0.5)


def test_specks_past_short_lines_do_not_move_the_right_edge() -> None:
    scan, rebuilt = block(lines=4), block(lines=4)
    for page in (scan, rebuilt):
        page[px(80) : px(150), px(200) : px(480)] = False
    for y in (82, 102, 122):
        scan[px(y) : px(y) + 3, px(560) : px(560) + 3] = True
    assert text_block_shift(scan, rebuilt)[2] == pytest.approx(0.0, abs=0.5)


def test_the_page_offset_is_the_largest_edge_shift() -> None:
    page = page_visual(block(), block(left=63.0, top=80.0, lines=25), 1, 1)
    assert page.shift[0] == pytest.approx(3.0, abs=0.5)
    assert page.offset == pytest.approx(100.0, abs=1.0)
