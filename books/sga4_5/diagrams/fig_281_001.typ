#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $Y$),
  fletcher.node((0, 1), $Z limits(arrow.r.long)^f X$),
  fletcher.edge((0, 0), (0, 1), "->", $f$, label-side: left),
)
