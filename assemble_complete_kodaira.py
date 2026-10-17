"""Assembles the complete Kunihiko Kodaira Complex Analysis monograph (Cambridge University Press style).

Produces:
1. TeX-compatible Master Markdown: output/kodaira/kodaira_complex_analysis.md (and book.md)
2. Master XeLaTeX Source:          output/kodaira/kodaira_complex_analysis.tex (and book.tex)
3. Master Typst Source:            output/kodaira/kodaira_complex_analysis.typ (and book.typ)
4. Publication-Grade PDF:          output/kodaira/kodaira_complex_analysis.pdf (and book.pdf)
"""

import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from assemble_complete_ahlfors import (
    clean_margin_and_inline_math,
    ends_complete_paragraph,
    join_cross_page_text,
    sanitize_math_code,
    split_first_paragraph,
    starts_new_block,
)

KODAIRA_CHAPTERS: list[tuple[int, str, int, int]] = [
    (1, "Holomorphic functions", 12, 70),
    (2, "Cauchy's Theorem", 71, 127),
    (3, "Conformal mappings", 128, 163),
    (4, "Analytic continuation", 164, 210),
    (5, "Riemann's Mapping Theorem", 211, 257),
    (6, "Riemann surfaces", 258, 329),
    (7, "The structure of Riemann surfaces", 330, 386),
    (8, "Analytic functions on a closed Riemann surface", 387, 404),
]

KODAIRA_RUNNING_HEADERS = (
    r"Holomorphic functions|Cauchy's Theorem|Conformal mappings|"
    r"Analytic continuation|Riemann's Mapping Theorem|Riemann surfaces|"
    r"The structure of\s*Riemann surfaces|Analytic functions on a closed Riemann surface|"
    r"Piecewise smooth curves|Cellular decomposition|Differentiability and homology|"
    r"The Riemann sphere|Linear fractional transformations|"
    r"Analytic continuation along curves|Analytic continuation by integrals|"
    r"Cauchy's Theorem \(continued\)|Correspondence of boundaries|The principle of reflection|"
    r"Differential forms|Differential forms on a Riemann surface|Dirichlet's Principle|"
    r"Planar Riemann surfaces|Compact Riemann surfaces|"
    r"Abelian differentials of the first kind|Abelian differentials of the second and third kind|"
    r"The Riemann[-–—]Roch Theorem|Abel's Theorem|Power series|Integrals|"
    r"Properties of holomorphic functions|Preface|Contents|Problems|References|Index"
)

SECTION_START_PAGES: dict[str, tuple[int, str]] = {
    "1.1": (12, "Holomorphic functions"),
    "1.2": (26, "Power series"),
    "1.3": (35, "Integrals"),
    "1.4": (58, "Properties of holomorphic functions"),
    "2.1": (71, "Piecewise smooth curves"),
    "2.2": (85, "Cellular decomposition"),
    "2.3": (112, "Cauchy's Theorem"),
    "2.4": (124, "Differentiability and homology"),
    "3.1": (128, "Conformal mappings"),
    "3.2": (143, "The Riemann sphere"),
    "3.3": (150, "Linear fractional transformations"),
    "4.1": (164, "Analytic continuation"),
    "4.2": (171, "Analytic continuation along curves"),
    "4.3": (191, "Analytic continuation by integrals"),
    "4.4": (201, "Cauchy's Theorem (continued)"),
    "5.1": (211, "Riemann's Mapping Theorem"),
    "5.2": (225, "Correspondence of boundaries"),
    "5.3": (235, "The principle of reflection"),
    "6.1": (258, "Differential forms"),
    "6.2": (271, "Riemann surfaces"),
    "6.3": (278, "Differential forms on a Riemann surface"),
    "6.4": (305, "Dirichlet's Principle"),
    "7.1": (330, "Planar Riemann surfaces"),
    "7.2": (351, "Compact Riemann surfaces"),
    "8.1": (387, "Abelian differentials of the first kind"),
    "8.2": (390, "Abelian differentials of the second and third kind"),
    "8.3": (392, "The Riemann-Roch Theorem"),
    "8.4": (399, "Abel's Theorem"),
}

