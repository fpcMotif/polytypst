# What each subagent gets under its brief

Paste the Subagent lines, the Shared notes and the book's own notes under each brief. Each book fact was read from the scan, so the subagent can tell the book's design from a defect.

## Subagent lines

- Check your 20 pages strictly, one at a time, each rebuilt PNG beside its scan PNG, line by line. The scan is the witness. Every page gets its audit line, PASS or FAIL.
- Run the check the brief names as `mise exec -- uv run python scripts/look_review.py check BOOK NN` from /Users/martinfan/devv/polytypst. It must print "ok".
- You must see each PNG as an image. When your tools cannot show you an image, stop and say so.
- When a scan page shows different text from its rebuilt page, open the scan pages before and after it, and name the matching one in "where".
- Put the paths of both 300 dpi crops, rebuilt and scan, in "evidence" for every finding about math.
- When a defect matches a cause id in the notes, add that id, such as "RC-04", to the end of "cause".

## Shared notes

- Cause ids for defects still open:
  - RC-04: the running head runs into its folio, as in "(REAL OR COMPLEX CASE)159", or the running head is body text.
  - RC-05: a footnote sits in the body text, not at the foot of the page.
  - THM-SPACE: no space after a theorem where the scan leaves one.
- Fixed on 2026-11-09, so each is a P0 regression when it appears:
  - RC-02: a chapter-opening page with no folio.
  - RC-03: a chapter number that the scan does not print, as in "1 Part I: Introductory Remarks".
  - RC-06: a theorem, lemma, corollary or proposition body in a style the scan does not use. The table below gives each book's style.
- The rebuild sets a typescript in a book face. That change passes.

## Statement style per book

| Body style | Books |
|---|---|
| italic | `hecke`, `weil`, `courant_hilbert1`, `functional_analysis`, `kashiwara` (with its items (1), (2)), `fermat` |
| upright | `fga`, `sga4_5` (underlined in the scan), `klein`, `fga_explained_barbara_fantechi_lothar_gottsche`, `kodaira`, `algebra2`, `fichtenholz_vol1`, `book4`, `dl5`, `複素多様体論` |
| not yet read | `analysis_elliott_h_lieb_michael_loss_2001`, `spivak_vol3`, `modern_geometry_vol2`, `newtonprincipia`: report the scan's style as one P3 finding with its page |

## Book facts

- `fermat`: an attribution after a head, as in "Theorem 9.22. (Jacobi)", is roman.
- `fga`, `sga4_5`: French spacing, a thin space before `; : ! ?` and inside « ».
- `kodaira`: 10 of 417 scan pages have no transcript. Text missing there has cause "transcript".
- `book4`, `dl5`: check code and pseudocode by the CS list in `docs/double-check-guide.md`.
