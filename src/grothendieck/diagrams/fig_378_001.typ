#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $R^(- 1) E$),
  fletcher.node((1, 0), $R'^(- 1) E$),
  fletcher.node((0, 1), $bold(S) ( R^(- 1) E )$),
  fletcher.node((1, 1), $bold(S) ( R'^(- 1) E )$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->"),
)
