from pathlib import Path

from PIL import Image, ImageDraw

from polytypst.compiler.diagrams import (
    SCAN_DIAGRAM_RE,
    is_unread_diagram,
    page_scan_diagrams,
    scan_diagram_typst,
    use_scan_diagrams,
)
from polytypst.compiler.source_numbers import number_chapter
from polytypst.ocr.pages import PageImage
from polytypst.vision import diagram_crops
from polytypst.vision.diagram_crops import diagram_boxes, match_boxes

SQUARE = "$$\n\\begin{array}{ccc}\nA & \\rightarrow & B \\\\\n\\downarrow & & \\downarrow \\\\\nC & \\rightarrow & D\n\\end{array}\n$$"
UNREAD = (
    "$$\n\\begin{array}{ccc}\n0 \\to A \\to B \\to C \\to 0 \\\\\n\\downarrow \\quad \\downarrow \\quad \\downarrow \\\\\n"
    "0 \\to A' \\to B' \\to C' \\to 0\n\\end{array}\n$$"
)


def page_with_a_numbered_diagram() -> Image.Image:
    page = Image.new("L", (600, 900), 255)
    draw = ImageDraw.Draw(page)
    for top in (50, 90, 130, 170, 500, 540):
        draw.rectangle((50, top, 550, top + 20), fill=0)
    for top in (300, 400):
        draw.rectangle((200, top, 400, top + 20), fill=0)
    draw.rectangle((210, 320, 214, 400), fill=0)
    draw.rectangle((390, 320, 394, 400), fill=0)
    draw.rectangle((55, 350, 75, 370), fill=0)
    return page


def test_a_centered_tall_block_is_a_diagram_and_its_equation_number_is_left_out():
    assert diagram_boxes(page_with_a_numbered_diagram()) == [(192, 292, 409, 429)]


def test_a_row_of_vertical_arrows_joins_full_width_rows_into_a_diagram():
    page = Image.new("L", (600, 900), 255)
    draw = ImageDraw.Draw(page)
    for top in (50, 80, 110, 300, 400, 600, 630):
        draw.rectangle((50, top, 550, top + 20), fill=0)
    for x in (100, 300, 500):
        draw.rectangle((x, 330, x + 4, 390), fill=0)
    assert diagram_boxes(page) == [(42, 292, 559, 429)]


def test_text_lines_alone_hold_no_diagram():
    page = Image.new("L", (600, 900), 255)
    draw = ImageDraw.Draw(page)
    for top in range(50, 600, 30):
        draw.rectangle((50, top, 550, top + 20), fill=0)
    assert diagram_boxes(page) == []


def test_boxes_are_matched_to_the_diagrams_nearest_their_place_in_the_transcript():
    boxes = [(0, 100, 10, 200), (0, 400, 10, 500), (0, 800, 10, 900)]
    assert match_boxes(boxes, [0.45, 0.82], 1000) == [boxes[1], boxes[2]]
    assert match_boxes(boxes[:1], [0.2, 0.5], 1000) is None


def test_a_diagram_with_a_snippet_or_crop_becomes_a_scan_diagram(tmp_path: Path):
    text = f"Soit\n\n{SQUARE}\n\net\n\n{SQUARE}\n\nfin."
    (tmp_path / "fig_012_002.png").touch()
    out = use_scan_diagrams(text, 12, tmp_path)
    assert out == f"Soit\n\n{SQUARE}\n\net\n\n$$\n\\scandiagram{{012_002}}\n$$\n\nfin."


def test_an_unread_diagram_has_its_own_numbers_and_leaves_the_array_diagrams_numbered_as_before(tmp_path: Path):
    text = f"Soit\n\n{UNREAD}\n\net\n\n{SQUARE}\n\nfin."
    assert [fig for _, fig in page_scan_diagrams(text, 12)] == ["012_u001", "012_001"]
    (tmp_path / "fig_012_u001.png").touch()
    (tmp_path / "fig_012_001.typ").touch()
    out = use_scan_diagrams(text, 12, tmp_path)
    assert out == "Soit\n\n$$\n\\scandiagram{012_u001}\n$$\n\net\n\n$$\n\\scandiagram{012_001}\n$$\n\nfin."
    assert SCAN_DIAGRAM_RE.fullmatch("\\scandiagram{012_u001}")


def test_only_a_multi_row_arrow_array_the_parser_cannot_read_is_unread():
    assert is_unread_diagram(UNREAD.strip("$\n"))
    assert is_unread_diagram(SQUARE.strip("$\n") + ",")
    assert not is_unread_diagram(SQUARE.strip("$\n"))
    assert not is_unread_diagram("\\begin{array}{ccc} 0 & \\to & A \\end{array}")
    assert not is_unread_diagram("\\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}")
    assert not is_unread_diagram("x = \\begin{array}{c} A \\\\ \\downarrow \\\\ B \\end{array}")


