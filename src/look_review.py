"""Full-page look review of a rebuilt book against its scan, split into page groups for checking agents.

`prepare` pairs every rebuilt page with its scan pages, renders both to PNG, measures each page's
overflow with the checker, and writes `pages.jsonl` and `groups.json`. Agents write
`group_NN.jsonl` (findings) and `group_NN.audit.jsonl` (one line per page). `append_findings`
gives the findings real ids and appends them to the shared findings file in one locked write.
"""

import fcntl
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import pymupdf

from .checker import AuditSpec, DocumentQualityChecker
from .review import finding_problems, gram_pages, transcript_grams

PAGES_FILE = "look_pages.jsonl"
GROUPS_FILE = "look_groups.json"
MERGED_FILE = "merged.json"


@dataclass(frozen=True)
class PageEntry:
    """One rebuilt page: its scan pages, its PNGs relative to the review folder, and the checker's overflow."""

    page: int
    scan_pages: list[int]
    rebuilt_png: str
    scan_pngs: list[str]
    overflow_pt: float
    overflow_what: str


@dataclass(frozen=True)
class GroupResult:
    appended: int
    first_id: str | None
    last_id: str | None


def rebuilt_to_scan(scan_map: dict[int, list[int]]) -> dict[int, list[int]]:
    """Invert a parity page map (scan page to rebuilt pages) into rebuilt page to scan pages, in scan order."""
    out: dict[int, list[int]] = {}
    for scan in sorted(scan_map):
        for page in scan_map[scan]:
            out.setdefault(page, []).append(scan)
    return dict(sorted(out.items()))


def shared_text_map(
    scan: dict[int, set[str]],
    where: dict[str, set[int]],
    min_share: float = 0.2,
    min_telling: int = 3,
) -> dict[int, list[int]]:
    """Scan page to every rebuilt page that holds at least `min_share` of the scan page's telling 4-grams,
    so a scan page split over two rebuilt pages maps to both. `where` is each gram's rebuilt pages.
    A telling gram is found on one or two rebuilt pages: common words say nothing about the page, and
    transcript markup never reaches the PDF. A page with fewer than `min_telling` telling grams is lost."""
    out = {}
    for number, grams in sorted(scan.items()):
        telling = [g for g in grams if 1 <= len(where.get(g, ())) <= 2]
        if len(telling) < min_telling:
            continue
        hits = Counter(p for g in telling for p in where[g])
        if pages := sorted(p for p, n in hits.items() if n >= min_share * len(telling)):
            out[number] = pages
    return out


def text_page_map(transcripts: Path, rebuilt: Path) -> dict[int, list[int]]:
    """A scan-to-rebuilt page map by shared text with the transcripts, for an edition that declares none."""
    return shared_text_map(transcript_grams(transcripts), gram_pages(rebuilt))


def group_ranges(page_count: int, size: int) -> list[tuple[int, int]]:
    """Inclusive 1-based page ranges of at most `size` pages that cover pages 1 to `page_count`."""
    return [
        (start, min(start + size - 1, page_count))
        for start in range(1, page_count + 1, size)
    ]


def finding_id(book: str, number: int) -> str:
    return f"B{book}-{number:02d}"


def next_id_number(findings: Path, book: str) -> int:
    """One more than the highest `B<book>-NN` id in the findings file, or 1."""
    if not findings.exists():
        return 1
    pattern = re.compile(rf'"id": ?"B{re.escape(book)}-(\d+)"')
    return (
        max(
            (int(m[1]) for m in pattern.finditer(findings.read_text(encoding="utf-8"))),
            default=0,
        )
        + 1
    )


def _jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def unaudited_pages(review: Path, page_count: int) -> list[int]:
    """Pages 1 to `page_count` that no `group_*.audit.jsonl` line covers."""
    seen = {
        row["page"]
        for audit in review.glob("group_*.audit.jsonl")
        for row in _jsonl(audit)
    }
    return [p for p in range(1, page_count + 1) if p not in seen]


