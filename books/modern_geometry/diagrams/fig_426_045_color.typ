#import "@preview/fletcher:0.5.8": diagram, node, edge

#diagram(
  axes: (ltr, btt),
  spacing: (2.5em, 2.5em),
  node-inset: 2pt,
  label-size: 11pt,
  
  // Axes in slate
  edge((-0.1, 0), (3.8, 0), "-|>", stroke: 1pt + rgb("#334155")),
  node((3.95, 0), text(fill: rgb("#1e293b"), font: "Times New Roman", math.italic("x"))),
  edge((0, -0.1), (0, 3.4), "-|>", stroke: 1pt + rgb("#334155")),
  node((0, 3.55), text(fill: rgb("#1e293b"), font: "Times New Roman", math.italic("y"))),
  node((-0.15, -0.15), text(fill: rgb("#334155"), font: "Times New Roman", math.italic("O"))),

  // Curve gamma in royal blue
  edge((1.1, 2.0), (2.4, 0.7), bend: 40deg, stroke: 2.2pt + rgb("#2563eb")),
  node((2.55, 0.7), text(fill: rgb("#1d4ed8"), weight: "bold", math.gamma)),

  // Point P on curve with gold center and navy border
  node((1.98, 1.62), shape: circle, radius: 3pt, stroke: 1.2pt + rgb("#1e293b"), fill: rgb("#fef08a")),

  // Tangent vector gamma-dot in emerald green
  edge((1.98, 1.62), (1.1, 2.5), "-|>", stroke: 1.4pt + rgb("#059669")),
  node((0.95, 2.7), text(fill: rgb("#047857"), weight: "bold", math.dot(math.gamma))),

  // Normal vector n in crimson red
  edge((1.98, 1.62), (3.1, 2.5), "-|>", stroke: 1.4pt + rgb("#dc2626")),
  node((3.25, 2.65), text(fill: rgb("#b91c1c"), weight: "bold", math.italic("n"))),

  // Dashed horizontal reference line in muted slate
  edge((1.98, 1.62), (3.8, 1.62), "--", stroke: (dash: "dashed", thickness: 0.8pt, paint: rgb("#94a3b8"))),

  // Angle arc theta in warm amber
  edge((2.78, 1.62), (2.66, 2.16), bend: -25deg, stroke: 1.1pt + rgb("#d97706")),
  node((2.95, 1.95), text(fill: rgb("#b45309"), weight: "bold", math.theta)),
)
