#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $frak(X)$),
  fletcher.node((1, 0), $frak(X) times_(frak(S)) frak(Y)$),
  fletcher.node((0, 1), $frak(S)$),
  fletcher.node((1, 1), $frak(Y)$),
  fletcher.edge((1, 0), (0, 0), "->", $p$, label-side: right),
  fletcher.edge((0, 0), (0, 1), "->", $f$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $q$, label-side: left),
  fletcher.edge((1, 1), (0, 1), "->", $g$, label-side: left),
)
