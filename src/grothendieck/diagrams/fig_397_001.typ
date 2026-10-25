#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright(bold(G r a s s))_n ( cal(E)' )$),
  fletcher.node((1, 0), $upright(bold(P)) (limits(and)^n cal(E)')$),
  fletcher.node((0, 1), $upright(bold(G r a s s))_n ( cal(E) )$),
  fletcher.node((1, 1), $upright(bold(P)) (limits(and)^n cal(E))$),
  fletcher.edge((0, 0), (1, 0), "->", $pi.alt_(cal(E)')$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $upright(bold(G r a s s))_n ( g )$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $upright(bold(G r a s s))_1 (limits(and)^n g)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $pi.alt_(cal(E))$, label-side: right),
)
