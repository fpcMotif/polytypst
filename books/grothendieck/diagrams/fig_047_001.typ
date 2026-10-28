#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $F(F^(upright("ad"))(X'_1))$),
  fletcher.node((1, 0), $F(F^(upright("ad"))(X'_2))$),
  fletcher.node((0, 1), $X'_1$),
  fletcher.node((1, 1), $X'_2$),
  fletcher.edge((0, 0), (1, 0), "->", $F(F^(upright("ad"))(u'))$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $sigma_(X'_1)$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $sigma_(X'_2)$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $u'$, label-side: right),
)
