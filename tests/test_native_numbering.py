import re
from pathlib import Path

import pymupdf
import pytest

from polytypst.compiler.monograph import compile_typst, typst_chapter_heading
from polytypst.compiler.source_numbers import (
    TYPST,
    TYPST_RULES,
    labels,
    link_references,
    number_chapter,
)
from polytypst.literal_numbers import literal_numbering_counts


def _figure(number: str) -> str:
    return f'#figure(\n  image("fig.png", width: 20%),\n  caption: [Figure {number} A circle.]\n)'


def test_a_numbering_closure_that_returns_fixed_text_is_hardcoded() -> None:
    source = TYPST.chapter_start + '#heading(level: 1, numbering: _ => "6")[Curvature]\n'
    assert literal_numbering_counts(source, TYPST).get("HARDCODED_NUMBERING") == 1


@pytest.mark.parametrize(("number", "style"), [("1", "source-figure-plain"), ("3.1", "source-figure-dotted")])
def test_a_figure_number_in_a_plain_or_dotted_style_comes_from_a_counter(number: str, style: str) -> None:
    numbered, _ = number_chapter(_figure(number), 3)
    assert "_ =>" not in numbered
    assert f"numbering: {style}" in numbered


def test_an_irregular_figure_number_stays_literal_and_is_counted() -> None:
    numbered, _ = number_chapter(_figure("3-6.1"), 3)
    assert literal_numbering_counts(TYPST.chapter_start + numbered, TYPST).get("HARDCODED_NUMBERING") == 1


@pytest.mark.parametrize(("label", "numbering", "shown"), [("Chapter 6", '"1"', "Chapter 6"), ("Appendix B", '"A"', "Appendix B")])
def test_a_labelled_chapter_heading_takes_its_number_from_the_counter(label: str, numbering: str, shown: str) -> None:
    heading = typst_chapter_heading("Curvature", label, "sec-6")
    assert "_ =>" not in heading
    assert f"numbering: {numbering}" in heading
    assert shown.split()[-1] not in re.sub(r"update\(\([^)]*\)\)|<[\w-]+>", "", heading)


def test_a_back_matter_label_heading_has_no_number() -> None:
    heading = typst_chapter_heading("Index", "Index", None)
    assert "_ =>" not in heading
    assert "numbering: none" in heading


def test_printed_figure_numbers_and_references_match_the_scan(tmp_path: Path) -> None:
    pymupdf.open().new_page(width=20, height=20).get_pixmap().save(tmp_path / "fig.png")
    body = "\n\n".join(
        [
            typst_chapter_heading("Curvature", "Chapter 3", "sec-3"),
            "See Figure 1 and Figure 2 and Figure 3.1.",
            _figure("1"),
            _figure("2"),
            _figure("3.1"),
        ]
    )
    numbered, _ = number_chapter(body, 3)
    linked = link_references(numbered, 3, {}, labels(numbered))
    preamble = '#let chapter-label = state("chapter-label", none)\n#show heading.where(level: 1): it => [#context chapter-label.get() #it.body]\n'
    typ = tmp_path / "book.typ"
    typ.write_text(preamble + TYPST_RULES + linked, encoding="utf-8")
    compile_typst(typ, tmp_path / "book.pdf")
    text = " ".join(page.get_text() for page in pymupdf.open(tmp_path / "book.pdf")).split()
    joined = " ".join(text)
    assert "Chapter 3 Curvature" in joined
    assert re.findall(r"图 (\S+?):? A circle", joined) == ["1", "2", "3.1"]
    assert "See 图 1 and 图 2 and 图 3.1." in joined
