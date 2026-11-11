from dataclasses import replace
from pathlib import Path

import pymupdf

from polytypst.books import book_by_key
from polytypst.compiler.monograph import (
    SOURCE_EQUATION_LAYOUT,
    SOURCE_NUMBER_RULES,
    MonographCompiler,
    compile_typst,
    typst_footnote_rules,
)
from polytypst.compiler.source_numbers import number_chapter


def _fn(text: str) -> str:
    return f"@@FNSTART@@{text}@@FNEND@@"


def test_theorem_strong_line_keeps_footnote_at_call_site():
    spec = book_by_key("fichtenholz_vol1").spec
    mc = MonographCompiler(spec)
    md = (
        "**定理** 若函数 $f(x, y)$ 是在有界闭域 $\\mathcal{D}$"
        + _fn("这里 $\\mathcal{D}$ 也可以是非连通域.")
        + " 中定义着而且连续的,则它必是有界的:"
    )
    typ = mc.format_typst(md)
    assert "#heading-note[" not in typ
    assert "$cal(D)$#footnote[" in typ
    assert "] 中定义着" in typ

    heading_typ = mc.format_typst("## 8.3 ELBO 的计算" + _fn("逆扩散过程服从正态分布。"))
    assert heading_typ.strip() == "== 8.3 ELBO 的计算#heading-note[逆扩散过程服从正态分布。]"


def test_display_footnote_call_mark_renders_on_display_and_splits_editor_note(tmp_path: Path):
    ficht_mc = MonographCompiler(book_by_key("fichtenholz_vol1").spec)
    raw_p212 = (
        "称为 $n$ 阶微分:\n\n"
        "$$d^n y = d(d^{n-1} y)^{19}).$$\n\n"
        "在这种情形:\n\n"
        "$$d^3 y = y''' \\cdot dx^3 ①$$\n\n"
        "① $dx^2, dx^3$ 恒理解为微分的幂.\n\n"
        "19) 我们强调指出: 当 $\\Delta x$ 固定时 $dy$ 是 $x$ 的函数.\n"
    )
    cleaned = ficht_mc.cleaner.clean(raw_p212, 212).body
    assert cleaned.count("@@FNSTART@@") == 2
    assert "^{19})" not in cleaned
    assert "19) 我们强调指出" not in cleaned.split("@@FNEND@@")[0]

    book4_spec = replace(book_by_key("book4").spec, footnote_style="circled", footnote_numbering="circled")
    b4_mc = MonographCompiler(book4_spec)
    raw_p199 = (
        "## 5.1 语言模型\n\n"
        "联合概率分解如下：\n\n"
        "$$\nP(w_1) = \\prod_{t=1}^{m} P(w_t) ^{\\text{①}}\n\\tag{5.4}\n$$\n\n"
        "接下来讨论乘法定理②。\n\n"
        "① 这里将 $P(w_1 | w_0)$ 作为 $P(w_1)$ 处理。\n\n"
        "② 参见第 7 章。\n"
    )
    b4_clean = b4_mc.cleaner.clean(raw_p199, 199).body
    typ_body, _resyncs = number_chapter(b4_mc.format_typst(b4_clean), 5)
    assert "<eq-c5-5-4>" in typ_body
    preamble = "\n".join(
        [
            b4_mc.build_typst_preamble(),
            typst_footnote_rules(book4_spec),
            SOURCE_NUMBER_RULES,
            SOURCE_EQUATION_LAYOUT,
        ]
    )
    typ_file = tmp_path / "b4.typ"
    pdf_file = tmp_path / "b4.pdf"
    typ_file.write_text(
        preamble + '\n#counter(heading).update((4,))\n#heading(level: 1, numbering: "1")[第5章]\n' + typ_body,
        encoding="utf-8",
    )
    compile_typst(typ_file, pdf_file)
    page = pymupdf.open(pdf_file)[-1]
    lines = [
        "".join(sp["text"] for sp in ln["spans"]).strip()
        for blk in page.get_text("dict")["blocks"]
        for ln in blk.get("lines", [])
    ]
    assert "(5.4)" in " ".join(lines)
    assert not any(ln in ("①", "②", "1", "2") and i < len(lines) - 1 for i, ln in enumerate(lines))
    assert any("乘法定理②" in ln or "乘法定理2" in ln for ln in lines)


