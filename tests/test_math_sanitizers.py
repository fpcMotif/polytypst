import re

from polytypst.compiler.typst_math import sanitize_math_code
from polytypst.tex_markdown import repair_ocr_math


def test_font_macro_script_is_braced_for_unicode_math() -> None:
    out = repair_ocr_math(
        r"\pi_W : \mathbb{P}_\mathbb{Z}^n", True
    )
    assert r"\mathbb{P}_{\mathbb{Z}}^n" in out


def test_prime_after_operator_limits_wraps_the_operator() -> None:
    out = repair_ocr_math(
        r"\prod_{m,n=-\infty}^\infty' (1 - q^{mn})", True
    )
    assert r"{\prod_{m,n=-\infty}^\infty}' (1 - q^{mn})" in out


def test_matrix_cell_starting_with_greek_macro_and_colon_is_not_a_named_arg() -> None:
    out = sanitize_math_code(
        r"\begin{pmatrix} \gamma : g^* E \to L & 0 \end{pmatrix}", True
    )
    assert re.search(r"[(,;]\s*gamma\s*:", out) is None
    assert re.search(r"\(\s*gamma\s*\)\s*:", out)
