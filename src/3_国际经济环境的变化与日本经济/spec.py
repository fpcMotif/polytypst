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
    top_pages=frozenset({46, 192, 300, 313, 332}),
    svg_single_pct=100,
    pair_figures=False,
    png_single_divisor=2700,
    png_single_range=(60, 100),
    png_max_height_ratio=1.3,
    png_min_pct_tall=60,
)

RUNNING_HEADER_REGEXES = (
    r"^(?:#+\s*|=+\s*)?\d{1,3}\s+国际经济环境的变化与日本经济.*$",
    r"^(?:#+\s*|=+\s*)?(?:序\s+)?国际经济环境的变化与日本经济\s+\d{1,3}.*$",
    r"^(?:#+\s*|=+\s*)?\d{1,2}\s+(?:进口竞争对日本国内产业的影响|日本对内直接投资的变化与经济影响|泡沫、通缩期的日本通商政策|泡沫、通缩期的日本食品和农业问题|货币和汇率政策\s*[（(]国际金融政策[)）]\s*变化|亚洲金融危机和日本金融机构的行动|汇率和国际收支|从老龄化等结构性要因来看日本的国际收支问题|内外价格差和汇率传导|少子老龄化时代的外国劳动者问题|经济全球化对\s*20\s*世纪\s*90\s*年代劳动力市场的影响)(?:\s+\d{1,3})?$",
    r"^(?:#+\s*|=+\s*)?(?:进口竞争对日本国内产业的影响|日本对内直接投资的变化与经济影响|泡沫、通缩期的日本通商政策|泡沫、通缩期的日本食品和农业问题|货币和汇率政策\s*[（(]国际金融政策[)）]\s*变化|亚洲金融危机和日本金融机构的行动|汇率和国际收支|从老龄化等结构性要因来看日本的国际收支问题|内外价格差和汇率传导|少子老龄化时代的外国劳动者问题|经济全球化对\s*20\s*世纪\s*90\s*年代劳动力市场的影响)\s+\d{1,3}$",
    r"^(?:#+\s*|=+\s*)?目录(?:\s+\d{1,3})?$",
)

# The section rule reads `3 20世纪…` as a number and a title only when the title starts with a non-digit.
WORD_JOINER = "⁠"

HEADED_BYLINES = ("伊藤元重", "本间正义", "德丸浩", "佐佐木百合")

FALSE_HEADINGS = (
    r"^(?:#+\s*)?为了政策目标。$",
)


def intl_econ_heading_hook(lt: str, chapter: int) -> str | None:
    for rx in RUNNING_HEADER_REGEXES:
        if re.match(rx, lt, re.IGNORECASE):
            return ""
    for rx in FALSE_HEADINGS:
        if re.match(rx, lt):
            return re.sub(r"^#+\s*", "", lt)
    if re.match(r"^#+\s*(?:（日本）内阁府经济社会综合研究所|作者简介|中文版前言|中文版序言|序\s*国际经济环境的变化与日本经济)$", lt):
        return ""
    if m := re.match(rf"^#+\s*((?:——|{'|'.join(HEADED_BYLINES)}).*)$", lt):
        return m.group(1)
    if m := re.match(r"^#+\s*(\d+\s*世纪.*)$", lt):
        return "### " + re.sub(r"\s+", "", m.group(1))
    if m := re.match(r"^#+\s*(\d+)\s+(\d+世纪.*)$", lt):
        return f"### {m.group(1)} {WORD_JOINER}{m.group(2)}"
    # The cleaner keeps only the first of equal headings across the book, which drops every later `1 前言` and `导 语`.
    if m := re.match(r"^#+\s*(.+?)\s*$", lt):
        inner = m.group(1)
        if re.sub(r"^\d+\s+", "", inner) in {c.title for c in CHAPTERS}:
            return None
        return f"### {inner}" if len(inner) <= 90 else inner
    return None


CHAPTERS = [
    ChapterSpec(0, "（日本）内阁府经济社会综合研究所", 1, 1),
    ChapterSpec(0, "编译委员会", 2, 2),
    ChapterSpec(0, "作者简介", 4, 5),
    ChapterSpec(0, "中文版前言", 6, 7),
    ChapterSpec(0, "中文版序言", 8, 15),
    ChapterSpec(0, "序 国际经济环境的变化与日本经济", 16, 24),
    ChapterSpec(1, "进口竞争对日本国内产业的影响", 30, 55),
    ChapterSpec(2, "日本对内直接投资的变化与经济影响", 56, 101),
    ChapterSpec(3, "泡沫、通缩期的日本通商政策", 102, 127),
    ChapterSpec(4, "泡沫、通缩期的日本食品和农业问题", 128, 162),
    ChapterSpec(5, "货币和汇率政策（国际金融政策）变化", 163, 189),
    ChapterSpec(6, "亚洲金融危机和日本金融机构的行动", 190, 218),
    ChapterSpec(7, "汇率和国际收支", 219, 251),
    ChapterSpec(8, "从老龄化等结构性要因来看日本的国际收支问题", 252, 279),
    ChapterSpec(9, "内外价格差和汇率传导", 280, 296),
    ChapterSpec(10, "少子老龄化时代的外国劳动者问题", 297, 323),
    ChapterSpec(11, "经济全球化对20世纪90年代劳动力市场的影响", 324, 347),
]

