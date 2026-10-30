# Page check: run, verify and fix

You check one book for transcript errors and scan typos. Then you fix the real ones in the book, and record each verdict. Two sources make claims. `lint` matches error classes that earlier books confirmed, in seconds. The checking agents follow `docs/page-check.md`, one agent for each range of pages. Each claim reaches the book only after a verifier read its zoom: in the first Book 4 run, 40 of 177 agent issues were false.

Run every command from `/Users/martinfan/devv/polytypst.mixed`. `BOOK` is a book number from 1 to 6, or the folder name of any other book under `books/`. `KEY` is the folder name under `books/`, such as `4_不良债权与金融危机`. `CHECK` is `output/page_check/BOOK/`.

`status` prints each stage's counts and the commands that are due:

```bash
uv run python scripts/book_check.py status BOOK
```

## Step 1. Lint the transcript

```bash
uv run python scripts/book_check.py lint BOOK
```

`lint` reads each transcript page with the book's fixups applied, and the built `.typ` file. It writes `CHECK/lint.jsonl`. Its rules:

| Rule | Finds | Confirmed in |
|---|---|---|
| `glued_words` | English words without a space, such as `forHuman` | Book 4 p88, Book 5 p264 |
| `broken_tag` | A table tag with a space, such as `</ tr>` | Book 4 p79 |
| `spaced_decimal` | A number with a space before its point, such as `-0 .4%` | Book 4 p349 |
| `lone_book_mark` | A 《 or 》 without its pair in the paragraph or across the page break | Book 4 p115 |
| `running_head` | A running head, such as `120 不良债权与金融危机`, in the built text | Book 4 p120 |

When a verifier confirms a new class of error in two places, add a rule for it to `scripts/book_check.py` with a test in `tests/test_book_check.py`.

Done when `CHECK/lint.jsonl` exists.

## Step 2. Run the checking agents

```bash
uv run python scripts/page_check.py run --books BOOK
uv run python scripts/page_check.py summary --books BOOK
```

`run` starts one `omp` agent for each range of 10 unchecked pages, 8 agents at a time. Run it in the background. Run it again for the pages that `summary` lists as `unchecked`. When the Gemini quota is out, `omp` exits 0 with a 429 error in the log, and the range stays unchecked.

Done when `summary` lists no `unchecked` page and no `bad line`.

## Step 3. Verify every claim

```bash
uv run python scripts/book_check.py triage BOOK
uv run python scripts/book_check.py verify BOOK
```

`triage` settles two kinds of claim as `false_positive` with `"by": "auto"`: two sides that differ only in character width or in spaces next to Chinese text, and an `extra_text` claim on the book's running head. The page cleaner drops running heads, and `lint` finds any that stay in the built book. For each other claim, it cuts a 300 dpi zoom of the scan at the claim's line and a page image. It writes the claims to `CHECK/queue.jsonl`. Run it again after `lint` or the checking agents add claims.

`verify` starts one Sonnet agent for each batch of 30 queued claims, 4 at a time. Each agent follows `docs/page-verify.md` and reads the images. `verify` adds their verdicts to `CHECK/verdicts.jsonl`. A batch whose output exists does not run again. The verdicts:

| Verdict | The zoom shows |
|---|---|
| `real` | The `scan` text, and the transcript differs from it |
| `scan_typo` | A typo, and the transcript lacks the text that makes sense. The verifier gives that text |
| `false_positive` | The transcript text, a scan typo that the transcript already corrects, or a difference of spacing or mark width only |
| `sum` | A table whose parts do not give its printed total |
| `unsure` | Neither image shows the place. `verify` leaves the claim unverified, for you to decide |

A verdict from the text alone is wrong when the scan prints the typo. In Book 4, 26 text-only verdicts of `false_positive` were `scan_typo` or `real`. Check every `scan_typo` and every swap of the two sides against the zoom yourself before you fix it.

Done when `status` shows 0 unverified.

## Step 4. Fix the book

First save the audit counts, so that step 6 can compare against them:

```bash
mise exec -- uv run python scripts/one_book.py KEY audit --save "CHECK/audit_before.json"
```

Fix each `real` and `scan_typo` issue in `books/KEY/book.toml`. Put a one-line comment above each rewrite:

- `# Scan typo: the scan prints X; meant Y.`
- `# The transcript has X; the scan prints Y.`

Choose the table by where the text is on the page:

| The text is in | Fix it in |
|---|---|
| The body text or a table | `[page_fixups]`, which rewrite the page after the cleaner |
| A figure caption, the notes under a figure, or a footnote | `[transcript_fixups]`, which rewrite the transcript before the cleaner takes these parts out of the page |
| The title of a chart that the build draws again | The chart's script in `scripts/bookN_figures/`, and the caption fixup |

Each table maps a scan page to a list of `[pattern, replacement]` pairs. `docs/scanned-books.md` describes both tables.

When you find an error that no issue named, it is a false negative. Fix it in the same way, and start its comment with `False negative (the page check missed it):`.

Done when each `real` and each `scan_typo` issue has a rewrite with its comment.

## Step 5. Record the verdicts

`triage` and `verify` write `CHECK/verdicts.jsonl`. For each claim that you decide yourself, such as an `unsure` one, add one JSON line. Copy `page`, `kind`, `transcript` and `scan` from the claim, because they match the verdict to its claim:

```json
{"page": 12, "line": 3, "kind": "word", "transcript": "必不可少", "scan": "必不可免", "verdict": "real", "detail": "p12: scan prints 必不可免, transcript has 必不可少", "by": "person"}
```

Write one JSON line for each false negative to `CHECK/false_negatives.jsonl`:

```json
{"page": 349, "kind": "table_cell", "transcript": "-0 .4%", "scan": "-0.4%", "fixed_by": "book.toml [page_fixups] 349", "note": "不良债权调整 row"}
```

Give `fixed_by` as `""` for a false negative that you did not fix. The false-positive rate is the count of `false_positive` verdicts divided by the count of verdicts other than `sum`.

To show the scan typos or the real issues to a person, build a sheet of scan strips. Each card is one line cut from the scan at 300 dpi:

```bash
uv run python scripts/scan_sheet.py BOOK --scan "SCAN" --verdicts scan_typo > "CHECK/scan_typos.html"
```

`--verdicts real` shows the transcript errors. For a hand-picked set with notes, write one JSON line for each card and pass `--cases FILE` instead. `CHECK/scan_typos.jsonl` for Book 4 is an example. The command names each card that it cannot place on stderr. Give that card a `band`.

Done when `status` shows 0 unverified.

## Step 6. Build and audit

```bash
mise exec -- uv run python scripts/one_book.py KEY build
mise exec -- uv run python scripts/one_book.py KEY audit --against "CHECK/audit_before.json"
uv run pytest -q
```

`tests/test_book_snapshots.py` compares each book spec with `tests/fixtures/book_snapshots.json`, so it fails for each new fixup. When it fails only for your fixups, write the fixture again from `snapshot()` in `tests/book_snapshot.py`. Then run `lint` again: a fixed error leaves `lint.jsonl`, because `lint` reads each page with its fixups.

Done when the build exits 0, no audit rule rises, the tests pass, and each fixed text is in the built `.typ` file.
