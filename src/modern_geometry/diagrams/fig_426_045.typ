#import "@preview/fletcher:0.5.8": diagram, node, edge

#diagram(
  axes: (ltr, btt),
  spacing: (2.5em, 2.5em),
  node-inset: 2pt,
  label-size: 11pt,
  
  // Axes
  edge((-0.1, 0), (3.8, 0), "-|>", stroke: 0.8pt),
  node((3.95, 0), math.italic("x")),
  edge((0, -0.1), (0, 3.4), "-|>", stroke: 0.8pt),
  node((0, 3.55), math.italic("y")),
  node((-0.15, -0.15), math.italic("O")),

  // Smooth Curve gamma
  edge((1.1, 2.0), (2.4, 0.7), bend: 40deg, stroke: 1.8pt),
  node((2.55, 0.7), math.gamma),

  // Point P on curve
  node((1.98, 1.62), shape: circle, radius: 2.2pt, stroke: 0.9pt, fill: white),

  // Tangent vector gamma-dot
  edge((1.98, 1.62), (1.1, 2.5), "-|>", stroke: 1.1pt),
  node((0.95, 2.7), math.dot(math.gamma)),

  // Normal vector n
  edge((1.98, 1.62), (3.1, 2.5), "-|>", stroke: 1.1pt),
  node((3.25, 2.65), math.italic("n")),

  // Dashed horizontal reference line from P
  edge((1.98, 1.62), (3.8, 1.62), "--", stroke: (dash: "dashed", thickness: 0.6pt)),

  // Angle arc theta
  edge((2.78, 1.62), (2.66, 2.16), bend: -25deg, stroke: 0.6pt),
  node((2.95, 1.95), math.theta),
)
