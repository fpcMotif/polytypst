import json
import os
import re
import subprocess
from dataclasses import asdict, fields
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from polytypst.compare_sheet import SHEET_LIMIT, Panel
from polytypst.look_review import (
    GroupResult,
    PageEntry,
    TextHit,
    append_findings,
    brief,
    close_workspace,
    crop,
    find_text,
    group_problems,
    group_ranges,
    missing_inputs,
    next_id_number,
    open_workspace,
    pair_sheets,
    parse_box,
    pass_rules,
    prepare,
    read_groups,
    read_pages,
    rebuilt_to_scan,
    sample_ranges,
    shared_text_map,
    spot_check,
    stock,
    unaudited_pages,
    write_groups,
)
from polytypst.review import Finding

REPO = Path(__file__).resolve().parent.parent


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


def test_sample_ranges_take_the_first_middle_and_last_group_of_a_long_book() -> None:
    assert sample_ranges(100, 10) == [(1, 10), (51, 60), (91, 100)]
    assert sample_ranges(25, 10) == [(1, 10), (11, 20), (21, 25)]


def test_unaudited_pages_lists_every_page_of_a_group_that_no_audit_line_covers(
    tmp_path: Path,
) -> None:
    write_groups(tmp_path, [(1, 3), (8, 9)])
    (tmp_path / "group_01.audit.jsonl").write_text(
        "\n".join(json.dumps({"page": p, "result": "PASS"}) for p in (1, 2, 8))
    )
    assert unaudited_pages(tmp_path) == [3, 9]


def test_a_review_prepared_before_the_cause_list_keeps_its_groups_and_free_causes(
    tmp_path: Path,
) -> None:
    (tmp_path / "look_groups.json").write_text("[[1, 2], [3, 4]]")
    (tmp_path / "group_01.jsonl").write_text(
        json.dumps(_finding(cause="src/compiler/monograph.py")) + "\n"
    )
    (tmp_path / "group_01.audit.jsonl").write_text(
        "\n".join(json.dumps({"page": p}) for p in (1, 2))
    )
    assert read_groups(tmp_path) == [(1, 2), (3, 4)]
    assert group_problems(tmp_path, 1, 1, 2) == []


def test_group_problems_names_a_cause_outside_the_list(tmp_path: Path) -> None:
    write_groups(tmp_path, [(1, 1)])
    rows = [
        _finding(cause="build"),
        _finding(cause="src/compiler/monograph.py"),
        _finding(),
    ]
    (tmp_path / "group_01.jsonl").write_text("\n".join(map(json.dumps, rows)))
    (tmp_path / "group_01.audit.jsonl").write_text(json.dumps({"page": 1}))
    assert group_problems(tmp_path, 1, 1, 1) == [
        "group_01.jsonl line 2: cause 'src/compiler/monograph.py' is not one of transcript, build, unknown",
        "group_01.jsonl line 3: cause None is not one of transcript, build, unknown",
    ]


def _pdf(path: Path, pages: list[str]) -> Path:
    doc = pymupdf.open()
    for text in pages:
        doc.new_page().insert_text((72, 100), text)
    doc.save(path)
    return path


def test_prepare_renders_the_pages_of_its_groups_and_renders_again_after_a_rebuild(
    tmp_path: Path,
) -> None:
    rebuilt = _pdf(tmp_path / "book.pdf", ["one", "two $x^2$", "three"])
    scan = _pdf(tmp_path / "scan.pdf", ["one", "two", "three"])
    review = tmp_path / "look"
    entries = prepare(rebuilt, scan, {1: [1], 2: [2], 3: [3]}, review, [(2, 3)], 40)
    assert [e.page for e in entries] == [2, 3]
    assert read_pages(review) == entries
    assert sorted(p.name for p in (review / "png").iterdir()) == [
        "pair_002.png",
        "pair_003.png",
        "r_002.png",
        "r_003.png",
        "s_002.png",
        "s_003.png",
    ]
    assert entries[0].pair_png == "png/pair_002.png"
    assert "UNRENDERED_MATH_DELIMITER" in entries[0].checker
    assert "UNRENDERED_MATH_DELIMITER" not in entries[1].checker
    old = (review / "png" / "r_002.png").read_bytes()
    os.utime(review / "png" / "r_002.png", (0, 0))
    _pdf(rebuilt, ["one", "two, set again", "three"])
    prepare(rebuilt, scan, {1: [1], 2: [2], 3: [3]}, review, [(2, 3)], 40)
    assert (review / "png" / "r_002.png").read_bytes() != old


