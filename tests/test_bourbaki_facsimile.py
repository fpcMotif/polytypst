import numpy as np

from polytypst.bourbaki.facsimile import PT_PER_PX, align_words, line_baseline, segments


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
