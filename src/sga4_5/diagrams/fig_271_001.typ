#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $Z'$),
  fletcher.node((1, 0), $X'$),
  fletcher.node((2, 0), $Y'$),
  fletcher.node((0, 1), $X limits(arrow.r.long)^u Y$),
  fletcher.node((1, 1), $Y limits(arrow.r.long)^v Z$),
  fletcher.node((2, 1), $X limits(arrow.r.long)^w Z$),
  fletcher.edge((0, 0), (0, 1), "->", $deg 1$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $i$, label-side: left),
  fletcher.edge((2, 0), (2, 1), "->"),
)
