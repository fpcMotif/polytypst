from pathlib import Path

import pytest

from polytypst.web_exporter import SitePage, site_pages

PAGE = '[[page]]\nslug = "{slug}"\neditions = ["vol1"]\ndomain = "Number Theory"\ndescription = "D"\n'


def _write(tmp_path: Path, key: str, text: str) -> Path:
    (tmp_path / key).mkdir(exist_ok=True)
    (tmp_path / key / "site.toml").write_text(text, encoding="utf-8")
    return tmp_path / key


def test_each_page_of_each_site_toml_is_listed_in_folder_order(tmp_path: Path):
    a = _write(tmp_path, "a", PAGE.format(slug="a-1") + "\n" + PAGE.format(slug="a-2"))
    (tmp_path / "b").mkdir()
    c = _write(tmp_path, "c", PAGE.format(slug="c-1"))
    folders = {"a": a, "b": tmp_path / "b", "c": c}

    assert [(p.key, p.slug, p.editions, p.domain, p.description) for p in site_pages(folders)] == [
        ("a", "a-1", ("vol1",), "Number Theory", "D"),
        ("a", "a-2", ("vol1",), "Number Theory", "D"),
        ("c", "c-1", ("vol1",), "Number Theory", "D"),
    ]


def test_a_page_takes_its_metadata_legend_and_layout_from_toml(tmp_path: Path):
    folder = _write(
        tmp_path,
        "s",
        '[[page]]\nslug = "s"\ndomain = "D"\ndescription = "d"\ntitle = "T"\nrendering = "vertical-classic"\n'
        'source = "@OUTPUT@/s"\nlegend = [{ color = "E73E29", label = "甲" }]\n[page.layout]\nfirst_page = 19\n',
    )

    [page] = site_pages({"s": folder})

    assert page == SitePage(
        "s", folder, "s", "D", "d", title="T", rendering="vertical-classic", source="@OUTPUT@/s",
        legend=(("E73E29", "甲"),), layout={"first_page": 19},
    )


def test_a_page_missing_a_required_key_names_its_file(tmp_path: Path):
    folder = _write(tmp_path, "a", PAGE.format(slug="a").replace('domain = "Number Theory"\n', ""))

    with pytest.raises(ValueError, match=r"a/site\.toml: a \[\[page\]\] needs the keys domain"):
        site_pages({"a": folder})


def test_a_page_with_an_unknown_key_names_its_file(tmp_path: Path):
    folder = _write(tmp_path, "a", PAGE.format(slug="a") + 'domian = "x"\n')

    with pytest.raises(ValueError, match=r"a/site\.toml: unknown \[\[page\]\] key domian"):
        site_pages({"a": folder})


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ('rendering = "comic"', r"rendering 'comic' is not one of"),
        ('chapters = "guess"', r"chapters 'guess' is not one of"),
        ('chapters = "site"', r'chapters = "site" needs .*site\.py'),
    ],
)
def test_a_page_with_a_bad_rendering_or_converter_names_its_file(tmp_path: Path, line: str, message: str):
    folder = _write(tmp_path, "a", PAGE.format(slug="a") + line + "\n")

    with pytest.raises(ValueError, match=message):
        site_pages({"a": folder})


def test_a_page_without_a_book_spec_exports_its_toml_metadata_and_measured_counts(tmp_path: Path):
    from polytypst.web_exporter import export_page

    built = tmp_path / "built"
    (built / "figures").mkdir(parents=True)
    (built / "reader.md").write_text(
        "# 第一章 开篇\n\n**要点** 一段。\n\n![图 1](figures/fig_1.svg)\n\n# 后记\n\n结尾。\n", encoding="utf-8"
    )
    (built / "figures" / "fig_1.svg").write_text("<svg/>", encoding="utf-8")
    folder = _write(
        tmp_path,
        "no_such_book",
        '[[page]]\nslug = "reader"\ndomain = "D"\ndescription = "d"\ntitle = "T"\nsubtitle = "S"\nauthor = "A"\n'
        f'language = "zh-CN"\nrendering = "editorial-business"\nchapters = "business-md"\nsource = "{built}"\nfiles = "reader"\n',
    )
    [page] = site_pages({"no_such_book": folder})

    entry = export_page(page, tmp_path, tmp_path / "assets")

    assert entry is not None
    assert {k: entry[k] for k in ("title", "subtitle", "author", "language", "renderingBadge")} == {
        "title": "T", "subtitle": "S", "author": "A", "language": "zh-CN", "renderingBadge": "Editorial HTML",
    }
    assert [(c["number"], c["title"]) for c in entry["chapters"]] == [("第一章", "开篇"), ("导言", "后记")]
    assert entry["stats"] == {"pages": 0, "figures": 0, "tables": 0, "chapters": 2}
    assert (tmp_path / "assets" / "reader" / "figures" / "fig_1.svg").is_file()
    assert entry["deliverables"] == {"pdf": "", "typst": "", "latex": "", "epub": ""}


def test_a_page_without_a_book_spec_or_title_names_the_missing_key(tmp_path: Path):
    from polytypst.web_exporter import export_page

    (tmp_path / "built").mkdir()
    (tmp_path / "built" / "book.md").write_text("# 第一章 开篇\n\n一段。\n", encoding="utf-8")
    folder = _write(
        tmp_path, "no_such_book",
        f'[[page]]\nslug = "x"\ndomain = "D"\ndescription = "d"\nchapters = "business-md"\nsource = "{tmp_path / "built"}"\n',
    )
    [page] = site_pages({"no_such_book": folder})

    with pytest.raises(ValueError, match=r"site\.toml: page x needs title, since no_such_book has no book spec"):
        export_page(page, tmp_path, tmp_path / "assets")


def test_figure_and_table_images_are_counted_by_their_toml_patterns(tmp_path: Path):
    from polytypst.web_exporter import _counts

    page = SitePage("k", tmp_path, "s", "D", "d", figure_images=r"fig\d", table_images=r"tab\d")
    html = '<p><img src="/a/5fig1.png"><img src="/a/5equ2.png"><img src="/a/5tab1.png"></p><table></table>'
    chapters = [{"blocks": [{"type": "html", "html": html}, {"type": "figure", "src": "/a/5fig1.png"}]}]

    assert _counts(page, chapters) == (1, 2)


def test_every_site_toml_in_books_parses():
    from polytypst.web_exporter import site_folders

    slugs = [p.slug for p in site_pages(site_folders())]

    assert len(slugs) == len(set(slugs))
    assert {"shitouji", "kerodon-ch1", "taocp-vol3", "modern-firm", "serre-arithmetique", "ahlfors"} <= set(slugs)
