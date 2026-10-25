import json
from pathlib import Path

import numpy as np
import pymupdf
import pytest

from polytypst import books as books_module
from polytypst import books_cli
from polytypst.compiler.monograph import MonographSpec
from polytypst.edition import Book, Edition, Parity, VisualLimits
from polytypst.parity import FACSIMILE
from polytypst.parity.visual import compare_runs, ink_regions, page_visual
from polytypst.parity.words import PT_PER_PX

W, H = 400.0, 300.0


def px(pt: float) -> int:
    return round(pt / PT_PER_PX)


def blank() -> np.ndarray:
    return np.zeros((px(H), px(W)), bool)


def text_line(ink: np.ndarray, top: float, dx: float = 0.0) -> np.ndarray:
    for left in range(40, 340, 12):
        ink[px(top) : px(top + 7), px(left + dx) : px(left + dx + 8)] = True
    return ink


def test_identical_pages_have_no_regions() -> None:
    ink = text_line(blank(), 50.0)
    assert ink_regions(ink, ink.copy()) == []


def test_a_rebuilt_shifted_by_less_than_the_match_distance_has_no_regions() -> None:
    assert ink_regions(text_line(blank(), 50.0), text_line(blank(), 50.0, dx=0.5)) == []


def test_rebuilt_ink_the_scan_does_not_have_is_an_extra_region_at_its_place() -> None:
    scan = text_line(blank(), 50.0)
    rebuilt = text_line(blank(), 50.0)
    rebuilt[px(120) : px(132), px(200) : px(260)] = True
    [region] = ink_regions(scan, rebuilt)
    assert region.kind == "extra"
    left, top, right, bottom = region.box
    assert (left, top, right, bottom) == pytest.approx((200.0, 120.0, 260.0, 132.0), abs=0.5)


def test_scan_ink_the_rebuilt_page_lacks_is_a_missing_region() -> None:
    scan = text_line(text_line(blank(), 50.0), 80.0)
    [region] = ink_regions(scan, text_line(blank(), 50.0))
    assert region.kind == "missing"
    assert region.box[1] == pytest.approx(80.0, abs=0.5)
    assert region.box[3] == pytest.approx(87.0, abs=0.5)


def test_specks_smaller_than_a_glyph_are_not_regions() -> None:
    scan = text_line(blank(), 50.0)
    rebuilt = scan.copy()
    rebuilt[px(150) : px(151), px(100) : px(101)] = True
    assert ink_regions(scan, rebuilt) == []


def test_page_shares_count_extra_and_missing_ink_against_each_page() -> None:
    scan = text_line(text_line(blank(), 50.0), 80.0)
    rebuilt = text_line(blank(), 50.0)
    page = page_visual(scan, rebuilt, 1, 1)
    assert page.extra == 0.0
    assert page.missing == pytest.approx(0.5, abs=0.02)


def test_a_page_whose_differing_ink_shrank_is_improved_and_one_that_grew_regressed() -> None:
    scan = text_line(text_line(blank(), 50.0), 80.0)
    good, bad = page_visual(scan, scan.copy(), 1, 1), page_visual(scan, text_line(blank(), 50.0), 1, 1)
    assert compare_runs([good], [bad]) == {"improved": [1], "regressed": []}
    assert compare_runs([bad], [good]) == {"improved": [], "regressed": [1]}


def write_pdf(path: Path, lines: list[str]) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    for i, line in enumerate(lines):
        _ = page.insert_text((40, 60 + 30 * i), line, fontsize=11)
    doc.save(path)


