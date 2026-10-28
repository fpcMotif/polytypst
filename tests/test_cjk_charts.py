from PIL import Image, ImageDraw

from polytypst.ocr.pages import OcrLine, PageImage
from polytypst.vision.cjk_charts import extract_cjk_charts, transcript_figure_ids

W, H = 1000, 1500
PROSE = "这是一个用于测试的正文段落，里面有足够多的汉字来构成一整行文字内容。"


def line(
    text: str, left: float, top: float, width: float, height: float = 0.023
) -> OcrLine:
    """An OCR line given by its top-left corner, converted to the bottom-left origin OCR uses."""
    return OcrLine(text, left, 1.0 - top - height, width, height)


def page(tmp_path, draw_body, lines):
    img = Image.new("L", (W, H), 255)
    draw_body(ImageDraw.Draw(img))
    path = tmp_path / "p_001.png"
    img.save(path)
    return PageImage(1, path), {1: tuple(lines)}


def ink(d, top: float, bottom: float, left: float = 0.12, right: float = 0.89):
    d.rectangle((left * W, top * H, right * W, bottom * H), fill=0)


def test_a_chart_is_cropped_between_the_prose_and_its_notes_without_erasing_axis_labels(
    tmp_path,
):
    def body(d):
        ink(d, 0.10, 0.123)
        ink(d, 0.13, 0.153)
        ink(d, 0.20, 0.50, 0.15, 0.85)
        ink(d, 0.51, 0.52, 0.15, 0.85)
        ink(d, 0.55, 0.565, 0.16, 0.7)
        ink(d, 0.58, 0.595, 0.3, 0.6)

    lines = [
        line(PROSE, 0.12, 0.10, 0.77),
        line("这一时期的干预很可能考虑汇率以外的要因。", 0.12, 0.13, 0.5),
        line(
            "1993 1994 1995 1996 1997 1998 1999 2000 2001 2002 年",
            0.15,
            0.51,
            0.7,
            0.01,
        ),
        line(
            "注：全部都道府县按薪酬水平顺序排列，使全国平均值为1的标准化。",
            0.16,
            0.55,
            0.6,
            0.015,
        ),
        line("图1-6 薪酬水平的地区性变化", 0.3, 0.58, 0.3, 0.015),
    ]
    pg, ocr = page(tmp_path, body, lines)
    [fig] = extract_cjk_charts([pg], ocr, tmp_path / "figures")
    left, top, right, bottom = fig.box or (0, 0, 0, 0)
    assert fig.figure_id == "1-6"
    assert fig.caption == "图 1-6 薪酬水平的地区性变化"
    assert 0.153 < top <= 0.20 and 0.52 <= bottom < 0.55
    assert left < 0.15 and right > 0.85
    with Image.open(tmp_path / "figures" / "fig_1-6.png") as crop:
        year_row = crop.crop((0, crop.height - 25, crop.width, crop.height - 10))
    assert year_row.getextrema()[0] == 0


def test_a_chart_starts_below_the_source_line_of_an_earlier_chart_whose_caption_ocr_missed(
    tmp_path,
):
    def body(d):
        ink(d, 0.10, 0.123)
        ink(d, 0.15, 0.40, 0.15, 0.85)
        ink(d, 0.42, 0.435, 0.3, 0.6)
        ink(d, 0.50, 0.80, 0.15, 0.85)
        ink(d, 0.82, 0.835, 0.3, 0.6)

    lines = [
        line(PROSE, 0.12, 0.10, 0.77),
        line(
            "（资料来源：笔者使用 UN Comtrade 数据库处理制作）", 0.3, 0.42, 0.3, 0.015
        ),
        line("图6-11", 0.13, 0.82, 0.07, 0.015),
    ]
    pg, ocr = page(tmp_path, body, lines)
    [fig] = extract_cjk_charts([pg], ocr, tmp_path / "figures")
    assert fig.figure_id == "6-11"
    _, top, _, bottom = fig.box or (0, 0, 0, 0)
    assert 0.435 < top <= 0.50 and 0.80 <= bottom < 0.82


def test_two_lettered_panels_of_one_figure_are_cropped_apart(tmp_path):
    def body(d):
        ink(d, 0.15, 0.40, 0.15, 0.85)
        ink(d, 0.42, 0.435, 0.3, 0.6)
        ink(d, 0.50, 0.80, 0.15, 0.85)
        ink(d, 0.82, 0.835, 0.4, 0.5)

    lines = [
        line("图10-7A 新员工各年龄段薪酬（女性，月收入）", 0.3, 0.42, 0.3, 0.015),
        line("图 10-7B", 0.4, 0.82, 0.1, 0.015),
    ]
    pg, ocr = page(tmp_path, body, lines)
    figs = extract_cjk_charts([pg], ocr, tmp_path / "figures")
    assert [(f.figure_id, f.caption) for f in figs] == [
        ("10-7A", "图 10-7A 新员工各年龄段薪酬（女性，月收入）"),
        ("10-7B", "图 10-7B"),
    ]
    assert (tmp_path / "figures" / "fig_10-7B.png").exists()


def _two_pages(tmp_path, first_body, first_lines, second_body, second_lines):
    first, first_ocr = page(tmp_path, first_body, first_lines)
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    second, second_ocr = page(second_dir, second_body, second_lines)
    pages = [first, PageImage(2, second.path)]
    return pages, {1: first_ocr[1], 2: second_ocr[1]}


