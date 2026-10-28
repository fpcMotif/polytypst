#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X times X times X$),
  fletcher.node((1, 0), $X times X$),
  fletcher.node((0, 1), $X times X$),
  fletcher.node((1, 1), $X$),
  fletcher.edge((0, 0), (1, 0), "->", $c_X times 1_X$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $1_X times c_X$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $c_X$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $c_X$, label-side: right),
)
