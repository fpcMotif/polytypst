import json
from pathlib import Path

import pymupdf
import pytest

from scripts import book_check

page_check = book_check.page_check
render_check = book_check.render_check


@pytest.fixture
def book(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A two-page book "x" whose pages are checked, linted and verified, with figure 图1-1 in the scan,
    the manifest and the rebuilt PDF, and an audit that exits 0."""
    store = tmp_path / "store"
    store.mkdir()
    results = tmp_path / "results"
    (results / "x" / "png").mkdir(parents=True)
    monkeypatch.setattr(page_check, "RESULTS", results)
    monkeypatch.setattr(page_check, "LEGACY", tmp_path / "legacy.json")
    monkeypatch.setattr(page_check, "transcript_path", lambda _book, page: store / f"p_{page:03d}.md")
    set_pages(monkeypatch, store, 2)
    monkeypatch.setattr(render_check, "scan_pages", lambda _book: {"图1-1": 1, "表1-1": 2})
    monkeypatch.setattr(book_check, "audit", lambda _book: (0, "all counts at or below the baseline"))
    check_pages(results / "x", 2, issues=[{"kind": "word", "transcript": "甲", "scan": "乙"}])
    (results / "x" / "lint.jsonl").write_text("", encoding="utf-8")
    verdict(results / "x", {"page": 1, "kind": "word", "transcript": "甲", "scan": "乙", "verdict": "real"})
    write_manifest(tmp_path, ["图 1-1 增长率"])
    write_pdf(tmp_path / "x.pdf", ["图 1-1 增长率", "表 1-1 数据"])
    return tmp_path


def set_pages(monkeypatch: pytest.MonkeyPatch, store: Path, count: int) -> None:
    for page in range(1, count + 1):
        (store / f"p_{page:03d}.md").write_text(f"第{page}页。\n", encoding="utf-8")
    monkeypatch.setattr(page_check, "transcript_pages", lambda _book: list(range(1, count + 1)))


def check_pages(out: Path, count: int, issues: list[dict] | None = None) -> None:
    records = []
    for page in range(1, count + 1):
        (out / "png" / f"p{page}.png").write_bytes(f"scan image {page}".encode())
        found = issues if page == 1 and issues else []
        records.append({"page": page, "issues": found, "receipt": page_check.receipt("x", page)})
    (out / f"p1-{count}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def verdict(out: Path, record: dict) -> None:
    with (out / "verdicts.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_manifest(root: Path, captions: list[str]) -> None:
    figures = [
        {"figure_id": str(n), "caption": c, "image_rel_path": f"figures/{n}.png", "source_page": 1}
        for n, c in enumerate(captions, 1)
    ]
    (root / "figures_manifest.json").write_text(json.dumps(figures, ensure_ascii=False), encoding="utf-8")


def write_pdf(path: Path, captions: list[str]) -> None:
    doc = pymupdf.open()
    for caption in captions:
        doc.new_page().insert_text((72, 72), caption, fontname="china-s")
    doc.save(path)


def run(root: Path) -> list[str]:
    return book_check.gate("x", root / "x.pdf", root / "figures_manifest.json")


def fails(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith("FAIL")]


def test_a_book_that_meets_every_check_passes(book: Path) -> None:
    lines = run(book)
    assert fails(lines) == []
    assert lines[-1] == "PASS"


def test_a_page_without_a_valid_receipt_fails_the_gate(book: Path) -> None:
    page_check.transcript_path("x", 2).write_text("第二页，改过。\n", encoding="utf-8")
    lines = run(book)
    assert any("page check" in line and "2" in line for line in fails(lines))
    assert lines[-1].startswith("FAIL")


def test_a_book_whose_lint_has_not_run_fails(book: Path) -> None:
    (page_check.RESULTS / "x" / "lint.jsonl").unlink()
    assert any("lint" in line for line in fails(run(book)))


def test_an_issue_with_no_verdict_fails(book: Path) -> None:
    (page_check.RESULTS / "x" / "verdicts.jsonl").unlink()
    assert any("verdicts" in line and "1 unverified" in line for line in fails(run(book)))


def test_no_issues_from_more_than_100_pages_gives_a_warning(
    book: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = page_check.RESULTS / "x"
    for path in out.glob("*.jsonl"):
        path.unlink()
    (out / "lint.jsonl").write_text("", encoding="utf-8")
    set_pages(monkeypatch, book / "store", 101)
    check_pages(out, 101)
    lines = run(book)
    assert any(line.startswith("WARN") and "0 issues from 101 pages" in line for line in lines)
    assert lines[-1] == "PASS"


def test_an_empty_figure_manifest_fails_and_names_the_missing_figure(book: Path) -> None:
    write_manifest(book, [])
    assert any("manifest" in line and "图1-1" in line for line in fails(run(book)))


def test_a_scan_figure_missing_from_the_rebuilt_pdf_fails(book: Path) -> None:
    write_pdf(book / "x.pdf", ["表 1-1 数据"])
    assert any("rebuilt PDF" in line and "图1-1" in line for line in fails(run(book)))


def test_a_missing_rebuilt_pdf_fails(book: Path) -> None:
    (book / "x.pdf").unlink()
    assert any("rebuilt PDF" in line for line in fails(run(book)))


def test_an_audit_that_exits_1_fails_with_its_last_line(book: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(book_check, "audit", lambda _book: (1, "glued_words rose from 3 to 9"))
    assert any("audit" in line and "glued_words rose from 3 to 9" in line for line in fails(run(book)))
