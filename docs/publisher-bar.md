# Publisher bar for rebuilt math books

This checklist holds a rebuilt PDF to the standard of AMS and Springer math books. It extends the look table in step 5 of `docs/prompts/math-book-check.md`. If the two ever differ, the look table wins until you fix this file.

## Rule 0: the scan wins

If the book's own scan and this bar conflict, follow the scan. Keep the original design and fix the defects. The bar sets the floor for a defect. It does not ask you to restyle a book.

## How to use it

1. Run `uv run python scripts/look_sheet.py BOOK output/look`.
2. Read each sheet against the rows below. Give each row PASS or FAIL, with the page.
3. Mark a row N/A when the scan has no such element.
4. Where a value says "unconfirmed", use the row's PASS rule only. Do not cite the value.

## Checklist

| Item | PASS when | Reference values | Source |
|---|---|---|---|
| Page and text block proportions | The text block is a tall rectangle. It is about 1.6 to 1.7 times as high as it is wide. The text block is centred on the page or offset as the scan offsets it. | AMS: 30 pc by 50.5 pc (360 by 606 pt), ratio 1.68. Springer: 117 mm by 191 mm on a 155 by 235 mm trim, ratio 1.63. | A1, S1 |
| Margins | Outer margin is wider than inner margin or equal to it. Foot margin is wider than head margin. No text, figure or table crosses the page edge. A wide figure or table may pass the text block by 5 mm at most. | Springer: 38 mm total side margin and 44 mm total head plus foot margin on the trim above. AMS: the class centres the block on the paper (`\calclayout`). AMS trim: unconfirmed. | S1, S2, A1 |
| Body size and leading, Latin | The `type` field has no `!`. The line pitch is 1.15 to 1.5 times the body size. Every page of the same kind uses one size and one pitch. | AMS: 10/12, 11/13 or 12/14 pt. Springer: body 10 pt by default, leading unconfirmed. Line length 45 to 75 characters, ideal 66. | A1, S2, B1 |
| Body size and leading, CJK | Body text sets on a square grid. The line pitch is 1.4 to 1.8 times the body size. A paragraph starts with an indent of the width the scan uses. | jlreq: line gap is 0.5 to 1 em, so the pitch is 1.5 to 2.0 em. clreq: first-line indent is 2 em. jlreq: first-line indent is 1 em. clreq gives no body-text ratio. | J1, C1, C2 |
| CJK line breaks | No closing mark or pause mark starts a line. No opening mark ends a line. | clreq 6.1.1 "basic" level: opening quotation marks, brackets and angle brackets never end a line. Closing marks and most pause or stop marks never start a line. | C3 |
| Widows and orphans | No page starts with the last line of a paragraph. No page ends with the first line of a paragraph. | At least two lines of a paragraph at the foot or head of a page. | S3, B1 |
| Hyphenation limits | No more than three consecutive lines end in a hyphen. No heading breaks at a hyphen. No chapter title breaks at a hyphen. | Three consecutive hyphens at most (Bringhurst, from secondary quotations). CMOS limit: unconfirmed. AMS and Springer headings rule: unconfirmed. The heading rule follows the look table. | B1, M1 |
| Running heads and folios | The running head and the folio sit at the same place on every page of a kind. A chapter-opening page has a folio and no running head. Even pages carry the chapter title. Odd pages carry the section title. | AMS: folio at the outer edge of the running head line, `\headheight` 8 pt, `\headsep` 14 pt. A plain page has a centred folio in `\scriptsize`. Springer: `\headsep` 12 pt. | A1, S1 |
| Chapter openings | Every chapter title starts at the same height. The title is bold and centred in the AMS style, or as the scan sets it. The number sits above the title. No running head prints on the page. | AMS: top space 7.5 pc, title 14.4/18 pt bold centred, number line in the normal size, 3 pc below the number. | A1, S2 |
| Heading hierarchy | Chapter, section, subsection and sub-subsection differ in size, weight or shape, and one level never looks like the next. Each level keeps one style on all pages. | AMS: section is bold and centred. Subsection is bold with a paragraph indent. Sub-subsection is italic. Paragraph indent 18 pt. | A1 |
| Theorem head | Head and number sit on the line of the body text, followed by a period or a space of the scan's width. The style is the same for every theorem of one kind. | AMS: head gap 5 pt plus 1 pt minus 1 pt. Plain and definition heads are bold. The remark head is italic. | A2 |
| Theorem body | Theorems, lemmas and propositions set in the body style of the scan. Definitions and remarks set upright. | AMS: plain body is italic. Definition and remark bodies are upright. Springer class defaults: unconfirmed. | A2, S4 |
| Proof and QED mark | A proof starts with an italic or small-capital "Proof". The QED mark is an empty square. It sits at the right edge of the last line, or on a line of its own if the last line is a display. | AMS: `\qedsymbol` is a square box 0.78 em wide, set flush right with a 1 em gap. Springer: `\qed` is an empty square, `\smartqed` sets it flush right. | A2, S4 |
| Display math spacing | A display has the same space above and below. The space is one line or less. A display never touches the line above or below. A display is centred or set at the book's indent. | AMS: the space comes from `\medskipamount`, value unconfirmed. Springer: value unconfirmed. | A1, S5 |
| Equation numbers | Numbers sit at the right margin. They use one form in the whole book. A number never overlaps the formula. A long formula moves the number to its own line. | AMS and Springer: right flush. Springer: sub-numbering such as (1.2a) is allowed. Number format: unconfirmed. | S5 |
| Table rules | A table has a top rule, a header rule and a bottom rule. It has no vertical rules and no other horizontal rules. A table has a caption. Rules are thin. | Springer: no vertical lines and no extra header lines. A table may pass the page width by 5 mm at most. Rule weights: unconfirmed. | S6 |
| Figure quality | A figure is a vector drawing or a clean raster. Lines are at least 0.5 pt at print size. Text in a figure is a sans serif face at 8 to 10 pt. Shading steps differ by 15 percent at least. | Springer: line weight 0.5 pt, lettering 8 to 10 pt, screens 15 to 60 percent, scanned line art 1200 dpi, photos 300 dpi. A figure may pass the text block by 5 mm at most. | S6 |
| Figure captions | The caption sits below a figure and above a table. It has no end punctuation. Parts a, b, c are in bold. A figure under 78 mm wide may take a side caption. | Springer: caption below the figure, flush left. Caption text follows normal rules for hyphenation and capitals. | S6 |
| Index layout | The index has two columns. Each entry starts on its own line. A subentry is indented under its entry. Page numbers follow the entry. The heading is set like a chapter title. | AMS: two columns, column gap 35 pt, `\footnotesize`, ragged right, heading 14.4/18 pt bold centred. Springer: layout comes from `svind.ist`, values unconfirmed. | A3, S7 |
| Notation layout | The list of symbols has one symbol per line. The symbol sits in the left column and its meaning in the right column. The list is in the front matter or at the back, as the scan places it. | Springer provides a list-of-symbols environment. Column widths: unconfirmed. | S8 |
| Front matter | The order follows the scan (usually half-title, title, copyright, dedication, preface, contents; the order is unconfirmed). Pages before the main text use roman folios. The main text starts at arabic 1. | Springer: `\frontmatter`, `\mainmatter` and `\backmatter` switch the three parts. AMS front-matter order and folio style: unconfirmed. | S2 |
| Contents | Each entry has a leader and a right-aligned page number. Subentries indent under their parent. Chapter entries have more space above them. | AMS: chapter entries 8 pt plus 1 pt above, section indent 1 pc, page number box 1.6 em. | A3 |

