---
type: is
id: is-01m600hqq6b6vb9zem8xd74ew5
title: Add polytypst migrate-state with dry run and --apply
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-3
dependencies:
  - type: blocks
    target: is-01m600hr7a3gtp6p37syxhk8sj
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-28T01:03:47.429Z
updated_at: 2026-10-28T01:03:47.946Z
---
Map old state to the new layout using legacy_state, per the table in the spec. Dry run by default; --apply moves without overwriting; never delete a transcript; keep both copies of differing line caches and report them; list unknown folders and leave them; a second run prints nothing to move. Done when the migration test on a temporary old-style tree passes all five rules.
