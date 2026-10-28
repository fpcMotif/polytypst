import subprocess

import pymupdf
import pytest

from polytypst.books import module
from polytypst.compiler.diagrams import parse_array_diagram
from polytypst.compiler.monograph import MonographCompiler
from polytypst.compiler.source_numbers import (
    LATEX,
    TYPST,
    TYPST_RULES,
    labels,
    link_citations,
    link_references,
    number_chapter,
)
from polytypst.literal_numbers import literal_numbering_counts

GROTHENDIECK_SPEC = module("grothendieck", "spec").GROTHENDIECK_SPEC


def test_paragraph_and_equation_numbers_come_from_counters():
    text = (
        "== § 1. Foncteurs représentables\n\n=== 1.1. Produits fibrés\n\n"
        "#strong[(1.1.1)] Soient $C$ une catégorie.\n\n"
        "$ g mapsto ( p_1 compose g ) $ <eq-1-1-1-1>\n\n"
        "#strong[Proposition (1.1.2)] Considérons.\n\n"
        "#strong[Lemme (1.1.3).] Soit."
    )
    out, resyncs = number_chapter(text, 1)
    assert "(1.1.1)" not in out and "(1.1.2)" not in out and "§ 1" not in out and "1.1." not in out
    assert "== Foncteurs représentables" in out and "=== Produits fibrés" in out
    assert '#source-paragraph[]#metadata("paragraph") <par-c1-1-1-1>' in out
    assert '#source-paragraph[Proposition]#metadata("paragraph") <par-c1-1-1-2>' in out
    assert '#source-paragraph[Lemme]#metadata("paragraph") <par-c1-1-1-3> Soit.' in out
    assert "numbering: source-equation-number, $ g mapsto ( p_1 compose g ) $) <eq-c1-1-1-1-1>" in out
    assert resyncs == []


def test_a_three_level_heading_number_comes_from_the_counters():
    text = "== 1 区域内贸易\n\n=== 1.1 出口\n\n==== 1.1.1 面向发达国家市场的出口情况\n\n正文。"
    typst, resyncs = number_chapter(text, 6)
    assert "==== 面向发达国家市场的出口情况" in typst and "1.1.1" not in typst
    latex, _ = number_chapter(text.replace("====", "####").replace("===", "###").replace("==", "##"), 6, LATEX)
    assert r"\sourcesubsubsection{面向发达国家市场的出口情况}" in latex
    assert resyncs == []


def test_a_display_equation_with_a_line_break_gets_a_counter_label():
    text = "== 1 前言\n\n$ p_11 = a \\\np_00 = b $ <eq-13-4>\n"
    out, _ = number_chapter(text, 13)
    assert "<eq-13-4>" not in out
    assert "<eq-c13-13-4>" in out


def test_a_number_the_counters_would_miss_is_resynced_and_reported():
    text = "== § 1. Foncteurs\n\n=== 1.1. Objets\n\n=== 1.2. Produits\n\n#strong[(1.2.1)] A.\n\n#strong[(1.2.3)] B."
    out, resyncs = number_chapter(text, 1)
    assert "#counter(heading).update((..c) => (c.pos().at(0, default: 0), 1, 2, 2))\n#source-paragraph" in out
    assert [r.line() for r in resyncs] == ["chapter 1: paragraph 1.2.3 would have been numbered 1.2.2"]


def test_a_paragraph_at_the_top_of_a_scan_page_keeps_its_page_mark():
    text = "== § 1. Foncteurs\n\n=== 1.1. Objets\n\n#strong[(1.1.1)] A.\n\n#src-top(28);(1.1.2) B."
    out, resyncs = number_chapter(text, 1)
    assert '#src-top(28);#source-paragraph[]#metadata("paragraph") <par-c1-1-1-2> B.' in out
    assert resyncs == []


def test_references_link_to_labels_in_this_and_other_chapters():
    known = labels("<par-c1-1-2-9> <par-c1-4-3-2> <eq-c2-1-3-2-1>")
    text = "résulte de (1.2.9). Voir (0, 4.3.2), (1.3.2.1) et (5.9.9); $x = (1.2.9)$"
    out = link_references(text, 2, {"0": 1, "I": 2}, known)
    assert "résulte de (1.2.9)." in out
    out = link_references("résulte de (1.2.9).", 1, {"0": 1, "I": 2}, known)
    assert out == "résulte de @par-c1-1-2-9."
    out = link_references(text, 2, {"0": 1, "I": 2}, known)
    assert "Voir @par-c1-4-3-2[0], @eq-c2-1-3-2-1 et (5.9.9)" in out
    assert "$x = (1.2.9)$" in out


