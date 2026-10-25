#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $( psi_(\*) ( cal(F)_1 ) )_(psi ( x ))$),
  fletcher.node((1, 0), $( cal(F)_1 )_x$),
  fletcher.node((0, 1), $( psi_(\*) ( cal(F)_2 ) )_(psi ( x ))$),
  fletcher.node((1, 1), $( cal(F)_2 )_x$),
  fletcher.edge((0, 0), (1, 0), "->", $psi_x$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $( psi_(\*) ( u ) )_(psi ( x ))$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $u_x$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $psi_x$, label-side: right),
)
