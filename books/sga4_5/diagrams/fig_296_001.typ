#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $D^(+) ( A )$),
  fletcher.node((2, 0), $D^(-) ( A )$),
  fletcher.node((1, 1), $D b ( A )$),
  fletcher.node((2, 1), $D$),
  fletcher.edge((0, 0), (2, 0), "->", $D ( A )$, label-side: left),
  fletcher.edge((0, 0), (1, 1), "->"),
  fletcher.edge((2, 0), (2, 1), "->"),
)