ABBREVIATIONS = {"T": "6", "G": "5"}


def test_citations_link_to_their_bibliography_entries():
    body = (
        "chez Kähler \\[8\\], voir \\[17\\] ((T, 1.7, d) et SGA, 3, I), (G, II, 5.9, cor. du th. 5.9.1), "
        "\\[4 bis\\], \\[SGA 4\\], I; consulter (T) et (T, X); $F(T, 1.2) = [8]$"
    )
    assert link_citations(["Hom(X', F(T))", "\\[6\\] Grothendieck."], ABBREVIATIONS)[0] == "Hom(X', F(T))"
    two_lines = "$ cal(G) ( cal(T) )\\\ncal(G) (T, 1.2) $"
    assert link_citations([two_lines, "\\[6\\] Grothendieck."], ABBREVIATIONS)[0] == two_lines
    assert link_citations(["#src-top(462);\\[1\\] Bourbaki."], {})[0] == (
        '#src-top(462);#metadata("citation") <bib-1>\\[1\\] Bourbaki.'
    )
    bibliography = "\\[4 bis\\] Giraud.\n\n\\[5\\] Godement.\n\n\\[6\\] Grothendieck.\n\n\\[8\\] Kähler.\n\n\\[SGA\\] Séminaire."
    out, bib = link_citations([body, bibliography], ABBREVIATIONS)
    assert out == (
        "chez Kähler #link(<bib-8>)[\\[8\\]], voir \\[17\\] ((#link(<bib-6>)[T, 1.7, d]) et #link(<bib-SGA>)[SGA], 3, I), "
        "(#link(<bib-5>)[G, II, 5.9, cor. du th. 5.9.1]), #link(<bib-4-bis>)[\\[4 bis\\]], "
        "#link(<bib-SGA>)[\\[SGA 4\\]], I; consulter (#link(<bib-6>)[T]) et (T, X); $F(T, 1.2) = [8]$"
    )
    assert bib.startswith('#metadata("citation") <bib-4-bis>\\[4 bis\\] Giraud.\n\n#metadata("citation") <bib-5>\\[5\\]')
    assert '#metadata("citation") <bib-SGA>\\[SGA\\] Séminaire.' in bib


def test_latex_citations_use_hyperlinks():
    text = "Kähler [8] et (T, 1.2), sans [5] ici (G, I, 1.9); $[8]$"
    out, bib = link_citations([text, "[6] Grothendieck.\n\n[8] Kähler."], ABBREVIATIONS, LATEX)
    assert out == "Kähler \\hyperlink{bib-8}{[8]} et (\\hyperlink{bib-6}{T, 1.2}), sans [5] ici (G, I, 1.9); $[8]$"
    assert bib == "\\hypertarget{bib-6}{}[6] Grothendieck.\n\n\\hypertarget{bib-8}{}[8] Kähler."


def test_multi_section_bibliographies_receive_unique_labels_per_section():
    ch1 = "Voir \\[1\\] et \\[4\\].\n\n\\[1\\] Artin.\n\n\\[4\\] Deligne."
    ch2 = "Voir \\[1\\], \\[4\\] et \\[9\\].\n\n\\[1\\] Bourbaki.\n\n\\[4\\] Grothendieck.\n\n\\[9\\] Serre."
    out1, out2 = link_citations([ch1, ch2], {})
    assert '<bib-s0-1>\\[1\\] Artin.' in out1
    assert '<bib-s1-1>\\[1\\] Bourbaki.' in out2
    assert '#link(<bib-s0-1>)[\\[1\\]]' in out1
    assert '#link(<bib-s1-1>)[\\[1\\]]' in out2
    assert '<bib-9>\\[9\\] Serre.' in out2
    assert '#link(<bib-9>)[\\[9\\]]' in out2


