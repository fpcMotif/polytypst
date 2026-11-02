# Table layout check of rebuilt books

Paste this prompt into an agent session, and fill in VALUES first. The agent rebuilds the Typst PDFs of the named books, measures every table page, looks at a spread sample of table pages, and fixes the general table rules in `src/compiler/tables.py`. It finishes when every gate passes, or when it reports which gate failed, with the gate's output.

## VALUES

- ROOT: `/Users/martinfan/devv/polytypst`, or the workspace that the run must use.
- BOOKS: the book keys to check, such as `1 2 3 4 5 6`.
- PER_BOOK: the number of table pages to look at in each book. `17` gives about 100 pages for six books.
- MODE: `check` to report only, or `fix` to change the table rules and rebuild.

## RULES

- Work in ROOT. Run Python as `uv run`, never bare `python` or `python3`. Put every path in double quotes.
- Build Typst PDFs only: `mise exec -- uv run python scripts/one_book.py KEY build --formats pdf`. TeX Live is not installed. Never run `xelatex`, `tlmgr`, `latexmk` or `--formats latex`.
- Fix a rule, never a page. A change goes in `src/compiler/tables.py` (or the shared code that produces the defect) and holds for every book. Never edit a generated `.typ` file in `output/`, and never add a per-table exception.
- A transcript defect is not a layout defect. When the cells of a row do not match the header (a row with more cells than the header, two numbers in one cell, a note row inside the table), report the book, the page and the table. Do not fix it in the compiler.
- Keep checks as they are. Leave every existing test unchanged unless your rule change is meant to change that output; then update the expectation and say why. Never weaken an assertion to pass.
- Each new rule gets a test in `tests/test_pipe_tables.py`. Watch the test fail with the old rule before you keep it.
- Report a check as passed only when you ran it in this session. Quote the last lines of its output.
- Leave version control alone: no commit, no push, no pull request.

## What a good table looks like

1. Every column of numbers or short labels has its natural width. No number touches the number in the next cell.
2. A column of text labels gets the rest of the line, and at least the width that most of its labels need. Labels do not stack one or two characters per line.
3. A long header breaks into two balanced lines at a natural point: after ：，、 or a space, or before an opening bracket. No line holds one lone character, such as "年", "岁" or "率". A header never breaks inside math, such as "$U M S T_t$". A wrapped row label never leaves one character on its last line, such as "汽车及配件制造 / 业".
4. A table that is too wide for the text column first tightens its side padding, then shrinks its type to 92% or 85%. A table that still does not fit turns 90° with its caption and floats, so text fills the page around it.
5. A caption stays on the page of its table. No page shows a large empty area that text could fill.
6. A data cell uses the minus sign "−", not the hyphen "-".

## STEP 1. Rebuild

1. For each KEY in BOOKS, run the build command above in the background, three at a time. Each build writes `output/KEY_*/KEY.pdf`.

Gate 1: every build exited 0, and no build log holds `Traceback` or `error:`.

## STEP 2. Measure

1. Run: `uv run python scripts/table_check.py measure output/KEY_*/KEY.pdf ...` with one PDF for each KEY.
2. For each page that the output lists, render it with `uv run python scripts/page_png.py PDF PREFIX --pages N --dpi 110` and look at it. A "stacked" page whose single characters are figure axis labels is not a defect.

Gate 2: no page has touching numbers, unless you traced it to a transcript defect and reported it.

## STEP 3. Look at a sample

1. Run: `uv run python scripts/table_check.py sample "SAMPLE_DIR" --per-book PER_BOOK output/KEY_*/KEY.pdf ...`
2. Open every PNG in SAMPLE_DIR. For each table, check the six points of "What a good table looks like". Ignore figures, OCR word errors and prose.
3. Write one line for each page: `b1p47: OK`, or the point number, the place and the visible text, such as `b5p71: 3 — "前期（1981—1989 / 年）" leaves a lone "年"`.
4. Sort the defects into layout defects (a rule in the compiler) and transcript defects (the cells themselves).

Gate 3: every sampled page has a line, and every defect is sorted.

## STEP 4. Fix the rules

Skip this step when MODE is `check`.

1. For each layout defect that repeats on two or more pages, find the rule that causes it in `src/compiler/tables.py`. Print the generated Typst for that table from `output/KEY_*/KEY.typ` and measure each width tier, before you change code.
2. Change the rule. Add a test that fails with the old rule and passes with the new one.
3. Run `mise exec -- uv run pytest -q`. Two failures are known and unrelated: `test_damaged_real_ocr_pages_compile_and_keep_their_neighbour_pages` and, under load, `test_a_runner_that_stops_writing_is_killed_after_the_lines_it_wrote`.
4. Repeat steps 1 to 3 of this prompt for every book. Compare the new counts and the new sample with the old ones.

Gate 4: the tests pass except the two known failures, and no measure or sample got worse.

## REPORT

1. A table of the measure counts for each book, before and after.
2. The sample lines, grouped into layout defects fixed, layout defects left, and transcript defects.
3. Each changed file as `path:line`, with the rule that changed.
4. Each check that you ran, with its command and its last output lines.
