#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $G_n$),
  fletcher.node((1, 0), $F_n$),
  fletcher.node((0, 1), $G_(n + 1)$),
  fletcher.node((1, 1), $F_(n + 1)$),
  fletcher.edge((0, 0), (1, 0), "->", $s'_n$, label-side: left),
  fletcher.edge((0, 1), (0, 0), "->", $h_n$, label-side: left),
  fletcher.edge((1, 1), (1, 0), "->", $g_n$, label-side: right),
  fletcher.edge((0, 1), (1, 1), "->", $s_(n + 1)$, label-side: right),
)
