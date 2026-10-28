#import "@preview/fletcher:0.5.8": diagram, node, edge

#diagram(
  spacing: (4.5em, 3.2em),
  node-inset: 5pt,
  label-size: 10pt,
  node((0, 0), text(fill: rgb("#1e3a8a"), weight: "bold", $T_x M$), fill: rgb("#eff6ff"), stroke: 0.8pt + rgb("#bfdbfe"), corner-radius: 4pt),
  node((1, 0), text(fill: rgb("#1e3a8a"), weight: "bold", $T_(F(x)) N$), fill: rgb("#eff6ff"), stroke: 0.8pt + rgb("#bfdbfe"), corner-radius: 4pt),
  node((0, 1), text(fill: rgb("#065f46"), weight: "bold", $M$), fill: rgb("#ecfdf5"), stroke: 0.8pt + rgb("#a7f3d0"), corner-radius: 4pt),
  node((1, 1), text(fill: rgb("#065f46"), weight: "bold", $N$), fill: rgb("#ecfdf5"), stroke: 0.8pt + rgb("#a7f3d0"), corner-radius: 4pt),
  edge((0, 0), (1, 0), "-|>", stroke: 1.2pt + rgb("#2563eb"), label: text(fill: rgb("#1d4ed8"), weight: "bold", $d F_x$), label-side: left),
  edge((0, 1), (1, 1), "-|>", stroke: 1.2pt + rgb("#059669"), label: text(fill: rgb("#047857"), weight: "bold", $F$), label-side: right),
  edge((0, 0), (0, 1), "-|>", stroke: 1pt + rgb("#64748b"), label: text(fill: rgb("#475569"), $pi_M$), label-side: right),
  edge((1, 0), (1, 1), "-|>", stroke: 1pt + rgb("#64748b"), label: text(fill: rgb("#475569"), $pi_N$), label-side: left),
)
