# Double-check a math or CS textbook

Use this guide to write the prompt for a double-check of a rebuilt textbook, or to run the double-check yourself. The bar is a rebuilt book that reads better than its scan and keeps the author's meaning. `docs/page-check-review.md` gives the commands for each stage. This guide gives the bar, the checklist, and the rules for the prompt.

Two words have one meaning in this guide. The **witness** is the scan, read at a 300 dpi zoom. A **claim** is any other input: a verdict, a review finding, an audit count, or an earlier report. Confirm each claim against the witness before you act on it.

## Write the prompt

1. Measure first. Give the agent counts with `file:line`, such as "671 `parallel f parallel_p`, 0 `norm()`". A guess in a prompt comes back as a confirmed finding.
2. Make the scan the witness and each input a claim. In Lieb–Loss, 88 of 96 "tag already present" verdicts were wrong. In the first Book 4 run, 40 of 177 page-check issues were false.
3. End each step on a check that the agent can run. "Every display on its pages has a decision" forces full coverage. "Check the tags" does not.
4. State the target behavior. Write "set operators upright", not "do not italicize operators". Keep a ban only for a hard guardrail. The guardrails: never `--update` a baseline, never loosen a check, never start `omp`.
5. Use one word for one meaning. Define *scan*, *transcript*, *rebuilt PDF*, *claim*, *verdict*, *proposal* and *lane* once, and do not use synonyms.
6. Write one action per sentence. Put the condition first: "When X, do Y." Use numbered steps for order and bullets for flat checklists.
7. Delete each line that does not change behavior, such as "be careful" or "be thorough".
8. Run `--help` for each command before you put it in the prompt. Earlier prompts named flags, files and models that the repository did not have.
9. Give each lane its own files. Read-only lanes write proposals in one agreed format. One owner applies the proposals to shared files such as `book.toml`. Agree on the format before the lanes start.
10. Use a reviewer model that is different from the writer model. Use a fast vision model for wide samples, and a strong model for code and for decisions about math.
11. Ask for proof: command tails, counts before and after, `file:line` for each fix, and the pages that fall short. Keep exit codes. A check piped into `tail` hides its failure.

## The bar

A rebuilt book can correct what the original press could not. It must not change the author's mathematics.

- Correct each scan typo, and put `# Scan typo: the scan prints X; meant Y.` above the fix. A typo that changes meaning, such as a sign or an index, needs proof from context or from the publisher's errata.
- Read the publisher's errata list when one exists. Use it as a second witness.
- Make notation consistent. When the scan uses two forms for one object, use the form that the scan uses most.
- Redraw figures as vectors, with labels in the book's fonts.
- Use one style for each element: headings, theorem heads, proofs, lists, captions and the index.
- Add what print cannot give: links, PDF bookmarks, searchable text and code that copies correctly.

## Checklist

### Process

- Sample the verifier's verdicts against zooms. A full class of `false_positive` verdicts can hide real defects.
- Test each audit rule on a known-bad example before you trust a count of 0. The heading rule skipped level-1 headings, and the reference rule skipped "Theorem N.M".
- Do not use an OCR vote for math. The local OCR blanks formulas. The OCR and the transcript can also share one error.
- Show the rebuilt page and the page after it, because the page map can drift.
- Audit all books before and after each change in `src/compiler/`, because shared code reaches each book.
- Check each output: Typst, LaTeX, and EPUB when the book has one.
- Run commands under `mise exec --`. It sets `POLYTYPST_BOOKS`, and the audit needs it.
- Read the logs for 429 errors. A job can exit 0 when the model quota is out.
- Run a timing test again alone before you blame a change for its failure.
- Compare the page counts first. A partial OCR run exits 1 and lists the pages that are still pending.
- Sample each part of the book: front matter, chapter openers, pages dense with math, proofs, exercises, figures, bibliography, index and the last pages.
- Compare in both directions. Content that the scan does not have is a defect, such as a symbol that a model "corrected".

### Content

- Missing or extra text, merged or split paragraphs, and words lost at a line or page break.
- Symbol confusions: l, 1 and I; O and 0; ε and ∈; ν and v; ∂ and δ; ρ and p; ω and w; κ and k; φ and ϕ; ↦ and →; | and ‖; ′ and ’.
- Subscripts, superscripts, primes, hats, bars, tildes, signs, limits of integrals and sums, fraction groups and matrix entries.
- Font classes: blackboard (ℝ), calligraphic (𝒜), script, fraktur (𝔤), bold vectors, and upright constants (e, i, and the d in dx).
- Footnotes and their marks, marginal notes, and notes under figures and tables.
- Text in figures: axis labels, node names and legends.

