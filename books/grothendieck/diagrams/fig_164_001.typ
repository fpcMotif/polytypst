#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $upright("gr")^compose ( M ) \u{2297}_(upright("gr")^compose ( A )) upright("gr")^bullet ( A )$),
  fletcher.node((1, 0), $upright("gr")^bullet ( M )$),
  fletcher.node((0, 1), $upright("gr")_(frak(J))^compose ( N_lambda ) \u{2297}_(upright("gr")_(frak(J))^compose ( B_lambda )) upright("gr")_(frak(J))^bullet ( B_lambda )$),
  fletcher.node((1, 1), $upright("gr")_(frak(J))^bullet ( N_lambda )$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $f_lambda$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $g_lambda$, label-side: right),
  fletcher.edge((0, 1), (1, 1), "->"),
)
