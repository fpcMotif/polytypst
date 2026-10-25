#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $cal(G) \u{2297}_(cal(B)) cal(G)$),
  fletcher.node((1, 0), $cal(G)$),
  fletcher.node((0, 1), $Psi_(\*) ( cal(F) \u{2297}_(cal(A)) cal(F) )$),
  fletcher.node((1, 1), $Psi_(\*) ( cal(F) )$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->", $u$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->"),
)