### Numbering and references

- Chapter, section, theorem, lemma, corollary, definition, example, exercise, figure, table and equation numbers come from counters. `src/compiler/source_numbers.py` makes them, and `src/literal_numbers.py` checks them.
- The numbering scheme is the scheme of the scan: per chapter or per section, shared theorem and equation counters, and lettered appendices (A.1).
- Each "Theorem 2.16", "(3)", "Exercise 4", "Figure 1.2", "Section 3.1" and "see p. 45" links to its target.
- Page references, the index and the table of contents use rebuilt page numbers, not scan page numbers.
- Citations link to the bibliography, in one style.
- The table of contents, the list of figures and the PDF bookmarks agree with the headings.

### Math

- Norms and absolute values use `norm()` and `abs()`, with attached scripts, no inner spaces, and delimiters sized to their content.
- Operators (sup, inf, lim, log, ln, det, tr, supp, dim), words in math, and labels such as loc and max are upright.
- Spacing around relations and binary operators is correct. A thin space comes before dx. An ellipsis is one character (…).
- Display equations align at their relation signs. Tags sit at the right, level with their lines. A long equation breaks at a relation, never in a fraction. The display keeps its end punctuation.
- Inline math has no tall fractions and no line break in a short formula.
- Cases, matrices, arrays and commutative diagrams match the scan.
- An accent is as wide as its argument.
- Theorem environments use one head style, the body style of the scan, one "Proof." label, and an end mark at the right margin.

### CS

- Code is exact: monospace font, the indentation of the scan, straight quotes, no ligatures, no hyphens added, and no smart dashes. Code copied from the PDF must run.
- A long code line wraps with a visible mark or uses a smaller font. It never goes past the margin.
- An identifier with an underscore, such as `max_len`, is code, not a subscript. Keywords and names longer than one letter are upright.
- Pseudocode keeps bold keywords, the indentation and line numbers of the scan, arrows such as ← and :=, and the comment style.
- Complexity notation uses an upright log, as in O(n log n).
- Grammars, BNF, regular expressions, command lines, prompts, file paths, URLs, hexadecimal and binary numbers, and bit diagrams are exact.
- Trees, graphs, automata, memory layouts and ASCII art are redrawn, or stay monospace and aligned.
- Truth tables and opcode tables are aligned, with rules, and their cells do not wrap.

### Typography

- No widow, no orphan, and no heading alone at the foot of a page. A figure or table sits near its first reference.
- No hyphen breaks in math, code, headings or proper names. No space before a hyphen, as in "μ-measure" and "C^∞-functions".
- An en dash marks a range (1–5). One style of dash marks a break in a sentence.
- A non-breaking space joins "Theorem 2.1", "p. 5", "Fig. 3", and a number to its unit.
- Prose uses curly quotes. Code uses straight quotes.
- No overfull line, and no raw markup (`#`, `$`, `\`, `**`, `##`, `<br>`).
- No missing glyph, no tofu box and no private-use character.
- Running heads, page numbers, chapter openers and part pages are consistent.
- Index entries nest, keep the order of the scan, and use rebuilt page numbers. The bibliography uses one style and has no bullets.

### PDF

- The text layer is searchable, and copied math gives sensible text.
- Fonts are embedded. The PDF metadata has the title, author and language.
- The PDF reads in grayscale. Line styles, not only colors, show different series.
- Figures have alt text. The PDF is tagged when the toolchain can tag it.

## Prompt skeleton

Fill in one line for each field. Give measured facts, not guesses.

```text
GOAL      <one sentence: the outcome and the bar>
BOOK      KEY, SCAN, transcript store, repository path
BAR       better than the scan; same meaning; the scan is the witness; each input is a claim
FACTS     measured counts with file:line, from the baseline
RULES     files that each lane owns; proposal format; checks never loosened; no omp commands; no VCS
WAVE 0    baseline: status, audit --save, audit of all books
WAVE 1    parallel lanes: read-only (tags, content, references) and code (numbering, math, text, CS code)
WAVE 2    integrate: sample 5 zooms for each lane; apply proposals; full test suite
WAVE 3    proof: rebuild, audits against the baseline, both compilers, 40 sampled pairs to a reviewer on a different model, one repeat
REPORT    lanes table; each defect class before and after; command tails; what is left, with pages
```

For a math book, the code lanes are numbering, math and text. For a CS book, add a lane for code and pseudocode. That lane checks that code copies exactly, that pseudocode agrees with the scan, and that identifiers stay out of math.
