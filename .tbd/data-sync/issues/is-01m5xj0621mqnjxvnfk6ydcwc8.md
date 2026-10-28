---
type: is
id: is-01m5xj0621mqnjxvnfk6ydcwc8
title: Change polytypst new-book to write books/<key>/book.toml
kind: task
status: open
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj06ewa30tbwrrcc8wz75f
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:03.360Z
updated_at: 2026-10-28T01:03:45.931Z
---
new_book.py writes book.toml and no longer edits pyproject.toml. Remove PACKAGES_RE and _list_package. Allow any folder name as the key. Done when tests/test_new_book.py covers the new output.
