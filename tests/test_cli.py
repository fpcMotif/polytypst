import pytest

from polytypst import books as books_module
from polytypst import books_cli, cli
from polytypst.compiler.monograph import MonographSpec
from polytypst.edition import Book, Edition


@pytest.fixture
def built(monkeypatch, tmp_path):
    calls = []
    edition = Edition(
        tmp_path / "x.pdf", lambda source, formats, footnotes: calls.append(formats), formats=frozenset({"pdf", "tex"})
    )
    book = Book(MonographSpec(slug="x", title="X", author="A"), tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    return calls


def test_build_makes_every_format_by_default(built):
    assert books_cli.main("build", ["probe"]) == 0
    assert built == [frozenset({"pdf", "tex"})]


def test_build_makes_only_the_requested_formats(built):
    assert books_cli.main("build", ["probe", "--formats", "pdf"]) == 0
    assert books_cli.main("build", ["probe", "--formats", ""]) == 0
    assert built == [frozenset({"pdf"}), frozenset()]


def test_build_rejects_a_format_the_edition_cannot_make(built, capsys):
    with pytest.raises(SystemExit):
        books_cli.main("build", ["probe", "--formats", "epub"])
    assert "epub" in capsys.readouterr().err
    assert built == []


def test_build_passes_the_footnote_numbering(monkeypatch, tmp_path):
    calls = []
    spec = MonographSpec(slug="x", title="X", author="A", footnote_style="paren")
    edition = Edition(tmp_path / "x.pdf", lambda source, formats, footnotes: calls.append(footnotes), spec=spec)
    book = Book(spec, tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    assert books_cli.main("build", ["probe"]) == 0
    assert books_cli.main("build", ["probe", "--footnotes", "running"]) == 0
    assert calls == ["original", "running"]


def test_build_rejects_running_footnotes_for_a_book_without_notes(built, capsys):
    with pytest.raises(SystemExit):
        books_cli.main("build", ["probe", "--footnotes", "running"])
    assert "footnotes" in capsys.readouterr().err
    assert built == []


def test_top_level_help_lists_the_book_commands(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["polytypst", "--help"])
    with pytest.raises(SystemExit):
        cli.main()
    out = capsys.readouterr().out
    for command in ("books", "build", "parity", "new-book"):
        assert f"polytypst {command}" in out
    assert "modern-firm" not in out
