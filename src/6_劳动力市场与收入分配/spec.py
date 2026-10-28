"""劳动力市场与收入分配 (日本内阁府经济社会综合研究所): monograph spec."""

from dataclasses import replace
from pathlib import Path
import re

from ..compiler.monograph import ChapterSpec, FigureLayout, MonographCompiler, MonographSpec

FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"

# The scan numbers sections "2" and subsections "2.1" with no period or §. Its running heads carry
# the book title on even pages and the numbered chapter title on odd pages.
SCAN_NUMBER_STYLE = """
#show heading.where(level: 2): set heading(numbering: (..n) => str(n.pos().at(1)) + "\\u{2002}")
#show heading.where(level: 3): set heading(numbering: (..n) => n.pos().slice(1).map(str).join(".") + "\\u{2002}")
#set page(header: context {
  let page-number = counter(page).get().first()
  let on-chapter-page = query(heading.where(level: 1)).any(h => h.location().page() == page-number)
  if page-number > 4 and not on-chapter-page {
    let chaps = query(heading.where(level: 1).before(here()))
    let title = if calc.odd(page-number) and chaps != () [#chaps.last().body] else [劳动力市场与收入分配]
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

FIGURE_LAYOUT = FigureLayout(
    caption_pattern=(
        r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?图\s*(?P<chapter>\d+)[\.\-]"
        r"(?P<number>\d+(?:\.\d+)?[A-Za-z]?)\.?(?:\s*[：:]?\s*(?P<title>.+?))?(?:\*\*)?\s*$"
    ),
    caption_format="图 {chapter}-{number}",
    # Crops are 600 dpi; the scan's text block is 2966 px wide, so a figure keeps its scan share of the line.
    png_single_divisor=2966,
    png_single_range=(45, 100),
    png_max_height_ratio=1.35,
    png_min_pct_tall=45,
    svg_single_pct=100,
    pair_figures=False,
)

CHAPTER_TITLES = r"(?:劳动分配率与工资的?下降|工资调整和雇佣调整与菲利普斯曲线[的]?变化|结构性失业与错配|20\s*世纪\s*90\s*年代后半期至\s*21\s*世纪前\s*5\s*年就业严峻化[的]?实证分析|20\s*世纪\s*80\s*年代后日本[的]?劳动时间|工会与雇佣调整|工龄工资、成果主义与工资结构|收入差距|泡沫经济以后的学校教育和教育政策|工资差距|泡沫经济以后性别工资差距的实际情况及其研究动向|工资与就业的?地区间差距|非正规雇佣增加[的]?背景及其政策措施|女性就业与少子化|年轻人就业问题和代际效应|日本老年人就业率居高不下以及变化[的]?主要原因|职业培训)"

# A chapter-title line without a page number is the chapter's own title only when its number is the chapter's.
CHAPTER_TITLE_RE = re.compile(rf"^#*\s*(?P<chapter>\d{{1,2}})\s+{CHAPTER_TITLES}[①-⑩]?$")

RUNNING_HEADER_REGEXES = (
    r"^(?:#+\s*|=+\s*)?\d{1,3}\s+劳动力市场与收入分配.*$",
    r"^(?:#+\s*|=+\s*)?劳动力市场与收入分配\s+\d{1,3}.*$",
    rf"^(?:#+\s*|=+\s*)?\d{{1,2}}\s+{CHAPTER_TITLES}\s+\d{{1,3}}$",
    rf"^(?:#+\s*|=+\s*)?{CHAPTER_TITLES}\s+\d{{1,3}}$",
    r"^(?:#+\s*|=+\s*)?序\s+劳动力市场与收入分配(?:\s+\d{1,3})?$",
    r"^(?:#+\s*|=+\s*)?中文版序言(?:\s+\d{1,3})?$",
    r"^(?:#+\s*|=+\s*)?中文版前言(?:\s+\d{1,3})?$",
    r"^(?:#+\s*|=+\s*)?作者简介(?:\s+\d{1,3})?$",
    r"^(?:#+\s*|=+\s*)?目录(?:\s+\d{1,3})?$",
)

FALSE_HEADINGS = (
    r"^(?:#+\s*)?2\s+NIES$",
    r"^(?:#+\s*)?分析研发费用的决定因素时.*$",
)

def labor_heading_hook(lt: str, _chapter: int) -> str | None:
    if _chapter == 0:
        return None
    # 1. Filter out running headers
    for rx in RUNNING_HEADER_REGEXES:
        if re.match(rx, lt, re.IGNORECASE):
            return ""
    # A number above the last chapter is the running head's folio, such as "89 结构性失业与错配".
    if (m_title := CHAPTER_TITLE_RE.match(lt)) and int(m_title["chapter"]) in (_chapter, *range(18, 100)):
        return ""
    # 2. Filter out false headings
    for rx in FALSE_HEADINGS:
        if re.match(rx, lt):
            return re.sub(r"^#+\s*", "", lt)
    # 3. Canonical section headings
    if m_sub := re.match(r"^#+\s*(\d{1,2}\.\d{1,2})\s+(\S.*)$", lt):
        return f"### {m_sub.group(1)} {m_sub.group(2).strip()}"
    if m_sec := re.match(r"^#+\s*(\d{1,2})\s+(\S.*)$", lt):
        # The shared section rule needs a non-digit after the number; a word joiner gives
        # "3 1990年以后的劳动分配率" one without printing anything.
        title = m_sec.group(2).strip()
        return f"## {m_sec.group(1)} {'⁠' if title[0].isdigit() else ''}{title}"
    return None

PANEL_LABELS_2_1 = (r"(?m)^（[1-6]）(?:日本|美国|加拿大|英国|法国|意大利)\n*", "")

CHAPTERS = [
    ChapterSpec(0, "作者简介", 4, 5),
    ChapterSpec(0, "中文版前言", 6, 7),
    ChapterSpec(0, "中文版序言", 8, 15),
    ChapterSpec(0, "序 劳动力市场与收入分配", 16, 22),
    ChapterSpec(1, "劳动分配率与工资的下降", 30, 66),
    ChapterSpec(2, "工资调整和雇佣调整与菲利普斯曲线的变化", 67, 95),
    ChapterSpec(3, "结构性失业与错配", 96, 148),
    ChapterSpec(4, "20世纪90年代后半期至21世纪前5年就业严峻化的实证分析", 149, 165),
    ChapterSpec(5, "20世纪80年代后日本的劳动时间", 166, 203),
    ChapterSpec(6, "工会与雇佣调整", 204, 228),
    ChapterSpec(7, "工龄工资、成果主义与工资结构", 229, 249),
    ChapterSpec(8, "收入差距", 250, 279),
    ChapterSpec(9, "泡沫经济以后的学校教育和教育政策", 280, 304),
    ChapterSpec(10, "工资差距", 305, 349),
    ChapterSpec(11, "泡沫经济以后性别工资差距的实际情况及其研究动向", 350, 373),
    ChapterSpec(12, "工资与就业的地区间差距", 374, 408),
    ChapterSpec(13, "非正规雇佣增加的背景及其政策措施", 409, 431),
    ChapterSpec(14, "女性就业与少子化", 432, 470),
    ChapterSpec(15, "年轻人就业问题和代际效应", 471, 491),
    ChapterSpec(16, "日本老年人就业率居高不下以及变化的主要原因", 492, 534),
    ChapterSpec(17, "职业培训", 535, 563),
]

LABOR_SPEC = MonographSpec(
    slug="6",
    title="劳动力市场与收入分配",
    author="（日本）内阁府经济社会综合研究所",
    publisher="中国金融出版社",
    year=2022,
    lang="zh",
    domain="economics",
    publisher_key="cambridge",
    source_pdf="6 劳动力市场与收入分配.pdf",
    pdf_name_markers=("劳动力市场与收入分配",),
    pdf_page_count=563,
    ocr_languages=("zh-Hans", "en-US"),
    footnote_reset="chapter",
    chapters=CHAPTERS,
    running_header_regexes=RUNNING_HEADER_REGEXES,
    heading_hook=labor_heading_hook,
    figure_dir="figures",
    figures=FIGURE_LAYOUT,
    cross_references=True,
    page_fixups={
        76: ((r"\\quad \(2, ([56])\)\$\$", r"\\quad (2.\1)$$"),),
        # Panel titles printed inside the figure crops.
        71: (PANEL_LABELS_2_1,),
        72: (PANEL_LABELS_2_1,),
        191: ((r"\A.*?(?=注：平均工资率)", ""),),
        232: ((r"(?m)^（各学历总计，年薪，男性 / 女性，对数差）\n*", ""),),
        233: ((r"(?m)^（男性，大学/高中学历，年薪，对数差）\n*", ""),),
        234: ((r"(?m)^（男性，(?:大学|高中)学历，年薪，与25[~～]29岁的对数差）\n*", ""),),
        298: ((r"(?m)^（[12]）(?:小学|初中)图书预算措施率和语文学力的关系\n*", ""),),
        310: ((r"(?m)^（[12]）\d+[~～]\d+岁\n*", ""),),
        333: ((r"(?m)^（[12]）40岁(?:以下|及以上)年龄段与不分年龄段时的比较\n*", ""),),
        334: ((r"(?m)^（[12]）不同(?:规模企业间|学历间)工资差距.*的变化（.*）\n*", ""),),
        368: ((r"(?m)^[^\n]*1986年的(?:教育水平|连续工龄|年龄结构成)[^\n]*\n*", ""),),
        496: ((r"(?m)^[#\s]*(?:65岁及以上|55[~～]59岁)\n*", ""),),
        516: (
            (r"男性 在职年金领取者 60.*?1997 2002年\n*", ""),
            (
                r"个人劳动性收入比例：\$R = \\frac\{y_i\}\{D\}\$\s*\$\$\\frac\{S\^\{0\.5\}\}\{S\^\{0\.5\}\}\$\$",
                "个人劳动性收入比例：\n\n$$R = \\frac{y_i / D}{S^{0.5}}$$",
            ),
        ),
        386: ((r"(?m)^\([ab]\) (?:基本工资|年度工资)\n*", ""),),
        390: ((r"(?m)^\([a-d]\) (?:相对地区就业|相对地区失业率|各地区失业率|相对劳动力参与率)\n*", ""),),
        # 图 10-26, 13-4 and 13-5 start one scan page before their caption; see figures.py.
        339: ((r"\Z", "\n\n![](figures/fig_10-26-panels.png)"),),
        340: ((r"\A.*?(?=注：1\.)", ""),),
        415: ((r"(?m)^\(a\) 1990年，男性\n*", ""),),
        416: ((r"(?m)^(?:\([abc]\) (?:1990|2000|2007)年，(?:男性|女性)|[□■] \S+)\n*", ""),),
        417: ((r"(?m)^\([bc]\) 20\d\d年，女性\n*", ""),),
        # The chapter 9 title carries note ①; the chapter heading comes from CHAPTERS, so the byline keeps the call.
        280: ((r"：赤林英夫", "：赤林英夫①"),),
    },
    latex_preamble=SCAN_NUMBER_STYLE_LATEX,
)
LABOR_SPEC = replace(
    LABOR_SPEC,
    typst_front_matter=SCAN_NUMBER_STYLE + MonographCompiler(LABOR_SPEC).build_typst_title_page(),
)

LABOR_ILLUSTRATED_SPEC = replace(
    LABOR_SPEC,
    slug="6_illustrated",
    book_aliases=False,
)
