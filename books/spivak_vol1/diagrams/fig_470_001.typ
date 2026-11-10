#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.6em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $H^(k-1) (U inter V)$),
  fletcher.node((1, 0), $H^k (M)$),
  fletcher.node((0, 1), $H_c^(l+1) (U inter V)^*$),
  fletcher.node((1, 1), $H_c^l (M)^*$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $P D$, label-side: left),
  fletcher.edge((1, 0), (1, 1), "->", $P D$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->"),
)
