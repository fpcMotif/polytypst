#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3em, 1.6em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [M]),
  node((1, 0), [S#super[−1]M]),
  node((0, 1), [(ST)#super[−1]M]),
  node((1, 1), [T′#super[−1];(S#super[−1]M)]),
  edge((0, 0), (1, 0), "->", $attach(italic(#[i]), t: #[S], b: #[M])$),
  edge((0, 1), (1, 1), "->", [_k_], label-side: right),
  edge((0, 0), (0, 1), "->", $attach(italic(#[i]), t: #[ST], b: #[A])$, label-side: right),
  edge((1, 0), (1, 1), "->", $attach(italic(#[i]), t: #[T′], b: #[S#super[−1]M])$, label-side: left),
)
