---
type: is
id: is-01m600hpnrpb52qnc436hvg03w
title: Replace out_dir, OUTPUT and book_state() uses in src/ with book.paths
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-10-27-book-catalog-toml.md
labels:
  - phase-2
dependencies:
  - type: blocks
    target: is-01m600hqffn37fnb0tax6c6tgd
parent_id: is-01m5xhys8sqjygcvfkff88zxra
created_at: 2026-10-28T01:03:46.359Z
updated_at: 2026-10-28T01:03:47.182Z
---
out_dir appears 333 times in 49 files and book_state() is called in 10 places. Start with the four that add markdown_pages by hand: vision/diagram_engine.py:538, vision/diagram_crops.py:107, goursat/build.py:192, 1_宏观经济与产业结构/figures.py:72. Builds write to build/<edition>/ and commands write only their own work/<command>/. Done when rg finds no OUTPUT or book_state(out_dir) in src/ and pytest passes.