KODAIRA_TYPST_PREAMBLE = r"""// ==============================================================================
// Kunihiko Kodaira — Complex Analysis (Cambridge University Press, 2007)
// Translated by A. Sevenster | Edited by A. F. Beardon and T. K. Carne
// Reconstructed & Typeset via Polytypst (Authentic Cambridge Monograph Standard)
// ==============================================================================

#set document(
  title: "Complex Analysis — Kunihiko Kodaira",
  author: "Kunihiko Kodaira",
  date: auto
)

// Royal Octavo (6.14 x 9.21 in) Cambridge University Press trim
#set page(
  width: 442pt,
  height: 663pt,
  margin: (inside: 56pt, outside: 56pt, top: 56pt, bottom: 62pt),
  header: context {
    let page-number = counter(page).get().first()
    let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
    if page-number > 4 and not on-chapter-page [
      #if calc.odd(page-number) [
        #let secs = query(heading.where(level: 2).before(here()))
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = if secs != () { secs.last().body } else if chaps != () { chaps.last().body } else { "Complex Analysis" }
        #grid(
          columns: (1fr, auto),
          align(left)[#text(8.5pt, font: "New Computer Modern", style: "italic")[#title]],
          align(right)[#text(9.5pt, font: "New Computer Modern")[#page-number]]
        )
      ] else [
        #let chaps = query(heading.where(level: 1).before(here()))
        #let title = if chaps != () { chaps.last().body } else { "Complex Analysis" }
        #grid(
          columns: (auto, 1fr),
          align(left)[#text(9.5pt, font: "New Computer Modern")[#page-number]],
          align(right)[#text(8.5pt, font: "New Computer Modern", style: "italic")[#title]]
        )
      ]
      #v(-0.35em)
      #line(length: 100%, stroke: 0.35pt + luma(120))
    ]
  },
  footer: none
)

#set text(
  font: "New Computer Modern",
  size: 10pt,
  lang: "en",
  hyphenate: true
)

#set par(
  leading: 0.65em,
  spacing: 0.85em,
  justify: true,
  first-line-indent: 1.5em,
  linebreaks: "optimized"
)

#show math.equation: set text(font: "New Computer Modern Math")
#set math.equation(numbering: "(1)")
#let dd = math.dif
#let dv(f, x, deg: none) = if deg == none { $(dif f)/(dif x)$ } else { $(dif^deg f)/(dif x^deg)$ }
#let pdv(f, x, deg: none) = if deg == none { $(partial f)/(partial x)$ } else { $(partial^deg f)/(partial x^deg)$ }
#show ref: it => {
  let target = str(it.target)
  if target.starts-with("eq-") {
    let raw = target.trim("eq-", at: start)
    let parts = raw.split("-")
    let disp = if parts.len() >= 2 { parts.at(-2) + "." + parts.last() } else { parts.last() }
    link(it.target)[(#disp)]
  } else {
    it
  }
}
#show math.equation.where(block: true): it => {
  if it.numbering == none {
    return it
  }
  layout(size => {
    let eq = math.equation(it.body, block: true, numbering: none)
    if not it.has("label") {
      let m = measure(eq)
      if m.width > size.width and m.width > 0pt {
        let factor = (size.width / m.width) * 100%
        align(center, scale(x: factor, y: factor, reflow: true, eq))
      } else {
        eq
      }
    } else {
      let lbl = str(it.label).trim("eq-", at: start)
      let parts = lbl.split("-")
      let disp = if parts.len() >= 2 { parts.at(-2) + "." + parts.last() } else { parts.last() }
      let num-box = [(#disp)]
      let avail = size.width - measure(num-box).width - 12pt
      let m = measure(eq)
      let fitted = if m.width > avail and m.width > 0pt {
        let factor = (avail / m.width) * 100%
        scale(x: factor, y: factor, reflow: true, eq)
      } else {
        eq
      }
      grid(
        columns: (1fr, auto),
        column-gutter: 0.8em,
        align: (center + horizon, right + horizon),
        fitted,
        num-box
      )
    }
  })
}

#show heading: set par(justify: false, first-line-indent: 0pt)

// Cambridge University Press Chapter & Section Headings
#show heading.where(level: 1): it => {
  v(2.4em)
  align(left)[
    #text(16pt, weight: "bold", font: "New Computer Modern")[#it.body]
  ]
  v(0.6em)
  line(length: 100%, stroke: 0.6pt + black)
  v(1.4em)
}

#show heading.where(level: 2): it => {
  v(1.4em)
  text(12pt, weight: "bold", font: "New Computer Modern")[#it.body]
  v(0.55em)
}

#show heading.where(level: 3): it => {
  v(1.1em)
  text(10.5pt, weight: "bold", style: "italic", font: "New Computer Modern")[#it.body]
  v(0.35em)
}

#show heading.where(level: 4): it => {
  v(0.95em)
  text(10pt, weight: "bold", font: "New Computer Modern")[#smallcaps(it.body)]
  v(0.4em)
}

#show figure.caption: it => [
  #v(0.35em)
  #text(8.5pt, font: "New Computer Modern")[#it.body]
]
"""

