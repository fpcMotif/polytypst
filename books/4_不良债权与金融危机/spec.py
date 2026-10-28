import re
from dataclasses import replace
from pathlib import Path

from polytypst.compiler.monograph import (
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
    png_single_divisor=2880,
    png_single_range=(50, 100),
    png_max_height_ratio=1.3,
)

RUNNING_HEADER_REGEXES = (
    r"^(?:#+\s*|=+\s*)?\d{1,3}\s*不良债权与金融危机.*$",
    r"^(?:#+\s*|=+\s*)?(?:序\s+)?不良债权与金融危机\s*\d{1,3}.*$",
    r"^(?:#+\s*|=+\s*)?目录(?:\s+\d{1,3})?$",
    r"^(?:#+\s*|=+\s*)?\d{1,2}\s+(?:受地价波动影响的日本经济|受地价波动影响日本经济|土地税制与地价的波动|土地税制与地价波动|银行破产与监督行政|借款企业破产法制与银行危机|借款企业的破产法制与银行危机|银行的经营恶化和破产处理|银行经营恶化和破产处理|人寿保险公司经营恶化|人寿保险公司的经营恶化|围绕公共资金投入的政治过程|围绕公共资金投入政治过程|不良债权处理政策的过程和论点|不良债权处理政策过程和论点|经济长期萧条与货币政策、汇率及银行信贷|资产负债表的崩溃与实体经济|资产负债表崩溃与实体经济|不良债权导致的资本和产出流失|不良债权导致资本和产出流失|泡沫经济与亚洲资本流动的变化|泡沫经济与亚洲资本流动变化)\s+\d{1,3}$",
    r"^(?:#+\s*|=+\s*)?(?:受地价波动影响的日本经济|受地价波动影响日本经济|土地税制与地价的波动|土地税制与地价波动|银行破产与监督行政|借款企业破产法制与银行危机|借款企业的破产法制与银行危机|银行的经营恶化和破产处理|银行经营恶化和破产处理|人寿保险公司经营恶化|人寿保险公司的经营恶化|围绕公共资金投入的政治过程|围绕公共资金投入政治过程|不良债权处理政策的过程和论点|不良债权处理政策过程和论点|经济长期萧条与货币政策、汇率及银行信贷|资产负债表的崩溃与实体经济|资产负债表崩溃与实体经济|不良债权导致的资本和产出流失|不良债权导致资本和产出流失|泡沫经济与亚洲资本流动的变化|泡沫经济与亚洲资本流动变化)\s+\d{1,3}$",
)

CHAPTERS = [
    ChapterSpec(0, "作者简介", 4, 5),
    ChapterSpec(0, "中文版前言", 6, 7),
    ChapterSpec(0, "中文版序言", 8, 15),
    ChapterSpec(0, "序 不良债权与金融危机", 16, 21),
    ChapterSpec(1, "受地价波动影响的日本经济", 26, 51, label="1"),
    ChapterSpec(2, "土地税制与地价的波动", 52, 88, label="2"),
    ChapterSpec(3, "银行破产与监督行政", 89, 109, label="3"),
    ChapterSpec(4, "借款企业的破产法制与银行危机", 110, 146, label="4"),
    ChapterSpec(5, "银行的经营恶化和破产处理", 147, 172, label="5"),
    ChapterSpec(6, "人寿保险公司的经营恶化", 173, 196, label="6"),
    ChapterSpec(7, "围绕公共资金投入的政治过程——从住专处理到竹中计划", 197, 222, label="7"),
    ChapterSpec(8, "不良债权处理政策的过程和论点", 223, 249, label="8"),
    ChapterSpec(9, "经济长期萧条与货币政策、汇率及银行信贷", 250, 299, label="9"),
    ChapterSpec(10, "资产负债表的崩溃与实体经济——20世纪90年代后的日本经济实证分析", 300, 336, label="10"),
    ChapterSpec(11, "不良债权导致的资本和产出流失", 337, 358, label="11"),
    ChapterSpec(12, "泡沫经济与亚洲资本流动的变化", 359, 387, label="12"),
    ChapterSpec(0, "后记", 388, 388),
]

