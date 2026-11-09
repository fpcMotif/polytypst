from pathlib import Path

import pytest

from polytypst.book_state import BookStateError, book_state, transcripts


@pytest.fixture
def pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "polytypst-books"
    root.mkdir()
    monkeypatch.setenv("POLYTYPST_BOOKS", str(root))
    return root


def holding(root: Path, key: str) -> Path:
    (root / key / "markdown_pages").mkdir(parents=True)
    return root / key


def test_pinned_root_wins_over_a_copy_beside_it(pin: Path) -> None:
    _ = holding(pin.parent / "polytypst-store-a", "book4")
    pinned = holding(pin, "book4")

    assert book_state(Path("output/book4")) == pinned


def test_book_found_only_in_a_store_beside_the_pin(pin: Path) -> None:
    weil = holding(pin.parent / "polytypst-store-weil", "weil")

    assert book_state(Path("output/weil")) == weil


def test_symlinked_copy_counts_once(pin: Path) -> None:
    real = holding(pin.parent / "polytypst-store-a", "book4")
    (pin.parent / "polytypst-store-b").mkdir()
    (pin.parent / "polytypst-store-b" / "book4").symlink_to(real)

    assert book_state(Path("output/book4")).resolve() == real.resolve()


def test_two_real_copies_beside_the_pin_stop_and_name_both(pin: Path) -> None:
    first = holding(pin.parent / "polytypst-store-a", "book4")
    second = holding(pin.parent / "polytypst-store-b", "book4")

    with pytest.raises(BookStateError, match="POLYTYPST_BOOKS") as stop:
        _ = book_state(Path("output/book4"))

    assert str(first) in str(stop.value) and str(second) in str(stop.value)


def test_new_book_goes_under_the_pin(pin: Path) -> None:
    _ = holding(pin.parent / "polytypst-store-a", "other")

    assert book_state(Path("output/fresh")) == pin / "fresh"


def test_unrelated_sibling_folders_are_not_stores(pin: Path) -> None:
    _ = holding(pin.parent / "somewhere-else", "book4")

    assert book_state(Path("output/book4")) == pin / "book4"


def test_no_pin_names_the_variable(pin: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = holding(pin, "book4")
    monkeypatch.delenv("POLYTYPST_BOOKS")

    with pytest.raises(BookStateError, match="POLYTYPST_BOOKS"):
        _ = book_state(Path("output/book4"))


def test_transcripts_live_in_the_book_state(pin: Path) -> None:
    weil = holding(pin.parent / "polytypst-store-weil", "weil")

    assert transcripts(Path("output/weil")) == weil / "markdown_pages"
