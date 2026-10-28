#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (1.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X$),
  fletcher.node((1, 0), $"Spec"(K')$),
  fletcher.node((0, 1), $Y$),
  fletcher.node((1, 1), $"Spec"(K)$),
  fletcher.edge((1, 0), (0, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $f$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((1, 1), (0, 1), "->"),
)
