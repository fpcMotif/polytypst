from dataclasses import replace
from typing import Any

import pytest

from polytypst.compiler.monograph import (
    MonographCompiler,
    MonographSpec,
    latex_safe_markdown,
)
from polytypst.compiler.presets import DOMAIN_PROFILES, resolve_composition


def test_an_unknown_domain_is_an_error_not_math():
    with pytest.raises(ValueError, match="finance"):
        resolve_composition(domain="finance")


def test_each_known_domain_resolves_to_its_own_profile():
    assert {key: resolve_composition(domain=key).domain.key for key in DOMAIN_PROFILES} == {k: k for k in DOMAIN_PROFILES}


def test_theorem_headings_are_the_domains_kinds_in_the_books_language():
    math = resolve_composition(lang="en", domain="math", theorem_layout=True).typst_heading_rules()
    economics = resolve_composition(lang="en", domain="economics", theorem_layout=True).typst_heading_rules()
    novel = resolve_composition(lang="en", domain="novel", theorem_layout=True).typst_heading_rules()
    assert 's.contains("notation")' in math and 's.contains("axiom")' in math
    assert 's.contains("proposition")' in economics and 's.contains("axiom")' not in economics
    assert "s.contains" not in novel and "false" in novel

    english = resolve_composition(lang="en", domain="math", theorem_layout=True)
    spelled = replace(english.language, numbering=replace(english.language.numbering, theorems=(("Theorem", "Théorème"),)))
    french = replace(english, language=spelled).typst_heading_rules()
    assert 's.contains("théorème")' in french and 's.contains("theorem")' not in french
    assert 's.contains("lemma")' in french


def test_a_book_without_theorem_layout_keeps_the_plain_heading_rules():
    rules = resolve_composition(lang="en", domain="math").typst_heading_rules()
    assert "is-thm-heading" not in rules and "s.contains" not in rules
    assert '#text(12.5pt, weight: "bold"' in rules
    assert resolve_composition(domain="math").theorem_heads == DOMAIN_PROFILES["math"].theorem_heads
    assert "Claim" in resolve_composition(domain="math", theorem_layout=True).theorem_heads


def test_a_spec_names_its_domain():
    without_domain: dict[str, Any] = {"slug": "x", "title": "T", "author": "A"}
    with pytest.raises(TypeError, match="domain"):
        MonographSpec(**without_domain)


def test_a_spec_rejects_an_unknown_domain():
    with pytest.raises(ValueError, match="banking"):
        MonographSpec(slug="x", title="T", author="A", domain="banking")


LEGEND = "图中各项如下。\n\n□ 正规雇员\n\n■ 非正规雇员\n"
PROOF = "Hence the map is onto. □\n"


def _typst(domain: str, text: str, theorem_layout: bool = False) -> str:
    spec = MonographSpec(slug="x", title="T", author="A", domain=domain, theorem_layout=theorem_layout)
    return MonographCompiler(spec).format_typst(text)


def test_an_economics_book_keeps_its_legend_squares():
    out = _typst("economics", LEGEND)
    assert "□ 正规雇员" in out and "■ 非正规雇员" in out
    assert "#qed" not in out and "square.stroked" not in out


def test_a_math_book_ends_a_proof_with_a_qed_box():
    assert "#qed" in _typst("math", PROOF)


def test_math_domain_normalizes_proof_labels():
    out1 = _typst("math", "*PROOF.* We prove the result directly.", theorem_layout=True)
    assert "#emph[Proof.] We prove the result directly." in out1

    out2 = _typst("math", "*PROOF OF THEOREM 4.2.* Let $x > 0$.", theorem_layout=True)
    assert "#emph[Proof of Theorem 4.2.] Let $x > 0$." in out2

    out_case = _typst("math", "*PROOF OF THEOREM 7.6 FOR THE CASE $p = 1$.* Let $j$ be given.", theorem_layout=True)
    assert "Inlinemath" not in out_case
    assert "For The Case $p = 1$.]" in out_case

    out3 = _typst("math", "*PROOF. Recall that $f$ is bounded.*", theorem_layout=True)
    assert "#emph[Proof.] Recall that $f$ is bounded." in out3

    out_econ = _typst("economics", "*PROOF.* We observe data.", theorem_layout=True)
    assert "#emph[Proof.]" not in out_econ

    assert "#emph[Proof.]" not in _typst("math", "*PROOF.* We prove the result directly.")


def test_proof_end_mark_in_text_and_display_math():
    out_text = _typst("math", "This completes the proof. ■\n- Next topic", theorem_layout=True)
    assert "#qed-filled\n\n- Next topic" in out_text
    assert "#qed\n\n- Next" in _typst("math", "This completes the proof. □\n- Next topic", theorem_layout=True)

    out_disp1 = _typst("math", "$$\nx = y \\quad \\blacksquare\n$$", theorem_layout=True)
    assert "$ x = y $" in out_disp1
    assert "#v(-0.4em, weak: true)\n#align(right)[$square.filled.medium$]" in out_disp1

    out_disp2 = _typst("math", "$$\nx = y ■\n$$", theorem_layout=True)
    assert "$ x = y $" in out_disp2
    assert "#v(-0.4em, weak: true)\n#align(right)[$square.filled.medium$]" in out_disp2

    assert "#qed-filled" not in _typst("math", "This completes the proof. ■\n- Next topic")
    assert "#align(right)[$square.filled.medium$]" not in _typst("math", "$$\nx = y ■\n$$")


def test_bullet_list_formatting():
    out_bullets = _typst("math", "● First bullet\n● Second bullet", theorem_layout=True)
    assert "- First bullet\n- Second bullet" in out_bullets
    assert "- First bullet" not in _typst("math", "● First bullet\n● Second bullet")


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