def test_figures_receive_counter_numbering_labels_and_linked_references():
    ch = (
        "== § 1. Courbes\n\n"
        "Voir Fig. 1.1 et Figure 1.2.\n\n"
        '#figure(\n  image("figures/fig_1_1.svg", width: 50%),\n  caption: [#strong[Fig. 1.1.] Le cercle.],\n  supplement: none\n)\n\n'
        '#figure(\n  image("figures/fig_1_2.svg", width: 50%),\n  caption: [#strong[Figure 1.2]]\n)'
    )
    numbered, _ = number_chapter(ch, 1)
    assert "<fig-1-1>" in numbered and "<fig-1-2>" in numbered
    assert "supplement: none" not in numbered
    assert "Fig. 1.1." not in numbered.split("#figure", 1)[1]
    known = labels(numbered)
    assert {"fig-1-1", "fig-1-2"} <= known
    linked = link_references(numbered, 1, {}, known)
    assert "Voir @fig-1-1 et @fig-1-2." in linked


def test_a_sub_numbered_chinese_figure_gets_its_own_label_and_reference():
    ch = (
        "== 10 工资差距\n\n"
        "其中一种是不分年龄段的统计（图 10-6.1），另一种见图 10-6.2。\n\n"
        '#figure(\n  image("figures/fig_10-6.1.png", width: 50%),\n  caption: [图 10-6.1 基尼系数（男性）]\n)\n\n'
        '#figure(\n  image("figures/fig_10-6.2.png", width: 50%),\n  caption: [图 10-6.2 基尼系数（男性雇员）]\n)'
    )
    numbered, _ = number_chapter(ch, 10)
    assert "<fig-10-6-1>" in numbered and "<fig-10-6-2>" in numbered
    assert 'numbering: _ => "10-6.1"' in numbered
    linked = link_references(numbered, 10, {}, labels(numbered))
    assert "（@fig-10-6-1），另一种见@fig-10-6-2。" in linked


def test_a_reference_followed_by_a_dot_and_a_digit_ends_before_the_dot():
    known = labels("<fig-10-6>")
    assert link_references("如图 10-6.1 所示", 10, {}, known) == "如图 10-6.1 所示"
    assert link_references("见图 10-6.", 10, {}, known) == "见@fig-10-6."



def test_latex_numbers_come_from_counters_and_references_use_ref():
    markdown = (
        "## § 1. Foncteurs représentables\n\n### 1.1. Objets\n\n"
        "**Proposition (1.1.1)** Soient $C$ une catégorie.\n\n"
        "$$\ng \\mapsto (p_1 \\circ g)\n$$ <eq-1-1-1-1>\n\n"
        "(1.1.3) Voir (1.1.1) et (1.1.1.1)."
    )
    out, resyncs = number_chapter(markdown, 1, LATEX)
    assert "\\sourcesection{Foncteurs représentables}" in out and "\\sourcesubsection{Objets}" in out
    assert "\\sourceparagraph{Proposition }\\label{par-c1-1-1-1} Soient" in out
    assert "\\begin{equation}\ng \\mapsto (p_1 \\circ g)\n\\label{eq-c1-1-1-1-1}\\end{equation}" in out
    assert "\\setcounter{sourcesection}{1}\\setcounter{sourcesubsection}{1}\\setcounter{sourceparagraph}{2}" in out
    assert [r.line() for r in resyncs] == ["chapter 1: paragraph 1.1.3 would have been numbered 1.1.2"]
    linked = link_references(out, 1, {"0": 1}, labels(out), LATEX)
    assert "Voir (\\ref{par-c1-1-1-1}) et \\eqref{eq-c1-1-1-1-1}." in linked
    assert "(0, \\ref{par-c1-1-1-1})" in link_references("(0, 1.1.1)", 2, {"0": 1}, labels(out), LATEX)


def test_parenthesized_notes_attach_to_their_calls():
    page = (
        "Soit $C$ une catégorie$^{(1)}$; pour deux objets.\n\n---\n\n"
        "$^{(1)}$ Nous considérons les catégories d'un point de vue «naïf».\n"
    )
    text, _, _ = MonographCompiler(GROTHENDIECK_SPEC).cleaner.clean(page, 27)
    assert "catégorie@@FNSTART@@Nous considérons les catégories d'un point de vue «naïf».@@FNEND@@;" in text
    assert "---" not in text


