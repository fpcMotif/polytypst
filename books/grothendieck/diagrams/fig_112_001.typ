#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X_(i j k)$),
  fletcher.node((1, 0), $X_(i k)$),
  fletcher.node((0, 1), $X_(i j)$),
  fletcher.node((1, 1), $X_i$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->", $f_(k i)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $f_(j i)$, label-side: right),
)
