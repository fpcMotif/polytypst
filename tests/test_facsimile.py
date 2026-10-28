import itertools
import re
from pathlib import Path

import numpy as np
import pymupdf
import pytest

from polytypst.books import book_by_key
from polytypst.compiler.typst_math import typst_command
from polytypst.facsimile import (
    Measure,
    Placement,
    compile_facsimile,
    page_words,
    preamble,
    split_across_lines,
    transcript_typst,
)
from polytypst.facsimile_text import chunks
from polytypst.ocr.pages import OcrLine
from polytypst.parity.words import PT_PER_PX, page_ink

FACSIMILE_STYLE = book_by_key("grothendieck").editions["facsimile"].facsimile

pytestmark = pytest.mark.skipif(
    typst_command() is None or not FACSIMILE_STYLE.font_file.exists(),
    reason="needs typst and the Grothendieck face",
)
W, H = 400.0, 120.0
MATH = {("\\mathcal{F} = \\tilde{M}", False): "cal(F) = tilde(M)"}


def render(tmp_path: Path, markdown: str, words: list[Placement]) -> np.ndarray:
    return page_ink(compile_page(tmp_path, markdown, words)[0])


def compile_page(
    tmp_path: Path, markdown: str, words: list[Placement]
) -> pymupdf.Document:
    body = transcript_typst(
        words,
        list(chunks(markdown)),
        MATH,
        Measure(FACSIMILE_STYLE),
        np.zeros((px(H), px(W)), bool),
    )
    typ = tmp_path / "page.typ"
    typ.write_text(
        preamble(FACSIMILE_STYLE)
        + f"#set page(width: {W}pt, height: {H}pt, margin: 0pt)\n"
        + "\n".join(body)
        + "\n",
        encoding="utf-8",
    )
    pdf = tmp_path / "page.pdf"
    compile_facsimile(typ, pdf)
    return pymupdf.open(pdf)


def test_the_facsimile_pdf_has_no_structure_tree_for_readers_to_walk(
    tmp_path: Path,
) -> None:
    doc = compile_page(
        tmp_path,
        "quasi-cohérents",
        [Placement("quasi-cohérents", 100.0, 160.0, 52.0, 62.0, 60.0)],
    )
    assert doc.xref_get_key(doc.pdf_catalog(), "StructTreeRoot") == ("null", "null")
    assert "MCID" not in doc[0].read_contents().decode("latin-1")


def test_an_ocr_line_the_ink_cannot_split_becomes_one_word_per_word_by_measured_width() -> (
    None
):
    ink = np.zeros((1000, 800), bool)
    ink[490:510, 80:480] = True
    line = OcrLine("Le faisceau est", x=0.1, y=0.49, w=0.5, h=0.02)
    words = page_words(ink, (line,), [], Measure(FACSIMILE_STYLE))
    assert [w.text for w in words] == ["Le", "faisceau", "est"]
    assert words[0].left == pytest.approx(80 * PT_PER_PX)
    assert words[-1].right == pytest.approx(480 * PT_PER_PX)
    widths = [w.right - w.left for w in words]
    assert widths[1] > widths[2] > widths[0]
    assert all(a.right < b.left for a, b in itertools.pairwise(words))


def test_ink_beside_an_ocr_line_on_its_row_becomes_a_textless_word_on_that_line() -> (
    None
):
    ink = np.zeros((1000, 800), bool)
    ink[490:510, 40:120] = True
    ink[485:515, 300:600] = True
    line = OcrLine("(1.2.3)", x=0.05, y=0.49, w=0.1, h=0.02)
    words = page_words(ink, (line,), [], Measure(FACSIMILE_STYLE))
    assert [w.text for w in words] == ["(1.2.3)", ""]
    assert words[1].line == words[0].line
    assert words[1].left == pytest.approx(300 * PT_PER_PX)
    assert words[1].right == pytest.approx(600 * PT_PER_PX)


