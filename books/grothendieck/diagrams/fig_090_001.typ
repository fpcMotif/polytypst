#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (4.5em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $cal(G)_1$),
  fletcher.node((1, 0), $cal(G)_2$),
  fletcher.node((0, 1), $psi_(\*) ( psi^(- 1) ( cal(G)_1 ) )$),
  fletcher.node((1, 1), $psi_(\*) ( psi^(- 1) ( cal(G)_2 ) )$),
  fletcher.edge((0, 0), (1, 0), "->", $w$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $rho_(cal(G)_1)$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $rho_(cal(G)_2)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $psi^(\*) ( psi^(- 1) ( w ) )$, label-side: right),
)
