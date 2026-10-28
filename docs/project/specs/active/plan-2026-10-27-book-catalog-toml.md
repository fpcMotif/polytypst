# Feature: A book is a project with one key

**Date:** 2026-10-27 (last updated 2026-10-28)

**Author:** fpcmotif, with Claude

**Status:** Draft

## At a glance

One book is spread over five places today, and the places do not even share a key. `src/<key>/` holds the spec as a Python package. `pyproject.toml` lists that package. `$POLYTYPST_SOURCES` holds the scan. `$POLYTYPST_BOOKS/<name>/` holds the transcripts. `output/<name>/` holds everything else, with no fixed layout. In the last two places, `<name>` is the output folder name, which differs from the key for 7 output folders.
This plan treats a book as a project that polytypst compiles. Each book has one key and two folders. The **book folder**, `books/<key>/` in git, holds what a person writes: `book.toml`, an optional `hooks.py`, and hand-made figures. The **state folder**, `$POLYTYPST_BOOKS/<key>/` outside git, holds what the machine makes. It uses one fixed layout for each pipeline stage. A `Book` handle derives every path from the key.
The compiler, OCR backends, parity measures and CLI verbs stay the same. The source scans stay in `$POLYTYPST_SOURCES`. The transcripts that exist today are moved, never made again.

## Overview

The natural mental model is a pipeline with one owner for each stage:

```text
┌────────────┐   ┌───────────────────────┐   ┌──────────────┐   ┌──────────────┐
│ Source     │──▶│ Transcripts + lines   │──▶│ Editions     │──▶│ Parity and   │
│ scan       │   │ (OCR: slow, kept)     │   │ (build/)     │   │ review       │
└────────────┘   └───────────────────────┘   └──────────────┘   └──────────────┘
```

A book is the project. polytypst is the compiler that you point at it, as `typst compile` is pointed at a project folder. Who made a file decides where it lives:

| Made by | Example | Where | Kept? |
| --- | --- | --- | --- |
| A person | `book.toml`, `hooks.py`, hand-drawn SVG | book folder, in git | Yes, under version control |
| OCR | transcripts, line cache | state folder | Yes, because OCR is slow and costs money |
| A build or a check | `.typ`, `.pdf`, renders, parity reports | state folder | No. `polytypst clean` can delete them. |

## Goals

- One key names a book everywhere: the book folder, the state folder, the CLI argument and `book_by_key`.
- A volume or a variant is an edition of one book. It is not a separate output folder.
- A data-only book is one file, `books/<key>/book.toml`, with no Python, no `__init__.py` and no `pyproject.toml` entry.
- A book that needs code adds `books/<key>/hooks.py`. A book with a custom pipeline keeps `books/<key>/book.py`.
- `books.open(key)` returns a `Book` handle. Callers get every path from it, and no caller builds a path from `out_dir` or `book_state()`.
- Each state folder has the same fixed layout. Ad hoc folders such as `output/bourbaki/test_10_diagrams/` have no place in it.
- A broken book stops only the commands that use that book.
- `polytypst migrate-state` moves the existing state into the new layout. It shows a dry run first, and it never deletes a transcript.

## Non-Goals

- No change to `MonographSpec` semantics, the compiler, OCR backends, parity measures or vision.
- No move of source scans. `$POLYTYPST_SOURCES` and `source_pdf` stay as they are.
- No rename of engine modules to match the stages, such as `scan/`, `ocr/`, `compile/` and `check/`. See Open Questions.
- No move of `kerodon` and `taocp`. They have no `book.py`, and only `src/web_exporter.py` reaches them. See Open Questions. `goursat` is now `books/goursat/`, with its spec in `book.toml` and its figures hook in `hooks.py`.
- No JSON. See Design.

## Background

These facts come from the repository at commit `84d81df0` and from the state folder on 2026-10-28.

### One book in five places

