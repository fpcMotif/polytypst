#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X$),
  fletcher.node((1, 0), $Y$),
  fletcher.node((0, 1), $""^s X$),
  fletcher.node((1, 1), $""^s Y$),
  fletcher.edge((0, 0), (1, 0), "->", $f$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $q_X$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $q_Y$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $""^s f$, label-side: right),
)
