# Fresh OCR of one scanned book

Paste this prompt into an agent session, and fill in VALUES first. The agent makes a fresh OCR of one scanned book, builds Typst, LaTeX and PDF, and checks the result against the scan. It finishes when every gate passes, or when it reports which gate failed, with the gate's output.

## VALUES

- SCAN: the absolute path of the scan PDF, in double quotes.
- KEY: the folder name under `books/`, such as `analysis_elliott_h_lieb_michael_loss_2001`. For a new book, the key is the scan's file name, lowercased, with each run of other characters than `a-z` and `0-9` turned into one `_`. Print it with `uv run python -c 'import re, sys, pathlib; print(re.sub(r"[^a-z0-9]+", "_", pathlib.Path(sys.argv[1]).stem.lower()).strip("_"))' "SCAN"`. For example, `Lectures on the orbit method (Kirillov A.A.).pdf` gives `lectures_on_the_orbit_method_kirillov_a_a`. Use the real key, never a short name such as `book4`.
- ROOT: the code checkout, `/Users/martinfan/devv/polytypst`. Only when another run works in it at the same time, a workspace with a short name, such as `/Users/martinfan/devv/polytypst.kirillov`.
- STORE: the folder that holds the book's transcripts. For a new book, `/Users/martinfan/devv/polytypst-books`, the store of every checked book. Only for a re-OCR of a book that `polytypst-books` already holds, a store of its own, `/Users/martinfan/devv/polytypst-store-NAME`, so the checked pages stay as they are. A re-OCR runs in a workspace.
- OUT: the book's output folder, `/Users/martinfan/devv/polytypst-output/KEY`. It holds the PDFs, `build/` with the `.md`, `.typ` and `.tex`, `figures/`, `page_renders/` and `logs/`.
- BACKEND: one literal backend string. Examples:
  - `colab:jina-ocr-v1?gpu=G4&workers=2&shards=3` for the self-hosted model on Colab GPUs.
  - `jina` for the Jina API.
- VERIFY_MODEL: the model for `polytypst page-check verify`, or `none`. With `none`, you verify the claims yourself.
- TRIAL: `no`, or `yes` to transcribe 10 pages before the whole book. Choose `yes` only for a BACKEND, model or language that no earlier book used.
- REPRODUCED_FIG: `false` or `true`. With `false`, each figure is a crop of the scan. With `true`, you draw each figure again in code as a vector SVG, and the scan crop is only your reference.
- FIG_STYLE, for REPRODUCED_FIG `true`: one of
  - `classic`: the look of a typeset mathematics book. Black line art, even stroke weights, labels in the body's serif and math fonts.
  - `mathematica`: the look of a Wolfram Mathematica plot. A thin frame or axes with ticks, smooth sampled curves, soft filled regions and shaded surfaces.
  - `3b1b`: the look of a 3Blue1Brown frame. A dark ground, a faint grid, and bright blue, yellow, green and red marks.
- FIG_COLOR, for REPRODUCED_FIG `true`: `mono` or `color`. `mono` uses one ink and greys, and tells curves apart by solid, dashed and dotted strokes and by weight. `color` uses at most four accent colours, and one meaning keeps one colour through the whole book.

## RULES

- Work in ROOT. When a runbook names `/Users/martinfan/devv/polytypst`, use ROOT. When it names a path under `output/`, use the same path under `/Users/martinfan/devv/polytypst-output/`.
- Write transcripts only in `STORE/KEY/`. Every other book's folder holds checked work.
- Stay on KEY. Fix pages in `STORE/KEY/` and files in `books/KEY/`, and read OUT. Learn a command from its `--help` and the docs named here. When a cause lies in `src/`, record the rule, page and scan evidence, and report it. Leave `src/` closed: the one source you read is `MonographSpec` in `src/compiler/monograph.py`, for `book.toml` fields, beside the model books that `docs/scanned-books.md` names. With REPRODUCED_FIG `true`, you also read `FigureSpec` and `FigureBook` in `src/vision/diagram_engine.py`. Read no other book, workspace, store, log or finding, and skip `recall` hits about other books. Filter shared files to KEY, for example `jq --arg k "KEY" '.[$k] // "no entry"' "quality/baseline.json"`.
- Run Python as `uv run`, never bare `python` or `python3`. Put every path in double quotes.
- Keep ROOT as code: the only files you add there are in `books/KEY/`. Transcripts go to STORE, and logs, sources, PDFs and every other file you make go to OUT.
- Take API keys from the environment or Varlock only. Never type, print or paste a key.
- Pass BACKEND to `--backend` exactly as written.
- Use VERIFY_MODEL only. When it fails, for example with "No API key", stop and report the error. Never switch to another model or provider.
- Keep checks as they are. Leave `src/checker.py`, every existing test, `tests/fixtures/book_snapshots.json` and `quality/baseline.json` unchanged, and never run `audit --update` or `--allow-rise`. When a check fails, fix the cause in the book's files, or report it.
- Report a check as passed only when you ran it in this session. Quote the last lines of its output.
- Long jobs: start each OCR run, build and check once, in the background, with its output in a log in `OUT/logs/`. Report its expected end time and its log path, and for a Colab BACKEND the compute units per hour. Then wait for it to exit, or read the log every 15 to 30 minutes.
- Leave version control alone after Step 0: no commit, no push, no pull request.

