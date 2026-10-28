#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $A$),
  fletcher.node((1, 0), $B$),
  fletcher.node((0, 1), $C$),
  fletcher.node((1, 1), $D$),
  fletcher.edge((0, 0), (1, 0), "->", $f$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $u$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $v$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $g$, label-side: right),
)
