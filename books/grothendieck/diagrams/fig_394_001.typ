#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright("Grass")_n \( cal(E)'_(( T )) \)$),
  fletcher.node((1, 0), $upright("Grass")_n \( cal(E)_(( T )) \)$),
  fletcher.node((0, 1), $upright("Grass")_n \( cal(E)'_(( T' )) \)$),
  fletcher.node((1, 1), $upright("Grass")_n \( cal(E)_(( T' )) \)$),
  fletcher.edge((0, 0), (1, 0), "->", $i_(g_(( T )))$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $i_(g_(( T' )))$, label-side: right),
)