def test_spot_check_picks_grave_findings_and_passed_pages_and_renders_them(
    tmp_path: Path,
) -> None:
    rebuilt = _pdf(tmp_path / "book.pdf", ["one", "two", "three", "four"])
    scan = _pdf(tmp_path / "scan.pdf", ["one", "two", "three", "four"])
    review = tmp_path / "look"
    prepare(rebuilt, scan, {n: [n] for n in range(1, 5)}, review, [(1, 4)], 40)
    rows = [
        _finding(severity="P3", where="rebuilt p1"),
        _finding(severity="P0", where="rebuilt p2, scan p2", what="lost paragraph"),
    ]
    (review / "group_01.jsonl").write_text("\n".join(map(json.dumps, rows)))
    (review / "group_01.audit.jsonl").write_text(
        "\n".join(
            json.dumps({"page": p, "scan_pages": [p], "result": r})
            for p, r in ((1, "FAIL"), (2, "FAIL"), (3, "PASS"), (4, "PASS"))
        )
    )
    items = spot_check(review, rebuilt, scan, dpi=40)
    assert [(i.item, i.page) for i in items] == [
        ("group_01.jsonl line 2", 2),
        ("PASS", 3),
        ("PASS", 4),
    ]
    assert items[0].text == "rebuilt p2, scan p2: lost paragraph"
    assert all((review / png).exists() for i in items for png in i.pngs)
    assert items[1].pngs == ["crops/spot_p003.png"]
    with Image.open(review / items[1].pngs[0]) as sheet:
        assert max(sheet.size) <= SHEET_LIMIT


def test_brief_names_only_look_review_verbs_and_every_finding_field(
    tmp_path: Path,
) -> None:
    template = (REPO / "docs" / "prompts" / "look-review-group.md").read_text(encoding="utf-8")
    pages = [PageEntry(p, [p + 4], f"png/r_{p:03d}.png", [f"png/s_{p + 4:03d}.png"], 0.0, "") for p in (1, 2)]
    text = brief(template, tmp_path, "weil", 1, 1, 2, pages, ["- fact"], _bar())
    assert all(p.startswith(str(tmp_path)) for p in re.findall(r"(?<![\w.])/(?:Users|private|var|tmp)/[^\s`]*", text))
    assert "src/" not in text
    assert "scripts/" not in text
    assert "mise " not in text
    assert not re.search(r"docs/[\w./-]+\.md", text)
    assert "| Theorem head |" in text
    assert f"`{tmp_path}/lr check 1`" in text
    assert f"`{tmp_path}/lr crop PAGE:BOX" in text
    assert all(f"`{f.name}`" in text for f in fields(Finding))


@pytest.mark.slow
def test_stock_writes_an_lr_that_runs_look_review_for_its_book_from_any_folder(
    tmp_path: Path,
) -> None:
    review, transcripts = tmp_path / "look" / "sample", tmp_path / "store"
    review.mkdir(parents=True)
    write_groups(review, [(1, 2)])
    (review / "look_pages.jsonl").write_text(
        "".join(
            json.dumps(asdict(PageEntry(p, scans, "", [], 0.0, ""))) + "\n"
            for p, scans in ((1, [5]), (2, [6, 7]))
        )
    )
    transcripts.mkdir()
    for n in (5, 6, 9):
        (transcripts / f"p_{n:03d}.md").write_text(f"page {n}")
    repo = tmp_path / "my repo"
    stock(review, repo, "数学 book", transcripts, sample=True)
    assert sorted(p.name for p in (review / "transcript").iterdir()) == ["p_005.md", "p_006.md"]
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "mise").write_text('#!/bin/sh\nfor a in "$@"; do echo "$a"; done\n')
    (fake / "mise").chmod(0o755)
    run = subprocess.run(
        [str(review / "lr"), "check", "7"],
        cwd="/",
        env={**os.environ, "PATH": f"{fake}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert run.stdout.splitlines() == [
        "exec", "-C", str(repo), "--", "uv", "run", "-q", "--project", str(repo), "python",
        str(repo / "scripts" / "look_review.py"), "check", "数学 book", "7", "--sample",
    ]


def _argv(lr: Path, *args: str, fake: Path) -> list[str]:
    """What `lr ARGS` hands to mise, with `fake/mise` printing its arguments one per line."""
    fake.mkdir(exist_ok=True)
    (fake / "mise").write_text('#!/bin/sh\nfor a in "$@"; do echo "$a"; done\n')
    (fake / "mise").chmod(0o755)
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}"}
    return subprocess.run([str(lr), *args], cwd="/", env=env, capture_output=True, text=True, check=True).stdout.splitlines()


