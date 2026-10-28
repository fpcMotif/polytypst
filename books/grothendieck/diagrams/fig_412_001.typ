#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $B = Gamma ( frak(Y) \, cal(O)_(frak(Y)) )$),
  fletcher.node((1, 0), $Gamma ( frak(X) \, cal(O)_(frak(X)) ) = A$),
  fletcher.node((0, 1), $B_(( g )) = Gamma ( frak(D) ( g ) \, cal(O)_(frak(Y)) )$),
  fletcher.node((1, 1), $Gamma ( frak(D) ( phi ( g ) ) \, cal(O)_(frak(X)) ) = A_(( phi ( g ) ))$),
  fletcher.edge((0, 0), (1, 0), "->", $phi$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $Gamma ( theta_(frak(D) ( g )) )$, label-side: right),
)
