#let book-title = "伦敦分行资金与交易业务阅读册"

// Open-source Source/Noto families first; macOS system fonts are the fallback.
#let latin-serif = ("Source Serif 4", "Charter")
#let cjk-serif = ("Noto Serif SC", "Songti SC")
// In Chinese text the CJK font sets quotes full-width; English blocks use en-serif.
#let latin-in-cjk(names) = names.map(n => (name: n, covers: "latin-in-cjk"))
#let serif = latin-in-cjk(latin-serif) + cjk-serif
#let en-serif = latin-serif + cjk-serif
#let sans = latin-in-cjk(("Source Sans 3", "Helvetica Neue")) + ("Source Han Sans", "PingFang SC")
#let symbols = en-serif + ("Apple Symbols",)
#let ink = rgb("#1b1b1b")
#let muted = luma(110)
#let rule-c = luma(200)
#let accent = rgb("#8c2f39")
#let wash = rgb("#f6f3ee")

#let page-w = 468pt
#let page-h = 702pt
#let page-margin = (inside: 50pt, outside: 42pt, top: 50pt, bottom: 44pt)
#let body-w = page-w - page-margin.inside - page-margin.outside
#let body-h = page-h - page-margin.top - page-margin.bottom

#set page(
  width: page-w,
  height: page-h,
  margin: page-margin,
  header: context {
    let p = here().page()
    let opens = query(heading.where(level: 1)).any(h => h.location().page() == p)
    if p > 3 and not opens {
      set text(7.4pt, font: sans, fill: muted, tracking: 0.02em)
      let chaps = query(heading.where(level: 1).before(here()))
      let cur = if chaps != () { chaps.last().body } else { book-title }
      let num = counter(page).display()
      if calc.even(p) {
        grid(columns: (auto, 1fr), text(weight: "bold", fill: ink, num), align(right, book-title))
      } else {
        grid(columns: (1fr, auto), cur, text(weight: "bold", fill: ink, num))
      }
      v(-4pt)
      line(length: 100%, stroke: 0.4pt + rule-c)
    }
  },
  footer: context {
    let p = here().page()
    if p > 3 and query(heading.where(level: 1)).any(h => h.location().page() == p) {
      align(center, text(7.4pt, font: sans, fill: muted, counter(page).display()))
    }
  },
)

// Fixed line edges keep the pitch even when Latin and CJK glyphs share a line.
#set text(font: serif, size: 9.6pt, lang: "zh", region: "cn", fill: ink, hyphenate: false, top-edge: 0.88em, bottom-edge: -0.12em)
#set par(leading: 0.7em, spacing: 0.62em, justify: true, first-line-indent: 2em, linebreaks: "optimized")
#show link: set text(fill: accent)
#show strong: set text(weight: "bold")

#set enum(
  numbering: n => text(font: sans, size: 0.8em, weight: "bold", fill: accent, str(n)),
  indent: 0pt,
  body-indent: 0.6em,
  spacing: 0.5em,
)
#set list(marker: text(fill: accent, "•"), indent: 0.1em, body-indent: 0.5em, spacing: 0.45em)

#set table(stroke: (x, y) => (top: if y == 0 { 0.8pt + ink } else { 0.4pt + rule-c }, bottom: 0.4pt + rule-c))

#show heading: set par(justify: false, first-line-indent: 0pt, leading: 0.55em)
#show heading: set text(font: sans, fill: ink, hyphenate: false)

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(18pt)
  block(below: 16pt, {
    text(17pt, weight: "bold", it.body)
    v(6pt, weak: false)
    line(length: 32pt, stroke: 2pt + accent)
  })
}

#show heading.where(level: 2): it => block(above: 16pt, below: 8pt, sticky: true, {
  text(12.6pt, weight: "bold", it.body)
})

#let en-start-or-heading = heading.where(level: 3).or(<en-start>)

#show heading.where(level: 3): it => context {
  let next = query(en-start-or-heading.after(here(), inclusive: false))
  if next != () and next.first().func() == metadata and next.first().value.long {
    pagebreak(weak: true)
  }
  block(above: 11pt, below: 4.5pt, sticky: true, {
    text(8.2pt, weight: "bold", fill: accent, tracking: 0.06em, it.body)
  })
}

