# Feature: Book catalog in `books/<key>/book.toml`

**Date:** 2026-10-27 (last updated 2026-10-27)

**Author:** fpcmotif, with Claude

**Status:** Draft

## At a glance

Today every book is a Python package (`polytypst.<key>`) inside the engine's `src/`. A new book therefore needs a hand-kept entry in `pyproject.toml`, an `__init__.py`, a boilerplate `book.py`, and Python code for data that is mostly titles, page numbers and regexes.
This plan moves each book to a folder `books/<key>/` that holds a `book.toml` with the spec and editions. An optional `hooks.py` holds the few functions that a spec needs, and a `book.py` remains only for books with a custom pipeline. A new module, `src/catalog.py`, loads these folders by path.
The engine and the CLI stay the same. They still receive the same `Book`, `Edition` and `MonographSpec` objects, and `books()`, `book_by_key()`, `book_for_scan()` and `book_specs()` keep their signatures.

## Overview

A book is content that the engine reads. It is not a library. This plan makes the code match that. A book becomes a data file that the catalog loads. It is no longer a package that setuptools ships.

## Goals

- A data-only book is one file: `books/<key>/book.toml`. It has no Python, no `__init__.py` and no `pyproject.toml` entry.
- A book that needs code adds `books/<key>/hooks.py`. The catalog binds each function to the spec field of the same name.
- A book with a custom pipeline keeps `books/<key>/book.py` that defines `BOOK`. This is the escape hatch.
- The folder is the registry. A folder with `book.toml` or `book.py` is a book, and its key is the folder name. Any folder name works, including `1_宏观经济与产业结构` and `複素多様体論`.
- The loader rejects unknown keys, wrong types and bad `Literal` values. The error names the file and the key.
- The catalog loads one book at a time. A broken book stops only the commands that use that book.
- `polytypst new-book` writes `books/<key>/book.toml` and does not change `pyproject.toml`.

## Non-Goals

- No change to `MonographSpec`, `Edition`, `Book`, the compiler, OCR, parity or vision.
- No change to the output layout under `output/<key>/`.
- No move of the engine from `src/` to `src/polytypst/`. `package-dir = { "polytypst" = "src" }` already gives the right import name.
- No move of `kerodon`, `goursat` and `taocp` in this plan. They have no `book.py`, and only `src/web_exporter.py` reaches them. See Open Questions.
- No JSON. See Design.

## Background

These facts come from the repository at commit `eabaa6b`.

- `src/books.py:13` already finds books at runtime with `PACKAGE.glob("*/book.py")`. The 26 `polytypst.<key>` entries in `pyproject.toml` exist only for setuptools.
- `src/new_book.py` rewrites `pyproject.toml` with the regex `PACKAGES_RE` to add each new book.
- `tests/test_packaging.py` exists only to keep the package list in step with the folders.
- The five folders with a numeric prefix are not valid package names. They ship through the `"polytypst" = ["[0-9]*/*.py"]` package-data glob.
- 28 folders have a `book.py`. Six of these files have the same short shape: bourbaki_lie, functional_analysis, hecke, kashiwara and ode_arnold, plus kodaira with a figures hook.
- `docs/scanned-books.md:19` says: "`polytypst build` and `polytypst audit` import every book, so a broken spec in one book stops them for all." `scripts/one_book.py` exists to work around this.
- 14 test files import book modules directly, for example `polytypst.hecke.spec`.

### Which spec fields need code

`Rewrite` is `tuple[str, str]` (`src/compiler/monograph.py:49`), so rewrites and page fixups are data. These `MonographSpec` fields are the only ones that take functions:

| Field | Books that set it |
| --- | --- |
| `heading_hook` | 1_, 3_, 4_, 6_ (economics), bourbaki, fichtenholz_vol1 |
| `source_line_breaks` | bourbaki |
| `justify_page_end` | bourbaki |

Code also appears at the edition level:

- `Book.figures`, for example kodaira's `generate_all_kodaira_figures`.
- `monograph_edition(prepare=...)`.
- `Parity.page_map`.
- `FacsimileStyle.install_diagrams`, for example `lambda out: []` in `src/algebra3/book.py`.

Every other field is a string, number, boolean, list, table or path.

## Design

### Approach

