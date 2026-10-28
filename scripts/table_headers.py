"""List tables whose second row the compiler will shift, because an empty cell follows a filled one.

Usage: mise exec -- uv run python scripts/table_headers.py KEY
       (KEY as in `polytypst books`, e.g. 3_国际经济环境的变化与日本经济)

The Typst table writer turns an empty cell after a filled one, in a table's first two rows,
into a colspan of the filled cell. A `rowspan="2"` header such as 自给型农户 leaves exactly
that empty cell in row 2, so 第 2 类兼业农户 spans three columns and every heading after it
moves. A first data row with blank cells, such as "| 1990 | 1.03 |  |  |", shifts the same
way. The script reads each page as the compiler does (transcript store, then the book's
cleaner and `page_fixups`), so a table already fixed prints nothing. Each line printed is a
page, the table's first row, and the row-2 cells that widen. Fix them as
`docs/scanned-books.md` "Tables" says. Loads only `books/KEY/`, like `one_book.py`.
"""

import argparse
import re

from polytypst.books import book_by_key
from polytypst.compiler.page_cleaner import PageCleaner
from polytypst.ocr.transcripts import TranscriptStore

TABLE = re.compile(r"<table>.*?</table>", re.DOTALL)
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
CELL = re.compile(r"<t[hd]([^>]*)>(.*?)</t[hd]>", re.DOTALL)
SPANNED = "\0"


def span(attrs: str, name: str) -> int:
    m = re.search(rf'{name}="(\d+)"', attrs)
    return int(m[1]) if m else 1


def first_rows(table: str) -> tuple[list[str], list[str]]:
    """The first two rows as grids: SPANNED under a colspan, "" under a rowspan from row 1 or for an empty cell."""
    grid: list[list[str]] = [[], []]
    held: set[int] = set()
    for r, row in enumerate(ROW.findall(table)[:2]):
        col = 0
        for attrs, text in CELL.findall(row):
            while r == 1 and col in held:
                grid[1].append("")
                col += 1
            text = re.sub(r"<[^>]+>", "", text).strip()
            for k in range(span(attrs, "colspan")):
                grid[r].append(text if k == 0 else SPANNED)
                if r == 0 and span(attrs, "rowspan") > 1:
                    held.add(col)
                col += 1
        while r == 1 and col in held:
            grid[1].append("")
            col += 1
    return grid[0], grid[1]


def holes(row: list[str]) -> list[int]:
    """Columns of empty cells that follow a filled cell, which the writer merges into it."""
    out, after_filled = [], False
    for i, cell in enumerate(row):
        if cell == "" and after_filled:
            out.append(i)
        elif cell not in ("", SPANNED):
            after_filled = True
    return out


def pipe_second_rows(body: str) -> list[list[str]]:
    """Row 2 of each pipe table in the cleaned page, in page order."""
    rows: list[list[str]] = []
    for block in re.findall(r"(?:^\|.*\|[ \t]*\n?)+", body, re.MULTILINE):
        lines = [
            ln
            for ln in block.strip().split("\n")
            if not re.fullmatch(r"[|\s:\-—–]+", ln)
        ]
        cells = [[c.strip() for c in ln.strip().split("|")[1:-1]] for ln in lines]
        rows.append(cells[1] if len(cells) > 1 else [])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("key")
    args = parser.parse_args()
    book = book_by_key(args.key)
    store = TranscriptStore(book.transcripts)
    cleaner = PageCleaner.for_spec(book.spec, book.out_dir)
    for path in sorted(book.transcripts.glob("p_*.md")):
        n = int(path.stem[2:])
        text = store.text(n) or ""
        tables = TABLE.findall(text)
        if not tables:
            continue
        built = pipe_second_rows(cleaner.clean(text, n)[0])
        for i, table in enumerate(tables):
            head, row2 = first_rows(table)
            cols = holes(row2)
            if i < len(built) and len(built) == len(tables):
                cols = [c for c in cols if c >= len(built[i]) or not built[i][c]]
            if cols:
                widened = sorted(
                    {
                        next(
                            row2[j]
                            for j in range(c, -1, -1)
                            if row2[j] not in ("", SPANNED)
                        )
                        for c in cols
                    }
                )
                print(
                    f"{path.stem} [{' | '.join(c for c in head if c != SPANNED)[:60]}] widens {widened}"
                )


if __name__ == "__main__":
    main()
