#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3em, 1.9em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A]),
  node((1, 0), [B]),
  node((0, 1), [A[S#super[−1]]]),
  node((1, 1), [B[T#super[−1]]]),
  edge((0, 0), (1, 0), "->", [_f_]),
  edge((0, 1), (1, 1), "->", [_f_′], label-side: right),
  edge((0, 0), (0, 1), "->", $attach(italic(#[i]), t: #[S], b: #[A])$, label-side: left),
  edge((1, 0), (1, 1), "->", $attach(italic(#[i]), t: #[T], b: #[B])$, label-side: left),
)
