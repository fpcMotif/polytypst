# Scanned books: build an edition and check it against the scan

This guide covers the commands that rebuild a scanned book and measure how closely the rebuilt PDF sits on the source scan. Four commands serve every book:

- `uv run polytypst books` lists each book and its editions. `[parity]` marks the editions you can check against the scan.
- `uv run polytypst build BOOK [--edition E] [--formats pdf,tex]` builds one edition. The default edition is the first one listed. By default it makes every format of the edition. `--formats` picks a subset of the PDF, LaTeX and EPUB steps, and the steps run in parallel. A monograph edition always writes Markdown and Typst, so `--formats ""` checks text only. The Bourbaki facsimile has no optional formats, because its PDF is its only output.
- `uv run polytypst parity BOOK --edition E [--pages 31-40]` checks a rebuilt edition against its source scan.
- `uv run polytypst new-book KEY --title T ...` writes the package of a new book. See [Add another book](#add-another-book).

Each command's `--help` gives its flags. This guide gives the order, the hidden inputs, and how to add a book. Bourbaki, *Commutative Algebra*, is the one book with parity editions today.

`GLOSSARY.md` defines the terms source scan, rebuilt PDF, page map, scan parity, transcript, transcript store, backend and line cache.

## Before you start

- Set `POLYTYPST_SOURCES` to the folder that holds the source scan, in the environment or in `mise.local.toml`. The spec's `source_pdf` names the file. Every tool also accepts `--source PATH`.
- `typst` must be on `PATH`. `mise.toml` pins it, so `mise exec --` or `mise run` puts it there. Fonts load from `fonts/`.
- To turn a PDF page into an image, use pymupdf: `doc[n].get_pixmap(dpi=300).save(path)`. ImageMagick, `mutool`, `pdftoppm` and `rsvg-convert` are not installed.
- Run Python through `uv run`. Run commands from the repository root, because output paths are relative (`output/bourbaki`).

## Transcribe the scan

A monograph edition compiles the transcripts in the book's transcript store, `output/<key>/<markdown_dir>/`. To fill the store, run `uv run polytypst SCAN.pdf -o output/<key> --backend BACKEND`. The command renders the pages to `page_renders/`, finds the figures, and sends each page that has no transcript to the backend. A blank page gets a blank-page marker and goes to no backend.

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
3. When vintage page heights drift, run `uv run python scripts/bourbaki_fit.py [ROUNDS]`. It rewrites `output/bourbaki/page_fit.json` and recompiles the vintage Typst source with `typst query` on each round. After it finishes, run step 2 again so the PDF uses the new fit.
4. Optionally, to tune the vintage typeface, run `uv run python scripts/bourbaki_linebreaks.py [NAME=k=v,...]`. It scores Typst input settings by how many scan line endings they reproduce, and writes `output/bourbaki/linebreaks.json`.
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

Diagrams are the Typst snippets `fig_PPP_NNN.typ`, where `PPP` is the source page. Parity renders each snippet through `src/parity/diagram_harness.typ` in the book's `DiagramText`, finds it on both pages, and reports dx, dy and the scale.

## Add another book

A book is a folder `src/<key>/` with a `book.py` that defines `BOOK`. The folder installs as the package `polytypst.<key>`. `src/books.py` finds every such file. Only `pyproject.toml` and `tests/test_books.py` name each book. The key is the folder name and the folder under `output/`. The key must be a Python identifier.

1. Run `uv run polytypst new-book <key> --title T --author A --source <scan file> --pages N`. The command writes `src/<key>/__init__.py`, `spec.py` and `book.py`. It also adds `"polytypst.<key>"` to `packages` in `pyproject.toml`.
2. Fill in the chapters, sections and figure layout in `src/<key>/spec.py`. The generated `book.py` sets `BOOK = Book(spec, OUTPUT / "<key>", {"monograph": monograph_edition(...)})`. `monograph_edition(spec, out_dir, summary)` makes an edition that compiles the OCR pages. To draw code-reproduced figures before each build, pass a `figures` function as the fourth argument. `src/kodaira/book.py` is the smallest model.
3. Add the spec to `test_specs_come_from_the_editions` in `tests/test_books.py`. If the spec is missing there, that test fails.
4. Run `uv run polytypst books` and confirm that the book and its editions appear.
5. To check an edition against its scan, set `source_pdf` on the book's `MonographSpec` to the scan's file name. Then pass `parity=Parity(page_map, tolerance, diagrams, diagram_text)` to the edition. The edition needs `diagrams` and `diagram_text` only when the book has diagram snippets. `src/bourbaki/book.py` is the model to follow.
6. Run `uv run polytypst parity <key> --edition <edition> --pages <a few pages>`, and read the overlays before you run the whole book.
