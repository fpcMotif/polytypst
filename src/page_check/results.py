import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, TypedDict

KINDS = {"word", "number", "table_cell", "table_shape", "missing_text", "extra_text", "order", "mark", "math", "sum", "scan_typo"}
VERDICTS = ("real", "scan_typo", "false_positive", "sum")


class Issue(TypedDict):
    page: int | None
    kind: str
    transcript: str
    scan: NotRequired[str]
    line: NotRequired[int]
    rule: NotRequired[str]
    note: NotRequired[str]
    where: NotRequired[str]
    zoom: NotRequired[str]
    page_image: NotRequired[str]


class Verdict(Issue):
    verdict: str
    detail: str
    by: str


type IssueKey = tuple[int, str, str, str]


def issue_key(issue: Issue) -> IssueKey:
    return (int(issue["page"] or 0), issue["kind"], issue.get("transcript", ""), issue.get("scan", ""))


def read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def append_jsonl(path: Path, records: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as out:
        out.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


@dataclass
class Tally:
    pages: set[int]
    checked: set[int]
    issue_pages: set[int]
    kinds: Counter[str]
    bad_lines: list[str]
    unproven: set[int]


@dataclass(frozen=True)
class Results:
    folder: Path

    @property
    def lint_path(self) -> Path:
        return self.folder / "lint.jsonl"

    @property
    def verdicts_path(self) -> Path:
        return self.folder / "verdicts.jsonl"

    @property
    def queue_path(self) -> Path:
        return self.folder / "queue.jsonl"

    @property
    def verify_folder(self) -> Path:
        return self.folder / "verify"

    def chunk_files(self) -> list[Path]:
        return sorted(self.folder.glob("p*.jsonl"))

    def page_issues(self) -> list[Issue]:
        return [
            {"page": int(record["page"]), **issue}
            for path in self.chunk_files()
            for record in read_jsonl(path)
            for issue in record["issues"]
        ]

    def linted(self) -> bool:
        return self.lint_path.exists()

    def lint_hits(self) -> list[Issue]:
        return read_jsonl(self.lint_path)

    def write_lint(self, hits: list[Issue]) -> None:
        write_jsonl(self.lint_path, hits)

    def verdicts(self) -> list[Verdict]:
        return read_jsonl(self.verdicts_path)

    def verdict_keys(self) -> set[IssueKey]:
        return {issue_key(v) for v in self.verdicts() if v.get("verdict") in VERDICTS}

    def add_verdicts(self, verdicts: list[Verdict]) -> None:
        append_jsonl(self.verdicts_path, verdicts)

    def queue(self) -> list[Issue]:
        return read_jsonl(self.queue_path)

    def write_queue(self, queue: list[Issue]) -> None:
        write_jsonl(self.queue_path, queue)

    def false_negatives(self) -> list[dict]:
        return read_jsonl(self.folder / "false_negatives.jsonl")
