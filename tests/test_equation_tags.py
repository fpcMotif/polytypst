import re
import shutil
import subprocess

import pymupdf

from polytypst.compiler.monograph import MonographCompiler, MonographSpec
from polytypst.compiler.page_cleaner import (
    PageCleaner,
    _label_page_equations,
    _label_section_equations,
)
from polytypst.compiler.source_numbers import (
    LATEX,
    LATEX_RULES,
    TYPST,
    TYPST_EQUATION_LAYOUT,
    TYPST_RULES,
    labels,
    link_references,
    number_chapter,
)
from polytypst.literal_numbers import literal_numbering_counts


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


def test_consecutive_displays_with_post_tags_and_cjk_standalone_tag_keep_each_number():
    zh_cleaner = PageCleaner.for_spec(
        MonographSpec("t", "T", "A", domain="math", lang="zh", cross_references=True)
    )
    cjk_page = (
        "考虑：(1) 连续，(2) 可微。\n\n"
        "$$y = x - \\varepsilon \\cdot \\sin x$$\n\n(3)\n\n很易指出函数单调增大。"
    )
    cjk_body = zh_cleaner.clean(cjk_page, 153).body
    assert "（1） 连续，（2） 可微" in cjk_body
    assert "<eq-3>" in cjk_body
    assert "（3）" not in cjk_body and "(3)" not in cjk_body

    seq_page = (
        "$$\\hat{\\mu} = \\frac{1}{N} \\sum_{n=1}^{N} x^{(n)}$$\n\n(2.1)\n\n"
        "$$\\hat{\\sigma} = \\sqrt{\\frac{1}{N} \\sum_{n=1}^{N} (x^{(n)} - \\hat{\\mu})^2}$$\n\n(2.2)\n\n"
        "上面式子给出参数估计。"
    )
    seq_body = zh_cleaner.clean(seq_page, 54).body
    assert "<eq-2-1>" in seq_body and "<eq-2-2>" in seq_body
    assert "(2.1)" not in seq_body and "(2.2)" not in seq_body

    page_cleaner = PageCleaner.for_spec(
        MonographSpec("t", "T", "A", domain="math", equation_numbering="page")
    )
    page_out = page_cleaner.clean("$$a = b$$\n\n(1)\n\n$$c = d$$\n\n(2)", 10).body
    assert "<eq-0-10-1>" in page_out and "<eq-0-10-2>" in page_out


def test_multipart_tag_aligned_end_number_and_align_env_keep_clean_labels():
    cleaner = PageCleaner.for_spec(
        MonographSpec("t", "T", "A", domain="math", cross_references=True)
    )
    kashiwara_out = cleaner.clean(
        "$$P(x, D_x) u = 0 \\tag{4.3.58}$$\n\n$$Q(x, D_x) u = 0 \\tag{5.4}$$",
        252,
    ).body
    assert "<eq-4-3-58>" in kashiwara_out
    assert "<eq-5-4>" in kashiwara_out
    assert "\\tag" not in kashiwara_out

    aligned_out = cleaner.clean(
        "$$\n\\begin{aligned}\na &= b \\\\\n&= c \\quad (5.4)\n\\end{aligned}\n$$\n\n"
        "$$\n\\begin{aligned}\nf(x) &= g(x) + o(1)\n\\end{aligned}\n$$",
        116,
    ).body
    assert "<eq-5-4>" in aligned_out and "(5.4)" not in aligned_out
    assert "o(1)" in aligned_out and "<eq-1>" not in aligned_out

    compiler = MonographCompiler(MonographSpec("t", "T", "A", domain="math"))
    typ = compiler.format_typst("(1) \\begin{align} x &= y \\end{align}")
    assert "<eq-1>" in typ and "<eq-align-" not in typ


