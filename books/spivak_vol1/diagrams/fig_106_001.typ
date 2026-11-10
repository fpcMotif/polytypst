#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 2.2em),
  label-size: 0.85em,
  fletcher.node((0, 0), $(T M)|U$),
  fletcher.node((1, 1), $T U$),
  fletcher.node((0, 2), $T M$),
  fletcher.node((1, 3), $T V$),
  fletcher.node((0, 4), $(T M)|V$),
  fletcher.edge((1, 1), (0, 0), "->", $tilde.eq$, label-side: right),
  fletcher.edge((0, 0), (0, 2), "->", $subset$, label-side: right),
  fletcher.edge((1, 1), (0, 2), "->", $i_*$, label-side: right),
  fletcher.edge((1, 3), (1, 1), "->", $j_*$, label-side: right),
  fletcher.edge((1, 3), (0, 2), "->", $overline(i)_*$, label-side: left),
  fletcher.edge((0, 4), (0, 2), "->", $subset$, label-side: right),
  fletcher.edge((1, 3), (0, 4), "->", $tilde.eq$, label-side: left),
)
