#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X_1$),
  fletcher.node((1, 0), $X_2$),
  fletcher.node((0, 1), $X_1^0$),
  fletcher.node((1, 1), $X_2^0$),
  fletcher.edge((0, 0), (1, 0), "->", $g$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $i_(X_1)$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $i_(X_2)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $g^0$, label-side: right),
)
