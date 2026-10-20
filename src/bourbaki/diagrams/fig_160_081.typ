#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (2.4em, 1.8em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A × M]),
  node((1, 0), [M]),
  node((0, 1), [$#[A]_cal(F)$ × $#[M]_cal(F)$]),
  node((1, 1), [$#[M]_cal(F)$]),
  edge((0, 0), (1, 0), "->", [$upright(phi.alt)$]),
  edge((0, 1), (1, 1), "->", [$upright(phi.alt)_cal(F)$], label-side: right),
  edge((0, 0), (0, 1), "->", [_j_#sub[A] × _j_#sub[M]], label-side: right),
  edge((1, 0), (1, 1), "->", [_j_#sub[M]], label-side: left),
)
