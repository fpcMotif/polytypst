#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $M_(f \, n)$),
  fletcher.node((1, 0), $M_(f g \, n)$),
  fletcher.node((0, 1), $M_f$),
  fletcher.node((1, 1), $M_(f g)$),
  fletcher.edge((0, 0), (1, 0), "->", $rho_(f g \, f)^n$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $phi_n^f$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $phi_n^(f g)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $rho_(f g \, f)$, label-side: right),
)
