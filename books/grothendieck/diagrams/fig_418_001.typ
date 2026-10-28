#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $( frak(X) \, cal(O)_(frak(X)) )$),
  fletcher.node((1, 0), $( frak(Y) \, cal(O)_(frak(Y)) )$),
  fletcher.node((0, 1), $( frak(X) \, cal(O)_(frak(X)) \/ cal(J) )$),
  fletcher.node((1, 1), $( frak(Y) \, cal(O)_(frak(Y)) \/ cal(K) )$),
  fletcher.edge((0, 0), (1, 0), "->", $f$, label-side: left),
  fletcher.edge((0, 1), (0, 0), "->"),
  fletcher.edge((1, 1), (1, 0), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $f'$, label-side: right),
)
