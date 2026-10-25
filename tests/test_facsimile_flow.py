import numpy as np
import pytest
from PIL import Image

from polytypst.facsimile import (
    FOOTNOTE_RULE,
    FOOTNOTE_SIZE,
    Outline,
    book_pitch,
    contents_pages,
    contents_parts,
    counted_lines,
    dropped_headings,
    flow_markup,
    flow_typst,
    glyph_count,
    line_entries,
    ocr_head,
    ocr_line_entries,
    page_frame,
    page_starts,
    placed_typst,
    running_head,
    with_foot_lines,
)
from polytypst.ocr.pages import OcrLine
from polytypst.parity.words import PT_PER_PX


def scan_page() -> np.ndarray:
    ink = np.zeros((3600, 2480), dtype=bool)
    ink[150:200, 300:1200] = True
    ink[220:226, 200:2200] = True
    for top in range(320, 1400, 80):
        ink[top : top + 60, 210:2190] = True
    ink[3500:3540, 1200:1260] = True
    return ink


def test_frame_is_the_text_block_between_running_head_and_folio() -> None:
    frame = page_frame(scan_page())
    assert frame is not None
    assert (frame.left, frame.top, frame.right) == pytest.approx(
        (210 * PT_PER_PX, 320 * PT_PER_PX, 2190 * PT_PER_PX)
    )
    assert frame.bottom == pytest.approx(1420 * PT_PER_PX)
    assert frame.line == pytest.approx(60 * PT_PER_PX)
    assert frame.rule == pytest.approx(
        (200 * PT_PER_PX, 220 * PT_PER_PX, 2200 * PT_PER_PX, 226 * PT_PER_PX)
    )
    assert frame.margins == ((150, 200), (3500, 3540))


def test_specks_and_short_lines_do_not_widen_the_text_block() -> None:
    ink = scan_page()
    ink[400:404, 40:44] = True
    ink[800:804, 2400:2404] = True
    ink[1040:1100, 210:2190] = False
    ink[1040:1100, 800:1600] = True
    frame = page_frame(ink)
    assert frame is not None
    assert (frame.left, frame.right) == pytest.approx((210 * PT_PER_PX, 2190 * PT_PER_PX))


def test_a_page_of_mostly_short_lines_keeps_the_full_measure() -> None:
    ink = scan_page()
    for top in range(320, 1200, 80):
        ink[top : top + 60, 1400:2190] = False
    frame = page_frame(ink)
    assert frame is not None
    assert (frame.left, frame.right) == pytest.approx((210 * PT_PER_PX, 2190 * PT_PER_PX))


def test_dust_above_and_below_the_text_is_not_the_frame_top_or_bottom() -> None:
    ink = scan_page()
    ink[250:258, 600:620] = True
    ink[1600:1606, 900:920] = True
    frame = page_frame(ink)
    assert frame is not None
    assert (frame.top, frame.bottom) == pytest.approx((320 * PT_PER_PX, 1420 * PT_PER_PX))


def test_a_skewed_header_rule_is_still_the_rule() -> None:
    ink = scan_page()
    ink[220:226] = False
    for x in range(200, 2200):
        y = 216 + x * 20 // 2000
        ink[y : y + 4, x] = True
    frame = page_frame(ink)
    assert frame is not None
    assert frame.top == pytest.approx(320 * PT_PER_PX)
    assert frame.rule is not None
    assert frame.margins[0] == (150, 200)


def head_page(folio_left: int) -> np.ndarray:
    ink = scan_page()
    ink[150:200] = False
    ink[150:200, 1000:1500] = True
    ink[160:190, folio_left : folio_left + 60] = True
    return ink


def test_the_running_head_box_is_the_title_beside_the_folio() -> None:
    ink = head_page(2100)
    frame = page_frame(ink)
    assert frame is not None
    head = running_head(ink, frame)
    assert head is not None
    assert (head.left, head.top, head.right, head.bottom) == pytest.approx(
        (1000 * PT_PER_PX, 150 * PT_PER_PX, 1500 * PT_PER_PX, 200 * PT_PER_PX)
    )


