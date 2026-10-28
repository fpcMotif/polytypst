#set page(width: auto, height: auto, margin: 15pt)
#import "@preview/fletcher:0.5.8": diagram, node, edge

#diagram(
  axes: (ltr, btt),
  spacing: (2.5em, 2.5em),
  node-inset: 2pt,
  label-size: 11pt,
  
  // Origin
  node((0, 0), shape: circle, radius: 1.5pt, fill: black),

  // Axes: x1 (down-right), x2 (up-right), x3 (up)
  edge((0, 0), (2.8, -1.8), "-|>", stroke: 0.9pt),
  node((3.0, -1.9), [#math.italic("x")#super[1]]),
  
  edge((0, 0), (2.8, 1.4), "-|>", stroke: 0.9pt),
  node((3.0, 1.5), [#math.italic("x")#super[2]]),
  
  edge((0, 0), (0, 3.2), "-|>", stroke: 0.9pt),
  node((0, 3.4), [#math.italic("x")#super[3]]),
  
  // Negative axes stubs
  edge((0, 0), (-0.6, 0.4), stroke: 0.6pt),
  edge((0, 0), (-0.6, -0.3), stroke: 0.6pt),
  edge((0, 0), (0, -0.6), stroke: 0.6pt),

  // Projections on axes
  node((1.4, -0.9), shape: circle, radius: 1.2pt, fill: black),
  node((1.55, -1.2), [#math.italic("x")#super[1]#sub[0]]),
  
  node((1.4, 0.7), shape: circle, radius: 1.2pt, fill: black),
  node((1.25, 0.95), [#math.italic("x")#super[2]#sub[0]]),

  // Base parallelogram in x1-x2 plane (dashed)
  edge((1.4, -0.9), (2.8, -0.2), "--", stroke: (dash: "dashed", thickness: 0.6pt)),
  edge((1.4, 0.7), (2.8, -0.2), "--", stroke: (dash: "dashed", thickness: 0.6pt)),

  // Vertical line up to P (dashed)
  edge((2.8, -0.2), (2.8, 2.2), "--", stroke: (dash: "dashed", thickness: 0.6pt)),
  
  // Point P
  node((2.8, 2.2), shape: circle, radius: 2.2pt, stroke: 0.9pt, fill: white),
)
