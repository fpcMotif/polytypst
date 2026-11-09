---
name: book-typography
description: Typeset a book in Typst or LaTeX to a publisher's standard and prove its pages, for math, CS, economics, literature, philosophy and Chinese or Japanese books. Use when you design a book's page frame (trim, margins, measure, leading, running heads, chapter openings), restyle or fix how a book PDF looks, or check spreads, baseline grid, word spacing, hyphens, widows and orphans in a rebuilt PDF.
---

# Book typography

A book page is judged as a **spread**: two facing pages whose text blocks, baselines and running heads match across the spine. Its quality is **page colour**: an even grey with no loose or tight lines, no rivers and no hyphen streaks. Every value you set serves those two words. The measured rules live in [references/rules.md](references/rules.md). The scripts and templates here put them into effect.

## Before you start

- **Branch.** Name the case first.
  - *New frame*: a book without a design. Start from a template.
  - *Restyle*: an existing Typst or LaTeX book. Keep its house style and fix defects.
  - *polytypst rebuild*: a book rebuilt from a scan. The scan's design wins (`docs/publisher-bar.md`, Rule 0). Use this skill's proof step and its rules as the floor for a defect, never as a reason to restyle.
- **Engine.** Typst keeps the baseline grid but cannot stretch a page, so a spread may end one line short. LaTeX (`\flushbottom`) keeps spreads level and lets displays drift off the grid. Read [references/typst.md](references/typst.md) or [references/latex.md](references/latex.md) for the engine you use, before you edit its source.
- **Tools.** Typst 0.15 (`typst`), tectonic (`~/.local/bin/tectonic`), and pymupdf through `uv run --project <polytypst root> python`.

## Steps

1. **Profile.** Pick the genre profile in [references/genres.md](references/genres.md) and read its section. For Chinese or Japanese, also read [references/cjk.md](references/cjk.md). Done when you can state the trim, body size and pitch, measure, figure style, heading scheme and hyphen streak limit.
2. **Frame.** For a new frame, copy [templates/book.typ](templates/book.typ) (`#show: book.with(genre: …)`) or [templates/book.tex](templates/book.tex) next to the book source. For a restyle, set the same values in the book's own preamble. Every vertical length is a whole number of lines. Done when the book compiles with no errors and no overfull lines in the log.
3. **Proof.** Run the checker on the PDF:

   ```
   uv run --project <polytypst root> python <skill dir>/proof.py BOOK.pdf --out PROOF_DIR --streak 2
   ```

   Pass `--streak 3` for literature and philosophy. Then look at the spread images in `PROOF_DIR`: every chapter opening, every page the checker names, and at least one spread in ten. Look for rivers, heads that collide with folios, figures that cross the text block, and running heads on opening pages.
4. **Fix.** Fix the frame before paragraphs, and paragraphs before page breaks. Use the levers below. After each fix, recompile and run step 3 again.

Done when `proof.py` prints no FAIL, and each WARN is either fixed or named with its page and a reason (a chapter end, the scan's own design, a paragraph that cannot be reset). You must also have viewed the spread images listed in step 3.

## Levers

| Symptom | Typst | LaTeX |
|---|---|---|
| Word spaces under 0.2 em or over 0.5 em | `justification-limits` as a ratio of the measured space, with the floor raised by the tracking. Allow hyphenation. | `\tolerance`, `\emergencystretch`, microtype protrusion |
| Hyphen streak over the limit | `costs: (hyphenation: 150%)` or more. Rewrite only as a last resort. | `\doublehyphendemerits=10000` |
| Widow or orphan | `costs: (widow:, orphan:)` above 100%, then a shorter footnote or a moved figure | `\widowpenalty`, `\clubpenalty`, `\enlargethispage` on both pages |
| Text off the grid after a block | `snap` the block. Use gaps of `line-gap + k × pitch`. | Accept it on pages with displays. Use `\flushbottom`. |
| Spread one line uneven | Move a float, or run both pages short | `\enlargethispage{±\baselineskip}` on both pages |
| Measure outside 45–75 characters | Change the text width, never the body size alone | `\settypeblocksize` |
| Heading split from its text | `block(sticky: true)` | Built in. Check `\needspace` in custom styles |

## Report

Give a table with one row per `proof.py` check (verdict, value, pages), then the spreads you viewed and what you saw on each. Say which branch you took and which rules the scan overrode.
