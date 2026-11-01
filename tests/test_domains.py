from typing import Any

import pytest

from polytypst.compiler.monograph import MonographCompiler, MonographSpec, latex_safe_markdown
from polytypst.compiler.presets import DOMAIN_PROFILES, resolve_composition


def test_an_unknown_domain_is_an_error_not_math():
    with pytest.raises(ValueError, match="finance"):
        resolve_composition(domain="finance")


def test_each_known_domain_resolves_to_its_own_profile():
    assert {key: resolve_composition(domain=key).domain.key for key in DOMAIN_PROFILES} == {k: k for k in DOMAIN_PROFILES}


def test_a_spec_names_its_domain():
    without_domain: dict[str, Any] = {"slug": "x", "title": "T", "author": "A"}
    with pytest.raises(TypeError, match="domain"):
        MonographSpec(**without_domain)


def test_a_spec_rejects_an_unknown_domain():
    with pytest.raises(ValueError, match="banking"):
        MonographSpec(slug="x", title="T", author="A", domain="banking")


LEGEND = "图中各项如下。\n\n□ 正规雇员\n\n■ 非正规雇员\n"
PROOF = "Hence the map is onto. □\n"


def _typst(domain: str, text: str) -> str:
    return MonographCompiler(MonographSpec(slug="x", title="T", author="A", domain=domain)).format_typst(text)


def test_an_economics_book_keeps_its_legend_squares():
    out = _typst("economics", LEGEND)
    assert "□ 正规雇员" in out and "■ 非正规雇员" in out
    assert "#qed" not in out and "square.stroked" not in out


def test_a_math_book_ends_a_proof_with_a_qed_box():
    assert "#qed" in _typst("math", PROOF)


def test_math_domain_normalizes_proof_labels():
    out1 = _typst("math", "*PROOF.* We prove the result directly.")
    assert "#emph[Proof.] We prove the result directly." in out1

    out2 = _typst("math", "*PROOF OF THEOREM 4.2.* Let $x > 0$.")
    assert "#emph[Proof of Theorem 4.2.] Let $x > 0$." in out2

    out3 = _typst("math", "*PROOF. Recall that $f$ is bounded.*")
    assert "#emph[Proof.] Recall that $f$ is bounded." in out3

    out_econ = _typst("economics", "*PROOF.* We observe data.")
    assert "#emph[Proof.]" not in out_econ


def test_proof_end_mark_in_text_and_display_math():
    out_text = _typst("math", "This completes the proof. ■\n- Next topic")
    assert "#qed\n\n- Next topic" in out_text

    out_disp1 = _typst("math", "$$\nx = y \\quad \\blacksquare\n$$")
    assert "$ x = y $" in out_disp1
    assert "#v(-0.4em, weak: true)\n#align(right)[$square.filled.medium$]" in out_disp1

    out_disp2 = _typst("math", "$$\nx = y ■\n$$")
    assert "$ x = y $" in out_disp2
    assert "#v(-0.4em, weak: true)\n#align(right)[$square.filled.medium$]" in out_disp2


def test_bullet_and_parenthesized_list_formatting():
    out_bullets = _typst("math", "● First bullet\n● Second bullet")
    assert "- First bullet\n- Second bullet" in out_bullets

    out_num = _typst("math", "(1) First item\n\n(2) Second item")
    assert "#par(first-line-indent: 0pt, hanging-indent: 1.8em)[#box(width: 1.8em)[(1)]First item]" in out_num
    assert "#par(first-line-indent: 0pt, hanging-indent: 1.8em)[#box(width: 1.8em)[(2)]Second item]" in out_num

    out_roman = _typst("math", "(i) First roman\n\n(ii) Second roman")
    assert "#par(first-line-indent: 0pt, hanging-indent: 1.8em)[#box(width: 1.8em)[(i)]First roman]" in out_roman


def test_latex_safe_markdown_preserves_equations_and_proofs():
    eq = r"\begin{equation} A & B \end{equation}"
    assert latex_safe_markdown(eq) == eq

    eq_qed = r"\begin{equation} x = y \quad \blacksquare \end{equation}"
    out_eq = latex_safe_markdown(eq_qed, proof_end_mark=True)
    assert r"\begin{equation} x = y \end{equation}" in out_eq
    assert r"\hfill$\blacksquare$" in out_eq

    hyphen_math = "$L^p$ -norm"
    assert latex_safe_markdown(hyphen_math) == "$L^p$-norm"

    proof_label = "*PROOF OF THEOREM 4.2.*"
    assert latex_safe_markdown(proof_label, proof_blocks=True) == r"\emph{Proof of Theorem 4.2.}"

