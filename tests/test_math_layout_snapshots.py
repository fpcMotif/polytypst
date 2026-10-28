import json
import re
from pathlib import Path

import pymupdf
import pytest

from polytypst.compiler.monograph import (
    ChapterSpec,
    MonographCompiler,
    MonographSpec,
    compile_typst,
    running_header_regexes,
)
from polytypst.compiler.typst_math import typst_command
from polytypst.fermat.spec import FERMAT_SPEC
from polytypst.goursat.build import goursat_markdown
from polytypst.goursat.figures import (
    GOURSAT_SVG_GENERATORS,
    normalize_goursat_markdown,
)
from polytypst.parity import FACSIMILE, SOURCE_PAGINATED, PageParity, compare, verdict
from polytypst.parity.ink_cache import InkCache
from polytypst.parity.words import page_ink
from polytypst.tex_markdown import repair_page_math
from polytypst.vision.figure_extractor import ExtractedFigure

FERMAT_PAGE_29_MD = (
    "1.1. FERMAT AND ELLIPTIC CURVES\n\n"
    "Lemma 1.4. Let $K$ be a field of characteristic different from 2. "
    "For $d \\in K$ define the sets $A_d$, $B_d$ and $C_d$ as follows:\n\n"
    "$$\nA_d = \\{(x, y, z) \\in K \\times K \\times K \\mid x^2 + y^2 = z^2, \\frac{1}{2}xy = d\\},\n$$\n\n"
    "$$\nB_d = \\{(u, v, w) \\in K \\times K \\times K \\mid u^2 + d = v^2, v^2 + d = w^2\\},\n$$\n\n"
    "$$\nC_d = \\{(x, y) \\in K \\times K \\mid y^2 = x^3 - d^2x, y \\neq 0\\}.\n$$\n\n"
    "Then there exist bijections between any two of $A_d$, $B_d$, and $C_d$.\n\n"
    "Indeed, between $A_d$ and $B_d$ we have two maps\n\n"
    "$$\nA_d \\to B_d; \\quad (x, y, z) \\longmapsto \\left( \\frac{y - x}{2}, \\frac{z}{2}, \\frac{x + y}{2} \\right),\n$$\n\n"
    "$$\nB_d \\to A_d; \\quad (u, v, w) \\longmapsto (w - u, w + u, 2v),\n$$\n\n"
    "and these maps are inverse to each other.\n\n"
    "Lemma 1.5. Let $K$ be a field of characteristic different from 2, and let $a$, $b$, and $c$ "
    "be distinct elements in $K$. Define $B$, $\\tilde{C}$ and $C$ by\n\n"
    "$$\nB = \\{(u, v, w) \\in K \\times K \\times K \\mid u^2 + a = v^2 + b = w^2 + c\\},\n$$\n\n"
    "$$\n\\tilde{C} = \\{(x, y) \\in K \\times K \\mid y^2 = (x - a)(x - b)(x - c)\\},\n$$\n\n"
    "$$\nC = \\{(x, y) \\in K \\times K \\mid y^2 = (x - a)(x - b)(x - c), y \\neq 0\\}\n$$\n\n"
    "$$\n= \\tilde{C} - \\{(a, 0), (b, 0), (c, 0)\\}.\n$$\n\n"
    "Then\n\n"
    "(1) There exist mutually inverse maps $f : B \\to C$ and $g : C \\to B$ given by\n\n"
    "$$\nf(u, v, w) = (u^2 + a + uv + vw + wu, (u + v)(v + w)(w + u)),\n$$\n\n"
    "$$\ng(x, y) = \\left( \\frac{1}{2y} \\left( (x - a)^2 - (b - a)(c - a) \\right), \\right.\n$$\n\n"
    "$$\n\\left. \\frac{1}{2y} \\left( (x - b)^2 - (a - b)(c - b) \\right), \\frac{1}{2y} \\left( (x - c)^2 - (a - c)(b - c) \\right) \\right).\n$$\n\n"
    "(2) There is a map $h : B \\to \\tilde{C}$ given by $h(u, v, w) = (u^2 + a, uvw)$."
)