def test_a_lost_vertical_arrow_keeps_its_label():
    diagram = parse_array_diagram(
        r"\begin{array}{ccccc}"
        r"X & \xleftarrow{p} & X_{(\varphi)} & \xleftarrow{p'} & (X_{(\varphi)})_{(\varphi')} \\"
        r"\pi & & & & \pi' \\"
        r"S & \xleftarrow{\varphi} & S' & \xleftarrow{\varphi'} & S''"
        r"\end{array}"
    )
    assert diagram is not None
    arrows = {(a.source, a.target, a.label, a.side) for a in diagram.arrows}
    assert ((1, 0), (0, 0), "p", "right") in arrows
    assert ((0, 0), (0, 1), r"\pi", "right") in arrows
    assert ((2, 0), (2, 1), r"\pi'", "right") in arrows
    assert ((2, 1), (1, 1), r"\varphi'", "left") in arrows


def test_slanted_arrows_point_the_way_their_names_say():
    diagram = parse_array_diagram(
        r"\begin{array}{ccc} A & \xrightarrow{v} & C \\ u \searrow & \nearrow w & \\ & B & \end{array}"
    )
    assert diagram is not None
    ends = {a.label: (a.source, a.target) for a in diagram.arrows}
    assert ends["u"] == ((0, 0), (1, 1))
    assert ends["w"] == ((1, 1), (2, 0))


def test_an_array_of_plain_entries_is_not_a_diagram():
    assert parse_array_diagram(r"\begin{array}{cc} a & b \\ c & d \\ e & f \end{array}") is None


def test_articles_roman_items_figures_and_references_use_counters_in_typst_and_latex():
    raw_typ = (
        "= 无穷小\n\n== § 4. 无穷小的比较\n\n=== 54. 预备命题\n\n=== 56. 根式的极限\n\n=== 61. 无穷小的尺度\n\n"
        "I. 设两个无穷小.\n\nII. 同阶.\n\nIII. 尺度.\n\n=== 62. 等价无穷小\n\n"
        "IV. 无穷小 $alpha$ 与 $beta$ 称为等价无穷小, 见 \\[61\\], \\[54, 4) 及 5)\\], 在 56, 3) 内及 \\[62(1)\\], 参阅图 119.\n\n"
        "$ lim_(z -> 0) beta / alpha = 1 $ <eq-1>\n\n"
        '#figure(\n  image("figures/fig_119.svg", width: 50%),\n  caption: [#strong[图 119] 圆外旋轮线],\n  supplement: none\n)'
    )
    assert set(literal_numbering_counts(raw_typ + " ①", TYPST)) >= {
        "LITERAL_HEADING_NUMBER",
        "LITERAL_ITEM_HEAD",
        "LITERAL_FIGURE_CAPTION",
    }
    num_typ, _ = number_chapter(raw_typ, 2, TYPST)
    linked_typ = link_references(num_typ, 2, {}, labels(num_typ), TYPST)
    assert "#heading(level: 3, numbering: source-article-number)[等价无穷小] <art-62>" in linked_typ
    assert "#source-roman-item 无穷小" in linked_typ
    assert "<eq-art-62-1>" in linked_typ and "<fig-119>" in linked_typ
    assert "\\[@art-61\\]" in linked_typ
    assert "\\[@art-54, 4) 及 5)\\]" in linked_typ
    assert "在 @art-56, 3) 内" in linked_typ
    assert "\\[@art-62@eq-art-62-1\\]" in linked_typ
    assert "参阅@fig-119." in linked_typ
    assert literal_numbering_counts(linked_typ, TYPST) == {}

    raw_tex = (
        "\\chapter{无穷小}\n\n## § 4. 无穷小的比较\n\n### 54. 预备命题\n\n### 56. 根式的极限\n\n### 61. 无穷小的尺度\n\n"
        "I. 设两个无穷小.\n\nII. 同阶.\n\nIII. 尺度.\n\n### 62. 等价无穷小\n\n"
        "IV. 无穷小 $\\alpha$ 与 $\\beta$ 称为等价无穷小, 见 [61], [54, 4) 及 5)], 在 56, 3) 内及 [62(1)], 参阅图 119.\n\n"
        "$$\n\\lim_{z \\to 0} \\frac{\\beta}{\\alpha} = 1\n$$ <eq-1>\n\n"
        "![**图 119** 圆外旋轮线](figures/fig_119.svg)"
    )
    num_tex, _ = number_chapter(raw_tex, 2, LATEX)
    linked_tex = link_references(num_tex, 2, {}, labels(num_tex), LATEX)
    assert "\\sourcearticle{等价无穷小}\\label{art-62}" in linked_tex
    assert "\\sourceroman 无穷小" in linked_tex
    assert "\\label{eq-art-62-1}\\end{equation}" in linked_tex
    assert "\\caption{圆外旋轮线}\\label{fig-119}" in linked_tex
    assert "[\\ref{art-61}]" in linked_tex
    assert "[\\ref{art-54}, 4) 及 5)]" in linked_tex
    assert "在 \\ref{art-56}, 3) 内" in linked_tex
    assert "[\\ref{art-62}\\eqref{eq-art-62-1}]" in linked_tex
    assert "参阅图 \\ref{fig-119}." in linked_tex
    assert literal_numbering_counts(linked_tex, LATEX) == {}


