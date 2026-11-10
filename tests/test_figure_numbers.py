import re

import pytest

from polytypst.compiler.source_numbers import (
    LATEX,
    TYPST,
    FigureCounter,
    FigureNumber,
    number_chapter,
)

FIGURES = ["1", "2", "4", "3.1", "3-6.1"]


@pytest.mark.parametrize(
    ("raw", "printed", "label", "n"),
    [
        ("1", "1", "fig-1", 1),
        ("3.1", "3.1", "fig-3-1", 1),
        ("3-6.1", "3-6.1", "fig-3-6-1", 1),
        ("3_2", "3-2", "fig-3-2", 2),
        ("4.2a", "4.2a", "fig-4-2a", 2),
        ("12", "12", "fig-12", 12),
    ],
)
def test_a_printed_figure_number_parses_to_its_label_and_count(raw: str, printed: str, label: str, n: int) -> None:
    assert FigureNumber.parse(raw) == FigureNumber(printed, label, n)


def test_the_counter_reports_a_skip_only_where_the_scan_jumps() -> None:
    counter = FigureCounter(3)
    assert [counter.advance(FigureNumber.parse(raw)) for raw in FIGURES] == [False, False, True, True, True]


def _typst(numbers: list[str]) -> str:
    return "\n\n".join(
        f'#figure(\n  image("fig.png", width: 20%),\n  caption: [Figure {n} A circle.]\n)' for n in numbers
    )


def _latex(numbers: list[str]) -> str:
    return "\n\n".join(f"![Figure {n} A circle.](fig.png)" for n in numbers)


def test_the_typst_writer_numbers_one_figure_list() -> None:
    numbered, _ = number_chapter(_typst(FIGURES), 3)
    figures = numbered.split("#figure(")[1:]
    assert [re.search(r"numbering: ([^,\n]+)", f).group(1) if "numbering:" in f else "" for f in figures] == [
        "source-figure-plain",
        "source-figure-plain",
        "source-figure-plain",
        "source-figure-dotted",
        '_ => "3-6.1"',
    ]
    assert re.findall(r"kind: image\)\)\.update\((\d+)\)\n#figure", numbered) == ["3", "0", "0"]
    assert re.findall(r"<(fig-[\w-]+)>", numbered) == ["fig-1", "fig-2", "fig-4", "fig-3-1", "fig-3-6-1"]


def test_the_latex_writer_numbers_the_same_figure_list() -> None:
    numbered, _ = number_chapter(_latex(FIGURES), 3, LATEX)
    assert re.findall(r"\\renewcommand\{\\thefigure\}\{(.*?)\}\\captionsetup", numbered) == [
        r"\arabic{figure}",
        r"\arabic{figure}",
        r"\arabic{figure}",
        r"\arabic{sourcechapter}.\arabic{figure}",
        "3-6.1",
    ]
    assert re.findall(r"\\setcounter\{figure\}\{(\d+)\}", numbered) == ["0", "1", "3", "0", "0"]
    assert re.findall(r"\\label\{(fig-[\w-]+)\}", numbered) == ["fig-1", "fig-2", "fig-4", "fig-3-1", "fig-3-6-1"]


def test_a_repeated_figure_number_is_left_as_written_by_both_writers() -> None:
    typst, _ = number_chapter(_typst(["1", "1"]), 3)
    latex, _ = number_chapter(_latex(["1", "1"]), 3, LATEX)
    assert typst.count("<fig-1>") == 1 and "caption: [Figure 1 A circle.]" in typst
    assert latex.count(r"\label{fig-1}") == 1 and "![Figure 1 A circle.](fig.png)" in latex


@pytest.mark.parametrize("writer", [TYPST, LATEX])
def test_both_writers_put_numbering_before_and_inside_a_figure(writer: object) -> None:
    before, inside = writer.figure_number(FigureNumber.parse("3.1"), 3, skipped=True)
    assert before and inside
