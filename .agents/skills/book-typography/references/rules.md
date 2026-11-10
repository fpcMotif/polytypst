# Measured rules for book pages

One row per rule. Where sources disagree, **Use** names the value this skill applies and the reason. The sources' own values stay in **Sources**. Engine recipes are in [typst.md](typst.md) and [latex.md](latex.md).

Section numbers come from secondary quotations, as in `docs/publisher-bar.md`. Cite a value to a reader only after you open the source.

## Frame

| Rule | Use | Sources |
|---|---|---|
| Measure | 45–75 characters per full line, 66 ideal. CJK: a whole number of characters, 35–40 typical. | Bringhurst 2.1.2. jlreq 2.2.4 |
| Leading | Latin pitch 1.2–1.4 × body size (10/12 to 10/14). CJK pitch 1.5–1.8 × body size. | plain TeX 10/12. AMS 10/12, 11/13, 12/14. jlreq 2.4 line gap 0.5–1 em |
| Text block | Height is a whole number of lines. Width about ⅔ of the trim. Height 1.6–1.7 × width. | AMS 30 × 50.5 pc (1.68). Springer 117 × 191 mm (1.63) |
| Margins | Inside < outside, head < foot. Use 2 : 3 for inside : outside and for head : foot. | Van de Graaf canon 1 : 1 : 2 : 3 (inner, top, outer, bottom) is for fine editions. Technical books run tighter. |
| Baseline grid | Prose baselines sit on one grid, and facing baselines align across the spine. Displays, figures and tables take a whole number of lines. | memoir `memdesign`, after Bringhurst |

## Spreads and page breaks

| Rule | Use | Sources |
|---|---|---|
| Spread depth | Facing pages end on the same line. Run both pages of a spread one line short or long together. | Bringhurst 2.4.9 and CMOS 16.139: equal, ±1 line. Artech/CRC (after Swanson): within 2 lines. This skill uses 1 line. |
| Widows | No page starts with the last line of a paragraph. | Bringhurst 2.4.8 |
| Orphans (club lines) | No page ends with the first line of a paragraph. | Springer instructions. TeX `\clubpenalty` |
| Heading at foot | A heading carries at least two lines of its text onto the same page. | Common house rule. Typst `sticky`, LaTeX `\@afterheading` |
| Chapter end | A chapter's last page may run short. It holds at least five lines. | House rule, so you choose the number |

## Page colour

| Rule | Use | Sources |
|---|---|---|
| Word space | 0.2 em minimum, 0.25–0.33 em typical, 0.5 em maximum. Under 2% of justified spaces fall outside 0.2–0.5 em. | Bringhurst 2.1.1 gives M/5 to M/2, with M/4 ideal. Knuth's CMR 10 pt uses 0.333 em +0.167 −0.111. |
| Line breaking | Use whole-paragraph optimisation (Knuth–Plass): badness 100·r³, LaTeX tolerance 200. | Knuth and Plass 1981 |
| Hyphen streak | At most 2 consecutive hyphenated lines in technical books and 3 in prose. | Swanson, *Mathematics into Type*, via CRC: 2. Bringhurst 2.4.3: 3. |
| Hyphen minimum | Leave 2 letters before the break and carry 3 after it. Break no proper names, headings, chapter titles or the last word of a paragraph. | Bringhurst 2.4.1–2.4.4. CMOS 7.36–7.47 |
| Letter-spacing | Lowercase 0, with at most ±1% elastic tracking for justification. Caps and small caps 5–10%. | Bringhurst 2.1.5–2.1.6 |
| Microtypography | Use protrusion always. Use expansion only up to 2%, and only on pdfTeX or LuaTeX. | Hàn Thế Thành 2001. microtype manual |
| Rivers | No white channel runs down three or more lines. Look at the spread images. | Hochuli, *Detail in Typography* |

## Headings, openings, running heads

