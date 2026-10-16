"""Academic Bibliography Parser and Formatter matching highest university press standards."""

import re
from dataclasses import dataclass
from typing import List, Tuple
from ..ocr.base import OCRPage


class BibliographyParser:
    def __init__(self, pages: List[OCRPage]):
        # Filter bibliography pages: from page 177 through 190
        self.bib_pages = [p for p in pages if 177 <= p.page_number <= 190]
        self.acknowledgement = (
            "顾晓波、冯丽君、胡安莱、曾景、王晓、孙晖、程诗、付欢、王小芽、马慕薇、"
            "张伟、李军、王建昌、王晓东、李一凡、刘燕平、刘蕊、范阳阳、秦升、程悦、"
            "徐秋慧、钟红英、赵文荣、李朝气、马二排、罗宇、刘头坤核对了书中的参考文献，在此表示感谢。"
        )

    def parse(self) -> Tuple[List[str], str]:
        """Extract and clean individual citation entries from OCR pages."""
        raw_lines = []
        for p in self.bib_pages:
            for l in p.lines:
                if l.y > 0.88 or l.y < 0.08:
                    continue
                t = l.text.strip()
                if not t or t == "参考文献":
                    continue
                raw_lines.append((l.x, l.y, l.w, t))

        citations = []
        current_entry = []

        def clean_punct(s: str) -> str:
            # Remove any Chinese acknowledgement text that leaked into the line
            s = re.sub(r"[\*＊]?[\u4e00-\u9fa5\s、，。]+核对了书中的参考文献[^\.]*", "", s)
            s = re.sub(r"[\u4e00-\u9fa5、]{8,}", "", s)
            s = s.replace("，", ", ").replace("：", ": ").replace("（", " (").replace("）", ") ")
            s = s.replace('”', '"').replace('“', '"').replace('’', "'").replace('‘', "'")
            s = re.sub(r"\s+", " ", s).strip()
            s = re.sub(r"(\d+)\s*[\-—–]\s*(\d+)", r"\1–\2", s)
            return s.strip()

        for x, y, w, text in raw_lines:
            if "核对了书中的参考文献" in text or "顾晓波" in text or "王晓东" in text or "在此表示感谢" in text:
                continue

            clean_t = text.strip()
            is_new = False
            # Starts with Author, Year: e.g. "Akerlof, G. A. (1970)" or "Abreu, D."
            if re.match(r"^[A-Z][a-zA-Z\s\.\,\'\-]{2,35}\s*\([12][09][0-9]{2}", clean_t):
                is_new = True
            elif re.match(r"^[A-Z][a-z]+,\s*[A-Z]\.", clean_t):
                is_new = True
            elif re.match(r"^[—\-\–\s]*\([12][09][0-9]{2}[a-z]?\)", clean_t):
                is_new = True

            if is_new and current_entry:
                entry_text = clean_punct(" ".join(current_entry))
                if len(entry_text) > 12:
                    citations.append(entry_text)
                current_entry = [text]
            else:
                if current_entry and current_entry[-1].endswith("-"):
                    current_entry[-1] = current_entry[-1][:-1] + text
                else:
                    current_entry.append(text)

        if current_entry:
            entry_text = clean_punct(" ".join(current_entry))
            if len(entry_text) > 12:
                citations.append(entry_text)

        # Split any combined repeat-author citations (e.g. "... New York: Free Press. - (1985) ...")
        expanded = []
        for c in citations:
            parts = re.split(r"(?<=\.)\s+([—\-]\s*\([12][09][0-9]{2}[a-z]?\)\s*)", c)
            if len(parts) > 1:
                base_author = c.split("(")[0].strip()
                expanded.append(parts[0].strip())
                for i in range(1, len(parts), 2):
                    dash_year = parts[i].strip()
                    rest = parts[i+1].strip() if i+1 < len(parts) else ""
                    expanded.append(f"{base_author} {dash_year} {rest}".strip())
            else:
                expanded.append(c)

        # Sort alphabetically
        expanded.sort(key=lambda s: s.lower())

        return expanded, self.acknowledgement

    @staticmethod
    def format_author_date_entry(entry: str) -> str:
        """Format raw entry into Chicago/OUP Author-Date standard."""
        m = re.match(r"^([^\(]+?)\s*[\(\[]\s*([12][09][0-9]{2}[a-z]?)\s*[\)\]][\.\s]*(.*)", entry)
        if not m:
            return entry

        author = m.group(1).strip().rstrip(".,")
        year = m.group(2).strip()
        rest = m.group(3).strip()

        if author in ["—", "-", "--", "——", "- ", "— "]:
            author = "———"

        # Check if article title in quotes: "Title." Journal, vol: pages.
        m_art = re.match(r'^[\"“\']([^\"”\']+)[\"”\'][\.\,\s]*(.*)', rest)
        if m_art:
            art_title = m_art.group(1).strip().rstrip(".")
            journal_part = m_art.group(2).strip()

            m_jour = re.match(r"^([A-Za-z\s\.\,\'\&\:\-]+?)[\,\s]+(\d+.*)", journal_part)
            if m_jour:
                j_name = m_jour.group(1).strip().rstrip(",")
                j_vol = m_jour.group(2).strip()
                rest_fmt = f'"{art_title}." _{j_name}_, {j_vol}'
            else:
                rest_fmt = f'"{art_title}." _{journal_part}_'
        else:
            parts = rest.split(". ", 1)
            if len(parts) == 2:
                b_title = parts[0].strip().rstrip(".")
                pub = parts[1].strip()
                rest_fmt = f"_{b_title}_. {pub}"
            else:
                rest_fmt = f"_{rest}_"

        # Normalize en-dashes in page numbers
        rest_fmt = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1–\2", rest_fmt)

        # Escape Typst special characters
        author = author.replace("@", "\\@").replace("[", "\\[").replace("]", "\\]")
        rest_fmt = rest_fmt.replace("@", "\\@").replace("[", "\\[").replace("]", "\\]")

        return f"*{author} ({year}).* {rest_fmt}"

    def format_typst(self) -> str:
        citations, ack = self.parse()
        out = [
            "== 参考文献\n",
            "// --- Highest Publisher Standard Bibliography (Chicago Author-Date / Oxford OUP) ---",
            "#set par(hanging-indent: 2.4em, first-line-indent: 0pt, leading: 0.95em, spacing: 1.15em, justify: true)",
            '#set text(font: ("Charter", "Libertinus Serif", "Songti SC"), size: 9pt)',
            ""
        ]

        for c in citations:
            fmt_c = self.format_author_date_entry(c)
            out.append(f"{fmt_c}\n")

        # Acknowledgement box
        out.append("\n#v(2.5em)")
        out.append("#align(center)[")
        out.append('  #box(width: 90%, stroke: 0.5pt + rgb("#cbd5e1"), inset: 1.2em, radius: 4pt, fill: rgb("#f8fafc"))[')
        out.append(f'    #text(8.5pt, fill: rgb("#475569"), font: "Songti SC")[特别鸣谢：{ack}]')
        out.append("  ]")
        out.append("]\n")

        return "\n".join(out)

    def format_markdown(self) -> str:
        citations, ack = self.parse()
        out = ["\n# 参考文献\n"]
        for c in citations:
            fmt_c = self.format_author_date_entry(c)
            # Remove Typst formatting for markdown
            out.append(f"\n{fmt_c}\n")
        out.append(f"\n> **特别鸣谢**：{ack}\n")
        return "\n".join(out)
