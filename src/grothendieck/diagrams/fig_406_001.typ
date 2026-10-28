#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright("Drap")_(bold(m)) \( cal(E)'_(( T )) \)$),
  fletcher.node((1, 0), $limits(product)_(1 lt.eq.slant i lt.eq.slant p) upright("Grass")_(m_i) \( cal(E)'_(( T )) \)$),
  fletcher.node((0, 1), $upright("Drap")_(bold(m)) \( cal(E)_(( T )) \)$),
  fletcher.node((1, 1), $limits(product)_(1 lt.eq.slant i lt.eq.slant p) upright("Grass")_(m_i) \( cal(E)_(( T )) \)$),
  fletcher.edge((0, 0), (1, 0), "->", $i_(cal(E)'_(( T )))$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $i_(u_(( T )))$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $i_(cal(E)_(( T )))$, label-side: right),
)
