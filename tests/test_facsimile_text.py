from polytypst.facsimile_text import Piece, Unit, chunks, match_units


def test_chunks_split_at_spaces_and_keep_math_emphasis_and_headings():
    assert chunks(
        "# Titre\n\n*Ens* la $u: Y \\to Y'$ catégorie$^{(1)}$;\n\n$$x = 0$$"
    ) == [
        (Piece("text", "Titre", "bold"),),
        (Piece("text", "Ens", "italic"),),
        (Piece("text", "la"),),
        (Piece("math", "u: Y \\to Y'"),),
        (Piece("text", "catégorie"), Piece("math", "^{(1)}"), Piece("text", ";")),
        (Piece("display", "x = 0"),),
    ]


def test_a_hyphen_before_a_space_and_inline_math_stays_one_chunk_as_the_scan_prints_it():
    assert chunks("ses sous- $A$-modules de") == [
        (Piece("text", "ses"),),
        (Piece("text", "sous-"), Piece("math", "A"), Piece("text", "-modules")),
        (Piece("text", "de"),),
    ]


def test_math_the_line_reader_misread_takes_the_scan_word_between_its_neighbours():
    cs = chunks("de $\\mathcal{F}$ sur $u(\\mathcal{F})$")
    assert match_units(cs, ["de", "&", "sur", "u(F)"], [0, 0, 0, 0]) == [
        Unit((0,), (0,)),
        Unit((1,), (1,)),
        Unit((2,), (2,)),
        Unit((3,), (3,)),
    ]


def test_a_display_that_ends_the_page_takes_the_free_line_after_the_prose():
    cs = chunks("on a et\n\n$$\\mathrm{Hom}(1_T, \\psi)$$")
    units = match_units(cs, ["on", "a", "et", "Hom(IT,", "V)"], [0, 0, 0, 1, 1])
    assert Unit((2,), (2,)) in units
    assert Unit((3,), (3, 4)) in units


def test_a_display_that_opens_the_page_takes_the_free_line_before_the_prose_not_the_running_head():
    cs = chunks("$$\\Psi_*(M) \\to N$$\n\n(4.2.2.2) est commutatif.")
    words = ["§", "4.", "Espaces", "95", "", "(4.2.2.2)", "est", "commutatif."]
    units = match_units(cs, words, [0, 0, 0, 0, 1, 2, 3, 3])
    assert Unit((0,), (4,)) in units
    assert Unit((1,), (5,)) in units


def test_a_display_shares_its_row_with_its_equation_number():
    cs = chunks("avec l'ensemble\n\n(9.8.4.5)\n\n$$\\prod_i H$$\n\nSi l'on")
    words = ["avec", "l'ensemble", "(9.8.4.5)", "I", "Homes", "", "Si", "l'on"]
    units = match_units(cs, words, [0, 0, 1, 1, 1, 2, 3, 3])
    assert Unit((2,), (2,)) in units
    assert Unit((3,), (3, 4, 5)) in units


def test_a_display_above_its_lower_set_equation_number_keeps_its_row():
    cs = chunks(
        "le morphisme canonique\n\n(3.2.7.2) $$g = g_1$$\n\n$$Z = X$$\n\nest un"
    )
    words = ["le", "morphisme", "canonique", "9=91", "(3.2.7.2)", "Z=X", "est", "un"]
    units = match_units(cs, words, [0, 0, 0, 1, 2, 3, 4, 4])
    assert Unit((3,), (4,)) in units
    assert Unit((4,), (3,)) in units
    assert Unit((5,), (5,)) in units


def test_a_display_takes_the_whole_lines_between_the_prose_around_it():
    cs = chunks("on a\n\n$$\\sum d_n = 0$$\n\ndonc")
    units = match_units(cs, ["on", "a", "dn", "", "donc"], [0, 0, 1, 2, 3])
    assert Unit((2,), (2, 3)) in units
    assert Unit((3,), (4,)) in units
