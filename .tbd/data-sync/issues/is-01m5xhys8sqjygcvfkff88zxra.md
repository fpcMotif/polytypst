---
type: is
id: is-01m5xhys8sqjygcvfkff88zxra
title: "A book is a project with one key: book folder in git, state folder outside"
kind: epic
status: open
priority: 2
version: 24
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
  - is-01m600hpdnpt42dxa5v3yf0y12
  - is-01m600hpnrpb52qnc436hvg03w
  - is-01m600hpzrjfdv53yg8zb8ttjm
  - is-01m600hq7snwe9tz08mc1tnxc1
  - is-01m600hqffn37fnb0tax6c6tgd
  - is-01m600hqq6b6vb9zem8xd74ew5
  - is-01m600hqz1y0dpxq6thst4v18p
  - is-01m600hr7a3gtp6p37syxhk8sj
  - is-01m600hrfxnr2ssaqdxnayankv
created_at: 2026-10-27T02:10:17.496Z
updated_at: 2026-10-28T01:03:48.220Z
---
Each book gets one key and two folders. books/<key>/ in git holds book.toml, an optional hooks.py and hand-made figures. $POLYTYPST_BOOKS/<key>/ holds transcripts/, lines/, renders/, build/<edition>/ and work/<command>/. catalog.open(key) returns a Book whose BookPaths derive every path from the key. Phase 1: book folders and book.toml. Phase 2: one key and the Book handle. Phase 3: migrate-state and the fixed state layout. Done when no src/<key>/, out_dir, OUTPUT or book_state(out_dir) remains, migrate-state has moved the real state after a reviewed dry run, and pytest passes.
