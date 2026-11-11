"""Full-page look review of a rebuilt book against its scan, split into page groups for checking agents.

`prepare` pairs every rebuilt page with its scan pages, renders both to PNG, measures each page's
overflow with the checker, and writes `pages.jsonl` and `groups.json`. Agents write
`group_NN.jsonl` (findings) and `group_NN.audit.jsonl` (one line per page). `append_findings`
gives the findings real ids and appends them to the shared findings file in one locked write.
"""

import fcntl
import json
import re
import shlex
import shutil
from collections import Counter
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

import pymupdf

from .checker import LAYOUT_TIER, TEXT_TIER, AuditSpec, DocumentQualityChecker
from .compare_sheet import Panel, write_sheet
from .review import SEVERITIES, Finding, finding_problems, gram_pages, transcript_grams

PAGES_FILE = "look_pages.jsonl"
GROUPS_FILE = "look_groups.json"
MERGED_FILE = "merged.json"
CAUSES = ("transcript", "build", "unknown")
GRAVE = ("P0", "P1")
BOXES = {
    "full": (0.0, 0.0, 1.0, 1.0),
    "top": (0.0, 0.0, 1.0, 0.4),
    "middle": (0.0, 0.3, 1.0, 0.7),
    "bottom": (0.0, 0.6, 1.0, 1.0),
}
FINDING_FIELDS = {
    "id": '`"TBD"`; merge gives the real id',
    "book": "the book key, `{book}`",
    "severity": f"one of {', '.join(SEVERITIES)}: P0 content wrong or lost, P1 visibly broken layout, P2 typographic bad practice, P3 nit",
    "format": "`typst`, `latex`, `both`, `vintage` or `transcript`: where the defect shows",
    "where": "the rebuilt page as `pN`, then the scan page, then `p_NNN.md:line` when you opened the transcript",
    "what": "one sentence that says what is wrong",
    "evidence": "a measure, a quote of at most 15 words, or a crop sheet path",
    "status": '`"open"`',
}


@dataclass(frozen=True)
class PageEntry:
    """One rebuilt page: its scan pages, its PNGs relative to the review folder, the checker's overflow,
    and the names of the checker's other text and layout rules that hit the page."""

    page: int
    scan_pages: list[int]
    rebuilt_png: str
    scan_pngs: list[str]
    overflow_pt: float
    overflow_what: str
    checker: list[str] = field(default_factory=list)
    pair_png: str = ""


@dataclass(frozen=True)
class SpotItem:
    """One item of a spot check: a grave finding or a page the audit passed, with its sheet."""

    item: str
    page: int | None
    scan_pages: list[int]
    text: str
    pngs: list[str]


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


