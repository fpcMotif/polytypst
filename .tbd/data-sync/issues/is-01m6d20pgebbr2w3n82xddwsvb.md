---
type: is
id: is-01m6d20pgebbr2w3n82xddwsvb
title: Make the scan command finish its pending pages (architecture candidate 2)
kind: task
status: in_progress
priority: 2
version: 3
delegate: claude-code@f
labels:
  - architecture
dependencies: []
hold: null
hold_until: null
created_at: 2026-11-02T02:39:33.901Z
updated_at: 2026-11-02T02:52:00.370Z
started_at: 2026-11-02T02:42:59.487Z
---
TranscriptStore.transcribe retries pending pages in rounds (stop on a round with no progress or after --rounds, default 3). Colab cluster VM names carry a run id so a run stops only its own VMs (retro fix 7). Branch scan-until-done from page-check-module.

## Notes

Built in jj change on bookmark scan-until-done (workspace ../polytypst.scan-until-done), on top of page-check-module. Tests: 5 new or changed tests went red first; full suite has the same 11 failures as page-check-module. Not pushed.
