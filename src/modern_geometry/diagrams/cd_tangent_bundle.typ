#import "@preview/fletcher:0.5.8": diagram, node, edge

#diagram(
  spacing: (4em, 3em),
  node-inset: 4pt,
  label-size: 10pt,
  node((0, 0), $T_x M$),
  node((1, 0), $T_(F(x)) N$),
  node((0, 1), $M$),
  node((1, 1), $N$),
  edge((0, 0), (1, 0), "->", $d F_x$, label-side: left),
  edge((0, 1), (1, 1), "->", $F$, label-side: right),
  edge((0, 0), (0, 1), "->", $pi_M$, label-side: right),
  edge((1, 0), (1, 1), "->", $pi_N$, label-side: left),
)
