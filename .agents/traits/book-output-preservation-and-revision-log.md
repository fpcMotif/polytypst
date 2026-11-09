---
name: book-output-preservation-and-revision-log
subject: "Code, scripts and cleanup operations that delete, move, overwrite or
  revise files of a book: its raw scanned transcripts, its generated Typst and
  TeX sources, and its review records."
requirement: Raw scanned transcripts (the per-page Markdown from OCR, such as
  markdown_pages and source_ocr) are never deleted, moved or edited by code or
  cleanup; generated .typ and .tex sources are never deleted; review records
  (.jsonl, .json, .md under review folders) are never deleted; and every
  revision step applied to a book appends a record of what changed and why to
  that book's review .jsonl, .json or .md log.
applicability: Applies to any change that touches the transcript store or the
  output root ($POLYTYPST_OUTPUT), including cleanup scripts and refactors of
  build paths. Rendered images, page renders, TeX auxiliary files (.aux, .log)
  and caches may be deleted when they can be regenerated.
purpose: Transcripts are the irreplaceable raw material of every rebuild, Typst
  and TeX sources show exactly what a build produced, and the review log is the
  history that continuous improvement builds on; losing any of them loses work
  that cannot be regenerated or audited.
guidance: Before a cleanup, classify files by kind and exclude transcripts,
  .typ, .tex and review records by rule rather than by folder; when a rebuild or
  fix changes a book, write the review record in the same step.
---
