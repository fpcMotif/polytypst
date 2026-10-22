import json
from pathlib import Path

import pymupdf

from polytypst import books_cli
from polytypst.review import (
    Finding,
    changes,
    latex_log_measures,
    pdf_measures,
    render_checklist,
    scan_grams,
    source_measures,
    text_map,
)

LINES = {
    1: [("Running Head 7", 0.95), ("alpha bravo charlie delta echo foxtrot", 0.5)],
    2: [("golf hotel india juliet kilo lima", 0.5)],
    3: [("mike november oscar papa quebec romeo", 0.5)],
}


def write_ocr(folder: Path) -> Path:
    ocr = folder / "source_ocr"
    ocr.mkdir(parents=True)
    for number, lines in LINES.items():
        rows = [
            {"text": t, "x": 0.1, "y": y, "w": 0.8, "h": 0.02, "confidence": 1.0}
            for t, y in lines
        ]
        (ocr / f"p{number:03d}.json").write_text(json.dumps(rows), encoding="utf-8")
    return ocr


def write_pdf(path: Path, pages: list[str], x: float = 40) -> Path:
    doc = pymupdf.open()
    for text in pages:
        doc.new_page(width=300, height=400).insert_text((x, 100), text, fontsize=9)
    doc.save(path)
    return path


def test_the_running_head_band_of_a_scan_page_is_not_content(tmp_path: Path) -> None:
    grams = scan_grams(write_ocr(tmp_path))
    assert not any("Running" in g or "Head" in g for g in grams[1])
    assert grams[1] and grams[2] and grams[3]


def test_each_scan_page_maps_to_the_rebuilt_page_that_holds_its_text(
    tmp_path: Path,
) -> None:
    grams = scan_grams(write_ocr(tmp_path))
    pdf = write_pdf(
        tmp_path / "r.pdf",
        ["golf hotel india juliet kilo lima", "alpha bravo charlie delta echo foxtrot"],
    )
    pages = {m.scan_page: m for m in text_map(grams, pdf)}
    assert (pages[1].rebuilt_page, pages[1].coverage) == (2, 1.0)
    assert (pages[2].rebuilt_page, pages[2].coverage) == (1, 1.0)
    assert (pages[3].rebuilt_page, pages[3].coverage) == (None, 0.0)


def test_text_set_past_the_right_page_edge_is_counted(tmp_path: Path) -> None:
    inside = write_pdf(tmp_path / "in.pdf", ["short line"])
    outside = write_pdf(
        tmp_path / "out.pdf",
        ["a line that starts near the edge and keeps going"],
        x=250,
    )
    assert pdf_measures(inside)["pages_text_past_edge"] == 0
    assert pdf_measures(outside)["pages_text_past_edge"] == 1


def test_latex_log_counts_overfull_boxes_missing_glyphs_and_undefined_references() -> (
    None
):
    log = (
        "Overfull \\hbox (60.5pt too wide) in paragraph at lines 3--4\n"
        "Overfull \\hbox (3.0pt too wide) in paragraph at lines 9--9\n"
        "Missing character: There is no ・ (U+30FB) in font Songti SC!\n"
        "LaTeX Warning: Reference `fig-1' on page 2 undefined on input line 7.\n"
        "LaTeX Font Warning: Font shape `TU/SongtiSC(0)/m/it' undefined\n"
        "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.\n"
    )
    m = latex_log_measures(log)
    assert (m["overfull_hbox"], m["overfull_hbox_over_50pt"], m["max_overfull_pt"]) == (
        2,
        1,
        60.5,
    )
    assert (
        m["missing_glyphs"],
        m["undefined_references"],
        m["font_shape_undefined"],
        m["rerun_needed"],
    ) == (1, 1, 1, 1)


def test_typst_source_counts_literal_numbers_links_footnotes_and_running_heads() -> (
    None
):
    src = (
        "=== 1 前言\n"
        "=== 结论\n"
        "如@fig-1-1 所示，见图 1-2 和表 2-3，式（1.4）。\n"
        "=== 标题#footnote[题注]\n"
        "文字#footnote[甲]#footnote[乙]。\n"
        "已经被日 2 通缩经济与货币政策\n"
        "\n"
        "本政府\n"
    )
    m = source_measures(src, "typst", ("通缩经济与货币政策",))
    assert (
        m["headings"],
        m["headings_with_typed_numbers"],
        m["heading_numbering_rule"],
    ) == (3, 1, 0)
    assert (
        m["links"],
        m["literal_figure_refs"],
        m["literal_table_refs"],
        m["literal_equation_refs"],
    ) == (1, 1, 1, 1)
    assert (m["footnotes"], m["chained_footnotes"], m["footnotes_in_headings"]) == (
        3,
        1,
        1,
    )
    assert m["running_head_leaks"] == 1


