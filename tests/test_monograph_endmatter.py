"""Tests for monograph end-matter preservation, HTML table normalization, and index formatting."""

from pathlib import Path

from polytypst.compiler.monograph import ChapterSpec, MonographCompiler, MonographSpec
from polytypst.tex_markdown import normalize_html_tables


def test_normalize_html_tables_index_style():
    raw_html = (
        "## E\n\n"
        "<table>\n"
        "<thead>\n"
        '  <tr class="section-header">\n'
        "    <th>ebene Koordinat</th>\n"
        "    <th>平面坐标</th>\n"
        "    <th>10</th>\n"
        "  </tr>\n"
        '  <tr class="section-header">\n'
        "    <th>Ebenenpaar</th>\n"
        "    <th>平面偶</th>\n"
        "    <th>18</th>\n"
        "  </tr>\n"
        "</thead>\n"
        "</table>"
    )
    cleaned = normalize_html_tables(raw_html)
    assert "<table" not in cleaned
    assert "ebene Koordinat 平面坐标 10" in cleaned
    assert "Ebenenpaar 平面偶 18" in cleaned


def test_normalize_html_tables_keeps_marked_cells():
    raw_html = "<table><tr><th>年度</th><th>差额</th></tr><tr><td><mark>1986</mark></td><td><mark>1.2</mark></td></tr></table>"
    assert "| <mark>1986</mark> | <mark>1.2</mark> |" in normalize_html_tables(raw_html)


def test_normalize_html_tables_grid_style():
    raw_html = (
        "<table>\n"
        "<thead>\n"
        '  <tr class="table-header">\n'
        "    <th>x</th>\n"
        "    <th>y</th>\n"
        "    <th>z</th>\n"
        "  </tr>\n"
        '  <tr class="table-header">\n'
        "    <th>-x</th>\n"
        "    <th>y</th>\n"
        "    <th>-z</th>\n"
        "  </tr>\n"
        "</thead>\n"
        "</table>"
    )
    cleaned = normalize_html_tables(raw_html)
    assert "<table" not in cleaned
    assert "| x | y | z |" in cleaned
    assert "| -x | y | -z |" in cleaned


def test_normalize_html_tables_keeps_empty_cells_in_their_columns():
    raw_html = (
        "<table>\n"
        "  <tr><th>(26)</th><th>a_00</th><th>a_01</th></tr>\n"
        "  <tr><th></th><th>a_10</th><th>a_11</th></tr>\n"
        "  <tr><td>a_20</td><td></td><td>a_22</td></tr>\n"
        "</table>"
    )
    cleaned = normalize_html_tables(raw_html)
    assert "| (26) | a_00 | a_01 |" in cleaned
    assert "|  | a_10 | a_11 |" in cleaned
    assert "| a_20 |  | a_22 |" in cleaned


def test_normalize_html_tables_tolerates_a_misspelled_closing_tag():
    raw_html = (
        "<table>\n"
        "  <tr>\n"
        "    <th>2. 障碍</th>\n"
        "    <th>A<br>(n = 84)</th>\n"
        "    <th>B<br>(n = 42)</the>\n"
        "    <th>A-B</th>\n"
        "  </tr>\n"
        "  <tr><th>成本高</th><th>60.7</th><th>38.1</th><th>22.6</th></tr>\n"
        "</table>"
    )
    cleaned = normalize_html_tables(raw_html)
    assert "| 2. 障碍 | A<br>(n = 84) | B<br>(n = 42) | A-B |" in cleaned
    assert "| 成本高 | 60.7 | 38.1 | 22.6 |" in cleaned


def test_normalize_html_tables_joins_ocr_spaced_decimals():
    raw_html = (
        "<table>\n"
        "  <tr><th>项目</th><th>A</th><th>B</th><th>A-B</th></tr>\n"
        "  <tr><th>人才</th><th>3. 6</th><th>0</th><th>-4. 7</th></tr>\n"
        "</table>"
    )
    cleaned = normalize_html_tables(raw_html)
    assert "| 人才 | 3.6 | 0 | -4.7 |" in cleaned