def test_a_foot_line_that_is_not_a_folio_joins_the_text_block() -> None:
    ink = scan_page()
    ink[3500:3540] = False
    for top in range(1400, 3340, 80):
        ink[top : top + 60, 210:2190] = True
    ink[3400:3450, 900:1500] = True
    frame = page_frame(ink)
    assert frame is not None
    assert frame.bottom < 3400 * PT_PER_PX
    grown = with_foot_lines(ink, frame, (ocr_line("x+y=1", 3395),))
    assert grown.bottom == pytest.approx(3450 * PT_PER_PX)
    assert with_foot_lines(ink, frame, (ocr_line("· 15 ·", 3395),)) == frame


def test_dust_above_the_head_does_not_take_the_running_head_band() -> None:
    ink = head_page(250)
    ink[75:83, 600:700] = True
    frame = page_frame(ink)
    assert frame is not None
    head = running_head(ink, frame)
    assert head is not None
    assert (head.left, head.right) == pytest.approx((1000 * PT_PER_PX, 1500 * PT_PER_PX))


def test_the_ocr_head_is_the_title_not_the_folio() -> None:
    ink = head_page(2100)
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("・ii・", 145, 2100, 2160), ocr_line("《选译》序", 145, 1000, 1500), ocr_line("正文", 320))
    assert ocr_head(ink, frame, lines) == "《选译》序"


def test_a_page_with_no_head_band_has_no_running_head() -> None:
    ink = scan_page()
    ink[150:226] = False
    frame = page_frame(ink)
    assert frame is not None
    assert running_head(ink, frame) is None


def glyph_page(pitch_px: int) -> np.ndarray:
    ink = np.zeros((3600, 2480), dtype=bool)
    for top in range(320, 1400, 80):
        for left in range(210, 2190 - pitch_px, pitch_px):
            ink[top : top + 50, left + 4 : left + pitch_px - 6] = True
    return ink


def test_the_book_pitch_is_the_advance_of_the_scan_glyphs() -> None:
    pages = [glyph_page(56), glyph_page(56)]
    frames = [page_frame(ink) for ink in pages]
    assert book_pitch([(ink, f) for ink, f in zip(pages, frames, strict=True) if f]) == pytest.approx(56 * PT_PER_PX)


def test_the_flow_box_holds_a_whole_number_of_glyphs_centred_on_the_ink() -> None:
    frame = page_frame(scan_page())
    assert frame is not None
    place = flow_typst(frame, 10.0, "")[0]
    width = 10.0 * round((frame.right - frame.left) / 10.0)
    assert f"dx: {(frame.left + frame.right - width) / 2:.2f}pt" in place
    assert f"flowfit({width:.2f}pt" in place


def test_full_bleed_cover_has_no_frame() -> None:
    assert page_frame(np.ones((3600, 2480), dtype=bool)) is None


def test_paragraphs_indent_after_a_sentence_and_not_after_a_comma() -> None:
    math = {("x,", True): "x,", ("y.", True): "y."}
    markup = flow_markup("甲\n\n$$x,$$\n\n乙\n\n$$y.$$\n\n丙", math, set())
    assert markup.split("\n\n") == ['#"甲"', "$ x, $", '#"乙"', "$ y. $", '#h(2em)#"丙"']


def test_a_leading_folio_is_dropped_and_an_equation_number_kept() -> None:
    assert flow_markup("· 32 ·\n\n甲\n\n(1)", {}, set()) == '#"甲"\n\n#h(2em)#"(1)"'


def test_an_html_table_becomes_a_typst_table() -> None:
    html = "<table>\n<tr><th>1</th><th>$a$</th></tr>\n<tr><td>e</td></tr>\n</table>"
    markup = flow_markup(html, {("a", False): "a"}, set())
    assert markup == '#align(center, table(columns: 2, stroke: 0.4pt, inset: 3pt, [#"1"], [$a$], [#"e"], []))'


def test_an_image_link_places_the_figure_file(tmp_path) -> None:
    Image.new("L", (100, 50)).save(tmp_path / "fig_1.png")
    wide = flow_markup("![图 1](fig_1.png)", {}, set(), tmp_path, 500.0)
    narrow = flow_markup("![图 1](fig_1.png)", {}, set(), tmp_path, 10.0)
    assert f'image("{tmp_path / "fig_1.png"}", width: {100 * PT_PER_PX:.2f}pt)' in wide
    assert 'width: 10.00pt' in narrow
    assert '"图 1"' in wide


