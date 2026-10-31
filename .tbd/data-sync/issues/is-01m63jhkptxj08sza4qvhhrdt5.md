---
type: is
id: is-01m63jhkptxj08sza4qvhhrdt5
title: "Book 4: Haiku 5.5 scan-image check of 115 undecided page-check findings"
kind: task
status: closed
priority: 3
version: 2
labels:
  - book4
  - page-check
dependencies: []
created_at: 2026-10-29T10:16:00.985Z
updated_at: 2026-10-31T07:10:35.294Z
closed_at: 2026-10-31T07:10:35.291Z
close_reason: "Superseded: book_check.py triage/verify on the mixed branch already verified Book 4 (4 unverified left)"
resolution: null
duplicate_of: null
---
Deferred from the Book 4 false-positive triage on the mixed worktree (1718d0c).

Input: /Users/martinfan/devv/polytypst.mixed/output/page_check/4/triage.json (script: triage.py beside it).
Queue: 98 findings with verdict 'undecided' and 17 with 'likely_false_positive' (OCR vote only), on 67 pages.
OCR votes can share an error with the transcript (p33 j=0.1, 2 should read 0, 1, 2), so each needs the scan image.

Plan: crop each finding's line band from output/page_check/4/png/pN.png and send the crop plus the transcript and checker readings to claude-haiku-5-5 (haiku-bite style, image in, one verdict out: transcript right / checker right / neither). Batch ~10 crops per call. Write verdicts back into triage.json.

Done when: no finding in triage.json has verdict undecided or likely_false_positive.
