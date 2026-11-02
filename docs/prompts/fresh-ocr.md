# Fresh OCR of one scanned book

Paste this prompt into an agent session, and fill in VALUES first. The agent makes a fresh OCR of one scanned book, builds Typst, LaTeX and PDF, and checks the result against the scan. It finishes when every gate passes, or when it reports which gate failed, with the gate's output.

## VALUES

- SCAN: the absolute path of the scan PDF, in double quotes.
- KEY: the folder name under `books/`, such as `analysis_elliott_h_lieb_michael_loss_2001`. For a new book, the slug that the run will create. Use the real key, never an example key such as `book4`.
- ROOT: `/Users/martinfan/devv/polytypst.fresh-KEY`. Every run gets its own workspace.
- STORE: `/Users/martinfan/devv/polytypst-store-fresh-KEY`. Every run gets its own transcript store. Never share it with another run.
- BACKEND: one literal backend string. Examples:
  - `colab:jina-ocr-v1?gpu=G4&workers=2&shards=3` for the self-hosted model on Colab GPUs.
  - `jina` for the Jina API.
- VERIFY_MODEL: the model for `book_check.py verify`, or `none`. With `none`, you verify the claims yourself.

## RULES

- Work in ROOT. When a runbook names `/Users/martinfan/devv/polytypst.mixed`, use ROOT.
- Write transcripts only in STORE. `/Users/martinfan/devv/polytypst-books` holds checked work, so only read it.
- Run Python as `uv run`, never bare `python` or `python3`. Put every path in double quotes.
- Take API keys from the environment or Varlock only. Never type, print or paste a key.
- Pass BACKEND to `--backend` exactly as written. Never add `--mode`, `--gpu-type`, `--colab-workers`, `--shards` or `--ocr-model`.
- Use VERIFY_MODEL only. When it fails, for example with "No API key", stop and report the error. Never switch to another model or provider.
- Keep checks as they are. Leave `src/checker.py`, every existing test, `tests/fixtures/book_snapshots.json` and `quality/baseline.json` unchanged, and never run `audit --update` or `--allow-rise`. When a check fails, fix the cause in the book's files, or report it.
- Report a check as passed only when you ran it in this session. Quote the last lines of its output.
- Long jobs: start each OCR run, build and check once, in the background, with its output in a log in ROOT. Report its expected end time and its log path, and for a Colab BACKEND the compute units per hour. Then wait for it to exit, or read the log every 15 to 30 minutes.
- Leave version control alone after Step 0: no commit, no push, no pull request.

## STEP 0. Set up

1. From `/Users/martinfan/devv/polytypst`, run: `jj workspace add --name fresh-KEY -r main "ROOT"`
2. Copy `mise.local.toml` from `/Users/martinfan/devv/polytypst.mixed` to ROOT. Set its `POLYTYPST_BOOKS` to STORE, and create STORE.
3. Read `AGENTS.md`, `GLOSSARY.md`, and the sections "Before you start" and "Transcribe the scan" of `docs/scanned-books.md`.
4. Run: `mise exec -- printenv POLYTYPST_BOOKS ; mise exec -- typst --version ; uv run polytypst --help ; uv run polytypst books`

Gate 0: `printenv` prints STORE. You know whether KEY is a known book in `books/KEY/` or a new one. A known book writes to `output/KEY/`. A new book needs `--lang` and `--domain`.

## STEP 1. Check Colab before you spend compute

Skip this step when BACKEND does not start with `colab`.

1. Run `uv run polytypst-colab usage`. When it shows no compute-unit balance, the colab CLI is missing or signed out: stop and report it.
2. Run `uv run polytypst-colab gpus`. Check that the model in BACKEND fits its GPU.

Gate 1: you wrote down the balance, the GPU and the model.

## STEP 2. Trial on 10 pages

1. Run in the background, with its output in `ROOT/ocr_trial.log`:
   `mise exec -- uv run polytypst "SCAN" --backend "BACKEND" --pages 1-10 --formats typst,latex,pdf`
   Add `--lang` and `--domain` only for a new book.
2. Wait for the command to exit. Read the log once at the end.
3. Open 3 pages from `STORE/KEY/markdown_pages/` next to the same pages in `output/KEY/page_renders/`. Compare words, numbers, tables, math and line order.

Gate 2: the command exited 0, pages 1 to 10 each have a Markdown page, and your 3 samples match their renders. If not, stop and report the bad pages.

## STEP 3. The whole book

1. Run the same command without `--pages`, once, in the background, with its output in `ROOT/ocr_full.log`. The trial pages stay as they are.
2. When it exits 1 with "N pages still pending", run the same command again. It transcribes only those pages. Repeat until it exits 0, at most 3 times.
3. For a Colab BACKEND, run `uv run polytypst-colab usage`. When it shows an active VM whose name your log printed, stop that VM with the colab CLI. Never stop a VM that another run started.

Gate 3:
- `markdown_pages` holds one file for each PNG in `page_renders`, and no page is empty.
- The log ends with "Verified N pages. Discrepancies found on M pages."
- You compared each flagged page with its render, and fixed each real error in STORE or listed it with its page number. On a Chinese or Japanese book, the cross-check flags many false pages, so treat its flags as hints.
- For a Colab BACKEND, usage shows 0 active VMs of this run.

## STEP 4. Build and compile

1. Run: `mise exec -- uv run python scripts/one_book.py KEY build`
2. Run: `mise exec -- typst compile --root / "output/KEY/FILE.typ"`. It must exit 0.
3. Compile the `.tex` file with the engine that its first lines name, with `-jobname KEY_latex`, so that it writes a separate PDF from Typst's. It must exit 0. Search its log for "Undefined control sequence", "Missing $", and overfull boxes wider than 10pt. When that engine is not on PATH, report Gate 4's LaTeX part as blocked.

Gate 4: both compile with exit 0, and you listed each LaTeX warning that you could not fix.

## STEP 5. Check the words against the scan

Follow `docs/page-check-review.md` from Step 1 to Step 6.

- Run `uv run python scripts/page_check.py chunks --books KEY --size 10`. For each range, follow `docs/page-check.md` yourself. Each page record needs the `receipt` that `page_check.py text` prints.
- With VERIFY_MODEL `none`, decide each queued claim yourself by following `docs/page-verify.md`. Otherwise run `uv run python scripts/book_check.py verify KEY --model VERIFY_MODEL` in the background.
- Fix each real and scan_typo verdict as Step 4 of `docs/page-check-review.md` says.

Gate 5: `uv run python scripts/book_check.py status KEY` shows every page checked and 0 unverified.

## STEP 6. Check the PDF

1. Follow Step 7 of `docs/page-check-review.md`. Run `render_check.py --run` in the background: it takes about 50 minutes for 121 pairs.
2. Search the `.typ` and `.tex` sources for these faults: inline math with spaces inside, like `$ x $`; an orphaned `{A}{B}` left from `\frac`; a single letter as a display equation; brackets that do not balance within a section; bullets in the bibliography.
3. Run: `uv run python scripts/book_check.py gate KEY`

Gate 6: the last line of `gate` is `PASS`, and the source search finds 0 faults, or you list each remaining one.

## REPORT (your last message)

- Each command that you ran, with BACKEND exactly as written.
- Each gate: PASS, FAIL or BLOCKED, with the last lines of its output. Quote the whole `gate` output.
- The pages that the cross-check flagged, and what you did on each one.
- For a Colab BACKEND, the compute units at the start and at the end.
- Every file that you created or changed, and what is still wrong, with page numbers.