## Sources

- A1: AMS class source, `amsclass.dtx` (amsbook options), CTAN `macros/latex/required/amscls`. https://tug.ctan.org/macros/latex/required/amscls/amsclass.dtx
- A2: Same file, theorem styles and `\qedsymbol` code, plus `amsthm` documentation.
- A3: Same file, `theindex`, `\l@chapter`, `\l@section` and `\@pnumwidth` code.
- S1: Springer SVMono author instructions, "Submitting your Manuscript". https://ftp.ast.cam.ac.uk/pub/rwa/outgoing/book/instruct.pdf
- S2: Springer SVMono reference guide, Sect. 2.1 to 2.4 and 2.11. https://ftp.ast.cam.ac.uk/pub/rwa/outgoing/book/refguide.pdf
- S3: Springer SVMono author instructions, "Page Breaks".
- S4: Springer SVMono reference guide, Sect. 2.6 (`\qed`, `\smartqed`, `\spdefaulttheorem`).
- S5: Springer SVMono author instructions, "Math".
- S6: Springer SVMono author instructions, "Figures, Tables and Their Captions".
- S7: Springer SVMono author instructions, "Index" and reference guide, Sect. 2.10.
- S8: Springer SVMono reference guide, list of symbols.
- B1: Bringhurst, The Elements of Typographic Style, 4th ed., ch. 2 (line length, hyphens). Values taken from secondary quotations, not from the book.
- M1: Chicago Manual of Style, 17th ed., 7.36 to 7.47 (word division). Not read directly.
- C1: W3C, Requirements for Chinese Text Layout, 6.2.1.1 (first-line indents). https://www.w3.org/TR/clreq/
- C2: W3C, Requirements for Japanese Text Layout, 2.4 (line gap) and 3.1.5 (first-line indent). https://www.w3.org/TR/jlreq/
- C3: W3C, Requirements for Chinese Text Layout, 6.1.1 (line start and line end prohibition).
