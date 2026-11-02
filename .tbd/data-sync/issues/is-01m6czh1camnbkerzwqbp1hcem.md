---
type: is
id: is-01m6czh1camnbkerzwqbp1hcem
title: Deepen page check into a src/page_check module behind PageCheck(book)
kind: task
status: in_progress
priority: 2
version: 4
delegate: claude-code@f
labels:
  - architecture
dependencies: []
hold: null
hold_until: null
created_at: 2026-11-02T01:56:03.590Z
updated_at: 2026-11-02T02:33:38.393Z
started_at: 2026-11-02T01:57:10.091Z
---
Move scripts/page_check.py, book_check.py, render_check.py and scan_sheet.py (branch `mixed`) into a deep `src/page_check/` module behind `PageCheck(book)`, reached through `polytypst page-check …`.

Decisions (architecture review grilling, 2026-11-02):

- Package: `__init__` (PageCheck), `results`, `agents`, `lint`, `verify` (triage, verify, status), `render`, `sheet`. The four scripts are deleted. The runbooks docs/page-check.md, page-check-review.md and render-check.md move to the new commands.
- Interface: `pages()`, `transcript(n)` (raw stored text), `printed(n)` (transcript and page fixups applied), `ocr_lines(n)` (from LineStore), `suspects(n)`, `tables(n)`, `strip(n, band, dpi)`, `results`.
- Book argument: a unique book-key prefix. The BOOKS alias map goes away.
- Transcripts come from the edition's transcript store, not a `markdown_pages/` glob.
- `src/evidence.py` owns one `strip(scan, page, band, dpi)` renderer, which replaces four.
- Results: typed records, same JSONL files, under `output/page_check/<key>/`. The folders `1`–`6` are renamed once. `book4/` is inspected first.
- Agent seam: `run_agents(runbook, jobs, model, parallel)` with an omp adapter and a fake adapter. Each workflow keeps its own default model, and the 3600 s timeout stays.
- Tests: a fixture book (one-page scan, transcript store, line cache) in tmp_path. Existing expectations, including the Book 4 errors, are kept. Tests go through the interfaces only.
- The mise.local.toml reader is deleted. `scripts` leaves the pytest pythonpath if no test needs it.
- GLOSSARY.md gains "Page check" and "Verdict".
- Branch `page-check-module` in its own worktree, cut from `mixed` after the in-progress edits there are committed.

Related: pt-x20z (BookPaths) and pt-un3g (book.paths). Use book.paths if it has landed.

## Notes

Pushed: mixed-review 5b001ee2 and page-check-module c6203759 on origin. Decided: when page-check-module merges into mixed, rename output/page_check/1-6 in the mixed checkout to the full book keys (1_宏观经济与产业结构 … 6_劳动力市场与收入分配) in the same step, then close this bead.
