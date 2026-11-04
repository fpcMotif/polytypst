#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.4em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $T U$),
  fletcher.node((2, 0), $T M$),
  fletcher.node((1, 1), $(T M)|U$),
  fletcher.edge((0, 0), (2, 0), "->", $i_*$),
  fletcher.edge((0, 0), (1, 1), "->", $tilde.eq$, label-side: right),
  fletcher.edge((1, 1), (2, 0), "->", $subset$, label-side: right),
  fletcher.node((4, 0), $T U$),
  fletcher.node((6, 0), $T N$),
  fletcher.node((5, 1), $T M$),
  fletcher.edge((4, 0), (6, 0), "->", $(f|U)_*$),
  fletcher.edge((4, 0), (5, 1), "->", $i_*$, label-side: right),
  fletcher.edge((5, 1), (6, 0), "->", $f_*$, label-side: right),
)
