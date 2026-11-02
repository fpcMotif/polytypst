---
type: is
id: is-01m6d38q10wk4pxcdar75v2wfd
title: Make the language and domain profiles the one source of heading and reference words (architecture candidate 3)
kind: task
status: in_progress
priority: 2
version: 2
delegate: claude-code@f
labels:
  - architecture
dependencies: []
hold: null
hold_until: null
created_at: 2026-11-02T03:01:25.151Z
updated_at: 2026-11-02T03:05:06.420Z
started_at: 2026-11-02T03:05:06.419Z
---
LanguageProfile spells theorem, reference and chapter words; DomainProfile lists kinds and math operators; one CompositionConfig method feeds the Typst heading template, source_numbers and literal_numbers. LaTeX level-1-to-chapter rule behind a book.toml switch. supp/loc rewrites gated on the domain. Branch profile-words from mixed-review.
