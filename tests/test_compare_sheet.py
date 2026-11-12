from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

from polytypst.compare_sheet import (
    FRAMES,
    MARK,
    Panel,
    diff_marks,
    find_text,
    share_rect,
    write_sheets,
)


def _pdf(path: Path, pages: list[list[tuple[float, str]]]) -> Path:
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page(width=400, height=600)
        for y, text in lines:
            page.insert_text((40, y), text, fontsize=12)
    doc.save(path)
    return path


def _has(image: Image.Image, colour: str) -> bool:
    rgb = tuple(int(colour[i : i + 2], 16) for i in (1, 3, 5))
    return bool((np.asarray(image.convert("RGB")) == rgb).all(axis=-1).any())


def test_find_text_gives_the_page_and_a_box_round_the_line(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(100, "first page")], [(300, "Theorem 4 holds here")]])
    page, (left, top, right, bottom) = find_text(pdf, "Theorem 4", pad=(0.05, 1.0))
    assert page == 2
    assert top < 300 / 600 < bottom
    assert bottom - top < 0.2
    assert (left, right) == (0.0, 1.0)


def test_find_text_matches_words_that_stand_apart_on_one_line(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(200, "Jha, Pranava Kumar, 69")]])
    assert find_text(pdf, "Kumar Jha") is not None
    assert find_text(pdf, "Kumar Idel") is None


def test_find_text_looks_only_on_the_page_it_is_given(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(100, "alpha")], [(100, "beta")]])
    assert find_text(pdf, "beta", page=1) is None
    assert find_text(pdf, "beta", page=2)[0] == 2


def test_rows_that_pass_the_limit_start_a_new_sheet_and_none_shrinks(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(y, f"line {y}") for y in range(60, 560, 40)]])
    rows = [[Panel(f"row {n}", pdf, 1)] for n in range(3)]
    outs = write_sheets(rows, tmp_path / "sheet.png", limit=700)
    assert [out.name for out in outs] == ["sheet-1.png", "sheet-2.png", "sheet-3.png"]
    sizes = []
    for out in outs:
        with Image.open(out) as sheet:
            assert max(sheet.size) <= 700
            sizes.append(sheet.size)
    assert len(set(sizes)) == 1


def test_rows_that_fit_stay_on_one_sheet_named_as_given(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(100, "short")]])
    outs = write_sheets([[Panel("a", pdf, 1)], [Panel("b", pdf, 1)]], tmp_path / "sheet.png")
    assert outs == [tmp_path / "sheet.png"]


def test_frames_change_colour_when_the_source_page_changes(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(100, "one")], [(100, "two")]])
    same = write_sheets([[Panel("a", pdf, 1)], [Panel("b", pdf, 1)]], tmp_path / "same.png", frame=True)
    with Image.open(same[0]) as sheet:
        assert _has(sheet, FRAMES[0])
        assert not _has(sheet, FRAMES[1])
    other = write_sheets([[Panel("a", pdf, 1)], [Panel("b", pdf, 2)]], tmp_path / "other.png", frame=True)
    with Image.open(other[0]) as sheet:
        assert _has(sheet, FRAMES[0])
        assert _has(sheet, FRAMES[1])


def test_a_sheet_stays_under_its_kilobyte_budget(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(y, "dense text " * 6) for y in range(40, 580, 14)]])
    rows = [[Panel("page", pdf, 1)]]
    free = write_sheets(rows, tmp_path / "free.png")[0]
    budget = free.stat().st_size // 1024 // 3
    tight = write_sheets(rows, tmp_path / "tight.png", kb=budget)[0]
    assert budget > 0
    assert tight.stat().st_size <= budget * 1024


def test_share_rect_maps_page_shares_to_points() -> None:
    rect = share_rect(pymupdf.Rect(10, 20, 410, 620), (0.25, 0.5, 0.75, 1.0))
    assert tuple(rect) == (110.0, 320.0, 310.0, 620.0)


def test_a_mark_is_drawn_round_its_box_and_nowhere_without_one(tmp_path: Path) -> None:
    pdf = _pdf(tmp_path / "book.pdf", [[(100, "top line"), (500, "bottom line")]])
    [plain] = write_sheets([[Panel("page", pdf, 1)]], tmp_path / "plain.png")
    [marked] = write_sheets([[Panel("page", pdf, 1, marks=((0.05, 0.78, 0.6, 0.88),))]], tmp_path / "marked.png")
    with Image.open(plain) as sheet:
        assert not _has(sheet, MARK)
    with Image.open(marked) as sheet:
        red = (np.asarray(sheet.convert("RGB")) == (220, 30, 30)).all(axis=-1)
        rows = np.nonzero(red.any(axis=1))[0]
        assert rows.min() > sheet.height / 2


def test_diff_marks_box_the_line_only_one_panel_has(tmp_path: Path) -> None:
    before = _pdf(tmp_path / "before.pdf", [[(100, "shared line")]])
    after = _pdf(tmp_path / "after.pdf", [[(100, "shared line"), (400, "a new line")]])
    assert diff_marks(Panel("a", before, 1), Panel("b", before, 1)) == ([], [])
    marks_a, marks_b = diff_marks(Panel("a", before, 1), Panel("b", after, 1))
    assert marks_a == marks_b
    [(_, top, _, bottom)] = marks_a
    assert top < 400 / 600 < bottom + 0.05
    assert top > 0.5


def test_a_panel_reads_an_image_file_as_its_one_page(tmp_path: Path) -> None:
    png = tmp_path / "crop.png"
    Image.new("RGB", (300, 120), "black").save(png)
    [out] = write_sheets([[Panel("image", png, 1)]], tmp_path / "sheet.png")
    with Image.open(out) as sheet:
        assert _has(sheet, "#000000")
