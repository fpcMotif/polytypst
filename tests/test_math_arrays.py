from polytypst.compiler.diagrams import parse_array_diagram
from polytypst.compiler.math_arrays import (
    MATRIX_EQUATIONS,
    SEQUENCE,
    SPEC_SHORT,
    UNREAD_DIAGRAM,
    array_misuses,
    repair_arrays,
)
from polytypst.compiler.monograph import ChapterSpec, MonographCompiler, MonographSpec
from polytypst.rules import all_rules

GROTHENDIECK_SEQUENCE = (
    "\\begin{array}{cccccccccc}\n0 & \\longrightarrow & \\mathcal{N} & \\xrightarrow{v} & \\mathcal{F}"
    " & \\xrightarrow{u} & \\mathcal{G} & \\xrightarrow{w} & \\mathcal{P} & \\longrightarrow 0,\n\\end{array}"
)
BOURBAKI_LIE_SHORT_SPEC = (
    "\\begin{array}{ccc}\nF & \\xrightarrow{i} & G & \\xrightarrow{p} & M \\\\\n"
    "\\downarrow \\phi & & \\downarrow \\gamma & & \\downarrow \\operatorname{Id} \\\\\n"
    "\\tilde{F} & \\xrightarrow{i} & \\tilde{G} & \\xrightarrow{p} & M.\n\\end{array}"
)
BOURBAKI_CHAINS_IN_CELLS = (
    "\\begin{array}{ccc}\n0 \\to A \\to B \\to C \\to 0 \\\\\n\\downarrow \\quad \\downarrow \\quad \\downarrow \\\\\n"
    "0 \\to A' \\to B' \\to C' \\to 0\n\\end{array}"
)
KLEIN_EQUATIONS = "\\begin{bmatrix} x \\cdot x = a \\\\ x \\cdot y = 0 \\end{bmatrix}"


def rules(text: str) -> list[str]:
    return [m.rule for m in array_misuses(text)]


def test_a_one_row_array_of_arrows_is_an_exact_sequence_and_becomes_one_formula():
    assert rules(GROTHENDIECK_SEQUENCE) == [SEQUENCE]
    out = repair_arrays(GROTHENDIECK_SEQUENCE)
    assert out == (
        "0 \\longrightarrow \\mathcal{N} \\xrightarrow{v} \\mathcal{F} \\xrightarrow{u} \\mathcal{G}"
        " \\xrightarrow{w} \\mathcal{P} \\longrightarrow 0,"
    )
    assert rules(out) == []


def test_a_row_wider_than_its_column_spec_gets_a_spec_as_wide_as_the_row():
    assert rules(BOURBAKI_LIE_SHORT_SPEC) == [SPEC_SHORT]
    out = repair_arrays(BOURBAKI_LIE_SHORT_SPEC)
    assert out.startswith("\\begin{array}{ccccc}\n")
    assert rules(out) == []
    assert parse_array_diagram(out) is not None


def test_the_page_cleaner_applies_both_array_repairs_without_repair_math():
    spec = MonographSpec(domain="math", slug="t", title="T", author="A", chapters=[ChapterSpec(1, "One", 1, 2)])
    assert not spec.repair_math
    page = f"Text.\n\n$$\n{GROTHENDIECK_SEQUENCE}\n$$\n\nMore.\n\n$$\n{BOURBAKI_LIE_SHORT_SPEC}\n$$\n"
    body = MonographCompiler(spec).cleaner.clean(page, pno=1).body
    assert "0 \\longrightarrow \\mathcal{N} \\xrightarrow{v}" in body
    assert "\\begin{array}{ccccc}" in body


def test_arrow_rows_the_diagram_parser_cannot_read_are_reported():
    assert rules(BOURBAKI_CHAINS_IN_CELLS) == [UNREAD_DIAGRAM]
    assert repair_arrays(BOURBAKI_CHAINS_IN_CELLS) == BOURBAKI_CHAINS_IN_CELLS
    assert rules("\\begin{matrix} A & \\to & B \\\\ \\downarrow & & \\downarrow \\\\ C & \\to & D \\end{matrix}") == [UNREAD_DIAGRAM]


def test_rows_of_horizontal_maps_alone_are_not_a_diagram():
    fermat2 = (
        "\\begin{array}{ccc}\nG/H & \\xrightarrow{\\cong} & \\operatorname{Gal}(M/K) \\\\\n"
        "\\text{class of } \\sigma & \\longmapsto & \\text{restriction of } \\sigma\n\\end{array}"
    )
    assert rules(fermat2) == []


def test_a_bracketed_matrix_of_equations_is_reported_and_a_real_matrix_is_not():
    assert rules(KLEIN_EQUATIONS) == [MATRIX_EQUATIONS]
    assert rules("\\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}") == []
    assert rules("\\begin{array}{l} u(x_0) = 0 \\\\ u(x_1) = 0 \\end{array}") == []


def test_a_readable_diagram_and_a_line_number_are_reported_right():
    readable = "\\begin{array}{ccc}\nA & \\to & B \\\\\n\\downarrow & & \\downarrow \\\\\nC & \\to & D\n\\end{array}"
    assert rules(readable) == []
    (misuse,) = array_misuses("text\n\n$$\n" + KLEIN_EQUATIONS + "\n$$")
    assert misuse.line == 4


def test_polytypst_rules_lists_every_array_rule():
    names = {r.name for r in all_rules() if r.stage == "source"}
    assert {SPEC_SHORT, SEQUENCE, UNREAD_DIAGRAM, MATRIX_EQUATIONS} <= names
