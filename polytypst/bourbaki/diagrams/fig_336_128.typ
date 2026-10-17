#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (1.9em, 1.7em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A]),
  node((1, 0), [A′]),
  node((0, 1), [R]),
  node((1, 1), [R′]),
  edge((0, 0), (1, 0), "->", [_f_]),
  edge((0, 1), (1, 1), "->", [_g_]),
  edge((0, 0), (0, 1), "->"),
  edge((1, 0), (1, 1), "->"),
)