FERMAT_PAGE_29_TYPST_SNAPSHOT = (
    "== 1.1 Fermat and elliptic curves\n\n"
    "#thm-break\n"
    "#strong[LEMMA 1.4.] #emph[Let $K$ be a field of characteristic different from 2. "
    "For $d in K$ define the sets $A_d$, $B_d$ and $C_d$ as follows:]\n\n"
    "$ A_d & = { ( x \\, y \\, z ) in K times K times K divides x^2 + y^2 = z^2 \\, 1 / 2 x y = d } \\,\\\n"
    "B_d & = { ( u \\, v \\, w ) in K times K times K divides u^2 + d = v^2 \\, v^2 + d = w^2 } \\,\\\n"
    "C_d & = { ( x \\, y ) in K times K divides y^2 = x^3 - d^2 x \\, y eq.not 0 } . $ \n\n"
    "#emph[Then there exist bijections between any two of $A_d$, $B_d$, and $C_d$.]\n\n"
    "Indeed, between $A_d$ and $B_d$ we have two maps\n\n"
    "$ A_d arrow.r B_d ; quad ( x \\, y \\, z ) & mapsto.long (frac(y - x, 2) \\, z / 2 \\, frac(x + y, 2)) \\,\\\n"
    "B_d arrow.r A_d ; quad ( u \\, v \\, w ) & mapsto.long ( w - u \\, w + u \\, 2 v ) \\, $ \n\n"
    "and these maps are inverse to each other.\n\n"
    "#thm-break\n"
    "#strong[LEMMA 1.5.] #emph[Let $K$ be a field of characteristic different from 2, and let $a$, $b$, and $c$ "
    "be distinct elements in $K$. Define $B$, $tilde(C)$ and $C$ by]\n\n"
    "$ B & = { ( u \\, v \\, w ) in K times K times K divides u^2 + a = v^2 + b = w^2 + c } \\,\\\n"
    "tilde(C) & = { ( x \\, y ) in K times K divides y^2 = ( x - a ) ( x - b ) ( x - c ) } \\,\\\n"
    "C & = { ( x \\, y ) in K times K divides y^2 = ( x - a ) ( x - b ) ( x - c ) \\, y eq.not 0 }\\\n"
    "& = tilde(C) - { ( a \\, 0 ) \\, ( b \\, 0 ) \\, ( c \\, 0 ) } . $ \n\n"
    "#emph[Then]\n\n"
    "#item-break\n"
    "(1) #emph[There exist mutually inverse maps $f : B arrow.r C$ and $g : C arrow.r B$ given by]\n\n"
    "$ f ( u \\, v \\, w ) & = #scale(x: 120%, y: 120%)[(] u^2 + a + u v + v w + w u \\, med ( u + v ) ( v + w ) ( w + u ) #scale(x: 120%, y: 120%)[)] \\,\\\n"
    "g ( x \\, y ) & = #scale(x: 180%, y: 180%)[\\(] frac(1, 2 y) ( ( x - a )^2 - ( b - a ) ( c - a ) ) \\,\\\n"
    " & #h(2em) frac(1, 2 y) ( ( x - b )^2 - ( a - b ) ( c - b ) ) \\, med frac(1, 2 y) ( ( x - c )^2 - ( a - c ) ( b - c ) ) #scale(x: 180%, y: 180%)[\\)] . $ \n\n"
    "#item-break\n"
    "(2) #emph[There is a map $h : B arrow.r tilde(C)$ given by $h ( u \\, v \\, w ) = ( u^2 + a \\, u v w )$.]"
)

FERMAT_PAGE_63_MD = (
    "(4) If $p$ is an odd prime number and $a, b \\in (\\mathbb{Z}_{(p)})^\\times$, then we have the following.\n\n"
    "(4-1) $(a, b)_p = 1$,\n\n"
    "(4-2) $(a, pb)_p = \\left(\\frac{a \\bmod p}{p}\\right)$.\n\n"
    "(5) If $a, b \\in \\mathbb{Z}_{(2)}^\\times$, then\n\n"
    "(5-1) $(a, b)_2 = \\begin{cases} 1 & \\text{if } a \\equiv 1 \\bmod 4 \\text{ or } b \\equiv 1 \\bmod 4, \\\\ "
    "-1 & \\text{if } a \\equiv b \\equiv -1 \\bmod 4. \\end{cases}$\n\n"
    "(5-2) $(a, 2b)_2$\n\n"
    "$$= \\begin{cases} 1 & \\text{if } a \\equiv 1 \\bmod 8 \\text{ or } a \\equiv 1 - 2b \\bmod 8, \\\\ "
    "-1 & \\text{otherwise.} \\end{cases}$$\n\n"
    "**THEOREM 2.5.** Let $a, b \\in \\mathbb{Q}^\\times$. Then $(a, b)_v$ is equal to 1 except for a finite number of $v$, and we have\n\n"
    "$$\\prod_v (a, b)_v = 1,$$\n\n"
    "where $v$ runs through all the prime numbers and $\\infty$.\n\n"
    "**PROOF OF THEOREM 2.5.** It suffices to show it in the following cases (i)–(ii).\n\n"
    "(i) $a$ and $b$ are two distinct odd prime numbers.\n\n"
    "(ii) $a$ is an odd prime number, and $b = -1$ or 2."
)

