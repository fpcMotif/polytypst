"""Kodaira, 複素多様体論 I・II・III (Iwanami, 1979-1981): the book's declarative monograph spec."""

from pathlib import Path

from ..compiler.monograph import ChapterSpec, MonographSpec

FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"

TYPST_FRONT_MATTER = """
#align(center + horizon)[
  #text(11pt)[岩波講座 基礎数学]
  #v(2.6em)
  #text(24pt, weight: "bold")[複素多様体論]
  #v(0.7em)
  #text(15pt)[I ・ II ・ III]
  #v(2.4em)
  #text(14pt)[小平邦彦]
  #v(5em)
  #line(length: 35%, stroke: 0.4pt + luma(140))
  #v(1.2em)
  #text(11pt)[岩波書店]
]

#pagebreak()

#outline(title: [目次], indent: 1.4em, depth: 2)

#pagebreak()
"""

LATEX_PREAMBLE = (
    "\\usepackage{xeCJK}\n"
    f"\\setCJKmainfont{{NotoSerifSC-Regular.otf}}[Path={FONTS_DIR}/]\n"
    # Proof-end squares and circles are not Latin Modern glyphs; route them to the
    # Japanese font, and map the one shape Noto Serif SC lacks to amssymb.
    '\\xeCJKDeclareCharClass{CJK}{"25A0, "25A1, "25B2, "25B3, "25BC, "25BD, '
    '"25C6, "25C7, "25CB, "25CE, "25CF, "25EF}\n'
    "\\usepackage{newunicodechar}\n"
    "\\newunicodechar{☐}{\\ensuremath{\\square}}"
)

FUKUSO_SPEC = MonographSpec(
    slug="fukuso_kodaira_complex_manifolds",
    title="複素多様体論 I・II・III",
    author="小平邦彦",
    publisher="岩波書店",
    series="岩波講座 基礎数学",
    year=1981,
    lang="ja",
    domain="math",
    chapters=[
        ChapterSpec(0, "はじめに", 5, 5),
        ChapterSpec(1, "第1章 正則関数", 7, 36),
        ChapterSpec(2, "第2章 複素多様体", 37, 90),
        ChapterSpec(3, "第3章 微分形式，ベクトル束，層", 97, 212),
        ChapterSpec(4, "第4章 無限小変形", 213, 240),
        ChapterSpec(5, "第5章 存在定理", 241, 320),
        ChapterSpec(6, "第6章 完備性の定理", 327, 364),
        ChapterSpec(7, "第7章 安定性の定理", 365, 408),
        ChapterSpec(8, "附録 多様体上の楕円型線型偏微分作用素", 409, 496),
        ChapterSpec(9, "あとがき", 497, 497),
    ],
    chapter_heading="{title}",
    running_header_regexes=(
        r"^第\s*\d+\s*章",
        r"^§",
        r"^\d{1,3}\s+第\s*\d+\s*章",
        r"^\d{1,3}\s+§",
        r"^\d{1,3}\s+附[録錄]",
        r"^附[録錄]\s",
        r"^岩波講座",
    ),
    typst_front_matter=TYPST_FRONT_MATTER,
    latex_preamble=LATEX_PREAMBLE,
    page_fixups={
        131: ((r"(\\leq q)\\\}", r"\1}"),),
        159: ((r"(\\begin\{array\}\{)cccccc(\})", r"\1cccccccccc\2"),),
        142: (
            (
                r"(\\sigma_\{h_0 \\cdots h_t j_s \\cdots j_q) \+ \\sum_\{t=s\+1\}",
                r"\1} + \\sum_{t=s+1}",
            ),
            (
                r"(\\sigma_\{h_0 \\cdots h_s \\cdots h_t j_t \\cdots j_q) \+ \\sum_\{s=t\+1\}",
                r"\1} + \\sum_{s=t+1}",
            ),
        ),
        178: (
            (
                r"(\\overline\{dz\^\{B_\{n-q\}\}) \\wedge",
                r"\1} \\wedge",
            ),
        ),
        198: (
            (
                (r"\$\$\s*2\\pi\\sqrt\{-1\} I\(S, \\gamma\)\s*=\s*\\sum m_\{ijk\}\s*"
                r"\\left\((.*?)\\right\.\s*\$\$\s*\$\$\s*\+(.*?)\s*\$\$\s*\$\$\s*\+"
                r"(.*?)\\right\)\.\s*\$\$"),
                r"$$2\\pi\\sqrt\{-1\} I(S, \\gamma) = \\sum m_\{ijk\} \\left(\1 \2 \3\\right).$$",
            ),
        ),
    },
    pdf_name_markers=("複素多様体論",),
    pdf_page_count=500,
)
