#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $cal(G) ( V )$),
  fletcher.node((1, 0), $cal(F) ( U )$),
  fletcher.node((0, 1), $cal(G) ( V' )$),
  fletcher.node((1, 1), $cal(F) ( U' )$),
  fletcher.edge((0, 0), (1, 0), "->", $u_(U \, V)$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $u_(U' \, V')$, label-side: right),
)