FERMAT_PAGE_63_TYPST_SNAPSHOT = (
    "(4) If $p$ is an odd prime number and $a \\, b in ( bb(Z)_(( p )) )^times$, then we have the following.\n\n"
    "#item-break\n"
    "(4-1) $( a \\, b )_p = 1$,\n\n"
    "#item-break\n"
    "(4-2) $( a \\, p b )_p = (frac(a med mod med p, p))$.\n\n"
    "#item-break\n"
    "(5) If $a \\, b in bb(Z)_(( 2 ))^times$, then\n\n"
    '$ upright("(5-1)") quad ( a \\, b )_2 & = cases(delim: "{", 1 & upright("if") med a equiv 1 med mod med 4 med upright("or") med b equiv 1 med mod med 4 \\,, - 1 & upright("if") med a equiv b equiv - 1 med mod med 4 \\,)\\\n'
    'upright("(5-2)") quad ( a \\, 2 b )_2 & = cases(delim: "{", 1 & upright("if") med a equiv 1 med mod med 8 med upright("or") med a equiv 1 - 2 b med mod med 8 \\,, - 1 & upright("otherwise.")) $ \n\n'
    "#thm-break\n"
    "#strong[THEOREM 2.5.] #emph[Let $a \\, b in bb(Q)^times$. Then $( a \\, b )_v$ is equal to 1 except for a finite number of $v$, and we have]\n\n"
    "$ product_v ( a \\, b )_v = 1 \\, $ \n\n"
    "where $v$ runs through all the prime numbers and $oo$.\n\n"
    "#sub-break\n"
    "#emph[Proof of Theorem 2.5.] It suffices to show it in the following cases (i)–(ii).\n\n"
    "#item-break\n"
    "(i) $a$ and $b$ are two distinct odd prime numbers.\n\n"
    "#item-break\n"
    "(ii) $a$ is an odd prime number, and $b = - 1$ or 2."
)

