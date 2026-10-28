---
type: is
id: is-01m5xj04sybp769agmsmgddrtq
title: Make src/books.py return books from both src/*/book.py and books/*/
kind: task
status: open
priority: 2
version: 6
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
  - type: blocks
    target: is-01m5xj05vk1xdhmv8vs0qye847
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:02.078Z
updated_at: 2026-10-28T01:03:45.900Z
---
During migration books(), book_by_key(), book_for_scan(), book_specs() and find_known_book() read both locations. A key defined in both is an error. Move the hard-coded sga4_5 aliases to the aliases key. A broken book must not stop book_by_key on another book. Done when polytypst books lists the same keys as before and an isolation test passes.
