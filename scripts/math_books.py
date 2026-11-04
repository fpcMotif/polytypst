"""Check every built math book with the deterministic checks and print one table that any agent can act on.

Usage: uv run python scripts/math_books.py [KEY...] [--json OUT]
"""

import argparse
import itertools
import json
import os
import re
import statistics
import subprocess
import sys
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from polytypst.books import book_folders, books
from polytypst.checker import LAYOUT_TIER, AuditSpec, DocumentQualityChecker
from polytypst.figure_counts import figure_counts
from polytypst.literal_numbers import edition_literal_counts

LAYOUT_RULES = ("FONT_FALLBACK", "MARGIN_OVERFLOW", "UNDERFULL_PAGE", "RUNNING_HEAD_FORMULA", "DUPLICATE_HEADING", "CONTENTS_WITHOUT_LEADERS", "HYPHENATED_HEADING")
TYPE_TARGETS = {"latin": ((45, 80), (1.15, 1.5)), "cjk": ((50, 90), (1.4, 1.8))}
CHECKED_RE = re.compile(r"page check: (\d+)/(\d+) pages, (\d+) issues")
UNVERIFIED_RE = re.compile(r"(\d+) unverified")


def store_roots() -> list[Path]:
    roots = [Path(os.environ["POLYTYPST_BOOKS"]).expanduser()] if os.environ.get("POLYTYPST_BOOKS") else []
    return roots + sorted(REPO.parent.glob("polytypst-store-*")) + [REPO.parent / "polytypst-books"]


def store_for(out_dir: Path) -> Path | None:
    return next((root for root in store_roots() if (root / out_dir.name).is_dir()), None)


def page_check(command: str, key: str, store: Path) -> list[str]:
    env = {**os.environ, "POLYTYPST_BOOKS": str(store)}
    done = subprocess.run(
        ["uv", "run", "polytypst", "page-check", command, key], cwd=REPO, env=env, capture_output=True, text=True, check=False
    )
    return [line for line in (done.stdout + done.stderr).splitlines() if line.strip() and not line.startswith("Bytecode")]


def layout_counts(edition) -> dict[str, int]:
    spec = AuditSpec.from_monograph(edition.spec)
    issues = DocumentQualityChecker(edition.rebuilt, spec).run_all_checks(frozenset({LAYOUT_TIER})).issues
    return dict(Counter(i.rule_name for i in issues if i.rule_name in LAYOUT_RULES))


def newest_input(key: str) -> float:
    inputs = [*(REPO / "src" / "compiler").rglob("*.py"), *book_folders()[key].rglob("*")]
    return max(path.stat().st_mtime for path in inputs if path.is_file())


def type_profile(edition) -> dict:
    checker = DocumentQualityChecker(edition.rebuilt, AuditSpec.from_monograph(edition.spec))
    body = checker._body_size
    widths, pitches, cjk = [], [], 0
    for pno in range(checker.spec.front_matter_pages, len(checker.doc)):
        frame = checker._text_block.get((pno + 1) % 2)
        if not frame or body is None:
            continue
        left, right = frame
        lines = [
            (r, spans)
            for r, spans in sorted(checker._body_line_spans(pno), key=lambda line: line[0].y0)
            if abs(statistics.mean(s["size"] for s in spans) - body) < 0.3 and not any("Math" in s["font"] for s in spans)
        ]
        for (upper, spans), (lower, _) in itertools.pairwise(lines):
            if upper.x0 < left + 2 and upper.x1 > right - 2:
                text = "".join(s["text"] for s in spans).strip()
                wide = [unicodedata.east_asian_width(c) in "WF" for c in text]
                cjk += 2 * sum(wide) > len(text)
                widths.append(len(text) + sum(wide))
                if 0.9 * body < lower.y0 - upper.y0 < 2.5 * body:
                    pitches.append((lower.y0 - upper.y0) / body)
    if not widths or not pitches:
        return {}
    script = "cjk" if 2 * cjk > len(widths) else "latin"
    cpl, pitch = round(statistics.median(widths)), round(statistics.median(pitches), 2)
    (cpl_lo, cpl_hi), (pitch_lo, pitch_hi) = TYPE_TARGETS[script]
    return {"script": script, "cpl": cpl, "pitch": pitch, "ok": cpl_lo <= cpl <= cpl_hi and pitch_lo <= pitch <= pitch_hi}


