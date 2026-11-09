"""The record of every fix to a book: what the scan was checked to read, what changed, and the shared cause behind it.

Three kinds of entry, each kept as JSONL under `quality/`:

- a `Verdict` (`verdicts.jsonl`) is a double-checked finding: what the scan prints, what the transcript has, and
  whose fault the difference is (`ocr`, `scan_typo`, `code`, `workflow`);
- a `Cause` (`causes.jsonl`) is a root cause shared across books, such as RC-06, with its status;
- a `Correction` (`corrections/<book>.jsonl`) is one fix on one page, every changed line in full, linked to the
  verdict it answers and the cause it belongs to.

`record` writes any of them and refuses an entry whose links point nowhere. `history` reads a book back with its
links joined, and lists the verdicts that no correction answers yet.
"""

import argparse
import dataclasses
import datetime
import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import REPO

QUALITY = REPO / "quality"
KINDS = ("ocr", "scan_typo", "code", "workflow")


@dataclass(frozen=True)
class Line:
    """One transcript line before and after a fix; `line` is its 0-based place on the cleaned page when known."""

    before: str
    after: str
    line: int | None = None

    def words(self) -> list[dict[str, str]]:
        """The runs of words that differ, as {"before", "after"} pairs."""
        a, b = self.before.split(" "), self.after.split(" ")
        ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
        return [
            {"before": " ".join(a[i1:i2]), "after": " ".join(b[j1:j2])}
            for op, i1, i2, j1, j2 in ops
            if op != "equal"
        ]


@dataclass(frozen=True)
class Verdict:
    id: str
    book: str
    verdict: str
    scan_page: int | None
    scan_reads: str
    transcript_reads: str
    fix: str = ""
    detail: str = ""
    checked_by: str = ""
    confirmed_by: str | None = None


@dataclass(frozen=True)
class Cause:
    id: str
    root_cause: str
    layer: str
    status: str
    notes: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Correction:
    book: str
    page: int | None
    kind: str
    lines: tuple[Line, ...]
    scan_reads: str
    evidence: str
    fixed_in: str
    finding: str = ""
    cause: str = ""
    commit: str = ""
    date: str = field(default_factory=lambda: datetime.date.today().isoformat())


@dataclass(frozen=True)
class Linked:
    correction: Correction
    verdict: Verdict | None
    cause: Cause | None


@dataclass(frozen=True)
class BookHistory:
    corrections: tuple[Linked, ...]
    open_verdicts: tuple[Verdict, ...]


def record(entry: Verdict | Cause | Correction, root: Path = QUALITY) -> None:
    """Append `entry`; a verdict or cause with the id of an earlier one replaces it.

    Raises ValueError for a kind outside KINDS, a correction with no lines, or a link to an unknown verdict or cause."""
    if isinstance(entry, Correction):
        if entry.kind not in KINDS:
            raise ValueError(f"kind {entry.kind!r} is not one of {KINDS}")
        if not entry.lines:
            raise ValueError("a correction needs at least one changed line")
        if entry.cause and entry.cause not in _by_id(root / "causes.jsonl", Cause):
            raise ValueError(f"no cause {entry.cause} in {root / 'causes.jsonl'}")
        if entry.finding and entry.finding not in _by_id(
            root / "verdicts.jsonl", Verdict
        ):
            raise ValueError(f"no verdict {entry.finding} in {root / 'verdicts.jsonl'}")
        _append(root / "corrections" / f"{entry.book}.jsonl", _row(entry))
        return
    if isinstance(entry, Verdict) and entry.verdict not in KINDS:
        raise ValueError(f"verdict {entry.verdict!r} is not one of {KINDS}")
    if isinstance(entry, Verdict):
        path = root / "verdicts.jsonl"
        rows = [_row(e) for e in {**_by_id(path, Verdict), entry.id: entry}.values()]
    else:
        path = root / "causes.jsonl"
        rows = [_row(e) for e in {**_by_id(path, Cause), entry.id: entry}.values()]
    _write(path, rows)


def history(book: str, root: Path = QUALITY) -> BookHistory:
    """Every correction of `book` with its verdict and cause, and the book's verdicts that no correction answers."""
    verdicts, causes = (
        _by_id(root / "verdicts.jsonl", Verdict),
        _by_id(root / "causes.jsonl", Cause),
    )
    corrections = [
        _correction(row) for row in _rows(root / "corrections" / f"{book}.jsonl")
    ]
    answered = {c.finding for c in corrections}
    return BookHistory(
        corrections=tuple(
            Linked(c, verdicts.get(c.finding), causes.get(c.cause)) for c in corrections
        ),
        open_verdicts=tuple(
            v for v in verdicts.values() if v.book == book and v.id not in answered
        ),
    )


def changed_lines(before: str, after: str) -> list[Line]:
    """The lines a fix changed on one cleaned page, each whole. Raises ValueError when the line count changed."""
    a, b = before.split("\n"), after.split("\n")
    if len(a) != len(b):
        raise ValueError(f"the page went from {len(a)} lines to {len(b)}")
    return [
        Line(before=x, after=y, line=n)
        for n, (x, y) in enumerate(zip(a, b, strict=True))
        if x != y
    ]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="polytypst corrections",
        description="Show a book's corrections and open verdicts.",
    )
    parser.add_argument("command", choices=["show"])
    parser.add_argument("book")
    args = parser.parse_args(argv)
    got = history(args.book)
    for linked in got.corrections:
        c = linked.correction
        cause = f" {c.cause} ({linked.cause.status})" if linked.cause else ""
        verdict = (
            f" {c.finding}: scan reads {linked.verdict.scan_reads!r}"
            if linked.verdict
            else ""
        )
        print(f"p{c.page} {c.kind}{cause}{verdict} [{c.commit or 'uncommitted'}]")
        for line in c.lines:
            for w in line.words():
                print(f"    {w['before']!r} -> {w['after']!r}")
    for v in got.open_verdicts:
        print(
            f"open {v.id} p{v.scan_page} {v.verdict}: scan reads {v.scan_reads!r}, transcript {v.transcript_reads!r}"
        )
    print(f"{len(got.corrections)} corrections, {len(got.open_verdicts)} open verdicts")
    return 0


def _row(entry: Verdict | Cause | Correction) -> dict[str, object]:
    row = dataclasses.asdict(entry)
    if isinstance(entry, Correction):
        row["lines"] = [
            {**dataclasses.asdict(line), "words": line.words()} for line in entry.lines
        ]
    return row


def _correction(row: dict[str, Any]) -> Correction:
    lines = tuple(
        Line(before=x["before"], after=x["after"], line=x.get("line"))
        for x in row["lines"]
    )
    fields = {k: v for k, v in row.items() if k != "lines"}
    return Correction(**fields, lines=lines)


def _by_id[T: (Verdict, Cause)](path: Path, kind: type[T]) -> dict[str, T]:
    return {row["id"]: kind(**row) for row in _rows(path)}


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _append(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )
