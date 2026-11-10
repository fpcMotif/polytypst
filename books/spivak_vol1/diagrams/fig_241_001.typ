#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (6em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), [$k$-forms on $M$]),
  fletcher.node((1, 0), [$k$-forms on $N$]),
  fletcher.node((0, 1), [$l$-forms on $M$]),
  fletcher.node((1, 1), [$l$-forms on $M$]),
  fletcher.edge((1, 0), (0, 0), "->", $f^*$, label-side: right),
  fletcher.edge((0, 0), (0, 1), "->", $D$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $D$, label-side: left),
  fletcher.edge((1, 1), (0, 1), "->", $f^*$, label-side: right),
)
