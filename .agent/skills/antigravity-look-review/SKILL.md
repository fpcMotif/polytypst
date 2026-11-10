---
name: antigravity-look-review
description: Look review of one group (G1 to G9) of unchecked math books in polytypst, run as an orchestrator that sends every page group to a subagent, a three-group sample first. Use when asked to run, resume or merge a look review for a group or a book of the Groups table.
---

# Look review of the unchecked math books

You are the orchestrator of a look review. Your workspace is W, /Users/martinfan/devv/polytypst-output/look_review, which holds every review and the command W/lr. The polytypst repository stays outside it. GROUP is the group the user names, such as G3. AGENTS is 8, unless the user names another number. Your books are the row of GROUP in the Groups table.

The page group is the unit of work: 10 rebuilt pages that one subagent checks strictly against the scan. The sample is three page groups of a book: front, middle and back. Each book's sample runs first. You check no page yourself, except in the spot check. Every page group goes to a subagent. The scan is the witness. A finding is one JSON line that a subagent writes, and it stays a claim until the witness confirms it.

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

1. Run every command from W, written exactly as in Tools. W/lr runs each tool in the repository with its scan, book and output folders. When W/lr is missing, stop and ask the user to run `mise exec -- uv run python scripts/look_review.py workspace` in the repository.
2. Start every subagent with `invoke_subagent` and `Workspace='inherit'`. Its world is LB: the brief names only LB's sheets, LB/transcript/ and LB/lr, and LB/lr runs check and crop for it from any folder. Antigravity cannot give a subagent another folder, because Workspace takes only inherit, share or branch, so the brief is what keeps it out of the repository.
3. Write only under /Users/martinfan/devv/polytypst-output/look_review/BOOK/, which holds the sample in BOOK/sample/. The merge also writes review_findings.jsonl and review_findings.md in /Users/martinfan/devv/polytypst-output/.
4. Leave the repository unchanged and unread: W/lr is your only way into it. No edits, no commits, no git or jj, no `audit --update`.
5. Use only the commands in Tools. When one prints an error that Tools does not list, report its last 20 lines and set that book aside.
6. When a usage or quota limit stops you, stop. Finished page groups stay on disk, and `status` shows what is left.

## Tools

BOOK is a key from the Groups table, such as fga. NN is a page-group number from `status`, such as 03. LB is the folder that prepare prints: /Users/martinfan/devv/polytypst-output/look_review/BOOK/sample for the sample, and /Users/martinfan/devv/polytypst-output/look_review/BOOK for the full pass.

SAMPLE is ` --sample` while you work on a book's sample, and nothing in its full pass. Put it at the end of every lr command except build.

status, brief and check end in a FileNotFoundError for look_groups.json until prepare has run for the book.

```text
build: make the rebuilt PDF.
   ./lr build BOOK
   Done: a line ending in ".pdf: N pages", and exit code 0. It takes minutes, so wait for it.
   A Traceback or a nonzero exit code is an error.
prepare: render the pages at 110 dpi, pair each rebuilt page with its scan pages, run the checker, write the page groups of 10, copy the transcript pages to LB/transcript/, and write LB/lr, the subagents' command.
   ./lr prepare BOOK SAMPLE
   Done: five lines, starting "rebuilt: PATH", "scan: PATH; pages paired by …", "N of M pages, G groups of 10; …", "checker: RULE on K pages, …" or "checker: no hits", and "folder: LB".
   "rebuilt:" followed by "(stale: …)": the PDF is older than the code. Run build again, then prepare again. When it is still stale, report that and go on.
   "… is missing; run: polytypst build BOOK": run build, then prepare again.
   "BOOK: no transcripts at PATH", a line naming POLYTYPST_BOOKS or the scan, or a KeyError: set the book aside.
   prepare renders again each PNG that is older than its PDF, and rewrites the page groups. Run it before any subagent starts on LB, and never after.
status: list the page groups.
   ./lr status BOOK SAMPLE
   Done: one line per page group, "group NN pA-B: done" or "group NN pA-B: todo (REASON)", then "all groups done" or "K groups todo".
brief: print the whole task for one page group.
   ./lr brief BOOK NN SAMPLE
   Done: text that names LB/group_NN.jsonl and LB/group_NN.audit.jsonl and ends with "Facts for this review". Paste it unchanged.
   An IndexError means NN is past the last page group.
check: test the two files of one page group.
   ./lr check BOOK NN SAMPLE
   Done: the line "ok", and exit code 0.
   Otherwise each line names one problem, such as "group_NN.audit.jsonl is missing", "group_NN.jsonl line 4: missing field 'evidence'", "cause 'book.toml' is not one of transcript, build, unknown" or "group_NN.audit.jsonl has no line for pages 41, 42".
crop: put boxes of rebuilt pages beside the same boxes of their scan pages on one sheet. REGION is PAGE:BOX or PAGE:BOX:SCANBOX, with BOX top, middle, bottom, full, or L,T,R,B in page shares.
   ./lr crop BOOK REGION [REGION …] SAMPLE
   Subagents run LB/lr crop REGION instead, which already knows BOOK and SAMPLE.
   Done: one path, LB/crops/sheet_….png.
   A line naming the box or the page instead: fix the REGION and run it again.
spot: pick 3 findings of severity P0 or P1 and 2 pages that the audit marks PASS, and render each as one sheet: its scan pages beside its rebuilt page.
   ./lr spot BOOK SAMPLE
   Done: one line per item with the path of its sheet under it, then "N items; write one line per item to LB/spot_check.jsonl".
   An item with no sheet path names no rebuilt page. Judge it from the pair sheets LB/png/pair_NNN.png of the pages its text names.
merge: number the findings of a finished LB and add them to the shared checklist. Run it once for the sample and once for the full pass.
   ./lr merge BOOK SAMPLE
   Done: "appended N findings (ID to ID); BOOK: P0 n, …", then "checklist: PATH".
   "K pages have no audit line: …; rerun those groups": queue the page groups that hold those pages.
   "BOOK is already merged; see PATH": that LB is done. Do not merge it again.
   Lines of the form "group_NN.jsonl line K: …": send them to a new subagent for that page group, then merge again.
```

