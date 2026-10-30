"""Plan, assist and tally the page-by-page check of the six economics books against their scans.

Usage:
  uv run python scripts/page_check.py text BOOK PAGE                # the transcript, with line numbers
  uv run python scripts/page_check.py suspects BOOK PAGE           # where the transcript and the local OCR disagree
  uv run python scripts/page_check.py cells BOOK PAGE               # each transcript table on the page, as rows
  uv run python scripts/page_check.py tablediff BOOK PAGE K SCAN.tsv  # transcript table K against the scan's reading
  uv run python scripts/page_check.py summary [--books 1,4]         # pages checked, issues by kind, gaps
  uv run python scripts/page_check.py chunks [--size 10] [--books 1,4]
  uv run python scripts/page_check.py run [--jobs 8] [--model gemini-3.8-flash] [--books 1,4]

docs/page-check.md is the runbook an agent follows for one chunk. Each chunk writes
output/page_check/BOOK/pFIRST-LAST.jsonl with one JSON line per scan page.
"""

import argparse
import json
import os
import re
import subprocess
import tomllib
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

if "POLYTYPST_BOOKS" not in os.environ:
    _local = Path(__file__).resolve().parent.parent / "mise.local.toml"
    if _local.is_file():
        _env = tomllib.loads(_local.read_text()).get("env", {})
        if "POLYTYPST_BOOKS" in _env:
            os.environ["POLYTYPST_BOOKS"] = _env["POLYTYPST_BOOKS"]

from polytypst.book_state import book_state

BOOKS = {
    "1": "1_宏观经济与产业结构",
    "2": "2 通缩经济与货币政策",
    "3": "3_国际经济环境的变化与日本经济",
    "4": "4_不良债权与金融危机",
    "5": "5_财政政策与社会保障",
    "6": "6_劳动力市场与收入分配",
}
RESULTS = Path("output/page_check")
KINDS = {"word", "number", "table_cell", "table_shape", "missing_text", "extra_text", "order", "mark", "math", "sum", "scan_typo"}
KEPT_CHAR = re.compile(r"[一-鿿A-Za-z0-9.%]")
BAND_PAD = 0.02


@dataclass
class Tally:
    pages: set[int]
    checked: set[int]
    issue_pages: set[int]
    kinds: Counter[str]
    bad_lines: list[str]


def book_key(book: str) -> str:
    """The transcript store name of BOOK: one of the six economics books by number, or any folder name under books/."""
    return BOOKS.get(book, book)


def scan_pdf(book: str) -> Path:
    from polytypst.books import books
    from polytypst.parity.source import source_pdf

    return source_pdf(books()[book_key(book)].spec)


def transcript_path(book: str, page: int) -> Path:
    return book_state(Path(book_key(book))) / "markdown_pages" / f"p_{page:03d}.md"


def transcript_pages(book: str) -> list[int]:
    store = book_state(Path(book_key(book))) / "markdown_pages"
    return sorted(int(m[1]) for p in store.glob("p_*.md") if (m := re.fullmatch(r"p_(\d+)\.md", p.name)))


def norm(text: str) -> str:
    return "".join(KEPT_CHAR.findall(unicodedata.normalize("NFKC", text)))


def prose_lines(markdown: str) -> list[tuple[int, str]]:
    """Each transcript line that holds prose, with its line number. Tables, display math and images are left out,
    and inline math is blanked, because the local OCR reads them as noise."""
    kept: list[tuple[int, str]] = []
    in_table = in_math = False
    for n, line in enumerate(markdown.splitlines(), 1):
        stripped = line.strip()
        if "<table" in stripped:
            in_table = True
        if in_table:
            in_table = "</table>" not in stripped
            continue
        if stripped.startswith("$$"):
            in_math = not (stripped.endswith("$$") and len(stripped) > 2) and not in_math
            continue
        if in_math or stripped.startswith(("|", "![")):
            continue
        kept.append((n, re.sub(r"\$[^$]*\$", " ", re.sub(r"<[^>]+>", "", line))))
    return kept


def ocr_lines(book: str, page: int) -> list[tuple[float, float, str]]:
    path = book_state(Path(book_key(book))) / "source_ocr" / f"p{page:03d}.json"
    boxes = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    # The local OCR measures y up from the bottom of the page.
    lines = [(1 - b["y"] - b["h"], 1 - b["y"], b["x"], b["text"]) for b in boxes]
    return [(top, bottom, text) for top, bottom, _, text in sorted(lines, key=lambda b: (round(b[0], 2), b[2]))]


