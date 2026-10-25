#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright(bold(G L)) ( cal(E) ) times_S upright(bold(S t i e f))_p ( cal(E) )$),
  fletcher.node((1, 0), $upright(bold(S t i e f))_p ( cal(E) )$),
  fletcher.node((0, 1), $upright(bold(G L)) ( cal(E) ) times_S upright(bold(D r a p))_m ( cal(E) )$),
  fletcher.node((1, 1), $upright(bold(D r a p))_m ( cal(E) )$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->"),
)
