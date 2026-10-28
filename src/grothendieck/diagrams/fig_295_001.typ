#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((1, 0), $kappa ( x )$),
  fletcher.node((0, 1), $kappa ( b )$),
  fletcher.node((1, 1), $kappa ( y )$),
  fletcher.edge((1, 0), (0, 1), "->", $gamma$, label-side: right),
  fletcher.edge((1, 1), (1, 0), "->", $alpha$, label-side: right),
  fletcher.edge((1, 1), (0, 1), "->", $beta$, label-side: left),
)
