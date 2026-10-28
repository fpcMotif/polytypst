---
name: scan-evidence
description: Prove a rebuilt-book defect against its scan and find its root cause. Use when a transcript word, footnote, call mark (①②) or OCR reading looks wrong, before changing shared code in src/compiler/ such as page_cleaner footnote splitting, and when a finding needs annotated scan evidence or an HTML report.
---

# Scan evidence

The scan is the witness. Every claim about a defect rests on a _zoom_ of the scan, and every fix lands at the _root cause_: the transcript when the OCR garbled it, the code only when the transcript matches the scan.

## Before you start

- **Book state**: transcripts (`markdown_pages/`) and the local OCR (`source_ocr/`) live in `$POLYTYPST_BOOKS/<output folder name>/`, which `mise.local.toml` sets. Run every command as `mise exec -- uv run polytypst ...`, and edit transcripts in that folder. A `markdown_pages/` left in `output/<book>/` can be a stale copy, and exporting `POLYTYPST_BOOKS=$PWD/output` over the mise value splits your edits from the store every build reads.
- **Values**: `FOLDER` (the output folder, in double quotes), `SCAN` (the source PDF), `BOOK` (the book number), as in `docs/reviewing-books.md`.

## Steps

1. **Zoom** each suspect span. Copy the span exactly as the local OCR read it from `source_ocr/pNNN.json` (`rg -u` the file), then run:

   ```
   mise exec -- uv run polytypst evidence zoom "FOLDER" --scan "SCAN" --page N --span "OCR TEXT" \
     --label "scan pN · what the scan prints · what the transcript has" --out "output/review_evidence/BOOK/NAME.png"
   ```

   Read the PNG. Read the mark in the inset, not in either OCR: on circled marks the jina backend writes `$P^\Omega$` or drops the mark, and the local OCR writes O or 0.
   Done when the red box sits on the span and you can state what the scan prints.

2. **Root cause.** Put three readings side by side: the scan (step 1), the transcript line as `file:line:col` (`rg -n --column`), and the local OCR. When the transcript differs from the scan, correct the transcript in the book state. Change code only when the transcript matches the scan and the output is still wrong.
   Done when each defect names its cause: transcript (OCR) or code.

3. **Blast radius**, only for a change to shared code under `src/compiler/`. Write the test first and watch it go _red_. Sweep every book with the cleaner alone, before and after the change, and compare:

   ```
   mise exec -- uv run polytypst evidence sweep output/[1-6]_* "output/2 通缩经济与货币政策" --out before.json
   mise exec -- uv run polytypst evidence diff before.json after.json
   ```

   The glob misses folder names with a space, so name those folders on their own. Check each changed page against its scan.
   Done when every changed page is listed by book and page and classified. A real note that became body text stops the change: find its garbled call (step 1) and correct the transcript, or revert.

4. **Attribute** each change you did not expect. Other sessions edit transcripts while you work. Sweep again with your change disabled: the same result means another session's edit.
   Done when each unexpected change is yours or named as theirs.

5. **Record** one line per defect in `output/review_findings.jsonl` (fields in `docs/reviewing-books.md`, step 6). Put `file:line:col` in `where` and the zoom PNG path in `evidence`. Run `mise exec -- uv run polytypst checklist output/review_findings.jsonl`.
   Done when the command prints the `checklist:` path.

6. **Report** the findings as one HTML page with each zoom inlined:

   ```
   mise exec -- uv run polytypst evidence report output/review_findings.jsonl --ids B2-39,B2-40 --title "TITLE" --out "REPORT.html"
   ```

   Screenshot it with `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=1100,2600 --screenshot=SHOT.png "file://REPORT.html"` and read the PNG.
   Done when every card shows its zoom.