def test_circled_run_in_labels_use_a_counter_that_restarts_with_each_run():
    raw = "==== （1） 实际\n\n①实际资本存量\n\n文本。\n\n②制造业\n\n④实际周转\n\n==== （2） 潜在\n\n①制造业潜在\n\n③潜在周转\n\n设 ①在句中。"
    out, resyncs = number_chapter(raw, 1, TYPST, circled=True)
    assert "#source-circled.update(0)\n#source-circled-item;实际资本存量" in out
    assert "#source-circled-item;制造业潜在" in out
    assert "#source-circled.update(3)\n#source-circled-item;实际周转" in out
    assert "#source-circled.update(0)\n#source-circled-item;制造业潜在" in out
    assert "#source-circled.update(2)\n#source-circled-item;潜在周转" in out
    assert "设 ①在句中" in out
    assert [r.kind for r in resyncs] == ["circled", "circled"]
    assert set(literal_numbering_counts(out.replace("设 ①在句中。", ""), TYPST)) == set()
    tex, _ = number_chapter(raw.replace("====", "####"), 1, LATEX, circled=True)
    assert "\\sourcecircled{}实际资本存量" in tex and "①" not in tex.replace("设 ①在句中", "")
    assert number_chapter(raw, 1, TYPST)[0].count("①") == 3


def test_latex_figures_fit_the_text_block():
    raw = "### 1. 前言\n\n![**图 1-1** 进口渗透和就业](figures/fig_1-1.png)"
    numbered, _ = number_chapter(raw, 1, LATEX)
    assert r"\includegraphics[width=\linewidth,height=0.75\textheight,keepaspectratio]{figures/fig_1-1.png}" in numbered
    assert r"\caption{进口渗透和就业}\label{fig-1-1}" in numbered


def test_subsections_under_articles_print_their_own_decimal_number(tmp_path):
    raw = "= 进口竞争\n\n=== 1. 前言\n\n正文.\n\n=== 2. 衡量进口竞争的标准\n\n=== 2.1 进口渗透率\n\n=== 2.2 进口相对价格\n\n=== 3. 结束语\n"
    numbered, _ = number_chapter(raw, 1, TYPST)
    typ = tmp_path / "doc.typ"
    _ = typ.write_text(TYPST_RULES + numbered, encoding="utf-8")
    _ = subprocess.run(["typst", "compile", str(typ)], check=True)
    with pymupdf.open(typ.with_suffix(".pdf")) as doc:
        lines = [line.strip() for page in doc for line in page.get_text().splitlines() if line.strip()]
    assert "2.1. 进口渗透率" in lines
    assert "2.2. 进口相对价格" in lines
    assert "2. 衡量进口竞争的标准" in lines
    assert "3. 结束语" in lines


