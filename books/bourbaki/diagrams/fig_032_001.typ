#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (1.3em, 1.9em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A]),
  node((1, 0), [B]),
  node((2, 0), [C]),
  node((1, 1), [D]),
  node((2, 1), [E]),
  edge((0, 0), (1, 0), "->", [_f_]),
  edge((1, 0), (2, 0), "->", [_g_]),
  edge((1, 0), (1, 1), "->", [_u_], label-side: right),
  edge((2, 0), (2, 1), "->", [_v_], label-side: right),
  edge((1, 1), (2, 1), "->", [_h_], label-side: right),
)
