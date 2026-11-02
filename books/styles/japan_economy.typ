#let latin = (name: "STIX Two Text", covers: regex("[\u{0}-\u{24F}]"))
#let serif = (latin, "Songti SC", "STSong")
#let sans = ("Noto Sans CJK SC", "Heiti SC")
#let kai = (latin, "STKaiti", "Kaiti SC")

#let pitch = 18.375pt
#let gap = 7.875pt
#let lines-tall(n) = n * pitch - gap

#set text(font: serif, size: 10.5pt, number-type: "lining", top-edge: 0.88em, bottom-edge: -0.12em, costs: (widow: 0%, orphan: 0%))
#set par(leading: gap, spacing: gap, first-line-indent: (amount: 2em, all: true), justify: true)
#show math.equation: set text(font: ("New Computer Modern Math", "Songti SC"))

#let plain-text(body) = if body.has("text") { body.text } else if body.has("children") { body.children.map(plain-text).join() } else { "" }
#let in-numbered-chapter(loc) = {
  let chaps = query(heading.where(level: 1).before(loc))
  counter(heading).at(loc).first() > 0 or (chaps != () and plain-text(chaps.last().body).match(regex("^\d{1,2} ")) != none)
}
#let head-number(it) = if it.numbering != none and in-numbered-chapter(it.location()) {
  context {
    let nums = counter(heading).get()
    let label = if type(it.numbering) == function { (it.numbering)(..nums) } else { numbering(it.numbering, ..nums) }
    if type(label) == str { label.trim("\u{2002}", at: end).trim(".", at: end) + "\u{2002}" } else { label }
  }
}
#show heading.where(level: 1): it => {
  counter(footnote).update(0)
  counter(figure.where(kind: image)).update(0)
  counter(figure.where(kind: table)).update(0)
  let back-matter = it.body.has("text") and it.body.text == "后记"
  let lead = plain-text(it.body).match(regex("^(\d{1,2}) "))
  let number = if lead != none { lead.captures.first() } else if it.numbering != none {
    numbering(it.numbering, ..counter(heading).at(it.location()))
  }
  v(if back-matter { 0pt } else { 2 * pitch })
  block(width: 100%, above: 0pt, below: 0pt)[
    #set par(first-line-indent: 0pt, justify: false, leading: 0.45em)
    #if number != none [
      #text(9.5pt, weight: "bold", font: sans, tracking: 0.3em)[第#h(0.3em)#number#h(0.3em)章]
      #v(0.4em)
    ]
    #line(length: 100%, stroke: 1.6pt)
    #v(0.9em)
    #layout(size => {
      show regex("^\d{1,2} "): none
      let title = text(20pt, weight: "bold", font: sans, it.body)
      let lines = calc.ceil(measure(title).width / (size.width * 0.9))
      block(width: if lines > 1 { measure(title).width / lines + 2em } else { 90% }, title)
    })
  ]
  v(if number != none { 0.9em } else { 2 * pitch })
}
#show heading.where(level: 2): set heading(numbering: (..n) => str(n.pos().at(1)) + "\u{2002}")
#show heading.where(level: 3): set heading(numbering: (..n) => n.pos().slice(1).map(str).join(".") + "\u{2002}")
#show heading.where(level: 4): set heading(numbering: (..n) => n.pos().slice(1).map(str).join(".") + "\u{2002}")
#show heading.where(level: 2): it => block(above: gap, below: gap, height: lines-tall(3), width: 100%, sticky: true, align(left + horizon, text(12pt, weight: "bold", font: sans)[#head-number(it)#it.body]))
#show heading.where(level: 3): it => block(above: gap, below: gap, height: lines-tall(2), width: 100%, sticky: true, align(left + horizon, text(10.5pt, weight: "bold", font: sans)[#head-number(it)#it.body]))
#show heading.where(level: 4): it => block(above: gap, below: gap, sticky: true, text(10.5pt, weight: "bold", font: sans)[#head-number(it)#it.body])

#let chapter-subtitle(body) = block(above: 0pt, below: 0.6em, width: 100%)[
  #set par(first-line-indent: 0pt, justify: false)
  #text(11pt, body)
]
#let chapter-byline(body) = block(above: 0.6em, below: 1.6 * pitch, width: 100%)[
  #show " ": h(1.2em)
  #align(right, text(11.5pt, font: kai, body))
  #v(0.2em)
  #line(length: 100%, stroke: 0.4pt)
]
#let chapter-abstract(note: [], body) = block(above: 0pt, below: pitch, width: 100%, breakable: true, grid(
  columns: (auto, 1fr),
  column-gutter: 0.9em,
  pad(top: 0.15em, stack(
    dir: ttb,
    spacing: 0.5em,
    ..("导", "语").map(c => text(11pt, weight: "bold", font: sans, fill: luma(60), c)),
    text(9.5pt, note),
  )),
  block(stroke: (left: 0.5pt + luma(120)), inset: (left: 1em, y: 0.1em), width: 100%)[
    #set text(9.5pt, font: kai)
    #set par(leading: 0.62em, spacing: 0.62em)
    #body
  ],
))

#show figure: set block(above: 1.2em, below: 0.35em)
#show figure.caption: it => block(above: 0.6em)[
  #set par(first-line-indent: 0pt, justify: false)
  #text(9pt)[#if it.supplement != none [#text(font: sans, weight: "medium")[#it.supplement #context it.counter.display(it.numbering)]#if it.body != [] [#h(1em)]]#it.body]
]
#let fig-note(body) = block(above: 0.35em, below: 1.2em, width: 100%, inset: 0pt)[
  #set align(start)
  #set text(8.5pt, fill: luma(35))
  #show regex("^[（(［\\[]?(?:资料来源|数据来源|注)[：:]"): set text(weight: "medium", fill: black)
  #set par(first-line-indent: 0pt, justify: true, spacing: 0.35em, leading: 0.52em)
  #body
]

#show table: it => layout(size => if measure(it, width: size.width).height < 0.78 * size.height { block(breakable: false, it) } else { it })
#show table: set text(size: 8.5pt, number-width: "tabular")
#show table: set par(first-line-indent: 0pt, justify: false, leading: 0.5em, linebreaks: "simple")
#set table(inset: (x: 0.45em, y: 0.42em))

#set footnote.entry(separator: line(length: 30%, stroke: 0.4pt), gap: 0.45em, clearance: 1em)
#show footnote.entry: set text(8.5pt)
#show footnote.entry: set par(first-line-indent: 0pt, leading: 0.55em)
