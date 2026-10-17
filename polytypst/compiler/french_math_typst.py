"""French Mathematical Typst compiler supporting high-standard academic math textbook publishing."""

import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

FRENCH_MATH_HEADER = """
#set document(title: "Cours d'arithmétique", author: "Jean-Pierre Serre")

// --- French Mathematical Monograph Layout (Single Column) ---
#set page(
  paper: "a4",
  columns: 1,
  margin: (top: 2.6cm, bottom: 2.5cm, inside: 2.8cm, outside: 2.5cm),
  header: context {
    let p = counter(page).get().first()
    let ch_on_page = query(selector(heading.where(level: 1))).filter(h => h.location().page() == p)
    if p > 4 and ch_on_page.len() == 0 {
      if calc.even(p) {
        align(left, text(8.5pt, fill: rgb("#555555"), font: "Libertinus Serif")[J.-P. Serre --- Cours d'arithmétique])
      } else {
        let headings = query(selector(heading.where(level: 1)).before(here()))
        let cur_chap = if headings.len() > 0 { headings.last().body } else { [] }
        align(right, text(8.5pt, fill: rgb("#555555"), font: "Libertinus Serif")[#cur_chap])
      }
      line(length: 100%, stroke: 0.4pt + rgb("#cccccc"))
    }
  },
  footer: context {
    let p = counter(page).get().first()
    if p > 2 {
      align(center, text(9pt, fill: rgb("#444444"), font: "Libertinus Serif")[#p])
    }
  }
)

// --- Mathematical Typography ---
#set text(
  font: ("Libertinus Serif", "New Computer Modern"),
  size: 10pt,
  lang: "fr"
)

#set par(
  justify: true,
  first-line-indent: 1.8em,
  leading: 0.92em,
  spacing: 1.15em
)

#let horizontalrule = line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))
#set figure(supplement: [Figure], numbering: "1")

// --- Heading Hierarchy & Textbook Styling ---
#show heading: set text(font: "Libertinus Serif", weight: "bold", fill: black)

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(1.5cm)
  text(17pt, weight: "bold")[#it.body]
  v(0.8cm)
}

#show heading.where(level: 2): it => block(spacing: 1.4em)[
  #v(0.8em)
  #text(13pt, weight: "bold")[#it.body]
  #v(0.4em)
]

#show heading.where(level: 3): it => block(spacing: 1.1em)[
  #v(0.5em)
  #text(11pt, weight: "bold")[#it.body]
  #v(0.2em)
]

// --- High-Standard Theorem & Lemma Styling (Bourbaki / PUF Style) ---
#let math-statement(body, italic-body: true) = block(
  width: 100%,
  above: 1.15em,
  below: 1.15em,
  breakable: true,
)[
  #set par(first-line-indent: 0pt)
  #show strong: set text(style: "normal", weight: "bold")
  #show math.equation: set text(style: "normal")
  #if italic-body [
    #show emph: it => text(style: "italic", it.body)
    #text(style: "italic")[#body]
  ] else [
    #body
  ]
]

#let theorem(body, title: none) = math-statement(body, italic-body: true)
#let lemma(body, title: none) = math-statement(body, italic-body: true)
#let proposition(body, title: none) = math-statement(body, italic-body: true)
#let corollary(body, title: none) = math-statement(body, italic-body: true)
#let definition(body, title: none) = math-statement(body, italic-body: false)

#let proof(body) = block(spacing: 1.1em)[
  #text(weight: "bold", style: "italic")[Démonstration.]
  #h(0.5em)
  #body
  #align(right)[#text(size: 8.5pt)[$square$]]
]

// --- Front Matter (Academic PUF Title Pages) ---
#align(center + horizon)[
  #text(12pt, tracking: 0.2em)[COLLECTION « LE MATHÉMATICIEN »]
  #v(0.3cm)
  #text(10pt)[dirigée par Jean-Pierre Kahane]
  #v(2.5cm)
  #text(26pt, weight: "bold")[COURS D'ARITHMÉTIQUE]
  #v(1.5cm)
  #text(13pt)[par]
  #v(0.2cm)
  #text(16pt, weight: "bold")[JEAN-PIERRE SERRE]
  #v(0.2cm)
  #text(11pt, style: "italic")[Professeur au Collège de France]
  #v(4.0cm)
  #text(11pt, weight: "bold")[PRESSES UNIVERSITAIRES DE FRANCE]
  #v(0.2cm)
  #text(9.5pt)[108, Boulevard Saint-Germain, Paris --- 1970]
]
#pagebreak()

// --- Academic Table des Matières (Table of Contents) ---
#outline(title: [Table des Matières], indent: 1.5em, depth: 3)
#pagebreak()
"""


EQUATION_TAGS_FILTER = Path(__file__).with_name("equation_tags.lua")
EQ_NUMBER = r"\((\d+)\)"
MAX_EQUATION_TAIL = 65
PUNCTUATION = (".", ",", ";", ":")
PAGES_WITH_TRUE_ANGLE_BRACKETS = {12, 132, 170, 172}
REL_PATTERNS = (
    r"=",
    r"\\equiv\b",
    r"\\leqslant\b",
    r"\\leq\b",
    r"\\geqslant\b",
    r"\\geq\b",
    r"\\to\b",
    r"\\mapsto\b",
)


def _tagged_display(body: str, number: str) -> str:
    return f"$${body.strip()} \\tag{{{number}}}$$"


def _tail_to_tex(tail: str) -> str:
    tokens: list[str] = []

    def push(token: str) -> None:
        if token not in PUNCTUATION and (not tokens or tokens[-1] in PUNCTUATION):
            token = rf"\quad {token}"
        tokens.append(token)

    for idx, part in enumerate(re.split(r"\$([^$]+)\$", tail)):
        if idx % 2:
            push(part.strip())
            continue
        lead_punct, words, punct = re.fullmatch(
            r"\s*([.,;:]?)\s*(.*?)\s*([.,;:]?)\s*", part, flags=re.DOTALL
        ).groups()
        if lead_punct:
            tokens.append(lead_punct)
        if words:
            lead_space = " " if tokens and tokens[-1] not in PUNCTUATION else ""
            push(rf"\text{{{lead_space}{words}{punct} }}")
        elif punct:
            tokens.append(punct)
    return " ".join(tokens)


