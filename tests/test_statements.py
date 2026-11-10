from polytypst.compiler.statements import style_statements

BOURBAKI_LIE_P325 = """**Corollary 1.** *Let G and H be Lie groups, $\\phi$ a Lie group morphism of G into H, N the kernel of $\\phi$ and $h = L(\\phi)$. Suppose that G is connected and that H is finite-dimensional.*

(i) N is a Lie subgroup of G and $L(N) = \\operatorname{Ker} h$.

(ii) *Let $H'$ be the integral subgroup of H with Lie algebra $\\operatorname{Im} h$. Then $\\phi(G) = H'$.*

(iii) *The mapping of $G/N$ into $H'$ derived from $\\phi$ when passing to the quotient is a Lie group isomorphism.*

(i) has already been proved (§ 3, no. 8, Proposition 28).

Let $\\psi$ be the Lie group morphism of $G/N$ into H derived from $\\phi$."""


def test_the_items_of_a_statement_are_italic_and_the_proof_that_restarts_at_i_is_not() -> (
    None
):
    # Scan p325 (book p307): items (i)-(iii) of Corollary 1 are italic; "(i) has already been proved" is roman.
    out = style_statements(BOURBAKI_LIE_P325, "italic").split("\n\n")
    assert (
        out[1] == "(i) *N is a Lie subgroup of G and $L(N) = \\operatorname{Ker} h$.*"
    )
    assert out[2].startswith("(ii) *Let $H'$") and out[2].endswith("= H'$.*")
    assert out[4] == "(i) has already been proved (§ 3, no. 8, Proposition 28)."
    assert out[5].startswith("Let $\\psi$")


def test_a_french_head_numbered_in_parentheses_gets_an_italic_statement() -> None:
    text = "**Proposition (6.1.4)** Supposons que chacun des $A_\\alpha$ soit un anneau local; soit"
    assert style_statements(text, "italic") == (
        "**Proposition (6.1.4)** *Supposons que chacun des $A_\\alpha$ soit un anneau local; soit*"
    )


def test_partial_italics_inside_a_statement_become_one_italic_statement() -> None:
    text = "**Corollaire (1.2.3).** Soit *X* un schéma et $f^*$ un morphisme *affine*."
    assert (
        style_statements(text, "italic")
        == "**Corollaire (1.2.3).** *Soit X un schéma et $f^*$ un morphisme affine.*"
    )


def test_a_bold_statement_style_sets_a_chinese_theorem_in_bold() -> None:
    text = "**定理 3** 对于每一个次数为 $n > 0$ 的标准多项式 $f \\in P[X]$, 至少存在一个分裂域."
    assert style_statements(text, "bold") == (
        "**定理 3** **对于每一个次数为 $n > 0$ 的标准多项式 $f \\in P[X]$, 至少存在一个分裂域.**"
    )


def test_proofs_definitions_and_upright_books_are_left_alone() -> None:
    text = "**Definition 2.** A group is *simple* if it has no normal subgroup.\n\n*Proof.* Clear."
    assert style_statements(text, "italic") == text
    assert style_statements(BOURBAKI_LIE_P325, "upright") == BOURBAKI_LIE_P325


def test_a_starred_condition_mark_in_a_statement_keeps_its_star() -> None:
    text = "**Theorem 2.** If condition (*) holds, then $f$ is *smooth*."
    assert (
        style_statements(text, "italic")
        == "**Theorem 2.** *If condition (*) holds, then $f$ is smooth.*"
    )


def test_bold_letters_and_numbered_displays_in_a_statement_are_kept() -> None:
    # bourbaki p198 prints the bold Z of (A_n)_{n in Z}; bourbaki_lie p304 numbers displays (1) and (2).
    text = "**Corollary.** Let A be a filtered ring and (Aₙ)ₙ∈**Z** its filtration.\n\n(1) $$x + y = 0$$"
    assert style_statements(text, "italic") == (
        "**Corollary.** *Let A be a filtered ring and (Aₙ)ₙ∈**Z** its filtration.*\n\n(1) $$x + y = 0$$"
    )


def test_a_statement_with_eleven_roman_items_styles_them_all() -> None:
    items = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi"]
    text = (
        "**Proposition 2.36.** Suppose that it has one of the properties\n\n"
        + "\n\n".join(f"({n}) is property {k}," for k, n in enumerate(items, 1))
    )
    out = style_statements(text, "italic").split("\n\n")
    assert out[-1] == "(xi) *is property 11,*"


def test_bracket_displays_and_lines_inside_a_display_are_never_wrapped() -> None:
    # bourbaki p116 writes item (1) as a \\[ ... \\] display.
    text = (
        "**Proposition 3.** The following are equivalent:\n\n"
        "(1) \\[ [K \\otimes M : K] = n \\]\n\n$$\n(2) x = y\n$$\n\n(2) the module is free."
    )
    out = style_statements(text, "italic")
    assert "(1) \\[ [K \\otimes M : K] = n \\]" in out
    # bourbaki p442 numbers a formula as "(1) $f(X) = ...$", which a later pass turns into a display.
    formula = "**Lemma 1.** There exists a polynomial of the form\n\n(1) $f(X) = 1 + X^k$\n\n(2) $g = 0$."
    assert style_statements(formula, "italic").endswith(
        "(1) $f(X) = 1 + X^k$\n\n(2) $g = 0$."
    )
    assert "$$\n(2) x = y\n$$" in out


def test_an_attribution_after_the_head_stays_roman_and_the_body_below_it_is_italic() -> (
    None
):
    # fermat scan p91: "Theorem 9.22. (Jacobi)" prints the attribution roman and the statement italic.
    text = "**Theorem 9.22.** (Jacobi)\n\n(1) For $n \\geq 1$, we have\n\n**Theorem 9.1.** (Mordell, 1917)\n\nThe group is finite."
    assert style_statements(text, "italic").split("\n\n") == [
        "**Theorem 9.22.** (Jacobi)",
        "(1) *For $n \\geq 1$, we have*",
        "**Theorem 9.1.** (Mordell, 1917)",
        "*The group is finite.*",
    ]


def test_an_environment_inside_a_dollar_display_does_not_end_the_display() -> None:
    # kashiwara scan p23: Theorem 1.1.1 is italic after a $$ \begin{array} ... \end{array} $$ diagram.
    text = "$$\n\\begin{array}{c}\nK_1 \\to K_2\n\\end{array}\n$$\n\n**Theorem 1.1.1.** The group is free."
    assert style_statements(text, "italic").endswith(
        "**Theorem 1.1.1.** *The group is free.*"
    )


def test_a_display_left_open_by_the_ocr_ends_at_the_blank_line() -> None:
    # bourbaki scan p511: Lemma 1 is italic though an earlier line on the page reads "(3) v(a) = sup(v(x));$$".
    text = "(3) v_{\\iota}$(a) = \\sup_{a \\in Ax} ($v_{\\iota}$(x));$$\n\n**Lemma 1.** If $A$ is a Krull domain."
    assert style_statements(text, "italic").endswith(
        "**Lemma 1.** *If $A$ is a Krull domain.*"
    )


def test_a_proof_after_an_attribution_head_stays_roman() -> None:
    # fermat scan p20: an attributed theorem whose statement is a display is followed by a roman proof.
    text = "**Theorem 9.2.** (Mordell)\n\n$$\nT_p = 0\n$$\n\n*Proof.* For each prime $p$, Mordell constructed"
    assert style_statements(text, "italic") == text


def test_styling_twice_gives_the_same_text_as_once() -> None:
    once = style_statements(BOURBAKI_LIE_P325, "italic")
    assert style_statements(once, "italic") == once
