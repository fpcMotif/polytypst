#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $V$),
  fletcher.node((1, 0), $V^*$),
  fletcher.node((0, 1), $W$),
  fletcher.node((1, 1), $W^*$),
  fletcher.edge((0, 0), (1, 0), "->", $i_V$),
  fletcher.edge((0, 0), (0, 1), "->", $f$, label-side: right),
  fletcher.edge((1, 1), (1, 0), "->", $f^*$, label-side: right),
  fletcher.edge((0, 1), (1, 1), "->", $i_W$),
)
