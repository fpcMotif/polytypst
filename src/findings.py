"""`polytypst findings`: look up review findings by id, book, cause, severity, status or text, each with its verdict."""

import argparse
import json
from pathlib import Path
from typing import Any

from .corrections import QUALITY
from .paths import OUTPUT

FINDINGS = OUTPUT / "review_findings.jsonl"
VERDICTS = QUALITY / "verdicts.jsonl"


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="polytypst findings",
        description="Show review findings, each with its verdict when quality/verdicts.jsonl holds one. "
        "Every filter given must match. `polytypst corrections show BOOK` lists a book's fixes.",
    )
    parser.add_argument("ids", nargs="*", help="finding ids, such as Bkashiwara-235 or X-01")
    parser.add_argument("--book", help="book key, such as kashiwara")
    parser.add_argument("--cause", help="shared root cause id, such as RC-06")
    parser.add_argument("--severity", choices=["P0", "P1", "P2", "P3"])
    parser.add_argument("--status", choices=["open", "fixed", "wontfix"])
    parser.add_argument("--match", help="text that the finding's where, what or evidence holds, case-insensitive")
    parser.add_argument("--file", type=Path, default=FINDINGS, help=f"findings JSONL (default: {FINDINGS})")
    parser.add_argument("--verdicts", type=Path, default=VERDICTS, help=f"verdicts JSONL (default: {VERDICTS})")
    args = parser.parse_args(argv)
    if not args.file.exists():
        print(f"{args.file} does not exist; `scripts/look_review.py merge` writes it")
        return 1
    rows = _rows(args.file)
    if missing := sorted(set(args.ids) - {r["id"] for r in rows}):
        print(f"no finding with id {', '.join(missing)} in {args.file}")
        return 1
    verdicts = {v["id"]: v for v in _rows(args.verdicts)} if args.verdicts.exists() else {}
    text = (args.match or "").casefold()
    chosen = [
        r
        for r in rows
        if (not args.ids or r["id"] in args.ids)
        and (args.book is None or r["book"] == args.book)
        and (args.cause is None or r.get("cause_id") == args.cause)
        and (args.severity is None or r["severity"] == args.severity)
        and (args.status is None or r.get("status", "open") == args.status)
        and text in f"{r['where']}\n{r['what']}\n{r['evidence']}".casefold()
    ]
    for r in chosen:
        cause = f" {r['cause_id']}" if r.get("cause_id") else ""
        print(f"{r['id']} {r['book']} {r['severity']} {r['format']} {r.get('status', 'open')}{cause}")
        print(f"    where: {r['where']}\n    what: {r['what']}\n    evidence: {r['evidence']}")
        if v := verdicts.get(r["id"]):
            print(
                f"    verdict {v['verdict']} scan p{v['scan_page']}: scan reads {v['scan_reads']!r}, "
                f"transcript {v['transcript_reads']!r}"
            )
    print(f"{len(chosen)} finding{'' if len(chosen) == 1 else 's'}")
    return 0
