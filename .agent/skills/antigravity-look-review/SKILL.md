---
name: antigravity-look-review
description: Look review of one group (G1 to G9) of unchecked math books in polytypst, run as an orchestrator that sends every 20-page page group to a subagent. Use when asked to run, resume or merge a look review for a group or a book of the Groups table.
---

# Look review of the unchecked math books

You are the orchestrator of a look review in /Users/martinfan/devv/polytypst. GROUP is the group the user names, such as G3. AGENTS is 8, unless the user names another number. Your books are the row of GROUP in the Groups table.

The page group is the unit of work: 20 rebuilt pages that one subagent checks strictly against the scan. You check no page yourself, except in the spot check. Every page group goes to a subagent. The scan is the witness. A finding is one JSON line that a subagent writes, and it stays a claim until the witness confirms it.

## Groups

The books in a group share a language and the same kinds of defects. Page counts are rebuilt-PDF pages on 2026-11-10.

| Group | Books (pages) |
|---|---|
| G1 French school | `fga` (172), `sga4_5` (187), `fga_explained_barbara_fantechi_lothar_gottsche` (353) |
| G2 Number theory | `hecke` (260), `weil` (296), `fermat` (196) |
| G3 Classical analysis | `courant_hilbert1` (531), `functional_analysis` (481) |
| G4 Analysis | `analysis_elliott_h_lieb_michael_loss_2001` (309), `kodaira` (398), `kashiwara` (252) |
| G5 Geometry with figures | `spivak_vol3` (256), `modern_geometry_vol2` (393) |
| G6 History and physics | `klein` (532), `newtonprincipia` (564) |
| G7 Chinese mathematics | `algebra2` (376), `fichtenholz_vol1` (579) |
| G8 Chinese deep learning | `book4` (231), `dl5` (236) |
| G9 Japanese | `複素多様体論` (503) |

These books are not ready for review:

- `modern_geometry` has no rebuilt PDF. After it is built, it joins G5.
- `modern_geometry_vol3` has no transcripts, and its title is that of another book.
- `ode_arnold` has no scan.
- `bourbaki` follows its own procedure in `docs/scanned-books.md`.

## Rules

1. Run every command from /Users/martinfan/devv/polytypst, written exactly as in Tools. `mise exec --` sets the scan, book and output folders, and the tools fail without it.
2. Run every subagent in this checkout, with worktree isolation off. mise.local.toml, which holds those folders, exists only here.
3. Write only under /Users/martinfan/devv/polytypst-output/look_review/BOOK/. The merge also writes review_findings.jsonl and review_findings.md in /Users/martinfan/devv/polytypst-output/.
4. Leave the repository unchanged: no edits, no commits, no git or jj, no `audit --update`.
5. Use only the commands in Tools. When one prints an error that Tools does not list, report its last 20 lines and set that book aside.
6. When a usage or quota limit stops you, stop. Finished page groups stay on disk, and `status` shows what is left.

## Tools

BOOK is a key from the Groups table, such as fga. NN is a page-group number from `status`, such as 03. LB is /Users/martinfan/devv/polytypst-output/look_review/BOOK.

uv may print "Bytecode compiled N files in …" first. That line is not output of the tool, so read past it.

status, brief and check end in a FileNotFoundError for look_groups.json until prepare has run for the book.

