#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $M$),
  fletcher.node((1, 0), $N$),
  fletcher.node((0, 1), $M_f$),
  fletcher.node((1, 1), $N_f$),
  fletcher.edge((0, 0), (1, 0), "->", $u$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $rho_(f \, 1)$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $rho_(f \, 1)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $w$, label-side: right),
)
