# Review a rebuilt book against its scan

This runbook checks one rebuilt book against its source scan and records each defect as a finding.
It works for any output folder. The book does not need a folder in `books/<key>/`.
For a registered edition with a page map, `polytypst parity` in `docs/scanned-books.md` is stricter.

The review only reads the book. Write files only in these places:

- `FOLDER/review/`
- `output/review_evidence/BOOK/`
- `output/review_findings.jsonl` and `output/review_findings.md`

## Before you start

Find these four values. Write them down, and use them in every command.

| Name | What it is | Example |
|---|---|---|
| `FOLDER` | The output folder of the book | `output/2 通缩经济与货币政策` |
| `SCAN` | The source scan PDF | `/Users/martinfan/Downloads/2 通缩经济与货币政策.pdf` |
| `PDF` | One rebuilt PDF in `FOLDER` | `output/2 通缩经济与货币政策/2.pdf` |
| `BOOK` | The book number, a short ID for file names | `2` |

Obey these rules in each step:

1. Run every command from the repository root `/Users/martinfan/devv/polytypst`.
2. Put each path in double quotes. Folder names can contain spaces and Chinese characters.
3. Run Python and the CLI through `uv run`.
4. Search `output/` with `rg -u`. Git ignores `output/`, so a plain `rg` finds nothing there.
5. If you do not know `SCAN`, ask the user for it. Do not guess the path.

## Terms

- **Coverage**: the share of a scan page's text that the rebuilt PDF also holds. Text off the page does not count. The value 1.0 means all text is there.
- **Text map**: for each scan page, the rebuilt page that holds most of its text. `review` makes it.
- **Redshift overlay**: the scan page and the rebuilt page drawn on each other. Red ink is only in the scan. Cyan ink is only in the rebuilt PDF. Black ink is in both.
- **Noise page**: a scan page with only a chart, a figure, or formulas. Its OCR text is noise, so its coverage is low although the page can be complete.
- **Finding**: one verified defect, written as one JSON line.

## Steps

### Step 1. Measure the folder

Run:

```bash
uv run polytypst review "FOLDER"
```

You see one line for each rebuilt PDF, and under it one `lowest coverage:` line:

```text
2.pdf: 335 pages, coverage median 0.917, 11 scan pages below half, 0 pages with text past the edge
  lowest coverage: scan 279 -> 251 (0.209), scan 55 -> 47 (0.282), ...
```

- If the command prints `has no OCR pages; pass --scan SCAN.pdf`, run it again with `--scan "SCAN"`. The OCR takes about 1 second for each page.
- If the command prints `skip book.pdf: same bytes as 2.pdf`, that is correct. It measures each file one time.

Done when `FOLDER/review/measures.json` exists and the command printed one line for each PDF.

### Step 2. Read the measures

Open `FOLDER/review/measures.json`. For each file and each measure, compare the value with the table in "Read the measures" at the end of this runbook.

Done when you have a list of each measure that misses its target, with its file name and value.

### Step 3. Check the pages with low coverage

Use the `lowest coverage:` line of step 1. Each item `scan S -> R (C)` gives scan page `S`, rebuilt page `R` and coverage `C`. Check every item with `C` below 0.5.

1. Make a side-by-side sheet of the two pages:

   ```bash
   uv run python scripts/review_sheet.py "output/review_evidence/BOOK/sheet_sS_rR.png" --panel "Scan=SCAN#S" --panel "Rebuilt=PDF#R" --diff 0,1
   ```

2. Open the PNG and look at it.
3. Decide with this table:

| What you see | Decision |
|---|---|
| The scan page has paragraphs or table rows that the rebuilt page does not have. | Real loss. Write a P0 finding in step 6. |
| `R` is `none`. The scan page has text. | Real loss: no rebuilt page has the text. Write a P0 finding. |
| The scan page is a noise page, and the rebuilt page has the same chart or formulas. | Noise. Write no finding. |
| The scan page is a noise page, but the rebuilt page has no chart or no formulas. | Real loss. Write a P0 finding. |

Done when you decided each item with `C` below 0.5.

### Step 4. Draw the overlays (only for a vintage or facsimile edition)

Do this step only when the PDF name contains `vintage` or `facsimile`. A normal monograph reflows the text, so its overlays do not match the scan by design.

```bash
uv run polytypst review "FOLDER" --scan "SCAN" --visual
```

The command takes about 1 minute for each 300 pages. Then open `FOLDER/review/visual_<PDF name>/index.html`. It shows the worst pages first.

Done when you looked at the 10 worst pages. If more than half of a page's ink is red or cyan, write a P1 finding.

### Step 5. Compare tables, figures and footnotes with the scan

Check at least 5 tables, 5 figures and 5 pages with footnotes. Find them in the transcript pages. The file `p_NNN.md` is scan page `NNN`.

