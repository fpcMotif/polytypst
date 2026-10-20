"""Kato, Kurokawa, Saito: Number Theory 1: Fermat's Dream (AMS, 2000)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"INTRODUCTION|RATIONAL POINTS ON ELLIPTIC CURVES|"
    r"CONICS AND [Pp]-ADIC NUMBERS|THE ZETA FUNCTION|\s*ZETA\s*|ALGEBRAIC NUMBER THEORY|"
    r"FERMAT AND NUMBER THEORY|FERMAT'S DREAM|PREFACE|CONTENTS|NOTATION|INDEX"
)

FERMAT_SPEC = MonographSpec(
    slug="fermat_dream",
    title="Number Theory 1: Fermat's Dream",
    author="Kazuya Kato, Nobushige Kurokawa, Takeshi Saito",
    translator="Masato Kuwata",
    publisher="American Mathematical Society",
    series="Translations of Mathematical Monographs, Volume 186",
    year=2000,
    publisher_key="springer",
    pdf_page_count=157,
    pdf_name_markers=("fermat", "kurokawa", "number theory 1"),
    preface_page=4,
    chapters=[
        ChapterSpec(0, "Introduction — Fermat and Number Theory", 10, 24),
        ChapterSpec(1, "Rational Points on Elliptic Curves", 25, 52),
        ChapterSpec(2, "Conics and $p$-adic Numbers", 53, 87),
        ChapterSpec(3, "The $\\zeta$ Function", 88, 108),
        ChapterSpec(4, "Algebraic Number Theory", 109, 139),
        ChapterSpec(5, "Rudiments on Dedekind Domains", 140, 142, label="Appendix A"),
        ChapterSpec(6, "Answers to Questions and Exercises", 143, 155, label=""),
    ],
    chapter_label="Chapter {number}",
    index_pages=(156, 157),
    index_title="INDEX",
    sections={
        "0.1": (12, "Before Fermat"),
        "0.2": (14, "Prime numbers and the sum of two squares"),
        "0.3": (15, r"$p = x^2 + 2y^2$, $p = x^2 + 3y^2, \ldots$"),
        "0.4": (16, "Pell's equations"),
        "0.5": (18, "Triangular numbers, quadrangular numbers, pentagonal numbers"),
        "0.6": (19, "Triangular numbers, squares, cubes"),
        "0.7": (20, "Right triangles and elliptic curves"),
        "0.8": (22, "Fermat's Last Theorem"),
        "1.1": (26, "Fermat and elliptic curves"),
        "1.2": (33, "Group structure of an elliptic curve"),
        "1.3": (39, "Mordell's theorem"),
        "2.1": (54, "Conics"),
        "2.2": (58, "Congruence"),
        "2.3": (62, "Conics and quadratic residue symbols"),
        "2.4": (67, r"$p$-adic number fields"),
        "2.5": (78, r"Multiplicative structure of the $p$-adic number field"),
        "2.6": (83, "Rational points on conics"),
        "3.1": (89, r"Three wonders of the values of the $\zeta$ function"),
        "3.2": (92, "Values at positive integers"),
        "3.3": (97, "Values at negative integers"),
        "4.1": (110, "Method of algebraic number theory"),
        "4.2": (119, "The heart of algebraic number theory"),
        "4.3": (130, "The class number formula for imaginary quadratic fields"),
        "4.4": (133, "Fermat's Last Theorem and Kummer"),
        "A.1": (140, "Definition of a Dedekind domain"),
        "A.2": (141, "Fractional ideal"),
    },
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?FIGURE\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_format="FIGURE {chapter}.{number}",
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    theorem_heads_upper=True,
    drop_line_regexes=(
        r"^FUDAN\b.*$",
        r"^[0-9A-Z\s]{10,}图书馆.*$",
        r"^Translations of MATHEMATICAL MONOGRAPHS.*$",
        r"^Volume \d+.*$",
        r"^American Mathematical Society.*$",
        r"^\d+\s+[A-Z\s\$\-\.\,]+$",
        r"^[A-Z\s\$\-\.\,]+\s+\d+$",
    ),
    pre_math_rewrites=(
        (r"\\text\{ord\}", r"\\operatorname{ord}"),
        (r"C\$_p\$", r"$C_p$"),
        (r"\(C\$_p\$\)", r"($C_p$)"),
    ),
    page_fixups={
        29: (
            (
                r"Then there exist bijections between any two of \$A_d\$, \$B_d\$, and \$C_d\$\.",
                r"*Then there exist bijections between any two of $A_d$, $B_d$, and $C_d$.*",
            ),
            (
                r"\$\$\s*A_d \\to B_d;\s*\\quad \(x, y, z\) \\longmapsto \\left\( \\frac\{y - x\}\{2\}, \\frac\{z\}\{2\}, \\frac\{x \+ y\}\{2\} \\right\),\s*\$\$\s*\$\$\s*B_d \\to A_d;\s*\\quad \(u, v, w\) \\longmapsto \(w - u, w \+ u, 2v\),\s*\$\$",
                "$$\n\\begin{aligned}\nA_d \\to B_d; \\quad (x, y, z) &\\longmapsto \\left( \\frac{y - x}{2}, \\frac{z}{2}, \\frac{x + y}{2} \\right), \\\\\nB_d \\to A_d; \\quad (u, v, w) &\\longmapsto (w - u, w + u, 2v),\n\\end{aligned}\n$$",
            ),
            (r"\nThen\n", "\n*Then*\n"),
            (
                r"\(1\) There exist mutually inverse maps \$f : B \\to C\$ and \$g : C \\to B\$ given by",
                r"(1) *There exist mutually inverse maps $f : B \to C$ and $g : C \to B$ given by*",
            ),
            (
                r"\$\$\s*f\(u, v, w\) = \(u\^2 \+ a \+ uv \+ vw \+ wu, \(u \+ v\)\(v \+ w\)\(w \+ u\)\),\s*\$\$\s*\$\$\s*g\(x, y\) = \\left\( \\frac\{1\}\{2y\} \\left\( \(x - a\)\^2 - \(b - a\)\(c - a\) \\right\), \\right\.\s*\$\$\s*\$\$\s*\\left\. \\frac\{1\}\{2y\} \\left\( \(x - b\)\^2 - \(a - b\)\(c - b\) \\right\), \\frac\{1\}\{2y\} \\left\( \(x - c\)\^2 - \(a - c\)\(b - c\) \\right\) \\right\)\.\s*\$\$",
                "$$\n\\begin{aligned}\nf(u, v, w) &= \\bigl(u^2 + a + uv + vw + wu,\\ (u + v)(v + w)(w + u)\\bigr), \\\\\ng(x, y) &= \\Bigl( \\frac{1}{2y}((x - a)^2 - (b - a)(c - a)), \\\\\n&\\qquad \\frac{1}{2y}((x - b)^2 - (a - b)(c - b)),\\ \\frac{1}{2y}((x - c)^2 - (a - c)(b - c)) \\Bigr).\n\\end{aligned}\n$$",
            ),
            (
                r"\(2\) There is a map \$h : B \\to \\tilde\{C\}\$ given by \$h\(u, v, w\) = \(u\^2 \+ a, uvw\)\$\.",
                r"(2) *There is a map $h : B \to \tilde{C}$ given by $h(u, v, w) = (u^2 + a, uvw)$.*",
            ),
        ),
        36: (
            (
                r"X = \\\{\\text\{ratio\}\(x : y : z\) \\mid x, y, z \\in K, \(x, y, z\) \\neq \(0, 0, 0\) \\\\ y\^2 z = ax\^3 \+ bx\^2 z \+ cx z\^2 \+ dz\^3\\\}",
                r"\begin{aligned} X = \bigl\{\,\text{ratio}(x : y : z) \mid &x, y, z \in K,\ (x, y, z) \neq (0, 0, 0), \\ &y^2 z = ax^3 + bx^2 z + cx z^2 + dz^3\,\bigr\} \end{aligned}",
            ),
        ),
        38: (
            (
                r"\(1\.5\) \$\\mathbb\{Z\}\^\{\\oplus r\} \\oplus\$ finite abelian group \$\(r \\geq 0\)\$,",
                r"$$\mathbb{Z}^{\oplus r} \oplus (\text{finite abelian group}) \quad (r \geq 0),$$ (1.5)",
            ),
        ),
        41: (
            (
                r"\\overline\{\(x - a, \\overline\{x - b, \\overline\{x - c\}\)\}",
                r"(\overline{x - a},\ \overline{x - b},\ \overline{x - c})",
            ),
            (
                r"\\overline\{\(\(a - b\)\(a - c\), \\overline\{a - b, \\overline\{a - c\}\)\}\}",
                r"((\overline{a - b})(\overline{a - c}),\ \overline{a - b},\ \overline{a - c})",
            ),
            (
                r"\\overline\{\(b - a, \\overline\{\(b - a\)\(b - c\), \\overline\{b - c\}\)\}\}",
                r"(\overline{b - a},\ (\overline{b - a})(\overline{b - c}),\ \overline{b - c})",
            ),
            (
                r"\\overline\{\(c - a, \\overline\{c - b\}, \\overline\{\(c - a\)\(c - b\)\}\)\}",
                r"(\overline{c - a},\ \overline{c - b},\ (\overline{c - a})(\overline{c - b}))",
            ),
        ),
        56: (
            (
                r"\\begin\{cases\}\s*\\text\{rational points on \} x\^2 \+ y\^2 = 1 \\\\ \\text\{different from \} \(-1, 0\)\s*\\end\{cases\}\s*\\longleftrightarrow\s*\\begin\{cases\}\s*1:1 & \\\{\\text\{rational numbers\}\\\}, \\\\\s*\(x, y\) & \\longmapsto \\frac\{y\}\{x \+ 1\}, \\\\\s*\\left\(\\frac\{1 - t\^2\}\{1 \+ t\^2\}, \\frac\{2t\}\{1 \+ t\^2\}\\right\) & \\longleftrightarrow t\.\s*\\end\{cases\}",
                r"\begin{aligned} \left\{ \begin{array}{c} \text{rational points on } x^2 + y^2 = 1 \\ \text{different from } (-1, 0) \end{array} \right\} &\underset{1:1}{\longleftrightarrow} \{\text{rational numbers}\} \\ (x, y) &\longmapsto \frac{y}{x + 1} \\ \left(\frac{1 - t^2}{1 + t^2}, \frac{2t}{1 + t^2}\right) &\longleftrightarrow t. \end{aligned}",
            ),
        ),
        63: (
            (
                r"\(5-1\) \$\(a, b\)_2 = \\begin\{cases\} 1 & \\text\{if \} a \\equiv 1 \\bmod 4 \\text\{ or \} b \\equiv 1 \\bmod 4, \\\\ -1 & \\text\{if \} a \\equiv b \\equiv -1 \\bmod 4\. \\end\{cases\}\$\s*\(5-2\) \$\(a, 2b\)_2\$\s*\$\$= \\begin\{cases\} 1 & \\text\{if \} a \\equiv 1 \\bmod 8 \\text\{ or \} a \\equiv 1 - 2b \\bmod 8, \\\\ -1 & \\text\{otherwise\.\} \\end\{cases\}\$\$",
                r"$$\begin{aligned} \text{(5-1)}\quad (a, b)_2 &= \begin{cases} 1 & \text{if } a \equiv 1 \bmod 4 \text{ or } b \equiv 1 \bmod 4, \\ -1 & \text{if } a \equiv b \equiv -1 \bmod 4, \end{cases} \\ \text{(5-2)}\quad (a, 2b)_2 &= \begin{cases} 1 & \text{if } a \equiv 1 \bmod 8 \text{ or } a \equiv 1 - 2b \bmod 8, \\ -1 & \text{otherwise.} \end{cases} \end{aligned}$$",
            ),
        ),
        78: (
            (
                r"additive group \$p\^m\\mathbb\{Z\}_p\$\s*\$\$\\cong \\text\{multiplicative group \} 1 \+ p\^m\\mathbb\{Z\}_p = \\\{1 \+ p\^m a \\mid a \\in \\mathbb\{Z\}_p\\\}\.\$\$",
                r"$$\text{additive group } p^m\mathbb{Z}_p \cong \text{multiplicative group } 1 + p^m\mathbb{Z}_p = \{1 + p^m a \mid a \in \mathbb{Z}_p\}.$$",
            ),
        ),
        83: (
            (
                r"\$\$\\exists x, y \\in \\mathbb\{Q\}_p \\text\{ such that \} -ab\^\{-1\}x\^2 \+ by\^2 = 1\$\$\s*\$\$\\Longleftrightarrow \\exists x, y, z \\in \\mathbb\{Q\}_p \\text\{ such that \} -ab\^\{-1\}x\^2 \+ by\^2 = z\^2\$\$\s*and \$\(x, y, z\) \\neq \(0, 0, 0\)\$\s*\$\$\\Longleftrightarrow \\exists x, y, z \\in \\mathbb\{Q\}_p \\text\{ such that \} \(by\)\^2 = ax\^2 \+ bz\^2\$\$\s*and \$\(x, y, z\) \\neq \(0, 0, 0\)\$\s*\$\$\\Longleftrightarrow \\exists x, y \\in \\mathbb\{Q\}_p \\text\{ such that \} ax\^2 \+ by\^2 = 1\.\$\$",
                r"$$\begin{aligned} &\exists x, y \in \mathbb{Q}_p \text{ such that } -ab^{-1}x^2 + by^2 = 1 \\ \Longleftrightarrow\;& \exists x, y, z \in \mathbb{Q}_p \text{ such that } -ab^{-1}x^2 + by^2 = z^2 \text{ and } (x, y, z) \neq (0, 0, 0) \\ \Longleftrightarrow\;& \exists x, y, z \in \mathbb{Q}_p \text{ such that } (by)^2 = ax^2 + bz^2 \text{ and } (x, y, z) \neq (0, 0, 0) \\ \Longleftrightarrow\;& \exists x, y \in \mathbb{Q}_p \text{ such that } ax^2 + by^2 = 1. \end{aligned}$$",
            ),
        ),
        90: (
            (
                r"the value of a \$\\zeta\$ function at \$s =\$ integer\s*\$\$\s*= \\text\{\(rational number\)\}\s*\$\$\s*\$\$\s*\\times \\text\{\(the power of \} \\pi \\text\{ or something similar to \} \\log\(1 \+ \\sqrt\{2\}\)\)\.\s*\$\$",
                r"$$\begin{aligned} &\text{the value of a } \zeta \text{ function at } s = \text{integer} \\ &\quad = \text{(rational number)} \times \bigl(\text{the power of } \pi \text{ or something similar to } \log(1 + \sqrt{2})\bigr). \end{aligned}$$",
            ),
            (
                r"For example, if \$r\$ is a positive even integer, Euler proved the formula\s*\$\$\s*\\zeta\(r\) = \\text\{\(rational number\)\} \\times \\\s*pi\^r \\quad \\text\{\(§3\.2, Corollary 3\.9\)\.\}\s*\$\$",
                "",
            ),
        ),
        92: (
            (
                r"left-hand side of \(3\.7\) = \$1 - \\dfrac\{\\pi\^2\}\{3!\}x\^2\$ \+ terms of degree 4 or higher\.",
                r"$$\text{left-hand side of (3.7)} = 1 - \frac{\pi^2}{3!}x^2 + \text{terms of degree 4 or higher}.$$",
            ),
            (
                r"right-hand side of \(3\.7\)\s*\$\$= 1 - \\left\(\\sum_\{n=1\}\^\{\\infty\} \\frac\{1\}\{n\^2\}\\right\) x\^2 \+ \\text\{terms of degree 4 or higher\}\.\$\$",
                r"$$\text{right-hand side of (3.7)} = 1 - \left(\sum_{n=1}^{\infty} \frac{1}{n^2}\right) x^2 + \text{terms of degree 4 or higher}.$$",
            ),
        ),
    },
)
