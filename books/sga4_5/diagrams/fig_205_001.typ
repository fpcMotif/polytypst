#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $0 arrow.r.long ( V_0^(\*) )_n arrow.r.long V_0^(\*) limits(arrow.r.long)^(x^n) V_0^(\*) arrow.r.long 0$),
  fletcher.node((0, 1), $0 arrow.r.long k^(\*) arrow.r.long V_0^(\*) limits(arrow.r.long)^zeta V_0^(\*) arrow.r.long 0$),
  fletcher.edge((0, 0), (0, 1), "->", $tau arrow.b arrow.b$, label-side: left),
)
