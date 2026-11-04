#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 0.4em),
  node-inset: 3pt,
  label-size: 0.85em,
  fletcher.node((0, 0), $(x, y)$),
  fletcher.node((1, 0), $x - y$),
  fletcher.node((2, 0), $x y^(-1)$),
  fletcher.node((0, 1), rotate(90deg, $in$)),
  fletcher.node((1, 1), rotate(90deg, $in$)),
  fletcher.node((2, 1), rotate(90deg, $in$)),
  fletcher.node((0, 2), $RR times RR$),
  fletcher.node((1, 2), $RR$),
  fletcher.node((2, 2), $S^1 = RR slash ZZ.$),
  fletcher.edge((0, 0), (1, 0), "|->"),
  fletcher.edge((1, 0), (2, 0), "|->"),
  fletcher.edge((0, 2), (1, 2), "->"),
  fletcher.edge((1, 2), (2, 2), "->"),
)
