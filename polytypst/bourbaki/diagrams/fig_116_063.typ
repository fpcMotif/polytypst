#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (3.5em, 1.8em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [L]),
  node((1, 0), [M]),
  node((0, 1), [$limits(product)_iota$ ((A/$frak(p)_iota$) ⊗ L)]),
  node((1, 1), [$limits(product)_iota$ ((A/$frak(p)_iota$) ⊗ M)]),
  edge((0, 0), (1, 0), "->", [_v_]),
  edge((0, 1), (1, 1), "->", [_v_′], label-side: right),
  edge((0, 0), (0, 1), "->", [_u_], label-side: right),
  edge((1, 0), (1, 1), "->", [_u_′], label-side: left),
)
