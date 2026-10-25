import json
import zipfile

import pymupdf
import pytest

from polytypst import books as books_module
from polytypst import books_cli, cli
from polytypst.compiler.monograph import MonographSpec
from polytypst.compiler.source_numbers import LATEX, TYPST
from polytypst.edition import Book, Edition


@pytest.fixture
def built(monkeypatch, tmp_path):
    calls = []
    edition = Edition(
        tmp_path / "x.pdf", lambda source, formats, footnotes: calls.append(formats), formats=frozenset({"pdf", "tex"})
    )
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    return calls


def test_build_makes_every_format_by_default(built):
    assert books_cli.main("build", ["probe"]) == 0
    assert built == [frozenset({"pdf", "tex"})]


def test_build_makes_only_the_requested_formats(built):
    assert books_cli.main("build", ["probe", "--formats", "pdf"]) == 0
    assert books_cli.main("build", ["probe", "--formats", ""]) == 0
    assert built == [frozenset({"pdf"}), frozenset()]


def test_build_rejects_a_format_the_edition_cannot_make(built, capsys):
    with pytest.raises(SystemExit):
        books_cli.main("build", ["probe", "--formats", "epub"])
    assert "epub" in capsys.readouterr().err
    assert built == []


def test_build_passes_the_footnote_numbering(monkeypatch, tmp_path):
    calls = []
    spec = MonographSpec(domain="math", slug="x", title="X", author="A", footnote_style="paren")
    edition = Edition(tmp_path / "x.pdf", lambda source, formats, footnotes: calls.append(footnotes), spec=spec)
    book = Book(spec, tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    assert books_cli.main("build", ["probe"]) == 0
    assert books_cli.main("build", ["probe", "--footnotes", "running"]) == 0
    assert calls == ["original", "running"]


def test_build_fails_when_literal_numbers_rise_above_the_baseline(monkeypatch, tmp_path, capsys):
    spec = MonographSpec(domain="math", slug="x", title="X", author="A")
    typst = TYPST.chapter_start + "#strong[定理 7] 设 $P$ 是域.\n"
    edition = Edition(
        tmp_path / "x.pdf", lambda source, formats, footnotes: (tmp_path / "x.typ").write_text(typst, encoding="utf-8"), spec=spec
    )
    book = Book(spec, tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_cli, "BASELINE", tmp_path / "baseline.json")
    assert books_cli.main("build", ["probe"]) == 1
    assert "TYPST_LITERAL_ITEM_HEAD 1 > 0" in capsys.readouterr().out
    (tmp_path / "baseline.json").write_text(json.dumps({"probe": {"monograph": {"TYPST_LITERAL_ITEM_HEAD": 1}}}))
    assert books_cli.main("build", ["probe"]) == 0


def test_build_rejects_running_footnotes_for_a_book_without_notes(built, capsys):
    with pytest.raises(SystemExit):
        books_cli.main("build", ["probe", "--footnotes", "running"])
    assert "footnotes" in capsys.readouterr().err
    assert built == []


BODY = "This paragraph is ordinary body prose that fills a page with enough characters."


def write_pdf(path, lines):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    for i, line in enumerate(lines):
        _ = page.insert_text((72, 120 + 40 * i), line, fontsize=11)
    doc.save(path)


@pytest.fixture
def audited(monkeypatch, tmp_path):
    pdf = tmp_path / "x.pdf"
    edition = Edition(pdf, lambda source, formats, footnotes: None)
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    return pdf, tmp_path / "baseline.json"


def test_audit_update_records_counts_that_the_next_audit_accepts(audited):
    pdf, baseline = audited
    write_pdf(pdf, [BODY, "Roy,~1952 wrote here"])
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline), "--update"]) == 0
    assert json.loads(baseline.read_text())["probe"]["monograph"]["NO_LITERAL_TILDE"] == 1
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline)]) == 0


