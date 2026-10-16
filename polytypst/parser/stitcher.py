"""Production document structure, heading hierarchy, and paragraph stitcher for polytypst."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from ..ocr.base import OCRLine, OCRPage


@dataclass
class FigureBlock:
    figure_id: int
    caption: str
    image_rel_path: str
    source_page: int


@dataclass
class DocumentSection:
    title: str
    level: int  # 1 = Part/Book, 2 = Chapter, 3 = Section, 4 = Subsection
    content_blocks: List[str] = field(default_factory=list)
    figures: List[FigureBlock] = field(default_factory=list)


@dataclass
class ParsedBook:
    title: str
    subtitle: str
    author: str
    translator: str
    publisher: str
    sections: List[DocumentSection] = field(default_factory=list)
    figures: List[FigureBlock] = field(default_factory=list)


# Known section titles from Table of Contents for exact heading mapping
KNOWN_SECTIONS = [
    "战略、组织和环境", "设计问题：设定战略和组织", "战略变革与组织变革",
    "动荡环境中的战略和组织", "互补性", "非凸性与非凹性", "紧密耦合和松散耦合",
    "市场失灵的原因和本质", "公司与市场", "公司的本质", "合作和主动",
    "激励问题的原因和本质", "简单代理理论", "绩效测量选择", "代理关系中的多重任务",
    "团体绩效报酬", "操控绩效测量", "主观评估", "名声", "PARC 和激励",
    "垂直范围", "水平范围", "内部组织和绩效", "整体系统",
    "收购性增长", "在已有公司中的创新", "多任务情况下的工作设计",
    "创建现代企业：对管理和领导的挑战", "参考文献"
]

# Internal diagram labels to be strictly suppressed from body prose
DIAGRAM_LABELS = {
    "设计者", "战略", "活动", "组织", "环境", "绩效",
    "通用汽车", "丰田", "福特", "多样性", "柔性", "高", "低", "？", "高多样性",
    "选择", "X", "Y", "Z", "X'", "1X2", "Ya", "13", "时间",
    "A", "B", "峰A", "峰B",
    "市场", "边界", "市场交易", "内部供应", "合作行为", "主动行为", "R"
}

# Anchor text phrases for exact semantic figure injection
FIGURE_ANCHORS = {
    1: ["模型如图1所示", "模型如图 1 所示", "模型如图1"],
    2: ["组织设计这些特征和战略选择互相匹配", "见图2", "见图 2"],
    3: ["假设选择是一维的", "图3中进行说明", "图 3 中进行说明"],
    4: ["最初关系如图4中的实曲线所示", "最初关系如图 4 中的实曲线所示", "如图4", "如图 4"],
    5: ["可以在图5中进行说明", "可以在图 5 中进行说明", "局部最佳，可以在图5", "局部最佳，可以在图 5"],
    6: ["箭头指向“高坡”", "如图6中所示", "如图 6 中所示"],
    7: ["战略和组织变革", "图7 非凹性", "图 7 非凹性"],
    8: ["使得两种所需的行为都变多", "图8来进行说明", "图 8 来进行说明"],
    9: ["可行的了（图9）", "可行的了（图 9）", "可行的了(图9)", "可行的了(图 9)"]
}


class DocumentStitcher:
    def __init__(self, pages: List[OCRPage], figures_map: Optional[Dict[int, FigureBlock]] = None):
        self.pages = sorted(pages, key=lambda p: p.page_number)
        self.figures_map = figures_map or {}

    def is_header_or_footer(self, line: OCRLine) -> bool:
        # Running header: y > 0.88
        if line.y > 0.88:
            return True
        # Running footer / page folio: y < 0.08
        if line.y < 0.08:
            return True
        # Standalone page numbers like "— 24 —", "24", "42"
        if re.match(r"^—?\s*\d+\s*—?$", line.text.strip()):
            return True
        return False

    def is_chapter_header(self, text: str, line: OCRLine) -> Optional[Tuple[str, str]]:
        clean = text.strip().replace("／", "1")
        m = re.match(r"^第\s*([0-9一二三四五六七八九十]+)\s*章\s*(.*)", clean)
        if m and (line.h > 0.025 or line.y > 0.70):
            num = m.group(1).strip()
            title = m.group(2).strip()
            return f"第{num}章", title
        return None

    def stitch_document(self) -> ParsedBook:
        book = ParsedBook(
            title="现代企业：基于绩效与增长的组织设计",
            subtitle="The Modern Firm: Organizational Design for Performance and Growth",
            author="约翰·罗伯茨 (John Roberts)",
            translator="马志英",
            publisher="中国人民大学出版社"
        )

        current_sec = DocumentSection(title="出版说明", level=2)
        book.sections.append(current_sec)

        current_para = []
        placed_figures = set()

        for page in self.pages:
            pno = page.page_number

            # --- FRONTMATTER HANDLING ---
            # Pages 1-4: Title / CIP
            if pno <= 4:
                continue

            # Page 5: 出版说明
            if pno == 5:
                if current_para:
                    current_sec.content_blocks.append("".join(current_para))
                    current_para = []
                current_sec = DocumentSection(title="出版说明", level=2)
                book.sections.append(current_sec)

            # Pages 6-8: 前言 (Author's Preface by John Roberts)
            if pno == 6:
                if current_para:
                    current_sec.content_blocks.append("".join(current_para))
                    current_para = []
                current_sec = DocumentSection(title="前言", level=2)
                book.sections.append(current_sec)
            # Pages 9-10: Table of Contents (Skip body generation to prevent duplicate TOC pages)
            if pno in (9, 10):
                continue

            # Pages 177-192: Bibliography and backmatter (Parsed by dedicated BibliographyParser)
            if pno >= 177:
                continue

            # Body lines excluding headers and footers
            body_lines = [l for l in page.lines if not self.is_header_or_footer(l)]

            # Check if this page has figures
            page_figs = [f for f in self.figures_map.values() if f.source_page == pno]

            # Figure caption indices to skip from body text
            caption_line_indices = set()
            for idx, line in enumerate(body_lines):
                t = line.text.replace(" ", "")
                for fig in page_figs:
                    if f"图{fig.figure_id}" in t and ("图" in t[:4] or "Figure" in t[:8]):
                        caption_line_indices.add(idx)

            for idx, line in enumerate(body_lines):
                text = line.text.strip()
                if not text:
                    continue
                # Skip Page 6 vertical header characters
                if pno == 6 and text in ["言", "前", "前言", "言前"]:
                    continue

                # Format publisher signature on Page 5
                if pno == 5 and "中国人民大学出版社" in text:
                    if current_para:
                        current_sec.content_blocks.append("".join(current_para))
                        current_para = []
                    current_sec.content_blocks.append("中国人民大学出版社")
                    continue

                # 1. Skip caption line (it will be rendered with the figure)
                if idx in caption_line_indices:
                    continue
                # 2. Skip internal diagram labels on figure pages
                if page_figs:
                    clean_short = text.replace("·", "").replace("•", "").strip()
                    if clean_short in DIAGRAM_LABELS or (
                        line.w < 0.18 and len(clean_short) <= 6 and
                        any(k in clean_short for k in ["通用汽车", "丰田", "福特", "低", "高", "多样性", "柔性", "选择", "时间", "环境", "绩效", "战略", "组织", "活动"])
                    ):
                        continue

                # 3. Check chapter header
                chap_info = self.is_chapter_header(text, line)
                if chap_info:
                    if current_para:
                        current_sec.content_blocks.append("".join(current_para))
                        current_para = []
                    num, title = chap_info
                    sec_title = f"{num} {title}"
                    current_sec = DocumentSection(title=sec_title, level=2)
                    book.sections.append(current_sec)
                    continue

                # 4. Check section header
                is_sec_heading = False
                for s in KNOWN_SECTIONS:
                    if s in text and (len(text) <= len(s) + 5) and line.w < 0.50:
                        if current_para:
                            current_sec.content_blocks.append("".join(current_para))
                            current_para = []
                        current_sec = DocumentSection(title=s, level=3)
                        book.sections.append(current_sec)
                        is_sec_heading = True
                        break
                if is_sec_heading:
                    continue

                # 5. Normal body text processing
                # Check paragraph start: indentation (line.x > 0.14) following a sentence ending
                is_para_start = (line.x > 0.14) and (not current_para or current_para[-1].endswith(("。", "！", "？", "：", "”", "’", "…")))

                if is_para_start and current_para:
                    completed_para = "".join(current_para)
                    current_sec.content_blocks.append(completed_para)
                    current_para = [text]

                    # Check if this paragraph contains a figure anchor!
                    for fig_id, anchors in FIGURE_ANCHORS.items():
                        if fig_id not in placed_figures and fig_id in self.figures_map:
                            if any(a in completed_para for a in anchors):
                                fig = self.figures_map[fig_id]
                                current_sec.figures.append(fig)
                                book.figures.append(fig)
                                current_sec.content_blocks.append(f"__FIGURE_{fig_id}__")
                                placed_figures.add(fig_id)
                else:
                    if current_para:
                        prev = current_para[-1]
                        if re.search(r"[a-zA-Z0-9]$", prev) and re.match(r"^[a-zA-Z0-9]", text):
                            current_para.append(" " + text)
                        else:
                            current_para.append(text)
                    else:
                        current_para.append(text)

        # Flush final paragraph
        if current_para:
            completed_para = "".join(current_para)
            current_sec.content_blocks.append(completed_para)
            for fig_id, anchors in FIGURE_ANCHORS.items():
                if fig_id not in placed_figures and fig_id in self.figures_map:
                    if any(a in completed_para for a in anchors):
                        fig = self.figures_map[fig_id]
                        current_sec.figures.append(fig)
                        book.figures.append(fig)
                        current_sec.content_blocks.append(f"__FIGURE_{fig_id}__")
                        placed_figures.add(fig_id)

        # Fallback for any unplaced figures (ensure none are lost)
        for fig_id, fig in self.figures_map.items():
            if fig_id not in placed_figures:
                current_sec.figures.append(fig)
                book.figures.append(fig)
                current_sec.content_blocks.append(f"__FIGURE_{fig_id}__")

        # Append professionally structured Bibliography
        from .bibliography import BibliographyParser
        bib_parser = BibliographyParser(self.pages)
        citations, ack = bib_parser.parse()
        bib_sec = DocumentSection(title="参考文献", level=2)
        for c in citations:
            bib_sec.content_blocks.append(f"__CITATION__{c}")
        if ack:
            bib_sec.content_blocks.append(f"__ACK__{ack}")
        book.sections.append(bib_sec)

        return book
