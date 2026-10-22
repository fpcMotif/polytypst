from pathlib import Path

import pymupdf
from conftest import PageRender

from polytypst.books import book_for_scan, books, find_known_book
from polytypst.edition import Book
from polytypst.hecke.spec import HECKE_SPEC
from polytypst.ocr.backend import Backend
from polytypst.ocr.blank import BLANK_TRANSCRIPT


def cached_backend(tmp_path: Path) -> Backend:
    cache = tmp_path / "cache"
    cache.mkdir()
    for n in (1, 2, 3):
        _ = (cache / f"p_{n:03d}.md").write_text(
            f"Cached transcript for page {n} of the book.", encoding="utf-8"
        )
    return Backend.parse(f"cached:?dir={cache}")


def test_adhoc_book_transcribes_a_photo_folder_into_its_own_store(
    tmp_path: Path, page_render: PageRender
) -> None:
    photos = page_render(1).path.parent
    for n in (2, 3):
        _ = page_render(n)
    book = Book.adhoc(photos, tmp_path / "out")

    result = book.transcribe(photos, cached_backend(tmp_path), pages={1, 3})

    assert result == {
        1: "Cached transcript for page 1 of the book.\n",
        3: "Cached transcript for page 3 of the book.\n",
    }
    assert book.transcripts == tmp_path / "out" / book.spec.markdown_dir
    assert sorted(p.name for p in book.transcripts.glob("p_*.md")) == [
        "p_001.md",
        "p_003.md",
    ]
    (edition,) = book.editions.values()
    assert edition.spec is book.spec
    assert [(c.start_page, c.end_page) for c in book.spec.chapters] == [(1, 3)]


def test_adhoc_book_marks_blank_pages_instead_of_transcribing_them(
    tmp_path: Path, page_render: PageRender
) -> None:
    for n in (1, 3):
        _ = page_render(n)
    photos = page_render(2, blank=True).path.parent

    result = Book.adhoc(photos, tmp_path / "out").transcribe(
        photos, cached_backend(tmp_path)
    )

    assert result[2] == BLANK_TRANSCRIPT
    assert result[3] == "Cached transcript for page 3 of the book.\n"


def test_a_scan_with_a_known_page_count_but_no_known_name_is_a_new_book(
    tmp_path: Path,
) -> None:
    assert HECKE_SPEC.pdf_page_count
    path = tmp_path / "Untitled scan.pdf"
    doc = pymupdf.open()
    for _ in range(HECKE_SPEC.pdf_page_count):
        doc.new_page()
    doc.save(path)

    assert book_for_scan(path) is None
    assert find_known_book(path) is None


def test_known_books_match_by_scan_name_slug_or_explicit_key(tmp_path: Path) -> None:
    hecke = books()["hecke"]
    assert book_for_scan(Path(HECKE_SPEC.source_pdf)) is hecke
    assert book_for_scan(tmp_path / f"{HECKE_SPEC.slug}.pdf") is hecke
    assert book_for_scan(tmp_path / "anything.pdf", key="hecke") is hecke
    assert find_known_book(Path(HECKE_SPEC.source_pdf)) is HECKE_SPEC
