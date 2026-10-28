#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((1, 0), $k'$),
  fletcher.node((0, 1), $A$),
  fletcher.node((2, 1), $K$),
  fletcher.node((1, 2), $k''$),
  fletcher.edge((0, 1), (1, 0), "->", $t'$, label-side: left),
  fletcher.edge((1, 0), (2, 1), "->", $f'$, label-side: left),
  fletcher.edge((0, 1), (1, 2), "->", $t''$, label-side: right),
  fletcher.edge((1, 2), (2, 1), "->", $f''$, label-side: right),
)
