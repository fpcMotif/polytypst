# Book heading hooks stay in Python

Books 1, 3, 4 and 6 each keep a `heading_hook` written in Python in their `hooks.py`. Their heading rules do not move into `book.toml` as data. The shared Chinese heading policy is already in `PageCleaner._normalized_heading` (`src/compiler/page_cleaner.py`). It maps number shapes to heading levels and drops a heading that repeats within one chapter. Books 2 and 5 have no heading hook and use that policy alone. Each hook adds only rules for its own book: it drops chapter titles and subtitles, keeps bylines and table titles as text, and marks false headings found in that book's transcript.

## Considered Options

- **Heading policy as `book.toml` tables, read by the cleaner.** An architecture review on 2026-11-09 proposed this. Its reasons were that four hooks read `book.toml` again, check running heads again, map number shapes again, and that book 6 copies book 1's false heading `2 NIES`. A deletion test rendered each book with one rule removed. The running-head check gave byte-identical output in all four books, because `_is_page_furniture` drops those lines before the hook sees them. `2 NIES` gave byte-identical output in books 1 and 6, because no transcript line matches it. After the hooks moved to `hooks.py`, two heading fixes landed, one in book 3 and one in book 4. Neither had to be copied to another hook. The tables would need fields for false headings, bylines, drop lists, level shapes, a word joiner and a fallback level. Only these four books would fill them. Bourbaki and Fichtenholz use the same `heading_hook` seam for other languages and would not fit the tables.

## Consequences

The hooks no longer check running heads, and they keep only false headings that match a heading line in their own transcript store. Deleting the other rules left the rendered editions of books 1 to 6 byte-identical. A fresh OCR run can print a deleted line as a heading again. The page check then finds it, and the rule can come back in that book's hook.

A new Chinese book gets the cleaner's heading policy with no hook. It needs a `heading_hook` only for rules that hold in that one book. A rule that two or more books need belongs in `_normalized_heading`, not in a hook or in a new `book.toml` table.
