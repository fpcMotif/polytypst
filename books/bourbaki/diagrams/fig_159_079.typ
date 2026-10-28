#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (1.6em, 1.8em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [P]),
  node((1, 0), [M]),
  node((0, 1), [Q]),
  node((1, 1), [$#[M]_cal(F)$]),
  edge((0, 0), (1, 0), "->", [_u_]),
  edge((0, 1), (1, 1), "->", [_v_], label-side: right),
  edge((0, 0), (0, 1), "->", [_h_], label-side: right),
  edge((1, 0), (1, 1), "->", [_j_#sub[M]], label-side: left),
)
