from polytypst.compiler.monograph import prose_displays_to_paragraphs

KASHIWARA_P117 = (
    r"$$((x_1, x_2), \sqrt{-1}(\xi_1, \xi_2)\infty) \notin \overline{\mathrm{S.S.}} f_1(f_2 - \tilde{f}_2)"
    r" \text{ holds; i.e. } \mathrm{sp} f_1(f_2 - \tilde{f}_2) = 0 \text{ at } ((x_1, x_2), \sqrt{-1}(\xi_1, \xi_2)\infty)."
    r" \text{ In a similar manner, one obtains } \mathrm{sp} f_1 f_2 = 0."
    "\n\n*Remark.* We proved Theorem 3.1.2 locally."
)


def test_unclosed_display_of_prose_becomes_a_paragraph_with_inline_math():
    out = prose_displays_to_paragraphs(KASHIWARA_P117)
    assert "$$" not in out
    assert "In a similar manner, one obtains $\\mathrm{sp} f_1 f_2 = 0.$" in out
    assert "holds; i.e. $\\mathrm{sp} f_1(f_2 - \\tilde{f}_2) = 0$ at" in out
    assert out.endswith("*Remark.* We proved Theorem 3.1.2 locally.")


def test_closed_display_of_prose_becomes_a_paragraph():
    page = (
        "such that\n\n$$\n|\\gamma(t - s)| < \\rho \\quad \\text{if } |t - s| < \\delta. "
        "\\text{ hence, if } |t-s| < \\delta, f(z, t) \\text{ is the power series expansion of the holomorphic function }"
        " f(z, s)\n$$\n\nNext."
    )
    out = prose_displays_to_paragraphs(page)
    assert "$$" not in out
    assert "is the power series expansion of the holomorphic function $f(z, s)$" in out
    assert out.startswith("such that\n\n")
    assert out.endswith("\n\nNext.")


def test_display_with_short_conditions_stays_a_display():
    page = "$$|f(\\gamma(t)) - f(\\gamma(s))| < \\varepsilon \\quad \\text{if } |t - s| < \\delta(\\varepsilon) \\quad \\text{and } t, s \\in [a, b].$$"
    assert prose_displays_to_paragraphs(page) == page


def test_tagged_or_aligned_display_of_prose_stays_a_display():
    tagged = "$$a = b \\text{ holds for every point of the open set where the function is defined } \\quad (1.7)$$"
    aligned = "$$\\begin{aligned} a &= b \\text{ holds for every point of the open set where it is defined } \\end{aligned}$$"
    assert prose_displays_to_paragraphs(tagged) == tagged
    assert prose_displays_to_paragraphs(aligned) == aligned