KODAIRA_TITLE_PAGE = r"""
#align(center + horizon)[
  #text(10pt, tracking: 0.14em, font: "New Computer Modern")[#smallcaps("Cambridge Studies in Advanced Mathematics")]
  #v(3em)
  #text(26pt, weight: "bold", font: "New Computer Modern")[COMPLEX ANALYSIS]
  #v(2.2em)
  #text(14pt, weight: "bold", font: "New Computer Modern")[#smallcaps("Kunihiko Kodaira")]
  #v(1.6em)
  #text(10pt, style: "italic", font: "New Computer Modern")[Translated by A. Sevenster\ Edited by A. F. Beardon and T. K. Carne]
  #v(5em)
  #line(length: 35%, stroke: 0.4pt + luma(140))
  #v(1.2em)
  #text(11pt, weight: "bold", tracking: 0.12em, font: "New Computer Modern")[CAMBRIDGE UNIVERSITY PRESS]
  #v(0.4em)
  #text(8.5pt, fill: luma(90), font: "New Computer Modern")[Cambridge · New York · Melbourne · Madrid · Cape Town · Singapore]
]

#pagebreak()

#outline(title: [Contents], indent: 1.4em, depth: 2)

#pagebreak()
"""


def make_kodaira_figure_typst(
    fig_id: str, raw_caption: str, fig_dir: Path, paired: bool = False
) -> str:
    clean_cap = raw_caption.strip().replace("**", "")
    clean_cap = clean_margin_and_inline_math(clean_cap)
    img_path = fig_dir / f"fig_{fig_id}.png"
    if not img_path.exists():
        return f"\n\n#align(center)[#emph[{clean_cap}]]\n\n"
    width_pct = 52
    with Image.open(img_path) as im:
        w_px, h_px = im.size
    if paired:
        width_pct = min(88, max(50, round(w_px / 650 * 100)))
    else:
        width_pct = min(78, max(26, round(w_px / 1350 * 100)))
        if h_px * (width_pct / 100.0) / max(w_px, 1) > 0.38:
            width_pct = max(24, round(0.38 * w_px / max(h_px, 1) * 100))
    return (
        f"#figure(\n"
        f'  image("figures/fig_{fig_id}.png", width: {width_pct}%),\n'
        f"  caption: [{clean_cap}],\n"
        f"  supplement: none\n"
        f")"
    )


def render_kodaira_figure_group(figs: list[tuple[str, str]], fig_dir: Path) -> str:
    if not figs:
        return ""
    valid_figs = [(fid, cap) for fid, cap in figs if (fig_dir / f"fig_{fid}.png").exists()]
    if not valid_figs:
        return ""
    if len(valid_figs) == 2:
        f1 = make_kodaira_figure_typst(valid_figs[0][0], valid_figs[0][1], fig_dir, paired=True)
        f2 = make_kodaira_figure_typst(valid_figs[1][0], valid_figs[1][1], fig_dir, paired=True)
        return (
            f"\n\n#align(center)[\n"
            f"  #grid(\n"
            f"    columns: (1fr, 1fr),\n"
            f"    column-gutter: 1.5em,\n"
            f"    align: center + bottom,\n"
            f"    [{f1}],\n"
            f"    [{f2}]\n"
            f"  )\n"
            f"]\n\n"
        )
    blocks = [
        f"\n\n#align(center)[\n  {make_kodaira_figure_typst(fid, cap, fig_dir)}\n]\n\n"
        for fid, cap in valid_figs
    ]
    return "".join(blocks)


