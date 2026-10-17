"""Dedicated compiler for John Roberts' The Modern Firm with highest publisher standards."""

import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

ROBERTS_TYPST_HEADER = """
#set document(title: "现代企业：基于绩效与增长的组织设计", author: "约翰·罗伯茨")

// --- Classical Book Geometry (A5 Monograph Golden Section) ---
#set page(
  paper: "a5",
  margin: (top: 2.2cm, bottom: 2.2cm, inside: 2.3cm, outside: 1.8cm),
  header: context {
    let p = counter(page).get().first()
    let ch_on_page = query(selector(heading.where(level: 1))).filter(h => h.location().page() == p)
    if p > 4 and ch_on_page.len() == 0 {
      if calc.even(p) {
        align(left, text(8.5pt, fill: rgb("#555555"), font: "Songti SC")[现代企业：基于绩效与增长的组织设计])
      } else {
        let headings = query(selector(heading.where(level: 1)).before(here()))
        let cur_chap = if headings.len() > 0 { headings.last().body } else { [] }
        align(right, text(8.5pt, fill: rgb("#555555"), font: "Songti SC")[#cur_chap])
      }
      line(length: 100%, stroke: 0.4pt + rgb("#cccccc"))
    }
  },
  footer: context {
    let p = counter(page).get().first()
    if p > 2 {
      align(center, text(9pt, fill: rgb("#444444"), font: "Charter")[#p])
    }
  }
)

// --- Classical Academic Book Typography ---
#set text(
  font: ("Songti SC", "STSong", "Hiragino Mincho ProN", "Charter", "Libertinus Serif"),
  size: 10pt,
  lang: "zh",
  hyphenate: false
)

#set par(
  justify: true,
  first-line-indent: 2em,
  leading: 1.25em,
  spacing: 1.25em
)

// --- Classical Book Heading Hierarchy (Songti SC Bold) ---
#show heading: set text(font: "Songti SC", weight: "bold")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(1.2cm)
  text(18pt, weight: "bold", fill: rgb("#0f172a"))[#it.body]
  v(0.8cm)
}

#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em)[
  #text(13pt, weight: "bold", fill: rgb("#1e293b"))[#it.body]
]

#show heading.where(level: 3): it => block(above: 1.2em, below: 0.5em)[
  #text(11pt, weight: "bold", fill: rgb("#334155"))[#it.body]
]

// --- Figure & Caption Styling ---
#set figure(supplement: [图], numbering: "1")
#show figure: set block(spacing: 1.8em)
#show figure.caption: it => [
  #v(0.5em)
  #text(8.5pt, fill: rgb("#555555"), font: "Songti SC")[#it.supplement #context it.counter.display(it.numbering)#h(0.6em)#it.body]
]

#set table(stroke: none, inset: (x: 0.2em, y: 0.3em))
#show table: set text(size: 9.5pt)
#show figure.where(kind: table): it => block(width: 100%, breakable: false, above: 1.4em, below: 1.2em)[
  #set par(leading: 0.4em, first-line-indent: 0pt, spacing: 0pt)
  #set block(spacing: 0pt)
  #line(length: 100%, stroke: 0.8pt)
  #v(0.45em)
  #grid(
    columns: (auto, 1fr),
    column-gutter: 1.2em,
    text(9pt, weight: "bold", font: "Songti SC")[#it.supplement #context it.counter.display(it.numbering)],
    align(center, text(9pt, weight: "bold", font: "Songti SC")[#it.caption.body]),
  )
  #v(0.45em)
  #line(length: 100%, stroke: 0.4pt)
  #it.body
  #v(0.2em)
  #line(length: 100%, stroke: 0.8pt)
]

// --- Front Matter ---
#align(center + horizon)[
  #text(9.5pt, tracking: 0.25em, fill: rgb("#64748b"), font: "Songti SC")[当代世界学术名著 · 经济学系列]
  #v(1.2cm)
  #text(22pt, weight: "bold", font: "Songti SC")[现代企业：基于绩效与增长的组织设计]
  #v(0.4cm)
  #text(11.5pt, fill: rgb("#475569"), font: "Charter")[The Modern Firm: Organizational Design for Performance and Growth]
  #v(2.5cm)
  #text(11.5pt, font: "Songti SC")[约翰·罗伯茨 (John Roberts) / 著]
  #v(0.3cm)
  #text(11pt, font: "Songti SC")[马志英 / 译]
  #v(3.0cm)
  #text(10.5pt, fill: rgb("#475569"), font: "Songti SC")[中国人民大学出版社]
]
#pagebreak()

// --- Dynamic Table of Contents ---
#outline(title: [目 录], indent: 1.5em, depth: 3)
#pagebreak()
"""

