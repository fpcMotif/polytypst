"""Felix Klein: Development of Mathematics in the 19th Century, Vol 2 (Chinese Translation)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"数学在19世纪的发展|线性不变量理论|狭义相对论|解析点变换群|"
    r"埃尔朗根纲领|单复变量函数|几何学基础|附录|编者前言|目录|引言|"
    r"人名索引|专业名词索引|译后记|DEVELOPMENT OF MATHEMATICS"
)

KLEIN_ZH_OCR_PROMPT = (
    "将此文档页面转录为精确、高保真的 Markdown 格式（符合 LaTeX 语法标准）。\n"
    "规则：\n"
    "1. 所有数学表达式、变量、公式均使用精确的 LaTeX 语法：行内公式用 $...$，独立公式用 $$...$$。\n"
    "2. 忠实保留所有中文字符、数学专业术语（如不变量、逆步、同步、李代数、黎曼度量等）及全角标点符号。\n"
    "3. 文档标题、章节、节标题用 Markdown (#, ##, ###) 清晰分级（如 # 第一章，## A 一般线性不变量理论，### §1 线性代换）。\n"
    "4. 定理、引理、定义、命题、证明等数学环境加粗（如 **定理 1.**, **定义 1.1.**, **证明.**, **注.**）。\n"
    "5. 独立公式如有编号请准确保留（如 (1), (2), (1.1)）。\n"
    "6. 完整保留正文、脚注及作者注释，不得遗漏任何内容。"
)

KLEIN_ZH_SPEC = MonographSpec(
    slug="klein_development_vol2_zh",
    title="数学在19世纪的发展（第二卷）",
    author="F. 克莱因",
    translator="李培廉",
    editor="丘成桐",
    publisher="高等教育出版社",
    series="数学翻译丛书",
    year=2010,
    publisher_key="cambridge",
    lang="zh",
    pdf_page_count=330,
    pdf_name_markers=("数学在19世纪的发展", "第二卷"),
    preface_page=5,
    ocr_prompt=KLEIN_ZH_OCR_PROMPT,
    chapters=[
        ChapterSpec(0, "引言", 11, 12),
        ChapterSpec(1, "第一章 线性不变量理论的基本概念初步", 13, 58),
        ChapterSpec(2, "第二章 力学与数学物理中的狭义相对论", 59, 134),
        ChapterSpec(3, "第三章 以二次微分形式为基础的解析点变换群", 135, 196),
        ChapterSpec(4, "附录 I 对新近以来几何学研究的比较考察（埃尔朗根纲领）", 197, 224),
        ChapterSpec(5, "附录 II 单复变量函数一般理论基础（黎曼）", 225, 270),
        ChapterSpec(6, "附录 III 黎曼关于几何学基础的假设", 271, 303),
        ChapterSpec(7, "人名索引", 304, 308),
        ChapterSpec(8, "专业名词索引 (Stichwortverzeichnis)", 309, 314),
        ChapterSpec(9, "译后记", 315, 330),
    ],
    sections={
        "1.1": (13, "线性代换、不变量的概念"),
        "2.1": (59, "经典天体力学与 Galilei-Newton 群的相对论"),
        "3.1": (135, "经典力学的一般 Lagrange 方程"),
    },
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?图\s*(?P<chapter>\d+)[\.\-](?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_format="图 {chapter}.{number}",
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    drop_line_regexes=(
        r"^高等教育出版社.*$",
        r"^数学翻译丛书.*$",
        r"^丘成桐主编.*$",
        r"^PDG\b.*$",
        r"^\d+\s*■\s*[^\n]+$",
        r"^■\s*[^\n]+\s*\d*$",
    ),
    pre_math_rewrites=(
        (r"\bUrvariabie\b", "Urvariable"),
        (r"\bkontragredicnt\b", "kontragredient"),
    ),
)
