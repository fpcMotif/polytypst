---
type: is
id: is-01m5xj05dq2yzn3s70rw29ghg0
title: Migrate multi-edition and facsimile books to book.toml
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
created_at: 2026-10-27T02:11:02.710Z
updated_at: 2026-10-28T01:53:36.866Z
---
Move fermat, kenji_alg, algebra2, algebra3, klein, siegel_symplectic, grothendieck, fga, sga4_5, modern_geometry, modern_geometry_vol2 and ahlfors. Express volume and illustrated variants as [editions.<name>.spec] overrides. Done when their snapshot tests pass.

## Notes

80c5f152: monograph editions in TOML are done. Still open: hooks.py binding and the facsimile kind; 16 books keep book.py until then.
