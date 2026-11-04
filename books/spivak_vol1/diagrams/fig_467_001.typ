#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (4.2em, 2.2em),
  label-size: 0.85em,
  fletcher.node((0, 0), $H_c^k (D - S)$),
  fletcher.node((1, 0), $H^k (D)$),
  fletcher.node((2, 0), $H^k (S)$),
  fletcher.node((1, 1.7), $H^k (M)$),
  fletcher.edge((0, 0), (1, 0), "->", $e$),
  fletcher.edge((1, 0), (2, 0), "->", $i^*$),
  fletcher.edge((0, 0), (1, 1.7), "->", $s^*$, label-side: right),
  fletcher.edge((1, 0), (1, 1.7), "->", $overline(s)_*$, label-side: right, shift: -3pt),
  fletcher.edge((1, 1.7), (1, 0), "->", $(pi|D)^*$, label-side: right, shift: -3pt),
  fletcher.edge((1, 1.7), (2, 0), "->", $pi_0^*$, label-side: right),
)
