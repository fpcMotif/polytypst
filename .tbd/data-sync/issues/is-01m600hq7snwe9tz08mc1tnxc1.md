---
type: is
id: is-01m600hq7snwe9tz08mc1tnxc1
title: Pass BookPaths to the figures and prepare hooks
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
created_at: 2026-10-28T01:03:46.937Z
updated_at: 2026-10-28T01:03:47.182Z
---
Hooks receive BookPaths instead of an out_dir. Update hooks.py of kodaira, ahlfors, fichtenholz_vol1, modern_geometry_vol2 and the economics books. Done when their figure builds write under build/<edition>/figures and snapshot tests pass.
