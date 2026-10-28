#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $cal(C) \u{2297}_(cal(A)) cal(C) \u{2297}_(cal(A)) cal(C)$),
  fletcher.node((1, 0), $cal(C) \u{2297}_(cal(A)) cal(C)$),
  fletcher.node((0, 1), $cal(C) \u{2297}_(cal(A)) cal(C)$),
  fletcher.node((1, 1), $cal(C)$),
  fletcher.edge((0, 0), (1, 0), "->", $phi times.o 1$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $1 times.o phi$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $phi$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $phi$, label-side: right),
)
