---
type: is
id: is-01m5xj050saryvnrrya4rptftj
title: Record spec snapshots of every edition from the current code
kind: task
status: open
priority: 2
version: 5
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj0573wtfktnvvew3jtqa4
  - type: blocks
    target: is-01m5xj05dq2yzn3s70rw29ghg0
  - type: blocks
    target: is-01m5xj05m79fatpw31bj9n6a5x
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:02.296Z
updated_at: 2026-10-28T01:03:45.905Z
---
Before any book moves, write repr(spec) for every edition of every book (hooks by function name) to test snapshots using the old src/<key> code. The migration tests compare catalog output against these snapshots, so they fail if the TOML drifts. Done when the snapshot test passes on the current tree.
