---
type: is
id: is-01m5xhys8sqjygcvfkff88zxra
title: "Book catalog: move books to books/<key>/book.toml with optional hooks.py"
kind: epic
status: open
priority: 2
version: 14
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels: []
dependencies: []
child_order_hints:
  - is-01m5xj047r1674dmcp2pt1rfjc
  - is-01m5xj04dhqzvhe4jg7zk4cmsd
  - is-01m5xj04kmhb5n5pzcmjk3g7kw
  - is-01m5xj04sybp769agmsmgddrtq
  - is-01m5xj050saryvnrrya4rptftj
  - is-01m5xj0573wtfktnvvew3jtqa4
  - is-01m5xj05dq2yzn3s70rw29ghg0
  - is-01m5xj05m79fatpw31bj9n6a5x
  - is-01m5xj05vk1xdhmv8vs0qye847
  - is-01m5xj0621mqnjxvnfk6ydcwc8
  - is-01m5xj0682858m2p53e39sr67f
  - is-01m5xj06ewa30tbwrrcc8wz75f
  - is-01m5xj06njta7tzxqc32a6cz2c
created_at: 2026-10-27T02:10:17.496Z
updated_at: 2026-10-27T02:11:03.986Z
---
Each book moves from a polytypst.<key> package in src/ to books/<key>/: book.toml for the spec and editions, an optional hooks.py for callable fields, and book.py only for custom pipelines. src/catalog.py loads the folders by path and keeps the books(), book_by_key(), book_for_scan() and book_specs() signatures. Done when every book loads from books/, pytest passes, and pyproject.toml lists no book packages.
