#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X_n$),
  fletcher.node((1, 0), $Y_n$),
  fletcher.node((0, 1), $frak(X)$),
  fletcher.node((1, 1), $frak(Y)$),
  fletcher.edge((0, 0), (1, 0), "->", $f_n$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $f$, label-side: right),
)
