#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $A$),
  fletcher.node((1, 0), $B_i$),
  fletcher.node((0, 1), $C$),
  fletcher.node((1, 1), $C_i$),
  fletcher.edge((0, 0), (1, 0), "->", $q_i$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $j$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $g_i$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $p_i$, label-side: right),
  fletcher.node((4, 0), $A$),
  fletcher.node((6, 0), $B$),
  fletcher.node((5, 0.7), $B_i$),
  fletcher.edge((4, 0), (6, 0), "->", $v$, label-side: left),
  fletcher.edge((4, 0), (5, 0.7), "->", $q_i$, label-side: right),
  fletcher.edge((6, 0), (5, 0.7), "->", $p'_i$, label-side: left),
)