def test_unread_ink_that_merges_with_read_lines_keeps_only_its_own_rows_and_columns() -> None:
    ink = np.zeros((1000, 800), bool)
    ink[400:440, 40:200] = True
    ink[450:490, 40:200] = True
    ink[425:465, 300:600] = True
    lines = (
        OcrLine("canonique fonctoriel", x=0.05, y=0.56, w=0.2, h=0.04),
        OcrLine("de Modules.", x=0.05, y=0.51, w=0.2, h=0.04),
    )
    words = page_words(ink, lines, [], Measure(FACSIMILE_STYLE))
    [unread] = [w for w in words if not w.text]
    assert (unread.left, unread.right) == pytest.approx((300 * PT_PER_PX, 600 * PT_PER_PX))
    assert (unread.top, unread.bottom) == pytest.approx((425 * PT_PER_PX, 465 * PT_PER_PX))


def test_a_caption_label_glued_to_its_number_reads_as_two_words() -> None:
    ink = np.zeros((1000, 800), bool)
    ink[400:440, 40:600] = True
    line = OcrLine("图6-4 经常账户顺差", x=0.05, y=0.56, w=0.7, h=0.04)
    assert [w.text for w in page_words(ink, (line,), [], Measure(FACSIMILE_STYLE))] == ["图", "6-4", "经常账户顺差"]


def test_a_sliver_of_ink_just_outside_a_read_line_is_not_a_textless_word() -> None:
    ink = np.zeros((1000, 800), bool)
    ink[400:440, 40:200] = True
    ink[446:447, 40:70] = True
    line = OcrLine("(1) Soit", x=0.05, y=0.56, w=0.2, h=0.04)
    assert [w.text for w in page_words(ink, (line,), [], Measure(FACSIMILE_STYLE))] == ["(1)", "Soit"]


def test_unread_lines_that_touch_become_one_textless_word_per_line() -> None:
    ink = np.zeros((1000, 800), bool)
    ink[100:136, 40:400] = True
    for top in (400, 439, 478):
        ink[top : top + 36, 120:600] = True
    line = OcrLine("Le faisceau est", x=0.05, y=0.864, w=0.45, h=0.036)
    unread = [w for w in page_words(ink, (line,), [], Measure(FACSIMILE_STYLE)) if not w.text]
    assert [round(w.top / PT_PER_PX) for w in unread] == [400, 439, 478]
    assert [round(w.bottom / PT_PER_PX) for w in unread] == [436, 475, 514]
    assert len({w.line for w in unread}) == 3


def test_a_tall_unread_arrow_with_no_gap_between_lines_stays_one_textless_word() -> None:
    ink = np.zeros((1000, 800), bool)
    ink[100:136, 40:400] = True
    ink[400:510, 300:304] = True
    ink[400:510, 500:504] = True
    line = OcrLine("Le faisceau est", x=0.05, y=0.864, w=0.45, h=0.036)
    unread = [w for w in page_words(ink, (line,), [], Measure(FACSIMILE_STYLE)) if not w.text]
    assert [(round(w.top / PT_PER_PX), round(w.bottom / PT_PER_PX)) for w in unread] == [(400, 510)]


def px(pt: float) -> int:
    return round(pt / PT_PER_PX)


def test_inline_math_takes_the_unclaimed_ink_between_its_neighbouring_words() -> None:
    ink = np.zeros((px(H), px(W)), bool)
    ink[px(52) : px(62), px(66) : px(78)] = True
    ink[px(52) : px(62), px(80) : px(95)] = True
    words = [
        Placement("continue", 20.0, 60.0, 52.0, 62.0, 60.0),
        Placement("X→Y", 80.0, 95.0, 52.0, 62.0, 60.0),
        Placement("et", 110.0, 120.0, 52.0, 62.0, 60.0),
    ]
    body = transcript_typst(
        words,
        chunks("continue $\\psi : X \\to Y$ et"),
        {("\\psi : X \\to Y", False): "psi : X -> Y"},
        Measure(FACSIMILE_STYLE),
        ink,
    )
    fitted = next(b for b in body if "inkfit" in b)
    assert f"dx: {px(66) * PT_PER_PX:.2f}pt" in fitted
    assert f"inkfit({(px(95) - px(66)) * PT_PER_PX:.2f}pt" in fitted


