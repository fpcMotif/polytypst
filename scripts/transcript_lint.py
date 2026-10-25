"""Find transcript lines that the compiler will misread, and notes the built Typst prints twice.

Usage: mise exec -- uv run python scripts/transcript_lint.py KEY [--check labels,notes,repeats,heads]

The checks (default: labels,notes,repeats):

- labels: a short "（1）…" or "(a) …" line on a figure's page or the page before it, after the
  spec's page fixups. It is usually a panel title that the crop already shows. Confirm with
  scripts/figure_leaks.py.
- notes: a footnote whose key is not a circled digit, in a book whose `footnote_style` is
  "circled" or empty. The splitter
  took a body line such as "(1) …" for a note. It runs before page fixups, so fix the line in
  the transcript store itself, for example "(1)" to "（1）".
- repeats: a paragraph of the built KEY's .typ that repeats the paragraph before it. Two
  identical notes in a row usually mean that the compiler moved one note away from its figure,
  as it does with two figures in a row that each have a note above the caption.
- heads: every numbered line and what the spec's heading hook makes of it. '' drops the line,
  None keeps it as text, and anything else is the heading it becomes. Use it after a change to
  the hook or to its running-head regexes.
"""

import argparse
import re
from importlib import import_module

from polytypst.compiler.page_cleaner import CIRCLED_DIGITS, split_page_footnotes
from polytypst.ocr.transcripts import TranscriptStore
from polytypst.vision.figure_extractor import load_figures_manifest

LABEL = re.compile(r"^[（(]([1-9]|[a-h])[）)]\s*(.{1,40})$")
NUMBERED = re.compile(r"^(?:#+\s*)?\d{1,2}(?:\.\d{1,2})?\s+\S")


def pages(store: TranscriptStore, spec=None):
    """Each page's transcript, after the spec's page fixups when `spec` is given."""
    for path in sorted(store.directory.glob("p_*.md")):
        number = int(path.stem[2:])
        text = store.text(number) or ""
        for pattern, repl in spec.page_fixups.get(number, ()) if spec else ():
            text = re.sub(pattern, repl if re.search(r"\\[1-9]|\\g<", repl) else lambda _, r=repl: r, text, flags=re.DOTALL)
        yield number, text


def labels(book, store: TranscriptStore) -> None:
    figure_pages = {f.source_page for f in load_figures_manifest(book.out_dir / "figures_manifest.json")}
    for number, text in pages(store, book.spec):
        if not {number, number + 1} & figure_pages:
            continue
        for i, line in enumerate(line.strip() for line in text.splitlines()):
            if LABEL.match(line) and not line.endswith(("。", "；", "，")):
                print(f"labels p{number} L{i}: {line}")


def notes(book, store: TranscriptStore) -> None:
    spec = book.spec
    if spec.footnote_style not in ("", "circled"):
        print(f"notes: skipped, the book's notes are {spec.footnote_style}")
        return
    for number, text in pages(store):
        _, found = split_page_footnotes(text, "circled", spec.folio_pattern)
        for key, note in found:
            if key not in CIRCLED_DIGITS:
                print(f"notes p{number}: key {key!r} {note[:40]}")


def repeats(book, _store: TranscriptStore) -> None:
    typ = book.out_dir / f"{book.spec.slug}.typ"
    paras = [p.strip() for p in re.split(r"\n\s*\n", typ.read_text(encoding="utf-8")) if p.strip()]
    for i, para in enumerate(paras):
        if len(para) < 6 or para.startswith(("#", "]", ")", "[")):
            continue
        if i and paras[i - 1] == para:
            print(f"repeats para {i}: {para[:80]}")


def heads(book, store: TranscriptStore) -> None:
    hook = book.spec.heading_hook
    if hook is None:
        print("heads: skipped, the spec has no heading hook")
        return
    chapter_of = {p: c.number for c in book.spec.chapters for p in range(c.start_page, c.end_page + 1)}
    for number, text in pages(store):
        chapter = chapter_of.get(number, 0)
        for i, line in enumerate(line.strip() for line in text.splitlines()):
            if NUMBERED.match(line) and (line.startswith("#") or len(line) <= 40):
                print(f"heads p{number} c{chapter} L{i} {hook(line, chapter)!r:40.40} | {line[:60]}")


CHECKS = {"labels": labels, "notes": notes, "repeats": repeats, "heads": heads}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("key", help="the folder name under src/, such as 6_劳动力市场与收入分配")
    parser.add_argument("--check", default="labels,notes,repeats", help=f"comma-separated, from {','.join(CHECKS)}")
    args = parser.parse_args()

    book = import_module(f"polytypst.{args.key}.book").BOOK
    store = TranscriptStore(book.transcripts)
    for name in args.check.split(","):
        CHECKS[name](book, store)


if __name__ == "__main__":
    main()
