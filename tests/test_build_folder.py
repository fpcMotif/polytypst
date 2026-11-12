from pathlib import Path

import pytest

from polytypst import books_cli
from polytypst.compiler.monograph import build_dir, build_source


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    book = tmp_path / "polytypst-output" / "kirillov"
    (book / "figures").mkdir(parents=True)
    _ = (book / "figures" / "f1.svg").write_text("<svg/>", encoding="utf-8")
    return book


def test_sources_sit_in_build_beside_the_pdf_by_default(out_dir: Path) -> None:
    assert build_source(out_dir / "kirillov1976.pdf", "typ") == out_dir / "build" / "kirillov1976.typ"


def test_polytypst_build_moves_the_sources_into_a_folder_per_book(
    out_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace" / "build"
    monkeypatch.setenv("POLYTYPST_BUILD", str(root))

    assert build_source(out_dir / "kirillov1976.pdf", "tex") == root / "kirillov" / "kirillov1976.tex"


def test_a_build_folder_elsewhere_still_reaches_the_book_figures(
    out_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace" / "build"
    monkeypatch.setenv("POLYTYPST_BUILD", str(root))

    build = build_dir(out_dir)

    assert build == root / "kirillov"
    assert (build / "figures" / "f1.svg").read_text(encoding="utf-8") == "<svg/>"


def test_build_dir_flag_sets_where_the_build_writes_its_sources(
    out_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[Path] = []
    monkeypatch.setattr(books_cli, "_build", lambda parser, args: seen.append(build_source(out_dir / "k.pdf", "typ")) or 0)

    assert books_cli.main("build", ["kirillov", "--build-dir", str(tmp_path / "ws" / "build")]) == 0
    assert seen == [tmp_path / "ws" / "build" / "kirillov" / "k.typ"]
