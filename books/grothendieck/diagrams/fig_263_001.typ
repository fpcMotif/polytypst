#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $B = cal(O)_(X, x)$),
  fletcher.node((1, 0), $cal(O)_(X', x')$),
  fletcher.node((0, 1), $A = cal(O)_(Y, y)$),
  fletcher.node((1, 1), $cal(O)_(Y', y') = hat(A)$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 1), (0, 0), "->", $phi$, label-side: left),
  fletcher.edge((1, 1), (1, 0), "->", $v$, label-side: right),
  fletcher.edge((0, 1), (1, 1), "->", $u$, label-side: right),
)