def test_normalize_html_tables_counts_columns_from_the_widest_row():
    raw_html = (
        "<table>\n"
        "  <tr><th></th><th>A/p</th></tr>\n"
        "  <tr><td>PID</td><td>YES</td><td>NO</td></tr>\n"
        "</table>"
    )
    cleaned = normalize_html_tables(raw_html)
    assert "|  | A/p |  |" in cleaned
    assert "| :--- | :---: | :---: |" in cleaned
    assert "| PID | YES | NO |" in cleaned


def test_drop_line_regexes_never_delete_body_index_entries():
    spec = MonographSpec(
        domain="math",
        slug="test_book",
        title="Test Book",
        author="Author",
        header_zone_lines=2,
        drop_line_regexes=(
            r"^Running Header.*$",
            r"^\d+\s+[A-Z\s]+$",
        ),
        chapters=[ChapterSpec(1, "人名索引", 1, 2)],
    )
    compiler = MonographCompiler(spec)

    body_text = (
        "Header Line 1\n"
        "Header Line 2\n"
        "Abraham, 39, 43\n"
        "Aronhold, 147, 177\n"
        "Beltrami, 99, 138, 150, 170–173\n"
        "Böcher, 3, 25, 71, 110\n"
        "Boltzmann, 63\n"
    )
    extracted, _, _ = compiler.cleaner.clean(body_text, pno=1)

    assert "Abraham, 39, 43" in extracted
    assert "Aronhold, 147, 177" in extracted
    assert "Beltrami, 99, 138, 150, 170–173" in extracted
    assert "Böcher, 3, 25, 71, 110" in extracted
    assert "Boltzmann, 63" in extracted


def test_pages_printed_sideways_in_the_scan_are_set_on_flipped_pages():
    spec = MonographSpec(
        domain="math", slug="t", title="T", author="A", chapters=[ChapterSpec(1, "C", 1, 4)], landscape_pages=frozenset({2, 3})
    )
    pages = [(1, "Body text that ends", [], []), (2, "| a | b |\n| --- | --- |\n| 1 | 2 |", [], []), (3, "注：wide table note.", [], []), (4, "continues here.", [], [])]
    compiler = MonographCompiler(spec)
    out = compiler.format_typst(compiler.stitch_chapter(pages, Path(".")))
    assert "\\#set page" not in out
    turn, back = out.index("#set page(flipped: true, columns: 1)"), out.index("#set page(flipped: false, columns: 1)")
    assert out.index("Body text that ends") < turn < out.index("[#strong[a]]") < out.index("注：wide table note.") < back
    assert back < out.index("continues here.")
    assert out.count("#set page(") == 2


def test_a_table_caption_sticks_to_its_table():
    spec = MonographSpec(domain="math", slug="t", title="T", author="A", chapters=[ChapterSpec(1, "C", 1, 1)])
    out = MonographCompiler(spec).format_typst("表 5-2 政府经济预期与实际值（2）\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n")
    assert "#block(sticky: true, width: 100%)[#align(center)[#strong[表 5-2 政府经济预期与实际值（2）]]]" in out


def test_index_chapter_formats_in_two_columns():
    spec = MonographSpec(
        domain="math",
        slug="test_book",
        title="Test Book",
        author="Author",
        chapters=[
            ChapterSpec(1, "Main Chapter", 1, 1),
            ChapterSpec(2, "人名索引", 2, 2),
        ],
    )
    compiler = MonographCompiler(spec)

    p1_data = [(1, "Main text body paragraph.", [], [])]

    s1 = compiler.stitch_chapter(p1_data, Path("."))
    formatted1 = compiler.format_typst(s1)
    assert "#columns(2" not in formatted1

    # In render, chapters with "索引" in title are wrapped in #columns(2, ...)
    rendered = compiler.render(Path("output/test_scratch"))
    assert "= 人名索引" in rendered.typst
    assert "#columns(2, gutter: 1.8em)" in rendered.typst
