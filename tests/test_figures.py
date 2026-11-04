from polytypst.books import book_by_key
from polytypst.compiler.diagrams import parse_array_diagram
from polytypst.compiler.monograph import MonographCompiler
from polytypst.figure_counts import figure_counts

SQUARE = r"""$$
\begin{array}{ccc}
G & \xrightarrow{f} & X \\
\downarrow & & \downarrow \\
H & \xrightarrow{g} & Y
\end{array}
$$"""

OCR_ROWS = r"""\begin{array}{ccc}
0 \to \mathcal{F} \to \mathcal{L}^0 \to \mathcal{L}^1 \to \cdots \\
\downarrow^\rho \quad \downarrow^{\rho_0} \quad \downarrow^{\rho_1} \\
0 \to \mathcal{G} \to \mathcal{M}^0 \to \mathcal{M}^1 \to \cdots
\end{array}"""


def test_a_row_of_several_vertical_arrows_in_one_cell_is_not_read_as_one_arrow() -> None:
    assert parse_array_diagram(OCR_ROWS) is None


def test_a_math_book_draws_an_array_diagram_with_fletcher() -> None:
    spec = book_by_key("kashiwara").spec
    assert spec.domain == "math" and not spec.commutative_diagrams
    typst = MonographCompiler(spec).format_typst(f"Text.\n\n{SQUARE}\n\nMore.")
    assert "fletcher.diagram(" in typst
    assert figure_counts(typst)["DIAGRAM_AS_ARRAY"] == 0


def test_a_diagram_left_as_aligned_rows_or_a_matrix_is_counted() -> None:
    aligned = "$ G & limits(arrow.r.long)^f & X\\\narrow.b &  & arrow.b\\\nH & limits(arrow.r.long)^g & Y $"
    matrix = "$ mat(delim: #none, Z^(n-1), x r i g h t a r r o w (d), Z^n; arrow.b, , arrow.b; Z, ->, Z) $"
    assert figure_counts(f"{aligned}\n\n{matrix}")["DIAGRAM_AS_ARRAY"] == 2


def test_aligned_equations_and_plain_matrices_are_not_diagrams() -> None:
    typst = (
        "$ f(x) & = x^2 \\\n & -> 0 $\n\n"
        "$ mat(1, 2; 3, 4) $\n\n"
        "$ x arrow.b y $\n\n"
        '$ #fletcher.diagram(fletcher.node((0, 0), $A$), fletcher.edge((0, 0), (0, 1), "->")) $'
    )
    assert figure_counts(typst)["DIAGRAM_AS_ARRAY"] == 0


def test_figures_are_counted_as_raster_or_vector() -> None:
    typst = (
        '#image("figures/fig_1.png", width: 50%)\n'
        '#image("figures/fig_2.svg")\n'
        '$ #(include "figures/fig_080_001.typ") $\n'
        '#image("figures/fig_3.pdf")\n'
        "$ #fletcher.diagram(spacing: 2em) $\n"
    )
    counts = figure_counts(typst)
    assert (counts["RASTER_FIGURE"], counts["VECTOR_FIGURE"]) == (1, 4)
