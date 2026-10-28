---
type: is
id: is-01m5xj05m79fatpw31bj9n6a5x
title: "Migrate books with hooks: economics books, bourbaki, fichtenholz_vol1, kodaira"
kind: task
status: open
priority: 2
version: 5
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-1
dependencies:
  - type: blocks
    target: is-01m5xj0682858m2p53e39sr67f
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-27T02:11:02.918Z
updated_at: 2026-10-28T01:53:37.607Z
---
Move the five numbered economics books, bourbaki (keeps book.py for Parity), fichtenholz_vol1 and kodaira. Their heading_hook, source_line_breaks, justify_page_end and figure functions go to hooks.py. FONTS_DIR becomes a relative path in TOML. Done when their snapshot tests pass and one economics book builds the same .typ output as before.

## Notes

80c5f152: monograph editions in TOML are done. Still open: hooks.py binding and the facsimile kind; 16 books keep book.py until then.
