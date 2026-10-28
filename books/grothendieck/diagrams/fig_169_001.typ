#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright("gr")^compose ( M ) \u{2297}_(upright("gr")^compose ( A )) upright("gr")^bullet ( A )$),
  fletcher.node((2, 0), $upright("gr")^bullet ( M )$),
  fletcher.node((1, 1), $upright("gr")^compose ( M ) \u{2297}_(upright("gr")^compose ( B )) upright("gr")^bullet ( B )$),
  fletcher.edge((0, 0), (2, 0), "->", $v$, label-side: left),
  fletcher.edge((0, 0), (1, 1), "->", $1 times.o u$, label-side: right),
  fletcher.edge((1, 1), (2, 0), "->", $w$, label-side: right),
)
