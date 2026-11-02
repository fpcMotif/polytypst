from scripts.protected_paths import blocked, parse_numstat


def test_a_change_to_the_snapshot_fixture_needs_a_reason() -> None:
    changes = [(51399, 3, "tests/fixtures/book_snapshots.json")]
    assert blocked(changes, "fix(books): update snapshots") == ["tests/fixtures/book_snapshots.json"]


def test_a_protected_change_line_with_a_reason_lets_it_through() -> None:
    changes = [(4, 4, "quality/baseline.json"), (2, 1, "src/checker.py")]
    message = "fix(audit): lower counts\n\nProtected-change: the cross-reference fix removed 285 unlinked references\n"
    assert blocked(changes, message) == []


def test_an_empty_reason_does_not_count() -> None:
    assert blocked([(1, 0, "src/checker.py")], "x\n\nProtected-change:   \n") == ["src/checker.py"]


def test_new_test_lines_are_free_but_edited_or_deleted_test_lines_are_not() -> None:
    changes = [(30, 0, "tests/test_new.py"), (2, 5, "tests/test_old.py"), (0, 40, "tests/test_gone.py")]
    assert blocked(changes, "test: more cases") == ["tests/test_old.py", "tests/test_gone.py"]


def test_other_files_are_not_protected() -> None:
    assert blocked([(9, 9, "src/compiler/monograph.py"), (1, 1, "docs/page-check.md")], "fix") == []


def test_numstat_reads_binary_files_as_changed() -> None:
    text = "3\t1\tsrc/checker.py\n-\t-\ttests/fixtures/scan.png\n"
    assert parse_numstat(text) == [(3, 1, "src/checker.py"), (1, 1, "tests/fixtures/scan.png")]
