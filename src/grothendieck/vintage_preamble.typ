#set document(
  title: "Éléments de Géométrie Algébrique I — A. Grothendieck and J. A. Dieudonné",
  author: "A. Grothendieck and J. A. Dieudonné",
  date: auto
)

#let body-font = ("STIX Two Text",)
#let chapter-label = state("chapter-label", none)

#let page-fit = json("page_fit.json")
#let fit-of(n) = page-fit.at("pages", default: (:)).at(str(n), default: (:))
#let fit-size(n) = fit-of(n).at("size", default: 9.5) * 1pt
#let fit-leading(n, k) = fit-of(n).at("leading", default: 5.1) * 1pt
#let mark(kind, key) = context [#metadata((kind: kind, key: key, page: here().page(), y: here().position().y.pt()))<src-mark>]
#let first-printed-page = 9
#let src-page(n) = {
  pagebreak(weak: true)
  if n >= first-printed-page { counter(page).update(n - first-printed-page + 1) }
  mark("page", n)
}
#let folio() = counter(page).get().first()
#let src-top(n) = mark("top", n)
#let src-end(n) = mark("end", n)
#let src-cont = h(-18pt)
#let chapter-pages() = query(heading.where(level: 1)).map(h => h.location().page())

#set page(
  width: 344pt,
  height: 572pt,
  margin: (left: 16pt, right: 19pt, top: 58pt, bottom: 6pt),
  header-ascent: 12pt,
  header: context {
    let pg = here().page()
    if pg in chapter-pages() { return }
    let chaps = query(heading.where(level: 1).before(here()))
    if chaps == () { return }
    let chap = chaps.last()
    set text(9.5pt)
    if calc.odd(folio()) {
      let secs = query(heading.where(level: 2)).filter(h => h.location().page() <= pg and h.location().page() >= chap.location().page())
      let title = if secs != () { [#counter(heading).at(secs.last().location()).slice(1, 2).map(n => "§ " + str(n) + ".").join() #secs.last().body] } else { chap.body }
      grid(columns: (1fr, auto, 1fr), [], align(center, title), align(right, counter(page).display()))
    } else {
      let number = if chap.numbering != none { (chap.numbering)(1) + ". " } else { "" }
      grid(columns: (1fr, auto, 1fr), align(left, counter(page).display()), align(center, [#number#chap.body]), [])
    }
  },
  footer: none,
)

#set text(font: body-font, size: 9.5pt, lang: "fr", hyphenate: true, number-type: "lining")
#set par(leading: 5.1pt, spacing: 5.1pt, justify: true, first-line-indent: (amount: 18pt, all: true))
#show math.equation: set text(font: ("STIX Two Math",))
#set math.mat(row-gap: 0.55em, column-gap: 0.8em)
#show math.equation.where(block: false): it => {
  show math.frac: set text(size: 0.85em)
  it
}
#show math.equation.where(block: true): set block(above: 0.7em, below: 0.7em)
#show math.equation.where(block: true): it => {
  if it.numbering == none { return it }
  let number = counter(math.equation).display(it.numbering)
  block(above: 0.7em, below: 0.7em, layout(size => {
    let eq = math.equation(it.body, block: true, numbering: none)
    let gap = measure(number).width + 12pt
    let w = measure(eq).width
    let fitted = if w > size.width - 2 * gap and w > 0pt {
      let s = (size.width - 2 * gap) / w * 100%
      scale(x: s, y: s, reflow: true, eq)
    } else { eq }
    grid(columns: (gap, 1fr, gap), align: (left + horizon, center + horizon, right), number, fitted, [])
  }))
}

#let thm-break = block(above: 0.7em, below: 0pt, sticky: true)[]
#let sub-break = block(above: 0.6em, below: 0pt, sticky: true)[]
#let item-break = block(above: 0.3em, below: 0pt)[]
#let qed = { h(0.6em); box(width: 1fr, align(right)[$square.stroked$]) }
#let dd = math.dif
#let dv(f, x, deg: none) = if deg == none { $(dif f)/(dif x)$ } else { $(dif^deg f)/(dif x^deg)$ }
#let pdv(f, x, deg: none) = if deg == none { $(partial f)/(partial x)$ } else { $(partial^deg f)/(partial x^deg)$ }
#let const = math.op("const")
#let ord = math.op("ord")
#let grad = math.op("grad")
#let rot = math.op("rot")
#let div = math.op("div")
#let rank = math.op("rank")

#show heading: set par(justify: false, first-line-indent: 0pt)
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(36pt)
  context {
    let label = chapter-label.get()
    if label != none {
      align(center, text(10.5pt, upper(label)))
      v(14pt)
    }
  }
  align(center, text(16pt, weight: "bold", it.body))
  v(30pt)
}
#show heading.where(level: 2): it => {
  v(1.6em, weak: true)
  align(center, text(12pt, weight: "bold")[#if it.numbering != none [#counter(heading).display(it.numbering) ]#it.body])
  v(1.2em, weak: true)
}
#show heading.where(level: 3): it => {
  v(1.2em, weak: true)
  text(11pt, weight: "bold")[#if it.numbering != none [#counter(heading).display(it.numbering) ]#it.body]
  v(0.6em, weak: true)
}

#show figure: set block(above: 1.0em, below: 1.0em)
#show figure.caption: it => text(8.5pt, it.body)
