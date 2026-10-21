from ..compiler.monograph import ChapterSpec, MonographSpec

LONDON_TREASURY_SPEC = MonographSpec(
    slug="london_branch_treasury_and_trading_reader",
    title="伦敦分行资金与交易业务阅读册",
    subtitle="从业者经验导读、轮岗问题与53篇原始文献汇编",
    author="赴任前阅读编委会",
    editor="Polytypst 金融实务丛书",
    publisher="伦敦分行资金与交易业务实务编纂",
    series="境外分行交易资金与资产负债管理系列",
    year=2026,
    publisher_key="cambridge",
    lang="zh",
    domain="economics",
    pdf_page_count=57,
    pdf_name_markers=("伦敦分行资金与交易业务阅读册", "london_branch_treasury"),
    source_pdf="伦敦分行资金与交易业务阅读册.pdf",
    chapters=[
        ChapterSpec(0, "导读与全书框架", 2, 7),
        ChapterSpec(1, "第一章 资金与资产负债管理", 8, 15),
        ChapterSpec(2, "第二章 外币货币市场与外汇", 16, 25),
        ChapterSpec(3, "第三章 现券与利率交易", 26, 33),
        ChapterSpec(4, "第四章 贵金属交易与商业链条", 34, 40),
        ChapterSpec(5, "第五章 组织协作与组合风险", 41, 45),
        ChapterSpec(6, "第六章 相邻行业的对照", 46, 48),
        ChapterSpec(7, "第七章 轮岗核实、词汇、现行规则与核验资料", 49, 57),
    ],
)
