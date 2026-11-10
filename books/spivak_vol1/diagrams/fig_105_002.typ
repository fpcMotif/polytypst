#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (1.8em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $(T' M)|U$),
  fletcher.node((1, 0), $T' U$),
  fletcher.node((2, 0), $T'(x(U))$),
  fletcher.node((3, 0), $(T RR^n)|x(U)$),
  fletcher.node((4, 0), $epsilon^n (RR^n)|x(U)$),
  fletcher.edge((1, 0), (0, 0), "->", $tilde.eq'$),
  fletcher.edge((1, 0), (2, 0), "->", $x_sharp$),
  fletcher.edge((2, 0), (3, 0), "->", $tilde.eq'$),
  fletcher.edge((3, 0), (4, 0), "->", $t'^n|x(U)$),
  fletcher.edge((0, 0), (4, 0), "->", $beta_x$, bend: -20deg, label-side: left),
)
