#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright("Drap")_m ( cal(E)' )$),
  fletcher.node((1, 0), $limits(product)_(1 lt.eq i lt.eq p) upright("Grass")_(m_i) ( cal(E)' )$),
  fletcher.node((0, 1), $upright("Drap")_m ( cal(E) )$),
  fletcher.node((1, 1), $limits(product)_(1 lt.eq i lt.eq p) upright("Grass")_(m_i) ( cal(E) )$),
  fletcher.edge((0, 0), (1, 0), "->", $i_(cal(E)')$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $upright("Drap")_m ( u )$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $limits(product)_i upright("Grass")_(m_i) ( u )$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $i_(cal(E))$, label-side: right),
)
