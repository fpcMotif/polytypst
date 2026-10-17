# EPUB and HTML ingestion

Ticket: devv-m9fh. Date: 2026-10-17. Tools tested: pandoc 3.7.0.2, typst 0.15.1.

## At a glance

polytypst has no EPUB or HTML input path today. Every compiler starts from page-level Markdown with TeX math (`$…$`, `$$…$$`). Pandoc can produce that Markdown from EPUB and HTML. It fails in five specific places: cross-file endnotes, figure cross-references, `\tag` and MathML equation labels, MathJax delimiters, and page chrome.

The change: add one ingestion stage that runs `pandoc -f epub` or `pandoc -f html+tex_math_single_backslash+tex_math_dollars` to `markdown+tex_math_dollars`. A Lua filter repairs the five losses before the result enters the existing pipeline. The EPUB side of the Edition keeps the current route, which is pandoc `-t epub3 --mathml` from the same Markdown.

What stays unchanged: the Markdown with TeX math stays the intermediate form. The Typst back end (`monograph.py` `format_typst`, `typst_math.py`, pandoc `-t typst` with `equation_tags.lua`) does not change. Typst's own HTML export is not yet ready to produce the EPUB.

## 1. The intermediate form today

All current compilers consume Markdown with TeX math and produce Typst in one of two ways:

- `polytypst/compiler/monograph.py` (`MonographCompiler.format_typst`, about line 1475) converts Markdown to Typst with regular expressions. It sends each `$…$` and `$$…$$` body through `sanitize_math_code`, and `polytypst/compiler/typst_math.py` holds the shared converter. That file exists only in the main checkout and is not on `origin/main` yet. It runs pandoc only for the LaTeX copy (`-f markdown+tex_math_dollars+raw_tex -t latex`, about line 1769).
- `polytypst/compiler/french_math_typst.py` (about line 871), `polytypst/compiler/roberts_jina_typst.py` (about line 463) and `polytypst/kerodon/compiler.py` (about line 181) run `pandoc -f markdown -t typst`. The French compiler adds `polytypst/compiler/equation_tags.lua`, which keeps `\tag{…}` as Typst equation numbers.
- `polytypst/core/pipeline.py` (`UniversalPDFPipeline.process`) has only a PDF entry point. It renders pages, runs OCR into `markdown_pages/p_NNN.md`, and stitches or calls `MonographCompiler`.

The contract for ingestion is therefore **one Markdown file with `$`-delimited TeX math, `![caption](path){#id}` figures, `[^n]` footnotes and ATX headings, with images in a figures directory**. An EPUB or HTML document that reaches this form can use every existing back end without change.

## 2. Measured pandoc behaviour

I built three test inputs:

1. A pandoc-made EPUB 3 with `--mathml`.
2. A hand-made EPUB 3 in the style of third-party publishers. It has a separate endnotes file, MathML without a TeX annotation, `<mlabeledtr>`, `<mmultiscripts>` and `<figure>`.
3. A web page with MathJax `\( \)` delimiters, KaTeX output, a Wikipedia math image and a plain list of footnotes.

