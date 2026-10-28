#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $U_(j i)$),
  fletcher.node((1, 0), $U_(i j)$),
  fletcher.node((0, 1), $U_(j i) inter U_(k i)$),
  fletcher.node((1, 1), $U_(i j) inter U_(k j)$),
  fletcher.edge((0, 0), (1, 0), "->", $theta_(i j)$, label-side: left),
  fletcher.edge((0, 1), (0, 0), "->"),
  fletcher.edge((1, 1), (1, 0), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $theta'_(i j)$, label-side: right),
)
