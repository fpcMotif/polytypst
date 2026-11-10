# Math book check (omp)

Start this runbook with:

```bash
omp -p --no-session --model google-antigravity/gemini-3.8-flash @docs/prompts/math-book-check-omp.md "BOOKS=hecke klein"
```

Your role is **runner**. Follow steps 1, 2 and 6 of `docs/prompts/math-book-check.md` for the books in BOOKS. Change no file.

- You run once, without a session. Run each command to its end, then read its output. Do not start a background job that outlives you.
- `page-check run` and `page-check verify` start more omp agents. Skip them. Report the command so that the caller can start it.
- End your output with the harness table for BOOKS and one line per FAIL, quoted.
