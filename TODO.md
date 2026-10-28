# TODO

Open problems in the Grothendieck facsimile (`polytypst build grothendieck --edition facsimile`).
Each item names the page in the source scan and what the rebuilt PDF does wrong.

## Math size

- [ ] p.379 and p.437: `A-module M` and `𝒪S-Algèbre` are set too big for their line.
- [ ] p.104: `𝒪Y-Modules` at the line end is set too big.
- [ ] p.325: `j*(𝒢)|U = j*(j*(𝒢)) = 𝒢` is set bigger than the scan. This came with the inline-math widening.
- [ ] p.177: `Aλ-module` is set far too small. This page is one of the 17 SHRUNKEN_DISPLAY_MATH pages.
- [ ] The other 13 SHRUNKEN_DISPLAY_MATH pages (`quality/baseline.json` holds 14).
- [ ] p.332: the vertical arrows between two diagram rows join the top row's display box, so `inkfit` stretches that row to twice its height.
- [ ] Pages 43, 44 and 184: the diagram rows next to an equation number get the wrong scan lines. On p.184 the bottom row `0 → E_{n+1} → …` is stretched across the number's row, and on p.44 the arrow row is stretched. Optical parity marks these three pages as regressed since the equation-number fix.
- [ ] p.42: the diagram `N → E ⇉ F` lost its second arrow `u₂`.
- [ ] Pages 242, 405, 469 and 471: small shifts of index entries and formulas, the same kind of error as before the unread-ink box fix.

## Missing text

- [ ] Bourbaki facsimile p.486: four lines are missing, from "(f) Suppose that A is a valuation ring" to "is the direct sum of a finite". Optical parity ranks it fifth in the book.

## Glyphs

- [ ] p.330: `𝒪X` is drawn as `CX`.

## Hyphenation

- [ ] p.462: `Hermann` is cut as `Herm-`, but the scan has `Her-`. The OCR misread the fragment, so the cut falls back to the ink width.

## Stale docstrings in `src/facsimile.py`

- [ ] `split_across_lines` still says it cuts "in proportion to each line's ink width". It now cuts at the scan's OCR fragment first.
- [ ] `page_words` does not mention the textless words for unread ink beside an OCR line.
- [ ] `transcript_typst` does not mention the `ink` parameter or inline-math widening.

## Other

- [ ] The Bourbaki vintage edition is line-broken like the scan, but does not set `scan_line_breaks`.
- [ ] `polytypst rules` does not show that facsimile editions skip HYPHENATED_PROPER_NOUN and the hyphen part of CROSS_PAGE_WORD_SPLIT.
- [ ] tbd is configured in `/Users/martinfan/devv/.tbd`, but `devv` is not a git repository, so `tbd` fails here.

## Monograph compiler (found in book 6, affects every book)

- [ ] `_SECTION_RE` in `src/compiler/source_numbers.py:113` needs a non-digit after the section number, so "3 1990年以后的劳动分配率" stays unnumbered. Each book's hook inserts a word joiner (U+2060) to work around it.
- [ ] Equations have no chapter-wise "(C.N)" numbering. Book 6 labels `eq-C-N` are read as section.N, which gives 6 numbering resyncs although the printed numbers are right.
- [ ] `_typst_hoist_heading_fn` in `src/compiler/monograph.py:1762` also matches a body paragraph that starts with `#strong[`, so its note marks move to the paragraph end (book 6 chapter 3).
- [ ] `split_page_footnotes` runs before `page_fixups`, so a body line that starts with "(1)" becomes note 1 and only a transcript edit can save it.
- [ ] When two figures in a row each have a note above the caption, both notes print under the second figure (book 6 p178, 图 5-10 and 5-11).
- [ ] `@@PAGEBREAK@@` becomes `#pagebreak()` in Typst only. LaTeX prints it as text, so a page fixup cannot force a page break.
- [ ] Transcripts copy chart text that the figure crop already shows. `scripts/figure_leaks.py` finds it per book. A build step could drop transcript lines that match OCR lines inside a figure box.
- [ ] `LEAKED_RUNNING_HEADER` counts a chapter heading that contains the book title, such as "序 劳动力市场与收入分配".
