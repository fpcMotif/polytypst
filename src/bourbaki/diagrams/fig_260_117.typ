#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (4em, 2.2em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [$frak(a)$#sub[_k_] ⊗#sub[A] M]),
  node((1, 0), [$frak(a)$ ⊗#sub[A] M]),
  node((2, 0), [($frak(a)$\/$frak(a)$#sub[_k_]) ⊗#sub[A] M]),
  node((3, 0), [0]),
  node((1, 1), [M]),
  node((2, 1), [(A\/$frak(J)$#super(typographic: false)[_k_]) ⊗#sub[A] M]),
  edge((0, 0), (1, 0), "->", [_i_ ⊗ 1#sub[M]]),
  edge((1, 0), (2, 0), "->", [_p_ ⊗ 1#sub[M]]),
  edge((2, 0), (3, 0), "->"),
  edge((1, 1), (2, 1), "->"),
  edge((1, 0), (1, 1), "->", [_j_], label-side: right),
  edge((2, 0), (2, 1), "->", [_h_ ⊗ 1#sub[M]], label-side: left),
)
