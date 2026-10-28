"""A. I. Kostrikin: Introduction to Algebra, Vol 2: Linear Algebra (Chinese Translation)."""

from dataclasses import replace

from polytypst.compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"空间与形式|线性算子|带有纯量乘积的向量空间|仿射空间与欧几里得点空间|"
    r"二次曲面|张量|附录|习题解答与提示|教法说明|索引|前言|目录|序言"
)

ALGEBRA2_OCR_PROMPT = (
    "将此文档页面转录为精确、高保真的 Markdown 格式（符合 LaTeX 语法标准）。\n"
    "规则：\n"
    "1. 所有数学表达式、变量、公式均使用精确的 LaTeX 语法：行内公式用 $...$，独立公式用 $$...$$。\n"
    "2. 忠实保留所有中文字符、数学专业术语（如向量空间、基底、特征值、特征向量、对偶空间、若尔当标准型、二次型、张量积等）及标点符号。\n"
    "3. 文档标题、章节、节标题用 Markdown (#, ##, ###) 清晰分级。\n"
    "4. 定理、引理、定义、命题、证明等数学环境加粗（如 **定理 1.**, **定义 1.1.**, **证明.**, **注.**）。\n"
    "5. 独立公式如有编号请准确保留（如 (1), (2), (1.1)）。\n"
    "6. 完整保留正文、脚注及作者注释，不得遗漏任何内容。"
)

ALGEBRA2_SPEC = MonographSpec(
    domain="math",
    slug="algebra2",
    title="代数学引论 (第2卷) 线性代数",
    author="A. И. 柯斯特利金",
    translator="牛凤文",
    publisher="高等教育出版社",
    series="俄罗斯数学教材选译",
    year=2006,
    publisher_key="cambridge",
    lang="zh",
    pdf_page_count=341,
    pdf_name_markers=("代数学引论", "第二卷", "线性代数", "柯斯特利金"),
    source_pdf="代数学引论（第二卷） 线性代数（第3版） (A.И.柯斯特利金) .pdf",
    preface_page=5,
    cross_references=True,
    ocr_prompt=ALGEBRA2_OCR_PROMPT,
    chapters=[
        ChapterSpec(0, "参考文献", 6, 7),
        ChapterSpec(1, "第1章 空间与形式", 17, 59),
        ChapterSpec(2, "第2章 线性算子", 60, 99),
        ChapterSpec(3, "第3章 带有纯量乘积的向量空间", 100, 162),
        ChapterSpec(4, "第4章 仿射空间与欧几里得点空间", 163, 202),
        ChapterSpec(5, "第5章 二次曲面", 203, 241),
        ChapterSpec(6, "第6章 张量", 242, 276),
        ChapterSpec(7, "第7章 附录", 277, 317),
        ChapterSpec(8, "习题解答与提示", 318, 332),
        ChapterSpec(9, "教法说明", 333, 335),
        ChapterSpec(10, "名词索引", 336, 341),
    ],
    latex_preamble=r"""
\usepackage{graphicx}
\setmainfont{Songti SC}
\XeTeXlinebreaklocale "zh"
\XeTeXlinebreakskip = 0pt plus 1pt
\providecommand{\tg}{\tan}
\providecommand{\ctg}{\cot}
\providecommand{\arctg}{\arctan}
\providecommand{\arcctg}{\operatorname{arcctg}}
\providecommand{\sh}{\sinh}
\providecommand{\ch}{\cosh}
\providecommand{\th}{\tanh}
\providecommand{\cth}{\coth}
""",
    figures=FigureLayout(caption_format="图 {number}"),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    skip_page_markers=("Anna's Archive", "DuXiu", "filename_decoded"),
    drop_line_regexes=(r"^#+\s*(?:习题解答与提示|教法说明|名词索引|索引)\s*$",),
    ocr_languages=("zh-Hans", "en-US"),
)

ALGEBRA2_ILLUSTRATED_SPEC = replace(
    ALGEBRA2_SPEC,
    slug="algebra2_illustrated",
    title="代数学引论 (第2卷) 线性代数 (彩色插图版)",
    figure_dir="figures_color",
)
