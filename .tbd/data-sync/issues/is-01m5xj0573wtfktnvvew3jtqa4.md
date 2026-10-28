---
type: is
id: is-01m5xj0573wtfktnvvew3jtqa4
title: Migrate data-only single-edition books to book.toml
kind: task
status: open
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj0682858m2p53e39sr67f
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:02.499Z
updated_at: 2026-10-28T01:03:54.391Z
---
Move hecke, kashiwara, ode_arnold, bourbaki_lie, functional_analysis, modern_geometry_vol3 and 複素多様体論 to books/<key>/book.toml with their asset folders. Delete their src/<key>/ packages and pyproject entries. Done when their snapshot tests pass.

## Notes

Record the book's old output folder names in legacy_state in book.toml, so that migrate-state (Phase 3) can map old state to key and edition.