def normalize_equation_markup(text: str, pno: int = 0) -> str:
    text = re.sub(r"(?<!\\)\\\[(.+?)(?<!\\)\\\]", lambda m: f"$${m[1].strip()}$$", text, flags=re.DOTALL)
    text = re.sub(rf"^{EQ_NUMBER}[ \t]*\$\$(.+?)\$\$", lambda m: _tagged_display(m[2], m[1]), text, flags=re.MULTILINE)
    text = re.sub(
        rf"\$\$([^$]+?)\s*\\q?quad\s*{EQ_NUMBER}\s*\$\$",
        lambda m: _tagged_display(m[1], m[2]),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"(\\begin\{aligned\})(.*?)(\\end\{aligned\})",
        lambda m: m[1]
        + re.sub(r"(&(?:(?!\\\\)[^\n&])+?)(?<!&)&(\s*(?:\\text\{|\(\\text\{))", r"\1&&\2", m[2])
        + m[3],
        text,
        flags=re.DOTALL,
    )

    if pno < 128:
        return text

    text = re.sub(
        r"(\([0-9]+\)[ \t]*\$[^$\n]+\$)\n\n((?:pour |si )?\$p\$[^\n]*premier[^\n]*)",
        r"\1, \2",
        text,
    )
    text = re.sub(
        r"\$\$([^\n$]+?)\\tag\{(\d+)\}\$\$\n\n((?:pour |si )?\$p\$[^\n]*premier[^\n]*)",
        lambda m: _tagged_display(f"{m[1].strip()} {_tail_to_tex(', ' + m[3])}", m[2]),
        text,
    )

    chunks = re.split(r"(\n\s*\n)", text)
    for i, chunk in enumerate(chunks):
        para = chunk.strip()
        m_block = re.fullmatch(rf"\$\$\s*{EQ_NUMBER}\s*(?:\\q?quad\b)?\s*([^$]+?)\s*\$\$", para) or re.fullmatch(
            rf"{EQ_NUMBER}\s*\$\$([^$]+)\$\$", para
        )
        if m_block:
            chunks[i] = _tagged_display(m_block[2], m_block[1])
            continue
        m_rows = re.fullmatch(r"\$\$\s*\\begin\{aligned\}(.+?)\\end\{aligned\}\s*\$\$", para, flags=re.DOTALL)
        if m_rows:
            rows = [
                re.fullmatch(rf"\s*{EQ_NUMBER}\s*&(.*?)\s*", row, flags=re.DOTALL)
                for row in re.split(r"\\\\\s*\n", m_rows[1])
            ]
            if all(rows):
                chunks[i] = "\n\n".join(
                    _tagged_display(re.sub(r"&+", r"\\qquad ", row[2].replace("\\quad", "", 1)), row[1]) for row in rows
                )
                continue
        m_inline = re.fullmatch(rf"{EQ_NUMBER}[ \t]*\$([^$]+)\$(.*)", para, flags=re.DOTALL)
        if m_inline and len(m_inline[3].strip()) <= MAX_EQUATION_TAIL:
            chunks[i] = _tagged_display(f"{m_inline[2]} {_tail_to_tex(m_inline[3])}", m_inline[1])
    return "".join(chunks)


