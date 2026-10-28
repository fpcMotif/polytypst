#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X_(upright("red"))$),
  fletcher.node((1, 0), $X_(upright("red")) times_Y X_(upright("red"))$),
  fletcher.node((0, 1), $X$),
  fletcher.node((1, 1), $X times_Y X$),
  fletcher.edge((0, 0), (1, 0), "->", $Delta_(X_(upright("red")))$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $j$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $j times_Y j$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $Delta_X$, label-side: right),
)
