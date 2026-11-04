# Check a math book

This runbook checks one or more rebuilt math books against their scans. Each agent reads it through its own spec:

| Agent | Spec | Role |
|---|---|---|
| Claude Code | `.claude/skills/math-book-check/SKILL.md` | fixer |
| Antigravity, Gemini 4 Argon | `.agents/skills/math-book-check/SKILL.md` | editor |
| Antigravity, Gemini 3.8 Flash | `.agents/skills/math-book-check/SKILL.md` | runner |
| omp, Gemini 3.8 Flash | `docs/prompts/math-book-check-omp.md` | runner |

A role sets the files that the agent can change:

| Role | Can run | Can change |
|---|---|---|
| runner | every command in this runbook | nothing |
| editor | every command in this runbook | `$POLYTYPST_BOOKS/<key>/` transcripts, `books/<key>/book.toml` |
| fixer | every command in this runbook | also `src/`, `tests/`, `scripts/` |

## Rules for every role

- A verdict comes only from command output. Quote the output line that shows each PASS and each FAIL.
- Results, receipts and verdicts come only from `polytypst page-check` commands. Write no `p*.jsonl`, `verdicts*` or `lint.jsonl` file yourself.
- Change `quality/baseline.json`, `tests/fixtures/book_snapshots.json` and `src/checker.py` only when the user tells you to in the chat.
- If a model has no key or no quota, stop and report the log line. Use the model that the command names.
- Start a long job once, in the background, with its output in a log. Report its log path and the time it will end. `page-check run` checks about 10 pages per agent in 5 to 15 minutes.

## Steps

1. Run the harness. It runs the deterministic checks and calls no model.

   ```bash
   uv run python scripts/math_books.py BOOK... --json output/math_books.json
   ```

   Leave out BOOK to check every built math book. The table has one row per book. Stop the step when each book in your task has a row.

2. For each row, find the first FAIL line in `output/math_books.json` (`gate_fails`). Do the action for that line:

   | FAIL line starts with | Action |
   |---|---|
   | `page check: ... missing` | `uv run polytypst page-check run BOOK` in the background, then `page-check summary BOOK` |
   | `lint` | `uv run polytypst page-check lint BOOK` |
   | `verdicts: ... unverified` | `uv run polytypst page-check triage BOOK`, then `page-check verify BOOK` in the background |
   | `figures` | `uv run polytypst page-check render BOOK --pdf PDF --run`, with PDF from the row |
   | `audit: ... rose: RULE` | step 3 or step 4 for each rule after `rose:` |

   If the row shows "no store", the book has no transcript store on this machine. Report the row and go to the next book.

3. Fix or report each rule in the row's `numbering` field. Each count is a number that the book prints as typed text instead of from a counter, a label or `@ref`:

   | Rule | Meaning | Where the cause usually is |
   |---|---|---|
   | `HARDCODED_NUMBERING` | A `numbering: _ => "..."` closure or a `\renewcommand{\thefigure}{...}` prints a fixed number. | A figure number that is not `N`, `C.N` or `C-N` for chapter C, or a chapter label that is not `Word N`, a roman numeral or a capital letter |
   | `LITERAL_ITEM_HEAD` | An item or equation number is typed as text, such as `Remarque (1.6.6)`. | The item heads in `books/<key>/book.toml`, or the item writer in `src/compiler/source_numbers.py` |
   | `UNLINKED_REFERENCE`, `UNLINKED_FIGURE_REFERENCE` | A reference is typed as text although its label exists. | The reference words in `books/<key>/book.toml` |
   | `REFERENCE_WITHOUT_TARGET` | A reference names a number that has no label. | A transcript that misread the number, or an item that the transcript dropped |

   The `Resyncs` column counts the places where the scan's number differs from the counter, and the counter jumps to the scan's number. The `resyncs_file` field names the list. For each line, open the scan page and give one verdict:

   - `real`: the scan skips or repeats the number. Keep the jump.
   - `transcript`: the transcript misread the number. An editor or a fixer corrects the transcript and builds the book again.
   - `scan_typo`: the scan misprints the number. Report the line and the scan page. Change nothing.

   Only a fixer gives a `scan_typo` verdict, after a second look at the scan.

4. Fix or report each layout rule in the row's `layout` field. The rules come from `src/checker.py` and run on the rebuilt PDF:

   | Rule | Meaning | Where the cause usually is |
   |---|---|---|
   | `FONT_FALLBACK` | Text is set in a font that the book's `.typ` source does not name. | The font stack in `src/compiler/presets.py`, or a glyph that the book needs, such as ❖ or ′ |
   | `MARGIN_OVERFLOW` | Ink is more than 3pt past the text block. | A wide display, an `array`, or a diagram |
   | `UNDERFULL_PAGE` | The text stops more than 20% above the page foot, and the next page opens no chapter. | A display that cannot break, or a page break in the transcript |
   | `RUNNING_HEAD_FORMULA` | The running head is a formula. | A display that the transcript wrote as a heading |
   | `DUPLICATE_HEADING` | A heading prints twice on its page. | A title line in the transcript under the chapter heading |
   | `CONTENTS_WITHOUT_LEADERS` | A contents page shows page numbers with no dot leaders. | The contents page in the transcript |

   Before you change shared code in `src/compiler/`, prove the defect against the scan with `.claude/skills/scan-evidence/SKILL.md`.

5. Run the harness again for the books that you changed. Stop when each row shows PASS and the `numbering` field shows none. If a FAIL line stays, quote it in your report.

## Report

Give one row per book. Show the harness row before and after, the commands that you ran, each open FAIL line, and the verdict for each resync.