def test_dagger_on_multi_display_attaches_without_corrupting_later_equation():
    lie_mc = MonographCompiler(book_by_key("bourbaki_lie").spec)
    raw_p132 = (
        "**DEFINITION 2.** *Let $E$ be a bigebra such that*\n\n"
        "$$\nE_0 = K.1\n$$\n\n"
        "(6)\n\n"
        "$$\nE_m.E_n \\subset E_{m+n}\n$$\n\n"
        "$$\nc(E_n) \\subset \\sum_{t+j=n} \\operatorname{Im}(E_t \\otimes E_j) \\quad \\text{for } n \\geq 0. \\dagger\n$$\n\n"
        "**PROPOSITION 6.** *Then $E_0^+ = \\{0\\}$ and*\n\n"
        "(7)\n\n"
        "$$\nc^+(E_n^+) \\subset \\sum_{t=1}^{n-1} \\operatorname{Im}(E_t^+ \\otimes E_{n-1}^+) \\quad \\text{for } n \\geq 0. \\dagger\n$$\n\n"
        "† If $A$ and $B$ are two submodules of $E$, we denote by $\\operatorname{Im}(A \\otimes B)$ the image.\n"
    )
    cleaned = lie_mc.cleaner.clean(raw_p132, 132).body
    typ_body, _ = number_chapter(lie_mc.format_typst(cleaned), 2)
    assert "<eq-c2-6>" in typ_body
    assert "<eq-c2-7>" in typ_body
    assert "and*†" not in cleaned
    assert "#footnote[" in typ_body


def test_circled_books_ignore_bare_parenthesized_items_and_equation_step_callouts():
    ficht_mc = MonographCompiler(book_by_key("fichtenholz_vol1").spec)
    raw_p379 = (
        "在下列各点同时等于零:\n\n"
        "(1) $x = y = 0 \\quad (u = 0), \\quad$ (2) $x = 0, y = \\pm \\frac{1}{\\sqrt{2}},$\n\n"
        "(3) $x = \\pm \\frac{1}{\\sqrt{2}}, y = 0.$\n\n"
        "最后, 注意在所考察的区间的端点有\n\n"
        "(6) $x = \\pm 1 \\quad (u = 0)$.\n"
    )
    clean_p379 = ficht_mc.cleaner.clean(raw_p379, 379).body
    assert "@@FNSTART@@" not in clean_p379
    assert "（1）" in clean_p379 and "（6）" in clean_p379

    raw_p472 = (
        "在函数 $f(x, y)$ 是可微分的假定之下$^{(1)}$, 求出切面方程 (10).\n\n"
        "切线 (9) 必定全部位于切面 (10) 内$^{31)}$. 平面$^{(2)}$.\n\n"
        "---\n\n"
        "$^{(1)}$ 我们在此处既已假定偏导数存在且为连续.\n\n"
        "$^{(2)}$ 关于这事已在 180 内讲过一部分.\n\n"
        "$^{31)}$ 同样可以验证.\n"
    )
    clean_p472 = ficht_mc.cleaner.clean(raw_p472, 472).body
    assert clean_p472.count("@@FNSTART@@") == 3

    dl5_mc = MonographCompiler(replace(book_by_key("dl5").spec, footnote_style="circled"))
    raw_dl5_p174 = (
        "$$\n\\begin{aligned}\n"
        "&= \\int q_{\\phi}(z|x) \\log \\frac{p_{\\theta}(x|z) p(z)}{q_{\\phi}(z|x)} \\mathrm{d}z \\quad \\text{①} \\\\\n"
        "&= \\int q_{\\phi}(z|x) \\log p_{\\theta}(x|z) \\mathrm{d}z \\quad \\text{②} \\\\\n"
        "&= - \\int q_{\\phi}(z|x) \\log \\frac{q_{\\phi}(z|x)}{p(z)} \\mathrm{d}z \\quad \\text{③}\n"
        "\\end{aligned}\n$$\n\n"
        "展开过程中式子的变换使用了以下公式。\n\n"
        "① $p_{\\theta}(x, z) = p_{\\theta}(x|z) p(z)$\n\n"
        "② $\\log AB = \\log A + \\log B$\n\n"
        "③ $\\log \\frac{A}{B} = -\\log \\frac{B}{A}$\n\n"
        "$$\n\\text{ELBO}(x; \\theta, \\phi) = J_1 - J_2 \\quad (7.10)\n$$\n"
    )
    clean_dl5_p174 = dl5_mc.cleaner.clean(raw_dl5_p174, 174).body
    assert "@@FNSTART@@" not in clean_dl5_p174
    assert "<eq-7-10>" in clean_dl5_p174
    assert "① $p_{\\theta}(x, z)" in clean_dl5_p174

    b5_mc = MonographCompiler(replace(book_by_key("5_财政政策与社会保障").spec, footnote_style="circled"))
    raw_b5_p100 = (
        "$EXP_t$ 是表示财政扩张的虚拟变量，满足表 3-2 的条件时取 $1^\\circ$ 。\n\n"
        "Hjelm（2002）作为理论基础②。可解释为一般形式③。\n\n"
        "① Hjelm（2002）p. 21 中财政虚拟变量的定义并非完全一致。\n\n"
        "② 如参见 Blanchard 和 Fischer（1989）。\n\n"
        "③ 因此，推算公式中解释变量不足。\n"
    )
    clean_b5_p100 = b5_mc.cleaner.clean(raw_b5_p100, 100).body
    assert clean_b5_p100.count("@@FNSTART@@") == 3
    assert "$1$@@FNSTART@@Hjelm" in clean_b5_p100


