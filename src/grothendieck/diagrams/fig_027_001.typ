#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright(bold(h))_X ( Y' )$),
  fletcher.node((1, 0), $upright(bold(h))_X ( Y )$),
  fletcher.node((0, 1), $upright(bold(h))_(X') ( Y' )$),
  fletcher.node((1, 1), $upright(bold(h))_(X') ( Y )$),
  fletcher.edge((0, 0), (1, 0), "->", $upright(bold(h))_X ( u )$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $upright(bold(h))_w ( Y' )$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $upright(bold(h))_w ( Y )$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $upright(bold(h))_(X') ( u )$, label-side: right),
)
