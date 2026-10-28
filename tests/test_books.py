import json
from pathlib import Path

from polytypst.books import (
    BOOKS_DIR,
    book_by_key,
    book_specs,
    books,
    find_known_book,
)
from polytypst.books_cli import parse_pages
from polytypst.compiler.monograph import MonographCompiler, is_unnumbered_chapter
from polytypst.edition import OUTPUT

ROOT = Path(__file__).parents[1]
SNAPSHOTS = json.loads((ROOT / "tests" / "fixtures" / "book_snapshots.json").read_text(encoding="utf-8"))


def test_every_book_folder_is_a_book():
    folders = {p.parent.name for pattern in ("*/book.toml", "*/book.py") for p in BOOKS_DIR.glob(pattern)}
    assert sorted(books()) == sorted(folders)
    assert list(books()["bourbaki"].editions) == ["vintage", "facsimile", "modern"]
    assert list(books()["grothendieck"].editions) == ["monograph", "vintage", "facsimile"]


def test_source_scans_are_named_relative_to_the_sources_folder():
    absolute = {slug: spec.source_pdf for slug, spec in book_specs().items() if Path(spec.source_pdf or "").is_absolute()}
    assert absolute == {}


def test_code_holds_no_home_directory_paths():
    hits = [
        f"{path.relative_to(ROOT)}:{n}"
        for folder in ("src", "scripts", "books")
        for pattern in ("*.py", "*.toml")
        for path in sorted((ROOT / folder).rglob(pattern))
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if "/Users/" in line
    ]
    assert hits == []


def test_specs_come_from_the_editions():
    recorded = {e["spec"]["slug"] for book in SNAPSHOTS.values() for e in book["editions"].values() if e["spec"]}
    assert set(book_specs()) == recorded
    kodaira = books()["kodaira"].spec
    assert find_known_book(Path(f"{kodaira.slug}.pdf")) is kodaira


def test_london_treasury_deliverables():
    import json

    out_dir = ROOT / "output" / "london_treasury"
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


def test_facsimile_edition_wires_one_to_one_page_map_and_style_diagrams(tmp_path: Path):
    import pymupdf

    from polytypst.edition import facsimile_edition
    grothendieck = book_by_key("grothendieck")
    FACSIMILE_STYLE = grothendieck.editions["facsimile"].facsimile
    GROTHENDIECK_SPEC = grothendieck.spec
    from polytypst.parity.report import FACSIMILE

    edition = facsimile_edition(GROTHENDIECK_SPEC, tmp_path, FACSIMILE_STYLE)
    assert edition.rebuilt == tmp_path / f"{FACSIMILE_STYLE.slug}.pdf"
    assert edition.scan_line_breaks is True
    assert edition.parity is not None
    assert edition.parity.tolerance == FACSIMILE
    assert edition.parity.diagrams == FACSIMILE_STYLE.diagram_dir
    assert edition.parity.diagram_text == FACSIMILE_STYLE.diagram_text
    assert edition.parity.page_map() == {}

    doc = pymupdf.open()
    for _ in range(3):
        doc.new_page(width=200, height=300)
    doc.save(edition.rebuilt)
    assert edition.parity.page_map() == {1: [1], 2: [2], 3: [3]}


def test_vector_figure_editions_require_vectors_and_do_not_copy_raster_pngs():
    specs = book_specs()
    for slug in (
        "kodaira_complex_analysis",
        "ahlfors_illustrated",
        "modern_geometry",
        "modern_geometry_illustrated",
        "modern_geometry_vol2",
        "modern_geometry_vol2_illustrated",
        "fichtenholz_vol1",
        "fichtenholz_vol1_illustrated",
    ):
        assert specs[slug].require_vector_figures is True

    smuggled = [
        str(path.relative_to(ROOT))
        for path in sorted(BOOKS_DIR.glob("*/figures.py"))
        if "color_target = out_dir_color / png.name" in path.read_text(encoding="utf-8")
    ]
    assert smuggled == []


def test_goursat_is_a_catalog_book_with_the_scans_chapters():
    book = book_by_key("goursat")
    assert book.out_dir == OUTPUT / "goursat_colab"
    assert list(book.editions) == ["monograph"]
    assert book.figures is not None
    chapters = [(c.number, c.title, c.start_page, c.end_page) for c in book.spec.chapters]
    assert chapters[:3] == [
        (0, "Author's Preface", 4, 5),
        (0, "Translator's Preface", 6, 6),
        (1, "Derivatives and Differentials", 12, 45),
    ]
    assert chapters[-2:] == [(12, "Surfaces", 504, 545), (0, "Index", 546, 553)]
    assert all(is_unnumbered_chapter(title) for number, title, *_ in chapters if number == 0)
    placed = {fid for figures in book.spec.extra_figures.values() for fid, _ in figures}
    assert len(placed) == 37 and {"2", "40", "52"} <= placed


def test_goursat_pages_get_math_repairs_and_lose_the_scans_chapter_lines():
    compiler = MonographCompiler(book_by_key("goursat").spec)
    raw = (
        "# CHAPTER II\n"
        "## IMPLICIT FUNCTIONS FUNCTIONAL DETERMINANTS CHANGE OF VARIABLE\n"
        "### I. IMPLICIT FUNCTIONS\n"
        "### 20. A particular case. We frequently study $f(x, y)$\n\n"
        "with x # 0, where differ-\nential elements apply."
    )
    body = compiler.cleaner.clean(raw, 46).body
    assert "CHAPTER II" not in body
    assert "FUNCTIONAL DETERMINANTS" not in body
    assert "x \\neq 0" in body
    assert "differential elements" in body
    typst = compiler.format_typst(body)
    assert "== I. IMPLICIT FUNCTIONS" in typst
    assert "20. A particular case." in typst
    assert "=== 20." not in typst


def test_goursat_keeps_the_break_between_two_titles_the_scan_sets_apart():
    compiler = MonographCompiler(book_by_key("goursat").spec)
    raw = {
        275: "## II. CHANGE OF VARIABLES AREA OF A SURFACE",
        303: "### I. MULTIPLE INTEGRALS CHANGE OF VARIABLES",
        357: "## II. SERIES OF COMPLEX TERMS MULTIPLE SERIES",
    }
    typst = "\n".join(compiler.format_typst(compiler.cleaner.clean(md, pno).body) for pno, md in raw.items())
    assert "== II. CHANGE OF VARIABLES, AREA OF A SURFACE" in typst
    assert "== I. MULTIPLE INTEGRALS, CHANGE OF VARIABLES" in typst
    assert "== II. SERIES OF COMPLEX TERMS, MULTIPLE SERIES" in typst


def test_goursat_drops_the_scan_speck_read_as_a_dot_before_an_equation():
    compiler = MonographCompiler(book_by_key("goursat").spec)
    raw = "$$\n\\cdot f(x, y, a) = 0, \\quad \\frac{f(x, y, a + h) - f(x, y, a)}{h} = 0,\n$$"
    body = compiler.cleaner.clean(raw, 435).body
    assert "\\cdot" not in body
    assert "f(x, y, a) = 0, \\quad" in body


