# Typst mechanics (0.15)

Every behaviour below was measured on Typst 0.15.1 with `proof.py`. [`../templates/book.typ`](../templates/book.typ) applies all of them.

## The grid

- **Line box.** `set text(top-edge: 0.88em, bottom-edge: -0.12em)` makes each line box exactly 1 em tall. The pitch is then `leading + 1em`, so set `leading = pitch - size`.
- **Paragraphs.** Set `par(spacing:)` equal to `leading`. Paragraphs then sit on the grid, and an indent marks each new one.
- **Block spacing.** Typst keeps the *larger* of two touching spacings (`below` of one block, `above` of the next). It does not add them. A gap of `line-gap + k × pitch` keeps the next baseline on the grid.
- **Snapping.** A display, figure or listing has an arbitrary height. `snap` measures it, pads it to `n × pitch − line-gap` and centres it, so the text after it returns to the grid. A snapped block cannot break across pages.
- **No vertical justification.** Typst has no `\flushbottom`, so it cannot stretch glue to fill a page. Pages keep the grid and may end one line short instead. If a spread differs by a line, move a figure, shorten a paragraph or adjust `costs`.

## Paragraphs and colour

- Use `par(justify: true, linebreaks: "optimized")` for Knuth–Plass breaking.
- `par(justification-limits: (spacing: (min:, max:), tracking: (min:, max:)))` accepts **ratios of the font's own space** only. A length such as `0% + 0.2em` fails with "ratio must be positive". Measure the space inside `context` (`measure[a b].width - measure[ab].width`) and divide. Spaces differ by font: STIX Two Text 0.235 em, Libertinus 0.25 em, Charter 0.278 em, New Computer Modern 0.333 em.
- Tracking also narrows the space glyph. With `tracking.min = -0.01em`, set the spacing minimum to 0.21 em, or spaces fall to about 0.18 em. Without negative tracking, loose lines appear instead (up to 5% of spaces over 0.5 em).
- The limits are soft. Typst exceeds them when a paragraph has no other solution, so `proof.py` still reports such lines.
- `text(costs: (hyphenation:, runt:, widow:, orphan:))` weights the breaks. Raise `widow` and `orphan` above 100% to forbid them harder. Raise `hyphenation` to reduce hyphen streaks. Typst has no hard limit on consecutive hyphens.
- A footnote moves with its call. A long note near a page foot can force a widow onto the next page. Shorten the note or move the call.

## Pages

- With `page(binding: left, margin: (inside:, outside:, top:, bottom:))`, odd pages are rectos.
- `pagebreak(to: "odd", weak: true)` puts a chapter on a recto. The blank verso before it gets the header that the header function computes, so the header must return nothing on it.
- Running heads use `context` with `query(heading.where(level: 1).before(here()))`. A section head on a recto uses the first level-2 heading on the page, or else the last one before it.
- Opening pages: compare `here().page()` with the pages of the level-1 headings. Drop the header there and put the folio in the footer.

## Gotchas

- `state.update(x)` calls `x` when `x` is a function. A symbol such as `sym.square.stroked` counts as one. Wrap it: `update([#x])`.
- `let measure = …` hides the built-in `measure`. Use another name.
- To call a function stored in a dictionary, wrap the access in parentheses: `(dict.at(k).f)(x)`.
- `document(author:)` takes a string or an array of strings, not content.
- When headings print no numbers, `counter(heading)` still reads 0. Keep a separate `counter("chapter")` for `(1.1)` equation and theorem numbers.
- Fonts come from the system through `typst fonts`. Libertinus Math is not installed on this machine. STIX Two Math and New Computer Modern Math are.
- `smallcaps(all: true)` sets capitals as small caps too. Add `tracking: 0.05em`–`0.1em` for running heads.
- To place a margin note from inside a paragraph, use `box(width: 0pt, place(dx: target - here().position().x, …))`. A bare `place(right)` lands under the line instead.
