from dataclasses import replace

from polytypst.books import module
from polytypst.compiler.source_numbers import LATEX, TYPST
from polytypst.literal_numbers import edition_literal_counts, literal_numbering_counts

ALGEBRA3_SPEC = module("algebra3", "spec").ALGEBRA3_SPEC

ABBREVIATIONS = ("T", "G")

TYPST_BOOK = (
    '#set math.equation(numbering: "(1.1)")\n'
    + TYPST.chapter_start
    + '#source-paragraph[]#metadata("paragraph") <par-c1-1-1-3> Soit $X$ (1.1.9) un objet.\n\n'
    + '#strong[Proposition] #source-item#metadata("item") <par-c1-1-1-3-1> Voir @par-c1-1-1-3.\n\n'
    + "#emph[Exemples (1.5.5)] Soient $F$ et $(1.2.3)$ et\n\n$ x = 0 quad (1.1.3.1) $\n\n"
    + "Remarque (1.6.6) Soient (1.1.3) et (0, 4.5) et (I, 1.1.3) et (II, 1.1.3) chez #link(<bib-8>)[\\[8\\]] et \\[7\\],\n"
    + "(#link(<bib-6>)[T, 1.7, d]) mais (T, 1.2) et (G, I, 1.9).\n\n"
    + '#metadata("citation") <bib-8>\\[8\\] Kähler, E.\n'
)


def test_typst_counts_every_number_and_citation_typed_as_text():
    assert literal_numbering_counts(
        TYPST_BOOK, TYPST, ABBREVIATIONS, {"0": 0, "I": 1}
    ) == {
        "LITERAL_ITEM_HEAD": 2,
        "UNLINKED_REFERENCE": 2,
        "REFERENCE_WITHOUT_TARGET": 3,
        "UNLINKED_CITATION": 3,
        "LITERAL_NUMBER_IN_MATH": 2,
    }


LATEX_BOOK = (
    "\\documentclass{book}\\setcounter{equation}{1}\n"
    + LATEX.chapter_start
    + "\\sourceparagraph{}\\label{par-c1-1-1-3} Soit $X_{(1.1.3)}$ un objet.\n\n"
    + "\\textbf{Corollaire (1.7.3)} Voir (\\ref{par-c1-1-1-3}) et (1.1.3), (\\hyperlink{bib-6}{T, 1.1}) et [8].\n\n"
    + "\\[\nx = 0 \\quad (1.1.3.1)\n\\]\n\nchez \\hyperlink{bib-8}{{[}8{]}} et {[}FAC{]}.\n\n"
    + "\\hypertarget{bib-8}{}\n\n{[}8{]} Kähler, E.\n"
)


def test_latex_counts_every_number_and_citation_typed_as_text():
    assert literal_numbering_counts(LATEX_BOOK, LATEX, ABBREVIATIONS) == {
        "LITERAL_ITEM_HEAD": 1,
        "UNLINKED_REFERENCE": 1,
        "UNLINKED_CITATION": 2,
        "LITERAL_NUMBER_IN_MATH": 2,
    }


def test_a_book_of_counters_links_and_targets_has_no_literal_numbers():
    native = (
        TYPST.chapter_start
        + '#source-paragraph[]#metadata("paragraph") <par-c1-1-1-3> Voir @par-c1-1-1-3 et #link(<bib-8>)[\\[8\\]].\n\n'
        + '#metadata("citation") <bib-8>\\[8\\] Kähler, E.\n'
    )
    assert literal_numbering_counts(native, TYPST, ABBREVIATIONS) == {}


def test_counts_work_without_chapter_start_and_flag_headings_and_figures():
    unnumbered_typst = (
        '#set math.equation(numbering: "(1.1)")\n'
        "#outline(title: [Contents])\n"
        "= 1 Courbes\n\n"
        "== § 1. Foncteurs\n\n"
        "=== 1.1. Produits\n\n"
        "Voir Fig. 1.1 et [8].\n\n"
        '#figure(\n  image("figures/fig_1_1.svg", width: 50%),\n  caption: [#strong[Fig. 1.1.] Le cercle.],\n  supplement: none\n)\n'
    )
    assert literal_numbering_counts(unnumbered_typst, TYPST) == {
        "LITERAL_HEADING_NUMBER": 2,
        "LITERAL_FIGURE_CAPTION": 1,
        "UNLINKED_FIGURE_REFERENCE": 1,
        "UNLINKED_CITATION": 1,
    }


