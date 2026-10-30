import functools
from collections.abc import Iterator
from pathlib import Path

import pytest

from polytypst import books as catalog
from polytypst.compiler.monograph import ChapterSpec, MonographCompiler, MonographSpec
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
    ("[editions.big]\nkind = 'facsimile'", "editions.big.facsimile: a facsimile edition needs"),
    ("[editions.big]\nkind = 'scroll'", "editions.big.kind: 'scroll' is not one of"),
    ("[hooks]\nheading_hook = 'nowhere'", "hooks.heading_hook: hooks.py defines no function 'nowhere'"),
    ("[hooks]\ncolour = 'red'", "hooks: unknown key colour"),
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


def hooked(folder: Path, toml: str, hooks: str) -> Path:
    write(folder, toml)
    (folder / "hooks.py").write_text(hooks, encoding="utf-8")
    return folder


def test_hooks_fill_fields_by_their_own_name_or_by_the_hooks_table(tmp_path: Path):
    folder = hooked(tmp_path / "hooked_names", MINIMAL + (
        "[hooks]\nfigures = 'draw'\n"
        "[editions.plain]\nsummary = 'plain'\n"
        "[editions.loud]\nprepare = 'get_ready'\n"
        "[editions.loud.hooks]\nheading_hook = 'shout'\n"
    ), (
        "def heading_hook(lt, chapter):\n    return None\n"
        "def shout(lt, chapter):\n    return lt.upper()\n"
        "def draw(out_dir):\n    return []\n"
        "def get_ready(source):\n    return None\n"
        "def _helper():\n    return None\n"
    ))
    book = catalog.load_toml("hooked_names", folder)
    assert book.spec.heading_hook.__name__ == "heading_hook"
    assert book.figures.__name__ == "draw"
    assert book.editions["plain"].spec.heading_hook.__name__ == "heading_hook"
    assert book.editions["loud"].spec.heading_hook.__name__ == "shout"
    prepare = dict(zip(book.editions["loud"].build.__code__.co_freevars, book.editions["loud"].build.__closure__))
    assert prepare["prepare"].cell_contents.__name__ == "get_ready"


def test_a_public_hook_that_fills_no_field_is_an_error(tmp_path: Path):
    folder = hooked(tmp_path / "hooked_stray", MINIMAL, "def stray(out_dir):\n    return []\n")
    with pytest.raises(catalog.BookFileError, match="stray fill no field"):
        catalog.load_toml("hooked_stray", folder)


def test_a_facsimile_edition_takes_its_style_from_toml_and_hooks(tmp_path: Path):
    folder = hooked(tmp_path / "hooked_facsimile", MINIMAL + (
        "[editions.facsimile]\nkind = 'facsimile'\n"
        "[editions.facsimile.hooks]\ndiagram_boxes = 'boxes'\n"
        "[editions.facsimile.facsimile]\n"
        "slug = 'probe_facsimile'\ntitle = 'Probe (facsimile)'\nfont_file = '/fonts/x.ttf'\n"
        "font_stack = '(\"X\")'\nsize = 9.5\nweight = 400\ndiagram_dir = '@BOOK@/diagrams'\n"
        "scan_pages = [2, 1]\n"
        "diagram_text = { font = 'X', size = 9.5, weight = 400 }\n"
    ), "def boxes():\n    return {}\n")
    edition = catalog.load_toml("hooked_facsimile", folder).editions["facsimile"]
    style = edition.facsimile
    assert style.slug == "probe_facsimile"
    assert style.font_file == Path("/fonts/x.ttf")
    assert style.diagram_dir == folder / "diagrams"
    assert style.scan_pages == frozenset({1, 2})
    assert style.diagram_boxes.__name__ == "boxes"
    assert style.install_diagrams(tmp_path) == []
    assert edition.rebuilt == OUTPUT / "hooked_facsimile" / "probe_facsimile.pdf"
    assert edition.parity is not None and edition.parity.diagrams == folder / "diagrams"


def test_a_style_token_becomes_the_shared_style_file(shelf: Path):
    (shelf / "styles").mkdir()
    (shelf / "styles" / "series.typ").write_text("#set text(size: 10.5pt)\n", encoding="utf-8")
    folder = write(shelf / "probe", MINIMAL + "typst_front_matter = '''#let a = 1\n@STYLE:series@\n#let b = 2'''\n")
    spec = catalog.load_toml("probe", folder).spec
    assert spec.typst_front_matter == "#let a = 1\n#set text(size: 10.5pt)\n\n#let b = 2"


def test_an_unknown_style_token_is_an_error(shelf: Path):
    folder = write(shelf / "probe", MINIMAL + "typst_front_matter = '@STYLE:missing@'\n")
    with pytest.raises(catalog.BookFileError, match="styles/missing.typ"):
        _ = catalog.load_toml("probe", folder)


def test_engine_tokens_become_the_compilers_own_title_page_and_preamble(tmp_path: Path):
    folder = write(tmp_path / "probe", MINIMAL + (
        "typst_front_matter = '''#let before = 1\n@ENGINE_TITLE_PAGE@'''\n"
        "typst_preamble = '''@ENGINE_PREAMBLE@\n#let after = 2'''\n"
    ))
    spec = catalog.load_toml("probe", folder).spec
    plain = MonographSpec(slug="probe", title="Probe", author="A", domain="math")
    assert spec.typst_front_matter == "#let before = 1\n" + MonographCompiler(plain).build_typst_title_page()
    assert spec.typst_preamble == MonographCompiler(plain).build_typst_preamble() + "\n#let after = 2"