PREFACE_CHART = "preface_exchange_rate.png"

# The compiler sets each chapter title itself, so a note on the scan's title line moves to the byline.
PAGE_FIXUPS = {
    1: ((r"\n+---.*\Z", "\n"),),
    2: ((r"\A.*?(?=日文版)", ""), (r"(葛 俊).*\Z", r"\1\n")),
    # The table writer merges trailing empty header cells into a colspan, so cells under a two-row heading get a joiner.
    132: ((r"(?m)(兼业农户 \|)  \|  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} |"),),
    171: (
        (r"(?m)^(\| constant .*\| GMPRD \|)  \|$", rf"\1 {WORD_JOINER} |"),
        (r"(?m)(\| <mark>0\.063<br>-2\.289</mark> \|)  \|  \|", rf"\1 {WORD_JOINER} | {WORD_JOINER} |"),
    ),
    175: ((r"(?m)(\| 超过 \| 低于 \|)  \|  \|  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} | {WORD_JOINER} |"),),
    247: ((r"(?m)(\| 服务收支 \|)  \|  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} |"),),
    248: ((r"(?m)(\| 资产 \| 负债 \|)  \|  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} |"),),
    255: ((r"(?m)^(\| 1955 \| 11\.9 \|)  \|  \|( 1980 \| 17\.9 \| 15\.4 \|)  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} |\2 {WORD_JOINER} |"),),
    256: ((r"(?m)^(\| 1963 \| 14\.9 \|)  \|  \|( 1988 \| 13\.0 \| 11\.9 \|)  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} |\2 {WORD_JOINER} |"),),
    285: ((r"(?m)^(\| 1990 \| 1\.03 \|)  \|  \|  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} | {WORD_JOINER} |"),),
    289: ((r"(?m)^(\| 美国（美元） \| 3\.57 \| 3\.57 \|)  \|  \|  \|$", rf"\1 {WORD_JOINER} | {WORD_JOINER} | {WORD_JOINER} |"),),
    17: ((r"（1973年3月=100）\n\n实际有效汇率的走势（1990年1月—2009年1月）",rf"![](figures/{PREFACE_CHART.removesuffix('.png')}.svg)"),),
    221: ((r"\A(?=### 2\.1 汇率的动向)", "### 2 汇率和国际收支\n\n"),),
    252: ((r"^### 8 从老龄化等结构性要因来看日本的国际收支问题(①)\n+(查尔斯 堀冈雄二 \(Charles Yuji Horioka\))", r"\2\1"),),
    324: ((r"^### 11 经济全球化对20世纪90年代劳动力市场的影响(①)\n+(神田玲子)", r"\2\1"),),
}

ITALIC_LATIN_STYLE = '#show emph: set text(font: ("Source Serif 4", "Songti SC", "STSong"))\n'

# Table 5-2 is the book's only 11-column table, and the scan rules every cell.
# Its grey shading takes a tint of the sage band on the scan's cover.
TABLE_5_2_GRID = """#show table.where(columns: (1.8fr,) + (1fr,) * 10): it => {
  set table.cell(stroke: 0.4pt + rgb("#2f3d31"), fill: white)
  let fields = it.fields()
  let cells = fields.remove("children").map(cell => {
    let cell_fields = cell.fields()
    if cell_fields.at("fill", default: none) != luma(215) { return cell }
    let body = cell_fields.remove("body")
    cell_fields.insert("fill", rgb("#d6e2d4"))
    table.cell(..cell_fields, body)
  })
  fields.insert("columns", (1.1fr,) + (1fr,) * 9 + (1.6fr,))
  table(..fields, ..cells)
}
"""

BASE_SPEC = MonographSpec(
    slug="3",
    title="国际经济环境的变化与日本经济",
    author="（日本）内阁府经济社会综合研究所",
    publisher="中国金融出版社",
    year=2022,
    lang="zh",
    domain="economics",
    publisher_key="cambridge",
    source_pdf="3 国际经济环境的变化与日本经济.pdf",
    pdf_name_markers=("国际经济环境的变化与日本经济",),
    pdf_page_count=347,
    ocr_languages=("zh-Hans", "en-US"),
    chapters=CHAPTERS,
    running_header_regexes=RUNNING_HEADER_REGEXES,
    heading_hook=intl_econ_heading_hook,
    figure_dir="figures",
    figures=FIGURE_LAYOUT,
    footnote_style="circled",
    page_fixups=PAGE_FIXUPS,
    book_aliases=True,
    cross_references=True,
)

INTL_ECON_SPEC = replace(
    BASE_SPEC,
    typst_front_matter=ITALIC_LATIN_STYLE + TABLE_5_2_GRID + MonographCompiler(BASE_SPEC).build_typst_title_page(),
)

INTL_ECON_ILLUSTRATED_SPEC = replace(
    INTL_ECON_SPEC,
    slug="3_illustrated",
    book_aliases=False,
)
