#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (6em, 2em),
  label-size: 0.85em,
  fletcher.node((0, 0), $"Hom"_S (X, Y)$),
  fletcher.node((1, 0), $"Hom"_(S') (X', Y')$),
  fletcher.node((2, 0), $"Hom"_(S'') (X'', Y'')$),
  fletcher.edge((0, 0), (1, 0), "->", $alpha^*$, label-side: left),
  fletcher.edge((1, 0), (2, 0), "->", shift: 3pt, $p_1^*$, label-side: left),
  fletcher.edge((1, 0), (2, 0), "->", shift: -3pt, $p_2^*$, label-side: right),
)