def test_unclaimed_ink_between_two_formulas_goes_to_the_one_on_its_left() -> None:
    ink = np.zeros((px(H), px(W)), bool)
    for a, b in ((80, 90), (93, 115), (120, 130), (133, 138), (140, 150)):
        ink[px(52) : px(62), px(a) : px(b)] = True
    words = [
        Placement("canoniques", 20.0, 70.0, 52.0, 62.0, 60.0),
        Placement("Os", 80.0, 90.0, 52.0, 62.0, 60.0),
        Placement("Os", 120.0, 130.0, 52.0, 62.0, 60.0),
        Placement("F.", 140.0, 150.0, 52.0, 62.0, 60.0),
        Placement("Aux", 160.0, 175.0, 52.0, 62.0, 60.0),
    ]
    body = transcript_typst(
        words,
        chunks("canoniques $\\mathcal{O}_S \\to \\mathcal{E}$, $\\mathcal{O}_S \\to \\mathcal{F}$. Aux"),
        {
            ("\\mathcal{O}_S \\to \\mathcal{E}", False): "cal(O)_S -> cal(E)",
            ("\\mathcal{O}_S \\to \\mathcal{F}", False): "cal(O)_S -> cal(F)",
        },
        Measure(FACSIMILE_STYLE),
        ink,
    )
    first, second = (
        tuple(map(float, re.search(r"dx: ([\d.]+)pt.*inkfit\(([\d.]+)pt", b).groups()))
        for b in body
        if "inkfit" in b
    )
    assert first[0] + first[1] == pytest.approx(px(115) * PT_PER_PX, abs=0.3)
    assert second[0] == pytest.approx(120.0, abs=0.3)


def test_inline_math_does_not_grow_into_the_ink_of_the_lines_above_and_below() -> None:
    ink = np.zeros((px(H), px(W)), bool)
    ink[px(52) : px(62), px(80) : px(95)] = True
    ink[px(52) : px(62), px(66) : px(78)] = True
    ink[px(30) : px(50), px(66) : px(78)] = True
    ink[px(64) : px(84), px(66) : px(78)] = True
    ink[px(49) : px(50.5), px(82) : px(90)] = True
    ink[px(53) : px(61), px(150) : px(160)] = True
    words = [
        Placement("continue", 20.0, 60.0, 52.0, 62.0, 60.0),
        Placement("X→Y", 80.0, 95.0, 52.0, 62.0, 60.0),
        Placement("et", 110.0, 120.0, 52.0, 62.0, 60.0),
        Placement("", 200.0, 260.0, 28.0, 86.0, 86.0),
    ]
    body = transcript_typst(
        words,
        chunks("continue $\\psi : X \\to Y$ et"),
        {("\\psi : X \\to Y", False): "psi : X -> Y"},
        Measure(FACSIMILE_STYLE),
        ink,
    )
    fitted = next(b for b in body if "inkfit" in b)
    top, height = map(
        float, re.search(r"dy: ([\d.]+)pt, inkfit\([\d.]+pt, ([\d.]+)pt", fitted).groups()
    )
    assert top == pytest.approx(52.0, abs=0.3)
    assert top + height == pytest.approx(62.0, abs=0.3)


def ink_right(ink: np.ndarray, top: float, bottom: float) -> float:
    cols = np.flatnonzero(
        ink[round(top / PT_PER_PX) : round(bottom / PT_PER_PX)].any(axis=0)
    )
    return cols[-1] * PT_PER_PX if cols.size else 0.0


@pytest.mark.parametrize(
    ("markdown", "scan", "width"),
    [
        ("quasi-cohérents", "quasi-cohérents", 20.0),
        ("*quasi-cohérents*", "quasi-cohérents", 20.0),
        ("$\\mathcal{F} = \\tilde{M}$", "F=M", 6.0),
    ],
    ids=["plain", "italic", "math"],
)
def test_text_too_wide_for_its_scan_box_shrinks_inside_it(
    tmp_path: Path, markdown: str, scan: str, width: float
) -> None:
    box = Placement(scan, 100.0, 100.0 + width, 52.0, 62.0, 60.0)
    ink = render(tmp_path, markdown, [box])
    assert 0 < ink_right(ink, 40.0, 80.0) <= box.right + 0.5


def test_a_word_hyphenated_over_two_lines_is_cut_where_the_scan_cuts_it() -> None:
    parts = [
        Placement("(Bour-", 200.0, 260.0, 22.0, 32.0, 30.0, 0),
        Placement("baki,", 40.0, 80.0, 72.0, 82.0, 80.0, 1),
    ]
    assert [p.text for p in split_across_lines("(Bourbaki,", parts)] == ["(Bour-", "baki,"]