Pages with tables:

```bash
rg -u -l '<table|^[|]' "FOLDER/markdown_pages"
```

Pages with figures:

```bash
rg -u -l '!\[' "FOLDER/markdown_pages"
```

Pages with footnotes:

```bash
rg -u -l '^[①②③④⑤⑥⑦⑧⑨⑩]' "FOLDER/markdown_pages"
```

For a registered book, five scripts list defects that you would otherwise find page by page. Check each listed item first:

```bash
mise exec -- uv run python scripts/table_headers.py KEY
uv run python scripts/lone_marks.py PDF
mise exec -- uv run python scripts/figure_leaks.py KEY
mise exec -- uv run python scripts/transcript_lint.py KEY
uv run python scripts/figure_sheet.py --pdf PDF "output/review_evidence/BOOK/figures"
```

- `table_headers.py` lists the tables whose second row the build shifts one or more columns.
- `lone_marks.py` lists the footnote marks that print alone on a line, usually after a title.
- `figure_leaks.py` lists transcript lines that repeat text inside a figure crop.
- `transcript_lint.py` lists panel titles near figures, body lines that the build reads as notes, and identical notes in a row.
- `figure_sheet.py --pdf` sheets every rebuilt page that holds an image, so you can see each figure at its printed size.

"Figures", "Tables" and "Notes" in `docs/scanned-books.md` give the fixes.

For each scan page `S`, find its rebuilt page `R` in `FOLDER/review/pages.csv`. Run `rg -u "^S," "FOLDER/review/pages.csv"` with the page number for `S`, without leading zeros. The column after the PDF name `:page` is `R`. Then make a sheet as in step 3, and check:

- **Table**: the same rows, the same columns, and the same number in each cell. The header cells are above the correct columns. A scan can show a table turned 90 degrees. Match its cells by their row and column labels, not by their position on the page.
- **Figure**: the image is there, it is the correct image, and it is not cut. The caption has the same number and text.
- **Footnote**: each marker in the text (①, ②, ...) points to the footnote with the same text as in the scan. A chart label is not a footnote. `scripts/note_bindings.py` lists the notes that can bind to an enumeration. "Notes" in `docs/scanned-books.md` gives the fix.
- **Heading and equation numbers**: they are the same as in the scan, and they do not skip or repeat.

Done when you checked 15 items and wrote down each difference.

### Step 6. Write the findings

Add one line to `output/review_findings.jsonl` for each defect from steps 2 to 5. Each line is one JSON object on one line, with these 8 fields:

| Field | Value |
|---|---|
| `id` | `B` + `BOOK` + `-` + a two-digit number, such as `B2-31`. Use the next number after the highest one for the book. |
| `book` | The folder name without `output/`, such as `2 通缩经济与货币政策` |
| `severity` | `P0`, `P1`, `P2` or `P3`, from the table below |
| `format` | `typst`, `latex`, `both`, `vintage` or `transcript` |
| `where` | The file and page, as `2.pdf p64, scan p74` or `2.typ:5051` |
| `what` | One sentence that tells what is wrong |
| `evidence` | A measure, a quote of at most 15 words, or a PNG path |
| `status` | `open` |

To find the highest existing number for book 2, run `rg -u -o '"id": ?"B2-[0-9]+' output/review_findings.jsonl`.

| Severity | Use it when | Example |
|---|---|---|
| `P0` | Content is wrong or lost. | A table value is wrong. A paragraph is missing. A footnote has the wrong text. |
| `P1` | The layout is visibly broken, but the content is there. | Text runs off the page. A caption is on a different page from its table. |
| `P2` | The typesetting uses a bad practice. | A number is typed as text, not made by a counter. A font has no italic. |
| `P3` | A small problem. | A stale file. A typo that the scan also has. |

Example line:

```json
{"id": "B2-03", "book": "2 通缩经济与货币政策", "severity": "P0", "format": "transcript", "where": "p_278.md, scan p278, Table 10-1", "what": "The 加拿大 column is missing, so each later value is under the wrong country.", "evidence": "Scan 美国 is 211, the rebuilt table shows 约 600. See output/review_evidence/2/sheet_s278_r251.png", "status": "open"}
```

Write a finding only when you saw the defect yourself. If the scan has the same defect, write no finding.

For a wrong word or mark, make the evidence PNG with `polytypst evidence zoom`, and put the transcript line as `file:line:col` in `where`. The steps are in `.claude/skills/scan-evidence/SKILL.md`.

Done when each defect from your notes is one line in the file.

### Step 7. Make the checklist

Run:

```bash
uv run polytypst checklist output/review_findings.jsonl
```

You see `N findings: ... open; checklist: output/review_findings.md`.

