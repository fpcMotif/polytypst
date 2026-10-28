#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (2.6em, 1.9em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A]),
  node((1, 0), [A′]),
  node((0, 1), [S#super[−1]A]),
  node((1, 1), [S#super[−1]A′]),
  edge((0, 0), (1, 0), "->", [_h_]),
  edge((0, 1), (1, 1), "->", [_h_#sub[1]], label-side: right),
  edge((0, 0), (0, 1), "->", [_i_], label-side: right),
  edge((1, 0), (1, 1), "->", [_i_′], label-side: left),
)
