#set page(width: auto, height: auto, margin: 15pt)
#import "@preview/fletcher:0.5.8": diagram, node, edge

#diagram(
  axes: (ltr, btt),
  spacing: (2.5em, 2.5em),
  node-inset: 2pt,
  label-size: 11pt,
  
  // Origin
  node((0, 0), shape: circle, radius: 2pt, fill: rgb("#0f172a")),

  // Axes in distinct primary hues
  // x1 axis in deep blue
  edge((0, 0), (2.8, -1.8), "-|>", stroke: 1.2pt + rgb("#2563eb")),
  node((3.0, -1.9), text(fill: rgb("#1d4ed8"), weight: "bold", [#math.italic("x")#super[1]])),
  
  // x2 axis in emerald green
  edge((0, 0), (2.8, 1.4), "-|>", stroke: 1.2pt + rgb("#059669")),
  node((3.0, 1.5), text(fill: rgb("#047857"), weight: "bold", [#math.italic("x")#super[2]])),
  
  // x3 axis in crimson red
  edge((0, 0), (0, 3.2), "-|>", stroke: 1.2pt + rgb("#dc2626")),
  node((0, 3.4), text(fill: rgb("#b91c1c"), weight: "bold", [#math.italic("x")#super[3]])),
  
  // Negative axes stubs in muted slate
  edge((0, 0), (-0.6, 0.4), stroke: 0.6pt + rgb("#94a3b8")),
  edge((0, 0), (-0.6, -0.3), stroke: 0.6pt + rgb("#94a3b8")),
  edge((0, 0), (0, -0.6), stroke: 0.6pt + rgb("#94a3b8")),

  // Coordinate projections
  node((1.4, -0.9), shape: circle, radius: 1.8pt, fill: rgb("#2563eb")),
  node((1.6, -1.25), text(fill: rgb("#1d4ed8"), [#math.italic("x")#super[1]#sub[0]])),
  
  node((1.4, 0.7), shape: circle, radius: 1.8pt, fill: rgb("#059669")),
  node((1.2, 1.0), text(fill: rgb("#047857"), [#math.italic("x")#super[2]#sub[0]])),

  // Base parallelogram in x1-x2 plane (dashed cyan)
  edge((1.4, -0.9), (2.8, -0.2), "--", stroke: (dash: "dashed", thickness: 0.8pt, paint: rgb("#0284c7"))),
  edge((1.4, 0.7), (2.8, -0.2), "--", stroke: (dash: "dashed", thickness: 0.8pt, paint: rgb("#0284c7"))),

  // Vertical line up to P in amber dashed
  edge((2.8, -0.2), (2.8, 2.2), "--", stroke: (dash: "dashed", thickness: 0.9pt, paint: rgb("#d97706"))),
  
  // Point P in amber gold
  node((2.8, 2.2), shape: circle, radius: 3.2pt, stroke: 1.4pt + rgb("#1e293b"), fill: rgb("#fef08a")),
)