## Phase A: prepare the sample of every book of the group

Prepare one book at a time, before any subagent starts. SAMPLE is ` --sample` through Phases A to C.

1. Run build for the book.
2. Run prepare for the book. Report its "N of M pages, G groups" line and its "checker:" line.

Phase A is done when every book has a "folder:" line or a reason it was set aside.

## Phase B: one queue of page groups for all books of the group

1. Run status for each prepared book. Every todo page group joins the queue, book by book.
2. Keep AGENTS subagents running. When a slot frees, give it the next page group in the queue that its book allows. A book whose spot check has not passed yet gets at most 3 page groups started. Skip to the next book while it waits.
3. Start a subagent for page group NN of BOOK with one message: the output of brief for BOOK NN, then the Subagent lines, the Shared note and BOOK's notes from [references/book-notes.md](references/book-notes.md).
4. When a subagent finishes, run check for BOOK NN. When it prints problems, send them back to that subagent once. When the second check also prints problems, put the page group back in the queue for a new subagent.
5. Spot check each book when its first 2 page groups print "ok":
   1. Run spot for the book, and open the sheet of each item. To read a region closer, run crop.
   2. Judge each item against the witness. Write one line for it to LB/spot_check.jsonl: `{"page": P, "item": "group_NN.jsonl line K" or "PASS", "agent_right": true or false, "why": "..."}`
   3. With 4 or 5 right, the book's spot check passes and its page groups flow freely. With 3 or fewer right, set the book aside and report the lines.

Phase B is done when the queue is empty and every subagent has finished.

## Phase C: merge

Run merge for each book whose status ends with "all groups done". Phase C is done when every book is merged or set aside.

## Phase D: the full pass

A book goes on to the full pass when its sample has no finding with a "cause_id" and its "checker:" line said "no hits". Run Phases A to C again for those books with SAMPLE empty. Skip the build when the "rebuilt:" line showed no "(stale: …)".

Every other book waits: a cause id or a checker rule is one fix in src/compiler or book.toml that changes many pages. Report its cause ids and checker rules with their page counts.

## Report

Write one block per book:

- Rebuilt pages checked of the page count, page groups, findings appended, and whether the full pass ran or what it waits for.
- Findings by severity (P0 to P3), by cause (transcript, build, unknown) and by cause id, and the "checker:" line.
- The spot check: how many of 5 the subagents got right.
- The 10 worst findings, each with its rebuilt page, its scan page and one line.
- Each failed command with its last 20 lines, and each book set aside with its reason.

## Close the workspace

Run `./lr clean` only when the user says that every look review is done. It removes W/lr and W/.agent, this skill's copy, and keeps every review and finding. To change this skill, edit it in the repository, then the user runs `workspace` again, which copies it to W anew.
