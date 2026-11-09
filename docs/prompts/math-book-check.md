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

   The `Built` column shows the date of the rebuilt PDF. `stale` means that a file in `src/compiler/` or in the book's folder is newer than the PDF, so the counts describe old output. A runner reports a stale row. An editor or a fixer builds the book again with `uv run polytypst build BOOK --formats pdf,tex`, then runs the harness again.

2. For each row, find the first FAIL line in `output/math_books.json` (`gate_fails`). Do the action for that line:

   | FAIL line starts with | Action |
   |---|---|
   | `page check: ... missing` | `uv run polytypst page-check run BOOK` in the background, then `page-check summary BOOK` |
   | `lint` | `uv run polytypst page-check lint BOOK` |
   | `verdicts: ... unverified` | `uv run polytypst page-check triage BOOK`, then `page-check verify BOOK` in the background |
   | `figures` | `uv run polytypst page-check render BOOK --pdf PDF --run`, with PDF from the row |
   | `audit: ... rose: RULE` | `uv run polytypst audit BOOK --hits`, then step 3 or step 4 for each rule after `rose:` |

   The row's `next` field lists the commands that the checks print. Run them as written.

   If the row shows "no store", the book has no transcript store on this machine. Report the row and go to the next book.

3. Fix or report each rule in the row's `numbering` field. Each count is a number that the book prints as typed text, not from a counter, a label or `@ref`.

   The `numbering_hits` field shows the first 5 hits of each rule. To list every hit, run `uv run polytypst audit BOOK --hits RULE`. Each line gives the generated `.typ` or `.tex` file, the line number and the typed text. To find the transcript page, search for the words of the hit, without markup, with `rg` in `$POLYTYPST_BOOKS/<key>/markdown_pages/`.

   An editor fixes each hit in the transcript or in `books/<key>/book.toml`. If the cause is in `src/`, an editor reports the hit line and the scan page.

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

4. Fix or report each layout rule in the row's `layout` field. The rules run on the rebuilt PDF. `uv run polytypst audit BOOK --hits RULE` gives the PDF page and the message of each hit:

   | Rule | Meaning | Where the cause usually is |
   |---|---|---|
   | `FONT_FALLBACK` | Text is set in a font that the book's `.typ` source does not name. | The font stack in `src/compiler/presets.py`, or a glyph that the book needs, such as ❖ or ′ |
   | `MARGIN_OVERFLOW` | Ink is more than 3pt past the text block. | A wide display, an `array`, or a diagram |
   | `UNDERFULL_PAGE` | The text stops more than 20% above the page foot, and the next page opens no chapter. | A display that cannot break, or a page break in the transcript |
   | `RUNNING_HEAD_FORMULA` | The running head is a formula. | A display that the transcript wrote as a heading |
   | `DUPLICATE_HEADING` | A heading prints twice on its page. | A title line in the transcript under the chapter heading |
   | `CONTENTS_WITHOUT_LEADERS` | A contents page shows page numbers with no dot leaders. | The contents page in the transcript |
   | `HYPHENATED_HEADING` | A heading breaks a word with a hyphen. | A heading show rule in `src/compiler/presets.py` or the book's `typst_preamble` that turns hyphenation back on |

   The `Figures` column counts the figures in the book's `.typ` source by kind. A `!` follows the count when a raster figure or an array diagram remains. The `figures` field holds the same counts:

   | Count | Meaning | Where the cause usually is |
   |---|---|---|
   | `DIAGRAM_AS_ARRAY` (`arrays`) | A commutative diagram or an exact sequence prints as aligned rows or a matrix, not as a fletcher drawing. | A transcript `array` whose objects and arrows are not one per `&` cell, such as `0 \to A \to B` above `\downarrow \quad \downarrow`. Rewrite the `array` with one object or one arrow in each cell. |
   | `RASTER_FIGURE` (`raster`) | A figure prints as a crop of the scan. | A figure with no redraw. Redraw it as `figures/fig_PPP_NNN.typ` with fletcher or CeTZ, or as an SVG. A runner and an editor report it. |
   | `VECTOR_FIGURE` (`vector`) | A figure prints as an SVG, a PDF, a Typst drawing or a fletcher diagram. | Nothing to fix. Compare each one with the scan in step 5. |

   Before you change shared code in `src/compiler/`, prove the defect against the scan with `.claude/skills/scan-evidence/SKILL.md`.

5. A fixer reviews the look of each book. A runner and an editor skip this step.

   ```bash
   uv run python scripts/math_books.py BOOK --json output/math_books.json
   uv run python scripts/look_sheet.py BOOK output/look
   ```

   The sheets show six sample pages: a chapter opening, the page with the most math, a table, a figure, a prose page and the index. Read each sheet and give each item PASS or FAIL, with the page that fails:

   | Item | PASS when |
   |---|---|
   | Type profile | The `type` field has no `!`. Latin text sets 45 to 80 characters per line, and CJK text 50 to 90 half-width units. The line pitch is 1.15 to 1.5 times the body size for Latin text, and 1.4 to 1.8 for CJK text. |
   | Hierarchy | Chapter title, section heading, theorem head and body text each have one size and one weight. No heading looks like body text, and no body text looks like a heading. |
   | Chapter opening | The title starts at the same height as in the other chapters. The title does not hyphenate, and no scan line such as a running head or "CHAPTER 2" prints under it. |
   | Math | Every display is centred or set to the book's indent. No prose or command name sets as math letters, such as 𝑥𝑟𝑖𝑔ℎ𝑡𝑎𝑟𝑟𝑜𝑤 or 𝐸𝑎𝑐ℎ𝑜𝑓. No formula prints as raw text, such as `int_N K`. Equation numbers align at the right margin. |
   | Tables | The header row is the scan's header, not its first data row. Rules are thin, and columns line up. |
   | Figures | A figure is a vector drawing, sits inside the text block, and has its caption below it. |
   | Index | Each entry starts on its own line, and subentries indent under it. No running head of the scan prints as a heading. |
   | Page | Text fills the page to the foot, except at the end of a chapter. Running heads and page numbers sit at the same place on every page. |

   For each FAIL, find the cause with `.claude/skills/scan-evidence/SKILL.md`. Fix it in the transcript, in `books/<key>/book.toml` or in `src/compiler/`, then build the book again.

6. Run the harness again for the books that you changed. Stop when each row shows PASS and the `numbering` field shows none. If a FAIL line stays, quote it in your report.

## Report

Give one row per book. Show the harness row before and after, the commands that you ran, each open FAIL line, and the verdict for each resync. For each fix that needs `src/`, give the hit line from `--hits` and the scan page.
