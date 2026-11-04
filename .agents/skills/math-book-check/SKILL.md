---
name: math-book-check
description: Check rebuilt math books against their scans in the Antigravity app. Use when the user asks to check, review or audit a math book or all math books.
---

# Math book check (Antigravity)

Follow `docs/prompts/math-book-check.md` step by step. Your model sets your role:

| Model | Role | What you do |
|---|---|---|
| Gemini 4 Argon | editor | All steps. Fix transcripts and `books/<key>/book.toml`. Report each fix that needs `src/`. |
| Gemini 3.8 Flash | runner | Steps 1, 2 and 6. Run the commands and report. Change no file. |

- Run each command in the terminal from the repository folder. Use `uv run` for every Python command.
- If a command runs longer than 2 minutes, start it once with its output in a log under `output/logs/`. Read the log every 15 to 30 minutes, not more often.
- Quote the harness row and each FAIL line in your report. A row that you did not run again is not PASS.
- If the terminal shows "No API key", "429" or "User location is not supported", stop and report that line.
