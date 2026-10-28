#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $F^(\*) G_0$),
  fletcher.node((1, 0), $G_0$),
  fletcher.node((0, 1), $F^(\*) G_0$),
  fletcher.node((1, 1), $G_0$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $( Phi^f )$, label-side: left),
  fletcher.edge((1, 0), (1, 1), "->", $Phi_0$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $( Phi^f )$, label-side: right),
)
