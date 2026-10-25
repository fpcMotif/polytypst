"""Г.М. 菲赫金哥尔茨: 微积分学教程（第一卷）."""

import re
from dataclasses import replace

from ..compiler.monograph import ChapterSpec, FigureLayout, MonographSpec

_ARTICLE_TITLE_LEN: tuple[int, ...] = (
    2, 6, 9, 9, 6, 6, 5, 4, 10, 7, 4, 7, 5, 7, 5, 2, 3, 13, 10, 2, 5, 6, 7, 4, 2, 15,
    4, 10, 8, 7, 3, 7, 16, 9, 2, 2, 8, 8, 4, 9, 32, 7, 8, 10, 7, 8, 5, 8, 6, 5, 7, 8,
    9, 2, 7, 2, 7, 12, 10, 6, 6, 5, 5, 3, 6, 13, 9, 7, 9, 7, 11, 8, 7, 8, 17, 14, 15,
    4, 2, 10, 6, 4, 6, 11, 10, 7, 4, 5, 8, 8, 10, 5, 6, 6, 7, 8, 10, 7, 2, 4, 4, 7,
    5, 13, 11, 8, 10, 9, 4, 12, 4, 6, 5, 4, 7, 10, 6, 2, 4, 13, 6, 4, 8, 15, 2, 7, 4,
    15, 9, 14, 8, 8, 6, 11, 8, 2, 4, 7, 10, 3, 8, 10, 7, 9, 2, 5, 7, 11, 2, 10, 18, 7,
    2, 7, 7, 5, 3, 5, 11, 9, 6, 10, 10, 4, 7, 9, 2, 4, 11, 7, 16, 12, 8, 5, 5, 8, 7,
    6, 3, 9, 7, 2, 6, 8, 10, 10, 4, 4, 4, 9, 7, 9, 4, 7, 4, 11, 11, 8, 8, 12, 4, 12,
    7, 12, 8, 6, 7, 6, 8, 2, 4, 9, 9, 6, 9, 7, 4, 2, 10, 5, 7, 2, 9, 2, 8, 10, 8, 6,
    2, 14, 2, 9, 2, 12, 2, 8, 12, 6, 2, 3, 7, 12, 4, 9, 2, 5, 10, 12, 12, 5, 8, 2, 7,
    16, 10, 6, 7, 9, 4, 9, 7, 2,
)
_CHAPTER_ARTICLE_RANGES: dict[int, tuple[int, int]] = {
    0: (1, 21),
    1: (22, 42),
    2: (43, 89),
    3: (90, 130),
    4: (131, 158),
    5: (159, 201),
    6: (202, 222),
    7: (223, 256),
    8: (257, 262),
}


def _split_article_line(rest: str, target_alnum: int) -> tuple[str, str]:
    s = rest.strip()
    if s.startswith("**") and "**" in s[2:]:
        idx = s.index("**", 2)
        title = s[2:idx].strip().rstrip(".")
        tail = s[idx + 2 :].strip()
    else:
        s = re.sub(r"^\*\*|\*\*$", "", s).strip()
        pos = 0
        matched_alnum = 0
        while pos < len(s) and matched_alnum < target_alnum:
            if s[pos].isalnum():
                matched_alnum += 1
            pos += 1
        while pos < len(s) and s[pos] in ")$）":
            pos += 1
        title = s[:pos].strip().rstrip(".")
        tail = s[pos:].strip()
    m_fn = re.match(r"^(\$\^\{\d+\)\}\$|\^\{\d+\)\}|[①-⑳])\s*(.*)$", tail)
    if m_fn:
        title = f"{title}{m_fn.group(1)}"
        tail = m_fn.group(2).strip()
    return title, tail


