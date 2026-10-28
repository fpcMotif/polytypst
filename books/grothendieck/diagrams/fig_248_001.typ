#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X$),
  fletcher.node((1, 0), $X_((S'))$),
  fletcher.node((0, 1), $Y$),
  fletcher.node((1, 1), $Y_((S'))$),
  fletcher.edge((1, 0), (0, 0), "->", $p$, label-side: right),
  fletcher.edge((0, 0), (0, 1), "->", $f$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $f_((S'))$, label-side: left),
  fletcher.edge((1, 1), (0, 1), "->", $q$, label-side: left),
)
