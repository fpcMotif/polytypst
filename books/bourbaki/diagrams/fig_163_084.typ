#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (1.6em, 1.8em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A#emph[s]]),
  node((1, 0), [N/$cal(F)$N]),
  node((0, 1), [$frak(m)$]),
  node((1, 1), [P/$cal(F)$P]),
  edge((0, 0), (1, 0), "->", [_v_]),
  edge((0, 1), (1, 1), "->", [_u_], label-side: right),
  edge((0, 0), (0, 1), "->", [_i_], label-side: right),
  edge((1, 0), (1, 1), "->", [_p_′], label-side: left),
)
