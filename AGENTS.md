# polytypst

- **Books**: before you build a book edition (`polytypst build`), check one against its scan (`polytypst parity`), audit quality and native numbering (`polytypst audit`), fix a book's figures, tables, notes, headings or equations, or add a book (`books/<key>/book.toml`), read `docs/scanned-books.md`.
- **Numbering**: sections, paragraphs, equations, figure captions, cross-references, and citations use counters, labels, and `@ref`/`\ref`/`\hyperlink` via `src/compiler/source_numbers.py` (`cross_references=True`), checked by `src/literal_numbers.py`.
- **Review**: before you review any output folder against its scan, redshift its pages, record findings, or track a rebuild's measures (`polytypst review`, `polytypst checklist`), read `docs/reviewing-books.md`.
- **Page check**: before you check transcript pages against their scan, word by word and table cell by table cell (`scripts/page_check.py`), read `docs/page-check.md`. Before you start the checking agents, or verify, fix and record their issues, read `docs/page-check-review.md`.
- **Evidence**: before you blame code for a wrong word, note or call mark (①②), change shared code in `src/compiler/`, or attach scan proof to a finding (`polytypst evidence`), read `.claude/skills/scan-evidence/SKILL.md`.
- **OCR**: before you transcribe a scan (`polytypst SCAN.pdf --backend`) or add an OCR backend (`src/ocr/backend.py`), read "Transcribe the scan" in `docs/scanned-books.md`.
- **PDF**: use `import pymupdf` and `pymupdf.open(path)` in files, `eval`, and `python -c` (`fitz` is deprecated). Outside the repo, such as in the scratchpad, run them with `uv run --project <repo root> python ...` so uv loads the project's pymupdf.
- **Terms**: `GLOSSARY.md` names the source scan, rebuilt PDF, page map, scan parity, transcript, transcript store, and backend.