def _fichtenholz_heading(lt: str, chapter: int) -> str | None:
    if re.match(r"^(?:#+\s*)?(?:绪论\s*实数|第[一二三四五六七]章\s*\S+|附录\s*函数扩充的问题|索引|校订后记)$", lt):
        return ""
    if m_sec := re.match(r"^(?:#+\s*)?(?:\*\*)?§\s*(\d+)\.?\s*(.+?)(?:\*\*)?$", lt):
        return f"## § {m_sec.group(1)}. {m_sec.group(2).strip()}"
    if chapter in _CHAPTER_ARTICLE_RANGES and (
        m_art := re.match(r"^(?:#{2,4}\s*)?(?:\*\*)?(\d{1,3})\.(?:\*\*)?\s*(.+)$", lt)
    ):
        n = int(m_art.group(1))
        lo, hi = _CHAPTER_ARTICLE_RANGES[chapter]
        if lo <= n <= hi:
            title, tail = _split_article_line(m_art.group(2), _ARTICLE_TITLE_LEN[n - 1])
            return f"### {n}. {title}\n\n{tail}" if tail else f"### {n}. {title}"
    return None


FICHTENHOLZ_VOL1_SPEC = MonographSpec(
    slug="fichtenholz_vol1",
    title="微积分学教程（第一卷）",
    author="Г.М. 菲赫金哥尔茨",
    publisher="高等教育出版社",
    publisher_key="cambridge",
    lang="zh",
    domain="math",
    ocr_languages=("zh-Hans", "en-US"),
    source_pdf="微积分学教程.第一卷 (Г.М.菲赫金哥尔茨).pdf",
    pdf_page_count=537,
    preface_page=3,
    index_pages=(530, 535),
    cross_references=True,
    require_vector_figures=True,
    footnote_style="circled",
    footnote_numbering="circled",
    heading_hook=_fichtenholz_heading,
    figures=FigureLayout(
        caption_pattern=r"^(?:!\[.*?\]\(.*?\)\s*)?(?:\*\*)?图\s*(?P<number>\d+[a-z]?)\.?(?:\*\*)?(?:\s+(?P<tail>.*))?\s*$",
        caption_format="图 {number}",
        supplement_none=False,
    ),
    chapters=[
        ChapterSpec(0, "实数", 12, 38, label="绪论"),
        ChapterSpec(1, "极限论", 39, 84, label="第一章"),
        ChapterSpec(2, "一元函数", 85, 162, label="第二章"),
        ChapterSpec(3, "导数及微分", 163, 236, label="第三章"),
        ChapterSpec(4, "利用导数研究函数", 237, 300, label="第四章"),
        ChapterSpec(5, "多元函数", 301, 390, label="第五章"),
        ChapterSpec(6, "函数行列式及其应用", 391, 446, label="第六章"),
        ChapterSpec(7, "微分学在几何上的应用", 447, 518, label="第七章"),
        ChapterSpec(8, "函数扩充的问题", 519, 529, label="附录"),
        ChapterSpec(9, "索引", 530, 535),
        ChapterSpec(10, "校订后记", 536, 537),
    ],
    latex_preamble=r"""
\usepackage{amsmath,amssymb}
\usepackage{xeCJK}
\setmainfont{Times New Roman}
\setCJKmainfont{Songti SC}
\providecommand{\tg}{\tan}
\providecommand{\ctg}{\cot}
\providecommand{\arctg}{\arctan}
\providecommand{\arcctg}{\operatorname{arcctg}}
\providecommand{\arectg}{\operatorname{arcctg}}
\providecommand{\arccotg}{\operatorname{arccot}}
\providecommand{\arsec}{\operatorname{arcsec}}
\providecommand{\arccsc}{\operatorname{arccsc}}
\providecommand{\sh}{\sinh}
\providecommand{\ch}{\cosh}
\providecommand{\th}{\tanh}
\providecommand{\cth}{\coth}
\providecommand{\Arcsin}{\operatorname{Arcsin}}
\providecommand{\Arctg}{\operatorname{Arctg}}
\providecommand{\varliminf}{\liminf}
\providecommand{\varlimsup}{\limsup}
\providecommand{\sbt}{\operatorname{sbt}}
\providecommand{\sbn}{\operatorname{sbn}}
""")

FICHTENHOLZ_VOL1_ILLUSTRATED_SPEC = replace(
    FICHTENHOLZ_VOL1_SPEC,
    slug="fichtenholz_vol1_illustrated",
    title="微积分学教程（第一卷，彩色插图版）",
    figure_dir="figures_color",
)