def test_superscript_books_split_latex_and_plain_called_foot_notes():
    ch_spec = book_by_key("courant_hilbert1").spec
    assert ch_spec.footnote_style == "superscript"
    ch_mc = MonographCompiler(ch_spec)
    raw_ch_p54 = (
        "not less than the corresponding numbers of the sequence $\\kappa_{j+1}, \\cdots, \\kappa_n$. $^1$\n\n"
        "Moreover, we may conclude: If a positive definite form is added\n\n"
        "$^1$ This may be illustrated geometrically: Let us consider the ellipse.\n"
    )
    clean_ch = ch_mc.cleaner.clean(raw_ch_p54, 54).body
    assert clean_ch.count("@@FNSTART@@") == 1
    assert "$^1$" not in clean_ch
    assert clean_ch.rstrip().endswith("If a positive definite form is added")

    fa_spec = book_by_key("functional_analysis").spec
    assert fa_spec.footnote_style == "superscript"
    assert fa_spec.footnote_reset == "chapter"
    fa_mc = MonographCompiler(fa_spec)
    raw_fa_p73 = (
        "**THEOREM.**¹² *Every linear functional $Ag$ in the space $L^2$ can be put in the form*\n\n"
        "$$\\|g_n\\| = 1, \\quad |Ag_n| \\to M_A.$$\n\n"
        "12 This theorem was discovered independently by M. Fréchet and F. Riesz [15].\n"
    )
    clean_fa = fa_mc.cleaner.clean(raw_fa_p73, 73).body
    assert clean_fa.count("@@FNSTART@@") == 1
    assert "¹²" not in clean_fa
    assert "12 This theorem" not in clean_fa.split("@@FNSTART@@")[0]

    uncalled_fa = "The proof follows immediately.\n\n12 This line has no call mark above.\n"
    assert "@@FNSTART@@" not in fa_mc.cleaner.clean(uncalled_fa, 74).body


