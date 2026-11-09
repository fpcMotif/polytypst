// Book frame for Typst 0.15. Import it and wrap the document:
//   #import "book.typ": *
//   #show: book.with(genre: "math", title: [Title], author: [Author])
// Every length below derives from the body size and the line pitch, so the
// baseline grid holds when a profile changes the size. Typst keeps the larger
// of two touching block spacings, so a gap of line-gap + k * pitch and a block
// of n * pitch - line-gap both keep the next baseline on the grid.

#let profiles = (
  // size, pitch, measure (characters), figures, heading numbers, hyphen streak limit
  math:       (size: 10pt,   pitch: 13pt,   chars: 66, figures: "lining",    numbered: true,  streak: 2, indent: 1.5em),
  cs:         (size: 10pt,   pitch: 13pt,   chars: 68, figures: "lining",    numbered: true,  streak: 2, indent: 1.5em),
  econ:       (size: 10.5pt, pitch: 13.5pt, chars: 66, figures: "lining",    numbered: true,  streak: 2, indent: 1.5em),
  literature: (size: 11pt,   pitch: 14.5pt, chars: 62, figures: "old-style", numbered: false, streak: 3, indent: 1em),
  philosophy: (size: 10.5pt, pitch: 14pt,   chars: 64, figures: "old-style", numbered: false, streak: 3, indent: 1.2em),
  zh:         (size: 10.5pt, pitch: 18pt,   chars: 38, figures: "lining",    numbered: true,  streak: 0, indent: 2em),
  ja:         (size: 9.5pt,  pitch: 16.5pt, chars: 40, figures: "lining",    numbered: true,  streak: 0, indent: 1em),
)

#let fonts = (
  latin: ("STIX Two Text", "Libertinus Serif", "New Computer Modern"),
  math: ("STIX Two Math", "New Computer Modern Math"),
  mono: ("DejaVu Sans Mono", "Fira Code"),
  // The Latin face covers Latin letters only, so CJK quotes and punctuation stay full width.
  zh: ((name: "STIX Two Text", covers: "latin-in-cjk"), "Songti SC"),
  ja: ((name: "STIX Two Text", covers: "latin-in-cjk"), "Hiragino Mincho ProN", "BIZ UDMincho"),
)

