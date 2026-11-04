#import "@preview/fletcher:0.5.8" as fletcher
#let path(top, down-first, down-second) = fletcher.diagram(
  spacing: (1.8em, 1.6em),
  label-size: 0.85em,
  fletcher.node((2, 0.5), $=$),
  fletcher.edge((0, 0), (1, 0), "->", top),
  fletcher.edge((1, 0), (1, 1), "->", down-first, label-side: right),
  fletcher.edge((3, 0), (3, 1), "->", down-second, label-side: left),
  fletcher.edge((3, 1), (4, 1), "->", top, label-side: right),
)
#grid(
  columns: 2,
  column-gutter: 4em,
  row-gutter: 1.2em,
  align: (left + horizon, center + horizon),
  $(d plus.o d) compose alpha = alpha compose d$, path($alpha$, $d plus.o d$, $d$),
  $d compose beta = beta compose (d plus.o d)$, path($beta$, $d$, $d plus.o d$),
)