def suspects(book: str, page: int) -> list[str]:
    t_chars: list[tuple[str, int]] = [(c, n) for n, line in prose_lines(transcript_path(book, page).read_text(encoding="utf-8")) for c in norm(line)]
    o_chars: list[tuple[str, float, float]] = [(c, top, bottom) for top, bottom, text in ocr_lines(book, page) for c in norm(text)]
    if not o_chars:
        return ["no local OCR for this page"]
    t_text, o_text = "".join(c for c, _ in t_chars), "".join(c for c, *_ in o_chars)
    found = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, t_text, o_text, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        j_near = min(j1, len(o_chars) - 1)
        top = min((o_chars[j][1] for j in range(j1, j2)), default=o_chars[j_near][1])
        bottom = max((o_chars[j][2] for j in range(j1, j2)), default=o_chars[j_near][2])
        line = t_chars[min(i1, len(t_chars) - 1)][1] if t_chars else 0
        band = f"{max(0.0, top - BAND_PAD):.2f},{min(1.0, bottom + BAND_PAD):.2f}"
        found.append(
            f"line {line} band {band} | transcript: {t_text[max(0, i1 - 4):i1]}[{t_text[i1:i2][:40]}]{t_text[i2:i2 + 4]}"
            f" | ocr: [{o_text[j1:j2][:40]}]"
        )
    return found


def table_rows(markdown: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    for html in re.findall(r"<table.*?</table>", markdown, re.DOTALL):
        rows = [re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.DOTALL) for r in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)]
        tables.append([[cell_text(c) for c in r] for r in rows if r])
    block: list[list[str]] = []
    for line in [*markdown.splitlines(), ""]:
        if line.strip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            if not all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells):
                block.append([cell_text(c) for c in cells])
        elif block:
            tables.append(block)
            block = []
    return tables


def cell_text(cell: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", re.sub(r"<[^>]+>", "", cell)))


def table_diff(transcript: list[list[str]], scan: list[list[str]]) -> list[str]:
    t_cells, s_cells = max(map(len, transcript), default=0), max(map(len, scan), default=0)
    out = [f"shape: transcript {len(transcript)} rows x {t_cells} cells, scan {len(scan)} rows x {s_cells} cells"]
    unpaired = list(range(len(transcript)))
    for s_row in scan:
        label = s_row[0] if s_row else ""
        match = next((i for i in unpaired if transcript[i][:1] == [label]), None)
        if match is None:
            out.append(f"row only in scan: {' | '.join(s_row)}")
            continue
        unpaired.remove(match)
        if diffs := cell_diffs(transcript[match], s_row):
            out.append(f"row {label!r}: " + "; ".join(diffs))
    out += [f"row only in transcript: {' | '.join(transcript[i])}" for i in unpaired]
    return out


def cell_diffs(t_row: list[str], s_row: list[str]) -> list[str]:
    diffs = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, t_row, s_row, autojunk=False).get_opcodes():
        if op == "replace":
            diffs.append(f"col {j1 + 1}: transcript {' | '.join(t_row[i1:i2])!r} scan {' | '.join(s_row[j1:j2])!r}")
        elif op == "insert":
            diffs.append(f"col {j1 + 1}: missing {' | '.join(s_row[j1:j2])!r}")
        elif op == "delete":
            diffs.append(f"col {j1 + 1}: extra {' | '.join(t_row[i1:i2])!r}")
    return diffs