| Place | What it holds | Named by |
| --- | --- | --- |
| `src/<key>/` | spec, hooks, figure code, diagrams | key |
| `pyproject.toml` | `polytypst.<key>` package entry | key |
| `$POLYTYPST_SOURCES/` | source scan | `source_pdf` file name |
| `$POLYTYPST_BOOKS/<name>/` | transcript store, `page_fit.json`, sometimes `source_ocr/` | output folder name |
| `output/<name>/` | renders, line cache, figures, rebuilt PDFs, reports | output folder name |

### The key changes from place to place

- `src/book_state.py:17` returns `Path(root) / Path(out_dir).name`. The state folder is named after the output folder, not after the key.
- 7 output folders differ from their key. They are `fermat → fermat2, fermat3`, `kenji_alg → kenji-alg, kenji-alg_vol1, kenji-alg_vol2`, `klein → klein_zh` and `siegel_symplectic → siegel-symplectic`.
- `src/books.py` hard-codes five aliases for `sga4_5`.

### Paths are built by hand

- `out_dir` appears 333 times in 49 files under `src/`. `OUTPUT` appears in 29 files.
- `book_state(...)` is called in 10 places. Four of them add `"markdown_pages"` by hand instead of using `spec.markdown_dir`. They are `src/vision/diagram_engine.py:538`, `src/vision/diagram_crops.py:107`, `src/goursat/build.py:192` and `src/1_宏观经济与产业结构/figures.py:72`.
- The transcript folder name is not fixed. Most books use `markdown_pages/`, but `$POLYTYPST_BOOKS/ahlfors/` uses `markdown/`.

### `output/` has no layout

- `output/` holds 73 folders for 28 books.
- `output/bourbaki/` alone holds 49 subfolders, for example `diagram_test`, `test_10_diagrams`, `redshift_fitted`, `parity_work` and `previews`.
- `$POLYTYPST_BOOKS` holds 35 folders. Some of them also hold a `source_ocr/` copy of the line cache.

### Books are packages

- `src/books.py:13` finds books at runtime with `PACKAGE.glob("*/book.py")`. The 26 `polytypst.<key>` entries in `pyproject.toml` exist only for setuptools.
- `src/new_book.py` rewrites `pyproject.toml` with the regex `PACKAGES_RE`. `tests/test_packaging.py` keeps the package list in step with the folders.
- The five folders with a numeric prefix are not valid package names. They ship through the `"[0-9]*/*.py"` package-data glob.
- `docs/scanned-books.md:19` says: "`polytypst build` and `polytypst audit` import every book, so a broken spec in one book stops them for all." `scripts/one_book.py` works around this.
- 14 test files import book modules directly, for example `polytypst.hecke.spec`.

### Which spec fields need code

`Rewrite` is `tuple[str, str]` (`src/compiler/monograph.py:49`), so rewrites and page fixups are data. These are the only `MonographSpec` fields that take functions:

| Field | Books that set it |
| --- | --- |
| `heading_hook` | 1_, 3_, 4_, 6_ (economics), bourbaki, fichtenholz_vol1 |
| `source_line_breaks` | bourbaki |
| `justify_page_end` | bourbaki |

Code also appears at the edition level:

- `Book.figures`, as in kodaira.
- `monograph_edition(prepare=...)`.
- `Parity.page_map`.
- `FacsimileStyle.install_diagrams`.

Every other field is data.

## Design

### Terms

- **Book**: a key, a book folder and a state folder.
- **Book folder**: `books/<key>/` in the repository. It holds what a person writes.
- **State folder**: `$POLYTYPST_BOOKS/<key>/`. It holds what the machine makes. The name `book_state()` already means this, and it keeps that meaning.
- **Edition**: one rebuild of a book, named inside the book, for example `monograph`, `vol2` or `facsimile`.

Phase 3 adds these terms to `GLOSSARY.md`.

### Layout

