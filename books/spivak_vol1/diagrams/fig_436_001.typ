#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $C_1^k$),
  fletcher.node((1, 0), $C_2^k$),
  fletcher.node((0, 1), $C_1^(k+1)$),
  fletcher.node((1, 1), $C_2^(k+1)$),
  fletcher.edge((0, 0), (1, 0), "->", $alpha^k$),
  fletcher.edge((0, 0), (0, 1), "->", $d_1^k$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $d_2^k$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $alpha^(k+1)$),
)
