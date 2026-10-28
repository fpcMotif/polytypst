#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (1.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X$),
  fletcher.node((2, 0), $X times_Z X$),
  fletcher.node((1, 1), $X times_Y X$),
  fletcher.edge((0, 0), (2, 0), "->", $Delta_(X \/ Z)$, label-side: left),
  fletcher.edge((0, 0), (1, 1), "->", $Delta_(X \/ Y)$, label-side: right),
  fletcher.edge((1, 1), (2, 0), "->", $j$, label-side: right),
)
