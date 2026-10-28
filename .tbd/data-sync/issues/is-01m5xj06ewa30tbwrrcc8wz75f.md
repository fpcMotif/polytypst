---
type: is
id: is-01m5xj06ewa30tbwrrcc8wz75f
title: Remove the book package machinery
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-2
dependencies:
  - type: blocks
    target: is-01m5xj06njta7tzxqc32a6cz2c
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:03.771Z
updated_at: 2026-10-27T02:11:03.986Z
---
Delete src/books.py (callers import polytypst.catalog), the book entries and the [0-9]*/*.py glob in pyproject.toml, tests/test_packaging.py and scripts/one_book.py. Done when no src/<key>/book.py remains, polytypst books lists every key, and pytest passes.