def test_audit_update_refuses_to_raise_a_recorded_count_without_allow_rise(audited, capsys):
    pdf, baseline = audited
    write_pdf(pdf, [BODY, BODY])
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline), "--update"]) == 0
    write_pdf(pdf, [BODY, "Roy,~1952 wrote here"])
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline), "--update"]) == 1
    assert "NO_LITERAL_TILDE 1 > 0" in capsys.readouterr().out
    assert "NO_LITERAL_TILDE" not in json.loads(baseline.read_text())["probe"]["monograph"]
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline), "--update", "--allow-rise"]) == 0
    assert json.loads(baseline.read_text())["probe"]["monograph"]["NO_LITERAL_TILDE"] == 1


def test_audit_update_lowers_a_count_that_fell(audited):
    pdf, baseline = audited
    write_pdf(pdf, [BODY, "Roy,~1952 wrote here"])
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline), "--update"]) == 0
    write_pdf(pdf, [BODY, BODY])
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline), "--update"]) == 0
    assert "NO_LITERAL_TILDE" not in json.loads(baseline.read_text())["probe"]["monograph"]


def test_audit_of_every_baseline_edition_fails_on_a_rule_that_rose(audited, capsys):
    pdf, baseline = audited
    write_pdf(pdf, [BODY, BODY])
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline), "--update"]) == 0
    write_pdf(pdf, [BODY, "Roy,~1952 wrote here"])
    assert books_cli.main("audit", ["--baseline", str(baseline)]) == 1
    assert "NO_LITERAL_TILDE 1 > 0" in capsys.readouterr().out


def test_audit_of_every_edition_fails_on_a_built_edition_missing_from_the_baseline(audited, capsys):
    pdf, baseline = audited
    write_pdf(pdf, [BODY, BODY])
    baseline.write_text("{}\n")
    assert books_cli.main("audit", ["--baseline", str(baseline)]) == 1
    assert "probe monograph: FAIL, no baseline" in capsys.readouterr().out
    assert books_cli.main("audit", ["--baseline", str(baseline), "--update"]) == 0
    assert books_cli.main("audit", ["--baseline", str(baseline)]) == 0


def test_audit_of_every_edition_skips_an_unbuilt_edition_missing_from_the_baseline(audited, capsys):
    _, baseline = audited
    baseline.write_text("{}\n")
    assert books_cli.main("audit", ["--baseline", str(baseline)]) == 0
    assert "probe" not in capsys.readouterr().out


def write_epub(path, text):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        )
        z.writestr(
            "content.opf",
            '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">x</dc:identifier>'
            "<dc:title>X</dc:title><dc:language>en</dc:language></metadata>"
            '<manifest><item id="c" href="c.xhtml" media-type="application/xhtml+xml"/></manifest>'
            '<spine><itemref idref="c"/></spine></package>',
        )
        z.writestr("c.xhtml", f'<html xmlns="http://www.w3.org/1999/xhtml"><body><p>{text}</p></body></html>')


def test_audit_checks_the_epub_an_edition_declares_beside_its_pdf(monkeypatch, tmp_path, capsys):
    pdf = tmp_path / "x.pdf"
    write_pdf(pdf, [BODY, BODY])
    write_epub(pdf.with_suffix(".epub"), f"{BODY} Roy,~1952 wrote here")
    edition = Edition(pdf, lambda source, formats, footnotes: None, formats=frozenset({"pdf", "epub"}))
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    baseline = tmp_path / "baseline.json"
    baseline.write_text("{}\n")
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline)]) == 1
    assert "EPUB_NO_LITERAL_TILDE 1 > 0" in capsys.readouterr().out


def test_audit_fails_when_a_declared_format_has_no_output(monkeypatch, tmp_path, capsys):
    pdf = tmp_path / "x.pdf"
    write_pdf(pdf, [BODY, BODY])
    edition = Edition(pdf, lambda source, formats, footnotes: None, formats=frozenset({"pdf", "tex"}))
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, {"monograph": edition})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    baseline = tmp_path / "baseline.json"
    baseline.write_text('{"probe": {"monograph": {}}}\n')
    assert books_cli.main("audit", ["--baseline", str(baseline)]) == 1
    assert "polytypst build probe --edition monograph --formats tex" in capsys.readouterr().out


def test_audit_counts_an_edition_with_no_baseline_against_zero(audited, capsys):
    pdf, baseline = audited
    write_pdf(pdf, [BODY, "Roy,~1952 wrote here"])
    baseline.write_text("{}\n")
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline)]) == 1
    assert "NO_LITERAL_TILDE 1 > 0" in capsys.readouterr().out


