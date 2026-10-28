#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3.2em, 2.2em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [M]),
  node((1, 0), [M\/N′]),
  node((0, 1), [S#super[−1]M]),
  node((1, 1), [S#super[−1]\(M\/N′)]),
  edge((0, 0), (1, 0), "->", [_p_]),
  edge((0, 1), (1, 1), "->", [S#super[−1]_p_], label-side: right),
  edge((0, 0), (0, 1), "->", [_u_], label-side: right),
  edge((1, 0), (1, 1), "->", [_v_], label-side: left),
)
