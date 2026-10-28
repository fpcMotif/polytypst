---
type: is
id: is-01m5xj05vk1xdhmv8vs0qye847
title: Move london_treasury to books/ with its book.py unchanged
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-2
dependencies:
  - type: blocks
    target: is-01m5xj0682858m2p53e39sr67f
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:03.155Z
updated_at: 2026-10-27T02:11:03.553Z
---
london_treasury has a custom pipeline. Move the folder to books/london_treasury/ and keep book.py as the escape hatch. Switch its intra-book imports to relative imports. Done when tests/test_london_wso.py passes.