BYLINES = {
    1: "樱川昌哉 樱川幸恵",
    2: "山崎福寿",
    3: "池尾和人",
    4: "田中亘",
    5: "深尾光洋",
    6: "植村信保",
    7: "久米郁男",
    8: "西村吉正",
    9: "深尾光洋",
    10: "小川一夫",
    11: "樱川昌哉 渡边善次",
    12: "吉野直行 饭岛高雄",
}
TOP_LEVEL_HEADINGS = re.compile(r"^(?:导\s*语|参考文献|附录\s*\d|补充说明)")
TABLE_TITLE = re.compile(r"^(?:附)?表\s*\d+[-.]\d+")


def npl_heading_hook(lt: str, chapter: int) -> str | None:
    """Sections become `##`, subsections `###`; chapter titles, subtitles and running heads drop; bylines stay text.

    The shared cleaner drops a `###` heading that any earlier chapter already had, which loses each
    chapter's "导 语" and "1 前言", so every heading line returns here."""
    text = re.sub(r"^#+\s*", "", lt).strip()
    if any(re.match(rx, lt) for rx in RUNNING_HEADER_REGEXES):
        return ""
    if not chapter and any(c.title == text for c in CHAPTERS):
        return ""
    title = next((c.title for c in CHAPTERS if c.number == chapter and chapter), "")
    if chapter and re.match(rf"^{chapter}\s+", text) and title.startswith(re.sub(r"^\d+\s+|①$", "", text)):
        return ""
    if text.startswith("——") and title.endswith(text.split("（")[0]):
        return ""
    if text == BYLINES.get(chapter):
        return text
    if not lt.startswith("#") or TABLE_TITLE.match(text):
        return text if lt.startswith("#") else None
    if re.match(r"^\d+\.\d+\s", text):
        return f"### {text}"
    if re.match(r"^\d+\s+\D", text) or TOP_LEVEL_HEADINGS.match(text):
        return f"## {text}"
    return f"### {text}"


# Book 4 numbers sections "2" and subsections "2.1" with no period or §, and its running heads
# carry the book title on even pages and the numbered chapter title on odd pages.
SCAN_NUMBER_STYLE = r"""
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
    } else [不良债权与金融危机]
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
    slug="4",
    title="不良债权与金融危机",
    author="（日本）内阁府经济社会综合研究所",
    publisher="中国金融出版社",
    series="",
    year=2022,
    lang="zh",
    domain="economics",
    publisher_key="cambridge",
    source_pdf="4 不良债权与金融危机.pdf",
    pdf_name_markers=("不良债权与金融危机",),
    pdf_page_count=389,
    ocr_languages=("zh-Hans", "en-US"),
    chapters=CHAPTERS,
    running_header_regexes=RUNNING_HEADER_REGEXES,
    heading_hook=npl_heading_hook,
    heading_rewrites=(
        (
            rf"^((?:池尾和人|{'|'.join(BYLINES.values())})(?:@@FNSTART@@[^\n]*?@@FNEND@@)?)$",
            r'#align(center)[#text(11pt)[\1]]',
        ),
    ),
    page_fixups={
        # The scan's chapter-title note marks move to the byline, because the chapter heading is built from the spec.
        52: ((r"(?m)^山崎福寿$", "山崎福寿①"),),
        147: ((r"(?m)^深尾光洋$", "深尾光洋①"),),
        300: ((r"(?m)^小川一夫$", "小川一夫①"),),
        133: ((r"(?m)^(## 4 为了私下协议重整的法律规制的灵活化)\n+### (——关于债转股（DES）)$", r"\1\2"),),
        # The crop of 图 9-8 holds the regression note beside the chart.
        261: ((r"\n单因素回归分析 1991年1月.*?\n实际利率函数\n[^\n]*\n", "\n"),),
    },
    figure_dir="figures",
    figures=FIGURE_LAYOUT,
    footnote_style="",
    footnote_numbering="1",
    footnote_reset="page",
    book_aliases=True,
    cross_references=True,
    chapter_heading="{title}",
    latex_preamble=SCAN_NUMBER_STYLE_LATEX,
)

NPL_CRISIS_SPEC = replace(
    BASE_SPEC,
    typst_front_matter=SCAN_NUMBER_STYLE + MonographCompiler(BASE_SPEC).build_typst_title_page(),
)

NPL_CRISIS_ILLUSTRATED_SPEC = replace(
    NPL_CRISIS_SPEC,
    slug="4_illustrated",
    figure_dir="figures_color",
    book_aliases=False,
)
