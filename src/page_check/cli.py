import argparse
import re
import sys
from collections import Counter
from collections.abc import Iterable
from difflib import unified_diff
from pathlib import Path

from ..book_state import BookStateError
from ..books import book_key, books
from . import RESULTS, PageCheck, cell_text, ranges, table_diff
from .check import MODEL as CHECK_MODEL
from .check import run
from .lint import lint
from .render import MODEL as RENDER_MODEL
from .render import RenderCheck
from .sheet import cases_from_jsonl, cases_from_verdicts, scan_sheet, sheets
from .verify import MODEL as VERIFY_MODEL
from .verify import gate, status, triage, verify

BOOK_HELP = "a book key, an alias, or a unique start of a key, such as 4 or fga"


def _print(lines: Iterable[str]) -> None:
    for line in lines:
        print(line, flush=True)


def _checks(names: list[str]) -> list[PageCheck]:
    if not names and RESULTS.is_dir():
        names = sorted(p.name for p in RESULTS.iterdir() if p.is_dir() and p.name != "logs")
    return [PageCheck.named(name) for name in names]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polytypst page-check",
        description="Check a book's transcripts page by page against its scan, then triage and verify the issues. "
        "docs/page-check.md, docs/page-check-review.md and docs/render-check.md are the runbooks.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("text", "the transcript of a page, with line numbers and its receipt"),
        ("clean", "the page as the page cleaner sets it, with line numbers; --diff shows what it changed"),
        ("suspects", "where the transcript and the local OCR disagree"),
        ("cells", "each transcript table on the page, as rows"),
        ("tablediff", "transcript table K against the scan's reading"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("book", help=BOOK_HELP)
        p.add_argument("page", type=int, help="scan page: the 1-based page of the scan PDF, as in p_NNN.md")
        if name == "clean":
            p.add_argument("--diff", action="store_true", help="a unified diff from the transcript to the cleaned page")
        if name == "tablediff":
            p.add_argument("table", type=int, help="table number on the page, from 1, as `cells` prints it")
            p.add_argument("scan_tsv", type=Path, help="the scan's table, one row per line, cells split by tabs")
    for name, help_text in (
        ("summary", "pages checked, issues by kind, gaps"),
        ("chunks", "the chunks of unchecked pages"),
        ("run", "start one agent for each chunk of unchecked pages"),
        ("status", "each stage's counts and the next command"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("books", nargs="*", help=f"{BOOK_HELP}; by default every book with page check results")
        if name in ("chunks", "run"):
            p.add_argument("--size", type=int, default=10, help="pages per chunk")
        if name == "run":
            p.add_argument("--jobs", type=int, default=8, help="agents at once")
            p.add_argument("--model", default=CHECK_MODEL)
    p = sub.add_parser("grep", help="transcript lines that match a regex, as KEY p_NNN:LINE: text")
    p.add_argument("pattern", help="a Python regex, matched against each transcript line")
    p.add_argument("books", nargs="*", help=f"{BOOK_HELP}; by default every book with transcripts")
    p = sub.add_parser("lint", help="known-error rules over the transcript and the built .typ")
    p.add_argument("book", help=BOOK_HELP)
    p = sub.add_parser("triage", help="settle width-only issues, cut a scan zoom for each other one")
    p.add_argument("book", help=BOOK_HELP)
    p.add_argument("--scan", type=Path, help="the scan PDF, by default the book's source scan")
    p = sub.add_parser("sheets", help="contact sheets of the queued zooms")
    p.add_argument("book", help=BOOK_HELP)
    p.add_argument("--size", type=int, default=30, help="strips per contact sheet")
    p = sub.add_parser("verify", help="start one agent for each batch of queued issues")
    p.add_argument("book", help=BOOK_HELP)
    p.add_argument("--size", type=int, default=30, help="issues per agent")
    p.add_argument("--jobs", type=int, default=4, help="agents at once")
    p.add_argument("--model", default=VERIFY_MODEL)
    p = sub.add_parser("render", help="pair each table and figure of a rebuilt PDF with its scan page")
    p.add_argument("book", help=BOOK_HELP)
    p.add_argument("--pdf", required=True, type=Path, help="the rebuilt PDF")
    p.add_argument("--scan", type=Path, help="the scan PDF, by default the book's source scan")
    p.add_argument("--labels", default="", help="comma-separated labels to render, such as 表1-1,图2-3")
    p.add_argument("--out", type=Path, help="the folder for the PNG files, by default $POLYTYPST_OUTPUT/render_check/KEY")
    p.add_argument("--run", action="store_true", help="render every pair and start the agents")
    p.add_argument("--size", type=int, default=6, help="labels per agent")
    p.add_argument("--jobs", type=int, default=8, help="agents at once")
    p.add_argument("--model", default=RENDER_MODEL)
    p = sub.add_parser("sheet", help="an HTML sheet of scan strips, written to stdout")
    p.add_argument("book", help=BOOK_HELP)
    p.add_argument("--scan", type=Path, help="the scan PDF, by default the book's source scan")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--cases", type=Path, help="a JSONL file with one card per line")
    source.add_argument("--verdicts", choices=["scan_typo", "real"], help="read the cards from the book's verdicts.jsonl")
    p.add_argument("--title", default="", help="the page title")
    p.add_argument("--intro", default="Each strip is cut straight from the scan PDF.", help="the line under the title")
    p.add_argument("--dpi", type=int, default=300)
    p = sub.add_parser("gate", help="PASS only when the receipts, lint, verdicts, figures and audit all pass")
    p.add_argument("book", help=BOOK_HELP)
    p.add_argument("--pdf", type=Path, help="the rebuilt PDF, by default the first edition's")
    p.add_argument("--manifest", type=Path, help="the figure manifest, by default figures_manifest.json in the book's output folder")
    return parser


def _page(args: argparse.Namespace) -> int:
    check = PageCheck.named(args.book)
    if not check.has(args.page):
        print(f"page {args.page} has no transcript; skip it")
        return 0
    if args.command == "text":
        lines = check.transcript(args.page).splitlines()
        print("\n".join(f"{n:4d}  {line}" for n, line in enumerate(lines, 1)))
        proof = check.receipt(args.page)
        print(f"receipt: {proof}" if proof else f"receipt: none; render {check.page_png(args.page)} first")
    elif args.command == "clean":
        cleaned = check.cleaned(args.page).splitlines()
        if args.diff:
            raw = check.transcript(args.page).splitlines()
            name = check.store.path(args.page).name
            print("\n".join(unified_diff(raw, cleaned, name, f"{name} cleaned", lineterm="")) or "the cleaner changed nothing")
        else:
            print("\n".join(f"{n:4d}  {line}" for n, line in enumerate(cleaned, 1)))
    elif args.command == "suspects":
        print("\n".join(check.suspects(args.page)) or "none")
    elif args.command == "cells":
        tables = check.tables(args.page)
        for k, rows in enumerate(tables, 1):
            print(f"table {k}: {len(rows)} rows")
            print("\n".join("\t".join(r) for r in rows))
        print(f"{len(tables)} tables" if tables else "no tables")
    else:
        lines = args.scan_tsv.read_text(encoding="utf-8").splitlines()
        scan = [[cell_text(c) for c in line.split("\t")] for line in lines if line.strip()]
        print("\n".join(table_diff(check.tables(args.page)[args.table - 1], scan)))
    return 0


def _grep(args: argparse.Namespace) -> int:
    try:
        re.compile(args.pattern)
    except re.error as error:
        print(f"{args.pattern!r} is not a Python regex: {error}")
        return 1
    hits, searched, missing = 0, 0, None
    for key in [book_key(name) for name in args.books] or list(books()):
        try:
            found = PageCheck.named(key).grep(args.pattern)
        except BookStateError as error:
            if args.books:
                raise
            missing = error
            continue
        searched += 1
        _print(f"{key} p_{page:03d}:{n}: {line}" for page, n, line in found)
        hits += len(found)
    if not searched and missing:
        raise missing
    print(f"{hits} lines in {searched} books")
    return 0


def _summary(check: PageCheck) -> list[str]:
    t = check.tally()
    lines = [
        (
            f"book {check.key}: {len(t.checked & t.pages)}/{len(t.pages)} pages checked, "
            f"{len(t.issue_pages)} with issues, {sum(t.kinds.values())} issues {dict(t.kinds.most_common())}"
        )
    ]
    if missing := sorted(t.pages - t.checked):
        lines.append(f"  unchecked: {ranges(missing)}")
    if unproven := sorted(t.unproven - t.checked):
        lines.append(f"  no valid receipt: {ranges(unproven)}")
    return lines + [f"  bad line {bad}" for bad in t.bad_lines]


def _render(args: argparse.Namespace) -> int:
    rc = RenderCheck(PageCheck.named(args.book, args.scan), args.pdf, args.out)
    if args.run:
        _print(rc.run(args.size, args.jobs, args.model))
        return 0
    wanted = [label for label in args.labels.split(",") if label]
    if not wanted:
        for label, page in rc.rebuilt.items():
            print(f"{label}\trebuilt {page}\tscan {rc.scan.get(label, '-')}")
        print(f"{len(rc.rebuilt)} captions, {len(rc.paired())} found in the scan", file=sys.stderr)
        return 0
    for label in wanted:
        if label not in rc.rebuilt or label not in rc.scan:
            print(f"{label}: not in the {'rebuilt PDF' if label not in rc.rebuilt else 'scan OCR'}", file=sys.stderr)
            continue
        rebuilt, scan = rc.render(label)
        print(f"{label}\t{rebuilt}\t{scan}")
    return 0


def _sheet(args: argparse.Namespace) -> int:
    check = PageCheck.named(args.book, args.scan)
    if args.cases:
        cases = cases_from_jsonl(args.cases.read_text(encoding="utf-8"))
    else:
        cases = cases_from_verdicts(check.results.verdicts(), args.verdicts)
    title = args.title or f"{check.key}: {args.verdicts or 'scan'} strips"
    page, missed = scan_sheet(check, cases, title, args.intro, args.dpi)
    for case in missed:
        print(f"p{case.page}: no OCR line holds {case.find!r}; give the case a band", file=sys.stderr)
    sys.stdout.write(page)
    print(f"{len(cases) - len(missed)} of {len(cases)} cards", file=sys.stderr)
    return 0


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    try:
        return _command(args)
    except BookStateError as error:
        print(error)
        return 1


def _command(args: argparse.Namespace) -> int:
    if args.command in ("text", "clean", "suspects", "cells", "tablediff"):
        return _page(args)
    if args.command == "grep":
        return _grep(args)
    if args.command in ("summary", "chunks", "run", "status"):
        checks = _checks(args.books)
        if args.command == "run":
            _print(run(checks, args.size, args.jobs, args.model))
            return 0
        for check in checks:
            if args.command == "chunks":
                _print(f"{check.key} {first} {last}" for first, last in check.chunks(args.size))
            else:
                _print(_summary(check) if args.command == "summary" else status(check))
        return 0
    if args.command == "render":
        return _render(args)
    if args.command == "sheet":
        return _sheet(args)
    check = PageCheck.named(args.book, getattr(args, "scan", None))
    if args.command == "gate":
        lines = gate(check, args.pdf, args.manifest)
        _print(lines)
        return 0 if lines[-1] == "PASS" else 1
    if args.command == "lint":
        found = lint(check)
        check.results.write_lint(found)
        for rule, n in Counter(h.get("rule") for h in found).most_common():
            examples = "; ".join(f"p{h['page']} {h['transcript']}" for h in found if h.get("rule") == rule)
            print(f"{rule}: {n}  {examples[:160]}")
        print(f"{len(found)} hits -> {check.results.lint_path}")
    elif args.command == "triage":
        settled, queued = triage(check)
        print(f"{settled} settled as false_positive (width, spacing or running head), {queued} queued with zooms -> {check.results.queue_path}")
    elif args.command == "sheets":
        written = sheets(check, args.size)
        print(f"{len(written)} contact sheet(s) -> {check.results.verify_folder / 'sheets'}")
    else:
        _print(verify(check, args.size, args.jobs, args.model))
    return 0
