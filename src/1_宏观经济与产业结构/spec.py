"""宏观经济与产业结构 (日本内阁府经济社会综合研究所): monograph spec."""

import re
from dataclasses import replace
from pathlib import Path

from ..compiler.monograph import (
    ChapterSpec,
    FigureLayout,
    MonographCompiler,
    MonographSpec,
)

FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"

FIGURE_LAYOUT = FigureLayout(
    caption_pattern=(
        r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?图\s*(?P<chapter>\d+)[\.\-]"
        r"(?P<number>\d+[A-Za-z]?)\.?(?:\s*[：:]?\s*(?P<title>.+?))?(?:\*\*)?\s*$"
    ),
    caption_format="图 {chapter}-{number}",
    svg_single_pct=100,
    pair_figures=False,
)

# Full-width figures that are taller than wide shrink to 330pt, about 60% of the 545pt text block,
# so a figure, its caption and some text share a page.
FIGURE_STYLE = r"""
#show image: it => layout(size => {
  let limit = 330pt
  if measure(it, width: size.width).height > limit { image(it.source, height: limit) } else { it }
})
"""

RUNNING_TITLES = (
    "20世纪80年代后的GDP缺口和潜在增长率",
    "日本经济中的消费与储蓄",
    "从泡沫期到通货紧缩期家庭预防性储蓄行为的变化",
    "设备投资分析趋势与日本经济",
    "日本泡沫期以后的经济预期、经济评估和经济政策",
    "亚洲的发展与日本经济",
    "劳动力供给、劳动力需求、技术进步和经济增长",
    "关于日本企业研发资产积累和效益的实证分析",
    "服务行业的生产率",
    "生产率、资源配置和日本的增长",
    "生产率变动和20世纪90年代后的日本经济",
    "日本的均衡实际利率",
    "日本经济周期的结构性变化",
)
# The transcripts set some running heads with spaces between words, as "20 世纪 80 年代后的 GDP 缺口".
_RUNNING_TITLE = "|".join(r"\s*".join(map(re.escape, t)) for t in RUNNING_TITLES)

RUNNING_HEADER_REGEXES = (
    r"^(?:#+\s*|=+\s*)?\d{1,3}\s+宏观经济与产业结构.*$",
    r"^(?:#+\s*|=+\s*)?宏观经济与产业结构\s+\d{1,3}.*$",
    rf"^(?:#+\s*|=+\s*)?\d{{1,2}}\s+(?:{_RUNNING_TITLE})(?:\s+\d{{1,3}})?$",
    rf"^(?:#+\s*|=+\s*)?(?:{_RUNNING_TITLE})\s+\d{{1,3}}$",
    r"^(?:#+\s*|=+\s*)?目录(?:\s+\d{1,3})?$",
)

FALSE_HEADINGS = (
    r"^(?:#+\s*)?2\s+NIES$",
    r"^(?:#+\s*)?分析研发费用的决定因素时.*$",
)

FALSE_HEADINGS = (
    *FALSE_HEADINGS,
    r"^(?:#+\s*)?5-2\s+分析股价与经济的关系。$",
)

BYLINES = (
    "深尾京司",
    "日本内阁府特命主管大臣（主管经济财政政策大臣）与谢野馨",
    "北坂真一",
    "堀雅博",
    "樱井宏二郎",
    "深尾京司 金荣悫",
)
TOP_LEVEL_HEADINGS = re.compile(r"^(?:导\s*语|参考文献|附录\s|补遗)")
TABLE_TITLE = re.compile(r"^(?:附)?表\s*\d+[-.]\d+")

WORD_JOINER = "⁠"


def _join_last_cell_after(value: str) -> tuple[str, str]:
    return (rf"(?m)^(\|[^\n]*\| {value} \|)  \|$", rf"\1 {WORD_JOINER} |")


def _drop_line(text: str) -> tuple[str, str]:
    return (rf"(?m)^{re.escape(text)}[ \t]*\n?", "")


