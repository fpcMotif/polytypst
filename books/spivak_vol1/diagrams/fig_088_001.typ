#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $E_1$),
  fletcher.node((1, 0), $E_2$),
  fletcher.node((0, 1), $B_1$),
  fletcher.node((1, 1), $B_2 ,$),
  fletcher.edge((0, 0), (1, 0), "->", $macron(f)$),
  fletcher.edge((0, 0), (0, 1), "->", $pi_1$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $pi_2$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $f$),
)
