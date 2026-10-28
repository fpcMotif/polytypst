---
type: is
id: is-01m5xj05vk1xdhmv8vs0qye847
title: Move london_treasury to books/ with its book.py unchanged
kind: task
status: closed
priority: 2
version: 5
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj0682858m2p53e39sr67f
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:03.155Z
updated_at: 2026-10-28T01:53:35.260Z
closed_at: 2026-10-28T01:53:35.259Z
close_reason: Done in commit 80c5f152 (workspace book-catalog).
resolution: null
duplicate_of: null
---
london_treasury has a custom pipeline. Move the folder to books/london_treasury/ and keep book.py as the escape hatch. Switch its intra-book imports to relative imports. Done when tests/test_london_wso.py passes.

## Notes

Record the book's old output folder names in legacy_state in book.toml, so that migrate-state (Phase 3) can map old state to key and edition.
