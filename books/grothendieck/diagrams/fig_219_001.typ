#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $A$),
  fletcher.node((1, 0), $Gamma(X, cal(O)_X)$),
  fletcher.node((0, 1), $A_(psi(x))$),
  fletcher.node((1, 1), $cal(O)_x$),
  fletcher.edge((0, 0), (1, 0), "->", $phi$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->"),
  fletcher.edge((1, 0), (1, 1), "->"),
  fletcher.edge((0, 1), (1, 1), "->", $theta_x^(\u{266F})$, label-side: right),
)