def test_audit_leaves_line_end_hyphens_to_an_edition_that_keeps_the_scan_line_breaks(monkeypatch, tmp_path, capsys):
    pdf = tmp_path / "x.pdf"
    doc = pymupdf.open()
    for lines in ([BODY, "il résulte du lemme de Nakayama et Bour-", "ouvert non vide est un espace topolo-"], [BODY, BODY]):
        page = doc.new_page(width=612, height=792)
        for i, line in enumerate(lines):
            _ = page.insert_text((72, 120 + 40 * i), line, fontsize=11)
    doc.save(pdf)
    build = lambda source, formats, footnotes: None
    editions = {"monograph": Edition(pdf, build), "facsimile": Edition(pdf, build, scan_line_breaks=True)}
    book = Book(MonographSpec(domain="math", slug="x", title="X", author="A"), tmp_path, editions)
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    baseline = tmp_path / "baseline.json"
    baseline.write_text('{"probe": {"monograph": {}, "facsimile": {}}}\n')
    assert books_cli.main("audit", ["--baseline", str(baseline)]) == 1
    out = capsys.readouterr().out
    monograph, facsimile = out.split("probe facsimile")
    assert "HYPHENATED_PROPER_NOUN 1 > 0" in monograph
    assert "CROSS_PAGE_WORD_SPLIT 1 > 0" in monograph
    assert facsimile.startswith(": ok")


def test_audit_counts_literal_numbers_in_the_typst_and_latex_beside_the_pdf(monkeypatch, tmp_path, capsys):
    pdf = tmp_path / "x.pdf"
    write_pdf(pdf, [BODY, BODY])
    _ = pdf.with_suffix(".typ").write_text(TYPST.chapter_start + "Remarque (1.6.6) Soient $F$ et (1.1.3).\n")
    _ = pdf.with_suffix(".tex").write_text(LATEX.chapter_start + "Voir {[}8{]}.\n")
    spec = MonographSpec(domain="math", slug="x", title="X", author="A", cross_references=True)
    book = Book(spec, tmp_path, {"monograph": Edition(pdf, lambda source, formats, footnotes: None, spec=spec)})
    monkeypatch.setattr(books_cli, "books", lambda: {"probe": book})
    monkeypatch.setattr(books_module, "books", lambda: {"probe": book})
    baseline = tmp_path / "baseline.json"
    baseline.write_text("{}\n")
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline)]) == 1
    out = capsys.readouterr().out
    assert "TYPST_LITERAL_ITEM_HEAD 1 > 0" in out
    assert "TYPST_REFERENCE_WITHOUT_TARGET 1 > 0" in out
    assert "LATEX_UNLINKED_CITATION 1 > 0" in out


def test_audit_fails_when_the_edition_is_not_built(audited, capsys):
    _, baseline = audited
    assert books_cli.main("audit", ["probe", "--baseline", str(baseline)]) == 1
    assert "polytypst build probe" in capsys.readouterr().out


def test_top_level_help_lists_the_book_commands(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["polytypst", "--help"])
    with pytest.raises(SystemExit):
        cli.main()
    out = capsys.readouterr().out
    for command in ("books", "build", "parity", "audit", "new-book"):
        assert f"polytypst {command}" in out
    assert "modern-firm" not in out


def test_book_build_runs_figures_and_shares_page_parser(tmp_path):
    import argparse

    events = []
    edition = Edition(
        tmp_path / "x.pdf",
        lambda source, formats, footnotes: events.append(("build", formats, footnotes)),
        formats=frozenset({"pdf", "tex"}),
    )
    book = Book(
        MonographSpec(domain="math", slug="x", title="X", author="A"),
        tmp_path,
        {"monograph": edition},
        figures=lambda out_dir: events.append(("figures", out_dir)),
    )
    built_edition = book.build()
    assert built_edition is edition
    assert events == [("figures", tmp_path), ("build", frozenset({"pdf", "tex"}), "original")]
    assert cli.page_set is books_cli.parse_pages
    with pytest.raises(argparse.ArgumentTypeError):
        books_cli.parse_pages("bad-range")
    assert not hasattr(books_module, "render_book_figures")

