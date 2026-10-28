---
type: is
id: is-01m5xj047r1674dmcp2pt1rfjc
title: Add src/catalog.py with folder discovery, lazy loading and a strict book.toml loader
kind: task
status: closed
priority: 2
version: 8
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj04dhqzvhe4jg7zk4cmsd
  - type: blocks
    target: is-01m5xj04kmhb5n5pzcmjk3g7kw
  - type: blocks
    target: is-01m5xj04sybp769agmsmgddrtq
  - type: blocks
    target: is-01m5xj0573wtfktnvvew3jtqa4
  - type: blocks
    target: is-01m5xj0621mqnjxvnfk6ydcwc8
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:01.496Z
updated_at: 2026-10-28T01:53:34.572Z
closed_at: 2026-10-28T01:53:34.569Z
close_reason: Done in commit 80c5f152 (workspace book-catalog).
resolution: null
duplicate_of: null
---
Discover books/<key>/ folders that hold book.toml or book.py without importing them. Load MonographSpec, ChapterSpec and FigureLayout from TOML: arrays become tuple or frozenset per annotation, dict[int,...] keys parse from strings, relative paths resolve against the book folder, running_headers feeds running_header_regexes(), aliases and out_dir are loader keys. Reject unknown keys, wrong types and bad Literal values with file and key in the error. Import book.py by path under polytypst_books.b_<hash> with submodule_search_locations. Done when loader tests compare sample TOML against hand-built specs and each rejection rule has a test that fails without the rule.