def test_a_numbered_heading_runs_into_the_next_paragraph_in_bold() -> None:
    markup = flow_markup("### 22. 变量\n\n在物理学内", {}, set())
    assert markup == '#h(2em)#text(weight: "bold")[#"22." #"变量"] #"在物理学内"'


def test_a_section_heading_prints_its_number_through_the_heading_counter() -> None:
    markup = flow_markup("## §1. 整序变量\n\n正文", {}, set(), outline=Outline({}))
    assert markup.split("\n\n")[0] == '#heading(level: 2, numbering: "§1.", outlined: true)[#"整序变量"] <chap-0-sec-1>'


def test_a_section_whose_number_the_count_misses_resyncs_the_counter() -> None:
    outline = Outline({})
    markup = flow_markup("# 第二章 函数\n\n## §3. 极限", {}, set(), outline=outline)
    assert markup.split("\n\n") == [
        '#counter(heading).update((1,))#heading(level: 1, numbering: "第一章", outlined: true)[#"函数"] <chap-2>',
        '#counter(heading).update((2, 2))#heading(level: 2, numbering: "§1.", outlined: true)[#"极限"] <chap-2-sec-3>',
    ]
    assert outline.resyncs == 2


def test_a_part_is_a_title_the_contents_lists_once_and_the_body_sets_as_a_heading() -> None:
    contents = "§1 群 1\n\n习题 5\n\n§2 环 6\n\n习题 9\n\n3. 齐次空间 7\n\n名词索引 240\n\n后记 250"
    body = "# 名词索引\n\n## 习题\n\n## 3. 齐次空间\n\n正文"
    assert contents_parts({1: contents, 2: body}, range(1, 2)) == {"名词索引": 0}


def test_the_contents_are_the_first_run_of_pages_listing_page_numbers_not_the_index() -> None:
    texts = {
        1: "前言\n\n正文",
        2: "目录\n\n绪论 1\n\n第一章 极限论 28",
        3: "§1. 有理数域 1\n\n§2. 无理数 5\n\n1. 有理数 (1)",
        4: "正文\n\n正文",
        5: "实数 8\n\n极限 30\n\n函数 74",
    }
    assert contents_pages(texts) == range(2, 4)


def test_one_misread_folio_does_not_restart_the_page_counter() -> None:
    folios = {8: [6], 9: [7], 12: [1], 13: [2], 14: [300], 15: [4], 16: [5]}
    assert page_starts(folios) == {8: 6, 12: 1}


def test_an_article_number_beside_the_folio_does_not_restart_the_page_counter() -> None:
    assert page_starts({12: [1], 13: [2, 114], 14: [3], 15: [116, 4]}) == {12: 1}


def test_a_misread_folio_beside_an_article_number_does_not_restart_the_page_counter() -> None:
    folios = {98: [87], 99: [88], 100: [89], 101: [50], 102: [91, 51], 103: [92]}
    assert page_starts(folios) == {98: 87}


def test_a_section_heading_dropped_by_line_locking_still_counts() -> None:
    ink = contents_page()
    frame = page_frame(ink)
    assert frame is not None
    entries = [("§3. 实数的算术运算", True), ("正文", False)]
    placed = [("正文", False, [(0, 100, 320, 380)])]
    hidden = dropped_headings(entries, placed, frame, Outline({}), {})
    assert len(hidden) == 1
    assert '#heading(level: 2, numbering: "§1.", outlined: true)[#"实数的算术运算"] <chap-0-sec-3>' in hidden[0]


def test_a_heading_that_is_not_a_chapter_or_section_is_left_out_of_the_running_heads() -> None:
    markup = flow_markup("## 习题\n\n正文", {}, set(), outline=Outline({}))
    assert markup.split("\n\n")[0] == '#heading(level: 2, outlined: false, [#"习题"])'


def test_a_contents_line_takes_its_number_and_page_from_the_heading_it_names() -> None:
    outline = Outline({}, in_contents=True)
    assert outline.entry("第二章 一元函数 74")[2] == '#facsimile-ref(<chap-2>, h => str(counter(page).at(h.location()).first()), "74")'
    lead, text, page = outline.entry("§3. 无穷小 110")
    assert lead == '#facsimile-ref(<chap-2-sec-3>, h => numbering(h.numbering, counter(heading).at(h.location()).last()), "§3.")'
    assert text == "无穷小 110"
    assert "<chap-2-sec-3>" in page
    assert outline.entry("34. 单调整序变量的极限 (53)") is None


