"""Run a look review of one book: prepare page pairs, brief checking agents per group, check and merge their files.

Usage:
  uv run python scripts/look_review.py prepare BOOK [--sample] [--size 10] [--dpi 110]
  uv run python scripts/look_review.py status BOOK [--sample]
  uv run python scripts/look_review.py brief BOOK GROUP [--sample]
  uv run python scripts/look_review.py check BOOK GROUP [--sample]
  uv run python scripts/look_review.py crop BOOK PAGE:BOX[:SCANBOX] [PAGE:BOX ...] [--scan] [--sample]
  uv run python scripts/look_review.py find BOOK TEXT [--sample]
  uv run python scripts/look_review.py zoom BOOK SCAN_PAGE SPAN [--label TEXT] [--sample]
  uv run python scripts/look_review.py spot BOOK [--sample]
  uv run python scripts/look_review.py merge BOOK [--sample]
  uv run python scripts/look_review.py workspace | clean

Pages: a page number means one of three things, and they differ in every book.
  rebuilt page  1-based page of the rebuilt PDF: PAGE in crop, `page` in look_pages.jsonl
  scan page     1-based page of the scan PDF: crop --scan, `scan_pages`, transcript/p_NNN.md, a verdict's scan_page
  printed page  the folio printed on the paper; no command takes it, so turn it into the others with find
To place a text, run find; to see a verdict's page, run crop --scan SCAN_PAGE:full.

--sample reviews three groups (front, middle, back) in output/look_review/BOOK/sample/, so the causes
that repeat through a book are found before every page is checked. Without it, files go to
output/look_review/BOOK/. The session runbook is docs/prompts/look-review.md, and the agent brief
template is docs/prompts/look-review-group.md.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from polytypst.book_state import BookStateError
from polytypst.books import books, newest_input
from polytypst.checker import AuditSpec
from polytypst.corrections import causes
from polytypst.evidence import zoom
from polytypst.look_review import (
    append_findings,
    brief,
    close_workspace,
    crop,
    find_text,
    group_problems,
    group_ranges,
    missing_inputs,
    open_workspace,
    pair_sheets,
    pass_rules,
    prepare,
    read_groups,
    read_pages,
    sample_ranges,
    spot_check,
    stock,
    text_page_map,
    unaudited_pages,
)
from polytypst.ocr.lines import source_ocr_dir
from polytypst.ocr.scan import SourceScanError
from polytypst.parity.source import source_pdf
from polytypst.paths import OUTPUT
from polytypst.review import read_findings, render_checklist

REVIEW_ROOT = OUTPUT / "look_review"
FINDINGS = OUTPUT / "review_findings.jsonl"
BRIEF = REPO / "docs" / "prompts" / "look-review-group.md"
DPI = 110
BAR = (REPO / "docs" / "prompts" / "math-book-check.md", REPO / "docs" / "publisher-bar.md")
SKILL = REPO / ".agent" / "skills" / "antigravity-look-review"


def _review(args: argparse.Namespace) -> Path:
    return (
        REVIEW_ROOT / args.book / "sample" if args.sample else REVIEW_ROOT / args.book
    )


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


def _transcripts(book) -> Path:
    try:
        return book.transcripts
    except BookStateError as error:
        sys.exit(str(error))


def _stored_transcripts(book) -> Path | None:
    try:
        return book.transcripts
    except BookStateError:
        return None


def _prepare(args: argparse.Namespace) -> int:
    book, edition, scan = _edition(args.book)
    review = _review(args)
    if edition.parity:
        scan_map, mapped_by = edition.parity.page_map(), "the edition's page map"
    else:
        transcripts = _transcripts(book)
        if not transcripts.is_dir():
            sys.exit(f"{args.book}: no transcripts at {transcripts}")
        scan_map, mapped_by = (
            text_page_map(transcripts, edition.rebuilt),
            f"shared text with {transcripts}",
        )
    page_count = len(pymupdf.open(edition.rebuilt))
    ranges = (sample_ranges if args.sample else group_ranges)(page_count, args.size)
    audit = (
        AuditSpec.from_monograph(edition.spec)
        if edition.spec
        else AuditSpec(front_matter_pages=0)
    )
    entries = prepare(edition.rebuilt, scan, scan_map, review, ranges, args.dpi, audit)
    stock(review, REPO, args.book, _stored_transcripts(book), args.sample)
    stale = edition.rebuilt.stat().st_mtime < newest_input(args.book)
    over = [e.page for e in entries if e.overflow_pt > 3]
    unpaired = [e.page for e in entries if not e.scan_pages]
    rules = Counter(rule for e in entries for rule in e.checker)
    print(
        f"rebuilt: {edition.rebuilt}{'  (stale: older than src/compiler or books/' + args.book + ')' if stale else ''}"
    )
    print(f"scan: {scan}; pages paired by {mapped_by}")
    print(
        f"{len(entries)} of {page_count} pages, {len(ranges)} groups of {args.size}; overflow > 3pt on {len(over)} pages; {len(unpaired)} pages with no scan page"
    )
    print(
        "checker: "
        + (
            ", ".join(f"{rule} on {n} pages" for rule, n in rules.most_common())
            or "no hits"
        )
    )
    print(f"folder: {review}")
    return 0


def _status(args: argparse.Namespace) -> int:
    review = _review(args)
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


def _facts(book, review: Path) -> list[str]:
    """What the checking agent would otherwise search for: the transcript folder, the statement style
    and the known cause ids."""
    lines = [
        f"- The transcript of scan page N is `{review}/transcript/p_NNN.md`. A scan page with no file there has no transcript."
    ]
    if book.spec.statement_style:
        lines.append(
            f"- `book.toml` sets theorem-like statements {book.spec.statement_style}. Another style is a defect only when the scan differs."
        )
    if known := causes("code"):
        lines.append(
            "- When a defect matches a known cause, add `cause_id` with its id, and write one finding for the whole group that lists the pages:"
        )
        lines += [
            f"  - {c.id} ({c.status.split(',')[0]}): {c.root_cause}" for c in known
        ]
    return lines


def _brief(args: argparse.Namespace) -> int:
    book, edition, scan = _edition(args.book)
    review = _review(args)
    first, last = read_groups(review)[args.group - 1]
    pages = read_pages(review)
    if missing_inputs(review, pages, first, last):
        stock(review, REPO, args.book, _stored_transcripts(book), args.sample)
        pair_sheets(review, edition.rebuilt, scan, pages, first, last, DPI)
    if missing := missing_inputs(review, pages, first, last):
        sample = " --sample" if args.sample else ""
        sys.exit(
            f"{review.resolve()} lacks {', '.join(missing)}: an older prepare made it. "
            f"Run: ./lr prepare {args.book}{sample}"
        )
    print(
        brief(
            BRIEF.read_text(encoding="utf-8"),
            review.resolve(),
            args.book,
            args.group,
            first,
            last,
            pages,
            _facts(book, review.resolve()),
            [r for doc in BAR for r in pass_rules(doc.read_text(encoding="utf-8"))],
        )
    )
    return 0


def _crop(args: argparse.Namespace) -> int:
    _, edition, scan = _edition(args.book)
    try:
        out = crop(_review(args), edition.rebuilt, scan, args.region, by_scan=args.scan)
    except ValueError as error:
        print(error)
        return 1
    print(out)
    return 0


def _find(args: argparse.Namespace) -> int:
    _, edition, _ = _edition(args.book)
    hits = find_text(_review(args), edition.rebuilt, args.text)
    for hit in hits:
        if hit.rebuilt is None:
            print(f"transcript of scan p{hit.scan_pages[0]}: crop it with --scan {hit.scan_pages[0]}:full")
        else:
            print(f"rebuilt p{hit.rebuilt} (scan pages {hit.scan_pages or 'none'}): crop it with {hit.rebuilt}:full")
    print(f"{len(hits)} pages hold {args.text!r}")
    return 0 if hits else 1


def _zoom(args: argparse.Namespace) -> int:
    book, _, scan = _edition(args.book)
    out = _review(args) / "crops" / f"zoom_p{args.page:03d}_{re.sub(r'[^\w.-]+', '-', args.span)[:40]}.png"
    try:
        print(zoom(scan, source_ocr_dir(book.out_dir), args.page, args.span, args.label or f"scan p{args.page}", out))
    except ValueError as error:
        print(error)
        return 1
    return 0


def _check(args: argparse.Namespace) -> int:
    review = _review(args)
    first, last = read_groups(review)[args.group - 1]
    problems = group_problems(review, args.group, first, last)
    print("ok" if not problems else "\n".join(problems))
    return 1 if problems else 0


def _spot(args: argparse.Namespace) -> int:
    _, edition, scan = _edition(args.book)
    review = _review(args)
    items = spot_check(review, edition.rebuilt, scan)
    for item in items:
        where = (
            f"rebuilt p{item.page}, scan pages {item.scan_pages or 'none'}"
            if item.page
            else "no page read from `where`"
        )
        print(f"{item.item} ({where}){': ' + item.text if item.text else ''}")
        for png in item.pngs:
            print(f"  {review / png}")
    print(
        f"{len(items)} items; write one line per item to {review / 'spot_check.jsonl'}"
    )
    return 0


def _merge(args: argparse.Namespace) -> int:
    review = _review(args)
    missing = unaudited_pages(review)
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


def _workspace(args: argparse.Namespace) -> int:
    open_workspace(REVIEW_ROOT, REPO, SKILL)
    print(f"workspace: {REVIEW_ROOT}; open the orchestrator there, run `{REVIEW_ROOT / 'lr'} clean` when every review is merged")
    return 0


def _clean(args: argparse.Namespace) -> int:
    close_workspace(REVIEW_ROOT)
    print(f"removed lr and .agent from {REVIEW_ROOT}; the reviews stay")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (run, text) in {
        "workspace": (_workspace, "make the look_review folder the orchestrator's workspace, with lr and the skill"),
        "clean": (_clean, "remove the workspace's lr and skill copy, and keep the reviews"),
    }.items():
        sub.add_parser(name, help=text).set_defaults(run=run)
    commands = {
        "prepare": (
            _prepare,
            "pair, render and check the pages, and split them into groups",
        ),
        "status": (_status, "list each group as done or todo"),
        "brief": (_brief, "print the checking agent's prompt for a group"),
        "check": (_check, "check one group's two files"),
        "crop": (_crop, "put boxes of rebuilt pages beside the same boxes of their scan pages on one sheet"),
        "find": (_find, "list the rebuilt pages and scan transcripts that hold a text, with their paired pages"),
        "zoom": (_zoom, "box a span on a scan page with a magnified inset, as polytypst evidence zoom does"),
        "spot": (_spot, "pick and render 3 grave findings and 2 passed pages to judge"),
        "merge": (_merge, "number the findings and append them"),
    }
    for name, (run, text) in commands.items():
        p = sub.add_parser(name, help=text)
        p.set_defaults(run=run)
        p.add_argument("book")
        if name in ("brief", "check"):
            p.add_argument("group", type=int)
        if name == "crop":
            p.add_argument(
                "region",
                nargs="+",
                help="PAGE:BOX or PAGE:BOX:SCANBOX; PAGE is a rebuilt page (a scan page with --scan); "
                "BOX is top, middle, bottom, full, or L,T,R,B as shares of the page",
            )
            p.add_argument(
                "--scan",
                action="store_true",
                help="read each PAGE as a scan page, as a verdict's scan_page is, and show its paired rebuilt pages",
            )
        if name == "find":
            p.add_argument("text", help="the text to look for, such as an equation number or a phrase")
        if name == "zoom":
            p.add_argument("page", type=int, help="scan page")
            p.add_argument("span", help="the span exactly as the local OCR read it")
            p.add_argument("--label", help="one line printed under the strip; scan pPAGE by default")
        if name == "prepare":
            p.add_argument("--size", type=int, default=10)
            p.add_argument("--dpi", type=int, default=DPI)
        p.add_argument(
            "--sample",
            action="store_true",
            help="the three-group sample in BOOK/sample/",
        )
    args = parser.parse_args()
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
