# Look review of one book

Paste this prompt into a session, and set BOOK first. The session checks the rebuilt PDF against the scan at the publisher bar (`docs/publisher-bar.md`). It finds defects and does not fix them.

The page group is the unit of work: 10 rebuilt pages that one checking agent compares with their scan pages. A sample is three page groups: the front, the middle, and the back with the index. A defect with a shared cause shows in the sample, so the sample runs first and the full pass runs only on a book whose sample is clean of shared causes.

## VALUES

- BOOK: the key under `books/`, such as `riemann`.
- AGENTS: the most checking agents at once. Use 4 unless the user names another number.
- SAMPLE: ` --sample` for the sample, or nothing for the full pass. Add it to every command below.

## RULES

- Run the session itself on Sonnet. It only queues page groups and reads one-line replies.
- Run every command from the repository root as `mise exec -- uv run python scripts/look_review.py ...`. `mise exec --` sets the scan, book and output folders. A checking agent runs only `lr check` and `lr crop` from the folder that `prepare` prints, as its brief says.
- Do not edit the transcript, `books/`, `src/` or docs. Do not build, commit, or run `audit --update`.
- Write only under the folder that `prepare` prints, plus the one merge into `review_findings.jsonl` beside it.
- `scripts/look_review.py` pairs, renders, measures, checks and merges. If it fails, report its error and stop.
- If you hit a usage limit, stop. The finished group files stay in place, and `status` shows what is left.

## Steps

1. Prepare the sample. This renders the page pairs, runs the checker on the PDF, writes the page groups, copies the transcript pages into the folder, and writes the folder's `lr` command for the checking agents.

   ```bash
   mise exec -- uv run python scripts/look_review.py prepare BOOK --sample
   ```

   It prints the rebuilt PDF, the scan, the page and group counts, and a `checker:` line with each rule and its page count. If it prints `stale`, build the book and prepare again.

2. List the page groups that still need an agent.

   ```bash
   mise exec -- uv run python scripts/look_review.py status BOOK SAMPLE
   ```

3. For each page group that `status` lists as `todo`, start one Sonnet subagent (Agent tool, model sonnet, general-purpose). Its whole prompt is: run this command and follow its output.

   ```bash
   mise exec -- uv run python scripts/look_review.py brief BOOK GROUP SAMPLE
   ```

   Run at most AGENTS at once. Start the next page group when one finishes. When `check BOOK GROUP SAMPLE` prints problems after an agent finishes, send them back to that agent once.

4. Spot check the book when its first 2 page groups are done.

   ```bash
   mise exec -- uv run python scripts/look_review.py spot BOOK SAMPLE
   ```

   It prints up to 3 P0 or P1 findings and 2 pages that the audit passed, each with one sheet that sets its scan pages beside its rebuilt page. Open each sheet and judge the item against the scan. To read a region closer, run `crop BOOK PAGE:BOX SAMPLE`, as the brief describes. Write one line per item to the `spot_check.jsonl` it names: `{"page": P, "item": "group_NN.jsonl line K" or "PASS", "agent_right": true or false, "why": "..."}`. With 3 or fewer right, stop and report the lines.

5. When `status` prints `all groups done`, merge.

   ```bash
   mise exec -- uv run python scripts/look_review.py merge BOOK SAMPLE
   ```

   It refuses to merge while a page has no audit line, or while a line is bad. Rerun the named page group, then merge again. It numbers the findings, appends them to `review_findings.jsonl` in one locked write, and writes the checklist.

6. Decide on the full pass. After the sample, count the findings that carry a `cause_id` and the rules on the `checker:` line of step 1.

   - Any of them: report them and stop. Each is one fix in `src/compiler/` or `book.toml` that changes many pages. The full pass waits for that fix and a rebuild.
   - None: run steps 1 to 5 again without `--sample`.

## Report

Give the pages checked of the page count, the findings by severity and by `cause`, the count for each `cause_id`, the `checker:` line, the spot check result, and the 10 worst defects with pages. Say whether the full pass ran or what it waits for.
