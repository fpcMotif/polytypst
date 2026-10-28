#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright("Hom")_(bold(C))(S, Y)$),
  fletcher.node((1, 0), $upright("Hom")_(bold(C)')(F(S), X')$),
  fletcher.node((0, 1), $upright("Hom")_(bold(C))(T, Y)$),
  fletcher.node((1, 1), $upright("Hom")_(bold(C)')(F(T), X')$),
  fletcher.edge((0, 0), (1, 0), "->", $tilde$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $upright("Hom")(w, 1_Y)$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $upright("Hom")(F(w), 1_(X'))$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $tilde$, label-side: right),
)