def _split_equation_for_alignment(eq: str) -> tuple[str, str, str, str] | None:
    if "\n" in eq.strip() or r"\begin{" in eq:
        return None
    m_tag = re.search(r"\s*(\\tag\{[^}]+\})\s*$", eq)
    tag = m_tag.group(1) if m_tag else ""
    body = eq[: m_tag.start()].strip() if m_tag else eq.strip()

    cond = ""
    m_cond = re.search(
        r"\s+(?:\\qquad\s*|\\quad\s+(?=\\text\{|\(|p\s|\\lambda|n\s|m\s|g_))(.*)$",
        body,
    )
    if m_cond:
        cond = m_cond.group(1).strip()
        body = body[: m_cond.start()].strip()

    depth = 0
    i = 0
    n = len(body)
    rel_pos = None
    while i < n:
        ch = body[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        elif body.startswith(r"\left", i):
            depth += 1
            i += 5
            continue
        elif body.startswith(r"\right", i):
            depth = max(0, depth - 1)
            i += 6
            continue
        elif depth == 0:
            for pat in REL_PATTERNS:
                if re.match(pat, body[i:]):
                    rel_pos = i
                    break
            if rel_pos is not None:
                break
        i += 1

    if rel_pos is None:
        return None
    lhs = body[:rel_pos].strip()
    rhs = body[rel_pos:].strip()
    return (lhs, rhs, cond, tag)


def _format_aligned_cluster(rows: list[tuple[str, str, str, str]]) -> str:
    has_cond = any(r[2] for r in rows)
    has_tag = any(r[3] for r in rows)
    env = "align*" if has_tag else "aligned"
    lines: list[str] = []
    for lhs, rhs, cond, tag in rows:
        line = f"{lhs} &{rhs}" if lhs else f"&{rhs}"
        if has_cond:
            line += f" && {cond}" if cond else " &&"
        if tag:
            line += f" {tag}"
        lines.append(line)
    body = " \\\\\n".join(lines)
    return f"$$\n\\begin{{{env}}}\n{body}\n\\end{{{env}}}\n$$"


def group_consecutive_display_equations(text: str) -> str:
    blocks = list(re.finditer(r"\$\$(.*?)\$\$", text, flags=re.DOTALL))
    if len(blocks) < 2:
        return text

    clusters: list[list[re.Match[str]]] = []
    cur: list[re.Match[str]] = []
    for b in blocks:
        if not cur:
            cur.append(b)
        else:
            between = text[cur[-1].end() : b.start()]
            if between.strip() == "":
                cur.append(b)
            else:
                if len(cur) >= 2:
                    clusters.append(cur)
                cur = [b]
    if len(cur) >= 2:
        clusters.append(cur)

    out = text
    for c in reversed(clusters):
        sub_run: list[tuple[re.Match[str], tuple[str, str, str, str]]] = []
        sub_runs: list[list[tuple[re.Match[str], tuple[str, str, str, str]]]] = []
        for m in c:
            parsed = _split_equation_for_alignment(m.group(1).strip())
            if parsed is not None:
                sub_run.append((m, parsed))
            else:
                if len(sub_run) >= 2:
                    sub_runs.append(sub_run)
                sub_run = []
        if len(sub_run) >= 2:
            sub_runs.append(sub_run)

        for sr in reversed(sub_runs):
            start_idx = sr[0][0].start()
            end_idx = sr[-1][0].end()
            replacement = _format_aligned_cluster([p for _, p in sr])
            out = out[:start_idx] + replacement + out[end_idx:]
    return out


def clean_serre_page(pno: int, raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text or len(text) <= 5:
        return ""

    if pno == 8:
        return "# PREMIÈRE PARTIE — MÉTHODES ALGÉBRIQUES"
    if pno == 102:
        return "# DEUXIÈME PARTIE — MÉTHODES ANALYTIQUES"

    if pno == 11:
        text = text.replace(
            "ii) *Soit $q = p^f$ ($f \\geqslant 1$), et soit $\\Omega$ une clôture algébrique de $\\mathbf{F}_p$",
            "ii) *Soit $q = p^f$ ($f \\geqslant 1$), et soit $\\Omega$ une clôture algébrique de $\\mathbf{F}_p$.*",
        )
        text = text.replace(
            "Sous-corps de $\\Omega$ formé des racines du polynôme $X^q - X$.*",
            "Il existe un unique sous-corps de $\\Omega$ formé des racines du polynôme $X^q - X$.",
        )
        text = text.replace(
            "iii) *Tout corps fini à $q$ éléments est isomorphe à $\\mathbf{F}_q$",
            "iii) *Tout corps fini à $q$ éléments est isomorphe à $\\mathbf{F}_q$.*",
        )
    elif pno == 14:
        text = text.replace(
            "**THÉORÈME 3 (Chevalley-Warning). — Soient**\n\n\\[ f_{\\alpha} \\in \\mathbb{K}[X_1, \\ldots, X_n] \\]\n\n*des polynômes",
            "**THÉORÈME 3 (Chevalley-Warning).** — *Soient $f_{\\alpha} \\in K[X_1, \\ldots, X_n]$ des polynômes",
        )
    elif pno == 16:
        text = text.replace("\\binom{x'}{p}", "\\left(\\frac{x'}{p}\\right)")
        text = text.replace("\\binom{j}{p}", "\\left(\\frac{y}{p}\\right)")
        text = text.replace("\\binom{xy}{p}", "\\left(\\frac{xy}{p}\\right)")
        text = text.replace("\\binom{x}{p}", "\\left(\\frac{x}{p}\\right)")
        text = text.replace("\\mathbf{F}_p^{**}", "\\mathbf{F}_p^{*2}")
    elif pno == 17:
        text = text.replace("- 1 est un carré", "$-1$ est un carré")
        text = text.replace("- 2 est un carré", "$2$ est un carré")
        text = text.replace(
            "\\left(\\frac{\\ell}{p}\\right) = \\left(\\frac{\\ell}{p}\\right) (-1)^{\\varepsilon(\\ell) \\varepsilon(p)}",
            "\\left(\\frac{\\ell}{p}\\right) = \\left(\\frac{p}{\\ell}\\right) (-1)^{\\varepsilon(\\ell) \\varepsilon(p)}",
        )
    elif pno == 18:
        text = text.replace("w^t + z", "w^{t+z}")
        text = text.replace("(-1)^{z(t)}", "(-1)^{\\varepsilon(\\ell)}")
        text = text.replace("(-1)^{\\varepsilon(t)}", "(-1)^{\\varepsilon(\\ell)}")
        text = text.replace(
            "\\binom{x}{z} w^{xp} = \\sum_{z \\in \\mathbb{F}_{\\ell}} \\left(\\frac{zb^{-1}}{\\ell}\\right)",
            "\\left(\\frac{x}{\\ell}\\right) w^{xp} = \\sum_{z \\in \\mathbb{F}_{\\ell}} \\left(\\frac{zp^{-1}}{\\ell}\\right)",
        )
    elif pno == 20:
        text = text.replace(
            "**LEMME (Gauss).** $-\\left(\\frac{a}{p}\\right) = \\prod_{s \\in \\mathbb{S}} e_s(a)$.",
            "**LEMME (Gauss).** — $\\left(\\frac{a}{p}\\right) = \\prod_{s \\in S} e_s(a)$.",
        )
    elif pno == 24:
        text = text.replace("\\Lambda_n", "A_n")
    elif pno == 31:
        text = text.replace(
            "**COROLLAIRE 3. — Supposons $p = 2$. Soit**\n\n$$\nf = \\sum a_{ij} X_i X_j\n$$\n\navec",
            "**COROLLAIRE 3.** — Supposons $p = 2$. Soit $f = \\sum a_{ij} X_i X_j$, avec",
        )
    elif pno == 32:
        text = text.replace("x^p^{-1} = 1", "x^{p-1} = 1")
    elif pno == 40:
        text = text.replace("p^x u", "p^\\alpha u")
        text = text.replace("\\chi \\beta \\varepsilon(v)", "\\alpha \\beta \\varepsilon(p)")
        text = text.replace("formule $\\vee$ )", "formule v)")
    elif pno == 47:
        text = text.replace("\\prod_{i=1}^{4 = n}", "\\prod_{i=1}^{i=n}")
        text = text.replace("tout entier $\\mathbb{N} \\geqslant 0$", "tout entier $N \\geqslant 0$")
        text = text.replace("\\geqslant \\mathbb{N}", "\\geqslant N")
    elif pno == 48:
        text = text.replace("m_i = p_1^N", "m_i = p_i^N")
    elif pno == 65:
        text = text.replace("(a_4, a_j)", "(a_i, a_j)")
    elif pno == 68:
        text = text.replace(
            "$$(-1, -1) \\langle -1, a_1 \\rangle (-1, a_2) \\langle a_3, a_3 \\rangle$$\n\n$$(a_1, a_2) (a_1, a_3) \\langle a_2, a_3 \\rangle = 1.$$",
            "$$(-1, -1) (-1, a_1) (-1, a_2) (a_3, a_3) (a_1, a_2) (a_1, a_3) (a_2, a_3) = 1.$$",
        )
    elif pno == 70:
        text = text.replace(
            "$$\nn(\\mathbf{X}, \\mathbf{Y}, \\mathbf{Z}) = \\mathbf{X}^2 \\mathbf{Y} \\mathbf{Z} + \\mathbf{Y}^2 \\mathbf{Z} \\mathbf{X} + \\mathbf{Z}^2 \\mathbf{X} \\mathbf{Y} + \\mathbf{X}^2 \\mathbf{Y}^2\n$$\n\n$$\n+ \\mathbf{Y}^2 \\mathbf{Z}^2 + \\mathbf{Z}^2 \\mathbf{X}^2 - \\mathbf{X}^4 - \\mathbf{Y}^4 - \\mathbf{Z}^4\n$$",
            "$$\\begin{aligned}\nn(\\mathbf{X}, \\mathbf{Y}, \\mathbf{Z}) &= \\mathbf{X}^2 \\mathbf{Y} \\mathbf{Z} + \\mathbf{Y}^2 \\mathbf{Z} \\mathbf{X} + \\mathbf{Z}^2 \\mathbf{X} \\mathbf{Y} + \\mathbf{X}^2 \\mathbf{Y}^2 \\\\\n&\\quad + \\mathbf{Y}^2 \\mathbf{Z}^2 + \\mathbf{Z}^2 \\mathbf{X}^2 - \\mathbf{X}^4 - \\mathbf{Y}^4 - \\mathbf{Z}^4\n\\end{aligned}$$",
        )
        text = text.replace(
            "$$\nf(\\mathbf{X}_1, \\ldots, \\mathbf{X}_9) = n(\\mathbf{X}_1, \\mathbf{X}_2, \\mathbf{X}_3)\n$$\n\n$$\n+ n(\\mathbf{X}_4, \\mathbf{X}_5, \\mathbf{X}_6) + n(\\mathbf{X}_7, \\mathbf{X}_8, \\mathbf{X}_9) ;\n$$",
            "$$f(\\mathbf{X}_1, \\ldots, \\mathbf{X}_9) = n(\\mathbf{X}_1, \\mathbf{X}_2, \\mathbf{X}_3) + n(\\mathbf{X}_4, \\mathbf{X}_5, \\mathbf{X}_6) + n(\\mathbf{X}_7, \\mathbf{X}_8, \\mathbf{X}_9) ;$$",
        )
    elif pno == 72:
        text = text.replace(
            "$n = 1, \\quad \\varepsilon = 1; \\quad \\begin{array}{lll} ou & n = 2, & d \\neq -1; \\\\ ou & n = 2, & \\varepsilon = 1; & ou & n \\geqslant 3. \\end{array}$",
            "$$\\begin{array}{lll} & n = 1, & \\varepsilon = 1 ; \\\\ \\text{ou} & n = 2, & d \\neq -1 ; \\\\ \\text{ou} & n = 2, & \\varepsilon = 1 ; \\\\ \\text{ou} & n \\geqslant 3. & \\end{array}$$",
        )
    elif pno == 73:
        text = text.replace("(-1)^{s/s - 1)/2}", "(-1)^{s(s - 1)/2}")
    elif pno == 83:
        text = text.replace("\\sum_{i-1}^{i-8}", "\\sum_{i=1}^{i=3}").replace("\\sum_{i-1}^{i-3}", "\\sum_{i=1}^{i=3}")
    elif pno == 85:
        text = text.replace("'BAB", "{}^t B A B")
        text = text.replace(
            "$$\n\\begin{aligned}\n(x + x') \\cdot (y + y') &= x \\cdot y + x' \\cdot y' \\\\\n\\text{si } x, y \\in E \\quad \\text{et} \\quad x', y' \\in E'.\n\\end{aligned}\n$$",
            "$$(x + x') \\cdot (y + y') = x \\cdot y + x' \\cdot y' \\quad \\text{si } x, y \\in E \\text{ et } x', y' \\in E'.$$",
        )
    elif pno == 107:
        text = text.replace(
            "\\sum_{x \\in \\widehat{G}} \\chi(x) &= n & si & x = 1 \\\\\n&= 0 & si & x \\neq 1.",
            "\\sum_{\\chi \\in \\widehat{G}} \\chi(x) &= n && \\text{si } x = 1 \\\\\n&= 0 && \\text{si } x \\neq 1.",
        )
    elif pno == 108:
        text = text.replace("\\binom{x}{p}", "\\left(\\frac{x}{p}\\right)")
        text = re.sub(
            r"<table>.*?</table>",
            lambda _: "$$\n\\begin{cases}\n\\chi(x) = 1 & \\text{si } x \\equiv \\pm 1 \\pmod{7} \\\\\n\\chi(x) = e^{2\\pi i/3} & \\text{si } x \\equiv \\pm 2 \\pmod{7} \\\\\n\\chi(x) = e^{4\\pi i/3} & \\text{si } x \\equiv \\pm 3 \\pmod{7}.\n\\end{cases}\n$$",
            text,
            flags=re.S,
        )
    elif pno == 109:
        text = text.replace("\\int_{\\mathbb{C}}", "\\int_C")
    elif pno == 110:
        text = text.replace("A_{m.n-1}", "A_{m,n-1}")
    elif pno == 111:
        text = text.replace("Arg $(z - z_0) \\leq \\alpha$", "$\\left|\\mathrm{Arg}(z - z_0)\\right| \\leq \\alpha$")
    elif pno == 112:
        text = text.replace("e^{-\\lambda_m' z}", "e^{-\\lambda_{m'} z}")
        text = text.replace("(e^{-\\lambda_n z} - e^{-\\lambda_{n+1} z})", "(e^{-\\lambda_n x} - e^{-\\lambda_{n+1} x})")
    elif pno == 118:
        text = re.sub(
            r"<table>.*?</table>",
            lambda _: "$$\n\\begin{aligned}\n\\zeta(-2n) &= 0 && \\text{si } n > 0 \\\\\n\\zeta(1-2n) &= (-1)^n B_n / 2n && \\text{si } n > 0.\n\\end{aligned}\n$$",
            text,
            flags=re.S,
        )
    elif pno == 120:
        text = text.replace("\\varphi(m)|f(p)", "\\varphi(m)/f(p)")
    elif pno == 123:
        text = text.replace("Soit $\\mathbb{P}_a l'ensemble", "Soit $\\mathbb{P}_a$ l'ensemble")
    elif pno == 130:
        text = text.replace("La figure de la page précédente", "[La figure 1](#fig:1)")
        text = text.replace("les transformés de D", "les transformés de $D$")
        text = text.replace("du groupe G.", "du groupe $G$.")
        text = text.replace(
            "que D est un domaine fondamental pour l'action de G sur le demi-plan H.",
            "que $D$ est un domaine fondamental pour l'action de $G$ sur le demi-plan $H$.",
        )
    elif pno == 137:
        text = text.replace("\\sum_{\\gamma \\in \\Gamma} 1/\\gamma^{2k}", "\\sum_{\\gamma \\in \\Gamma}' 1/\\gamma^{2k}")
    elif pno == 138:
        text = text.replace(
            "|mz + n|^2 = m^2 z \\bar{z} + 2mnR(z) + n^2 \\\\\n\\geq m^2 - mn + n^2 = |m\\varphi - n|^2.",
            "\\begin{aligned}\n|mz + n|^2 &= m^2 z \\bar{z} + 2mnR(z) + n^2 \\\\\n&\\geq m^2 - mn + n^2 = |m\\rho - n|^2.\n\\end{aligned}",
        )
        text = text.replace("|m\\varphi - n|", "|m\\rho - n|")
    elif pno in (141, 142):
        text = text.replace("métromorphe", "méromorphe")
        text = text.replace("nizéro", "ni zéro")
        text = text.replace("\\int_{E} \\frac{df}{f}", "\\int_{E}^{A} \\frac{df}{f}")
        text = text.replace("tel celui représenté ci-contre", "tel celui représenté sur [la figure 2](#fig:2)")
        text = text.replace("comme l'indique la figure", "comme l'indique [la figure 2](#fig:2)")
        text = text.replace("l'arc BB'", "l'arc $BB'$")
        text = text.replace("des arcs CC' et DD'", "des arcs $CC'$ et $DD'$")
        text = text.replace("des arcs BB', CC', DD'", "des arcs $BB'$, $CC'$, $DD'$")
        text = text.replace("l'arc AB en l'arc ED'", "l'arc $AB$ en l'arc $ED'$")
        text = text.replace("l'arc B'C en l'arc DC'", "l'arc $B'C$ en l'arc $DC'$")
        target_eq = "$$\\frac{1}{2i\\pi} \\int_{\\mathcal{C}} \\frac{df}{f} = \\sum_{p \\in H/G} v_p(f).$$"
        fig2_md = (
            target_eq
            + "\n\n![Contour d'intégration $\\mathcal{C}$ sur le domaine fondamental $D$](figures/serre_fig_2_contour.svg){#fig:2}"
        )
        text = text.replace(target_eq, fig2_md)
    elif pno == 139:
        text = text.replace("\\Delta = g_2^8 - 27g_3^2", "\\Delta = g_2^3 - 27g_3^2")
    elif pno == 144:
        text = text.replace("\\sum_{p \\in H_1 G}", "\\sum_{p \\in H/G}")
        text = text.replace("\\mathfrak{C}. G_k", "\\mathbf{C} G_k")
        text = text.replace("\\frac{1}{3} v_p(f)", "\\frac{1}{3} v_\\rho(f)").replace("v_p(G_2) = 1", "v_\\rho(G_2) = 1")
    elif pno == 148:
        text = text.replace("2^2 3^3 1823 := 196884", "2^2 \\cdot 3^3 \\cdot 1823 = 196884")
        text = text.replace("2^{11} 5.2099 = 21493760.", "2^{11} \\cdot 5 \\cdot 2099 = 21493760.")
    elif pno == 150:
        text = text.replace("\\frac{1}{n(z + n)^k}", "\\frac{1}{(z + n)^k}")
        text = text.replace("\\sum_{a|n} d^k", "\\sum_{d|n} d^k")
    elif pno == 151:
        text = text.replace("2^3 \\cdot 33", "2^3 \\cdot 3^3")
        text = text.replace(
            "$$\n\\begin{aligned}\nE_2 &= 1 + 240 \\sum_{n-1}^{\\infty} \\sigma_3(n) q^n, & g_2 &= (2\\pi)^4 \\frac{1}{2^2 \\cdot 3} E_2 \\\\\nE_3 &= 1 - 504 \\sum_{n=1}^{\\infty} \\sigma_5(n) q^n, & g_3 &= (2\\pi)^6 \\frac{1}{2^3 \\cdot 3^3} E_3\n\\end{aligned}\n$$",
            "$$E_2 = 1 + 240 \\sum_{n=1}^{\\infty} \\sigma_3(n) q^n, \\quad g_2 = (2\\pi)^4 \\frac{1}{2^2 \\cdot 3} E_2$$\n\n$$E_3 = 1 - 504 \\sum_{n=1}^{\\infty} \\sigma_5(n) q^n, \\quad g_3 = (2\\pi)^6 \\frac{1}{2^3 \\cdot 3^3} E_3$$",
        )
    elif pno == 152:
        text = text.replace("65520 = 24.3^2.5.7.13", "65520 = 2^4 \\cdot 3^2 \\cdot 5 \\cdot 7 \\cdot 13")
        text = text.replace("\\sigma_3(n) \\sigma_5(n-m)", "\\sigma_3(m) \\sigma_5(n-m)")
    elif pno == 154:
        text = text.replace("(1 - q)^n$24.", "(1 - q^n)^{24}$.")
    elif pno == 155:
        text = text.replace("G_1(z) = \\sum_n \\sum_{m>n}'", "G_1(z) = \\sum_n \\sum_m'")
    elif pno == 156:
        text = text.replace("$G_1(-1/z) = z^2 G(-1/z)$", "$G_1(-1/z) = z^2 G(z)$")
        text = text.replace(
            "$$\\frac{1}{(m-1+nz)} \\frac{1}{\\langle m + nz \\rangle} - \\frac{1}{\\langle m + nz \\rangle^2}$$\n\n$$= \\frac{1}{\\langle m + nz \\rangle^2 (m-1+nz)}$$",
            "$$\\frac{1}{(m-1+nz)(m+nz)} - \\frac{1}{(m+nz)^2} = \\frac{1}{(m+nz)^2 (m-1+nz)}$$",
        )
    elif pno == 157:
        text = text.replace("\\frac{dF(-1/z)}{d(-1/z)}", "\\frac{dF(-1/z)}{F(-1/z)}")
        text = text.replace("\\frac{dF(z)}{dz} + 12", "\\frac{dF(z)}{F(z)} + 12")
    elif pno == 158:
        text = text.replace("\\tau(n) \\equiv n \\sigma_8(n)", "\\tau(n) \\equiv n \\sigma_3(n)")
        text = text.replace("suivant : $n=1$", "suivant :")
    elif pno == 160:
        text = text.replace("R_\\lambda R_{\\mu\\lambda}", "R_\\lambda R_\\mu")
        text = text.replace("T(\\hat{p})", "T(p)")
        text = text.replace("\\Gamma^r", "\\Gamma''").replace("\\Gamma^w", "\\Gamma''")
    elif pno == 161:
        text = text.replace("\\mathbb{R}_\\lambda", "R_\\lambda").replace("\\mathbb{R}_p", "R_p")
    elif pno == 163:
        text = text.replace("ad-b", "ad=n")
    elif pno == 166:
        text = text.replace("p^{2k} - 1 - 2s", "p^{2k-1-2s}")
    elif pno == 169:
        text = text.replace("a^{2k-1} |a^s d^s", "a^{2k-1} / a^s d^s")
    elif pno == 170:
        text = text.replace("dx dy (y^2", "dx dy / y^2")
        text = text.replace(
            "$\\operatorname{E}_2^x \\operatorname{E}_8^3$, avec $2x + 3\\beta = k$",
            "$\\mathrm{E}_2^\\alpha \\mathrm{E}_3^\\beta$, avec $2\\alpha + 3\\beta = k$",
        )
    elif pno == 173:
        text = text.replace("\\mu(V/|\\Gamma|)", "\\mu(V/\\Gamma)")
        text = text.replace("f = e^{-\\pi |x|_1^2 + \\ldots + x_n^2}.", "f = e^{-\\pi (x_1^2 + \\ldots + x_n^2)}.")
    elif pno == 177:
        text = text.replace("240 \\sigma_8(m)", "240 \\sigma_3(m)")
    elif pno == 179:
        text = text.replace("-243^{2}5.7.13/691.", "-2^4 \\cdot 3^2 \\cdot 5 \\cdot 7 \\cdot 13 / 691.")
        text = text.replace("273^{3}5^{3}/691.", "2^7 \\cdot 3^3 \\cdot 5^3 / 691.")
        text = text.replace("210^{3}.227/691.", "2^{10} \\cdot 3 \\cdot 227 / 691.")
    elif pno in (180, 181, 182):
        text = text.replace("C. JACONI", "C. JACOBI")
        text = text.replace("algebraischer Zahlkörper", "algebraischen Zahlkörper")
        text = text.replace("Geometrie Algebra", "Geometric Algebra")
        text = text.replace("K. PRACIAR", "K. PRACHAR")
        text = text.replace("A. WELL", "A. WEIL")
    elif pno in (184, 185):
        text = text.replace("**Z, N, Q, R, C**", "$\\mathbf{Z}, \\mathbf{N}, \\mathbf{Q}, \\mathbf{R}, \\mathbf{C}$")
        text = text.replace(
            "**A\\*** : ensemble des éléments inversibles d'un anneau A.",
            "$A^*$ : ensemble des éléments inversibles d'un anneau $A$.",
        )
        text = text.replace("**A\\***", "$A^*$")
        text = text.replace("**F_q**", "$\\mathbf{F}_q$")
        text = text.replace("**Z_p**", "$\\mathbf{Z}_p$")
        text = text.replace("**U = Z_p^***", "$U = \\mathbf{Z}_p^*$")
        text = text.replace("**Q_p**", "$\\mathbf{Q}_p$")
        text = text.replace("\\binom{x}{p}", "\\left(\\frac{x}{p}\\right)")
        text = text.replace("\\widehat{\\otimes}", "\\hat{\\oplus}")
        text = text.replace("I_\\pm, I_-, U, \\Gamma_{S}, \\Gamma_{S^n}", "I_+, I_-, U, \\Gamma_8, \\Gamma_{16}")
        text = text.replace("q = e^{2\\pi i\\varepsilon}", "q = e^{2\\pi i z}")
        text = text.replace("\\Delta = g_3^2 - 27g_3^2", "\\Delta = g_2^3 - 27g_3^2")
    elif pno == 186:
        text = text.replace("Dirichlet (série de —) : IV.2.2.", "Dirichlet (série de —) : VI.2.2.")

    text = text.replace("le demi-plan H", "le demi-plan $H$")
    text = text.replace("mémorophe", "méromorphe").replace("holomorphé", "holomorphe")
    text = text.replace("\\text{si} \\quad", "\\text{si }").replace("\\text{et} \\quad", "\\text{et }")
    text = text.replace("\\mathbb{R}(", "R(")
    text = re.sub(
        r"\\mathbb\{([A-Za-z])\}",
        lambda m: f"\\mathbf{{{m.group(1)}}}" if m.group(1) in "ZNQRCF" else m.group(1),
        text,
    )
    for abs_expr in ("a_n", "\\tau(p)", "f(z)", "mz + n", "m\\rho - n", "\\gamma"):
        text = text.replace(f"|{abs_expr}|", f"\\left|{abs_expr}\\right|")
    text = re.sub(
        r"\$+[^$]+\$+",
        lambda m_math: re.sub(
            r"(?<!\\left)(?<!\\right)\|([^\n|$=<>;:]+?)(?<!\\left)(?<!\\right)\|",
            lambda m_bar: (
                m_bar.group(0)
                if any(
                    bad in m_bar.group(1)
                    for bad in (
                        r"\leq",
                        r"\geq",
                        r"\in",
                        r"\subset",
                        r"\to",
                        r"\Leftrightarrow",
                        r"\mid",
                        r"\nmid",
                        "&",
                        r"\\",
                    )
                )
                else rf"\left|{m_bar.group(1).strip()}\right|"
            ),
            m_math.group(0),
        ),
        text,
    )
    text = text.replace("\\varprojlim_n", "\\underset{\\longleftarrow}{\\lim}_n")
    text = text.replace("\\varprojlim", "\\underset{\\longleftarrow}{\\lim}")
    text = text.replace("\\varinjlim", "\\underset{\\longrightarrow}{\\lim}")
    text = text.replace("\\cotg", "\\operatorname{cotg}")
    text = re.sub(r"_\{([a-z])-(\d)\}\^\{\\infty\}", r"_{\1=\2}^{\\infty}", text)
    if pno not in PAGES_WITH_TRUE_ANGLE_BRACKETS:
        text = text.replace("\\langle", "(").replace("\\rangle", ")")

    text = re.sub(
        r"^#\s*CHAPITRE\s+V\s*\n+##\s*FORMES QUADRATIQUES ENTIÈRES\s*\n+###\s*A DISCRIMINANT\s*\$\\pm\s*1\$",
        r"# CHAPITRE V — FORMES QUADRATIQUES ENTIÈRES À DISCRIMINANT $\\pm 1$",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"^#\s*CHAPITRE\s+([IVX]+)\s*\n+##\s*([^\n]+)",
        r"# CHAPITRE \1 — \2",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"^##\s*APPENDICE\s*\n+###\s*Sommes de trois carrés",
        "## Appendice : Sommes de trois carrés",
        text,
        flags=re.M,
    )

    text = normalize_equation_markup(text, pno)
    lines = text.splitlines()
    out_lines: List[str] = []
    for line in lines:
        s = line.strip()
        if re.match(r"^J\.-P\.\s*SERRE\s*\d*$", s, re.I):
            continue
        if re.match(r"^\d+\s+COURS D'ARITHMÉTIQUE$", s, re.I):
            continue
        if re.match(
            r"^(?:CORPS\s+.*|SYMBOLE DE HILBERT|FORMES\s+.*|LE THÉORÈME\s+.*|INTRODUCTION|BIBLIOGRAPHIE|INDEX\s+.*)\s+\d+$",
            s,
            re.I,
        ):
            continue
        if pno == 40 and s == "# SYMBOLE DE HILBERT":
            continue
        if pno == 182 and s.upper() == "# BIBLIOGRAPHIE":
            continue

        if pno == 180 and s.lower() == "# bibliographie":
            out_lines.append("# BIBLIOGRAPHIE")
            continue
        if pno == 184 and s.lower() == "# index des notations":
            out_lines.append("# INDEX DES NOTATIONS")
            continue
        if pno == 186 and s.lower() == "# index terminologique":
            out_lines.append("# INDEX TERMINOLOGIQUE")
            continue
        if pno == 19 and s == "## APPENDICE":
            out_lines.append("## Appendice")
            continue
        if pno == 181 and s in ("Formes quadratiques", "Fonctions L et séries de Dirichlet"):
            out_lines.append(f"## {s}")
            continue

        m_sec = re.match(r"^(?:#+\s*)?(§\s*\d+\..*)$", s)
        if m_sec:
            out_lines.append(f"## {m_sec.group(1)}")
            continue

        m_sub = re.match(r"^(?:#+\s*)?(\d+\.\d+\.\s+[A-ZÉÈÊÀÂÎÔÛÇ*].*)$", s)
        if m_sub and pno < 180:
            out_lines.append(f"### {m_sub.group(1)}")
            continue

        if s.startswith("#"):
            if re.match(r"^#\s+(?:INTRODUCTION|PREMIÈRE PARTIE|DEUXIÈME PARTIE|CHAPITRE\s+[IVX]+|BIBLIOGRAPHIE|INDEX\s+)", s):
                out_lines.append(s)
            elif re.match(r"^##\s+(?:Appendice|Quelques classiques|Corps de nombres|Formes quadratiques|Fonctions )", s):
                out_lines.append(s)
            else:
                demoted = re.sub(r"^#+\s*", "", s)
                out_lines.append(f"**{demoted}**")
            continue

        m_thm = re.match(
            r"^\*{0,2}(THÉORÈME|Théorème|PROPOSITION|Proposition|LEMME|Lemme|COROLLAIRE|Corollaire|DÉFINITION|Définition)"
            r"(\s*[0-9A-Z']*)\*{0,2}(\s*(?:\([^)]+\))?)\s*\.?\*{0,2}\s*(?:—|--|-)\s*(.*)$",
            s,
        )
        if m_thm:
            kw = m_thm.group(1).upper()
            num = m_thm.group(2).strip()
            note = m_thm.group(3).strip()
            rest = m_thm.group(4).strip()
            label = f"{kw}{(' ' + num) if num else ''}{(' ' + note) if note else ''}."
            out_lines.append(f"**{label}** — {rest}")
            continue

        out_lines.append(line)

    if pno in (184, 185, 186, 187):
        non_empty = [l.strip() for l in out_lines if l.strip()]
        return "\n\n".join(non_empty).strip()

    cleaned_page = "\n".join(out_lines).strip()
    if pno == 129:
        cleaned_page += (
            "\n\n![Domaine fondamental $D$ du groupe modulaire $\\mathrm{SL}_2(\\mathbf{Z})/\\{\\pm 1\\}$]"
            "(figures/serre_fig_1_domaine_fondamental.svg){#fig:1}"
        )
    return cleaned_page


def stitch_serre_pages(pages: List[Tuple[int, str]]) -> str:
    if not pages:
        return ""
    acc = pages[0][1]
    for pno, cur in pages[1:]:
        acc_r = acc.rstrip()
        cur_l = cur.lstrip()
        if pno >= 180 or cur_l.startswith("#"):
            acc = acc_r + "\n\n" + cur_l
            continue
        if re.search(r"[a-zA-ZéèêëàâîïôûùçÉÈÊËÀÂÎÏÔÛÙÇ]-$", acc_r):
            acc = acc_r[:-1] + cur_l
            continue
        last_line = acc_r.splitlines()[-1].strip()
        first_line = cur_l.splitlines()[0].strip()
        ends_complete = (
            last_line.endswith((".", "!", "?", ":", "$$", "*"))
            or last_line.startswith("#")
            or last_line.startswith("![")
        )
        starts_new_block = (
            first_line.startswith(("#", "**", "$$", "![", "*Remarque", "*Exemple"))
            or bool(re.match(r"^(?:[0-9]+\)|[ivx]+\)|[a-z]\))\s", first_line))
        )
        if not ends_complete and not starts_new_block:
            acc = acc_r + " " + cur_l
        else:
            acc = acc_r + "\n\n" + cur_l
    return group_consecutive_display_equations(acc) + "\n"


def _is_balanced_typst(s: str) -> bool:
    return len(re.findall(r"(?<!\\)\[", s)) == len(re.findall(r"(?<!\\)\]", s))


def wrap_serre_theorems_in_typst(typst_body: str) -> str:
    typst_body = re.sub(r"(^=+ [^\n]+\n(?:<[^>]+>\n)?)(?!\n)", r"\1\n", typst_body, flags=re.M)
    blocks = typst_body.split("\n\n")
    env_map = {
        "THÉORÈME": "theorem",
        "PROPOSITION": "proposition",
        "LEMME": "lemma",
        "COROLLAIRE": "corollary",
        "DÉFINITION": "definition",
    }
    out_blocks: List[str] = []
    i = 0
    n = len(blocks)
    while i < n:
        blk = blocks[i]
        s = blk.strip()
        matched_env = None
        for kw, env_name in env_map.items():
            if re.match(rf"^(?:#strong\[)?{kw}\b", s, re.I):
                matched_env = env_name
                break
        if matched_env and _is_balanced_typst(s):
            s = re.sub(
                r"^(#strong\[[^\]]+\])\s*---",
                r'\1 #text(style: "normal")[---]',
                s,
                count=1,
            )
            parts = [s]
            j = i + 1
            while j < n:
                nxt = blocks[j].strip()
                if not nxt or not _is_balanced_typst(nxt):
                    break
                if re.match(
                    r"^(?:=+\s|#strong\[(?:THÉORÈME|PROPOSITION|LEMME|COROLLAIRE|DÉFINITION|Démonstration|Remarque|Exemple)|#emph\[(?:Démonstration|Remarque|Exemple))",
                    nxt,
                    re.I,
                ):
                    break
                prev = parts[-1].rstrip()
                is_sub_item = bool(re.match(r"^(?:#emph\[)?(?:ii|iii|iv|b|c|d|2|3)\)\s", nxt))
                is_math_block = nxt.startswith(("$", "#block(", "#[#set math.equation"))
                prev_incomplete = prev.endswith((":", ":]", ",", ";")) or (
                    not prev.endswith((".", ".)", ".]", "$", "}", ")"))
                )
                if is_sub_item or (is_math_block and prev_incomplete):
                    parts.append(nxt)
                    j += 1
                    if is_math_block and j < n:
                        after_math = blocks[j].strip()
                        if (
                            after_math
                            and _is_balanced_typst(after_math)
                            and (
                                after_math[0].islower()
                                or after_math.startswith("#emph[")
                                and len(after_math) > 6
                                and after_math[6].islower()
                            )
                        ):
                            parts.append(after_math)
                            j += 1
                    continue
                break
            joined = "\n\n".join(parts)
            out_blocks.append(f"#{matched_env}[\n{joined}\n]")
            i = j
            continue
        out_blocks.append(blk)
        i += 1
    return "\n\n".join(out_blocks)


class FrenchMathTypstCompiler:
    def __init__(self, markdown_dir: Path):
        self.markdown_dir = markdown_dir

    def convert_markdown_to_typst_body(self, full_md_path: Path) -> str:
        """Use pandoc to accurately convert LaTeX math Markdown into native Typst syntax."""
        cmd = [
            "pandoc", str(full_md_path),
            "-f", "markdown",
            "-t", "typst",
            "--lua-filter", str(EQUATION_TAGS_FILTER),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Pandoc conversion failed:\n{res.stderr}")
        out_text = res.stdout
        out_text = out_text.replace("angle.l", "chevron.l").replace("angle.r", "chevron.r")
        out_text = re.sub(r"\bsect\b", "inter", out_text)
        out_text = out_text.replace("times.circle", "⊗")
        out_text = out_text.replace("plus.circle", "⊕")
        out_text = out_text.replace("dot.circle", "⊙")
        out_text = re.sub(
            r"upright\(([A-Za-z]+(?:\s+[A-Za-z]+)+)\)",
            lambda m: f'upright("{m.group(1).replace(" ", "")}")',
            out_text,
        )
        out_text = re.sub(r"#link\(<fig:(\d+)>\)\[[^\]]+\];?", r"@fig-\1", out_text)
        out_text = re.sub(r"<fig:(\d+)>", r"<fig-\1>", out_text)
        out_text = wrap_serre_theorems_in_typst(out_text)
        return out_text

    def assemble_canonical_book(self, out_typ_path: Path) -> Path:
        out_typ_path.parent.mkdir(parents=True, exist_ok=True)

        # Canonical page ordering according to Serre's Table of Contents:
        # Exclude blank/hallucinated flyleaves (p_001, p_002, p_003, p_007, p_008)
        # Exclude duplicate printed TOC at end (p_188, p_189) which is now generated in Frontmatter
        # Exclude publisher advertisement catalogue (p_190, p_191, p_192)
        valid_page_indices = list(range(5, 188))

        print(f"Assembling {len(valid_page_indices)} canonical pages...")

        cleaned_pages: List[Tuple[int, str]] = []
        for pno in valid_page_indices:
            p_file = self.markdown_dir / f"p_{pno:03d}.md"
            if p_file.exists():
                raw = p_file.read_text(encoding="utf-8", errors="ignore")
                cleaned = clean_serre_page(pno, raw)
                if cleaned:
                    cleaned_pages.append((pno, cleaned))

        combined_md_path = out_typ_path.parent / "combined_serre.md"
        stitched_md = stitch_serre_pages(cleaned_pages)
        combined_md_path.write_text(stitched_md, encoding="utf-8")

        # Convert to Typst via Pandoc
        typst_body = self.convert_markdown_to_typst_body(combined_md_path)

        # Prepend French Mathematical styling, Front Matter, and dynamic Table des Matières
        full_typst = FRENCH_MATH_HEADER + "\n\n" + typst_body

        with open(out_typ_path, "w", encoding="utf-8") as fp:
            fp.write(full_typst)

        out_tex_path = out_typ_path.with_suffix(".tex")
        subprocess.run(
            [
                "pandoc",
                str(combined_md_path.resolve()),
                "-f",
                "markdown",
                "-t",
                "latex",
                "--standalone",
                "-V",
                "documentclass=book",
                "-V",
                "lang=fr",
                "-o",
                str(out_tex_path.resolve()),
            ],
            check=True,
            cwd=str(out_typ_path.parent.resolve()),
        )
        tex_text = out_tex_path.read_text(encoding="utf-8")
        tex_text = re.sub(r"\\hyperref\[fig:(\d+)\]\{[^\}]+?\}", r"Figure~\\ref{fig:\1}", tex_text)
        tex_text = re.sub(r"\\\[\s*(\\begin\{align\*\}[\s\S]*?\\end\{align\*\})\s*\\\]", r"\1", tex_text)
        tex_text = re.sub(
            r"(^\\textbf\{(?:THÉORÈME|PROPOSITION|LEMME|COROLLAIRE)[^}]*\}\s*---\s*)(?!\\emph\{)([^\n]+(?:\n(?![\n\\])[^\n]+)*)",
            r"\1\\emph{\2}",
            tex_text,
            flags=re.M,
        )
        out_tex_path.write_text(tex_text, encoding="utf-8")

        out_epub_path = out_typ_path.with_suffix(".epub")
        subprocess.run(
            [
                "pandoc",
                str(combined_md_path.resolve()),
                "-f",
                "markdown",
                "-t",
                "epub3",
                "--mathml",
                "--lua-filter",
                str(EQUATION_TAGS_FILTER),
                "--toc",
                "--toc-depth=3",
                "--metadata",
                "title=Cours d'arithmétique",
                "--metadata",
                "author=Jean-Pierre Serre",
                "--metadata",
                "lang=fr",
                f"--resource-path={out_typ_path.parent.resolve()}",
                "-o",
                str(out_epub_path.resolve()),
            ],
            check=True,
            cwd=str(out_typ_path.parent.resolve()),
        )

        return out_typ_path

    def compile_pdf(self, typst_path: Path, output_pdf: Path) -> Path:
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "nix", "--extra-experimental-features", "nix-command flakes", "shell", "nixpkgs#typst",
            "--command", "typst", "compile", str(typst_path.resolve()), str(output_pdf.resolve())
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(typst_path.parent.resolve()))
        if res.returncode != 0:
            raise RuntimeError(f"Typst compilation failed:\n{res.stderr}")
        return output_pdf