def test_symbol_books_split_touching_star_italic_and_multi_paragraph_notes():
    spivak_spec = book_by_key("spivak_vol1").spec
    assert spivak_spec.footnote_style == "symbol"
    assert spivak_spec.footnote_marks == ("*", "**", "***")
    sp_mc = MonographCompiler(spivak_spec)
    raw_sp_p49 = (
        "This will not be proved here.* Of course, for $\\alpha = \\omega$ the proof\n\n"
        "*For a proof see Munkres, *Elementary Differential Topology*.\n"
    )
    clean_sp = sp_mc.cleaner.clean(raw_sp_p49, 49).body
    assert "here.@@FNSTART@@For a proof see Munkres, *Elementary Differential Topology*.@@FNEND@@" in clean_sp
    assert clean_sp.rstrip().endswith("the proof")

    klein_mc = MonographCompiler(book_by_key("klein").spec)
    raw_klein_p356 = (
        "For larger primes the degree does not drop down in this way.*\n\n"
        "led to a new group theoretic-geometric program for elliptic modular functions (1879).**\n\n"
        "1. One is to enumerate all the subgroups in order to create a domain of discontinuity\n\n"
        "*The first proof of this theorem of Galois was given by E. Betti in 1853 (*Ann. di Sc.* Vol. 4 = *Oeuvres* Vol. I).\n\n"
        "A complete discussion of the group of the modular equation was then given by Gierster: *Math. Ann.* Vol. 18 (1884).\n\n"
        "** See Klein: *Ges. Abh.* Vol. 3 (*Zur Systematik*).\n"
    )
    clean_klein = klein_mc.cleaner.clean(raw_klein_p356, 356).body
    assert clean_klein.count("@@FNSTART@@") == 2
    assert "Gierster" in clean_klein.split("@@FNSTART@@")[1].split("@@FNEND@@")[0]
    assert clean_klein.rstrip().endswith("create a domain of discontinuity")

    goursat_spec = book_by_key("goursat").spec
    assert goursat_spec.footnote_style == "symbol"
    assert goursat_spec.footnote_marks == ("*", "†", "‡", "§")
    go_mc = MonographCompiler(goursat_spec)
    raw_go_p182 = (
        "**87. Transcendental character of $e$.** *The number $e$ is not a root of any algebraic equation whose coefficients are all integers.**\n\n"
        "* The present proof is due to D. Hilbert.\n"
    )
    clean_go_182 = go_mc.cleaner.clean(raw_go_p182, 182).body
    assert "*The number $e$ is not a root of any algebraic equation whose coefficients are all integers.*@@FNSTART@@The present proof is due to D. Hilbert.@@FNEND@@" in clean_go_182

    raw_go_p186 = (
        "## IV. GENERALIZATIONS OF THE IDEA OF AN INTEGRAL IMPROPER INTEGRALS LINE INTEGRALS*\n\n"
        "To sum up, *the necessary and sufficient condition is that $\\mu$ should be less than unity.*\n\n"
        "*It is possible, if desired, to read the next chapter before reading the closing sections of this chapter.*\n"
    )
    clean_go_186 = go_mc.cleaner.clean(raw_go_p186, 186).body
    assert "LINE INTEGRALS@@FNSTART@@It is possible, if desired, to read the next chapter before reading the closing sections of this chapter.@@FNEND@@" in clean_go_186

    lie_mc = MonographCompiler(book_by_key("bourbaki_lie").spec)
    raw_lie_p245 = (
        "**Remark.** Let $H$ be a connected Lie group, $\\hat{H}$ its universal covering$^\\dagger$ and $\\pi$ the mapping. When we speak of $\\hat{H}$\n\n"
        "$^\\dagger$ Cf. *General Topology*, Chapter XI.\n"
    )
    clean_lie_245 = lie_mc.cleaner.clean(raw_lie_p245, 245).body
    assert "covering@@FNSTART@@Cf. *General Topology*, Chapter XI.@@FNEND@@" in clean_lie_245
    assert clean_lie_245.rstrip().endswith("When we speak of $\\hat{H}$")

    raw_lie_p439 = (
        "then the group is holohederically isomorphic to an analytic group.† Following his\n\n"
        "† Lie had already stated without proof a result of this type ([3 g], no. 7).\n\n"
        "The result of F. Schur was to lead Hilbert in 1900 to ask if the same conclusion remained true.\n"
    )
    clean_lie_439 = lie_mc.cleaner.clean(raw_lie_p439, 439).body
    assert clean_lie_439.count("@@FNSTART@@") == 1
    assert "The result of F. Schur" in clean_lie_439.split("@@FNSTART@@")[1].split("@@FNEND@@")[0]
    assert clean_lie_439.rstrip().endswith("Following his")


