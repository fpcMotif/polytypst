from dataclasses import replace

import pytest

from polytypst.compiler.monograph import (
    CONTINUATION_OP_RE,
    MonographCompiler,
    MonographSpec,
    compile_typst,
)
from polytypst.compiler.typst_math import (
    clean_margin_and_inline_math,
    convert_environments,
    convert_math_batch,
    normalize_typst_differentials,
)


def convert(code: str, display: bool = False) -> str:
    return convert_math_batch([(code, display)])[0]


def layout_convert(code: str) -> str:
    return convert_math_batch([(code, False)], theorem_layout=True)[0]


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


def _tight(code: str) -> str:
    return convert(code).replace(" ", "")


def test_a_norm_becomes_a_norm_call_that_keeps_its_scripts():
    assert _tight(r"\|f\|_p") == "norm(f)_p"
    assert _tight(r"\|f\|_p^2") == "norm(f)_p^2"
    assert _tight(r"\left\| f \right\|_{L^p}") == "norm(f)_(L^p)"
    assert _tight(r"\lVert u \rVert") == "norm(u)"
    assert _tight(r"\|f\| + \|g\|") == "norm(f)+norm(g)"
    assert _tight(r"\left\| \|f\|_{L^p} \right\|_{L^q}") == "norm(norm(f)_(L^p))_(L^q)"


def test_bars_that_are_not_one_norm_stay_bars():
    assert "norm" not in convert(r"\ell \parallel m, m \parallel n")
    assert "norm" not in convert(r"\|x, y\|")
    assert "norm" not in convert(r"a \| b")


def test_supp_is_an_upright_operator():
    assert convert(r"\supp f") == convert(r"\operatorname{supp} f") == 'op("supp") f'


def test_a_starred_operator_name_sets_its_scripts_as_limits():
    out = convert(r"\operatorname*{ess\,sup}_{x \in X} f(x)")
    assert out.startswith('op("ess sup", limits: #true)_(x in X)'), out
    assert 'op("argmax", limits: #true)' in convert(r"\operatorname*{argmax}_{y} g(y)")


def test_absolute_values_become_typst_abs_calls():
    assert layout_convert(r"|x - y|") == "abs(x - y)"
    assert layout_convert(r"|x - y|^2") == "abs(x - y)^2"
    assert layout_convert(r"\left| \frac{a}{b} \right|") == "abs(a / b)"
    assert layout_convert(r"\bigl| x \bigr|") == "abs(x)"
    assert "norm" not in layout_convert(r"|x|")


def test_bars_in_set_builders_and_evaluations_survive():
    set_builder = convert(r"\{ x \in \mathbb{R}^n : |x| < 1 \}")
    assert "abs(x)" in set_builder
    assert "<" in set_builder
    assert "abs" not in convert(r"f|_A")


def test_upright_math_operators():
    assert convert(r"\sup_{x \in X} f(x)") == "sup_(x in X) f ( x )"
    assert convert(r"\inf_{x \in X} f(x)") == "inf_(x in X) f ( x )"
    assert convert(r"\lim_{n \to \infty} a_n") == "lim_(n arrow.r oo) a_n"
    assert convert(r"\log(x) + \ln(y)") == "log ( x ) + ln ( y )"
    assert convert(r"\det(A)") == "det ( A )"
    assert "op(\"supp\")" in convert(r"\supp f")
    assert "op(\"supp\")" in convert(r"\operatorname{supp} f")


def test_loc_in_subscripts_is_upright():
    for expr in (
        r"L^p_{\text{loc}}",
        r"L^p_{loc}",
        r"L^p_{\mathrm{loc}}",
        r"L^1_{\operatorname{loc}}",
    ):
        res = layout_convert(expr)
        assert '"loc"' in res or 'upright("loc")' in res
        assert "l o c" not in res


def test_star_operator_spacing_and_scripts():
    conv = layout_convert(r"f * g")
    assert "ast.op" in conv
    conv_paren = layout_convert(r"(f * g)")
    assert "ast.op" in conv_paren
    assert layout_convert(r"f^*") == "f^ast"
    assert layout_convert(r"f_*") == "f_ast"
    assert layout_convert(r"f^\ast") == "f^ast"
    assert layout_convert(r"f_\ast") == "f_ast"
    res = layout_convert(r"(f * g)^*(x)")
    assert "ast.op" in res and "^ast" in res


def test_ellipses_horizontal_and_centered():
    assert layout_convert(r"\dots") == "…"
    assert layout_convert(r"\ldots") == "…"
    assert "…" in layout_convert(r"x_1, \dots, x_n")
    assert "…" in layout_convert(r"x_1, \ldots, x_n")
    assert layout_convert(r"\cdots") == "dots.c"
    assert "dots.c" in layout_convert(r"x_1 + \cdots + x_n")
    assert "…" in layout_convert(r"x_1 + ... + x_n")
    assert "…" not in convert(r"x_1, \dots, x_n")


def test_sized_delimiters():
    res1 = layout_convert(r"\left\langle x, y \right\rangle")
    assert res1.startswith("lr(chevron.l") and res1.endswith("chevron.r)")
    res2 = layout_convert(r"\bigl\langle x, y \bigr\rangle")
    assert res2.startswith("#scale(x: 120%, y: 120%)[chevron.l]")
    assert layout_convert(r"\left[ \frac{a}{b} \right]") == "lr([ a / b ])"
    assert layout_convert(r"\left\{ \frac{a}{b} \right\}") == "lr({ a / b })"


def test_widehat_conversion():
    assert convert(r"\widehat{f}") == "hat(f)"
    wide = convert(r"\widehat{f * g}")
    assert "hat(" in wide or "accent(" in wide


@pytest.mark.parametrize(
    ("latex", "spelled"),
    [
        (r"X \xrightarrow{f} Y", "x r i g h t"),
        (r"X \xrightarrow[\sim]{(p_1, p_2)} Y", "x r i g h t"),
        (r"A \xleftarrow{g} B", "x l e f t"),
        (r"\tfrac{1}{2}", "t f r a c"),
        (r"X \hookrightarrow Y", "h o o k"),
    ],
)
def test_arrow_and_fraction_commands_are_not_spelled_out_by_the_regex_fallback(tmp_path, latex: str, spelled: str) -> None:
    out = convert(latex + r" \unknownocrmacro", display=True)
    assert spelled not in out
    assert any(mark in out for mark in ("⟶", "⟵", "↪", "/"))
    typ = tmp_path / "a.typ"
    typ.write_text(f"$ {out} $\n", encoding="utf-8")
    compile_typst(typ, tmp_path / "a.pdf")


