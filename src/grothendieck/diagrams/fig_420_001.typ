#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X_lambda$),
  fletcher.node((2, 0), $frak(Y)$),
  fletcher.node((1, 1), $frak(X)$),
  fletcher.edge((0, 0), (2, 0), "->", $g_lambda$, label-side: left),
  fletcher.edge((0, 0), (1, 1), "->", $f_lambda$, label-side: right),
  fletcher.edge((1, 1), (2, 0), "->", $g$, label-side: right),
)
