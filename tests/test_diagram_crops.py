from pathlib import Path

from PIL import Image, ImageDraw

from polytypst.compiler.diagrams import scan_diagram_typst, use_scan_diagrams
from polytypst.compiler.source_numbers import number_chapter
from polytypst.vision.diagram_crops import diagram_boxes, match_boxes

SQUARE = "$$\n\\begin{array}{ccc}\nA & \\rightarrow & B \\\\\n\\downarrow & & \\downarrow \\\\\nC & \\rightarrow & D\n\\end{array}\n$$"


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