def two_diagram_page() -> Image.Image:
    page = Image.new("L", (600, 900), 255)
    draw = ImageDraw.Draw(page)
    for top in (50, 90, 450, 490, 820):
        draw.rectangle((50, top, 550, top + 20), fill=0)
    for top in (200, 300, 600, 700):
        draw.rectangle((200, top, 400, top + 20), fill=0)
    for top in (220, 620):
        draw.rectangle((210, top, 214, top + 80), fill=0)
        draw.rectangle((390, top, 394, top + 80), fill=0)
    return page


def test_scan_boxes_go_to_array_and_unread_diagrams_in_page_order(tmp_path: Path, monkeypatch):
    store = tmp_path / "markdown_pages"
    store.mkdir()
    (store / "p_012.md").write_text(f"Soit\n\n{UNREAD}\n\net\n\n{SQUARE}\n\nfin.\n", encoding="utf-8")
    (tmp_path / "page_renders").mkdir()
    two_diagram_page().save(tmp_path / "page_renders" / "p_012.png")
    monkeypatch.setattr(diagram_crops, "transcripts", lambda _: store)
    boxes = {fig: box for fig, (_, box) in diagram_crops.scan_diagram_boxes(tmp_path).items()}
    assert boxes == {"012_u001": (192, 192, 409, 329), "012_001": (192, 592, 409, 729)}


def test_a_scan_with_too_few_diagrams_still_crops_the_array_diagrams(tmp_path: Path, monkeypatch):
    store = tmp_path / "markdown_pages"
    store.mkdir()
    (store / "p_012.md").write_text(f"Soit\n\n{SQUARE}\n\net\n\n{UNREAD}\n\nfin.\n", encoding="utf-8")
    (tmp_path / "page_renders").mkdir()
    page_with_a_numbered_diagram().save(tmp_path / "page_renders" / "p_012.png")
    monkeypatch.setattr(diagram_crops, "transcripts", lambda _: store)
    assert list(diagram_crops.scan_diagram_boxes(tmp_path)) == ["012_001"]


def test_a_book_box_replaces_or_drops_an_unread_crop_and_old_crops_go(tmp_path: Path, monkeypatch):
    store = tmp_path / "markdown_pages"
    store.mkdir()
    (store / "p_012.md").write_text(f"Soit\n\n{UNREAD}\n\net\n\n{UNREAD}\n\nfin.\n", encoding="utf-8")
    (tmp_path / "page_renders").mkdir()
    render = tmp_path / "page_renders" / "p_012.png"
    two_diagram_page().save(render)
    figures = tmp_path / "figures"
    figures.mkdir()
    (figures / "fig_099_u001.png").touch()
    monkeypatch.setattr(diagram_crops, "transcripts", lambda _: store)

    class Scan:
        def pages(self, out_dir: Path, dpi: int, numbers: list[int]) -> list[PageImage]:
            assert numbers == [12]
            return [PageImage(12, render)]

    written = diagram_crops.install_unread_diagrams(tmp_path, Scan(), 200, {"012_u001": (0, 0, 50, 40), "012_u002": ()})
    assert [p.name for p in written] == ["fig_012_u001.png"]
    assert sorted(p.name for p in figures.iterdir()) == ["fig_012_u001.png"]
    with Image.open(figures / "fig_012_u001.png") as im:
        assert im.size == (50, 40)


def test_a_snippet_is_included_and_a_crop_keeps_its_printed_width(tmp_path: Path):
    Image.new("L", (600, 150), 255).save(tmp_path / "fig_012_001.png")
    assert (
        scan_diagram_typst("012_001", tmp_path, "figures")
        == '#image("figures/fig_012_001.png", width: 144.0pt)'
    )
    (tmp_path / "fig_012_001.typ").touch()
    assert (
        scan_diagram_typst("012_001", tmp_path, "figures")
        == '#(include "figures/fig_012_001.typ")'
    )


def test_a_numbered_scan_diagram_takes_its_number_from_the_counter():
    for body in (
        '#(include "figures/fig_036_001.typ")',
        '#image("figures/fig_036_001.png", width: 144.0pt)',
    ):
        text = f"== § 1. Foncteurs\n\n=== 1.2. Objets\n\n$ {body} $ <eq-1-2-9-1>"
        out, _ = number_chapter(text, 1)
        assert f"numbering: source-equation-number, $ {body} $) <eq-c1-1-2-9-1>" in out
