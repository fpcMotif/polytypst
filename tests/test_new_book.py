from pathlib import Path

import pytest

from polytypst.books import load_toml
from polytypst.new_book import scaffold_book


def test_new_book_writes_a_book_toml_that_the_catalog_loads(tmp_path: Path):
    written = scaffold_book(tmp_path, "hartshorne", "Algebraic Geometry", "Robin Hartshorne", "hartshorne.pdf", 512, domain="math")

    assert [p.relative_to(tmp_path).as_posix() for p in written] == ["books/hartshorne/book.toml"]
    book = load_toml("hartshorne", tmp_path / "books" / "hartshorne")
    assert book.spec.source_pdf == "hartshorne.pdf"
    assert book.spec.pdf_page_count == 512
    assert book.spec.domain == "math"
    assert book.spec.cross_references is True
    assert [(c.number, c.start_page, c.end_page) for c in book.spec.chapters] == [(1, 1, 512)]
    assert list(book.editions) == ["monograph"]
    assert not (tmp_path / "pyproject.toml").exists()


def test_new_book_quotes_titles_with_apostrophes_and_any_script(tmp_path: Path):
    scaffold_book(tmp_path, "複素_hilbert", "Hilbert's \"Theorem\"", "Ann O'Neil", "h.pdf", 9, domain="math")
    book = load_toml("複素_hilbert", tmp_path / "books" / "複素_hilbert")
    assert book.spec.title == "Hilbert's \"Theorem\""
    assert book.spec.author == "Ann O'Neil"


def test_new_book_refuses_an_existing_or_dashed_key(tmp_path: Path):
    scaffold_book(tmp_path, "hartshorne", "T", "A", "h.pdf", 1, domain="math")
    with pytest.raises(ValueError, match="exists"):
        scaffold_book(tmp_path, "hartshorne", "T", "A", "h.pdf", 1, domain="math")
    with pytest.raises(ValueError, match="dashes"):
        scaffold_book(tmp_path, "my-book", "T", "A", "h.pdf", 1, domain="math")


def test_new_book_refuses_an_unknown_domain(tmp_path: Path):
    with pytest.raises(ValueError, match="finance"):
        scaffold_book(tmp_path, "mishkin", "T", "A", "m.pdf", 1, domain="finance")
    assert not (tmp_path / "books" / "mishkin").exists()
