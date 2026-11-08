from dataclasses import replace
from pathlib import Path

import pymupdf
import pytest

from polytypst.books import book_by_key
from polytypst.compiler.monograph import MonographCompiler, compile_typst
from polytypst.compiler.page_design import Length, PageDesign, RunningHeads

DESIGN = PageDesign(
    width_pt=400,
    height_pt=600,
    margin_inside_pt=40,
    margin_outside_pt=90,
    margin_top_pt=60,
    margin_bottom_pt=70,
    body_size_pt=10,
    font='"New Computer Modern"',
    lang="en",
    hyphenate=True,
    leading=Length(0.52, "em"),
    par_spacing=Length(0.52, "em"),
    first_line_indent=Length(1.5, "em"),
    display_above=Length(1.3, "em"),
    display_below=Length(1.3, "em"),
    display_leading=Length(0.88, "em"),
    running_heads=RunningHeads(
        head_size_pt=8.5,
        folio_size_pt=9.5,
        head_style="italic",
        rule_pt=0,
        first_page=1,
    ),
)


def _build(tmp_path: Path, design: PageDesign) -> pymupdf.Document:
    paragraph = " ".join(["The quick brown fox jumps over the lazy dog."] * 14)
    body = "= Opening\n\n" + "\n\n".join([paragraph] * 12) + "\n"
    typ = tmp_path / "d.typ"
    typ.write_text(design.typst("Probe") + body, encoding="utf-8")
    compile_typst(typ, tmp_path / "d.pdf")
    return pymupdf.open(tmp_path / "d.pdf")


def _body_words(page: pymupdf.Page, design: PageDesign) -> list[tuple[float, ...]]:
    top, bottom = design.margin_top_pt, design.height_pt - design.margin_bottom_pt
    return [w for w in page.get_text("words") if top <= w[1] and w[3] <= bottom]


def test_the_margins_must_leave_a_text_block() -> None:
    with pytest.raises(ValueError, match="no text block"):
        _ = replace(DESIGN, margin_inside_pt=200, margin_outside_pt=200)


def test_a_length_is_in_pt_or_em() -> None:
    assert Length.parse("4.3pt").pt(10) == 4.3
    assert Length.parse("0.52em").pt(10) == pytest.approx(5.2)
    with pytest.raises(ValueError, match="pt or em"):
        _ = Length.parse("12px")


def test_the_page_and_the_text_block_take_the_designs_sizes(tmp_path: Path) -> None:
    doc = _build(tmp_path, DESIGN)
    assert len(doc) >= 3
    for number, page in enumerate(doc, start=1):
        assert (round(page.rect.width), round(page.rect.height)) == (400, 600)
        left = min(w[0] for w in _body_words(page, DESIGN))
        right = max(w[2] for w in _body_words(page, DESIGN) if w[4][-1].isalpha())
        inner_left = DESIGN.margin_inside_pt if number % 2 else DESIGN.margin_outside_pt
        assert left == pytest.approx(inner_left, abs=1.5), number
        assert right == pytest.approx(inner_left + DESIGN.text_width_pt, abs=1.5), (
            number
        )


def test_a_chapter_opening_has_a_foot_folio_and_no_running_head(tmp_path: Path) -> None:
    doc = _build(tmp_path, DESIGN)
    opening, following = doc[0], doc[1]

    def head(page: pymupdf.Page) -> list[str]:
        return [w[4] for w in page.get_text("words") if w[3] <= DESIGN.margin_top_pt]

    def foot(page: pymupdf.Page) -> list[str]:
        return [
            w[4]
            for w in page.get_text("words")
            if w[1] >= DESIGN.height_pt - DESIGN.margin_bottom_pt
        ]

    assert head(opening) == []
    assert foot(opening) == ["1"]
    assert head(following) == ["2", "Opening"]
    assert foot(following) == []


@pytest.mark.parametrize("key", ["kodaira", "fga"])
def test_a_book_preamble_carries_its_design(key: str) -> None:
    compiler = MonographCompiler(book_by_key(key).spec)
    design = compiler.design
    preamble = compiler.build_typst_preamble()
    assert f"width: {design.width_pt:g}pt" in preamble
    assert f"size: {design.body_size_pt:g}pt" in preamble
    assert f"leading: {design.leading}" in preamble