| Rule | Use | Sources |
|---|---|---|
| Chapter opening | Starts on a recto. Use one sink for the whole book (4–8 lines). The first paragraph has no indent. There is no running head, and the folio moves to the foot or is dropped. | CMOS 1.16. CRC: number 4 lines down, title 2 lines below. AMS 7.5 pc top space. |
| Heading levels | Each level differs from the next in size, weight or shape. Use at most three visible levels below the chapter. Headings sit on the grid. | AMS `amsbook` |
| Running heads | Verso shows the chapter, recto the section. Set them in small caps, letterspaced 5–10%, at 1–2 pt under body size. The folio goes at the outer edge. Omit them on openings, part titles and blank pages. | CMOS 1.10–1.16. AMS sets 8 pt caps. |
| Running head length | The head clears a four-digit folio. Shorten long titles. | SIAM style manual |
| Blank pages | A blank verso before a recto opening carries no head and no folio. | CMOS 1.16 |

## Mathematics

| Rule | Use | Sources |
|---|---|---|
| Display space | About one line above and below. Use less when the line before a display is short. | plain TeX `\abovedisplayskip` 12pt plus 3 minus 9; short skip 0pt plus 3pt |
| Math spacing | Thin 3 mu, medium 4 mu, thick 5 mu. Do not hand-tune spacing around relations or operators. | TeXbook ch. 18. OpenType MATH applies the same |
| Inline fractions | Use the solidus `(a+b)/(c+d)` in running text and stacked fractions in displays. | Swanson. IEEE style |
| Breaking displays | Break before a relation or operator. Align at the relation, or indent continuation lines 2 em. In inline math, break after the relation. | TeXbook p. 195. Swanson 3.3.5 |
| Equation numbers | Use one form, `(chapter.n)`, set flush right. Move a number to its own line when the formula is too wide. | SIAM, Springer, IEEE right; AMS default left. This skill uses right unless the house style says left. |
| Theorems | Head bold (plain, definition) or italic (remark). Plain body italic; definition and remark bodies upright. CJK bodies stay upright. | `amsthm` |
| Proof end | An open square at the right of the last line, or on its own line after a display. Omit it after a theorem with no proof. | AMS `\qedsymbol`. UTR #25 (U+220E) |
| Upright symbols | Numerals, units, `d` in integrals (house choice), operator names (`sin`, `lim`) and multi-letter names stay upright. | ISO 80000-2. TeXbook |

## Text details

| Rule | Use | Sources |
|---|---|---|
| Figures | Old-style figures in literature and humanities prose. Lining figures in math, CS, economics, tables and all caps. | Bringhurst 3.2.1. AMS, SIAM and IEEE use lining figures. |
| Small caps | Use the font's real small caps, letterspaced 5–10%, for acronyms in prose-heavy books. Never scale capitals down. | Bringhurst 3.2.2 |
| Dashes | Hyphen, en dash for ranges, em dash (or a spaced en dash) for breaks, and a minus sign in math. These are four different glyphs. | TeXbook ch. 2. Tschichold prefers a spaced en dash. |
| Quotes | Curly quotes in the book's language convention. Straight quotes appear only in code. | CMOS ch. 6. TeXbook p. 3 |
| Ligatures | fi, fl, ff, ffi and ffl on in text and off in code. | TeXbook p. 4 |
| Notes | Footnotes at 0.8 × body size with a short rule. Note numbers are superscript in text and full size (or superscript) in the note. | CMOS ch. 14 |
| Tables | Three rules (top, head, bottom), no verticals. Caption above, numbers right-aligned on the decimal point. | Springer instructions. `booktabs` |
| Figure captions | Caption below, at 0.9 × body size, with no full stop after a fragment. | Springer instructions |

## Reprints of older books

| Rule | Use | Sources |
|---|---|---|
| Fidelity model | Choose one model per book. A type facsimile keeps lines and pages. A reset reprint reflows them. | Bowers and Gaskell, bibliography practice |
| Source pagination | In a reset reprint, put the old page number in the outer margin `[142]` at the line where the old page begins. | CMOS 1.4 and 14.159 |
| Editorial lite | Keep valid notation and numbering as printed. Correct only real errors, and list each correction. | AMS Chelsea reprints: "if it isn't wrong, let it stand" |
| Scan wins | In polytypst rebuilds, the scan's own design wins over this table. This table sets the floor for a defect. | `docs/publisher-bar.md` Rule 0 |
