import pytest

from polytypst import cli


def test_top_level_help_lists_the_book_commands(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["polytypst", "--help"])
    with pytest.raises(SystemExit):
        cli.main()
    out = capsys.readouterr().out
    for command in ("books", "build", "parity", "new-book"):
        assert f"polytypst {command}" in out
    assert "modern-firm" not in out
