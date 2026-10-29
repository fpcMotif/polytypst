# Scanned books: build an edition and check it against the scan

This guide covers the commands that rebuild a scanned book and measure how closely the rebuilt PDF sits on the source scan. Four commands serve every book:

- `uv run polytypst books` lists each book and its editions. `[parity]` marks the editions you can check against the scan.
- `uv run polytypst build BOOK [--edition E] [--formats pdf,tex]` builds one edition. The default edition is the first one listed. By default it makes every format of the edition. `--formats` picks a subset of the PDF, LaTeX and EPUB steps, and the steps run in parallel. A monograph edition always writes Markdown and Typst, so `--formats ""` checks text only. The Bourbaki facsimile has no optional formats, because its PDF is its only output.
- `uv run polytypst parity BOOK --edition E [--pages 31-40]` checks a rebuilt edition against its source scan.
- `uv run polytypst audit [BOOK] [--edition E]` checks every built format and counts any literal numbers or unlinked references/citations (`src/literal_numbers.py`) against `quality/baseline.json`.
- `uv run polytypst new-book KEY --title T ...` writes the package of a new book with `cross_references=True`. See [Add another book](#add-another-book).

Each command's `--help` gives its flags. This guide gives the order, the hidden inputs, and how to add a book. Bourbaki, *Commutative Algebra*, is the one book with parity editions today.

`GLOSSARY.md` defines the terms source scan, rebuilt PDF, page map, scan parity, transcript, transcript store, backend and line cache.

## Before you start

- Set `POLYTYPST_SOURCES` to the folder that holds the source scan, in the environment or in `mise.local.toml`. The spec's `source_pdf` names the file. Every tool also accepts `--source PATH`.
- Set `POLYTYPST_BOOKS` to the folder that holds each book's state. If it is not set, `build`, `audit` and the transcript tools stop with `BookStateError`. Under `mise exec`, the value in `mise.local.toml` replaces an exported one. Run `mise exec -- printenv POLYTYPST_BOOKS` and edit the transcripts in that folder, `$POLYTYPST_BOOKS/<key>/markdown_pages/`.
- `polytypst build` and `polytypst audit` import every book, so a broken spec in one book stops them for all. Then run `mise exec -- uv run python scripts/one_book.py KEY build` or `... KEY audit`, which imports only that book. For a book with no entry in `quality/baseline.json`, run `... KEY audit --save before.json` before a change and `... KEY audit --against before.json` after it. Each rule whose count rose or fell prints. `--issues RULE,...` prints the page and text of each issue of those rules. `... KEY cli COMMAND [ARGS]` runs any other `polytypst` command, such as `review` or `parity`, with only that book loaded.
- `typst` must be on `PATH`. `mise.toml` pins it, so `mise exec --` or `mise run` puts it there. Fonts load from `fonts/`.
- To turn PDF pages into images, run `uv run python scripts/page_png.py PDF OUT_PREFIX --pages 58,59 [--dpi 300] [--clip L,T,R,B]`. `--clip` keeps a box in shares of the page, so a figure's labels can be read at print size. ImageMagick, `mutool`, `pdftoppm` and `rsvg-convert` are not installed.
- Run Python through `uv run`. Run commands from the repository root, because output paths are relative (`output/bourbaki`).

## Transcribe the scan

A monograph edition compiles the transcripts in the book's transcript store, `$POLYTYPST_BOOKS/<key>/<markdown_dir>/`. To fill the store, run `uv run polytypst SCAN --backend BACKEND`, and add `--book KEY` when the scan's file name does not name the book. SCAN is a PDF, a folder of page images, or one image. The command picks the book in this order: the `--book` key, then the book whose slug, `source_pdf` or `pdf_name_markers` match the file name. A page count never picks a book. A scan that matches no book becomes a new one-chapter book in `output/<slug>/`, or in the `-o` folder. A known book always writes to `output/<key>/`. In a folder, the pages follow the natural order of the file names, so `IMG_99.jpg` comes before `IMG_100.jpg`. When most of the first five sheets are landscape, each sheet is split down the spine into two pages. The command renders the pages to `page_renders/` and records the source and settings in `renders.json`. A later run renders only the missing pages, or all pages again when the source or settings change. The command then finds the figures and sends each page that has no transcript to the backend. Figure extraction runs only on an unsplit PDF, because it reads the PDF's text layer. A blank page gets a blank-page marker and goes to no backend. Last, the command builds the book's first edition, the same build that `polytypst build KEY` runs.

| Backend | Runs on | Needs |
| --- | --- | --- |
| `colab` (the default) | Colab GPUs with a self-hosted model | the `colab` CLI, signed in |
| `local:MODEL` | this machine's GPU, MPS or CPU | the model's Python packages |
| `gemini[:MODEL]` | the Gemini API | `GEMINI_API_KEY` |
| `openai:MODEL` | an OpenAI-compatible API, such as vLLM or Ollama | `OPENAI_API_KEY`, or `key_env=` for a server without a key |
| `jina` | the Jina API | `JINA_API_KEY` |
| `mistral` | the Mistral OCR API | `MISTRAL_API_KEY` |
| `cached:?dir=PATH` | the transcripts in another folder | nothing |

Options follow a `?`, as in `colab?gpu=A100&workers=3` or `openai:qwen2.5-vl?base_url=http://gpu-box:8000/v1&key_env=`. An unknown option stops the command and lists the valid options. `uv run polytypst-colab gpus` shows which self-hosted model fits which Colab GPU.

Varlock reads the API keys from the macOS Keychain, through `.env.schema`. To add a key, run `security add-generic-password -s polytypst.GEMINI_API_KEY -a "$USER" -w`. Then `varlock load` shows the key as set.

`transcripts.json` records the backend, the model and a hash of the prompt for each transcript. If you change the backend or the book's `ocr_prompt`, the store keeps the old transcripts and reports their count. To redo them, add `--retranscribe`. To limit a run to some pages, add `--pages 3,7-9`.

If a page keeps failing, the store leaves it pending and reports it at the end, so a second run tries it again. If the backend fails as a whole, the command stops. A rejected key, a missing key, a missing Colab CLI, and five failed pages in a row are such failures.

## Bourbaki procedure

1. Build the facsimile: `uv run polytypst build bourbaki --edition facsimile`. The first run also writes the line cache to `output/bourbaki/source_ocr/`, with one JSON file per page, `lines.json` and `pages.json`. Apple Vision makes the lines on macOS, and Tesseract makes them elsewhere, in English and French. Later runs reuse the cache.
2. Build the vintage edition: `uv run polytypst build bourbaki --edition vintage`. It forces the scan's line breaks, so it reads the line cache. It runs OCR first on the pages that the cache lacks.
3. When vintage page heights drift, run `uv run python books/bourbaki/tools/fit.py [ROUNDS]`. It rewrites `$POLYTYPST_BOOKS/bourbaki/page_fit.json` and recompiles the vintage Typst source with `typst query` on each round. After it finishes, run step 2 again so the PDF uses the new fit.
4. Optionally, to tune the vintage typeface, run `uv run python books/bourbaki/tools/linebreak_search.py [NAME=k=v,...]`. It scores Typst input settings by how many scan line endings they reproduce, and writes `$POLYTYPST_BOOKS/bourbaki/linebreaks.json`.
5. Check each edition: `uv run polytypst parity bourbaki --edition facsimile`, then `--edition vintage`. Add `--pages 31-40` for a page range. The vintage page map comes from the `<src-mark>` markers in `output/bourbaki/bourbaki_1970_vintage.typ`, so run step 2 before this step.
6. Open `output/bourbaki/parity_<edition>/index.html`. Use "fail" and "worst word first" to find the pages to fix. In each overlay, red ink is only on the scan, cyan ink is only in the rebuilt PDF, and black ink is in both. The CSV beside it has one row per page.

The edition is done when `polytypst parity` exits with status 0. It exits with status 1 when any page breaks the edition's tolerance.

## What parity measures

Scan parity compares ink with ink, in points, with no shift between the pages. On the scan, the words come from the OCR lines, split at the ink gaps between words. On the rebuilt PDF, the words come from the text layer. Each word's box is the ink inside its text box, and its baseline is the glyph origin.

| Tolerance | Used by | Words | Page offset | Lines | Diagrams |
| --- | --- | --- | --- | --- | --- |
| `FACSIMILE` | facsimile | every word within 0.5pt; at most 1% of words over | 0.3pt | not checked | 1pt, 2% scale |
| `SOURCE_PAGINATED` | vintage | 1.5pt, only on lines that break where the scan breaks | 1pt | every baseline within 1.5pt; same line count; no overflow | 1pt, 2% scale |

A page also fails when fewer than half of its scan words match a rebuilt word. A low match share points to OCR errors or missing text, not to drift. The tolerances live in `src/parity/report.py`.

## Optical parity

`polytypst parity BOOK --edition E --visual` compares only the ink of the two page images. It reads no OCR and no text layer, so it works for any edition with a page map, in any language and typeface. Rebuilt ink with no scan ink within 1pt is extra. Scan ink that the rebuilt page lacks is missing. Differing ink closer than 6pt along a line, or 2pt across lines, joins into one boxed region, and regions under 4pt² are dropped.

The report goes to `output/<book>/visual_<edition>/`. `index.html` crops the book's largest regions with the scan above the rebuilt page, and then lists every differing page with its overlay, worst first. `regions.csv` has one row per region, and `summary.json` has the counts and the mean extra and missing share per page. `--top N` sets how many regions get crops; the default is 100.

To check a change, keep a copy of the PDF from before it and pass that copy as `--against OLD.pdf`. This implies `--visual`. The report then adds the old build to each crop. A page improves or regresses when its extra plus missing share falls or rises by more than 0.002. The command exits with status 1 when any page regressed. The regions measure every difference, including a different math typeface, so use the ranking to choose what to fix, and use `--against` to see that a fix made no page worse.

To set a limit for every page, pass `--max-missing SHARE`, `--max-extra SHARE`, or both. A share is a number from 0 to 1, such as `0.3`. Each flag implies `--visual`. The command lists the pages whose missing or extra share is above the limit, and then exits with status 1. On the Grothendieck facsimile, `--max-missing 0.3` fails on pages 1 and 468–474.

Diagrams are the Typst snippets `fig_PPP_NNN.typ`, where `PPP` is the source page. Parity renders each snippet through `src/parity/diagram_harness.typ` in the book's `DiagramText`, finds it on both pages, and reports dx, dy and the scale.

## Fix a monograph's figures, tables, notes and equations

These rules come from book 4, `src/4_不良债权与金融危机/`, book 3, `src/3_国际经济环境的变化与日本经济/`, book 6, `src/6_劳动力市场与收入分配/`, and book 1, `src/1_宏观经济与产业结构/`. Use those books as the models. After each fix, rebuild the edition, find the changed pages with `uv run python scripts/find_pages.py PDF "TEXT"`, and look at them next to the scan with `scripts/review_sheet.py`. Stop when the page looks like the scan and no audit count rises.

### Figures

- **Size.** The default `FigureLayout.png_max_height_ratio=0.38` limits a figure's height to 0.38 of its width, so most charts print small. To print figures at the scan's size, set `pair_figures=False`, `png_single_range=(50, 100)` and `png_max_height_ratio=1.3`. Also set `png_single_divisor` to the pixel width of a crop that fills the text width: the scan's text width in points × the crop dpi / 72. For book 6, 356 pt at 600 dpi gives 2966, so each figure keeps its share of the scan's line.
- **Code-drawn SVG figures.** Set `svg_single_pct=100` and `pair_figures=False`, so that each figure fills the text width. A tall figure then pushes its caption to the next page. The `typst_front_matter` in book 1's `book.toml` adds a Typst `#show image` rule that caps an image's height at 330pt, about 60% of the text block.
- **Figures printed twice.** The OCR often writes an inline `![](figures/fig_…)` link as well as the caption line that places the same figure. Compare `rg -c 'image\(' output/<key>/<slug>.typ` with the number of figures. Drop the inline links with a `pre_math_rewrites` entry, as book 1 does. Before that, give a figure that has only an inline link a caption line in the transcript, or the figure is lost.
- **Bad crops.** Run `uv run python scripts/figure_sheet.py output/<key>/figures OUT_DIR` and look at each sheet. A crop that holds only notes, a cut chart, or a caption with no `fig_*.png` is bad.
- **Figures on the page.** Run `uv run python scripts/figure_sheet.py --pdf PDF OUT_DIR [--pages 180,323]`. It sheets the rebuilt pages that hold an image. A figure printed too small, two charts squeezed side by side, or a crop edge that catches half of a note line shows at print size. To set a crop edge, look at the bottom tenth of the crop PNG. The note line under a chart sits about 0.01 of the page height below its axis labels.
- **Re-crops.** Write a `draw_figures(out_dir)` function in `books/<key>/hooks.py`, and bind it with `figures = 'draw_figures'` in the `[hooks]` table of `book.toml`. It runs before each build. Give each figure its scan page and a box in fractions of the page, and crop the scan at 600 dpi. To join panels from two pages, stack the crops into one image. Leave out the caption, the notes and the source line, because the transcript keeps them as text.
- **Figures that start a page early.** When a chart starts on the scan page before its caption, crop both pages in a `prepare(source)` function in `hooks.py`. Name it with `prepare = 'prepare'` in the edition's `[editions.<name>]` table. It runs before each build of that edition. Book 6's `figures.py` either stacks the two crops into one image or keeps the early panels as a separate uncaptioned image. A `page_fixups` rewrite (`r"\Z"` → `"\n\n![](figures/fig_10-26-panels.png)"`) places that image on the early page.
- **Figure text.** The transcript often repeats text that the image shows: axis labels, panel titles, legends, or a diagram typed as tables. Delete that text with a `page_fixups` rewrite. If you keep it, it prints twice or becomes a footnote. `mise exec -- uv run python scripts/figure_leaks.py KEY` lists each transcript line that matches OCR text inside a figure box. `mise exec -- uv run python scripts/transcript_lint.py KEY --check labels` lists short panel titles such as "（1）日本" near a figure. Both read the transcripts after the page fixups, so a fixed book lists nothing.
- **Captions, figure notes and footnotes.** The cleaner takes captions, figure notes and, for a book with a `footnote_style`, footnotes out of the page text before `page_fixups` run, so a page fixup cannot change them. Use a `[transcript_fixups]` table in `book.toml` instead. It has the same form as `[page_fixups]`, and it runs on the transcript before the cleaner reads it. Book 4 uses it to correct scan typos in two captions and one figure note.

### Tables

- **Shifted second row.** In a table's first two rows, the Typst writer merges an empty cell into a colspan of the filled cell before it. A `rowspan="2"` header leaves such an empty cell in row 2, and a first data row with blank cells has them too. The filled cell then spans the blank columns, and every cell after it moves right. Run `mise exec -- uv run python scripts/table_headers.py KEY`. It lists each table that the build will shift, and a fixed table prints nothing.
- **Fix a shifted row.** In the transcript, drop the `rowspan` from row 1 and give row 2 one cell for every column. Then fill each empty cell in row 2 with U+2060 (a word joiner) through a `page_fixups` rewrite on the pipe-table line, as page fixup 132 in book 3's `book.toml` does. The transcript store deletes invisible characters, so a U+2060 typed in the transcript is lost. `page_fixups` run after the store reads the page.
- **Band row.** A row that names a group, such as a country across the whole table, prints as a shaded full-width band when its only cell is `**text**`.
- **Transcript damage.** Compare each table with the scan cell by cell. OCR adds stray letters ("C钢铁"), cuts a header into a stray line (". 贸易自由化"), and misreads labels ("93SMA"). When the structure is past repair, write the table again as a pipe table that you read from the scan.

### Notes

- A note binds to the first glyph in its page body that matches its mark. When an enumeration such as "；③其他情况" comes before the real call "其他情况③", the note binds to the enumeration.
- Run `uv run python scripts/note_bindings.py $POLYTYPST_BOOKS/<key>/markdown_pages`. It lists each note whose mark occurs more than once on its page, and the place where the note binds.
- If a note binds to an enumeration, give the real call and the note line a mark that the page does not use, such as ⑳. Typst numbers the notes in order, so the printed mark stays correct. Dingbat digits (➀) do not work, because the transcript reader changes them to ①.
- A note mark on a chapter title is lost, because the compiler takes the chapter heading from the spec. Move the mark to the byline with a `page_fixups` rewrite. `uv run python scripts/lone_marks.py PDF` lists each mark that prints alone on a line. A finished edition lists none.
- In a book with circled notes, the splitter takes a body line that starts with "(1)" for note 1. It runs before `page_fixups`, so change the line in the transcript store itself, for example "(1)" to "（1）". `mise exec -- uv run python scripts/transcript_lint.py KEY --check notes` lists each note whose key is not a circled digit.
- A body line that starts with ① and has no call above it, such as "①实际资本存量" in an appendix list, stays in the body. The splitter keeps such uncalled lines. The scan prints them as plain text, so leave the mark as text. `TYPST_LITERAL_ITEM_HEAD` counts each one.
- When two figures in a row each have a note above the caption, both notes print under the second figure. `transcript_lint.py KEY --check repeats` lists two identical notes in a row. A page fixup cannot move them back, because the compiler places the figures first.

### Equations

- A long display equation on one line shrinks to fit the text width, sometimes to 4 pt. In the transcript, split it into `\begin{aligned} ... \end{aligned}` lines that each fit the width.
- A multi-line equation prints no number today, even when the transcript has `\quad (10.8)` after it. The equation pattern in `TypstWriter.events` (`src/compiler/source_numbers.py:181`) matches `\\.` and so stops at the `\` that ends a Typst math line.

### Headings

- `heading_rewrites` run before the Typst writer escapes `#`, `[` and `]` (`src/compiler/monograph.py:1590`). A rewrite that writes a Typst call, such as `#enum(...)[\1]`, prints that call as text. Write Markdown in a rewrite, such as `###` or `**`.
- Book 1's `macro_heading_hook` is a general model. It returns `""` for running heads and chapter-title repeats, and text for bylines and table titles. It sets the level from the number's shape: `N.N.N` or `（N）` gives `####`, `N.N` gives `###`, and `N title` gives `##`.
- `heading_hook(line, chapter)` sees every line of the page. Return the heading text for each heading line. If the hook returns `None`, the shared cleaner drops a heading that an earlier chapter already had, such as "1 前言".
- The section rule reads `3 20世纪90年代…` as section 3 only when the title starts with a non-digit. Return `"### 3 ⁠" + title` from the hook. A title that starts with a number and has no section number, such as "20世纪90年代末之前的状况", needs `"### "` and its spaces removed, or it becomes section 20.
- The scan's own table of contents is not part of any chapter. Start the first front-matter `ChapterSpec` after it. Give each front-matter part (作者简介, 前言, 序) its own `ChapterSpec`, and have the hook return `""` for the scan's copy of that title.
- A running header that the cleaner removes as page furniture never reaches the hook. To keep a section heading that matches a running header, add it back with a `page_fixups` rewrite.
- Make each `running_header_regexes` entry require the folio, as in `\d{1,2}\s+TITLE\s+\d{1,3}$`. A regex without it also drops a section heading that repeats a chapter title, such as "2 工会与雇佣调整" in chapter 6. Some running heads put the folio first, such as "89 结构性失业与错配". Drop a chapter-title line whose number is above the last chapter. The OCR can put spaces inside a running head, such as "20 世纪 80 年代后的 GDP 缺口". Put `\s*` between the characters of each title's regex, as the `running_header_regexes` in book 1's `book.toml` do. After a change to the hook or its regexes, run `transcript_lint.py KEY --check heads`. It prints each numbered line and what the hook makes of it.
- To print section numbers as the scan does, such as "2" and "2.1" with no §, set show rules in `typst_front_matter` and redefine `\sourcesection` and `\sourcesubsection` in `latex_preamble`. Both come after the shared numbering rules, so they win. The `typst_front_matter` in book 6's `book.toml` also sets the running heads: the book title on even pages and the chapter title on odd pages.

### Audit rises that are not defects

- `TYPST_UNLINKED_REFERENCE` and `LATEX_UNLINKED_REFERENCE` count a date such as "在3月28日" when the book has numbered articles.
- `LEAKED_RUNNING_HEADER` counts the book title in front-matter prose and in a chapter title such as "序 不良债权与金融危机".
- `CROSS_PAGE_WORD_SPLIT` counts an English term that breaks at a page end, such as "Total Factor / Productivity", after larger figures move the page breaks.
- `TYPST_LITERAL_ITEM_HEAD` rises when a ①②③ enumeration stops holding a wrong note and prints as text.
- `NO_SOLO_PAGE` counts a front-matter list, such as 作者简介, whose last line moves to a new page. The `@@PAGEBREAK@@` marker works only in Typst, so a page fixup cannot force a break for both formats.

## Add another book

A book is a folder `books/<key>/`. The key is the folder name, and any folder name without a dash works. `src/books.py` finds every folder that holds a `book.toml` or a `book.py`. Nothing else lists the books, and the `polytypst` package does not contain them. A book loads only when a command uses it.

- **`book.toml`** describes a book with data only. Its top-level keys are the fields of `MonographSpec` (`src/compiler/monograph.py`), with the same names. Write regexes and preambles as literal strings (`'...'` or `'''...'''`), so that backslashes stay as written. `@REPO@` in a string becomes the repository folder, for example `[Path=@REPO@/fonts/]`. `@BOOK@` in a path becomes the book folder, for example `diagram_dir = '@BOOK@/diagrams'`. `@ENGINE_TITLE_PAGE@` in `typst_front_matter` and `@ENGINE_PREAMBLE@` in `typst_preamble` become the compiler's own title page and preamble for that spec. `aliases` lists other keys for the book. Each `[editions.<name>]` table makes a monograph edition, with a `summary` and an optional `[editions.<name>.spec]` table of fields that differ from the top level. An edition with `kind = 'facsimile'` takes its `FacsimileStyle` fields from an `[editions.<name>.facsimile]` table. The first edition is the default. The loader rejects an unknown key, a wrong type or a bad value, and names the file and the key. `books/hecke/book.toml` and `books/fermat/book.toml` are the models, and `books/fga/book.toml` is the model for a facsimile edition.
- **`hooks.py`** holds the functions of a book that needs code: figure functions, a heading hook, a `prepare` step or facsimile diagram boxes. A function with the name of a field fills that field, such as `heading_hook`, `figures` or `install_diagrams`. A `[hooks]` table at the top level, or in an edition, binds a function with another name, as `heading_hook = 'macro_heading_hook'`. An edition's `prepare = 'NAME'` names its prepare function. Each public function must fill a field, so give a helper a leading `_`. `hooks.py` imports the engine as `from polytypst.edition import ...` and its own files as `from .figures import ...`. When a function needs the spec at run time, it imports `book_by_key` inside the function. `books/1_宏观经济与产业结构/` and `books/grothendieck/` are the models.
- **`book.py`** is only for a book that `book.toml` cannot describe, such as a parity page map or its own build pipeline. It defines `BOOK = Book(...)`. `books/bourbaki/` and `books/london_treasury/` are the two such books. A test reaches a file of a book with `polytypst.books.module("<key>", "<file>")`, and it reaches a spec with `book_by_key("<key>").spec`.

1. Run `uv run polytypst new-book <key> --title T --author A --source <scan file> --pages N`. The command writes `books/<key>/book.toml`.
2. Fill in the chapters, sections and figure layout in `books/<key>/book.toml`. To draw code-reproduced figures before each build, bind a `figures` function from `hooks.py` and set `require_vector_figures = true` in `book.toml`. Register every figure in a `FigureBook` (`src/vision/diagram_engine.py`) split by chapter (`figures_chN.py`), and verify zero missing IDs with `book.verify_completeness(out_dir)`. `books/kodaira/figures.py` is the model for SVG figures and `books/grothendieck/hooks.py` for `fig_PPP_NNN.typ` diagrams.
3. Run `uv run polytypst books` and confirm that the book and its editions appear.
4. To check an edition against its scan, set `source_pdf` to the scan's file name. A facsimile edition gets a one-to-one page map from its loader. Any other edition needs a `book.py` that passes `parity=Parity(page_map, tolerance, diagrams, diagram_text)` to the edition. The edition needs `diagrams` and `diagram_text` only when the book has diagram snippets. `books/bourbaki/book.py` is the model to follow.
5. Run `uv run polytypst parity <key> --edition <edition> --pages <a few pages>`, and read the overlays before you run the whole book.
