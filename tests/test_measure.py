import numpy as np

from polytypst.parity.measure import CELL, PageMeasure, page_measure, worse


def page(*boxes: tuple[int, int, int, int]) -> np.ndarray:
    ink = np.zeros((800, 600), bool)
    for top, left, bottom, right in boxes:
        ink[top:bottom, left:right] = True
    return ink


def test_a_rebuild_with_all_the_scan_ink_covers_the_page() -> None:
    scan = page((100, 100, 140, 300), (200, 100, 240, 300))
    measured = page_measure(scan, scan.copy(), 7)
    assert (measured.page, measured.coverage, measured.extra, measured.missing) == (7, 1.0, 0.0, 0.0)
    assert measured.misses == {}


def test_a_line_the_rebuild_lacks_is_an_uncovered_text_miss() -> None:
    scan = page((96, 96, 136, 296), (200, 96, 240, 296))
    built = page((96, 96, 136, 296))
    measured = page_measure(scan, built, 1)
    line_cells = (40 // CELL) * (200 // CELL)
    assert measured.coverage < 0.6
    assert measured.misses == {"text": line_cells}
    assert measured.missing > 0.4


def test_a_page_is_worse_when_coverage_falls_or_a_share_rises() -> None:
    old = PageMeasure(1, 0.98, 0.05, 0.05, 0.10)
    assert worse(PageMeasure(1, 0.98, 0.05, 0.05, 0.10), old) == []
    assert worse(PageMeasure(1, 0.99, 0.04, 0.04, 0.09), old) == []
    assert worse(PageMeasure(1, 0.97, 0.05, 0.05, 0.10), old) == ["coverage 0.98 -> 0.97"]
    assert worse(PageMeasure(1, 0.98, 0.06, 0.05, 0.12), old) == ["extra 0.05 -> 0.06", "layout 0.1 -> 0.12"]
