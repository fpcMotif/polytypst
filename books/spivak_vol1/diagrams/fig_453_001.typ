#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (1.4em, 1.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $H^1 (RR^2)$),
  fletcher.node((1, 0), $H^1 (M) plus.o H^1 (V)$),
  fletcher.node((2, 0), $H^1 (M inter V)$),
  fletcher.node((3, 0), $H^2 (RR^2),$),
  fletcher.node((0, 1), $0$),
  fletcher.node((1, 1), $0$),
  fletcher.node((3, 1), $0$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((1, 0), (2, 0), "->"),
  fletcher.edge((2, 0), (3, 0), "->"),
  fletcher.node((0, 0.5), $parallel$),
  fletcher.node((1, 0.5), $parallel$),
  fletcher.node((3, 0.5), $parallel$),
)
