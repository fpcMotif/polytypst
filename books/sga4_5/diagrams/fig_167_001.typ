#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $bb(H)^1 ( X times macron(X) \, G )$),
  fletcher.node((1, 0), $bb(H)^2 ( X times macron(X) \, j_(!) mu_n )$),
  fletcher.node((0, 1), $bb(H)^1 ( X \, R p r_(1 \*)^G )$),
  fletcher.node((1, 1), $bb(H)^2 ( X \, R p r_(1 \*)^j mu_n )$),
  fletcher.edge((0, 0), (1, 0), "->", $partial$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $\| \| ( 1 )$, label-side: left),
  fletcher.edge((1, 0), (1, 1), "->", $\| \|$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $partial$, label-side: right),
)
