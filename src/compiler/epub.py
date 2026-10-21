"""EPUB and LaTeX compilers using Pandoc and custom stylesheets."""

import subprocess
from pathlib import Path

from ..parser.stitcher import ParsedBook

DEFAULT_EPUB_CSS = """
body {
    font-family: "PingFang SC", "Songti SC", "Noto Serif CJK SC", serif;
    line-height: 1.65;
    margin: 5%;
    text-align: justify;
}

h1, h2, h3, h4 {
    font-family: "PingFang SC", "Heiti SC", sans-serif;
    font-weight: bold;
    color: #111111;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 {
    font-size: 1.8em;
    border-bottom: 2px solid #eaeaea;
    padding-bottom: 0.3em;
}

h2 {
    font-size: 1.4em;
}

h3 {
    font-size: 1.15em;
}

p {
    text-indent: 2em;
    margin: 0.5em 0;
}

figure {
    text-align: center;
    margin: 1.5em auto;
}

figure img {
    max-width: 95%;
    height: auto;
    display: block;
    margin: 0 auto;
}

figcaption {
    font-size: 0.9em;
    color: #555555;
    margin-top: 0.5em;
    font-style: italic;
    text-indent: 0;
}
"""


class PandocCompilers:
    def __init__(self, book: ParsedBook):
        self.book = book

    def generate_markdown(self) -> str:
        b = self.book
        lines = [
            f"% {b.title}",
            f"% {b.author}",
            f"% 译者：{b.translator} | {b.publisher}",
            "",
            f"# {b.title}",
            "",
            f"*{b.subtitle}*",
            "",
            f"**作者**：{b.author}  ",
            f"**译者**：{b.translator}  ",
            f"**出版社**：{b.publisher}  ",
            "",
            "---",
            ""
        ]

        figures_by_id = {f.figure_id: f for f in b.figures}

        for sec in b.sections:
            if not sec.content_blocks:
                continue

            if sec.level == 2:
                lines.append(f"\n# {sec.title}\n")
            elif sec.level == 3:
                lines.append(f"\n## {sec.title}\n")
            else:
                lines.append(f"\n### {sec.title}\n")

            for block in sec.content_blocks:
                if block.startswith("__FIGURE_") and block.endswith("__"):
                    fig_id_str = block[len("__FIGURE_"):-len("__")]
                    try:
                        fig_id = int(fig_id_str)
                        fig = figures_by_id.get(fig_id)
                        if fig:
                            import re
                            clean_caption = re.sub(r"^(图\s*\d+\s*|Figure\s*\d+\s*[:\.\s]*)", "", fig.caption).strip()
                            lines.append(f"\n![图 {fig.figure_id} {clean_caption}]({fig.image_rel_path})\n")
                    except ValueError:
                        continue
                elif block.startswith("__CITATION__"):
                    citation = block[len("__CITATION__"):]
                    lines.append(f"\n* {citation}\n")
                elif block.startswith("__ACK__"):
                    ack_text = block[len("__ACK__"):]
                    lines.append(f"\n> **特别鸣谢**：{ack_text}\n")
                else:
                    clean_p = block.strip()
                    if clean_p:
                        lines.append(f"\n{clean_p}\n")

        return "\n".join(lines)

    def compile_epub(self, md_path: Path, output_epub: Path, css_path: Path | None = None) -> Path:
        output_epub.parent.mkdir(parents=True, exist_ok=True)
        if not css_path:
            css_path = output_epub.parent / "epub.css"
            with open(css_path, "w") as f:
                f.write(DEFAULT_EPUB_CSS)

        cmd = [
            "pandoc", str(md_path.resolve()),
            "-o", str(output_epub.resolve()),
            "--css", str(css_path.resolve()),
            "--toc", "--toc-depth=3",
            "--metadata", f"title={self.book.title}",
            "--metadata", f"author={self.book.author}",
            "--metadata", f"publisher={self.book.publisher}",
            "--metadata", "lang=zh-CN"
        ]
        res = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(md_path.parent.resolve()))
        if res.returncode != 0:
            raise RuntimeError(f"EPUB compilation failed:\n{res.stderr}")
        return output_epub

    def compile_latex(self, md_path: Path, output_tex: Path) -> Path:
        output_tex.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "pandoc", str(md_path.resolve()),
            "-o", str(output_tex.resolve()),
            "--standalone",
            "--toc",
            "--pdf-engine=xelatex",
            "-V", "documentclass=ctexbook",
            "-V", "geometry:margin=2.5cm"
        ]
        res = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(md_path.parent.resolve()))
        if res.returncode != 0:
            raise RuntimeError(f"LaTeX generation failed:\n{res.stderr}")
        return output_tex
