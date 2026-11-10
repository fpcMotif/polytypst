# Genre profiles

A profile is the set of house-style choices that changes with the kind of book. The numbers match `profiles` in [`../templates/book.typ`](../templates/book.typ). Change both together.

| Profile | Body / pitch | Measure | Figures | Headings | Hyphen streak | Indent |
|---|---|---|---|---|---|---|
| `math` | 10 / 13 pt | 66 | lining | numbered 1.1 | 2 | 1.5 em |
| `cs` | 10 / 13 pt | 68 | lining | numbered 1.1 | 2 | 1.5 em |
| `econ` | 10.5 / 13.5 pt | 66 | lining | numbered 1.1 | 2 | 1.5 em |
| `literature` | 11 / 14.5 pt | 62 | old-style | unnumbered | 3 | 1 em |
| `philosophy` | 10.5 / 14 pt | 64 | old-style | unnumbered | 3 | 1.2 em |
| `zh` | 10.5 / 18 pt | 38 characters | lining | numbered | none | 2 em, every paragraph |
| `ja` | 9.5 / 16.5 pt | 40 characters | lining | numbered | none | 1 em, every paragraph |

## Math

- Read the Mathematics rows of [rules.md](rules.md) in full.
- Theorem, lemma, proposition and corollary share one counter per chapter. Definitions and remarks join it unless the house style says otherwise.
- Equation numbers take the form `(chapter.n)`. Number only the equations that the text cites.
- Keep the notation index, the bibliography and the index in the back matter. The index is set in two columns.

## Computer science

- Code is set in a monospace face at about 0.82 × body size, black, with no syntax colour in print. Use a ligature-free face, or turn ligatures off.
- Indent listings by the paragraph indent. Break a long listing across pages only at a blank line.
- Algorithms (pseudocode) use a numbered float with a caption above, keywords in bold, and line numbers at 0.8 × body size.
- Set a URL or identifier in running text in mono, with breaks allowed after `/`, `.` and `_`.

## Economics and social science

- Tables carry the argument. Use three rules, decimal-aligned numbers and a note line under the table at 0.8 × body size for the source and significance stars.
- Charts are vector images at 8–9 pt lettering in the body face or a matching sans. Lines are at least 0.5 pt, with no background tint.
- The reference list is author–date, with a hanging indent of 1.5 em.
- Displays follow the math rules. Number them only when the text cites them.

## Literature

- Use no section numbers. Mark scene breaks with a blank line, or with a centred ornament when the break falls at a page edge.
- Dialogue follows the language's quotation convention. Do not hyphenate the last word of a paragraph.
- Chapter openings may use a drop cap or small caps for the first words. Use one treatment for the whole book.
- Old-style figures appear in prose and in folios.

## Philosophy and humanities

- Notes run long, so place them as footnotes at 0.8 × body size. Keep a note's call and its first line on the same page.
- Indent block quotations on both sides and keep them at body size, so the lines stay on the grid.
- Greek, German and other scripts need a font that covers them. Set `lang` on each passage so hyphenation follows that language.
- Use small caps for acronyms and for author names in a running bibliography.

## Chinese and Japanese

Read [cjk.md](cjk.md). It covers the character grid, punctuation widths, line-break prohibitions and mixed Latin and math text.