ROBERTS_FIGURES_META = {
    1: "设计问题就是在特定的环境下选择战略和组织以达到最大绩效",
    2: "互补性可以产生离散的内在相互匹配模式",
    3: "选择和绩效关系的经典模型",
    4: "选择和绩效的关系发生改变",
    5: "非凹性的绩效关系",
    6: "非凹性允许存在多个不同的内在相互匹配的点",
    7: "非凹性绩效关系转变导致最佳绩效点的不连续改变",
    8: "合作和主动行为",
    9: "长期关系拓宽了可实现的行为的组合",
}


def fix_cjk_english_typography(line: str) -> str:
    s = line.strip()
    if not s or s.startswith(("#", "![", "|", ": ")):
        return s
    if re.match(r"^图\s*[1-9]\s+(?!来进行说明)", s) or re.match(r"^表\s*[12]\s+", s):
        return s

    exact_replacements = [
        ("（General Motor)，", "（General Motors），"),
        ("（General Motor)", "（General Motors）"),
        ("（Pekka Ala - Pietila)（", "（Pekka Ala-Pietilä）（"),
        ("（Pekka Ala - Pietila)", "（Pekka Ala-Pietilä）"),
        ("Katherine Doonik", "Katherine Doornik"),
        ("Collin Mayer", "Colin Mayer"),
        ("Montgomery and Wernerfeldt", "Montgomery and Wernerfelt"),
        ("Montgomery and Wernerfeld", "Montgomery and Wernerfelt"),
        ("Stultz（1990）", "Stulz (1990)"),
        ("Saioner", "Saloner"),
        ("Company of Adventures", "Company of Adventurers"),
        ("Lincoln Electric company", "Lincoln Electric Company"),
        ("都在水平2上操作", "都在水平 $2$ 上操作"),
        ("都在水平 2 上操作", "都在水平 $2$ 上操作"),
        ("活动的水平到3", "活动的水平到 $3$"),
        ("活动的水平到 3", "活动的水平到 $3$"),
    ]
    for old, new in exact_replacements:
        s = s.replace(old, new)

    s = re.sub(r"(?<![\$A-Za-z])([XYZR])\s*点", r"$\1$ 点", s)
    s = re.sub(r"(?<![\$A-Za-z])X'\s*处", r"$X'$ 处", s)
    s = re.sub(r"(标记(?:为|的)|朝向)\s*(?<![\$A-Za-z])([XYAB])(?![A-Za-z\$])", r"\1 $\2$", s)
    s = re.sub(r"即\s*(?<![\$A-Za-z])B(?=\s*[，。])", r"即 $B$", s)
    s = re.sub(r"(?<![\$A-Za-z])A\s*和\s*B(?![A-Za-z\$])", r"$A$ 和 $B$", s)
    s = re.sub(r"从\s*(?<![\$A-Za-z])X\s*转变到\s*Y(?![A-Za-z\$])", r"从 $X$ 转变到 $Y$", s)
    s = re.sub(r"从\s*(?<![\$A-Za-z])X\s*转变到\s*\$Y\$", r"从 $X$ 转变到 $Y$", s)

    s = re.sub(r"([\u4e00-\u9fff])\s*,\s*(?=[\u4e00-\u9fff\[])", r"\1，", s)
    s = re.sub(r"(?<=[a-zA-Z0-9%\)\$])\s*,\s*(?=[\u4e00-\u9fff])", "，", s)
    s = re.sub(r"([\u4e00-\u9fff])\s*;\s*", r"\1；", s)
    s = re.sub(r";\s*(?=[\u4e00-\u9fff])", "；", s)
    s = re.sub(r"([\u4e00-\u9fff])\s*:\s*(?=[\u4e00-\u9fff])", r"\1：", s)
    s = re.sub(r"([\u4e00-\u9fff])\s*!\s*", r"\1！", s)
    s = re.sub(r"([\u4e00-\u9fff])\s*\?\s*", r"\1？", s)

    s = re.sub(r"\(([^()]*[\u4e00-\u9fff][^()]*)\)", r"（\1）", s)
    s = re.sub(r"([\u4e00-\u9fff\u201d])\s*\(([^()]+)\)(?=\s*[\u4e00-\u9fff，。；：！？、])", r"\1（\2）", s)
    s = re.sub(r"（([^（）]+)\)", r"（\1）", s)
    s = re.sub(r"\(([^（）]+)）", r"（\1）", s)

    s = re.sub(r"([A-Za-z\.\u00C0-\u017F]+)\s*（(\d{4}[a-z]?(?:\s*[，,;；:]\s*[\d\-a-z]+)*)）", r"\1 (\2)", s)
    s = re.sub(r"([A-Za-z\.\u00C0-\u017F]+)\((\d{4}[a-z]?)", r"\1 (\2", s)

    def _norm_en_paren(m: re.Match) -> str:
        inner = m.group(1)
        if re.search(r"[\u4e00-\u9fff]", inner):
            return m.group(0)
        inner = re.sub(r"\s*；\s*", "; ", inner)
        inner = re.sub(r"\s*，\s*", ", ", inner)
        inner = re.sub(r"\s*：\s*", ": ", inner)
        inner = re.sub(r"([A-Za-z\.\u00C0-\u017F]+)\((\d{4})", r"\1 (\2", inner)
        return f"（{inner}）"

    s = re.sub(r"（([^（）]+)）", _norm_en_paren, s)

    s = re.sub(r"(?<!\[)图\s*([1-9])(?!\])", r"[图 \1](#fig:\1)", s)
    s = re.sub(r"(?<!\[)表\s*([12])(?!\])", r"[表 \1](#tab:\1)", s)

    s = re.sub(r"([\u4e00-\u9fff])(\$[^\$]+\$)", r"\1 \2", s)
    s = re.sub(r"(\$[^\$]+\$)([\u4e00-\u9fff])", r"\1 \2", s)
    s = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z0-9%\)])([\u4e00-\u9fff])", r"\1 \2", s)
    s = re.sub(r"([\u4e00-\u9fff])(\[图\s*\d+\]\(#fig:\d+\))", r"\1 \2", s)
    s = re.sub(r"(\[图\s*\d+\]\(#fig:\d+\))([\u4e00-\u9fff])", r"\1 \2", s)
    s = re.sub(r"([\u4e00-\u9fff])(\[表\s*\d+\]\(#tab:\d+\))", r"\1 \2", s)
    s = re.sub(r"(\[表\s*\d+\]\(#tab:\d+\))([\u4e00-\u9fff])", r"\1 \2", s)
    s = re.sub(r"(。\s*\[\d+\])(?=[\u4e00-\u9fff])", r"\1 ", s)

    s = re.sub(r" {2,}", " ", s)
    return s


