#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright(H)^i ( X \, f_(\*) bb(F) )$),
  fletcher.node((1, 0), $upright(H)^i ( X \, f_(\*) bb(F) )$),
  fletcher.node((0, 1), $upright(H)^i ( X' \, bb(F) )$),
  fletcher.node((1, 1), $upright(H)^i ( X' \, bb(F) )$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $parallel$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $parallel$, label-side: right),
  fletcher.edge((0, 1), (1, 1), "->"),
)
