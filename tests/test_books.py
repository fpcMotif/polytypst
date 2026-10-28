import json
from pathlib import Path

from polytypst.books import BOOKS_DIR, book_specs, books, find_known_book, module
from polytypst.books_cli import parse_pages

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
    FACSIMILE_STYLE = module("grothendieck").FACSIMILE_STYLE
    GROTHENDIECK_SPEC = module("grothendieck", "spec").GROTHENDIECK_SPEC
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


