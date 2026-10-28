import json
from pathlib import Path

import pytest
from book_snapshot import snapshot

from polytypst.books import books

SNAPSHOTS = json.loads((Path(__file__).parent / "fixtures" / "book_snapshots.json").read_text(encoding="utf-8"))


def test_every_snapshot_has_a_book() -> None:
    assert sorted(books()) == sorted(SNAPSHOTS)


@pytest.mark.parametrize("key", sorted(SNAPSHOTS))
def test_book_matches_its_snapshot_from_before_the_move(key: str) -> None:
    assert json.loads(json.dumps(snapshot(books()[key]), ensure_ascii=False, sort_keys=True)) == SNAPSHOTS[key]
