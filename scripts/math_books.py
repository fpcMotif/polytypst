"""Check every built math book with the deterministic checks and print one table that any agent can act on.

Usage: uv run python scripts/math_books.py [KEY...] [--json OUT]
"""

import argparse
import json
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from polytypst.book_state import BookStateError
from polytypst.books import books, newest_input
from polytypst.edition_audit import EditionAudit, EditionNotBuilt, audit_edition
from polytypst.figure_counts import figure_counts
from polytypst.page_check import PageCheck
from polytypst.page_check.verify import gate, progress

LAYOUT_RULES = ("FONT_FALLBACK", "MARGIN_OVERFLOW", "UNDERFULL_PAGE", "RUNNING_HEAD_FORMULA", "RUNNING_HEAD_CROWDED", "CHAPTER_OPENING_NO_FOLIO", "DUPLICATE_HEADING", "CONTENTS_WITHOUT_LEADERS", "HYPHENATED_HEADING")
CJK_LANGS = ("zh", "ja", "ko")
HIT_SAMPLE = 5


def transcript_script(pages: Path) -> str:
    text = "".join(page.read_text(encoding="utf-8") for page in pages.glob("p_*.md"))
    wide = sum(unicodedata.east_asian_width(c) in "WF" for c in text)
    latin = sum(c.isascii() and c.isalpha() for c in text)
    return "cjk" if wide > 0.15 * (wide + latin) else "latin"


def script_mismatch(transcripts: Path, lang: str) -> str | None:
    """A FAIL line when the store's text is not in the script that `lang` names, else None."""
    script = transcript_script(transcripts)
    if script != ("cjk" if lang.split("_")[0] in CJK_LANGS else "latin"):
        return f"FAIL store: {transcripts} reads as {script} text, but book.toml says lang = {lang}"
    return None


def audit_fields(audit: EditionAudit) -> dict:
    """The row's layout, type and numbering fields, read from one edition audit."""
    kind = audit.type_profile
    numbering = audit.stage("source")
    return {
        "layout": {rule: n for rule, n in audit.counts.items() if rule in LAYOUT_RULES},
        "type": {"script": kind.script, "cpl": kind.cpl, "pitch": kind.pitch, "ok": kind.ok} if kind else {},
        "numbering": {rule: len(hits) for rule, hits in numbering.items()},
        "numbering_hits": {rule: [hit.line for hit in hits[:HIT_SAMPLE]] for rule, hits in numbering.items()},
    }


def check_book(key: str, book, name: str) -> dict:
    edition = book.editions[name]
    row: dict = {"book": key, "pdf": str(edition.rebuilt)}
    built = edition.rebuilt.stat().st_mtime
    row["built"] = datetime.fromtimestamp(built).strftime("%Y-%m-%d")
    row["stale"] = built < newest_input(key)
    try:
        store, problem = book.transcripts, None
    except BookStateError as error:
        store, problem = None, f"FAIL store: {error}"
    if store and not store.is_dir():
        store = None
    if store:
        problem = script_mismatch(store, edition.spec.lang)
        store = None if problem else store
    row["store"] = str(store) if store else None
    if problem:
        row |= {"gate": problem, "gate_fails": [problem]}
    if store:
        check = PageCheck.named(key)
        done = progress(check)
        lines = gate(check)
        row |= {
            "checked": f"{done.checked}/{done.pages}",
            "issues": done.issues,
            "unverified": done.unverified,
            "next": done.next,
            "gate": lines[-1],
            "gate_fails": [line for line in lines if line.startswith("FAIL ")],
        }
    try:
        row |= audit_fields(audit_edition(book, name))
    except EditionNotBuilt as error:
        row |= {"layout": {}, "type": {}, "numbering": {}, "numbering_hits": {}}
        row.setdefault("gate_fails", []).append(f"FAIL audit: {error}")
        row.setdefault("gate", f"FAIL audit: {error}")
    typ = edition.source("typ")
    row["figures"] = dict(figure_counts(typ.read_text(encoding="utf-8"))) if typ.exists() else None
    if any(line.startswith("FAIL audit") for line in row.get("gate_fails", [])):
        row.setdefault("next", []).append(f"uv run polytypst audit {key} --hits")
    resyncs = book.out_dir / f"{edition.spec.slug}-numbering-resyncs.txt"
    row["resyncs"] = len(resyncs.read_text(encoding="utf-8").splitlines()) if resyncs.exists() else None
    row["resyncs_file"] = str(resyncs) if resyncs.exists() else None
    return row


def math_books(keys: list[str]) -> list[tuple[str, object, str]]:
    found = []
    for key, book in books().items():
        name = next(iter(book.editions))
        edition = book.editions[name]
        if (keys and key not in keys) or edition.spec is None or edition.spec.domain != "math" or not edition.rebuilt.exists():
            continue
        found.append((key, book, name))
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
        gate = "no store" if not r["store"] and not r.get("gate_fails") else "PASS" if r["gate"] == "PASS" else (r["gate_fails"] or [r["gate"]])[0][:70]
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
