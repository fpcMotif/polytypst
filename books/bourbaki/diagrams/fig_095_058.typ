#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3.5em, 1.9em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [S#super[−1]M]),
  node((1, 0), [S#super[−1]N]),
  node((0, 1), [T#super[−1]M]),
  node((1, 1), [T#super[−1]N]),
  edge((0, 0), (1, 0), "->", [S#super[−1]_u_]),
  edge((0, 1), (1, 1), "->", [T#super[−1]_u_], label-side: right),
  edge((0, 0), (0, 1), "->", $attach(italic(#[i]), t: #[T,S], b: #[M])$, label-side: right),
  edge((1, 0), (1, 1), "->", $attach(italic(#[i]), t: #[T,S], b: #[N])$, label-side: left),
)
