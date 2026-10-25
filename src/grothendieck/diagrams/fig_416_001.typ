#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $frak(X)$),
  fletcher.node((2, 0), $frak(Y)$),
  fletcher.node((1, 1), $frak(S)$),
  fletcher.edge((0, 0), (2, 0), "->", $u$, label-side: left),
  fletcher.edge((0, 0), (1, 1), "->"),
  fletcher.edge((2, 0), (1, 1), "->"),
)
