"""Tests for monograph end-matter preservation, HTML table normalization, and index formatting."""

from pathlib import Path
from polytypst.cleaner.tex_markdown import TeXMarkdownCleaner
from polytypst.compiler.monograph import ChapterSpec, MonographCompiler, MonographSpec


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
    cleaned = TeXMarkdownCleaner.normalize_html_tables(raw_html)
    assert "<table" not in cleaned
    assert "ebene Koordinat 平面坐标 10" in cleaned
    assert "Ebenenpaar 平面偶 18" in cleaned


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
    cleaned = TeXMarkdownCleaner.normalize_html_tables(raw_html)
    assert "<table" not in cleaned
    assert "| x | y | z |" in cleaned
    assert "| -x | y | -z |" in cleaned


def test_drop_line_regexes_never_delete_body_index_entries():
    spec = MonographSpec(
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
    extracted, _, _ = compiler.extract_page_parts(body_text, pno=1)

    assert "Abraham, 39, 43" in extracted
    assert "Aronhold, 147, 177" in extracted
    assert "Beltrami, 99, 138, 150, 170–173" in extracted
    assert "Böcher, 3, 25, 71, 110" in extracted
    assert "Boltzmann, 63" in extracted


def test_index_chapter_formats_in_two_columns():
    spec = MonographSpec(
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
