#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $H^1 ( X \, cal(O)_X^(\*) )$),
  fletcher.node((1, 0), $H^1 ( X' \, cal(O)_(X')^(\*) )$),
  fletcher.node((0, 1), $upright("Pic") ( X )$),
  fletcher.node((1, 1), $upright("Pic") ( X' )$),
  fletcher.edge((0, 0), (1, 0), "->", $H^1 ( u )$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $phi_X wreath$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $wreath quad phi_(X')$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $upright("Pic") ( u )$, label-side: right),
)
