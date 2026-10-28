"""Г.М. 菲赫金哥尔茨: 微积分学教程（第三卷） / Modern Geometry Vol 3."""

from ..compiler.monograph import ChapterSpec, MonographSpec

MODERN_GEOMETRY_VOL3_SPEC = MonographSpec(
    slug="modern_geometry_vol3",
    title="微积分学教程（第三卷）",
    author="Г.М. 菲赫金哥尔茨",
    publisher="高等教育出版社",
    publisher_key="cambridge",
    lang="zh",
    domain="math",
    source_pdf="微积分学教程（第3卷） (Г.М.菲赫金哥尔茨).pdf",
    pdf_page_count=559,
    preface_page=3,
    index_pages=(550, 555),
    index_title="索引",
    figure_pages=frozenset({211, 247, 266, 327, 381, 389, 398, 438, 443, 457, 459, 460, 549, 601, 609}),
    chapters=[
        ChapterSpec(15, "第十五章 曲线积分•斯蒂尔切斯积分", 12, 103),
        ChapterSpec(16, "第十六章 二重积分", 104, 203),
        ChapterSpec(17, "第十七章 曲面面积・曲面积分", 204, 260),
        ChapterSpec(18, "第十八章 三重积分及多重积分", 261, 351),
        ChapterSpec(19, "第十九章 傅里叶级数", 352, 484),
        ChapterSpec(20, "第二十章 傅里叶级数（续）", 485, 532),
        ChapterSpec(21, "附录 极限的一般观点", 533, 549),
        ChapterSpec(22, "校订后记", 556, 558),
    ],
    latex_preamble=r"""
\usepackage{amsmath,amssymb}
\usepackage{xeCJK}
\setmainfont{Times New Roman}
\setCJKmainfont{Songti SC}
\xeCJKDeclareCharClass{CJK}{"2460->"2473, "2070->"209F, "24D0->"24E9}
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
""",
)
