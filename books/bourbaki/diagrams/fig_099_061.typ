#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3.8em, 1.6em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [M]),
  node((1, 0), [M/N]),
  node((0, 1), [S#super[−1]M]),
  node((1, 1), [S#super[−1]M/S#super[−1]N]),
  edge((0, 0), (1, 0), "->", [_h_]),
  edge((0, 1), (1, 1), "->", [S#super[−1]_h_], label-side: right),
  edge((0, 0), (0, 1), "->", $attach(italic(#[i]), t: #[S], b: #[M])$, label-side: right),
  edge((1, 0), (1, 1), "->", $attach(italic(#[i]), t: #[S], b: #[M/N])$, label-side: left),
)
