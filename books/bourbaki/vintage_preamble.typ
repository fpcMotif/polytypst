#set document(
  title: "Commutative Algebra (Chapters 1–7) — Nicolas Bourbaki",
  author: "Nicolas Bourbaki",
  date: auto
)

#let tune(key, default) = sys.inputs.at(key, default: default)
#let body-font = (tune("font", "Baskervville"), "STIX Two Text")
#let chapter-label = state("chapter-label", none)

#let plain(it) = {
  if type(it) == str { it }
  else if it.has("text") { it.text }
  else if it.has("children") { it.children.map(plain).join() }
  else if it.has("body") { plain(it.body) }
  else if it.has("child") { plain(it.child) }
  else { " " }
}
#let split-number(it) = {
  let s = plain(it).trim()
  let m = s.match(regex("^(?:§\s*)?(\d+)\.\s*(.*)$"))
  if m == none { (none, s) } else { (m.captures.at(0), m.captures.at(1)) }
}
#let chapter-pages() = query(heading.where(level: 1)).map(h => h.location().page())

#let page-fit = json("page_fit.json")
#let fit-of(n) = page-fit.at("pages", default: (:)).at(str(n), default: (:))
#let fit-size(n) = fit-of(n).at("size", default: 9.6) * float(tune("size-scale", "1")) * 1pt
#let fit-leading(n, k) = fit-of(n).at("leading", default: 4.3) * 1pt
#let fit-fig-leading(fig) = page-fit.at("figs", default: (:)).at(fig, default: 4.3) * 1pt
#let mark(kind, key) = context [#metadata((kind: kind, key: key, page: here().page(), y: here().position().y.pt()))<src-mark>]
#let first-printed-page = 31
#let src-page(n) = {
  v(fit-of(n - 1).at("reserve", default: 0) * 1pt)
  pagebreak(weak: true)
  if n >= first-printed-page { counter(page).update(n - first-printed-page + 1) }
  mark("page", n)
}
#let folio() = counter(page).get().first()
#let src-top(n) = mark("top", n)
#let src-end(n) = mark("end", n)
#let src-fig(fig) = mark("fig", fig)
#let src-cont = h(-1.1em)

#set page(
  width: 388pt,
  height: 609pt,
  margin: (inside: 32pt, outside: 32pt, top: 74pt, bottom: 66pt),
  header-ascent: 14pt,
  footer-descent: 12pt,
  header: context {
    let pg = here().page()
    if pg <= 4 or pg in chapter-pages() { return }
    let chaps = query(heading.where(level: 1).before(here()))
    if chaps == () { return }
    let chap = chaps.last()
    let roman = if chap.numbering != none { (chap.numbering)(1) } else { "" }
    set text(7.6pt, weight: 700, tracking: 0.04em)
    if calc.odd(folio()) {
      let in-chapter = h => h.location().page() >= chap.location().page() and h.location().page() <= pg
      let secs = query(heading.where(level: 2)).filter(in-chapter)
      let heads = query(selector(heading.where(level: 2)).or(heading.where(level: 3))).filter(in-chapter)
      let (sec-num, sec-title) = if secs != () { split-number(secs.last().body) } else { (none, plain(chap.body)) }
      let (no-num, no-title) = if heads != () and heads.last().level == 3 { split-number(heads.last().body) } else { (none, sec-title) }
      let title = upper(no-title)
      let mark = if sec-num == none { "" } else if no-num == none { "§ " + sec-num } else { "§ " + sec-num + "." + no-num }
      grid(columns: (1fr, auto, 1fr), [], align(center, title), align(right, text(9.6pt, weight: 500, tracking: 0pt, mark)))
    } else {
      grid(columns: (1fr, auto, 1fr), align(left, roman), align(center, upper(plain(chap.body))), [])
    }
  },
  footer: context {
    let pg = here().page()
    if pg <= 4 { return }
    set text(9.6pt, weight: 500)
    let n = counter(page).display()
    if calc.odd(folio()) { align(right, n) } else { align(left, n) }
  },
)