def group_problems(review: Path, group: int, first: int, last: int) -> list[str]:
    """What is missing or bad in the two files of one group; empty when the group is done."""
    findings, audit = (
        review / f"group_{group:02d}.jsonl",
        review / f"group_{group:02d}.audit.jsonl",
    )
    problems = [f"{p.name} is missing" for p in (findings, audit) if not p.exists()]
    if problems:
        return problems
    for path in (findings, audit):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                problems.append(f"{path.name} line {n}: not valid JSON ({error.msg})")
                continue
            if path == findings and (bad := finding_problems(row)):
                problems.append(f"{path.name} line {n}: " + "; ".join(bad))
    if not problems:
        seen = {row.get("page") for row in _jsonl(audit)}
        missing = [p for p in range(first, last + 1) if p not in seen]
        if missing:
            problems.append(
                f"{audit.name} has no line for pages {', '.join(map(str, missing))}"
            )
    return problems


def group_files(review: Path) -> list[Path]:
    return sorted(
        p for p in review.glob("group_*.jsonl") if not p.name.endswith(".audit.jsonl")
    )


def append_findings(review: Path, book: str, findings: Path) -> GroupResult:
    """Number the group findings of `review` and append them to `findings`; raise ValueError on bad lines or a second merge."""
    if (review / MERGED_FILE).exists():
        raise ValueError(f"{book} is already merged; see {review / MERGED_FILE}")
    rows, errors = [], []
    for path in group_files(review):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"{path.name} line {n}: not valid JSON ({error.msg})")
                continue
            if problems := finding_problems(row):
                errors.append(f"{path.name} line {n}: " + "; ".join(problems))
            rows.append(row)
    if errors:
        raise ValueError("\n".join(errors))
    with findings.open("a+", encoding="utf-8") as out:
        fcntl.flock(out, fcntl.LOCK_EX)
        start = next_id_number(findings, book)
        ids = [finding_id(book, start + i) for i in range(len(rows))]
        out.write(
            "".join(
                json.dumps(row | {"id": i}, ensure_ascii=False) + "\n"
                for row, i in zip(rows, ids)
            )
        )
    (review / MERGED_FILE).write_text(json.dumps({"ids": ids}), encoding="utf-8")
    return GroupResult(len(rows), ids[0] if ids else None, ids[-1] if ids else None)


def prepare(
    rebuilt: Path,
    scan: Path,
    scan_map: dict[int, list[int]],
    review: Path,
    size: int,
    dpi: int,
) -> list[PageEntry]:
    """Render page pairs to `review/png/`, measure overflow, and write `pages.jsonl` and `groups.json`. Existing PNGs are kept."""
    png = review / "png"
    png.mkdir(parents=True, exist_ok=True)
    doc, scan_doc = pymupdf.open(rebuilt), pymupdf.open(scan)
    checker = DocumentQualityChecker(rebuilt, AuditSpec(front_matter_pages=0))
    pairs = rebuilt_to_scan(scan_map)
    entries = []
    for page in range(1, len(doc) + 1):
        scans = pairs.get(page, [])
        rebuilt_png = png / f"r_{page:03d}.png"
        if not rebuilt_png.exists():
            doc[page - 1].get_pixmap(dpi=dpi).save(rebuilt_png)
        scan_pngs = []
        for s in scans:
            out = png / f"s_{s:03d}.png"
            if not out.exists():
                scan_doc[s - 1].get_pixmap(dpi=dpi).save(out)
            scan_pngs.append(str(out.relative_to(review)))
        by, what = checker.page_overflow(page - 1)
        entries.append(
            PageEntry(
                page,
                scans,
                str(rebuilt_png.relative_to(review)),
                scan_pngs,
                round(max(by, 0.0), 1),
                what[:80],
            )
        )
    (review / PAGES_FILE).write_text(
        "".join(json.dumps(asdict(e), ensure_ascii=False) + "\n" for e in entries),
        encoding="utf-8",
    )
    (review / GROUPS_FILE).write_text(
        json.dumps(group_ranges(len(doc), size)), encoding="utf-8"
    )
    return entries


def read_pages(review: Path) -> list[PageEntry]:
    return [PageEntry(**row) for row in _jsonl(review / PAGES_FILE)]


def read_groups(review: Path) -> list[tuple[int, int]]:
    return [
        tuple(g) for g in json.loads((review / GROUPS_FILE).read_text(encoding="utf-8"))
    ]
