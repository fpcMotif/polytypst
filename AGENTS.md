# polytypst

- **Books**: before you build a book edition (`polytypst build`), check one against its scan (`polytypst parity`), or add a book (`src/<key>/book.py`), read `docs/scanned-books.md`.
- **Review**: before you review any output folder against its scan, redshift its pages, record findings, or track a rebuild's measures (`polytypst review`, `polytypst checklist`), read `docs/reviewing-books.md`.
- **OCR**: before you transcribe a scan (`polytypst SCAN.pdf --backend`) or add an OCR backend (`src/ocr/backend.py`), read "Transcribe the scan" in `docs/scanned-books.md`.
- **Terms**: `GLOSSARY.md` names the source scan, rebuilt PDF, page map, scan parity, transcript, transcript store, and backend.
