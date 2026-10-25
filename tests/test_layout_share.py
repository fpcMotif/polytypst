import numpy as np
import pytest

from polytypst.parity.visual import LAYOUT_LIMIT, layout_share


def text_block(top: int, pitch: int = 80, lines: int = 30) -> np.ndarray:
    ink = np.zeros((3600, 2400), dtype=bool)
    for row in range(top, top + pitch * lines, pitch):
        ink[row : row + 50, 300:2100] = True
    return ink


def test_the_same_page_has_no_layout_difference() -> None:
    assert layout_share(text_block(400), text_block(400)) == 0.0


def test_a_blank_rebuild_differs_in_every_inked_cell() -> None:
    assert layout_share(text_block(400), np.zeros((3600, 2400), dtype=bool)) == 1.0


def test_lines_set_half_a_line_lower_stay_under_the_limit() -> None:
    assert layout_share(text_block(400), text_block(440)) < LAYOUT_LIMIT


def test_a_rebuild_holding_the_top_third_of_the_text_goes_over_the_limit() -> None:
    assert layout_share(text_block(400), text_block(400, lines=10)) > LAYOUT_LIMIT


def test_a_rebuild_missing_the_last_third_of_the_text_goes_over_the_limit() -> None:
    assert layout_share(text_block(400), text_block(400, lines=20)) > LAYOUT_LIMIT


def test_layout_counts_cells_inked_on_one_page_over_cells_inked_on_either() -> None:
    scan = np.zeros((1200, 1200), dtype=bool)
    rebuilt = np.zeros((1200, 1200), dtype=bool)
    scan[0:100, 0:200] = True
    rebuilt[0:100, 100:300] = True
    assert layout_share(scan, rebuilt) == pytest.approx(2 / 3, abs=1e-4)