FERMAT_PAGE_38_41_56_SPECS: tuple[tuple[int, str, str], ...] = (
    (
        38,
        (
            "## 1.3. Mordell's theorem\n\n"
            "(a) **Statement of Mordell's theorem.** Mordell proved the following theorem in 1922.\n\n"
            "**THEOREM 1.12** (Mordell's theorem). *Let $E$ be an elliptic curve over $\\mathbb{Q}$. "
            "Then the group $E(\\mathbb{Q})$ is a finitely generated abelian group.*\n\n"
            "By the fundamental theorem on abelian groups, a finitely generated abelian group is isomorphic to\n\n"
            "(1.5) $\\mathbb{Z}^{\\oplus r} \\oplus$ finite abelian group $(r \\geq 0)$,\n\n"
            "where $\\mathbb{Z}^{\\oplus r}$ denotes the direct sum of $r$ copies of $\\mathbb{Z}$."
        ),
        (
            "== 1.3 Mordell's theorem\n\n"
            "#thm-break\n"
            "#strong[(a) Statement of Mordell's theorem.] Mordell proved the following theorem in 1922.\n\n"
            "#thm-break\n"
            "#strong[THEOREM 1.12.] (Mordell's theorem) #emph[Let $E$ be an elliptic curve over $bb(Q)$. "
            "Then the group $E ( bb(Q) )$ is a finitely generated abelian group.]\n\n"
            "By the fundamental theorem on abelian groups, a finitely generated abelian group is isomorphic to\n\n"
            '$ bb(Z)^(plus.o r) plus.o ( upright("finite abelian group") ) quad ( r gt.eq 0 ) \\, $ <eq-1-5>\n\n'
            "where $bb(Z)^(plus.o r)$ denotes the direct sum of $r$ copies of $bb(Z)$."
        ),
    ),
    (
        41,
        (
            "**PROPOSITION 1.14.** *Let $a$, $b$, and $c$ be distinct rational numbers. Define the map*\n\n"
            "$$\\partial(P) = \\begin{cases} \\overline{(x - a, \\overline{x - b, \\overline{x - c})} & \\text{if } P \\neq O, (a, 0), (b, 0), (c, 0), \\\\ "
            "\\overline{((a - b)(a - c), \\overline{a - b, \\overline{a - c})}} & \\text{if } P = (a, 0), \\\\ "
            "\\overline{(b - a, \\overline{(b - a)(b - c), \\overline{b - c})}} & \\text{if } P = (b, 0), \\\\ "
            "\\overline{(c - a, \\overline{c - b}, \\overline{(c - a)(c - b)})} & \\text{if } P = (c, 0), \\\\ "
            "(1, 1, 1) & \\text{if } P = O. \\end{cases}$$\n\n"
            "(1) *The map $\\partial$ is a group homomorphism.*"
        ),
        (
            "#strong[PROPOSITION 1.14.] #emph[Let $a$, $b$, and $c$ be distinct rational numbers. Define the map]\n\n"
            '$ partial ( P ) = cases(delim: "{", ( overline(x - a) \\, med overline(x - b) \\, med overline(x - c) ) & upright("if") med P eq.not O \\, ( a \\, 0 ) \\, ( b \\, 0 ) \\, ( c \\, 0 ) \\,, '
            '( ( overline(a - b) ) ( overline(a - c) ) \\, med overline(a - b) \\, med overline(a - c) ) & upright("if") med P = ( a \\, 0 ) \\,, '
            '( overline(b - a) \\, med ( overline(b - a) ) ( overline(b - c) ) \\, med overline(b - c) ) & upright("if") med P = ( b \\, 0 ) \\,, '
            '( overline(c - a) \\, med overline(c - b) \\, med ( overline(c - a) ) ( overline(c - b) ) ) & upright("if") med P = ( c \\, 0 ) \\,, '
            '( 1 \\, 1 \\, 1 ) & upright("if") med P = O .) $ \n\n'
            "#item-break\n"
            "(1) #emph[The map $partial$ is a group homomorphism.]"
        ),
    ),
    (
        56,
        (
            "To sum up, we have the following one-to-one correspondence:\n\n"
            "$$\n\\begin{cases}\n\\text{rational points on } x^2 + y^2 = 1 \\\\ \\text{different from } (-1, 0)\n\\end{cases}\n"
            "\\longleftrightarrow\n"
            "\\begin{cases}\n1:1 & \\{\\text{rational numbers}\\}, \\\\\n"
            "(x, y) & \\longmapsto \\frac{y}{x + 1}, \\\\\n"
            "\\left(\\frac{1 - t^2}{1 + t^2}, \\frac{2t}{1 + t^2}\\right) & \\longleftrightarrow t.\n\\end{cases}\n$$"
        ),
        (
            "To sum up, we have the following one-to-one correspondence:\n\n"
            '$ mat(delim: "{", upright("rational points on") med x^2 + y^2 = 1; upright("different from") med ( - 1 \\, 0 )) & limits(arrow.l.r.long)_(1 : 1) { upright("rational numbers") }\\\n'
            "( x \\, y ) & mapsto.long frac(y, x + 1)\\\n"
            "(frac(1 - t^2, 1 + t^2) \\, frac(2 t, 1 + t^2)) & arrow.l.r.long t . $"
        ),
    ),
)

GOURSAT_RAW_PAGE = (
    "A COURSE IN MATHEMATICAL ANALYSIS\n"
    "II, § 20] IMPLICIT FUNCTIONS 87\n"
    "42\n"
    "Let $ f(x, y) = 0 $ and \\( P(x, y) \\) be *analytic* functions with y # 0.\n"
    "(29) \\[ \\frac{dy}{dx} = -\\frac{\\partial f}{\\partial x} \\left( \\frac{\\partial f}{\\partial y} \\right)^{-1}, "
    "\\quad \\int_0^x \\frac{d^2 y}{dt^2} dt + d\\alpha = d(uv) \\]\n\n"
    "FIG. 1. The geometric derivative.\n\n"
    "For the branch\n"
    "$$\\left\\{ \\begin{array}{l} u = x^2 \\\\ v = y^2 \\end{array} \\right.$$\n"
    "as shown in (Fig. 14)."
)

