import numpy as np

from polytypst.parity.words import PT_PER_PX, align_words, line_baseline, segments


def test_page_ink_ignores_a_readers_red_pen_but_keeps_black_print_under_it():
    import pymupdf

    from polytypst.parity.words import page_ink

    doc = pymupdf.open()
    page = doc.new_page(width=200, height=100)
    page.draw_line((10, 38), (180, 38), color=(0.85, 0.1, 0.1), width=3)
    page.draw_rect(pymupdf.Rect(20, 20, 120, 40), color=None, fill=(0, 0, 0))
    ink = page_ink(page)
    px = 1 / PT_PER_PX
    assert ink[round(30 * px), round(70 * px)]
    assert ink[round(38 * px), round(70 * px)]
    assert not ink[round(38 * px), round(150 * px)]


def test_page_ink_on_a_page_without_color_matches_mupdfs_gray_render():
    import pymupdf

    from polytypst.parity.words import INK_LEVEL, SCAN_DPI, page_ink

    doc = pymupdf.open()
    page = doc.new_page(width=200, height=100)
    for i, v in enumerate([0.2, 0.5, 0.54, 0.8]):
        page.insert_text((10, 20 + 20 * i), "gray ink abc", fontsize=14, color=(v, v, v))
    pix = page.get_pixmap(dpi=SCAN_DPI, colorspace=pymupdf.csGRAY)
    gray = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    assert np.array_equal(page_ink(page), gray < INK_LEVEL)


def test_align_words_merges_a_word_split_by_a_wide_letter_gap():
    segs = [(0, 10), (13, 20), (22, 33)]
    assert align_words([10, 20], 3, segs) == [(0, 10), (13, 33)]


def test_align_words_keeps_one_segment_per_word_when_counts_match():
    segs = [(0, 30), (40, 50), (60, 90)]
    assert align_words([30, 10, 30], 10, segs) == segs


def test_align_words_gives_up_when_there_are_fewer_segments_than_words():
    assert align_words([10, 10, 10], 3, [(0, 10), (13, 40)]) is None


def test_segments_split_only_at_gaps_of_word_space_width():
    ink = np.zeros((10, 100), bool)
    gap = round(0.9 / PT_PER_PX)
    ink[2:8, 0:10] = True
    ink[2:8, 11:20] = True
    ink[2:8, 20 + gap : 40] = True
    assert segments(ink, 0, 100, 0, 10) == [(0, 20), (20 + gap, 40)]


def test_line_baseline_is_bottom_of_the_dense_band_not_the_descenders():
    ink = np.zeros((30, 50), bool)
    ink[10:20, 0:50] = True
    ink[20:26, 0:3] = True
    assert line_baseline(ink, 0, 50, 0, 30) == 20
