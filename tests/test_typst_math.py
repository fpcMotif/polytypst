from dataclasses import replace

import pytest

from polytypst.compiler.monograph import (
    CONTINUATION_OP_RE,
    MonographCompiler,
    MonographSpec,
)
from polytypst.compiler.typst_math import (
    clean_margin_and_inline_math,
    convert_environments,
    convert_math_batch,
    normalize_typst_differentials,
)


def convert(code: str, display: bool = False) -> str:
    return convert_math_batch([(code, display)])[0]


def test_section_sign_survives_conversion():
    assert convert(r"\S 2") == "section 2"
    assert "section 6" in convert(r"(\S 6, \text{Corollary 1})")


def test_regex_fallback_still_applies_the_macro_rewrites():
    out = convert(r"\Psi \longmapsto b(\varphi) \unknownocrmacro")
    assert "⟼" in out
    assert "l o n g" not in out


def test_every_book_gets_the_circle_and_operator_name_rewrites():
    bare = MonographSpec(domain="math", slug="t", title="T", author="A")
    explicit = replace(
        bare,
        pre_math_rewrites=(
            (r"plus\.circle", r"\\u{2295}"),
            (r"\\text\{Hom\}", r"\\operatorname{Hom}"),
            (r"\\text\{S\.S\.\}", r"\\operatorname{S.S.}"),
        ),
    )
    text = r"Let $\text{Hom}(A, B) plus.circle \text{S.S.}(u)$ be given."
    expected = MonographCompiler(explicit).format_typst(text)
    assert "⊕" in expected or "2295" in expected
    assert MonographCompiler(bare).format_typst(text) == expected


def test_square_operator_keeps_full_size():
    assert convert(r"\square \varphi") == "square.stroked phi"


def test_plain_matrix_gets_no_parentheses():
    assert convert_environments(r"\begin{matrix} A & B \\ C & D \end{matrix}").startswith("mat(delim: #none,")
    assert convert_environments(r"\begin{pmatrix} A \end{pmatrix}").startswith('mat(delim: "(",')
    fallback = convert(r"\left. \begin{matrix} P = 0, \\ Q \neq 0, \end{matrix} \right\} \unknownocrmacro", True)
    assert "mat(delim: #none," in fallback


def test_display_row_starting_with_a_spaced_plus_is_a_continuation():
    assert CONTINUATION_OP_RE.match(r"+ \int_\gamma d \log f")
    assert CONTINUATION_OP_RE.match(r"\to 0")
    assert not CONTINUATION_OP_RE.match(r"\top")


def test_mod_keeps_the_latex_gap_before_it():
    assert convert(r"a \equiv b \mod m", True) == "a equiv b quad mod med m"


def test_section_sign_inside_text_keeps_the_text():
    assert convert(r"\text{see \S 3}") == 'upright("see § 3")'


def test_dollar_signs_nested_in_text_do_not_leak():
    out = convert(r"\omega_j e_j \quad \text{($\S 3$, formula (30))}", True)
    assert "$" not in out
    assert "§ 3, formula (30)" in out


def test_convert_math_batch_and_margin_helper_return_finished_typst_math():
    out = convert(r"\int f(x) dx \neq \prod_{i=1}^n a_i \unknownocrmacro")
    assert "dif x" in out
    assert "!=" in out
    assert "product" in out
    titled = clean_margin_and_inline_math(r"Section on $\int f(x) dx \neq 0 \unknownocrmacro$")
    assert "dif x" in titled
    assert "!=" in titled


def test_run_typst_resolves_binary_once_without_triple_retry(monkeypatch, tmp_path):
    import subprocess

    import pytest

    from polytypst.compiler import typst_math
    from polytypst.compiler.monograph import compile_typst
    from polytypst.compiler.typst_math import REPO_FONTS_DIR

    calls = []

    def fake_run(cmd, **_kwargs):
        calls.append(cmd)
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(typst_math, "typst_command", lambda fallback_nix=True: ("typst",))
    monkeypatch.setattr(typst_math, "_embedded_typst", lambda: None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        compile_typst(tmp_path / "a.typ", tmp_path / "a.pdf", "--root", "/")

    assert calls == [
        [
            "typst",
            "compile",
            "--font-path",
            str(REPO_FONTS_DIR),
            "--root",
            "/",
            str(tmp_path / "a.typ"),
            str(tmp_path / "a.pdf"),
        ]
    ]


@pytest.mark.slow
def test_real_differentials_become_upright_dif():
    assert "dif z" in convert(r"\int_\gamma f(z) dz")
    assert "dif mu" in convert(r"\int_X g \, d\mu")
    assert "thin" not in convert(r"\int f(x)\,dx")
    assert convert(r"\frac{df^1}{dt}").count("dif") == 2
    assert convert(r"\frac{dA}{dB}").count("dif") == 2
    assert convert(r"dy = f'(x) dx").count("dif") == 2
    assert convert("dx") == "dif x"
    assert convert(r"\frac{d}{dz} f").startswith("frac(dif, dif z)")
    assert convert(r"\frac{d^2}{dx^2} f").startswith("frac(dif^2, dif x^2)")


def test_differentials_from_built_books_become_upright_dif():
    for body, upright in (
        ("integral_e f ( xi_1 , xi_2 ) d xi_1 d xi_2", 2),
        ("integral_0^T sin^2 theta ((dif phi)/(dif t))^2 d t.", 3),
        ("-(d P_(n)(z))/(d z)", 2),
        ("d abs(gamma ( t )) \\/ d t", 2),
        ("d y = y_(x') dot.op d x.", 2),
        ("d y = y_(x') dot.op Delta x .", 1),
        ("lambda'_theta = frac(2 d, d theta) abs(lambda'_theta)", 2),
        ("frac(partial u, partial x_1) dot d(dif x_1)", 2),
        ("d^2 y = d ( d y ) .", 3),
        ("frac(d log z, d z) = 1 / z", 2),
        ("Delta y = d y", 1),
        ("y_(x') dot.op Delta x = d y .", 1),
        ("d thin d u = 0", 2),
        ("d d u = 0", 2),
        ("d u = 0", 1),
        ("dif^2 y = d ( d y ) = d ( y' dot.op d x )", 5),
        ("d^n y = d ( d^(n - 1) y )", 3),
        ("d ( \\* d u ) = d d v = 0", 4),
        ("f ( z ) d z = phi + i \\* phi .", 1),
    ):
        out = normalize_typst_differentials(body)
        assert out.count("dif") == upright and "difif" not in out, (body, out)


@pytest.mark.slow
def test_a_d_that_is_not_a_differential_stays_italic():
    for code in (
        r"d(x, y) \le d(x, z) + d(z, y)",
        r"dA = F \cos t",
        r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
        r"ad - bc",
        r"d = 2",
        r"\frac{d}{2}",
        r"x^2 = c z^1 + d z^2",
        r"g(a, d, d)",
        r"a_d x + d",
    ):
        assert "dif" not in convert(code), code