| Feature | Result | Evidence |
|---|---|---|
| Headings and sections | Kept. Spine files are joined in order, and each file adds an empty `[]{#ch1.xhtml}` anchor. | EPUB → Markdown output |
| MathML with an `application/x-tex` annotation (pandoc, KaTeX, many LaTeX-to-EPUB tools) | **Exact TeX survives.** The reader takes the annotation verbatim and skips MathML parsing. | `\tag{1.1}` and `aligned` came back byte for byte |
| MathML without an annotation | Converted by texmath. The result is valid but noisy. `f:Ω→ℂ` became `\left. f:\Omega\rightarrow\mathbb{C} \right.`, and `mmultiscripts` became `{}_{i}^{}R_{j}^{}`. | hand-made EPUB |
| `<mlabeledtr>` equation label "(1.1)" | **Lost.** The label cell is dropped, and the row becomes `\begin{matrix}…\end{matrix}`. | hand-made EPUB |
| `\tag{1.1}` through plain `-t typst` | **Lost.** The Typst writer emits the equation without the number. `equation_tags.lua` repairs this and produces `#[#set math.equation(numbering: _ => [(1.1)]); $ … $]`. | `pandoc src.md -t typst` with and without the filter |
| Images | Kept. `--extract-media=DIR` writes them out. The paths are relative to the working directory, not to `-o`, so running in a subdirectory produced a doubled `tt/tt/media` path. | Typst compile error "file not found" |
| `<figure>` with `<figcaption>` | Becomes a Typst `#figure(image(...), caption: [...]) <fig-1-1>`. The caption text keeps "Figure 1.1." as literal text. | hand-made EPUB |
| Same-file `epub:type="footnote"` | Becomes a real footnote. The backlink leaves a stray `. ` at the start of the note text. | pandoc-made EPUB: `[^1]: . Footnote…` |
| Endnotes in a separate file with `epub:type="endnotes"` / `endnote` | **Not recognised.** They stay as an ordered list, and the noteref stays a link. | hand-made EPUB, first variant |
| Endnotes in a separate file with `epub:type="rearnotes"` / `role="doc-endnotes"` | **Note text is deleted.** The reader stores the notes, but the noteref `notes.xhtml#note-1` is not a `#` link, so nothing replaces it. | hand-made EPUB, second variant: the endnote body is gone from the output |
| Internal links to figures | **Broken.** Links are rewritten to `#ch1.xhtml_fig-1-1`, but the figure keeps the id `fig-1-1`. `typst compile` fails with ``label `<ch1.xhtml_fig-1-1>` does not exist``. | Typst compile |
| MathJax `\(…\)` and `\[…\]` in HTML | Kept as literal text by default. They become math with `-f html+tex_math_single_backslash`. | web page |
| KaTeX HTML | Clean. Pandoc takes the MathML annotation, and the `katex-html` copy did not appear in the output. | web page |
| Wikipedia math image (`alt="{\displaystyle …}"`) | Becomes an image of the formula. The TeX in `alt` is not used. | web page |
| Plain HTML footnotes (`<sup><a href="#fn1">`) | Stay as a superscript link and an ordered list. | web page |
| Page chrome (`<nav>`) | Kept as body text. | web page |
| pandoc's standalone Typst template | Fails on Typst 0.15 with "font fallback list must not be empty". polytypst uses body output and its own preamble, so this does not affect it. | `pandoc -s -t typst` then `typst compile` |

### Why these losses happen

