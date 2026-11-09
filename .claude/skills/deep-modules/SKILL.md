---
name: deep-modules
description: polytypst's layer on codebase-design, mapping deep modules onto the Python pipeline and the Typst and LaTeX source it writes. Use when you design or split a module in src/ or books/, add a compiler pass, OCR backend or per-book hook, place a seam between Python and Typst or LaTeX, or run an architecture review here.
---

# Deep modules in polytypst

This skill is a **layer**. The vocabulary, the principles and the general processes live in `codebase-design`. This skill adds only what is specific to polytypst: where each term lands in this repo, what an interface means in a text pipeline, and how to test it.

## Step 1: load the shared vocabulary

Call the Skill tool with `mattpocock-skills:codebase-design` before anything else. Use its terms exactly: **module**, **interface**, **implementation**, **depth**, **seam**, **adapter**, **leverage**, **locality**. Apply its principles as written: the deletion test, "the interface is the test surface", and "one adapter is a hypothetical seam, two make a real one".

**Done when:** codebase-design is loaded in this turn. Then use the sections below as the polytypst reading of each term.

## Where the terms land

| Term | In polytypst |
|---|---|
| Module | A function, a `.py` file, a package such as `src/ocr/`, a book folder `books/<key>/`, or a Typst `#let` function in a preamble |
| Seam with real adapters | `Transcriber` in `src/ocr/pages.py`, with live, worker and cached transcribers in `src/ocr/` |
| Seam with real adapters | The output formats that `run_formats` in `src/compiler/monograph.py` runs: a Typst writer and a LaTeX writer |
| Seam between languages | The preamble functions that the written source calls, such as `chapter-subtitle` and `fig-note` in `books/styles/japan_economy.typ` |
| Per-book adapter | A book folder's hooks and spec, filled only where books truly differ |
| Test stand-in | `CachedTranscriber` in `src/ocr/cached.py`, which replays the transcript store through the `Transcriber` seam |

Domain names come from `GLOSSARY.md` (source scan, transcript, transcript store, backend, page map). Name a module after the domain concept it owns.

## Interface in a text pipeline

A polytypst module reads text and writes text, so its interface covers:

- the **input dialect**: which Markdown, LaTeX math and HTML tables it accepts,
- the **output dialect**: the Typst or LaTeX it writes, the labels such as `<eq:3.2>` it emits, and the preamble functions that the text calls,
- **idempotence**: a text pass run twice gives the same text as one run,
- **pass order**: which passes must run before it,
- **error modes**: `OCRBackendError`, a Typst or tectonic compile error,
- **configuration**: `book.toml` keys, `sys.inputs` tune keys, environment variables.

A run of exported passes that every caller must call in the right order is **shallow**. The deep form is one entry point that owns the order and keeps the passes private (a leading `_`).

## Two layers, one design

Python decides content and structure. The preamble decides layout.

- **Write calls into the preamble.** Python writes `#fig-note[...]`, and the `#let` function owns fonts, spacing and page rules. Layout knobs that vary by book come in through `sys.inputs` (see `tune` in `books/bourbaki/vintage_preamble.typ`), so Python passes values, not code.
- **Compute once, write twice.** A chapter number or equation label is computed once in Python, then written by both the Typst and the LaTeX writer.
- **Escape at one seam.** Each output dialect has one escape function, such as `escape_typst_text`.
- **Fix shared defects in `src/`.** A fix that two book folders copy belongs behind one interface in `src/`. A hook that one book uses stays a value in its `book.toml`.

## Dependency categories here

codebase-design's DEEPENING.md defines four categories. In polytypst they are:

1. **In-process**: `str -> str` passes in `src/compiler/` and `src/tex_markdown.py`. Merge them and test the merged entry point with example text.
2. **Local-substitutable**: the `typst` and `tectonic` binaries, pymupdf on a scan, the transcript store, the line cache, diagram caches. Take a path or a value at the interface. Tests read `tests/fixtures/`.
3. **Remote but owned**: the Colab and local GPU workers in `src/ocr/`. A `Protocol` port, with `CachedTranscriber` as the test adapter.
4. **True external**: Gemini, Mistral and OpenAI-compatible APIs. Inject the client. Keys come from the environment through `api_key` in `src/ocr/backend.py`.

## Testing at a text interface

Test through the interface at three levels, from cheapest to widest:

1. **Examples**: input text in, expected text out. Take the expected text from the scan or from the Typst or LaTeX documentation.
2. **Properties** with `hypothesis`: idempotence, no lost characters, balanced delimiters.
3. **Compile**: the written source compiles with `typst` or `tectonic -X compile`. Only a compile proves the output dialect.

Assert on the written text, its labels and the compile result. Intermediate strings between private passes are implementation.

## Additions to the shared processes

- **Design it twice** (codebase-design's DESIGN-IT-TWICE.md): add the input dialect, output dialect and pass order to each brief's constraints. Add a fourth design constraint when the candidate writes Typst or LaTeX: "Move as much as possible into preamble functions, and keep the Python side to content and structure."
- **Architecture review** (`improve-codebase-architecture`): load this skill after codebase-design. Read the matching pointer in `AGENTS.md` and its doc before you judge an area, because those docs record why a seam sits where it does.
