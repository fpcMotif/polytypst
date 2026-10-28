from pathlib import Path

import pytest

from polytypst.web_exporter import site_pages

PAGE = '[[page]]\nslug = "{slug}"\neditions = ["vol1"]\ndomain = "Number Theory"\ndescription = "D"\n'


def test_each_page_of_each_site_toml_is_listed_in_folder_order(tmp_path: Path):
    for key, text in (("a", PAGE.format(slug="a-1") + "\n" + PAGE.format(slug="a-2")), ("b", None), ("c", PAGE.format(slug="c-1"))):
        (tmp_path / key).mkdir()
        if text:
            (tmp_path / key / "site.toml").write_text(text, encoding="utf-8")
    folders = {k: tmp_path / k for k in ("a", "b", "c")}

    assert site_pages(folders) == [
        ("a", "a-1", ("vol1",), "Number Theory", "D"),
        ("a", "a-2", ("vol1",), "Number Theory", "D"),
        ("c", "c-1", ("vol1",), "Number Theory", "D"),
    ]


def test_a_page_with_a_missing_or_unknown_key_names_its_file(tmp_path: Path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "site.toml").write_text(PAGE.format(slug="a").replace('domain = "Number Theory"\n', 'domian = "x"\n'))

    with pytest.raises(ValueError, match=r"a/site\.toml: each \[\[page\]\] needs exactly the keys"):
        site_pages({"a": tmp_path / "a"})
