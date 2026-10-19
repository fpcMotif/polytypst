# Scanned books: build an edition and check it against the scan

This guide covers the commands that rebuild a scanned book and measure how closely the rebuilt PDF sits on the source scan. Three commands serve every book:

- `uv run polytypst books` lists each book and its editions. `[parity]` marks the editions you can check against the scan.
- `uv run polytypst build BOOK [--edition E]` builds one edition. The default edition is the first one listed.
- `uv run polytypst parity BOOK --edition E [--pages 31-40]` checks a rebuilt edition against its source scan.

Each command's `--help` gives its flags. This guide gives the order, the hidden inputs, and how to add a book. Bourbaki, *Commutative Algebra*, is the one book with parity editions today.

Terms (source scan, rebuilt PDF, page map, scan parity) are defined in `GLOSSARY.md`.

## Before you start

- Set `POLYTYPST_SOURCES` to the folder that holds the source scan, in the environment or in `mise.local.toml`. The spec's `source_pdf` names the file. Every tool also accepts `--source PATH`.
- `typst` must be on `PATH`. Fonts load from `fonts/`.
- Run Python through `uv run`. Run commands from the repository root, because output paths are relative (`output/bourbaki`).

## Bourbaki procedure

1. Build the facsimile: `uv run polytypst build bourbaki --edition facsimile`. The first run also writes the source OCR cache to `output/bourbaki/source_ocr/` (Apple Vision, one JSON file per page plus `pages.json`). Later runs reuse the cache.
2. Build the vintage edition: `uv run polytypst build bourbaki --edition vintage`. It forces the scan's line breaks, so it reads the source OCR cache. It runs OCR first when the cache is missing.
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

A page also fails when fewer than half of its scan words match a rebuilt word. A low match share points to OCR errors or missing text, not to drift. The tolerances live in `polytypst/parity/report.py`.

Diagrams are the Typst snippets `fig_PPP_NNN.typ`, where `PPP` is the source page. Parity renders each snippet through `polytypst/parity/diagram_harness.typ` in the book's `DiagramText`, finds it on both pages, and reports dx, dy and the scale.

## Add another book

A book is a package `polytypst/<key>/` with a `book.py` that defines `BOOK`. `polytypst/books.py` finds every such file, so no shared file names a book. The key is the package name and the folder under `output/`.

1. Write `polytypst/<key>/book.py`. Set `BOOK = Book(spec, OUTPUT / "<key>", {name: edition, ...}, figures)`. `monograph_edition(spec, out_dir, summary)` makes an edition that compiles the OCR pages. `figures` is optional and draws code-reproduced figures before each build. `polytypst/kodaira/book.py` is the smallest model.
2. Run `uv run polytypst books` and confirm that the book and its editions appear.
3. To check an edition against its scan, set `source_pdf` on the book's `MonographSpec` to the scan's file name. Then pass `parity=Parity(page_map, tolerance, diagrams, diagram_text)` to the edition. `diagrams` and `diagram_text` are needed only when the book has diagram snippets. `polytypst/bourbaki/book.py` is the model to follow.
4. Run `uv run polytypst parity <key> --edition <edition> --pages <a few pages>`, and read the overlays before you run the whole book.
