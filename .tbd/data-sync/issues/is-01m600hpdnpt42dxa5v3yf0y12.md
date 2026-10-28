---
type: is
id: is-01m600hpdnpt42dxa5v3yf0y12
title: Add BookPaths and make catalog.open() return the Book handle
kind: task
status: open
priority: 2
version: 6
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-2
dependencies:
  - type: blocks
    target: is-01m600hpnrpb52qnc436hvg03w
  - type: blocks
    target: is-01m600hpzrjfdv53yg8zb8ttjm
  - type: blocks
    target: is-01m600hq7snwe9tz08mc1tnxc1
  - type: blocks
    target: is-01m600hqq6b6vb9zem8xd74ew5
  - type: blocks
    target: is-01m600hqz1y0dpxq6thst4v18p
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-28T01:03:46.101Z
updated_at: 2026-10-28T01:03:47.681Z
---
BookPaths derives transcripts, lines, renders, page_fit, build(edition) and work(command, ...) from the key and $POLYTYPST_BOOKS, per the layout table in the spec. catalog.open(key) returns a Book with .paths. Done when a test checks every attribute against the spec's layout table for an underscore key and a Chinese key.
