#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright("gr")^compose ( M ) \u{2297}_(upright("gr")^compose ( A )) upright("gr")^bullet ( A )$),
  fletcher.node((1, 0), $upright("gr")^compose ( N ) \u{2297}_(upright("gr")^compose ( A )) upright("gr")^bullet ( A )$),
  fletcher.node((0, 1), $upright("gr")^bullet ( M )$),
  fletcher.node((1, 1), $upright("gr")^bullet ( N )$),
  fletcher.edge((0, 0), (1, 0), "->", $upright("gr")^compose ( u ) \u{2297} 1$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $phi_M$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $phi_N$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $upright("gr") ( u )$, label-side: right),
)
