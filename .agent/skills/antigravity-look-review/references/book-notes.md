# What each subagent gets under its brief

Paste the Subagent lines, the Shared note and the book's own notes under each brief. The brief itself ends with the cause list, the known cause ids and the check command. Each book fact was read from the scan, so the subagent can tell the book's design from a defect.

## Subagent lines

- Check your pages strictly, one pair sheet at a time. The scan is the witness. Every page gets its audit line, PASS or FAIL.
- You must see each PNG as an image. When your tools cannot show you an image, stop and say so.
- When a scan page shows different text from its rebuilt page, open the scan pages before and after it, and name the matching one in "where".
- Put the path of the crop sheet that shows the region, scan beside rebuilt, in "evidence" for every finding about a lost display.
- A known cause that the brief marks "fixed" or "holding" is a P0 regression when it appears.
- Use "cause_id": "THM-SPACE" when no space follows a theorem where the scan leaves one.

## Shared note

The rebuild sets a typescript in a book face. That change passes. For RC-06, the table below gives each book's statement style.

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