#let entry-num(n) = box(text(font: sans, weight: "bold", fill: accent, n)) + h(0.45em)
#let entry-sub(s) = text(weight: "regular", fill: muted, s)

#let meta-label(s) = text(6.9pt, font: sans, weight: "bold", fill: muted, tracking: 0.05em, s)

#let reddit-orange = rgb("#ff4500")
#let reddit-logo(fill, size) = image(
  bytes("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><path fill=\"" + fill.to-hex() + "\" d=\"" + reddit-path + "\"/></svg>"),
  format: "svg",
  height: size,
)

// One article's provenance. The English title links to the original page.
#let meta-card(en-title, url, author, date-line, priority, bg-line, access-line) = block(
  width: 100%,
  fill: wash,
  inset: (x: 10pt, top: 8pt, bottom: 8pt),
  radius: 2pt,
  above: 2pt,
  below: 12pt,
)[
  #set par(first-line-indent: 0pt, justify: false, leading: 0.55em, spacing: 0.3em)
  #grid(
    columns: (1fr, auto),
    column-gutter: 8pt,
    link(url, text(10.4pt, style: "italic", font: symbols, fill: ink)[#if url.contains("reddit.com") [#box(baseline: 1.8pt, reddit-logo(reddit-orange, 10pt)) ]#en-title #text(7.5pt, fill: accent, style: "normal", sym.arrow.tr)]),
    if priority != none {
      box(inset: (x: 4pt, y: 2.5pt), radius: 1.5pt, fill: accent, text(6.8pt, font: sans, weight: "bold", fill: white, priority))
    },
  )
  #v(5pt)
  #set text(8.1pt)
  #grid(
    columns: (auto, 1fr),
    column-gutter: 9pt,
    row-gutter: 5pt,
    meta-label[作者], author,
    meta-label[日期], date-line,
    meta-label[出处], bg-line,
    meta-label[获取], access-line,
  )
]

#let en-head(s) = block(above: 9pt, below: 4pt, sticky: true, {
  set par(justify: false)
  text(9pt, weight: "bold", hyphenate: false, s)
})
#let en-caps(s) = block(above: 9pt, below: 4pt, sticky: true, text(7.4pt, font: sans, weight: "bold", tracking: 0.08em, fill: accent, s))
#let en-label(s) = block(above: 6pt, below: 2pt, sticky: true, s)
#let en-toc(entry, page) = block(above: 1.5pt, below: 1.5pt, {
  set par(justify: false)
  entry
  box(width: 1fr, inset: (x: 3pt), repeat(gap: 2.2pt, text(fill: rule-c, ".")))
  text(number-type: "lining", page)
})
#let en-quote(s) =block(inset: (left: 8pt), stroke: (left: 1.2pt + rule-c), above: 6pt, below: 6pt, text(style: "italic", s))

// A Reddit comment card: avatar disc, handle, then the body under a thread line.
#let reddit-comment(name, body, prefix: "u/", tag: none, icon: none) = {
  let deleted = name.starts-with("[")
  let hash = name.clusters().fold(7, (a, c) => calc.rem(a * 31 + str.to-unicode(c), 9973))
  let col = if deleted { luma(170) } else { reddit-palette.at(calc.rem(hash, reddit-palette.len())) }
  block(above: 9pt, below: 2pt, sticky: true, {
    if icon == none {
      box(baseline: 2.4pt, reddit-logo(col, 12pt))
    } else {
      box(baseline: 2.4pt, width: 12pt, height: 12pt, {
        circle(radius: 6pt, fill: col.lighten(78%), stroke: 0.4pt + col.lighten(40%))
        place(center + horizon, image(bytes(icon), format: "svg", width: 9pt, height: 9pt))
      })
    }
    h(4pt)
    text(7.6pt, font: sans, weight: "bold", fill: ink, if deleted { name } else { prefix + name })
    if tag not in (none, "") {
      h(5pt)
      text(6.8pt, font: sans, fill: muted, tag)
    }
  })
  block(above: 2pt, below: 6pt, inset: (left: 5.6pt), breakable: true,
    block(stroke: (left: 0.7pt + rule-c), inset: (left: 9.4pt, top: 0pt, bottom: 1pt), breakable: true, {
      set par(spacing: 0.5em)
      body
    }))
}

