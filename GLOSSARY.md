# polytypst

polytypst re-typesets scanned mathematics books as Typst, LaTeX and EPUB. This glossary names the things that OCR makes and the things that the checks compare.

## Language

**Source scan**:
The original scan of a book: a PDF, a folder of page images, or one image. It is the ground truth for text, layout and diagrams. Scan parity needs a PDF.
_Avoid_: original, ground truth PDF, input PDF

**Rebuilt PDF**:
The PDF that polytypst typesets for one edition of a book.
_Avoid_: output, reproduction, ours

**Page map**:
The pairing of each source scan page with the rebuilt PDF page or pages that hold its text.
_Avoid_: page alignment, page mapping

**Transcript**:
The Markdown with TeX math that OCR makes from one source scan page. The compilers read it, not the scan.
_Avoid_: OCR page, markdown page, md

**Transcript store**:
The folder of a book's transcripts, one `p_NNN.md` file per page, plus `transcripts.json`. That file records which backend and prompt made each transcript. The store sends only the missing pages to a backend.
_Avoid_: markdown cache, markdown_pages, OCR cache

**Backend**:
The OCR service that makes transcripts, written as `KIND[:MODEL][?KEY=VALUE&...]`, as in `gemini` or `local:deepseek-ocr`. The kinds are gemini, openai, jina, mistral, local, colab and cached.
_Avoid_: OCR engine, mode

**Line cache**:
The folder of OCR lines with their boxes for a book, `output/<key>/source_ocr/`, one `pNNN.json` file per page, plus `lines.json`. That file records which line reader made each page. Scan parity, the facsimile and figure extraction read it. A line reader is Apple Vision on macOS and Tesseract elsewhere, in the languages that the book's `ocr_languages` names.
_Avoid_: source OCR, Vision cache, OCR pages

**Scan parity**:
How far each word, line and diagram of a rebuilt PDF page sits from the same ink on its source scan page, in points.
_Avoid_: redshift, overlay score, pixel parity
