#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright(R) Gamma ( X_(t') \, E \| X_(t') )$),
  fletcher.node((1, 0), $upright(R) Gamma ( X_(s') \, E \| X_(s') )$),
  fletcher.node((0, 1), $upright(R) Gamma ( X'_(t') \, E \| X'_(t') )$),
  fletcher.node((1, 1), $upright(R) Gamma ( X'_(s') \, E \| X'_(s') )$),
  fletcher.edge((0, 0), (1, 0), "->", $op("cosp") ( u )$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $op("cosp") ( u' )$, label-side: right),
)
