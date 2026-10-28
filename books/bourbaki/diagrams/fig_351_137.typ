#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3.1em, 2.2em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A]),
  node((1, 0), [B]),
  node((0, 1), [A[X, X#super[−1]]]),
  node((1, 1), [B[X, X#super[−1]]]),
  edge((0, 0), (1, 0), "->", [$upright(rho)$]),
  edge((0, 1), (1, 1), "->", [$upright(rho)$′], label-side: right),
  edge((0, 0), (0, 1), "->", [_j_#sub[A]], label-side: right),
  edge((1, 0), (1, 1), "->", [_j_#sub[B]], label-side: left),
)
