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
#show heading: set text(font: "Libertinus Serif", weight: "bold")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(1.5cm)
  text(18pt, weight: "bold", fill: rgb("#0f172a"))[#it.body]
  v(0.8cm)
}

#show heading.where(level: 2): it => block(spacing: 1.4em)[
  #v(0.8em)
  #text(13pt, weight: "bold", fill: rgb("#1e293b"))[#it.body]
  #v(0.4em)
]

#show heading.where(level: 3): it => block(spacing: 1.1em)[
  #v(0.5em)
  #text(11pt, weight: "bold", fill: rgb("#334155"))[#it.body]
  #v(0.2em)
]

// --- High-Standard Theorem & Lemma Styling (Bourbaki / Springer GTM Style) ---
#let theorem(body, title: none) = block(
  width: 100%,
  stroke: (left: 2.5pt + rgb("#2563eb")),
  inset: (left: 0.9em, y: 0.5em),
  spacing: 1.3em,
  fill: rgb("#f8fafc")
)[
  #if title != none [
    #text(weight: "bold", fill: rgb("#1d4ed8"))[Théorème (#title)]
    #v(0.2em)
  ]
  #text(style: "italic")[#body]
]

#let lemma(body, title: none) = block(
  width: 100%,
  stroke: (left: 2.5pt + rgb("#0284c7")),
  inset: (left: 0.9em, y: 0.5em),
  spacing: 1.3em,
  fill: rgb("#f8fafc")
)[
  #if title != none [
    #text(weight: "bold", fill: rgb("#0369a1"))[Lemme (#title)]
    #v(0.2em)
  ]
  #text(style: "italic")[#body]
]

#let proposition(body, title: none) = block(
  width: 100%,
  stroke: (left: 2.5pt + rgb("#0d9488")),
  inset: (left: 0.9em, y: 0.5em),
  spacing: 1.3em,
  fill: rgb("#f8fafc")
)[
  #if title != none [
    #text(weight: "bold", fill: rgb("#0f766e"))[Proposition (#title)]
    #v(0.2em)
  ]
  #text(style: "italic")[#body]
]

#let corollary(body, title: none) = block(
  width: 100%,
  stroke: (left: 2.5pt + rgb("#4f46e5")),
  inset: (left: 0.9em, y: 0.5em),
  spacing: 1.3em,
  fill: rgb("#f8fafc")
)[
  #if title != none [
    #text(weight: "bold", fill: rgb("#4338ca"))[Corollaire (#title)]
    #v(0.2em)
  ]
  #text(style: "italic")[#body]
]

#let definition(body, title: none) = block(
  width: 100%,
  stroke: (left: 2.5pt + rgb("#475569")),
  inset: (left: 0.9em, y: 0.5em),
  spacing: 1.3em,
  fill: rgb("#f8fafc")
)[
  #if title != none [
    #text(weight: "bold", fill: rgb("#334155"))[Définition (#title)]
    #v(0.2em)
  ]
  #body
]

#let proof(body) = block(spacing: 1.1em)[
  #text(weight: "bold", style: "italic")[Démonstration.]
  #h(0.5em)
  #body
  #align(right)[#text(size: 8.5pt)[$square$]]
]

// --- Front Matter (Academic PUF Title Pages) ---
#align(center + horizon)[
  #text(12pt, tracking: 0.2em, fill: rgb("#64748b"))[COLLECTION « LE MATHÉMATICIEN »]
  #v(0.3cm)
  #text(10pt, fill: rgb("#64748b"))[dirigée par Jean-Pierre Kahane]
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


def clean_serre_page(pno: int, raw_text: str) -> str:
    text = raw_text.strip()
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
    elif pno == 24:
        text = text.replace("\\Lambda_n", "A_n")
    elif pno == 108:
        text = text.replace("\\binom{x}{p}", "\\left(\\frac{x}{p}\\right)")
        text = re.sub(
            r"<table>.*?</table>",
            lambda _: "$$\n\\begin{cases}\n\\chi(x) = 1 & \\text{si } x \\equiv \\pm 1 \\pmod{7} \\\\\n\\chi(x) = e^{2\\pi i/3} & \\text{si } x \\equiv \\pm 2 \\pmod{7} \\\\\n\\chi(x) = e^{4\\pi i/3} & \\text{si } x \\equiv \\pm 3 \\pmod{7}.\n\\end{cases}\n$$",
            text,
            flags=re.S,
        )
    elif pno == 118:
        text = re.sub(
            r"<table>.*?</table>",
            lambda _: "$$\n\\begin{aligned}\n\\zeta(-2n) &= 0 && \\text{si } n > 0 \\\\\n\\zeta(1-2n) &= (-1)^n B_n / 2n && \\text{si } n > 0.\n\\end{aligned}\n$$",
            text,
            flags=re.S,
        )
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
    elif pno == 154:
        text = text.replace("(1 - q)^n$24.", "(1 - q^n)^{24}$.")
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
    text = text.replace("\\varprojlim_n", "\\underset{\\longleftarrow}{\\lim}_n")
    text = text.replace("\\varprojlim", "\\underset{\\longleftarrow}{\\lim}")
    text = text.replace("\\varinjlim", "\\underset{\\longrightarrow}{\\lim}")
    text = text.replace("\\cotg", "\\operatorname{cotg}")

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

        m_thm = re.match(r"^(THÉORÈME|PROPOSITION|LEMME|COROLLAIRE|DÉFINITION)(\s+\d*\s*\.\s*—\s*.*)$", s)
        if m_thm:
            out_lines.append(f"**{m_thm.group(1)}{m_thm.group(2)[:m_thm.group(2).find('—')].rstrip()}** — {m_thm.group(2)[m_thm.group(2).find('—')+1:].lstrip()}")
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
    return acc + "\n"


def wrap_serre_theorems_in_typst(typst_body: str) -> str:
    blocks = typst_body.split("\n\n")
    env_map = {
        "THÉORÈME": "theorem",
        "PROPOSITION": "proposition",
        "LEMME": "lemma",
        "COROLLAIRE": "corollary",
        "DÉFINITION": "definition",
    }
    out_blocks: List[str] = []
    for blk in blocks:
        s = blk.strip()
        matched_env = None
        for kw, env_name in env_map.items():
            if re.match(rf"^(?:#strong\[)?{kw}\b", s, re.I):
                matched_env = env_name
                break
        if matched_env:
            opens = len(re.findall(r"(?<!\\)\[", s))
            closes = len(re.findall(r"(?<!\\)\]", s))
            if opens == closes:
                out_blocks.append(f"#{matched_env}[\n{s}\n]")
                continue
        out_blocks.append(blk)
    return "\n\n".join(out_blocks)


class FrenchMathTypstCompiler:
    def __init__(self, markdown_dir: Path):
        self.markdown_dir = markdown_dir

    def convert_markdown_to_typst_body(self, full_md_path: Path) -> str:
        """Use pandoc to accurately convert LaTeX math Markdown into native Typst syntax."""
        cmd = [
            "pandoc", str(full_md_path),
            "-f", "markdown",
            "-t", "typst"
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

