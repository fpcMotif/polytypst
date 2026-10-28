#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X_u$),
  fletcher.node((2, 0), $X_v$),
  fletcher.node((1, 1), $S$),
  fletcher.edge((0, 0), (2, 0), "->", $f$, label-side: left),
  fletcher.edge((0, 0), (1, 1), "->", $u$, label-side: right),
  fletcher.edge((2, 0), (1, 1), "->", $v$, label-side: left),
)