@pytest.fixture
def facsimile(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    scan, rebuilt = tmp_path / "scan.pdf", tmp_path / "rebuilt.pdf"
    write_pdf(scan, ["The first line of the page.", "The second line of the page."])
    edition = Edition(
        rebuilt, lambda source, formats, footnotes: None, parity=Parity(lambda: {1: [1]}, FACSIMILE)
    )
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"facsimile": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    return scan, rebuilt


def test_parity_visual_writes_a_report_of_the_regions_without_reading_ocr(facsimile, tmp_path: Path) -> None:
    scan, rebuilt = facsimile
    write_pdf(rebuilt, ["The first line of the page."])
    out = tmp_path / "visual"
    assert books_cli.main("parity", ["probe", "--source", str(scan), "--visual", "--out", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["pages"] == 1
    assert summary["regions"]["missing"] == 1
    assert "p001" in (out / "index.html").read_text()


def test_parity_visual_crops_only_the_largest_regions_of_the_book(facsimile, tmp_path: Path) -> None:
    scan, rebuilt = facsimile
    write_pdf(rebuilt, [])
    out = tmp_path / "visual"
    assert books_cli.main("parity", ["probe", "--source", str(scan), "--visual", "--top", "1", "--out", str(out)]) == 0
    assert json.loads((out / "summary.json").read_text())["regions"]["missing"] == 2
    assert len(list((out / "img").glob("*_scan.png"))) == 1


def test_parity_against_an_older_build_fails_when_a_page_got_worse(facsimile, tmp_path: Path) -> None:
    scan, rebuilt = facsimile
    old = tmp_path / "old.pdf"
    write_pdf(old, ["The first line of the page.", "The second line of the page."])
    write_pdf(rebuilt, ["The first line of the page."])
    args = ["probe", "--source", str(scan), "--against", str(old), "--out", str(tmp_path / "v")]
    assert books_cli.main("parity", args) == 1
    write_pdf(old, ["The first line of the page."])
    write_pdf(rebuilt, ["The first line of the page.", "The second line of the page."])
    assert books_cli.main("parity", args) == 0


def test_parity_fails_when_a_page_misses_more_scan_ink_than_the_limit(facsimile, tmp_path: Path, capsys) -> None:
    scan, rebuilt = facsimile
    write_pdf(rebuilt, ["The first line of the page."])
    args = ["probe", "--source", str(scan), "--out", str(tmp_path / "v"), "--max-missing"]
    assert books_cli.main("parity", [*args, "0.6"]) == 0
    assert books_cli.main("parity", [*args, "0.4"]) == 1
    assert "missing over 0.4: page 1" in capsys.readouterr().out


def test_parity_fails_when_a_page_has_more_rebuilt_ink_off_the_scan_than_the_limit(facsimile, tmp_path: Path, capsys) -> None:
    scan, rebuilt = facsimile
    write_pdf(rebuilt, ["The first line of the page.", "The second line of the page.", "A third line."])
    args = ["probe", "--source", str(scan), "--out", str(tmp_path / "v"), "--max-extra"]
    assert books_cli.main("parity", [*args, "0.5"]) == 0
    assert books_cli.main("parity", [*args, "0.1"]) == 1
    assert "extra over 0.1: page 1" in capsys.readouterr().out


def write_lines_at(path: Path, left: float, lines: list[str]) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    for i, line in enumerate(lines):
        _ = page.insert_text((left, 60 + 30 * i), line, fontsize=11)
    doc.save(path)


def test_parity_fails_when_the_text_block_moved_further_than_the_offset_limit(facsimile, tmp_path: Path, capsys) -> None:
    scan, rebuilt = facsimile
    write_lines_at(rebuilt, 60, ["The first line of the page.", "The second line of the page."])
    args = ["probe", "--source", str(scan), "--out", str(tmp_path / "v"), "--max-offset"]
    assert books_cli.main("parity", [*args, "25"]) == 0
    assert books_cli.main("parity", [*args, "5"]) == 1
    assert "offset over 5.0: page 1" in capsys.readouterr().out


def test_parity_checks_an_edition_against_its_own_visual_limits_by_default(monkeypatch, tmp_path: Path, capsys) -> None:
    scan, rebuilt = tmp_path / "scan.pdf", tmp_path / "rebuilt.pdf"
    write_pdf(scan, ["The first line of the page.", "The second line of the page."])
    write_lines_at(rebuilt, 60, ["The first line of the page.", "The second line of the page."])
    parity = Parity(lambda: {1: [1]}, FACSIMILE, visual=VisualLimits(offset=5.0))
    edition = Edition(rebuilt, lambda source, formats, footnotes: None, parity=parity)
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"facsimile": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    assert books_cli.main("parity", ["probe", "--source", str(scan), "--out", str(tmp_path / "v")]) == 1
    assert "offset over 5.0: page 1" in capsys.readouterr().out
    write_lines_at(rebuilt, 40, ["The first line of the page.", "The second line of the page."])
    assert books_cli.main("parity", ["probe", "--source", str(scan), "--out", str(tmp_path / "v")]) == 0


def test_the_report_gives_region_boxes_as_plain_numbers(facsimile, tmp_path: Path) -> None:
    scan, rebuilt = facsimile
    write_pdf(rebuilt, ["The first line of the page."])
    out = tmp_path / "visual"
    _ = books_cli.main("parity", ["probe", "--source", str(scan), "--visual", "--out", str(out)])
    page = (out / "index.html").read_text()
    assert "pt² at (" in page
    assert "np.float64" not in page


def test_parity_rejects_a_limit_that_is_not_a_share(facsimile, capsys) -> None:
    scan, _ = facsimile
    with pytest.raises(SystemExit):
        books_cli.main("parity", ["probe", "--source", str(scan), "--max-missing", "1.5"])
    assert "a share from 0 to 1" in capsys.readouterr().err