def clean_and_strip_page_lines(pno: int, text: str) -> List[str]:
    """Strip scanned headers, footers, and redundant titles from raw page text."""
    text = re.sub(r"<table>.*?</table>", "", text, flags=re.S)
    lines = text.splitlines()
    cleaned = []

    real_chapter_openers = {11, 30, 55, 80, 116, 151, 173}

    for idx, l in enumerate(lines):
        s = l.strip()
        if not s:
            continue

        # Strip scanned running headers
        if idx == 0:
            if s == "现代企业：基于绩效与增长的组织设计":
                continue
            if re.match(r"^(?:#+\s*)?第\s*\d+\s*章", s) and pno not in real_chapter_openers:
                continue
            if pno in (7, 8) and s in ["前言", "# 前言", "## 前言"]:
                continue

        # Strip standalone page folios
        if re.match(r"^—?\s*\d+\s*—?$", s):
            continue

        if pno == 5 and s.startswith("#"):
            cleaned.append("# 出版说明")
            continue

        if pno == 6 and s in ("# 前言", "## 前言", "前言"):
            cleaned.append("# 前言")
            continue

        if pno in real_chapter_openers and re.match(r"^#+\s*第\s*(\d+)\s*章\s+(.*)$", s):
            m_ch = re.match(r"^#+\s*第\s*(\d+)\s*章\s+(.*)$", s)
            if m_ch:
                cleaned.append(f"# 第{m_ch.group(1)}章 {m_ch.group(2).strip()}")
                continue

        if pno in (93, 103) and s.startswith("# "):
            cleaned.append("#" + s)
            continue

        if s in ("**注释**", "# 注释", "## 注释"):
            cleaned.append("## 注释")
            continue

        if s.startswith("## "):
            s = re.sub(r"\[\d+\]$", "", s).strip()
            cleaned.append(s)
            continue

        m_fig = re.match(r"^图\s*([1-9])\s+(.*)$", s)
        if m_fig:
            fig_id = int(m_fig.group(1))
            rest = m_fig.group(2).strip()
            if not rest.startswith("来进行说明"):
                cap = ROBERTS_FIGURES_META.get(fig_id, rest)
                cleaned.append(f"![{cap}](figures/fig_{fig_id}.svg){{#fig:{fig_id}}}")
                continue

        m_tab = re.match(r"^表\s*([12])\s+(.*)$", s)
        if m_tab:
            tab_id = int(m_tab.group(1))
            tab_title = m_tab.group(2).strip()
            cleaned.append(f"__TABLE_CAPTION_{tab_id}__:{tab_title}")
            continue

        if s.startswith("|"):
            cleaned.append(s)
            continue

        cleaned.append(s)

    return cleaned