def extract_kodaira_page_parts(
    md_text: str,
    ch_num: int,
    pno: int,
    fig_dir: Path,
) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    raw_lines = md_text.splitlines()
    body_lines: list[str] = []
    top_figs: list[tuple[str, str]] = []
    bot_figs: list[tuple[str, str]] = []
    seen_figs_on_page: set[str] = set()

    for idx, l in enumerate(raw_lines):
        lt = l.strip()
        if not lt:
            body_lines.append("")
            continue

        # Strip standalone page numbers (roman or arabic)
        if re.match(r"^(?:\d{1,3}|[ivxlcdm]+)$", lt, re.IGNORECASE):
            continue

        # Strip running headers in the first 3 non-empty lines of a page
        non_empty_so_far = len([b for b in body_lines if b.strip()])
        if non_empty_so_far <= 2:
            if re.match(rf"^(?:#+\s*)?(?:{KODAIRA_RUNNING_HEADERS})(?:\s+\d{{1,3}})?$", lt, re.IGNORECASE):
                continue
            if re.match(rf"^\d{{1,3}}\s+(?:{KODAIRA_RUNNING_HEADERS})$", lt, re.IGNORECASE):
                continue
            m_sec_hdr = re.match(r"^(?:#+\s*)?(\d+\.\d+)\s+(.+?)(?:\s+\d{1,3})?$", lt)
            if m_sec_hdr:
                sec_id = m_sec_hdr.group(1)
                expected = SECTION_START_PAGES.get(sec_id)
                if not expected or expected[0] != pno:
                    continue

        # Strip Chapter number / title line at start of chapter page (we emit canonical chapter heading)
        if pno in {c[2] for c in KODAIRA_CHAPTERS} and non_empty_so_far <= 2:
            if re.match(r"^(?:#+\s*)?[1-8]$", lt):
                continue
            if re.match(rf"^(?:#+\s*)?(?:{KODAIRA_RUNNING_HEADERS})$", lt, re.IGNORECASE):
                continue

        # Detect standalone figure caption line: Fig. X.Y
        m_fig = re.match(
            r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?Fig(?:ure)?\.\s*(\d+)\.(\d+[a-z]?)\.?(?:\*\*)?\s*$",
            lt,
            re.IGNORECASE,
        )
        if m_fig:
            fid = f"{m_fig.group(1)}_{m_fig.group(2)}"
            if fid not in seen_figs_on_page:
                seen_figs_on_page.add(fid)
                cap = f"Fig. {m_fig.group(1)}.{m_fig.group(2)}"
                if non_empty_so_far <= 2:
                    top_figs.append((fid, cap))
                else:
                    bot_figs.append((fid, cap))
            continue

        # Normalize section headings X.Y on their true start page
        m_sec = re.match(r"^(?:#+\s*|\*\*)?(\d+\.\d+)\s+([^\*\n]+?)(?:\*\*)?$", lt)
        if m_sec and m_sec.group(1) in SECTION_START_PAGES:
            sec_id = m_sec.group(1)
            start_p, canon_title = SECTION_START_PAGES[sec_id]
            if pno == start_p:
                body_lines.append(f"## {sec_id} {canon_title}")
                continue
            elif non_empty_so_far <= 3:
                continue

        # Normalize subsection headings: a. Title, b. Title, c. Title, d. Title, e. Title
        m_sub = re.match(
            r"^(?:#+\s*|\*\*)?([a-e])\.\s+([A-Z][A-Za-z0-9\s\-,'\(\)]{2,60}?)(?:\*\*)?\.?$",
            lt,
        )
        if m_sub and len(lt) < 72:
            body_lines.append(f"### {m_sub.group(1)}. {m_sub.group(2).strip()}")
            continue

        body_lines.append(l)

    s = "\n".join(body_lines).strip()

    # Equation numbering extraction: (1.1), (2.15), etc. -> <eq-pno-ch-num>
    s = re.sub(
        r"\\tag\{\(?(\d+)\.(\d+[a-z']?)\)?\}",
        rf"\\tag{{{pno}-\1-\2}}",
        s,
    )
    s = re.sub(
        r"\$\$(.*?)\$\$\s*\((\d+)\.(\d+[a-z']?)\)",
        rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
        s,
        flags=re.DOTALL,
    )
    s = re.sub(
        r"\\\[(.*?)\\\]\s*\((\d+)\.(\d+[a-z']?)\)",
        rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
        s,
        flags=re.DOTALL,
    )
    s = re.sub(
        r"\$\$(.*?)\\hfill\s*\((\d+)\.(\d+[a-z']?)\)\s*\$\$",
        rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
        s,
        flags=re.DOTALL,
    )
    s = re.sub(
        r"\$\$(.*?)(?:\\qquad|\\quad)\s*\((\d+)\.(\d+[a-z']?)\)\s*\$\$",
        rf"\n\n$$\n\1\n$$ <eq-{pno}-\2-\3>\n\n",
        s,
        flags=re.DOTALL,
    )
    s = re.sub(
        r"\$\$(.*?)\\tag\{([0-9a-zA-Z'-]+)\}(.*?)\$\$",
        r"\n\n$$\n\1\3\n$$ <eq-\2>\n\n",
        s,
        flags=re.DOTALL,
    )
    # Clean any remaining unparsed \tag{...}
    s = re.sub(r"\\tag\{[^{}]*\}", "", s)

    return s.strip(), top_figs, bot_figs