```text
build: make the rebuilt PDF.
   mise exec -- uv run python scripts/one_book.py BOOK build --formats pdf
   Done: a line ending in ".pdf: N pages", and exit code 0. It takes minutes, so wait for it.
   A Traceback or a nonzero exit code is an error.
prepare: render every page at 110 dpi, pair each rebuilt page with its scan pages, and split the book into page groups of 20.
   mise exec -- uv run python scripts/look_review.py prepare BOOK
   Done: four lines, starting "rebuilt: PATH", "scan: PATH; pages paired by …", "N pages, G groups of 20; …" and "folder: LB".
   "rebuilt:" followed by "(stale: …)": the PDF is older than the code. Run build again, then prepare again. When it is still stale, report that and go on.
   "… is missing; run: polytypst build BOOK": run build, then prepare again.
   "BOOK: no transcripts at PATH", a line naming POLYTYPST_BOOKS or the scan, or a KeyError: set the book aside.
   prepare keeps the PNGs and rewrites the page groups. Run it before any subagent starts on the book, and never after.
status: list the page groups.
   mise exec -- uv run python scripts/look_review.py status BOOK
   Done: one line per page group, "group NN pA-B: done" or "group NN pA-B: todo (REASON)", then "all groups done" or "K groups todo".
brief: print the whole task for one page group: its pages, their PNG paths, the bar, the file formats and the check to run.
   mise exec -- uv run python scripts/look_review.py brief BOOK NN
   Done: text that names LB/group_NN.jsonl and LB/group_NN.audit.jsonl. Paste it unchanged.
   An IndexError means NN is past the last page group.
check: test the two files of one page group.
   mise exec -- uv run python scripts/look_review.py check BOOK NN
   Done: the line "ok", and exit code 0.
   Otherwise each line names one problem, such as "group_NN.audit.jsonl is missing", "group_NN.jsonl line 4: missing field 'evidence'", "severity 'high' is not one of P0, P1, P2, P3" or "group_NN.audit.jsonl has no line for pages 41, 42".
merge: number the findings of a finished book and add them to the shared checklist. Run it once per book.
   mise exec -- uv run python scripts/look_review.py merge BOOK
   Done: "appended N findings (ID to ID); BOOK: P0 n, …", then "checklist: PATH".
   "K pages have no audit line: …; rerun those groups": queue the page groups that hold those pages.
   "BOOK is already merged; see PATH": the book is done. Do not merge it again.
   Lines of the form "group_NN.jsonl line K: …": send them to a new subagent for that page group, then merge again.
page_png: render pages of one PDF at a chosen zoom, for the spot check.
   mise exec -- uv run python scripts/page_png.py PDF PREFIX --pages P[,P…] --dpi 300
   Pages count from 1. Each page is written to PREFIX + "pP.png", and its path is printed.
   Add --clip L,T,R,B, each a share of the page from 0 to 1, to crop. An IndexError means the page is past the end of the PDF.
```

## Phase A: prepare every book of the group

Prepare one book at a time, before any subagent starts.

1. Run build for the book.
2. Run prepare for the book. Report its "N pages, G groups" line.

Phase A is done when every book has a "folder:" line or a reason it was set aside.

## Phase B: one queue of page groups for all books of the group

1. Run status for each prepared book. Every todo page group joins the queue, book by book.
2. Keep AGENTS subagents running. When a slot frees, give it the next page group in the queue that its book allows. A book whose spot check has not passed yet gets at most 3 page groups started. Skip to the next book while it waits.
3. Start a subagent for page group NN of BOOK with one message: the output of brief for BOOK NN, then the Subagent lines, the Shared notes and BOOK's notes from [references/book-notes.md](references/book-notes.md).
4. When a subagent finishes, run check for BOOK NN. When it prints problems, send them back to that subagent once. When the second check also prints problems, put the page group back in the queue for a new subagent.
5. Spot check each book when its first 2 page groups print "ok":
   1. Pick 3 findings of severity P0 or P1, and 2 pages that the audit file marks PASS.
   2. For each item, take the rebuilt page P and its "scan_pages" S from the audit line. Render both with page_png: the rebuilt PDF from the "rebuilt:" line with PREFIX LB/crops/spot_rebuilt_ and pages P, and the scan from the "scan:" line with PREFIX LB/crops/spot_scan_ and pages S.
   3. Judge each item against the witness. Write one line for it to LB/spot_check.jsonl: `{"page": P, "item": "group_NN line K" or "PASS", "agent_right": true or false, "why": "..."}`
   4. With 4 or 5 right, the book's spot check passes and its page groups flow freely. With 3 or fewer right, set the book aside and report the 5 lines.

Phase B is done when the queue is empty and every subagent has finished.

## Phase C: merge

Run merge for each book whose status ends with "all groups done". Phase C is done when every book is merged or set aside.

## Report

Write one block per book:

- Rebuilt pages, page groups, findings appended.
- Findings by severity (P0 to P3) and by cause (transcript, book.toml, src/compiler).
- The spot check: how many of 5 the subagents got right.
- The 10 worst findings, each with its rebuilt page, its scan page and one line.
- Each failed command with its last 20 lines, and each book set aside with its reason.
