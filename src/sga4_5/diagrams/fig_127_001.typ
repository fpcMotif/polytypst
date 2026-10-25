#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $F_(upright("abs"))^(\*) G$),
  fletcher.node((1, 0), $G$),
  fletcher.node((0, 1), $F_(upright("abs"))^(\*) bb(Q)$),
  fletcher.node((1, 1), $bb(Q)$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $Phi'$, label-side: left),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->"),
)
