# Full-page look review of one book

Paste this prompt into a session, and set BOOK first. The session checks every page of the rebuilt PDF against the scan at the publisher bar (`docs/publisher-bar.md`). It finds defects and does not fix them.

## VALUES

- BOOK: the key under `books/`, such as `riemann`.
- AGENTS: the most checking agents at once. Use 4 unless the user names another number.

## RULES

- Set `POLYTYPST_SOURCES` to the folder that holds the scan PDFs. If the book's transcripts are in more than one store, `prepare` stops and asks for `POLYTYPST_BOOKS`. Set it to the store that `scripts/math_books.py BOOK` names.
- Do not edit the transcript, `books/`, `src/` or docs. Do not build, commit, or run `audit --update`.
- Write only under `output/look_review/BOOK/`, plus the one merge into `output/review_findings.jsonl`.
- Do not write a page-map, render, overflow or merge script of your own. `scripts/look_review.py` does each of these. If it fails, report its error and stop.
- If you hit a usage limit, stop. The finished group files stay in place, and `status` shows what is left.

## Steps

1. Prepare the pages. This renders every page pair, measures overflow, and splits the pages into groups of 20.

   ```bash
   uv run python scripts/look_review.py prepare BOOK
   ```

   It prints the rebuilt PDF, the scan, the page count and the group count. If it prints `stale`, name it in the report and go on.

2. List the groups that still need an agent.

   ```bash
   uv run python scripts/look_review.py status BOOK
   ```

3. For each group that `status` lists as `todo`, start one Sonnet subagent (Agent tool, model sonnet, general-purpose). Pass it, as its whole prompt, the output of:

   ```bash
   uv run python scripts/look_review.py brief BOOK GROUP
   ```

   Run at most AGENTS at once. Start the next group when one finishes.

4. When `status` prints `all groups done`, merge.

   ```bash
   uv run python scripts/look_review.py merge BOOK
   ```

   It refuses to merge while a page has no audit line, or while a line is bad. Rerun the named group, then merge again. It numbers the findings, appends them to `output/review_findings.jsonl` in one locked write, and writes the checklist.

## Report

Give the page count, the findings by severity and by cause, the 10 worst defects with pages, and the causes that likely affect other books.