```text
┌──────────────────────┐   path import   ┌──────────────────┐   ┌──────────────────┐
│ books/<key>/         │────────────────▶│ src/catalog.py   │──▶│ cli, build,      │
│   book.toml          │                 │ books()          │   │ parity, review   │
│   hooks.py   (opt.)  │                 │ book_by_key()    │   │ (unchanged)      │
│   book.py    (opt.)  │                 │ book_for_scan()  │   └──────────────────┘
│   diagrams/ figures/ │                 └──────────────────┘
└──────────────────────┘
```

The catalog resolves a folder in this order:

1. If `book.py` exists, the catalog imports it and uses its `BOOK`. A `book.toml` can exist beside it, and `book.py` can read it with `catalog.load_spec(folder)`.
2. If there is no `book.py`, the catalog reads `book.toml`, binds `hooks.py` if it exists, and builds the `Book`.
3. If neither file exists, the folder is not a book.

### Why TOML and not JSON

Specs hold many regexes and LaTeX or Typst preambles. TOML literal strings (`'...'` and `'''...'''`) keep backslashes as written. JSON doubles each one, so `\s*` becomes `"\\s*"`. TOML also allows comments. Python 3.11 reads TOML with the built-in `tomllib`, and the project already requires Python 3.11 or later.

### `book.toml` schema

The top-level keys are the fields of `MonographSpec`, with the same names and meanings. The loader adds four keys:

| Key | Meaning |
| --- | --- |
| `aliases` | Other keys that `book_by_key` accepts. This replaces the hard-coded `sga4_5` aliases in `src/books.py`. |
| `out_dir` | The output folder. The default is `output/<key>`. |
| `running_headers` | A list of titles. The loader joins them with `\|`, passes them to `running_header_regexes()`, and appends the result to `running_header_regexes`. |
| `editions` | A table of editions. See Editions. |

Type rules:

- A TOML array becomes a `tuple` or a `frozenset`, as the field's annotation says.
- A TOML table becomes a `ChapterSpec`, a `FigureLayout` or a `dict`, as the annotation says.
- Keys of a `dict[int, ...]` field are strings in TOML. The loader parses them as integers.
- A relative path resolves against the book folder. For example, `"../../fonts"` is the repo's `fonts/` folder. This replaces `Path(__file__).resolve().parents[2] / "fonts"`.
- A callable field must not appear in TOML. It comes only from `hooks.py`.

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
- `out_dir`: an optional output folder.
- `spec`: an optional table of `MonographSpec` overrides. The loader applies it with `dataclasses.replace`. This covers fermat's vol1, vol2 and vol3, and the `*_ILLUSTRATED_SPEC` variants.
- `facsimile`: for `kind = "facsimile"`, a table of `FacsimileStyle` fields.

The first edition is the default, as it is today. If a book has no `editions` table, the catalog makes one `monograph` edition.

`parity` stays in `book.py` in this plan. It needs `Parity.page_map`, which is a function, and only bourbaki uses it.

### `hooks.py`

`hooks.py` is a plain module that the loader imports by path. It can import from the engine (`from polytypst.compiler.monograph import ...`) and use relative imports inside the book folder. The loader binds names with these rules:

- A function with the name of a callable `MonographSpec` field fills that field. The names are `heading_hook`, `source_line_breaks` and `justify_page_end`.
- A function named `figures` fills `Book.figures`.
- An edition can name a different function. For example, `hooks = { heading_hook = "illustrated_heading_hook" }`, or `prepare = "draw_figures"` for `monograph_edition(prepare=...)`.
- The loader raises an error when `book.toml` names a hook that `hooks.py` does not define. It also raises an error when `hooks.py` defines a public function that nothing binds.

### Module loading

`catalog.py` imports `hooks.py` and `book.py` with `importlib.util.spec_from_file_location`. It uses the synthetic package name `polytypst_books.b_<hash of key>` and sets `submodule_search_locations=[folder]`. This keeps relative imports such as `from .figures import ...` working, and it accepts any folder name.

`books()` lists the folders without importing them. `book_by_key()` loads only the book that it returns. `books(load=True)` loads every book and reports each failure with its key. Thus one broken book does not hide the others.

### Components

