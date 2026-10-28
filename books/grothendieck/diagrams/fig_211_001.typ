#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $B ⊗_A B ⊗_A B$),
  fletcher.node((1, 0), $B ⊗_A B$),
  fletcher.node((0, 1), $B ⊗_A B$),
  fletcher.node((1, 1), $B$),
  fletcher.edge((0, 0), (1, 0), "->", $phi ⊗ 1$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $1 ⊗ phi$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $phi$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $phi$, label-side: right),
  fletcher.node((3, 0), $B ⊗_A B$),
  fletcher.node((5, 0), $B ⊗_A B$),
  fletcher.node((4, 1), $B$),
  fletcher.edge((3, 0), (5, 0), "->", $sigma$, label-side: left),
  fletcher.edge((3, 0), (4, 1), "->", $phi$, label-side: right),
  fletcher.edge((5, 0), (4, 1), "->", $phi$, label-side: left),
)
