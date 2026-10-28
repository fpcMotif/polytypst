#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.5em, 2.2em),
  label-size: 0.85em,
  fletcher.node((0, 0), $beta_1^*(xi')$),
  fletcher.node((1, 0), $beta_2^*(xi')$),
  fletcher.node((0, 1), $beta_1^*(eta')$),
  fletcher.node((1, 1), $beta_2^*(eta')$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 1), (1, 1), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $u$, label-side: left),
  fletcher.edge((1, 0), (1, 1), "->", $u$, label-side: right),
)
