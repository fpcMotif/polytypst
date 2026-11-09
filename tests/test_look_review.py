import json
from pathlib import Path

import pytest

from polytypst.look_review import (
    GroupResult,
    append_findings,
    group_problems,
    group_ranges,
    next_id_number,
    rebuilt_to_scan,
    shared_text_map,
    unaudited_pages,
)


def _finding(**extra: str) -> dict:
    row = {
        "id": "TBD",
        "book": "b",
        "severity": "P1",
        "format": "typst",
        "where": "p1",
        "what": "w",
        "evidence": "e",
        "status": "open",
    }
    return row | extra


def test_rebuilt_to_scan_inverts_a_scan_page_map_and_keeps_scan_order() -> None:
    scan_map = {7: [1], 8: [1, 2], 9: [], 10: [3]}
    assert rebuilt_to_scan(scan_map) == {1: [7, 8], 2: [8], 3: [10]}


def test_shared_text_map_maps_a_split_scan_page_to_both_rebuilt_pages_and_drops_a_lost_one() -> (
    None
):
    scan = {
        5: {"aaaa", "bbbb", "cccc", "dddd", "eeee"},
        6: {"ffff", "gggg", "hhhh", "iiii", "jjjj"},
        7: {"kkkk"},
    }
    where = {
        "aaaa": {1},
        "bbbb": {1},
        "cccc": {1},
        "dddd": {2},
        "eeee": {2},
        "ffff": {2, 9},
        "gggg": {3, 4, 7},
        "zzzz": {3},
    }
    assert shared_text_map(scan, where) == {5: [1, 2]}


def test_shared_text_map_ignores_transcript_markup_that_never_reaches_the_pdf() -> None:
    markup = {f"m{i:03d}" for i in range(17)}
    common = {"the1", "the2", "the3", "the4"}
    scan = {12: markup | common | {"uni1", "uni2", "uni3"}}
    where = {g: {1, 2, 3, 4} for g in common} | {"uni1": {4}, "uni2": {4}, "uni3": {4}}
    assert shared_text_map(scan, where) == {12: [4]}


def test_group_ranges_split_pages_into_fixed_size_inclusive_ranges() -> None:
    assert group_ranges(45, 20) == [(1, 20), (21, 40), (41, 45)]


def test_next_id_number_continues_after_the_highest_id_of_the_book_only(
    tmp_path: Path,
) -> None:
    findings = tmp_path / "review_findings.jsonl"
    findings.write_text(
        "\n".join(
            json.dumps(_finding(id=i))
            for i in ("Briemann-07", "Briemann-12", "Bother-40")
        )
        + "\n"
    )
    assert next_id_number(findings, "riemann") == 13
    assert next_id_number(tmp_path / "missing.jsonl", "riemann") == 1


def test_unaudited_pages_lists_every_page_no_audit_line_covers(tmp_path: Path) -> None:
    (tmp_path / "group_01.audit.jsonl").write_text(
        "\n".join(json.dumps({"page": p, "result": "PASS"}) for p in (1, 2, 4))
    )
    assert unaudited_pages(tmp_path, 5) == [3, 5]


def test_group_problems_is_empty_only_when_both_files_are_valid_and_every_page_is_audited(
    tmp_path: Path,
) -> None:
    assert group_problems(tmp_path, 1, 1, 3) == [
        "group_01.jsonl is missing",
        "group_01.audit.jsonl is missing",
    ]
    (tmp_path / "group_01.jsonl").write_text(json.dumps(_finding()) + "\n{bad\n")
    (tmp_path / "group_01.audit.jsonl").write_text(
        "\n".join(json.dumps({"page": p}) for p in (1, 3))
    )
    assert [p.split(":")[0] for p in group_problems(tmp_path, 1, 1, 3)] == [
        "group_01.jsonl line 2"
    ]
    (tmp_path / "group_01.jsonl").write_text(json.dumps(_finding()) + "\n")
    assert group_problems(tmp_path, 1, 1, 3) == [
        "group_01.audit.jsonl has no line for pages 2"
    ]
    (tmp_path / "group_01.audit.jsonl").write_text(
        "\n".join(json.dumps({"page": p}) for p in (1, 2, 3))
    )
    assert group_problems(tmp_path, 1, 1, 3) == []


def test_append_findings_gives_real_ids_and_appends_valid_lines(tmp_path: Path) -> None:
    review = tmp_path / "look"
    review.mkdir()
    (review / "group_01.jsonl").write_text(
        json.dumps(_finding(cause="transcript")) + "\n"
    )
    (review / "group_02.jsonl").write_text(json.dumps(_finding(severity="P0")) + "\n")
    findings = tmp_path / "review_findings.jsonl"
    findings.write_text(json.dumps(_finding(id="Bb-03")) + "\n")
    result = append_findings(review, "b", findings)
    assert result == GroupResult(appended=2, first_id="Bb-04", last_id="Bb-05")
    ids = [json.loads(line)["id"] for line in findings.read_text().splitlines()]
    assert ids == ["Bb-03", "Bb-04", "Bb-05"]


def test_append_findings_refuses_bad_lines_and_writes_nothing(tmp_path: Path) -> None:
    review = tmp_path / "look"
    review.mkdir()
    (review / "group_01.jsonl").write_text(json.dumps(_finding(severity="P9")) + "\n")
    findings = tmp_path / "review_findings.jsonl"
    with pytest.raises(ValueError, match="group_01.jsonl line 1"):
        append_findings(review, "b", findings)
    assert not findings.exists()


def test_append_findings_twice_does_not_duplicate_a_book(tmp_path: Path) -> None:
    review = tmp_path / "look"
    review.mkdir()
    (review / "group_01.jsonl").write_text(json.dumps(_finding()) + "\n")
    findings = tmp_path / "review_findings.jsonl"
    append_findings(review, "b", findings)
    with pytest.raises(ValueError, match="already merged"):
        append_findings(review, "b", findings)
