#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X times_Y X$),
  fletcher.node((1, 0), $X times_S X$),
  fletcher.node((0, 1), $Y$),
  fletcher.node((1, 1), $Y times_S Y$),
  fletcher.edge((0, 0), (1, 0), "->", $j$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $pi$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $f times_S f$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $Delta_Y$, label-side: right),
)
