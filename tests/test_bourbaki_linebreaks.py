from polytypst.bourbaki.linebreaks import Ending, insert_breaks, keep_fitting_breaks, last_line_fills, line_endings

FULL_LINE = "phisms of $A$-modules and the canonical map of $M$ into $S^{-1}M$ is injective"


def test_line_endings_keep_two_words_of_context_and_the_next_line_start():
    lines = ["Let A be a ring, B an", "A-algebra (not necessarily homo-", "morphism) and S a subset."]
    assert line_endings(lines) == [
        Ending("b", "an", "a", False, 7),
        Ending("necessarily", "homo", "morphism", True, 12),
    ]


def test_break_goes_after_trailing_punctuation_of_the_matched_word():
    body = "Let A be a ring, and B an algebra."
    assert insert_breaks(body, [Ending("a", "ring", "and", False, 5)]) == "Let A be a ring,@@BR@@and B an algebra."


def test_hyphenated_ending_splits_the_word_at_the_scan_hyphen():
    body = "a unique homomorphism j with"
    assert insert_breaks(body, [Ending("unique", "homo", "morphism", True, 3)]) == "a unique homo@@HY@@morphism j with"


def test_no_break_inside_math_or_across_a_paragraph_end():
    body = "where x $a in B$ is fixed.\n\nThen b is"
    endings = [Ending("a", "in", "b", False, 3), Ending("is", "fixed", "then", False, 5)]
    assert insert_breaks(body, endings) == body


def test_a_phrase_that_repeats_breaks_where_the_two_word_context_matches():
    body = "called in this case and in this way, called in this sense"
    endings = [Ending("and", "in", "this", False, 6)]
    assert insert_breaks(body, endings) == "called in this case and in@@BR@@this way, called in this sense"


def test_a_line_about_one_measure_wide_keeps_its_forced_break():
    body = f"x {FULL_LINE}@@BR@@the ring is noetherian."
    assert keep_fitting_breaks(body) == body


def test_a_forced_line_too_short_to_justify_drops_with_every_later_break_in_its_paragraph():
    body = f"x {FULL_LINE}@@BR@@Let A be@@BR@@a ring and homo@@HY@@morphism.\n\nx {FULL_LINE}@@BR@@end."
    assert keep_fitting_breaks(body) == (
        f"x {FULL_LINE}@@BR@@Let A be a ring and homomorphism.\n\nx {FULL_LINE}@@BR@@end."
    )


def test_a_line_too_wide_for_the_measure_drops_its_break():
    body = f"Then {FULL_LINE} and more words@@BR@@end."
    assert keep_fitting_breaks(body) == f"Then {FULL_LINE} and more words end."


def test_a_two_line_run_ending_part_way_along_its_second_line_drops_its_break():
    body = f"x {FULL_LINE} and more words in the group of G which is@@BR@@compatible."
    assert keep_fitting_breaks(body) == f"x {FULL_LINE} and more words in the group of G which is compatible."


def test_a_page_ending_on_a_full_forced_line_keeps_the_justified_end():
    assert last_line_fills(f"Text.\n\nx {FULL_LINE}@@BR@@x {FULL_LINE}")


def test_a_page_ending_part_way_along_its_last_line_does_not_justify_it():
    assert not last_line_fills(f"Text.\n\nx {FULL_LINE}@@BR@@compatible with the group structure")
