import functools
from collections.abc import Iterator
from pathlib import Path

import pytest

from polytypst import books as catalog
from polytypst.compiler.monograph import ChapterSpec, MonographSpec
from polytypst.edition import OUTPUT

MINIMAL = 'slug = "probe"\ntitle = "Probe"\nauthor = "A"\ndomain = "math"\n'


def write(folder: Path, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "book.toml").write_text(text, encoding="utf-8")
    return folder


@pytest.fixture
def shelf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr(catalog, "BOOKS_DIR", tmp_path)
    monkeypatch.setattr(catalog, "books", functools.cache(catalog.books.__wrapped__))
    yield tmp_path


def test_book_toml_fields_become_the_spec_with_their_annotated_types(tmp_path: Path):
    folder = write(tmp_path / "probe", MINIMAL + (
        "year = 1981\n"
        "pdf_name_markers = ['probe', 'sonde']\n"
        "figure_pages = [3, 1]\n"
        "problems_pages = [10, 12]\n"
        "chapters = [{ number = 1, title = 'One', start_page = 1, end_page = 9 }]\n"
        "latex_preamble = '''\n\\usepackage{x}\n'''\n"
        "[page_fixups]\n'12' = [['a\\s+b', 'c']]\n"
        "[sections]\n'1.1' = [3, 'Intro']\n"
        "[figures]\ntop_pages = [2]\n"
    ))
    spec = catalog.load_toml("probe", folder).spec
    assert spec == MonographSpec(
        slug="probe", title="Probe", author="A", domain="math", year=1981,
        pdf_name_markers=("probe", "sonde"), figure_pages=frozenset({1, 3}), problems_pages=(10, 12),
        chapters=[ChapterSpec(1, "One", 1, 9)], latex_preamble="\\usepackage{x}\n",
        page_fixups={12: (("a\\s+b", "c"),)}, sections={"1.1": (3, "Intro")},
        figures=spec.figures,
    )
    assert spec.figures.top_pages == frozenset({2})


@pytest.mark.parametrize(("line", "message"), [
    ("colour = 'red'", "unknown key colour"),
    ("year = 'old'", "year: expected int"),
    ("footnote_reset = 'decade'", "footnote_reset: 'decade' is not one of"),
    ("heading_hook = 'mine'", "heading_hook: a function cannot be set"),
    ("problems_pages = [1, 2, 3]", "problems_pages: expected 2 items"),
    ("[page_fixups]\nfirst = []", "page_fixups: key 'first' is not an integer"),
    ("[editions.big]\nkind = 'facsimile'", "editions.big.kind: 'facsimile' needs a book.py"),
    ("[editions.big]\nsize = 3", "editions.big: unknown key size"),
    ("[editions.big.spec]\ncolour = 'red'", "editions.big.spec: unknown key colour"),
])
def test_book_toml_errors_name_the_file_and_the_key(tmp_path: Path, line: str, message: str):
    folder = write(tmp_path / "probe", MINIMAL + line + "\n")
    with pytest.raises(catalog.BookFileError) as error:
        catalog.load_toml("probe", folder)
    assert str(folder / "book.toml") in str(error.value)
    assert message in str(error.value)


def test_a_missing_required_field_is_an_error(tmp_path: Path):
    folder = write(tmp_path / "probe", 'slug = "probe"\ntitle = "Probe"\nauthor = "A"\n')
    with pytest.raises(catalog.BookFileError, match="domain"):
        catalog.load_toml("probe", folder)


def test_editions_override_the_spec_and_keep_their_old_output_folder(tmp_path: Path):
    folder = write(tmp_path / "probe", MINIMAL + (
        "legacy_state = 'probe3'\n"
        "[editions.vol3]\nsummary = 'volume 3'\n"
        "[editions.vol2]\nsummary = 'volume 2'\nlegacy_state = 'probe2'\n"
        "[editions.vol2.spec]\nslug = 'probe_two'\nyear = 1990\n"
    ))
    book = catalog.load_toml("probe", folder)
    assert book.out_dir == OUTPUT / "probe3"
    assert list(book.editions) == ["vol3", "vol2"]
    assert book.editions["vol3"].rebuilt == OUTPUT / "probe3" / "probe.pdf"
    assert book.editions["vol2"].rebuilt == OUTPUT / "probe2" / "probe_two.pdf"
    assert book.editions["vol2"].spec.year == 1990
    assert book.editions["vol2"].spec.title == "Probe"


def test_a_book_without_editions_gets_one_monograph(tmp_path: Path):
    book = catalog.load_toml("probe", write(tmp_path / "probe", MINIMAL))
    assert list(book.editions) == ["monograph"]
    assert book.out_dir == OUTPUT / "probe"


def test_repo_token_becomes_the_repository_folder(tmp_path: Path):
    folder = write(tmp_path / "probe", MINIMAL + "latex_preamble = '[Path=@REPO@/fonts/]'\n")
    spec = catalog.load_toml("probe", folder).spec
    assert spec.latex_preamble == f"[Path={catalog.BOOKS_DIR.parent}/fonts/]"


def test_a_broken_book_stops_only_itself(shelf: Path):
    write(shelf / "good", MINIMAL.replace("probe", "good"))
    write(shelf / "broken", MINIMAL + "year = 'old'\n")
    assert sorted(catalog.books()) == ["broken", "good"]
    assert catalog.book_by_key("good").spec.slug == "good"
    with pytest.raises(catalog.BookLoadError, match="'broken'"):
        catalog.book_by_key("broken")


def test_aliases_and_hyphens_find_a_book(shelf: Path):
    write(shelf / "sga_x", MINIMAL + "aliases = ['sgax']\n")
    assert catalog.book_by_key("sgax") is catalog.book_by_key("sga_x")
    assert catalog.book_by_key("sga-x") is catalog.book_by_key("sga_x")
    with pytest.raises(KeyError, match="unknown book 'nope'"):
        catalog.book_by_key("nope")


def test_a_python_book_imports_its_own_files_by_relative_import(shelf: Path):
    folder = shelf / "py_book"
    folder.mkdir()
    (folder / "spec.py").write_text(
        "from polytypst.compiler.monograph import MonographSpec\n"
        "SPEC = MonographSpec(slug='py_book', title='T', author='A', domain='math')\n", encoding="utf-8")
    (folder / "book.py").write_text(
        "from polytypst.edition import OUTPUT, Book, monograph_edition\n"
        "from .spec import SPEC\n"
        "BOOK = Book(SPEC, OUTPUT / 'py_book', {'monograph': monograph_edition(SPEC, OUTPUT / 'py_book')})\n",
        encoding="utf-8")
    assert catalog.book_by_key("py_book").spec.slug == "py_book"
    assert catalog.module("py_book", "spec").SPEC is catalog.book_by_key("py_book").spec