GOURSAT_MD_SNAPSHOT = (
    "Let $f(x, y) = 0$ and $P(x, y)$ be *analytic* functions with y \\neq 0.\n\n"
    "$$\n\\frac{\\mathrm{d} y}{\\mathrm{d} x} = -\\frac{\\partial f}{\\partial x} "
    "\\left( \\frac{\\partial f}{\\partial y} \\right)^{-1}, \\quad "
    "\\int_0^x \\frac{\\mathrm{d}^2 y}{\\mathrm{d} t^2} \\mathrm{d} t + \\mathrm{d} \\alpha = \\mathrm{d}(uv) \\tag{29}\n$$\n\n"
    "FIG. 1. The geometric derivative.\n\n"
    "![FIG. 1. The geometric derivative.](figures/fig_1.svg){#fig:1}\n\n"
    "For the branch\n\n"
    "$$\n\\begin{cases}\nu = x^2 \\\\ v = y^2\n\\end{cases}\n$$\n\n"
    "as shown in (Fig. 14)."
)

GOURSAT_TYPST_SNAPSHOT = (
    "Let $f ( x \\, y ) = 0$ and $P ( x \\, y )$ be #emph[analytic] functions with y \\!= 0.\n\n"
    "$ frac(dif y, dif x) = - frac(partial f, partial x) (frac(partial f, partial y))^(- 1) \\, "
    "quad integral_0^x frac(dif^2 y, dif t^2) dif t + dif alpha = dif ( u v ) $ <eq-1-1-29>\n\n"
    "FIG. 1. The geometric derivative.\n\n"
    "{\\#fig:1}\n\n"
    "For the branch\n\n"
    '$ cases(delim: "{", u = x^2 & , v = y^2 & ) $ \n\n'
    "as shown in (Fig. 14)."
)

GOURSAT_FIGURE_TYPST_SNAPSHOT = (
    "#figure(\n"
    '  image("figures/fig_1.svg", width: 58%),\n'
    "  caption: [#strong[FIG. 1.1.] The geometric derivative.],\n"
    "  supplement: none\n"
    ")"
)

SERRE_RAW_PAGE = (
    "CHAPITRE VII\n"
    "92 COURS D'ARITHMÉTIQUE\n"
    "92\n"
    "**PROPOSITION 7.** *Soit $f$ une forme modulaire sur $\\operatorname{SL}_2(\\mathbf{Z})$ "
    "avec $\\operatorname{Arg}(z)$ borné et $|f(z) - f(w)| \\leq |z - w|$.*\n\n"
    "(44) \\[ F(-1/z) = z^{12} F(z), \\quad \\Delta(z) = g_2^3 - 27g_3^2 = q \\prod_{n=1}^{\\infty} (1 - q^n)^{24}. \\]\n\n"
    "Sur l'espace projectif on obtient le produit\n\n"
    "(45) $$\\prod_{m,n=-\\infty}^{\\infty}' (1 - q^{mn}) \\quad \\text{sur } \\mathbb{P}_\\mathbb{Z}^n \\setminus \\{0\\}$$\n\n"
    "Les opérateurs de Hecke vérifient\n\n"
    "$$R_\\lambda R_\\mu = R_{\\lambda + \\mu}$$\n\n"
    "$$T(p) f = \\sum_{n=1}^{\\infty} a_{pn} q^n$$\n\n"
    "*Proof.* Ceci démontre la proposition. □"
)

SERRE_TYPST_SNAPSHOT = (
    '#strong[Proposition 7.] #emph[Soit $f$ une forme modulaire sur $op("SL")_2 ( upright(bold(Z)) )$ '
    'avec $op("Arg") ( z )$ borné et $abs(f ( z ) - f ( w )) lt.eq abs(z - w)$.]\n\n'
    "$ F ( - 1 \\/ z ) = z^12 F ( z ) \\, quad Delta ( z ) = g_2^3 - 27 g_3^2 = q product_(n = 1)^oo ( 1 - q^n )^24 . $ <eq-7-92-44>\n\n"
    "#h(1.2em);Sur l'espace projectif on obtient le produit\n\n"
    '$ product_(m \\, n = - oo)^oo\' ( 1 - q^(m n) ) quad upright("sur") med bb(P)_(bb(Z))^n without { 0 } $ <eq-7-92-45>\n\n'
    "Les opérateurs de Hecke vérifient\n\n"
    "$ R_lambda R_mu & = R_(lambda + mu)\\\n"
    "T ( p ) f & = sum_(n = 1)^oo a_(p n) q^n $ \n\n"
    "#sub-break\n"
    "#emph[Proof.] Ceci démontre la proposition.#qed"
)