def test_open_workspace_gives_the_orchestrator_lr_and_its_skill_and_close_removes_only_them(
    tmp_path: Path,
) -> None:
    root, repo = tmp_path / "look_review", tmp_path / "my repo"
    skill = repo / ".agent" / "skills" / "antigravity-look-review"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("skill")
    (skill / "references" / "book-notes.md").write_text("notes")
    (root / "weil").mkdir(parents=True)
    (root / "weil" / "group_01.jsonl").write_text("{}")
    open_workspace(root, repo, skill)
    copy = root / ".agent" / "skills" / "antigravity-look-review"
    assert (copy / "SKILL.md").read_text() == "skill"
    assert (copy / "references" / "book-notes.md").read_text() == "notes"
    run = ["exec", "-C", str(repo), "--", "uv", "run", "-q", "--project", str(repo), "python"]
    assert _argv(root / "lr", "status", "weil", "--sample", fake=tmp_path / "bin") == [
        *run, str(repo / "scripts" / "look_review.py"), "status", "weil", "--sample",
    ]
    assert _argv(root / "lr", "build", "weil", fake=tmp_path / "bin") == [
        *run, str(repo / "scripts" / "one_book.py"), "weil", "build", "--formats", "pdf",
    ]
    close_workspace(root)
    assert sorted(p.name for p in root.iterdir()) == ["weil"]
    assert (root / "weil" / "group_01.jsonl").exists()


def test_parse_box_takes_names_and_page_shares_and_refuses_points() -> None:
    assert parse_box("middle") == (0.0, 0.3, 1.0, 0.7)
    assert parse_box("0,0.4,1,0.8") == (0.0, 0.4, 1.0, 0.8)
    with pytest.raises(ValueError, match="shares of the page"):
        parse_box("70,50,530,650")
    with pytest.raises(ValueError, match="not one of"):
        parse_box("centre")


def test_pair_sheet_puts_scan_beside_rebuilt_without_the_white_margins(
    tmp_path: Path,
) -> None:
    rebuilt = _pdf(tmp_path / "book.pdf", ["one"])
    scan = _pdf(tmp_path / "scan.pdf", ["one"])
    review = tmp_path / "look"
    [entry] = prepare(rebuilt, scan, {1: [1]}, review, [(1, 1)], 72)
    with Image.open(review / entry.pair_png) as pair, Image.open(review / entry.rebuilt_png) as page:
        assert pair.width < 2 * page.width
        assert pair.height < page.height


def test_a_panel_of_a_page_the_pdf_lacks_names_the_pdf_and_its_page_count(tmp_path: Path) -> None:
    scan = _pdf(tmp_path / "scan.pdf", ["one", "two", "three"])
    for page in (0, 4):
        with pytest.raises(ValueError, match=r"scan\.pdf has 3 pages"):
            Panel("scan", scan, page)
    assert Panel("scan", scan, 3).page == 3


def test_crop_puts_every_region_of_one_call_on_one_sheet_within_the_image_limit(
    tmp_path: Path,
) -> None:
    rebuilt = _pdf(tmp_path / "book.pdf", ["one", "two"])
    scan = _pdf(tmp_path / "scan.pdf", ["one", "two", "two again"])
    review = tmp_path / "look"
    prepare(rebuilt, scan, {1: [1], 2: [2], 3: [2]}, review, [(1, 2)], 40)
    out = crop(review, rebuilt, scan, ["1:top", "2:0,0,0.4,0.2:full"])
    assert out.parent == review / "crops"
    with Image.open(out) as sheet:
        assert max(sheet.size) <= SHEET_LIMIT
    with pytest.raises(ValueError, match="not in this review"):
        crop(review, rebuilt, scan, ["9:top"])
    with pytest.raises(ValueError, match="PAGE:BOX"):
        crop(review, rebuilt, scan, ["top"])


def test_crop_by_scan_page_brings_the_rebuilt_pages_paired_with_it(tmp_path: Path) -> None:
    rebuilt = _pdf(tmp_path / "book.pdf", ["one", "two"])
    scan = _pdf(tmp_path / "scan.pdf", ["one", "two", "two again"])
    review = tmp_path / "look"
    prepare(rebuilt, scan, {1: [1], 2: [2], 3: [2]}, review, [(1, 2)], 40)
    out = crop(review, rebuilt, scan, ["3:top"], by_scan=True)
    assert out.name == "sheet_scan_3-top.png"
    with pytest.raises(ValueError, match="scan page 9 pairs with no rebuilt page"):
        crop(review, rebuilt, scan, ["9:top"], by_scan=True)


