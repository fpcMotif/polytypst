from pathlib import Path

from polytypst.books import book_specs, books, find_known_book
from polytypst.books_cli import parse_pages

PACKAGE = Path(__file__).parents[1] / "polytypst"


def test_every_book_py_is_a_book():
    assert sorted(books()) == sorted(p.parent.name for p in PACKAGE.glob("*/book.py"))
    assert list(books()["bourbaki"].editions) == ["vintage", "facsimile", "modern"]


def test_specs_come_from_the_editions():
    from polytypst.ahlfors.spec import AHLFORS_ILLUSTRATED_SPEC, AHLFORS_SPEC
    from polytypst.bourbaki.spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC
    from polytypst.bourbaki_lie.spec import BOURBAKI_LIE_SPEC
    from polytypst.fermat.spec import FERMAT_SPEC
    from polytypst.fermat.spec_vol2 import FERMAT2_SPEC
    from polytypst.kashiwara.spec import KASHIWARA_SPEC
    from polytypst.klein.spec import KLEIN_SPEC
    from polytypst.klein.zh_spec import KLEIN_ZH_SPEC
    from polytypst.kodaira.spec import KODAIRA_SPEC

    every = (AHLFORS_SPEC, AHLFORS_ILLUSTRATED_SPEC, BOURBAKI_SPEC, BOURBAKI_1970_SPEC, BOURBAKI_LIE_SPEC,
             FERMAT_SPEC, FERMAT2_SPEC, KASHIWARA_SPEC, KLEIN_SPEC, KLEIN_ZH_SPEC, KODAIRA_SPEC)
    assert set(book_specs()) == {s.slug for s in every}
    kodaira = books()["kodaira"].spec
    assert find_known_book(Path("x.pdf"), kodaira.pdf_page_count) is not None


def test_parse_pages():
    assert parse_pages("31-34,40") == {31, 32, 33, 34, 40}
    assert parse_pages("7") == {7}