def _is_para_complete(para_str: str) -> bool:
    s = re.sub(r"(?:\[\d+\])+$", "", para_str.strip()).strip()
    if not s:
        return True
    open_paren = (s.count("（") + s.count("(")) > (s.count("）") + s.count(")"))
    if open_paren:
        return False
    return s.endswith(("。", "！", "？", "”", "’", "…", "）", ")"))


def heal_and_weld_corpus(pages_data: List[Tuple[int, List[str]]]) -> str:
    """Seamlessly weld paragraphs across physical page breaks preventing orphan words and unclosed parentheses."""
    corpus_blocks: List[str] = []
    current_para: List[str] = []
    pending_figures: List[str] = []
    pending_table_caption: tuple[int, str] | None = None
    current_table: list[str] = []

    def _flush_table() -> None:
        nonlocal current_table, pending_table_caption
        if current_table:
            table_block = "\n".join(current_table)
            if pending_table_caption is not None:
                tab_id, tab_title = pending_table_caption
                table_block += f"\n\n: {tab_title} {{#tab:{tab_id}}}"
                pending_table_caption = None
            corpus_blocks.append(table_block)
            current_table = []

    for pno, lines in pages_data:
        for line in lines:
            if line.startswith("__TABLE_CAPTION_"):
                if current_para:
                    corpus_blocks.append(fix_cjk_english_typography("".join(current_para)))
                    current_para = []
                _flush_table()
                m_tc = re.match(r"^__TABLE_CAPTION_(\d+)__:(.*)$", line)
                if m_tc:
                    pending_table_caption = (int(m_tc.group(1)), m_tc.group(2))
                continue

            if line.startswith("|"):
                if current_para:
                    corpus_blocks.append(fix_cjk_english_typography("".join(current_para)))
                    current_para = []
                current_table.append(line)
                continue

            if current_table:
                _flush_table()

            if line.startswith("#"):
                if current_para:
                    corpus_blocks.append(fix_cjk_english_typography("".join(current_para)))
                    current_para = []
                if pending_figures:
                    corpus_blocks.extend(pending_figures)
                    pending_figures = []
                corpus_blocks.append(line)
                continue

            if line.startswith("!["):
                if current_para and not _is_para_complete("".join(current_para)):
                    pending_figures.append(line)
                else:
                    if current_para:
                        corpus_blocks.append(fix_cjk_english_typography("".join(current_para)))
                        current_para = []
                    corpus_blocks.append(line)
                continue

            if not current_para:
                current_para = [line]
            else:
                prev_joined = "".join(current_para)
                if _is_para_complete(prev_joined):
                    corpus_blocks.append(fix_cjk_english_typography(prev_joined))
                    if pending_figures:
                        corpus_blocks.extend(pending_figures)
                        pending_figures = []
                    current_para = [line]
                else:
                    if re.search(r"[a-zA-Z0-9]$", prev_joined) and re.match(r"^[a-zA-Z0-9]", line):
                        current_para.append(" " + line)
                    else:
                        current_para.append(line)
                    if _is_para_complete("".join(current_para)) and pending_figures:
                        corpus_blocks.append(fix_cjk_english_typography("".join(current_para)))
                        current_para = []
                        corpus_blocks.extend(pending_figures)
                        pending_figures = []

    if current_table:
        _flush_table()
    if current_para:
        corpus_blocks.append(fix_cjk_english_typography("".join(current_para)))
    if pending_figures:
        corpus_blocks.extend(pending_figures)

    return "\n\n".join(corpus_blocks)


