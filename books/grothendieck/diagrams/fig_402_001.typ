#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright(bold(P)) ( cal(E)' ) times_S upright(bold(P)) ( cal(F)' )$),
  fletcher.node((1, 0), $upright(bold(P)) \( cal(E)' \u{2297}_(cal(O)_S) cal(F)' \)$),
  fletcher.node((0, 1), $upright(bold(P)) ( cal(E) ) times_S upright(bold(P)) ( cal(F) )$),
  fletcher.node((1, 1), $upright(bold(P)) \( cal(E) \u{2297}_(cal(O)_S) cal(F) \)$),
  fletcher.edge((0, 0), (1, 0), "->", $zeta_(cal(E)' \, cal(F)')$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $upright(bold("Grass"))_1 ( g ) times_S upright(bold("Grass"))_1 ( h )$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $upright(bold("Grass"))_1 ( g \u{2297} h )$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $zeta_(cal(E) \, cal(F))$, label-side: right),
)