#set text(
  font: body-font,
  size: 9.6pt,
  weight: int(tune("weight", "500")),
  tracking: float(tune("tracking", "0")) * 1pt,
  spacing: float(tune("word-spacing", "100")) * 1%,
  lang: "en",
  hyphenate: true,
  number-type: "lining",
)
#set par(
  leading: 4.3pt,
  spacing: 4.3pt,
  justify: true,
  justification-limits: (
    spacing: (min: float(tune("shrink-spacing", "66.67")) * 1% + 0pt, max: 150% + 0pt),
    tracking: (min: float(tune("shrink-tracking", "-0.02")) * 1em, max: 0em),
  ),
  first-line-indent: (amount: 1.1em, all: true),
  linebreaks: tune("linebreaks", "optimized"),
)
#show strong: it => text(weight: 500)[#smallcaps(it.body)]
#show emph: it => {
  set text(style: "italic")
  show regex("\b[A-Z]\b"): set text(style: "normal")
  it.body
}

#show math.equation: set text(font: ("STIX Two Math",), weight: "regular")
#show math.equation: it => {
  show regex("[A-Z0-9]"): l => text(font: body-font, weight: 500, style: "normal", math.upright(l))
  show regex("\b[a-z]\b"): l => text(font: body-font, weight: 500, style: "italic", math.upright(l))
  it
}
#set math.equation(numbering: "(1)")
#set math.mat(row-gap: 0.55em, column-gap: 0.8em)
#show math.equation.where(block: false): it => {
  show math.frac: set text(size: 0.85em)
  it
}
#show math.equation.where(block: true): set block(above: 0.9em, below: 0.9em)
#let page-fill(weight) = v(weight * float(tune("fill", "1")) * 1fr, weak: true)
#let thm-break = { page-fill(1); block(above: 1.1em, below: 0pt, sticky: true)[] }
#let sub-break = { page-fill(0.5); block(above: 0.6em, below: 0pt, sticky: true)[] }
#let item-break = { page-fill(0.5); block(above: 0.3em, below: 0pt)[] }
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
#show ref: it => {
  let target = str(it.target)
  if target.starts-with("eq-") {
    let raw = target.trim("eq-", at: start)
    link(it.target)[(#raw.split("-").last())]
  } else {
    it
  }
}
#show math.equation.where(block: true): it => {
  if it.numbering == none {
    return it
  }
  page-fill(1)
  block(above: 0.9em, below: 0.9em, layout(size => {
    let eq = math.equation(it.body, block: true, numbering: none)
    let num-box = if it.has("label") {
      [(#str(it.label).trim("eq-", at: start).split("-").last())]
    } else { none }
    let avail = size.width - if num-box != none { measure(num-box).width + 12pt } else { 0pt }
    let m = measure(eq)
    let fitted = if m.width > avail and m.width > 0pt {
      scale(x: avail / m.width * 100%, y: avail / m.width * 100%, reflow: true, eq)
    } else { eq }
    if num-box == none { fitted } else {
      grid(columns: (1fr, auto), column-gutter: 0.8em, align: (center + horizon, right + horizon), fitted, num-box)
    }
  }))
  page-fill(1)
}

#show heading: set par(justify: false, first-line-indent: 0pt)
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  if it.numbering != none and (it.numbering)(1) == "I" { counter(page).update(1) }
  v(-10pt)
  context {
    let label = chapter-label.get()
    if label != none {
      align(center, text(8.6pt, weight: 700, tracking: 0.05em, upper(label)))
      v(16pt)
    }
  }
  align(center, text(19pt, weight: 500, it.body))
  v(112pt)
}
#show heading.where(level: 2): it => {
  v(2.2em, weak: true)
  let (num, title) = split-number(it.body)
  align(center, text(11pt, weight: 500, tracking: 0.06em,
    upper(if num != none { num + ". " + title } else { title })))
  v(1.6em, weak: true)
}
#show heading.where(level: 3): it => {
  v(1.3em, weak: true)
  text(7.8pt, weight: 700, tracking: 0.03em, upper(plain(it.body)))
  v(0.9em, weak: true)
}
#show heading.where(level: 4): it => {
  v(1.0em, weak: true)
  text(9.6pt, style: "italic", it.body)
  v(0.5em, weak: true)
}

#show figure: set block(above: 1.0em, below: 1.0em)
#show figure.caption: it => text(8.6pt, it.body)
#show image: set block(above: 0.8em, below: 0.8em)
