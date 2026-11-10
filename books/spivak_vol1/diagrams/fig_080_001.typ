#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $T RR^n$),
  fletcher.node((1, 0), $T RR^m$),
  fletcher.node((0, 1), $RR^n$),
  fletcher.node((1, 1), $RR^m$),
  fletcher.node((2.3, 0.5), $pi compose f_* = f compose pi.$),
  fletcher.edge((0, 0), (1, 0), "->", $f_*$),
  fletcher.edge((0, 0), (0, 1), "->", $pi$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $pi$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $f$),
)