FIGURE_TEXT_FIXUPS = {
    213: ((r"\A.*\Z", ""),),
    41: (_drop_line('资本投入量（实际、潜在）估算'), _drop_line('制造业实际利用率（使用采矿业指数）'), _drop_line('制造业资本存量'), _drop_line('制造业潜在利用率（剔除经济因素）'), _drop_line('非制造业实际利用率（使用第三产业活动指数）'), _drop_line('非制造业资本存量'), _drop_line('非制造业潜在利用率（剔除经济因素）'), _drop_line('实际资本投入量'), _drop_line('潜在资本投入量'), _drop_line('柯布-道格拉斯生产函数'), _drop_line('$Y = AK^\\alpha L^{\\alpha-1}$'), _drop_line('$Y$：生产量（实际GDP）'), _drop_line('$K$：资本投入量'), _drop_line('$L$：劳动投入量'), _drop_line('$\\alpha$：资本份额（假定为0.33）'), _drop_line('A：TFP（全要素生产率）'), _drop_line('潜在GDP GDP缺口'), _drop_line('※ GDP缺口是实际GDP和潜在GDP之间的偏差率'), _drop_line('实际劳动投入量'), _drop_line('潜在劳动投入量'), _drop_line('总实际劳动时间'), _drop_line('HP滤波器'), _drop_line('潜在劳动时间'), _drop_line('就业人数'), _drop_line('潜在就业人数'), _drop_line('（15岁及以上人口×趋势劳动力参与率）'), _drop_line('×（1—结构性失业率）'), _drop_line('劳动投入量（实际、潜在）估算'),),
    44: (_drop_line('（1）制造业资本利用率'), _drop_line('（×年第一季度）'), _drop_line('（2）非制造业资本利用率'), _drop_line('（3）失业率'),),
    46: (_drop_line('（2）潜在增长率的变化'),),
    48: (_drop_line('（3）GDP缺口和有效职位空缺率'),),
    49: (_drop_line('CPI增长率（%）'), _drop_line('6.0'), _drop_line('5.0'), _drop_line('4.0'), _drop_line('3.0'), _drop_line('2.0'), _drop_line('1.0'), _drop_line('0.0'), _drop_line('-1.0'), _drop_line('-2.0'), _drop_line('GDP缺口（%，反向符号）'), _drop_line('CPI增长率1985—1995 线性（CPI增长率1985—1995）'), _drop_line('CPI增长率1996—2006 线性（CPI增长率1996—2006）'),),
    50: (_drop_line('（1）HP滤波器'),),
    53: (_drop_line('（1）截至1991年'), _drop_line('（×年第一季度）'), _drop_line('——整个时期 ——仅变更时期'), _drop_line('◇ 使用当时的GDP'), _drop_line('（2）截至1997年'),),
    56: (_drop_line('（2）奥肯定律'),),
    199: (_drop_line('美国 日本'), _drop_line('经常账户收支与GDP之比'), _drop_line('商品、服务净出口与GDP之比（名义）'), _drop_line('商品、服务净出口与GDP之比（实际）'),),
    216: (_drop_line('口农产品和食品'),),
    227: (_drop_line('（2）女性'), _drop_line('万人'), _drop_line('6000'), _drop_line('5000'), _drop_line('4000'), _drop_line('3000'), _drop_line('2000'), _drop_line('1000'),),
    228: (_drop_line('（1）男性'), _drop_line('（2）女性'),),
    234: (_drop_line('（2）劳动时间=基于《劳动力调查》'),),
    238: (_drop_line('（2）男性'), _drop_line('（3）女性'),),
    240: (_drop_line('（1）男性'), _drop_line('（2）女性'),),
    327: (_drop_line('## 机电、邮政和通信'), _drop_line('## 机电以外的制造业'), _drop_line('## 第一产业、建筑、水电燃气'), _drop_line('## 金融和对企业服务'), _drop_line('## 商业和运输'), _drop_line('## 对个人和社会服务'),),
    338: (_drop_line('日本企业在亚洲的名义产值变化（1990—2002）/国内生产（1990）（%）'),),
}


def _not_a_caption(sentence_start: str) -> tuple[str, str]:
    return (rf"(?m)^({sentence_start})", rf"{WORD_JOINER}\1")


PAGE_FIXUPS = {
    224: (_not_a_caption(r"图 7-1 显示了"),),
    361: (_not_a_caption(r"图 11-3 \(3\) 显示了"),),
}