def tally(book: str) -> Tally:
    t = Tally(set(transcript_pages(book)), set(), set(), Counter(), [])
    for path in sorted((RESULTS / book).glob("p*.jsonl")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                record = json.loads(line)
                page, issues = int(record["page"]), record["issues"]
                kinds = [i["kind"] for i in issues]
            except (ValueError, KeyError, TypeError) as error:
                t.bad_lines.append(f"{path}:{n}: {error}")
                continue
            if unknown := [k for k in kinds if k not in KINDS]:
                t.bad_lines.append(f"{path}:{n}: unknown kind {unknown}")
            t.checked.add(page)
            t.kinds.update(kinds)
            if issues:
                t.issue_pages.add(page)
    return t


def chunks(t: Tally, book: str, size: int) -> list[tuple[str, int, int]]:
    todo = sorted(t.pages - t.checked)
    return [(book, todo[i], todo[min(i + size, len(todo)) - 1]) for i in range(0, len(todo), size)]


def check_chunk(book: str, first: int, last: int, model: str) -> str:
    (RESULTS / book / "png").mkdir(parents=True, exist_ok=True)
    log = RESULTS / "logs" / f"{book}_{first}-{last}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    prompt = f"Follow this runbook with BOOK={book} FIRST={first} LAST={last}."
    with log.open("w", encoding="utf-8") as out:
        code = subprocess.run(
            ["omp", "-p", "--no-session", "--model", model, "@docs/page-check.md", prompt],
            stdout=out, stderr=subprocess.STDOUT, timeout=3600, check=False,
        ).returncode
    tail = log.read_text(encoding="utf-8").strip().splitlines()[-1:] or [""]
    return f"{book} {first}-{last}: exit {code}, {tail[0][:120]}"


def ranges(pages: list[int]) -> str:
    spans: list[list[int]] = []
    for p in pages:
        if spans and p == spans[-1][1] + 1:
            spans[-1][1] = p
        else:
            spans.append([p, p])
    return ",".join(f"{a}" if a == b else f"{a}-{b}" for a, b in spans)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("text", "suspects", "cells", "tablediff"):
        p = sub.add_parser(name)
        p.add_argument("book", help="a book number from 1 to 6, or a folder name under books/")
        p.add_argument("page", type=int)
        if name == "tablediff":
            p.add_argument("table", type=int, help="table number on the page, from 1, as `cells` prints it")
            p.add_argument("scan_tsv", type=Path, help="the scan's table, one row per line, cells split by tabs")
    for name in ("summary", "chunks", "run"):
        p = sub.add_parser(name)
        p.add_argument("--books", default="1,2,3,4,5,6", help="comma-separated book numbers")
        p.add_argument("--size", type=int, default=10, help="pages per chunk")
        p.add_argument("--jobs", type=int, default=8, help="omp agents at once")
        p.add_argument("--model", default="gemini-3.8-flash")
    args = parser.parse_args()

    if args.command in ("text", "suspects", "cells", "tablediff") and not transcript_path(args.book, args.page).exists():
        print(f"page {args.page} has no transcript; skip it")
        return
    if args.command == "text":
        lines = transcript_path(args.book, args.page).read_text(encoding="utf-8").splitlines()
        print("\n".join(f"{n:4d}  {line}" for n, line in enumerate(lines, 1)))
        return
    if args.command == "suspects":
        print("\n".join(suspects(args.book, args.page)) or "none")
        return
    if args.command in ("cells", "tablediff"):
        tables = table_rows(transcript_path(args.book, args.page).read_text(encoding="utf-8"))
        if args.command == "cells":
            for k, rows in enumerate(tables, 1):
                print(f"table {k}: {len(rows)} rows")
                print("\n".join("\t".join(r) for r in rows))
            print(f"{len(tables)} tables" if tables else "no tables")
            return
        scan = [[cell_text(c) for c in line.split("\t")] for line in args.scan_tsv.read_text(encoding="utf-8").splitlines() if line.strip()]
        print("\n".join(table_diff(tables[args.table - 1], scan)))
        return

    books = args.books.split(",")
    if args.command == "run":
        todo = [chunk for book in books for chunk in chunks(tally(book), book, args.size)]
        print(f"{len(todo)} chunks, {args.jobs} at a time, logs in {RESULTS / 'logs'}", flush=True)
        with ThreadPoolExecutor(args.jobs) as pool:
            for line in pool.map(lambda c: check_chunk(*c, args.model), todo):
                print(line, flush=True)
        return
    for book in books:
        t = tally(book)
        if args.command == "chunks":
            for chunk in chunks(t, book, args.size):
                print(*chunk)
            continue
        missing = sorted(t.pages - t.checked)
        print(
            f"book {book}: {len(t.checked & t.pages)}/{len(t.pages)} pages checked, "
            f"{len(t.issue_pages)} with issues, {sum(t.kinds.values())} issues {dict(t.kinds.most_common())}"
        )
        if missing:
            print(f"  unchecked: {ranges(missing)}")
        for bad in t.bad_lines:
            print(f"  bad line {bad}")


if __name__ == "__main__":
    main()
