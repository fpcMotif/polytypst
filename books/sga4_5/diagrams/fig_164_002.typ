#import "@preview/fletcher:0.5.8" as fletcher

#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $0 arrow.r.long upright(H)^0 ( X \, A ) arrow.r.long upright(H)^0 ( X \, bb(F) ) arrow.r.long upright(H)^0 ( X \, G ) arrow.r.long 0$),
  fletcher.node((0, 1), $0 arrow.r.long upright(H)^(- 1) ( X \, bb(F) ) arrow.r.long upright(H)^(- 1) ( X \, G ) arrow.r.long upright(H)^0 ( X \, A ) arrow.r.long upright(H)^0 ( X \, bb(F) ) arrow.r.long upright(H)^0 ( X \, G )$),
  fletcher.edge((0, 0), (0, 1), "->", $quad quad quad quad arrow.b quad quad quad arrow.b$, label-side: left),
)