TABLE_EMPTY_CELL_FIXUPS = {
    69: ((r"(?m)^(\| （1） \| 1\.055<br>\(61\.78\) \|)  \|  \|", rf"\1 {WORD_JOINER} | {WORD_JOINER} |"),),
    79: (_join_last_cell_after(r"80\.7"),),
    299: (_join_last_cell_after(r"0\.523"),),
    300: (_join_last_cell_after(r"0\.944"), _join_last_cell_after(r"0\.447")),
    301: (_join_last_cell_after(r"0\.046"), _join_last_cell_after(r"0\.493")),
    302: (_join_last_cell_after(r"0\.111"),),
    382: ((r"(?m)^(\|  \| 估算值 \| \$t\$ 值 \|)  \|", rf"\1 {WORD_JOINER} |"),),
}


def macro_heading_hook(lt: str, chapter: int) -> str | None:
    """Sections become `##`, subsections `###` and `####`; chapter titles, subtitles and running heads drop; bylines stay text.

    The shared cleaner drops a heading that an earlier chapter already had, which loses each
    chapter's "导 语" and "1 前言", so every heading line returns here."""
    if any(re.match(rx, lt, re.IGNORECASE) for rx in RUNNING_HEADER_REGEXES):
        return ""
    text = re.sub(r"^#+\s*", "", lt).strip()
    if any(re.match(rx, lt) for rx in FALSE_HEADINGS):
        return text
    if not lt.startswith("#"):
        return None
    if text in BYLINES or TABLE_TITLE.match(text):
        return text
    if not chapter:
        return "" if any(c.title == text for c in CHAPTERS if not c.number) else None
    title = next(c.title for c in CHAPTERS if c.number == chapter)
    if re.match(rf"^{chapter}\s+", text) and title.startswith(re.sub(r"^\d+\s+", "", text)):
        return ""
    if text.startswith("——") and title.endswith(text):
        return ""
    if text.startswith("参考文献（续）"):
        return ""
    if re.match(r"^\d+\.\d+\.\d+\s", text) or re.match(r"^[（(]\d+[）)]", text):
        return f"#### {text}"
    if re.match(r"^\d+\.\d+\s", text):
        return f"### {text}"
    if re.match(r"^\d{1,2}\s+\S", text) or TOP_LEVEL_HEADINGS.match(text):
        return f"## {text}"
    return f"### {text}"

# Scan pages 1-3 are the cover, title page and a blank, and 32-35 are the scan's contents; the edition makes its own.
CHAPTERS = [
    ChapterSpec(0, "作者简介", 4, 5),
    ChapterSpec(0, "研究会和各小组委员会等委员名单", 6, 9),
    ChapterSpec(0, "致读者", 10, 11),
    ChapterSpec(0, "写在《泡沫/通缩时期的日本经济与经济政策》出版之际", 12, 13),
    ChapterSpec(0, "“泡沫/通缩时期的日本经济与经济政策研究”", 14, 15),
    ChapterSpec(0, "中文版前言", 16, 17),
    ChapterSpec(0, "中文版序言", 18, 25),
    ChapterSpec(0, "序 宏观经济与产业结构", 26, 31),
    ChapterSpec(1, "20世纪80年代后的GDP缺口和潜在增长率", 36, 63, label="1"),
    ChapterSpec(2, "日本经济中的消费与储蓄——20世纪80年代后的概观", 64, 84, label="2"),
    ChapterSpec(3, "从泡沫期到通货紧缩期家庭预防性储蓄行为的变化", 85, 106, label="3"),
    ChapterSpec(4, "设备投资分析趋势与日本经济——投资过剩还是投资不足", 107, 142, label="4"),
    ChapterSpec(5, "日本泡沫期以后的经济预期、经济评估和经济政策——发展历程和现时评估", 143, 194, label="5"),
    ChapterSpec(6, "亚洲的发展与日本经济——外需动向、汇率和日本的国际竞争力", 195, 222, label="6"),
    ChapterSpec(7, "劳动力供给、劳动力需求、技术进步和经济增长", 223, 259, label="7"),
    ChapterSpec(8, "关于日本企业研发资产积累和效益的实证分析", 260, 290, label="8"),
    ChapterSpec(9, "服务行业的生产率", 291, 316, label="9"),
    ChapterSpec(10, "生产率、资源配置和日本的增长", 317, 347, label="10"),
    ChapterSpec(11, "生产率变动和20世纪90年代后的日本经济", 348, 368, label="11"),
    ChapterSpec(12, "日本的均衡实际利率", 369, 401, label="12"),
    ChapterSpec(13, "日本经济周期的结构性变化", 402, 423, label="13"),
    ChapterSpec(0, "后记", 424, 425),
]

