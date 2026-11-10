#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (6em, 3em),
  label-size: 0.85em,
  fletcher.node((0.5, 0), $T RR^n$),
  fletcher.node((0, 1), $T A'$),
  fletcher.node((1, 1), $(T RR^n)|A'$),
  fletcher.edge((0, 1), (0.5, 0), "->", $(j compose i)_*$, label-side: left),
  fletcher.edge((1, 1), (0.5, 0), "->", $subset$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $tilde.eq$),
)