def _collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _write_ocr_cache(source: Path, cache: Path) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    page = pymupdf.open(source)[0]
    w, h = page.rect.width, page.rect.height
    lines: dict[float, list[tuple[float, float, float, float, str]]] = {}
    for x0, y0, x1, y1, word, *_ in page.get_text("words"):
        lines.setdefault(round(y1 / 2.0) * 2.0, []).append((x0, y0, x1, y1, word))
    out = []
    for words in lines.values():
        words.sort()
        x0, y0 = min(item[0] for item in words), min(item[1] for item in words)
        x1, y1 = max(item[2] for item in words), max(item[3] for item in words)
        out.append(
            {
                "text": " ".join(item[4] for item in words),
                "x": x0 / w,
                "y": (h - y1) / h,
                "w": (x1 - x0) / w,
                "h": (y1 - y0) / h,
            }
        )
    (cache / "p001.json").write_text(json.dumps(out), encoding="utf-8")
    (cache / "pages.json").write_text(json.dumps({"1": [w, h]}), encoding="utf-8")


def test_fermat_lemma_bijections_and_hilbert_cases_typst_snapshot() -> None:
    compiler = MonographCompiler(FERMAT_SPEC)
    body_29, _, _ = compiler.cleaner.clean(FERMAT_PAGE_29_MD, 29)
    assert (
        _collapse_blank_lines(compiler.format_typst(body_29))
        == FERMAT_PAGE_29_TYPST_SNAPSHOT
    )

    body_63, _, _ = compiler.cleaner.clean(FERMAT_PAGE_63_MD, 63)
    assert (
        _collapse_blank_lines(compiler.format_typst(body_63))
        == FERMAT_PAGE_63_TYPST_SNAPSHOT
    )


def test_fermat_mordell_proposition_and_conics_correspondence_typst_snapshot() -> None:
    compiler = MonographCompiler(FERMAT_SPEC)
    preamble = compiler.build_typst_preamble()
    for expected_rule in (
        "#set math.mat(row-gap: 0.55em, column-gap: 0.8em)",
        "#set math.cases(gap: 0.55em)",
        "show math.frac: set text(size: 0.85em)",
        "#show math.equation.where(block: true): set block(above: 1.3em, below: 1.3em)",
        "#let thm-break = block(above: 1.65em, below: 0pt, sticky: true)[]",
        "#let sub-break = block(above: 1.35em, below: 0pt, sticky: true)[]",
        "#let item-break = block(above: 1.0em, below: 0pt)[]",
        "#let qed = { h(0.6em); box(width: 1fr, align(right)[$square.stroked$]) }",
    ):
        assert expected_rule in preamble

    for pno, raw_md, expected_typst in FERMAT_PAGE_38_41_56_SPECS:
        body, _, _ = compiler.cleaner.clean(raw_md, pno)
        assert _collapse_blank_lines(compiler.format_typst(body)) == expected_typst


