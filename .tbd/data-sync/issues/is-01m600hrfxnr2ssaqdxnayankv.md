---
type: is
id: is-01m600hrfxnr2ssaqdxnayankv
title: Remove legacy_state from every book.toml
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-3
dependencies:
  - type: blocks
    target: is-01m5xj06njta7tzxqc32a6cz2c
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-28T01:03:48.220Z
updated_at: 2026-10-28T01:03:48.776Z
---
After the real migration, delete legacy_state keys and the loader's support for them. Done when no book.toml has legacy_state and pytest passes.
