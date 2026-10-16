"""Kerodon Document Compiler for Typst, XeLaTeX, and EPUB."""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .extractor import KerodonChapter, KerodonEnvironment, KerodonSection, KerodonSubsection


class KerodonCompiler:
    """Compiles structured Kerodon chapters into Typst PDF, XeLaTeX, and EPUB."""

    TYPST_PREAMBLE = r"""// ==============================================================================
// Kerodon: An Online Resource for Homotopy-Coherent Mathematics
// Author: Jacob Lurie
// Chapter 1: The Language of ∞-Categories
// Reconstructed & Typeset via Polytypst (OUP / Chicago Author-Date Standard)
// ==============================================================================

#set document(
  title: "Kerodon — Chapter 1: The Language of ∞-Categories",
  author: "Jacob Lurie",
  date: auto
)

#set page(
  paper: "a4",
  margin: (x: 2.5cm, top: 2.5cm, bottom: 2.5cm),
  header: context {
    let page-number = counter(page).get().first()
    if page-number > 1 [
      #grid(
        columns: (1fr, 1fr),
        align(left)[#text(8pt, fill: rgb("#64748b"), font: "Libertinus Serif")[Chapter 1: The Language of $oo$-Categories]],
        align(right)[#text(8pt, fill: rgb("#64748b"), font: "Libertinus Serif")[Jacob Lurie · Kerodon]]
      )
      #line(length: 100%, stroke: 0.4pt + rgb("#cbd5e1"))
    ]
  },
  footer: context {
    let page-number = counter(page).get().first()
    align(center)[#text(9pt, fill: rgb("#475569"))[#page-number]]
  }
)

#set text(
  font: ("Libertinus Serif", "New Computer Modern"),
  size: 10pt,
  lang: "en",
  hyphenate: false
)

#set par(
  leading: 0.85em,
  spacing: 1.15em,
  justify: true,
  first-line-indent: 1.5em
)

#show math.equation: set text(font: "New Computer Modern Math")

// --- Styling Environments ---
#let math-box(
  title: "",
  number: "",
  tag: "",
  body,
  stroke-color: rgb("#cbd5e1"),
  bg-color: rgb("#f8fafc"),
  accent-color: rgb("#1e293b")
) = {
  block(
    width: 100%,
    stroke: (left: 2.5pt + stroke-color, rest: 0.4pt + rgb("#e2e8f0")),
    radius: (right: 3pt),
    fill: bg-color,
    inset: (x: 1.2em, top: 0.9em, bottom: 0.9em),
    spacing: 1.4em,
    breakable: true,
    [
      #grid(
        columns: (1fr, auto),
        align(left)[
          #text(weight: "bold", fill: accent-color)[#title #number]
          #if tag != "" [
            #h(0.4em)
            #text(7.5pt, fill: rgb("#64748b"))[(Tag #tag)]
          ]
        ],
        align(right)[
          #if tag != "" [
            #link("https://kerodon.net/tag/" + tag)[#text(7.5pt, fill: rgb("#2563eb"))[kerodon.net/#tag ↗]]
          ]
        ]
      )
      #v(0.4em)
      #set par(first-line-indent: 0pt)
      #body
    ]
  )
}

#let definition(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Definition (#title)] else [Definition],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#2563eb"),
  bg-color: rgb("#eff6ff"),
  accent-color: rgb("#1d4ed8")
)

#let theorem(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Theorem (#title)] else [Theorem],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#d97706"),
  bg-color: rgb("#fffbeb"),
  accent-color: rgb("#b45309")
)

#let proposition(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Proposition (#title)] else [Proposition],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#d97706"),
  bg-color: rgb("#fffbeb"),
  accent-color: rgb("#b45309")
)

#let lemma(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Lemma (#title)] else [Lemma],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#d97706"),
  bg-color: rgb("#fffbeb"),
  accent-color: rgb("#b45309")
)

#let corollary(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Corollary (#title)] else [Corollary],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#d97706"),
  bg-color: rgb("#fffbeb"),
  accent-color: rgb("#b45309")
)

#let remark(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Remark (#title)] else [Remark],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#64748b"),
  bg-color: rgb("#f8fafc"),
  accent-color: rgb("#334155")
)

#let example(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Example (#title)] else [Example],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#059669"),
  bg-color: rgb("#ecfdf5"),
  accent-color: rgb("#047857")
)

#let notation(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Notation (#title)] else [Notation],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#7c3aed"),
  bg-color: rgb("#faf5ff"),
  accent-color: rgb("#6d28d9")
)

#let warning(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Warning (#title)] else [Warning],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#dc2626"),
  bg-color: rgb("#fef2f2"),
  accent-color: rgb("#b91c1c")
)

#let exercise(number: "", title: "", tag: "", body) = math-box(
  title: if title != "" [Exercise (#title)] else [Exercise],
  number: number,
  tag: tag,
  body,
  stroke-color: rgb("#0284c7"),
  bg-color: rgb("#f0f9ff"),
  accent-color: rgb("#0369a1")
)

#let commutative-diagram(tag: "", latex: "", image-path: none, caption: "") = {
  align(center)[
    #block(
      width: 90%,
      stroke: 0.5pt + rgb("#cbd5e1"),
      radius: 4pt,
      inset: (x: 1.2em, y: 1em),
      fill: rgb("#f8fafc"),
      spacing: 1.4em,
      [
        #grid(
          columns: (1fr, auto),
          align(left)[
            #text(8.5pt, weight: "bold", fill: rgb("#1e293b"))[Commutative Diagram]
            #if tag != "" [
              #h(0.4em)
              #text(7.5pt, fill: rgb("#64748b"))[(Tag #tag)]
            ]
          ],
          align(right)[
            #if tag != "" [
              #link("https://kerodon.net/tag/" + tag)[#text(7.5pt, fill: rgb("#2563eb"))[kerodon.net/#tag ↗]]
            ]
          ]
        )
        #v(0.5em)
        #if image-path != none [
          #align(center)[#image(image-path, width: 45%)]
        ] else if latex != "" [
          #v(0.3em)
          #align(center)[
            #box(
              fill: rgb("#ffffff"),
              stroke: 0.4pt + rgb("#e2e8f0"),
              inset: (x: 0.8em, y: 0.5em),
              radius: 3pt
            )[
              #text(7.5pt, font: "DejaVu Sans Mono", fill: rgb("#334155"))[#latex]
            ]
          ]
        ]
        #if caption != "" [
          #v(0.3em)
          #align(center)[#text(8pt, style: "italic", fill: rgb("#64748b"))[#caption]]
        ]
      ]
    )
  ]
}

"""

    def __init__(self, chapter: KerodonChapter):
        self.chapter = chapter

    @staticmethod
    def _split_text_math(text: str) -> str:
        pattern = re.compile(r"\\(text(?:normal|rm|it|bf)?)\{([^{}]*\$[^{}]*)\}")
        def repl(m):
            inner = m.group(2)
            parts = inner.split("$")
            res = []
            for idx, p in enumerate(parts):
                if idx % 2 == 0:
                    if p:
                        res.append(f"\\text{{{p}}}")
                else:
                    res.append(f" {p} ")
            return "".join(res)
        for _ in range(3):
            text, n = pattern.subn(repl, text)
            if n == 0:
                break
        return text

    @classmethod
    def clean_kerodon_tex_for_pandoc(cls, text: str) -> str:
        text = text.replace(r"\textnormal{", r"\text{")
        text = re.sub(r"\\operatorname\{\s*\{\\bf\s*\\Delta\s*\}\s*\}", r"\\mathbf{\\Delta}", text)
        text = re.sub(r"\\operatorname\{\\bf\s*\\Delta\s*\}", r"\\mathbf{\\Delta}", text)
        text = re.sub(r"\\operatorname\{\\(mathcal|mathbf|mathrm|mathbb|mathfrak|mathscr)\{([^}]+)\}\s*\}", r"\\\1{\2}", text)
        text = re.sub(r"\\operatorname\{\\partial\s*\\Delta\s*\}", r"\\partial \\Delta", text)
        text = re.sub(r"\\operatorname\{([A-Za-z0-9\\]+)_\{([^}]+)\}\s*\}", r"\\operatorname{\1}_{\2}", text)
        text = re.sub(r"\\operatorname\{([A-Za-z0-9\\]+)\^\{([^}]+)\}\s*\}", r"\\operatorname{\1}^{\2}", text)
        text = re.sub(r"\\operatorname\{\\([a-zA-Z]+)\}", r"\\\1", text)
        text = text.replace(r"\varinjlim", r"\underset{\longrightarrow}{\lim}")
        text = text.replace(r"\varprojlim", r"\underset{\longleftarrow}{\lim}")
        text = cls._split_text_math(text)
        return text

    def generate_typst(self, output_path: Path) -> str:
        """Assemble the complete Typst master source document using batch Pandoc conversion."""
        # Step 1: Collect all environments and prepare for batch Pandoc conversion
        all_envs: List[KerodonEnvironment] = []
        for sec in self.chapter.sections:
            all_envs.extend(sec.intro_environments)
            for sub in sec.subsections:
                all_envs.extend(sub.environments)

        diag_map = {}
        combined_markdown = []
        boundary = "\n\nKERODONENVSEPARATOR\n\n"

        for env_idx, env in enumerate(all_envs):
            raw_text = env.body_markdown

            # Extract diagrams into unique alphanumeric markers
            def diag_repl(m):
                d_idx = len(diag_map)
                code = m.group(1).strip()
                # Find corresponding diagram object for this environment
                existing_diags_this_env = [v for v in diag_map.values() if v[0] == env.tag]
                diag_sub_idx = len(existing_diags_this_env)
                img_p = None
                if diag_sub_idx < len(env.diagrams):
                    img_p = env.diagrams[diag_sub_idx].image_path
                elif env.diagrams:
                    img_p = env.diagrams[0].image_path
                diag_map[f"DIAGTAGPH{d_idx}END"] = (env.tag, code, img_p)
                return f"\n\nDIAGTAGPH{d_idx}END\n\n"

            text = re.sub(r":::COMMUTATIVE_DIAGRAM:::(.*?):::END_DIAGRAM:::", diag_repl, raw_text, flags=re.DOTALL)
            text = self.clean_kerodon_tex_for_pandoc(text)
            # Trim whitespace immediately inside $ ... $
            text = re.sub(r"(?<!\$)\$(?!\$)\s*([^\$\n]+?)\s*(?<!\$)\$(?!\$)", r"$\1$", text)
            title_src = self.clean_kerodon_tex_for_pandoc(env.title) if env.title else ""
            title_src = re.sub(r"(?<!\$)\$(?!\$)\s*([^\$\n]+?)\s*(?<!\$)\$(?!\$)", r"$\1$", title_src)
            combined_markdown.append(f"KERODONTITLESTART {title_src} KERODONTITLEEND\n\n{text}")

        big_input = boundary.join(combined_markdown)

        # Step 2: Convert in one fast pass with Pandoc
        res = subprocess.run(
            ["pandoc", "-f", "markdown+tex_math_dollars", "-t", "typst"],
            input=big_input,
            text=True,
            capture_output=True
        )
        converted_typst_all = res.stdout

        # Split converted Typst bodies
        converted_bodies = converted_typst_all.split("KERODONENVSEPARATOR")

        # Step 3: Replace diagram placeholders with Typst commutative-diagram calls
        cleaned_bodies = []
        cleaned_titles = []
        for body in converted_bodies:
            t_match = re.search(r"KERODONTITLESTART\s*(.*?)\s*KERODONTITLEEND", body, flags=re.DOTALL)
            if t_match:
                cleaned_titles.append(t_match.group(1).strip())
                body = body[:t_match.start()] + body[t_match.end():]
            else:
                cleaned_titles.append("")
            for ph, (d_tag, d_code, img_p) in diag_map.items():
                if ph in body:
                    safe_code = d_code.replace("\\", "\\\\").replace('"', '\\"').replace("[", "\\[").replace("]", "\\]")
                    img_prop = f'"{img_p}"' if img_p else "none"
                    call_code = f'\n#commutative-diagram(tag: "{d_tag}", latex: "{safe_code}", image-path: {img_prop})\n'
                    body = body.replace(ph, call_code)
            cleaned_bodies.append(body.strip())

        # Step 4: Assemble document structure
        out = [self.TYPST_PREAMBLE]
        clean_ch_title = self.chapter.title.replace(r"$\infty$", "$oo$").replace(r"\infty", "oo")
        out.append(f"= Chapter {self.chapter.number}: {clean_ch_title}\n")
        out.append(f'#text(9pt, fill: rgb("#64748b"))[Original Author: Jacob Lurie · Web Tag: #link("https://kerodon.net/tag/{self.chapter.tag}")[{self.chapter.tag}]]\n')
        out.append("#v(1em)\n")

        if self.chapter.intro_text:
            clean_intro = self.chapter.intro_text.replace(r"$\infty$", "$oo$").replace(r"\infty", "oo")
            out.append(f"{clean_intro}\n\n#v(1em)\n")

        env_cursor = 0
        for sec in self.chapter.sections:
            clean_sec_title = sec.title.replace(r"$\infty$", "$oo$").replace(r"\infty", "oo")
            out.append(f"== Section {sec.number}: {clean_sec_title}\n")
            out.append(f'#text(8.5pt, fill: rgb("#64748b"))[Tag #link("https://kerodon.net/tag/{sec.tag}")[{sec.tag}]]\n\n')

            for env in sec.intro_environments:
                body = cleaned_bodies[env_cursor] if env_cursor < len(cleaned_bodies) else env.body_markdown
                t_val = cleaned_titles[env_cursor] if env_cursor < len(cleaned_titles) else env.title
                env_cursor += 1
                out.append(self._wrap_environment(env, body, t_val))

            for sub in sec.subsections:
                clean_sub_title = sub.title.replace(r"$\infty$", "$oo$").replace(r"\infty", "oo")
                out.append(f"=== Subsection {sub.number}: {clean_sub_title}\n")
                out.append(f'#text(8.5pt, fill: rgb("#64748b"))[Tag #link("https://kerodon.net/tag/{sub.tag}")[{sub.tag}]]\n\n')

                for env in sub.environments:
                    body = cleaned_bodies[env_cursor] if env_cursor < len(cleaned_bodies) else env.body_markdown
                    t_val = cleaned_titles[env_cursor] if env_cursor < len(cleaned_titles) else env.title
                    env_cursor += 1
                    out.append(self._wrap_environment(env, body, t_val))

        typ_code = "\n".join(out)
        Path(output_path).write_text(typ_code, encoding="utf-8")
        return typ_code

    def _wrap_environment(self, env: KerodonEnvironment, typst_body: str, typst_title: str = "") -> str:
        """Wrap body text in styled Typst environment function."""
        func_name = "remark"
        t = env.env_type.lower()
        if "definition" in t:
            func_name = "definition"
        elif "theorem" in t:
            func_name = "theorem"
        elif "proposition" in t:
            func_name = "proposition"
        elif "lemma" in t:
            func_name = "lemma"
        elif "corollary" in t:
            func_name = "corollary"
        elif "example" in t:
            func_name = "example"
        elif "notation" in t:
            func_name = "notation"
        elif "warning" in t:
            func_name = "warning"
        elif "exercise" in t:
            func_name = "exercise"
        else:
            func_name = "remark"

        clean_t = (typst_title or env.title).replace(r"$\infty$", "$oo$").replace(r"\infty", "oo").strip()
        title_arg = f"[{clean_t}]" if clean_t else '""'
        return f'#{func_name}(number: "{env.number}", title: {title_arg}, tag: "{env.tag}")[\n{typst_body}\n]\n\n'
    def compile_pdf(self, typst_path: Path, pdf_path: Path):
        """Compile Typst source to PDF via nix shell."""
        cmd = ["nix", "shell", "nixpkgs#typst", "--command", "typst", "compile", str(typst_path), str(pdf_path)]
        subprocess.run(cmd, check=True)

    def generate_latex(self, output_path: Path) -> str:
        """Generate master XeLaTeX document with native xypic and tikz-cd support."""
        out = [
            r"\documentclass[11pt,a4paper]{book}",
            r"\usepackage{amsmath,amssymb,amsthm}",
            r"\usepackage[all,cmtip]{xy}",
            r"\usepackage{tikz-cd}",
            r"\usepackage{hyperref}",
            r"\usepackage[margin=2.5cm]{geometry}",
            r"\newtheorem{theorem}{Theorem}[section]",
            r"\newtheorem{proposition}[theorem]{Proposition}",
            r"\newtheorem{lemma}[theorem]{Lemma}",
            r"\newtheorem{corollary}[theorem]{Corollary}",
            r"\theoremstyle{definition}",
            r"\newtheorem{definition}[theorem]{Definition}",
            r"\newtheorem{example}[theorem]{Example}",
            r"\newtheorem{remark}[theorem]{Remark}",
            r"\newtheorem{notation}[theorem]{Notation}",
            r"\newtheorem{exercise}[theorem]{Exercise}",
            r"\begin{document}",
            f"\\chapter{{{self.chapter.title}}}",
            f"\\noindent \\textbf{{Jacob Lurie}} \\hfill \\texttt{{Tag {self.chapter.tag}}}\n",
            self.chapter.intro_text,
        ]

        for sec in self.chapter.sections:
            out.append(f"\\section{{{sec.title}}} \\label{{tag:{sec.tag}}}\n")
            for env in sec.intro_environments:
                out.append(self._format_environment_latex(env))
            for sub in sec.subsections:
                out.append(f"\\subsection{{{sub.title}}} \\label{{tag:{sub.tag}}}\n")
                for env in sub.environments:
                    out.append(self._format_environment_latex(env))

        out.append(r"\end{document}")
        tex_code = "\n".join(out)
        Path(output_path).write_text(tex_code, encoding="utf-8")
        return tex_code

    def _format_environment_latex(self, env: KerodonEnvironment) -> str:
        """Format environment for LaTeX."""
        env_name = "remark"
        t = env.env_type.lower()
        if "definition" in t:
            env_name = "definition"
        elif "theorem" in t:
            env_name = "theorem"
        elif "proposition" in t:
            env_name = "proposition"
        elif "lemma" in t:
            env_name = "lemma"
        elif "corollary" in t:
            env_name = "corollary"
        elif "example" in t:
            env_name = "example"
        elif "notation" in t:
            env_name = "notation"
        elif "exercise" in t:
            env_name = "exercise"

        title_arg = f"[{env.title}]" if env.title else ""
        body = env.body_markdown

        # Replace diagram markers with pure LaTeX \xymatrix
        def replace_diag_tex(m):
            code = m.group(1).strip()
            return f"\n\\[\n{code}\n\\]\n"

        body = re.sub(r":::COMMUTATIVE_DIAGRAM:::(.*?):::END_DIAGRAM:::", replace_diag_tex, body, flags=re.DOTALL)

        return f"\\begin{{{env_name}}}{title_arg} \\label{{tag:{env.tag}}}\n{body}\n\\end{{{env_name}}}\n\n"

    def generate_markdown(self, output_path: Path) -> str:
        h = chr(35)
        out = [
            f"{h} Chapter {self.chapter.number}: {self.chapter.title}\n",
            f"**Jacob Lurie** · Tag `{self.chapter.tag}`\n",
            self.chapter.intro_text + "\n" if self.chapter.intro_text else "",
        ]
        for sec in self.chapter.sections:
            out.append(f"{h}{h} Section {sec.number}: {sec.title} (Tag `{sec.tag}`)\n")
            for env in sec.intro_environments:
                out.append(self._format_environment_md(env))
            for sub in sec.subsections:
                out.append(f"{h}{h}{h} Subsection {sub.number}: {sub.title} (Tag `{sub.tag}`)\n")
                for env in sub.environments:
                    out.append(self._format_environment_md(env))
        md_code = "\n".join(out)
        Path(output_path).write_text(md_code, encoding="utf-8")
        return md_code

    def _format_environment_md(self, env: KerodonEnvironment) -> str:
        title_str = f" ({env.title})" if env.title else ""
        diag_idx = 0
        def replace_diag_md(m):
            nonlocal diag_idx
            img_p = None
            if diag_idx < len(env.diagrams):
                img_p = env.diagrams[diag_idx].image_path
            elif env.diagrams:
                img_p = env.diagrams[0].image_path
            diag_idx += 1
            if img_p:
                return f"\n\n![Commutative Diagram {env.tag}]({img_p})\n\n"
            return ""
        body = re.sub(r":::COMMUTATIVE_DIAGRAM:::(.*?):::END_DIAGRAM:::", replace_diag_md, env.body_markdown, flags=re.DOTALL)
        body = self.clean_kerodon_tex_for_pandoc(body)
        return f"**{env.env_type} {env.number}{title_str}** [Tag `{env.tag}`].\n\n{body}\n\n"

    def compile_epub(self, md_path: Path, epub_path: Path, resource_dir: Path):
        cmd = [
            "pandoc",
            str(md_path),
            "-o",
            str(epub_path),
            "--mathml",
            f"--resource-path={resource_dir}",
            "--metadata",
            f"title=Kerodon — Chapter {self.chapter.number}: {self.chapter.title}",
            "--metadata",
            "author=Jacob Lurie",
        ]
        subprocess.run(cmd, check=True)

