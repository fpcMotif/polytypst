"""Typst compiler producing exquisite Chinese book output with Songti SC typography and publication figures."""

import subprocess
import re
from pathlib import Path
from ..parser.stitcher import ParsedBook


class TypstCompiler:
    def __init__(self, book: ParsedBook, font_style: str = "songti"):
        self.book = book
        self.font_style = font_style

    def generate_typst_source(self) -> str:
        b = self.book

        lines = [
            f'#set document(title: "{b.title}", author: "{b.author}")',
            "",
            "// --- Page & Margins Setup (Classical Book Golden Ratio) ---",
            "#set page(",
            '  paper: "a5",',
            "  margin: (top: 2.2cm, bottom: 2.2cm, inside: 2.3cm, outside: 1.8cm),",
            "  header: context {",
            "    let p = counter(page).get().first()",
            "    if p > 4 {",
            "      if calc.even(p) {",
            f'        align(left, text(8.5pt, fill: rgb("666666"), font: "Songti SC")[{b.title}])',
            "      } else {",
            '        let headings = query(selector(heading.where(level: 2)).before(here()))',
            "        let cur_chap = if headings.len() > 0 { headings.last().body } else { [] }",
            '        align(right, text(8.5pt, fill: rgb("666666"), font: "Songti SC")[#cur_chap])',
            "      }",
            '      line(length: 100%, stroke: 0.4pt + rgb("cccccc"))',
            "    }",
            "  },",
            "  footer: context {",
            "    let p = counter(page).get().first()",
            "    if p > 2 {",
            '      align(center, text(9pt, fill: rgb("555555"), font: "Charter")[#p])',
            "    }",
            "  }",
            ")",
            "",
            "// --- Exquisite Chinese Book Typography ---",
            '#set text(',
            '  font: ("Songti SC", "STSong", "Hiragino Mincho ProN", "Charter", "Libertinus Serif", "STIX Two Math"),',
            '  size: 10pt,',
            '  lang: "zh"',
            ')',
            "",
            "// --- Breathable Line Height & Clean Paragraph Indent ---",
            "#set par(",
            "  justify: true,",
            "  first-line-indent: 2em,",
            "  leading: 1.25em,",
            "  spacing: 1.25em",
            ")",
            "",
            "// --- Headings with PingFang SC / Heiti SC Hierarchy ---",
            '#show heading: set text(font: ("PingFang SC", "Heiti SC"), weight: "bold")',
            "",
            "#show heading.where(level: 2): it => {",
            "  pagebreak(weak: true)",
            "  v(1.2cm)",
            '  text(17pt, weight: "bold", fill: rgb("111111"))[#it.body]',
            "  v(0.8cm)",
            "}",
            "",
            "#show heading.where(level: 3): it => {",
            "  v(1.2em)",
            '  text(12pt, weight: "bold", fill: rgb("222222"))[#it.body]',
            "  v(0.6em)",
            "}",
            "",
            "// --- Figure & Caption Styling ---",
            "#show figure: set block(spacing: 1.8em)",
            "#show figure.caption: it => [",
            "  #v(0.5em)",
            '  #text(8.5pt, fill: rgb("555555"), font: ("Songti SC", "PingFang SC"))[#it.body]',
            "]",
            "",
            "// --- Title Page ---",
            "#align(center + horizon)[",
            '  #text(9pt, tracking: 0.25em, fill: rgb("666666"), font: "Songti SC")[当代世界学术名著 · 经济学系列]',
            "  #v(1.2cm)",
            f'  #text(21pt, weight: "bold", font: "PingFang SC")[{b.title}]',
            "  #v(0.4cm)",
            f'  #text(11pt, fill: rgb("444444"), font: "Charter")[{b.subtitle}]',
            "  #v(2.5cm)",
            f'  #text(11pt, font: "Songti SC")[著：{b.author}]',
            "  #v(0.3cm)",
            f'  #text(10.5pt, font: "Songti SC")[译：{b.translator}]',
            "  #v(3.0cm)",
            f'  #text(10pt, fill: rgb("555555"), font: "Songti SC")[{b.publisher}]',
            "]",
            "#pagebreak()",
            "",
            "// --- Dynamic Table of Contents ---",
            "#outline(title: [目 录], indent: 1.5em, depth: 3)",
            "#pagebreak()",
            ""
        ]

        figures_by_id = {f.figure_id: f for f in b.figures}

        for sec in b.sections:
            if not sec.content_blocks:
                continue

            if sec.level == 2:
                lines.append(f"== {sec.title}\n")
            elif sec.level == 3:
                lines.append(f"=== {sec.title}\n")
            else:
                lines.append(f"==== {sec.title}\n")

            for block in sec.content_blocks:
                if block.startswith("__FIGURE_") and block.endswith("__"):
                    fig_id_str = block[len("__FIGURE_"):-len("__")]
                    try:
                        fig_id = int(fig_id_str)
                        fig = figures_by_id.get(fig_id)
                        if fig:
                            clean_caption = re.sub(r"^(图\s*\d+\s*|Figure\s*\d+\s*[:\.\s]*)", "", fig.caption).strip()
                            lines.append("#figure(")
                            lines.append(f'  image("{fig.image_rel_path}", width: 72%),')
                            lines.append(f'  caption: [图 {fig.figure_id}  {clean_caption}]')
                            lines.append(f") <fig-{fig.figure_id}>\n")
                    except Exception:
                        pass
                elif block.startswith("__CITATION__"):
                    citation = block[len("__CITATION__"):]
                    escaped = citation.replace("\\", "\\\\")
                    escaped = escaped.replace("*", "\\*")
                    escaped = escaped.replace("[", "\\[").replace("]", "\\]")
                    escaped = escaped.replace("@", "\\@")
                    escaped = escaped.replace("<", "\\<").replace(">", "\\>")
                    lines.append(f'#par(hanging-indent: 2.2em, first-line-indent: 0pt, leading: 0.9em, spacing: 1.1em)[#text(9pt, font: ("Charter", "Libertinus Serif", "Songti SC"))[{escaped}]]\n')
                elif block.startswith("__ACK__"):
                    ack_text = block[len("__ACK__"):]
                    lines.append("\n#v(2.5em)")
                    lines.append("#align(center)[")
                    lines.append('  #box(width: 90%, stroke: 0.5pt + rgb("#cbd5e1"), inset: 1.2em, radius: 4pt, fill: rgb("#f8fafc"))[')
                    lines.append(f'    #text(8.5pt, fill: rgb("#475569"), font: "Songti SC")[特别鸣谢：{ack_text}]')
                    lines.append("  ]")
                    lines.append("]\n")
                else:
                    clean_p = block.strip()
                    if clean_p:
                        # Sanitize Typst formatting characters
                        escaped_p = clean_p.replace("\\", "\\\\")
                        escaped_p = escaped_p.replace("*", "\\*")
                        escaped_p = escaped_p.replace("_", "\\_")
                        escaped_p = escaped_p.replace("[", "\\[").replace("]", "\\]")
                        escaped_p = escaped_p.replace("$", "\\$")
                        escaped_p = escaped_p.replace("<", "\\<").replace(">", "\\>")
                        escaped_p = escaped_p.replace("@", "\\@")
                        lines.append(f"{escaped_p}\n")
        return "\n".join(lines)

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