// The English original, set two-up. Its heading is the title, linked to the source.
#let en-gutter = 14pt
#let en-col-w = (body-w - en-gutter) / 2
#let source-text-count = counter("source-text")

#let en-style(body) = {
  set text(font: en-serif, size: 8.3pt, lang: "en", hyphenate: true)
  show link: it => underline(stroke: 0.35pt + rule-c, offset: 1.8pt, text(fill: ink, it.body))
  set par(first-line-indent: 0pt, leading: 0.52em, spacing: 0.6em, justify: true)
  set list(spacing: 0.35em)
  set enum(spacing: 0.35em)
  body
}

#let en-col-height(body) = measure(block(width: en-col-w, en-style(body))).height

#let en-starts-paragraph(children, i) = {
  let f = children.at(i).func()
  f not in (parbreak, [ ].func(), list.item, enum.item, terms.item) and (
    i == 0 or children.at(i - 1).func() == parbreak or f in (block, [].func())
  )
}

#let en-marked-body(id, children, cut) = {
  [#metadata((id: id, at: "top")) <en-mark>]
  for (i, child) in children.enumerate() {
    if en-starts-paragraph(children, i) { [#metadata((id: id, at: i)) <en-mark>] }
    if cut != none and i == cut.at {
      if cut.reserve > 0pt {
        place(bottom, float: true, scope: "column", clearance: 0pt, block(height: cut.reserve))
      } else {
        colbreak()
      }
    }
    child
  }
  [#metadata((id: id, at: "end")) <en-mark>]
}

#let en-last-page-cut(id, children, pitch) = {
  let marks = query(<en-mark>).filter(m => m.value.id == id)
  let end = marks.find(m => m.value.at == "end")
  if end == none { return none }
  let last-page = end.location().page()
  let top = marks.first().location()
  let col-top = if top.page() == last-page { top.position().y } else { page-margin.top }
  let first = marks.find(m => type(m.value.at) == int and m.location().page() == last-page)
  if first == none { return none }
  let pos = first.location().position()
  if pos.x > page-w / 2 { return none }
  let spill = pos.y - col-top
  let target = (spill + en-col-height(children.slice(first.value.at).join()) + pitch) / 2
  let reserve = page-h - page-margin.bottom - col-top - target
  if target < spill + pitch { (at: first.value.at, reserve: 0pt) }
  else if reserve > 0pt { (at: first.value.at, reserve: reserve) }
}

// The English original, set two-up. Its heading is the title, linked to the source.
#let source-text(title, url, body) = {
  source-text-count.step()
  context {
    let id = source-text-count.get().first()
    let children = if body.has("children") { body.children } else { (body,) }
    let head = {
      line(length: 100%, stroke: 0.6pt + ink)
      block(above: 7pt, below: 7pt, sticky: true, link(url, text(10.2pt, weight: "bold", font: symbols, fill: ink, lang: "en")[#if url.contains("reddit.com") [#box(baseline: 1.8pt, reddit-logo(reddit-orange, 10pt)) ]#title #text(8pt, fill: accent, weight: "regular", sym.arrow.tr)]))
    }
    let pitch = en-col-height[x \ x] - en-col-height[x]
    let short-h = (en-col-height(body) + pitch) / 2
    let slack = 2 * pitch
    let long = measure(block(width: body-w, head)).height + 7pt + short-h + slack > body-h
    if long {
      let prev = query(en-start-or-heading.before(here(), inclusive: false))
      if prev == () or prev.last().func() != heading { pagebreak(weak: true) }
    }
    [#metadata((long: long)) <en-start>]
    block(width: 100%, above: 10pt, below: 14pt, breakable: long, {
      head
      en-style(if long {
        columns(2, gutter: en-gutter, en-marked-body(id, children, en-last-page-cut(id, children, pitch)))
      } else {
        block(height: short-h + slack, columns(2, gutter: en-gutter, {
          place(bottom, float: true, scope: "column", clearance: 0pt, block(height: slack))
          body
        }))
      })
    })
  }
}

#show outline.entry: set text(9pt)
#show outline.entry.where(level: 1): it => {
  set text(font: sans, weight: "bold")
  block(above: 10pt, below: 4pt, it)
}
#set outline.entry(fill: box(width: 1fr, repeat(gap: 3pt, text(fill: rule-c, "."))))
