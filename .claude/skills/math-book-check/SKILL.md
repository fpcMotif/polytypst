---
name: math-book-check
description: Check rebuilt math books against their scans and fix the defects. Use to check, review or audit math books, and before a scratch script checks a book.
---

# Math book check (Claude Code)

Your role is **fixer**. Follow `docs/prompts/math-book-check.md` step by step.

- Run the harness and every `page-check` command with `run_in_background` when it runs longer than 2 minutes. Wait for its exit notice. Do not poll.
- Page checks run through `page-check run`, which starts omp agents on Gemini 3.8 Flash. Use those agents. If a check needs something the commands cannot do, add it to `src/checker.py` or `src/page_check/` with a test that goes red first. A scratch script is for one probe only.
- `page-check verify` uses `claude-sonnet-5-5` through omp. If omp has no Anthropic key, stop and report the log line.
- Record a baseline with `polytypst audit BOOK --update` only when the user tells you to in the chat.
