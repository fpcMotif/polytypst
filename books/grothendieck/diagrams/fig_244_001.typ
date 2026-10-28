#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $"Spec"(kappa(x))$),
  fletcher.node((1, 0), $"Spec"(kappa(x_i))$),
  fletcher.node((0, 1), $X$),
  fletcher.node((1, 1), $X_i$),
  fletcher.edge((0, 0), (1, 0), "->", $q_i$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $j$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $g_i$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $p_i$, label-side: right),
)