def format_kodaira_typst(s: str) -> str:
    fig_blocks: list[str] = []

    def save_fig(m: re.Match[str]) -> str:
        idx = len(fig_blocks)
        fig_blocks.append(m.group(0))
        return f"\n\n@@FIGBLOCK{idx}@@\n\n"

    s = re.sub(
        r"#align\(center\)\[\n.*?\n\]",
        save_fig,
        s,
        flags=re.DOTALL,
    )

    s = s.replace('"', "''")

    # Convert Markdown headings to Typst headings
    s = re.sub(r"^###\s+([a-e]\.\s+.*?)$", r"=== \1", s, flags=re.MULTILINE)
    s = re.sub(r"^##\s+(\d+\.\d+\s+.*?)$", r"== \1", s, flags=re.MULTILINE)
    s = re.sub(r"^###\s+(.*?)$", r"=== \1", s, flags=re.MULTILINE)
    s = re.sub(r"^##\s+(.*?)$", r"== \1", s, flags=re.MULTILINE)
    s = re.sub(r"^#\s+(.*?)$", r"= \1", s, flags=re.MULTILINE)

    s = (
        s.replace('f"', "f''")
        .replace('w"', "w''")
        .replace('z"', "z''")
        .replace('y"', "y''")
        .replace('g"', "g''")
    )
    s = s.replace(r"\leqq", "<=").replace(r"\geqq", ">=")

    display_blocks: list[tuple[str, str]] = []

    def save_display(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        label = m.group(2) if m.group(2) else ""
        idx = len(display_blocks)
        display_blocks.append((body, label))
        return f"\n\n@@DISPLAYBLOCK{idx}@@\n\n"

    s = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\n\1\n$$", s, flags=re.DOTALL)
    s = re.sub(
        r"\$\$\s*(.*?)\s*\$\$\s*(<eq-[^>]+>)?",
        save_display,
        s,
        flags=re.DOTALL,
    )

    # Clean stray odd dollars on a single line
    cleaned_lines: list[str] = []
    for line in s.splitlines():
        if line.count("$") % 2 != 0:
            line = re.sub(r"(?<!\$)\$(?!\$)", "", line, count=1)
        cleaned_lines.append(line)
    s = "\n".join(cleaned_lines)

    inline_blocks: list[str] = []
    prose_re = re.compile(
        r"differential|equations|functions|polynomial|converges|identically|"
        r"derivative|continuous|condition|sufficient|necessary|arbitrary|"
        r"original|equation|type|ordinary|point|removable|singularity|coefficients|"
        r"holomorphic|meromorphic|neighborhood|connected|compact",
        re.IGNORECASE,
    )

    def save_inline(m: re.Match[str]) -> str:
        code = m.group(1)
        if prose_re.search(code) and "\\" not in code:
            clean_w = code.replace('"', "").strip()
            return f" {clean_w} "
        idx = len(inline_blocks)
        inline_blocks.append(code)
        return f"@@INLINEMATH{idx}@@"

    s = re.sub(r"\$([^$\n]+)\$", save_inline, s)

    s = re.sub(r"(?<![=\s])#", r"\#", s)
    s = re.sub(r"<(?!eq-|fig-|sec-)", r"\< ", s)
    s = re.sub(r"^\s*/\s*", r"\/ ", s, flags=re.MULTILINE)
    s = s.replace("*/", "* /")

    s = re.sub(r"^(\s*)\*(?=\d+\.)", r"\1\\*", s, flags=re.MULTILINE)
    s = re.sub(
        r"\*\*((?:(?!\n\n|@@DISPLAYBLOCK)[^\*])+?)\*\*",
        r"#strong[\1]",
        s,
    )
    s = re.sub(
        r"(?<![\\\*])\*((?:(?!\n\n|@@DISPLAYBLOCK)[^\*])+?)\*(?!\*)",
        r"#emph[\1]",
        s,
    )
    s = re.sub(r"(?<!\\)\*", r"\\*", s)
    s = re.sub(r"(?<![a-zA-Z0-9])_(?![a-zA-Z0-9])", r"\\_", s)
    s = s.replace(r"\cdots", "...").replace(r"\ldots", "...")

    s = re.sub(r"(@@INLINEMATH\d+@@)\s+([.,;:?!\)])", r"\1\2", s)
    s = re.sub(r"(\()\s+(@@INLINEMATH\d+@@)", r"\1\2", s)

    s = re.sub(
        r"@@INLINEMATH(\d+)@@",
        lambda m: (
            f"${sanitize_math_code(inline_blocks[int(m.group(1))], is_display=False)}$"
        ),
        s,
    )

    def restore_display(m: re.Match[str]) -> str:
        body, label = display_blocks[int(m.group(1))]
        clean_body = sanitize_math_code(body, is_display=True)
        return f"\n$ {clean_body} $ {label}\n"

    s = re.sub(r"@@DISPLAYBLOCK(\d+)@@", restore_display, s)
    s = re.sub(r"@@FIGBLOCK(\d+)@@", lambda m: fig_blocks[int(m.group(1))], s)
    return s


def stitch_kodaira_chapter(
    pages_data: list[tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]],
    fig_dir: Path,
) -> str:
    acc = ""
    pending_figs: list[tuple[str, str]] = []

    for idx, (_pno, text, top_figs, bot_figs) in enumerate(pages_data):
        if not text and not top_figs and not bot_figs:
            continue

        all_top_figs = pending_figs + top_figs
        pending_figs = []
        starts_lower = bool(text.strip()) and text.lstrip()[0].islower()
        continues_prev = (
            not ends_complete_paragraph(acc) and not starts_new_block(text)
        ) or starts_lower

        if not acc:
            acc = render_kodaira_figure_group(all_top_figs, fig_dir) + text
        elif continues_prev:
            first_p, rest_p = split_first_paragraph(text)
            acc = join_cross_page_text(acc, first_p)
            if all_top_figs:
                acc += render_kodaira_figure_group(all_top_figs, fig_dir)
            if rest_p:
                acc += "\n\n" + rest_p
        else:
            if all_top_figs:
                acc += render_kodaira_figure_group(all_top_figs, fig_dir)
            acc += "\n\n" + text

        if bot_figs:
            next_starts_lower = (
                idx + 1 < len(pages_data)
                and bool(pages_data[idx + 1][1].strip())
                and pages_data[idx + 1][1].lstrip()[0].islower()
            )
            if ends_complete_paragraph(acc) and not next_starts_lower:
                acc += render_kodaira_figure_group(bot_figs, fig_dir)
            else:
                pending_figs.extend(bot_figs)

    if pending_figs:
        acc += render_kodaira_figure_group(pending_figs, fig_dir)

    return acc


