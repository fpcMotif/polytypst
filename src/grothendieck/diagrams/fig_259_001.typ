#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X_i$),
  fletcher.node((1, 0), $Y_i$),
  fletcher.node((0, 1), $X$),
  fletcher.node((1, 1), $Y$),
  fletcher.edge((0, 0), (1, 0), "->", $f_i$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $j_i$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $h_i$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $f$, label-side: right),
)
