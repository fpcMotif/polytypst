"""Find transcript errors, scan typos and false positives in a scanned book, in stages that any book can reuse.

Usage:
  uv run python scripts/book_check.py lint BOOK                  # known-error rules over the transcript and the built .typ
  uv run python scripts/book_check.py triage BOOK [--scan PDF]   # settle width-only issues, cut a scan zoom for each other one
  uv run python scripts/book_check.py sheets BOOK [--size 30]
  uv run python scripts/book_check.py verify BOOK [--size 30] [--jobs 4] [--model claude-sonnet-5-5]
  uv run python scripts/book_check.py status [BOOK ...]          # each stage's counts and the next command

BOOK is a book number from 1 to 6 or a folder name under books/. The page check agents
(`scripts/page_check.py run`) write the issues. lint, triage and verify write next to them in
output/page_check/BOOK/. docs/page-check-review.md is the runbook.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import page_check
import pymupdf
import scan_sheet

from polytypst.figure_leaks import apply_page_fixups

GLUED_WORDS = re.compile(r"\b[A-Za-z]*?[a-z]{2}[A-Z][a-z]{2,}\b")
NAME_PREFIX = re.compile(r"(?:Ma?c|Mc|De|Le|La|Van|Von|O)[A-Z]")
BROKEN_TAG = re.compile(r"</\s+\w|<\s+/?t[hdr]\b|<t[hdr]\s+>")
SPACED_DECIMAL = re.compile(r"(?<![\d.])\d+ \.\d")
RUNNING_HEAD = re.compile(
    r"\d{1,3}\s+[^\n。，；《》]{1,30}|[^\n。，；《》]{1,30}\s+\d{1,3}"
)
RULE_KINDS = {
    "glued_words": "word",
    "broken_tag": "table_shape",
    "spaced_decimal": "number",
    "lone_book_mark": "mark",
    "dead_fixup": "word",
    "multiline_delete": "missing_text",
}
NO_AUTO_VERDICT = {"sum", "table_shape"}
ZOOM_PAD = 0.02
ZOOM_DPI = 300
PAGE_DPI = 150
VERIFY_MODEL = "claude-sonnet-5-5"


def hit(rule: str, line: int, text: str) -> dict:
    return {
        "line": line,
        "kind": RULE_KINDS.get(rule, "extra_text"),
        "rule": rule,
        "transcript": text,
        "scan": "",
    }


def text_blocks(markdown: str) -> list[tuple[int, str]]:
    """Each paragraph of a page with its first line number, leaving out headings such as a transcribed running head."""
    blocks, first = [], 1
    for block in re.split(r"\n\s*\n", markdown):
        if (
            block.strip()
            and not block.lstrip().startswith("#")
            and not RUNNING_HEAD.fullmatch(block.strip())
        ):
            blocks.append((first, block))
        first += block.count("\n") + 2
    return blocks


def book_marks_open(block: str) -> int:
    return block.count("《") - block.count("》")


def lint_page(markdown: str, before: str = "", after: str = "") -> list[dict]:
    """The places on one transcript page that match an error the page check confirmed in an earlier book.
    `before` and `after` are the pages around it, for a title in 《》 that runs across the page break."""
    found = []
    for n, line in enumerate(markdown.splitlines(), 1):
        for m in BROKEN_TAG.finditer(line):
            found.append(
                hit(
                    "broken_tag", n, line[max(0, m.start() - 12) : m.end() + 12].strip()
                )
            )
    for n, line in page_check.prose_lines(markdown):
        for m in GLUED_WORDS.finditer(line):
            if not NAME_PREFIX.match(m[0]):
                found.append(hit("glued_words", n, m[0]))
        for m in SPACED_DECIMAL.finditer(line):
            found.append(
                hit("spaced_decimal", n, line[max(0, m.start() - 4) : m.end() + 2])
            )
    blocks = text_blocks(markdown)
    next_opens = book_marks_open(text_blocks(after)[0][1]) if text_blocks(after) else 0
    prev_opens = (
        book_marks_open(text_blocks(before)[-1][1]) if text_blocks(before) else 0
    )
    for k, (first, block) in enumerate(blocks):
        opened = book_marks_open(block)
        runs_on = (k == len(blocks) - 1 and opened > 0 and next_opens < 0) or (
            k == 0 and opened < 0 and prev_opens > 0
        )
        if opened and not runs_on and not block.lstrip().startswith(("|", "<table")):
            found.append(
                hit("lone_book_mark", first, block.strip().splitlines()[0][:40])
            )
    return found


def lint_typ(typ: str, title: str) -> list[dict]:
    """Running heads, such as `120 不良债权与金融危机`, that the page cleaner left in the built book's text."""
    head = re.compile(
        rf"^\s*(?:\d{{1,3}}\s*{re.escape(title)}|{re.escape(title)}\s*\d{{1,3}})\s*$"
    )
    return [
        hit("running_head", n, line.strip())
        for n, line in enumerate(typ.splitlines(), 1)
        if head.match(line)
    ]


