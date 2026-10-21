from polytypst.compiler.monograph import _label_page_equations, _label_section_equations


def test_section_tag_after_a_blank_line_labels_the_display():
    page = "$$\nf(z) = g(z).\n$$\n\n(1.37)\n\nNext paragraph."
    out = _label_section_equations(page, 48)
    assert "$$ <eq-1-37>" in out
    assert "(1.37)" not in out


def test_inline_tagged_equation_with_trailing_period_becomes_a_display():
    page = r"(6) $(\mathfrak{Z} - i\mathfrak{E})(\mathfrak{Z} + i\mathfrak{E})^{-1} = \mathfrak{Z}_0$."
    out = _label_page_equations(page, 1, 20)
    assert "<eq-1-20-6>" in out
    assert out.count("$$") == 2
    assert r"\mathfrak{Z}_0." in out


def test_section_labeller_promotes_a_plain_number_tag_too():
    out = _label_section_equations(r"(6) $(\mathfrak{Z} - i\mathfrak{E})^{-1} = \mathfrak{Z}_0$.", 20)
    assert "<eq-6>" in out
    assert out.count("$$") == 2


def test_consecutive_tagged_lines_keep_their_own_numbers():
    for gap in ("\n", "\n\n"):
        page = f"hence\n\n(19) $\\mathfrak{{B}}_1(\\mathfrak{{J}}_1) = \\mathfrak{{E}}$,{gap}(20) $\\mathfrak{{B}}_1(\\mathfrak{{J}}_2) = \\mathfrak{{J}}_1$."
        out = _label_section_equations(page, 18)
        assert "<eq-19>" in out
        assert "<eq-20>" in out
        assert "(20)" not in out
        out = _label_page_equations(page, 2, 18)
        assert "<eq-2-18-20>" in out


def test_section_inline_tagged_equation_with_trailing_comma_becomes_a_display():
    out = _label_section_equations(r"(2.4) $a_n = \sum_{k} b_k c_{n-k}$,", 30)
    assert "<eq-2-4>" in out
    assert "c_{n-k}," in out