If you see `has bad lines`, each following line names a line number and the problem. Correct those lines in `output/review_findings.jsonl`. Then run the command again.

Done when the command prints the `checklist:` path.

### Step 8. Report

Tell the user these items:

1. The coverage median and the number of pages below half for each PDF, from step 1.
2. The number of new findings for each severity.
3. The 3 worst findings, each with its `id` and `what`.
4. The path `output/review_findings.md`.

## Read the measures

| Measure | File | Target | What a miss means |
|---|---|---|---|
| `coverage_median` | each PDF | 0.9 or more | Text is lost, garbled, or off the page. |
| `pages_coverage_below_half` | each PDF | only noise pages | Some pages lost their text. Step 3 checks them. |
| `pages_text_past_edge` | each PDF | 0 | Lines do not break. In a Chinese LaTeX book, the preamble has no `xeCJK` or `ctex`. |
| `mean_missing`, `mean_extra` | each PDF, with `--visual` | near 0 for a vintage or facsimile edition | The page does not match the scan. |
| `headings_with_typed_numbers` | `.typ`, `.tex` | 0 | Heading numbers are text, not counters. |
| `heading_numbering_rule` | `.typ`, `.tex` | 1 | The source has no heading numbering rule. |
| `literal_figure_refs`, `literal_table_refs`, `literal_equation_refs` | `.typ`, `.tex` | falls after each fix | References are text, not links. Each figure caption also counts as one. |
| `links` | `.typ`, `.tex` | rises after each fix | The count of `@label` links in Typst, or `\ref` links in LaTeX. |
| `unnumbered_display_math` | `.tex` | 0 when the Typst source numbers its equations | LaTeX lost the equation numbers. |
| `footnotes` | `.typ`, `.tex` | the number of footnotes in the scan | Chart labels or list markers became footnotes. |
| `chained_footnotes`, `footnotes_in_headings` | `.typ`, `.tex` | 0 | Footnote markers are in a row, or in a heading. The markers can point to the wrong notes. |
| `running_head_leaks` | `.typ`, `.tex` | 0 | The scan's page headers are in the body text. If the book has a second running head, add `--running-head "TEXT"` in step 1. |
| `checker_*` | `.typ`, `.tex` | 0 | The rules of `src/literal_numbers.py`. |
| `overfull_hbox_over_50pt`, `missing_glyphs`, `undefined_references`, `font_shape_undefined`, `rerun_needed` | LaTeX `.log` | 0 | The LaTeX build is incomplete, or its fonts do not have the glyphs. |
| `repeated_sentences` | transcript `.md` | 0, if the scan does not repeat the sentence | The transcript repeats text in a loop. |
| `halfwidth_commas_after_han` | transcript `.md` | 0 | Chinese text uses the comma `,` in place of `，`. |

## After a rebuild

Each run of `review` adds one line to `FOLDER/review/history.jsonl`. The next run prints each measure that changed, as `FILE measure: old -> new`.

1. Run `uv run polytypst review "FOLDER"` again.
2. For each open finding of the book, look at its measure or make its sheet again.
3. If the defect is gone, change the finding's `status` to `fixed`. If the scan has the same defect, change it to `wontfix`.
4. Run `uv run polytypst checklist output/review_findings.jsonl` again.

## When a command fails

| Message | Cause | What to do |
|---|---|---|
| `is not a folder` | The path is wrong or not in quotes. | Run `eza output` and copy the folder name. Put it in double quotes. |
| `has no OCR pages; pass --scan SCAN.pdf` | The folder has no OCR of the scan. | Add `--scan "SCAN"`. |
| `--visual needs --scan` | Step 4 needs the scan. | Add `--scan "SCAN"`. |
| `has bad lines` | A finding line is wrong. | Correct each line it names, then run the command again. |
| `No such file or directory: scripts/review_sheet.py` | You are not in the repository root. | Run `cd /Users/martinfan/devv/polytypst`, then run the command again. |
| `ModuleNotFoundError` or `command not found: polytypst` | The command did not use `uv run`. | Put `uv run` before the command. |
| `book 'OTHER' failed to load`, or a `SyntaxError` or `NameError` in `books/OTHER/` | The CLI loads every book to match the scan, and another book's `book.toml` or `book.py` is broken. | Run `mise exec -- uv run python scripts/one_book.py KEY cli review "FOLDER" --scan "SCAN"`, which loads only book `KEY`. |
| `BookStateError: set POLYTYPST_BOOKS` | The book state folder is not set. | Put `mise exec --` before the command, so `mise.local.toml` sets it. Without that file, export it to the folder that holds each book's state. |
| `page ... out of range` or an empty sheet | `R` or `S` is wrong. | Look up `R` again in `pages.csv`. Pages count from 1. |
