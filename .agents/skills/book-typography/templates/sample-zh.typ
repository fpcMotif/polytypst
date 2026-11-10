// Proof sheet for the CJK profiles. Compile with --input genre=ja for Japanese.
#import "book.typ": *
#show: book.with(genre: sys.inputs.at("genre", default: "zh"), title: [样张], author: "polytypst")

= 测度与积分

== 外测度

设 $E subset RR$，记 $m^*(E)$ 为它的外测度。外测度满足单调性、可数次可加性，并且对区间给出它的长度。这里的“长度”指区间端点之差（即 $b - a$），它在平移下不变。我们在本章中讨论 Lebesgue 测度的构造，以及它与 Riemann 积分的关系——这两者在有界闭区间上的连续函数上给出相同的值。

$ m^*(E) = inf { sum_(k=1)^infinity ell(I_k) : E subset union.big_(k=1)^infinity I_k } $

#theorem("定理", name: [Carathéodory])[$m^*$-可测集全体构成一个 $sigma$-代数，且 $m^*$ 限制在其上是一个测度。]

#proof[设 $A$、$B$ 可测。由外测度的定义，对任意集合 $T$ 都有 $m^*(T) <= m^*(T inter A) + m^*(T without A)$，故只需证明反向不等式。]

可测集的全体包含所有开集与闭集，因而包含全部 Borel 集。一个集合称为零测集，如果它的外测度为零；可数集都是零测集，Cantor 集也是零测集，尽管它不可数。#lorem(30)
