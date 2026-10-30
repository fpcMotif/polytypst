from scripts.render_check import caption_label


def test_a_caption_line_gives_its_label() -> None:
    assert caption_label("表1-1 GDP 缺口估算方法之比较") == "表1-1"
    assert caption_label("图 1-1\n采用生产函数法的 GDP 缺口比较") == "图1-1"
    assert caption_label("图 11-2") == "图11-2"
    assert caption_label("表 10-5 日本的再配置效应（市场经济，1975—2005 年）") == "表10-5"
    assert caption_label("附表5-1 研究会成员") == "附表5-1"
    assert caption_label("附表 A 统计数据的来源") == "附表A"


def test_a_sentence_that_names_a_table_is_not_a_caption() -> None:
    assert caption_label("表1-1 显示了内阁府、日本银行、国际货币基金组织和经济合作与发展组织对日本 GDP 缺口的估算结果，各机构采用的方法与数据各不相同，因此估算值存在一定差异。") is None
    assert caption_label("如表1-1所示") is None
    assert caption_label("表 10-5 的结果显示，从资本和劳动力的整体再配置效应来看") is None
    assert caption_label("图 11-4 显示了当劳动力努力水平对超额劳动时间的弹性") is None
    assert caption_label("表1-10") == "表1-10"
