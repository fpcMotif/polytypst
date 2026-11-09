# Look review of one page group

`scripts/look_review.py brief BOOK GROUP` fills in this prompt for one checking agent. Do not edit the filled copy by hand.

You check rebuilt pages {first} to {last} of `{book}` against the scan at the publisher bar. You only read and write two files.

## Read first

1. `docs/publisher-bar.md`. Rule 0: the book's own scan wins. Do not call a FAIL when the scan has the same design.
2. `docs/prompts/math-book-check.md`, step 5 (the look table).

## Pages

Open each rebuilt PNG and each of its scan PNGs with the Read tool. Paths are relative to `{review}`. The overflow is already measured by the checker, so do not measure it again. A page with `overflow_pt` above 3 fails the overflow check.

{pages}

A page with no scan page shares no text with any transcript page, as a contents page or a page that lost its text does. Open the scan pages of the pages before and after it, and say in `where` which scan page you compared.

To read a small region at 300 dpi, run `uv run python scripts/page_png.py PDF PREFIX --pages N --dpi 300 --clip L,T,R,B`. The rebuilt PDF is `{rebuilt}` and the scan is `{scan}`. Write crops only under `{review}/crops/`.

## Checks

Be harsh and strict. A page passes only when it has no defect. A doubt is a FAIL with evidence. Check in this order:

1. Looks: chapter openings (a "CHAPTER N" line under the title, a doubled "§ N. §N.", a chapter title on the page that ends the previous chapter), heading hierarchy, running heads and folios, the index (entries merged into paragraphs, missing entries), tables (the first data row set as a header, scattered cells), widows, orphans, hyphenated headings, and spacing rules of the book's language.
2. Figures: a raster crop where a vector drawing belongs, raw label text such as `T_{{f(x)}}`, doubled captions, and commutative diagrams set as arrays.
3. Numbering: numbers typed as text, gaps or doubles against the scan, equation numbers missing although the text cites them, and equation numbers off the right margin.
4. Content: lost or wrong math (dropped bars, accents, sum signs, wrong indices), lost paragraphs, and footnotes left in the body.
5. Overflow: from `overflow_pt` above.

## Write

Write exactly two files:

- `{review}/group_{group:02d}.jsonl`: one finding per line, valid JSON, with the fields of `docs/reviewing-books.md` step 6. Set `id` to `"TBD"` and `book` to `"{book}"`. Put the rebuilt page, the scan page and the transcript `p_NNN.md:line` when known in `where`. Add `cause`: `transcript`, `book.toml`, or `src/compiler` with the file and function. Write one finding for a defect that repeats on several pages, and list the pages in `where`.
- `{review}/group_{group:02d}.audit.jsonl`: one line per page {first} to {last}, as `{{"page": N, "scan_pages": [..], "result": "PASS" or "FAIL", "checks": {{"looks": .., "figures": .., "numbering": .., "content": .., "overflow": ..}}, "overflow_pt": X}}`. Each check is `PASS`, `FAIL` or `N/A`.

Run `uv run python scripts/look_review.py check {book} {group}`. It must print `ok`. Fix the lines it names.

Reply with one line: the count of findings by severity.
