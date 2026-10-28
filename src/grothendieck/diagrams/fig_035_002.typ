#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X times_S Y$),
  fletcher.node((1, 0), $X' times_S Y$),
  fletcher.node((2, 0), $X'' times_S Y$),
  fletcher.node((0, 1), $X$),
  fletcher.node((1, 1), $X'$),
  fletcher.node((2, 1), $X''$),
  fletcher.edge((0, 0), (1, 0), "->", $f times_S 1_Y$, label-side: left),
  fletcher.edge((1, 0), (2, 0), "->", $f' times_S 1_Y$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $p$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $p'$, label-side: right),
  fletcher.edge((2, 0), (2, 1), "->", $p''$, label-side: right),
  fletcher.edge((0, 1), (1, 1), "->", $f$, label-side: right),
  fletcher.edge((1, 1), (2, 1), "->", $f'$, label-side: right),
)