## STEP 0. Set up

1. When ROOT is a workspace, run from `/Users/martinfan/devv/polytypst`: `jj workspace add --name NAME -r main "ROOT"`, then copy `mise.local.toml` from `/Users/martinfan/devv/polytypst` to ROOT. For a re-OCR, set `POLYTYPST_BOOKS` in that copy to STORE: it is the one `mise.local.toml` you edit. When ROOT is `/Users/martinfan/devv/polytypst`, skip this item: its `mise.local.toml` stays as it is.
2. Create `STORE/KEY/` and `OUT/logs/`.
3. Read `AGENTS.md`, `GLOSSARY.md`, and the sections "Before you start" and "Transcribe the scan" of `docs/scanned-books.md`.
4. Run: `mise exec -- printenv POLYTYPST_BOOKS ; mise exec -- typst --version ; uv run polytypst --help ; uv run polytypst books`

Gate 0: `mise exec -- printenv POLYTYPST_BOOKS` prints STORE. You know whether KEY is a known book in `books/KEY/` or a new one. A known book writes to OUT. A new book needs `--lang` and `--domain`.

## STEP 1. Check Colab before you spend compute

Skip this step when BACKEND does not start with `colab`.

1. Run `uv run polytypst-colab usage`. When it shows no compute-unit balance, the colab CLI is missing or signed out: stop and report it.
2. Run `uv run polytypst-colab gpus`. Check that the model in BACKEND fits its GPU.

Gate 1: you wrote down the balance, the GPU and the model.

## STEP 2. Trial on 10 pages

Skip this step when TRIAL is `no`.

1. Run in the background, with its output in `OUT/logs/ocr_trial.log`:
   `mise exec -- uv run polytypst "SCAN" --backend "BACKEND" --pages 1-10 --formats typst,latex,pdf`
   Add `--lang` and `--domain` only for a new book.
2. Wait for the command to exit. Read the log once at the end.
3. Open 3 pages from `STORE/KEY/markdown_pages/` next to the same pages in `OUT/page_renders/`. Compare words, numbers, tables, math and line order.

Gate 2: the command exited 0, pages 1 to 10 each have a Markdown page, and your 3 samples match their renders. If not, stop and report the bad pages.

## STEP 3. The whole book

1. Run once in the background, with its output in `OUT/logs/ocr_full.log`:
   `mise exec -- uv run polytypst "SCAN" --backend "BACKEND" --formats typst,latex,pdf`
   Add `--lang` and `--domain` only for a new book. After a trial, the trial pages stay as they are.
2. When it exits 1 with "N pages still pending", run the same command again. It transcribes only those pages. Repeat until it exits 0, at most 3 times.
3. For a Colab BACKEND, run `uv run polytypst-colab usage`. When it shows an active VM whose name your log printed, stop that VM with the colab CLI. Never stop a VM that another run started.

Gate 3:
- `markdown_pages` holds one file for each PNG in `page_renders`, and no page is empty.
- The log ends with "Verified N pages. Discrepancies found on M pages."
- You compared each flagged page with its render, and fixed each real error in STORE or listed it with its page number. The log names each flagged page and its reason on a `[Page N]` line under "Verified". On a Chinese or Japanese book, the cross-check flags many false pages, so treat its flags as hints.
- Each page that you fixed in STORE has a correction: `gate` in Step 6 fails for an edited page with none. Before you edit a page, copy it to `OUT/before/`. After the edit, run `uv run polytypst corrections record KEY PAGE --kind ocr --before "OUT/before/p_NNN.md" --after "STORE/KEY/markdown_pages/p_NNN.md" --scan-reads "WHAT THE SCAN PRINTS" --evidence "OUT/page_renders/p_NNN.png"`. It finds the changed lines itself.
- For a Colab BACKEND, usage shows 0 active VMs of this run.

## STEP 4. Build and compile

1. For a new book, first write its spec: run `uv run polytypst new-book KEY --title "TITLE" --author "AUTHOR" --source "SCAN FILE NAME" --pages N --domain DOMAIN`, then fill in its chapters in `books/KEY/book.toml` from the scan's contents page.
2. Run: `mise exec -- uv run python scripts/one_book.py KEY build --formats pdf,tex`
3. Run: `mise exec -- typst compile --root / "OUT/build/FILE.typ" "OUT/FILE.pdf"`. It must exit 0.
4. Run: `tectonic -X compile --keep-logs -o "OUT/latex" "OUT/build/FILE.tex"`. It writes its PDF and its log to `OUT/latex/`, apart from Typst's PDF. It must exit 0. Search the log for "Undefined control sequence", "Missing $", and overfull boxes wider than 10pt. Never run `xelatex`. When `tectonic` is not on PATH, report Gate 4's LaTeX part as blocked.