def test_dl5_zhu_footnotes_split_while_table_notes_stay():
    dl5_mc = MonographCompiler(replace(book_by_key("dl5").spec, footnote_style="circled"))
    raw_dl5_p165 = (
        "（1）基于固定的正态分布 $^1$ 生成潜变量 $z$ 。\n\n"
        "如图 7-2 所示，VAE 使用神经网络将潜变量 $z$ 变换为观测变量 $x$ 。假\n\n"
        "注 1：固定的正态分布是一种事先设定了均值向量和协方差矩阵的正态分布。\n"
    )
    clean_165 = dl5_mc.cleaner.clean(raw_dl5_p165, 165).body
    assert "固定的正态分布@@FNSTART@@固定的正态分布是一种事先设定了均值向量和协方差矩阵的正态分布。@@FNEND@@" in clean_165
    assert clean_165.rstrip().endswith("假")

    b6_mc = MonographCompiler(replace(book_by_key("6_劳动力市场与收入分配").spec, footnote_style="circled"))
    raw_b6_p136 = (
        "<table><tr><td>（注1）5.0</td><td>（注2）5.9</td></tr></table>\n\n"
        "注1：1988—1991年的平均值。\n\n"
        "注2：2003—2007年的平均值。\n"
    )
    clean_b6 = b6_mc.cleaner.clean(raw_b6_p136, 136).body
    assert "@@FNSTART@@" not in clean_b6
    assert "注1：1988—1991年的平均值。" in clean_b6


def test_symbol_marks_filter_mid_page_italic_and_circled_superscript_editor_call():
    lie_mc = MonographCompiler(book_by_key("bourbaki_lie").spec)
    raw_lie_p262 = (
        "We extend the product * to a bilinear mapping.\n\n"
        "**PROPOSITION 13.** *Let $t \\in \\mathcal{F}^{(s)}(G)$ such that*\n\n"
        "\\[ s + s' + s'' \\leqslant r. \\]\n\n"
        "*Then $(t * t') * u = t * (t' * u)$.*\n\n"
        "In particular, $\\mathcal{F}^{(\\infty)}(X)$ is a left module over $\\mathcal{F}^{(\\infty)}(G)$ with the product *.\n"
    )
    clean_lie = lie_mc.cleaner.clean(raw_lie_p262, 262).body
    assert "@@FNSTART@@" not in clean_lie
    assert "(t * t') * u = t * (t' * u)" in clean_lie

    riemann_mc = MonographCompiler(book_by_key("riemann").spec)
    raw_riemann_p57 = (
        "Assume that these equations are linearly independent*, this important proposition follows:\n\n"
        "*Subject to this condition, uniform functions of position exist only if $m \\geq p + 1$; and these functions contain $m - p + 1$ arbitrary constants which enter linearly.*\n\n"
        "Now let the $m$ infinities be moveable, then $m$ new degrees\n\n"
        "* If they are not so, the consequence will be that the number of uniform functions will be *greater* than that given in the text.\n"
    )
    clean_riemann = riemann_mc.cleaner.clean(raw_riemann_p57, 57).body
    assert clean_riemann.count("@@FNSTART@@") == 1
    assert "*Subject to this condition" in clean_riemann
    assert "independent@@FNSTART@@If they are not so" in clean_riemann

    ficht_mc = MonographCompiler(book_by_key("fichtenholz_vol1").spec)
    raw_ficht_p97 = (
        "它就称为函数 $y = f(x)$ 的反函数$^{15}$ .\n\n"
        "考察例题:\n\n"
        "1) 设 $y = a^x (a > 1)$ .\n\n"
        "$^{15)}$ 如果函数 $f$ 的反函数是单值的,那么函数本身称为可逆的.\n"
    )
    clean_ficht = ficht_mc.cleaner.clean(raw_ficht_p97, 97).body
    assert clean_ficht.count("@@FNSTART@@") == 1
    assert "反函数@@FNSTART@@如果函数 $f$ 的反函数是单值的" in clean_ficht