#let words = (
  // CJK faces have no italic, so a CJK theorem body stays upright.
  en: (chapter: n => [Chapter #n], proof: [Proof.], italic: true),
  zh: (chapter: n => [第#n;章], proof: [证明], italic: false),
  ja: (chapter: n => [第#n;章], proof: [証明], italic: false),
)
#let book-words = state("book-words", words.en)

#let frame = state("book-frame", none)
// Counts chapters whether or not headings print numbers; equations and theorems read it.
#let chapter = counter("chapter")

// Pads a block that cannot break (a display, figure or short listing) to whole
// grid lines and centres it, leaving at least half a body size above and below.
#let snap(body) = context {
  let f = frame.get()
  if f == none { return body }
  layout(size => {
    let h = measure(body, width: size.width).height
    let n = calc.ceil((h + f.line-gap + f.size) / f.pitch)
    block(height: n * f.pitch - f.line-gap, width: 100%, above: f.line-gap, below: f.line-gap, breakable: false, align(horizon, body))
  })
}

// The running heads read these. A chapter opening carries no running head.
#let opening-pages() = query(heading.where(level: 1)).map(h => h.location().page())

#let running-head(p) = context {
  let pg = here().page()
  if pg in opening-pages() { return }
  let chapters = query(heading.where(level: 1).before(here()))
  if chapters == () { return }
  let on-page = query(heading.where(level: 2)).filter(h => h.location().page() == pg)
  let before = query(heading.where(level: 2).before(here()))
  let section = if on-page != () { on-page.first() } else if before != () { before.last() } else { chapters.last() }
  let folio = counter(page).display()
  set text(size: p.size * 0.85, number-type: "lining")
  let label(h) = smallcaps(all: true, text(tracking: 0.06em, h.body))
  if calc.even(pg) { folio; h(1fr); label(chapters.last()); h(1fr) }
  else { h(1fr); label(section); h(1fr); folio }
}

#let opening-folio(p) = context {
  if here().page() in opening-pages() {
    set text(size: p.size * 0.85, number-type: "lining")
    align(center, counter(page).display())
  }
}

#let book(
  genre: "math",
  title: none,
  author: none,     // a string: PDF metadata takes no markup
  trim: (155mm, 235mm),
  binding: left,
  sink: 6,          // chapter sink in lines of the grid
  qed: sym.square.stroked,
  body,
) = {
  let p = profiles.at(genre)
  let cjk = genre in ("zh", "ja")
  let lang = if cjk { genre } else { "en" }
  let family = if cjk { fonts.at(genre) } else { fonts.latin }

  // Text block: the measure sets the width, a whole number of grid lines the height.
  let text-width = if cjk { p.chars * p.size } else { p.chars * p.size * 0.47 }
  let side = trim.at(0) - text-width
  let lines = calc.floor((trim.at(1) * 0.74) / p.pitch)
  let depth = lines * p.pitch
  let head-foot = trim.at(1) - depth

  set document(title: title, author: if author == none { () } else { (author,) })
  set page(
    width: trim.at(0),
    height: trim.at(1),
    binding: binding,
    margin: (inside: side * 0.4, outside: side * 0.6, top: head-foot * 0.4, bottom: head-foot * 0.6),
    header: running-head(p),
    header-ascent: p.pitch,
    footer: opening-folio(p),
    footer-descent: p.pitch,
  )

  // A line box of exactly 1em makes the line pitch equal to leading + 1em.
  set text(
    font: family,
    size: p.size,
    lang: lang,
    number-type: p.figures,
    top-edge: 0.88em,
    bottom-edge: -0.12em,
    hyphenate: not cjk,
    cjk-latin-spacing: auto,
    costs: (hyphenation: 100%, runt: 100%, widow: 100%, orphan: 100%),
  )
  set par(
    justify: true,
    linebreaks: "optimized",
    leading: p.pitch - p.size,
    spacing: p.pitch - p.size,
    // Latin books skip the indent after a heading; clreq and jlreq indent every paragraph.
    first-line-indent: (amount: p.indent, all: cjk),
  )
  // Word spaces between Bringhurst's 0.2 em floor and a 0.4 em soft ceiling,
  // whatever space the font draws. The limits take ratios of that space only.
  // Tracking also narrows the space glyph, so the floor carries the tracking.
  show: rest => context {
    let space = measure[a b].width - measure[ab].width
    let track = 0.01em
    set par(justification-limits: if cjk {
      (spacing: (min: 100%, max: 100%), tracking: (min: 0em, max: 0.05em))
    } else {
      (spacing: (min: (0.2em + track).to-absolute() / space * 100%, max: 0.4em.to-absolute() / space * 100%),
       tracking: (min: -track, max: track))
    })
    rest
  }

  // Vertical space is line-gap plus a whole number of grid lines.
  let line-gap = p.pitch - p.size
  let skip(n) = line-gap + n * p.pitch
  frame.update((width: trim.at(0), outside: side * 0.6, size: p.size, pitch: p.pitch, line-gap: line-gap))

  set heading(numbering: if p.numbered { "1.1" } else { none })
  show heading.where(level: 1): it => {
    pagebreak(to: "odd", weak: true)
    counter(math.equation).update(0)
    counter(figure.where(kind: image)).update(0)
    counter(figure.where(kind: table)).update(0)
    counter("theorem").update(0)
    chapter.step()
    block(height: sink * p.pitch - line-gap, width: 100%, above: 0pt, below: line-gap, {
      set par(first-line-indent: 0em, justify: false)
      if it.numbering != none {
        let label = (words.at(lang).chapter)(counter(heading).display("1"))
        if cjk { text(size: p.size * 1.2, label) }
        else { text(size: p.size * 1.2, number-type: "lining", tracking: 0.08em, smallcaps(all: true, label)) }
        linebreak()
      }
      text(size: p.size * 1.7, weight: "regular", it.body)
    })
  }
  show heading.where(level: 2): it => {
    block(above: skip(1), below: line-gap, sticky: true, {
      set par(first-line-indent: 0em, justify: false)
      set text(size: p.size, weight: "bold", hyphenate: false)
      if it.numbering != none { counter(heading).display(); h(0.6em) }
      it.body
    })
  }
  show heading.where(level: 3): it => {
    block(above: skip(1), below: line-gap, sticky: true, {
      set par(first-line-indent: 0em, justify: false)
      set text(style: "italic", hyphenate: false)
      it.body
    })
  }

  // Math: numbers flush right as (chapter.n); a display snaps to whole grid lines.
  show math.equation: set text(font: fonts.math)
  set math.equation(numbering: n => context {
    let ch = chapter.get().first()
    numbering("(1.1)", ch, n)
  })
  show math.equation.where(block: true): snap

  // Code: smaller mono, black in print, indented and snapped. Long listings that
  // must break across pages need their own unsnapped show rule.
  show raw: set text(font: fonts.mono, size: 0.82em)
  set raw(theme: none)
  show raw.where(block: true): it => snap(pad(left: p.indent, it))

  // Tables: caption above, three rules, no verticals. Figures: caption below.
  show figure.where(kind: table): set figure.caption(position: top)
  set table(stroke: none, inset: (x: 0.5em, y: 0.2em))
  show figure.caption: set text(size: p.size * 0.9)
  show figure: snap

  set footnote.entry(separator: line(length: 4em, stroke: 0.4pt), gap: 0.3em, clearance: p.pitch)
  show footnote.entry: set text(size: p.size * 0.8)

  set list(indent: 0em, body-indent: 0.6em)
  set enum(indent: 0em, body-indent: 0.6em)
  // Block quotes stay at body size so their lines keep the grid.
  show quote.where(block: true): set block(inset: (left: p.indent * 2, right: p.indent), above: skip(1), below: skip(1))

  state("book-qed").update([#qed])
  book-words.update(words.at(lang))
  state("book-skip").update(skip(1))
  body
}

// Three-rule table: top and bottom rules heavier than the header rule.
#let rules-table(columns: auto, align: auto, header, ..rows) = table(
  columns: columns,
  align: align,
  table.hline(stroke: 0.8pt),
  table.header(..header),
  table.hline(stroke: 0.4pt),
  ..rows,
  table.hline(stroke: 0.8pt),
)

// Theorems. `plain` sets an italic body; `definition` and `remark` stay upright.
#let theorem-counter = counter("theorem")
#let theorem(kind, style: "plain", name: none, body) = context block(above: state("book-skip").get(), below: state("book-skip").get(), {
  theorem-counter.step()
  let head = context [#kind #chapter.get().first().#theorem-counter.get().first()]
  let head = if style == "remark" { emph(head) } else { strong(head) }
  let note = if name == none { [] } else { [ (#name)] }
  set par(first-line-indent: 0em)
  if style == "plain" and book-words.get().italic { [#head#note. #emph(body)] } else { [#head#note. #body] }
})

// Proof: italic head, the end mark flush right on the last line.
#let proof(body) = context block(above: state("book-skip").get(), below: state("book-skip").get(), {
  set par(first-line-indent: 0em)
  context [#emph(book-words.get().proof) #body#h(1fr)#state("book-qed").get()]
})

// Reprint marker: the source page number in the outer margin, as CMOS 1.4 describes.
// It assumes binding on the left, so odd pages are rectos.
#let origpage(n) = context {
  let f = frame.get()
  let label = text(size: 0.75em, number-type: "lining")[[#n]]
  let x = here().position().x
  let target = if calc.odd(here().page()) { f.width - f.outside + 0.8em } else { f.outside - 0.8em - measure(label).width }
  box(width: 0pt, place(dx: target - x, dy: -0.75em, label))
}
