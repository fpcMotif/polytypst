#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $A_alpha$),
  fletcher.node((1, 0), $A_beta$),
  fletcher.node((0, 1), $S_alpha^(- 1) A_alpha$),
  fletcher.node((1, 1), $S_beta^(- 1) A_beta$),
  fletcher.edge((0, 0), (1, 0), "->", $phi_(beta alpha)$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $rho_(beta alpha)$, label-side: right),
)
