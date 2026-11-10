#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (4.2em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $RR^k$),
  fletcher.node((1, 0), $F(V)$),
  fletcher.node((0, 1), $RR^k$),
  fletcher.edge((0, 0), (1, 0), "->", $F(bold(upright(e)) -> bold(upright(v)))$),
  fletcher.edge((0, 1), (0, 0), "->", $h(A)$, label-side: left),
  fletcher.edge((0, 1), (1, 0), "->", $F(bold(upright(e)) -> bold(upright(w)))$, label-side: right),
)