- **Per-file parsing.** The EPUB reader parses each spine document separately with `readHtml`, then `fixInternalReferences` prefixes ids as `file_ident`. It rewrites `Span`, `Code`, `Div`, `Header` and `CodeBlock` ids, but not `Figure` ids, so links to figures break. Notes are resolved inside a single `readHtml` call, so a noteref cannot reach a note in another file. Source: `archiveToEPUB`, `parseSpineElem` and `fixInternalReferences` in [Readers/EPUB.hs](https://github.com/jgm/pandoc/blob/main/src/Text/Pandoc/Readers/EPUB.hs).
- **Note vocabulary.** `eNoteref` accepts `epub:type="noteref"` or `role="doc-noteref"` only when `href` starts with `#`. `eFootnote` accepts `footnote` and `rearnote`. `eFootnotes` accepts `footnotes`, `rearnotes` or `role="doc-endnotes"`. Source: [Readers/HTML.hs](https://github.com/jgm/pandoc/blob/main/src/Text/Pandoc/Readers/HTML.hs). The current vocabulary is EPUB SSV 1.1. It marks `rearnote` and `rearnotes` as deprecated ("replaced by endnotes") and also deprecates `endnote` to match DPUB-ARIA 1.1 ([EPUB SSV 1.1, Notes](https://www.w3.org/TR/epub-ssv-11/)). Current EPUBs therefore use `endnotes` with plain `<li id>` items, which is the case pandoc does not recognise.
- **Math.** `pMath` uses an `annotation encoding="application/x-tex"` when present. Otherwise it converts the MathML with texmath (`readMathML` then `writeTeX`). On failure it emits a span with the class `math` ([Readers/HTML.hs](https://github.com/jgm/pandoc/blob/main/src/Text/Pandoc/Readers/HTML.hs), [texmath](https://github.com/jgm/texmath)). EPUB 3 permits only Presentation MathML in content ([EPUB 3.3 §1.3.4](https://www.w3.org/TR/epub-33/#sec-overview-relations-mathml)), so texmath's MathML reader covers the input domain. It does not cover labels.
- **HTML math delimiters.** The HTML reader enables only `auto_identifiers`, `line_blocks`, `native_divs` and `native_spans` by default (`pandoc --list-extensions=html`). `tex_math_single_backslash` "causes anything between `\(` and `\)` to be interpreted as inline TeX math" ([manual](https://pandoc.org/MANUAL.html#extension-tex_math_single_backslash)).

## 3. Alternatives compared

| Option | Structure | Images | Footnotes | Math into Typst | Verdict |
|---|---|---|---|---|---|
| **pandoc** `-f epub` / `-f html` ([manual](https://pandoc.org/MANUAL.html)) | Good. It builds a typed AST with headings, divs, figures and tables, and a Lua filter can repair it. | Good with `--extract-media` | Same-file notes work. Cross-file notes are lost (see above). | Best available. It keeps exact TeX from annotations and uses texmath for bare MathML. The output feeds the existing Typst paths. | **Use it.** It is already a dependency, and the gaps can be fixed with a filter. |
| calibre `ebook-convert` to TXT with `--txt-output-formatting=markdown` ([docs](https://manual.calibre-ebook.com/generated/en/ebook-convert.html)) | Fair | Only with `--keep-image-references` | Flattened | The docs do not mention MathML. | Reject. Useful only for DRM-free format conversion (MOBI/AZW3 → EPUB) before pandoc. |
| Microsoft MarkItDown EPUB converter ([source](https://github.com/microsoft/markitdown/blob/main/packages/markitdown/src/markitdown/converters/_epub_converter.py)) | Fair. It sends each spine file to its HTML converter (BeautifulSoup and a markdownify subclass). | Images are not extracted. | Not handled | No math handling in either converter | Reject. It is built for LLM text, not typesetting. |
| Custom ebooklib + BeautifulSoup walker | As good as written | Manual | Manual | Must call texmath, pandoc or a MathML-to-TeX library anyway | Reject as the main path. Keep it as the place for pre-pass fixes if a Lua filter is not enough. |
| Typst-side math conversion: [MiTeX](https://github.com/mitex-rs/mitex) (`@preview/mitex:0.2.7`, LaTeX to Typst in Rust/WASM) or [tex2typst](https://github.com/qwinsi/tex2typst) (JavaScript, both directions) | n/a | n/a | n/a | TeX to Typst only. Neither reads MathML. | Keep as a fallback for formulas that `sanitize_math_code` or pandoc's Typst writer cannot convert. MiTeX can render raw TeX inside the Typst file. |

For web pages, the boilerplate (nav, sidebars, comments) must be removed before pandoc. A readability-style extractor or a site-specific CSS selector does this. pandoc has no such step. This research did not evaluate a specific extractor.

## 4. Recommended ingestion design

1. **Normalise the source.**
   - For EPUB, run the input as is.
   - For HTML, select the main content element first, such as `article` or `main`.
2. **Convert with pandoc.**
   - For EPUB: `pandoc in.epub -f epub -t markdown+tex_math_dollars --extract-media=figures --lua-filter=ingest_fixups.lua -o book.md`, with the working directory set to the output directory.
   - For HTML: `-f html+tex_math_single_backslash+tex_math_dollars`.
3. **`ingest_fixups.lua` repairs the five losses.**
   - **Notes.** Before pandoc, or in a pre-pass over the EPUB, collect every element with `epub:type` `footnote`, `endnote` or `rearnote`, or role `doc-footnote` or `doc-endnote`, plus `<li id>` elements inside `endnotes` or `footnotes` containers in any spine file. Rewrite each cross-file noteref href to `#id`. A Lua filter cannot do this alone, because the note text is already gone before filters run. This step is a short Python pass with zipfile and lxml over the XHTML. In the filter, replace remaining `.noteref` links with `pandoc.Note`, and remove the leading backlink and `. ` from note bodies.
   - **Figure ids.** Prefix `Figure` ids the way `fixInternalReferences` prefixes other ids, or strip the `file.xhtml_` prefix from links. Then rename `fig-…` and `eq-…` ids to the `<fig-N>` and `<eq-N>` forms that `format_typst` keeps (it does not escape `<eq-`, `<fig-` or `<sec-`).
   - **Equation labels.** Before pandoc, turn `<mlabeledtr>` labels into `\tag{…}` inside the TeX annotation, or keep them as an attribute. The existing `equation_tags.lua` then numbers them in Typst.
   - **Math images.** When an `<img>` has `alt` text in the form `{\displaystyle …}` (MediaWiki), replace it with `Math` from the alt text.
   - **File anchors.** Drop the empty `[]{#chNNN.xhtml}` spans, which become Typst labels that are attached to nothing.
4. **Join the pipeline.** Write `book.md` and `figures/` where `pipeline.py` writes them today, and hand them to the existing back ends. The entry point is a new `UniversalPDFPipeline` sibling. It skips rendering, OCR and verification. These steps exist only because PDF has no text layer that can be trusted.
5. **Test with fixtures.** Keep a small EPUB and HTML fixture set (the three inputs above) in tests. Assert that the note text survives, that `typst compile` succeeds, and that `(1.1)` appears in the PDF text.

## 5. Producing the EPUB side of the Edition

The EPUB must be built **from the same Markdown, with pandoc `-t epub3 --mathml`**. `french_math_typst.py` and `roberts_jina_typst.py` already do this. `polytypst/compiler/epub.py` (`PandocCompilers.compile_epub`) does it without `--mathml`, so its math is raw TeX that EPUB readers cannot render.

- **Math.** `--mathml` writes Presentation MathML with an `annotation encoding="application/x-tex"` copy. A later re-ingest of the Edition is therefore lossless (measured above). The manual says MathML "is supported natively by the main web browsers and most e-book readers" ([manual, Math rendering](https://pandoc.org/MANUAL.html#math-rendering-in-html)). In pandoc newer than 3.7, `--mathml` is deprecated in favour of `--math-method=mathml`.
- **Equation numbers.** `equation_tags.lua` already runs on the EPUB path in `french_math_typst.py`. Every EPUB build needs it so that numbers match the PDF.
- **Notes.** pandoc writes `<aside epub:type="footnote" role="doc-footnote">`, which pandoc reads back and current reading systems recognise.
- **Packaging.** Use `--split-level` to split chapters, `--epub-cover-image`, `--epub-embed-font` and `--css` ([manual](https://pandoc.org/MANUAL.html#epubs)). Validate with [EPUBCheck](https://github.com/w3c/epubcheck) in CI.
- **Typst HTML export is not the EPUB route yet.** Typst 0.15 `--features html` emits native MathML and DPUB-ARIA footnotes (`role="doc-noteref"`, `role="doc-endnotes"`), which was measured with a test file. However:
  - The docs say "Do not use this feature for production use cases" ([Typst HTML](https://typst.app/docs/reference/html/)).
  - The output is HTML syntax with an unclosed `<meta charset="utf-8">`. EPUB XHTML must be well-formed XML ([EPUB 3.3 §3.9](https://www.w3.org/TR/epub-33/#sec-xml-constraints)).
  - It drops the visible "(1)" equation number.
  - Its MathML has no TeX annotation.
  - The multi-file `bundle` target is also experimental ([Typst bundle](https://typst.app/docs/reference/bundle/)).
- **Rejected: Typst → pandoc → EPUB.** `pandoc -f typst` ignores `math.equation(numbering:)`, so equations lose their numbers and `@eq1` becomes the text `[eq1]`. Typst is a worse EPUB source than the Markdown.

## Open questions

1. Which EPUB sources matter first: publisher EPUBs (bare MathML, `endnotes`) or LaTeX-generated EPUBs (TeX annotations)? The note pre-pass and `mlabeledtr` handling matter only for the first group.
2. Should ingested EPUBs bypass `MonographCompiler.format_typst` and use pandoc `-t typst` with `equation_tags.lua`? Pandoc's Typst writer is AST-based and safer for clean input. `format_typst` is tuned for OCR noise.
3. What is the target for reading systems without MathML support, such as some Kindle paths? The choice is between SVG fallbacks (`--webtex` needs network access, and Typst `html.frame` is experimental) and MathML only.
4. DRM: do we accept only DRM-free EPUBs, and do we state this in the CLI?
5. Should ingestion live in `pipeline.py` as a new class, or behind a common `Source` interface shared with the PDF path?