def assemble_jina_bibliography(md_dir: Path) -> Tuple[str, str]:
    entries: List[str] = []
    ack_text = ""

    for pno in range(177, 191):
        p = md_dir / f"p_{pno:03d}.md"
        if not p.exists():
            continue
        for raw_line in p.read_text(encoding="utf-8").splitlines():
            s = raw_line.strip()
            if not s:
                continue
            if s in ("# 参考文献*", "# 参考文献", "参考文献", "现代企业：基于绩效与增长的组织设计"):
                continue
            if "核对了书中的参考文献" in s:
                ack_text = s.lstrip("* ").strip()
                continue
            is_new = bool(re.match(r"^(?:[A-Z]|[\u2014\-]{2,})", s)) and bool(
                re.search(r"[\(\uff08]\d{4}", s[:110])
            )
            if is_new or not entries:
                entries.append(s)
            else:
                prev = entries[-1]
                if prev.endswith("-*"):
                    entries[-1] = prev[:-2] + s.replace(", ", "*, ", 1)
                elif prev.endswith("-"):
                    entries[-1] = prev[:-1] + s
                else:
                    entries[-1] = prev + " " + s

    formatted_entries: List[str] = []
    for e in entries:
        e = e.replace("（", "(").replace("）", ")").replace("Saioner", "Saloner")
        if "*" not in e:
            e = re.sub(r"(”\s+)([A-Z][A-Za-z\s&\:\-]+?)(,\s*\d+)", r"\1*\2*\3", e, count=1)
        formatted_entries.append(e)

    md_lines = ["# 参考文献", ""]
    for e in formatted_entries:
        md_lines.append(f"* {e}")
    if ack_text:
        md_lines.extend(["", f"> **特别鸣谢**：{ack_text}"])

    typ_lines = ["= 参考文献", ""]
    if ack_text:
        typ_lines.extend(
            [
                '#block(fill: rgb("#f8fafc"), inset: 1em, radius: 4pt, stroke: 0.5pt + rgb("#cbd5e1"))[',
                f'  #text(size: 9pt, fill: rgb("#475569"))[*特别鸣谢*：{ack_text}]',
                "]",
                "#v(0.8em)",
                "",
            ]
        )
    typ_lines.append('#set text(font: ("Charter", "Libertinus Serif", "Songti SC"))')
    typ_lines.append("#set par(hanging-indent: 2em, first-line-indent: 0em, spacing: 0.85em)")
    for e in formatted_entries:
        t_entry = re.sub(r"\*([^*]+)\*", r"#emph[\1]", e)
        typ_lines.append(f"{t_entry}\n")

    return "\n".join(md_lines), "\n".join(typ_lines)


