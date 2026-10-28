---
type: is
id: is-01m600hqffn37fnb0tax6c6tgd
title: Delete Book.out_dir, Edition.rebuilt, OUTPUT, markdown_dir, books.py and one_book.py
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-2
dependencies:
  - type: blocks
    target: is-01m600hr7a3gtp6p37syxhk8sj
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-28T01:03:47.182Z
updated_at: 2026-10-28T01:03:47.946Z
---
Remove the old path APIs after every caller uses book.paths: Book.out_dir, Edition.rebuilt, OUTPUT, book_state(out_dir), MonographSpec.markdown_dir, src/books.py and scripts/one_book.py. Done when pytest passes and polytypst build hecke works.
