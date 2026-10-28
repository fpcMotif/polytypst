import re
import tomllib
from pathlib import Path

from polytypst.edition import OUTPUT
from polytypst.facsimile import FigureArt

from .figures import crop_macro_figures, figure_page_art, figure_page_boxes

OUT_DIR = OUTPUT / "1_宏观经济与产业结构"
_BOOK = tomllib.loads((Path(__file__).parent / "book.toml").read_text(encoding="utf-8"))
RUNNING_HEADER_REGEXES = tuple(_BOOK["running_header_regexes"])
CHAPTERS = _BOOK["chapters"]

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
        if any(c["title"] == text for c in CHAPTERS if not c["number"]):
            return ""
        return lt.strip() if lt.startswith("##") else None
    title = next(c["title"] for c in CHAPTERS if c["number"] == chapter)
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


def draw_figures(out_dir: Path) -> list[Path]:
    crop_macro_figures(out_dir)
    return sorted((out_dir / "figures").glob("fig_*.png"))


def figure_boxes() -> dict[int, list[tuple[float, float, float, float]]]:
    return figure_page_boxes(OUT_DIR)


def figure_art() -> dict[int, list[FigureArt]]:
    return figure_page_art(OUT_DIR)