# The scan numbers sections "2" and subsections "2.1" with no period or §, and its running heads
# carry the book title on even pages and the numbered chapter title on odd pages.
# Chinese typesetting also indents the first paragraph after a heading.
SCAN_NUMBER_STYLE = r"""
#set par(first-line-indent: (amount: 2em, all: true))
#show heading.where(level: 1): it => {
  v(2.4em)
  align(left)[
    #text(16pt, weight: "bold", font: ("Songti SC", "STSong", "New Computer Modern"))[#if it.numbering != none [#numbering(it.numbering, ..counter(heading).at(it.location()))#h(1em)]#it.body]
  ]
  v(0.6em)
  line(length: 100%, stroke: 0.6pt + black)
  v(1.4em)
}
#show heading.where(level: 2): set heading(numbering: (..n) => str(n.pos().at(1)) + "\u{2002}")
#show heading.where(level: 3): set heading(numbering: (..n) => n.pos().slice(1).map(str).join(".") + "\u{2002}")
#set page(header: context {
  let page-number = counter(page).get().first()
  let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
  if page-number > 4 and not on-chapter-page {
    let chaps = query(heading.where(level: 1).before(here()))
    let title = if calc.odd(page-number) and chaps != () {
      let c = chaps.last()
      if c.numbering != none [#numbering(c.numbering, ..counter(heading).at(c.location()))#h(0.8em)#c.body] else [#c.body]
    } else [宏观经济与产业结构]
    let head = text(8.5pt, font: ("Songti SC", "STSong", "New Computer Modern"))[#title]
    let folio = text(9.5pt, font: ("Songti SC", "STSong", "New Computer Modern"))[#page-number]
    if calc.odd(page-number) {
      grid(columns: (1fr, auto), align(left, head), align(right, folio))
    } else {
      grid(columns: (auto, 1fr), align(left, folio), align(right, head))
    }
    v(-0.35em)
    line(length: 100%, stroke: 0.35pt + luma(120))
  }
})
"""

SCAN_NUMBER_STYLE_LATEX = (
    r"\renewcommand\sourcesection[1]{\refstepcounter{sourcesection}\setcounter{equation}{0}"
    r"\section*{\arabic{sourcesection}\quad #1}\addcontentsline{toc}{section}{\arabic{sourcesection}\quad #1}}"
    r"\renewcommand\sourcesubsection[1]{\refstepcounter{sourcesubsection}\setcounter{equation}{0}"
    r"\subsection*{\thesourcesubsection\quad #1}}"
)

BASE_SPEC = MonographSpec(
    slug="1",
    title="宏观经济与产业结构",
    author="（日本）内阁府经济社会综合研究所",
    publisher="中国金融出版社",
    year=2022,
    lang="zh",
    domain="economics",
    publisher_key="cambridge",
    source_pdf="1 宏观经济与产业结构.pdf",
    pdf_name_markers=("宏观经济与产业结构",),
    pdf_page_count=425,
    ocr_languages=("zh-Hans", "en-US"),
    chapters=CHAPTERS,
    running_header_regexes=RUNNING_HEADER_REGEXES,
    heading_hook=macro_heading_hook,
    figure_dir="figures",
    figures=FIGURE_LAYOUT,
    cross_references=True,
    circled_items=True,
    chapter_heading="{title}",
    latex_preamble=SCAN_NUMBER_STYLE_LATEX,
    page_fixups=PAGE_FIXUPS | TABLE_EMPTY_CELL_FIXUPS | FIGURE_TEXT_FIXUPS,
    # The OCR's inline image links repeat the figures that the caption lines already place and number.
    pre_math_rewrites=((r"!\[[^\]\n]*\]\(figures/fig_[^)\n]*\)", ""),),
)

MACRO_SPEC = replace(
    BASE_SPEC,
    typst_front_matter=SCAN_NUMBER_STYLE + FIGURE_STYLE + MonographCompiler(BASE_SPEC).build_typst_title_page(),
)

ILLUSTRATED_BASE_SPEC = replace(
    BASE_SPEC,
    slug="1_illustrated",
    book_aliases=False,
)

MACRO_ILLUSTRATED_SPEC = replace(
    ILLUSTRATED_BASE_SPEC,
    typst_front_matter=SCAN_NUMBER_STYLE + FIGURE_STYLE + MonographCompiler(ILLUSTRATED_BASE_SPEC).build_typst_title_page(),
)
