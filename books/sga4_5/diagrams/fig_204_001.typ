#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $0 arrow.r.long G_(n d) arrow.r.long G limits(arrow.r.long)^(x^(n d)) G arrow.r.long 0$),
  fletcher.node((0, 1), $0 arrow.r.long G_n arrow.r.long G limits(arrow.r.long)^(x^n) G arrow.r.long 0$),
  fletcher.edge((0, 0), (0, 1), "->", $x^d arrow.b x^d$, label-side: left),
)
