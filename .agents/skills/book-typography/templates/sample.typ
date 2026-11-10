// Proof sheet for book.typ. Compile with --input genre=literature to try another profile.
#import "book.typ": *
#show: book.with(genre: sys.inputs.at("genre", default: "math"), title: [Sample], author: "polytypst")

= Measures and Their Spaces

== Outer measure

#lorem(120)

#lorem(90) For a set $E subset RR$ we write $m^*(E)$ for its outer measure, and #origpage(142) the fraction $(a+b)\/(c+d)$ stays on one line in running text.

$ m^*(E) = inf { sum_(k=1)^infinity ell(I_k) : E subset union.big_(k=1)^infinity I_k } $ <outer>

#theorem("Theorem", name: [Carathéodory])[The family of $m^*$-measurable sets is a $sigma$-algebra, and $m^*$ restricted to it is a measure.]

#proof[Take $A$ and $B$ measurable. By @outer the sum splits over $A$ and its complement. #lorem(40)]

#theorem("Definition", style: "definition")[A set $E$ is _null_ when $m^*(E) = 0$.]

#lorem(140)#footnote[#lorem(25)]

#figure(
  rules-table(columns: 3, align: (left, right, right),
    ([Set], [$m^*$], [Null]),
    [Cantor set], [$0$], [yes],
    [$QQ inter [0,1]$], [$0$], [yes],
    [$[0,1]$], [$1$], [no],
  ),
  caption: [Outer measure of three sets],
)

```python
def outer(intervals):
    return sum(b - a for a, b in intervals)
```

#lorem(160)

=== A remark on rivers

#lorem(200)

#quote(block: true)[#lorem(45)]

#lorem(260)

= Integration

== Simple functions

#lorem(300)

$ integral_X f dif mu = sup { integral_X s dif mu : 0 <= s <= f, s "simple" } $

#lorem(400)
