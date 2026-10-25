#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $X$),
  fletcher.node((1, 0), $X_((phi))$),
  fletcher.node((2, 0), $(X_((phi)))_((phi'))$),
  fletcher.node((0, 1), $S$),
  fletcher.node((1, 1), $S'$),
  fletcher.node((2, 1), $S''$),
  fletcher.edge((1, 0), (0, 0), "->", $p$, label-side: right),
  fletcher.edge((2, 0), (1, 0), "->", $p'$, label-side: right),
  fletcher.edge((0, 0), (0, 1), "->", $pi$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $pi'$, label-side: right),
  fletcher.edge((2, 0), (2, 1), "->", $pi''$, label-side: right),
  fletcher.edge((1, 1), (0, 1), "->", $phi$, label-side: left),
  fletcher.edge((2, 1), (1, 1), "->", $phi'$, label-side: left),
)