def _chart_opening_page_two(d):
    ink(d, 0.08, 0.40, 0.15, 0.85)
    ink(d, 0.42, 0.435, 0.4, 0.6)


CAPTION_ON_PAGE_TWO = [line("图8-8 4变量VAR模型的脉冲响应函数", 0.3, 0.42, 0.4, 0.015)]


def test_a_chart_split_over_a_page_break_is_cropped_whole(tmp_path):
    def chart_at_foot(d):
        ink(d, 0.10, 0.123)
        ink(d, 0.40, 0.90, 0.15, 0.85)

    pages, ocr = _two_pages(
        tmp_path,
        chart_at_foot,
        [line(PROSE, 0.12, 0.10, 0.77), line("具有显著的负向影响。", 0.12, 0.13, 0.3)],
        _chart_opening_page_two,
        CAPTION_ON_PAGE_TWO,
    )
    [fig] = extract_cjk_charts(pages, ocr, tmp_path / "figures")
    with Image.open(tmp_path / "figures" / "fig_8-8.png") as crop:
        height = crop.height
    assert fig.source_page == 2
    assert height > (0.50 + 0.32) * H


def test_a_footnote_at_the_foot_of_a_page_is_not_put_above_the_next_chart(tmp_path):
    paragraph = (0.10, 0.13, 0.16, 0.19, 0.22, 0.25)

    def footnote_at_foot(d):
        for top in paragraph:
            ink(d, top, top + 0.023)
        ink(d, 0.75, 0.751, 0.12, 0.35)
        for top in (0.76, 0.79, 0.82, 0.85, 0.88):
            ink(d, top, top + 0.015, 0.12, 0.85)

    note = "① 估算时期为季度单位，使用最小二乘法估算，数据来自内阁府的统计"
    pages, ocr = _two_pages(
        tmp_path,
        footnote_at_foot,
        [
            *(line(PROSE, 0.12, top, 0.77) for top in paragraph),
            *(
                line(note, 0.12, top, 0.73, 0.015)
                for top in (0.76, 0.79, 0.82, 0.85, 0.88)
            ),
        ],
        _chart_opening_page_two,
        CAPTION_ON_PAGE_TWO,
    )
    _ = extract_cjk_charts(pages, ocr, tmp_path / "figures")
    with Image.open(tmp_path / "figures" / "fig_8-8.png") as crop:
        assert crop.height < 0.40 * H


def test_a_table_continued_at_the_foot_of_a_page_is_not_put_above_the_next_chart(
    tmp_path,
):
    def table_at_foot(d):
        ink(d, 0.10, 0.123)
        ink(d, 0.40, 0.415, 0.8, 0.86)
        ink(d, 0.42, 0.90, 0.12, 0.86)

    cells = [
        line("36.8  11.4  1886  1.02", 0.5, top, 0.3, 0.012)
        for top in (0.45, 0.55, 0.65, 0.75)
    ]
    pages, ocr = _two_pages(
        tmp_path,
        table_at_foot,
        [line(PROSE, 0.12, 0.10, 0.77), line("续表", 0.8, 0.40, 0.06, 0.015), *cells],
        _chart_opening_page_two,
        CAPTION_ON_PAGE_TWO,
    )
    _ = extract_cjk_charts(pages, ocr, tmp_path / "figures")
    with Image.open(tmp_path / "figures" / "fig_8-8.png") as crop:
        assert crop.height < 0.40 * H


def test_a_sentence_that_mentions_a_figure_does_not_take_its_caption(tmp_path):
    def mention_page(d):
        ink(d, 0.20, 0.45, 0.15, 0.85)
        ink(d, 0.50, 0.525)

    def chart_page(d):
        ink(d, 0.20, 0.50, 0.15, 0.85)
        ink(d, 0.52, 0.537, 0.15, 0.85)

    first, first_lines = page(
        tmp_path,
        mention_page,
        [
            line(
                "图 11-5（1）以表格形式按年代汇总了上述结果，从表中可以证实，根",
                0.12,
                0.50,
                0.71,
            )
        ],
    )
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    long_caption = (
        "图11-5 非制造业TFP变化率（JIP估算值）和超额劳动时间变化率变化（1980—2005年）"
    )
    paragraph = [line(PROSE, 0.12, top, 0.77) for top in (0.60, 0.63, 0.66)]
    second, second_lines = page(
        second_dir, chart_page, [line(long_caption, 0.15, 0.52, 0.7, 0.017), *paragraph]
    )
    second = PageImage(2, second.path)
    [fig] = extract_cjk_charts(
        [first, second], {1: first_lines[1], 2: second_lines[1]}, tmp_path / "figures"
    )
    assert fig.source_page == 2
    assert fig.caption.startswith("图 11-5 非制造业TFP变化率")


def test_a_bold_transcript_caption_names_its_figure():
    page = "正文提到图 12-4 的收入。\n\n**图 12-5 地方政府的支出 (剔除支出利息) 与基础财政收支 (对 GDP 比率)**"
    assert transcript_figure_ids([page]) == {"12-5"}


def test_sub_numbered_transcript_captions_name_separate_figures():
    page = "图 10-4.1 中薪阶层占比\n\n图 10-4.2 工资的沃尔夫森极化指数\n\n图 10-5 工资分布"
    assert transcript_figure_ids([page]) == {"10-4.1", "10-4.2", "10-5"}