def sample_ranges(page_count: int, size: int) -> list[tuple[int, int]]:
    """The first, middle and last group of `group_ranges`: front matter, body, and back matter with the index."""
    ranges = group_ranges(page_count, size)
    return (
        ranges
        if len(ranges) <= 3
        else [ranges[0], ranges[len(ranges) // 2], ranges[-1]]
    )


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


def unaudited_pages(review: Path) -> list[int]:
    """Pages of the review's groups that no `group_*.audit.jsonl` line covers."""
    seen = {
        row["page"]
        for audit in review.glob("group_*.audit.jsonl")
        for row in _jsonl(audit)
    }
    return [
        p
        for first, last in read_groups(review)
        for p in range(first, last + 1)
        if p not in seen
    ]


def _lists_causes(review: Path) -> bool:
    """Whether the review's findings must take `cause` from CAUSES. A review prepared before that list keeps free text."""
    path = review / GROUPS_FILE
    return path.exists() and isinstance(
        json.loads(path.read_text(encoding="utf-8")), dict
    )


def group_problems(review: Path, group: int, first: int, last: int) -> list[str]:
    """What is missing or bad in the two files of one group; empty when the group is done."""
    findings, audit = (
        review / f"group_{group:02d}.jsonl",
        review / f"group_{group:02d}.audit.jsonl",
    )
    problems = [f"{p.name} is missing" for p in (findings, audit) if not p.exists()]
    if problems:
        return problems
    listed = _lists_causes(review)
    for path in (findings, audit):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                problems.append(f"{path.name} line {n}: not valid JSON ({error.msg})")
                continue
            if path != findings:
                continue
            bad = finding_problems(row)
            if listed and row.get("cause") not in CAUSES:
                bad.append(
                    f"cause {row.get('cause')!r} is not one of {', '.join(CAUSES)}"
                )
            if bad:
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


def _render(
    doc: pymupdf.Document, page: int, out: Path, dpi: int, source: Path
) -> None:
    """Write 1-based `page` of `doc` to `out`, unless `out` is already newer than the PDF at `source`."""
    if not out.exists() or out.stat().st_mtime < source.stat().st_mtime:
        doc[page - 1].get_pixmap(dpi=dpi).save(out)


def pair_name(page: int) -> str:
    """The pair sheet of rebuilt `page`, relative to the review folder."""
    return f"png/pair_{page:03d}.png"


def _write_pair(out: Path, rebuilt: Path, scan: Path, page: int, scans: list[int], dpi: int) -> None:
    """Write the pair sheet of `page`, its `scans` beside it, unless `out` is newer than both PDFs."""
    if not out.exists() or out.stat().st_mtime < max(rebuilt.stat().st_mtime, scan.stat().st_mtime):
        write_sheet(
            [[Panel(f"scan p{s}", scan, s) for s in scans] + [Panel(f"rebuilt p{page}", rebuilt, page)]],
            out,
            dpi,
        )


def pair_sheets(
    review: Path, rebuilt: Path, scan: Path, pages: list[PageEntry], first: int, last: int, dpi: int
) -> None:
    """Write the missing or stale pair sheets of pages `first` to `last`, as a review that an older `prepare` made lacks them."""
    for e in pages:
        if first <= e.page <= last:
            _write_pair(review / (e.pair_png or pair_name(e.page)), rebuilt, scan, e.page, e.scan_pages, dpi)


def prepare(
    rebuilt: Path,
    scan: Path,
    scan_map: dict[int, list[int]],
    review: Path,
    ranges: list[tuple[int, int]],
    dpi: int,
    audit: AuditSpec | None = None,
) -> list[PageEntry]:
    """Render the page pairs of `ranges` to `review/png/`, run the checker with `audit`, and write the pages and groups files.

    A PNG older than its PDF is rendered again, so a review after a rebuild shows the new pages."""
    png = review / "png"
    png.mkdir(parents=True, exist_ok=True)
    doc, scan_doc = pymupdf.open(rebuilt), pymupdf.open(scan)
    checker = DocumentQualityChecker(rebuilt, audit or AuditSpec(front_matter_pages=0))
    hits: dict[int, set[str]] = {}
    for issue in checker.run_all_checks(frozenset({TEXT_TIER, LAYOUT_TIER})).issues:
        if issue.rule_name != "MARGIN_OVERFLOW":
            hits.setdefault(issue.page_num, set()).add(issue.rule_name)
    pairs = rebuilt_to_scan(scan_map)
    entries = []
    for page in (p for first, last in ranges for p in range(first, last + 1)):
        scans = pairs.get(page, [])
        rebuilt_png = png / f"r_{page:03d}.png"
        _render(doc, page, rebuilt_png, dpi, rebuilt)
        scan_pngs = []
        for s in scans:
            out = png / f"s_{s:03d}.png"
            _render(scan_doc, s, out, dpi, scan)
            scan_pngs.append(str(out.relative_to(review)))
        pair_png = review / pair_name(page)
        _write_pair(pair_png, rebuilt, scan, page, scans, dpi)
        by, what = checker.page_overflow(page - 1)
        entries.append(
            PageEntry(
                page,
                scans,
                str(rebuilt_png.relative_to(review)),
                scan_pngs,
                round(max(by, 0.0), 1),
                what[:80],
                sorted(hits.get(page, ())),
                str(pair_png.relative_to(review)),
            )
        )
    (review / PAGES_FILE).write_text(
        "".join(json.dumps(asdict(e), ensure_ascii=False) + "\n" for e in entries),
        encoding="utf-8",
    )
    write_groups(review, ranges)
    return entries


def spot_check(
    review: Path, rebuilt: Path, scan: Path, dpi: float | None = None
) -> list[SpotItem]:
    """Up to 3 grave findings, one per group file, and 2 pages the audit passed, each as one sheet under `review/crops/`:
    its scan pages beside its rebuilt page, at `dpi` or as large as the sheet allows.

    A finding's page is the first `pN` of its `where`. A finding with no such page of the review gets no sheet."""
    scans = {e.page: e.scan_pages for e in read_pages(review)}

    def pngs(page: int | None, scan_pages: list[int]) -> list[str]:
        if page is None:
            return []
        out = write_sheet(
            [
                [Panel(f"scan p{s}", scan, s) for s in scan_pages]
                + [Panel(f"rebuilt p{page}", rebuilt, page)]
            ],
            review / "crops" / f"spot_p{page:03d}.png",
            dpi,
        )
        return [str(out.relative_to(review))]

    items = []
    for path in group_files(review):
        grave = [
            (n, row)
            for n, row in enumerate(_jsonl(path), 1)
            if row.get("severity") in GRAVE
        ]
        if not grave or len(items) == 3:
            continue
        n, row = grave[0]
        found = re.search(r"\bp(\d+)", row["where"])
        page = int(found[1]) if found and int(found[1]) in scans else None
        text = f"{row['where']}: {row['what']}"
        items.append(
            SpotItem(
                f"{path.name} line {n}",
                page,
                scans.get(page, []),
                text,
                pngs(page, scans.get(page, [])),
            )
        )
    passed = [
        row
        for audit in sorted(review.glob("group_*.audit.jsonl"))
        for row in _jsonl(audit)
        if row.get("result") == "PASS" and row.get("page") in scans
    ]
    items += [
        SpotItem(
            "PASS",
            row["page"],
            scans[row["page"]],
            "",
            pngs(row["page"], scans[row["page"]]),
        )
        for row in passed[:2]
    ]
    return items


def parse_box(text: str) -> tuple[float, float, float, float]:
    """A crop box: a name of BOXES, or L,T,R,B as shares of the page between 0 and 1."""
    if text in BOXES:
        return BOXES[text]
    try:
        left, top, right, bottom = (float(v) for v in text.split(","))
    except ValueError:
        raise ValueError(
            f"box {text!r} is not one of {', '.join(BOXES)} or four numbers L,T,R,B"
        ) from None
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError(
            f"box {text!r}: L,T,R,B are shares of the page between 0 and 1, such as 0,0.4,1,0.8, not points or pixels"
        )
    return left, top, right, bottom


def crop(review: Path, rebuilt: Path, scan: Path, regions: list[str], by_scan: bool = False) -> Path:
    """One sheet under `review/crops/` with a row per region `PAGE:BOX[:SCANBOX]`: the scan pages' box, then the rebuilt page's.

    PAGE is a rebuilt page, or with `by_scan` a scan page, which brings every rebuilt page paired with it.
    Each row zooms as far as its box allows within the sheet width, so a narrow box reads small marks."""
    scans = {e.page: e.scan_pages for e in read_pages(review)}
    rows = []
    for region in regions:
        page, _, boxes = region.partition(":")
        if not page.isdigit() or not boxes:
            raise ValueError(f"region {region!r} is not PAGE:BOX or PAGE:BOX:SCANBOX, such as 41:middle or 41:0,0.2,0.5,0.4:bottom")
        box, _, scan_box = boxes.partition(":")
        if by_scan:
            pages = [r for r, s in scans.items() if int(page) in s]
            if not pages:
                paired = sorted({s for pair in scans.values() for s in pair})
                raise ValueError(
                    f"scan page {page} pairs with no rebuilt page of this review; its scan pages are {paired[0]} to {paired[-1]}"
                    if paired
                    else "this review pairs no scan pages"
                )
            row_scans = [int(page)]
        else:
            if int(page) not in scans:
                raise ValueError(f"rebuilt page {page} is not in this review; its pages are {min(scans)} to {max(scans)}")
            pages, row_scans = [int(page)], scans[int(page)]
        rows.append(
            [Panel(f"scan p{s} {scan_box or box}", scan, s, parse_box(scan_box or box)) for s in row_scans]
            + [Panel(f"rebuilt p{p} {box}", rebuilt, p, parse_box(box)) for p in pages]
        )
    prefix = "scan_" if by_scan else ""
    name = "_".join(re.sub(r"[^\w.-]+", "-", r) for r in regions)[:120]
    return write_sheet(rows, review / "crops" / f"sheet_{prefix}{name}.png")


@dataclass(frozen=True)
class TextHit:
    """A page that holds the searched text: a `rebuilt` page with its paired `scan_pages`, or a scan page's transcript."""

    rebuilt: int | None
    scan_pages: list[int]


def find_text(review: Path, rebuilt: Path, text: str) -> list[TextHit]:
    """Every rebuilt page of the review whose text holds `text`, then every scan page whose transcript holds it.

    Whitespace runs match any whitespace run. The scan side reads `review/transcript/`, as a scan has no text layer."""
    scans = {e.page: e.scan_pages for e in read_pages(review)}

    def holds(page_text: str) -> bool:
        return " ".join(text.split()) in " ".join(page_text.split())

    with pymupdf.open(rebuilt) as doc:
        hits = [TextHit(p, scans[p]) for p in sorted(scans) if p <= doc.page_count and holds(doc[p - 1].get_text())]
    for path in sorted((review / "transcript").glob("p_*.md")):
        if holds(path.read_text(encoding="utf-8")):
            hits.append(TextHit(None, [int(path.stem[2:])]))
    return hits


def stock(review: Path, repo: Path, book: str, transcripts: Path | None, sample: bool) -> None:
    """Make `review` all a checking agent needs: its own `lr` command, and the transcript pages of its scan pages.

    `review/lr VERB ARGS` runs scripts/look_review.py VERB for `book` (and `--sample`) from any folder, with
    the repo's mise environment, so the agent needs no path, tool or file inside `repo`. A book without
    `transcripts` gets an empty `review/transcript/`."""
    copies = review / "transcript"
    copies.mkdir(parents=True, exist_ok=True)
    for scan_page in sorted({s for e in read_pages(review) for s in e.scan_pages}):
        source = transcripts / f"p_{scan_page:03d}.md" if transcripts else None
        if source and source.exists():
            shutil.copy2(source, copies / source.name)
    q = shlex.quote
    lr = review / "lr"
    lr.write_text(
        "#!/bin/sh\n"
        'verb="$1"; shift\n'
        f"exec {_runner(repo)} "
        f'{q(str(repo / "scripts" / "look_review.py"))} "$verb" {q(book)} "$@"'
        + (" --sample" if sample else "")
        + "\n",
        encoding="utf-8",
    )
    lr.chmod(0o755)


def _runner(repo: Path) -> str:
    """The shell words that run a Python file of `repo` with its uv project and mise environment, from any folder."""
    q = shlex.quote(str(repo))
    return f"mise exec -C {q} -- uv run -q --project {q} python"


def open_workspace(root: Path, repo: Path, skill: Path) -> None:
    """Make `root` (the folder of all look reviews) a workspace for the orchestrator, outside `repo`.

    `root/lr VERB BOOK ...` runs scripts/look_review.py, and `root/lr build BOOK` runs one_book.py's PDF build.
    The skill folder is copied to `root/.agent/skills/`, so an agent opened on `root` loads it.
    `close_workspace` removes both again."""
    run, scripts = _runner(repo), repo / "scripts"
    q = shlex.quote
    lr = root / "lr"
    root.mkdir(parents=True, exist_ok=True)
    lr.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = build ]; then\n'
        '  shift; book="$1"; shift\n'
        f'  exec {run} {q(str(scripts / "one_book.py"))} "$book" build --formats pdf "$@"\n'
        "fi\n"
        f'exec {run} {q(str(scripts / "look_review.py"))} "$@"\n',
        encoding="utf-8",
    )
    lr.chmod(0o755)
    copy = root / ".agent" / "skills" / skill.name
    shutil.rmtree(copy, ignore_errors=True)
    shutil.copytree(skill, copy)


