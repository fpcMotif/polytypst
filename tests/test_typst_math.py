from dataclasses import replace

from polytypst.compiler.monograph import (
    CONTINUATION_OP_RE,
    MonographCompiler,
    MonographSpec,
)
from polytypst.compiler.typst_math import (
    clean_margin_and_inline_math,
    convert_environments,
    convert_math_batch,
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


