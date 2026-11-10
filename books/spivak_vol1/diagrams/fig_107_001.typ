#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (4em, 3em),
  label-size: 0.85em,
  fletcher.node((0, 0), $T A$),
  fletcher.node((1, 0), $(T RR^n)|A$),
  fletcher.node((2, 0), $epsilon^n (RR)^n|A$),
  fletcher.node((0, 1), $T B$),
  fletcher.node((1, 1), $(T RR^m)|B$),
  fletcher.node((2, 1), $epsilon^m (RR)^m|B$),
  fletcher.edge((0, 0), (1, 0), "->", $tilde.eq$),
  fletcher.edge((1, 0), (2, 0), "->", $t^n|A$),
  fletcher.edge((0, 1), (1, 1), "->", $tilde.eq$),
  fletcher.edge((1, 1), (2, 1), "->", $t^m|B$),
  fletcher.edge((0, 0), (0, 1), "->", $f_*$, label-side: right),
  fletcher.edge((2, 0), (2, 1), "->", $"old" f_*$, label-side: left),
)