```diff
+ books/<key>/                    book folder, in git
+   book.toml                     metadata, chapters, editions
+   hooks.py                      optional functions for callable fields
+   book.py                       optional, only for a custom pipeline
+   site.toml                     optional: the book's pages on the website
+   tools/                        optional: scripts that serve only this book
+   figures/  diagrams/           hand-made SVG and Typst
+ $POLYTYPST_BOOKS/<key>/         state folder, not in git
+   transcripts/                  kept: p_NNN.md and transcripts.json
+   lines/                        kept: line cache, pNNN.json and lines.json
+   page_fit.json  linebreaks.json   kept: measured fits
+   renders/                      cache: page renders of the source scan
+   build/<edition>/              disposable: .typ .tex .pdf .epub, figures
+   work/<command>/               disposable: parity, review, facsimile ink, crops
- src/<key>/                      replaced by books/<key>/
- output/                         replaced by the state folders
```

Each `work/` subfolder belongs to one command, for example `work/parity/<edition>/`, `work/review/` or `work/ink/`. A command writes only its own subfolder. `polytypst clean <key>` deletes `build/`, `work/` and `renders/`. It never deletes `transcripts/`, `lines/` or the fit files.

### The `Book` handle

`books.open(key)` returns a `Book`. The handle is the only interface that callers need.

```python
book = books.open("fermat")
book.paths.transcripts            # $POLYTYPST_BOOKS/fermat/transcripts
book.paths.build("vol2")          # $POLYTYPST_BOOKS/fermat/build/vol2
book.paths.work("parity", "vol2") # $POLYTYPST_BOOKS/fermat/work/parity/vol2
book.transcribe(backend)
book.build("vol2", formats)
book.parity("vol2")
```

`BookPaths` derives each path from the key and `$POLYTYPST_BOOKS`. `Book.out_dir`, `Edition.rebuilt`, `OUTPUT` and the free function `book_state(out_dir)` go away. `Edition.rebuilt` becomes `book.paths.build(name) / f"{key}.pdf"`. `MonographSpec.markdown_dir` goes away because the transcript folder is always `transcripts/`.

`Book.adhoc(source)` handles a scan that has no book folder. It keeps working, with the key taken from the spec slug.

### Why TOML and not JSON

Specs hold many regexes and LaTeX or Typst preambles. TOML literal strings (`'...'` and `'''...'''`) keep backslashes as written. JSON doubles each one, so `\s*` becomes `"\\s*"`. TOML also allows comments. Python 3.11 reads TOML with the built-in `tomllib`, and the project already requires Python 3.11 or later.

### `book.toml` schema

The top-level keys are the fields of `MonographSpec`, with the same names and meanings. The loader adds these keys:

| Key | Meaning |
| --- | --- |
| `aliases` | Other keys that `book_by_key` accepts. This replaces the hard-coded `sga4_5` aliases. |
| `running_headers` | Not built yet. A list of titles. The loader joins them with `\|`, passes them to `running_header_regexes()`, and appends the result to `running_header_regexes`. |
| `editions` | A table of editions. See Editions. |
| `hooks` | A table that binds a callable field, or `figures`, to a `hooks.py` function with another name. See `hooks.py`. |
| `legacy_state` | During migration only: the old output folder name of this book or of one edition. Until Phase 2, it also sets the output folder (`output/<legacy_state>/`). Phase 3 removes it. |

Type rules:

- A TOML array becomes a `tuple` or a `frozenset`, as the field's annotation says.
- A TOML table becomes a `ChapterSpec`, a `FigureLayout` or a `dict`, as the annotation says.
- Keys of a `dict[int, ...]` field are strings in TOML. The loader parses them as integers.
- The token `@REPO@` in a string becomes the absolute path of the repository root. For example, `"@REPO@/fonts"` is the repo's `fonts/` folder. Other strings stay as written, because many path fields, such as `source_pdf`, are scan file names and not paths.
- In a `Path` field, such as a facsimile's `diagram_dir`, the token `@BOOK@` becomes the book folder.
- In `typst_front_matter`, the token `@ENGINE_TITLE_PAGE@` becomes the compiler's own title page for that spec. In `typst_preamble`, `@ENGINE_PREAMBLE@` becomes the compiler's own preamble. A book that extends the engine's Typst thus keeps up with the engine.
- TOML has no null. A field whose `None` means the same as its default, such as `header_zone_lines`, is left out.
- A callable field must not appear in TOML. It comes only from `hooks.py`.
- The loader rejects unknown keys, wrong types and bad `Literal` values. The error names the file and the key.