def test_footnotes_from_the_first_note_mark_to_the_page_end_are_set_small_under_a_rule() -> None:
    markup = flow_markup("正文\n\n⁵) 注一\n\n续注\n\n①注二", {}, set())
    body, notes = markup.split("\n\n", 1)
    assert body == '#"正文"'
    assert notes.startswith(f"{FOOTNOTE_RULE}\n\n#text(size: {FOOTNOTE_SIZE}em)[")
    assert '#"续注"' in notes and '#"①注二"' in notes


def test_run_together_contents_entries_split_at_each_page_number() -> None:
    assert line_entries("· ii ·\n\n# 目录\n\n1. 商群的概念 21 2. 群的同态定理 23\n\n第 2 章 群的结构 36") == [
        ("目录", True),
        ("1. 商群的概念 21", False),
        ("2. 群的同态定理 23", False),
        ("第 2 章 群的结构 36", False),
    ]


def test_a_display_formula_is_one_entry_with_its_dollars() -> None:
    assert line_entries("甲\n\n$$x\n= 1$$\n\n乙") == [("甲", False), ("$$x\n= 1$$", False), ("乙", False)]


def test_a_page_with_a_table_is_not_line_locked() -> None:
    assert line_entries("甲\n\n<table><tr><td>1</td></tr></table>") is None


def locked_typst(ink: np.ndarray, frame, entries: list[tuple[str, bool]], size: float, math: dict) -> list[str] | None:
    placed = counted_lines(entries, ink, frame)
    return placed_typst(ink, frame, placed, size, math) if placed else None


def contents_page() -> np.ndarray:
    ink = scan_page()[:, :]
    ink[320:1400] = False
    for top in range(320, 640, 80):
        ink[top : top + 60, 210:700] = True
        ink[top + 50 : top + 60, 760:1900 : 30] = True
        ink[top : top + 60, 2050:2190] = True
    return ink


def test_a_contents_line_puts_its_page_number_right_of_the_leader() -> None:
    ink = contents_page()
    frame = page_frame(ink)
    assert frame is not None
    entries = [("目录", True)] + [(f"第{k}节 群 {k}0", False) for k in range(4)]
    out = locked_typst(ink, frame, entries, 60 * PT_PER_PX, {})
    assert out is not None
    numbers = [s for s in out if '"30"' in s]
    assert len(numbers) == 1 and f"dx: {2050 * PT_PER_PX:.2f}pt" in numbers[0]
    titles = [s for s in out if '#"第3节" #"群"' in s]
    assert len(titles) == 1 and f"inkfit({490 * PT_PER_PX:.2f}pt" in titles[0]
    assert sum("repeat(" in s for s in out) == 4


def test_leader_dots_in_a_tall_bold_line_are_still_a_leader() -> None:
    ink = contents_page()
    for top in range(320, 640, 80):
        ink[top - 10 : top, 210:400] = True
    frame = page_frame(ink)
    assert frame is not None
    out = locked_typst(ink, frame, [(f"第{k}章 群 {k}0", True) for k in range(4)], 60 * PT_PER_PX, {})
    assert out is not None
    title = next(s for s in out if '#"第3章"' in s)
    assert f"inkfit({490 * PT_PER_PX:.2f}pt" in title


def test_a_speck_past_an_index_line_does_not_take_its_page_number() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in range(320, 640, 80):
        ink[top : top + 60, 210:1800] = True
    ink[350:354, 2100:2104] = True
    frame = page_frame(ink)
    assert frame is not None
    out = locked_typst(ink, frame, [("条目, 30", False)] * 4, 60 * PT_PER_PX, {})
    assert out is not None
    assert not any("repeat(" in s for s in out)
    assert f"inkfit({1590 * PT_PER_PX:.2f}pt" in out[0] and '#"30"' in out[0]


def ocr_line(text: str, top: int, left: int = 210, right: int = 2190) -> OcrLine:
    return OcrLine(text, left / 2480, 1 - (top + 60) / 3600, (right - left) / 2480, 60 / 3600)


