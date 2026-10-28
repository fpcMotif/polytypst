import ast
import tomllib
from pathlib import Path

import pytest

from polytypst.new_book import scaffold_book

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "pyproject.toml").write_text((ROOT / "pyproject.toml").read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def test_new_book_writes_a_registered_package(repo: Path):
    written = scaffold_book(repo, "hartshorne", "Algebraic Geometry", "Robin Hartshorne", "hartshorne.pdf", 512, domain="math")

    assert sorted(p.relative_to(repo).as_posix() for p in written) == [
        "src/hartshorne/__init__.py",
        "src/hartshorne/book.py",
        "src/hartshorne/spec.py",
    ]
    for path in written:
        ast.parse(path.read_text(encoding="utf-8"))
    spec = (repo / "src/hartshorne/spec.py").read_text(encoding="utf-8")
    assert 'source_pdf="hartshorne.pdf"' in spec
    assert "pdf_page_count=512" in spec
    assert 'domain="math"' in spec
    assert "BOOK = Book(" in (repo / "src/hartshorne/book.py").read_text(encoding="utf-8")

    packages = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]["packages"]
    assert "polytypst.hartshorne" in packages
    assert packages == sorted(packages)


def test_new_book_quotes_titles_with_apostrophes(repo: Path):
    scaffold_book(repo, "hilbert", "Hilbert's Theorem", "Ann O'Neil", "h.pdf", 9, domain="math")
    spec = (repo / "src/hilbert/spec.py").read_text(encoding="utf-8")
    ast.parse(spec)
    assert "Hilbert's Theorem" in spec


def test_new_book_refuses_an_existing_or_invalid_key(repo: Path):
    scaffold_book(repo, "hartshorne", "T", "A", "h.pdf", 1, domain="math")
    with pytest.raises(ValueError, match="exists"):
        scaffold_book(repo, "hartshorne", "T", "A", "h.pdf", 1, domain="math")
    with pytest.raises(ValueError, match="identifier"):
        scaffold_book(repo, "my-book", "T", "A", "h.pdf", 1, domain="math")


def test_new_book_refuses_an_unknown_domain(repo: Path):
    with pytest.raises(ValueError, match="finance"):
        scaffold_book(repo, "mishkin", "T", "A", "m.pdf", 1, domain="finance")
    assert not (repo / "src/mishkin").exists()