def test_a_chinese_word_broken_over_two_lines_takes_no_hyphen() -> None:
    parts = [
        Placement("增长方", 200.0, 260.0, 22.0, 32.0, 30.0, 0),
        Placement("式", 40.0, 60.0, 72.0, 82.0, 80.0, 1),
    ]
    assert [p.text for p in split_across_lines("增长方式", parts)] == ["增长方", "式"]


def test_a_chinese_line_is_cut_after_the_characters_that_end_the_scan_line() -> None:
    parts = [
        Placement("甲乙丙与现金和", 40.0, 110.0, 22.0, 32.0, 30.0, 0),
        Placement("存款相比", 40.0, 80.0, 72.0, 82.0, 80.0, 1),
    ]
    assert [p.text for p in split_across_lines("甲的乙的丙与现金和存款相比", parts)] == ["甲的乙的丙与现金和", "存款相比"]


def test_the_transcript_word_is_cut_at_the_fragment_the_scan_shows_on_each_line() -> None:
    words = [
        Placement("(Bour-", 200.0, 260.0, 22.0, 32.0, 30.0, 0),
        Placement("baki,", 40.0, 80.0, 72.0, 82.0, 80.0, 1),
    ]
    body = transcript_typst(
        words, chunks("(Bourbaki,"), {}, Measure(FACSIMILE_STYLE), np.zeros((px(H), px(W)), bool)
    )
    assert any('"(Bour-"' in b for b in body)
    assert any('"baki,"' in b for b in body)


def test_a_styled_run_over_two_scan_lines_is_set_on_both_lines() -> None:
    words = [
        Placement("甲乙丙丁戊", 40.0, 95.0, 22.0, 32.0, 30.0, 0),
        Placement("己庚辛", 40.0, 73.0, 72.0, 82.0, 80.0, 1),
    ]
    body = transcript_typst(
        words, chunks("甲乙丙丁**戊己**庚辛"), {}, Measure(FACSIMILE_STYLE), np.zeros((px(H), px(W)), bool)
    )
    first = [b for b in body if "dy: 30.00pt" in b]
    second = [b for b in body if "dy: 80.00pt" in b]
    assert first and second
    assert "己" not in "".join(first) and "己" in "".join(second)


def test_a_word_with_math_hyphenated_over_two_lines_puts_its_tail_on_the_second_line() -> None:
    words = [
        Placement("sous-(A)-mo-", 200.0, 270.0, 22.0, 32.0, 30.0, 0),
        Placement("dules", 40.0, 70.0, 72.0, 82.0, 80.0, 1),
    ]
    body = transcript_typst(
        words, chunks("sous- $A$-modules"), {("A", False): "A"}, Measure(FACSIMILE_STYLE),
        np.zeros((px(H), px(W)), bool),
    )
    head = next(b for b in body if "inkfit" in b)
    assert "dx: 200.00pt" in head
    assert "-mo-" in head
    assert any('"dules"' in b for b in body)


def test_a_scan_break_at_the_words_own_hyphen_keeps_the_hyphen_on_the_first_line() -> None:
    parts = [
        Placement("quasi-", 200.0, 230.0, 22.0, 32.0, 30.0, 0),
        Placement("cohérent,", 40.0, 85.0, 72.0, 82.0, 80.0, 1),
    ]
    assert [p.text for p in split_across_lines("quasi-cohérent,", parts)] == ["quasi-", "cohérent,"]


def test_a_misread_scan_fragment_falls_back_to_the_ink_width_cut() -> None:
    parts = [
        Placement("chap-", 200.0, 230.0, 22.0, 32.0, 30.0, 0),
        Placement("mann", 40.0, 110.0, 72.0, 82.0, 80.0, 1),
    ]
    assert [p.text for p in split_across_lines("Hermann", parts)] == ["He-", "rmann"]


def test_an_italic_word_hyphenated_over_two_lines_is_split_between_them(
    tmp_path: Path,
) -> None:
    first = Placement("quasi-", 340.0, 370.0, 22.0, 32.0, 30.0, 0)
    second = Placement("cohérent,", 40.0, 85.0, 72.0, 82.0, 80.0, 1)
    ink = render(tmp_path, "*quasi-cohérent,*", [first, second])
    assert ink_right(ink, 15.0, 40.0) <= first.right + 0.5
    assert 0 < ink_right(ink, 65.0, 90.0) <= second.right + 0.5
