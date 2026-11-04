#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (3.2em, 2.6em),
  label-size: 0.85em,
  fletcher.node((0, 0), $i_* ([x, v]_p) = [I, D(i compose x^(-1))(x(p))(v)]_(i(p))$),
  fletcher.node((0, 1), $(i(p), D(i compose x^(-1))(x(p))(v)) in (M, i)_p;$),
  fletcher.node((1.3, 0), $"by (c)"$),
  fletcher.edge((0, 0), (0, 1), "->", $t^n = t_I$, label-side: right),
)
