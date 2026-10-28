---
type: is
id: is-01m5xj04kmhb5n5pzcmjk3g7kw
title: Bind hooks.py functions to callable spec fields by name
kind: task
status: open
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj05m79fatpw31bj9n6a5x
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:01.876Z
updated_at: 2026-10-28T01:03:45.894Z
---
Functions named heading_hook, source_line_breaks or justify_page_end fill those MonographSpec fields. figures fills Book.figures. An edition may rename a hook (hooks = {heading_hook = "..."}) or set prepare. Raise an error for a hook named in TOML but missing, and for a public hooks.py function that nothing binds. Callable fields in TOML are an error. Done when each rule has a failing-first test.