def check_book(key: str, book, edition) -> dict:
    row: dict = {"book": key, "pdf": str(edition.rebuilt)}
    built = edition.rebuilt.stat().st_mtime
    row["built"] = datetime.fromtimestamp(built).strftime("%Y-%m-%d")
    row["stale"] = built < newest_input(key)
    store = store_for(book.out_dir)
    row["store"] = str(store) if store else None
    if store:
        status = page_check("status", key, store)
        gate = page_check("gate", key, store)
        checked = next((m for line in status if (m := CHECKED_RE.search(line))), None)
        unverified = next((m for line in status if (m := UNVERIFIED_RE.search(line))), None)
        row |= {
            "checked": f"{checked[1]}/{checked[2]}" if checked else "?",
            "issues": int(checked[3]) if checked else None,
            "unverified": int(unverified[1]) if unverified else None,
            "next": [line.split("next:", 1)[1].strip() for line in status if "next:" in line],
            "gate": gate[-1] if gate else "no output",
            "gate_fails": [line for line in gate if line.startswith("FAIL ")],
        }
    row["layout"] = layout_counts(edition)
    row["type"] = type_profile(edition)
    typ = edition.rebuilt.with_suffix(".typ")
    row["figures"] = dict(figure_counts(typ.read_text(encoding="utf-8"))) if typ.exists() else None
    row["numbering"] = edition_literal_counts(edition.rebuilt, edition.spec)
    resyncs = book.out_dir / f"{edition.spec.slug}-numbering-resyncs.txt"
    row["resyncs"] = len(resyncs.read_text(encoding="utf-8").splitlines()) if resyncs.exists() else None
    row["resyncs_file"] = str(resyncs) if resyncs.exists() else None
    return row


def math_books(keys: list[str]) -> list[tuple[str, object, object]]:
    found = []
    for key, book in books().items():
        edition = next(iter(book.editions.values()))
        if (keys and key not in keys) or edition.spec is None or edition.spec.domain != "math" or not edition.rebuilt.exists():
            continue
        found.append((key, book, edition))
    return found


def table(rows: list[dict]) -> str:
    out = [
        "| Book | Built | Checked pages | Issues | Unverified | Gate | Numbering | Resyncs | Layout hits | Type | Figures | Next command |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        layout = ", ".join(f"{rule} {n}" for rule, n in sorted(r["layout"].items())) or "none"
        numbering = ", ".join(f"{rule} {n}" for rule, n in sorted(r["numbering"].items())) or "none"
        nxt = r["next"][0].split("#")[0].strip() if r.get("next") else ""
        kind = r["type"]
        type_cell = f"{kind['cpl']} cpl, {kind['pitch']}x{'' if kind['ok'] else ' !'}" if kind else "-"
        figs = r["figures"]
        figures_cell = (
            f"{figs['VECTOR_FIGURE']} vector, {figs['RASTER_FIGURE']} raster, {figs['DIAGRAM_AS_ARRAY']} arrays"
            + (" !" if figs["RASTER_FIGURE"] or figs["DIAGRAM_AS_ARRAY"] else "")
            if figs
            else "-"
        )
        gate = "no store" if not r["store"] else "PASS" if r["gate"] == "PASS" else (r["gate_fails"] or [r["gate"]])[0][:70]
        out.append(
            f"| {r['book']} | {r['built']}{' stale' if r['stale'] else ''} | {r.get('checked', '-')} | {r.get('issues', '-')} | {r.get('unverified', '-')} "
            f"| {gate} | {numbering} | {r['resyncs'] if r['resyncs'] is not None else '-'} | {layout} | {type_cell} | {figures_cell} | {f'`{nxt}`' if nxt else '-'} |"
        )
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys", nargs="*", help="book keys; all built math books when empty")
    parser.add_argument("--json", type=Path, help="write each book's row, with every FAIL line, to this file")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    targets = math_books(args.keys)
    with ThreadPoolExecutor(args.jobs) as pool:
        rows = list(pool.map(lambda target: check_book(*target), targets))
    print(table(rows))
    if args.json:
        args.json.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if all(r.get("gate") == "PASS" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