Example, from `src/hecke/spec.py` and `src/hecke/book.py`:

```toml
slug = "hecke"
title = "Lectures on the Theory of Algebraic Numbers"
author = "Erich Hecke"
translator = "George U. Brauer and Jay R. Goldman"
publisher = "Springer-Verlag"
series = "Graduate Texts in Mathematics"
year = 1981
domain = "math"
footnote_style = "superscript"
footnote_reset = "chapter"
preface_page = 5
references_page = 249
pdf_page_count = 249
source_pdf = "Lectures on the theory of algebraic numbers (Hecke, Erich).pdf"
pdf_name_markers = ["hecke", "algebraic numbers"]

running_headers = [
  "Lectures on the Theory of Algebraic Numbers", "Erich Hecke",
  "Translators' Preface", "Author's Preface", "Contents",
  # ... the remaining chapter titles
]

latex_preamble = '''
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
'''

chapters = [
  { number = 1, title = "Elements of Rational Number Theory", start_page = 11, end_page = 25 },
  { number = 2, title = "Abelian Groups", start_page = 26, end_page = 49 },
]

[editions.monograph]
summary = "monograph"
```

### Editions

Each `[editions.<name>]` table has these keys:

- `kind`: `"monograph"` (the default) or `"facsimile"`.
- `summary`: a short description of the edition.
- `spec`: an optional table of `MonographSpec` overrides. The loader applies it with `dataclasses.replace`.
- `facsimile`: for `kind = "facsimile"`, a table of `FacsimileStyle` fields. Its callable fields come from `hooks.py`. `install_diagrams` defaults to `no_diagrams`.
- `visual`: for `kind = "facsimile"`, an optional table of `VisualLimits`.
- `hooks`: an optional table that binds callable fields of this edition to `hooks.py` functions.
- `prepare`: for `kind = "monograph"`, the name of a `hooks.py` function that runs before each build.

The first edition is the default. If a book has no `editions` table, the catalog makes one `monograph` edition. An edition has no `out_dir` key, because `BookPaths` derives it.

This replaces the separate output folders. For example, fermat becomes one book with the editions `vol3`, `vol2` and `vol1`:

```toml
[editions.vol3]
summary = "volume 3"

[editions.vol2]
summary = "volume 2"
spec = { slug = "fermat2", title = "...", chapters = [ ... ] }

[editions.vol1]
summary = "volume 1"
spec = { slug = "fermat", title = "...", chapters = [ ... ] }
```

`parity` stays in `book.py` in this plan, because `Parity.page_map` is a function and only bourbaki uses it.

### `hooks.py`

`hooks.py` is a plain module that the loader imports by path. It can import from the engine (`from polytypst.compiler.monograph import ...`) and use relative imports inside the book folder. The loader binds names with these rules:

- A function with the name of a callable `MonographSpec` field fills that field at the top level. The names are `heading_hook`, `source_line_breaks` and `justify_page_end`.
- A function named `figures` fills `Book.figures`. Until Phase 2 it receives the output folder. Phase 2 passes `BookPaths`.
- In a facsimile edition, a function with the name of a callable `FacsimileStyle` field fills that field. The names are `install_diagrams`, `diagram_boxes`, `figure_boxes` and `figure_art`.
- The top-level `[hooks]` table binds a function with another name, for example `heading_hook = "macro_heading_hook"` or `figures = "draw_figures"`.
- An edition can name a different function, for example `hooks = { heading_hook = "illustrated_heading_hook" }`, or `prepare = "draw_figures"`. An edition's monograph spec inherits the top-level hooks and takes no hook by name.
- A hook that needs spec data reads it from `book.toml` with `tomllib`, or calls `book_by_key` inside the function at run time. It never copies the data.
- The loader raises an error when `book.toml` names a hook that `hooks.py` does not define. It also raises an error when `hooks.py` defines a public function that nothing binds.

### Discovery and loading

