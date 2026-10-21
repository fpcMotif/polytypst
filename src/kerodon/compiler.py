"""Kerodon Document Compiler for Typst, XeLaTeX, and EPUB matching authentic LaTeX treatise typography."""

import re
import subprocess
from pathlib import Path

from .extractor import (
    KerodonChapter,
    KerodonEnvironment,
)


class KerodonCompiler:
    """Compiles structured Kerodon chapters into Typst PDF, XeLaTeX, and EPUB with authentic LaTeX typography."""

    TYPST_PREAMBLE = r"""// ==============================================================================
// Kerodon: An Online Resource for Homotopy-Coherent Mathematics
// Author: Jacob Lurie
// Formatted matching authentic Princeton / Stacks Project LaTeX standards
// ==============================================================================

#set document(
  title: "Kerodon — Jacob Lurie",
  author: "Jacob Lurie",
  date: auto
)

#set page(
  paper: "us-letter",
  margin: (left: 90pt, right: 90pt, top: 72pt, bottom: 72pt),
  header: context {
    let page-number = counter(page).get().first()
    if page-number > 1 [
      #if calc.odd(page-number) [
        #grid(
          columns: (1fr, auto),
          align(left)[#text(9pt, font: "New Computer Modern", style: "italic")[#smallcaps("The Language of oo-Categories")]],
          align(right)[#text(10pt, font: "New Computer Modern")[#page-number]]
        )
      ] else [
        #grid(
          columns: (auto, 1fr),
          align(left)[#text(10pt, font: "New Computer Modern")[#page-number]],
          align(right)[#text(9pt, font: "New Computer Modern", style: "italic")[#smallcaps("Kerodon · Jacob Lurie")]]
        )
      ]
      #v(-0.3em)
      #line(length: 100%, stroke: 0.4pt + rgb("#000000"))
    ]
  },
  footer: none
)

#set text(
  font: ("New Computer Modern", "Latin Modern Roman"),
  size: 10.95pt,
  lang: "en",
  hyphenate: false
)

#set par(
  leading: 0.72em,
  spacing: 0.95em,
  justify: true,
  first-line-indent: 1.5em
)

#show math.equation: set text(font: "New Computer Modern Math")

// Heading Typography
#show heading.where(level: 1): it => {
  v(1.5em)
  text(18pt, weight: "bold", font: "New Computer Modern")[#it.body]
  v(0.8em)
}

#show heading.where(level: 2): it => {
  v(1.4em)
  text(14.3pt, weight: "bold", font: "New Computer Modern")[#it.body]
  v(0.6em)
}

#show heading.where(level: 3): it => {
  v(1.1em)
  text(12pt, weight: "bold", font: "New Computer Modern")[#it.body]
  v(0.4em)
}

// Margin Tag Placement (matches kerodon.pdf left-margin tag at x=60pt)
#let tag-margin(tag) = {
  if tag != "" {
    place(
      left,
      dx: -42pt,
      dy: 0.05em,
      link("https://kerodon.net/tag/" + tag)[
        #text(8pt, font: "DejaVu Sans Mono", fill: rgb("#64748b"))[#tag]
      ]
    )
  }
}

// Academic Mathematical Environments (Clean, Classical LaTeX monograph style)
#let theorem-like(kind: "", number: "", title: "", tag: "", body) = {
  block(width: 100%, spacing: 1.2em, breakable: true)[
    #tag-margin(tag)
    #set text(style: "italic")
    *#kind #number*#if title != "" [ (#title)]*. *#body
  ]
}

#let theorem(number: "", title: "", tag: "", body) = theorem-like(kind: "Theorem", number: number, title: title, tag: tag, body)
#let proposition(number: "", title: "", tag: "", body) = theorem-like(kind: "Proposition", number: number, title: title, tag: tag, body)
#let lemma(number: "", title: "", tag: "", body) = theorem-like(kind: "Lemma", number: number, title: title, tag: tag, body)
#let corollary(number: "", title: "", tag: "", body) = theorem-like(kind: "Corollary", number: number, title: title, tag: tag, body)

#let def-like(kind: "", number: "", title: "", tag: "", body) = {
  block(width: 100%, spacing: 1.2em, breakable: true)[
    #tag-margin(tag)
    #set text(style: "normal")
    *#kind #number*#if title != "" [ (#title)]*. *#body
  ]
}

#let definition(number: "", title: "", tag: "", body) = def-like(kind: "Definition", number: number, title: title, tag: tag, body)
#let remark(number: "", title: "", tag: "", body) = def-like(kind: "Remark", number: number, title: title, tag: tag, body)
#let example(number: "", title: "", tag: "", body) = def-like(kind: "Example", number: number, title: title, tag: tag, body)
#let notation(number: "", title: "", tag: "", body) = def-like(kind: "Notation", number: number, title: title, tag: tag, body)
#let warning(number: "", title: "", tag: "", body) = def-like(kind: "Warning", number: number, title: title, tag: tag, body)
#let exercise(number: "", title: "", tag: "", body) = def-like(kind: "Exercise", number: number, title: title, tag: tag, body)
#let variant(number: "", title: "", tag: "", body) = def-like(kind: "Variant", number: number, title: title, tag: tag, body)
#let construction(number: "", title: "", tag: "", body) = def-like(kind: "Construction", number: number, title: title, tag: tag, body)
#let convention(number: "", title: "", tag: "", body) = def-like(kind: "Convention", number: number, title: title, tag: tag, body)
#let question(number: "", title: "", tag: "", body) = def-like(kind: "Question", number: number, title: title, tag: tag, body)

// Clean Centered Commutative Diagram (Classical LaTeX Display Math style)
#let commutative-diagram(tag: "", latex: "", image-path: none, caption: "") = {
  align(center)[
    #block(spacing: 1.4em)[
      #if image-path != none [
        #image(image-path, width: 45%)
      ] else [
        #text(9pt, style: "italic", fill: rgb("#64748b"))[[Commutative Diagram]]
      ]
    ]
  ]
}

"""

    def __init__(self, chapter: KerodonChapter):
        self.chapter = chapter

    @staticmethod
    def clean_kerodon_tex_for_pandoc(s: str) -> str:
        s = re.sub(r"\\operatorname\{\{\\bf\s*\\Delta\s*\}\}", r"\\mathbf{\\Delta}", s)
        s = re.sub(r"\{\\bf\s*\\Delta\s*\}", r"\\mathbf{\\Delta}", s)
        s = re.sub(r"\\operatorname\{Set_\{?\\Delta\s*\}?\}", r"\\mathrm{Set}_{\\mathbf{\\Delta}}", s)
        s = re.sub(r"\\operatorname\{\\raise\s*\{[^}]*\}\{\\square\s*\}\}", r"\\square", s)
        s = re.sub(r"\\operatorname\{\\partial\s*\\raise\s*\{[^}]*\}\{\\square\s*\}\}", r"\\partial\\square", s)
        s = re.sub(r"\\boldsymbol\s*\{\\sqcap\s*\}", r"\\sqcap", s)
        s = re.sub(r"\\boldsymbol\s*\{\\sqcup\s*\}", r"\\sqcup", s)
        s = re.sub(r"\\textnormal\{", r"\\text{", s)
        s = re.sub(r"\\varinjlim", r"\\mathrm{colim}", s)
        s = re.sub(r"\\varprojlim", r"\\lim", s)
        s = re.sub(r"\\xRightarrow\s*\{([^}]*)\}", r"\\xrightarrow{\\Rightarrow \\; \1}", s)
        s = re.sub(r"\\xhookrightarrow\s*\{([^}]*)\}", r"\\hookrightarrow", s)
        s = re.sub(r"\\Newextarrow\{[^}]*\}\{[^}]*\}\{[^}]*\}", "", s)
        # Ensure space before $ if preceded by letter/punct
        s = re.sub(r"([a-zA-Z0-9,\.\:\;])(?<!\$)\$(?!\$)", r"\1 $", s)
        # Ensure space after $ if followed by letter
        s = re.sub(r"(?<!\$)\$(?!\$)([a-zA-Z0-9])", r"$ \1", s)
        # Clean whitespace immediately inside single $ ... $
        s = re.sub(r"(?<!\$)\$(?!\$)\s*([^\$\n]+?)\s*(?<!\$)\$(?!\$)", r"$\1$", s)
        return s

    def clean_title_for_typst(self, title: str) -> str:
        """Convert any LaTeX math in chapter/section titles to valid Typst syntax."""
        if "$" not in title and "\\" not in title:
            return title.strip()
        s = re.sub(r"\$\s*([^\$]+?)\s*\$", r"$\1$", title)
        res = subprocess.run(
            ["pandoc", "-f", "markdown+tex_math_dollars", "-t", "typst"],
            input=s,
            check=False,
            text=True,
            capture_output=True
        )
        out_t = res.stdout.strip()
        out_t = out_t.replace("times.circle", "⊗").replace("plus.circle", "⊕")
        return out_t
    def generate_typst(self, output_path: Path) -> str:
        """Assemble Typst source document matching authentic LaTeX monograph layout."""
        all_envs: list[KerodonEnvironment] = []
        for sec in self.chapter.sections:
            all_envs.extend(sec.intro_environments)
            for sub in sec.subsections:
                all_envs.extend(sub.environments)

        from concurrent.futures import ThreadPoolExecutor

        clean_kerodon_tex_for_pandoc = self.clean_kerodon_tex_for_pandoc


        def convert_single_env(env: KerodonEnvironment) -> str:
            raw_text = env.body_markdown

            # 1. Replace with alphanumeric placeholder
            diag_map = {}
            def diag_repl(m):
                d_idx = len(diag_map)
                code = m.group(1).strip()
                # Check disk for cropped image
                img_p = None
                fig_candidates = [
                    Path("output/kerodon/figures") / f"diag_{env.tag}_{d_idx+1}.png",
                    Path("output/kerodon/figures") / f"diag_{env.tag}.png"
                ]
                for fc in fig_candidates:
                    if fc.exists():
                        img_p = f"figures/{fc.name}"
                        break
                diag_map[f"DIAGREPLPH{d_idx}ZEROX"] = (code, img_p)
                return f"\n\nDIAGREPLPH{d_idx}ZEROX\n\n"

            text = re.sub(r":::COMMUTATIVE_DIAGRAM:::(.*?):::END_DIAGRAM:::", diag_repl, raw_text, flags=re.DOTALL)
            text = clean_kerodon_tex_for_pandoc(text)

            res = subprocess.run(
                ["pandoc", "-f", "markdown+tex_math_dollars", "-t", "typst"],
                input=text,
                check=False,
                text=True,
                capture_output=True
            )
            body = res.stdout

            # 2. Replace placeholders AFTER pandoc
            for ph, (code, img_p) in diag_map.items():
                safe_code = code.replace("\\", "\\\\").replace('"', '\\"').replace("[", "\\[").replace("]", "\\]")
                img_prop = f'"{img_p}"' if img_p else "none"
                call_code = f'\n#commutative-diagram(tag: "{env.tag}", latex: "{safe_code}", image-path: {img_prop})\n'
                body = body.replace(ph, call_code)

            body = body.replace("times.circle", "⊗").replace("plus.circle", "⊕").replace("dot.circle", "⊙").replace("ast.circle", "⊛")
            body = body.replace("angle.l", "chevron.l").replace("angle.r", "chevron.r")
            body = body.replace("lt.tri", "lt.closed").replace("gt.tri", "gt.closed")
            body = re.sub(r"\bsect\b", "inter", body)
            body = body.replace("boxtimes", "times.square")
            return body.strip()

        with ThreadPoolExecutor(max_workers=10) as ex:
            cleaned_bodies = list(ex.map(convert_single_env, all_envs))

        out = [self.TYPST_PREAMBLE]
        clean_ch_title = self.clean_title_for_typst(self.chapter.title)
        out.append(f"= Chapter {self.chapter.number}: {clean_ch_title}\n")
        out.append("#v(0.5em)\n")

        if self.chapter.intro_text:
            clean_intro = self.clean_title_for_typst(self.chapter.intro_text)
            out.append(f"{clean_intro}\n\n#v(1em)\n")

        env_cursor = 0
        for sec in self.chapter.sections:
            clean_sec_title = self.clean_title_for_typst(sec.title)
            out.append(f"== Section {sec.number}: {clean_sec_title}\n\n")

            for env in sec.intro_environments:
                body = cleaned_bodies[env_cursor] if env_cursor < len(cleaned_bodies) else env.body_markdown
                env_cursor += 1
                out.append(self._wrap_environment(env, body))

            for sub in sec.subsections:
                clean_sub_title = self.clean_title_for_typst(sub.title)
                out.append(f"=== Subsection {sub.number}: {clean_sub_title}\n\n")

                for env in sub.environments:
                    body = cleaned_bodies[env_cursor] if env_cursor < len(cleaned_bodies) else env.body_markdown
                    env_cursor += 1
                    out.append(self._wrap_environment(env, body))

        typ_code = "\n".join(out)
        Path(output_path).write_text(typ_code, encoding="utf-8")
        return typ_code

    def _wrap_environment(self, env: KerodonEnvironment, typst_body: str) -> str:
        """Wrap body text in styled Typst environment matching classical LaTeX."""
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
        elif "variant" in t:
            func_name = "variant"
        elif "construction" in t:
            func_name = "construction"
        elif "convention" in t:
            func_name = "convention"
        elif "question" in t:
            func_name = "question"
        else:
            func_name = "remark"

        safe_title = self.clean_title_for_typst(env.title).replace('"', '\\"') if env.title else ""
        return f'#{func_name}(number: "{env.number}", title: "{safe_title}", tag: "{env.tag}")[\n{typst_body}\n]\n\n'

    def compile_pdf(self, typst_path: Path, pdf_path: Path):
        """Compile Typst source to PDF via nix shell."""
        cmd = ["nix", "shell", "nixpkgs#typst", "--command", "typst", "compile", str(typst_path), str(pdf_path)]
        subprocess.run(cmd, check=True)

    def generate_latex(self, output_path: Path) -> str:
        """Generate master XeLaTeX document with native xypic and tikz-cd support."""
        out = [
            r"\documentclass[11pt,letterpaper]{book}",
            r"\usepackage{amsmath,amssymb,amsthm}",
            r"\usepackage[all,cmtip]{xy}",
            r"\usepackage{tikz-cd}",
            r"\usepackage{hyperref}",
            r"\usepackage[margin=1.25in]{geometry}",
            r"\newtheorem{theorem}{Theorem}[section]",
            r"\newtheorem{proposition}[theorem]{Proposition}",
            r"\newtheorem{lemma}[theorem]{Lemma}",
            r"\newtheorem{corollary}[theorem]{Corollary}",
            r"\theoremstyle{definition}",
            r"\newtheorem{definition}[theorem]{Definition}",
            r"\newtheorem{example}[theorem]{Example}",
            r"\newtheorem{remark}[theorem]{Remark}",
            r"\newtheorem{notation}[theorem]{Notation}",
            r"\newtheorem{warning}[theorem]{Warning}",
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
        elif "warning" in t:
            env_name = "warning"
        elif "exercise" in t:
            env_name = "exercise"

        title_arg = f"[{env.title}]" if env.title else ""
        body = env.body_markdown

        def replace_diag_tex(m):
            code = m.group(1).strip()
            return f"\n\\[\n{code}\n\\]\n"

        body = re.sub(r":::COMMUTATIVE_DIAGRAM:::(.*?):::END_DIAGRAM:::", replace_diag_tex, body, flags=re.DOTALL)
        return f"\\begin{{{env_name}}}{title_arg} \\label{{tag:{env.tag}}}\n{body}\n\\end{{{env_name}}}\n\n"
