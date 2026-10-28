"""Build or audit one book while importing only that book's package.

Usage: mise exec -- uv run python scripts/one_book.py KEY build [--edition NAME] [--formats pdf,tex]
       mise exec -- uv run python scripts/one_book.py KEY audit [--edition NAME] [--issues RULE,...]
           [--save COUNTS.json] [--against COUNTS.json]
       mise exec -- uv run python scripts/one_book.py KEY cli COMMAND [ARGS...]

`polytypst build` and `polytypst audit` import every book, so one broken spec stops them for all
books. This script loads `books/KEY/` alone. `cli` runs any `polytypst` command, such as
`review "FOLDER" --scan "SCAN"` or `parity KEY --edition E`, with only this book loaded. `audit` prints the same counts as
`polytypst audit`. `--issues` prints each issue of the named checker rules with its page.
`--save` writes the counts, and `--against` prints each rule whose count rose or fell since a save,
so a book with no entry in quality/baseline.json still gets a before-and-after check.
Run through `mise exec` so that POLYTYPST_BOOKS names the transcript store.
"""

import argparse
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

from polytypst.books import book_by_key
from polytypst.books_cli import DOCUMENT_FORMATS, format_output
from polytypst.checker import AuditSpec, DocumentQualityChecker
from polytypst.literal_numbers import edition_literal_counts


def audit(edition, issue_rules: set[str]) -> Counter[str]:
    spec = AuditSpec.from_monograph(edition.spec) if edition.spec else AuditSpec()
    spec = replace(spec, scan_line_breaks=edition.scan_line_breaks)
    counts: Counter[str] = Counter()
    for fmt in sorted(edition.formats | {"pdf"}):
        if fmt not in DOCUMENT_FORMATS:
            continue
        path = format_output(edition, fmt)
        if not path.exists():
            print(f"missing {fmt}: {path}")
            continue
        for issue in DocumentQualityChecker(path, spec).run_all_checks().issues:
            counts[f"{DOCUMENT_FORMATS[fmt]}{issue.rule_name}"] += 1
            if issue.rule_name in issue_rules:
                print(f"{fmt} p{issue.page_num} {issue.rule_name}: {issue.context_snippet[:70]!r}")
    if edition.spec:
        counts.update(edition_literal_counts(edition.rebuilt, edition.spec))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("key", help="the folder name under books/, such as 6_劳动力市场与收入分配")
    parser.add_argument("command", choices=("build", "audit", "cli"))
    parser.add_argument("--edition", help="default: the book's first edition")
    parser.add_argument("--formats", default="pdf", help="build: comma-separated formats (default: pdf)")
    parser.add_argument("--issues", default="", help="audit: comma-separated rule names to print in full")
    parser.add_argument("--save", type=Path, help="audit: write the counts to this JSON file")
    parser.add_argument("--against", type=Path, help="audit: compare with counts saved earlier")
    split = 3 if sys.argv[2:3] == ["cli"] else len(sys.argv)
    args = parser.parse_args(sys.argv[1:split])

    book = book_by_key(args.key)
    if args.command == "cli":
        import polytypst.books
        import polytypst.books_cli

        polytypst.books.books = polytypst.books_cli.books = lambda: {args.key: book}
        from polytypst.cli import main as cli_main

        sys.argv = ["polytypst", *sys.argv[split:]]
        sys.exit(cli_main())
    name = args.edition or next(iter(book.editions))
    if args.command == "build":
        book.build(name, None, frozenset(f for f in args.formats.split(",") if f))
        return

    counts = audit(book.editions[name], {r for r in args.issues.split(",") if r})
    print(json.dumps(dict(sorted(counts.items())), indent=1, ensure_ascii=False))
    print(f"{args.key} {name}: {counts.total()} issues")
    if args.against:
        before = Counter(json.loads(args.against.read_text(encoding="utf-8")))
        for rule in sorted(set(before) | set(counts)):
            if counts[rule] != before[rule]:
                word = "rose" if counts[rule] > before[rule] else "fell"
                print(f"  {word}: {rule} {before[rule]} -> {counts[rule]}")
        print(f"  total {before.total()} -> {counts.total()}")
    if args.save:
        args.save.write_text(json.dumps(dict(sorted(counts.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