def test_orphaned_figure_captions_and_raster_fallbacks_are_counted():
    typst_with_leaks = (
        TYPST.chapter_start
        + '#figure(\n  image("figures/fig_1.png", width: 50%),\n  caption: [Le cercle.]\n) <fig-1>\n\n'
        + "#align(center)[\n  #emph[Figure 2. Le tore.]\n]\n\n"
        + "图 145\n"
    )
    assert literal_numbering_counts(
        typst_with_leaks, TYPST, require_vector_figures=True
    ) == {
        "RASTER_FIGURE_FALLBACK": 1,
        "ORPHANED_FIGURE_CAPTION": 2,
    }
    assert literal_numbering_counts(
        typst_with_leaks, TYPST, require_vector_figures=False
    ) == {
        "ORPHANED_FIGURE_CAPTION": 2,
    }

    latex_with_leaks = (
        LATEX.chapter_start
        + "\\begin{figure}\\includegraphics[width=0.5\\linewidth]{figures/fig_1.png}\\caption{Le cercle.}\\label{fig-1}\\end{figure}\n\n"
        + "\\begin{center}\\emph{Figure 2. Le tore.}\\end{center}\n\n"
        + "图 145\n"
    )
    assert literal_numbering_counts(
        latex_with_leaks, LATEX, require_vector_figures=True
    ) == {
        "RASTER_FIGURE_FALLBACK": 1,
        "ORPHANED_FIGURE_CAPTION": 2,
    }



def test_a_bold_head_ending_in_a_typed_number_is_literal_in_any_language():
    typst = (
        TYPST.chapter_start
        + "#strong[定理 7] 设 $P$ 含有 1 的 $n$ 个不相同的 $n$ 次根.\n\n"
        + "#strong[Theorem 3.1.] Let $X$ be a curve.\n\n"
        + "#strong[Satz 2] Es sei $X$ eine Kurve.\n\n"
        + "#strong[证明] 由定理 7 可知.\n\n"
        + "#strong[1.] Erstens.\n\n"
        + "见 #strong[定理 7] 的证明.\n"
    )
    latex = LATEX.chapter_start + "\\textbf{定理 7} 设 $P$ 是域.\n\n\\textbf{证明} 显然.\n"
    assert literal_numbering_counts(typst, TYPST) == {"LITERAL_ITEM_HEAD": 3}
    assert literal_numbering_counts(latex, LATEX) == {"LITERAL_ITEM_HEAD": 1}


def test_a_p_value_in_a_table_cell_is_not_a_reference():
    typst = TYPST.chapter_start + "#table(\n  columns: 2,\n  [二阶自相关检验], [0.41 (0.679)]\n)\n"
    latex = (
        LATEX.chapter_start
        + "\\begin{longtable}{ll}\n二阶自相关检验 & 0.41 (0.679) \\\\\n\\end{longtable}\n\n"
        + "\\begin{tabular}{ll}\nt & 1.55 (0.121) \\\\\n\\end{tabular}\n"
    )
    assert literal_numbering_counts(typst, TYPST) == {}
    assert literal_numbering_counts(latex, LATEX) == {}


def test_every_book_is_held_to_native_numbering(tmp_path):
    rebuilt = tmp_path / "book.pdf"
    rebuilt.with_suffix(".typ").write_text(TYPST.chapter_start + "#strong[定理 7] 设 $P$ 是域.\n", encoding="utf-8")
    spec = replace(ALGEBRA3_SPEC, cross_references=False)
    assert edition_literal_counts(rebuilt, spec) == {"TYPST_LITERAL_ITEM_HEAD": 1}

