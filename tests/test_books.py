from pathlib import Path

from polytypst.books import book_specs, books, find_known_book
from polytypst.books_cli import parse_pages

PACKAGE = Path(__file__).parents[1] / "src"

def test_every_book_py_is_a_book():
    assert sorted(books()) == sorted(p.parent.name for p in PACKAGE.glob("*/book.py"))
    assert list(books()["bourbaki"].editions) == ["vintage", "facsimile", "modern"]


def test_source_scans_are_named_relative_to_the_sources_folder():
    absolute = {slug: spec.source_pdf for slug, spec in book_specs().items() if Path(spec.source_pdf or "").is_absolute()}
    assert absolute == {}


def test_code_holds_no_home_directory_paths():
    root = PACKAGE.parent
    hits = [
        f"{path.relative_to(root)}:{n}"
        for folder in ("src", "scripts")
        for path in sorted((root / folder).rglob("*.py"))
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if "/Users/" in line
    ]
    assert hits == []


def test_specs_come_from_the_editions():
    from polytypst.ahlfors.spec import AHLFORS_ILLUSTRATED_SPEC, AHLFORS_SPEC
    from polytypst.bourbaki.spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC
    from polytypst.bourbaki_lie.spec import BOURBAKI_LIE_SPEC
    from polytypst.fermat.spec import FERMAT_SPEC
    from polytypst.fermat.spec_vol2 import FERMAT2_SPEC
    from polytypst.fermat.spec_vol3 import FERMAT3_SPEC
    from polytypst.kashiwara.spec import KASHIWARA_SPEC
    from polytypst.kenji_alg.spec import KENJI_ALG_SPEC
    from polytypst.kenji_alg.spec_vol2 import KENJI_ALG2_SPEC
    from polytypst.kenji_alg.spec_vol3 import KENJI_ALG3_SPEC
    from polytypst.klein.spec import KLEIN_SPEC
    from polytypst.klein.zh_spec import KLEIN_ZH_SPEC
    from polytypst.kodaira.spec import KODAIRA_SPEC
    from polytypst.london_treasury.spec import LONDON_TREASURY_SPEC
    from polytypst.複素多様体論.spec import FUKUSO_SPEC

    every = (
        AHLFORS_SPEC,
        AHLFORS_ILLUSTRATED_SPEC,
        BOURBAKI_SPEC,
        BOURBAKI_1970_SPEC,
        BOURBAKI_LIE_SPEC,
        FERMAT_SPEC,
        FERMAT2_SPEC,
        FERMAT3_SPEC,
        FUKUSO_SPEC,
        KASHIWARA_SPEC,
        KLEIN_SPEC,
        KLEIN_ZH_SPEC,
        KODAIRA_SPEC,
        KENJI_ALG_SPEC,
        KENJI_ALG2_SPEC,
        KENJI_ALG3_SPEC,
        LONDON_TREASURY_SPEC,
    )
    assert set(book_specs()) == {s.slug for s in every}
    kodaira = books()["kodaira"].spec
    assert find_known_book(Path("x.pdf"), kodaira.pdf_page_count) is not None


def test_london_treasury_deliverables():
    import json

    out_dir = PACKAGE.parent / "output" / "london_treasury"
    links_path = out_dir / "extracted_links.json"
    assert links_path.exists()
    links = json.loads(links_path.read_text(encoding="utf-8"))
    assert len(links) == 53
    assert all(len(item["clean_text"]) > 200 for item in links)
    for ext in ("pdf", "typ", "tex", "epub", "md"):
        assert (out_dir / f"book.{ext}").exists()


def test_parse_pages():
    assert parse_pages("31-34,40") == {31, 32, 33, 34, 40}
    assert parse_pages("7") == {7}
