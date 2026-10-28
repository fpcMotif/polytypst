#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $( frak(I)^n \/ frak(I)^(n + 1) ) \u{2297}_(A \/ frak(I)) ( M \/ frak(I) M )$),
  fletcher.node((1, 0), $frak(I)^n M \/ frak(I)^(n + 1) M$),
  fletcher.node((0, 1), $( frak(I)^n \/ frak(I)^(n + 1) ) \u{2297}_(A \/ frak(I)) ( M \/ frak(I) M )$),
  fletcher.node((1, 1), $med frak(I)^n M \/ frak(I)^(n + 1) M$),
  fletcher.edge((0, 0), (1, 0), "->"),
  fletcher.edge((0, 0), (0, 1), "->", $1 times.o upright("gr")^compose ( w )$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $upright("gr")^n ( w )$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->"),
)
