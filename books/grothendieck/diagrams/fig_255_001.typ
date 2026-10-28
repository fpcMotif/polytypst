#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X(K)$),
  fletcher.node((1, 0), $Y(K)$),
  fletcher.node((0, 1), $X(K')$),
  fletcher.node((1, 1), $Y(K')$),
  fletcher.edge((0, 0), (1, 0), "->", $alpha$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $phi$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $phi'$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $alpha'$, label-side: right),
)
