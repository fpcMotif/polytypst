# Python 3.15 with the GIL

polytypst runs on the standard Python 3.15 build, not on the free-threaded 3.15t build. PyMuPDF holds the GIL while it renders a page, so threads cannot overlap PyMuPDF work. Parallel page work runs in processes instead, as `measure_pages` in `src/parity/measure.py` does.

## Considered Options

- **Free-threaded 3.15t.** PyMuPDF 1.28.2 has no 3.15t wheel. Its source build stops at the check `py_limited_api=True and Py_GIL_DISABLED=1 are not supported together`. With `PYMUPDF_SETUP_PY_LIMITED_API=0` the build gets further, then fails with `use of undeclared identifier 'PyString_FromString'` in the generated MuPDF bindings. A working build would still not help. The CPython documentation says that the interpreter turns the GIL back on when it imports an extension module that does not declare free-threading support.
- **Threads around PyMuPDF.** On 48 pages at 300 dpi with Python 3.12 and PyMuPDF 1.28.2, serial rendering took 0.79 s, 8 threads took 0.78 s, and 8 processes took 0.29 s.
- **Replace PyMuPDF with pylopdf.** pylopdf 0.16.0 ships cp315t wheels and renders with its own Rust rasterizer. On 48 pages of the book 1 source scan at 300 dpi, PyMuPDF took 7.2 s and pylopdf took 91.8 s serially and 118.0 s with 8 threads. Its pixels matched PyMuPDF's on those scan pages. On the rebuilt PDF it took 1.51 s against PyMuPDF's 0.65 s. Its API also differs (`page.pixmap`, `page.words()`, a drawing canvas), so all 42 files would change.
- **Replace PyMuPDF with pypdfium2.** 42 source files call PyMuPDF. `get_drawings`, `show_pdf_page` and `insert_text` have no direct pypdfium2 equivalent. PDFium is not thread-safe either, so the change would not make threads useful.

## Consequences

The Rust extension in `native/` declares `gil_used = false`. A hot render path that moves into it can release the GIL and use threads on either Python build. Try 3.15t again when PyMuPDF publishes free-threaded wheels.
