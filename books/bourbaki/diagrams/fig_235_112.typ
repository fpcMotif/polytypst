#import "@preview/fletcher:0.5.8": diagram, node, edge
#diagram(
  spacing: (1.6em, 1.8em),
  node-inset: 3pt,
  label-size: 0.7em,
  label-sep: 0.15em,
  node((0, 0), [A/$frak(n)^k$]),
  node((1, 0), [$#[A]_frak(n)$/($frak(n)#[A]_frak(n))^k$]),
  node((0, 1), [Â/$hat(frak(n))^k$]),
  node((1, 1), [$#[Â]_hat(frak(n))$/($hat(frak(n))#[Â]_hat(frak(n)))^k$]),
  edge((0, 0), (1, 0), "->"),
  edge((0, 1), (1, 1), "->"),
  edge((0, 0), (0, 1), "->", [_h_], label-side: right),
  edge((1, 0), (1, 1), "->", [_h_′], label-side: left),
)