def close_workspace(root: Path) -> None:
    """Remove what `open_workspace` added to `root`: its `lr` and the skill copies. The reviews stay."""
    (root / "lr").unlink(missing_ok=True)
    shutil.rmtree(root / ".agent", ignore_errors=True)


def command(review: Path | str, verb: str, *args: object) -> str:
    """The exact shell line of one look_review.py verb, as a checking agent runs it through `review/lr`."""
    return " ".join([f"{review}/lr", verb, *map(str, args)])


def finding_schema(book: str) -> list[str]:
    """The brief's lines on each field of a finding, one per field of `Finding`; a new field without help raises KeyError."""
    lines = [
        f"  - `{f.name}`: {FINDING_FIELDS[f.name].format(book=book)}"
        for f in fields(Finding)
    ]
    lines.append(
        f"  - `cause`: one of {', '.join(CAUSES)}: `transcript` when `p_NNN.md` holds the wrong or missing text, "
        "`build` when the transcript is right, `unknown` when you did not open it. `build` is the whole answer: "
        "a later step finds where the build goes wrong."
    )
    example = {
        "id": "TBD",
        "book": book,
        "severity": "P0",
        "format": "typst",
        "where": "p41, scan p45, p_045.md:12",
        "what": "The display after (3.2) is lost.",
        "evidence": "crops/sheet_41-middle.png",
        "status": "open",
        "cause": "build",
    }
    return lines + ["  - Example line:", "", f"    {json.dumps(example, ensure_ascii=False)}"]


