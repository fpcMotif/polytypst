from pathlib import Path

from polytypst.books import book_specs, books, find_known_book
from polytypst.books_cli import parse_pages

PACKAGE = Path(__file__).parents[1] / "src"

def test_every_book_py_is_a_book():
    assert sorted(books()) == sorted(p.parent.name for p in PACKAGE.glob("*/book.py"))
    assert list(books()["bourbaki"].editions) == ["vintage", "facsimile", "modern"]
    assert list(books()["grothendieck"].editions) == ["monograph", "vintage", "facsimile"]


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
    from polytypst.algebra2.spec import ALGEBRA2_ILLUSTRATED_SPEC, ALGEBRA2_SPEC
    from polytypst.algebra3.spec import ALGEBRA3_SPEC
    from polytypst.ahlfors.spec import AHLFORS_ILLUSTRATED_SPEC, AHLFORS_SPEC
    from polytypst.bourbaki.spec import BOURBAKI_1970_SPEC, BOURBAKI_SPEC
    from polytypst.bourbaki_lie.spec import BOURBAKI_LIE_SPEC
    from polytypst.fermat.spec import FERMAT_SPEC
    from polytypst.fermat.spec_vol2 import FERMAT2_SPEC
    from polytypst.fermat.spec_vol3 import FERMAT3_SPEC
    from polytypst.fga.spec import FGA_SPEC
    from polytypst.fichtenholz_vol1.spec import (
        FICHTENHOLZ_VOL1_ILLUSTRATED_SPEC,
        FICHTENHOLZ_VOL1_SPEC,
    )
    from polytypst.functional_analysis.spec import FUNCTIONAL_ANALYSIS_SPEC
    from polytypst.grothendieck.spec import GROTHENDIECK_1971_SPEC, GROTHENDIECK_SPEC
    from polytypst.hecke.spec import HECKE_SPEC
    from polytypst.kashiwara.spec import KASHIWARA_SPEC
    from polytypst.kenji_alg.spec import KENJI_ALG_SPEC
    from polytypst.kenji_alg.spec_vol2 import KENJI_ALG2_SPEC
    from polytypst.kenji_alg.spec_vol3 import KENJI_ALG3_SPEC
    from polytypst.klein.spec import KLEIN_SPEC
    from polytypst.klein.zh_spec import KLEIN_ZH_SPEC
    from polytypst.kodaira.spec import KODAIRA_SPEC
    from polytypst.london_treasury.spec import LONDON_TREASURY_SPEC
    from polytypst.modern_geometry.spec import (
        MODERN_GEOMETRY_ILLUSTRATED_SPEC,
        MODERN_GEOMETRY_SPEC,
    )
    from polytypst.modern_geometry_vol2.spec import (
        MODERN_GEOMETRY_VOL2_ILLUSTRATED_SPEC,
        MODERN_GEOMETRY_VOL2_SPEC,
    )
    from polytypst.modern_geometry_vol3.spec import MODERN_GEOMETRY_VOL3_SPEC
    from polytypst.sga4_5.spec import SGA4_5_SPEC
    from polytypst.siegel_symplectic.spec import SIEGEL_SYMPLECTIC_SPEC
    from polytypst.siegel_symplectic.styles import STYLED_SPECS
    from polytypst.複素多様体論.spec import FUKUSO_SPEC
    from polytypst.ode_arnold.spec import ODE_ARNOLD_SPEC
    import importlib
    chinese_specs = {
        "1_宏观经济与产业结构": ("MACRO_SPEC", "MACRO_ILLUSTRATED_SPEC"),
        "3_国际经济环境的变化与日本经济": ("INTL_ECON_SPEC", "INTL_ECON_ILLUSTRATED_SPEC"),
        "4_不良债权与金融危机": ("NPL_CRISIS_SPEC", "NPL_CRISIS_ILLUSTRATED_SPEC"),
        "5_财政政策与社会保障": ("FISCAL_POLICY_SPEC", "FISCAL_POLICY_ILLUSTRATED_SPEC"),
        "6_劳动力市场与收入分配": ("LABOR_SPEC", "LABOR_ILLUSTRATED_SPEC"),
    }

    every = (
        *(
            getattr(importlib.import_module(f".{package}.spec", "polytypst"), name)
            for package, names in chinese_specs.items()
            for name in names
        ),
        ALGEBRA2_ILLUSTRATED_SPEC,
        ALGEBRA2_SPEC,
        ALGEBRA3_SPEC,
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
        GROTHENDIECK_SPEC,
        GROTHENDIECK_1971_SPEC,
        KLEIN_SPEC,
        KLEIN_ZH_SPEC,
        KODAIRA_SPEC,
        KENJI_ALG_SPEC,
        KENJI_ALG2_SPEC,
        KENJI_ALG3_SPEC,
        LONDON_TREASURY_SPEC,
        MODERN_GEOMETRY_SPEC,
        MODERN_GEOMETRY_ILLUSTRATED_SPEC,
        MODERN_GEOMETRY_VOL2_SPEC,
        MODERN_GEOMETRY_VOL2_ILLUSTRATED_SPEC,
        MODERN_GEOMETRY_VOL3_SPEC,
        SIEGEL_SYMPLECTIC_SPEC,
        *STYLED_SPECS.values(),
        HECKE_SPEC,
        FGA_SPEC,
        SGA4_5_SPEC,
        FICHTENHOLZ_VOL1_SPEC,
        FICHTENHOLZ_VOL1_ILLUSTRATED_SPEC,
        FUNCTIONAL_ANALYSIS_SPEC,
        ODE_ARNOLD_SPEC,
    )
    assert set(book_specs()) == {s.slug for s in every}
    kodaira = books()["kodaira"].spec
    assert find_known_book(Path(f"{kodaira.slug}.pdf")) is kodaira


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


def test_facsimile_edition_wires_one_to_one_page_map_and_style_diagrams(tmp_path: Path):
    import pymupdf

    from polytypst.edition import facsimile_edition
    from polytypst.grothendieck.book import FACSIMILE_STYLE
    from polytypst.grothendieck.spec import GROTHENDIECK_SPEC
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
        str(path.relative_to(PACKAGE.parent))
        for path in sorted(PACKAGE.glob("*/figures.py"))
        if "color_target = out_dir_color / png.name" in path.read_text(encoding="utf-8")
    ]
    assert smuggled == []


