#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $M_f$),
  fletcher.node((1, 0), $N_f$),
  fletcher.node((0, 1), $M_g$),
  fletcher.node((1, 1), $N_g$),
  fletcher.edge((0, 0), (1, 0), "->", $u_f$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $rho_(g \, f)$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $rho_(g \, f)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $u_g$, label-side: right),
)
