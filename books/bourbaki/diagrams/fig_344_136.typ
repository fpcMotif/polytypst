#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (2.0em, 2.0em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A]),
  node((1, 0), [S#super[−1]A]),
  node((0, 1), [R]),
  node((1, 1), [S#super[−1]R]),
  edge((0, 0), (1, 0), "->", [$i_upright(A)^upright(S)$]),
  edge((0, 1), (1, 1), "->", [$i_upright(R)^upright(S)$], label-side: right),
  edge((0, 0), (0, 1), "->", [_h_], label-side: right),
  edge((1, 0), (1, 1), "->", [S#super[−1]_h_], label-side: left),
)