def format_kodaira_index(md_dir: Path) -> str:
    entries: list[str] = []
    for pno in range(414, 418):
        p_file = md_dir / f"p_{pno:03d}.md"
        if not p_file.exists():
            continue
        for raw_line in p_file.read_text(encoding="utf-8").splitlines():
            lt = raw_line.strip()
            if not lt:
                continue
            if re.match(r"^(?:#+\s*)?Index$", lt, re.IGNORECASE):
                continue
            if re.match(r"^\d{1,3}\s+Index$|^Index\s+\d{1,3}$|^\d{1,3}$", lt, re.IGNORECASE):
                continue
            line_clean = lt.replace('"', "''").replace("#", r"\#")
            line_clean = re.sub(r"\*([^\*]+)\*", r"#emph[\1]", line_clean)
            line_clean = clean_margin_and_inline_math(line_clean)
            entries.append(line_clean)

    joined = "\n\n".join(entries)
    return (
        "\n= Index\n\n"
        "#columns(2, gutter: 1.8em)[\n"
        "  #set text(size: 9pt)\n"
        "  #set par(first-line-indent: 0pt, hanging-indent: 1.2em, leading: 0.52em, spacing: 0.48em, justify: false)\n"
        f"  {joined}\n"
        "]\n"
    )


def build_tex_markdown_and_outputs(out_dir: Path) -> None:
    out_dir = Path(out_dir)
    md_dir = out_dir / "markdown_pages"
    fig_dir = out_dir / "figures"

    # 1. Assemble Master TeX-compatible Markdown (kodaira_complex_analysis.md & book.md)
    md_sections: list[str] = [
        "---\n"
        'title: "Complex Analysis"\n'
        'author: "Kunihiko Kodaira"\n'
        'translator: "A. Sevenster"\n'
        'editor: "A. F. Beardon and T. K. Carne"\n'
        'publisher: "Cambridge University Press"\n'
        "year: 2007\n"
        "---\n\n"
        "# Complex Analysis\n\n"
        "**Kunihiko Kodaira**  \n"
        "*Translated by A. Sevenster · Edited by A. F. Beardon and T. K. Carne*  \n"
        "**Cambridge University Press**\n"
    ]

    typst_sections: list[str] = [
        KODAIRA_TYPST_PREAMBLE,
        KODAIRA_TITLE_PAGE,
    ]

    # Preface (page 10)
    pref_file = md_dir / "p_010.md"
    if pref_file.exists():
        pref_raw = pref_file.read_text(encoding="utf-8")
        pref_body, _, _ = extract_kodaira_page_parts(pref_raw, 0, 10, fig_dir)
        pref_body = re.sub(r"^(?:#+\s*)?Preface\s*\n+", "", pref_body, flags=re.IGNORECASE).strip()
        md_sections.append(f"\n## Preface\n\n{pref_body}\n")
        typst_sections.append(
            "\n= Preface\n\n" + format_kodaira_typst(pref_body) + "\n#pagebreak(weak: true)\n"
        )

    # Chapters 1 through 8
    for ch_num, ch_title, start_p, end_p in KODAIRA_CHAPTERS:
        pages_data: list[tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]] = []
        ch_md_pages: list[str] = [f"\n# Chapter {ch_num}: {ch_title}\n"]

        for pno in range(start_p, end_p + 1):
            p_file = md_dir / f"p_{pno:03d}.md"
            if not p_file.exists():
                continue
            raw_text = p_file.read_text(encoding="utf-8").strip()
            if len(raw_text) < 20 or "1.1.1.1.1" in raw_text or "musical compositions" in raw_text:
                continue
            p_body, top_f, bot_f = extract_kodaira_page_parts(raw_text, ch_num, pno, fig_dir)
            pages_data.append((pno, p_body, top_f, bot_f))

            # Build Markdown page with grounded figures
            md_page = p_body
            for fid, cap in top_f:
                if (fig_dir / f"fig_{fid}.png").exists():
                    md_page = f"![{cap}](figures/fig_{fid}.png)\n\n" + md_page
            for fid, cap in bot_f:
                if (fig_dir / f"fig_{fid}.png").exists():
                    md_page = md_page + f"\n\n![{cap}](figures/fig_{fid}.png)"
            ch_md_pages.append(md_page)

        md_sections.append("\n\n".join(ch_md_pages))
        stitched = stitch_kodaira_chapter(pages_data, fig_dir)
        formatted = format_kodaira_typst(stitched)
        typst_sections.append(f"\n= {ch_num} {ch_title}\n\n" + formatted)
        typst_sections.append("\n#pagebreak(weak: true)\n")

    # Problems (pages 405 to 412)
    prob_pages: list[tuple[int, str, list[tuple[str, str]], list[tuple[str, str]]]] = []
    prob_md: list[str] = ["\n# Problems\n"]
    for pno in range(405, 413):
        p_file = md_dir / f"p_{pno:03d}.md"
        if p_file.exists():
            raw_text = p_file.read_text(encoding="utf-8").strip()
            p_body, top_f, bot_f = extract_kodaira_page_parts(raw_text, 9, pno, fig_dir)
            p_body = re.sub(r"^(?:#+\s*)?Problems\s*\n+", "", p_body, flags=re.IGNORECASE).strip()
            prob_pages.append((pno, p_body, top_f, bot_f))
            prob_md.append(p_body)
    if prob_pages:
        md_sections.append("\n\n".join(prob_md))
        stitched_prob = stitch_kodaira_chapter(prob_pages, fig_dir)
        typst_sections.append(
            "\n= Problems\n\n" + format_kodaira_typst(stitched_prob) + "\n#pagebreak(weak: true)\n"
        )

    # References (page 413)
    ref_file = md_dir / "p_413.md"
    if ref_file.exists():
        ref_raw = ref_file.read_text(encoding="utf-8").strip()
        ref_body, _, _ = extract_kodaira_page_parts(ref_raw, 9, 413, fig_dir)
        ref_body = re.sub(r"^(?:#+\s*)?References\s*\n+", "", ref_body, flags=re.IGNORECASE).strip()
        md_sections.append(f"\n# References\n\n{ref_body}\n")
        typst_sections.append(
            "\n= References\n\n" + format_kodaira_typst(ref_body) + "\n#pagebreak(weak: true)\n"
        )

    # Index (pages 414 to 417)
    typst_sections.append(format_kodaira_index(md_dir))

    # Write Master TeX-compatible Markdown
    full_md = "\n\n".join(md_sections)
    md_out = out_dir / "kodaira_complex_analysis.md"
    md_book = out_dir / "book.md"
    md_out.write_text(full_md, encoding="utf-8")
    shutil.copy2(md_out, md_book)
    print(f"Generated TeX-compatible Markdown: {md_out} ({md_out.stat().st_size / (1024*1024):.2f} MB)")

    # Write Master Typst
    full_typ = "\n".join(typst_sections)
    typ_out = out_dir / "kodaira_complex_analysis.typ"
    typ_book = out_dir / "book.typ"
    typ_out.write_text(full_typ, encoding="utf-8")
    shutil.copy2(typ_out, typ_book)
    print(f"Generated Typst source: {typ_out} ({typ_out.stat().st_size / (1024*1024):.2f} MB)")

    # Generate XeLaTeX via Pandoc with book class
    tex_out = out_dir / "kodaira_complex_analysis.tex"
    tex_book = out_dir / "book.tex"
    subprocess.run(
        [
            "pandoc",
            str(md_out),
            "-f",
            "markdown+tex_math_dollars+raw_tex",
            "-t",
            "latex",
            "-s",
            "--top-level-division=chapter",
            "-V",
            "documentclass=book",
            "-V",
            "geometry:paperwidth=6.14in,paperheight=9.21in,margin=0.78in",
            "-o",
            str(tex_out),
        ],
        check=True,
    )
    shutil.copy2(tex_out, tex_book)
    print(f"Generated LaTeX source: {tex_out} ({tex_out.stat().st_size / (1024*1024):.2f} MB)")

    # Compile Typst to PDF
    pdf_out = out_dir / "kodaira_complex_analysis.pdf"
    pdf_book = out_dir / "book.pdf"
    print(f"Compiling {typ_out} to PDF...")
    subprocess.run(
        ["nix", "shell", "nixpkgs#typst", "--command", "typst", "compile", str(typ_out), str(pdf_out)],
        check=True,
    )
    shutil.copy2(pdf_out, pdf_book)

    import pymupdf

    doc = pymupdf.open(str(pdf_out))
    print(f"\n🏆 SUCCESS! Compiled Kodaira Complex Analysis PDF:")
    print(f"   PDF Path:    {pdf_out}")
    print(f"   Total Pages: {len(doc)} pages")
    print(f"   File Size:   {pdf_out.stat().st_size / (1024*1024):.2f} MB")


if __name__ == "__main__":
    build_tex_markdown_and_outputs(Path("output/kodaira"))
