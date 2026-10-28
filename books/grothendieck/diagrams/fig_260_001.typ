#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X times_Y Y'$),
  fletcher.node((1, 0), $Y times_Y Y' = Y'$),
  fletcher.node((0, 1), $X times_S Y'$),
  fletcher.node((1, 1), $Y times_S Y'$),
  fletcher.edge((0, 0), (1, 0), "->", $f times 1_(Y')$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $f_((Y'))$, label-side: right),
)
