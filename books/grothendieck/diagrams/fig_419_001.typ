#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $B$),
  fletcher.node((1, 0), $A$),
  fletcher.node((0, 1), $B \/ frak(K)$),
  fletcher.node((1, 1), $A \/ frak(J)$),
  fletcher.edge((0, 0), (1, 0), "->", $phi$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $phi'$, label-side: right),
)
