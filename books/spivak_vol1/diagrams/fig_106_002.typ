#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (5em, 4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $(T M)|U$),
  fletcher.node((1, 0), $epsilon^n (RR^n)|x(U)$),
  fletcher.node((0, 1), $(T M)|V$),
  fletcher.node((1, 1), $epsilon^n (RR^n)|y(V)$),
  fletcher.edge((0, 0), (1, 0), "->", $alpha_x$),
  fletcher.edge((0, 1), (1, 1), "->", $alpha_y$, label-side: right),
  fletcher.edge((0, 1), (0, 0), "->", $subset$, label-side: right),
  fletcher.edge((1, 1), (1, 0), "->", $subset$, label-side: right),
)