The book folders are in `books/`, relative to the repository root. The catalog finds that root from its own file location, not from the working directory.

A folder is a book if it holds `book.toml` or `book.py`. If `book.py` exists, the catalog uses its `BOOK`. Otherwise, the catalog reads `book.toml` and binds `hooks.py`.

The catalog is `src/books.py`. It keeps the module name so that existing callers and tests keep working. It imports `book.py` and its sibling modules by path with `importlib.util.spec_from_file_location`. The package name is `polytypst_books.<key>`, or `polytypst_books.b_<sha1 of key>` when the key is not a Python identifier. It sets `submodule_search_locations=[folder]`, so relative imports work and any folder name is accepted. `module(key, name)` returns one module of a Python book.

`books()` returns a mapping. Listing its keys imports nothing. A lookup loads only that book. A book that fails to load raises `BookLoadError`, which names the key, and the other books still load.

### `polytypst migrate-state`

The command moves the existing state into the new layout. It reads `legacy_state` from each `book.toml` to map old folder names to a key and an edition.

| Old path | New path |
| --- | --- |
| `$POLYTYPST_BOOKS/<old>/markdown_pages/` or `markdown/` | `$POLYTYPST_BOOKS/<key>/transcripts/` |
| `output/<old>/source_ocr/` or `$POLYTYPST_BOOKS/<old>/source_ocr/` | `$POLYTYPST_BOOKS/<key>/lines/` |
| `$POLYTYPST_BOOKS/<old>/page_fit.json`, `linebreaks.json` | `$POLYTYPST_BOOKS/<key>/` |
| `output/<old>/page_renders/` | `$POLYTYPST_BOOKS/<key>/renders/` |
| `output/<old>/<slug>.{typ,tex,pdf,epub}` and `figures/` | `$POLYTYPST_BOOKS/<key>/build/<edition>/` |

Rules:

1. Without `--apply`, the command prints every planned move and every folder that it will leave alone. It changes nothing.
2. With `--apply`, it moves files. It never overwrites a file and never deletes a transcript.
3. If two copies of the line cache differ, it keeps both and reports the conflict.
4. It leaves unknown folders, such as `output/bourbaki/test_10_diagrams/`, where they are and lists them. You decide what to keep.
5. A second run with nothing to move prints "nothing to move" and exits 0.

### API changes

- Changed: `polytypst.books` is the catalog. `books()`, `book_by_key()`, `book_for_scan()`, `book_specs()` and `find_known_book()` keep their signatures. New: `module()`, `load_toml()`, `BOOKS_DIR`, `BookFileError` and `BookLoadError`.
- New: `BookPaths` and the `Book.paths` attribute.
- New CLI commands: `polytypst migrate-state [--apply]` and `polytypst clean <key>`.
- Removed: `Book.out_dir`, `Edition.rebuilt`, `OUTPUT`, `book_state(out_dir)`, `MonographSpec.markdown_dir` and `scripts/one_book.py`.
- The wheel no longer contains books.

## Implementation Plan

There are three phases. Each phase is one PR.

### Phase 1: Book folders and `book.toml`

- [x] Turn `src/books.py` into the catalog, with discovery, lazy loading and the strict TOML loader.
- [x] Support `[editions.*]` with the `monograph` kind and `spec` overrides.
- [x] Support the `facsimile` kind in TOML, with an `[editions.<name>.facsimile]` table of `FacsimileStyle` fields.
- [x] Bind `hooks.py` functions by name. Raise an error for a missing or unbound hook.
- [x] Record snapshots of every book, edition and spec from the old code (`tests/fixtures/book_snapshots.json`).
- [x] Move all 28 books to `books/<key>/` in one change, so no dual discovery is needed.
- [x] Move the Python books to `book.toml` plus `hooks.py`. 27 of 29 books now use `book.toml`. `bourbaki` keeps `book.py` for its parity page map, and `london_treasury` keeps it for its own build pipeline.
- [x] Switch the tests and scripts to the catalog. Change `new-book` to write `book.toml`.
- [x] Delete the package entries, the `[0-9]*/*.py` glob and `tests/test_packaging.py`.
- [x] Remove book names from engine code. The website list moves to `books/<key>/site.toml`. The compiler stops looking for diagrams in other books' output folders. Generic scripts take `KEY`. Book-only scripts move to `books/<key>/tools/` or read their folder from the catalog.