def test_a_paragraph_is_cut_at_the_scan_line_breaks_the_ocr_reads() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in range(320, 560, 80):
        ink[top : top + 60, 210:2190] = True
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("甲乙丙丁", 320), ocr_line("戊已y庚", 400), ocr_line("辛壬$x$", 480))
    entries = [("目录", True), ("甲乙丙丁戊己 $y$ 庚辛壬 $x$", False)]
    placed = ocr_line_entries(entries, ink, frame, lines)
    assert placed is not None
    assert [(text, bold, [band[2] for band in bands]) for text, bold, bands in placed] == [
        ("甲乙丙丁", False, [320]),
        ("戊己 $y$ 庚", False, [400]),
        ("辛壬 $x$", False, [480]),
    ]


def test_a_line_end_the_ocr_misreads_stays_on_its_line() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in (320, 400):
        ink[top : top + 60, 210:2190] = True
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("及其应用(5", 320), ocr_line("单调整序变量", 400))
    entries = [("及其应用 (50)", False), ("§3. 单调整序变量 53", False)]
    placed = ocr_line_entries(entries, ink, frame, lines)
    assert placed is not None
    assert [text for text, _, _ in placed] == ["及其应用 (50)", "§3. 单调整序变量 53"]


def test_a_page_number_the_next_line_also_reads_stays_with_its_entry() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in (320, 400):
        ink[top : top + 60, 210:2190] = True
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("第二章一元函数", 320), ocr_line("74", 400, 2000, 2190), ocr_line("§1.函数概念", 400))
    entries = [("第二章 一元函数 74", True), ("§1. 函数概念 74", False)]
    placed = ocr_line_entries(entries, ink, frame, lines)
    assert placed is not None
    assert [text for text, _, _ in placed] == ["第二章 一元函数 74", "§1. 函数概念 74"]


def test_a_page_opening_with_a_section_mark_keeps_the_mark() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in (320, 400):
        ink[top : top + 60, 210:2190] = True
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("3.实数的算术运算", 320), ocr_line("今转而建立", 400))
    entries = [("§3. 实数的算术运算", True), ("今转而建立", False)]
    placed = ocr_line_entries(entries, ink, frame, lines)
    assert placed is not None
    assert placed[0][0] == "§3. 实数的算术运算"


def test_a_line_ending_inside_inline_math_keeps_the_formula_whole() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in (320, 400):
        ink[top : top + 60, 210:2190] = True
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("甲乙AB", 320), ocr_line("=C丙丁", 400))
    placed = ocr_line_entries([(r"甲乙 $AB = C$ 丙丁", False)], ink, frame, lines)
    assert placed is not None
    assert [text for text, _, _ in placed] == [r"甲乙 $AB = C$", "丙丁"]


def test_a_page_starting_inside_inline_math_keeps_the_formula_whole() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in (320, 400):
        ink[top : top + 60, 210:2190] = True
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("C甲乙", 320), ocr_line("丙丁", 400))
    placed = ocr_line_entries([(r"$\alpha C$ 甲乙 丙丁", False)], ink, frame, lines)
    assert placed is not None
    assert [text for text, _, _ in placed] == [r"$\alpha C$ 甲乙", "丙丁"]


def formula_page() -> np.ndarray:
    ink = scan_page()
    ink[320:1400] = False
    for top in (320, 400, 640, 720):
        ink[top : top + 60, 210:2190] = True
    ink[480:520, 900:1500] = True
    ink[540:580, 900:1500] = True
    return ink


def test_a_display_formula_takes_the_scan_lines_between_its_text_lines() -> None:
    ink = formula_page()
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("甲乙丙丁", 320), ocr_line("戊己", 400), ocr_line("xy", 480), ocr_line("庚辛", 640), ocr_line("壬癸", 720))
    entries = [("甲乙丙丁戊己", False), ("$$\\frac{a}{b}$$", False), ("庚辛壬癸", False)]
    placed = ocr_line_entries(entries, ink, frame, lines)
    assert placed is not None
    display = [bands for text, _, bands in placed if text.startswith("$$")]
    assert [[band[2] for band in bands] for bands in display] == [[480, 540]]
    out = placed_typst(ink, frame, placed, 60 * PT_PER_PX, {("\\frac{a}{b}", True): "frac(a, b)"})
    assert out is not None
    formula = next(s for s in out if "frac(a, b)" in s)
    assert f"dx: {900 * PT_PER_PX:.2f}pt, dy: {480 * PT_PER_PX:.2f}pt" in formula
    assert f"inkfit({600 * PT_PER_PX:.2f}pt, {100 * PT_PER_PX:.2f}pt, text(size: {60 * PT_PER_PX:.2f}pt, box($ frac(a, b) $)))" in formula


