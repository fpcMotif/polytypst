---
type: is
id: is-01m5xj06ewa30tbwrrcc8wz75f
title: Remove the book package entries from pyproject.toml
kind: task
status: open
priority: 2
version: 6
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m600hpdnpt42dxa5v3yf0y12
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:03.771Z
updated_at: 2026-10-28T01:03:48.566Z
---
Delete the polytypst.<key> book entries and the [0-9]*/*.py package-data glob in pyproject.toml, and tests/test_packaging.py. src/books.py and scripts/one_book.py stay until Phase 2. Done when no src/<key>/book.py remains, polytypst books lists every key, and pytest passes.
