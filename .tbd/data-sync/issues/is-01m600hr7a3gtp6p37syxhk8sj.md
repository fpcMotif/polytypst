---
type: is
id: is-01m600hr7a3gtp6p37syxhk8sj
title: Run migrate-state on the real state after a reviewed dry run
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-3
dependencies:
  - type: blocks
    target: is-01m600hrfxnr2ssaqdxnayankv
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-28T01:03:47.946Z
updated_at: 2026-10-28T01:03:48.220Z
---
Run the dry run on the real $POLYTYPST_BOOKS and output/. Show the plan to the user and wait for approval before --apply. After --apply, check transcript counts per book against the dry run. The user deletes output/ after checking. Done when the user confirms the moved state.