def test_each_article_without_a_label_prints_its_own_number(tmp_path):
    seen: set[str] = set()
    chapters = (
        "= 泡沫\n\n=== 1. 前言\n\n=== 2. 观点\n\n=== 3. 危机\n",
        "= 全球化\n\n正文.\n\n=== 2. 观点\n\n=== 3. 再检验\n\n=== 4. 本文的研究分析\n",
        "= 零利率\n\n=== 1. 问题\n\n=== 2. 要点\n",
    )
    numbered = [number_chapter(text, n, TYPST, seen)[0] for n, text in enumerate(chapters, start=1)]
    typ = tmp_path / "doc.typ"
    _ = typ.write_text(TYPST_RULES + "".join(numbered), encoding="utf-8")
    _ = subprocess.run(["typst", "compile", str(typ)], check=True)
    with pymupdf.open(typ.with_suffix(".pdf")) as doc:
        lines = [line.strip() for page in doc for line in page.get_text().splitlines() if line.strip()]
    assert [line for line in lines if line[0].isdigit()] == [
        "1. 前言", "2. 观点", "3. 危机",
        "2. 观点", "3. 再检验", "4. 本文的研究分析",
        "1. 问题", "2. 要点",
    ]


def test_article_numbers_do_not_link_dates_multiples_or_journal_volumes():
    body = (
        "日本也在4月7日上调了基准利率, 在 4 月恢复.\n\n"
        "{lb}1990 年的倍率为 6.80 倍, 约为其 2 倍.{rb}\n\n"
        "Brunello, G. (1990), Journal of the Japanese Economies, 4 (2), pp. 121–138.\n\n"
        "Saxonhouse (1993), Journal of Economic Perspectives, 7 (3), pp. 21–43.\n\n"
        "参看 {lb}2{rb} 与在 4 内."
    )
    cases = (
        (TYPST, "===", "\\[", "\\]", lambda n: f"@art-{n}"),
        (LATEX, "###", "[", "]", lambda n: rf"\ref{{art-{n}}}"),
    )
    for writer, marks, lb, rb, ref in cases:
        raw = "".join(f"{marks} {n}. 标题{n}\n\n" for n in (1, 2, 4, 7)) + body.format(lb=lb, rb=rb)
        numbered, _ = number_chapter(raw, 1, writer)
        linked = link_references(numbered, 1, {}, labels(numbered), writer)
        assert "在4月7日" in linked
        assert "在 4 月恢复" in linked
        assert "约为其 2 倍" in linked
        assert "Economies, 4 (2), pp." in linked
        assert "Perspectives, 7 (3), pp." in linked
        assert f"{lb}{ref(2)}{rb}" in linked and f"在 {ref(4)} 内" in linked


def test_a_latex_figure_includes_the_png_beside_an_svg():
    out, _ = number_chapter("![图 1-2 非线性规则](figures/fig_1-2.svg)", 1, LATEX)
    assert "{figures/fig_1-2.png}" in out


def test_a_latex_figure_caption_escapes_percent_ampersand_and_hash():
    out, _ = number_chapter("![图 8-5 前1%高收入群体 & 第#1组](figures/fig_8-5.png)", 1, LATEX)
    assert "\\caption{前1\\%高收入群体 \\& 第\\#1组}" in out


@pytest.mark.slow
def test_a_latex_figure_caption_prints_its_source_number(tmp_path):
    out, _ = number_chapter("![图 8-8 4 变量 VAR 模型](figures/fig_8-8.png)\n\n见图 8-8。", 1, LATEX)
    linked = link_references(out, 1, {}, labels(out), LATEX)
    assert literal_numbering_counts(linked, LATEX) == {}
    pymupdf.open().new_page().get_pixmap().save(tmp_path / "fig_8-8.png")
    body = linked.replace("figures/fig_8-8.png", "fig_8-8.png")
    source = tmp_path / "f.tex"
    _ = source.write_text(
        "\\documentclass{article}\\usepackage{graphicx}\\usepackage{caption}"
        "\\captionsetup[figure]{labelformat=empty}\\usepackage{fontspec}\\setmainfont{Songti SC}"
        f"\\begin{{document}}{body}\\end{{document}}",
        encoding="utf-8",
    )
    for _pass in range(2):
        _ = subprocess.run(["xelatex", "-interaction=nonstopmode", "f.tex"], check=False, cwd=tmp_path, capture_output=True)
    text = "".join(page.get_text() for page in pymupdf.open(tmp_path / "f.pdf"))
    text = text.replace(" ", "").replace(" ", "")
    assert "图8-84变量VAR模型" in text
    assert "见图8-8" in text
