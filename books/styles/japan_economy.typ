#let serif = ((name: "Source Serif 4", covers: "latin-in-cjk"), "Songti SC", "STSong")
#let sans = ((name: "Source Sans 3", covers: "latin-in-cjk"), "Noto Sans CJK SC", "Heiti SC")

#set text(font: serif, size: 10.5pt, number-type: "lining")
#set par(leading: 0.82em, spacing: 0.82em, first-line-indent: (amount: 2em, all: true), justify: true)
#show math.equation: set text(font: ("New Computer Modern Math", "Songti SC"))

#let head-number(it) = if it.numbering != none and counter(heading).at(it.location()).first() > 0 {
  counter(heading).display(it.numbering)
}
#show heading.where(level: 1): it => {
  let back-matter = it.body.has("text") and it.body.text == "后记"
  v(if back-matter { 0em } else { 3em })
  block(width: 100%, below: 0pt)[
    #set par(first-line-indent: 0pt, justify: false)
    #text(18pt, weight: "bold", font: sans)[#if it.numbering != none and counter(heading).at(it.location()).first() > 0 [#numbering(it.numbering, ..counter(heading).at(it.location()))#h(0.8em)]#it.body]
  ]
  v(0.7em)
  line(length: 100%, stroke: 0.8pt + black)
  v(if back-matter { 1em } else { 2em })
}
#show heading.where(level: 2): it => block(above: 2.1em, below: 1em, sticky: true, text(13.5pt, weight: "bold", font: sans)[#head-number(it)#it.body])
#show heading.where(level: 3): it => block(above: 1.6em, below: 0.8em, sticky: true, text(11.5pt, weight: "bold", font: sans)[#head-number(it)#it.body])
#show heading.where(level: 4): it => block(above: 1.3em, below: 0.6em, sticky: true, text(10.5pt, weight: "bold", font: sans)[#head-number(it)#it.body])

#show figure: set block(above: 1.8em, below: 1.2em)
#show figure.caption: it => block(above: 0.7em)[
  #set par(first-line-indent: 0pt, justify: false)
  #text(9.5pt)[#if it.supplement != none [#text(font: sans, weight: "medium")[#it.supplement #context it.counter.display(it.numbering)]#if it.body != [] [#h(1em)]]#it.body]
]
#let fig-note(body) = block(above: 0em, below: 1.6em, width: 100%)[
  #set text(8.5pt)
  #set par(first-line-indent: 0pt, justify: true, spacing: 0.4em, leading: 0.55em)
  #body
]

#show table: it => layout(size => if measure(it, width: size.width).height < 0.4 * size.height { block(breakable: false, it) } else { it })
#show table: set text(size: 8.5pt, number-width: "tabular")
#show table: set par(first-line-indent: 0pt, justify: false, leading: 0.5em)
#set table(inset: (x: 0.45em, y: 0.42em))

#set footnote.entry(separator: line(length: 30%, stroke: 0.4pt), gap: 0.45em, clearance: 1em)
#show footnote.entry: set text(8.5pt)
#show footnote.entry: set par(first-line-indent: 0pt, leading: 0.55em)