def test_a_display_whose_ocr_matches_only_inline_math_keeps_its_scan_line() -> None:
    ink = formula_page()
    ink[540:580] = False
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("甲乙丙丁", 320), ocr_line("戊己", 400), ocr_line("x+y", 480), ocr_line("庚辛", 640), ocr_line("壬癸", 720))
    entries = [("甲乙丙丁戊己", False), ("$$x + y$$", False), ("$x$ 庚辛壬癸", False)]
    placed = ocr_line_entries(entries, ink, frame, lines)
    assert placed is not None
    assert [[band[2] for band in bands] for text, _, bands in placed if text.startswith("$$")] == [[480]]


def test_a_display_formula_with_no_scan_line_of_its_own_is_not_line_locked() -> None:
    ink = formula_page()
    ink[480:580] = False
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("甲乙丙丁", 320), ocr_line("戊己", 400), ocr_line("庚辛", 640), ocr_line("壬癸", 720))
    entries = [("甲乙丙丁戊己", False), ("$$x$$", False), ("庚辛壬癸", False)]
    assert ocr_line_entries(entries, ink, frame, lines) is None


def test_a_scan_line_the_transcript_lacks_is_placed_as_a_crop_of_the_scan(tmp_path) -> None:
    ink = formula_page()
    frame = page_frame(ink)
    assert frame is not None
    lines = (ocr_line("甲乙丙丁", 320), ocr_line("戊己", 400), ocr_line("图1", 480), ocr_line("庚辛", 640), ocr_line("壬癸", 720))
    entries = [("甲乙丙丁戊己", False), ("庚辛壬癸", False)]
    placed = ocr_line_entries(entries, ink, frame, lines)
    assert placed is not None
    assert [[band[2] for band in bands] for text, _, bands in placed if not text] == [[480], [540]]
    out = placed_typst(ink, frame, placed, 60 * PT_PER_PX, {}, tmp_path / "crop")
    assert out is not None
    crops = [s for s in out if "image(" in s]
    assert len(crops) == 2
    assert f"dx: {900 * PT_PER_PX:.2f}pt, dy: {480 * PT_PER_PX:.2f}pt" in crops[0]
    assert f"width: {600 * PT_PER_PX:.2f}pt, height: {40 * PT_PER_PX:.2f}pt" in crops[0]
    assert sorted(Image.open(png).size for png in tmp_path.glob("crop_*.png")) == [(600, 40), (600, 40)]


def test_inline_math_counts_its_symbols_not_its_latex_commands() -> None:
    assert glyph_count(r"甲 $\frac{x_n}{y_n}$") == pytest.approx(1.0 + 4 * 0.55)


def test_a_page_whose_lines_do_not_match_the_scan_is_not_line_locked() -> None:
    ink = contents_page()
    frame = page_frame(ink)
    assert frame is not None
    assert locked_typst(ink, frame, [("甲 1", False)] * 3, 60 * PT_PER_PX, {}) is None


def test_two_columns_take_the_transcript_lines_column_by_column() -> None:
    ink = scan_page()
    ink[320:1400] = False
    for top in range(320, 640, 80):
        ink[top : top + 60, 210:1000] = True
        ink[top : top + 60, 1300:2190] = True
    frame = page_frame(ink)
    assert frame is not None
    out = locked_typst(ink, frame, [(f"条目{k}", False) for k in range(8)], 60 * PT_PER_PX, {})
    assert out is not None
    fifth = next(s for s in out if '"条目4"' in s)
    assert f"dx: {1300 * PT_PER_PX:.2f}pt, dy: {320 * PT_PER_PX:.2f}pt" in fifth


def test_running_head_copied_as_a_heading_is_dropped() -> None:
    seen: set[str] = set()
    outline = Outline({})
    first = flow_markup("## §5. 方程\n\n正文", {}, seen, outline=outline)
    again = flow_markup("# §5. 方程\n\n计算", {}, seen, outline=outline)
    assert first.startswith('#counter(heading).update((0, 4))#heading(level: 2, numbering: "§1.", outlined: true)[#"方程"]')
    assert again == '#"计算"'
