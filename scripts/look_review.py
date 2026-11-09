"""Run a full-page look review of one book: prepare page pairs, brief checking agents per group, check and merge their files.

Usage:
  uv run python scripts/look_review.py prepare BOOK [--size 20] [--dpi 110]
  uv run python scripts/look_review.py status BOOK
  uv run python scripts/look_review.py brief BOOK GROUP
  uv run python scripts/look_review.py check BOOK GROUP
  uv run python scripts/look_review.py merge BOOK

Files go to output/look_review/BOOK/. The session runbook is docs/prompts/look-review.md, and the
agent brief template is docs/prompts/look-review-group.md.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from polytypst.book_state import BookStateError
from polytypst.books import books, newest_input
from polytypst.look_review import (
    append_findings,
    group_problems,
    prepare,
    read_groups,
    read_pages,
    text_page_map,
    unaudited_pages,
)
from polytypst.ocr.scan import SourceScanError
from polytypst.parity.source import source_pdf
from polytypst.paths import OUTPUT
from polytypst.review import read_findings, render_checklist

REVIEW_ROOT = OUTPUT / "look_review"
FINDINGS = OUTPUT / "review_findings.jsonl"
BRIEF = REPO / "docs" / "prompts" / "look-review-group.md"


def _edition(key: str):
    book = books()[key]
    edition = next(iter(book.editions.values()))
    if not edition.rebuilt.exists():
        sys.exit(f"{edition.rebuilt} is missing; run: polytypst build {key}")
    try:
        scan = source_pdf(book.spec)
    except SourceScanError as error:
        sys.exit(str(error))
    return book, edition, scan


def _prepare(args: argparse.Namespace) -> int:
    book, edition, scan = _edition(args.book)
    review = REVIEW_ROOT / args.book
    if edition.parity:
        scan_map, mapped_by = edition.parity.page_map(), "the edition's page map"
    else:
        try:
            transcripts = book.transcripts
        except BookStateError as error:
            sys.exit(str(error))
        if not transcripts.is_dir():
            sys.exit(f"{args.book}: no transcripts at {transcripts}")
        scan_map, mapped_by = (
            text_page_map(transcripts, edition.rebuilt),
            f"shared text with {transcripts}",
        )
    entries = prepare(edition.rebuilt, scan, scan_map, review, args.size, args.dpi)
    groups = read_groups(review)
    stale = edition.rebuilt.stat().st_mtime < newest_input(args.book)
    over = [e.page for e in entries if e.overflow_pt > 3]
    unpaired = [e.page for e in entries if not e.scan_pages]
    print(
        f"rebuilt: {edition.rebuilt}{'  (stale: older than src/compiler or books/' + args.book + ')' if stale else ''}"
    )
    print(f"scan: {scan}; pages paired by {mapped_by}")
    print(
        f"{len(entries)} pages, {len(groups)} groups of {args.size}; overflow > 3pt on {len(over)} pages; {len(unpaired)} pages with no scan page"
    )
    print(f"folder: {review}")
    return 0


def _status(args: argparse.Namespace) -> int:
    review = REVIEW_ROOT / args.book
    todo = 0
    for group, (first, last) in enumerate(read_groups(review), 1):
        problems = group_problems(review, group, first, last)
        todo += bool(problems)
        print(
            f"group {group:02d} p{first}-{last}: "
            + ("done" if not problems else "todo (" + "; ".join(problems[:2]) + ")")
        )
    print("all groups done" if not todo else f"{todo} groups todo")
    return 0


def _brief(args: argparse.Namespace) -> int:
    _, edition, scan = _edition(args.book)
    review = REVIEW_ROOT / args.book
    first, last = read_groups(review)[args.group - 1]
    pages = [e for e in read_pages(review) if first <= e.page <= last]
    lines = "\n".join(
        f"- p{e.page}: rebuilt `{e.rebuilt_png}`; scan pages {e.scan_pages or 'none'} "
        f"`{'`, `'.join(e.scan_pngs) or '-'}`; overflow_pt {e.overflow_pt}"
        + (f" ({e.overflow_what})" if e.overflow_pt > 3 else "")
        for e in pages
    )
    body = BRIEF.read_text(encoding="utf-8").split("\n\n", 2)[2]
    print(
        body.format(
            book=args.book,
            group=args.group,
            first=first,
            last=last,
            review=review.relative_to(REPO),
            pages=lines,
            rebuilt=edition.rebuilt,
            scan=scan,
        )
    )
    return 0


def _check(args: argparse.Namespace) -> int:
    review = REVIEW_ROOT / args.book
    first, last = read_groups(review)[args.group - 1]
    problems = group_problems(review, args.group, first, last)
    print("ok" if not problems else "\n".join(problems))
    return 1 if problems else 0


def _merge(args: argparse.Namespace) -> int:
    review = REVIEW_ROOT / args.book
    missing = unaudited_pages(review, len(read_pages(review)))
    if missing:
        print(
            f"{len(missing)} pages have no audit line: {', '.join(map(str, missing[:30]))}; rerun those groups"
        )
        return 1
    try:
        result = append_findings(review, args.book, FINDINGS)
        findings = read_findings(FINDINGS)
    except ValueError as error:
        print(error)
        return 1
    FINDINGS.with_suffix(".md").write_text(render_checklist(findings), encoding="utf-8")
    mine = Counter(f.severity for f in findings if f.id.startswith(f"B{args.book}-"))
    print(
        f"appended {result.appended} findings ({result.first_id} to {result.last_id}); {args.book}: "
        + ", ".join(f"{s} {n}" for s, n in sorted(mine.items()))
    )
    print(f"checklist: {FINDINGS.with_suffix('.md')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser(
        "prepare",
        help="pair, render and measure every page, and split them into groups",
    )
    p.add_argument("book")
    p.add_argument("--size", type=int, default=20)
    p.add_argument("--dpi", type=int, default=110)
    for name, text in (
        ("status", "list each group as done or todo"),
        ("merge", "number the findings and append them"),
    ):
        sub.add_parser(name, help=text).add_argument("book")
    for name, text in (
        ("brief", "print the checking agent's prompt for a group"),
        ("check", "check one group's two files"),
    ):
        q = sub.add_parser(name, help=text)
        q.add_argument("book")
        q.add_argument("group", type=int)
    args = parser.parse_args()
    return {
        "prepare": _prepare,
        "status": _status,
        "brief": _brief,
        "check": _check,
        "merge": _merge,
    }[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
