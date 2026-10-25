#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $C$),
  fletcher.node((1, 0), $B_s$),
  fletcher.node((0, 1), $C_(frak(q))$),
  fletcher.node((1, 1), $B_(frak(p))$),
  fletcher.edge((0, 0), (1, 0), "->", $sigma$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $phi$, label-side: right),
)
