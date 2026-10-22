"""Carl Ludwig Siegel: Symplectic Geometry (1943/1964)."""

from ..compiler.monograph import ChapterSpec, MonographSpec, running_header_regexes

RUNNING_HEADERS = (
    r"Symplectic Geometry|Carl Ludwig Siegel|Introduction|The Symplectic Group|"
    r"The Symplectic Metric|Discontinuous Groups|Hermitian Forms|"
    r"The Fundamental Domain of the Modular Group|The Fundamental Domain of the Group|"
    r"The Volume of the Fundamental Domain of the Modular Group|Commensurable Groups|"
    r"Unit Groups of Quinary Quadratic Forms|Preface|Contents|Errata"
)

SIEGEL_SYMPLECTIC_SPEC = MonographSpec(
    slug="siegel_symplectic",
    title="Symplectic Geometry",
    footnote_style="symbol",
    footnote_marks=("*", "**", "***"),
    author="Carl Ludwig Siegel",
    publisher="Academic Press",
    series="",
    year=1943,
    preface_page=9,
    chapters=[
        ChapterSpec(1, "Introduction", 13, 19),
        ChapterSpec(2, "The Symplectic Group", 20, 27),
        ChapterSpec(3, "The Symplectic Metric", 28, 36),
        ChapterSpec(4, "Discontinuous Groups", 37, 41),
        ChapterSpec(5, "Hermitian Forms", 42, 47),
        ChapterSpec(6, "The Fundamental Domain of the Modular Group", 48, 55),
        ChapterSpec(7, "The Fundamental Domain of the Group Lambda(G, S)", 56, 61),
        ChapterSpec(8, "The Volume of the Fundamental Domain of the Modular Group", 62, 76),
        ChapterSpec(9, "Commensurable Groups", 77, 85),
        ChapterSpec(10, "Unit Groups of Quinary Quadratic Forms", 86, 98),
    ],
    latex_preamble=(
        r"\usepackage{fancyhdr}" "\n"
        r"\pagestyle{fancy}" "\n"
        r"\fancyhf{}" "\n"
        r"\fancyhead[LE]{\small\thepage\quad\textsc{Carl Ludwig Siegel}}" "\n"
        r"\fancyhead[RO]{\small\textsc{Symplectic Geometry}\quad\thepage}" "\n"
        r"\renewcommand{\headrulewidth}{0pt}"
    ),
    running_header_regexes=running_header_regexes(rf"(?:{RUNNING_HEADERS})\.?"),
    drop_line_regexes=(rf"^#+\s*(?:{RUNNING_HEADERS})(?:\s+\d{{1,3}})?\s*$",),
    pdf_name_markers=("siegel", "symplectic"),
    pdf_page_count=104,
    source_pdf="SYMPLECTIC GEOMETRY. Reprinted from American Journal of Mathematics, Vol . LXV, No. 1, January, 1943. (Carl Ludwig Siegel).pdf",
)
