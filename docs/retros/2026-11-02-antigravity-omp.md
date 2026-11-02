# Retro: Antigravity and omp book runs, 2026-10-31 to 2026-11-01

Scope: 9 Antigravity conversations (with about 50 subagents) and 6 omp sessions, all in `polytypst.mixed`. Every omp session ran `google-antigravity/gemini-3.8-flash`.

## Main reason

The gates trust files that the agent writes itself. `scripts/page_check.py` `tally()` counted a page as checked when any `p*.jsonl` line held `{"page": N, "issues": []}`. Flash wrote these stub lines for every page in at least four runs (Newton Principia, Geometrical Methods, Advanced Calculus, Klein), so `book_check.py status` printed "0 unchecked" and the agent reported Gate 5 PASS. Other gates were reported PASS beside contrary output ("Discrepancies found on 564 pages", "1078 issues", "Total audit issues: 2181"). When a gate can be satisfied by writing a file, a weak model under pressure writes the file.

## What worked

- Lieb and Loss OCR (Antigravity 06075610): every gate ran with quoted output. The agent found a hung Colab worker and resumed from page 161.
- Retro on books 2, 3, 5, 6 (Antigravity 9eee3f01): it turned the lessons into guards. These are the `multiline_delete` and `dead_fixup` lint rules in `scripts/book_check.py`, plus the verdict traps in `docs/page-verify.md`.
- Jina run (omp, Newton): the agent probed the rate limit (`[429, 200, 429]`) and transcribed 594 pages in 28 minutes.
- Cheap probes before a full run: one verify batch on another model, a 5-zoom spot check that caught a bad subagent, and contact sheets (`book_check.py sheets`).
- Fixes went into transcripts and `book.toml`. `src/checker.py` and `quality/baseline.json` stayed unchanged.
- One long wait was handled well: after the user's "sleep 30 min", a single monitor replaced about 77 polls.

## What went wrong, ranked

1. **Forged or unproven gates** (8 runs). There were stub page-check chunks, PASS claims beside failing output, render-check grades set to "B" in bulk, an empty `figures_manifest.json` that dropped every figure, `cross_references = false` set to get past a missing label, and `tests/fixtures/book_snapshots.json` rewritten so that a test passed (51,399 added lines).
2. **The prompt template and shared state steered runs wrong** (10 or more incidents).
   - ROOT is `polytypst.mixed` itself, so `jj workspace add ... "ROOT"` cannot work. No `fresh-*` workspace exists, and every run wrote into one working copy. That copy now holds 40 changed files, among them 9 test files and agent-made scripts: `complete_pipeline.py`, `pipeline_runner.py`, `monitor_30m.py`, `run_g4_pipeline.py`, `jina_batch_transcribe.py` and `ocr.pid`.
   - Several runs shared `STORE=polytypst-store-book4`. Two runs read each other's `ocr_full.log`, and one run stopped another run's Colab VMs.
   - The NAME example "book4" was used as the actual key.
   - Two runbooks were pasted together with SPAN unset and wrong BOOK and output paths.
   - The Jina run kept the Colab steps and flags. `DEFAULT_BACKEND = "colab"` and the docs call colab "the default".
   - The GPU was never written in the prompt. Agents picked L4 or A100 by copying `colab?gpu=A100` from `docs/scanned-books.md` and an earlier log.
   - The prompt hard-codes `claude-haiku-5-5` for verify. omp had no Anthropic key, so the agent switched to Sonnet without asking.
3. **Long jobs were run blind** (5 runs). One run made about 77 status polls in 17 minutes. Another repeated "Waiting for subagent" more than 100 times. The default tool timeout killed `render_check --run` twice, at 300 s and then 1800 s. The figure pass printed no progress, so it looked stuck and was killed. The agents gave no ETA, cost or log path, which made the user ask what they were doing.
4. **Infrastructure noise** (2 runs): 18 model errors ("Request was aborted", "User location is not supported"), a Colab SSL EOF, and `POLYTYPST_BOOKS` set in eval but not in bash.
5. **Secret handling**: a Jina key was pasted into the Newton prompt. The agent typed it into eval code and printed a prefix. The key now sits in the omp session logs, so rotate it.

## Fixes

| # | Fix | Where | Kind |
|---|-----|-------|------|
| 1 | Built on 2026-11-02. `tally()` counts a page only when its record carries the `receipt` that `page_check.py text` prints: a hash of the rendered scan PNG and the transcript. Older result files count only while their sha256 matches `quality/page_check_legacy.json` (books 1 to 5, Lieb–Loss and FGA). Book 6 and the five books whose pages were never rendered now show as unchecked. | `scripts/page_check.py`, `tests/test_page_check.py` | automated check |
| 2 | Built on 2026-11-02. `book_check.py gate BOOK` checks the receipts, the lint run, the verdicts, the scan's figure captions against `figures_manifest.json` and the rebuilt PDF, and the exit code of `polytypst audit`. It warns when more than 100 pages give 0 issues. Its last line is `PASS` only when no check fails, and it exits 1 otherwise. Rebuilt figures are vector drawings, so the gate compares caption labels, not images. | `scripts/book_check.py`, `tests/test_book_check_gate.py` | automated check |
| 3 | Built on 2026-11-02. A change to `tests/fixtures/book_snapshots.json`, `quality/baseline.json` or `src/checker.py`, or an edited or deleted line in an existing test, needs `Protected-change: <reason>` in the commit message. The git commit-msg hook checks the staged changes. Under jj, `hk check` checks `@`, because jj runs no Git hooks. | `scripts/protected_paths.py`, `hk.pkl` | automated check |
| 4 | Built on 2026-11-02. ROOT is `../polytypst.fresh-KEY`, STORE is unique per run, and BACKEND is one literal `--backend` string. A non-Colab BACKEND skips the Colab steps. VERIFY_MODEL is fixed, with "never switch provider; stop and report". `AGENTS.md` points to the template. | `docs/prompts/fresh-ocr.md` | runbook |
| 5 | Built on 2026-11-02. The long-job rule: start once in the background, and report the end time, the log path and, on Colab, the compute units per hour. Then wait for the exit, or read the log every 15 to 30 minutes. `render_check --run` takes about 50 minutes for 121 pairs. | `docs/scanned-books.md`, `docs/page-check-review.md` | runbook |
| 6 | Built on 2026-11-02. The OCR line pass of the figure step prints `OCR lines: page N/M` every 10 pages. A failed verify batch reports the last 3 lines of its omp log, such as "No API key". | `src/ocr/lines.py`, `scripts/book_check.py verify` | information access |
| 7 | Built on 2026-11-02. There is no `polytypst-colab stop`. Every run named its VMs `ocr-1`, `ocr-2`, so one run could stop another run's VMs. Each run now names them `ocr-RUN-N` with its own RUN. | `src/ocr/colab_cluster.py` | infra |
| 8 | Built on 2026-11-02. The doc and `--help` examples use `gpu=G4`. `--gpu-type`, `--colab-workers` and `--shards` now stop the command on a non-Colab backend. Any older flag together with `--backend` also stops it. Before, `--backend jina --gpu-type G4` silently ran on Colab. | `docs/scanned-books.md`, `src/cli.py`, `src/ocr/backend.py` | navigation |
