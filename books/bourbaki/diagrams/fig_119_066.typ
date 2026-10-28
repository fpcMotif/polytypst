#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (2.2em, 1.8em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [M]),
  node((1, 0), [K ⊗#sub[A] M]),
  node((0, 1), [$#[M]_frak(m)$]),
  node((1, 1), [(K ⊗#sub[A] $#[M])_frak(m)$]),
  edge((0, 0), (1, 0), "->"),
  edge((0, 1), (1, 1), "->"),
  edge((0, 0), (0, 1), "->"),
  edge((1, 0), (1, 1), "->"),
)