class RobertsJinaTypstCompiler:
    def __init__(self, md_dir: Path, figures_dir: Path):
        self.md_dir = md_dir
        self.figures_dir = figures_dir

    def convert_markdown_to_typst_body(self, full_md_path: Path) -> str:
        cmd = ["pandoc", str(full_md_path), "-f", "markdown", "-t", "typst"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Pandoc conversion failed:\n{res.stderr}")
        return res.stdout

    def assemble_and_compile(self, out_typ_path: Path, out_pdf_path: Path) -> Path:
        out_typ_path.parent.mkdir(parents=True, exist_ok=True)
        out_dir = out_typ_path.parent.resolve()

        # 1. Clean and gather pages
        pages_data: List[Tuple[int, List[str]]] = []

        p5 = self.md_dir / "p_005.md"
        if p5.exists():
            p5_lines = clean_and_strip_page_lines(5, p5.read_text(encoding="utf-8"))
            pages_data.append((5, p5_lines))

        # p_006 to p_008: 前言
        for pno in [6, 7, 8]:
            p = self.md_dir / f"p_{pno:03d}.md"
            if p.exists():
                c_lines = clean_and_strip_page_lines(pno, p.read_text(encoding="utf-8"))
                if c_lines:
                    pages_data.append((pno, c_lines))

        # Chapters 1 to 7 (p_011 to p_176)
        for pno in range(11, 177):
            p = self.md_dir / f"p_{pno:03d}.md"
            if p.exists():
                c_lines = clean_and_strip_page_lines(pno, p.read_text(encoding="utf-8"))
                if c_lines:
                    pages_data.append((pno, c_lines))

        # Weld corpus across page breaks
        welded_body = heal_and_weld_corpus(pages_data)
        bib_md, bib_typst = assemble_jina_bibliography(self.md_dir)

        combined_md_path = out_dir / "combined_roberts_jina.md"
        combined_md_path.write_text(welded_body + "\n\n", encoding="utf-8")

        book_md_path = out_dir / "book.md"
        book_md_path.write_text(welded_body + "\n\n" + bib_md + "\n", encoding="utf-8")

        # Convert to Typst body
        typst_body = self.convert_markdown_to_typst_body(combined_md_path)

        # Inject vector figures
        for fig_id, cap_label in ROBERTS_FIGURES_META.items():
            fig_snippet = (
                f"\n#figure(\n"
                f'  image("figures/fig_{fig_id}.svg"),\n'
                f"  caption: [{cap_label}]\n"
                f") <fig-{fig_id}>\n"
            )
            typst_body = re.sub(
                rf"#figure\(\s*image\(\"figures/fig_{fig_id}\.svg\"\).*?\)(?:\s*<fig:{fig_id}>)?",
                lambda _: fig_snippet.strip(),
                typst_body,
                flags=re.S,
            )

        typst_body = re.sub(r"#link\(<fig:(\d+)>\)\[图\s*\1\];?", r"@fig-\1", typst_body)
        typst_body = re.sub(r"#link\(<tab:(\d+)>\)\[表\s*\1\];?", r"@tab-\1", typst_body)
        typst_body = re.sub(
            r",\s*caption:\s*\[([^\]]+?)\s*\{\\#tab:([12])\}\]\s*,\s*kind:\s*table\s*\)",
            r',\n  caption: figure.caption(position: top, [\1]),\n  supplement: [表],\n  numbering: "1",\n  kind: table,\n) <tab-\2>',
            typst_body,
        )
        typst_body = re.sub(
            r"columns: 2,\s*align: \(auto,auto,\),\s*table\.header\(\[(逻辑[^\]]*)\], \[\],\),\s*table\.hline\(\),",
            r"columns: (1fr, 1fr),\n    align: left + horizon,\n    table.cell(colspan: 2, inset: (x: 0.2em, y: 0.5em))[*\1*],\n    table.hline(stroke: 0.4pt),",
            typst_body,
        )

        # Clean any stray unescaped closing brackets that could cause parse errors
        typst_body = re.sub(r"\n\](?=[^\n\]]+)", r"\n\\]", typst_body)

        full_typst = ROBERTS_TYPST_HEADER + "\n\n" + typst_body + "\n\n#pagebreak(weak: true)\n" + bib_typst

        with open(out_typ_path, "w", encoding="utf-8") as fp:
            fp.write(full_typst)

        # Compile PDF
        out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "nix", "--extra-experimental-features", "nix-command flakes", "shell", "nixpkgs#typst",
            "--command", "typst", "compile", str(out_typ_path.resolve()), str(out_pdf_path.resolve())
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(out_dir))
        if res.returncode != 0:
            raise RuntimeError(f"Typst compilation failed:\n{res.stderr}")

        out_tex_path = out_typ_path.with_suffix(".tex")
        subprocess.run(
            [
                "pandoc",
                str(book_md_path.resolve()),
                "-f",
                "markdown",
                "-t",
                "latex",
                "--standalone",
                "-V",
                "documentclass=ctexbook",
                "-o",
                str(out_tex_path.resolve()),
            ],
            check=True,
            cwd=str(out_dir),
        )
        tex_text = out_tex_path.read_text(encoding="utf-8")
        tex_text = re.sub(r"\\hyperref\[fig:(\d+)\]\{图\s*\1\}", r"图~\\ref{fig:\1}", tex_text)
        tex_text = re.sub(r"\\hyperref\[tab:(\d+)\]\{表\s*\1\}", r"表~\\ref{tab:\1}", tex_text)
        tex_text = re.sub(
            r"\\caption\{([^\n\}]+?)\s*\\\{\\#tab:([12])\\\}",
            r"\\caption{\1}\\label{tab:\2}",
            tex_text,
        )
        out_tex_path.write_text(tex_text, encoding="utf-8")

        out_epub_path = out_typ_path.with_suffix(".epub")
        subprocess.run(
            [
                "pandoc",
                str(book_md_path.resolve()),
                "-f",
                "markdown",
                "-t",
                "epub3",
                "--mathml",
                "--toc",
                "--toc-depth=2",
                "--metadata",
                "title=现代企业：基于绩效与增长的组织设计",
                "--metadata",
                "author=约翰·罗伯茨 (John Roberts)",
                "--metadata",
                "lang=zh-CN",
                f"--resource-path={out_dir}",
                "-o",
                str(out_epub_path.resolve()),
            ],
            check=True,
            cwd=str(out_dir),
        )

        return out_pdf_path