5. When a compile fails or a page looks wrong, find the cause with these commands before you write a script:
   - `mise exec -- uv run polytypst page-check lint KEY` lists broken tags, broken LaTeX and dead `book.toml` rewrites in the transcript and the built `.typ`, each with its page.
   - `mise exec -- uv run polytypst page-check clean KEY PAGE --diff` shows what the page cleaner changes on one page.
   - `uv run python scripts/crop_sheet.py "OUT/logs/look.png" --across "SCAN" --across "OUT/FILE.pdf" --across "OUT/latex/FILE.pdf" --frame --pad 0.25,1 "Fig 2=~No solution. (b) Infinitely many" "Table 1=~TABLE 1 Reflections"` sets each named figure, table or formula of the scan beside both rebuilt PDFs in one image. After `~`, give words that stand only at that place, such as the caption's own text: `FIGURE 2` alone stands in every section. `scripts/figure_sheet.py "OUT/figures" "OUT/logs"` sheets every figure crop.

6. Fix the figures yourself. Follow "Figures" in `docs/scanned-books.md`.
   - Run `uv run python scripts/figure_sheet.py "OUT/figures" "OUT/logs"` and `uv run python scripts/figure_sheet.py --pdf "OUT/FILE.pdf" "OUT/logs"`, and look at every sheet.
   - Each caption in the scan has one figure, with its own file name. A crop holds the whole drawing and none of the caption, notes or body text. Set a bad crop's box in a `draw_figures(out_dir)` function in `books/KEY/hooks.py`.
   - Each figure prints at about the scan's size, under its own caption, in both PDFs.
7. With REPRODUCED_FIG `true`, draw each figure again, chapter by chapter. The quality of the scan crop does not matter here: it only shows you what to draw.
   - Follow step 2 of "Add another book" in `docs/scanned-books.md`. Register every figure in a `FigureBook`, one `figures_chN.py` for each chapter, as `books/kodaira/figures.py` does. Set `require_vector_figures = true` only when every figure has its SVG.
   - Content comes first. The redraw holds every curve, point, region, arrow, axis value and label of the scan figure, in the same places and proportions, and adds none. Set labels as math, not as plain letters.
   - Then the look. Draw every figure in FIG_STYLE and FIG_COLOR, to the standard of a professional publisher: one set of stroke weights, fonts, arrowheads and margins for the whole book, labels that touch no line, and no clipped edge.
   - After each chapter, build, then set each redraw beside its scan crop with `scripts/crop_sheet.py`, and look at every sheet. Redo a figure whose content differs from the scan.
   - A figure that you cannot draw faithfully keeps its scan crop. List it in the report with its page.

Gate 4: both compile with exit 0, and you listed each LaTeX warning that you could not fix. Every caption in the scan has its figure in both PDFs, and you looked at every figure sheet. With REPRODUCED_FIG `true`, each figure is a redraw in FIG_STYLE and FIG_COLOR that you compared with its scan crop, or it is on your list of figures kept as crops.

## STEP 5. Check the words against the scan

Follow `docs/page-check-review.md` from Step 1 to Step 6.

- Run `uv run polytypst page-check chunks KEY --size 10`. For each range, follow `docs/page-check.md` yourself. Write each page record with `polytypst page-check record`, never by hand.
- With VERIFY_MODEL `none`, decide each queued claim yourself by following `docs/page-verify.md`. Otherwise run `uv run polytypst page-check verify KEY --model VERIFY_MODEL` in the background.
- Fix each real and scan_typo verdict as Step 4 of `docs/page-check-review.md` says.

Gate 5: `uv run polytypst page-check status KEY` shows every page checked and 0 unverified.

## STEP 6. Check the PDF

1. Follow Step 7 of `docs/page-check-review.md`. Run `polytypst page-check render --run` in the background: it takes about 50 minutes for 121 pairs.
2. Search the `.typ` and `.tex` sources in `OUT/build/` for these faults: inline math with spaces inside, like `$ x $`; an orphaned `{A}{B}` left from `\frac`; a single letter as a display equation; brackets that do not balance within a section; bullets in the bibliography.
3. Run: `uv run polytypst page-check gate KEY`

Gate 6: the last line of `gate` is `PASS`, and the source search finds 0 faults, or you list each remaining one.

## REPORT (your last message)

- Each command that you ran, with BACKEND exactly as written.
- Each gate: PASS, FAIL or BLOCKED, with the last lines of its output. Quote the whole `gate` output.
- The pages that the cross-check flagged, and what you did on each one.
- The figures: how many the scan has, how many you re-cropped, and with REPRODUCED_FIG `true`, how many you drew again and which ones stayed crops.
- For a Colab BACKEND, the compute units at the start and at the end.
- Every file that you created or changed, and what is still wrong, with page numbers.
