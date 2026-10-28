#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $F_(i j)$),
  fletcher.node((1, 0), $F_i$),
  fletcher.node((0, 1), $F_j$),
  fletcher.node((1, 1), $F$),
  fletcher.edge((0, 0), (1, 0), "->", $u_(j i)$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $u_(i j)$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $u_i$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $u_j$, label-side: right),
)
