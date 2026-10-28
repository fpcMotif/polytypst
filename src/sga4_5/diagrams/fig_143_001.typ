#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $H^0 ( X - D \, frak(E)_m )$),
  fletcher.node((1, 0), $H_D^1 ( X \, frak(E)_m )$),
  fletcher.node((0, 1), $H^1 ( X - D \, mu_n )$),
  fletcher.node((1, 1), $H_D^2 ( X \, mu_n )$),
  fletcher.edge((0, 0), (1, 0), "->", $partial$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $partial$, label-side: left),
  fletcher.edge((1, 0), (1, 1), "->", $partial$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $partial$, label-side: right),
)