def test_suffixed_and_appendix_equation_tags_compile_with_counters(tmp_path):
    zh_spec = MonographSpec(
        "t", "T", "A", domain="math", lang="zh", cross_references=True, normalize_headings=False
    )
    cleaner = PageCleaner.for_spec(zh_spec)
    raw_zh = (
        "## § 3. 反函数\n\n"
        "### 73. 反函数例题\n\n"
        "$$y = x - \\varepsilon \\sin x$$\n\n(3)\n\n"
        "$$E = M + \\varepsilon \\sin E$$\n\n(3a)\n\n"
        "$$x = \\varphi(u, v)$$ \\quad (15)\n\n"
        "$$u = \\lambda(x, y), \\quad (15^*)$$\n\n"
        "关系式 (15) 与 (15*) 以及 (3a) 等价。\n\n"
        "$$\\frac{\\partial}{\\partial \\mu} \\log p(x) = \\Sigma^{-1}(x - \\mu)$$\n\n(A.6)\n\n"
        "推导用到了 (A.6)。"
    )
    cleaned = cleaner.clean(raw_zh, 153).body
    assert "<eq-3>" in cleaned
    assert "<eq-3a>" in cleaned
    assert "<eq-15-star>" in cleaned
    assert "<eq-A-6>" in cleaned

    en_cleaner = PageCleaner.for_spec(
        MonographSpec("t", "T", "A", domain="math", cross_references=True)
    )
    en_cleaned = en_cleaner.clean(
        "$$\\|x\\|^2 \\ge \\sum |c_k|^2$$\n\n(1')\n\nBy equation (1') and condition (26a),\n\n$$a^q \\equiv 1$$\n\n(26a)",
        149,
    ).body
    assert "<eq-1-prime>" in en_cleaned and "<eq-26a>" in en_cleaned

    compiler = MonographCompiler(zh_spec)
    typ_body = compiler.format_typst(cleaned)
    num_typ, _resyncs = number_chapter(typ_body, 5, TYPST)
    linked_typ = link_references(num_typ, 5, {}, labels(num_typ), TYPST)
    assert literal_numbering_counts(linked_typ, TYPST) == {}
    assert "@eq-art-73-15-star" in linked_typ
    assert "@eq-art-73-3a" in linked_typ
    assert "@eq-c5-A-6" in linked_typ

    if shutil.which("typst"):
        typ_doc = (
            compiler.build_typst_preamble()
            + "\n"
            + TYPST_RULES
            + "\n"
            + TYPST_EQUATION_LAYOUT
            + "\n"
            + linked_typ
        )
        typ_file = tmp_path / "eq.typ"
        typ_file.write_text(typ_doc, encoding="utf-8")
        subprocess.run(["typst", "compile", str(typ_file)], check=True)
        with pymupdf.open(typ_file.with_suffix(".pdf")) as doc:
            pdf_text = "\n".join(p.get_text() for p in doc)
        for tag in ("(3)", "(3a)", "(15*)", "(A.6)"):
            assert tag in pdf_text

    num_tex, _ = number_chapter(cleaned, 5, LATEX)
    linked_tex = link_references(num_tex, 5, {}, labels(num_tex), LATEX)
    assert literal_numbering_counts(linked_tex, LATEX) == {}
    assert r"\eqref{eq-art-73-15-star}" in linked_tex
    assert r"\eqref{eq-art-73-3a}" in linked_tex
    assert r"\eqref{eq-c5-A-6}" in linked_tex
    if shutil.which("tectonic"):
        tex_file = tmp_path / "eq.tex"
        tex_body = re.sub(r"[\u4e00-\u9fff。，]", "x", linked_tex)
        tex_file.write_text(
            "\\documentclass{article}\\usepackage{amsmath}\\usepackage{hyperref}"
            f"{LATEX_RULES}\\begin{{document}}{tex_body}\\end{{document}}",
            encoding="utf-8",
        )
        res = subprocess.run(
            ["tectonic", "-X", "compile", "-C", str(tex_file)],
            check=False,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            with pymupdf.open(tex_file.with_suffix(".pdf")) as doc:
                tex_pdf_text = "\n".join(p.get_text() for p in doc)
            for tag in ("(3)", "(3a)", "(15*)", "(A.6)"):
                assert tag in tex_pdf_text


def test_enumerated_list_items_with_pure_math_stay_inline_across_clean_and_repair():
    cleaner = PageCleaner.for_spec(
        MonographSpec("t", "T", "A", domain="math", cross_references=True, repair_math=True)
    )
    hecke_page = (
        "for each integer $a$, which has the following properties:\n\n"
        "(1) $\\chi(a) = \\chi(b)$, if $a \\equiv b \\pmod{n}$.\n\n"
        "(2) $\\chi(a)\\chi(b) = \\chi(ab)$.\n\n"
        "(3) $\\chi(a) \\neq 0$ for all $a$ relatively prime to $n$."
    )
    hecke_out = cleaner.clean(hecke_page, 59).body
    assert "$$" not in hecke_out and "<eq-" not in hecke_out
    assert "(2) $\\chi(a)\\chi(b) = \\chi(ab)$." in hecke_out

    kodaira_page = (
        "**Schwarz's Lemma.** Satisfying:\n\n"
        "(1) $|f(z)| \\leq 1$ for all $z$,\n\n"
        "(2) $f(0) = 0$,\n\n"
        "then\n\n$$|f(z)| \\leq |z|, \\qquad (3.11)$$"
    )
    kodaira_out = cleaner.clean(kodaira_page, 141).body
    assert "(2) $f(0) = 0$," in kodaira_out
    assert "<eq-2>" not in kodaira_out and "<eq-3-11>" in kodaira_out

    algebra_sol_page = (
        "(3) $J(A) = \\text{diag}(2, 4, 4), \\quad J(B) = J_1(2) + J_2(4)$.\n\n"
        "**2.4.5** 研究域 $\\mathfrak{K}$ 的扩张域。"
    )
    zh_cleaner = PageCleaner.for_spec(
        MonographSpec("t", "T", "A", domain="math", lang="zh", cross_references=True, repair_math=True)
    )
    alg_out = zh_cleaner.clean(algebra_sol_page, 323).body
    assert "$$" not in alg_out and "<eq-" not in alg_out


def test_display_footnote_preserves_equation_tag_and_goursat_enables_numbering() -> None:
    from pathlib import Path

    from polytypst.books import books

    bourbaki_spec = MonographSpec(
        "t",
        "T",
        "A",
        domain="math",
        footnote_style="symbol",
        equation_numbering="section",
        cross_references=True,
    )
    bourbaki_page = (
        "Then $E_0^+ = \\{0\\}$ and\n\n"
        "(7)\n\n"
        "$$\n"
        "c^+(E_n^+) \\subset \\sum_{t=1}^{n-1} \\operatorname{Im}(E_t^+ \\otimes E_{n-1}^+) \\quad \\text{for } n \\geq 0. \\dagger\n"
        "$$\n\n"
        "As $E_0 = K.1$, we conclude by (7).\n\n"
        "† If $A$ and $B$ are two submodules of $E$, we denote by $\\operatorname{Im}(A \\otimes B)$ the image."
    )
    cleaned = PageCleaner.for_spec(bourbaki_spec).clean(bourbaki_page, 132).body
    assert "$$ <eq-7>@@FNSTART@@" in cleaned or ("$$ <eq-7>" in cleaned and "@@FNSTART@@" in cleaned)
    assert "(7)" not in cleaned.split("As $E_0")[0]
    assert "If $A$ and $B$ are two submodules" in cleaned

    latex_chapter = (
        "## I. FIRST SECTION\n\n"
        "$$\nf(x) = x\n$$ <eq-2>\n\n"
        "## II. SECOND SECTION\n\n"
        "$$\ng(x) = x^2\n$$ <eq-1>\n"
    )
    numbered_tex, _ = number_chapter(latex_chapter, 1, writer=LATEX)
    assert "\\setcounter{equation}{0}\n## II. SECOND SECTION" in numbered_tex

    goursat_spec = books()["goursat"].spec
    assert goursat_spec.equation_numbering == "none"
    goursat_p109 = (
        "**48. Taylor's series.** Therefore we have\n\n"
        "(7) $f(a + h) = f(a) + \\frac{h}{1!} f'(a) + \\cdots$"
    )
    goursat_cleaned = PageCleaner.for_spec(goursat_spec, Path()).clean(goursat_p109, 109).body
    assert "\\tag{7}" in goursat_cleaned
    assert "<eq-7>" in MonographCompiler(goursat_spec).format_typst(goursat_cleaned)
    goursat_tex, _ = number_chapter(goursat_cleaned, 3, writer=LATEX)
    assert "\\begin{equation}" in goursat_tex and "\\tag{7}" not in goursat_tex

    book4_spec = MonographSpec(
        "t",
        "T",
        "A",
        domain="math",
        lang="zh",
        footnote_style="circled",
        equation_numbering="section",
        cross_references=True,
    )
    book4_page = "$$\n\\begin{aligned}\nx &= 1 ① \\\\\ny &= 2\n\\end{aligned}\n\\quad (5.4)\n$$\n\n① 简化数学式。"
    book4_cleaned = PageCleaner.for_spec(book4_spec).clean(book4_page, 199).body
    assert "$$ <eq-5-4>@@FNSTART@@简化数学式。@@FNEND@@" in book4_cleaned
    book4_typ = MonographCompiler(book4_spec).format_typst(book4_cleaned)
    assert "<eq-5-4>" in book4_typ




