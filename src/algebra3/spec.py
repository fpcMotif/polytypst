"""A. I. Kostrikin: Introduction to Algebra, Vol 3: Basic Structures (Chinese Translation)."""

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographSpec,
    running_header_regexes,
)

RUNNING_HEADERS = (
    r"群论的构造|群的结构|表示论基础|环[·\.]\s*代数[·\.]\s*模|"
    r"伽罗瓦理论初步|附录|习题的答案与提示|教学法方面的意见|"
    r"前言|目录|引言|名词索引"
)

ALGEBRA3_OCR_PROMPT = (
    "将此文档页面转录为精确、高保真的 Markdown 格式（符合 LaTeX 语法标准）。\n"
    "规则：\n"
    "1. 所有数学表达式、变量、公式均使用精确的 LaTeX 语法：行内公式用 $...$，独立公式用 $$...$$。\n"
    "2. 忠实保留所有中文字符、数学专业术语（如典型群、同构、正交群、酉群、李代数、特征标等）及标点符号。\n"
    "3. 文档标题、章节、节标题用 Markdown (#, ##, ###) 清晰分级。\n"
    "4. 定理、引理、定义、命题、证明等数学环境加粗（如 **定理 1.**, **定义 1.1.**, **证明.**, **注.**）。\n"
    "5. 独立公式如有编号请准确保留（如 (1), (2), (1.1)）。\n"
    "6. 完整保留正文、脚注及作者注释，不得遗漏任何内容。"
)

ALGEBRA3_SPEC = MonographSpec(
    domain="math",
    slug="algebra3",
    title="代数学引论 (第3卷) 基本结构",
    author="A. И. 柯斯特利金",
    translator="郭文彬",
    publisher="高等教育出版社",
    series="俄罗斯数学教材选译",
    year=2008,
    publisher_key="cambridge",
    lang="zh",
    pdf_page_count=262,
    pdf_name_markers=("代数学引论", "基本结构", "第3卷", "柯斯特利金"),
    source_pdf="代数学引论 第3卷 基本结构 第2版 (A.И.柯斯特利金著) .pdf",
    preface_page=7,
    cross_references=False,
    references_page=253,
    ocr_prompt=ALGEBRA3_OCR_PROMPT,
    chapters=[
        ChapterSpec(1, "第1章 群论的构造", 16, 50, label="第1章"),
        ChapterSpec(2, "第2章 群的结构", 51, 82, label="第2章"),
        ChapterSpec(3, "第3章 表示论基础", 83, 137, label="第3章"),
        ChapterSpec(4, "第4章 环. 代数. 模", 138, 180, label="第4章"),
        ChapterSpec(5, "第5章 伽罗瓦理论初步", 181, 232, label="第5章"),
        ChapterSpec(6, "附录 未解决的问题", 233, 237),
        ChapterSpec(7, "习题的答案与提示", 238, 246, label="习题答案"),
        ChapterSpec(8, "教学法方面的意见与补充材料", 247, 253),
        ChapterSpec(9, "名词索引", 254, 261),
    ],
    sections={
        "1.1": (16, "小维数的典型群"),
        "1.2": (25, "子群的陪集"),
        "1.3": (29, "群在集合上的作用"),
        "1.4": (36, "商群与同态"),
        "2.1": (51, "可解群与单群"),
        "2.2": (57, "西罗 (Sylow) 定理"),
        "2.3": (62, "有限生成交换群"),
        "2.4": (75, "线性李群"),
        "3.1": (83, "线性表示的定义和例子"),
        "3.2": (95, "酉性和可约性"),
        "3.3": (101, "有限旋转群"),
        "3.4": (107, "线性表示的特征标"),
        "3.5": (114, "有限群的不可约表示"),
        "3.6": (124, "群 SU(2) 和群 SO(3) 的表示"),
        "3.7": (127, "表示的张量积"),
        "4.1": (138, "环论构造"),
        "4.2": (145, "关于环的一些结果"),
        "4.3": (154, "模"),
        "4.4": (161, "域上代数"),
        "4.5": (175, "李代数 sl(2) 上的不可约模"),
        "5.1": (181, "域的有限扩张"),
        "5.2": (188, "有限域"),
        "5.3": (197, "伽罗瓦对应"),
        "5.4": (204, "伽罗瓦群的计算"),
        "5.5": (215, "伽罗瓦扩张及相近的问题"),
        "5.6": (225, "有限群中的刚性和有理性"),
        "5.7": (231, "结束语"),
    },
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?图\s*(?:(?P<chapter>\d+)[\.\-])?(?P<number>\d+[a-z]?)\.?(?:\*\*)?\s*(?P<tail>.*)$",
        caption_format="图 {number}",
    ),
    running_header_regexes=running_header_regexes(RUNNING_HEADERS),
    skip_page_markers=("Anna's Archive", "DuXiu", "filename_decoded"),
    drop_line_regexes=(r"^#+\s*(?:习题的答案与提示|教学法方面的意见|名词索引)\s*$",),
    ocr_languages=("zh-Hans", "en-US"),
)