- New: `src/catalog.py`. It holds discovery, the TOML loader, hook binding and lazy loading.
- New: `books/<key>/` for each book in `src/` that has a `book.py`.
- Changed: `src/books.py` re-exports `catalog` during migration, and then goes away.
- Changed: `src/new_book.py` writes `book.toml`. It loses `PACKAGES_RE` and `_list_package`.
- Changed: the 14 test files that import book modules use `catalog.book_by_key("<key>").spec` instead.
- Removed at the end: the 26 book entries and the `[0-9]*/*.py` glob in `pyproject.toml`, `tests/test_packaging.py`, and `scripts/one_book.py`, which lazy loading makes unnecessary.

### API Changes

- `books()`, `book_by_key()`, `book_for_scan()`, `book_specs()` and `find_known_book()` keep their signatures. They move to `polytypst.catalog`.
- New: `catalog.load_spec(folder) -> MonographSpec`, for a `book.py` that wants its data from TOML.
- The books folder is `Path("books")`, relative to the working directory. This matches `OUTPUT = Path("output")`. The wheel no longer contains books.

## Implementation Plan

The plan has two phases. Each phase is one PR.

### Phase 1: Catalog and loader beside the old discovery

- [ ] Add `src/catalog.py` with folder discovery, lazy loading and the strict TOML loader for `MonographSpec`, `ChapterSpec` and `FigureLayout`.
- [ ] Support `[editions.*]` with the `monograph` and `facsimile` kinds and `spec` overrides.
- [ ] Bind `hooks.py` functions by field name. Raise an error for a missing or unbound hook.
- [ ] Make `src/books.py` return books from both `src/*/book.py` and `books/*/`. Reject a key that both locations define.
- [ ] Add loader tests. Each test writes a sample `book.toml` and compares the result with a hand-built `MonographSpec`.

### Phase 2: Migrate every book and remove the package machinery

- [ ] Move the single-edition, data-only books: hecke, kashiwara, ode_arnold, bourbaki_lie, functional_analysis, modern_geometry_vol3 and 複素多様体論.
- [ ] Move the multi-edition and facsimile books: fermat, kenji_alg, algebra2, algebra3, klein, siegel_symplectic, grothendieck, fga, sga4_5, modern_geometry, modern_geometry_vol2 and ahlfors.
- [ ] Move the books with hooks: the five economics books, bourbaki (which keeps `book.py` for `Parity`), fichtenholz_vol1 and kodaira.
- [ ] Move london_treasury with its `book.py` unchanged.
- [ ] Switch the 14 test files to `catalog`.
- [ ] Change `new-book` to write `book.toml`.
- [ ] Delete `src/books.py`, the book entries and the glob in `pyproject.toml`, `tests/test_packaging.py` and `scripts/one_book.py`.
- [ ] Update `docs/scanned-books.md` (lines 19, 91 and 138 to 144), `docs/reviewing-books.md` (lines 4 and 250) and the Books line in `AGENTS.md`.

## Testing Strategy

- **Spec snapshots.** Before a book moves, the old code writes `repr(spec)` for each edition of that book to a snapshot. After the move, the catalog must produce an equal spec. Tests compare hooks by function name. The snapshot comes from the old code, so the test fails if the TOML drifts from it.
- **Loader errors.** Each rejection rule has a test that fails without the rule. The rules are unknown key, wrong type, bad `Literal`, missing hook, unbound hook and duplicate key.
- **Isolation.** A test puts a broken `book.toml` beside a good one. `book_by_key` on the good book must succeed.
- **End to end.** `uv run polytypst books` lists the same keys before and after the move. `uv run pytest -q` passes. `polytypst build` for hecke and for one economics book gives the same `.typ` output as before.

## Rollout Plan

Phase 1 merges first. During the migration, both locations work. Phase 2 moves the books in the batches above, and the last batch removes the old discovery. No user command changes.

## Open Questions

- Should `kerodon`, `goursat` and `taocp` move to `books/` as code-only folders, with `web_exporter.py` loading them through the catalog? Today the engine imports kerodon (`src/web_exporter.py:10`), which reverses the direction of the dependency.
- Does anyone run polytypst from an installed wheel outside the repo? If so, add a `POLYTYPST_BOOKS` environment variable or a `--books` option.
- Should the project generate a JSON Schema from `MonographSpec`, so that editors such as Taplo can check `book.toml` while you type?
- Should `parity` move to TOML with a `page_map` hook, so that bourbaki can drop its `book.py`?

## References

- `src/books.py`, `src/edition.py`, `src/new_book.py`, `src/compiler/monograph.py`
- `tests/test_packaging.py`, `tests/test_books.py`
- `docs/scanned-books.md`