def pass_rules(markdown: str) -> list[str]:
    """The rows of the first `| Item | PASS when |` table in `markdown`, cut to those two columns.

    The bar docs also hold reference values, sources, and commands for the fixer, which a checking agent does not need."""
    rows: list[str] = []
    for line in (raw.strip() for raw in markdown.splitlines()):
        if not rows and line.startswith("| Item | PASS when"):
            rows.append(line)
        elif rows and line.startswith("|"):
            if not line.startswith("|---"):
                cells = re.split(r"(?<!\\)\|", line)
                rows.append(f"| {cells[1].strip()} | {cells[2].strip()} |")
        elif rows:
            break
    return rows[1:]


def brief(
    template: str,
    review: Path | str,
    book: str,
    group: int,
    first: int,
    last: int,
    pages: list[PageEntry],
    facts: list[str],
    bar: list[str],
) -> str:
    """The checking agent's whole prompt for one group: `template` filled in with `bar` (rows of `pass_rules`), then "Facts for this review"."""
    page_lines = "\n".join(
        f"- p{e.page}: `{e.pair_png or pair_name(e.page)}`, scan pages {e.scan_pages or 'none'}; "
        f"overflow_pt {e.overflow_pt}"
        + (f" ({e.overflow_what})" if e.overflow_pt > 3 else "")
        + (f"; checker: {', '.join(e.checker)}" if e.checker else "")
        for e in pages
        if first <= e.page <= last
    )
    body = template.split("\n\n", 2)[2].format(
        book=book,
        group=group,
        first=first,
        last=last,
        review=review,
        pages=page_lines,
        bar="\n".join(["| Item | PASS when |", "|---|---|", *bar]),
        crop=command(review, "crop", "PAGE:BOX", "[PAGE:BOX ...]"),
    )
    tail = [
        "## Facts for this review",
        "",
        *facts,
        "- Each line of the findings file has these fields:",
        *finding_schema(book),
        "",
        f"- The check command of this review is `{command(review, 'check', group)}`.",
    ]
    return body + "\n" + "\n".join(tail)


def missing_inputs(review: Path, pages: list[PageEntry], first: int, last: int) -> list[str]:
    """The files under `review` that the brief of pages `first` to `last` names but `review` lacks, relative to it.

    A page entry without a pair sheet comes from an older `prepare`, so its missing sheet is the one prepare writes now."""
    named = ["lr", "transcript/"] + [e.pair_png or pair_name(e.page) for e in pages if first <= e.page <= last]
    return [name for name in named if not (review / name).exists()]


def read_pages(review: Path) -> list[PageEntry]:
    return [PageEntry(**row) for row in _jsonl(review / PAGES_FILE)]


def write_groups(review: Path, ranges: list[tuple[int, int]]) -> None:
    (review / GROUPS_FILE).write_text(json.dumps({"groups": ranges}), encoding="utf-8")


def read_groups(review: Path) -> list[tuple[int, int]]:
    """The page ranges of the review's groups, also from a file written before groups carried the cause list."""
    stored = json.loads((review / GROUPS_FILE).read_text(encoding="utf-8"))
    return [
        tuple(g) for g in (stored["groups"] if isinstance(stored, dict) else stored)
    ]
