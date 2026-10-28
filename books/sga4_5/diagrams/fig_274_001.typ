#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $dots.h arrow.r 0 arrow.r 0' arrow.r Y^(\*) arrow.r 0 arrow.r dots.h$),
  fletcher.node((0, 1), $dots.h arrow.r 0 arrow.r X^(\*) arrow.r Y^(\*) arrow.r 0 arrow.r dots.h$),
  fletcher.edge((0, 0), (0, 1), "->", $arrow.b arrow.b arrow.b$, label-side: left),
)