def test_find_text_names_rebuilt_pages_with_their_scan_pages_and_matching_transcripts(
    tmp_path: Path,
) -> None:
    rebuilt = _pdf(tmp_path / "book.pdf", ["one", "see (4.3.60) here"])
    scan = _pdf(tmp_path / "scan.pdf", ["one", "two", "three"])
    review = tmp_path / "look"
    prepare(rebuilt, scan, {1: [1], 2: [2], 3: [2]}, review, [(1, 2)], 40)
    (review / "transcript").mkdir(exist_ok=True)
    (review / "transcript" / "p_003.md").write_text("$$ x \\tag{4.3.60} $$", encoding="utf-8")
    assert find_text(review, rebuilt, "4.3.60") == [TextHit(2, [2, 3]), TextHit(None, [3])]
    assert find_text(review, rebuilt, "absent") == []


def test_brief_lists_one_pair_sheet_per_page(tmp_path: Path) -> None:
    template = (REPO / "docs" / "prompts" / "look-review-group.md").read_text(encoding="utf-8")
    pages = [PageEntry(1, [5], "png/r_001.png", ["png/s_005.png"], 0.0, "", [], "png/pair_001.png")]
    text = brief(template, tmp_path, "weil", 1, 1, 1, pages, [], [])
    assert "png/pair_001.png" in text
    assert "png/r_001.png" not in text


def test_brief_names_no_single_page_pngs_beside_its_pair_sheet_wording(tmp_path: Path) -> None:
    template = (REPO / "docs" / "prompts" / "look-review-group.md").read_text(encoding="utf-8")
    older = [PageEntry(1, [5], "png/r_001.png", ["png/s_005.png"], 0.0, "")]
    text = brief(template, tmp_path, "weil", 1, 1, 1, older, [], [])
    assert "Open each page's pair sheet" in text
    assert "png/r_001.png" not in text
    assert "png/s_005.png" not in text


def test_pair_sheets_writes_the_sheets_an_older_prepare_left_out_of_a_group(
    tmp_path: Path,
) -> None:
    rebuilt = _pdf(tmp_path / "book.pdf", ["one", "two", "three"])
    scan = _pdf(tmp_path / "scan.pdf", ["one", "two", "three"])
    review = tmp_path / "look"
    prepare(rebuilt, scan, {1: [1], 2: [2], 3: [3]}, review, [(1, 3)], 40)
    for page in (1, 2, 3):
        (review / "png" / f"pair_{page:03d}.png").unlink()
    older = [PageEntry(e.page, e.scan_pages, e.rebuilt_png, e.scan_pngs, 0.0, "") for e in read_pages(review)]
    pair_sheets(review, rebuilt, scan, older, 1, 2, 40)
    assert missing_inputs(review, older, 1, 2) == ["lr", "transcript/"]
    assert not (review / "png" / "pair_003.png").exists()


def test_missing_inputs_names_what_an_older_prepare_left_out_of_the_review(tmp_path: Path) -> None:
    review = tmp_path / "weil"
    (review / "png").mkdir(parents=True)
    pages = [
        PageEntry(1, [5], "png/r_001.png", ["png/s_005.png"], 0.0, ""),
        PageEntry(2, [6], "png/r_002.png", ["png/s_006.png"], 0.0, "", [], "png/pair_002.png"),
        PageEntry(3, [7], "png/r_003.png", ["png/s_007.png"], 0.0, ""),
    ]
    assert missing_inputs(review, pages, 1, 2) == ["lr", "transcript/", "png/pair_001.png", "png/pair_002.png"]
    for name in ("lr", "png/pair_001.png", "png/pair_002.png"):
        (review / name).write_text("")
    (review / "transcript").mkdir()
    assert missing_inputs(review, pages, 1, 2) == []


def _bar() -> list[str]:
    docs = REPO / "docs"
    return pass_rules((docs / "prompts" / "math-book-check.md").read_text(encoding="utf-8")) + pass_rules(
        (docs / "publisher-bar.md").read_text(encoding="utf-8")
    )


def test_pass_rules_keeps_only_the_item_and_pass_columns_of_the_bar_tables() -> None:
    rows = _bar()
    assert rows[0].startswith("| Type profile | The `type` field has no `!`.")
    assert any(r.startswith("| Index layout |") for r in rows)
    assert all(r.count(" | ") == 1 for r in rows)
    assert not any("scripts/" in r or "src/" in r or "https://" in r for r in rows)


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
