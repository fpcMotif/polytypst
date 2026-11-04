#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.6em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $T(S^1, i)$),
  fletcher.node((2, 0), $S^1 times RR^1$),
  fletcher.node((1, 1), $S_1$),
  fletcher.node((3.2, 0.5), $[pi'(a, b) = a]$),
  fletcher.edge((0, 0), (2, 0), "->", $f_1$),
  fletcher.edge((0, 0), (1, 1), "->", $pi$, label-side: right),
  fletcher.edge((2, 0), (1, 1), "->", $pi'$, label-side: left),
)