def test_goursat_differentials_delimiters_and_figure_grounding_snapshot(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    (fig_dir / "fig_1.svg").write_text(GOURSAT_SVG_GENERATORS["1"](), encoding="utf-8")

    fig = ExtractedFigure(
        figure_id="1",
        caption="FIG. 1. The geometric derivative.",
        image_rel_path="figures/fig_1.png",
        source_page=1,
    )
    stitched = goursat_markdown([(1, GOURSAT_RAW_PAGE)], [fig])
    goursat_md = normalize_goursat_markdown("## CHAPTER I\n\n" + stitched)
    ch1_md = goursat_md.split("# CHAPTER I: DERIVATIVES AND DIFFERENTIALS\n\n", 1)[1]
    assert _collapse_blank_lines(ch1_md) == GOURSAT_MD_SNAPSHOT

    compiler = MonographCompiler(
        MonographSpec(
            domain="math",
            slug="goursat_test",
            title="A Course in Mathematical Analysis",
            author="Edouard Goursat",
            equation_numbering="page",
            chapters=[ChapterSpec(1, "Derivatives and Differentials", 1, 1)],
        )
    )
    body, top_f, bot_f = compiler.cleaner.clean(ch1_md, 1)
    stitched_ch = compiler.stitch_chapter([(1, body, top_f, bot_f)], fig_dir)
    assert (
        _collapse_blank_lines(compiler.format_typst(stitched_ch))
        == GOURSAT_TYPST_SNAPSHOT
    )
    assert (
        compiler.make_figure_typst("1", "FIG. 1.1. The geometric derivative.", fig_dir)
        == GOURSAT_FIGURE_TYPST_SNAPSHOT
    )


def test_serre_display_brackets_tags_operators_and_bars_typst_snapshot() -> None:
    compiler = MonographCompiler(
        MonographSpec(
            domain="math",
            slug="serre_test",
            title="Cours d'arithmétique",
            author="Jean-Pierre Serre",
            lang="fr",
            equation_numbering="page",
            chapters=[ChapterSpec(7, "Formes modulaires", 92, 92)],
            running_header_regexes=running_header_regexes("CHAPITRE VII|COURS D'ARITHMÉTIQUE"),
        )
    )
    body, _, _ = compiler.cleaner.clean(repair_page_math(SERRE_RAW_PAGE), 92)
    assert _collapse_blank_lines(compiler.format_typst(body)) == SERRE_TYPST_SNAPSHOT


@pytest.mark.slow
@pytest.mark.skipif(
    typst_command() is None, reason="needs typst to compile layout page"
)
def test_math_layout_compiled_page_scan_parity_snapshot(tmp_path: Path) -> None:
    spec = MonographSpec(
        domain="math",
        slug="parity_math",
        title="Number Theory",
        author="Kato",
        publisher_key="springer",
        chapters=[ChapterSpec(1, "Elliptic Curves", 1, 1)],
    )
    compiler = MonographCompiler(spec)
    page_md = (
        "**LEMMA 1.4.** *Let $K$ be a field with characteristic distinct from 2. "
        "For every element $d$ in $K$ there exist bijections between the sets.*\n\n"
        "(1) *There exist mutually inverse maps between the sets preserving the differential $dy = 3 x dx$.*\n\n"
        "*Proof.* Direct substitution into the rational coordinates establishes the bijection for every point."
    )
    body, _, _ = compiler.cleaner.clean(page_md, 1)
    typ_src = (
        compiler.build_typst_preamble() + "\n" + compiler.format_typst(body) + "\n"
    )

    typ_file = tmp_path / "source.typ"
    src_pdf = tmp_path / "source.pdf"
    typ_file.write_text(typ_src, encoding="utf-8")
    compile_typst(typ_file, src_pdf)
    _write_ocr_cache(src_pdf, tmp_path / "ocr")

    rebuilt_pdf = tmp_path / "rebuilt.pdf"
    compile_typst(typ_file, rebuilt_pdf)
    scan = InkCache(src_pdf, tmp_path / "ink", page_ink)
    page_ok: PageParity = compare(
        scan, rebuilt_pdf, {1: [1]}, ocr=tmp_path / "ocr", work=tmp_path / "work"
    )[0]
    assert (
        page_ok.lines_source,
        page_ok.lines_rebuilt,
        page_ok.words_source,
        len(page_ok.words),
        page_ok.ink_iou,
    ) == (6, 6, 53, 53, 1.0)
    assert verdict(page_ok, FACSIMILE) == []
    assert verdict(page_ok, SOURCE_PAGINATED) == []

    broken_src = (
        typ_src.replace("#thm-break\n", "")
        .replace("#item-break\n", "")
        .replace("#sub-break\n", "")
    )
    broken_typ = tmp_path / "broken.typ"
    broken_pdf = tmp_path / "broken.pdf"
    broken_typ.write_text(broken_src, encoding="utf-8")
    compile_typst(broken_typ, broken_pdf)
    page_broken: PageParity = compare(
        scan, broken_pdf, {1: [1]}, ocr=tmp_path / "ocr", work=tmp_path / "work"
    )[0]
    assert verdict(page_broken, SOURCE_PAGINATED) == [
        "page offset +14.88,+0.06pt",
        "5 words off by more than 1.5pt",
        "2 baselines off by more than 1.5pt",
    ]