### Phase 2: One key and the `Book` handle

- [ ] Add `BookPaths` and `Book.paths`, and make `books.open()` return the handle.
- [ ] Replace each `out_dir`, `OUTPUT` and `book_state(...)` use in `src/` with `book.paths`. Start with the four places that add `"markdown_pages"` by hand.
- [ ] Turn the fermat, kenji_alg and klein output-folder variants into editions under one key.
- [ ] Pass `BookPaths` to the `figures` and `prepare` hooks.
- [ ] Delete `Book.out_dir`, `Edition.rebuilt`, `OUTPUT`, `MonographSpec.markdown_dir` and `scripts/one_book.py`.

### Phase 3: State layout and migration

- [ ] Add `polytypst migrate-state` with dry run, `--apply`, the no-overwrite rule and the conflict report.
- [ ] Add `polytypst clean <key>`.
- [ ] Run the dry run on the real `$POLYTYPST_BOOKS` and `output/`, and review the plan with the user before `--apply`.
- [ ] Remove `legacy_state` from every `book.toml` after the move.
- [ ] Update `GLOSSARY.md` (book, book folder, state folder, transcript store, line cache), `docs/scanned-books.md`, `docs/reviewing-books.md` and the Books line in `AGENTS.md`.

## Testing Strategy

- **Book snapshots.** Before the move, the old code writes every book, edition and spec as JSON to `tests/fixtures/book_snapshots.json`. Hooks appear by function name, and each edition's build shows the values it closes over. After the move, the catalog must produce equal JSON. The snapshot comes from the old code, so the test fails if the TOML drifts.
- **Loader errors.** Each rejection rule has a test that fails without the rule. The rules are unknown key, wrong type, bad `Literal`, missing hook, unbound hook and duplicate key.
- **Isolation.** A broken `book.toml` beside a good one must not stop a lookup of the good one.
- **Paths.** A test checks each `BookPaths` attribute against the layout table in this spec, for a key with an underscore and for a key with Chinese characters.
- **Migration.** A test builds a temporary old-style tree with transcripts, two differing line caches, an unknown folder and a renamed output folder. The dry run must change nothing. `--apply` must move every known file, keep both line caches, leave the unknown folder, and keep every transcript byte for byte. A second run must print "nothing to move".
- **End to end.** `uv run polytypst books` lists the same keys before and after. `uv run pytest -q` passes. `polytypst build` for hecke, one economics book and fermat `vol2` gives the same `.typ` output as before.

## Rollout Plan

1. Phase 1 merges. All books move in one change, so only `books/` holds books after it.
2. Phase 2 merges. Builds now write under the state folder, but the old state stays where it is.
3. Phase 3 merges. The user reviews the `migrate-state` dry run, then runs `--apply`.
4. After the user checks the moved state, the user deletes `output/`.

## Open Questions

- Should `build/` stay inside the repository as `output/<key>/<edition>/` (gitignored), so that rebuilt PDFs are easy to open from the editor?
- Should the engine modules be renamed by stage (`scan/`, `ocr/`, `compile/`, `check/`) in a later plan?
- Should `kerodon` and `taocp` become book folders, with `web_exporter.py` loading them through the catalog? Today the engine imports kerodon (`src/web_exporter.py:10`).
- Should `parity` move to TOML with a `page_map` hook, so that bourbaki can drop its `book.py`?
- Should the project generate a JSON Schema from `MonographSpec`, so that editors can check `book.toml` while you type?

## References

- `src/books.py`, `src/book_state.py`, `src/edition.py`, `src/new_book.py`, `src/compiler/monograph.py`, `src/parity/source.py`
- `tests/test_packaging.py`, `tests/test_books.py`
- `GLOSSARY.md`, `docs/scanned-books.md`, `docs/reviewing-books.md`
