#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $T M$),
  fletcher.node((1, 0), $T N$),
  fletcher.node((0, 1), $T' M$),
  fletcher.node((1, 1), $T' N$),
  fletcher.edge((0, 0), (1, 0), "->", $f_*$),
  fletcher.edge((0, 0), (0, 1), "->", $e_M$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $e_N$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $f_sharp$),
)
