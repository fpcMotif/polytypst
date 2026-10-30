# Page check: run, verify and fix

You run the page check of one book and verify each issue that the checking agents record. Then you fix the real ones in the book, and record each verdict. The checking agents follow `docs/page-check.md`, one agent for each range of pages. Their issues are claims: in the first Book 4 run, 40 of 177 were false. An issue reaches the book only after a verifier read its zoom.

Run every command from `/Users/martinfan/devv/polytypst.mixed`. `BOOK` is the book number, such as `4`. `KEY` is the folder name under `books/`, such as `4_不良债权与金融危机`. `CHECK` is `output/page_check/BOOK/`.

## Step 1. Run the checking agents

```bash
uv run python scripts/page_check.py run --books BOOK
uv run python scripts/page_check.py summary --books BOOK
```

`run` starts one `omp` agent for each range of 10 unchecked pages, 8 agents at a time. Run it in the background. Run it again for the pages that `summary` lists as `unchecked`.

Done when `summary` lists no `unchecked` page and no `bad line`.

## Step 2. Verify every issue

Give each issue to a verifier subagent that reads its zoom. Use Sonnet, with about 30 issues for each subagent. Give the subagent each issue as it is in `CHECK/p*.jsonl`, with the path of the page PNG and of the zoom. The verifier decides one verdict for each issue:

| Verdict | The zoom shows |
|---|---|
| `real` | The `scan` text, and the transcript differs from it |
| `scan_typo` | A typo that the transcript copies. The verifier gives the text that makes sense |
| `false_positive` | The transcript text, or a difference of spacing or mark width only |
| `sum` | A table whose parts do not give its printed total |

The verifier reads the zoom for every verdict. A verdict from the text alone is wrong when the scan prints the typo. In Book 4, 26 text-only verdicts of `false_positive` were `scan_typo` or `real`. Check every `scan_typo` and every swap of the two sides against the zoom yourself before you fix it.

Done when every issue has a verdict that a verifier took from the zoom.

## Step 3. Fix the book

First save the audit counts, so that step 5 can compare against them:

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

## Step 4. Record the verdicts

Write one JSON line for each issue to `CHECK/verdicts.jsonl`:

```json
{"page": 12, "line": 3, "kind": "word", "transcript": "必不可少", "scan": "必不可免", "verdict": "real", "detail": "p12: scan prints 必不可免, transcript has 必不可少"}
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

Done when `verdicts.jsonl` has one line for each issue in `CHECK/p*.jsonl`.

## Step 5. Build and audit

```bash
mise exec -- uv run python scripts/one_book.py KEY build
mise exec -- uv run python scripts/one_book.py KEY audit --against "CHECK/audit_before.json"
uv run pytest -q
```

`tests/test_book_snapshots.py` compares each book spec with `tests/fixtures/book_snapshots.json`, so it fails for each new fixup. When it fails only for your fixups, write the fixture again from `snapshot()` in `tests/book_snapshot.py`.

Done when the build exits 0, no audit rule rises, the tests pass, and each fixed text is in the built `.typ` file.
