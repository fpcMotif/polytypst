import hashlib
import json
from pathlib import Path

import pytest

from scripts import page_check


@pytest.fixture
def book(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    store = tmp_path / "store"
    store.mkdir()
    (store / "p_001.md").write_text("第一页。\n", encoding="utf-8")
    (store / "p_002.md").write_text("第二页。\n", encoding="utf-8")
    results = tmp_path / "results"
    (results / "x" / "png").mkdir(parents=True)
    monkeypatch.setattr(page_check, "RESULTS", results)
    monkeypatch.setattr(page_check, "LEGACY", tmp_path / "legacy.json")
    monkeypatch.setattr(page_check, "transcript_path", lambda _book, page: store / f"p_{page:03d}.md")
    monkeypatch.setattr(page_check, "transcript_pages", lambda _book: [1, 2])
    return results / "x"


def render(out: Path, page: int) -> None:
    (out / "png" / f"p{page}.png").write_bytes(f"scan image {page}".encode())


def write(out: Path, *records: dict) -> Path:
    path = out / "p1-2.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


def test_a_stub_record_with_no_receipt_does_not_count_as_checked(book: Path) -> None:
    render(book, 1)
    write(book, {"page": 1, "issues": []}, {"page": 2, "issues": []})
    t = page_check.tally("x")
    assert t.checked == set()
    assert t.unproven == {1, 2}


def test_a_record_with_the_receipt_from_text_counts_as_checked(book: Path) -> None:
    render(book, 1)
    write(book, {"page": 1, "issues": [], "receipt": page_check.receipt("x", 1)})
    assert page_check.tally("x").checked == {1}


def test_no_receipt_exists_before_the_scan_page_is_rendered(book: Path) -> None:
    assert page_check.receipt("x", 2) is None


def test_a_made_up_receipt_does_not_count(book: Path) -> None:
    render(book, 1)
    write(book, {"page": 1, "issues": [], "receipt": "0123456789ab"})
    assert page_check.tally("x").unproven == {1}


def test_a_check_goes_stale_when_the_transcript_changes(book: Path) -> None:
    render(book, 1)
    write(book, {"page": 1, "issues": [], "receipt": page_check.receipt("x", 1)})
    page_check.transcript_path("x", 1).write_text("第一页，改过。\n", encoding="utf-8")
    assert page_check.tally("x").unproven == {1}


def test_a_listed_legacy_file_counts_until_someone_edits_it(book: Path) -> None:
    path = write(book, {"page": 1, "issues": []})
    page_check.LEGACY.write_text(
        json.dumps({"x": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}}), encoding="utf-8"
    )
    assert page_check.tally("x").checked == {1}
    write(book, {"page": 1, "issues": []}, {"page": 2, "issues": []})
    assert page_check.tally("x").checked == set()