def is_multiline_delete(pat: str, rep: str, matched: str) -> bool:
    if rep or "\n" not in matched.strip():
        return False
    if "(?m)" in pat and r"\|" not in pat:
        return True
    return len(matched) > 300 and not any(
        k in pat for k in (r"\A", r"\Z", "(?s)", ".*?", "<table")
    )


def lint_fixups(
    markdown: str,
    fixups: tuple[tuple[str, str], ...],
    page_fixups: tuple[tuple[str, str], ...] = (),
    cleaned: str | None = None,
) -> list[dict]:
    from polytypst.compiler.page_cleaner import (
        normalize_html_tables,
        split_page_footnotes,
    )

    found = []
    text = markdown
    for pat, rep in fixups:
        m = re.search(pat, text, flags=re.DOTALL)
        if not m:
            found.append(hit("dead_fixup", 1, pat[:40]))
            continue
        if is_multiline_delete(pat, rep, m[0]):
            line = text[: m.start()].count("\n") + 1
            found.append(hit("multiline_delete", line, m[0].splitlines()[0][:40]))
        text = apply_page_fixups(text, ((pat, rep),))
    if not page_fixups:
        return found
    if cleaned is None:
        cleaned, _ = split_page_footnotes(
            normalize_html_tables(text), "circled", r"^\d+$"
        )
    for pat, rep in page_fixups:
        m = re.search(pat, cleaned, flags=re.DOTALL) or (
            None if rep else re.search(pat, text, flags=re.DOTALL)
        )
        if not m:
            found.append(hit("dead_fixup", 1, pat[:40]))
            continue
        if is_multiline_delete(pat, rep, m[0]):
            src = cleaned if re.search(pat, cleaned, flags=re.DOTALL) else text
            line = src[: m.start()].count("\n") + 1
            found.append(hit("multiline_delete", line, m[0].splitlines()[0][:40]))
        cleaned = apply_page_fixups(cleaned, ((pat, rep),))
        text = apply_page_fixups(text, ((pat, rep),))
    return found