def test_latex_display_math_without_a_number_is_counted() -> None:
    src = "\\[\na=b\n\\]\n\\begin{equation}\nc=d\n\\label{eq-1}\\end{equation}\n见\\ref{eq-1}"
    m = source_measures(src, "latex", ())
    assert (m["unnumbered_display_math"], m["links"]) == (1, 1)


def test_a_measure_that_rose_is_reported_and_one_that_fell_is_not() -> None:
    old = {"a": 3, "b": 5, "c": 0.9}
    new = {"a": 4, "b": 2, "c": 0.9, "d": 1}
    assert changes(old, new) == ["a: 3 -> 4", "b: 5 -> 2", "d: new 1"]


def test_checklist_orders_findings_by_severity_with_open_before_closed() -> None:
    findings = [
        Finding("B-2", "book", "P2", "typst", "x.typ:1", "minor", "e"),
        Finding(
            "B-1", "book", "P0", "latex", "x.tex:1", "lost text", "e", status="fixed"
        ),
        Finding("B-3", "book", "P0", "typst", "x.typ:2", "wrong table", "e"),
    ]
    text = render_checklist(findings)
    assert text.index("B-3") < text.index("B-1") < text.index("B-2")
    assert "- [ ] **B-3**" in text and "- [x] **B-1**" in text


def test_review_writes_measures_pages_and_history_and_reports_changes(
    tmp_path: Path, capsys
) -> None:
    folder = tmp_path / "1_Book Title"
    write_ocr(folder)
    write_pdf(
        folder / "1.pdf",
        ["alpha bravo charlie delta echo foxtrot", "golf hotel india juliet kilo lima"],
    )
    (folder / "1.typ").write_text("=== 1 前言\n见图 1-1。\n", encoding="utf-8")
    scan = write_pdf(tmp_path / "scan.pdf", ["x", "y", "z"])
    assert books_cli.main("review", [str(folder), "--scan", str(scan)]) == 0
    out = folder / "review"
    measures = json.loads((out / "measures.json").read_text(encoding="utf-8"))
    assert measures["1.pdf"]["pages_coverage_below_half"] == 1
    assert measures["1.typ"]["literal_figure_refs"] == 1
    assert "scan_page,1.pdf:page,1.pdf:coverage" in (out / "pages.csv").read_text(
        encoding="utf-8"
    )
    assert len((out / "history.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    (folder / "1.typ").write_text("=== 1 前言\n见图 1-1 和图 1-2。\n", encoding="utf-8")
    capsys.readouterr()
    assert books_cli.main("review", [str(folder), "--scan", str(scan)]) == 0
    out_text = capsys.readouterr().out
    assert "1.typ literal_figure_refs: 1 -> 2" in out_text
    assert "lowest coverage: scan 3 -> none (0.0), scan 1 -> 1 (1.0), scan 2 -> 2 (1.0)" in out_text


def test_checklist_command_renders_markdown_beside_the_findings(tmp_path: Path) -> None:
    path = tmp_path / "findings.jsonl"
    path.write_text(
        json.dumps(Finding("X-1", "all", "P1", "both", "w", "what", "ev").__dict__)
        + "\n",
        encoding="utf-8",
    )
    assert books_cli.main("checklist", [str(path)]) == 0
    assert "- [ ] **X-1**" in (tmp_path / "findings.md").read_text(encoding="utf-8")


def test_checklist_names_each_bad_line_and_writes_nothing(tmp_path: Path, capsys) -> None:
    good = Finding("X-1", "all", "P1", "both", "w", "what", "ev").__dict__
    lines = [
        good,
        good | {"id": "X-2", "severity": "P5"},
        {k: v for k, v in good.items() if k != "evidence"} | {"id": "X-3"},
        good,
        good | {"id": "X-4", "status": "done"},
    ]
    path = tmp_path / "findings.jsonl"
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n{not json\n", encoding="utf-8")
    assert books_cli.main("checklist", [str(path)]) == 1
    out = capsys.readouterr().out
    for n, word in ((2, "severity"), (3, "evidence"), (4, "X-1"), (5, "status"), (6, "JSON")):
        assert f"line {n}:" in out and word in out
    assert not (tmp_path / "findings.md").exists()
