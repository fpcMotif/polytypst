#import "@preview/fletcher:0.5.8" as fletcher
#fletcher.diagram(
  spacing: (2.6em, 2.4em),
  label-size: 0.85em,
  fletcher.node((0, 0), $B ⊗_A B ⊗_A N$),
  fletcher.node((1, 0), $B ⊗_A N$),
  fletcher.node((0, 1), $B ⊗_A N$),
  fletcher.node((1, 1), $N$),
  fletcher.edge((0, 0), (1, 0), "->", $phi ⊗ 1$, label-side: left),
  fletcher.edge((0, 0), (0, 1), "->", $1 ⊗ phi$, label-side: right),
  fletcher.edge((1, 0), (1, 1), "->", $psi$, label-side: left),
  fletcher.edge((0, 1), (1, 1), "->", $psi$, label-side: right),
)
