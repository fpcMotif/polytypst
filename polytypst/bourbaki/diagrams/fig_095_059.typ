#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3.1em, 1.9em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A]),
  node((1, 0), [S#super[−1]A]),
  node((0, 1), [(ST)#super[−1]A]),
  node((1, 1), [T′#super[−1];(S#super[−1]A)]),
  edge((0, 0), (1, 0), "->", $attach(italic(#[i]), t: #[S], b: #[A])$),
  edge((0, 1), (1, 1), "->", [_j_], label-side: right),
  edge((0, 0), (0, 1), "->", $attach(italic(#[i]), t: #[ST], b: #[M])$, label-side: right),
  edge((1, 0), (1, 1), "->", $attach(italic(#[i]), t: #[T′], b: #[S#super[−1]A])$, label-side: left),
)
