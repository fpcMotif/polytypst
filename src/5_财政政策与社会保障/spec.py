import re
from dataclasses import replace
from pathlib import Path

from ..compiler.monograph import ChapterSpec, FigureLayout, MonographSpec

FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"

FIGURE_LAYOUT = FigureLayout(
    caption_pattern=(
        r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?图\s*(?P<chapter>\d+)[\.\-]"
        r"(?P<number>\d+[A-Za-z]?)\.?(?:\s*[：:]?\s*(?P<title>.+?))?(?:\*\*)?\s*$"
    ),
    caption_format="图 {chapter}-{number}",
    pair_figures=False,
    svg_single_pct=100,
    png_single_divisor=2900,
    png_single_range=(55, 92),
    png_max_height_ratio=0.9,
    png_min_pct_tall=50,
)

CHAPTERS = [
    ChapterSpec(0, "作者简介", 4, 5),
    ChapterSpec(0, "中文版前言", 6, 7),
    ChapterSpec(0, "中文版序言", 8, 15),
    ChapterSpec(0, "序 财政政策与社会保障", 16, 27),
    ChapterSpec(1, "财政可持续性和财政管理评估", 32, 60),
    ChapterSpec(2, "20世纪90年代公共投资政策评估", 61, 87),
    ChapterSpec(3, "日本发生非凯恩斯效应的可能性", 88, 125),
    ChapterSpec(4, "1996年至1998年财政政策的施行对经济和物价走势的影响", 126, 155),
    ChapterSpec(5, "利用制度信息计算财政乘数", 156, 181),
    ChapterSpec(6, "20世纪80年代后的养老金改革与社会保障资产", 182, 206),
    ChapterSpec(7, "医疗保险制度的推进及其对日本经济的影响", 207, 245),
    ChapterSpec(8, "20世纪90年代代际再分配政策的变迁", 246, 264),
    ChapterSpec(9, "税收制度", 265, 309),
    ChapterSpec(10, "资产税收制度与“泡沫”", 310, 343),
    ChapterSpec(11, "对所得征税中税收弹性系数的分析", 344, 368),
    ChapterSpec(12, "泡沫和通货紧缩时期的地方财政", 369, 388),
    ChapterSpec(13, "各级政府间财政软预算约束", 389, 417),
    ChapterSpec(14, "日本财政投融资", 418, 454),
    ChapterSpec(0, "后记", 455, 455),
]

_CHAPTER_TITLES = "|".join(
    r"\s*".join(re.escape(ch) for ch in c.title if not ch.isspace()) for c in CHAPTERS if c.number
)
RUNNING_HEADER_REGEXES = (
    r"^(?:#+\s*|=+\s*)?\d{1,3}\s+财政政策与社会保障.*$",
    r"^(?:#+\s*|=+\s*)?(?:序\s+)?财政政策与社会保障\s+\d{1,3}.*$",
    r"^(?:#+\s*|=+\s*)?目录(?:\s+\d{1,3})?$",
    rf"^(?:#+\s*)?(?:\d{{1,2}}\s*)?(?:{_CHAPTER_TITLES})\s*\d{{1,3}}$",
)

FISCAL_POLICY_SPEC = MonographSpec(
    slug="5",
    title="5 财政政策与社会保障",
    author="（日本）内阁府经济社会综合研究所",
    publisher="中国金融出版社",
    year=2022,
    lang="zh",
    domain="economics",
    publisher_key="cambridge",
    source_pdf="5 财政政策与社会保障.pdf",
    pdf_name_markers=("财政政策与社会保障",),
    pdf_page_count=455,
    ocr_languages=("zh-Hans", "en-US"),
    chapters=CHAPTERS,
    running_header_regexes=RUNNING_HEADER_REGEXES,
    header_zone_lines=4,
    heading_rewrites=((r"^(#{2,3}\s+\d{1,2})\s+(?=\d)", "\\1 ⁠"),),
    figure_dir="figures",
    figures=FIGURE_LAYOUT,
    footnote_style="",
    footnote_numbering="1",
    footnote_reset="page",
    book_aliases=True,
    cross_references=True,
    chapter_heading="{title}",
)

FISCAL_POLICY_ILLUSTRATED_SPEC = replace(
    FISCAL_POLICY_SPEC,
    slug="5_illustrated",
    book_aliases=False,
)
