import re
import tomllib
from pathlib import Path

from polytypst.edition import OUTPUT

from .figures import crop_cross_page_figures

OUT_DIR = OUTPUT / "6_劳动力市场与收入分配"
RUNNING_HEADER_REGEXES = tuple(
    tomllib.loads((Path(__file__).parent / "book.toml").read_text(encoding="utf-8"))["running_header_regexes"]
)

CHAPTER_TITLES = r"(?:劳动分配率与工资的?下降|工资调整和雇佣调整与菲利普斯曲线[的]?变化|结构性失业与错配|20\s*世纪\s*90\s*年代后半期至\s*21\s*世纪前\s*5\s*年就业严峻化[的]?实证分析|20\s*世纪\s*80\s*年代后日本[的]?劳动时间|工会与雇佣调整|工龄工资、成果主义与工资结构|收入差距|泡沫经济以后的学校教育和教育政策|工资差距|泡沫经济以后性别工资差距的实际情况及其研究动向|工资与就业的?地区间差距|非正规雇佣增加[的]?背景及其政策措施|女性就业与少子化|年轻人就业问题和代际效应|日本老年人就业率居高不下以及变化[的]?主要原因|职业培训)"
# A chapter-title line without a page number is the chapter's own title only when its number is the chapter's.
CHAPTER_TITLE_RE = re.compile(rf"^#*\s*(?P<chapter>\d{{1,2}})\s+{CHAPTER_TITLES}[①-⑩]?$")

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


def prepare(source: Path | None) -> None:
    crop_cross_page_figures(OUT_DIR, source)