def squash(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+(?=[^\x00-\x7f])|(?<=[^\x00-\x7f])\s+", "", text)


def auto_verdict(issue: dict) -> str | None:
    """`false_positive` when the two sides differ only in character width or in spaces next to Chinese text.
    Spaces between Latin words and inside tags still count, so those issues go to a verifier."""
    t, s = issue.get("transcript", ""), issue.get("scan", "")
    if issue["kind"] in NO_AUTO_VERDICT or t == s or squash(t) != squash(s):
        return None
    return "false_positive"


def running_head_claim(issue: dict, title: str) -> bool:
    """An `extra_text` claim on a page's running head. The page cleaner drops running heads, and `lint` finds any left in the built book."""
    head = issue.get("transcript", "").strip().lstrip("#").strip()
    return (
        issue["kind"] == "extra_text"
        and not issue.get("scan")
        and title in head
        and bool(RUNNING_HEAD.fullmatch(head))
    )


def issue_key(page: int, issue: dict) -> tuple:
    return (
        int(page),
        issue["kind"],
        issue.get("transcript", ""),
        issue.get("scan", ""),
    )


def results(book: str) -> Path:
    return page_check.RESULTS / book


def read_jsonl(path: Path) -> list[dict]:
    return (
        [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if path.exists()
        else []
    )


def append_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("a", encoding="utf-8") as out:
        out.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def agent_issues(book: str) -> list[dict]:
    found = []
    for path in sorted(results(book).glob("p*.jsonl")):
        for record in read_jsonl(path):
            found += [
                {"page": int(record["page"]), **issue} for issue in record["issues"]
            ]
    return found


def verdict_keys(book: str) -> set[tuple]:
    return {
        issue_key(v["page"], v) for v in read_jsonl(results(book) / "verdicts.jsonl")
    }


def built_typ(book: str) -> Path | None:
    out = Path("output") / page_check.book_key(book)
    return next(
        (p for p in sorted(out.glob("*.typ")) if p.stem in (book, "book", out.name)),
        None,
    )


def book_spec(book: str):
    from polytypst.books import books

    return (
        books()[book_key].spec
        if (book_key := page_check.book_key(book)) in books()
        else None
    )


def book_fixups(book: str) -> dict[int, tuple]:
    """The book's transcript and page fixups by page, so that lint reads each page as the book prints it."""
    spec = book_spec(book)
    if spec is None:
        return {}
    pages = set(spec.transcript_fixups) | set(spec.page_fixups)
    return {
        p: (*spec.transcript_fixups.get(p, ()), *spec.page_fixups.get(p, ()))
        for p in pages
    }


def lint(book: str) -> list[dict]:
    from dataclasses import replace

    from polytypst.compiler.page_cleaner import PageCleaner

    found = []
    pages = page_check.transcript_pages(book)
    spec = book_spec(book)
    cleaner = (
        PageCleaner.for_spec(
            replace(spec, page_fixups={}, equation_numbering=None),
            asset_root=Path("output") / page_check.book_key(book),
        )
        if spec is not None
        else None
    )
    texts = []
    for page in pages:
        text = page_check.transcript_path(book, page).read_text(encoding="utf-8")
        t_rules = spec.transcript_fixups.get(page, ()) if spec else ()
        p_rules = spec.page_fixups.get(page, ()) if spec else ()
        cleaned = (
            re.sub(
                r"@@FNSTART@@.*?@@FNEND@@",
                "①",
                cleaner.clean(text, page).body,
                flags=re.DOTALL,
            )
            if cleaner is not None
            else None
        )
        found += [
            {"page": page, **h} for h in lint_fixups(text, t_rules, p_rules, cleaned)
        ]
        texts.append(apply_page_fixups(text, (*t_rules, *p_rules)))
    for k, page in enumerate(pages):
        before, after = (
            texts[k - 1] if k else "",
            texts[k + 1] if k + 1 < len(texts) else "",
        )
        found += [{"page": page, **h} for h in lint_page(texts[k], before, after)]
    if typ := built_typ(book):
        found += [
            {"page": None, "where": str(typ), **h}
            for h in lint_typ(typ.read_text(encoding="utf-8"), book_title(book))
        ]
    return found


def book_title(book: str) -> str:
    return re.sub(r"^\d+[_ ]", "", page_check.book_key(book))


def zoom(book: str, doc: pymupdf.Document, issue: dict, out: Path) -> str:
    """A 300 dpi strip of the scan around the issue's line, or the whole page when no OCR line holds its text."""
    texts = [t for t in (issue.get("scan", ""), issue.get("transcript", "")) if t]
    keys = [
        k for n in (12, 6, 3) for t in texts if len(page_check.norm(k := t[:n])) >= 2
    ]
    cases = (scan_sheet.Case(page=issue["page"], scan=key, find=key) for key in keys)
    band = next((b for case in cases if (b := scan_sheet.find_band(book, case))), None)
    band = (
        (max(0.0, band[0] - ZOOM_PAD), min(1.0, band[1] + ZOOM_PAD))
        if band
        else (0.0, 1.0)
    )
    out.write_bytes(
        scan_sheet.strip_png(
            doc, issue["page"], band, ZOOM_DPI if band != (0.0, 1.0) else PAGE_DPI
        )
    )
    return str(out)


def triage(book: str, scan: Path) -> tuple[int, int]:
    folder = results(book) / "verify"
    folder.mkdir(parents=True, exist_ok=True)
    done = verdict_keys(book)
    lint_hits = [
        {**h, "note": f"lint: {h['rule']}"}
        for h in read_jsonl(results(book) / "lint.jsonl")
        if h["page"]
    ]
    pending = [
        i
        for i in [*agent_issues(book), *lint_hits]
        if issue_key(i["page"], i) not in done
    ]
    title = book_title(book)
    settled, open_claims = [], []
    for issue in pending:
        if auto_verdict(issue):
            settled.append(
                {
                    **issue,
                    "verdict": "false_positive",
                    "detail": "width or spacing only",
                    "by": "auto",
                }
            )
        elif running_head_claim(issue, title):
            settled.append(
                {
                    **issue,
                    "verdict": "false_positive",
                    "detail": "running head, which the build drops",
                    "by": "auto",
                }
            )
        else:
            open_claims.append(issue)
    append_jsonl(results(book) / "verdicts.jsonl", settled)
    doc = pymupdf.open(scan)
    queue = []
    for k, issue in enumerate(open_claims):
        page_image = folder / f"page{issue['page']}.png"
        if not page_image.exists():
            page_image.write_bytes(
                scan_sheet.strip_png(doc, issue["page"], (0.0, 1.0), PAGE_DPI)
            )
        zoomed = zoom(book, doc, issue, folder / f"p{issue['page']}_{k}.png")
        queue.append({**issue, "zoom": zoomed, "page_image": str(page_image)})
    (results(book) / "queue.jsonl").write_text(
        "".join(json.dumps(q, ensure_ascii=False) + "\n" for q in queue),
        encoding="utf-8",
    )
    return len(settled), len(queue)


def verify_batch(items: Path, out: Path, model: str) -> str:
    with out.with_suffix(".log").open("w", encoding="utf-8") as log:
        code = subprocess.run(
            [
                "omp",
                "-p",
                "--no-session",
                "--model",
                model,
                "@docs/page-verify.md",
                f"Follow this runbook with ITEMS={items} OUT={out}.",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=3600,
            check=False,
        ).returncode
    return f"{out.name}: exit {code}, {len(read_jsonl(out))} of {len(read_jsonl(items))} verdicts"


def verify(book: str, size: int, jobs: int, model: str) -> int:
    """Start one agent for each batch of queued issues, then add their verdicts to verdicts.jsonl. A batch whose
    output exists is not run again, so a rerun only starts the batches that failed."""
    folder = results(book) / "verify"
    done = verdict_keys(book)
    queue = [
        q
        for q in read_jsonl(results(book) / "queue.jsonl")
        if issue_key(q["page"], q) not in done
    ]
    batches = []
    for i in range(0, len(queue), size):
        part = queue[i : i + size]
        name = hashlib.sha1(
            repr([issue_key(q["page"], q) for q in part]).encode()
        ).hexdigest()[:8]
        items, out = folder / f"q{name}.jsonl", folder / f"v{name}.jsonl"
        items.write_text(
            "".join(json.dumps(q, ensure_ascii=False) + "\n" for q in part),
            encoding="utf-8",
        )
        batches.append((items, out))
    todo = [b for b in batches if not b[1].exists()]
    print(
        f"{len(queue)} issues, {len(todo)} of {len(batches)} batches to run, {jobs} at a time",
        flush=True,
    )
    with ThreadPoolExecutor(jobs) as pool:
        for line in pool.map(lambda b: verify_batch(*b, model), todo):
            print(line, flush=True)
    queued = {issue_key(q["page"], q): q for q in queue}
    added = []
    for _, out in batches:
        for v in read_jsonl(out):
            key = issue_key(v["page"], v)
            if (
                key in queued
                and key not in done
                and v.get("verdict") in ("real", "scan_typo", "false_positive", "sum")
            ):
                done.add(key)
                q = queued[key]
                added.append(
                    {
                        k: q[k]
                        for k in ("page", "line", "kind", "transcript", "scan")
                        if k in q
                    }
                    | {
                        "verdict": v["verdict"],
                        "detail": v.get("detail", ""),
                        "by": model,
                    }
                )
    append_jsonl(results(book) / "verdicts.jsonl", added)
    return len(added)


def contact_sheet(
    cards: list[tuple[str, Path]], out: Path, width: int = 1200, max_crop_h: int = 260
) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    header_h, pad = 28, 6
    font = ImageFont.load_default(size=14)
    loaded: list[tuple[str, Image.Image]] = []
    for label, img_path in cards:
        with Image.open(img_path) as raw:
            img = raw.convert("RGB")
        if img.width > width - 2 * pad:
            scale = (width - 2 * pad) / img.width
            img = img.resize(
                (width - 2 * pad, max(1, round(img.height * scale))), Image.LANCZOS
            )
        if img.height > max_crop_h:
            img = img.crop((0, 0, img.width, max_crop_h))
        loaded.append((label, img))
    total_h = sum(header_h + img.height + pad for _, img in loaded) + pad
    canvas = Image.new("RGB", (width, max(1, total_h)), (245, 245, 245))
    draw = ImageDraw.Draw(canvas)
    y = pad
    for label, img in loaded:
        draw.rectangle([pad, y, width - pad, y + header_h - 2], fill=(35, 40, 50))
        draw.text((pad + 6, y + 6), label[:140], fill=(255, 255, 255), font=font)
        y += header_h
        canvas.paste(img, (pad, y))
        y += img.height + pad
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def sheets(book: str, size: int = 30) -> list[Path]:
    done = verdict_keys(book)
    seen: set[tuple] = set()
    cards: list[tuple[str, Path]] = []
    for idx, q in enumerate(read_jsonl(results(book) / "queue.jsonl")):
        key = issue_key(q["page"], q)
        if key in done or key in seen:
            continue
        seen.add(key)
        img_path = Path(q.get("zoom") or q.get("page_image", ""))
        if not img_path.exists():
            continue
        t = " ".join(q.get("transcript", "").splitlines())[:42]
        s = " ".join(q.get("scan", "").splitlines())[:42]
        label = (
            f"#{idx} p{q['page']} L{q.get('line', 1)} [{q['kind']}] | T: {t} | S: {s}"
        )
        cards.append((label, img_path))
    out_dir = results(book) / "verify" / "sheets"
    written = []
    for n, start in enumerate(range(0, len(cards), size), 1):
        written.append(
            contact_sheet(cards[start : start + size], out_dir / f"sheet_{n:02d}.png")
        )
    return written


def status(book: str) -> list[str]:
    t = page_check.tally(book)
    linted = (results(book) / "lint.jsonl").exists()
    lint_hits = read_jsonl(results(book) / "lint.jsonl")
    claims = [*agent_issues(book), *(h for h in lint_hits if h["page"])]
    verdicts = read_jsonl(results(book) / "verdicts.jsonl")
    keys = {issue_key(v["page"], v) for v in verdicts}
    unverified = {issue_key(i["page"], i) for i in claims} - keys
    queued = {
        issue_key(q["page"], q) for q in read_jsonl(results(book) / "queue.jsonl")
    }
    by = Counter(v["verdict"] for v in verdicts)
    judged = sum(n for k, n in by.items() if k != "sum")
    lines = [
        f"book {book} ({page_check.book_key(book)})",
        f"  page check: {len(t.checked & t.pages)}/{len(t.pages)} pages, {len(claims) - len(lint_hits)} issues",
        f"  lint: {dict(Counter(h['rule'] for h in lint_hits)) if linted else 'not run'}",
        f"  verdicts: {dict(by)}, {sum(v.get('by') == 'auto' for v in verdicts)} auto, {len(unverified)} unverified"
        + (
            f", false-positive rate {by['false_positive'] / judged:.0%}"
            if judged
            else ""
        ),
        f"  false negatives: {len(read_jsonl(results(book) / 'false_negatives.jsonl'))}",
    ]
    steps = []
    if missing := sorted(t.pages - t.checked):
        steps.append(
            f"uv run python scripts/page_check.py run --books {book}   # unchecked {page_check.ranges(missing)}"
        )
    if not linted:
        steps.append(f"uv run python scripts/book_check.py lint {book}")
    if unverified - queued:
        steps.append(f"uv run python scripts/book_check.py triage {book}")
    elif unverified:
        steps.append(f"uv run python scripts/book_check.py verify {book}")
    if by["real"] or by["scan_typo"]:
        steps.append(
            "fix the real and scan_typo verdicts: docs/page-check-review.md, Step 4"
        )
    return [*lines, *(f"  next: {s}" for s in steps)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("lint", "triage", "sheets", "verify"):
        p = sub.add_parser(name)
        p.add_argument(
            "book", help="a book number from 1 to 6, or a folder name under books/"
        )
        if name == "triage":
            p.add_argument(
                "--scan", type=Path, help="the scan PDF, when the book has no book.toml"
            )
        if name == "sheets":
            p.add_argument(
                "--size", type=int, default=30, help="strips per contact sheet"
            )
        if name == "verify":
            p.add_argument("--size", type=int, default=30, help="issues per agent")
            p.add_argument("--jobs", type=int, default=4, help="agents at once")
            p.add_argument("--model", default=VERIFY_MODEL)
    p = sub.add_parser("status")
    p.add_argument("books", nargs="*", default=list(page_check.BOOKS))
    args = parser.parse_args()

    if args.command == "lint":
        found = lint(args.book)
        results(args.book).mkdir(parents=True, exist_ok=True)
        path = results(args.book) / "lint.jsonl"
        path.write_text(
            "".join(json.dumps(h, ensure_ascii=False) + "\n" for h in found),
            encoding="utf-8",
        )
        for rule, n in Counter(h["rule"] for h in found).most_common():
            examples = "; ".join(
                f"p{h['page']} {h['transcript']}" for h in found if h["rule"] == rule
            )
            print(f"{rule}: {n}  {examples[:160]}")
        print(f"{len(found)} hits -> {path}")
    elif args.command == "triage":
        settled, queued = triage(args.book, args.scan or page_check.scan_pdf(args.book))
        print(
            f"{settled} settled as false_positive (width, spacing or running head), {queued} queued with zooms -> {results(args.book) / 'queue.jsonl'}"
        )
    elif args.command == "sheets":
        written = sheets(args.book, args.size)
        print(
            f"{len(written)} contact sheet(s) -> {results(args.book) / 'verify' / 'sheets'}"
        )
    elif args.command == "verify":
        print(f"{verify(args.book, args.size, args.jobs, args.model)} verdicts added")
    else:
        for book in args.books:
            print("\n".join(status(book)))


if __name__ == "__main__":
    sys.exit(main())
