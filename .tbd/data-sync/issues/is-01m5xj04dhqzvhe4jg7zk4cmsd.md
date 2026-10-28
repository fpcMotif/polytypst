---
type: is
id: is-01m5xj04dhqzvhe4jg7zk4cmsd
title: "Support [editions.*] tables: monograph and facsimile kinds with spec overrides"
kind: task
status: open
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj05dq2yzn3s70rw29ghg0
  - type: blocks
    target: is-01m5xj05m79fatpw31bj9n6a5x
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:01.680Z
updated_at: 2026-10-27T02:11:02.918Z
---
Each [editions.<name>] has kind (monograph default, or facsimile), summary, out_dir, a spec table applied with dataclasses.replace, and a facsimile table of FacsimileStyle fields. First edition is the default. No editions table means one monograph edition. Done when tests cover fermat-style multi-volume overrides and an algebra3-style facsimile edition.