def test_symbol_notes_with_multiline_displays_preserve_math_parity_and_compile(tmp_path: Path):
    go_spec = book_by_key("goursat").spec
    go_mc = MonographCompiler(go_spec)
    raw_p29 = (
        "Hence the ratio approaches zero as a limit, and we find $f_{xy} = 0$.*\n\n"
        "* A similar remark may be made regarding functions of a single variable. "
        "For example, $f(x) = x^3 \\cos 1/x$ has the derivative\n\n"
        "$$f'(x) = 3x^2 \\cos \\frac{1}{x} + x \\sin \\frac{1}{x},$$\n\n"
        "and $f'(x)$ has no derivative for $x = 0$. But the ratio\n\n"
        "$$\n\\frac{f(2\\alpha) - 2f(\\alpha) + f(0)}{\\alpha^2},\n$$\n\n"
        "or $8\\alpha \\cos(1/2\\alpha) - 2\\alpha \\cos(1/\\alpha)$, has the limit zero.\n"
    )
    raw_p30 = (
        "# III. THE DIFFERENTIAL NOTATION\n\n"
        "The differential notation, which has been in use longer than any other,* is due to Leibniz.\n\n"
        "* With the possible exception of Newton's notation. — TRANS.\n"
    )
    raw_p378 = (
        "This gives the formula (A) which was to be proved.*\n\n"
        "176. Examples. 1) Let us return to the integral:\n\n"
        "$$\n- \\int_0^{+\\infty} e^{-\\alpha x} \\sin x \\, dx,\n$$\n\n"
        "* The formula for differentiation may be deduced easily from (A). If $\\alpha$ lies in $(\\alpha_0, \\alpha_1)$, we have\n\n"
        "$$\n\\int_{\\alpha_0}^{\\alpha} du \\int_{\\alpha_0}^{+\\infty} f_u(x, u) dx = \\int_{\\alpha_0}^{+\\infty} dx \\int_{\\alpha_0}^{\\alpha} f_u(x, u) du,\n$$\n\n"
        "where $\\alpha$ has been replaced by $u$. Finally we find\n\n"
        "$$\nF'(\\alpha) = \\Phi(\\alpha).\n$$\n"
    )
    c29 = go_mc.cleaner.clean(raw_p29, 29).body
    c30 = go_mc.cleaner.clean(raw_p30, 30).body
    c378 = go_mc.cleaner.clean(raw_p378, 378).body
    for page_body in (c29, c30, c378):
        assert "$$" not in page_body.split("@@FNSTART@@")[1].split("@@FNEND@@")[0]
    typ_body = go_mc.format_typst(f"{c29}\n\n{c30}\n\n{c378}")
    assert "@@FNSTART@@" not in typ_body and "F N E N D" not in typ_body
    typ_file = tmp_path / "goursat.typ"
    pdf_file = tmp_path / "goursat.pdf"
    typ_file.write_text(
        go_mc.build_typst_preamble() + "\n" + typst_footnote_rules(go_spec) + "\n" + typ_body,
        encoding="utf-8",
    )
    compile_typst(typ_file, pdf_file)
    assert pdf_file.exists()





